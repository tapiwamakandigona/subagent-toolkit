---
name: static-export-webapp
description: Working patterns for Next.js (and similar framework) products built as static exports — what output export forbids, the public env-var matrix, the full verification chain from lint through serving the exported output, reading bundled framework docs when the version postdates your training data, mandatory security review for payments and auth code, and the Capacitor APK packaging variant. Use when building or modifying a framework app whose deploy artifact is a static out/ or dist/ directory.
license: MIT
metadata:
  version: "2.0.0"
---

# Static-Export Web App Development

A static-export app looks like a normal framework app but ships as plain files — no server at runtime. Every server-dependent feature you add compiles fine in dev and then breaks the export or the deployed site. The discipline: know what the export forbids, verify the exported artifact (not the dev server), and treat money/auth code as review-gated.

## 1. What static export forbids

With Next.js `output: 'export'` (and equivalents elsewhere), these do not exist at runtime:

- Server-rendered-per-request pages, server actions, and API route handlers that need a server (routes must be statically renderable).
- Middleware, on-demand ISR/revalidation, cookies/headers read at request time.
- Dynamic routes without a full `generateStaticParams` enumeration.
- The framework image optimizer (needs `images.unoptimized` or a custom loader).

Anything server-side goes to an external backend (serverless functions, a BaaS). If a task seems to require adding a route handler, that's a signal to put the logic in the backend platform instead — **do not remove `output: 'export'` to make a feature fit**; that's an architecture change requiring explicit approval.

## 2. The environment variable matrix

- Only `NEXT_PUBLIC_*`-prefixed vars reach the client bundle, and they are **baked in at build time** — changing them requires a rebuild, not a redeploy.
- CI supplies them from repository variables/secrets; local builds need them in `.env.local`. Keep a committed `.env.example` listing every required **name** (never values).
- A missing public var usually doesn't fail the build — it produces a site that misbehaves at runtime (undefined endpoints, broken auth). Add an explicit build-time assertion or a smoke test that catches it.
- Public vars are visible to every site visitor: only non-secret identifiers (project IDs, endpoints) belong there. A secret in a `NEXT_PUBLIC_*` var is a leak.

## 3. The framework may be newer than you

Framework majors ship faster than model training cycles. **Before writing any code, check the installed version and read the docs bundled in the repo** — e.g. `node_modules/next/dist/docs/` or the package's own `docs/`/README — rather than trusting your memory of the API. Repos that know this often say so in their agent doc (`AGENTS.md` etc.); obey it. Symptoms of ignoring this rule: deprecated config keys, removed APIs, and "worked in my head" code that fails lint or build immediately.

## 4. The verification chain

Run in order; each stage gates the next. The dev server proves nothing about the export.

```
1. npm run lint                # or the repo's lint script
2. npx vitest run              # unit tests — including PARITY TESTS:
                               # money/fee/order logic implemented on both
                               # frontend and backend must share test vectors
                               # asserting identical results; a drift here is
                               # a real-money bug
3. npm run build               # MUST succeed AND produce out/ (or dist/) —
                               # an export error here is a §1 violation
4. npx serve out/              # serve the actual artifact (any static server)
5. Headless-smoke key routes   # load each critical route in headless
                               # Chromium: zero console errors, key content
                               # present; screenshot for evidence
```

Report which stages ran and their results. "Build passed" without stage 5 means the deployed site was never actually exercised.

## 5. Security review is mandatory for payments/auth code

Any change touching payment vending, order state, balances, or authentication gets an independent **security-review pass before merge** (load the security-review skill; in a multi-agent setup, a separate reviewer role). Classic findings in this class of app: trusting the wrong hop of `X-Forwarded-For`, missing locks around reconciliation paths, unbounded currency/amount inputs, client-computed prices trusted by the backend. Frontend/backend parity tests (§4) are the regression net for review findings — extend them with every fix.

## 6. Capacitor APK variant

When the product also ships as an Android app wrapping the static export:

```
1. Build the static export (out/ is the webDir in capacitor.config).
2. npx cap sync android           # copies web assets + plugin config
3. npx @capacitor/assets generate # icons + splash from source images
4. Patch AndroidManifest.xml      # deep-link scheme for OAuth callbacks —
                                  # regeneration (cap add android) LOSES
                                  # manual edits, so pipelines patch the
                                  # manifest via script after sync; keep
                                  # that step or sign-in breaks on device
5. Sign: keystore from CI secrets (base64-decoded at build time), never
   committed. Debug builds for artifacts/testing, signed for release.
6. Per-ABI splits for release APK size; plus one universal APK for
   sideload/beta distribution.
```

The CI APK build doubles as the verification that the export + native wrapper still compose — treat a red APK job as a product break even if the web build is green.

## Pre-handoff checklist

- [ ] Installed framework version checked; bundled docs consulted for any API used
- [ ] No feature added that violates static export; `output: 'export'` untouched
- [ ] Full chain run: lint → tests (parity included) → build produces `out/` → served → headless smoke
- [ ] Env-var names documented; no secret in any public var
- [ ] Payments/auth changes flagged for security review before merge
- [ ] If Capacitor: manifest patch step preserved, keystore never committed
