# Authenticated Web Sessions

Discipline for browser-automation work that logs into real accounts (Google, LinkedIn, banking-adjacent, anything with 2FA). The failure mode this prevents: a session silently expires mid-task, the agent re-logs-in sloppily, and half the work happens against a logged-out page.

## 1. Session lifetime is a decision, not a default

- **Always set an explicit session timeout when creating the session.** Provider defaults are short (Browserbase: ~300 s) and will kill the session between two steps of a multi-step task. For account-login work, create the session with a long lifetime up front — e.g. `get_browser(name, timeout_seconds=21600)` for a 6-hour window. You cannot extend a dead session; you can only re-login in a new one, which may re-trigger 2FA.
- One task family = one named session. Reuse the same name across script invocations to reconnect instead of re-authenticating.
- **Check login state at the start of every script**, not just the first: assert the URL/title is the logged-in surface before acting. A `goto` that lands on `accounts.google.com/...signin` means the session or cookies died — handle it, don't click into the void.

## 2. 2FA is a human-in-the-loop step — design for it

- Expect the first login (and sometimes re-logins) to fire a push prompt / pick-a-number to the owner's phone. Message the owner immediately with exactly what to tap, then **poll for the post-login URL in the background** (e.g. a loop checking every 10 s for up to 10 min) rather than blocking on a fixed sleep.
- Subsequent fresh sessions often skip 2FA (device trust) — but never count on it in the plan.

## 3. Act like the DOM is hostile

- **Filter every locator with `:visible`.** SPAs (Gmail especially) keep stale hidden views in the DOM; the "first matching row" is frequently an invisible one and clicks time out confusingly.
- **Rich-text editors under CSP:** direct `el.innerHTML = ...` can throw `TrustedHTML` errors. Insert via a Trusted Types policy + `execCommand`: create `trustedTypes.createPolicy(name, {createHTML: s => s})`, then `document.execCommand('insertHTML', false, policy.createHTML(html))` on the focused contenteditable.
- **Hovercards/overlays intercept clicks.** Avoid mousing over entity chips (contacts, profiles); prefer keyboard navigation and shortcuts when a click keeps getting intercepted.
- Attach files via `expect_file_chooser` on the real attach control, not by hunting hidden `<input type=file>` nodes.

## 4. Verify from the service's own record, then screenshot

- DOM-attribute scraping for verification is brittle (e.g. recipient chips whose `data-name` is empty). **Before an irreversible action (Send, Post, Pay): take a screenshot and confirm the fields visually**; assert on cheap invariants (subject text, body length, attachment chip count) and let a failed assert abort the action — a false abort costs a retry, a false send costs trust.
- **After the action, verify in the system of record**, not the toast alone: search Sent mail / posted feed / order history, and check the failure channel too (e.g. `from:mailer-daemon newer_than:1h` for email bounces).
- Clean up side effects of failed attempts (stray drafts, half-filled forms) or report them to the owner explicitly.

## 5. Report state honestly

A session that died and was re-authenticated, a 2FA prompt the owner approved, an attempt that left a stray draft — all belong in the handoff report. The next agent inherits the account state you leave behind.
