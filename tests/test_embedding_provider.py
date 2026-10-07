from types import SimpleNamespace
from unittest.mock import Mock

from personal_document_intelligence_api.retrieval.embeddings.openai import (
    OpenAIEmbeddingProvider,
)


def test_embed_texts_returns_vectors_in_input_order() -> None:
    client = Mock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[0.3, 0.4]),
            SimpleNamespace(index=0, embedding=[0.1, 0.2]),
        ]
    )
    provider = OpenAIEmbeddingProvider(
        client=client,
        model="test-model",
        dimensions=2,
    )

    embeddings = provider.embed_texts(["first", "second"])

    assert embeddings == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]
