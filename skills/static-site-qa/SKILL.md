---
name: static-site-qa
description: A pre-deploy QA pass for hand-rolled static sites (plain HTML/CSS/JS, no framework) — local serving, screenshots at mobile and desktop breakpoints, link checking, HTML validation, SEO/Lighthouse checks, sitemap consistency with the page structure, and post-deploy live-URL verification. Use before merging or deploying any change to a hand-maintained static website, especially visual or content changes.
license: MIT
metadata:
  version: "2.0.0"
---

# Static Site QA

Hand-rolled static sites usually have **zero automated verification** — no build to fail, no tests to run — so plausible-looking changes get merged on faith. The canonical failure mode: an agent ships a batch of "quick win" visual improvements, nobody rendered them, they look broken on mobile, and the whole merged PR gets **reverted**. A reverted PR costs more trust than ten slow-but-verified ones. This skill is the checklist that prevents it.

## 1. Serve and look — always

Never assess HTML/CSS changes from source. Serve and render:

```bash
python3 -m http.server 8000   # from the site root
```

Then screenshot every changed page headless, at minimum two breakpoints:

```bash
chromium --headless=new --disable-gpu --window-size=390,844 \
  --screenshot=mobile.png http://localhost:8000/changed-page/
chromium --headless=new --disable-gpu --window-size=1440,900 \
  --screenshot=desktop.png http://localhost:8000/changed-page/
```

Actually **look at the screenshots** (mobile first — that's where hand-rolled CSS breaks): clipped text, overlapping elements, fixed-position widgets covering tappable links, broken images, horizontal scroll. Mobile overlap bugs — a floating button covering a nav link — are invisible in source and obvious in a 390px screenshot. Attach the screenshots to your report as evidence.

## 2. Link and markup checks

- **Link check** every internal href and asset reference — a crawl from the local server (e.g. a recursive fetch script or any link-checker tool) asserting no 404s. Hand-edited nav and cross-page links rot constantly.
- **HTML validation** on changed pages (W3C validator via API, or a local validator). Hand-rolled HTML accumulates unclosed tags and duplicate IDs that render "fine" until they don't.
- Check for case-sensitivity mismatches in paths — many static hosts are case-sensitive; local filesystems often aren't.

## 3. SEO surface

Hand-rolled sites that care about SEO carry these; keep them consistent with every change:

- **`sitemap.xml`** — every page added/removed/renamed must be reflected. Stale sitemap entries are silent SEO damage.
- **`robots.txt`** — present, not accidentally disallowing everything.
- **Per-page metadata** — `<title>`, meta description, canonical URL, **Open Graph tags** (`og:title`, `og:image`, ...) so shared links unfurl, and **JSON-LD** structured data where the site uses it (validate the JSON parses).
- Run **Lighthouse** (SEO + accessibility + performance categories) on changed pages when available; treat new regressions versus the unchanged pages as blockers.

## 4. Directory-per-page consistency

Sites structured as one directory per page (`about/index.html`, `blog/<slug>/index.html`) encode their URL scheme in the filesystem. When adding a page:

- Follow the existing directory convention exactly — don't introduce `page.html` flat files into a directory-per-page site.
- Add the URL to `sitemap.xml` and to whatever nav/index pages list content (blog indexes, footers).
- Reuse the site's shared `styles.css`/`script.js` conventions instead of adding per-page copies.

Cross-check: every directory containing an `index.html` should appear in the sitemap, and every sitemap URL should resolve locally. This pairwise check catches both halves of the drift.

## 5. Post-deploy verification

The deploy pipeline reporting success is not the finish line:

1. Wait for the deploy to reach its terminal "ready"/published state (poll if the platform supports it).
2. **Fetch the live URL** of each changed page — assert 200 and the presence of a string unique to the new content (proves cache/CDN actually serves the new version).
3. Spot-check one screenshot of the live page if the change was visual.

Only then report the change as shipped.

## Pre-merge checklist

- [ ] Served locally; screenshots taken at mobile + desktop breakpoints and inspected
- [ ] Link check clean; HTML validated on changed pages
- [ ] sitemap.xml, robots.txt, og/meta/JSON-LD consistent with the change
- [ ] Directory-per-page convention followed; sitemap ↔ pages cross-check passes
- [ ] Lighthouse run where available; no new regressions
- [ ] After deploy: live URL fetched and confirmed serving the new content
