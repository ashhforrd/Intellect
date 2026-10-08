from personal_document_intelligence_api.knowledge.models import (
    KnowledgeGraph,
)


class InvalidKnowledgeGraphError(ValueError):
    pass


def validate_knowledge_graph(graph: KnowledgeGraph) -> None:
    concept_ids = {concept.id for concept in graph.concepts}

    if len(concept_ids) != len(graph.concepts):
        raise InvalidKnowledgeGraphError("Knowledge graph contains duplicate concept IDs")

    for relation in graph.relations:
        if relation.source_id not in concept_ids:
            raise InvalidKnowledgeGraphError(f"Unknown source concept: {relation.source_id}")

        if relation.target_id not in concept_ids:
            raise InvalidKnowledgeGraphError(f"Unknown target concept: {relation.target_id}")
