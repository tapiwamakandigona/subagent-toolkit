# Security Review Checklist

The full working checklist. Run every section that applies to the artifact under review; record N/A explicitly rather than skipping silently. Severity guide: **C**ritical / **H**igh / **M**edium / **L**ow shown per item as the *typical* severity when found — adjust to context.

## 1. Secrets & credentials

- [ ] (C) Grep for hardcoded credentials: `password|passwd|secret|api[_-]?key|token|credential`, `BEGIN (RSA|EC|OPENSSH) PRIVATE KEY`, provider prefixes `sk_live_|sk_test_|ghp_|gho_|AKIA|xoxb-|xoxp-`
- [ ] (C) Same grep over **git history** (`git log -p | grep`, or a scanner) — removed ≠ rotated
- [ ] (H) Config files, `.env`, test fixtures, notebooks, CI YAML checked — not just source
- [ ] (H) Secrets never logged: check what goes into log statements — full headers, full URLs (keys in query params), request/response dumps, exception messages echoing config
- [ ] (M) Secrets not passed as CLI arguments (visible in `ps`/shell history); env vars or files instead
- [ ] (M) `.env`/key files in `.gitignore`; deploy artifacts don't bundle them
- [ ] (M) Tokens/keys are least-privilege (scopes) and rotatable; no shared "god" credential

## 2. Injection

**SQL / query languages**
- [ ] (C) No query built by concatenation/f-string/format with external input — parameterized only
- [ ] (H) ORM escape hatches (`raw()`, `extra()`, `text()`) checked with the same rigor
- [ ] (M) LIKE patterns and ORDER BY columns from user input allowlisted (parameterization doesn't cover identifiers)

**Shell / process**
- [ ] (C) No `shell=True` / `os.system` / backticks with interpolated input; argument lists used
- [ ] (H) Argument injection: inputs that could start with `-` are separated (`--`) or allowlisted
- [ ] (H) Filenames/refs passed to tools (git, ffmpeg, imagemagick, curl) validated — these tools have option-injection and URL-scheme attack surface of their own

**Path**
- [ ] (C) User-influenced paths resolved and containment-checked against the intended base dir
- [ ] (H) Archive extraction guarded against zip-slip (`../` entries) and symlinks
- [ ] (M) Filenames regenerated server-side (IDs → paths), not attacker-chosen

**Web output**
- [ ] (H) XSS: untrusted data escaped for its context (HTML body vs attribute vs JS vs URL); framework auto-escaping not bypassed (`|safe`, `dangerouslySetInnerHTML`, `v-html`)
- [ ] (H) Server-side template injection: no user input in template *source* strings
- [ ] (M) Untrusted URLs validated for scheme (block `javascript:`, `data:`, `file:`)

**Prompt (agent pipelines)**
- [ ] (C) Untrusted content (web pages, docs, emails, tool output) fenced and labeled as data-not-instructions before entering an LLM prompt
- [ ] (C) Tool authority proportional to content trust: agents reading untrusted content cannot trigger irreversible/external actions (sends, writes, deletes, purchases) without confirmation
- [ ] (H) Outputs derived from untrusted content are treated as untrusted downstream (taint propagates)
- [ ] (M) System-prompt/instruction hierarchy states that fetched content never overrides operator instructions

## 3. Authentication

- [ ] (C) Password storage: bcrypt/scrypt/argon2 with per-user salt — flag MD5/SHA-1/SHA-256-unsalted/plaintext/reversible
- [ ] (H) Credential comparison constant-time (no early-exit string compare on tokens/MACs)
- [ ] (H) Session tokens: cryptographically random, expire, invalidated on logout and password change
- [ ] (H) Password reset tokens single-use, time-limited, not guessable, not leaked via referrer
- [ ] (M) Login/reset endpoints rate-limited (credential stuffing); generic failure messages (no user-enumeration oracle)
- [ ] (M) Cookies: `HttpOnly`, `Secure`, `SameSite` set for session cookies
- [ ] (M) JWT: algorithm pinned (reject `none`/algorithm-confusion), expiry enforced, signature actually verified

## 4. Authorization

- [ ] (C) **IDOR pass:** every endpoint/function taking an object ID has an explicit ownership/role check — find the line, per endpoint
- [ ] (C) Privilege checks server-side on **every** request/verb (not just the page that renders the button; not just GET)
- [ ] (H) Mass assignment: request bodies can't set fields like `role`, `is_admin`, `owner_id` (allowlist the settable fields)
- [ ] (H) Multi-tenancy: every query scoped by tenant, not just by object ID
- [ ] (M) Admin/debug endpoints (`/admin`, `/debug`, `/metrics`, feature flags) gated, not merely unlisted

## 5. Dependencies & supply chain

- [ ] (H) Ecosystem audit run (`pip-audit` / `npm audit` / `cargo audit` / `govulncheck`) and criticals triaged
- [ ] (H) Lockfile present and diffed in review; new dependencies justified
- [ ] (H) No install-from-URL / git-HEAD / unpinned versions in production dependency lists
- [ ] (M) Hand-typed package names checked for typosquats
- [ ] (M) CI: third-party actions/plugins pinned to a hash, not a mutable tag

## 6. Unsafe deserialization & dynamic execution

- [ ] (C) No `pickle.loads`, `yaml.load` (non-Safe), `marshal`, Java native deserialization, `unserialize` on attacker-influenced data
- [ ] (C) No `eval`/`exec`/`Function()`/`vm.runInContext` on constructed strings containing external input
- [ ] (H) XML parsing hardened (XXE off — `defusedxml` or entity resolution disabled)
- [ ] (M) JSON schemas validated on ingest (type confusion at trust boundaries)

## 7. Input handling & uploads

- [ ] (H) File type validated by content (magic bytes), not extension or Content-Type header
- [ ] (H) Uploads stored outside the web root, with server-generated names, size-capped
- [ ] (M) All external input length/type/range-validated at the boundary (allowlist over blocklist)
- [ ] (M) Decompression bombs: size limits on archive/image/XML expansion
- [ ] (M) SSRF: user-supplied URLs fetched server-side are scheme/host-restricted; internal ranges (169.254.169.254, RFC1918) blocked

## 8. Transport, storage, errors

- [ ] (H) TLS everywhere external; certificate verification never disabled (`verify=False` is a finding, not a workaround)
- [ ] (M) Sensitive data at rest encrypted or justified; PII inventoried and minimized
- [ ] (M) Error responses don't leak stack traces, paths, versions, or SQL to clients (log detail server-side instead)
- [ ] (L) Security headers on web responses: `Content-Security-Policy`, `X-Content-Type-Options`, `Strict-Transport-Security`

## Reporting format

Per finding: `severity | file:line | attack in one sentence | fix direction`. Order by severity. Demonstrated-locally beats theoretical; **never test suspected vulnerabilities against production or third-party systems**. Leaked live credentials = incident: report immediately, recommend rotation first.
