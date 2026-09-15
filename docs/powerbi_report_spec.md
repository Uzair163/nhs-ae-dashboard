# Report Layout Spec — 4 Pages

Import order: `Dim_Date.csv`, `Dim_Trust.csv`, `Fact_AE.csv`, `Fact_Forecast.csv` from `output/powerbi_model/`. Build relationships and measures per `docs/powerbi_measures.md` before starting on visuals.

Global slicers (place on every page, or use a bookmark-linked filter pane): `Dim_Date[financial_year]`, `Dim_Trust[parent_org]` (region).

---

## Page 1 — National Performance

**Purpose**: answer "how is NHS A&E doing", and immediately surface that the headline number understates the real problem.

| Visual | Fields | Notes |
|---|---|---|
| Card | `[Pct Within 4Hrs]`, latest month | Big headline number top-left |
| Card | `[Type1 Pct Within 4Hrs]`, latest month | Placed right next to the headline card — the contrast is the point |
| Line chart | `Dim_Date[date_key]` (axis), `[Pct Within 4Hrs]` and `[Type1 Pct Within 4Hrs]` and `[Type3 Pct Within 4Hrs]` (values) | The "hidden gap" chart from the findings doc — three lines, full history |
| Line chart (small multiple or shaded background) | Same axis, `is_winter` as a background band | Makes winter pressure visually obvious without needing a caption |

**Caption/text box**: one line stating the Type 1 vs Type 3 gap finding directly — don't make the viewer infer it from the chart alone.

---

## Page 2 — The 12-Hour Wait Crisis

**Purpose**: the strongest single finding — lead with this if the dashboard is ever demoed live.

| Visual | Fields | Notes |
|---|---|---|
| Card | `[Pct 12Plus Hr Wait]`, Jan 2026 specifically pinned (not just "latest") | Label it "Current record: Jan 2026" |
| Line chart | `Dim_Date[date_key]`, `[Pct 12Plus Hr Wait]` | Full history, annotate Dec 2022 and Jan 2026 as the two peaks |
| Combo chart (line + forecast) | Actual + `Fact_Forecast[pct_12plus_wait_forecast]`, last 24 months + 6 forecast months | Use a dashed line style or different color for the forecast segment |
| Text box | Headline stat: "January 2026 (13.1%) already exceeds the widely-reported December 2022 record (10.55%)" | This is the line to lead an interview answer with |

---

## Page 3 — Trust Comparison

**Purpose**: which Trusts are structurally struggling, not just having a bad winter.

| Visual | Fields | Notes |
|---|---|---|
| Slicer | `Fact_AE[suspect_zero_breach_flag]` defaulted to exclude `True` | Make this visible, not hidden — it's a feature, not housekeeping |
| Bar chart, sorted ascending | `Dim_Trust[org_name]` (axis), `[Pct Within 4Hrs (Clean)]` for latest financial year (values) | Top/bottom N filter, e.g. bottom 20 |
| Table | `Dim_Trust[org_name]`, `[Pct Within 4Hrs (Clean)]` 2019-20 vs 2025-26, `Dim_Trust[persistent_bottom_quartile]` | Conditional formatting on the persistent-bottom-quartile column |
| Map (if using a region shape file) or a matrix by `parent_org` | `[Pct Within 4Hrs (Clean)]` by region | Optional — only include if you want a geographic angle, not essential |

---

## Page 4 — Winter 2026-27 Forecast

**Purpose**: the forward-looking, "what should we plan for" page.

| Visual | Fields | Notes |
|---|---|---|
| Table | `Fact_Forecast[date_key]`, `pct_within_4hrs_forecast`, `pct_within_4hrs_uncertainty_pp`, `pct_12plus_wait_forecast`, `pct_12plus_wait_uncertainty_pp` | The raw forecast table, small and clean |
| Line chart with error bands | Same as Page 2's forecast chart, but for `pct_within_4hrs_forecast` this time | Shade the uncertainty band using the `_uncertainty_pp` columns as +/- offsets |
| Text box | The methodology summary from `docs/forecast_methodology.md` — the backtest comparison table specifically | This is the page where a technical interviewer will ask "how did you build this", so the method needs to be visible, not just the output |

---

## Design notes
- Keep the color for "Type 1" and "12+ hour wait" consistent across all 4 pages (e.g. a warning red/orange) — it's the same underlying crisis story told from different angles, and consistent color reinforces that.
- Don't hide the `suspect_zero_breach_flag` slicer on Page 3 — showing it, defaulted to exclude, is itself evidence of the data-quality rigor this project is meant to demonstrate.
