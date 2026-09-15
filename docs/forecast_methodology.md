# Winter 2026-27 Forecast Methodology

## Goal
Forecast national 4-hour performance and 12+ hour trolley wait risk for the upcoming winter (Sep 2026 - Feb 2027), the kind of output an NHS performance/planning team would actually be asked to produce ahead of winter.

## Methods tested (backtested on the most recent available year, per calendar month)

| Method | Mean Absolute Error |
|---|---|
| Linear trend fit on all years (2019-2025) | ~7.7 percentage points |
| Linear trend fit on 2022+ only | ~1.8 percentage points |
| 2-year average, same calendar month | ~2.1 percentage points |
| **Naive: same month, previous year** | **~1.3 percentage points (best)** |

## Why the naive method wins
A&E performance is dominated by a strong, fairly stable annual seasonal pattern (winter pressure, summer relief) rather than a smooth underlying trend. Fitting a linear trend across the full 2019-2025 history is biased by the sharp structural decline during 2020-2022 (COVID + workforce pressure) — that model keeps extrapolating the decline forward into a period (2023-2026) where performance actually plateaued. A simple "repeat last year's same month" forecast sidesteps this entirely, since it only ever extrapolates from the most recent, most representative regime.

This isn't a case for avoiding more sophisticated methods on principle — a proper SARIMA or seasonal exponential smoothing model, given a longer and more stable history, would likely do better still. It's a case for testing before committing: the fancier trend-based method here was worse, and reporting that honestly is itself useful for a performance team, not a limitation to hide.

## Forecast output
See `output/forecast_winter_2026_27.csv`. Uncertainty bands are the standard deviation of the naive method's own historical one-step-ahead backtest errors, per month — a simple but honest measure of how much this specific method has been wrong by historically, not a formal prediction interval.

## Headline result
January 2027's 12+ hour wait risk is forecast at 13.1% (±1.3pp) of emergency admissions — the same level as the current record set in January 2026, not an improvement. Under this method, "next winter" is expected to be at least as severe as the worst winter in the dataset, not better.
