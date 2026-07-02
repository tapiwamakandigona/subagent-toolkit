# API Error Taxonomy — Per-Code Handling Guide

Reference table for classifying HTTP API failures. The governing question for every retry decision on a write: *"what happens if the original actually succeeded?"*

## Status-code table

| Code | Meaning | Retry? | Notes |
|---|---|---|---|
| 400 | Bad request | **No** | Your request is malformed. Read the error body; fix; then it's a new request, not a retry |
| 401 | Unauthenticated | Once, after refresh | Refresh/re-fetch the token once. A second 401 = real credential problem; stop (repeated attempts can trigger lockouts) |
| 402 | Payment required | No | Account/billing state; escalate to the account owner |
| 403 | Forbidden | **No** | Authenticated but not allowed: missing scope, IP allowlist, plan limit. Retrying never helps; some WAFs also use 403 for bot-blocking — check the body |
| 404 | Not found | No* | Wrong URL/ID or deleted resource. *Exception: immediately after creating the resource, some systems are eventually consistent — one delayed re-check is reasonable |
| 405 | Method not allowed | No | Wrong verb; re-read the docs |
| 408 | Request timeout | Yes | Server-side timeout; retry with backoff. For writes, idempotency rules apply |
| 409 | Conflict | Depends | Version conflict / duplicate. Don't blind-retry: re-fetch current state, reconcile, then decide. A 409 on create with an idempotency key often means "already done" — that's success |
| 410 | Gone | No | Permanently removed; also used for deprecated API versions |
| 412 / 428 | Precondition failed/required | Depends | ETag/If-Match optimistic concurrency: re-fetch, re-apply your change, resend with the new ETag |
| 413 | Payload too large | No | Chunk/batch the request smaller |
| 415 | Unsupported media type | No | Wrong `Content-Type` header (JSON sent as form-encoded is the classic) |
| 422 | Unprocessable entity | **No** | Validation failure; the body almost always lists field-level errors — parse and fix |
| 429 | Rate limited | **Yes** | Honor `Retry-After` exactly if present; else backoff + jitter. Also *slow down proactively* — repeated 429s escalate to bans on some providers |
| 500 | Internal server error | Yes (reads) | Backoff + jitter, 3–5 attempts. Writes: only with idempotency key or check-then-retry |
| 501 | Not implemented | No | Endpoint doesn't exist on this version/deployment |
| 502 / 503 / 504 | Bad gateway / unavailable / gateway timeout | Yes | Infrastructure-level transients; same write caveat. 503 may carry `Retry-After` — honor it |

## Transport-level failures (no status code)

| Failure | Retry? | Notes |
|---|---|---|
| DNS resolution failure | Once, then stop | Usually config (wrong base URL) or environment, not transient |
| Connection refused | Briefly | Service down or wrong port; a couple of backoff attempts, then report |
| Connection reset / broken pipe | Yes | Transient network; standard backoff |
| TLS certificate error | **No** | Never bypass verification to "make it work." Wrong base URL, expired cert, or interception — report it |
| Read timeout | Yes, carefully | **The request may have succeeded.** For writes this is the canonical ambiguous failure: idempotency key or check-then-retry, never blind resend |

## Application-level failures (2xx that still failed)

Some APIs return `200 OK` with an error in the body (`{"ok": false, "error": "…"}`, GraphQL's `errors` array, batch endpoints with per-item statuses). Always check the body's own success indicator, not just the HTTP status. Classify the body error using the same logic: transient (server hiccup) vs. request-wrong (validation) vs. auth.

## Contract-drift failures

The call "succeeds" but the response doesn't match your expectations:

- Missing/renamed fields, changed types, changed enum values → **stop, don't coerce**. Capture the actual response verbatim as evidence, diff against the documented schema, and report. Silently adapting to drifted schemas produces corrupt data downstream.
- Empty results where data is expected → distinguish "truly empty" from "wrong filter/permissions/environment" (test keys pointed at an empty sandbox is a classic). Verify with a query you know has results.

## Backoff recipe

```
delay = min(cap, base * 2^attempt) + random(0, jitter)
# e.g. base=1s, cap=60s, jitter=1s, max_attempts=5
```

- Honor `Retry-After` (seconds, or an HTTP-date — handle both) in preference to computed backoff.
- Budget total elapsed time, not just attempt count, so a slow-failing endpoint can't consume the whole task.
- Log each retry: attempt number, cause, delay. Retries that happen silently hide systemic problems.
