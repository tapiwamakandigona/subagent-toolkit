#!/usr/bin/env python3
"""Use saved credentials inside an authorized Playwright-compatible script."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from credential_store import CredentialError, read_secret, redact_output


class BrowserCredentialError(Exception):
    pass


def https_origin(url: str) -> tuple[str, str, int]:
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username:
            raise ValueError("not a plain HTTPS origin")
        return "https", parsed.hostname.lower(), parsed.port or 443
    except ValueError:
        raise BrowserCredentialError("Credential fill requires an approved HTTPS origin") from None


def require_origin(page_url: str, authorized_origin: str) -> None:
    if https_origin(page_url) != https_origin(authorized_origin):
        raise BrowserCredentialError("Page origin differs from the credential's approved origin")


def safe_error(error: Exception, values: list[str]) -> str:
    message = redact_output(
        str(error).encode("utf-8", errors="replace"),
        [value.encode("utf-8") for value in values],
    ).decode("utf-8", errors="replace")
    return f"{type(error).__name__}: {message}"


async def fill_saved_login(
    page,
    *,
    authorized_origin: str,
    username_alias: str,
    password_alias: str,
    username_selector: str,
    password_selector: str,
    store: str | Path | None = None,
) -> None:
    """Fill only; caller controls supported submission and the login evidence."""
    require_origin(page.url, authorized_origin)
    if not username_selector.strip() or not password_selector.strip():
        raise BrowserCredentialError("Inspect the login form and provide explicit selectors")
    values: list[str] = []
    try:
        username = read_secret(username_alias, store).decode("utf-8")
        values.append(username)
        password = read_secret(password_alias, store).decode("utf-8")
        values.append(password)
        password_field = page.locator(password_selector)
        if (await password_field.get_attribute("type") or "").lower() != "password":
            raise BrowserCredentialError("Refusing to fill a password into a non-password input")
        await page.locator(username_selector).fill(username)
        require_origin(page.url, authorized_origin)
        await password_field.fill(password)
        require_origin(page.url, authorized_origin)
    except (CredentialError, UnicodeDecodeError) as error:
        raise BrowserCredentialError(
            "Saved login unavailable or not text: " + safe_error(error, values)
        ) from None
    except Exception as error:
        raise BrowserCredentialError(
            "Browser credential fill failed: " + safe_error(error, values)
        ) from None


async def confirm_signed_in(page, *, authorized_origin: str, selector: str) -> bool:
    require_origin(page.url, authorized_origin)
    if not selector.strip():
        raise BrowserCredentialError("A positive signed-in selector is required")
    return await page.locator(selector).is_visible()
