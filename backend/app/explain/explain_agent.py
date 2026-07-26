"""Explain Agent - orchestrates the full Why? / root-cause analysis pipeline."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from app.agents.cube_client import CubeClient
from app.agents.llm_factory import LLMFactory
from app.config.settings import settings
from app.explain.confidence_score import ConfidenceBreakdown, ConfidenceScorer
from app.explain.metric_analyzer import MetricAnalyzer, MetricSnapshot
from app.explain.prompts import EXPLAIN_ANALYST_SYSTEM_PROMPT, WHY_QUESTION_HINTS
from app.explain.recommendation_engine import RecommendationEngine
from app.explain.root_cause import RootCauseAnalyzer, RootCauseFinding

logger = logging.getLogger("metricmind.explain.agent")


class ExplainAgent:
    """Answers "Why?" questions with an evidence-based, structured explanation.

    Pipeline:
        question
          -> why-question detection
          -> MetricAnalyzer (hint extraction + Cube/snapshot)
          -> RootCauseAnalyzer (findings)
          -> RecommendationEngine (actions)
          -> ConfidenceScorer (0-100%)
          -> (optional) LLM synthesis
          -> ExplainResponse dict
    """

    def __init__(
        self,
        llm_provider: Optional[Literal["groq", "openai", "gemini"]] = None,
        use_llm_synthesis: bool = False,
    ) -> None:
        self.provider = llm_provider or settings.llm_provider
        self.use_llm_synthesis = use_llm_synthesis
        self.metric_analyzer = MetricAnalyzer()
        self.root_cause = RootCauseAnalyzer()
        self.recommendations = RecommendationEngine()
        self.confidence = ConfidenceScorer()
        try:
            self.cube_client: Optional[CubeClient] = CubeClient()
        except Exception:
            self.cube_client = None
            logger.warning("CubeClient unavailable - will use analyzer fallbacks")

        self._llm = None

    # ------------------------------------------------------------------
    # Why-question detection
    # ------------------------------------------------------------------
    def is_supported(self, question: str) -> bool:
        q = (question or "").strip().lower()
        if not q:
            return False
        if any(h in q for h in WHY_QUESTION_HINTS):
            return True
        if q.startswith(("why", "how come", "how did")):
            return True
        return any(
            term in q
            for term in (
                " caused ",
                " cause of ",
                " causes ",
                " reason for ",
                " reasons for ",
                " explain why ",
                " explain ",
                " analysis ",
                " root cause ",
            )
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def explain(self, question: str) -> Dict[str, Any]:
        start = time.perf_counter()
        question = (question or "").strip()

        log_event: Dict[str, Any] = {
            "question": question,
            "cube_queries": [],
            "metrics_analyzed": [],
            "root_cause": [],
            "provider": self.provider,
            "confidence": 0,
            "recommendations": [],
            "execution_time_ms": 0,
            "errors": [],
        }

        try:
            if not question:
                raise ValueError("Question cannot be empty.")
            if not self.is_supported(question):
                raise ValueError(
                    "This question type is not supported for root-cause analysis. "
                    "Try phrasing as a Why? question (e.g., 'Why did European margin decrease?')."
                )

            snapshot = self.metric_analyzer.build_snapshot(question)
            log_event["cube_queries"] = snapshot.cube_queries
            log_event["metrics_analyzed"] = list(snapshot.current.keys())

            findings = self.root_cause.analyze(snapshot)
            log_event["root_cause"] = [
                {"reason": f.reason_text, "weight": f.weight, "metric": f.evidence_metric}
                for f in findings
            ]

            recommendations = self.recommendations.recommend(snapshot, findings)
            log_event["recommendations"] = recommendations

            breakdown = self.confidence.score(snapshot, findings)
            log_event["confidence"] = breakdown.total

            response = self._build_response(question, snapshot, findings, recommendations, breakdown)

            if self.use_llm_synthesis:
                try:
                    narrative = await self._synthesize_with_llm(
                        question, snapshot, findings, recommendations, breakdown
                    )
                    response["narrative"] = narrative
                except Exception as exc:  # LLM failure must not break the endpoint
                    logger.warning("LLM synthesis failed: %s", exc)
                    log_event["errors"].append(f"llm_synthesis: {exc}")
                    response["narrative"] = None

            duration = (time.perf_counter() - start) * 1000
            log_event["execution_time_ms"] = round(duration, 1)
            self._write_log(log_event, success=True)
            return response
        except ValueError as exc:
            duration = (time.perf_counter() - start) * 1000
            log_event["execution_time_ms"] = round(duration, 1)
            log_event["errors"].append(str(exc))
            self._write_log(log_event, success=False)
            raise
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            log_event["execution_time_ms"] = round(duration, 1)
            log_event["errors"].append(str(exc))
            self._write_log(log_event, success=False)
            raise RuntimeError(f"Explain engine failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Response builder
    # ------------------------------------------------------------------
    def _build_response(
        self,
        question: str,
        snapshot: MetricSnapshot,
        findings: List[RootCauseFinding],
        recommendations: List[str],
        breakdown: ConfidenceBreakdown,
    ) -> Dict[str, Any]:
        current = snapshot.current or {}
        summary = {
            "region": snapshot.region or "Global",
            "period": snapshot.period,
            "revenue": round(float(current.get("revenue") or 0), 2),
            "cost": round(float(current.get("cost") or 0), 2),
            "shipping_cost": round(float(current.get("shipping_cost") or 0), 2),
            "discount_amount": round(float(current.get("discount_amount") or 0), 2),
            "profit": round(float(current.get("profit") or 0), 2),
            "margin": round(float(current.get("margin") or 0) * 100, 2),
            "orders": int(current.get("orders") or 0),
            "customers": int(current.get("customers") or 0),
            "aov": round(float(current.get("aov") or 0), 2),
            "primary_metric": snapshot.primary_metric,
            "direction_hint": snapshot.direction_hint,
            "period_deltas_pct": snapshot.deltas_pct,
            "period_deltas_abs": snapshot.deltas_abs,
        }
        possible_reasons = [f.reason_text for f in findings]
        return {
            "question": question,
            "summary": summary,
            "possible_reasons": possible_reasons,
            "confidence": breakdown.total,
            "confidence_breakdown": breakdown.components,
            "recommendations": recommendations,
            "provider": self.provider,
            "data_source": snapshot.source,
        }

    # ------------------------------------------------------------------
    # LLM synthesis
    # ------------------------------------------------------------------
    async def _synthesize_with_llm(
        self,
        question: str,
        snapshot: MetricSnapshot,
        findings: List[RootCauseFinding],
        recommendations: List[str],
        breakdown: ConfidenceBreakdown,
    ) -> Optional[str]:
        if self._llm is None:
            self._llm = LLMFactory.create_llm(provider=self.provider, temperature=0.1)

        analysis_payload = json.dumps(
            {
                "question": question,
                "snapshot_metrics": snapshot.current,
                "deltas_pct": snapshot.deltas_pct,
                "root_cause_findings": [asdict(f) for f in findings],
                "recommendations": recommendations,
                "confidence": breakdown.total,
                "confidence_breakdown": breakdown.components,
            },
            default=str,
        )
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=EXPLAIN_ANALYST_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "ANALYSIS RESULTS (strictly base your answer on these; do NOT invent values):\n"
                    + analysis_payload
                    + "\n\nUser question: "
                    + question
                    + "\n\nReply only with a clear, structured business explanation in plain Markdown."
                )
            ),
        ]
        response = await self._llm.ainvoke(messages)
        content = getattr(response, "content", "")
        if isinstance(content, list):
            parts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in content]
            return "\n".join(parts).strip() or None
        return (str(content).strip()) or None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _write_log(self, event: Dict[str, Any], success: bool) -> None:
        try:
            log_path = Path(__file__).resolve().parents[2] / "logs"
            log_path.mkdir(parents=True, exist_ok=True)
            path = log_path / "explain_events.jsonl"
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"success": success, **event}, default=str) + "\n")
        except Exception as exc:
            logger.warning("Failed to write explain log: %s", exc)
