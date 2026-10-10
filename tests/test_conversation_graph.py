from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from personal_document_intelligence_api.api.dependencies.auth import get_current_owner_id
from personal_document_intelligence_api.api.dependencies.knowledge import (
    get_knowledge_graph_extractor,
)
from personal_document_intelligence_api.database.models.project import ProjectRole
from personal_document_intelligence_api.knowledge.models import (
    KnowledgeConcept,
    KnowledgeGraph,
    KnowledgeRelation,
)
from personal_document_intelligence_api.main import create_app


def test_generate_conversation_graph() -> None:
    extractor = Mock()
    extractor.extract.return_value = KnowledgeGraph(
        concepts=(
            KnowledgeConcept(
                id="neuroplasticity",
                label="Neuroplasticity",
                description="The brain changes through experience.",
                source_chunk_ids=(),
            ),
            KnowledgeConcept(
                id="deliberate-practice",
                label="Deliberate Practice",
                description="Repeated practice strengthens neural pathways.",
                source_chunk_ids=(),
            ),
        ),
        relations=(
            KnowledgeRelation(
                source_id="deliberate-practice",
                target_id="neuroplasticity",
                label="drives",
                source_chunk_ids=(),
            ),
        ),
    )
    app = create_app()
    app.dependency_overrides[get_knowledge_graph_extractor] = lambda: extractor
    app.dependency_overrides[get_current_owner_id] = lambda: "user:test-member"
    client = TestClient(app)
    project_id = uuid4()

    with patch(
        "personal_document_intelligence_api.api.routes.knowledge."
        "ProjectRepository.get_membership",
        new=AsyncMock(return_value=Mock(role=ProjectRole.EDITOR)),
    ):
        response = client.post(
            "/knowledge/conversation-graph",
            json={
                "project_id": str(project_id),
                "turns": [
                    {
                        "question": "How does practice affect the brain?",
                        "answer": "Practice strengthens pathways through neuroplasticity.",
                    }
                ],
            },
        )

    assert response.status_code == 200
    assert response.json()["concepts"][0]["label"] == "Neuroplasticity"
    assert response.json()["relations"][0]["label"] == "drives"
    extractor.extract.assert_called_once()
