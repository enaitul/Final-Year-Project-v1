import mysql.connector
import pandas as pd
import os
import re
import sys
import time
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# MySQL Configuration
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "ai_tester",
    "password": "AiTester@123",
    "database": "ai_testing_test"
}

CSV_FILE = "test_cases/300testcases.csv"
REPORT_DIR = "reports"


# ============================================================
# Connect to MySQL
# ============================================================

def connect_database():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            print("✅ Connected to MySQL")
            return connection

    except mysql.connector.Error as error:
        print(f"❌ MySQL connection failed: {error}")

    return None


# ============================================================
# Load Test Cases
# ============================================================

def load_test_cases():
    try:
        df = pd.read_csv(CSV_FILE)

        print(f"✅ Loaded {len(df)} test cases")

        return df

    except Exception as error:
        print(f"❌ Failed to load CSV: {error}")

    return None


# ============================================================
# Determine What the Test Expects
# ============================================================

def determine_expected_status(row):
    """
    Determine whether the test is expected to succeed or raise an error.

    Important:
    Do NOT treat the word "error" alone as an indication that an error
    is expected. For example:
        "No error raised, a warning is issued"
    is clearly a SUCCESS expectation.
    """

    test_type = str(row["Test_Type"]).strip().lower()
    expected_result = str(row["Expected_Result"]).strip().lower()
    expected_error = str(row["Expected_Error"]).strip().lower()

    # Explicit success wording takes priority.
    success_phrases = [
        "no error",
        "without error",
        "success",
        "successful",
        "succeeds",
        "executed successfully",
        "warning is issued",
        "warning only",
        "database left unchanged",
        "empty result set",
        "0 rows",
        "zero rows",
        "returns null",
    ]

    if any(phrase in expected_result for phrase in success_phrases):
        return "SUCCESS_EXPECTED"

    # Only treat clearly negative wording as an expected SQL error.
    error_phrases = [
        "should fail",
        "expected error",
        "error should be raised",
        "error is raised",
        "must fail",
        "rejected",
        "invalid operation",
        "not allowed",
        "cannot be executed",
        "violation should occur",
    ]

    if any(phrase in expected_result for phrase in error_phrases):
        return "ERROR_EXPECTED"

    # Expected_Error can also explicitly indicate that an error is expected.
    # Ignore values such as "None", "None (warning only)", NaN, etc.
    valid_expected_error = (
        expected_error
        and expected_error not in {"none", "nan", "none (warning only)", ""}
    )

    if valid_expected_error and any(
        phrase in expected_error
        for phrase in ["error", "exception", "violation", "denied", "rejected"]
    ):
        return "ERROR_EXPECTED"

    # Most negative tests expect MySQL to reject their SQL. A few negative
    # cases intentionally use valid SQL that returns no rows; those were
    # handled by the explicit success phrases above.
    if test_type == "negative":
        return "ERROR_EXPECTED"

    # Default: if there is no clear indication of an expected error,
    # assume the SQL is expected to execute successfully.
    return "SUCCESS_EXPECTED"


# ============================================================
# CSV Setup / Fixture Support
# ============================================================

def extract_setup_sql(preconditions):
    """Get only SQL after ``Setup:`` from a CSV precondition cell.

    The CSV mixes setup SQL with beginner-friendly explanatory sentences.
    This extracts the part after ``Setup:`` and stops before the standard
    instruction beginning ``Execute this test`` (or before ``Cleanup:``).
    """
    text = str(preconditions or "")
    match = re.search(r"\bsetup:\s*(.*?)(?=\s+execute this test\b|\s+cleanup:|$)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def split_setup_statements(setup_sql):
    """Split fixture SQL while keeping BEGIN ... END routines intact."""
    pieces = []
    buffer = []
    quote = None
    escaped = False

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
            quote = character
            buffer.append(character)
        elif character == ";":
            statement = "".join(buffer).strip()
            if statement:
                pieces.append(statement)
            buffer = []
        else:
            buffer.append(character)

    final_statement = "".join(buffer).strip()
    if final_statement:
        pieces.append(final_statement)

    # Procedure and trigger bodies contain semicolons. Rejoin their pieces
    # until their final END keyword so mysql-connector receives one statement.
    statements = []
    compound = None
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

    if compound is not None:
        statements.append(compound)
    return statements


def run_setup(cursor, connection, row):
    """Run a test case's explicit Setup SQL and preserve transaction setups."""
    setup_sql = extract_setup_sql(row.get("Preconditions", ""))
    statements = split_setup_statements(setup_sql)

    # Ignore the plain-English notes that follow a semicolon in some CSV
    # cells, for example "(ensures a clean slate...)" or "none required".
    # Only explicitly recognised SQL commands may be run as test fixtures.
    sql_start = re.compile(
        r"^\s*(ALTER|BEGIN|CALL|COMMIT|CREATE|DELETE|DROP|EXPLAIN|INSERT|"
        r"RENAME|ROLLBACK|SAVEPOINT|SET|START|TRUNCATE|UPDATE|USE)\b",
        re.IGNORECASE,
    )
    statements = [statement for statement in statements if sql_start.match(statement)]
    has_open_transaction = False

    for statement in statements:
        cursor.execute(statement)
        if cursor.with_rows:
            cursor.fetchall()
        if re.match(r"\s*(START\s+TRANSACTION|BEGIN)\b", statement, re.IGNORECASE):
            has_open_transaction = True

    # Standard fixtures need to be committed so an expected-error rollback
    # does not remove the rows/tables that make the test meaningful.
    if statements and not has_open_transaction:
        connection.commit()


# ============================================================
# Format SELECT Results for the Response Report
# ============================================================

def format_query_result(cursor, rows):
    """Return query rows as a readable table with the real column names.

    ``fetchall()`` returns Python tuples such as ``[(1, 'Asha')]``. That
    preserves values but is hard to read in the response TXT file. MySQL
    supplies column names in ``cursor.description``; this makes a table from
    those same values without changing any database data.
    """
    if not rows:
        return "Rows returned: 0\n(No rows returned)"

    headers = [str(column[0]) for column in cursor.description]

    def display(value):
        if value is None:
            return "NULL"
        return str(value).replace("\n", "\\n").replace("\r", "\\r")

    table_rows = [[display(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in table_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def table_line(values):
        return "|" + "|".join(
            f" {value:<{widths[index]}} "
            for index, value in enumerate(values)
        ) + "|"

    return "\n".join([
        f"Rows returned: {len(rows)}",
        border,
        table_line(headers),
        border,
        *(table_line(row) for row in table_rows),
        border,
    ])


# ============================================================
# Execute One Test Case
# ============================================================

def execute_test(connection, row):
    start_time = time.perf_counter()

    test_id = str(row["Test_Case_ID"])
    feature_id = str(row["Feature_ID"])
    feature_name = str(row["Feature_Name"])
    test_type = str(row["Test_Type"])
    test_description = str(row.get("Test_Description", "")).strip()

    sql_query = str(row["SQL_Query"]).strip()
    expected_result = str(row["Expected_Result"]).strip()
    expected_error = str(row["Expected_Error"]).strip()

    result = {
        "Test_Case_ID": test_id,
        "Feature_ID": feature_id,
        "Feature_Name": feature_name,
        "Test_Type": test_type,
        "Test_Description": test_description,
        "SQL_Query": sql_query,
        "Expected_Result": expected_result,
        "Expected_Error": expected_error,
        "Actual_Result": "",
        "Actual_Error": "",
        "Status": "FAIL",
        "Executed_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Execution_Time": 0.0
    }

    cursor = None

    try:

        # ----------------------------------------------------
        # Validate SQL
        # ----------------------------------------------------

        if not sql_query or sql_query.lower() == "nan":

            result["Actual_Error"] = "SQL query is empty"
            result["Status"] = "FAIL"

            return result

        cursor = connection.cursor()

        # TC007 intentionally uses another database. Resetting here prevents
        # that one test from accidentally changing every later test's schema.
        cursor.execute(f"USE `{DB_CONFIG['database']}`")
        cursor.execute("SET SQL_SAFE_UPDATES = 0")

        # Create the exact fixture requested in the CSV before the test SQL.
        # Setup errors are reported honestly and the test query is not run.
        try:
            run_setup(cursor, connection, row)
        except mysql.connector.Error as error:
            result["Actual_Error"] = f"Setup failed: {error}"
            return result

        print()
        print(f"▶ Running {test_id} | {feature_id} | {test_type}")
        print(f"  SQL: {sql_query[:150]}")

        # ----------------------------------------------------
        # Determine expectation BEFORE execution
        # ----------------------------------------------------

        expected_status = determine_expected_status(row)

        # ----------------------------------------------------
        # Execute SQL
        # ----------------------------------------------------

        cursor.execute(sql_query)

        # ----------------------------------------------------
        # Query returned rows
        # ----------------------------------------------------

        if cursor.with_rows:

            rows = cursor.fetchall()

            # Keep the real returned values and their MySQL column names in
            # a table so SELECT results are readable in the response file.
            result["Actual_Result"] = format_query_result(cursor, rows)

        # ----------------------------------------------------
        # Query changed database
        # ----------------------------------------------------

        else:

            affected_rows = cursor.rowcount

            result["Actual_Result"] = (
                f"Query executed successfully. "
                f"Rows affected: {affected_rows}"
            )

        # ----------------------------------------------------
        # If an error was EXPECTED but SQL succeeded
        # ----------------------------------------------------

        if expected_status == "ERROR_EXPECTED":

            result["Status"] = "FAIL"

            result["Actual_Error"] = (
                "Expected SQL error, but query executed successfully."
            )

            # Roll back any accidental changes
            try:
                connection.rollback()
            except mysql.connector.Error:
                pass

        # ----------------------------------------------------
        # If success was EXPECTED and SQL succeeded
        # ----------------------------------------------------

        else:

            connection.commit()

            result["Status"] = "PASS"

    # ========================================================
    # MySQL Error
    # ========================================================

    except mysql.connector.Error as error:

        error_message = str(error)

        result["Actual_Error"] = error_message

        # ----------------------------------------------------
        # Error was expected
        # ----------------------------------------------------

        expected_status = determine_expected_status(row)

        if expected_status == "ERROR_EXPECTED":

            result["Status"] = "PASS"

        # ----------------------------------------------------
        # Error was NOT expected
        # ----------------------------------------------------

        else:

            result["Status"] = "FAIL"

        # ----------------------------------------------------
        # Roll back failed operation
        # ----------------------------------------------------

        try:
            connection.rollback()
        except mysql.connector.Error:
            pass

    # ========================================================
    # Other Python Error
    # ========================================================

    except Exception as error:

        result["Actual_Error"] = str(error)
        result["Status"] = "FAIL"

        try:
            connection.rollback()
        except mysql.connector.Error:
            pass

    # ========================================================
    # Cleanup
    # ========================================================

    finally:

        result["Execution_Time"] = time.perf_counter() - start_time

        if cursor is not None:

            try:
                cursor.close()
            except mysql.connector.Error:
                pass

    return result


# ============================================================
# Display One Test Result
# ============================================================

def print_test_result(result):
    """Display a single test result in a clean, readable format."""

    status = result.get("Status", "UNKNOWN")
    status_icon = "PASS" if status == "PASS" else "FAIL"

    print()
    print("=" * 70)
    print(" " * 20 + "TEST RESULT")
    print("=" * 70)

    print(f"Test ID       : {result.get('Test_Case_ID', '')}")
    print(
        f"Feature       : {result.get('Feature_ID', '')} — "
        f"{result.get('Feature_Name', '')}"
    )
    print(f"Test Type     : {result.get('Test_Type', '')}")
    print(f"Status        : [{status_icon}]")

    print()
    print("SQL EXECUTED")
    print("-" * 70)
    print(result.get("SQL_Query") or "None")

    print()
    print("EXPECTED RESULT")
    print("-" * 70)
    print(result.get("Expected_Result") or "None")

    print()
    print("EXPECTED ERROR")
    print("-" * 70)
    print(result.get("Expected_Error") or "None")

    print()
    print("ACTUAL RESULT")
    print("-" * 70)
    print(result.get("Actual_Result") or "None")

    print()
    print("ACTUAL ERROR")
    print("-" * 70)
    print(result.get("Actual_Error") or "None")

    print()
    print(f"Executed At   : {result.get('Executed_At', '')}")
    print("=" * 70)


# ============================================================
# Save Report
# ============================================================

def save_report(results):
    """Save test results to a timestamped CSV report."""

    os.makedirs(REPORT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(
        REPORT_DIR,
        f"test_report_{timestamp}.csv"
    )

    results_df = pd.DataFrame(results)
    results_df.to_csv(report_file, index=False)

    return report_file


def get_next_response_file(report_dir):
    """Return the next sequentially numbered response file path: response_1.txt, response_2.txt, ..."""
    os.makedirs(report_dir, exist_ok=True)
    existing_indices = []
    for fname in os.listdir(report_dir):
        match = re.match(r"^response_(\d+)\.txt$", fname)
        if match:
            existing_indices.append(int(match.group(1)))
    next_index = max(existing_indices, default=0) + 1
    return os.path.join(report_dir, f"response_{next_index}.txt")


def save_response_notepad(results):
    """
    Save database responses in Notepad format, exactly as required:

        Test case id
        Test type (Positive / Negative / Edge)
        Test description
        Execution status: pass/fail
        Query executed
        Database response
        Query execution time
    """

    os.makedirs(REPORT_DIR, exist_ok=True)
    response_file = get_next_response_file(REPORT_DIR)

    with open(response_file, "w", encoding="utf-8") as file:

        for result in results:

            # Database response: whatever MySQL actually returned —
            # the fetched rows / affected-row message on success,
            # or the MySQL error text on failure. Never synthesized.
            database_response = (
                result["Actual_Result"]
                if result["Actual_Result"]
                else result["Actual_Error"]
            )

            file.write("=" * 70 + "\n")
            file.write(f"Test Case ID: {result['Test_Case_ID']}\n")
            file.write(f"Test Type: {result.get('Test_Type', '')}\n")
            file.write(f"Test Description: {result.get('Test_Description', '')}\n")
            file.write(f"Execution Status: {result['Status']}\n")
            file.write(f"Query Executed: {result['SQL_Query']}\n")
            file.write(f"Database Response: {database_response}\n")
            file.write(
                f"Query Execution Time: "
                f"{result['Execution_Time']:.6f} seconds\n"
            )
            file.write("=" * 70 + "\n\n")

    return response_file


# ============================================================
# Print Test Summary
# ============================================================

def print_summary(results_df):

    total = len(results_df)

    passed = len(
        results_df[
            results_df["Status"] == "PASS"
        ]
    )

    failed = len(
        results_df[
            results_df["Status"] == "FAIL"
        ]
    )

    pass_percentage = (
        (passed / total) * 100
        if total > 0
        else 0
    )

    print()
    print("=" * 70)
    print("                    TEST SUMMARY")
    print("=" * 70)

    print(f"Total Tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")
    print(f"Pass Rate   : {pass_percentage:.2f}%")

    print("=" * 70)


# ============================================================
# Main Test Runner
# ============================================================

def main():

    print("=" * 70)
    print("             AI MYSQL AUTOMATED TESTING")
    print("=" * 70)

    # --------------------------------------------------------
    # Load test cases
    # --------------------------------------------------------

    test_cases = load_test_cases()

    if test_cases is None:
        return

    # --------------------------------------------------------
    # Connect to MySQL
    # --------------------------------------------------------

    connection = connect_database()

    if connection is None:
        return

    results = []

    print()
    print("🚀 Starting test execution...")
    print(f"Total tests: {len(test_cases)}")

    # --------------------------------------------------------
    # Execute every test case
    # --------------------------------------------------------

    for _, row in test_cases.iterrows():

        test_result = execute_test(
            connection,
            row
        )

        results.append(test_result)

        print(f"  → {test_result['Status']} | {test_result['Test_Case_ID']} | {test_result['Feature_Name']}")

    # --------------------------------------------------------
    # Close database connection
    # --------------------------------------------------------

    try:
        connection.close()
    except mysql.connector.Error:
        pass

    print()
    print("✅ Test execution completed.")

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    results_df = pd.DataFrame(results)

    # --------------------------------------------------------
    # Save response Notepad
    # --------------------------------------------------------

    response_file = save_response_notepad(results)

    # --------------------------------------------------------
    # Print summary
    # --------------------------------------------------------

    print_summary(results_df)

    print()
    print("📝 Response Notepad saved to:")
    print(response_file)


# ============================================================
# Program Entry Point
# ============================================================

if __name__ == "__main__":
    main()

