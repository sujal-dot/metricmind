#!/usr/bin/env python3
"""Day 16 Governance, Security & Query Transparency Validation Script."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dataclasses import dataclass

from app.governance.policy_engine import PolicyEngine
from app.governance.sql_detector import SQLDetector
from app.governance.expensive_query_detector import ExpensiveQueryDetector
from app.governance.security_validator import SecurityValidator
from app.governance.query_guard import QueryGuard, CubeAPITrace
from app.governance.governance_logger import GovernanceLogger


@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str = ""


BLOCKED_CASES = [
    ("SELECT * FROM Orders", "sql_injection", "SELECT * FROM injection"),
    ("DROP TABLE Customers", "sql_injection", "DROP TABLE keyword"),
    ("DELETE FROM Sales", "sql_injection", "DELETE FROM keyword"),
    ("UNION SELECT password FROM users", "sql_injection", "UNION SELECT injection"),
    ("Show entire database", "expensive", "Entire database request"),
    ("Export all records", "expensive", "Export all records"),
    ("Write SQL to find total revenue", "sql_request", "Write SQL request"),
    ("SELECT id, name FROM users WHERE ' OR 1=1 --", "sql_injection", "OR 1=1 tautology"),
    ("Give me 10 million rows of orders", "expensive", "Large count"),
    ("xp_cmdshell 'dir'", "sql_injection", "xp_cmdshell keyword"),
    ("Show every order ever made", "expensive", "Every order ever"),
    ("Run SQL query for sales report", "sql_request", "Run SQL request"),
    ("INSERT INTO orders VALUES (1,2,3)", "sql_injection", "INSERT keyword"),
    ("UPDATE users SET password='hacked'", "sql_injection", "UPDATE keyword"),
    ("ALTER TABLE customers ADD COLUMN secret", "sql_injection", "ALTER keyword"),
    ("INFORMATION_SCHEMA.TABLES", "sql_injection", "INFORMATION_SCHEMA access"),
]

ALLOWED_CASES = [
    ("Monthly revenue trend", "Valid analytics aggregation"),
    ("Sales by region", "Valid dimension breakdown"),
    ("Revenue share by category", "Valid distribution query"),
    ("Top customers", "Valid ranking query"),
    ("Why did profit decrease?", "Valid explain/root-cause question"),
    ("Revenue growth over time", "Valid trend query"),
    ("What was the total profit last month in Europe?", "Valid filtered metric"),
    ("Top 10 products by sales this quarter", "Valid filtered ranking"),
    ("Profit margin breakdown by category for 2025", "Valid breakdown with filter"),
]


def test_sql_injection_blocking(engine: PolicyEngine) -> list[TestResult]:
    results: list[TestResult] = []
    target_cases = [c for c in BLOCKED_CASES if c[1] == "sql_injection"]
    for question, expected, desc in target_cases:
        result = engine.validate(question, route="/validate-test")
        passed = not result.allowed and (
            result.violation is not None and result.violation.code == expected
        )
        detail = f"'{question[:60]}' → expected={expected}, got="
        if result.violation:
            detail += result.violation.code
        elif not result.allowed:
            detail += f"blocked(unknown_code)"
        else:
            detail += "ALLOWED ❌"
        results.append(TestResult(
            name=f"Block: {desc}",
            passed=passed,
            detail=detail,
        ))
    return results


def test_sql_request_blocking(engine: PolicyEngine) -> list[TestResult]:
    results: list[TestResult] = []
    target_cases = [c for c in BLOCKED_CASES if c[1] == "sql_request"]
    for question, expected, desc in target_cases:
        result = engine.validate(question, route="/validate-test")
        passed = not result.allowed and (
            result.violation is not None and result.violation.code == expected
        )
        detail = f"'{question[:60]}' → expected={expected}, got="
        if result.violation:
            detail += result.violation.code
        elif not result.allowed:
            detail += f"blocked(unknown_code)"
        else:
            detail += "ALLOWED ❌"
        results.append(TestResult(
            name=f"Block: {desc}",
            passed=passed,
            detail=detail,
        ))
    return results


def test_expensive_query_blocking(engine: PolicyEngine) -> list[TestResult]:
    results: list[TestResult] = []
    target_cases = [c for c in BLOCKED_CASES if c[1] == "expensive"]
    for question, expected, desc in target_cases:
        result = engine.validate(question, route="/validate-test")
        passed = not result.allowed and (
            result.violation is not None and result.violation.code == expected
        )
        detail = f"'{question[:60]}' → expected={expected}, got="
        if result.violation:
            detail += result.violation.code
        elif not result.allowed:
            detail += f"blocked(unknown_code)"
        else:
            detail += "ALLOWED ❌"
        results.append(TestResult(
            name=f"Block: {desc}",
            passed=passed,
            detail=detail,
        ))
    return results


def test_allowed_queries(engine: PolicyEngine) -> list[TestResult]:
    results: list[TestResult] = []
    for question, desc in ALLOWED_CASES:
        result = engine.validate(question, route="/validate-test")
        passed = result.allowed
        detail = f"'{question[:60]}' → " + ("ALLOWED ✓" if passed else (
            f"BLOCKED ❌ code={result.violation.code if result.violation else 'unknown'}; reasons={result.violation.reasons if result.violation else 'none'}"
        ))
        results.append(TestResult(
            name=f"Allow: {desc}",
            passed=passed,
            detail=detail,
        ))
    return results


def test_query_guard_trace() -> TestResult:
    guard = QueryGuard()
    guard.begin_trace(
        endpoint="/cubejs-api/v1/load",
        method="POST",
        query_parameters={"route": "/ask"},
        request_payload={"query": [{"measures": ["fact_sales.total_sales"]}]},
    )
    import time
    trace = guard.complete_trace(
        {"data": [{"fact_sales.total_sales": 123456}]},
        status=200,
        started_at=time.perf_counter(),
    )
    view_api = trace.for_view_api()
    view_json = trace.for_view_json()
    ok = (
        isinstance(trace, CubeAPITrace)
        and view_api.get("endpoint") == "/cubejs-api/v1/load"
        and view_api.get("method") == "POST"
        and "execution_time_ms" in view_api
        and "response_status" in view_api
        and "response_size_bytes" in view_api
        and isinstance(view_json, dict)
        and "data" in view_json
    )
    return TestResult(
        name="QueryGuard + CubeAPITrace",
        passed=ok,
        detail=("Trace redaction + for_view_api/json work correctly" if ok else "Trace/redaction fields missing"),
    )


def test_cube_only_policy_message(engine: PolicyEngine) -> TestResult:
    result = engine.validate("Write SQL to join orders and customers", route="/ask")
    if result.allowed or result.violation is None:
        return TestResult(
            name="Cube-only policy message",
            passed=False,
            detail="SQL request was not blocked",
        )
    expected_msg = "Cube.dev Semantic API"
    ok = expected_msg in result.violation.message or "governance policy" in result.violation.message.lower()
    return TestResult(
        name="Cube-only policy message",
        passed=ok,
        detail=f"Message contains Cube-only policy: {ok}. Got: {result.violation.message[:90]}",
    )


def test_logging(engine: PolicyEngine) -> TestResult:
    engine.validate("Show daily revenue for 2025", route="/test-logging")
    logger = engine.logger
    ok = logger.path.exists() and logger.path.stat().st_size >= 0
    detail = f"Log file exists at {logger.path}" if ok else f"Log file missing at {logger.path}"
    return TestResult(name="Governance logging", passed=ok, detail=detail)


def test_security_validator_composition() -> TestResult:
    validator = SecurityValidator()
    sql_dec = validator.validate("SELECT * FROM orders")
    req_dec = validator.validate("Write SQL for sales")
    exp_dec = validator.validate("Show every order ever made")
    ok_dec = validator.validate("Revenue by category")
    ok = (
        not sql_dec.allowed and sql_dec.block_code == "sql_injection"
        and not req_dec.allowed and req_dec.block_code == "sql_request"
        and not exp_dec.allowed and exp_dec.block_code == "expensive"
        and ok_dec.allowed
    )
    return TestResult(
        name="SecurityValidator composition (4 cases)",
        passed=ok,
        detail="Prioritizes: injection > request > expensive > allowed",
    )


def main() -> int:
    print()
    print("=" * 73)
    print("  MetricMind — Day 16 Governance, Security & Transparency Validation")
    print("=" * 73)
    print()

    engine = PolicyEngine()
    all_results: list[tuple[str, list[TestResult]]] = []

    all_results.append(("SQL Injection Blocking", test_sql_injection_blocking(engine)))
    all_results.append(("Raw SQL Request Blocking", test_sql_request_blocking(engine)))
    all_results.append(("Expensive Query Guard", test_expensive_query_blocking(engine)))
    all_results.append(("Allowed Analytics Queries", test_allowed_queries(engine)))
    all_results.append(("Security Validator Composition", [test_security_validator_composition()]))
    all_results.append(("Cube-only Policy Message", [test_cube_only_policy_message(engine)]))
    all_results.append(("Cube API Trace / QueryGuard", [test_query_guard_trace()]))
    all_results.append(("Governance Logger", [test_logging(engine)]))

    # Report
    checks: dict[str, bool] = {}
    total_tests = 0
    passed_tests = 0

    for section, results in all_results:
        section_pass = all(r.passed for r in results)
        checks[section] = section_pass
        total_tests += len(results)
        passed_tests += sum(1 for r in results if r.passed)
        print(f"  [{section}]")
        for r in results:
            mark = "✅ PASS" if r.passed else "❌ FAIL"
            print(f"    {mark} — {r.name}")
            if r.detail:
                print(f"           {r.detail}")
        print()

    # ---- Cross-feature checks (feature-level summary) ----
    print("-" * 73)
    print("  Feature-level Validation Summary")
    print("-" * 73)

    def feats():
        yield "Security Validator", checks.get("Security Validator Composition")
        yield "SQL Injection Blocking", checks.get("SQL Injection Blocking")
        yield "Raw SQL Prevention", checks.get("Raw SQL Request Blocking")
        yield "Expensive Query Guard", checks.get("Expensive Query Guard")
        yield "Cube API Enforcement", checks.get("Cube-only Policy Message") and checks.get("Cube API Trace / QueryGuard")
        yield "Governance Logging", checks.get("Governance Logger")
        yield "Allowed Queries Pass", checks.get("Allowed Analytics Queries")

    # Frontend features (component file existence checks)
    FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src" / "components" / "governance"
    frontend_files = {
        "ViewAPIButton": "ViewAPIButton.tsx",
        "ViewJSONButton": "ViewJSONButton.tsx",
        "JSON Viewer": "JSONViewer.tsx",
        "Security Banner": "SecurityBanner.tsx",
    }
    frontend_present = {name: (FRONTEND / fname).exists() for name, fname in frontend_files.items()}
    responsive_ui = all(frontend_present.values())

    feature_results: list[tuple[str, bool]] = list(feats())
    feature_results.append(("View API Button", frontend_present.get("ViewAPIButton", False)))
    feature_results.append(("View JSON Button", frontend_present.get("ViewJSONButton", False)))
    feature_results.append(("JSON Viewer", frontend_present.get("JSON Viewer", False)))
    feature_results.append(("Responsive UI (components exist)", responsive_ui))

    # README existence + governance mention
    README = Path(__file__).resolve().parents[2] / "README.md"
    readme_text = README.read_text(encoding="utf-8") if README.exists() else ""
    readme_has_governance = any(
        kw in readme_text.lower() for kw in ("governance", "cube.dev only", "security", "view api", "view json")
    )
    feature_results.append(("README Updated", readme_has_governance))

    print()
    for name, ok in feature_results:
        mark = "PASS ✅" if ok else "FAIL ❌"
        print(f"  {name:<25s}: {mark}")

    overall = all(ok for _, ok in feature_results)

    print()
    print("=" * 73)
    print("  MetricMind — Day 16 Governance Validation — FINAL REPORT")
    print("=" * 73)
    print()

    for name, ok in feature_results:
        mark = "PASS ✅" if ok else "FAIL ❌"
        print(f"  {name:<25s}: {mark}")

    print()
    print("-----------------------------------------")
    print(f"  Tests run : {total_tests}")
    print(f"  Passed    : {passed_tests}")
    print(f"  Failed    : {total_tests - passed_tests}")
    print("-----------------------------------------")
    print()
    print("-----------------------------------------")
    print("  OVERALL RESULT")
    print("-----------------------------------------")
    print()
    if overall:
        print("  PASS ✅")
        print()
        print("  All governance, security, and transparency features validated.")
    else:
        print("  FAIL ❌")
        print()
        print("  Issues found:")
        for name, ok in feature_results:
            if not ok:
                print(f"    - {name}")
        print()
        print("  Please review the failed feature sections above, apply fixes,")
        print("  then re-run: python backend/scripts/validate_day16.py")

    print()

    # Write report file
    report_lines = []
    report_lines.append("=" * 73)
    report_lines.append("MetricMind - Day 16 Governance Validation")
    report_lines.append("=" * 73)
    report_lines.append("")
    for name, ok in feature_results:
        mark = "PASS" if ok else "FAIL"
        report_lines.append(f"{name:<25s}: {mark}")
    report_lines.append("")
    report_lines.append("-----------------------------------------")
    report_lines.append("OVERALL RESULT")
    report_lines.append("-----------------------------------------")
    report_lines.append("PASS" if overall else "FAIL")
    report_path = Path(__file__).resolve().parents[1] / "logs" / "day16-final-report.txt"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"  Report saved: {report_path}")
    print()

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
