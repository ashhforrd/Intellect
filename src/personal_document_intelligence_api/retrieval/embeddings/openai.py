from collections.abc import Sequence
from typing import Any

from openai import OpenAIError

from .base import EmbeddingProviderError


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        client: Any,
        model: str,
        dimensions: int,
    ) -> None:
        self.client = client
        self.model = model
        self.embedding_dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self.embedding_dimensions

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=list(texts),
                dimensions=self.dimensions,
                encoding_format="float",
            )
        except OpenAIError as error:
            raise EmbeddingProviderError("Could not generate embeddings") from error

        ordered_embeddings = sorted(
            response.data,
            key=lambda item: item.index,
        )

        return [item.embedding for item in ordered_embeddings]
