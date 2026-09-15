"""
Shared data-loading and aggregation functions for the NHS A&E Streamlit app.

Kept separate from the Streamlit UI code deliberately: everything in this file
is plain pandas and can be tested and verified without running Streamlit at
all (which matters here since Streamlit isn't installed in the environment
this was built in — see README for details). If something in the app looks
wrong, the bug is almost certainly in app.py / pages/*.py, not here, since
every function below was checked against known values before being used.
"""

import os

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "powerbi_model")

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def load_data():
    """Load the four star-schema tables and return as a dict of DataFrames."""
    dim_date = pd.read_csv(os.path.join(DATA_DIR, "Dim_Date.csv"))
    dim_trust = pd.read_csv(os.path.join(DATA_DIR, "Dim_Trust.csv"))
    fact_ae = pd.read_csv(os.path.join(DATA_DIR, "Fact_AE.csv"))
    fact_forecast = pd.read_csv(os.path.join(DATA_DIR, "Fact_Forecast.csv"))

    # Join fact table to both dimensions once, up front, so every page works
    # off one wide, ready-to-filter DataFrame rather than re-joining repeatedly.
    df = fact_ae.merge(dim_date, on="date_key", how="left").merge(dim_trust, on="org_code", how="left")
    df["month_name"] = pd.Categorical(df["month_name"], categories=MONTH_ORDER, ordered=True)

    return {
        "dim_date": dim_date,
        "dim_trust": dim_trust,
        "fact_ae": fact_ae,
        "fact_forecast": fact_forecast,
        "joined": df,
    }


def national_monthly_trend(df, exclude_suspect=False):
    """
    National monthly 4-hour performance, Type 1, and Type 3 splits.
    Returns one row per date_key, sorted chronologically.

    exclude_suspect=False by default here deliberately: at national level the
    flagged rows are a small share of total volume and the effect washes out
    (see docs/schema_log.md) — this mirrors the Power BI spec, which uses the
    unfiltered measure on the national trend page but the "(Clean)" one for
    Trust-level ranking.
    """
    d = df[~df["suspect_zero_breach_flag"]] if exclude_suspect else df

    g = d.groupby(["date_key", "calendar_year", "month_number", "month_name"], observed=True).agg(
        total_attendances=("total_attendances", "sum"),
        total_over4hrs=("total_over4hrs", "sum"),
        ae_type1=("ae_type1", "sum"),
        over4hrs_type1=("over4hrs_type1", "sum"),
        ae_other=("ae_other", "sum"),
        over4hrs_other=("over4hrs_other", "sum"),
        waited_12plus_hrs_dta=("waited_12plus_hrs_dta", "sum"),
        emergency_admissions_type1=("emergency_admissions_type1", "sum"),
        emergency_admissions_type2=("emergency_admissions_type2", "sum"),
        emergency_admissions_other=("emergency_admissions_other", "sum"),
        other_emergency_admissions=("other_emergency_admissions", "sum"),
    ).reset_index()

    g["pct_within_4hrs"] = 100 * (1 - g["total_over4hrs"] / g["total_attendances"])
    g["type1_pct_within_4hrs"] = 100 * (1 - g["over4hrs_type1"] / g["ae_type1"])
    g["type3_pct_within_4hrs"] = 100 * (1 - g["over4hrs_other"] / g["ae_other"])
    g["total_emergency_admissions"] = (
        g["emergency_admissions_type1"] + g["emergency_admissions_type2"]
        + g["emergency_admissions_other"] + g["other_emergency_admissions"]
    )
    g["pct_12plus_wait"] = 100 * g["waited_12plus_hrs_dta"] / g["total_emergency_admissions"]

    g = g.sort_values(["calendar_year", "month_number"]).reset_index(drop=True)
    g["period_label"] = g["month_name"].astype(str).str[:3] + " " + (g["calendar_year"] % 100).astype(str).str.zfill(2)
    return g


def trust_ranking(df, baseline_fy="2019-2020", recent_fy="2025-2026", min_volume=5000):
    """
    Trust-level baseline-vs-recent comparison, EXCLUDING suspect zero-breach
    rows entirely (unlike the national trend). This is the function that
    would have produced the misleading Nottingham 97% artifact if it hadn't
    excluded flagged rows — see docs/schema_log.md.
    """
    d = df[~df["suspect_zero_breach_flag"]]

    g = d.groupby(["org_code", "org_name", "parent_org", "financial_year"]).agg(
        total_attendances=("total_attendances", "sum"),
        total_over4hrs=("total_over4hrs", "sum"),
    ).reset_index()
    g["pct_within_4hrs"] = 100 * (1 - g["total_over4hrs"] / g["total_attendances"])

    baseline = g[g["financial_year"] == baseline_fy].set_index("org_code")
    recent = g[g["financial_year"] == recent_fy].set_index("org_code")

    common = baseline.index.intersection(recent.index)
    baseline = baseline.loc[common]
    recent = recent.loc[common]

    result = pd.DataFrame({
        "org_code": common,
        "org_name": baseline["org_name"].values,
        "parent_org": baseline["parent_org"].values,
        "baseline_pct": baseline["pct_within_4hrs"].values,
        "baseline_attendances": baseline["total_attendances"].values,
        "recent_pct": recent["pct_within_4hrs"].values,
        "recent_attendances": recent["total_attendances"].values,
    })
    result = result[
        (result["baseline_attendances"] >= min_volume) & (result["recent_attendances"] >= min_volume)
    ].reset_index(drop=True)
    result["change_pp"] = result["recent_pct"] - result["baseline_pct"]

    q1_baseline = result["baseline_pct"].quantile(0.25)
    q1_recent = result["recent_pct"].quantile(0.25)
    result["persistent_bottom_quartile"] = (result["baseline_pct"] <= q1_baseline) & (
        result["recent_pct"] <= q1_recent
    )

    return result.sort_values("recent_pct").reset_index(drop=True)
