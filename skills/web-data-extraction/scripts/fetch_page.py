#!/usr/bin/env python3
"""Polite, cached page fetcher with markdown conversion.

Reference implementation of the fetch -> cache -> markdown pipeline from
the web-data-extraction skill. Standard library only for fetching/caching;
markdown conversion uses `markdownify` if available, else a minimal fallback.

Usage:
    python fetch_page.py <url> [more urls...] [--cache-dir .fetch_cache] [--delay 1.0]

Prints markdown for each URL to stdout (separated by a header line) and
caches raw HTML on disk so re-runs never re-fetch.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.request

USER_AGENT = "subagent-toolkit-fetcher/1.0 (+https://github.com/your-org/subagent-toolkit)"
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
TIMEOUT_S = 20
SOFT_FAILURE_MARKERS = ("captcha", "access denied", "enable javascript", "are you a robot")


def cache_path(cache_dir: pathlib.Path, url: str) -> pathlib.Path:
    return cache_dir / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")


def fetch(url: str, cache_dir: pathlib.Path) -> str:
    """Fetch URL with caching, retries with exponential backoff + jitter."""
    path = cache_path(cache_dir, url)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")

    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            if _looks_like_soft_failure(body):
                raise RuntimeError(f"soft failure page (captcha/consent shell): {url}")
            cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            return body
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code not in RETRY_STATUSES:
                raise  # non-retryable 4xx: fail loudly
            retry_after = e.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else (2**attempt + random.random())
        except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
            last_err = e
            delay = 2**attempt + random.random()
        if attempt < MAX_RETRIES:
            print(f"[retry {attempt + 1}/{MAX_RETRIES}] {url}: {last_err} (sleep {delay:.1f}s)", file=sys.stderr)
            time.sleep(delay)
    raise RuntimeError(f"failed after {MAX_RETRIES} retries: {url}: {last_err}")


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


def to_markdown(body: str) -> str:
    try:
        from markdownify import markdownify  # type: ignore

        return markdownify(body, strip=["script", "style"])
    except ImportError:
        parser = _TextExtractor()
        parser.feed(body)
        return parser.text()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--cache-dir", default=".fetch_cache", type=pathlib.Path)
    ap.add_argument("--delay", default=1.0, type=float, help="seconds between requests (politeness)")
    args = ap.parse_args()

    for i, url in enumerate(args.urls):
        if i > 0:
            time.sleep(args.delay + random.random() * 0.5)
        body = fetch(url, args.cache_dir)
        print(f"\n\n===== {url} =====\n")
        print(to_markdown(body))


if __name__ == "__main__":
    main()
