# Data Validation Checklist

Run this before analysis on any dataset you didn't generate yourself in this session. Record the answers — they belong in your working notes and (summarized) in the final report's caveats section.

## A. Structural

| # | Check | How | Red flag |
|---|---|---|---|
| 1 | Row count | `len(df)` / `wc -l` / `SELECT COUNT(*)` | Differs >10% from stated total or expectation |
| 2 | Column count & names | compare against schema/docs | Missing expected columns; unnamed columns (`Unnamed: 3` is a pandas parse-failure tell) |
| 3 | Encoding & delimiter | open the raw file head in a text editor/`head -c 2000` | Mojibake (`Ã©`), whole rows in one column (wrong delimiter), BOM characters |
| 4 | Header row | first data row vs. column names | Data in the header, or headers repeated mid-file (concatenated exports) |
| 5 | Duplicates | count distinct on the natural key | Any duplicate on a supposedly-unique key |

## B. Per-column

| # | Check | How | Red flag |
|---|---|---|---|
| 6 | Dtype | `df.dtypes` / inspect | Numeric column typed as object/string; dates as strings |
| 7 | Null rate | `df.isna().mean()` | >5% on a required field; also check *disguised* nulls: `""`, `"N/A"`, `"null"`, `"-"`, `0` or `-1` used as sentinel, `1970-01-01` |
| 8 | Numeric range | min / max / negative count | Impossible values: negative quantities, 0 prices, percentages >100 |
| 9 | Date range | min / max | Dates in the future, before the system existed, or clustered on one day (batch-import artifact) |
| 10 | Categorical cardinality | `value_counts()` on category-like columns | Near-duplicate categories (`"NY"` vs `"New York"` vs `"new york "` — trailing whitespace and case) |
| 11 | Units consistency | inspect a sample + docs | Mixed units in one column (cents and dollars; seconds and ms) — often visible as a bimodal distribution ~1000× apart |

## C. Cross-column & semantic

| # | Check | How | Red flag |
|---|---|---|---|
| 12 | Internal consistency | derived fields vs. components | `total ≠ price × qty`; `end_date < start_date`; percentages that don't sum to ~100 |
| 13 | Referential integrity | joins to related tables | Foreign keys with no match (orphaned rows silently dropped by inner joins) |
| 14 | Time coverage | rows per day/week plotted or tabulated | Gaps or spikes — a missing week skews any trend computed over it |
| 15 | Random-sample eyeball | 10 random rows read fully | Anything that surprises you. Trust the surprise; investigate it |

## D. Join hygiene (when combining tables)

- Check row counts **before and after every join**. An unexpected increase means a duplicate-key fan-out; an unexpected decrease means an inner join silently dropped rows.
- Prefer explicit join type + a post-join assertion (`assert len(joined) == len(left)` for a 1:1 enrichment join).
- After a left join, check the null rate of the joined columns — high nulls mean the join key didn't match, not that the data is missing.

## Disposition rules

For each anomaly found, choose one, and write it down:

1. **Fix in code** (parse the currency string, strip whitespace, normalize categories) — with a logged count of affected rows.
2. **Exclude** (drop rows/columns) — with a logged count and the exclusion rule stated in the report.
3. **Escalate** (the data source is broken; the analysis can't proceed honestly) — report rather than paper over.

Never option 4 (ignore silently).
