#!/usr/bin/env python3
"""Validate a saved MySQL response TXT file and compare with standard baseline without executing SQL."""

import csv
import re
from collections import Counter
from pathlib import Path


REQUIRED_FIELDS = (
    "Test_Case_ID",
    "Test_Type",
    "Execution_Status",
    "Query_Executed",
    "Database_Response",
    "Query_Execution_Time",
)

LABELS = {
    "Test Case ID:": "Test_Case_ID",
    "Test Type:": "Test_Type",
    "Test Case Type:": "Test_Type",
    "Test Description:": "Test_Description",
    "Execution Status:": "Execution_Status",
    "Query Executed:": "Query_Executed",
    "Database Response:": "Database_Response",
    "Query Execution Time:": "Query_Execution_Time",
}


def find_latest_response(report_directory):
    """Return the response_N.txt file with the highest sequence number (or newest legacy response)."""
    indexed_files = []
    legacy_files = []
    for f in report_directory.glob("response_*.txt"):
        m = re.match(r"^response_(\d+)\.txt$", f.name)
        if m:
            indexed_files.append((int(m.group(1)), f))
        elif re.match(r"^response_\d{8}_\d{6}\.txt$", f.name):
            legacy_files.append(f)

    if indexed_files:
        indexed_files.sort(key=lambda item: item[0])
        return indexed_files[-1][1]
    if legacy_files:
        legacy_files.sort()
        return legacy_files[-1]
    return None


def read_expected_cases(csv_file):
    """Read full test cases metadata and IDs from the original CSV."""
    if not csv_file.exists():
        return {}, [f"Original CSV file was not found: {csv_file}"]

    try:
        with csv_file.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "Test_Case_ID" not in reader.fieldnames:
                return {}, ["Original CSV does not contain a Test_Case_ID column."]
            cases_map = {}
            for row in reader:
                tid = str(row.get("Test_Case_ID", "")).strip()
                if tid:
                    cases_map[tid] = row
            return cases_map, []
    except (OSError, csv.Error) as error:
        return {}, [f"Could not read original CSV: {error}"]


def read_expected_ids(csv_file):
    """Read test IDs from the original CSV using only the standard library."""
    cases_map, problems = read_expected_cases(csv_file)
    return list(cases_map.keys()), problems


def parse_response_file(response_file):
    """Parse the project's labeled TXT format, keeping multi-line values intact."""
    try:
        lines = response_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [], [f"Could not read response file: {error}"]

    records = []
    file_problems = []
    current = None
    current_field = None

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Lines of only '=' separate records in the actual generated file.
        if stripped and set(stripped) == {"="}:
            if current is not None:
                records.append(current)
                current = None
                current_field = None
            continue

        matched_label = next((label for label in LABELS if stripped.startswith(label)), None)
        if matched_label:
            if current is None:
                current = {"_line": line_number}
            field_name = LABELS[matched_label]
            # A repeated ID label starts a new record even when a separator is absent.
            if field_name == "Test_Case_ID" and "Test_Case_ID" in current:
                records.append(current)
                current = {"_line": line_number}
            current[field_name] = stripped[len(matched_label):].strip()
            current_field = field_name
        elif current is not None and current_field and stripped:
            # Tolerant of wrapped SQL or MySQL messages.
            # Stop if we hit an OUTPUT COMPARISON section banner
            if stripped == "OUTPUT COMPARISON:" or stripped.startswith("+---"):
                current_field = None
            else:
                previous = current.get(current_field, "")
                current[current_field] = (previous + "\n" + stripped).strip()
        elif stripped and not stripped.startswith("+") and not stripped.startswith("|") and stripped != "OUTPUT COMPARISON:":
            file_problems.append(f"Line {line_number} - Text outside a test case record: {stripped}")

    if current is not None:
        records.append(current)

    if not records:
        file_problems.append("No test case records were found in the response file.")
    return records, file_problems


def validate_records(records, expected_ids, csv_problems, expected_cases_map=None):
    """Validate fields, IDs, duplicates, types, query consistency, and CSV coverage."""
    problems = list(csv_problems)
    id_counts = Counter(record.get("Test_Case_ID", "").strip() for record in records)
    duplicate_ids = sorted(test_id for test_id, count in id_counts.items() if test_id and count > 1)
    invalid_indexes = set()

    for index, record in enumerate(records):
        test_id = record.get("Test_Case_ID", "").strip()
        name = test_id or f"Record {index + 1}"
        record_problems = []

        for field in REQUIRED_FIELDS:
            if not record.get(field, "").strip():
                record_problems.append(f"Missing {field.replace('_', ' ').lower()}")

        if test_id and not re.fullmatch(r"TC\d{3,}", test_id):
            record_problems.append("Invalid test case ID format")

        test_type_value = record.get("Test_Type", "").strip()
        if test_type_value and test_type_value.lower() not in {"positive", "negative", "edge"}:
            record_problems.append("Invalid test type (use Positive, Negative, or Edge)")

        if record.get("Execution_Status", "").strip().upper() not in {"PASS", "FAIL"}:
            record_problems.append("Invalid execution status (use PASS or FAIL)")

        time_value = record.get("Query_Execution_Time", "").strip()
        if time_value and not re.fullmatch(r"(?:\d+(?:\.\d+)?|\.\d+)(?:\s*(?:seconds?|secs?|s))?", time_value, re.IGNORECASE):
            record_problems.append("Invalid query execution time")

        if test_id and id_counts[test_id] > 1:
            record_problems.append("Duplicate test case")

        # Minute check: cross-reference with CSV expectations if available
        if expected_cases_map and test_id in expected_cases_map:
            csv_item = expected_cases_map[test_id]
            expected_type = str(csv_item.get("Test_Type", "")).strip()
            if test_type_value and expected_type and test_type_value.lower() != expected_type.lower():
                record_problems.append(f"Test type mismatch: got '{test_type_value}', expected '{expected_type}'")

            # Check query non-empty
            expected_sql = str(csv_item.get("SQL_Query", "")).strip()
            actual_sql = record.get("Query_Executed", "").strip()
            if actual_sql and expected_sql:
                norm_act = " ".join(actual_sql.split()).rstrip(";")
                norm_exp = " ".join(expected_sql.split()).rstrip(";")
                if norm_act != norm_exp:
                    record_problems.append("Query executed differs from expected CSV query")

        if record_problems:
            invalid_indexes.add(index)
            problems.extend(f"{name} - {problem}" for problem in record_problems)

    response_ids = {test_id for test_id in id_counts if test_id}
    expected_set = set(expected_ids)
    missing_ids = sorted(expected_set - response_ids)
    unexpected_ids = sorted(response_ids - expected_set) if expected_ids else []

    problems.extend(f"{test_id} - Missing test case" for test_id in missing_ids)
    problems.extend(f"{test_id} - Unexpected test case ID" for test_id in unexpected_ids)

    csv_duplicates = sorted(test_id for test_id, count in Counter(expected_ids).items() if test_id and count > 1)
    problems.extend(f"{test_id} - Duplicate ID in original CSV" for test_id in csv_duplicates)

    return {
        "total": len(records),
        "valid": len(records) - len(invalid_indexes),
        "invalid": len(invalid_indexes),
        "duplicates": len(duplicate_ids),
        "missing": missing_ids,
        "unexpected": unexpected_ids,
        "problems": problems,
        "is_valid": not problems,
    }


def compare_with_standard_baseline(current_records, standard_file):
    """
    Compare current response records minutely against the standard baseline file.
    Detects regressions (tests failing that previously passed) and output differences.
    """
    if not standard_file.exists():
        return {
            "has_baseline": False,
            "is_match": False,
            "regressions": [],
            "discrepancies": [],
            "matched_count": 0,
            "total_baseline": 0,
            "total_current": len(current_records),
        }

    baseline_records_list, _ = parse_response_file(standard_file)
    baseline_map = {
        r.get("Test_Case_ID", "").strip(): r
        for r in baseline_records_list
        if r.get("Test_Case_ID")
    }

    regressions = []
    discrepancies = []
    matched_count = 0

    for record in current_records:
        test_id = record.get("Test_Case_ID", "").strip()
        if not test_id:
            continue

        if test_id not in baseline_map:
            discrepancies.append(f"{test_id} - Test case not present in standard baseline.")
            continue

        base_rec = baseline_map[test_id]
        cur_status = record.get("Execution_Status", "").strip().upper()
        base_status = base_rec.get("Execution_Status", "").strip().upper()

        cur_resp = " ".join(record.get("Database_Response", "").split())
        base_resp = " ".join(base_rec.get("Database_Response", "").split())

        # Check for regressions
        if base_status == "PASS" and cur_status == "FAIL":
            regressions.append(
                f"{test_id} [REGRESSION]: Status changed from PASS to FAIL!\n"
                f"  Current error: {record.get('Database_Response', '')[:120]}"
            )
        elif base_status != cur_status:
            discrepancies.append(
                f"{test_id} [STATUS CHANGED]: Baseline status {base_status} -> Current status {cur_status}"
            )
        elif cur_resp != base_resp:
            discrepancies.append(
                f"{test_id} [OUTPUT DIFF]: Response differs from standard baseline.\n"
                f"  Baseline: {base_rec.get('Database_Response', '')[:80]}\n"
                f"  Current : {record.get('Database_Response', '')[:80]}"
            )
        else:
            matched_count += 1

    total = len(current_records)
    is_match = (len(regressions) == 0 and len(discrepancies) == 0 and matched_count == total)

    return {
        "has_baseline": True,
        "is_match": is_match,
        "regressions": regressions,
        "discrepancies": discrepancies,
        "matched_count": matched_count,
        "total_baseline": len(baseline_map),
        "total_current": total,
    }


def validate_response(response_file, csv_file):
    """Read and validate files, returning parsed records and a summary dictionary."""
    records, parse_problems = parse_response_file(response_file)
    cases_map, csv_problems = read_expected_cases(csv_file)
    expected_ids = list(cases_map.keys())
    summary = validate_records(records, expected_ids, csv_problems, expected_cases_map=cases_map)
    summary["problems"] = parse_problems + summary["problems"]
    summary["is_valid"] = not summary["problems"]
    return records, summary
