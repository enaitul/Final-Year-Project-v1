#!/usr/bin/env python3
"""Run the MySQL CSV suite sequentially, or one independent group by CLI."""
import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import mysql.connector
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_CONFIG = {"host": "localhost", "user": "ai_tester", "password": "AiTester@123", "database": "ai_testing_test"}
CSV_FILE = PROJECT_ROOT / "test_cases" / "300testcases.csv"
REPORT_DIR = PROJECT_ROOT / "reports"


def log(message, prefix=""):
    print(f"{prefix}{message}")


def connect_database(prefix=""):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            log("Connected to MySQL", prefix)
            return connection
    except mysql.connector.Error as error:
        log(f"MySQL connection failed: {error}", prefix)
    return None


def load_test_cases(csv_file=CSV_FILE, prefix=""):
    try:
        cases = pd.read_csv(csv_file)
        log(f"Loaded {len(cases)} test cases from {csv_file}", prefix)
        return cases
    except Exception as error:
        log(f"Could not load CSV file {csv_file}: {error}", prefix)
        return None


def determine_expected_status(row):
    """Keep the project's original positive/negative/edge decision rules."""
    test_type = str(row["Test_Type"]).strip().lower()
    expected_result = str(row["Expected_Result"]).strip().lower()
    expected_error = str(row["Expected_Error"]).strip().lower()
    success_phrases = ("no error", "without error", "success", "successful", "succeeds", "executed successfully", "warning is issued", "warning only", "database left unchanged", "empty result set", "0 rows", "zero rows", "returns null")
    if any(phrase in expected_result for phrase in success_phrases):
        return "SUCCESS_EXPECTED"
    error_phrases = ("should fail", "expected error", "error should be raised", "error is raised", "must fail", "rejected", "invalid operation", "not allowed", "cannot be executed", "violation should occur")
    if any(phrase in expected_result for phrase in error_phrases):
        return "ERROR_EXPECTED"
    valid_error = expected_error and expected_error not in {"none", "nan", "none (warning only)", ""}
    if valid_error and any(word in expected_error for word in ("error", "exception", "violation", "denied", "rejected")):
        return "ERROR_EXPECTED"
    return "ERROR_EXPECTED" if test_type == "negative" else "SUCCESS_EXPECTED"


def extract_setup_sql(preconditions):
    """Extract setup between Setup: and the beginner-facing instruction text."""
    match = re.search(r"\bsetup:\s*(.*?)(?=\s+(?:execute this test|use the shared project database)\b|\s+cleanup:|$)", str(preconditions or ""), re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def split_setup_statements(setup_sql):
    """Split semicolon statements, while retaining procedure/trigger BEGIN...END blocks."""
    pieces, buffer, quote, escaped = [], [], None, False
    for character in setup_sql:
        if quote:
            buffer.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"'", '"', '`'}:
            quote, buffer = character, buffer + [character]
        elif character == ";":
            statement = "".join(buffer).strip()
            if statement:
                pieces.append(statement)
            buffer = []
        else:
            buffer.append(character)
    if "".join(buffer).strip():
        pieces.append("".join(buffer).strip())
    statements, compound = [], None
    for piece in pieces:
        if compound is not None:
            compound += "; " + piece
            if re.search(r"\bEND\s*$", piece, re.IGNORECASE):
                statements.append(compound)
                compound = None
        elif re.match(r"\s*CREATE\s+(PROCEDURE|TRIGGER)\b", piece, re.IGNORECASE) and not re.search(r"\bEND\s*$", piece, re.IGNORECASE):
            compound = piece
        else:
            statements.append(piece)
    return statements + ([compound] if compound else [])


def run_setup(cursor, connection, row):
    statements = split_setup_statements(extract_setup_sql(row.get("Preconditions", "")))
    sql_start = re.compile(r"^\s*(ALTER|BEGIN|CALL|COMMIT|CREATE|DELETE|DROP|EXPLAIN|INSERT|RENAME|ROLLBACK|SAVEPOINT|SET|START|TRUNCATE|UPDATE|USE)\b", re.IGNORECASE)
    statements = [statement for statement in statements if sql_start.match(statement)]
    open_transaction = False
    for statement in statements:
        # Make fixture setup idempotent when supplied cases reuse an email address.
        if re.match(r"^\s*INSERT\s+INTO\s+employees\b", statement, re.IGNORECASE):
            for email in re.findall(r"'([^']+@[^']+)'", statement):
                cursor.execute("DELETE FROM employee_projects WHERE emp_id IN (SELECT emp_id FROM employees WHERE email = %s)", (email,))
                cursor.execute("DELETE FROM employees WHERE email = %s", (email,))
        if re.match(r"^\s*INSERT\s+INTO\s+departments\b", statement, re.IGNORECASE):
            statement = re.sub(r"(\(\s*(\d+)\s*,\s*')([^']+)(')", lambda item: f"{item.group(1)}{item.group(3)}_{item.group(2)}{item.group(4)}", statement)
        if re.match(r"^\s*DELETE\s+FROM\s+projects\s+WHERE\s+project_id\b", statement, re.IGNORECASE):
            cursor.execute(re.sub(r"^\s*DELETE\s+FROM\s+projects", "DELETE FROM employee_projects", statement, flags=re.IGNORECASE))
        cursor.execute(statement)
        if cursor.with_rows:
            cursor.fetchall()
        if re.match(r"\s*(START\s+TRANSACTION|BEGIN)\b", statement, re.IGNORECASE):
            open_transaction = True
    if statements and not open_transaction:
        connection.commit()


def format_query_result(cursor, rows):
    if not rows:
        return "Rows returned: 0\n(No rows returned)"
    headers = [str(column[0]) for column in cursor.description]
    values = [["NULL" if value is None else str(value).replace("\n", "\\n").replace("\r", "\\r") for value in row] for row in rows]
    widths = [max(len(headers[index]), *(len(row[index]) for row in values)) for index in range(len(headers))]
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    def line(items):
        return "|" + "|".join(f" {value:<{widths[index]}} " for index, value in enumerate(items)) + "|"
    return "\n".join([f"Rows returned: {len(rows)}", border, line(headers), border, *(line(row) for row in values), border])


def execute_test(connection, row, prefix=""):
    started = time.perf_counter()
    result = {"Test_Case_ID": str(row["Test_Case_ID"]), "Feature_ID": str(row["Feature_ID"]), "Feature_Name": str(row["Feature_Name"]), "Test_Type": str(row["Test_Type"]), "Test_Description": str(row.get("Test_Description", "")).strip(), "SQL_Query": str(row["SQL_Query"]).strip(), "Expected_Result": str(row["Expected_Result"]).strip(), "Expected_Error": str(row["Expected_Error"]).strip(), "Actual_Result": "", "Actual_Error": "", "Status": "FAIL", "Executed_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Execution_Time": 0.0}
    cursor = None
    try:
        if not result["SQL_Query"] or result["SQL_Query"].lower() == "nan":
            result["Actual_Error"] = "SQL query is empty"
            return result
        cursor = connection.cursor()
        cursor.execute(f"USE `{DB_CONFIG['database']}`")
        cursor.execute("SET SQL_SAFE_UPDATES = 0")
        run_setup(cursor, connection, row)
        log(f"Running {result['Test_Case_ID']} | {result['Feature_ID']} | {result['Test_Type']}", prefix)
        expected = determine_expected_status(row)
        cursor.execute(result["SQL_Query"])
        if cursor.with_rows:
            result["Actual_Result"] = format_query_result(cursor, cursor.fetchall())
        else:
            result["Actual_Result"] = f"Query executed successfully. Rows affected: {cursor.rowcount}"
        if expected == "ERROR_EXPECTED":
            result["Actual_Error"] = "Expected SQL error, but query executed successfully."
            connection.rollback()
        else:
            connection.commit()
            result["Status"] = "PASS"
    except mysql.connector.Error as error:
        result["Actual_Error"] = str(error)
        if determine_expected_status(row) == "ERROR_EXPECTED":
            result["Status"] = "PASS"
        try:
            connection.rollback()
        except mysql.connector.Error:
            pass
    except Exception as error:
        result["Actual_Error"] = str(error)
        try:
            connection.rollback()
        except mysql.connector.Error:
            pass
    finally:
        result["Execution_Time"] = time.perf_counter() - started
        if cursor:
            cursor.close()
    return result


def get_next_response_file(report_dir):
    report_dir.mkdir(parents=True, exist_ok=True)
    indices = [int(match.group(1)) for path in report_dir.glob("response_*.txt") if (match := re.match(r"response_(\d+)\.txt$", path.name))]
    return report_dir / f"response_{max(indices, default=0) + 1}.txt"


def write_response(results, response_file):
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with response_file.open("w", encoding="utf-8", newline="\n") as file:
        for result in results:
            response = result["Actual_Result"] or result["Actual_Error"]
            file.write("=" * 70 + "\n")
            file.write(f"Test Case ID: {result['Test_Case_ID']}\nTest Type: {result['Test_Type']}\nTest Description: {result['Test_Description']}\nExecution Status: {result['Status']}\nQuery Executed: {result['SQL_Query']}\nDatabase Response: {response}\nQuery Execution Time: {result['Execution_Time']:.6f} seconds\n")
            file.write("=" * 70 + "\n\n")
    return response_file


def print_summary(results, prefix=""):
    total = len(results)
    passed = sum(item["Status"] == "PASS" for item in results)
    log(f"Summary: {passed}/{total} passed; {total - passed} failed; {(passed / total * 100) if total else 0:.2f}% pass rate", prefix)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the MySQL automated test suite.")
    parser.add_argument("--group", type=int, choices=range(1, 5), help="Run group 1, 2, 3, or 4.")
    parser.add_argument("--db-name", help="Database name to connect to.")
    parser.add_argument("--response-out", type=Path, help="Response TXT output path.")
    parser.add_argument("--csv", type=Path, help="Override the input CSV path.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    group_mode = args.group is not None
    prefix = f"[group{args.group}] " if group_mode else ""
    if args.db_name:
        DB_CONFIG["database"] = args.db_name
    csv_file = args.csv or (PROJECT_ROOT / "test_cases" / f"group{args.group}.csv" if group_mode else CSV_FILE)
    response_file = args.response_out or (REPORT_DIR / f"response_group{args.group}.txt" if group_mode else get_next_response_file(REPORT_DIR))
    if not csv_file.is_absolute():
        csv_file = PROJECT_ROOT / csv_file
    if not response_file.is_absolute():
        response_file = PROJECT_ROOT / response_file
    log("AI MYSQL AUTOMATED TESTING", prefix)
    cases = load_test_cases(csv_file, prefix)
    if cases is None:
        return 1
    connection = connect_database(prefix)
    if connection is None:
        return 1
    try:
        results = [execute_test(connection, row, prefix) for _, row in cases.iterrows()]
    finally:
        connection.close()
    write_response(results, response_file)
    print_summary(results, prefix)
    log(f"Response file saved: {response_file}", prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
