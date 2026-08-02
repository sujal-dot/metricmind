"""Metric Analyzer - retrieve and compare business metrics from Cube API / MetricsService."""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.agents.cube_client import CubeClient
from app.services.metrics_service import MetricsService

logger = logging.getLogger("metricmind.explain.metric_analyzer")

REGION_ALIASES: Dict[str, List[str]] = {
    "Europe": ["europe", "european", "eu"],
    "North America": ["north america", "na", "us", "usa", "canada", "united states"],
    "Asia Pacific": ["asia pacific", "apac", "asia", "japan", "china", "australia", "india"],
    "Latin America": ["latin america", "latam", "south america", "brazil", "mexico"],
    "Middle East": ["middle east", "mena", "uae", "saudi"],
    "Africa": ["africa", "african", "nigeria", "egypt", "south africa"],
}


@dataclass
class MetricSnapshot:
    """A comparable snapshot of all relevant metrics for an explain query."""

    question: str
    region: Optional[str] = None
    period: Optional[str] = None
    primary_metric: str = "margin"
    direction_hint: str = "unknown"

    current: Dict[str, float] = field(default_factory=dict)
    prior: Dict[str, float] = field(default_factory=dict)
    deltas_pct: Dict[str, float] = field(default_factory=dict)
    deltas_abs: Dict[str, float] = field(default_factory=dict)

    cube_queries: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "demo"

    def get(self, key: str) -> Optional[float]:
        return self.current.get(key)

    def pct_change(self, key: str) -> Optional[float]:
        return self.deltas_pct.get(key)

    def abs_change(self, key: str) -> Optional[float]:
        return self.deltas_abs.get(key)


class MetricAnalyzer:
    """Extract region/metric/period hints from question and build comparable snapshots."""

    SERVICE_METRIC_MAP: Dict[str, str] = {
        "total_revenue": "revenue",
        "total_profit": "profit",
        "profit_margin": "margin",
        "total_orders": "orders",
        "total_customers": "customers",
        "average_order_value": "aov",
    }

    METRIC_HINTS: Tuple[Tuple[str, str], ...] = (
        ("shipping costs", "shipping_cost"),
        ("shipping cost", "shipping_cost"),
        ("logistics cost", "shipping_cost"),
        ("customer retention", "retention"),
        ("average order value", "aov"),
        ("profit margin", "margin"),
        ("aov", "aov"),
        ("margin", "margin"),
        ("discounts", "discount_amount"),
        ("discount", "discount_amount"),
        ("revenue", "revenue"),
        ("sales", "revenue"),
        ("profit", "profit"),
        ("order count", "orders"),
        ("orders", "orders"),
        ("customer count", "customers"),
        ("customers", "customers"),
        ("quantity", "quantity"),
        ("costs", "cost"),
        ("cost", "cost"),
    )

    DIRECTION_HINTS: Tuple[Tuple[str, str], ...] = (
        ("decrease", "down"),
        ("decreased", "down"),
        ("drop", "down"),
        ("dropped", "down"),
        ("fell", "down"),
        ("falling", "down"),
        ("fall", "down"),
        ("decline", "down"),
        ("declining", "down"),
        ("declined", "down"),
        ("slower", "down"),
        ("slow", "down"),
        ("lower", "down"),
        ("high", "up"),
        ("higher", "up"),
        ("increase", "up"),
        ("increased", "up"),
        ("growing", "up"),
        ("grew", "up"),
        ("growth", "up"),
        ("rise", "up"),
        ("risen", "up"),
        ("outperform", "up"),
        ("outperforming", "up"),
        ("better", "up"),
    )

    CUBE_MEASURE_MAP: Dict[str, str] = {
        "FactSales.revenue": "revenue",
        "FactSales.profit": "profit",
        "FactSales.totalOrders": "orders",
        "FactSales.totalCustomers": "customers",
        "FactSales.averageOrderValue": "aov",
        "FactSales.margin": "margin_ratio",
        "FactSales.discountAmount": "discount_amount",
        "FactSales.cost": "cost",
    }

    def __init__(self, metrics_service: Optional[MetricsService] = None):
        self.metrics_service = metrics_service or MetricsService()
        try:
            self.cube_client: Optional[CubeClient] = CubeClient()
        except Exception:
            self.cube_client = None
            logger.warning("CubeClient unavailable in MetricAnalyzer - will use fallbacks")

    # ------------------------------------------------------------------
    # Why-question detection
    # ------------------------------------------------------------------
    @staticmethod
    def is_why_question(question: str) -> bool:
        q = question.strip().lower()
        if not q:
            return False
        if q.startswith(("why ", "why'd ", "why has ", "why have ")):
            return True
        return any(
            hint in q
            for hint in (
                "why ",
                "what caused ",
                "causes of ",
                "reason for ",
                "reasons for ",
                "explain why ",
                "how come ",
            )
        )

    # ------------------------------------------------------------------
    # Hint extraction
    # ------------------------------------------------------------------
    def detect_region(self, question: str) -> Optional[str]:
        q = question.lower()
        for region, aliases in REGION_ALIASES.items():
            if any(a in q for a in aliases):
                return region
        return None

    def detect_primary_metric(self, question: str) -> str:
        q = question.lower()
        for phrase, metric in self.METRIC_HINTS:
            if phrase in q:
                return metric
        return "margin"

    def detect_direction(self, question: str) -> str:
        q = question.lower()
        for phrase, direction in self.DIRECTION_HINTS:
            if phrase in q:
                return direction
        return "unknown"

    def detect_period(self, question: str) -> Optional[str]:
        q = question.lower()
        m = re.search(r"\b(20\d{2})\b", q)
        if m:
            return f"year {m.group(1)}"
        for period in ("last month", "this month", "last quarter", "this quarter",
                        "last year", "this year", "last week", "today", "yesterday"):
            if period in q:
                return period
        return None

    # ------------------------------------------------------------------
    # Convenience API for QA/test pipelines
    # ------------------------------------------------------------------
    def detect_hints(self, question: str) -> Dict[str, Any]:
        """Aggregate all hint detectors into a single hints dict."""
        region = self.detect_region(question)
        primary_metric = self.detect_primary_metric(question)
        direction_hint = self.detect_direction(question)
        period = self.detect_period(question)
        return {
            "region": region,
            "primary_metric": primary_metric,
            "direction_hint": direction_hint,
            "period": period,
            "is_why": MetricAnalyzer.is_why_question(question),
        }

    async def analyze(
        self,
        hints: Optional[Dict[str, Any]] = None,
        question: Optional[str] = None,
    ) -> Tuple[MetricSnapshot, List["RootCauseFinding"], int, "ConfidenceBreakdown", List[str], Dict[str, Any]]:
        """Full evidence-based analysis path: snapshot → findings → score → recs.

        Accepts either a pre-built hints dict (region/metric/period/direction) or a
        raw question. Returns the same tuple the ExplainAgent assembles internally,
        avoiding any LLM call. Used by QA and for quick CLI inspections.
        """
        from app.explain.root_cause import RootCauseAnalyzer
        from app.explain.recommendation_engine import RecommendationEngine
        from app.explain.confidence_score import ConfidenceScorer

        if hints is None:
            if question is None:
                raise ValueError("analyze requires either hints dict or question string")
            hints = self.detect_hints(question)
        region = hints.get("region")
        primary_metric = hints.get("primary_metric") or "margin"
        direction_hint = hints.get("direction_hint") or "unknown"
        period = hints.get("period")

        q_for_snapshot = question or f"why {primary_metric} {direction_hint} in {region or 'global'}"
        snapshot = await self.build_snapshot(q_for_snapshot)
        if region:
            snapshot.region = region
        if period:
            snapshot.period = period
        if primary_metric:
            snapshot.primary_metric = primary_metric
        if direction_hint and direction_hint != "unknown":
            snapshot.direction_hint = direction_hint

        findings = RootCauseAnalyzer().analyze(snapshot)
        breakdown = ConfidenceScorer().score(snapshot, findings)
        recs = RecommendationEngine().recommend(snapshot, findings)
        reasons_meta = {
            "findings": [
                {
                    "reason": f.reason_text,
                    "evidence_metric": f.evidence_metric,
                    "evidence_value_pct": f.evidence_value_pct,
                    "weight": f.weight,
                }
                for f in findings
            ],
        }
        return snapshot, findings, breakdown.total, breakdown, recs, reasons_meta

    def analyze_sync(
        self,
        hints: Optional[Dict[str, Any]] = None,
        question: Optional[str] = None,
    ) -> Tuple[MetricSnapshot, List["RootCauseFinding"], int, "ConfidenceBreakdown", List[str], Dict[str, Any]]:
        """Synchronous wrapper for analyze() — runs via asyncio.run()."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return loop.run_until_complete(self.analyze(hints=hints, question=question))
        except RuntimeError:
            pass
        return asyncio.run(self.analyze(hints=hints, question=question))

    # ------------------------------------------------------------------
    # Snapshot builders
    # ------------------------------------------------------------------

    @staticmethod
    def _default_date_ranges() -> Tuple[Tuple[date, date], Tuple[date, date]]:
        """Return (current_date_range, prior_date_range) for Cube queries.

        Default window: current = last 90 days, prior = 90 days before that.
        """
        today = date.today()
        current_to = today
        current_from = today - timedelta(days=89)
        prior_to = current_from - timedelta(days=1)
        prior_from = prior_to - timedelta(days=89)
        return (current_from, current_to), (prior_from, prior_to)

    def _build_cube_query(
        self,
        region: Optional[str],
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Build a Cube.dev query dict for measures + region filter + time range."""
        measures = [
            "FactSales.revenue",
            "FactSales.profit",
            "FactSales.totalOrders",
            "FactSales.totalCustomers",
            "FactSales.averageOrderValue",
            "FactSales.margin",
            "FactSales.discountAmount",
            "FactSales.cost",
        ]

        filters: List[Dict[str, Any]] = []
        if region:
            filters.append({
                "member": "DimRegion.region",
                "operator": "equals",
                "values": [region],
            })

        time_dimensions: List[Dict[str, Any]] = []
        if date_from and date_to:
            time_dimensions.append({
                "dimension": "DimDate.fullDate",
                "dateRange": [date_from.isoformat(), date_to.isoformat()],
            })

        return {
            "measures": measures,
            "filters": filters,
            "timeDimensions": time_dimensions,
        }

    @staticmethod
    def _estimate_missing(metrics: Dict[str, float]) -> Dict[str, float]:
        """Cross-derive missing metrics from available ones. Never returns empty dict."""
        m = dict(metrics)

        revenue = m.get("revenue", 0.0)
        profit = m.get("profit", 0.0)
        cost = m.get("cost", 0.0)
        orders = m.get("orders", 0)
        aov = m.get("aov", 0.0)
        margin_ratio = m.get("margin_ratio", 0.0)
        discount_amount = m.get("discount_amount", 0.0)

        if revenue == 0 and aov > 0 and orders > 0:
            revenue = aov * orders
            m["revenue"] = revenue
        if profit == 0 and revenue > 0 and margin_ratio > 0:
            profit = revenue * margin_ratio
            m["profit"] = profit
        if profit == 0 and revenue > 0 and cost > 0 and revenue > cost:
            profit = revenue - cost
            m["profit"] = profit
        if cost == 0 and revenue > 0 and profit > 0:
            cost = revenue - profit
            m["cost"] = cost
        if margin_ratio == 0 and revenue > 0 and profit > 0:
            margin_ratio = profit / revenue
            m["margin_ratio"] = margin_ratio
        if aov == 0 and orders > 0 and revenue > 0:
            aov = revenue / orders
            m["aov"] = aov
        if orders == 0 and aov > 0 and revenue > 0:
            orders = int(round(revenue / aov))
            m["orders"] = orders

        if discount_amount == 0 and revenue > 0:
            discount_amount = round(revenue * 0.03, 2)
            m["discount_amount"] = discount_amount

        shipping_cost = m.get("shipping_cost", 0.0)
        if shipping_cost == 0 and revenue > 0:
            shipping_cost = round(revenue * 0.10, 2)
            m["shipping_cost"] = shipping_cost

        customers = m.get("customers", 0)
        if customers == 0 and orders > 0:
            customers = max(1, int(round(orders * 0.35)))
            m["customers"] = customers

        margin = m.get("margin", 0.0)
        if margin == 0 and margin_ratio > 0:
            margin = margin_ratio
            m["margin"] = margin
        if margin == 0 and revenue > 0 and profit > 0:
            margin = profit / revenue
            m["margin"] = margin

        for key in ("revenue", "profit", "cost", "shipping_cost", "discount_amount", "aov"):
            if key in m and isinstance(m[key], (int, float)):
                m[key] = float(round(m[key], 2))
        if "orders" in m:
            m["orders"] = int(m["orders"])
        if "customers" in m:
            m["customers"] = int(m["customers"])
        if "margin" in m and m["margin"] > 1:
            m["margin"] = m["margin"] / 100.0
        if "margin_ratio" in m and m["margin_ratio"] > 1:
            m["margin_ratio"] = m["margin_ratio"] / 100.0

        if not m:
            fallback_rev = 1_000_000.0
            m = {
                "revenue": fallback_rev,
                "profit": round(fallback_rev * 0.20, 2),
                "cost": round(fallback_rev * 0.80, 2),
                "shipping_cost": round(fallback_rev * 0.10, 2),
                "discount_amount": round(fallback_rev * 0.03, 2),
                "orders": 2000,
                "customers": 700,
                "aov": round(fallback_rev / 2000, 2),
                "margin": 0.20,
                "margin_ratio": 0.20,
            }
            logger.warning("MetricAnalyzer fallback to fully-estimated baseline metrics")
        return m

    async def _run_cube_query(
        self,
        query: Dict[str, Any],
    ) -> Tuple[Dict[str, float], Optional[Dict[str, Any]]]:
        """Run a Cube query and extract mapped metrics. Returns (metrics, trace_info_or_None)."""
        if self.cube_client is None:
            return {}, None
        try:
            response = await self.cube_client.load(query)
            data_rows = response.get("data") or [{}]
            row = data_rows[0] if data_rows else {}
            extracted: Dict[str, float] = {}
            for cube_key, internal_key in self.CUBE_MEASURE_MAP.items():
                if cube_key in row and row[cube_key] is not None:
                    try:
                        extracted[internal_key] = float(row[cube_key])
                    except (TypeError, ValueError):
                        continue
            internal_orders = extracted.get("orders", 0.0)
            if internal_orders > 0 and abs(internal_orders - int(internal_orders)) < 0.5:
                extracted["orders"] = float(int(round(internal_orders)))
            internal_customers = extracted.get("customers", 0.0)
            if internal_customers > 0 and abs(internal_customers - int(internal_customers)) < 0.5:
                extracted["customers"] = float(int(round(internal_customers)))
            trace_info = {
                "query": query,
                "response_sample_keys": list(row.keys()),
                "extracted_metrics": list(extracted.keys()),
                "row": row,
            }
            return extracted, trace_info
        except Exception as exc:
            logger.warning("MetricAnalyzer Cube query failed: %s", exc)
            return {}, None

    async def build_snapshot(self, question: str) -> MetricSnapshot:
        question = question.strip()
        region = self.detect_region(question)
        primary = self.detect_primary_metric(question)
        direction = self.detect_direction(question)
        period = self.detect_period(question)

        (cur_from, cur_to), (prior_from, prior_to) = self._default_date_ranges()

        current_query = self._build_cube_query(region, cur_from, cur_to)
        prior_query = self._build_cube_query(region, prior_from, prior_to)

        current_raw, current_trace = await self._run_cube_query(current_query)
        prior_raw, prior_trace = await self._run_cube_query(prior_query)

        cube_queries: List[Dict[str, Any]] = []
        if current_trace is not None:
            cube_queries.append({
                "phase": "current",
                "query": current_trace["query"],
                "row": current_trace["row"],
            })
        else:
            cube_queries.append({
                "phase": "current",
                "query": current_query,
                "row": None,
                "error": "cube_load_failed",
            })
        if prior_trace is not None:
            cube_queries.append({
                "phase": "prior",
                "query": prior_trace["query"],
                "row": prior_trace["row"],
            })
        else:
            cube_queries.append({
                "phase": "prior",
                "query": prior_query,
                "row": None,
                "error": "cube_load_failed",
            })

        current_ok = bool(current_raw and any(v and v > 0 for v in current_raw.values()))
        prior_ok = bool(prior_raw and any(v and v > 0 for v in prior_raw.values()))

        if not current_ok:
            try:
                svc_result = await self.metrics_service.get_metrics(
                    date_from=cur_from,
                    date_to=cur_to,
                    region=region,
                )
                for svc_key, internal_key in self.SERVICE_METRIC_MAP.items():
                    if svc_key in svc_result and internal_key not in current_raw:
                        current_raw[internal_key] = float(svc_result[svc_key])
                        if svc_key == "profit_margin" and current_raw[internal_key] > 1:
                            current_raw[internal_key] = current_raw[internal_key] / 100.0
            except Exception as exc:
                logger.warning("MetricAnalyzer metrics_service fallback for current failed: %s", exc)

        if not prior_ok:
            try:
                svc_result = await self.metrics_service.get_metrics(
                    date_from=prior_from,
                    date_to=prior_to,
                    region=region,
                )
                for svc_key, internal_key in self.SERVICE_METRIC_MAP.items():
                    if internal_key not in prior_raw or prior_raw.get(internal_key, 0) == 0:
                        prior_raw[internal_key] = float(svc_result[svc_key])
                        if svc_key == "profit_margin" and prior_raw[internal_key] > 1:
                            prior_raw[internal_key] = prior_raw[internal_key] / 100.0
            except Exception as exc:
                logger.warning("MetricAnalyzer metrics_service fallback for prior failed: %s", exc)

        current = self._estimate_missing(current_raw)
        prior = self._estimate_missing(prior_raw)

        if not prior and current:
            rev_ratio = 0.92
            profit_ratio = 0.88
            prior = {}
            for k, v in current.items():
                if k in ("margin", "margin_ratio"):
                    prior[k] = v
                elif k in ("orders", "customers"):
                    prior[k] = max(1, int(round(v * rev_ratio)))
                else:
                    if k == "profit":
                        prior[k] = round(v * profit_ratio, 2)
                    else:
                        prior[k] = round(v * rev_ratio, 2)
            logger.warning("MetricAnalyzer: prior period unavailable, using proportional estimate from current")

        deltas_pct: Dict[str, float] = {}
        deltas_abs: Dict[str, float] = {}
        for key in current:
            c = float(current[key])
            p = prior.get(key)
            if p is None:
                continue
            p = float(p)
            if p == 0 and c == 0:
                continue
            deltas_abs[key] = round(c - p, 2)
            if p != 0:
                deltas_pct[key] = round((c - p) / abs(p) * 100, 2)
            elif c != 0:
                deltas_pct[key] = 100.0 if c > 0 else -100.0

        current_after_ok = bool(current_raw and any(v and v > 0 for v in current_raw.values()))
        prior_after_ok = bool(prior_raw and any(v and v > 0 for v in prior_raw.values()))

        if current_after_ok and prior_after_ok:
            source = "cube_api"
        elif current_after_ok or prior_after_ok:
            source = "cube_api_partial"
        else:
            source = "demo"

        snapshot = MetricSnapshot(
            question=question,
            region=region,
            period=period,
            primary_metric=primary,
            direction_hint=direction,
            current=current,
            prior=prior,
            deltas_pct=deltas_pct,
            deltas_abs=deltas_abs,
            cube_queries=cube_queries,
            source=source,
        )
        logger.info(
            "Built snapshot question=%s region=%s primary=%s direction=%s source=%s",
            question,
            region,
            primary,
            direction,
            source,
        )
        return snapshot

    def build_snapshot_sync(self, question: str) -> MetricSnapshot:
        """Synchronous wrapper for build_snapshot() — runs via asyncio.run()."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return loop.run_until_complete(self.build_snapshot(question))
        except RuntimeError:
            pass
        return asyncio.run(self.build_snapshot(question))
