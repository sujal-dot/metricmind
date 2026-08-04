"""SQL Injection and Raw-SQL detector.

Does NOT execute SQL — purely string/regex heuristics against the user question
so dangerous questions never reach the LLM agent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---- Token / keyword heuristics -------------------------------------------------
DANGEROUS_DML_DDL: tuple[str, ...] = (
    "drop table",
    "alter table",
    "create table",
    "delete from",
    "insert into",
    "update ",
    "truncate table",
    "exec(",
    "execute(",
    "exec ",
    "execute ",
    "xp_cmdshell",
    "information_schema",
    "sysobjects",
    "syscolumns",
    "master.dbo",
    "pg_catalog",
    "sqlite_master",
    "show tables",
    "show databases",
    "describe table",
    "desc table",
    "grant ",
    "revoke ",
)

# SQL keywords that by themselves indicate the user is asking for raw SQL
SQL_REQUEST_KEYWORDS: tuple[str, ...] = (
    "write sql",
    "generate sql",
    "give me sql",
    "show me sql",
    "can you write sql",
    "sql query for",
    "please write sql",
    "run this sql",
    "execute this sql",
    "run sql",
    "execute sql",
    "explain this sql",
    "explain sql",
    "raw sql",
    "direct sql",
    "sql statement",
)

# Regex patterns that match injections -------------------------------------------
_INJECTION_PATTERNS: tuple[tuple[str, str], ...] = (
    # OR 1=1 / AND 1=1 style tautologies (allow whitespace variations)
    (r"\b(or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?", "tautology"),
    # Comment sequences: -- or /* ... */
    (r"--", "sql_comment"),
    (r"/\*[\s\S]*?\*/", "block_comment"),
    # UNION SELECT / UNION ALL SELECT
    (r"\bunion\s+(all\s+)?select\b", "union_select"),
    # Stacked queries / second statement
    (r";\s*(drop|delete|update|insert|alter|create|truncate|exec|execute)\b", "stacked_statement"),
    # Blind injection style: ' OR 'a'='a
    (r"['\"]\s*(or|and)\s*['\"][^'\"]+['\"]\s*=\s*['\"]", "string_tautology"),
    # SELECT * FROM ... (user asking for raw select)
    (r"\bselect\s+\*\s+from\b", "select_star"),
    # INTO OUTFILE / COPY - data exfiltration
    (r"\b(into\s+outfile|into\s+dumpfile|copy\s+.*\s+to)\b", "exfiltration"),
)


@dataclass
class SQLDetectionResult:
    question: str
    is_sql_injection: bool
    is_sql_request: bool
    matched_injection_reasons: list[str] = field(default_factory=list)
    matched_request_reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def blocked(self) -> bool:
        return self.is_sql_injection or self.is_sql_request


class SQLDetector:
    """Detect SQL injection attempts or direct SQL requests from user questions."""

    def __init__(self) -> None:
        self._compiled = [
            (re.compile(pat, re.IGNORECASE), tag) for pat, tag in _INJECTION_PATTERNS
        ]

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------
    def detect(self, question: str) -> SQLDetectionResult:
        text = (question or "").strip()
        lowered = text.lower()

        reasons_inj: list[str] = []
        for pattern, tag in self._compiled:
            if pattern.search(text):
                reasons_inj.append(tag)

        for phrase in DANGEROUS_DML_DDL:
            if phrase in lowered:
                reasons_inj.append(f"keyword:{phrase}")

        reasons_req: list[str] = []
        for phrase in SQL_REQUEST_KEYWORDS:
            if phrase in lowered:
                reasons_req.append(f"request:{phrase}")

        # Handle edge: pure "SELECT ... FROM ..." is SQL, even without SQL_REQUEST prefix
        if not reasons_req:
            plain_sql = re.search(r"\bselect\b.+?\bfrom\b", text, re.IGNORECASE | re.DOTALL)
            if plain_sql:
                reasons_req.append("request:select_from_statement")

        is_inj = bool(reasons_inj)
        is_req = bool(reasons_req)
        confidence = self._confidence(is_inj, is_req, reasons_inj, reasons_req)
        return SQLDetectionResult(
            question=text,
            is_sql_injection=is_inj,
            is_sql_request=is_req,
            matched_injection_reasons=reasons_inj,
            matched_request_reasons=reasons_req,
            confidence=confidence,
        )

    # ---------------------------------------------------------------
    # Internal
    # ---------------------------------------------------------------
    @staticmethod
    def _confidence(
        is_inj: bool,
        is_req: bool,
        reasons_inj: list[str],
        reasons_req: list[str],
    ) -> float:
        score = 0.0
        if is_inj:
            score += 0.4 + 0.1 * min(len(reasons_inj), 3)
        if is_req:
            score += 0.4 + 0.08 * min(len(reasons_req), 3)
        return round(min(score, 1.0), 3)
