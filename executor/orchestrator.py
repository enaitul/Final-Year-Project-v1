#!/usr/bin/env python3
"""Set up databases, then run the four independent groups at the same time."""
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXECUTOR = PROJECT_ROOT / "executor"
REPORTS = PROJECT_ROOT / "reports"


def main():
    REPORTS.mkdir(exist_ok=True)
    print("Step 1/5: creating fresh group databases...")
    setup = subprocess.run([sys.executable, str(EXECUTOR / "setup_group_databases.py")], cwd=PROJECT_ROOT)
    if setup.returncode != 0:
        print("Setup failed, so no test groups were started.")
        return setup.returncode
    print("Step 2/5: launching four groups in parallel...")
    started = {}
    processes = {}
    log_files = {}
    for number in range(1, 5):
        log_path = REPORTS / f"agent_group{number}.log"
        log_file = log_path.open("w", encoding="utf-8", newline="\n")
        command = [sys.executable, str(EXECUTOR / "test_runner.py"), "--group", str(number), "--db-name", f"ai_testing_group{number}"]
        started[number] = time.perf_counter()
        processes[number] = subprocess.Popen(command, cwd=PROJECT_ROOT, stdout=log_file, stderr=subprocess.STDOUT)
        log_files[number] = (log_file, log_path)
    print("Step 3/5: group output is being written to reports/agent_groupN.log.")
    results = []
    for number in range(1, 5):
        code = processes[number].wait()
        elapsed = time.perf_counter() - started[number]
        log_files[number][0].close()
        results.append((number, code, elapsed, log_files[number][1]))
    print("Step 4/5: all group processes finished.")
    print("Step 5/5: execution summary")
    print("Group | DB                 | Exit Code | Elapsed (s) | Log")
    print("------|--------------------|-----------|-------------|---------------------------")
    for number, code, elapsed, log_path in results:
        print(f"{number:<5} | ai_testing_group{number:<2} | {code:<9} | {elapsed:>11.2f} | {log_path.relative_to(PROJECT_ROOT)}")
    failed = [number for number, code, _, _ in results if code != 0]
    if failed:
        print(f"One or more groups failed: {', '.join(map(str, failed))}. Read their log files for details.")
        return 1
    print("All groups completed successfully. Next run: python executor/merge_and_validate.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
