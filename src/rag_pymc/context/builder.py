"""Deterministic construction of bounded context from ranked chunks."""

from collections import defaultdict
from collections.abc import Sequence
from typing import Literal

from rag_pymc.context.protocols import TokenCounter
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    ContextItem,
    RetrievedChunk,
    SearchQuery,
    render_context_item_v1,
)


class ContextConstructionError(ValueError):
    """Raised when candidates or context accounting violate the policy."""


class RankedContextBuilder:
    """Build a canonical rank prefix without truncating individual chunks."""

    name = "ranked-context-v1"
    rendering_policy: Literal["context-item-text-v1"] = "context-item-text-v1"
    truncation_policy: Literal["rank-prefix-whole-item-v1"] = "rank-prefix-whole-item-v1"

    def __init__(self, token_counter: TokenCounter) -> None:
        """Configure context accounting through a project-owned counter boundary."""
        counter_name = token_counter.name
        if not isinstance(counter_name, str) or not counter_name.strip():
            msg = "token counter name must not be empty"
            raise ContextConstructionError(msg)
        self._token_counter = token_counter
        self._token_counter_name = counter_name.strip()

    def build(
        self,
        query: SearchQuery,
        retrieved: Sequence[RetrievedChunk],
        *,
        token_budget: int,
    ) -> ConstructedContext:
        """Return a deterministic complete-item prefix within the token budget."""
        if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget < 1:
            msg = "token_budget must be a positive integer"
            raise ContextConstructionError(msg)

        candidates = self._canonicalize(retrieved)
        self._validate_version_boundaries(query, candidates)
        items: list[ContextItem] = []
        used_tokens = 0
        omitted_chunk_ids: tuple[str, ...] = ()

        for candidate_index, result in enumerate(candidates):
            position = len(items) + 1
            chunk = result.chunk
            rendered_text = render_context_item_v1(
                position=position,
                retrieval_rank=result.rank,
                retriever=result.retriever,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                source_url=chunk.source_url,
                library=chunk.library,
                library_version=chunk.library_version,
                source_type=chunk.source_type,
                title=chunk.title,
                section=chunk.section,
                api_symbols=chunk.api_symbols,
                content=chunk.content,
            )
            token_count = self._count_tokens(rendered_text)
            if used_tokens + token_count > token_budget:
                omitted_chunk_ids = tuple(
                    candidate.chunk.chunk_id for candidate in candidates[candidate_index:]
                )
                break

            items.append(
                ContextItem(
                    position=position,
                    retrieval_rank=result.rank,
                    retriever=result.retriever,
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    library=chunk.library,
                    library_version=chunk.library_version,
                    source_type=chunk.source_type,
                    source_url=chunk.source_url,
                    title=chunk.title,
                    section=chunk.section,
                    api_symbols=chunk.api_symbols,
                    content=chunk.content,
                    rendered_text=rendered_text,
                    token_count=token_count,
                )
            )
            used_tokens += token_count

        immutable_items = tuple(items)
        return ConstructedContext(
            builder_version=self.name,
            rendering_policy=self.rendering_policy,
            truncation_policy=self.truncation_policy,
            query=query,
            token_counter=self._token_counter_name,
            token_budget=token_budget,
            used_tokens=used_tokens,
            items=immutable_items,
            included_chunk_ids=tuple(item.chunk_id for item in immutable_items),
            omitted_chunk_ids=omitted_chunk_ids,
        )

    @staticmethod
    def _canonicalize(retrieved: Sequence[RetrievedChunk]) -> tuple[RetrievedChunk, ...]:
        chunks_by_id: dict[str, Chunk] = {}
        for result in retrieved:
            chunk_id = result.chunk.chunk_id
            existing = chunks_by_id.get(chunk_id)
            if existing is not None and existing != result.chunk:
                msg = f"retrieval results contain conflicting chunks for {chunk_id}"
                raise ContextConstructionError(msg)
            chunks_by_id[chunk_id] = result.chunk

        ordered = sorted(
            retrieved,
            key=lambda result: (result.rank, result.chunk.chunk_id, result.retriever),
        )
        seen: set[str] = set()
        canonical: list[RetrievedChunk] = []
        for result in ordered:
            chunk_id = result.chunk.chunk_id
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            canonical.append(result)
        return tuple(canonical)

    @staticmethod
    def _validate_version_boundaries(
        query: SearchQuery,
        candidates: Sequence[RetrievedChunk],
    ) -> None:
        versions_by_library: defaultdict[str, set[str]] = defaultdict(set)
        for result in candidates:
            chunk = result.chunk
            if query.library is not None and chunk.library.casefold() != query.library.casefold():
                msg = (
                    f"chunk {chunk.chunk_id} library {chunk.library!r} conflicts with "
                    f"query library {query.library!r}"
                )
                raise ContextConstructionError(msg)
            if query.library_version is not None and chunk.library_version != query.library_version:
                msg = (
                    f"chunk {chunk.chunk_id} version {chunk.library_version!r} conflicts with "
                    f"query version {query.library_version!r}"
                )
                raise ContextConstructionError(msg)
            versions_by_library[chunk.library.casefold()].add(chunk.library_version)

        conflicting = {
            library: versions
            for library, versions in versions_by_library.items()
            if len(versions) > 1
        }
        if conflicting:
            details = ", ".join(
                f"{library}={sorted(versions)}" for library, versions in sorted(conflicting.items())
            )
            msg = f"context candidates mix library versions: {details}"
            raise ContextConstructionError(msg)
        if len(versions_by_library) > 1:
            libraries = ", ".join(sorted(versions_by_library))
            msg = f"context candidates mix libraries without a compatibility policy: {libraries}"
            raise ContextConstructionError(msg)

    def _count_tokens(self, rendered_text: str) -> int:
        token_count = self._token_counter.count_tokens(rendered_text)
        if isinstance(token_count, bool) or not isinstance(token_count, int) or token_count < 1:
            msg = "token counter must return a positive integer for each rendered item"
            raise ContextConstructionError(msg)
        return token_count
