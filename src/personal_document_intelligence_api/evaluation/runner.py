import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.session import (
    async_session_factory,
)
from personal_document_intelligence_api.evaluation.cases import (
    RetrievalEvaluationCase,
)
from personal_document_intelligence_api.evaluation.retrieval import (
    RetrievalCaseResult,
    evaluate_retrieval_case,
)
from personal_document_intelligence_api.retrieval.embeddings.factory import (
    create_embedding_provider,
)
from personal_document_intelligence_api.retrieval.search_service import (
    SemanticSearchService,
)


def load_cases(path: Path) -> list[RetrievalEvaluationCase]:
    raw_cases: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    return [
        RetrievalEvaluationCase(
            name=case["name"],
            question=case["question"],
            expected_terms=tuple(case["expected_terms"]),
        )
        for case in raw_cases
    ]


async def evaluate(
    *,
    dataset_path: Path,
    owner_id: str,
    limit: int,
) -> list[RetrievalCaseResult]:
    cases = load_cases(dataset_path)
    embedding_provider = create_embedding_provider()

    async with async_session_factory() as session:
        search_service = SemanticSearchService(
            repository=DocumentChunkRepository(session),
            embedding_provider=embedding_provider,
        )

        results: list[RetrievalCaseResult] = []

        for case in cases:
            retrieved_chunks = await search_service.search(
                query=case.question,
                owner_id=owner_id,
                limit=limit,
            )
            evaluation = evaluate_retrieval_case(
                case,
                retrieved_chunks,
            )
            results.append(evaluation)

            print(f"\n{evaluation.name}")
            print(f"  Hit: {'yes' if evaluation.hit else 'no'}")
            print(f"  Term coverage: {evaluation.term_coverage:.1%}")
            print(f"  Matched terms: {', '.join(evaluation.matched_terms) or 'none'}")

    return results


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate semantic retrieval quality.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evals/retrieval_cases.json"),
    )
    parser.add_argument(
        "--owner-id",
        default="local-development-user",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )

    return parser.parse_args()


async def main() -> None:
    arguments = parse_arguments()

    results = await evaluate(
        dataset_path=arguments.dataset,
        owner_id=arguments.owner_id,
        limit=arguments.limit,
    )

    hit_rate = sum(result.hit for result in results) / len(results)
    average_coverage = sum(result.term_coverage for result in results) / len(results)

    print("\nSummary")
    print(f"  Hit rate: {hit_rate:.1%}")
    print(f"  Average term coverage: {average_coverage:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
