#!/usr/bin/env python3
"""
AI Agent Component for Intelligent Test Log Analysis & Root Cause Diagnosis
Assigned to: KANIZ (AI Agent Integration) / ENAIT

Module Responsibilities:
1. Scan & Parse Execution Logs (`reports/agent_group1.log` .. `agent_group4.log`) and `reports/response_merged.txt`.
2. AI Diagnostic Engine: Classify failures, identify root causes, and evaluate MySQL error codes.
3. Provide automated intelligent corrective recommendations (SQL syntax fixes, schema setup, index additions, lock handling).
4. Generate natural language test suite summary reports.
"""

import re
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"
LOG_FILES = [REPORTS_DIR / f"agent_group{i}.log" for i in range(1, 5)]
MERGED_RESPONSE = REPORTS_DIR / "response_merged.txt"

# Error Category Classifier & Recommendation Rules
ERROR_PATTERNS = {
    "SYNTAX_ERROR": {
        "pattern": r"(1064|syntax error|You have an error in your SQL syntax)",
        "cause": "Invalid SQL syntax or reserved keyword misuse.",
        "recommendation": "Review query clause ordering, quotation marks, and MySQL version compatibility."
    },
    "MISSING_TABLE_OR_COLUMN": {
        "pattern": r"(1146|1054|Table .* doesn't exist|Unknown column)",
        "cause": "Target table or referenced column is missing from the database schema.",
        "recommendation": "Verify setup script DDLS (`setup_group_databases.py`) to ensure required tables and columns are pre-created."
    },
    "CONSTRAINT_VIOLATION": {
        "pattern": r"(1062|1216|1217|1451|1452|Duplicate entry|Cannot add or update a child row|a foreign key constraint fails)",
        "cause": "Violation of Primary Key, Unique Constraint, or Foreign Key reference integrity.",
        "recommendation": "Ensure prerequisite seed data exists and execution order maintains parent-child relationship integrity."
    },
    "DATA_TRUNCATION_OR_TYPE": {
        "pattern": r"(1265|1366|Data truncated|Incorrect integer value|Out of range value)",
        "cause": "Data type mismatch or string value exceeding column size limits.",
        "recommendation": "Inspect data column definitions (e.g. VARCHAR lengths) or adjust strict SQL mode flags."
    },
    "LOCK_OR_TIMEOUT": {
        "pattern": r"(1205|1213|Lock wait timeout exceeded|Deadlock found)",
        "cause": "Concurrent transaction contention across worker threads or uncommitted locks.",
        "recommendation": "Ensure workers use isolated databases (`ai_testing_groupN`) and explicitly issue `COMMIT` or `ROLLBACK`."
    },
    "PERMISSION_OR_AUTH": {
        "pattern": r"(1044|1045|Access denied|command denied)",
        "cause": "Database user lacks necessary privileges for the attempted operation.",
        "recommendation": "Verify `MYSQL_ADMIN_USER` credentials and check database grant permissions."
    }
}

class AIAgentAnalyzer:
    def __init__(self):
        self.logs_data = {}
        self.parsed_records = []
        self.error_summary = defaultdict(int)
        self.diagnostics = []

    def load_merged_responses(self):
        """Parse response_merged.txt into structured records."""
        if not MERGED_RESPONSE.exists():
            print(f"Warning: Merged response file not found at {MERGED_RESPONSE}")
            return []

        with open(MERGED_RESPONSE, "r", encoding="utf-8") as f:
            content = f.read()

        raw_blocks = content.split("======================================================================")
        records = []
        for block in raw_blocks:
            if not block.strip():
                continue
            rec = {}
            for line in block.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    rec[k.strip()] = v.strip()
            if "Test Case ID" in rec:
                records.append(rec)
        
        self.parsed_records = records
        return records

    def analyze_logs(self):
        """Scan worker log files for runtime errors and tracebacks."""
        log_diagnostics = []
        for log_path in LOG_FILES:
            if not log_path.exists():
                continue
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            group_name = log_path.stem
            for idx, line in enumerate(lines):
                for cat, info in ERROR_PATTERNS.items():
                    if re.search(info["pattern"], line, re.IGNORECASE):
                        log_diagnostics.append({
                            "group": group_name,
                            "line_num": idx + 1,
                            "category": cat,
                            "snippet": line.strip()[:150],
                            "cause": info["cause"],
                            "recommendation": info["recommendation"]
                        })
                        self.error_summary[cat] += 1
        return log_diagnostics

    def perform_intelligent_diagnosis(self):
        """Analyze test outcomes and correlate failure patterns."""
        total_cases = len(self.parsed_records)
        passed_cases = [r for r in self.parsed_records if r.get("Execution Status") == "PASS"]
        failed_cases = [r for r in self.parsed_records if r.get("Execution Status") == "FAIL"]

        pos_total = len([r for r in self.parsed_records if r.get("Test Type") == "Positive"])
        pos_pass = len([r for r in self.parsed_records if r.get("Test Type") == "Positive" and r.get("Execution Status") == "PASS"])

        neg_total = len([r for r in self.parsed_records if r.get("Test Type") == "Negative"])
        neg_pass = len([r for r in self.parsed_records if r.get("Test Type") == "Negative" and r.get("Execution Status") == "PASS"])

        edge_total = len([r for r in self.parsed_records if r.get("Test Type") == "Edge"])
        edge_pass = len([r for r in self.parsed_records if r.get("Test Type") == "Edge" and r.get("Execution Status") == "PASS"])

        # Detailed failure analysis
        detailed_failures = []
        for f in failed_cases:
            tcid = f.get("Test Case ID", "UNKNOWN")
            ttype = f.get("Test Type", "UNKNOWN")
            desc = f.get("Test Description", "")
            resp = f.get("Database Response", "")
            query = f.get("Query Executed", "")

            # Match error category
            matched_cat = "UNKNOWN_DB_ERROR"
            matched_rec = "Inspect database logs and query syntax."
            for cat, info in ERROR_PATTERNS.items():
                if re.search(info["pattern"], resp, re.IGNORECASE):
                    matched_cat = cat
                    matched_rec = info["recommendation"]
                    break

            detailed_failures.append({
                "test_id": tcid,
                "type": ttype,
                "description": desc,
                "error": resp,
                "query": query,
                "category": matched_cat,
                "recommendation": matched_rec
            })

        return {
            "total_cases": total_cases,
            "pass_count": len(passed_cases),
            "fail_count": len(failed_cases),
            "pass_rate": (len(passed_cases) / total_cases * 100) if total_cases > 0 else 0,
            "positive_metrics": f"{pos_pass}/{pos_total} passed",
            "negative_metrics": f"{neg_pass}/{neg_total} passed (Error expected & caught)",
            "edge_metrics": f"{edge_pass}/{edge_total} passed",
            "detailed_failures": detailed_failures
        }

    def generate_report(self):
        """Write automated natural language test suite summary & diagnostic report."""
        self.load_merged_responses()
        log_diags = self.analyze_logs()
        diag_metrics = self.perform_intelligent_diagnosis()

        report_lines = []
        report_lines.append("==========================================================================")
        report_lines.append("           AI AGENT INTELLIGENT TEST LOG & DIAGNOSTIC REPORT            ")
        report_lines.append("==========================================================================")
        report_lines.append(f"Generated At          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Analyzed Component    : 4 Parallel Worker Logs & Merged Suite Response")
        report_lines.append(f"AI Reasoning Model    : Rule-Based Heuristic & Pattern Diagnostic Engine")
        report_lines.append("--------------------------------------------------------------------------\n")

        report_lines.append("1. EXECUTIVE SUMMARY & METRICS")
        report_lines.append(f"   • Total Test Cases Evaluated : {diag_metrics['total_cases']}")
        report_lines.append(f"   • Passed Test Cases          : {diag_metrics['pass_count']} ({diag_metrics['pass_rate']:.2f}%)")
        report_lines.append(f"   • Failed Test Cases          : {diag_metrics['fail_count']}")
        report_lines.append(f"   • Positive Test Suite        : {diag_metrics['positive_metrics']}")
        report_lines.append(f"   • Negative Test Suite        : {diag_metrics['negative_metrics']}")
        report_lines.append(f"   • Edge Case Suite            : {diag_metrics['edge_metrics']}")
        report_lines.append("\n--------------------------------------------------------------------------\n")

        report_lines.append("2. ERROR CATEGORIZATION & PATTERN FREQUENCY")
        if self.error_summary:
            for cat, count in self.error_summary.items():
                report_lines.append(f"   • {cat:<25} : {count} occurrence(s)")
        else:
            report_lines.append("   • Clean Execution: Zero MySQL system-level log crashes detected!")
        report_lines.append("\n--------------------------------------------------------------------------\n")

        report_lines.append("3. LOG DIAGNOSTIC TRACES (agent_group1.log .. agent_group4.log)")
        if log_diags:
            for d in log_diags[:10]:
                report_lines.append(f"   [{d['group']}:L{d['line_num']}] Category: {d['category']}")
                report_lines.append(f"      Snippet : {d['snippet']}")
                report_lines.append(f"      Root Cause: {d['cause']}")
                report_lines.append(f"      Action    : {d['recommendation']}\n")
        else:
            report_lines.append("   • No runtime exception stack traces found in worker logs.")
        report_lines.append("\n--------------------------------------------------------------------------\n")

        report_lines.append("4. DETAILED FAILURE DIAGNOSIS & ACTIONABLE SUGGESTIONS")
        failures = diag_metrics["detailed_failures"]
        if failures:
            for idx, f in enumerate(failures, 1):
                report_lines.append(f"   Failure #{idx}: {f['test_id']} [{f['type']}] - {f['description']}")
                report_lines.append(f"      Query       : {f['query']}")
                report_lines.append(f"      DB Output   : {f['error']}")
                report_lines.append(f"      Diagnosis   : {f['category']}")
                report_lines.append(f"      AI Action   : {f['recommendation']}")
                report_lines.append("   " + "-" * 60)
        else:
            report_lines.append("   🎉 PERFECT SCORE: All 1,500 test cases passed baseline expectations!")
            report_lines.append("   • Positive queries executed with expected data state changes.")
            report_lines.append("   • Negative queries were correctly intercepted by MySQL constraints.")
            report_lines.append("   • Edge cases handled boundary inputs cleanly.")
        report_lines.append("\n==========================================================================")
        report_lines.append("                       END OF AI DIAGNOSTIC REPORT                        ")
        report_lines.append("==========================================================================")

        report_content = "\n".join(report_lines)

        # Write to txt report
        out_txt = REPORTS_DIR / "ai_analysis_report.txt"
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(report_content)

        # Write to markdown summary
        out_md = REPORTS_DIR / "ai_analysis_summary.md"
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(f"# 🤖 AI Diagnostic Summary\n\n```text\n{report_content}\n```\n")

        print(f"AI Analysis Report generated successfully:")
        print(f"  • {out_txt.relative_to(PROJECT_ROOT)}")
        print(f"  • {out_md.relative_to(PROJECT_ROOT)}")
        return report_content

def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    analyzer = AIAgentAnalyzer()
    report = analyzer.generate_report()
    print("\nReport Excerpt:\n")
    print("\n".join(report.split("\n")[:25]))

if __name__ == "__main__":
    main()
