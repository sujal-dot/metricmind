"""Recommendation Engine - generate actionable business recommendations from findings."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from app.explain.metric_analyzer import MetricSnapshot
from app.explain.root_cause import RootCauseFinding

logger = logging.getLogger("metricmind.explain.recommendations")


@dataclass
class Recommendation:
    text: str
    priority: int  # 1 (highest) - 5
    trigger_metric: str
    supported: bool = True


METRIC_RECOMMENDATION_BANK: Dict[str, List[Dict[str, object]]] = {
    "shipping_cost": [
        {
            "test": lambda d: d is not None and d > 3,
            "priority": 1,
            "text": "Review shipping partners and negotiate rates with 2–3 carriers to reduce per-parcel cost.",
        },
        {
            "test": lambda d: d is not None and d > 6,
            "priority": 2,
            "text": "Consolidate small orders and introduce a free-shipping threshold to cut shipping density.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Optimize fulfillment geography by routing orders from the warehouse closest to the customer.",
        },
        {
            "test": lambda d: d is not None and d < -3,
            "priority": 3,
            "text": "Validate that lower shipping spend is not coming from slower delivery that can hurt NPS.",
        },
    ],
    "discount_amount": [
        {
            "test": lambda d: d is not None and d > 5,
            "priority": 1,
            "text": "Reduce excessive promotional discounts; replace blanket %-off with targeted loyalty offers.",
        },
        {
            "test": lambda d: d is not None and d > 10,
            "priority": 2,
            "text": "Audit coupon-stacking and price-match overrides at the order line level.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Shift discount mix from %-off to bundling and gift-with-purchase to protect margin.",
        },
    ],
    "cost": [
        {
            "test": lambda d: d is not None and d > 4,
            "priority": 1,
            "text": "Review supplier costs; run a structured RFQ with 3+ vendors for top SKUs.",
        },
        {
            "test": lambda d: d is not None and d > 7,
            "priority": 2,
            "text": "Optimize high-cost product pricing or sunset low-margin SKUs.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Improve inventory planning (safety stock + reorder points) to cut rush / expedite costs.",
        },
    ],
    "revenue": [
        {
            "test": lambda d: d is not None and d < 0,
            "priority": 1,
            "text": "Increase marketing investment in underperforming regions / channels with proven CAC payback.",
        },
        {
            "test": lambda d: d is not None and d < -5,
            "priority": 2,
            "text": "Launch a win-back campaign for churned customers using retention cohorts.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Double down on the top 20% of SKUs / segments that drive 80% of gross profit.",
        },
    ],
    "margin": [
        {
            "test": lambda d: d is not None and d < 0,
            "priority": 1,
            "text": "Re-price low-margin SKUs and introduce a tiered pricing / volume-discount structure.",
        },
        {
            "test": lambda d: True,
            "priority": 2,
            "text": "Shift product mix toward high-margin categories via merchandising, search, and recommendations.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Monitor regional logistics expenses weekly with a cost-per-order dashboard.",
        },
    ],
    "profit": [
        {
            "test": lambda d: True,
            "priority": 2,
            "text": "Focus on high-margin products; reallocate marketing spend to profitable segments.",
        },
        {
            "test": lambda d: d is not None and d < 0,
            "priority": 1,
            "text": "Stabilize COGS and discount depth first before chasing additional volume.",
        },
    ],
    "orders": [
        {
            "test": lambda d: d is not None and d < 0,
            "priority": 1,
            "text": "Investigate conversion funnel drop-offs; run cart-recovery experiments.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Improve customer retention with post-purchase nurture and loyalty benefits.",
        },
    ],
    "customers": [
        {
            "test": lambda d: d is not None and d < 0,
            "priority": 1,
            "text": "Improve customer retention: personalize outreach and reduce churn with loyalty programs.",
        },
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Increase marketing in underpenetrated regions with the strongest LTV:CAC ratios.",
        },
    ],
    "retention": [
        {
            "test": lambda d: True,
            "priority": 1,
            "text": "Improve customer retention with a structured loyalty program and post-purchase nurture.",
        },
        {
            "test": lambda d: True,
            "priority": 2,
            "text": "Segment customers by cohort tenure; target the churn-prone segment with reactive offers.",
        },
    ],
    "aov": [
        {
            "test": lambda d: True,
            "priority": 3,
            "text": "Improve average order value with cross-sell, bundles, and product recommendations at checkout.",
        },
    ],
}


class RecommendationEngine:
    """Generate up to ~5 actionable recommendations from snapshot + findings."""

    def recommend(
        self,
        snapshot: MetricSnapshot,
        findings: List[RootCauseFinding],
    ) -> List[str]:
        triggers = [f.evidence_metric for f in findings if f.weight >= 0.3]
        if snapshot.primary_metric not in triggers:
            triggers.insert(0, snapshot.primary_metric)

        seen: set = set()
        recs: List[Recommendation] = []

        for metric in triggers:
            deltas = snapshot.deltas_pct or {}
            delta = deltas.get(metric)
            templates = METRIC_RECOMMENDATION_BANK.get(metric) or []
            for template in templates:
                test_fn = template["test"]  # type: ignore[assignment]
                if not test_fn(delta):
                    continue
                text: str = template["text"]  # type: ignore[assignment]
                if text in seen:
                    continue
                seen.add(text)
                recs.append(
                    Recommendation(
                        text=text,
                        priority=template["priority"],  # type: ignore[arg-type]
                        trigger_metric=metric,
                        supported=True,
                    )
                )
                if len(recs) >= 8:
                    break
            if len(recs) >= 8:
                break

        if not recs:
            recs.append(
                Recommendation(
                    text="Continue monitoring key metrics weekly; set alerts when movement exceeds ±5%.",
                    priority=3,
                    trigger_metric=snapshot.primary_metric,
                )
            )

        recs.sort(key=lambda r: (r.priority, -len(triggers) if r.trigger_metric in triggers else 99))
        texts = [r.text for r in recs[:5]]

        logger.info(
            "Generated %d recommendations for primary=%s (returning top %d)",
            len(recs),
            snapshot.primary_metric,
            len(texts),
        )
        return texts
