import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.config.settings import settings
from app.services.database import get_engine

logger = logging.getLogger("metricmind.api.users")

router = APIRouter(prefix="/api/v1/users", tags=["users"])


DUMMY_HASH = "$2b$12$devPlaceholderDummyPasswordHashThatIsLongEnough1234"


class EnsureDevUserRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None


def _row_to_user_dict(row) -> dict:
    d = dict(row._mapping)
    return {
        "id": d["id"],
        "email": d["email"],
        "full_name": d.get("full_name"),
        "role": d.get("role", "viewer"),
        "is_active": bool(d.get("is_active", True)),
    }


@router.post("/ensure-dev")
async def ensure_dev_user(
    body: EnsureDevUserRequest,
    engine: Engine = Depends(get_engine),
):
    if settings.is_production:
        raise HTTPException(status_code=404, detail="Resource not found")

    email = str(body.email).strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        with engine.begin() as conn:
            existing = conn.execute(
                text(
                    """
                    SELECT id, email, full_name, role, is_active
                    FROM users WHERE LOWER(email) = :email
                    """
                ),
                {"email": email},
            ).fetchone()

            if existing:
                return _row_to_user_dict(existing)

            inserted = conn.execute(
                text(
                    """
                    INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at, updated_at)
                    VALUES (:email, :full_name, :hp, 'viewer', TRUE, NOW(), NOW())
                    RETURNING id, email, full_name, role, is_active
                    """
                ),
                {
                    "email": email,
                    "full_name": body.full_name,
                    "hp": DUMMY_HASH,
                },
            ).fetchone()

            if not inserted:
                raise HTTPException(status_code=500, detail="Failed to insert user")

            return _row_to_user_dict(inserted)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to ensure dev user for email %s", email)
        raise HTTPException(status_code=500, detail="Database error") from exc
