---
name: api-integration
description: Patterns for integrating with third-party APIs reliably and safely. Covers reading docs and OpenAPI specs before the first call, authentication handling without leaking secrets, pagination and rate-limit discipline, idempotency for write operations, a retryable-versus-not error taxonomy, testing against sandboxes before production, and webhook basics. Use when a task requires calling, integrating, or building against an external HTTP API — especially one with authentication or write operations.
license: MIT
metadata:
  version: "1.1.0"
---

# API Integration

API integrations fail expensively: a retried non-idempotent POST double-charges a customer; a logged token leaks; an unpaginated GET silently analyzes 100 of 12,000 records. The write side and the auth side deserve the most care.

## 1. Read before you call

- Find the **official docs and the OpenAPI/Swagger spec** (`/openapi.json`, `/swagger.json`, a "Developers" page) before the first request. Ten minutes of reading beats two hours of probing.
- Extract these specifics into your notes: auth scheme, base URL per environment, **rate limits**, pagination style, error format, versioning scheme (URL vs header), and whether a **sandbox** exists.
- Check the version/changelog. Copy-pasted examples from blog posts routinely target deprecated versions.
- No docs? Probe the *read-only* endpoints first, capture real responses as fixtures, and treat every inferred behavior as an assumption to state in your report. Never probe write endpoints to "see what happens."

## 2. Auth — and never logging it

- Common schemes, in rough order of frequency: API key in a header (`Authorization: Bearer …` or `X-API-Key`), OAuth 2.0 (client-credentials for machine-to-machine; authorization-code for user data), HMAC-signed requests (AWS-style), basic auth. Match the docs exactly — a key sent in the wrong header yields misleading 401/403s.
- Secrets come from **environment variables or a secrets manager**, never from source code, and never hardcoded "temporarily." Fail fast with a clear message if the env var is unset.
- **Never log a credential.** The leak paths are rarely `print(api_key)` — they're logging the full request headers, logging the URL when the key is a query param, echoing the failing `curl` command into a report, and committing a `.env` file. Redact before logging: `key[:4] + "…"` is enough to identify which key without exposing it.
- OAuth tokens expire: handle refresh on 401 (once — a second 401 after refresh is a real auth failure, not a retry candidate).
- Request the **minimum scopes** the task needs.

## 3. Pagination and rate limits

- Assume every list endpoint paginates, even when your test query fits in one page. Identify the style — cursor (`next_cursor`/`next` URL: follow it exactly), offset (`?offset=&limit=`), or page number — and **loop until the terminator** (empty page, absent cursor), with a hard page cap against infinite loops.
- Verify totals when the API states them: your item count must match the reported `total` (± known duplicates). Log per-page counts; silent truncation is the most common integration bug.
- Respect rate limits *before* hitting them: read the limit from docs or `X-RateLimit-Remaining` headers, and pace requests (sleep when remaining is low). On **429**, honor `Retry-After` exactly if present; otherwise exponential backoff with jitter (1s, 2s, 4s…, cap ~60s).
- Bulk endpoints beat loops: one `?ids=1,2,3` call replaces 100 GETs. Look for them.

## 4. Writes and idempotency

Writes are where retries turn dangerous:

- **Before any retry of a write, answer: "what happens if the original actually succeeded?"** A timeout does not mean the operation failed — the response was lost, not necessarily the write.
- Use **idempotency keys** when the API supports them (Stripe-style `Idempotency-Key` header): generate one UUID per logical operation, reuse it on retries. This makes retrying timeouts safe.
- No idempotency support? Then on ambiguous failure (timeout, 5xx after a write), **check-then-retry**: query whether the resource was created before re-sending. Never blind-retry a POST.
- Prefer naturally idempotent verbs where the API offers a choice (PUT with a client-chosen ID over POST).
- Log every write with its request ID/response ID — your audit trail when reconciliation is needed.

## 5. Error taxonomy: retry or don't

Classify before handling — full table with per-code guidance in [references/error-taxonomy.md](references/error-taxonomy.md):

| Class | Examples | Action |
|---|---|---|
| Transient | 429, 408, 500, 502, 503, 504, timeouts, connection reset | Retry with backoff + jitter (writes: only with idempotency, §4) |
| Your request is wrong | 400, 404, 405, 409, 422 | **Never retry unchanged.** Fix the request; the error body usually says what's wrong — read it |
| Your auth is wrong | 401, 403 | Refresh token once (401); otherwise stop and report — retrying can lock the account |
| Contract broken | Parse failures, missing fields, schema drift | Stop; capture the actual response as evidence; report |

- Parse the **error body**, not just the status code — good APIs return machine-readable detail (`{"error": {"code": "…", "message": "…"}}`) that names the exact problem.
- Cap total retries (3–5) and total elapsed time. Log every retry with attempt number and cause.

## 6. Sandbox before production

- If the API has a sandbox/test mode (test keys, staging base URL), **all development happens there**; production keys enter only for the final verified run. Test keys and live keys are often distinguishable by prefix (`sk_test_` vs `sk_live_`) — check which you're holding before any write.
- No sandbox? Mock it: record real read-endpoint responses as fixtures and test your pipeline against them. For destructive operations with no sandbox, do one minimal canary operation, verify it end-to-end, then proceed.
- Dry-run flags (`?dry_run=true`, `--validate-only`) exist on many write APIs — look for them.

## 7. Webhooks (receiving)

- **Verify signatures** (`X-*-Signature` HMAC headers) before trusting any payload — an unverified webhook endpoint is an open door for forged events.
- Respond 2xx fast, process async; slow handlers cause the sender to retry, creating duplicates.
- Handle **duplicate delivery** (at-least-once is the norm): dedupe on the event ID.
- Don't trust webhook payload contents for money-relevant state — treat the event as a hint and re-fetch the resource from the API.

## Pre-integration checklist

- [ ] Docs/spec read; auth, rate limits, pagination style, sandbox noted
- [ ] Secrets via env vars; nothing secret in code, logs, or reports
- [ ] Pagination loops to the terminator; totals verified where stated
- [ ] Retry policy matches the taxonomy; writes idempotent or check-then-retry
- [ ] Developed against sandbox/mocks; live keys only for the verified final run
- [ ] Every failure path captures the response body as evidence
