"""add projects and project-scoped indexes

Revision ID: 88aa9e4db401
Revises: 6c0892d228db
Create Date: 2026-10-10 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "88aa9e4db401"
down_revision: str | Sequence[str] | None = "6c0892d228db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    project_role = postgresql.ENUM(
        "owner",
        "editor",
        "viewer",
        name="project_role",
        create_type=False,
    )
    project_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("member_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("role", project_role, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "member_id", name="uq_project_members_project_member"),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_member_id", "project_members", ["member_id"])

    op.execute("CREATE TEMP TABLE legacy_projects (owner_id varchar(128), project_id uuid)")
    op.execute(
        "INSERT INTO legacy_projects (owner_id, project_id) "
        "SELECT owner_id, gen_random_uuid() FROM documents GROUP BY owner_id"
    )
    op.execute(
        "INSERT INTO projects (id, name) "
        "SELECT project_id, 'Personal project' FROM legacy_projects"
    )
    op.execute(
        "INSERT INTO project_members (id, project_id, member_id, role) "
        "SELECT gen_random_uuid(), project_id, owner_id, 'owner'::project_role "
        "FROM legacy_projects"
    )

    op.add_column("documents", sa.Column("project_id", sa.UUID(), nullable=True))
    op.execute(
        "UPDATE documents SET project_id = legacy_projects.project_id "
        "FROM legacy_projects WHERE documents.owner_id = legacy_projects.owner_id"
    )
    op.alter_column("documents", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_documents_project_id_projects",
        "documents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_project_status", "documents", ["project_id", "status"])

    op.add_column("document_chunks", sa.Column("project_id", sa.UUID(), nullable=True))
    op.execute(
        "UPDATE document_chunks SET project_id = documents.project_id "
        "FROM documents WHERE document_chunks.document_id = documents.id"
    )
    op.alter_column("document_chunks", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_document_chunks_project_id_projects",
        "document_chunks",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_document_chunks_project_id", "document_chunks", ["project_id"])
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_text_fts ON document_chunks "
        "USING gin (to_tsvector('simple', text))"
    )

    op.create_table(
        "project_insights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("thread_id", sa.String(length=160), nullable=False),
        sa.Column("takeaways", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_insights_project_id", "project_insights", ["project_id"])
    op.create_index("ix_project_insights_thread_id", "project_insights", ["thread_id"])
    op.create_index(
        "ix_project_insights_project_thread_created",
        "project_insights",
        ["project_id", "thread_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("project_insights")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_text_fts")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_index("ix_document_chunks_project_id", table_name="document_chunks")
    op.drop_constraint(
        "fk_document_chunks_project_id_projects",
        "document_chunks",
        type_="foreignkey",
    )
    op.drop_column("document_chunks", "project_id")
    op.drop_index("ix_documents_project_status", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_constraint("fk_documents_project_id_projects", "documents", type_="foreignkey")
    op.drop_column("documents", "project_id")
    op.drop_table("project_members")
    op.drop_table("projects")
    postgresql.ENUM(name="project_role").drop(op.get_bind(), checkfirst=True)
