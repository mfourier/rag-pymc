from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl, ValidationError

from rag_pymc.context import (
    ContextBuilder,
    ContextConstructionError,
    RankedContextBuilder,
)
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    ContextItem,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)
from rag_pymc.retrieval import TechnicalTokenizer

NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)
SOURCE_URL = "https://docs.example.test/api/pymc.sample.html"


def make_chunk(
    chunk_id: str,
    *,
    document_id: str | None = None,
    section: str | None = "Overview",
    content: str | None = None,
    library: str = "pymc",
    library_version: str = "6.1.0",
    source_url: str = SOURCE_URL,
    api_symbols: tuple[str, ...] = ("pymc.sample",),
) -> Chunk:
    chunk_content = content or f"Complete evidence for {chunk_id}."
    return Chunk(
        chunk_id=chunk_id,
        document_id=document_id or f"document_{chunk_id}",
        library=library,
        library_version=library_version,
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl(source_url),
        title="pymc.sample",
        section=section,
        content=chunk_content,
        content_hash=sha256(chunk_content.encode()).hexdigest(),
        api_symbols=api_symbols,
        created_at=NOW,
    )


def make_result(
    chunk: Chunk,
    *,
    rank: int,
    retriever: str = "weighted-rrf-v1",
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=chunk,
        score=1.0 / rank,
        rank=rank,
        retriever=retriever,
    )


def make_builder() -> ContextBuilder:
    return RankedContextBuilder(TechnicalTokenizer())


def test_builder_returns_bounded_context_with_complete_provenance() -> None:
    first = make_chunk("chunk_a", section="Parameters")
    second = make_chunk(
        "chunk_b",
        section="Examples",
        api_symbols=("pymc.sample", "pymc.Model"),
    )
    query = SearchQuery(
        text="How do I sample a model?",
        top_k=2,
        library="pymc",
        library_version="6.1.0",
    )

    context = make_builder().build(
        query,
        (make_result(second, rank=2), make_result(first, rank=1)),
        token_budget=10_000,
    )

    assert context.schema_version == "1"
    assert context.builder_version == "ranked-context-v1"
    assert context.rendering_policy == "context-item-text-v1"
    assert context.truncation_policy == "rank-prefix-whole-item-v1"
    assert context.query == query
    assert context.token_counter == "technical-v1"
    assert context.included_chunk_ids == ("chunk_a", "chunk_b")
    assert context.omitted_chunk_ids == ()
    assert context.used_tokens == sum(item.token_count for item in context.items)
    assert context.used_tokens <= context.token_budget

    item = context.items[1]
    assert item.position == 2
    assert item.retrieval_rank == 2
    assert item.retriever == "weighted-rrf-v1"
    assert item.chunk_id == second.chunk_id
    assert item.document_id == second.document_id
    assert item.source_url == second.source_url
    assert item.section == second.section
    assert item.library_version == second.library_version
    assert item.api_symbols == second.api_symbols
    assert item.content == second.content
    assert item.rendered_text.endswith(second.content)
    assert item.token_count == TechnicalTokenizer().count_tokens(item.rendered_text)


class SpyCounter:
    name = "spy-counter-v1"

    def __init__(self) -> None:
        self.texts: list[str] = []

    def count_tokens(self, text: str) -> int:
        self.texts.append(text)
        return len(text.split())


def test_canonical_rendering_counts_metadata_and_content() -> None:
    counter = SpyCounter()
    chunk = make_chunk("chunk_a", section=None, content="Evidence body.")
    result = make_result(chunk, rank=3, retriever="test-retriever")

    context = RankedContextBuilder(counter).build(
        SearchQuery(text="query"),
        (result,),
        token_budget=1_000,
    )

    expected = "\n".join(
        (
            "Context item: 1",
            "Retrieval rank: 3",
            "Retrieval strategy: test-retriever",
            "Chunk ID: chunk_a",
            "Document ID: document_chunk_a",
            f"Source URL: {SOURCE_URL}",
            "Library: pymc",
            "Library version: 6.1.0",
            "Source type: api_reference",
            "Title: pymc.sample",
            "Section: Unsectioned",
            "API symbols: pymc.sample",
            "",
            "Content:",
            "Evidence body.",
        )
    )
    item = context.items[0]
    assert counter.texts == [expected]
    assert item.rendered_text == expected
    assert item.token_count == len(expected.split())
    assert item.token_count > len(chunk.content.split())
    assert context.used_tokens == item.token_count


def test_budget_exact_fit_and_one_token_short_preserve_rank_prefix() -> None:
    first = make_result(make_chunk("chunk_a"), rank=1)
    second = make_result(make_chunk("chunk_b"), rank=2)
    full = make_builder().build(
        SearchQuery(text="query"),
        (first, second),
        token_budget=10_000,
    )
    first_cost = full.items[0].token_count

    exact = make_builder().build(
        SearchQuery(text="query"),
        (first, second),
        token_budget=first_cost,
    )
    short = make_builder().build(
        SearchQuery(text="query"),
        (first, second),
        token_budget=first_cost - 1,
    )

    assert exact.included_chunk_ids == ("chunk_a",)
    assert exact.omitted_chunk_ids == ("chunk_b",)
    assert exact.used_tokens == exact.token_budget
    assert short.included_chunk_ids == ()
    assert short.omitted_chunk_ids == ("chunk_a", "chunk_b")
    assert short.used_tokens == 0


def test_oversized_first_item_does_not_pack_a_smaller_tail() -> None:
    first = make_result(make_chunk("chunk_a", content="long evidence " * 200), rank=1)
    second = make_result(make_chunk("chunk_b", content="short evidence"), rank=2)
    second_only = make_builder().build(
        SearchQuery(text="query"),
        (second,),
        token_budget=10_000,
    )

    context = make_builder().build(
        SearchQuery(text="query"),
        (first, second),
        token_budget=second_only.used_tokens,
    )

    assert context.items == ()
    assert context.omitted_chunk_ids == ("chunk_a", "chunk_b")


def test_shuffled_rank_ties_produce_identical_json() -> None:
    results = (
        make_result(make_chunk("chunk_c"), rank=2),
        make_result(make_chunk("chunk_b"), rank=1),
        make_result(make_chunk("chunk_a"), rank=1),
    )
    query = SearchQuery(text="query")

    first = make_builder().build(query, results, token_budget=10_000)
    second = make_builder().build(query, tuple(reversed(results)), token_budget=10_000)

    assert first.included_chunk_ids == ("chunk_a", "chunk_b", "chunk_c")
    assert first.model_dump_json() == second.model_dump_json()
    serialized = first.model_dump(mode="json")
    assert "generated_at" not in serialized
    assert "latency_ms" not in serialized


def test_constructed_context_round_trips_through_json_without_drift() -> None:
    context = make_builder().build(
        SearchQuery(text="query", library="pymc", library_version="6.1.0"),
        (make_result(make_chunk("chunk_a"), rank=1),),
        token_budget=10_000,
    )

    serialized = context.model_dump_json()
    restored = ConstructedContext.model_validate_json(serialized)

    assert restored == context
    assert restored.model_dump_json() == serialized
    assert restored.items[0].source_url == context.items[0].source_url
    assert restored.items[0].rendered_text == context.items[0].rendered_text


def test_identical_duplicates_are_counted_once_with_canonical_metadata() -> None:
    chunk = make_chunk("chunk_a")
    candidates = (
        make_result(chunk, rank=3, retriever="sparse"),
        make_result(chunk, rank=1, retriever="zeta-retriever"),
        make_result(chunk, rank=1, retriever="alpha-retriever"),
    )

    first = make_builder().build(SearchQuery(text="query"), candidates, token_budget=10_000)
    second = make_builder().build(
        SearchQuery(text="query"),
        tuple(reversed(candidates)),
        token_budget=10_000,
    )

    assert first.included_chunk_ids == ("chunk_a",)
    assert first.items[0].retrieval_rank == 1
    assert first.items[0].retriever == "alpha-retriever"
    assert first.model_dump_json() == second.model_dump_json()


def test_conflicting_duplicate_is_rejected_before_budgeting() -> None:
    original = make_result(make_chunk("chunk_a", content="first payload"), rank=1)
    conflicting = make_result(make_chunk("chunk_a", content="different payload"), rank=2)

    with pytest.raises(ContextConstructionError, match="conflicting chunks for chunk_a"):
        make_builder().build(
            SearchQuery(text="query"),
            (original, conflicting),
            token_budget=1,
        )


def test_distinct_sections_from_one_source_are_not_deduplicated() -> None:
    overview = make_chunk("chunk_overview", document_id="document_shared", section="Overview")
    examples = make_chunk("chunk_examples", document_id="document_shared", section="Examples")

    context = make_builder().build(
        SearchQuery(text="query"),
        (make_result(examples, rank=2), make_result(overview, rank=1)),
        token_budget=10_000,
    )

    assert context.included_chunk_ids == ("chunk_overview", "chunk_examples")
    assert {item.document_id for item in context.items} == {"document_shared"}
    assert {str(item.source_url) for item in context.items} == {SOURCE_URL}


def test_empty_retrieval_returns_valid_empty_context() -> None:
    context = make_builder().build(SearchQuery(text="query"), (), token_budget=100)

    assert context.items == ()
    assert context.included_chunk_ids == ()
    assert context.omitted_chunk_ids == ()
    assert context.used_tokens == 0


def test_builder_rejects_query_and_candidate_version_conflicts() -> None:
    pymc_61 = make_result(make_chunk("chunk_a", library_version="6.1.0"), rank=1)
    pymc_60 = make_result(make_chunk("chunk_b", library_version="6.0.0"), rank=2)

    with pytest.raises(ContextConstructionError, match="query version"):
        make_builder().build(
            SearchQuery(text="query", library="pymc", library_version="6.1.0"),
            (pymc_60,),
            token_budget=10_000,
        )

    with pytest.raises(ContextConstructionError, match="mix library versions"):
        make_builder().build(
            SearchQuery(text="query"),
            (pymc_61, pymc_60),
            token_budget=10_000,
        )

    with pytest.raises(ContextConstructionError, match="query library"):
        make_builder().build(
            SearchQuery(text="query", library="arviz"),
            (pymc_61,),
            token_budget=10_000,
        )


def test_builder_rejects_mixed_libraries_without_compatibility_policy() -> None:
    pymc = make_result(make_chunk("chunk_pymc", library="pymc"), rank=1)
    arviz = make_result(
        make_chunk(
            "chunk_arviz",
            library="arviz",
            library_version="1.2.0",
            api_symbols=("arviz.summary",),
        ),
        rank=2,
    )

    with pytest.raises(ContextConstructionError, match="mix libraries"):
        make_builder().build(
            SearchQuery(text="query"),
            (pymc, arviz),
            token_budget=1,
        )


def test_constructed_context_rejects_inconsistent_accounting_and_identity() -> None:
    valid = make_builder().build(
        SearchQuery(text="query"),
        (make_result(make_chunk("chunk_a"), rank=1),),
        token_budget=10_000,
    )
    inconsistent_tokens = valid.model_dump()
    inconsistent_tokens["used_tokens"] = valid.used_tokens + 1
    overlapping_ids = valid.model_dump()
    overlapping_ids["omitted_chunk_ids"] = ("chunk_a",)

    with pytest.raises(ValidationError, match="sum of context item token counts"):
        ConstructedContext.model_validate(inconsistent_tokens)
    with pytest.raises(ValidationError, match="must not overlap"):
        ConstructedContext.model_validate(overlapping_ids)


def test_context_item_rejects_noncanonical_rendering() -> None:
    valid = make_builder().build(
        SearchQuery(text="query"),
        (make_result(make_chunk("chunk_a"), rank=1),),
        token_budget=10_000,
    )
    item_data = valid.items[0].model_dump()
    item_data["rendered_text"] = "Content that does not match the structured evidence."

    with pytest.raises(ValidationError, match="canonical context-item-text-v1"):
        ContextItem.model_validate(item_data)


def test_context_models_do_not_coerce_booleans_to_integer_accounting_fields() -> None:
    empty_context = {
        "builder_version": "ranked-context-v1",
        "rendering_policy": "context-item-text-v1",
        "truncation_policy": "rank-prefix-whole-item-v1",
        "query": SearchQuery(text="query"),
        "token_counter": "technical-v1",
        "token_budget": True,
        "used_tokens": 0,
    }

    with pytest.raises(ValidationError, match="token_budget"):
        ConstructedContext.model_validate(empty_context)


class FixedCounter:
    def __init__(self, *, name: str, count: int) -> None:
        self.name = name
        self.count = count

    def count_tokens(self, text: str) -> int:
        return self.count


def test_builder_rejects_invalid_counter_identity_and_counts() -> None:
    with pytest.raises(ContextConstructionError, match="name must not be empty"):
        RankedContextBuilder(FixedCounter(name=" ", count=1))

    builder = RankedContextBuilder(FixedCounter(name="zero-v1", count=0))
    with pytest.raises(ContextConstructionError, match="positive integer"):
        builder.build(
            SearchQuery(text="query"),
            (make_result(make_chunk("chunk_a"), rank=1),),
            token_budget=10_000,
        )


@pytest.mark.parametrize("token_budget", [0, -1, True, 1.5])
def test_builder_rejects_invalid_token_budgets(token_budget: object) -> None:
    with pytest.raises(ContextConstructionError, match="positive integer"):
        make_builder().build(
            SearchQuery(text="query"),
            (),
            token_budget=token_budget,  # type: ignore[arg-type]
        )
