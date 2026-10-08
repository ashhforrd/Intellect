from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from personal_document_intelligence_api.database.base import Base


class KnowledgeGraphRecord(Base):
    __tablename__ = "knowledge_graphs"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class KnowledgeConceptRecord(Base):
    __tablename__ = "knowledge_concepts"
    __table_args__ = (
        UniqueConstraint(
            "graph_id",
            "concept_key",
            name="uq_knowledge_concepts_graph_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    graph_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        index=True,
    )
    concept_key: Mapped[str] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source_chunk_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PostgreSQLUUID(as_uuid=True)))


class KnowledgeRelationRecord(Base):
    __tablename__ = "knowledge_relations"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    graph_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        index=True,
    )
    source_key: Mapped[str] = mapped_column(String(128))
    target_key: Mapped[str] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(128))
    source_chunk_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PostgreSQLUUID(as_uuid=True)))
