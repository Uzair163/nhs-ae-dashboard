# Power BI Data Model & DAX Measures

## Model structure (star schema)

```
Dim_Date (95 rows: 89 actual months + 6 forecast months, flagged is_forecast)
  |
  +-- date_key --< Fact_AE (14,440 rows, one per Trust-month)
  |                   |
  +-- date_key --< Fact_Forecast (6 rows, winter 2026-27)
  
Dim_Trust (179 rows) --org_code--< Fact_AE
```

Import all four CSVs from `output/powerbi_model/`. Set relationships:
- `Dim_Date[date_key]` (1) → `Fact_AE[date_key]` (many)
- `Dim_Date[date_key]` (1) → `Fact_Forecast[date_key]` (many)
- `Dim_Trust[org_code]` (1) → `Fact_AE[org_code]` (many)

Mark `Dim_Date` as the official Date table (Model view → right-click Dim_Date → "Mark as date table", using a proper `Date` column — see note below on adding one if you want native Power BI time-intelligence functions like `SAMEPERIODLASTYEAR`).

## Why weighted, not simple, averages
`Fact_AE` does not include a pre-computed `pct_within_4hrs` column deliberately. Averaging a percentage column directly (e.g. `AVERAGE(Fact_AE[pct_within_4hrs])`) would silently give every Trust-month equal weight regardless of volume — a Trust with 500 attendances would count the same as one with 20,000. All measures below compute the percentage from summed numerators and denominators instead, which is the only way to get a correct number when slicing by Trust, region, or time period.

## Core measures

```dax
Total Attendances = SUM(Fact_AE[total_attendances])

Total Over 4Hrs = SUM(Fact_AE[total_over4hrs])

Pct Within 4Hrs =
DIVIDE(
    [Total Attendances] - [Total Over 4Hrs],
    [Total Attendances]
)

Total Emergency Admissions =
SUM(Fact_AE[emergency_admissions_type1]) +
SUM(Fact_AE[emergency_admissions_type2]) +
SUM(Fact_AE[emergency_admissions_other]) +
SUM(Fact_AE[other_emergency_admissions])

Total 12Plus Hr Waits = SUM(Fact_AE[waited_12plus_hrs_dta])

Pct 12Plus Hr Wait =
DIVIDE([Total 12Plus Hr Waits], [Total Emergency Admissions])
```

## Type 1 vs Type 3 split (the "hidden gap" finding)

```dax
Type1 Attendances = SUM(Fact_AE[ae_type1])
Type1 Over4Hrs = SUM(Fact_AE[over4hrs_type1])
Type1 Pct Within 4Hrs = DIVIDE([Type1 Attendances] - [Type1 Over4Hrs], [Type1 Attendances])

Type3 Attendances = SUM(Fact_AE[ae_other])
Type3 Over4Hrs = SUM(Fact_AE[over4hrs_other])
Type3 Pct Within 4Hrs = DIVIDE([Type3 Attendances] - [Type3 Over4Hrs], [Type3 Attendances])

Type1 vs Type3 Gap (pp) = ([Type3 Pct Within 4Hrs] - [Type1 Pct Within 4Hrs]) * 100
```

## Data-quality exclusion (suspect zero-breach rows)

```dax
Total Attendances (Clean) =
CALCULATE(
    [Total Attendances],
    Fact_AE[suspect_zero_breach_flag] = "False"
)

Pct Within 4Hrs (Clean) =
CALCULATE(
    [Pct Within 4Hrs],
    Fact_AE[suspect_zero_breach_flag] = "False"
)
```
Use the "(Clean)" versions for any Trust-level ranking or comparison visual — the raw versions are fine for the national trend view, since the excluded Trusts are a small share of national volume and the effect washes out at that level, but they'd badly distort a Trust-by-Trust ranking (this is exactly the Nottingham 97% artifact from earlier).

## Year-on-year comparison
Power BI's built-in time-intelligence functions (`SAMEPERIODLASTYEAR`, `DATEADD`) need a proper contiguous `Date` column (one row per day) on the date table, not just a month key. If you want native YoY measures, add a `Date` column to `Dim_Date` as the first day of each month (`DATE(calendar_year, month_number, 1)`) via a calculated column, then mark that as the date table's key column instead of `date_key`. Otherwise, a manual approach works fine given the data is monthly, not daily:

```dax
Pct Within 4Hrs LY =
CALCULATE(
    [Pct Within 4Hrs],
    FILTER(
        ALL(Dim_Date),
        Dim_Date[month_number] = SELECTEDVALUE(Dim_Date[month_number]) &&
        Dim_Date[calendar_year] = SELECTEDVALUE(Dim_Date[calendar_year]) - 1
    )
)

Pct Within 4Hrs YoY Change (pp) = ([Pct Within 4Hrs] - [Pct Within 4Hrs LY]) * 100
```

## Persistent bottom-quartile flag
Already baked into `Dim_Trust.csv` as a `persistent_bottom_quartile` boolean column (computed the same way as `docs/findings.md`: bottom 25% in both 2019-20 and 2025-26, using the flag-excluded panel). Just drag it onto a visual as a filter or legend split — no DAX needed. If you'd rather see the logic live inside the model instead of baked in from Python, it's re-creatable with `RANKX` over the two financial years, but there's no real benefit to redoing it that way for this dashboard.

## Row-level security (optional, but named on your CV skills list)
To demonstrate RLS: create a role filtered on `Dim_Trust[parent_org]` (the NHS region field), e.g.
```dax
[parent_org] = USERPRINCIPALNAME()
```
mapped via a bridging table of user emails to region, so a regional manager only sees their own region's Trusts. Not required for a single-user portfolio dashboard, but worth setting up once to have a concrete, demonstrable RLS example if asked about it directly.
