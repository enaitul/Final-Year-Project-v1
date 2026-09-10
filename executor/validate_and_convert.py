#!/usr/bin/env python3
"""Validate response files and compare against the standard baseline file."""

import argparse
import csv
import textwrap
from pathlib import Path

from validate_response import (
    REQUIRED_FIELDS,
    find_latest_response,
    validate_response,
    compare_with_standard_baseline,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
CSV_FILE = PROJECT_ROOT / "test_cases" / "300testcases.csv"
STANDARD_FILE = REPORTS_DIR / "standard_test_results.txt"


def write_validation_report(path, response_file, summary, comparison=None):
    """Write comprehensive validation report with minute checks and baseline comparison."""
    lines = [
        "========================================",
        "RESPONSE FILE VALIDATION & REGRESSION REPORT",
        "========================================",
        "",
        f"Response file checked: {response_file}",
    ]

    if comparison and comparison.get("has_baseline"):
        lines.append(f"Standard baseline compared against: {STANDARD_FILE}")

    lines.extend([
        f"Total test cases found: {summary['total']}",
        f"Valid test cases: {summary['valid']}",
        f"Invalid test cases: {summary['invalid']}",
        f"Duplicate test cases: {summary['duplicates']}",
        f"Missing test cases: {len(summary['missing'])}",
        f"Unexpected test cases: {len(summary['unexpected'])}",
        "",
        f"Minute Validation Status: {'PASS' if summary['is_valid'] else 'FAIL'}",
    ])

    if comparison and comparison.get("has_baseline"):
        matched = comparison["matched_count"]
        total = comparison["total_current"]
        lines.extend([
            "",
            "----------------------------------------",
            "COMPARISON WITH STANDARD BASELINE",
            "----------------------------------------",
            f"Baseline match rate: {matched} / {total} ({(matched/total*100) if total else 0:.2f}%)",
            f"Regressions detected: {len(comparison['regressions'])}",
            f"Output discrepancies detected: {len(comparison['discrepancies'])}",
            f"Baseline Consistency Verdict: {'PASS' if comparison['is_match'] else 'FAIL'}",
        ])

        if comparison["regressions"]:
            lines.append("\nRegressions (tests that passed in baseline but failed in this run):")
            lines.extend(f"  - {reg}" for reg in comparison["regressions"])

        if comparison["discrepancies"]:
            lines.append("\nDiscrepancies against standard baseline:")
            lines.extend(f"  - {disc}" for disc in comparison["discrepancies"])

    overall_pass = summary["is_valid"] and (not comparison or not comparison.get("has_baseline") or comparison["is_match"])
    lines.extend([
        "",
        f"Overall Run Verdict: {'PASS' if overall_pass else 'FAIL'}",
        "",
        "Validation Problems Found:",
    ])
    lines.extend(summary["problems"] or ["No validation problems found."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_csv_expected_map(csv_file):
    """Load expected results, errors, and feature details keyed by Test_Case_ID."""
    expected_map = {}
    if not csv_file.exists():
        return expected_map
    with csv_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            tid = str(row.get("Test_Case_ID", "")).strip()
            if tid:
                expected_map[tid] = row
    return expected_map


def build_side_by_side(expected_text, actual_text, left_width=48, min_right_width=52):
    """Format expected output and actual database output side by side in an aligned table."""
    def split_to_lines(text, width):
        out = []
        for raw_line in str(text or "").splitlines():
            raw_line = raw_line.rstrip()
            if not raw_line:
                out.append("")
            elif len(raw_line) <= width or raw_line.startswith("+") or raw_line.startswith("|"):
                out.append(raw_line)
            else:
                wrapped = textwrap.wrap(raw_line, width=width)
                out.extend(wrapped if wrapped else [""])
        return out or [""]

    actual_lines_raw = str(actual_text or "").splitlines()
    max_act = max((len(l.rstrip()) for l in actual_lines_raw), default=0)
    right_width = max(min_right_width, min(max_act, 80))

    left_lines = split_to_lines(expected_text, left_width)
    right_lines = split_to_lines(actual_text, right_width)

    max_rows = max(len(left_lines), len(right_lines))
    left_lines += [""] * (max_rows - len(left_lines))
    right_lines += [""] * (max_rows - len(right_lines))

    border = "+" + "-" * (left_width + 2) + "+" + "-" * (right_width + 2) + "+"
    hdr_exp = "EXPECTED OUTPUT"
    hdr_act = "DATABASE OUTPUT (ACTUAL)"
    header = f"| {hdr_exp:<{left_width}} | {hdr_act:<{right_width}} |"

    rows = [border, header, border]
    for l, r in zip(left_lines, right_lines):
        rows.append(f"| {l:<{left_width}} | {r:<{right_width}} |")
    rows.append(border)
    return "\n".join(rows)


def write_standard_results(records, csv_file):
    """Write standard test results with header metadata and side-by-side comparison."""
    expected_map = load_csv_expected_map(csv_file)
    text_path = STANDARD_FILE
    blocks = []

    for record in records:
        test_id = record.get("Test_Case_ID", "").strip()
        csv_meta = expected_map.get(test_id, {})

        feature_id = csv_meta.get("Feature_ID", "")
        feature_name = csv_meta.get("Feature_Name", "")
        feature_display = f"{feature_id} — {feature_name}" if feature_id and feature_name else (feature_name or feature_id)

        exp_res = str(csv_meta.get("Expected_Result", "")).strip()
        exp_err = str(csv_meta.get("Expected_Error", "")).strip()

        has_valid_error = (
            exp_err
            and exp_err.lower() not in {"nan", "none", "none (warning only)", ""}
        )

        if has_valid_error:
            expected_output = f"Expected Result: {exp_res}\nExpected Error: {exp_err}"
        else:
            expected_output = exp_res or "Execution without error"

        actual_output = record.get("Database_Response", "").strip()
        comparison_box = build_side_by_side(expected_output, actual_output)

        block_lines = [
            f"Test Case ID: {test_id}",
        ]
        if feature_display:
            block_lines.append(f"Feature: {feature_display}")
        block_lines.extend([
            f"Test Type: {record.get('Test_Type', csv_meta.get('Test_Type', ''))}",
            f"Execution Status: {record.get('Execution_Status', '')}",
            f"Query Executed: {record.get('Query_Executed', '')}",
            f"Database Response: {actual_output}",
            f"Query Execution Time: {record.get('Query_Execution_Time', '')}",
            "",
            "OUTPUT COMPARISON:",
            comparison_box,
        ])
        blocks.append("\n".join(block_lines))

    separator = "\n" + "=" * 70 + "\n\n"
    text_path.write_text(separator.join(blocks) + "\n", encoding="utf-8")
    return text_path


def write_explanation(path):
    path.write_text("""========================================
HOW RESPONSE VALIDATION & BASELINE COMPARISON WORKS
========================================

1. Sequential Response Files
   Every test execution automatically generates a sequentially numbered
   response file in reports/:
   - First run  -> reports/response_1.txt
   - Second run -> reports/response_2.txt
   - Third run  -> reports/response_3.txt, and so forth.
   This makes it immediately obvious which run is the latest.

2. Minute Validation
   The validation system meticulously inspects the response file:
   - Validates Test Case ID formatting (TCxxx)
   - Confirms Test Type matches positive/negative/edge expectations
   - Ensures execution status is valid (PASS/FAIL)
   - Verifies SQL query executed and execution times
   - Guarantees 100% test coverage against 300testcases.csv (no duplicates, no missing)

3. Phase 1: First Run (Baseline Establishment)
   On the initial run (when no standard file exists):
   - The response file is minutely validated.
   - If correct and passing, it is saved into the standard baseline:
     reports/standard_test_results.txt
   - Each test case displays the Expected Output and the Actual Database
     Output side by side in an aligned comparison box.

4. Phase 2: Future Runs (Regression & Output Comparison)
   On all future test runs:
   - The new response file is minutely validated.
   - It is compared test-by-test against reports/standard_test_results.txt.
   - It verifies:
     a) Status consistency: Detects if any test case regressed from PASS to FAIL.
     b) Output consistency: Compares database response against the standard output.
   - Any discrepancies or regressions are highlighted in reports/response_validation_report.txt.

5. Workflow Diagram

Run Test Runner
↓
Generates response_N.txt (sequential: response_1, response_2...)
↓
Validate Response Minutely
↓
Is standard_test_results.txt present?
  ├─ NO (First Run) ──> Store validated results as standard_test_results.txt
  │                    (With Side-by-Side Expected vs Actual Comparison)
  │
  └─ YES (Future Run) ─> Compare response_N.txt against standard_test_results.txt
                       Detect regressions & discrepancies
                       Generate Validation & Comparison Report
""", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Validate a MySQL response file and compare against standard baseline.")
    parser.add_argument("--response", type=Path, help="Optional path to a specific response TXT file.")
    parser.add_argument("--update-baseline", action="store_true", help="Force updating the standard baseline file.")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(exist_ok=True)
    response_file = args.response.resolve() if args.response else find_latest_response(REPORTS_DIR)
    if response_file is None:
        print("No response_*.txt file was found in reports.")
        return 1

    records, summary = validate_response(response_file, CSV_FILE)
    report_path = REPORTS_DIR / "response_validation_report.txt"
    explanation_path = REPORTS_DIR / "how_response_validation_works.txt"

    standard_exists = STANDARD_FILE.exists()
    comparison = None

    if standard_exists and not args.update_baseline:
        comparison = compare_with_standard_baseline(records, STANDARD_FILE)

    write_validation_report(report_path, response_file, summary, comparison)
    write_explanation(explanation_path)

    print("========================================")
    print("RESPONSE VALIDATION & BASELINE CHECK")
    print("========================================")
    print(f"Response file: {response_file.resolve().relative_to(PROJECT_ROOT.resolve())}")
    print(f"Total test cases: {summary['total']}")
    print(f"Valid: {summary['valid']}")
    print(f"Invalid: {summary['invalid']}")
    print(f"Minute Validation: {'PASS' if summary['is_valid'] else 'FAIL'}")

    if not standard_exists or args.update_baseline:
        if summary["is_valid"]:
            text_path = write_standard_results(records, CSV_FILE)
            mode_msg = "Updated" if args.update_baseline else "Established initial"
            print(f"{mode_msg} standard baseline: {text_path.resolve().relative_to(PROJECT_ROOT.resolve())}")
        else:
            print("Standard baseline was not created because minute validation failed.")
    else:
        matched = comparison["matched_count"]
        total = comparison["total_current"]
        print("----------------------------------------")
        print(f"Compared against standard baseline: {STANDARD_FILE.resolve().relative_to(PROJECT_ROOT.resolve())}")
        print(f"Baseline Match: {matched}/{total} ({(matched/total*100) if total else 0:.1f}%)")
        print(f"Regressions: {len(comparison['regressions'])}")
        print(f"Discrepancies: {len(comparison['discrepancies'])}")
        verdict = "PASS" if comparison["is_match"] and summary["is_valid"] else "FAIL"
        print(f"Baseline Consistency: {verdict}")

    print(f"Validation report saved: {report_path.resolve().relative_to(PROJECT_ROOT.resolve())}")
    print("========================================")
    
    overall_ok = summary["is_valid"] and (not comparison or comparison["is_match"])
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
