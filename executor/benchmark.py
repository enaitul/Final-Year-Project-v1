#!/usr/bin/env python3
"""Benchmark: sequential vs parallel execution of the 4 independent test groups.

Place this file at: Final-Year-Project-v1/executor/benchmark.py
Run from project root: python executor/benchmark.py
"""
import csv
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXECUTOR = ROOT / "executor"
REPORTS = ROOT / "reports"
LOG_DIR = REPORTS / "benchmark_logs"
REPORTS.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

GROUPS = [1, 2, 3, 4]
RUNS = 5                 # repetitions per mode (use 2 for a quick test)
WARMUP = True            # one untimed run to warm up MySQL
INCLUDE_MERGE = True     # also time merge_and_validate.py (serial step)


def worker_cmd(group):
    return [
        sys.executable, str(EXECUTOR / "test_runner.py"),
        "--group", str(group),
        "--db-name", f"ai_testing_group{group}",
    ]


def start_worker(group, tag):
    """Start one worker; output goes to a log file, same as orchestrator.py."""
    log = open(LOG_DIR / f"{tag}_group{group}.log", "w", encoding="utf-8", newline="\n")
    proc = subprocess.Popen(worker_cmd(group), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    return proc, log


def reset_databases():
    """Fresh DBs before every run. Timed separately, not part of execution time."""
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(EXECUTOR / "setup_group_databases.py")],
        cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("setup_group_databases.py FAILED:")
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(1)
    return time.perf_counter() - t0


def run_sequential(tag):
    per_group = {}
    start = time.perf_counter()
    for g in GROUPS:
        t0 = time.perf_counter()
        proc, log = start_worker(g, tag)
        code = proc.wait()
        log.close()
        per_group[g] = time.perf_counter() - t0
        if code != 0:
            raise RuntimeError(f"Group {g} failed (exit {code}); see {LOG_DIR}")
    return time.perf_counter() - start, per_group


def run_parallel(tag):
    start = time.perf_counter()
    running = {g: start_worker(g, tag) for g in GROUPS}
    per_group = {}
    while running:
        for g, (proc, log) in list(running.items()):
            code = proc.poll()
            if code is not None:
                per_group[g] = time.perf_counter() - start   # true finish time
                log.close()
                if code != 0:
                    raise RuntimeError(f"Group {g} failed (exit {code}); see {LOG_DIR}")
                del running[g]
        time.sleep(0.01)
    return time.perf_counter() - start, per_group


def time_merge():
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(EXECUTOR / "merge_and_validate.py")],
        cwd=ROOT, capture_output=True, text=True,
    )
    elapsed = time.perf_counter() - t0
    # Exit code != 0 can just mean "validation found invalid records".
    # Only treat it as a crash if no merge happened at all.
    if "Merged" not in result.stdout:
        print("merge_and_validate.py FAILED to merge:")
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(1)
    return elapsed


def read_worker_stats(group):
    """Parse reports/response_groupN.txt -> (cases, passed, sum of per-test seconds)."""
    text = (REPORTS / f"response_group{group}.txt").read_text(encoding="utf-8")
    statuses = re.findall(r"Execution Status: (\w+)", text)
    times = re.findall(r"Query Execution Time: ([\d.]+) seconds", text)
    return len(statuses), statuses.count("PASS"), sum(map(float, times))


def one_run(name, fn):
    setup_t = reset_databases()
    exec_t, per_group = fn(name)
    worker = {g: read_worker_stats(g) for g in GROUPS}   # read BEFORE merge
    merge_t = time_merge() if INCLUDE_MERGE else 0.0
    return setup_t, exec_t, per_group, merge_t, worker


def stats(values):
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return statistics.mean(values), sd, min(values), max(values)


def main():
    if WARMUP:
        print("Warm-up run (not recorded)...")
        one_run("warmup", run_parallel)

    rows = []
    data = {"sequential": [], "parallel": []}
    fns = {"sequential": run_sequential, "parallel": run_parallel}

    for i in range(1, RUNS + 1):
        order = ["sequential", "parallel"]
        if i % 2 == 0:               # alternate order to avoid bias
            order.reverse()
        for name in order:
            setup_t, exec_t, per_group, merge_t, worker = one_run(name, fns[name])
            data[name].append((exec_t, merge_t))
            cases = sum(w[0] for w in worker.values())
            passed = sum(w[1] for w in worker.values())
            db_work = sum(w[2] for w in worker.values())
            print(f"Run {i} | {name:<10} | exec {exec_t:7.2f}s | merge {merge_t:5.2f}s | pass {passed}/{cases}")
            rows.append({
                "run": i, "mode": name,
                "setup_seconds": round(setup_t, 3),
                "exec_seconds": round(exec_t, 3),
                "merge_seconds": round(merge_t, 3),
                "end_to_end_seconds": round(exec_t + merge_t, 3),
                "cases_run": cases,
                "cases_passed": passed,
                "sum_per_test_seconds": round(db_work, 3),
                **{f"group{g}_seconds": round(per_group[g], 3) for g in GROUPS},
            })

    with open(REPORTS / "benchmark_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    # Correctness check: both modes must produce the same pass count
    seq_pass = {r["cases_passed"] for r in rows if r["mode"] == "sequential"}
    par_pass = {r["cases_passed"] for r in rows if r["mode"] == "parallel"}
    if seq_pass != par_pass or len(seq_pass) != 1:
        print(f"WARNING: pass counts differ: seq={seq_pass}, par={par_pass}. "
              "Investigate before trusting the timings.")
    else:
        print(f"Correctness check OK: every run passed {next(iter(seq_pass))} cases.")

    seq = [e for e, _ in data["sequential"]]
    par = [e for e, _ in data["parallel"]]
    seq_m, seq_sd, seq_min, seq_max = stats(seq)
    par_m, par_sd, par_min, par_max = stats(par)
    speedup = seq_m / par_m
    efficiency = speedup / len(GROUPS)

    merge_m = statistics.mean(m for _, m in data["parallel"])
    e2e_seq = seq_m + merge_m
    e2e_par = par_m + merge_m

    summary = f"""Benchmark run: {datetime.now():%Y-%m-%d %H:%M:%S}
Test cases: 1500 ({len(GROUPS)} groups x 375) | Runs per mode: {RUNS}

EXECUTION ONLY (workers, excludes DB setup and merge)
Sequential : mean {seq_m:.2f}s  std {seq_sd:.2f}s  min {seq_min:.2f}s  max {seq_max:.2f}s
Parallel   : mean {par_m:.2f}s  std {par_sd:.2f}s  min {par_min:.2f}s  max {par_max:.2f}s
Speedup    : {speedup:.2f}x
Efficiency : {efficiency:.1%}  (ideal = 100%)
Time saved : {(1 - par_m / seq_m):.1%}

END-TO-END (execution + merge_and_validate)
Sequential : {e2e_seq:.2f}s
Parallel   : {e2e_par:.2f}s
Speedup    : {e2e_seq / e2e_par:.2f}x
"""
    print("\n" + summary)
    (REPORTS / "benchmark_summary.txt").write_text(summary)

    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(["Sequential", "Parallel"], [seq_m, par_m],
               yerr=[seq_sd, par_sd], capsize=6, color=["#c0504d", "#4f81bd"])
        ax.set_ylabel("Execution time (s)")
        ax.set_title(f"Speedup: {speedup:.2f}x")
        fig.tight_layout()
        fig.savefig(REPORTS / "benchmark_chart.png", dpi=150)
    except ImportError:
        print("matplotlib not installed, skipping chart (pip install matplotlib)")


if __name__ == "__main__":
    main()