# Browser & authenticated sessions

Moved verbatim from HARNESS.md in v3.2.0 so the always-read protocol stays small.
Read this before any task that logs into a site through a browser.

When an agent logs into a site through a browser, **open a long-running,
6-hour session** — not the short default. A run that authenticates and then
loses the session mid-task has to re-login (re-triggering 2FA and burning a
human interaction) or silently fails on an expired session.

- **Create the session with a 6-hour keep-alive.** Browser sessions default
  to a short idle timeout (300s in the Viktor SDK); pass the max instead.
  In the Viktor SDK: `get_browser(name, timeout_seconds=21600)` (21600s =
  6h). 6h is the Browserbase per-session ceiling. VERIFIED 2026-07-25:
  `timeout_seconds=21600` is accepted and the session is created; the 300s
  default is what causes premature drops.
- **One named session, reconnect — never re-create.** Use a stable session
  name (`get_browser("gmail")`) and reconnect to it across script runs;
  re-creating a session throws away the logged-in state and forces another
  login. Only `close_browser(name)` when the whole task is done.
- **Login is a one-time cost per session; do the whole job inside it.**
  After login the site's own auth cookies persist far beyond the browser
  session (Google's, VERIFIED, last ~400 days), so the binding constraint
  is the browser session lifetime, not the cookies — which is exactly why
  the session must be long. Batch all authenticated work into the single
  6h window.
- **2FA is a human handoff.** When a login hits 2FA (device prompt, code,
  passkey), post the exact prompt to the human and wait for approval; where
  offered, tick "don't ask again on this device" so a reconnect within the
  session doesn't re-challenge. Never guess or loop on a challenge.
- **Evidence before "logged in".** Confirm auth by an authenticated URL or
  a signed-in DOM element (e.g. landed on `myaccount.google.com`), not by
  the absence of an error. Label it VERIFIED only with that evidence.
