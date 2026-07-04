---
name: buildless-web-verify
description: Verification patterns for browser apps and games that deliberately ship with no build step — plain ES modules, import maps, vendored libraries, static hosting. Covers the local-server + headless-Chromium smoke-test harness (console-error capture, renderer init checks, driving the app via exposed window globals, screenshots, JSON verdicts), the "never introduce a build step" pre-handoff check, GitHub Pages verbatim-upload gotchas, and honest labeling of performance claims. Use when modifying or verifying any repo that runs directly from source in the browser.
license: MIT
metadata:
  version: "2.0.0"
---

# Buildless Web App Verification

Buildless repos are a deliberate architecture, not a missing feature: the deploy pipeline uploads the working tree **verbatim** to static hosting, so what runs locally under a dumb file server is exactly what ships. The two ways agents break these repos are (1) introducing a build step or external dependency that the pipeline can't process, and (2) shipping changes that were never actually loaded in a browser. This skill prevents both.

## 1. Recognize the constraint before editing

Signals that a repo is intentionally buildless:

- No `package.json`, or one that exists only for dev tooling — no `build` script.
- An **import map** in `index.html` mapping bare specifiers to local `vendor/` paths.
- Libraries, addons, and fonts **vendored** into the repo instead of installed or CDN-loaded.
- A deploy workflow that uploads the repo root as-is (no build job before the upload step).
- An agent-facing doc (`AI_CONTEXT.md`, `AGENTS.md`, etc.) stating "no build step" — this outranks a README that may claim CDN loading or anything else stale.

Once recognized, record "no build step" as a hard constraint in your task notes and re-check it before handoff (§4).

## 2. The headless smoke-test harness

The verification shape that works: a small Python (or Node) script that serves the repo, loads it in headless Chromium, and emits a machine-readable verdict.

```
1. Serve:      python3 -m http.server <port> from the repo root (background).
2. Load:       headless Chromium with software GL flags:
               --headless=new --disable-gpu --use-gl=swiftshader
               (WebGL apps need software rendering headless; a black canvas
               with no console error usually means GPU init failed silently)
3. Capture:    subscribe to console messages and pageerror events from load.
4. Assert:     zero console errors; renderer/app object initialized
               (e.g. canvas has nonzero size, main loop ticked at least once).
5. Drive:      call exposed window globals (window.__app / window.__game)
               to simulate interaction — pointer lock, gamepads, and real
               keyboard focus DO NOT work headless. The app must expose
               test hooks; add them if missing (guarded, cheap, shippable).
6. Screenshot: capture at least one frame after interaction for visual
               regression evidence; save alongside the verdict.
7. Verdict:    print a JSON object ({"pass": bool, "errors": [...],
               "checks": {...}}) and exit 0/1 so CI and orchestrators can
               consume it without parsing prose.
```

Keep the harness **in the repo** (a `tools/` directory), self-contained, and runnable with one command. One harness per concern (smoke, combat/interaction, visual, metadata) beats one mega-script.

What the harness cannot prove — say so explicitly in your report:

- **Real input feel** (pointer lock, WASD, touch) — flag "manual play-test needed."
- **Performance targets** ("60fps on low-end phones") — these require CPU/GPU-throttled traces on representative hardware. Without them, label every performance claim **unverified**. Never report a perf improvement based on code inspection alone.

## 3. GitHub Pages verbatim-upload gotchas

When the deploy is "upload repo root to Pages," these break silently:

- **`.nojekyll`** must exist at the root, or Jekyll processing eats directories starting with `_` and can mangle the site. Never delete it.
- **Import-map paths must stay relative** (`./vendor/...`). Absolute paths break under the `/repo-name/` subpath Pages serves project sites from.
- **Service-worker cache versioning**: if the repo has a `sw.js`, bump its cache version string on every release, or returning users get the old build indefinitely. A stale SW is the classic "works for me, broken for users" report.
- Case-sensitive paths: Pages is case-sensitive; local filesystems often aren't. The headless harness catches this because it serves over HTTP.

## 4. Pre-handoff check: did I introduce a build step?

Run this checklist before every handoff on a buildless repo:

- [ ] No new `package.json`, `vite.config.*`, `webpack.config.*`, `tsconfig.json` (for compiled TS), or any file implying compilation.
- [ ] No new `import` of a bare specifier that isn't in the import map, and no new CDN `<script src>` — grep your diff for `https://` in script/link tags and for bare imports.
- [ ] Any new library is **vendored** (copied into `vendor/` with its license) and added to the import map with a relative path.
- [ ] The smoke harness passes from a clean serve (`python3 -m http.server` + harness, exit 0).
- [ ] `.nojekyll` still present; `sw.js` cache version bumped if release-worthy.
- [ ] Perf claims in your report are backed by traces or labeled unverified.

## 5. Operating loop for these repos

These repos usually carry a roadmap and an agent doc. The loop that keeps them healthy: pick **one** increment → implement → run every harness in `tools/` → update the changelog/roadmap/agent doc → deploy → verify the live URL loads. Never stack unverified increments, and never break the deployed default branch — the working tree *is* the artifact.
