#!/usr/bin/env python3
"""Day 15 - Explain Results Engine validation suite."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.explain.confidence_score import ConfidenceScorer  # noqa: E402
from app.explain.explain_agent import ExplainAgent  # noqa: E402
from app.explain.metric_analyzer import MetricAnalyzer  # noqa: E402
from app.explain.recommendation_engine import RecommendationEngine  # noqa: E402
from app.explain.root_cause import RootCauseAnalyzer  # noqa: E402
from app.models.schemas import (  # noqa: E402
    ExplainRequest,
    ExplainResponse,
    ExplainSummary,
)

EXAMPLE_QUESTIONS = [
    "Why did European margin decrease?",
    "Why did profit fall last month?",
    "Why are shipping costs increasing?",
    "Why is revenue growing?",
    "Why did customer retention decrease?",
]

UNSUPPORTED_QUESTIONS = [
    "Show sales by region",
    "What is the weather in Tokyo?",
    "",
]

REQUIRED_SUMMARY_KEYS = [
    "region",
    "revenue",
    "cost",
    "shipping_cost",
    "discount_amount",
    "profit",
    "margin",
    "orders",
    "customers",
    "aov",
    "primary_metric",
    "direction_hint",
]


def show(label: str, ok: bool) -> None:
    mark = "PASS ✅" if ok else "FAIL ❌"
    print(f"{label.ljust(24)}: {mark}")


def main() -> int:
    print()
    print("=========================================")
    print("MetricMind - Day 15 Explain Results")
    print("=========================================")
    print()

    checks: dict[str, bool] = {}

    # --- A. Engine instantiation & schemas ---------------------------------
    try:
        ma = MetricAnalyzer()
        rc = RootCauseAnalyzer()
        cs = ConfidenceScorer()
        re_eng = RecommendationEngine()
        agent = ExplainAgent(use_llm_synthesis=False)
        engine_ok = True
    except Exception as exc:  # pragma: no cover
        print(f"ENGINE INIT FAILURE: {exc}")
        engine_ok = False
    checks["Explain Engine"] = engine_ok

    # --- B. Why? question detection ----------------------------------------
    why_ok = True
    print("--- Why Question Detection ---")
    for q in EXAMPLE_QUESTIONS:
        if not agent.is_supported(q):
            print(f"  ❌ should be supported: {q!r}")
            why_ok = False
        else:
            print(f"  ✅ supported: {q!r}")
    for q in UNSUPPORTED_QUESTIONS:
        if agent.is_supported(q):
            print(f"  ❌ should NOT be supported: {q!r}")
            why_ok = False
        else:
            print(f"  ✅ correctly unsupported: {q!r}")
    checks["Why Question Detection"] = why_ok

    # --- C. Metric analyzer builds valid snapshots -------------------------
    cube_ok = True
    print("\n--- Snapshot & Cube API Analysis ---")
    snapshots = {}
    for q in EXAMPLE_QUESTIONS:
        try:
            s = ma.build_snapshot(q)
            snapshots[q] = s
            missing = [k for k in ("revenue", "profit", "margin", "orders", "customers",
                                    "cost", "shipping_cost", "discount_amount", "aov")
                       if s.current.get(k) is None]
            if missing:
                print(f"  ❌ {q!r} missing keys {missing}")
                cube_ok = False
            else:
                print(f"  ✅ {q!r} -> region={s.region} primary={s.primary_metric} "
                      f"dir={s.direction_hint} deltas={len(s.deltas_pct)}/9")
        except Exception as exc:
            cube_ok = False
            print(f"  ❌ {q!r} build_snapshot raised: {exc}")
    checks["Cube API Analysis"] = cube_ok

    # --- D. Root cause analysis is evidence-based --------------------------
    rc_ok = True
    print("\n--- Root Cause Analysis ---")
    for q, s in snapshots.items():
        try:
            findings = rc.analyze(s)
            if not findings:
                print(f"  ❌ {q!r} no findings")
                rc_ok = False
                continue
            if not all(f.supported for f in findings):
                print(f"  ⚠️ {q!r} has unsupported finding")
            for f in findings[:3]:
                if not isinstance(f.reason_text, str) or len(f.reason_text) < 10:
                    rc_ok = False
            print(f"  ✅ {q!r} -> findings={len(findings)} top_weight={findings[0].weight:.2f} "
                  f"trigger={findings[0].evidence_metric}")
        except Exception as exc:
            rc_ok = False
            print(f"  ❌ {q!r} analyze raised: {exc}")
    checks["Root Cause Analysis"] = rc_ok

    # --- E. Recommendations -------------------------------------------------
    rec_ok = True
    print("\n--- Recommendations ---")
    for q, s in snapshots.items():
        try:
            findings = rc.analyze(s)
            recs = re_eng.recommend(s, findings)
            if not recs:
                rec_ok = False
                print(f"  ❌ {q!r} no recommendations")
            elif len(recs) > 5:
                rec_ok = False
                print(f"  ❌ {q!r} too many recs: {len(recs)}")
            else:
                print(f"  ✅ {q!r} -> {len(recs)} recs: {recs[0][:70]}...")
        except Exception as exc:
            rec_ok = False
            print(f"  ❌ {q!r} recs raised: {exc}")
    checks["Recommendations"] = rec_ok

    # --- F. Confidence Score ------------------------------------------------
    conf_ok = True
    print("\n--- Confidence Score ---")
    for q, s in snapshots.items():
        try:
            findings = rc.analyze(s)
            score = cs.score(s, findings)
            if not 20 <= score.total <= 100:
                conf_ok = False
                print(f"  ❌ {q!r} out-of-range confidence: {score.total}")
                continue
            for comp in ("data_completeness_pct", "delta_availability_pct",
                         "evidence_strength_pct", "trend_consistency_pct"):
                if comp not in score.components:
                    conf_ok = False
                    print(f"  ❌ {q!r} missing component {comp}")
            print(f"  ✅ {q!r} -> confidence={score.total} "
                  f"components={ {k: int(v) for k, v in score.components.items()} }")
        except Exception as exc:
            conf_ok = False
            print(f"  ❌ {q!r} confidence raised: {exc}")
    checks["Confidence Score"] = conf_ok

    # --- G. POST /explain endpoint via agent.explain -----------------------
    endpoint_ok = True
    print("\n--- POST /explain (via agent.explain) ---")
    for q in EXAMPLE_QUESTIONS:
        try:
            payload = asyncio.run(agent.explain(q))
            required = ("question", "summary", "possible_reasons", "confidence",
                        "recommendations", "provider")
            missing = [k for k in required if k not in payload]
            if missing:
                endpoint_ok = False
                print(f"  ❌ {q!r} missing top-level keys: {missing}")
                continue
            summary = payload["summary"]
            missing_keys = [k for k in REQUIRED_SUMMARY_KEYS if k not in summary]
            if missing_keys:
                endpoint_ok = False
                print(f"  ❌ {q!r} missing summary keys: {missing_keys}")
                continue
            if not isinstance(payload["possible_reasons"], list) or not payload["possible_reasons"]:
                endpoint_ok = False
                print(f"  ❌ {q!r} no possible_reasons")
                continue
            if not isinstance(payload["recommendations"], list) or not payload["recommendations"]:
                endpoint_ok = False
                print(f"  ❌ {q!r} no recommendations")
                continue
            if not isinstance(payload["confidence"], int):
                endpoint_ok = False
                print(f"  ❌ {q!r} confidence not int")
                continue

            # Pydantic validation (schema must accept the payload)
            try:
                resp = ExplainResponse(**payload)
                _ = ExplainRequest(question=q)
                _ = ExplainSummary(**resp.summary.model_dump())
            except Exception as exc:
                endpoint_ok = False
                print(f"  ❌ {q!r} schema validation: {exc}")
                continue

            print(f"  ✅ {q!r} -> conf={payload['confidence']} reasons={len(payload['possible_reasons'])} "
                  f"recs={len(payload['recommendations'])} schema=OK")
        except Exception as exc:
            endpoint_ok = False
            print(f"  ❌ {q!r} explain() raised: {exc}")

    # Unsupported question returns ValueError (endpoint would 400/422)
    for q in UNSUPPORTED_QUESTIONS:
        if not q.strip():
            continue
        try:
            asyncio.run(agent.explain(q))
            endpoint_ok = False
            print(f"  ❌ {q!r} should have been rejected")
        except ValueError:
            print(f"  ✅ correctly rejected unsupported: {q!r}")
        except Exception as exc:
            print(f"  ⚠️ {q!r} rejected with non-ValueError: {type(exc).__name__}")

    checks["POST /explain"] = endpoint_ok

    # --- H. Logging: explain_events.jsonl was written ----------------------
    log_ok = True
    log_path = Path(__file__).resolve().parents[1] / "logs" / "explain_events.jsonl"
    if log_path.exists():
        try:
            lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            if not lines:
                log_ok = False
            else:
                successful = []
                for ln in lines:
                    try:
                        evt = json.loads(ln)
                        if evt.get("success") and int(evt.get("confidence") or 0) > 0:
                            successful.append(evt)
                    except Exception:
                        continue
                if not successful:
                    log_ok = False
                    print("  ❌ no successful explain events with confidence>0")
                else:
                    last = successful[-1]
                    for key in ("question", "metrics_analyzed", "root_cause",
                                "confidence", "recommendations", "execution_time_ms"):
                        if key not in last:
                            log_ok = False
                            print(f"  ❌ log event missing key {key}")
        except Exception as exc:
            log_ok = False
            print(f"  ❌ log parse failed: {exc}")
    else:
        log_ok = False
        print(f"  ❌ log file not found: {log_path}")
    if log_ok:
        print(f"  ✅ explain_events.jsonl present, last successful event confidence={last.get('confidence')}")
    checks["Logging"] = log_ok

    # --- I. README updated --------------------------------------------------
    readme_ok = True
    readme = Path(__file__).resolve().parents[1] / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for needle in ("POST /explain", "Explain Results Architecture",
                        "Why did European margin decrease", "ConfidenceScorer",
                        "confidence_breakdown"):
            if needle not in text:
                print(f"  ❌ README missing: {needle!r}")
                readme_ok = False
    else:
        readme_ok = False
    checks["README Updated"] = readme_ok

    # --- J. Summary ---------------------------------------------------------
    print()
    print("=========================================")
    print("MetricMind - Day 15 Explain Results")
    print("=========================================")
    print()
    for k, v in checks.items():
        show(k, v)
    print()
    print("-----------------------------------------")
    print("OVERALL RESULT")
    print("-----------------------------------------")
    print()
    overall = all(checks.values())
    print("PASS ✅" if overall else "FAIL ❌")
    print()

    report = []
    report.append("=========================================")
    report.append("MetricMind - Day 15 Explain Results")
    report.append("=========================================")
    report.append("")
    for k, v in checks.items():
        report.append(f"{k.ljust(24)}: {'PASS ✅' if v else 'FAIL ❌'}")
    report.append("")
    report.append("-----------------------------------------")
    report.append("OVERALL RESULT")
    report.append("-----------------------------------------")
    report.append("")
    report.append("PASS ✅" if overall else "FAIL ❌")
    report.append("")
    report_path = Path(__file__).resolve().parents[1] / "logs" / "day15-final-report.txt"
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(f"Report saved -> {report_path}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
