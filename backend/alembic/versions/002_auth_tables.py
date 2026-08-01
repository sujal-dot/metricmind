"""add auth tables

Revision ID: 002
Revises: 001
Create Date: 2026-07-27 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        if_not_exists=True,
    )

    op.create_table(
        "conversations",
        sa.Column(
            "id",
            UUID(),
            server_default=sa.func.gen_random_uuid(),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_conversations_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversations_user_id_updated_at_desc",
        "conversations",
        ["user_id", "updated_at"],
        unique=False,
        postgresql_ops={"updated_at": "DESC"},
        if_not_exists=True,
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_messages_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        if_not_exists=True,
    )
    op.create_index(
        "ix_messages_conversation_id_created_at_asc",
        "messages",
        ["conversation_id", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "ASC"},
        if_not_exists=True,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("route", sa.String(length=255), nullable=True),
        sa.Column("actor_ip", sa.String(length=64), nullable=True),
        sa.Column(
            "metadata",
            JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_audit_logs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
        if_not_exists=True,
    )
    op.create_index(
        "ix_audit_logs_user_id_created_at_desc",
        "audit_logs",
        ["user_id", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
        if_not_exists=True,
    )
    op.create_index(
        "ix_audit_logs_event_type_created_at_desc",
        "audit_logs",
        ["event_type", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_logs_event_type_created_at_desc",
        table_name="audit_logs",
        if_exists=True,
    )
    op.drop_index(
        "ix_audit_logs_user_id_created_at_desc",
        table_name="audit_logs",
        if_exists=True,
    )
    op.drop_table("audit_logs", if_exists=True)

    op.drop_index(
        "ix_messages_conversation_id_created_at_asc",
        table_name="messages",
        if_exists=True,
    )
    op.drop_table("messages", if_exists=True)

    op.drop_index(
        "ix_conversations_user_id_updated_at_desc",
        table_name="conversations",
        if_exists=True,
    )
    op.drop_table("conversations", if_exists=True)

    op.drop_table("users", if_exists=True)
