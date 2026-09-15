"""
NHS A&E Waiting Times — Ingest Layer
------------------------------------
Reads every raw monthly CSV under raw/NHS Data/<financial_year>/*.csv,
standardises column names across three known schema eras, filters to
Trust-level rows, and stacks everything into one long panel
(Trust x Month x Year).

Schema eras identified by inspecting all 89 raw files (see docs/schema_log.md):
  Era A (2019-20, 12 files):        16 cols, "Number of A&E attendances..." naming
  Era B (Apr-Jul 2020, 4 files):    16 cols, "A&E attendances..." naming (no booked fields)
  Era C (Aug 2020 onward, 73 files): 22 cols, adds 6 "Booked Appointments" fields

One file (Monthly-AE-September-2024.csv) has 6 trailing blank columns plus a
stray character in the header — handled by trimming any column whose header
is empty after stripping.

Booked appointments are a SUBSET of the main Type 1/2/Other attendance figures,
not additional attendances — confirmed in NHS England's own statistical
commentaries ("providers are increasingly able to split them out from total
attendances"). Totals below therefore use only the Type 1/2/Other columns.
"""

import csv
import os
import re
from datetime import datetime

RAW_ROOT = os.path.join(os.path.dirname(__file__), "..", "raw", "NHS Data")

# Canonical column name -> list of raw header names that map to it across eras.
# Booked-appointment fields are canonical too, but will be None/blank pre-Aug 2020.
COLUMN_MAP = {
    "ae_type1": ["Number of A&E attendances Type 1", "A&E attendances Type 1"],
    "ae_type2": ["Number of A&E attendances Type 2", "A&E attendances Type 2"],
    "ae_other": [
        "Number of A&E attendances Other A&E Department",
        "A&E attendances Other A&E Department",
    ],
    "ae_booked_type1": ["A&E attendances Booked Appointments Type 1"],
    "ae_booked_type2": ["A&E attendances Booked Appointments Type 2"],
    "ae_booked_other": ["A&E attendances Booked Appointments Other Department"],
    "over4hrs_type1": [
        "Number of attendances over 4hrs Type 1",
        "Attendances over 4hrs Type 1",
    ],
    "over4hrs_type2": [
        "Number of attendances over 4hrs Type 2",
        "Attendances over 4hrs Type 2",
    ],
    "over4hrs_other": [
        "Number of attendances over 4hrs Other A&E Department",
        "Attendances over 4hrs Other Department",
    ],
    "over4hrs_booked_type1": ["Attendances over 4hrs Booked Appointments Type 1"],
    "over4hrs_booked_type2": ["Attendances over 4hrs Booked Appointments Type 2"],
    "over4hrs_booked_other": ["Attendances over 4hrs Booked Appointments Other Department"],
    "waited_4_12hrs_dta": ["Patients who have waited 4-12 hs from DTA to admission"],
    "waited_12plus_hrs_dta": ["Patients who have waited 12+ hrs from DTA to admission"],
    "emergency_admissions_type1": ["Emergency admissions via A&E - Type 1"],
    "emergency_admissions_type2": ["Emergency admissions via A&E - Type 2"],
    "emergency_admissions_other": ["Emergency admissions via A&E - Other A&E department"],
    "other_emergency_admissions": ["Other emergency admissions"],
}

NUMERIC_CANONICAL_COLS = [
    c for c in COLUMN_MAP if c not in ()
]

# Build reverse lookup: raw header -> canonical name
RAW_TO_CANONICAL = {}
for canonical, raw_names in COLUMN_MAP.items():
    for raw in raw_names:
        RAW_TO_CANONICAL[raw] = canonical

PERIOD_RE = re.compile(r"MSitAE-([A-Z]+)-(\d{4})", re.IGNORECASE)


def read_header(fpath):
    """Read and clean the header row, dropping trailing empty-named columns."""
    with open(fpath, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        raw_header = next(reader)
    # Trim from the end: drop any trailing column whose name is blank once stripped
    header = [h.strip() for h in raw_header]
    while header and header[-1] == "":
        header.pop()
    return header


def read_file(fpath, financial_year):
    """Read one raw CSV, standardise columns, filter to Trust rows, return list of dicts."""
    header = read_header(fpath)
    n_cols = len(header)

    records = []
    skipped_non_trust = 0
    skipped_total_row = 0

    with open(fpath, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip raw header, we use our cleaned one
        for row in reader:
            row = row[:n_cols]  # drop any trailing garbage columns beyond cleaned header
            if len(row) < n_cols:
                row = row + [""] * (n_cols - len(row))
            rec_raw = dict(zip(header, row))

            org_code = (rec_raw.get("Org Code") or "").strip()
            period = (rec_raw.get("Period") or "").strip()

            if not org_code:
                continue
            if "total" in org_code.lower() or "total" in period.lower():
                skipped_total_row += 1
                continue
            if len(org_code) != 3:
                skipped_non_trust += 1
                continue

            m = PERIOD_RE.search(period)
            if not m:
                # Shouldn't happen given the scan, but don't silently drop data
                raise ValueError(f"Unrecognised Period value {period!r} in {fpath}")
            month_name, cal_year = m.group(1).title(), int(m.group(2))

            rec = {
                "financial_year": financial_year,
                "month": month_name,
                "calendar_year": cal_year,
                "org_code": org_code,
                "parent_org": (rec_raw.get("Parent Org") or "").strip(),
                "org_name": (rec_raw.get("Org name") or "").strip(),
            }

            # Initialise every canonical numeric field to None first. This matters for
            # eras that genuinely lack a field (e.g. booked-appointment columns before
            # Aug 2020) so those stay None rather than being skipped entirely.
            for canonical in COLUMN_MAP:
                rec[canonical] = None

            # Only walk columns this file's OWN header actually has. Looping over every
            # era's synonym list here (rather than this file's real columns) was the bug:
            # a later synonym absent from this era would overwrite a value the earlier,
            # correct synonym had already set for the same canonical field.
            for raw_name in header:
                canonical = RAW_TO_CANONICAL.get(raw_name)
                if canonical is None:
                    continue
                val = rec_raw.get(raw_name)
                if val is not None and val.strip() != "":
                    rec[canonical] = int(val.strip())

            records.append(rec)

    return records, skipped_non_trust, skipped_total_row


def build_panel():
    """Walk all raw files and build the full long-format panel."""
    all_records = []
    file_log = []
    total_skipped_non_trust = 0
    total_skipped_total_row = 0

    for financial_year in sorted(os.listdir(RAW_ROOT)):
        ydir = os.path.join(RAW_ROOT, financial_year)
        if not os.path.isdir(ydir):
            continue
        for fname in sorted(os.listdir(ydir)):
            if not fname.lower().endswith(".csv"):
                continue
            fpath = os.path.join(ydir, fname)
            records, skipped_non_trust, skipped_total_row = read_file(fpath, financial_year)
            all_records.extend(records)
            total_skipped_non_trust += skipped_non_trust
            total_skipped_total_row += skipped_total_row
            file_log.append(
                {
                    "financial_year": financial_year,
                    "file": fname,
                    "trust_rows": len(records),
                    "non_trust_rows_dropped": skipped_non_trust,
                    "total_rows_dropped": skipped_total_row,
                }
            )

    return all_records, file_log, total_skipped_non_trust, total_skipped_total_row


if __name__ == "__main__":
    records, file_log, n_non_trust, n_total = build_panel()
    print(f"Built panel with {len(records)} Trust-month rows from {len(file_log)} files")
    print(f"Dropped {n_non_trust} non-Trust provider rows (UCCs/health centres, 5-6 char codes)")
    print(f"Dropped {n_total} aggregate TOTAL rows")
