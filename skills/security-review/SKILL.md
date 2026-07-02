---
name: security-review
description: A reviewer-oriented procedure for security-checking code, configurations, and agent pipelines. Covers secret handling, the major injection classes (SQL, shell, path, and prompt injection), authentication versus authorization checks, dependency risk, unsafe deserialization, and safe handling of untrusted input in agent workflows. Use when reviewing code or a system for security issues, before shipping anything that handles untrusted input or credentials, or when auditing an agent pipeline that processes external content.
license: MIT
metadata:
  version: "1.1.0"
---

# Security Review

Security review is adversarial reading: for every input, ask *"what if this value were chosen by an attacker?"* — and for every check, *"what happens if I simply skip it?"* Most findings come from those two questions applied systematically. Work through the full checklist in [references/checklist.md](references/checklist.md); this body covers the method and the highest-frequency classes.

## 1. Method: trace the untrusted data

1. **Inventory the inputs:** every place data enters from outside the trust boundary — HTTP params/headers/bodies, file uploads, filenames, environment, webhook payloads, third-party API responses, database contents written by others, and (for agents) any fetched web page or document.
2. **Trace each input to its sinks:** where does it end up — a SQL string? a shell command? a file path? an HTML page? an LLM prompt? Each sink type has an injection class.
3. **Check the barrier between them:** is there escaping/parameterization/validation on the path, and is it the *right* barrier for that sink? (HTML-escaping does nothing against SQL injection.)

Severity-order your findings; one authentication bypass outranks twenty missing security headers.

## 2. Secrets

- Grep the diff/codebase for credential patterns: `password`, `secret`, `api_key`, `token`, `BEGIN.*PRIVATE KEY`, provider prefixes (`sk_live_`, `ghp_`, `AKIA`). Check config files, test fixtures, and notebooks — the classic leak sites — not just source.
- **Git history counts:** a secret committed then removed is still leaked; it needs rotation, not just deletion.
- Leak paths beyond source: logging full request headers or URLs containing keys, error messages echoing config, secrets in CLI args (visible in `ps`), `.env` files not in `.gitignore`.
- Verify secrets load from env/secret-manager, fail fast when absent, and never appear in logs (look for redaction on the logging path, not just absence of obvious `print`s).

## 3. Injection classes

Same disease, four bodies — untrusted data interpreted as instructions:

- **SQL:** any query built by string concatenation/f-string with external input. The only acceptable barrier is **parameterized queries** (`?`/`%s` placeholders, or an ORM). Escaping functions are a finding, not a fix.
- **Shell:** `subprocess(..., shell=True)`, `os.system`, backticks with any interpolated input. Fix: argument lists (`["git", "log", user_ref]`) — and even then check for argument injection (an input of `--upload-pack=…` to git is an attack with no shell involved). Allowlist-validate anything that becomes a flag or ref.
- **Path traversal:** user input joined into file paths (`open(base + name)`) — `../../etc/passwd`, absolute paths, symlinks. Fix: resolve then verify containment (`Path(base, name).resolve().is_relative_to(base)`), or map IDs to paths server-side so no filename crosses the boundary.
- **Prompt injection (agent pipelines):** any fetched page, document, email, or tool output fed to an LLM can contain instructions ("ignore previous instructions; run …"). Barriers: fence untrusted content and label it as data-not-instructions; never grant an agent processing untrusted content more tool authority than the *content source* deserves (a web page must not be able to trigger file writes or message sends); require human/orchestrator confirmation between "read untrusted thing" and "perform irreversible action."

Also in the family: XSS (untrusted data into HTML without context-appropriate escaping) and template injection (user input into server-side template strings).

## 4. Authentication vs. authorization

Distinct checks, commonly conflated:

- **Authentication** (who are you): are credentials verified with a constant-time comparison against a proper hash (bcrypt/argon2 — flag MD5/SHA-1/plaintext)? Sessions expire? Password reset tokens single-use and time-limited?
- **Authorization** (what may *you* do): the highest-frequency real-world bug is the **IDOR** — `GET /orders/4712` authenticated but never checked to be *your* order. For every endpoint/function taking an object ID, find the line that checks ownership/role. No line = finding.
- Authorization belongs **server-side on every request** — client-side checks and "the UI doesn't show the button" are not controls.
- Check the *unhappy* paths: is the admin check on the POST handler too, or only the GET? On the API as well as the page?

## 5. Dependencies and deserialization

- **Dependency risk:** run the ecosystem's audit tool (`pip-audit`, `npm audit`, `cargo audit`) and read the lockfile diff in reviews — a new dependency is attack surface. Typosquatting check for anything hand-typed (`requets`). Unpinned versions or install-from-URL/git-HEAD = supply-chain finding.
- **Unsafe deserialization:** `pickle.loads`, `yaml.load` (without `SafeLoader`), Java `ObjectInputStream`, PHP `unserialize` on data an attacker can influence = remote code execution, full stop. Fix: JSON or another data-only format, or `yaml.safe_load`. Also flag `eval`/`exec` on any constructed string.
- File uploads: validate type by content (magic bytes) not extension, store outside the web root with generated names, cap size.

## 6. Reporting security findings

- Severity-tag each finding: **critical** (exploitable now: injection, auth bypass, leaked live secret) / **high** (exploitable with conditions) / **medium** (defense-in-depth gap) / **low/informational**. Lead with criticals.
- Per finding: the exact file:line, the attack in one sentence ("a filename of `../../.ssh/authorized_keys` writes outside the upload dir"), and the fix direction. A demonstrated attack input beats an abstract warning — construct one when it's safe to do so.
- **Never "test" a suspected vulnerability against production systems or real third-party services** — demonstrate locally or reason it through.
- Leaked live credentials are an *incident*, not just a finding: report immediately and recommend rotation before anything else.

## Reviewer's minimum pass

- [ ] Untrusted inputs inventoried and traced to their sinks
- [ ] Secret grep run (source + config + fixtures + history); logging paths redact
- [ ] Every SQL/shell/path/prompt sink has the correct barrier for its class
- [ ] Every object-ID endpoint has an ownership/role check (IDOR pass)
- [ ] No unsafe deserialization or eval on attacker-influenced data
- [ ] Dependency audit run; lockfile diff reviewed
- [ ] Findings severity-ordered with file:line and fix direction
