#!/usr/bin/env python3
"""Selective execution: run chosen test cases / features and report PASS/FAIL.

Place at: Final-Year-Project-v1/executor/selective_runner.py
Reuses the execution logic in test_runner.py (no changes needed there).

Examples (run from project root):
  python executor/selective_runner.py --list
  python executor/selective_runner.py --feature F025
  python executor/selective_runner.py --feature F001 F002 --type Negative
  python executor/selective_runner.py --test-id TC373 TC374 TC375
  python executor/selective_runner.py --feature-name employee --show FAIL
"""
import argparse
import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import test_runner as tr   # works because this file is in the same executor/ folder

ROOT = tr.PROJECT_ROOT
REPORTS = tr.REPORT_DIR
DEFAULT_CSV = ROOT / "master_test_cases_fixed.csv"


def parse_args():
    p = argparse.ArgumentParser(description="Run selected test cases and report PASS/FAIL.")
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Test case CSV (default: master_test_cases_fixed.csv)")
    p.add_argument("--db-name", default="ai_testing_group1", help="Database to run against")
    p.add_argument("--feature", nargs="+", help="Feature_ID(s), e.g. F001 F025")
    p.add_argument("--feature-name", help="Substring of Feature_Name (case-insensitive)")
    p.add_argument("--test-id", nargs="+", help="Test_Case_ID(s), e.g. TC373 TC374")
    p.add_argument("--type", nargs="+", help="Test_Type(s), e.g. Positive Negative Edge")
    p.add_argument("--limit", type=int, help="Run only the first N matching cases")
    p.add_argument("--show", choices=["ALL", "PASS", "FAIL"], default="ALL",
                   help="Which results to print in the table (default ALL)")
    p.add_argument("--reset", action="store_true", help="Recreate fresh group databases before running")
    p.add_argument("--list", action="store_true", help="List available features and exit")
    return p.parse_args()


def norm(series):
    return series.astype(str).str.strip().str.lower()


def apply_filters(df, a):
    if a.feature:
        df = df[norm(df["Feature_ID"]).isin({x.strip().lower() for x in a.feature})]
    if a.feature_name:
        df = df[df["Feature_Name"].astype(str).str.contains(a.feature_name, case=False, na=False)]
    if a.test_id:
        df = df[norm(df["Test_Case_ID"]).isin({x.strip().lower() for x in a.test_id})]
    if a.type:
        df = df[norm(df["Test_Type"]).isin({x.strip().lower() for x in a.type})]
    if a.limit:
        df = df.head(a.limit)
    return df


def list_features(df):
    print(f"{len(df)} test cases in total\n")
    print(f"{'Feature_ID':<11} {'Feature_Name':<35} {'Cases':>5}  Types")
    print("-" * 75)
    for fid, grp in df.groupby("Feature_ID", sort=True):
        types = ", ".join(f"{t}:{n}" for t, n in grp["Test_Type"].value_counts().items())
        print(f"{str(fid):<11} {str(grp['Feature_Name'].iloc[0]):<35} {len(grp):>5}  {types}")


def main():
    a = parse_args()
    csv_path = a.csv if a.csv.is_absolute() else ROOT / a.csv
    df = tr.load_test_cases(csv_path)
    if df is None:
        return 1

    if a.list:
        list_features(df)
        return 0

    selected = apply_filters(df, a)
    if selected.empty:
        print("No test cases match those filters. Use --list to see available features.")
        return 1
    print(f"Selected {len(selected)} of {len(df)} test cases.")

    if a.reset:
        print("Resetting databases...")
        r = subprocess.run([sys.executable, str(ROOT / "executor" / "setup_group_databases.py")],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            return 1

    tr.DB_CONFIG["database"] = a.db_name
    connection = tr.connect_database()
    if connection is None:
        return 1
    try:
        results = [tr.execute_test(connection, row) for _, row in selected.iterrows()]
    finally:
        connection.close()

    # ---- pass/fail table ----
    print("\nTest_Case_ID  Feature  Type      Status  Time(s)")
    print("-" * 52)
    for r in results:
        if a.show != "ALL" and r["Status"] != a.show:
            continue
        print(f"{r['Test_Case_ID']:<13} {r['Feature_ID']:<8} {r['Test_Type']:<9} "
              f"{r['Status']:<7} {r['Execution_Time']:.4f}")
        if r["Status"] == "FAIL":
            reason = r["Actual_Error"] or "Unexpected result"
            print(f"    reason: {reason[:120]}")

    # ---- summary ----
    per_feature = defaultdict(lambda: [0, 0])
    for r in results:
        per_feature[r["Feature_ID"]][0 if r["Status"] == "PASS" else 1] += 1
    passed = sum(v[0] for v in per_feature.values())
    failed = sum(v[1] for v in per_feature.values())
    print("\nPer-feature summary")
    for fid, (p, f) in sorted(per_feature.items()):
        print(f"  {fid:<8} pass {p:<4} fail {f:<4}")
    print(f"\nTOTAL: {passed}/{len(results)} passed, {failed} failed "
          f"({passed / len(results) * 100:.2f}% pass rate)")

    # ---- save outputs ----
    REPORTS.mkdir(exist_ok=True)
    out_csv = REPORTS / "selective_results.csv"
    fields = ["Test_Case_ID", "Feature_ID", "Feature_Name", "Test_Type", "Status",
              "Execution_Time", "Actual_Error", "SQL_Query"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    tr.write_response(results, REPORTS / "response_selective.txt")
    print(f"\nSaved: {out_csv.relative_to(ROOT)} and reports/response_selective.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())