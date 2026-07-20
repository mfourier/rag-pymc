"""Inspectable in-memory Okapi BM25 index."""

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery
from rag_pymc.retrieval.filters import matches_filters
from rag_pymc.retrieval.tokenization import TechnicalTokenizer


@dataclass(frozen=True, slots=True)
class _IndexedChunk:
    chunk: Chunk
    term_frequencies: Counter[str]
    length: int


class BM25Index:
    """Rank chunks with Okapi BM25 after applying exact metadata filters."""

    name = "bm25-v1"

    def __init__(
        self,
        chunks: Sequence[Chunk],
        *,
        tokenizer: TechnicalTokenizer | None = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        """Build an immutable in-memory lexical representation."""
        if k1 <= 0:
            msg = "k1 must be greater than zero"
            raise ValueError(msg)
        if not 0 <= b <= 1:
            msg = "b must be between zero and one"
            raise ValueError(msg)

        self.tokenizer = tokenizer or TechnicalTokenizer()
        self.k1 = k1
        self.b = b
        self._chunks = tuple(
            _IndexedChunk(
                chunk=chunk,
                term_frequencies=Counter(tokens),
                length=len(tokens),
            )
            for chunk in chunks
            for tokens in (self.tokenizer.tokenize(chunk.content),)
        )

    def search(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Return positive-score BM25 matches with deterministic tie-breaking."""
        candidates = tuple(item for item in self._chunks if matches_filters(item.chunk, query))
        if not candidates:
            return []

        query_terms = self.tokenizer.tokenize(query.text)
        if not query_terms:
            return []

        average_length = sum(item.length for item in candidates) / len(candidates)
        document_frequency = {
            term: sum(term in item.term_frequencies for item in candidates)
            for term in set(query_terms)
        }
        scored = [
            (
                self._score(item, query_terms, document_frequency, len(candidates), average_length),
                item,
            )
            for item in candidates
        ]
        ranked = sorted(
            ((score, item) for score, item in scored if score > 0),
            key=lambda pair: (-pair[0], pair[1].chunk.chunk_id),
        )[: query.top_k]

        return [
            RetrievedChunk(
                chunk=item.chunk,
                score=score,
                rank=rank,
                retriever=self.name,
            )
            for rank, (score, item) in enumerate(ranked, start=1)
        ]

    def _score(
        self,
        item: _IndexedChunk,
        query_terms: tuple[str, ...],
        document_frequency: dict[str, int],
        corpus_size: int,
        average_length: float,
    ) -> float:
        score = 0.0
        for term, query_frequency in Counter(query_terms).items():
            term_frequency = item.term_frequencies.get(term, 0)
            if term_frequency == 0:
                continue
            frequency = document_frequency[term]
            inverse_document_frequency = math.log(
                1 + (corpus_size - frequency + 0.5) / (frequency + 0.5)
            )
            length_ratio = item.length / average_length if average_length else 0.0
            denominator = term_frequency + self.k1 * (1 - self.b + self.b * length_ratio)
            score += (
                query_frequency
                * inverse_document_frequency
                * term_frequency
                * (self.k1 + 1)
                / denominator
            )
        return score
