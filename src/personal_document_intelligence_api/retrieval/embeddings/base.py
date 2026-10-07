from collections.abc import Sequence
from typing import Protocol


class EmbeddingProviderError(Exception):
    pass


class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int: ...

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]: ...
