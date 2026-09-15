# Schema and Data Quality Log

Findings from inspecting all 89 raw monthly files (Apr 2019 – Aug 2026).

## Schema eras

| Era | Coverage | Files | Columns | Notes |
|---|---|---|---|---|
| A | 2019-20, all 12 months | 12 | 16 | Columns prefixed "Number of A&E attendances..." |
| B | 2020-21, Apr–Jul only | 4 | 16 | Prefix dropped: "A&E attendances Type 1" etc. No booked-appointment fields yet |
| C | Aug 2020 onward (all years through Aug 2026) | 72 | 22 | Adds 6 "Booked Appointments" fields (confirmed by NHS England definitions doc v5.0, Aug 2020: "reflects the addition of booked appointments to the collection") |
| D (anomaly, not a real era) | 1 file only | 1 | 28 raw | `Monthly-AE-September-2024.csv` has 6 trailing blank columns plus a stray "a" character in the header — an editing artifact, not a schema change. Handled by trimming trailing blank-named columns in `read_header()`. |

## Provider types mixed into every file

Each raw file contains three provider types distinguished by Org Code length:
- **3-character codes** — NHS Trusts (the panel's actual analysis unit)
- **5/6-character codes** — Urgent Treatment Centres, minor injury units, GP-led health centres (excluded from the panel)
- A literal aggregate **TOTAL row** per file, inconsistently spelled across the dataset: `TOTAL` (59 files), `Total` (17 files), `TOTAl` (1 file). Filtered case-insensitively on both Org Code and Period.

Across all 89 files: 4,027 non-Trust provider rows and 77 TOTAL rows were dropped, leaving 14,440 Trust-month rows.

## Booked appointments are a subset, not additional attendances

NHS England's statistical commentaries (e.g. July 2021: "as the data on booked appointments is new... providers are increasingly able to split them out from total attendances") confirm booked appointments are already counted within the Type 1/2/Other attendance figures. The 4-hour performance formula therefore uses only Type 1/2/Other columns as the denominator — adding booked figures on top would double-count.

## Bug found and fixed during ingest development

Initial ingest logic looped over every era's column-name synonym for every row, rather than only the columns present in that file's own header. For Era A/B files, a later-era synonym absent from the file (e.g. `"A&E attendances Type 1"` in a 2019-20 file) returned `None` and silently overwrote a value the correct, earlier synonym had already set for the same canonical field. This wiped core attendance figures to `None` (defaulting to 0 in the derived totals) for all 16 Era A/B files before being caught — nothing in the original three validation checks (duplicates, range, row-count anomalies) detected it, since 0% wasn't out of the 0–100 range and row counts were unaffected. Caught only by sanity-checking national aggregated performance against publicly known NHS figures (December 2022's well-documented low of ~67%). A dedicated all-null check was added to the validation step as a result.

## Second data-quality finding: non-reporting Trusts, not genuine 100% performance

NHS England's own data-quality guidance states that "during the period of May 2019 to May 2023 fourteen NHS Trusts undertook field testing of new UEC performance metrics and stopped reporting information on four hour performance." This produces a distinctive pattern in the raw data: meaningful attendance volume (often 5,000+ a month) alongside exactly zero recorded over-4-hour breaches — which reads as a perfect 100% performance if taken at face value.

Verified for Nottingham University Hospitals NHS Trust specifically: April 2019 shows a real 66.7% performance, then 11 of the next 12 months show exactly 0 breaches. An independent source (Statista, citing NHS England Q4 2018/19 data) put Nottingham's real 4-hour performance at under 63% the previous quarter — confirming the "100%" months are a non-reporting artifact, not genuine improvement.

Scanning the full panel for the pattern (>1,000 attendances, 0 recorded breaches) found 1,026 Trust-month rows across 41 Trusts. Most show the pattern for close to 49 consecutive months ending in 2023-24 — matching NHS's stated window almost exactly — and these are flagged as `suspect_zero_breach_flag = True` in the output panel and excluded from Trust-level ranking and forecasting. A smaller group (e.g. Assura Vertis Urgent Care Centres, First Community Health and Care CIC, DHU Health Care) show the pattern across the *entire* dataset span rather than stopping at 2023-24 — these are genuinely low-acuity urgent care providers where near-zero breaches may be real rather than a reporting gap, so the flag is documented as a heuristic rather than a confirmed fact for every row it catches.
