---
name: web-data-extraction
description: Patterns for fetching and extracting data from websites reliably and politely. Covers fetch-to-markdown pipelines, pagination strategies, rate limiting and robots etiquette, structured extraction into schemas, and validating scraped data before use. Use when a task requires collecting data from web pages, APIs, or feeds at more than trivial scale.
license: MIT
metadata:
  version: "1.1.0"
---

# Web Data Extraction

Scraping fails quietly: pages change, selectors miss, pagination truncates, and you end up analyzing 40% of the data while believing you have 100%. Every pattern here exists to make failure *loud*.

## 1. Before scraping: look for the front door

In order of preference:

1. **Official API** — check for `/api/`, developer docs, or an OpenAPI spec.
2. **Structured feeds** — RSS/Atom, sitemaps (`/sitemap.xml`), JSON-LD / OpenGraph metadata embedded in pages (often the cleanest data on the page).
3. **Hidden JSON** — many "HTML" sites load data via XHR; inspect network calls or look for `<script type="application/json">` / `__NEXT_DATA__` blobs. Parsing that JSON beats parsing rendered HTML every time.
4. HTML scraping — last resort.

Check `robots.txt` and the site's terms; respect disallow rules and never scrape auth-walled or personal data.

## 2. Fetch → markdown pipeline

For content pages (articles, docs, listings), the robust pipeline is:

```
fetch HTML → strip boilerplate (nav/footer/ads) → convert to markdown → extract from markdown
```

Markdown conversion normalizes away most markup churn and makes content LLM-friendly. See [scripts/fetch_page.py](scripts/fetch_page.py) for a starting-point fetcher with retries, timeouts, caching, robots.txt checking, and backoff — adapt it to the target site rather than treating it as complete.

Fetching rules:

- Set a **descriptive User-Agent**, a timeout (10–30s), and retries with exponential backoff + jitter (e.g. 1s, 2s, 4s) on 429/5xx/timeouts only. Never retry 4xx other than 429/408.
- **Cache raw responses to disk** keyed by URL before any parsing. Re-running extraction must not mean re-fetching. This also preserves evidence of what you actually saw.
- Detect soft failures: HTTP 200 pages that are actually error/consent/captcha pages. Check for expected content markers, not just status codes.
- JavaScript-rendered pages: static fetch returns an empty shell — detect this (tiny body, no target content) and switch to a real browser tool rather than parsing the shell.

## 3. Pagination

- Identify the mechanism: `?page=N`, `?offset=`, cursor tokens, "load more" XHR, or `rel="next"` links. Prefer the underlying API/XHR endpoint over clicking through rendered pages.
- **Always verify totals:** if the site states "1,240 results", your extracted count must match (±duplicates). If no total is stated, page until an empty page *and* confirm the last page overlaps nothing.
- Guard against infinite loops: hard cap on pages, and stop if a page's content hash repeats.
- Record per-page counts in a log — silent mid-pagination truncation is the most common cause of incomplete datasets.

## 4. Rate limiting & politeness

- Default: **≤1 request/second per host**, sequential, unless the site's API docs allow more.
- Honor `Retry-After` headers on 429 exactly.
- Batch runs at scale: add jitter, run during off-peak if scheduled, and back off aggressively at the first 429 — getting IP-banned mid-task destroys the whole dataset.
- Fetch each URL once (that's what the cache is for).

## 5. Structured extraction

- Define the target schema **before** extracting: field names, types, required vs. optional, e.g.

  ```json
  {"title": "str", "price": "float|null", "currency": "str", "posted_at": "ISO date", "url": "str"}
  ```

- Prefer stable anchors over brittle ones: semantic attributes (`data-*`, `itemprop`, aria labels) > element ids > class names > positional selectors (`div:nth-child(3)` breaks first).
- When using an LLM for extraction, pass the markdown + the schema and require JSON output with `null` for missing fields — never let it guess values.
- Extraction code must **fail loudly per-field**: a missing field yields `null` + a logged warning, not a skipped record or a fabricated default.

## 6. Validate before you use it

Scraped data is guilty until proven innocent. Minimum validation pass:

| Check | Example |
|---|---|
| Row count vs. expectation | matches stated total / historical size ±10% |
| Null rate per field | price null in 2% is fine; 60% means the selector broke |
| Type & range sanity | prices > 0, dates within plausible window, URLs resolve |
| Duplicates | key-field uniqueness (URL, ID) |
| Spot check | manually open 3–5 source pages and compare against extracted rows |

The spot check is non-negotiable — it's the only step that catches "selector matched the wrong element everywhere, consistently."

Record provenance with the dataset: fetch date, source URLs, extractor version. Data without provenance can't be trusted or reproduced later.
