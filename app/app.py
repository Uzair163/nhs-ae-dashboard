import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
import data  # noqa: E402

st.set_page_config(page_title="NHS A&E Performance", page_icon="🏥", layout="wide")

d = data.load_data()
df = d["joined"]
trend = data.national_monthly_trend(df)

st.title("NHS England A&E Performance, Apr 2019 – Aug 2026")
st.caption(
    "Built from NHS England's public monthly A&E statistics as a Reproducible Analytical "
    "Pipeline (raw CSVs → validated panel → this app). See the Methodology page in the "
    "sidebar repo link for the full write-up, including two real data-quality issues found "
    "and fixed during development."
)

latest = trend.iloc[-1]
type1_gap = latest["type3_pct_within_4hrs"] - latest["type1_pct_within_4hrs"]

col1, col2, col3 = st.columns(3)
col1.metric(
    f"National 4-hour performance ({latest['period_label']})",
    f"{latest['pct_within_4hrs']:.1f}%",
)
col2.metric(
    f"Type 1 (major A&E) performance ({latest['period_label']})",
    f"{latest['type1_pct_within_4hrs']:.1f}%",
    help="The major emergency departments where seriously ill patients go — this is well below the blended national figure.",
)
col3.metric(
    "Gap vs Type 3 (minor units)",
    f"{type1_gap:.1f} pp",
    help="How much better minor injury units perform than major A&E — this gap has nearly doubled since 2019.",
)

st.subheader("The hidden gap: national headline vs. major A&E departments")
st.markdown(
    "The national blended figure is propped up by Type 3 minor injury units, which have "
    "stayed near 95–99% throughout. Type 1 departments — where the seriously ill actually "
    "go — collapsed to the mid-50s%/low-60s% from 2022 onward and have not recovered."
)

chart_df = trend.set_index("period_label")[
    ["pct_within_4hrs", "type1_pct_within_4hrs", "type3_pct_within_4hrs"]
].rename(columns={
    "pct_within_4hrs": "National (blended)",
    "type1_pct_within_4hrs": "Type 1 (major A&E)",
    "type3_pct_within_4hrs": "Type 3 (minor units)",
})
st.line_chart(chart_df, height=420)

with st.expander("Show underlying monthly data"):
    st.dataframe(
        trend[["period_label", "pct_within_4hrs", "type1_pct_within_4hrs", "type3_pct_within_4hrs", "total_attendances"]]
        .rename(columns={
            "period_label": "Month",
            "pct_within_4hrs": "National %",
            "type1_pct_within_4hrs": "Type 1 %",
            "type3_pct_within_4hrs": "Type 3 %",
            "total_attendances": "Total attendances",
        }),
        use_container_width=True,
        hide_index=True,
    )

st.sidebar.markdown("### Pages")
st.sidebar.markdown(
    "- **National Performance** (this page)\n"
    "- **12-Hour Wait Crisis**\n"
    "- **Trust Comparison**\n"
    "- **Winter Forecast**"
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Data source: [NHS England A&E statistics]"
    "(https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/)"
)
