from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl

from rag_pymc.application import ContextInspectionService
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)


def make_result() -> RetrievedChunk:
    content = "Evidence for pymc.sample."
    chunk = Chunk(
        chunk_id="chunk_sample",
        document_id="document_sample",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl("https://docs.example.test/pymc.sample.html"),
        title="pymc.sample",
        section="Overview",
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        api_symbols=("pymc.sample",),
        created_at=datetime(2026, 7, 21, tzinfo=UTC),
    )
    return RetrievedChunk(
        chunk=chunk,
        score=1.0,
        rank=1,
        retriever="recording-retriever-v1",
    )


def make_context(query: SearchQuery, *, token_budget: int) -> ConstructedContext:
    return ConstructedContext(
        builder_version="recording-builder-v1",
        rendering_policy="context-item-text-v1",
        truncation_policy="rank-prefix-whole-item-v1",
        query=query,
        token_counter="recording-counter-v1",
        token_budget=token_budget,
        used_tokens=0,
    )


class RecordingRetriever:
    def __init__(
        self,
        results: list[RetrievedChunk],
        *,
        error: Exception | None = None,
    ) -> None:
        self.results = results
        self.error = error
        self.queries: list[SearchQuery] = []

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return self.results


class RecordingContextBuilder:
    name = "recording-builder-v1"
    rendering_policy = "context-item-text-v1"
    truncation_policy = "rank-prefix-whole-item-v1"

    def __init__(
        self,
        result: ConstructedContext,
        *,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[SearchQuery, Sequence[RetrievedChunk], int]] = []

    def build(
        self,
        query: SearchQuery,
        retrieved: Sequence[RetrievedChunk],
        *,
        token_budget: int,
    ) -> ConstructedContext:
        self.calls.append((query, retrieved, token_budget))
        if self.error is not None:
            raise self.error
        return self.result


def test_inspect_retrieves_and_builds_once_then_returns_exact_context() -> None:
    query = SearchQuery(text="How do I sample?", library="pymc", library_version="6.1.0")
    retrieved = [make_result()]
    expected = make_context(query, token_budget=512)
    retriever = RecordingRetriever(retrieved)
    builder = RecordingContextBuilder(expected)
    service = ContextInspectionService(retriever=retriever, context_builder=builder)

    actual = service.inspect(query, token_budget=512)

    assert actual is expected
    assert retriever.queries == [query]
    assert len(builder.calls) == 1
    built_query, built_retrieved, built_budget = builder.calls[0]
    assert built_query is query
    assert built_retrieved is retrieved
    assert built_budget == 512


def test_inspect_propagates_retriever_errors_without_building() -> None:
    query = SearchQuery(text="query")
    expected = make_context(query, token_budget=100)
    retrieval_error = RuntimeError("retrieval failed")
    retriever = RecordingRetriever([], error=retrieval_error)
    builder = RecordingContextBuilder(expected)
    service = ContextInspectionService(retriever=retriever, context_builder=builder)

    with pytest.raises(RuntimeError) as raised:
        service.inspect(query, token_budget=100)

    assert raised.value is retrieval_error
    assert retriever.queries == [query]
    assert builder.calls == []


def test_inspect_propagates_builder_errors_after_one_retrieval() -> None:
    query = SearchQuery(text="query")
    retrieved = [make_result()]
    expected = make_context(query, token_budget=100)
    builder_error = ValueError("context build failed")
    retriever = RecordingRetriever(retrieved)
    builder = RecordingContextBuilder(expected, error=builder_error)
    service = ContextInspectionService(retriever=retriever, context_builder=builder)

    with pytest.raises(ValueError) as raised:
        service.inspect(query, token_budget=100)

    assert raised.value is builder_error
    assert retriever.queries == [query]
    assert len(builder.calls) == 1
    assert builder.calls[0][1] is retrieved
    assert builder.calls[0][2] == 100
