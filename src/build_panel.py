"""
NHS A&E Waiting Times — Derive + Validate + Output
----------------------------------------------------
Takes the standardised records from ingest.build_panel(), derives the
4-hour performance metric, runs validation checks, and writes the clean
analysis-ready panel to output/ae_panel.csv plus a validation log.

4-hour performance formula:
    total_attendances = ae_type1 + ae_type2 + ae_other
    total_over4hrs     = over4hrs_type1 + over4hrs_type2 + over4hrs_other
    pct_within_4hrs     = 100 * (1 - total_over4hrs / total_attendances)

Booked-appointment columns are NOT added into these totals: NHS England's own
statistical commentaries describe booked appointments as attendances that
providers can "split... out from total attendances" — i.e. a subset of the
main Type 1/2/Other figures, not additional ones. Adding them in would double-count.
"""

import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from ingest import build_panel  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


def derive_metrics(rec):
    total_attendances = (rec["ae_type1"] or 0) + (rec["ae_type2"] or 0) + (rec["ae_other"] or 0)
    total_over4hrs = (
        (rec["over4hrs_type1"] or 0) + (rec["over4hrs_type2"] or 0) + (rec["over4hrs_other"] or 0)
    )
    total_booked = (
        (rec["ae_booked_type1"] or 0) + (rec["ae_booked_type2"] or 0) + (rec["ae_booked_other"] or 0)
    )

    if total_attendances > 0:
        pct_within_4hrs = round(100 * (1 - total_over4hrs / total_attendances), 2)
    else:
        pct_within_4hrs = None

    rec["total_attendances"] = total_attendances
    rec["total_over4hrs"] = total_over4hrs
    rec["total_booked_attendances"] = total_booked
    rec["pct_within_4hrs"] = pct_within_4hrs

    # Data-quality flag: NHS England's own guidance states that 14 Trusts stopped
    # reporting 4-hour performance during a field-testing period from May 2019 to
    # May 2023. A Trust-month with meaningful attendance volume but exactly zero
    # recorded breaches is very likely this non-reporting artifact, not a genuine
    # 100% result (verified for Nottingham University Hospitals against a known
    # ~63% real Q4 2018/19 performance immediately before this pattern starts).
    # Threshold of 1000 attendances excludes small, genuinely low-acuity providers
    # for whom near-zero breaches could be real, but flagging is a heuristic, not
    # a confirmed per-Trust fact for every case caught below the threshold.
    rec["suspect_zero_breach_flag"] = total_attendances > 1000 and total_over4hrs == 0

    return rec


def validate(records):
    """Run the three checks from the project brief. Returns list of issue strings."""
    issues = []

    # 1. No duplicate Trust-month rows
    seen = {}
    for r in records:
        key = (r["org_code"], r["financial_year"], r["month"])
        seen.setdefault(key, 0)
        seen[key] += 1
    dupes = {k: v for k, v in seen.items() if v > 1}
    if dupes:
        issues.append(f"DUPLICATE Trust-month rows found: {len(dupes)} keys, e.g. {list(dupes.items())[:5]}")

    # 2. 4-hour performance must be within 0-100%
    out_of_range = [
        r for r in records
        if r["pct_within_4hrs"] is not None and not (0 <= r["pct_within_4hrs"] <= 100)
    ]
    if out_of_range:
        issues.append(f"OUT-OF-RANGE performance values: {len(out_of_range)} rows")
        for r in out_of_range[:5]:
            issues.append(
                f"    {r['org_name']} {r['month']} {r['calendar_year']}: {r['pct_within_4hrs']}%"
            )

    # 3. Row counts per month look sane — flag months where Trust count deviates
    #    more than 15% from the rolling dataset median
    counts_by_period = defaultdict(int)
    for r in records:
        counts_by_period[(r["financial_year"], r["month"], r["calendar_year"])] += 1

    counts = sorted(counts_by_period.values())
    median_count = counts[len(counts) // 2]
    for period, count in counts_by_period.items():
        deviation = abs(count - median_count) / median_count
        if deviation > 0.15:
            issues.append(
                f"ROW COUNT ANOMALY: {period} has {count} Trusts "
                f"(median across dataset is {median_count}, {deviation:.0%} deviation)"
            )

    # 4. No row should have every core attendance field null — a real bug during
    #    development (a column-mapping overwrite) produced exactly this pattern
    #    silently, and none of the checks above caught it.
    all_null = [
        r for r in records
        if r["ae_type1"] is None and r["ae_type2"] is None and r["ae_other"] is None
    ]
    if all_null:
        issues.append(
            f"ALL-NULL core attendance fields: {len(all_null)} rows have "
            f"ae_type1, ae_type2, and ae_other all missing"
        )

    # 5. Sense-check: attendances over 4hrs should never exceed total attendances
    impossible = [r for r in records if r["total_over4hrs"] > r["total_attendances"]]
    if impossible:
        issues.append(f"IMPOSSIBLE VALUES: {len(impossible)} rows where over-4hr count exceeds total attendances")
        for r in impossible[:5]:
            issues.append(
                f"    {r['org_name']} {r['month']} {r['calendar_year']}: "
                f"over4hrs={r['total_over4hrs']} > total={r['total_attendances']}"
            )

    # 6. Report the suspect zero-breach data-quality flag (informational, not a failure —
    #    see derive_metrics() for the NHS-documented reasoning behind this heuristic)
    n_suspect = sum(1 for r in records if r["suspect_zero_breach_flag"])
    issues.append(
        f"INFO: {n_suspect} Trust-month rows flagged as suspect zero-breach "
        f"(>1000 attendances, 0 recorded breaches — likely non-reporting artifact, see docs/schema_log.md)"
    )

    return issues


def write_panel(records, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "financial_year", "month", "calendar_year", "org_code", "parent_org", "org_name",
        "ae_type1", "ae_type2", "ae_other",
        "ae_booked_type1", "ae_booked_type2", "ae_booked_other",
        "over4hrs_type1", "over4hrs_type2", "over4hrs_other",
        "over4hrs_booked_type1", "over4hrs_booked_type2", "over4hrs_booked_other",
        "waited_4_12hrs_dta", "waited_12plus_hrs_dta",
        "emergency_admissions_type1", "emergency_admissions_type2",
        "emergency_admissions_other", "other_emergency_admissions",
        "total_attendances", "total_over4hrs", "total_booked_attendances", "pct_within_4hrs",
        "suspect_zero_breach_flag",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main():
    records, file_log, n_non_trust, n_total = build_panel()
    records = [derive_metrics(r) for r in records]
    issues = validate(records)

    panel_path = os.path.join(OUTPUT_DIR, "ae_panel.csv")
    write_panel(records, panel_path)

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "validation_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"NHS A&E panel build — validation log\n")
        f.write(f"Rows in panel: {len(records)}\n")
        f.write(f"Files ingested: {len(file_log)}\n")
        f.write(f"Non-Trust provider rows dropped: {n_non_trust}\n")
        f.write(f"Aggregate TOTAL rows dropped: {n_total}\n\n")
        if issues:
            f.write(f"ISSUES FOUND ({len(issues)}):\n")
            for issue in issues:
                f.write(f"  - {issue}\n")
        else:
            f.write("No validation issues found.\n")

    print(f"Panel written to {panel_path} ({len(records)} rows)")
    print(f"Validation log written to {log_path}")
    print()
    if issues:
        print(f"{len(issues)} validation issue(s) found — see log for detail:")
        for issue in issues[:15]:
            print(" ", issue)
    else:
        print("No validation issues found.")


if __name__ == "__main__":
    main()
