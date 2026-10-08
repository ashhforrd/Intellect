from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.knowledge_graph import (
    KnowledgeConceptRecord,
    KnowledgeGraphRecord,
    KnowledgeRelationRecord,
)
from personal_document_intelligence_api.knowledge.models import (
    KnowledgeGraph,
)


class KnowledgeGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace_for_document(
        self,
        document_id: UUID,
        graph: KnowledgeGraph,
    ) -> None:
        statement = select(KnowledgeGraphRecord).where(
            KnowledgeGraphRecord.document_id == document_id
        )
        result = await self.session.execute(statement)
        existing_graph = result.scalar_one_or_none()

        if existing_graph is not None:
            await self.session.delete(existing_graph)
            await self.session.flush()

        graph_record = KnowledgeGraphRecord(
            document_id=document_id,
        )
        self.session.add(graph_record)
        await self.session.flush()

        concept_records = [
            KnowledgeConceptRecord(
                graph_id=graph_record.id,
                concept_key=concept.id,
                label=concept.label,
                description=concept.description,
                source_chunk_ids=list(concept.source_chunk_ids),
            )
            for concept in graph.concepts
        ]
        relation_records = [
            KnowledgeRelationRecord(
                graph_id=graph_record.id,
                source_key=relation.source_id,
                target_key=relation.target_id,
                label=relation.label,
                source_chunk_ids=list(relation.source_chunk_ids),
            )
            for relation in graph.relations
        ]

        self.session.add_all([*concept_records, *relation_records])
        await self.session.flush()
