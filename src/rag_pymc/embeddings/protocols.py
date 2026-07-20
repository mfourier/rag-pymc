"""Project-owned embedding interfaces."""

from collections.abc import Sequence
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

type EmbeddingMatrix = NDArray[np.float32]


class Embedder(Protocol):
    """Encode retrieval queries and documents behind a provider-neutral boundary."""

    name: str
    model_id: str
    revision: str
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingMatrix:
        """Encode corpus documents into one row per input text."""
        ...

    def embed_query(self, text: str) -> EmbeddingMatrix:
        """Encode one search query as a one-row matrix."""
        ...
