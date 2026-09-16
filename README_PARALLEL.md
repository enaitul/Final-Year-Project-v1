# Parallel MySQL Test Execution

The 1,500-case suite is split into four independent 375-case groups. Four local Python worker processes run concurrently, each against its own disposable MySQL database. This is Python multi-process orchestration, not an LLM-agent framework.

| Group | IDs | Database |
|---|---|---|
| 1 | TC001-TC375 | ai_testing_group1 |
| 2 | TC376-TC750 | ai_testing_group2 |
| 3 | TC751-TC1125 | ai_testing_group3 |
| 4 | TC1126-TC1500 | ai_testing_group4 |

## Run the complete workflow

```powershell
$env:MYSQL_ADMIN_USER = "root"
$env:MYSQL_ADMIN_PASSWORD = "<your-password>"
python executor\setup_group_databases.py
python executor\orchestrator.py
python executor\merge_and_validate.py
Get-Content reports\response_validation_report.txt
```

The setup command drops and recreates only the four disposable group databases. Never store important data in them.

## Outputs

- `reports/agent_groupN.log`: worker logs.
- `reports/response_groupN.txt`: per-worker results.
- `reports/response_merged.txt`: all 1,500 results in ID order.
- `reports/combined_group_test_cases.csv`: combined validation source.
- `reports/response_validation_report.txt`: final verdict.
- `reports/standard_test_results.txt`: baseline after a valid first run.

If a group fails, inspect its matching `agent_groupN.log`, correct the issue, recreate the disposable databases, and rerun.
