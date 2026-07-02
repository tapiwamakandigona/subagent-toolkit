"""Unit tests for fetch_page.py: Retry-After parsing (incl. HTTP-date form),
URL scheme allowlist, soft-failure behavior, and charset handling.

Network access is faked via monkeypatched urlopen — no real requests.
"""

import email.message
import email.utils
import io
import time
import urllib.request

import pytest

import fetch_page


# ------------------------------------------------------- Retry-After --------

def test_retry_after_integer_seconds():
    assert fetch_page.parse_retry_after("7", attempt=0) == 7.0


def test_retry_after_http_date():
    future = email.utils.formatdate(time.time() + 30, usegmt=True)
    delay = fetch_page.parse_retry_after(future, attempt=0)
    assert 20 <= delay <= 35


def test_retry_after_http_date_in_past_clamps_to_zero():
    past = email.utils.formatdate(time.time() - 3600, usegmt=True)
    assert fetch_page.parse_retry_after(past, attempt=0) == 0.0


def test_retry_after_garbage_falls_back_to_backoff():
    delay = fetch_page.parse_retry_after("soon-ish", attempt=2)
    assert 4.0 <= delay <= 5.0  # 2**2 + jitter


def test_retry_after_missing_falls_back_to_backoff():
    delay = fetch_page.parse_retry_after(None, attempt=1)
    assert 2.0 <= delay <= 3.0


def test_retry_after_capped_at_60s():
    assert fetch_page.parse_retry_after("999999", attempt=0) == 60.0


# --------------------------------------------------- scheme allowlist -------

def test_file_scheme_rejected(tmp_path):
    with pytest.raises(fetch_page.FetchError, match="scheme"):
        fetch_page.fetch("file:///etc/hostname", tmp_path)


def test_ftp_scheme_rejected(tmp_path):
    with pytest.raises(fetch_page.FetchError, match="scheme"):
        fetch_page.fetch("ftp://example.com/x", tmp_path)


def test_http_scheme_allowed(tmp_path, monkeypatch):
    _install_fake_response(monkeypatch, b"<html>" + b"x" * 600 + b"</html>")
    body = fetch_page.fetch("http://example.test/", tmp_path, respect_robots=False)
    assert "xxx" in body


# ------------------------------------------------------- fake urlopen -------

class _FakeResponse:
    def __init__(self, payload: bytes, content_type="text/html", charset=None,
                 url="http://example.test/"):
        self.headers = email.message.Message()
        ct = content_type + (f"; charset={charset}" if charset else "")
        self.headers["Content-Type"] = ct
        self.url = url
        self._buf = io.BytesIO(payload)

    def read(self):
        return self._buf.read()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _install_fake_response(monkeypatch, payload, **kwargs):
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(req)
        return _FakeResponse(payload, **kwargs)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return calls


# ------------------------------------------------------- soft failure -------

def test_small_page_warns_and_returns_body(tmp_path, monkeypatch, capsys):
    calls = _install_fake_response(monkeypatch, b"<html>tiny</html>")
    body = fetch_page.fetch("http://example.test/tiny", tmp_path,
                            respect_robots=False)
    assert body == "<html>tiny</html>"
    assert len(calls) == 1  # deterministic detection: no retries
    assert "soft-failure" in capsys.readouterr().err


def test_soft_failure_not_cached(tmp_path, monkeypatch):
    _install_fake_response(monkeypatch, b"<html>tiny</html>")
    fetch_page.fetch("http://example.test/tiny", tmp_path, respect_robots=False)
    assert not fetch_page.cache_path(tmp_path, "http://example.test/tiny").exists()


def test_captcha_marker_warns_and_returns(tmp_path, monkeypatch, capsys):
    payload = b"<html>please solve this CAPTCHA to continue" + b" pad" * 200 + b"</html>"
    _install_fake_response(monkeypatch, payload)
    body = fetch_page.fetch("http://example.test/blocked", tmp_path,
                            respect_robots=False)
    assert "CAPTCHA" in body
    assert "soft-failure" in capsys.readouterr().err


def test_normal_page_cached(tmp_path, monkeypatch):
    payload = b"<html><body>" + b"content " * 100 + b"</body></html>"
    _install_fake_response(monkeypatch, payload)
    url = "http://example.test/page"
    body = fetch_page.fetch(url, tmp_path, respect_robots=False)
    assert fetch_page.cache_path(tmp_path, url).exists()
    # Second call served from cache: no urlopen needed.
    monkeypatch.setattr(urllib.request, "urlopen", _raise_if_called)
    assert fetch_page.fetch(url, tmp_path, respect_robots=False) == body


def _raise_if_called(*a, **k):
    raise AssertionError("urlopen called despite cache hit")


# ---------------------------------------------------------- charset ---------

def test_declared_charset_honored(tmp_path, monkeypatch):
    payload = ("<html>" + "héllo wörld " * 60 + "</html>").encode("latin-1")
    _install_fake_response(monkeypatch, payload, charset="iso-8859-1")
    body = fetch_page.fetch("http://example.test/latin", tmp_path,
                            respect_robots=False)
    assert "héllo wörld" in body


def test_missing_charset_defaults_to_utf8(tmp_path, monkeypatch):
    payload = ("<html>" + "héllo " * 100 + "</html>").encode("utf-8")
    _install_fake_response(monkeypatch, payload)
    body = fetch_page.fetch("http://example.test/utf8", tmp_path,
                            respect_robots=False)
    assert "héllo" in body


def test_binary_content_type_rejected(tmp_path, monkeypatch):
    _install_fake_response(monkeypatch, b"%PDF-1.7 ....",
                           content_type="application/pdf")
    with pytest.raises(fetch_page.FetchError, match="content-type"):
        fetch_page.fetch("http://example.test/doc.pdf", tmp_path,
                         respect_robots=False)


# ------------------------------------------------------ markdown path -------

def test_strip_boilerplate_removes_script_content():
    html = ("<html><head><style>.a{color:red}</style></head><body>"
            "<script>var x=1;</script><nav>Menu</nav>"
            "<p>Real content</p><footer>Foot</footer></body></html>")
    out = fetch_page.strip_boilerplate(html)
    assert "var x=1" not in out
    assert ".a{color:red}" not in out
    assert "Menu" not in out
    assert "Foot" not in out
    assert "Real content" in out
