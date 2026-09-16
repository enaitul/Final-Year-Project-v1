# Current 1,500-Case Split

| Group | File | Cases | Test-case IDs | Primary coverage |
|---|---|---:|---|---|
| 1 | `test_cases/group1.csv` | 375 | TC001-TC375 | Core DDL, DML, and query cases |
| 2 | `test_cases/group2.csv` | 375 | TC376-TC750 | Mutation and update cases |
| 3 | `test_cases/group3.csv` | 375 | TC751-TC1125 | Query and analytical cases |
| 4 | `test_cases/group4.csv` | 375 | TC1126-TC1500 | Advanced, transaction, and runtime cases |
| Total | — | **1,500** | TC001-TC1500 | Complete suite |

## Independence rules

- Every group runs in its own disposable MySQL database.
- Setup SQL creates or resets the data needed by its case.
- Group responses and logs are written to separate files.
- The merge stage sorts by `Test_Case_ID` and validates all 1,500 IDs.
