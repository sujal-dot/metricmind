import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.auth.passwords import verify_password, hash_password
from app.config.settings import settings


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_user(row: Any) -> dict:
    data = dict(row._mapping)
    return {
        "id": data["id"],
        "email": data["email"],
        "full_name": data.get("full_name"),
        "role": data.get("role", "viewer"),
        "is_active": bool(data.get("is_active", True)),
    }


class AuthService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def register_user(self, email: str, password: str, full_name: str | None = None) -> dict | None:
        normalized = email.strip().lower()
        if not normalized or not password:
            return None
        hashed = hash_password(password)
        with self.engine.begin() as conn:
            existing = conn.execute(
                text("SELECT id FROM users WHERE LOWER(email) = :email"),
                {"email": normalized},
            ).fetchone()
            if existing is not None:
                return None
            row = conn.execute(
                text(
                    """
                    INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at, updated_at)
                    VALUES (:email, :full_name, :hashed_password, 'viewer', TRUE, NOW(), NOW())
                    RETURNING id, email, full_name, role, is_active
                    """
                ),
                {
                    "email": normalized,
                    "full_name": full_name.strip() if full_name else None,
                    "hashed_password": hashed,
                },
            ).fetchone()
        return _row_to_user(row) if row is not None else None

    def authenticate_user(self, email: str, password: str) -> dict | None:
        normalized = email.strip().lower()
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT id, email, full_name, hashed_password, role, is_active
                    FROM users
                    WHERE LOWER(email) = :email
                    """
                ),
                {"email": normalized},
            ).fetchone()
        if row is None:
            return None
        data = dict(row._mapping)
        if not data.get("is_active", True):
            return None
        if not verify_password(password, data.get("hashed_password") or ""):
            return None
        return _row_to_user(row)

    def create_session(self, user_id: int) -> tuple[str, str, datetime]:
        session_token = secrets.token_urlsafe(48)
        csrf_token = secrets.token_urlsafe(32)
        expires_at = _utcnow() + timedelta(minutes=settings.session_ttl_minutes)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO user_sessions (
                        user_id,
                        session_token_hash,
                        csrf_token_hash,
                        created_at,
                        expires_at
                    )
                    VALUES (
                        :user_id,
                        :session_token_hash,
                        :csrf_token_hash,
                        NOW(),
                        :expires_at
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "session_token_hash": _hash_token(session_token),
                    "csrf_token_hash": _hash_token(csrf_token),
                    "expires_at": expires_at,
                },
            )
        return session_token, csrf_token, expires_at

    def get_user_for_session(self, session_token: str) -> dict | None:
        if not session_token:
            return None
        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        u.id,
                        u.email,
                        u.full_name,
                        u.role,
                        u.is_active
                    FROM user_sessions s
                    JOIN users u ON u.id = s.user_id
                    WHERE s.session_token_hash = :session_token_hash
                      AND s.revoked_at IS NULL
                      AND s.expires_at > NOW()
                      AND u.is_active = TRUE
                    """
                ),
                {"session_token_hash": _hash_token(session_token)},
            ).fetchone()
            if row is not None:
                conn.execute(
                    text(
                        """
                        UPDATE user_sessions
                        SET last_seen_at = NOW()
                        WHERE session_token_hash = :session_token_hash
                        """
                    ),
                    {"session_token_hash": _hash_token(session_token)},
                )
        return _row_to_user(row) if row is not None else None

    def validate_csrf(self, session_token: str, csrf_token: str) -> bool:
        if not session_token or not csrf_token:
            return False
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT id
                    FROM user_sessions
                    WHERE session_token_hash = :session_token_hash
                      AND csrf_token_hash = :csrf_token_hash
                      AND revoked_at IS NULL
                      AND expires_at > NOW()
                    """
                ),
                {
                    "session_token_hash": _hash_token(session_token),
                    "csrf_token_hash": _hash_token(csrf_token),
                },
            ).fetchone()
        return row is not None

    def revoke_session(self, session_token: str) -> None:
        if not session_token:
            return
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE user_sessions
                    SET revoked_at = NOW()
                    WHERE session_token_hash = :session_token_hash
                      AND revoked_at IS NULL
                    """
                ),
                {"session_token_hash": _hash_token(session_token)},
            )
