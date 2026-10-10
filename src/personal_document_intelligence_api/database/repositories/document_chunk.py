from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import Document
from personal_document_intelligence_api.database.models.document_chunk import (
    DocumentChunk,
)
from personal_document_intelligence_api.database.models.project import ProjectMember
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
    TextChunk,
)


class ChunkEmbeddingCountMismatchError(ValueError):
    pass


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace_for_document(
        self,
        document_id: UUID,
        project_id: UUID,
        chunks: Sequence[TextChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ChunkEmbeddingCountMismatchError("Every chunk must have exactly one embedding")

        statement = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await self.session.execute(statement)

        database_chunks = [
            DocumentChunk(
                document_id=document_id,
                project_id=project_id,
                position=position,
                section_position=chunk.section_position,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                page_number=chunk.page_number,
                embedding=list(embedding),
            )
            for position, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]

        self.session.add_all(database_chunks)
        await self.session.flush()

    async def semantic_search(
        self,
        *,
        owner_id: str,
        project_id: UUID,
        query_embedding: Sequence[float],
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[SemanticSearchResult]:
        distance = DocumentChunk.embedding.cosine_distance(list(query_embedding)).label("distance")

        statement = (
            select(DocumentChunk, Document.filename, distance)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .join(
                ProjectMember,
                ProjectMember.project_id == DocumentChunk.project_id,
            )
            .where(
                DocumentChunk.project_id == project_id,
                ProjectMember.member_id == owner_id,
            )
            .order_by(distance)
            .limit(limit)
        )

        if document_id is not None:
            statement = statement.where(DocumentChunk.document_id == document_id)

        result = await self.session.execute(statement)

        return [
            SemanticSearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                page_number=chunk.page_number,
                score=1 - float(cosine_distance),
                document_name=filename,
            )
            for chunk, filename, cosine_distance in result.all()
        ]

    async def list_for_document(
        self,
        *,
        document_id: UUID,
        owner_id: str,
        project_id: UUID,
        limit: int,
    ) -> Sequence[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .join(
                ProjectMember,
                ProjectMember.project_id == DocumentChunk.project_id,
            )
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.project_id == project_id,
                Document.project_id == project_id,
                ProjectMember.member_id == owner_id,
            )
            .order_by(DocumentChunk.position)
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return result.scalars().all()
