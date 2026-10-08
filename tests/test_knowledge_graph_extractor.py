from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from personal_document_intelligence_api.knowledge.extractor import (
    OpenAIKnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.schemas import (
    ExtractedConcept,
    ExtractedRelation,
    KnowledgeGraphExtraction,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


def test_extract_knowledge_graph() -> None:
    client = Mock()
    chunk_id = uuid4()
    context = SemanticSearchResult(
        chunk_id=chunk_id,
        document_id=uuid4(),
        text="Dynamic programming uses states and transitions.",
        page_number=1,
        score=0.9,
    )
    client.responses.parse.return_value = SimpleNamespace(
        output_parsed=KnowledgeGraphExtraction(
            concepts=[
                ExtractedConcept(
                    id="dynamic-programming",
                    label="Dynamic Programming",
                    description="A problem-solving technique.",
                    source_numbers=[1],
                ),
                ExtractedConcept(
                    id="state",
                    label="State",
                    description="Represents a subproblem.",
                    source_numbers=[1],
                ),
            ],
            relations=[
                ExtractedRelation(
                    source_id="dynamic-programming",
                    target_id="state",
                    label="uses",
                    source_numbers=[1],
                )
            ],
        )
    )
    extractor = OpenAIKnowledgeGraphExtractor(
        client=client,
        model="test-model",
    )

    graph = extractor.extract([context])

    assert len(graph.concepts) == 2
    assert graph.concepts[0].source_chunk_ids == (chunk_id,)
    assert graph.relations[0].label == "uses"
