"""Confidence Score module - 0-100% score based on data completeness & evidence."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from app.explain.metric_analyzer import MetricSnapshot
from app.explain.root_cause import RootCauseFinding

logger = logging.getLogger("metricmind.explain.confidence")


@dataclass
class ConfidenceBreakdown:
    data_completeness: float
    delta_availability: float
    evidence_strength: float
    trend_consistency: float
    total: int

    @property
    def components(self) -> dict:
        return {
            "data_completeness_pct": round(self.data_completeness, 1),
            "delta_availability_pct": round(self.delta_availability, 1),
            "evidence_strength_pct": round(self.evidence_strength, 1),
            "trend_consistency_pct": round(self.trend_consistency, 1),
        }


EXPECTED_KEYS = (
    "revenue",
    "profit",
    "margin",
    "orders",
    "customers",
    "cost",
    "shipping_cost",
    "discount_amount",
    "aov",
)


class ConfidenceScorer:
    """Compute a 0-100% confidence score from snapshot + findings."""

    def score(
        self,
        snapshot: MetricSnapshot,
        findings: List[RootCauseFinding],
    ) -> ConfidenceBreakdown:
        data_completeness = self._data_completeness(snapshot)
        delta_availability = self._delta_availability(snapshot)
        evidence_strength = self._evidence_strength(findings)
        trend_consistency = self._trend_consistency(snapshot, findings)
        total_raw = (
            data_completeness * 0.30
            + delta_availability * 0.25
            + evidence_strength * 0.30
            + trend_consistency * 0.15
        )
        total = int(round(max(20.0, min(100.0, total_raw))))
        breakdown = ConfidenceBreakdown(
            data_completeness=round(data_completeness, 2),
            delta_availability=round(delta_availability, 2),
            evidence_strength=round(evidence_strength, 2),
            trend_consistency=round(trend_consistency, 2),
            total=total,
        )
        logger.info(
            "Confidence score=%d components=%s",
            breakdown.total,
            breakdown.components,
        )
        return breakdown

    def _data_completeness(self, snapshot: MetricSnapshot) -> float:
        current = snapshot.current or {}
        present = sum(1 for k in EXPECTED_KEYS if current.get(k) is not None)
        return (present / len(EXPECTED_KEYS)) * 100

    def _delta_availability(self, snapshot: MetricSnapshot) -> float:
        deltas = snapshot.deltas_pct or {}
        present = sum(1 for k in EXPECTED_KEYS if deltas.get(k) is not None)
        return (present / len(EXPECTED_KEYS)) * 100

    def _evidence_strength(self, findings: List[RootCauseFinding]) -> float:
        if not findings:
            return 25.0
        top = findings[0].weight if findings else 0.0
        avg = sum(f.weight for f in findings) / max(1, len(findings))
        strong_count = sum(1 for f in findings if f.weight >= 0.5)
        strong_bonus = min(40, strong_count * 10)
        base = (top * 0.6 + avg * 0.4) * 100
        return min(100, base + strong_bonus * 0.3)

    def _trend_consistency(
        self,
        snapshot: MetricSnapshot,
        findings: List[RootCauseFinding],
    ) -> float:
        direction = snapshot.direction_hint or "unknown"
        primary = snapshot.primary_metric or "margin"
        delta = snapshot.deltas_pct.get(primary)

        if delta is None:
            return 50.0

        hinted_up = direction == "up"
        hinted_down = direction == "down"
        delta_up = delta > 0

        matches_hint = (
            (hinted_up and delta_up)
            or (hinted_down and not delta_up)
            or direction == "unknown"
        )

        consistency_base = 70 if matches_hint else 35

        alignments = 0
        checked = 0
        for finding in findings:
            if finding.evidence_value_pct is None:
                continue
            checked += 1
            if finding.weight >= 0.5:
                alignments += 1

        alignment_bonus = (alignments / max(1, checked)) * 30 if checked > 0 else 15
        return min(100, consistency_base + alignment_bonus)
