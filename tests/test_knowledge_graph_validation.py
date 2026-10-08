from uuid import uuid4

import pytest

from personal_document_intelligence_api.knowledge.models import (
    KnowledgeConcept,
    KnowledgeGraph,
    KnowledgeRelation,
)
from personal_document_intelligence_api.knowledge.validation import (
    InvalidKnowledgeGraphError,
    validate_knowledge_graph,
)


def test_validate_knowledge_graph() -> None:
    chunk_id = uuid4()
    graph = KnowledgeGraph(
        concepts=(
            KnowledgeConcept(
                id="dynamic-programming",
                label="Dynamic Programming",
                description="A problem-solving technique.",
                source_chunk_ids=(chunk_id,),
            ),
            KnowledgeConcept(
                id="state",
                label="State",
                description="Information describing a subproblem.",
                source_chunk_ids=(chunk_id,),
            ),
        ),
        relations=(
            KnowledgeRelation(
                source_id="dynamic-programming",
                target_id="state",
                label="uses",
                source_chunk_ids=(chunk_id,),
            ),
        ),
    )

    validate_knowledge_graph(graph)


def test_reject_unknown_relation_target() -> None:
    graph = KnowledgeGraph(
        concepts=(),
        relations=(
            KnowledgeRelation(
                source_id="unknown",
                target_id="missing",
                label="uses",
                source_chunk_ids=(),
            ),
        ),
    )

    with pytest.raises(InvalidKnowledgeGraphError):
        validate_knowledge_graph(graph)
