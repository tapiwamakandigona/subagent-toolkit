#!/usr/bin/env python3
"""Polite, cached page fetcher with markdown conversion.

Reference implementation of the fetch -> cache -> markdown pipeline from
the web-data-extraction skill. Standard library only for fetching/caching;
markdown conversion uses `markdownify` if available, else a minimal fallback.

Usage:
    python fetch_page.py <url> [more urls...] [--cache-dir .fetch_cache]
                         [--delay 1.0] [--no-cache] [--no-robots]

Prints markdown for each URL to stdout (separated by a header line) and
caches raw HTML on disk so re-runs never re-fetch (bypass with --no-cache).
Checks robots.txt before fetching (skip with --no-robots).

Known limitation: only the URL *scheme* is validated — http(s) requests to
internal/link-local addresses (e.g. 169.254.169.254) are still reachable, and
the scheme of redirect targets is not re-validated.
"""

from __future__ import annotations

import argparse
import email.utils
import hashlib
import html.parser
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

USER_AGENT = (
    "subagent-toolkit-fetcher/1.1 "
    "(+https://github.com/tapiwamakandigona/subagent-toolkit)"
)
RETRY_STATUSES = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 3
MAX_RETRY_DELAY_S = 60.0
TIMEOUT_S = 20
SOFT_FAILURE_MARKERS = ("captcha", "access denied", "enable javascript", "are you a robot")
ALLOWED_SCHEMES = {"http", "https"}
TEXTUAL_CONTENT_RE = re.compile(
    r"^(text/|application/(xhtml\+xml|xml|json|rss\+xml|atom\+xml))", re.I
)

_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}


class FetchError(Exception):
    """A fetch failed in a way worth a clean error message (no traceback)."""


def cache_path(cache_dir: pathlib.Path, url: str) -> pathlib.Path:
    return cache_dir / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")


def parse_retry_after(value: str | None, attempt: int) -> float:
    """Parse a Retry-After header (int seconds or HTTP-date per RFC 9110).

    Falls back to exponential backoff on any parse failure. The returned
    delay is always capped at MAX_RETRY_DELAY_S and never negative.
    """
    delay: float | None = None
    if value:
        value = value.strip()
        try:
            delay = float(int(value))
        except ValueError:
            try:
                dt = email.utils.parsedate_to_datetime(value)
                delay = dt.timestamp() - time.time()
            except (ValueError, TypeError, OverflowError):
                delay = None
    if delay is None:
        delay = 2**attempt + random.random()
    return max(0.0, min(delay, MAX_RETRY_DELAY_S))


def check_url_scheme(url: str) -> None:
    scheme = urllib.parse.urlsplit(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise FetchError(
            f"unsupported URL scheme {scheme or '(none)'!r} (only http/https): {url}"
        )


def robots_allows(url: str) -> bool:
    """Check robots.txt for the URL's host (cached per scheme+host).

    If robots.txt cannot be fetched or parsed, proceed with a warning.
    """
    parts = urllib.parse.urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        robots_url = origin + "/robots.txt"
        try:
            req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                rp.parse(resp.read().decode("utf-8", errors="replace").splitlines())
            _robots_cache[origin] = rp
        except urllib.error.HTTPError as e:
            # 4xx (no robots.txt) conventionally means "everything allowed".
            _robots_cache[origin] = None
            if e.code >= 500:
                print(f"[warn] robots.txt fetch failed ({e.code}) for {origin}: "
                      "proceeding without robots check", file=sys.stderr)
        except Exception as e:  # network errors: proceed, but say so
            _robots_cache[origin] = None
            print(f"[warn] robots.txt unavailable for {origin} ({e}): "
                  "proceeding without robots check", file=sys.stderr)
    rp = _robots_cache[origin]
    return rp is None or rp.can_fetch(USER_AGENT, url)


def decode_body(resp) -> str:
    """Decode an HTTP response using its declared charset (fallback utf-8).

    Raises FetchError for clearly binary content-types.
    """
    ctype = resp.headers.get_content_type() or ""
    if ctype and not TEXTUAL_CONTENT_RE.match(ctype):
        raise FetchError(f"binary or non-text content-type {ctype!r}: {resp.url}")
    charset = resp.headers.get_content_charset() or "utf-8"
    raw = resp.read()  # read once: the stream is exhausted after this
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:  # unknown charset label
        return raw.decode("utf-8", errors="replace")


def fetch(url: str, cache_dir: pathlib.Path, use_cache: bool = True,
          respect_robots: bool = True) -> str:
    """Fetch URL with caching, retries with exponential backoff + jitter."""
    check_url_scheme(url)
    path = cache_path(cache_dir, url)
    if use_cache and path.exists():
        return path.read_text(encoding="utf-8", errors="replace")

    if respect_robots and not robots_allows(url):
        raise FetchError(f"blocked by robots.txt: {url}")

    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                body = decode_body(resp)
            if _looks_like_soft_failure(body):
                # Deterministic detection: warn and return, do NOT retry or
                # hard-fail (small legit pages exist), and do not cache it.
                print(f"[warn] possible soft-failure page (captcha/consent shell "
                      f"or tiny body, {len(body)} bytes): {url}", file=sys.stderr)
                return body
            cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            return body
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code not in RETRY_STATUSES:
                raise FetchError(f"HTTP {e.code} {e.reason}: {url}") from e
            delay = parse_retry_after(e.headers.get("Retry-After"), attempt)
        except FetchError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            delay = min(2**attempt + random.random(), MAX_RETRY_DELAY_S)
        if attempt < MAX_RETRIES:
            print(f"[retry {attempt + 1}/{MAX_RETRIES}] {url}: {last_err} "
                  f"(sleep {delay:.1f}s)", file=sys.stderr)
            time.sleep(delay)
    raise FetchError(f"failed after {MAX_RETRIES} retries: {url}: {last_err}")


def _looks_like_soft_failure(body: str) -> bool:
    if len(body) < 500:  # suspiciously tiny: likely a JS shell or block page
        return True
    head = body[:4000].lower()
    return any(marker in head for marker in SOFT_FAILURE_MARKERS)


class _TextExtractor(html.parser.HTMLParser):
    """Minimal boilerplate-stripping HTML -> markdown-ish text (fallback)."""

    SKIP = {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form"}
    BLOCK = {"p", "div", "li", "tr", "br", "section", "article"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
        elif self._skip_depth == 0:
            if tag in {"h1", "h2", "h3", "h4"}:
                self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
            elif tag == "li":
                self.parts.append("\n- ")
            elif tag in self.BLOCK:
                self.parts.append("\n")
            elif tag == "a":
                href = dict(attrs).get("href")
                if href:
                    self.parts.append(f"[link:{href}] ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self.parts.append(data.strip() + " ")

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


_BOILERPLATE_TAGS = ("script", "style", "nav", "footer", "aside", "noscript")
_BOILERPLATE_RE = re.compile(
    r"<(%s)\b[^>]*>.*?</\1\s*>" % "|".join(_BOILERPLATE_TAGS),
    re.IGNORECASE | re.DOTALL,
)


def strip_boilerplate(body: str) -> str:
    """Remove boilerplate ELEMENTS (tags + their content) before conversion.

    markdownify's strip=[...] removes tags but keeps their text content,
    leaking JS/CSS/nav text into the "clean" markdown output.
    """
    prev = None
    while prev != body:  # handle (rare) nested same-tag elements
        prev = body
        body = _BOILERPLATE_RE.sub("", body)
    return body


def to_markdown(body: str) -> str:
    try:
        from markdownify import markdownify  # type: ignore

        return markdownify(strip_boilerplate(body))
    except ImportError:
        parser = _TextExtractor()
        parser.feed(body)
        return parser.text()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--cache-dir", default=".fetch_cache", type=pathlib.Path)
    ap.add_argument("--delay", default=1.0, type=float,
                    help="seconds between requests (politeness)")
    ap.add_argument("--no-cache", action="store_true",
                    help="always re-fetch, ignoring any cached copy")
    ap.add_argument("--no-robots", action="store_true",
                    help="skip the robots.txt check")
    args = ap.parse_args()
    if args.delay < 0:
        print("[warn] --delay must be >= 0; using 0", file=sys.stderr)
        args.delay = 0.0

    for i, url in enumerate(args.urls):
        if i > 0:
            time.sleep(args.delay + random.random() * 0.5)
        try:
            body = fetch(url, args.cache_dir, use_cache=not args.no_cache,
                         respect_robots=not args.no_robots)
        except FetchError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"\n\n===== {url} =====\n")
        print(to_markdown(body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
