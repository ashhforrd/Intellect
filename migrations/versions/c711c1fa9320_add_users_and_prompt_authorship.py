"""add users and prompt authorship

Revision ID: c711c1fa9320
Revises: 88aa9e4db401
Create Date: 2026-10-10 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from personal_document_intelligence_api.security import hash_password

revision: str = "c711c1fa9320"
down_revision: str | Sequence[str] | None = "88aa9e4db401"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LUCAS_ID = "10000000-0000-4000-8000-000000000001"
KEZIA_ID = "10000000-0000-4000-8000-000000000002"
ATQIYA_ID = "10000000-0000-4000-8000-000000000003"
DEMO_PASSWORD = "IntellectDemo!2026"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    users = sa.table(
        "users",
        sa.column("id", sa.UUID()),
        sa.column("email", sa.String()),
        sa.column("display_name", sa.String()),
        sa.column("password_hash", sa.String()),
    )
    op.bulk_insert(
        users,
        [
            {
                "id": LUCAS_ID,
                "email": "lucas@intellect.id",
                "display_name": "Lucas",
                "password_hash": hash_password(DEMO_PASSWORD, salt=b"intellect-lucas-1"),
            },
            {
                "id": KEZIA_ID,
                "email": "kezia@intellect.id",
                "display_name": "Kezia",
                "password_hash": hash_password(DEMO_PASSWORD, salt=b"intellect-kezia-1"),
            },
            {
                "id": ATQIYA_ID,
                "email": "atqiya@intellect.id",
                "display_name": "Atqiya Haydar",
                "password_hash": hash_password(DEMO_PASSWORD, salt=b"intellect-atqiya1"),
            },
        ],
    )

    # Preserve the existing development workspace while replacing only its
    # temporary local identity with the seeded Atqiya account.
    op.execute(
        "UPDATE project_members SET member_id = 'user:" + ATQIYA_ID + "', "
        "display_name = 'Atqiya Haydar' WHERE member_id = 'local-development-user'"
    )
    op.execute(
        "UPDATE documents SET owner_id = 'user:" + ATQIYA_ID + "' "
        "WHERE owner_id = 'local-development-user'"
    )

    # A fresh database has no legacy project, so create one team workspace.
    op.execute(
        "INSERT INTO projects (id, name) "
        "SELECT gen_random_uuid(), 'Intellect Team Workspace' "
        "WHERE NOT EXISTS (SELECT 1 FROM projects)"
    )
    op.execute(
        "INSERT INTO project_members (id, project_id, member_id, display_name, role) "
        "SELECT gen_random_uuid(), p.id, 'user:" + ATQIYA_ID + "', 'Atqiya Haydar', "
        "'owner'::project_role FROM projects p "
        "WHERE NOT EXISTS (SELECT 1 FROM project_members pm WHERE pm.project_id = p.id)"
    )
    for user_id, display_name in ((LUCAS_ID, "Lucas"), (KEZIA_ID, "Kezia")):
        op.execute(
            "INSERT INTO project_members (id, project_id, member_id, display_name, role) "
            "SELECT gen_random_uuid(), p.id, 'user:"
            + user_id
            + "', '"
            + display_name
            + "', 'editor'::project_role FROM projects p "
            "JOIN project_members owner ON owner.project_id = p.id "
            "AND owner.member_id = 'user:"
            + ATQIYA_ID
            + "' AND owner.role = 'owner'::project_role "
            "ON CONFLICT (project_id, member_id) DO NOTHING"
        )

    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("thread_id", sa.String(length=160), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_turns_author_id", "conversation_turns", ["author_id"])
    op.create_index("ix_conversation_turns_project_id", "conversation_turns", ["project_id"])
    op.create_index("ix_conversation_turns_thread_id", "conversation_turns", ["thread_id"])
    op.create_index(
        "ix_conversation_turns_project_thread_created",
        "conversation_turns",
        ["project_id", "thread_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("conversation_turns")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
