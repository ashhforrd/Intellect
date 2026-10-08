import asyncio
from uuid import UUID

from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
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
        repository: DocumentChunkRepository,
        extractor: KnowledgeGraphExtractor,
        max_chunks: int,
    ) -> None:
        self.repository = repository
        self.extractor = extractor
        self.max_chunks = max_chunks

    async def generate(
        self,
        *,
        document_id: UUID,
        owner_id: str,
    ) -> KnowledgeGraph:
        chunks = await self.repository.list_for_document(
            document_id=document_id,
            owner_id=owner_id,
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

        return await asyncio.to_thread(
            self.extractor.extract,
            sources,
        )
