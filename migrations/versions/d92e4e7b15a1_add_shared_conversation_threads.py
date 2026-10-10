"""add shared conversation threads

Revision ID: d92e4e7b15a1
Revises: c711c1fa9320
Create Date: 2026-10-10 22:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d92e4e7b15a1"
down_revision: str | Sequence[str] | None = "c711c1fa9320"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_threads",
        sa.Column("id", sa.String(length=160), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", "project_id"),
    )
    op.create_index(
        "ix_conversation_threads_created_by",
        "conversation_threads",
        ["created_by"],
    )
    op.create_index(
        "ix_conversation_threads_project_updated",
        "conversation_threads",
        ["project_id", "updated_at"],
    )

    op.execute(
        """
        INSERT INTO conversation_threads
            (id, project_id, title, created_by, is_archived, created_at, updated_at)
        SELECT DISTINCT ON (turn.project_id, turn.thread_id)
            turn.thread_id,
            turn.project_id,
            LEFT(turn.question, 120),
            turn.author_id,
            false,
            turn.created_at,
            (
                SELECT MAX(latest.created_at)
                FROM conversation_turns latest
                WHERE latest.project_id = turn.project_id
                  AND latest.thread_id = turn.thread_id
            )
        FROM conversation_turns turn
        ORDER BY turn.project_id, turn.thread_id, turn.created_at, turn.id
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_threads_project_updated",
        table_name="conversation_threads",
    )
    op.drop_index("ix_conversation_threads_created_by", table_name="conversation_threads")
    op.drop_table("conversation_threads")
