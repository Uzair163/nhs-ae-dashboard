import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import data  # noqa: E402
import filters  # noqa: E402
import theme  # noqa: E402

st.set_page_config(page_title="Trust Comparison", page_icon="🏥", layout="wide")

d = data.load_data()
df = d["joined"]

selected_regions, selected_trusts = filters.sidebar_filters(d["dim_trust"])
filtered_df = filters.apply_filters(df, selected_regions, selected_trusts)
scope = filters.scope_label(selected_regions, selected_trusts)

st.title("Trust Comparison: 2019-20 vs 2025-26")
st.caption(f"**Showing: {scope}**")

if filtered_df.empty:
    st.warning("No data matches the current filter selection. Try clearing filters in the sidebar.")
    st.stop()

n_flagged = int(filtered_df["suspect_zero_breach_flag"].sum())
n_flagged_trusts = filtered_df[filtered_df["suspect_zero_breach_flag"]]["org_code"].nunique()

st.info(
    f"**Data-quality exclusion applied**: {n_flagged:,} Trust-month rows across "
    f"{n_flagged_trusts} Trusts are excluded from this page. NHS England's own guidance "
    f"states 14 Trusts stopped reporting 4-hour breaches during a May 2019-May 2023 "
    f"field-testing period — those rows show implausible near-100% performance if included "
    f"(verified against Nottingham University Hospitals' real ~63-67% baseline). "
    f"See docs/schema_log.md for the full investigation."
)

ranking = data.trust_ranking(filtered_df)

if ranking.empty:
    st.warning(
        "No Trust has enough volume in both 2019-20 and 2025-26 within the current filter "
        "selection to compare. Try widening the Region/Trust filter."
    )
    st.stop()

show_persistent_only = st.checkbox("Show only persistent bottom-quartile Trusts (struggling in both years)")
display_df = ranking[ranking["persistent_bottom_quartile"]] if show_persistent_only else ranking

st.subheader(f"{'Persistent bottom-quartile Trusts' if show_persistent_only else 'All Trusts'} ({len(display_df)})")

col1, col2 = st.columns([2, 1])
with col1:
    bottom_20 = ranking.head(20).set_index("org_name")[["recent_pct"]].rename(
        columns={"recent_pct": "2025-26 performance %"}
    )
    st.caption("Lowest-performing Trusts, 2025-26 (flag-excluded)")
    st.bar_chart(bottom_20, height=500, color=[theme.NHS_RED])

with col2:
    st.caption("Persistent bottom-quartile summary")
    st.metric("Trusts struggling in BOTH 2019-20 and 2025-26", int(ranking["persistent_bottom_quartile"].sum()))
    st.metric("Total Trusts compared", len(ranking))
    st.metric(
        "Median change, 2019-20 → 2025-26",
        f"{ranking['change_pp'].median():+.1f} pp",
        help="Median across all compared Trusts — negative means performance has fallen for most Trusts, not just the worst ones.",
    )

st.subheader("Full comparison table")
table_df = display_df[["org_name", "parent_org", "baseline_pct", "recent_pct", "change_pp", "persistent_bottom_quartile"]].copy()
table_df["baseline_pct"] = table_df["baseline_pct"].round(1)
table_df["recent_pct"] = table_df["recent_pct"].round(1)
table_df["change_pp"] = table_df["change_pp"].round(1)
table_df = table_df.rename(columns={
    "org_name": "Trust",
    "parent_org": "NHS Region",
    "baseline_pct": "2019-20 %",
    "recent_pct": "2025-26 %",
    "change_pp": "Change (pp)",
    "persistent_bottom_quartile": "Persistent bottom quartile",
})
st.dataframe(table_df, use_container_width=True, hide_index=True, height=500)
