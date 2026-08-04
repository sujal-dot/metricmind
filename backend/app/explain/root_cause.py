"""Root Cause Analyzer - identify evidence-based drivers of metric changes."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.explain.metric_analyzer import MetricSnapshot

logger = logging.getLogger("metricmind.explain.root_cause")


@dataclass
class RootCauseFinding:
    """A single possible root cause with supporting evidence."""

    reason_text: str
    evidence_metric: str
    evidence_value_pct: float | None
    weight: float  # 0.0 - 1.0, how strong the evidence is
    supported: bool = True


PRIMARY_METRIC_CAUSE_TEMPLATES: dict[str, list[dict[str, object]]] = {
    "margin": [
        {
            "trigger": "shipping_cost",
            "test": lambda d: d is not None and d > 5,
            "text_pos": "Shipping costs increased by {pct:.1f}%, compressing gross margin.",
            "text_neg": "Shipping costs decreased by {pct:.1f}%, helping margin expansion.",
            "weight": 0.8,
        },
        {
            "trigger": "discount_amount",
            "test": lambda d: d is not None and abs(d) > 6,
            "text_pos": "Discounts were higher than the prior period (change of {pct:.1f}%), reducing per-order profitability.",
            "text_neg": "Discounts reduced by {pct:.1f}%, lifting per-order profitability.",
            "weight": 0.75,
        },
        {
            "trigger": "cost",
            "test": lambda d: d is not None and abs(d) > 4,
            "text_pos": "Product / COGS costs rose by {pct:.1f}%, outpacing revenue growth.",
            "text_neg": "Product / COGS costs improved by {pct:.1f}%, improving unit economics.",
            "weight": 0.7,
        },
        {
            "trigger": "revenue",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Revenue grew {pct:.1f}% but was offset by rising expenses.",
            "text_neg": "Revenue contracted {pct:.1f}%, reducing operating leverage.",
            "weight": 0.55,
        },
        {
            "trigger": "aov",
            "test": lambda d: d is not None and abs(d) > 4,
            "text_pos": "Average order value changed {pct:.1f}%, shifting mix toward lower-margin SKUs.",
            "text_neg": "Average order value improved {pct:.1f}%, shifting mix toward higher-margin SKUs.",
            "weight": 0.5,
        },
        {
            "trigger": "customers",
            "test": lambda d: d is not None and abs(d) > 5,
            "text_pos": "Customer mix shifted {pct:.1f}%, with a larger share of new (lower-margin) customers.",
            "text_neg": "Customer base improved {pct:.1f}% with a larger returning-customer share.",
            "weight": 0.4,
        },
    ],
    "revenue": [
        {
            "trigger": "orders",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Order volume changed by {pct:.1f}%, directly driving revenue movement.",
            "text_neg": "Order volume changed by {pct:.1f}%, directly driving revenue movement.",
            "weight": 0.85,
        },
        {
            "trigger": "aov",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Average order value changed {pct:.1f}%, adding to revenue per transaction.",
            "text_neg": "Average order value changed {pct:.1f}%, reducing revenue per transaction.",
            "weight": 0.7,
        },
        {
            "trigger": "customers",
            "test": lambda d: d is not None and abs(d) > 5,
            "text_pos": "Active customer count moved {pct:.1f}%, impacting total addressable demand.",
            "text_neg": "Active customer count moved {pct:.1f}%, impacting total addressable demand.",
            "weight": 0.6,
        },
        {
            "trigger": "discount_amount",
            "test": lambda d: d is not None and abs(d) > 6,
            "text_pos": "Promotional discount activity changed {pct:.1f}%, impacting net price realization.",
            "text_neg": "Promotional discount activity changed {pct:.1f}%, impacting net price realization.",
            "weight": 0.5,
        },
    ],
    "profit": [
        {
            "trigger": "revenue",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Revenue moved {pct:.1f}%, the largest single driver of profit change.",
            "text_neg": "Revenue moved {pct:.1f}%, the largest single driver of profit change.",
            "weight": 0.8,
        },
        {
            "trigger": "cost",
            "test": lambda d: d is not None and abs(d) > 4,
            "text_pos": "COGS / cost of sales changed {pct:.1f}%, widening or narrowing gross margin.",
            "text_neg": "COGS / cost of sales changed {pct:.1f}%, widening or narrowing gross margin.",
            "weight": 0.75,
        },
        {
            "trigger": "shipping_cost",
            "test": lambda d: d is not None and abs(d) > 5,
            "text_pos": "Shipping cost moved {pct:.1f}%, a meaningful P&L line item.",
            "text_neg": "Shipping cost moved {pct:.1f}%, a meaningful P&L line item.",
            "weight": 0.65,
        },
        {
            "trigger": "discount_amount",
            "test": lambda d: d is not None and abs(d) > 5,
            "text_pos": "Discounts moved {pct:.1f}%, affecting net revenue.",
            "text_neg": "Discounts moved {pct:.1f}%, affecting net revenue.",
            "weight": 0.55,
        },
    ],
    "shipping_cost": [
        {
            "trigger": "orders",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Order volume changed {pct:.1f}% — more shipments naturally increase total shipping cost.",
            "text_neg": "Order volume changed {pct:.1f}% — fewer shipments naturally reduce total shipping cost.",
            "weight": 0.8,
        },
        {
            "trigger": "aov",
            "test": lambda d: d is not None and d > 3,
            "text_pos": "Average order value rose {pct:.1f}%, likely correlating with heavier / larger parcels that cost more to ship.",
            "text_neg": "Average order value fell {pct:.1f}%, likely correlating with smaller parcels that cost less to ship.",
            "weight": 0.55,
        },
        {
            "trigger": "revenue",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Revenue activity changed {pct:.1f}%; shipping scales with sales volume.",
            "text_neg": "Revenue activity changed {pct:.1f}%; shipping scales with sales volume.",
            "weight": 0.5,
        },
    ],
    "orders": [
        {
            "trigger": "customers",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Active customer count changed {pct:.1f}%, directly driving orders.",
            "text_neg": "Active customer count changed {pct:.1f}%, directly driving orders.",
            "weight": 0.85,
        },
        {
            "trigger": "discount_amount",
            "test": lambda d: d is not None and abs(d) > 6,
            "text_pos": "Promotional intensity changed {pct:.1f}%, impacting conversion and order count.",
            "text_neg": "Promotional intensity changed {pct:.1f}%, impacting conversion and order count.",
            "weight": 0.6,
        },
        {
            "trigger": "revenue",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Revenue movement of {pct:.1f}% is consistent with the order-volume change.",
            "text_neg": "Revenue movement of {pct:.1f}% is consistent with the order-volume change.",
            "weight": 0.5,
        },
    ],
    "customers": [
        {
            "trigger": "orders",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Order volume changed {pct:.1f}%, consistent with the customer count movement.",
            "text_neg": "Order volume changed {pct:.1f}%, consistent with the customer count movement.",
            "weight": 0.7,
        },
        {
            "trigger": "revenue",
            "test": lambda d: d is not None and abs(d) > 3,
            "text_pos": "Revenue changed {pct:.1f}%, indicating a shift in traffic / acquisition.",
            "text_neg": "Revenue changed {pct:.1f}%, indicating a shift in traffic / acquisition.",
            "weight": 0.5,
        },
        {
            "trigger": "discount_amount",
            "test": lambda d: d is not None and abs(d) > 5,
            "text_pos": "Promotional activity changed {pct:.1f}%, which usually moves new-customer acquisition rates.",
            "text_neg": "Promotional activity changed {pct:.1f}%, which usually moves new-customer acquisition rates.",
            "weight": 0.45,
        },
    ],
    "retention": [
        {
            "trigger": "customers",
            "test": lambda d: d is not None and d < 0,
            "text_pos": "Active customer count dropped {pct:.1f}%, signaling churn / reduced returning orders.",
            "text_neg": "Active customer count rose {pct:.1f}%, signaling better returning-order frequency.",
            "weight": 0.8,
        },
        {
            "trigger": "aov",
            "test": lambda d: d is not None and d < 0,
            "text_pos": "AOV slipped {pct:.1f}%, often a symptom of churn among higher-LTV customers.",
            "text_neg": "AOV grew {pct:.1f}%, often a signal of stronger returning-customer engagement.",
            "weight": 0.55,
        },
        {
            "trigger": "discount_amount",
            "test": lambda d: d is not None and abs(d) > 5,
            "text_pos": "Promotions moved {pct:.1f}%; a heavy promo-only customer base can reduce retention.",
            "text_neg": "Promotions moved {pct:.1f}%; a healthy non-promo mix improves returning behavior.",
            "weight": 0.4,
        },
    ],
}


class RootCauseAnalyzer:
    """Analyze a MetricSnapshot and return evidence-weighted root cause findings."""

    TEMPLATES = PRIMARY_METRIC_CAUSE_TEMPLATES

    def analyze(self, snapshot: MetricSnapshot) -> list[RootCauseFinding]:
        primary = snapshot.primary_metric or "margin"
        templates = self.TEMPLATES.get(primary) or self.TEMPLATES["margin"]

        findings: list[RootCauseFinding] = []

        for template in templates:
            trigger: str = template["trigger"]  # type: ignore[assignment]
            delta_pct = snapshot.deltas_pct.get(trigger)

            if delta_pct is None:
                continue

            test_fn = template["test"]  # type: ignore[assignment]
            if not test_fn(delta_pct):
                continue

            text_pos: str = template["text_pos"]  # type: ignore[assignment]
            text_neg: str = template["text_neg"]  # type: ignore[assignment]
            weight: float = template["weight"]  # type: ignore[assignment]

            abs_delta = abs(delta_pct)
            if delta_pct >= 0:
                reason = text_pos.format(pct=abs_delta)
            else:
                reason = text_neg.format(pct=abs_delta)

            strength_weight = min(1.0, weight + min(abs_delta / 40, 0.2))
            findings.append(
                RootCauseFinding(
                    reason_text=reason,
                    evidence_metric=trigger,
                    evidence_value_pct=delta_pct,
                    weight=round(strength_weight, 3),
                    supported=True,
                )
            )

        findings.sort(key=lambda f: f.weight, reverse=True)

        if not findings:
            default: RootCauseFinding
            if snapshot.direction_hint == "down":
                default = RootCauseFinding(
                    reason_text=(
                        f"No single line item showed a large-enough shift to "
                        f"explain the {primary} movement alone; consider "
                        f"cross-period mix analysis."
                    ),
                    evidence_metric=primary,
                    evidence_value_pct=snapshot.deltas_pct.get(primary),
                    weight=0.25,
                    supported=True,
                )
            elif snapshot.direction_hint == "up":
                default = RootCauseFinding(
                    reason_text=(
                        f"The {primary} improvement appears broadly based across "
                        f"multiple contributing metrics rather than one dominant driver."
                    ),
                    evidence_metric=primary,
                    evidence_value_pct=snapshot.deltas_pct.get(primary),
                    weight=0.25,
                    supported=True,
                )
            else:
                default = RootCauseFinding(
                    reason_text=(
                        "Insufficient period-over-period signal to isolate a root cause; "
                        "more historical data points would improve confidence."
                    ),
                    evidence_metric=primary,
                    evidence_value_pct=snapshot.deltas_pct.get(primary),
                    weight=0.2,
                    supported=True,
                )
            findings = [default]

        logger.info(
            "Root cause analysis for primary=%s produced %d findings (top weight=%.2f)",
            primary,
            len(findings),
            findings[0].weight if findings else 0,
        )
        return findings
