---
name: data-analysis
description: Methodology for loading, cleaning, and analyzing tabular data (CSV, JSON, SQL, spreadsheets) without fooling yourself. Covers sanity-checking data before analysis, writing reproducible analysis scripts instead of ad-hoc REPL math, honest aggregation (denominators, baselines, Simpson's paradox), and choosing charts versus tables for the result. Use when a task involves computing numbers, statistics, or trends from a dataset — especially data you did not produce yourself.
license: MIT
metadata:
  version: "2.0.0"
---

# Data Analysis

The characteristic analysis failure isn't a wrong formula — it's a correct computation on data you never checked, aggregated in a way that hides the real story. Every rule here exists to keep the numbers honest.

## 1. Sanity-check the data before any analysis

Never compute a single statistic before profiling. Minimum first pass (run the full checklist in [references/validation-checklist.md](references/validation-checklist.md) for anything that matters):

- **Row count** vs. expectation — stated total, historical size, or a back-of-envelope estimate. Off by >10%? Stop and find out why before proceeding.
- **Null rate per column.** A field that's 2% null is normal; 60% null means the column is unusable or the load broke. Decide per-column: drop rows, impute (and say so), or exclude the column.
- **Dtypes:** numbers loaded as strings (`"1,234"`, `"$5.00"`, `"N/A"`), dates loaded as text, booleans as `"yes"/"no"`. Silent string-typed numbers are the #1 cause of wrong aggregates — `sum()` on strings concatenates or errors, and `mean()` on a partially-numeric column silently drops rows in some tools.
- **Duplicates** on the natural key (ID, URL, email). Duplicated rows inflate every count downstream.
- **Range sanity:** min/max of every numeric column, date range of every date column. Negative ages, prices of 0, timestamps from 1970 — find them now.
- **Eyeball 10 random rows** (random, not head — the top of a file is often atypical: headers, test data, oldest records).

## 2. Reproducible scripts, not REPL archaeology

- Every number in your deliverable must come from **a script in a file** that runs end-to-end from the raw data. Ad-hoc REPL math produces numbers nobody (including you, 20 minutes later) can reproduce or audit.
- The script's pipeline: `load → validate (assert the §1 checks) → clean → derive → aggregate → output`. Put `assert` statements on the load-time invariants (row count bounds, required columns present) so a changed input fails loudly instead of producing subtly wrong output.
- **Never modify the raw data file.** Cleaning happens in code; the raw file is evidence.
- Log what cleaning removed: "dropped 47 rows (3.1%) with null price" belongs in the script output and the report. Silent row-dropping is fabrication's quiet cousin.
- Record provenance with any output dataset: source, extraction date, script version/path.

## 3. Honest aggregation

The math is easy; the traps are semantic:

- **Every rate/percentage gets its denominator stated.** "Conversion rose to 12%" — of visitors? of signups? of a segment? Ambiguous denominators are how analyses mislead without lying.
- **Every comparison gets a baseline.** "40% faster" than what, measured when, under what conditions?
- **Simpson's paradox check:** before reporting any aggregate comparison between groups, break it down by the 1–2 most plausible confounders (time period, segment, size class). If the per-group direction contradicts the aggregate direction, report the breakdown — the aggregate alone is misleading.
- **Means hide; distributions tell.** For anything skewed (latency, revenue, counts) report median + p90/p95 or the mean *with* the max. A mean moved by three outliers is not a trend.
- Small-n humility: percentages on n<30 get the raw counts alongside ("3 of 7", not "43%").
- Correlation language stays correlational. You may write "associated with"; you may not write "caused" unless you have a controlled comparison.
- Cross-foot the output: do the segment rows sum to the total? Do percentages sum to ~100%? Internal inconsistency is the cheapest error to catch and the most embarrassing to ship.

## 4. Chart vs. table vs. sentence

- **Sentence:** ≤3 numbers. "Revenue rose 12% QoQ to $1.4M" needs no visual.
- **Table:** the reader compares items or looks up their own row. Exact values matter.
- **Chart:** the *shape* is the finding — trend, distribution, outlier, seasonality. If you can't say what shape the chart shows in one sentence, it's decoration; use a table.
- Chart discipline: label axes with units, start bar-chart y-axes at zero, one message per chart, and put the takeaway in the title ("Churn concentrated in month 1", not "Churn by month").

## 5. Before reporting numbers

- Recompute the headline figure a second way (different grouping, a quick independent script, or a hand calculation on a sample). Two paths to the same number is verification; one path is hope.
- Re-read the original question. The most common analysis failure is precisely answering a question nobody asked.
- State limitations in the deliverable: rows excluded, columns imputed, time window, known biases in collection. A flagged caveat builds trust; a discovered one destroys it.

## Pre-submit checklist

- [ ] §1 profile run on the raw data; anomalies resolved or disclosed
- [ ] Every number traceable to a runnable script; raw data untouched
- [ ] Every rate has a denominator; every comparison a baseline
- [ ] Aggregate comparisons checked against at least one group breakdown
- [ ] Headline figure independently recomputed
- [ ] Exclusions, imputations, and caveats disclosed
