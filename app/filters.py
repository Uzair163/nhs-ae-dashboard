"""
Shared sidebar Region/Trust filters.

Every page that calls sidebar_filters() uses the same two widget keys
("filter_regions", "filter_trusts"), so Streamlit's session_state keeps the
selection in sync as the user moves between pages — pick a Region on page 1,
it's still applied when you click through to page 2.

Winter Forecast doesn't use this: the forecast model only ever produces one
national figure per month, there's no Trust-level breakdown to filter.
"""
import streamlit as st


def sidebar_filters(dim_trust):
    """Render Region + Trust multiselects in the sidebar and return the
    selected values. Trust options narrow automatically to whichever
    Region(s) are selected."""
    st.sidebar.markdown("### Filters")

    regions = sorted(dim_trust["parent_org"].dropna().unique())
    selected_regions = st.sidebar.multiselect("NHS Region", regions, key="filter_regions")

    trust_pool = (
        dim_trust[dim_trust["parent_org"].isin(selected_regions)]
        if selected_regions
        else dim_trust
    )
    trust_options = sorted(trust_pool["org_name"].unique())

    # If narrowing the Region filter drops a previously-picked Trust out of
    # scope, clean session_state *before* the widget below reads it — a
    # remembered value containing an option that no longer exists raises an
    # error rather than being silently ignored.
    if "filter_trusts" in st.session_state:
        st.session_state["filter_trusts"] = [
            t for t in st.session_state["filter_trusts"] if t in trust_options
        ]

    selected_trusts = st.sidebar.multiselect("Trust", trust_options, key="filter_trusts")

    if st.sidebar.button("Clear filters"):
        st.session_state["filter_regions"] = []
        st.session_state["filter_trusts"] = []
        st.rerun()

    return selected_regions, selected_trusts


def apply_filters(df, selected_regions, selected_trusts):
    """Filter the joined DataFrame down to the selected Region(s)/Trust(s).
    An empty selection for either means "no restriction on that dimension"."""
    filtered = df
    if selected_regions:
        filtered = filtered[filtered["parent_org"].isin(selected_regions)]
    if selected_trusts:
        filtered = filtered[filtered["org_name"].isin(selected_trusts)]
    return filtered


def scope_label(selected_regions, selected_trusts):
    """Short human-readable description of the current filter scope, used
    in page titles/captions so it's always clear what's being shown."""
    if selected_trusts:
        return f"{len(selected_trusts)} selected Trust" + ("s" if len(selected_trusts) != 1 else "")
    if selected_regions:
        return f"{len(selected_regions)} selected NHS Region" + ("s" if len(selected_regions) != 1 else "")
    return "England (all Trusts)"
