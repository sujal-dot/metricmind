"""Detect expensive / over-broad analytics queries.

Heuristics here operate only on the natural-language question text — they block
questions that would request "all the data" before any agent work is done.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Phrases that ask for the entire dataset -------------------------------------
DATA_DUMP_PHRASES: tuple[str, ...] = (
    "every order ever",
    "all orders ever",
    "all transactions ever",
    "entire database",
    "entire dataset",
    "entire table",
    "entire raw data",
    "complete raw data",
    "all the raw data",
    "all raw data",
    "all the transactions",
    "all transactions",
    "all the orders",
    "export all records",
    "export all the records",
    "export everything",
    "export entire",
    "export all data",
    "dump all",
    "dump the database",
    "backup all",
    "download all orders",
    "download all data",
    "download all transactions",
    "download every",
    "show all orders",
    "show every order",
    "return every order",
    "return all orders",
    "return all transactions",
    "return all the data",
    "all records ever",
    "all rows",
    "every row",
    "every record",
    "all records",
)

# Numeric "give me millions of rows" hints -------------------------------------
LARGE_COUNT_PATTERN = re.compile(
    r"\b(?:show|return|get|export|download|list)\s+(?:(?:top|first|last)\s+)?(\d{4,}|1\s*m(?:illion)?|[2-9]\s*m(?:illion)?)\b",
    re.IGNORECASE,
)

SIZE_UNIT_PHRASES: tuple[str, ...] = (
    "million rows",
    "millions of rows",
    "millions of records",
    "10 million",
    "10m rows",
    "5 million",
    "billions",
)

# Filter indicators — if a question contains these, we consider it narrowed -----
NARROWING_INDICATORS: tuple[str, ...] = (
    "last month",
    "this month",
    "last week",
    "this week",
    "last year",
    "this year",
    "last quarter",
    "this quarter",
    "yesterday",
    "today",
    " in january",
    " in february",
    " in march",
    " in april",
    " in may",
    " in june",
    " in july",
    " in august",
    " in september",
    " in october",
    " in november",
    " in december",
    " by region",
    "by region",
    " by category",
    "by category",
    " by product",
    "by product",
    " by customer",
    "by customer",
    " for europe",
    " for north america",
    " for asia",
    "in europe",
    "in north america",
    "in the us",
    "in the usa",
    "top 10",
    "top 5",
    "top 20",
    "top 3",
    "top customers",
    "top products",
    "trend",
    "monthly",
    "yearly",
    "quarterly",
    "weekly",
    "daily",
    "share",
    "breakdown",
    "why did",
    "why is",
    "why are",
    "why has",
)


@dataclass
class ExpensiveQueryResult:
    question: str
    is_expensive: bool
    suggested_filters: list[str] = field(default_factory=list)
    matched_reasons: list[str] = field(default_factory=list)
    has_narrowing: bool = False
    severity: str = "none"  # "low" | "medium" | "high" | "none"

    @property
    def blocked(self) -> bool:
        return self.is_expensive


class ExpensiveQueryDetector:
    """Detect data-dump requests and suggest filters."""

    def detect(self, question: str) -> ExpensiveQueryResult:
        text = (question or "").strip()
        lowered = text.lower()

        reasons: list[str] = []
        for phrase in DATA_DUMP_PHRASES:
            if phrase in lowered:
                reasons.append(f"dump:{phrase}")

        size_match = LARGE_COUNT_PATTERN.search(text)
        if size_match:
            reasons.append(f"large_count:{size_match.group(1)}")
        for phrase in SIZE_UNIT_PHRASES:
            if phrase in lowered:
                reasons.append(f"size:{phrase}")

        narrowing = any(ind in lowered for ind in NARROWING_INDICATORS)
        if not reasons:
            return ExpensiveQueryResult(
                question=text,
                is_expensive=False,
                suggested_filters=[],
                matched_reasons=[],
                has_narrowing=narrowing,
                severity="none",
            )

        # If the question has reasonable narrowing, downgrade severity
        if narrowing and len(reasons) == 1 and not any(
            r.startswith("dump:") for r in reasons
        ):
            severity = "medium"
            is_exp = False
        else:
            severity = "high" if any(r.startswith("dump:") for r in reasons) else "medium"
            is_exp = True

        suggested = self._suggest(lowered)
        return ExpensiveQueryResult(
            question=text,
            is_expensive=is_exp,
            suggested_filters=suggested,
            matched_reasons=reasons,
            has_narrowing=narrowing,
            severity=severity,
        )

    @staticmethod
    def _suggest(lowered: str) -> list[str]:
        suggestions: list[str] = []
        if not any(t in lowered for t in ("month", "year", "quarter", "week", "day")):
            suggestions.append("Add a time filter such as 'last month' or '2025'")
        if not any(r in lowered for r in ("region", "europe", "america", "asia", "country")):
            suggestions.append("Add a region filter (e.g. 'for Europe')")
        if not any(c in lowered for c in ("category", "product", "segment")):
            suggestions.append("Add a product or category filter")
        if "top" not in lowered:
            suggestions.append("Request a ranking, e.g. 'top 10 by revenue'")
        return suggestions[:3]
