# Browser authentication — authorized password use

Browser login with an operator-provided password is supported when the
operator owns/controls the account, authorizes the task, and the platform
permits the flow. Do not refuse merely because a password is involved or
force an API-only substitute for a specifically requested browser workflow.

## Runtime-only secrets

Store aliases outside every repository in a directory with mode 700, files
with mode 600. A new agent reads only the store pointer and alias names.
Inside its script, use `browser_credentials.fill_saved_login`; do not `cat`
values, pass them in CLI args, or put them in prompts/logs/state files.
Inspect the actual form to choose selectors; never guess them.

The helper checks the approved HTTPS origin and a real password input. It
fills but does not submit, claim login, defeat MFA or bypass a CAPTCHA.
Confirm login using a positive signed-in UI element before claiming success.
Hand user-presence, approval, recovery and MFA challenges requiring the
operator to them; do not brute-force or loop on failed authentication.

## Verification pages: capability is not permission

Do not treat every verification page as an automatic refusal. Complete
ordinary verification using the supported browser/model workflow when the
site and tool permit automated completion. If the challenge requires human
action, automation is prohibited, or completion would defeat anti-bot/access
controls, hand it to the operator. Do not use repeated retries, solver farms,
identity/fingerprint spoofing, or other evasion as a fallback.
This package does not test or claim any model's CAPTCHA-solving capability.

## One session, real lifecycle

Use one stable named session for the task. Reconnect while it remains alive
rather than creating a fresh session per script. On Viktor the currently
documented helper is `get_browser(name, timeout_seconds=21600)`: that is a
six-hour hard lifetime from creation, not an idle timeout. Sessions may close
at turn end; `keep_alive=True` is only for a background job that still needs it.
It does not promise persistence across new threads/agents. An expired session
requires a fresh session and legitimate login, not an assumed authenticated state.

## Example (selectors must come from the real form)

```python
from sdk.utils.browser import get_browser
from browser_credentials import fill_saved_login, confirm_signed_in

browser = await get_browser("authorized-portal", timeout_seconds=21600)
await browser.goto(approved_login_url)
await fill_saved_login(
    browser.page,
    authorized_origin=approved_origin,
    username_alias="portal_username",
    password_alias="portal_password",
    username_selector=inspected_username_selector,
    password_selector=inspected_password_selector,
)
await browser.page.locator(inspected_submit_selector).click()
await browser.page.locator(inspected_signed_in_selector).wait_for(state="visible")
assert await confirm_signed_in(
    browser.page, authorized_origin=approved_origin,
    selector=inspected_signed_in_selector,
)
```

This is a script fragment, not a tested live account login. The portable
helper accepts any Playwright-compatible page; the `sdk` import is Viktor-specific.

## Recording and saved-login injection

Private local files do not make a remote browser's recording private. Do not
capture login network traffic, dump cookies/headers, record Playwright traces
with values, or take unmasked login screenshots. Verify provider recording
settings/redaction rather than promising mode 600 protects remote artifacts.

When exposed by the current platform, Viktor's `list_browser_logins()` shows
sites/usernames only; focusing the password field and calling
`browser.inject_login(origin)` types a saved value server-side without returning
it to the agent. Check tool availability in the current environment first.
Saved-login injection was not exercised by these local regression tests.
If a remote provider cannot meet the account's secret-handling requirements,
use a controlled local browser or a human login handoff. Ordinary authorized
browser work can continue once authenticated.
