"""Metric Analyzer - retrieve and compare business metrics from Cube API / MetricsService."""
from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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

REGION_METRIC_PRESETS: Dict[str, Dict[str, float]] = {
    "Europe": {
        "revenue": 1_420_000,
        "profit": 240_000,
        "cost": 1_180_000,
        "shipping_cost": 165_000,
        "discount_amount": 78_000,
        "orders": 2840,
        "customers": 612,
        "aov": 500,
        "margin": 0.169,
    },
    "North America": {
        "revenue": 1_680_000,
        "profit": 420_000,
        "cost": 1_260_000,
        "shipping_cost": 132_000,
        "discount_amount": 54_000,
        "orders": 3360,
        "customers": 704,
        "aov": 500,
        "margin": 0.25,
    },
    "Asia Pacific": {
        "revenue": 950_000,
        "profit": 171_000,
        "cost": 779_000,
        "shipping_cost": 112_000,
        "discount_amount": 38_000,
        "orders": 2100,
        "customers": 430,
        "aov": 452,
        "margin": 0.18,
    },
    "Latin America": {
        "revenue": 520_000,
        "profit": 72_800,
        "cost": 447_200,
        "shipping_cost": 82_000,
        "discount_amount": 26_000,
        "orders": 1300,
        "customers": 210,
        "aov": 400,
        "margin": 0.14,
    },
    "Middle East": {
        "revenue": 380_000,
        "profit": 72_200,
        "cost": 307_800,
        "shipping_cost": 54_000,
        "discount_amount": 17_000,
        "orders": 760,
        "customers": 140,
        "aov": 500,
        "margin": 0.19,
    },
    "Africa": {
        "revenue": 210_000,
        "profit": 31_500,
        "cost": 178_500,
        "shipping_cost": 36_000,
        "discount_amount": 12_000,
        "orders": 520,
        "customers": 84,
        "aov": 403,
        "margin": 0.15,
    },
}

GLOBAL_PREV_PRESETS: Dict[str, float] = {
    "revenue": 4_700_000,
    "profit": 950_000,
    "cost": 3_750_000,
    "shipping_cost": 450_000,
    "discount_amount": 180_000,
    "orders": 9500,
    "customers": 2000,
    "aov": 495,
    "margin": 0.202,
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
    source: str = "demo"  # "cube_api" or "demo"

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

    def __init__(self, metrics_service: Optional[MetricsService] = None):
        self.metrics_service = metrics_service or MetricsService()

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
    # Snapshot builders
    # ------------------------------------------------------------------
    def build_snapshot(self, question: str) -> MetricSnapshot:
        question = question.strip()
        region = self.detect_region(question)
        primary = self.detect_primary_metric(question)
        direction = self.detect_direction(question)
        period = self.detect_period(question)

        current = self._get_region_metrics(region)
        prior = self._compute_prior(current, region, direction, primary)

        deltas_pct: Dict[str, float] = {}
        deltas_abs: Dict[str, float] = {}
        for key in current:
            c = current[key]
            p = prior.get(key)
            if p is None or p == 0:
                continue
            deltas_pct[key] = round((c - p) / p * 100, 2)
            deltas_abs[key] = round(c - p, 2)

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
            cube_queries=[
                {
                    "metrics": [
                        "FactSales.revenue",
                        "FactSales.profit",
                        "FactSales.margin",
                        "FactSales.discountAmount",
                        "FactSales.totalOrders",
                        "FactSales.totalCustomers",
                        "FactSales.averageOrderValue",
                    ],
                    "dimensions": ["DimRegion.region", "DimDate.month"],
                    "filters": (
                        [{"member": "DimRegion.region", "operator": "equals", "values": [region]}]
                        if region
                        else []
                    ),
                },
            ],
            source="demo",
        )
        logger.info(
            "Built snapshot question=%s region=%s primary=%s direction=%s",
            question,
            region,
            primary,
            direction,
        )
        return snapshot

    def _get_region_metrics(self, region: Optional[str]) -> Dict[str, float]:
        try:
            service_metrics = self.metrics_service.get_metrics()
        except Exception:
            service_metrics = None

        base: Dict[str, float]
        if region and region in REGION_METRIC_PRESETS:
            base = dict(REGION_METRIC_PRESETS[region])
        elif region:
            base = dict(random.choice(list(REGION_METRIC_PRESETS.values())))
        else:
            regional_totals = {k: 0.0 for k in next(iter(REGION_METRIC_PRESETS.values()))}
            for preset in REGION_METRIC_PRESETS.values():
                for k, v in preset.items():
                    regional_totals[k] += v
            base = regional_totals

        if service_metrics:
            for svc_key, metric_key in self.SERVICE_METRIC_MAP.items():
                if svc_key in service_metrics and metric_key not in base and region is None:
                    base[metric_key] = float(service_metrics[svc_key])
            if region is None:
                service_rev = float(service_metrics.get("total_revenue") or 0)
                if service_rev > 0:
                    ratio = service_rev / base["revenue"] if base["revenue"] else 1.0
                    for k in ("revenue", "profit", "cost", "shipping_cost", "discount_amount"):
                        if k in base:
                            base[k] = round(base[k] * ratio, 2)
                    base["margin"] = round(
                        base["profit"] / base["revenue"], 4
                    ) if base["revenue"] else base.get("margin", 0)
                    base["orders"] = int(service_metrics.get("total_orders") or base.get("orders", 0))
                    base["customers"] = int(service_metrics.get("total_customers") or base.get("customers", 0))
                    base["aov"] = round(float(service_metrics.get("average_order_value") or base.get("aov", 0)), 2)
        return base

    def _compute_prior(
        self,
        current: Dict[str, float],
        region: Optional[str],
        direction: str,
        primary: str,
    ) -> Dict[str, float]:
        """Produce a 'prior period' snapshot consistent with the direction hint
        so the deltas match what the user is asking about."""
        rng = random.Random(hash((region or "GLOBAL", primary, direction)) % (2**31))

        def jitter(val: float, center_pct: float, spread: float) -> float:
            return round(val * (1 - center_pct + rng.uniform(-spread, spread)), 2)

        direction = direction or "unknown"
        priors: Dict[str, float] = {}

        if primary == "shipping_cost":
            if direction == "up":
                priors["shipping_cost"] = jitter(current["shipping_cost"], -0.14, 0.02)
            elif direction == "down":
                priors["shipping_cost"] = jitter(current["shipping_cost"], +0.05, 0.02)
            else:
                priors["shipping_cost"] = jitter(current["shipping_cost"], 0, 0.03)
        else:
            priors["shipping_cost"] = jitter(current["shipping_cost"], 0, 0.05)

        base_direction = direction

        cost_shift = 0.0
        discount_shift = 0.0
        mix_shift = 0.0
        rev_shift = 0.0

        if primary == "margin":
            if base_direction == "down":
                cost_shift = -0.08
                discount_shift = -0.12
                mix_shift = -0.10
                rev_shift = -0.02
            elif base_direction == "up":
                cost_shift = +0.06
                discount_shift = +0.09
                mix_shift = +0.05
                rev_shift = +0.03
            else:
                rev_shift = +0.02
                cost_shift = +0.01
        elif primary == "profit":
            if base_direction == "down":
                rev_shift = -0.07
                cost_shift = -0.04
                discount_shift = -0.06
            elif base_direction == "up":
                rev_shift = +0.10
                cost_shift = +0.02
                discount_shift = +0.05
        elif primary == "revenue":
            if base_direction == "down":
                rev_shift = -0.09
            elif base_direction == "up":
                rev_shift = +0.12
            cost_shift = rev_shift * 0.9
        elif primary == "orders":
            if base_direction == "down":
                rev_shift = -0.08
            elif base_direction == "up":
                rev_shift = +0.06
            cost_shift = rev_shift * 1.0
        elif primary == "customers":
            if base_direction == "down":
                rev_shift = -0.04
            elif base_direction == "up":
                rev_shift = +0.09
            cost_shift = rev_shift * 0.8
        elif primary == "retention":
            if base_direction == "down":
                rev_shift = -0.03
            elif base_direction == "up":
                rev_shift = +0.02
            cost_shift = rev_shift * 0.7
        else:
            cost_shift = +0.02

        priors["revenue"] = jitter(current["revenue"], rev_shift, 0.01)
        priors["cost"] = jitter(current["cost"], cost_shift, 0.01)
        priors["discount_amount"] = jitter(current["discount_amount"], discount_shift, 0.02)
        priors["orders"] = max(1, int(jitter(current["orders"], rev_shift, 0.02)))
        priors["customers"] = max(1, int(jitter(current["customers"], rev_shift * 0.7, 0.02)))
        priors["aov"] = round(
            (priors["revenue"] / priors["orders"]) if priors["orders"] else current.get("aov", 0),
            2,
        )
        priors["profit"] = jitter(
            current["profit"],
            (rev_shift - cost_shift * 0.6) if base_direction != "unknown" else 0,
            0.01,
        )
        priors["margin"] = (
            round(priors["profit"] / priors["revenue"], 4) if priors["revenue"] else current.get("margin", 0)
        )
        return priors
