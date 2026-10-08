from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import Document
from personal_document_intelligence_api.database.models.knowledge_graph import (
    KnowledgeConceptRecord,
    KnowledgeGraphRecord,
    KnowledgeRelationRecord,
)
from personal_document_intelligence_api.knowledge.models import (
    KnowledgeConcept,
    KnowledgeGraph,
    KnowledgeRelation,
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

    async def get_for_document(
        self,
        *,
        document_id: UUID,
        owner_id: str,
    ) -> KnowledgeGraph | None:
        graph_statement = (
            select(KnowledgeGraphRecord)
            .join(
                Document,
                Document.id == KnowledgeGraphRecord.document_id,
            )
            .where(
                KnowledgeGraphRecord.document_id == document_id,
                Document.owner_id == owner_id,
            )
        )
        graph_result = await self.session.execute(graph_statement)
        graph_record = graph_result.scalar_one_or_none()

        if graph_record is None:
            return None

        concepts_statement = (
            select(KnowledgeConceptRecord)
            .where(KnowledgeConceptRecord.graph_id == graph_record.id)
            .order_by(KnowledgeConceptRecord.concept_key)
        )
        relations_statement = (
            select(KnowledgeRelationRecord)
            .where(KnowledgeRelationRecord.graph_id == graph_record.id)
            .order_by(
                KnowledgeRelationRecord.source_key,
                KnowledgeRelationRecord.target_key,
                KnowledgeRelationRecord.label,
            )
        )

        concepts_result = await self.session.execute(concepts_statement)
        relations_result = await self.session.execute(relations_statement)

        return KnowledgeGraph(
            concepts=tuple(
                KnowledgeConcept(
                    id=record.concept_key,
                    label=record.label,
                    description=record.description,
                    source_chunk_ids=tuple(record.source_chunk_ids),
                )
                for record in concepts_result.scalars().all()
            ),
            relations=tuple(
                KnowledgeRelation(
                    source_id=record.source_key,
                    target_id=record.target_key,
                    label=record.label,
                    source_chunk_ids=tuple(record.source_chunk_ids),
                )
                for record in relations_result.scalars().all()
            ),
        )
