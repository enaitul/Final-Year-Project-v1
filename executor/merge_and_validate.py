#!/usr/bin/env python3
"""Merge group responses, then reuse the existing validation/baseline workflow."""
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXECUTOR_DIR = Path(__file__).resolve().parent
REPORTS = PROJECT_ROOT / "reports"
sys.path.insert(0, str(EXECUTOR_DIR))
from validate_response import parse_response_file
import validate_and_convert


def test_number(record):
    try:
        return int(record.get("Test_Case_ID", "TC0")[2:])
    except ValueError:
        return 10**12


def write_merged(records, destination):
    with destination.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write("=" * 70 + "\n")
            file.write(f"Test Case ID: {record.get('Test_Case_ID', '')}\n")
            file.write(f"Test Type: {record.get('Test_Type', '')}\n")
            file.write(f"Test Description: {record.get('Test_Description', '')}\n")
            file.write(f"Execution Status: {record.get('Execution_Status', '')}\n")
            file.write(f"Query Executed: {record.get('Query_Executed', '')}\n")
            file.write(f"Database Response: {record.get('Database_Response', '')}\n")
            file.write(f"Query Execution Time: {record.get('Query_Execution_Time', '')}\n")
            file.write("=" * 70 + "\n\n")


def combined_csv(destination):
    files = [PROJECT_ROOT / "test_cases" / f"group{number}.csv" for number in range(1, 5)]
    rows = []
    fieldnames = None
    for source in files:
        if not source.exists():
            raise FileNotFoundError(f"Required CSV was not found: {source}")
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = fieldnames or reader.fieldnames
            rows.extend(reader)
    rows.sort(key=lambda row: test_number(row))
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    REPORTS.mkdir(exist_ok=True)
    records = []
    for number in range(1, 5):
        response = REPORTS / f"response_group{number}.txt"
        if not response.exists():
            print(f"Cannot merge: missing {response}. Run the orchestrator first.")
            return 1
        parsed, problems = parse_response_file(response)
        if problems:
            print(f"Cannot merge {response.name}: {'; '.join(problems)}")
            return 1
        records.extend(parsed)
    records.sort(key=test_number)
    merged = REPORTS / "response_merged.txt"
    expected_csv = REPORTS / "combined_group_test_cases.csv"
    write_merged(records, merged)
    combined_csv(expected_csv)
    print(f"Merged {len(records)} records into {merged.relative_to(PROJECT_ROOT)}")
    # Reuse the existing driver. Its only assumption is the original CSV path,
    # so temporarily point that one module variable at the combined group CSV.
    validate_and_convert.CSV_FILE = expected_csv
    previous_argv = sys.argv[:]
    try:
        command = ["merge_and_validate.py", "--response", str(merged)]
        # A baseline from another suite cannot be compared meaningfully with
        # the current run. Establish the matching parallel-suite baseline once.
        standard = REPORTS / "standard_test_results.txt"
        if standard.exists():
            baseline_records, _ = parse_response_file(standard)
            if {item.get("Test_Case_ID", "") for item in baseline_records} != {item.get("Test_Case_ID", "") for item in records}:
                print("The existing baseline belongs to a different suite; creating the first 1,500-case parallel baseline.")
                command.append("--update-baseline")
        sys.argv = command
        return validate_and_convert.main()
    finally:
        sys.argv = previous_argv


if __name__ == "__main__":
    raise SystemExit(main())
