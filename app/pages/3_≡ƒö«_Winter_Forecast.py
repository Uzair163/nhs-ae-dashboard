import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import data  # noqa: E402

st.set_page_config(page_title="Winter Forecast", page_icon="🔮", layout="wide")

d = data.load_data()
forecast = d["fact_forecast"].merge(d["dim_date"], on="date_key", how="left")
forecast = forecast.sort_values(["calendar_year", "month_number"]).reset_index(drop=True)
forecast["period_label"] = forecast["month_name"] + " " + forecast["calendar_year"].astype(str)

st.title("Winter 2026-27 Forecast")

st.markdown(
    "**Method**: naive seasonal forecast (each month's forecast = the same month last year), "
    "chosen after backtesting against three alternatives. It won because A&E performance is "
    "dominated by a strong, stable seasonal pattern rather than a smooth trend — a linear "
    "regression fit across the full 2019-2025 history keeps extrapolating the sharp 2020-22 "
    "decline into a period that actually plateaued, making it the *worst* of the four methods "
    "tested, not the best. Full write-up in docs/forecast_methodology.md."
)

with st.expander("Show the backtest comparison"):
    st.table({
        "Method": [
            "Linear trend, all years (2019-2025)",
            "Linear trend, 2022+ only",
            "2-year average, same month",
            "Naive: same month, last year (used)",
        ],
        "Mean absolute error": ["~7.7 pp", "~1.8 pp", "~2.1 pp", "~1.3 pp (best)"],
    })

jan27 = forecast[forecast["month_name"] == "January"].iloc[0]
st.warning(
    f"**January 2027's 12+ hour wait risk is forecast at {jan27['pct_12plus_wait_forecast']:.1f}% "
    f"(±{jan27['pct_12plus_wait_uncertainty_pp']:.1f}pp) — the same as the current record set in "
    f"January 2026, not an improvement.** Under this method, next winter is expected to be at "
    f"least as severe as the worst winter in the dataset."
)

st.subheader("Forecast table")
st.dataframe(
    forecast[[
        "period_label", "pct_within_4hrs_forecast", "pct_within_4hrs_uncertainty_pp",
        "pct_12plus_wait_forecast", "pct_12plus_wait_uncertainty_pp",
    ]].rename(columns={
        "period_label": "Month",
        "pct_within_4hrs_forecast": "4-hr performance forecast %",
        "pct_within_4hrs_uncertainty_pp": "+/- (pp)",
        "pct_12plus_wait_forecast": "12+hr wait forecast %",
        "pct_12plus_wait_uncertainty_pp": "+/- (pp)",
    }),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Forecast chart: 4-hour performance")
chart_df = forecast.set_index("period_label")[["pct_within_4hrs_forecast"]].rename(
    columns={"pct_within_4hrs_forecast": "Forecast 4-hr performance %"}
)
st.line_chart(chart_df, height=350)

st.caption(
    "Uncertainty bands (+/-) are the standard deviation of this method's own historical "
    "one-step-ahead backtest errors, per calendar month — an honest measure of how wrong this "
    "specific method has been historically, not a formal statistical prediction interval."
)
