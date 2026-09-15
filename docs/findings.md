# Key Findings

## 1. The national headline figure hides a much worse story at major A&E departments
National blended 4-hour performance (currently ~72-75%) is propped up by Type 3/minor injury units, which have run at 95-99% throughout the entire period. Type 1 departments — the major A&E units where seriously ill and injured patients actually go — collapsed from ~77-81% in 2019 to a sustained 55-63% since 2022, and have never recovered. The gap between the two has nearly doubled: ~25 percentage points in 2019, ~35-40 points from 2022 onward. Reporting only the blended national figure, as most public commentary does, materially understates how bad major A&E performance actually is.

## 2. The 12+ hour trolley wait crisis is currently worse than the widely-reported 2022 "record"
12+ hour waits from decision-to-admit rose from a negligible 0.08-0.09% of emergency admissions pre-COVID to a widely-reported peak of 10.55% in December 2022. That figure is often cited as the record low point for NHS emergency care. It is not the record: January 2026 reached 13.1% — the highest point in the entire dataset — and the series has not returned to anywhere near pre-2022 levels since. This is a stronger, more current, and more newsworthy finding than the original 4-hour framing, and is worth leading with.

## 3. 19 Trusts are persistent bottom-quartile performers, not just COVID casualties
Comparing 2019-20 (pre-COVID baseline) against 2025-26 (most recent full year), 19 Trusts sit in the bottom quartile in BOTH years — including East Cheshire, The Shrewsbury and Telford Hospital, Royal United Hospitals Bath, and Hull University Teaching Hospitals. These are structural, persistent underperformers rather than Trusts knocked down temporarily by the pandemic. This ranking excludes the 41 Trusts affected by the non-reporting data-quality issue documented in schema_log.md — including them (as an early, unvalidated version of this analysis did) produces a misleading ranking with implausible "97% performer" results.

## Data-quality issues caught during development (see schema_log.md for full detail)
- A column-mapping bug in the ingest pipeline silently nulled core attendance figures for 16 files (2019-20 through mid-2020) before being caught by sanity-checking national trends against known NHS figures.
- 41 Trusts show a documented NHS England non-reporting artifact (zero recorded breaches despite meaningful attendance volume) tied to a stated May 2019-May 2023 field-testing period — flagged in the panel and excluded from ranking/forecasting rather than treated as genuine 100% performance.
