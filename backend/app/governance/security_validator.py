"""Security Validator — composes SQL + expensive-query detection into one decision."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.governance import sql_detector as _sql
from app.governance import expensive_query_detector as _eq
from app.governance.prompts import (
    CUBE_ONLY_POLICY_MESSAGE,
    EXPENSIVE_QUERY_SUGGESTION_MESSAGE,
    SECURITY_BLOCKED_MESSAGE,
)


@dataclass
class SecurityDecision:
    """Unified security decision returned from SecurityValidator.validate."""

    question: str
    allowed: bool
    block_reason: Optional[str] = None
    block_code: Optional[str] = None  # "sql_injection" / "sql_request" / "expensive"
    sql_result: Optional[_sql.SQLDetectionResult] = None
    expensive_result: Optional[_eq.ExpensiveQueryResult] = None
    suggested_filters: List[str] = field(default_factory=list)

    @property
    def human_message(self) -> str:
        if self.allowed:
            return "Request passed governance validation."
        if self.block_code == "sql_request":
            return CUBE_ONLY_POLICY_MESSAGE
        if self.block_code == "expensive":
            msg = EXPENSIVE_QUERY_SUGGESTION_MESSAGE
            if self.suggested_filters:
                msg += " Suggested filters: " + "; ".join(self.suggested_filters) + "."
            return msg
        return SECURITY_BLOCKED_MESSAGE


class SecurityValidator:
    """Validate a user question against the SQL + expensive-query policies."""

    def __init__(self) -> None:
        self.sql_detector = _sql.SQLDetector()
        self.expensive_detector = _eq.ExpensiveQueryDetector()

    def validate(self, question: str) -> SecurityDecision:
        text = (question or "").strip()
        if not text:
            return SecurityDecision(
                question=text,
                allowed=False,
                block_reason="Empty question",
                block_code="sql_injection",
            )

        sql_res = self.sql_detector.detect(text)
        expensive_res = self.expensive_detector.detect(text)

        # Priority: SQL-injection > SQL-request > expensive
        if sql_res.is_sql_injection:
            reasons = ", ".join(sql_res.matched_injection_reasons)
            return SecurityDecision(
                question=text,
                allowed=False,
                block_reason=f"SQL injection detected: {reasons}",
                block_code="sql_injection",
                sql_result=sql_res,
                expensive_result=expensive_res,
            )
        if sql_res.is_sql_request:
            reasons = ", ".join(sql_res.matched_request_reasons)
            return SecurityDecision(
                question=text,
                allowed=False,
                block_reason=f"Raw SQL request blocked: {reasons}",
                block_code="sql_request",
                sql_result=sql_res,
                expensive_result=expensive_res,
            )
        if expensive_res.is_expensive:
            return SecurityDecision(
                question=text,
                allowed=False,
                block_reason="Expensive query detected",
                block_code="expensive",
                sql_result=sql_res,
                expensive_result=expensive_res,
                suggested_filters=expensive_res.suggested_filters,
            )

        return SecurityDecision(
            question=text,
            allowed=True,
            sql_result=sql_res,
            expensive_result=expensive_res,
            suggested_filters=expensive_res.suggested_filters,
        )
