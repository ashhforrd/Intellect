import asyncio
import re
from collections import Counter
from dataclasses import replace
from uuid import UUID

from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
    EmbeddingProviderError,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


class EmptySearchQueryError(ValueError):
    pass


_CANDIDATE_MULTIPLIER = 4
_MINIMUM_CANDIDATES = 20
_MAXIMUM_CANDIDATES = 80
_MAX_CHUNKS_PER_DOCUMENT = 3
_FILENAME_TOKEN_BONUS = 0.12
_MAX_FILENAME_BONUS = 0.30
_FILENAME_STOP_WORDS = {
    "about",
    "adalah",
    "aja",
    "akan",
    "apa",
    "dari",
    "dan",
    "dengan",
    "document",
    "dokumen",
    "file",
    "final",
    "ini",
    "jadi",
    "mau",
    "pdf",
    "project",
    "saja",
    "saya",
    "tersebut",
    "the",
    "untuk",
    "yang",
}


class SemanticSearchService:
    def __init__(
        self,
        repository: DocumentChunkRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.repository = repository
        self.embedding_provider = embedding_provider

    async def search(
        self,
        *,
        query: str,
        owner_id: str,
        project_id: UUID,
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[SemanticSearchResult]:
        normalized_query = " ".join(query.split())

        if not normalized_query:
            raise EmptySearchQueryError("Search query must not be empty")

        embeddings = await asyncio.to_thread(
            self.embedding_provider.embed_texts,
            [normalized_query],
        )

        if len(embeddings) != 1:
            raise EmbeddingProviderError("Embedding provider returned an unexpected result")

        candidate_limit = limit
        if document_id is None:
            candidate_limit = min(
                max(limit * _CANDIDATE_MULTIPLIER, _MINIMUM_CANDIDATES),
                _MAXIMUM_CANDIDATES,
            )

        candidates = await self.repository.semantic_search(
            owner_id=owner_id,
            project_id=project_id,
            query_embedding=embeddings[0],
            limit=candidate_limit,
            document_id=document_id,
        )

        if document_id is not None:
            return candidates[:limit]

        return _rerank_project_candidates(normalized_query, candidates, limit)


def _significant_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) >= 3 and token not in _FILENAME_STOP_WORDS
    }


def _filename_bonus(query_tokens: set[str], filename: str) -> float:
    overlap = query_tokens & _significant_tokens(filename)
    return min(len(overlap) * _FILENAME_TOKEN_BONUS, _MAX_FILENAME_BONUS)


def _rerank_project_candidates(
    query: str,
    candidates: list[SemanticSearchResult],
    limit: int,
) -> list[SemanticSearchResult]:
    query_tokens = _significant_tokens(query)
    boosted = [
        replace(
            candidate,
            score=min(
                candidate.score
                + _filename_bonus(query_tokens, candidate.document_name),
                1.0,
            ),
        )
        for candidate in candidates
    ]
    ranked = sorted(
        boosted,
        key=lambda item: item.score,
        reverse=True,
    )

    selected: list[SemanticSearchResult] = []
    selected_ids: set[UUID] = set()
    document_counts: Counter[UUID] = Counter()

    for candidate in ranked:
        if document_counts[candidate.document_id] >= _MAX_CHUNKS_PER_DOCUMENT:
            continue
        selected.append(candidate)
        selected_ids.add(candidate.chunk_id)
        document_counts[candidate.document_id] += 1
        if len(selected) == limit:
            return selected

    # When only one or two documents have useful candidates, fill remaining
    # slots rather than reducing the available grounding context.
    for candidate in ranked:
        if candidate.chunk_id in selected_ids:
            continue
        selected.append(candidate)
        if len(selected) == limit:
            break

    return selected
