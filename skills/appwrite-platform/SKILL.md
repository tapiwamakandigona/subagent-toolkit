---
name: appwrite-platform
description: Agent-oriented patterns for building on Appwrite — Sites deployments via the REST API with status polling, Functions development and isolated testing, OAuth deep-link callback schemes on mobile, and the secret-hygiene line between public project identifiers and private API keys. Use when a task deploys to Appwrite Sites, writes or modifies Appwrite Functions, wires up Appwrite Auth, or touches a repo whose CI or scripts call the Appwrite API.
license: MIT
metadata:
  version: "2.0.0"
---

# Appwrite Platform Work

Appwrite commonly serves as the whole backend for static-first products: Sites for hosting, Functions for server logic, Auth for login, Databases for state. Agents break these setups in predictable ways — treating a POST-accepted deployment as a finished deploy, leaking API keys into logs, and "fixing" deploy scripts that were deliberately shaped that way. This skill covers the working patterns.

## 1. Sites deployment: tar → POST → poll → fetch

The reliable deploy shape for a static site, whether in CI or a local script:

```
1. Tar the site, EXCLUDING what must never ship:
   tar czf site.tar.gz --exclude .git --exclude .github \
       --exclude '.deploy_key*' --exclude '*.env*' --exclude deploy.py .
2. POST to the deployments endpoint:
   curl -s -X POST "$ENDPOINT/v1/sites/$SITE_ID/deployments" \
     -H "X-Appwrite-Project: $PROJECT_ID" \
     -H "X-Appwrite-Key: $APPWRITE_API_KEY" \
     -F "code=@site.tar.gz" -F "activate=true"
3. POLL the returned deployment ID until status is "ready"
   (sleep 5–10s between polls, hard timeout ~5 min; "failed" → fetch and
   report the build logs). The POST returning 2xx means "accepted", not
   "deployed" — THE POLL IS THE DEPLOY VERIFICATION. A script that fires
   the POST and exits green has verified nothing.
4. Fetch the live URL afterward and check for a 200 and expected content.
   Only then report the deploy as done.
```

Never echo the curl command with the real key into logs or reports (see §4).

## 2. Respect the repo's existing deploy style

Two legitimate styles coexist, and converting between them is a product decision, not a fix:

- **CI-based**: a workflow deploys on push, key held in CI secrets.
- **Local-script-based**: a gitignored key file (e.g. `.deploy_key`) read by a deploy script, run by a human or agent with filesystem access. Repos sometimes **deliberately removed** their CI deploy in favor of this — check the history/agent docs before "restoring" a CI workflow.

If the repo uses a local key file and you don't have it, you **cannot deploy** — say so in your report rather than inventing a new pipeline.

## 3. Functions

- Server logic lives in Functions (typically `node-appwrite` runtime), not in a long-running server. Each function is a small self-contained package under something like `functions/<name>/`.
- **Test Functions in isolation** before deploying: invoke the handler locally with a stubbed request/response context and fixture payloads. Function code paths that touch money or external payment providers additionally need a reviewer/security pass (see the security-review skill).
- A Function's environment variables are configured server-side; document required names in the repo (`.env.example` style, names only, never values).

## 4. Secret hygiene: identifiers vs. keys

Get this line exactly right:

| Value | Class | May appear in code/CI/logs? |
|---|---|---|
| Endpoint URL (`https://<region>.cloud.appwrite.io/v1`) | Public identifier | Yes |
| Project ID, Site ID, Function ID, Database/Collection IDs | Public identifier | Yes |
| `X-Appwrite-Key` API key values | **Secret** | **Never** |
| OAuth client secrets, signing keystores | **Secret** | **Never** |

- Project IDs appearing in committed configs are **not** a security finding — don't file them as leaks, and don't "fix" them into secrets.
- API keys come from CI secrets or a gitignored local file. The leak paths to guard: logging full request headers, echoing the deploy `curl` into a report, committing the key file because a tar/exclude rule missed it.
- If you must reference which key was used, identify it by scope/name, never by value or prefix beyond a few characters.

## 5. OAuth deep-link callbacks on mobile

OAuth on a wrapped mobile app (Capacitor and similar) returns via a **custom URL scheme** (e.g. `myapp://auth-callback`), which must be registered in `AndroidManifest.xml` (intent filter) and the iOS equivalent.

The trap: build pipelines that **regenerate** the native project (`npx cap add android`, re-scaffolds) wipe manual manifest edits, so working setups often re-inject the intent filter with a patch script in CI **after** regeneration. Consequences:

- Never assume the manifest in the repo is the manifest that ships — read the CI workflow for patch steps.
- If you regenerate the native project locally, re-run the patch step or re-apply the scheme, or sign-in silently breaks (the OAuth round-trip completes but the app never receives the callback).
- The callback scheme string must match exactly across the OAuth provider config, the Appwrite platform settings, and the manifest — a mismatch fails only at runtime, on device.

## Pre-handoff checklist

- [ ] Deploy verified by **polling to `ready`** and fetching the live URL — not by the POST succeeding
- [ ] Tar excluded `.git`, CI config, key files, env files
- [ ] No API key value in any log, report, or committed file; IDs not misreported as secrets
- [ ] Functions tested in isolation with fixtures before deploy
- [ ] Existing deploy style (CI vs local key file) respected; inability to deploy reported, not worked around
- [ ] Mobile OAuth: manifest patch step accounted for after any native-project regeneration
