import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.auth.dependencies import get_current_user, require_csrf
from app.services.database import get_engine

logger = logging.getLogger("metricmind.api.conversations")

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=512)


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=512)


class AppendMessageRequest(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=20000)
    metadata: Optional[dict] = None


def _row_to_dict(row: Any) -> dict:
    d = dict(row._mapping)
    for k, v in d.items():
        if isinstance(v, UUID):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def _message_row_to_dict(row: Any) -> dict:
    d = _row_to_dict(row)
    md = d.get("metadata")
    if isinstance(md, str):
        try:
            d["metadata"] = json.loads(md)
        except Exception:
            d["metadata"] = {}
    elif md is None:
        d["metadata"] = {}
    return d


@router.get("")
async def list_conversations(
    user: dict = Depends(get_current_user),
    engine: Engine = Depends(get_engine),
):
    u = user
    try:
        with engine.connect() as conn:
            sql = text(
                """
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COALESCE(COUNT(m.id), 0)::INTEGER AS message_count
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                WHERE c.user_id = :user_id
                GROUP BY c.id, c.title, c.created_at, c.updated_at
                ORDER BY c.updated_at DESC NULLS LAST
                """
            )
            result = conn.execute(sql, {"user_id": u["id"]})
            rows = [_row_to_dict(r) for r in result.fetchall()]
            return rows
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to list conversations for user %s", u["id"])
        raise HTTPException(status_code=500, detail="Database error") from exc


@router.post("")
async def create_conversation(
    body: CreateConversationRequest,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_csrf),
    engine: Engine = Depends(get_engine),
):
    u = user
    title = body.title if body.title and body.title.strip() else "New Conversation"
    try:
        with engine.begin() as conn:
            sql = text(
                """
                INSERT INTO conversations (user_id, title, created_at, updated_at)
                VALUES (:user_id, :title, NOW(), NOW())
                RETURNING id, title, created_at, updated_at
                """
            )
            row = conn.execute(sql, {"user_id": u["id"], "title": title}).fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
            d = _row_to_dict(row)
            d["message_count"] = 0
            return d
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create conversation for user %s", u["id"])
        raise HTTPException(status_code=500, detail="Database error") from exc


def _get_conversation_owner(conn: Any, conversation_id: str) -> Optional[int]:
    sql = text("SELECT user_id FROM conversations WHERE id = :id::uuid")
    row = conn.execute(sql, {"id": conversation_id}).fetchone()
    return row.user_id if row else None


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user: dict = Depends(get_current_user),
    engine: Engine = Depends(get_engine),
):
    u = user
    try:
        with engine.connect() as conn:
            owner = _get_conversation_owner(conn, str(conversation_id))
            if owner is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            if owner != u["id"]:
                raise HTTPException(status_code=403, detail="Forbidden")

            conv_sql = text(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations WHERE id = :id::uuid
                """
            )
            conv_row = conn.execute(conv_sql, {"id": str(conversation_id)}).fetchone()
            conv = _row_to_dict(conv_row)

            msg_sql = text(
                """
                SELECT id, role, content, metadata, created_at
                FROM messages
                WHERE conversation_id = :id::uuid
                ORDER BY created_at ASC, id ASC
                """
            )
            msg_rows = conn.execute(msg_sql, {"id": str(conversation_id)}).fetchall()
            conv["messages"] = [_message_row_to_dict(r) for r in msg_rows]

            count_sql = text(
                "SELECT COUNT(*)::INTEGER AS cnt FROM messages WHERE conversation_id = :id::uuid"
            )
            count_row = conn.execute(count_sql, {"id": str(conversation_id)}).fetchone()
            conv["message_count"] = count_row.cnt if count_row else len(conv["messages"])

            return conv
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get conversation %s", conversation_id)
        raise HTTPException(status_code=500, detail="Database error") from exc


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    body: UpdateConversationRequest,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_csrf),
    engine: Engine = Depends(get_engine),
):
    u = user
    try:
        with engine.begin() as conn:
            owner = _get_conversation_owner(conn, str(conversation_id))
            if owner is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            if owner != u["id"]:
                raise HTTPException(status_code=403, detail="Forbidden")

            sql = text(
                """
                UPDATE conversations
                SET title = COALESCE(:title, title),
                    updated_at = NOW()
                WHERE id = :id::uuid
                RETURNING id, title, created_at, updated_at
                """
            )
            row = conn.execute(
                sql,
                {"id": str(conversation_id), "title": body.title},
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Conversation not found")
            d = _row_to_dict(row)
            return d
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to update conversation %s", conversation_id)
        raise HTTPException(status_code=500, detail="Database error") from exc


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_csrf),
    engine: Engine = Depends(get_engine),
):
    u = user
    try:
        with engine.begin() as conn:
            owner = _get_conversation_owner(conn, str(conversation_id))
            if owner is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            if owner != u["id"]:
                raise HTTPException(status_code=403, detail="Forbidden")

            sql = text("DELETE FROM conversations WHERE id = :id::uuid")
            conn.execute(sql, {"id": str(conversation_id)})
            return {"ok": True, "id": str(conversation_id)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to delete conversation %s", conversation_id)
        raise HTTPException(status_code=500, detail="Database error") from exc


@router.post("/{conversation_id}/messages")
async def append_message(
    conversation_id: UUID,
    body: AppendMessageRequest,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_csrf),
    engine: Engine = Depends(get_engine),
):
    u = user
    try:
        with engine.begin() as conn:
            owner = _get_conversation_owner(conn, str(conversation_id))
            if owner is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            if owner != u["id"]:
                raise HTTPException(status_code=403, detail="Forbidden")

            md_json = json.dumps(body.metadata) if body.metadata is not None else "{}"
            sql = text(
                """
                INSERT INTO messages (conversation_id, role, content, metadata, created_at)
                VALUES (:cid::uuid, :role, :content, :md::jsonb, NOW())
                RETURNING id, role, content, metadata, created_at
                """
            )
            row = conn.execute(
                sql,
                {
                    "cid": str(conversation_id),
                    "role": body.role,
                    "content": body.content,
                    "md": md_json,
                },
            ).fetchone()

            up_sql = text(
                "UPDATE conversations SET updated_at = NOW() WHERE id = :id::uuid"
            )
            conn.execute(up_sql, {"id": str(conversation_id)})

            if not row:
                raise HTTPException(status_code=500, detail="Failed to insert message")
            return _message_row_to_dict(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to append message to conversation %s", conversation_id)
        raise HTTPException(status_code=500, detail="Database error") from exc
