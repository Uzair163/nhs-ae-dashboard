import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import data  # noqa: E402

st.set_page_config(page_title="12-Hour Wait Crisis", page_icon="🔥", layout="wide")

d = data.load_data()
df = d["joined"]
trend = data.national_monthly_trend(df)
forecast = d["fact_forecast"].merge(d["dim_date"], on="date_key", how="left")
forecast = forecast.sort_values(["calendar_year", "month_number"])
forecast["period_label"] = forecast["month_name"].str[:3] + " " + (forecast["calendar_year"] % 100).astype(str).str.zfill(2)

st.title("The 12-Hour Trolley Wait Crisis")

jan26_row = trend[trend["period_label"] == "Jan 26"]
dec22_row = trend[trend["period_label"] == "Dec 22"]
jan26 = jan26_row["pct_12plus_wait"].iloc[0] if len(jan26_row) else None
dec22 = dec22_row["pct_12plus_wait"].iloc[0] if len(dec22_row) else None

st.error(
    f"**January 2026 ({jan26:.1f}% of emergency admissions waited 12+ hours) already exceeds "
    f"the widely-reported December 2022 'record' of {dec22:.1f}%.** The crisis most public "
    f"commentary treats as a past low point is not the worst point in this dataset — the most "
    f"recent winter is."
)

col1, col2 = st.columns(2)
col1.metric("December 2022 (widely cited as the record)", f"{dec22:.1f}%")
col2.metric("January 2026 (actual record in this data)", f"{jan26:.1f}%", delta=f"{jan26-dec22:+.1f} pp vs Dec 2022")

st.subheader("Full history: 12+ hour waits as a share of emergency admissions")
full_chart = trend.set_index("period_label")[["pct_12plus_wait"]].rename(
    columns={"pct_12plus_wait": "% waiting 12+ hrs"}
)
st.line_chart(full_chart, height=380)

st.subheader("Last 24 months, plus the Winter 2026-27 forecast")
recent = trend.tail(24)[["period_label", "pct_12plus_wait"]].copy()
recent["type"] = "Actual"
fc = forecast[["period_label", "pct_12plus_wait_forecast"]].rename(columns={"pct_12plus_wait_forecast": "pct_12plus_wait"})
fc["type"] = "Forecast"

# bridge point so the forecast line connects visually to the last actual point
bridge = recent.tail(1).copy()
bridge["type"] = "Forecast"
combined = pd.concat([recent, bridge, fc], ignore_index=True)

pivot = combined.pivot_table(index="period_label", columns="type", values="pct_12plus_wait", aggfunc="first")
# preserve chronological order (pivot_table sorts alphabetically by default)
order = list(recent["period_label"]) + list(fc["period_label"])
pivot = pivot.reindex(order)
st.line_chart(pivot, height=380)

st.caption(
    "Forecast method: naive same-month-last-year, backtested at ~1.3 percentage points mean "
    "absolute error — the best of four methods tested, beating a linear trend model whose "
    "full-history fit was biased by the 2020-22 structural break. See docs/forecast_methodology.md."
)

with st.expander("Show underlying monthly data"):
    st.dataframe(
        trend[["period_label", "pct_12plus_wait", "waited_12plus_hrs_dta", "total_emergency_admissions"]]
        .rename(columns={
            "period_label": "Month",
            "pct_12plus_wait": "% 12+ hr waits",
            "waited_12plus_hrs_dta": "12+ hr waits (count)",
            "total_emergency_admissions": "Emergency admissions",
        }),
        use_container_width=True,
        hide_index=True,
    )
