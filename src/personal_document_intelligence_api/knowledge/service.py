import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.knowledge_graph import (
    KnowledgeGraphRepository,
)
from personal_document_intelligence_api.knowledge.base import (
    KnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.models import (
    KnowledgeGraph,
    KnowledgeSource,
)


class DocumentHasNoChunksError(ValueError):
    pass


class KnowledgeGraphService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DocumentChunkRepository,
        graph_repository: KnowledgeGraphRepository,
        extractor: KnowledgeGraphExtractor,
        max_chunks: int,
    ) -> None:
        self.session = session
        self.repository = repository
        self.graph_repository = graph_repository
        self.extractor = extractor
        self.max_chunks = max_chunks

    async def generate(
        self,
        *,
        document_id: UUID,
        owner_id: str,
        project_id: UUID,
    ) -> KnowledgeGraph:
        chunks = await self.repository.list_for_document(
            document_id=document_id,
            owner_id=owner_id,
            project_id=project_id,
            limit=self.max_chunks,
        )

        if not chunks:
            raise DocumentHasNoChunksError("Document has no processed chunks")

        sources = [
            KnowledgeSource(
                chunk_id=chunk.id,
                text=chunk.text,
            )
            for chunk in chunks
        ]

        graph = await asyncio.to_thread(
            self.extractor.extract,
            sources,
        )

        try:
            await self.graph_repository.replace_for_document(
                document_id,
                graph,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return graph
