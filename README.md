# NHS England A&E Performance Dashboard

**Live dashboard:** [add your Streamlit Cloud URL here]

An end-to-end analysis of NHS England's public monthly A&E statistics (Apr 2019 – Aug 2026, 89 months, 179 Trusts), built as a Reproducible Analytical Pipeline (RAP): raw NHS CSVs → validated, star-schema data model → a public interactive dashboard, plus a Power BI-ready export.

This isn't a "here's a chart" project. The point was to work the way a real NHS performance/insight team would: pull the raw monthly releases, deal with the schema changes and reporting artifacts inside them, catch the kind of silent errors that produce a confidently wrong number, and turn the result into findings someone could actually act on.

## The headline findings

1. **The national 4-hour figure hides a much worse story.** The blended national number is propped up by Type 3 (minor injury) units, which have run at 95–99% throughout. Type 1 departments — where the seriously ill actually go — collapsed from ~77–81% in 2019 to a sustained 55–63% since 2022 and have never recovered. The gap between the two has roughly doubled.
2. **The 12-hour trolley wait crisis is currently worse than the widely-reported 2022 "record."** December 2022's 10.55% is the figure usually cited as the low point. It isn't the record: January 2026 hit 13.1%, the worst month in the dataset.
3. **19 Trusts are persistent, structural bottom-quartile performers** — not just Trusts still recovering from COVID. Comparing the 2019-20 baseline against 2025-26, the same 19 Trusts sit in the bottom quartile in both years.

Full write-up: [`docs/findings.md`](docs/findings.md).

## Two real data-quality bugs caught along the way

- **A silent ingest bug** wiped core attendance figures to zero for 16 files (2019-20 to mid-2020) because the ingest loop applied later-era column synonyms to earlier-era files. It passed all three original validation checks (duplicates, range, row-count) — 0% isn't out of range. Caught by sanity-checking the aggregated national trend against a known public figure (Dec 2022 ≈ 67%), which led to adding a dedicated all-null check.
- **A non-reporting artifact affecting 41 Trusts:** NHS England's own guidance confirms 14 Trusts stopped reporting 4-hour breaches for field testing between May 2019 and May 2023, which shows up in the raw data as "0 breaches despite 5,000+ attendances" — indistinguishable from perfect performance unless you know to look for it. Verified against an independent source (Nottingham University Hospitals' real ~63–67% vs the ~100% the raw data implies), then flagged and excluded from ranking and forecasting rather than taken at face value.

Full detail: [`docs/schema_log.md`](docs/schema_log.md).

## The forecast

Backtested four forecasting methods for Winter 2026-27 before picking one — a naive "same month last year" model beat two linear-trend approaches and a 2-year average, because performance is driven by a stable seasonal pattern, not a smooth trend that a straight line can extrapolate. Reported the losing methods and why, rather than only the winner. See [`docs/forecast_methodology.md`](docs/forecast_methodology.md).

## Dashboard

Four pages, filterable by NHS Region and Trust, styled to the NHS colour palette:

| Page | What it shows |
|---|---|
| National Performance | Headline KPIs, the Type 1 vs Type 3 trend line, monthly attendance volumes, attendance mix by department type |
| 12-Hour Wait Crisis | Full history of 12+ hour waits, the "current record vs widely-reported record" comparison |
| Trust Comparison | 2019-20 vs 2025-26 ranking, persistent bottom-quartile flag, data-quality exclusions applied |
| Winter Forecast | Backtest comparison, forecast table and chart with uncertainty bands |

## Tech stack

- **Python / pandas** — ingest, validation, panel-building, forecasting (`src/`)
- **Streamlit** — interactive dashboard (`app/`)
- **Power BI-ready star schema** — `Dim_Date`, `Dim_Trust`, `Fact_AE`, `Fact_Forecast` exported to `output/powerbi_model/`, with DAX measures documented in `docs/powerbi_measures.md`
- **matplotlib** — pie chart on the National Performance page

## Repo structure

```
raw/                  Original NHS England monthly CSVs (89 files, Apr 2019–Aug 2026)
src/                  RAP pipeline: ingest.py -> build_panel.py -> forecast.py
output/               Validated panel (ae_panel.csv), forecast output, Power BI model CSVs
app/                  Streamlit dashboard (app.py, data.py, filters.py, theme.py, pages/)
docs/                 Findings, forecast methodology, schema/data-quality log, Power BI spec
logs/                 Validation run log
```

## Running it locally

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

## Regenerating the data

Re-running `src/ingest.py` → `src/build_panel.py` → `src/forecast.py` against new raw files regenerates `output/ae_panel.csv` and the forecast. Re-running the Power BI export step regenerates `output/powerbi_model/*.csv`, which the Streamlit app picks up automatically — no app code changes needed.

## Data source

[NHS England: A&E Attendances and Emergency Admissions](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/) — published monthly, publicly available.
