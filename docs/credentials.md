# Credentials

Moved verbatim from HARNESS.md in v3.2.0 so the always-read protocol stays small.
Read this when the operator pastes or a task needs a credential.

The operator provisions credentials **per environment — usually by pasting
them into chat**. That paste is the provisioning step, not a policy
violation. Refusing to store it strands the whole environment without
credentials.

- **Store it immediately, outside any repo.** Put pasted credentials in a
  locked-down local file (secrets dir `700`, file `600`), confirm the
  storage path back to the operator, and use them for tasks from there —
  never from chat scrollback.
- **Flag exposure once, then move on.** If credentials arrived in plaintext
  chat or are visibly reused across services, say so once with concrete
  rotation advice — then proceed with the work. Don't block on it, and
  don't repeat the warning every run.
- **Values never leave the secrets file.** No credential values in commits,
  logs, reports, prompts, state files, or issue text. When flagging an
  anomaly (e.g. a suspicious trailing character), describe it without
  printing the value.
- **Missing ≠ inventable.** If a task needs a credential that isn't
  present, stop and ask; never guess, scaffold placeholders, or dig one
  out of unrelated chat history.

## High-autonomy credential handoff

Using an operator-authorized credential for the stated service/task is an
ordinary step, not a new permission request. A fresh agent checks the private
store's aliases and loads values inside code; it never prints the files into
model-visible output. `templates/credential_store.py` supplies 700/600 storage,
availability checks, and output-redacted subprocess use. Browser passwords
are supported via `templates/browser_credentials.py`; see `docs/browser.md`.
Missing credentials block only the dependent feature, not independent work.
Keep actual values out of standing instructions and this package.
