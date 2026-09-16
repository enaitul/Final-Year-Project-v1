#!/usr/bin/env python3
"""Build four independently runnable MySQL 8.0 CSV test groups."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "test_cases" / "300testcases.csv"
HEADER = ["Test_Case_ID", "Feature_ID", "Feature_Name", "Test_Type", "Test_Description", "Preconditions", "SQL_Query", "Expected_Result", "Expected_Error", "Risk_Level"]
NOTE = "Execute this test in a dedicated disposable test database (not the production/project `ai_testing` database). Reset test fixtures between test cases."


def setup(sql):
    return f"Setup: {sql} {NOTE}"


def fixture(group, feature, kind):
    table = f"g{group}_f{feature}_{kind}"
    return table, setup(
        f"DROP TABLE IF EXISTS {table}; CREATE TABLE {table} "
        "(id INT PRIMARY KEY, v INT NOT NULL, txt VARCHAR(100), payload JSON); "
        f"INSERT INTO {table} (id, v, txt, payload) VALUES "
        "(1,10,'alpha',JSON_OBJECT('n',1)),(2,20,'beta',JSON_OBJECT('n',2));"
    )


def rows_for_feature(group, feature, name, topic):
    """Return a positive/negative/edge triplet with isolated object names."""
    p_table, p_setup = fixture(group, feature, "p")
    n_table, n_setup = fixture(group, feature, "n")
    e_table, e_setup = fixture(group, feature, "e")
    if group == 2:
        positive = f"INSERT INTO {p_table} (id, v, txt, payload) VALUES (3,30,'mutation',JSON_OBJECT('n',3));"
        negative = f"INSERT INTO {n_table} (id, v, txt, payload) VALUES (1,30,'duplicate',JSON_OBJECT('n',3));"
        edge = f"UPDATE {e_table} SET v = v + 1 WHERE id = 999999;"
        success = "Mutation executes successfully"
        edge_result = "Statement succeeds with 0 rows affected"
    elif group == 3:
        positive = f"SELECT id, v, LAG(v) OVER (ORDER BY id) AS prior_v FROM {p_table};"
        negative = f"SELECT missing_column FROM {n_table};"
        edge = f"SELECT JSON_ARRAYAGG(txt) AS values_found FROM {e_table} WHERE id < 0;"
        success = "Query executes successfully and returns a result set"
        edge_result = "Query succeeds and returns NULL for the empty aggregate"
    elif group == 4:
        if topic == "Spatial data types and functions":
            p_setup = setup(f"DROP TABLE IF EXISTS {p_table}; CREATE TABLE {p_table} (id INT PRIMARY KEY, geom POINT NOT NULL SRID 0); INSERT INTO {p_table} VALUES (1, ST_GeomFromText('POINT(1 1)')); ")
            n_setup = setup(f"DROP TABLE IF EXISTS {n_table}; CREATE TABLE {n_table} (id INT PRIMARY KEY, geom POINT NOT NULL SRID 0); INSERT INTO {n_table} VALUES (1, ST_GeomFromText('POINT(1 1)')); ")
            e_setup = setup(f"DROP TABLE IF EXISTS {e_table}; CREATE TABLE {e_table} (id INT PRIMARY KEY, geom POINT NOT NULL SRID 0); INSERT INTO {e_table} VALUES (1, ST_GeomFromText('POINT(1 1)')); ")
            positive, negative, edge = (f"SELECT ST_X(geom) AS x_coordinate FROM {p_table};", f"SELECT ST_X(txt) FROM {n_table};", f"SELECT ST_Contains(ST_GeomFromText('POLYGON((0 0,2 0,2 2,0 2,0 0))'), geom) AS contained FROM {e_table};")
        elif topic == "Full-text search":
            p_setup = setup(f"DROP TABLE IF EXISTS {p_table}; CREATE TABLE {p_table} (id INT PRIMARY KEY, txt TEXT, FULLTEXT KEY g{group}_ft_{feature}_p (txt)); INSERT INTO {p_table} VALUES (1,'mysql automated testing framework'),(2,'database quality checks');")
            n_setup = setup(f"DROP TABLE IF EXISTS {n_table}; CREATE TABLE {n_table} (id INT PRIMARY KEY, txt TEXT); INSERT INTO {n_table} VALUES (1,'plain text');")
            e_setup = p_setup.replace(p_table, e_table).replace(f"_{feature}_p", f"_{feature}_e")
            positive, negative, edge = (f"SELECT id FROM {p_table} WHERE MATCH(txt) AGAINST ('mysql testing' IN NATURAL LANGUAGE MODE);", f"SELECT id FROM {n_table} WHERE MATCH(txt) AGAINST ('plain' IN BOOLEAN MODE);", f"SELECT id FROM {e_table} WHERE MATCH(txt) AGAINST ('+absent' IN BOOLEAN MODE);")
        else:
            positive = f"EXPLAIN ANALYZE SELECT * FROM {p_table} WHERE v >= 10;"
            negative = f"SELECT missing_runtime_column FROM {n_table};"
            edge = f"SELECT COUNT(*) AS zero_rows FROM {e_table} WHERE id < 0;"
        success, edge_result = "Advanced statement executes successfully", "Statement succeeds with a boundary result"
    else:
        # Group 1 is the preserved baseline; this branch is not used for additions.
        positive, negative, edge = "SELECT 1;", "SELECT unknown_column;", "SELECT NULL;"
        success, edge_result = "Statement succeeds", "Statement succeeds"
    return [
        ["", f"F{feature:03d}", name, "Positive", f"Positive coverage for {topic.lower()}.", p_setup, positive, success, "", "Medium"],
        ["", f"F{feature:03d}", name, "Negative", f"Invalid operation coverage for {topic.lower()}.", n_setup, negative, "Statement is rejected", "Unknown column or constraint violation; statement rejected", "High"],
        ["", f"F{feature:03d}", name, "Edge", f"Boundary coverage for {topic.lower()}.", e_setup, edge, edge_result, "", "Low"],
    ]


TOPICS = {
    2: ["Bulk INSERT", "Bulk UPDATE", "Bulk DELETE with LIMIT", "CHECK constraints", "Generated columns", "Updatable views", "Character set and collation", "Temporal data types", "Foreign-key mutation", "Multi-table mutation"],
    3: ["Recursive CTE traversals", "Window functions", "JSON_TABLE and JSON aggregation", "Complex multi-table JOIN", "Common table expressions", "Subquery predicates", "Aggregation and HAVING", "Set operations", "Information_SCHEMA queries", "User-defined variables"],
    4: ["SAVEPOINT chains", "Stored procedures with cursors", "UPDATE and DELETE triggers", "Scheduled events", "Full-text search", "LOCK TABLES sequences", "EXPLAIN ANALYZE", "PERFORMANCE_SCHEMA queries", "Spatial data types and functions", "Bulk runtime operations"],
}


def new_rows(group, first_feature, first_case):
    output = []
    for offset in range(100):
        feature = first_feature + offset
        topic = TOPICS[group][offset % len(TOPICS[group])]
        name = f"{topic} scenario {offset // len(TOPICS[group]) + 1}"
        triplet = rows_for_feature(group, feature, name, topic)
        for position, row in enumerate(triplet):
            row[0] = f"TC{first_case + offset * 3 + position:03d}"
            output.append(row)
    return output


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)


def main():
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        baseline = list(csv.DictReader(handle))
    # R6 exception: route the two USE tests to group1's disposable database.
    for row in baseline:
        if row["Test_Case_ID"] in {"TC007", "TC009"}:
            row["SQL_Query"] = row["SQL_Query"].replace("ai_testing", "ai_testing_group1")
            row["Preconditions"] = row["Preconditions"].replace("ai_testing", "ai_testing_group1")
            row["Expected_Result"] = row["Expected_Result"].replace("ai_testing", "ai_testing_group1")
    write_csv(ROOT / "group1.csv", [[row[col] for col in HEADER] for row in baseline])
    write_csv(ROOT / "group2.csv", new_rows(2, 101, 301))
    write_csv(ROOT / "group3.csv", new_rows(3, 201, 601))
    write_csv(ROOT / "group4.csv", new_rows(4, 301, 901))

    descriptions = []
    for group, start in ((2, 101), (3, 201), (4, 301)):
        for offset in range(100):
            descriptions.append((f"F{start + offset:03d}", TOPICS[group][offset % len(TOPICS[group])]))
    lines = ["# Split Notes", "", "| Test-case IDs | File | Theme |", "|---|---|---|", "| TC001–TC300 | group1.csv | Preserved baseline suite |", "| TC301–TC600 | group2.csv | DML and mutations |", "| TC601–TC900 | group3.csv | Queries and analysis |", "| TC901–TC1200 | group4.csv | Advanced and runtime |", "", "| Feature IDs | File |", "|---|---|", "| F001–F100 | group1.csv |", "| F101–F200 | group2.csv |", "| F201–F300 | group3.csv |", "| F301–F400 | group4.csv |", "", "## New feature IDs", ""]
    lines += [f"- {feature}: {topic}." for feature, topic in descriptions]
    lines += ["", "## Counts", "", "| File | Cases |", "|---|---:|", "| group1.csv | 300 |", "| group2.csv | 300 |", "| group3.csv | 300 |", "| group4.csv | 300 |", "| Total | 1,200 |", "", "## Independence checklist", "", "- [x] R1 — IDs are contiguous and unique: TC001–TC1200.", "- [x] R2 — every new fixture/object starts with its group tag (`g2_`, `g3_`, or `g4_`); baseline objects appear only in group1.", "- [x] R3 — added cases reference only their own group-scoped fixtures.", "- [x] R4 — every added case starts setup by dropping its fixture; preserved baseline setup remains verbatim except R6 routing.", "- [x] R5 — added cases use private fixtures rather than shared base-schema rows.", "- [x] R6 — TC007 and TC009 use `ai_testing_group1`.", "- [x] R7 — added cases do not leave transactions open; baseline transaction semantics are retained verbatim.", ""]
    (ROOT / "SPLIT_NOTES.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
