#!/usr/bin/env python3
"""Create four clean MySQL databases from the project's base-schema dump."""
import os
import re
import sys
from pathlib import Path
import mysql.connector

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DUMP_FILE = PROJECT_ROOT / "ai_testing_test.sql"
GROUP_DATABASES = [f"ai_testing_group{number}" for number in range(1, 5)]
# Use an administrator account because CREATE DATABASE and GRANT need admin rights.
ADMIN_CONFIG = {"host": os.getenv("MYSQL_HOST", "localhost"), "user": os.getenv("MYSQL_ADMIN_USER", "root"), "password": os.getenv("MYSQL_ADMIN_PASSWORD", "")}
TEST_USER = os.getenv("MYSQL_TEST_USER", "ai_tester")
TEST_HOST = os.getenv("MYSQL_TEST_HOST", "localhost")


def create_statements():
    """Read only CREATE TABLE statements and put parent tables before FK tables."""
    text = DUMP_FILE.read_text(encoding="utf-8")
    found = re.findall(r"CREATE TABLE `([^`]+)` \(.*?\) ENGINE=.*?;", text, flags=re.IGNORECASE | re.DOTALL)
    statements = {name: match.group(0) for name in found for match in [re.search(rf"CREATE TABLE `{re.escape(name)}` \(.*?\) ENGINE=.*?;", text, flags=re.IGNORECASE | re.DOTALL)]}
    required = ("departments", "projects", "employees", "employee_projects")
    missing = [name for name in required if name not in statements]
    if missing:
        raise RuntimeError(f"Could not find base table definitions in {DUMP_FILE}: {', '.join(missing)}")
    return [statements[name] for name in required]


def main():
    try:
        statements = create_statements()
        admin = mysql.connector.connect(**ADMIN_CONFIG)
    except (OSError, RuntimeError, mysql.connector.Error) as error:
        print(f"Setup could not start: {error}")
        print("Tip: set MYSQL_ADMIN_USER and MYSQL_ADMIN_PASSWORD to a MySQL account allowed to CREATE DATABASE and GRANT privileges.")
        return 1
    try:
        cursor = admin.cursor()
        for database in GROUP_DATABASES:
            cursor.execute(f"DROP DATABASE IF EXISTS `{database}`")
            cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{database}`.* TO %s@%s", (TEST_USER, TEST_HOST))
            cursor.execute(f"USE `{database}`")
            for statement in statements:
                cursor.execute(statement)
            admin.commit()
            print(f"Created {database} [OK]")
        cursor.execute("FLUSH PRIVILEGES")
        admin.commit()
        print("All four group databases are ready.")
        return 0
    except mysql.connector.Error as error:
        admin.rollback()
        print(f"Database setup failed: {error}")
        print("Check the administrator credentials and that the ai_tester account exists.")
        return 1
    finally:
        admin.close()


if __name__ == "__main__":
    raise SystemExit(main())
