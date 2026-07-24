from datetime import UTC, datetime
from typing import Literal

import pytest
from pydantic import ValidationError

from rag_pymc.domain import Chunk, Difficulty
from rag_pymc.evaluation import (
    AdjudicationProvenance,
    AnnotationProvenance,
    AtomicGoldClaim,
    EvaluationDatasetError,
    GoldEvidenceSupportSet,
    Phase5DevelopmentDataset,
    Phase5DevelopmentExample,
    hash_phase5_corpus,
    validate_phase5_development_corpus,
)
from tests.factories import make_chunk as make_test_chunk

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
CORPUS_HASH_POLICY: Literal["canonical-chunk-identity-json-v1"] = "canonical-chunk-identity-json-v1"


def make_chunk(
    chunk_id: str,
    *,
    content: str | None = None,
    library: str = "pymc",
    library_version: str = "6.1.0",
) -> Chunk:
    resolved_content = content or f"Evidence in {chunk_id}."
    return make_test_chunk(
        chunk_id,
        resolved_content,
        library=library,
        version=library_version,
        source_url=f"https://docs.example.test/{chunk_id}.html",
        title="Synthetic API",
        section="Details",
        symbols=("pymc.sample",),
        created_at=NOW,
    )


def make_dataset(
    chunks: tuple[Chunk, ...],
    *,
    support_chunk_ids: tuple[str, ...] = ("chunk_a",),
    example_library: str = "pymc",
    example_library_version: str = "6.1.0",
) -> Phase5DevelopmentDataset:
    example = Phase5DevelopmentExample(
        query_id="dev_q_001",
        query_text="How do I use the synthetic API?",
        query_family="synthetic-api",
        template_family="single-api-workflow",
        library=example_library,
        library_version=example_library_version,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=hash_phase5_corpus(chunks),
        corpus_answerable=True,
        intent="synthetic_intent",
        difficulty=Difficulty.INTERMEDIATE,
        expected_api_symbols=("pymc.sample",),
        gold_claims=(
            AtomicGoldClaim(
                claim_id="dev_q_001_claim_001",
                text="A synthetic corpus-supported claim.",
                support_sets=(GoldEvidenceSupportSet(chunk_ids=support_chunk_ids),),
            ),
        ),
        annotation=AnnotationProvenance(
            annotator_ids=("annotator_001",),
            guideline_version="phase5-annotation-guidelines-v1",
            batch_id="annotation-batch-001",
            annotated_at=NOW,
        ),
        adjudication=AdjudicationProvenance(
            adjudicator_ids=("adjudicator_001",),
            guideline_version="phase5-adjudication-guidelines-v1",
            batch_id="adjudication-batch-001",
            adjudicated_at=NOW,
        ),
    )
    return Phase5DevelopmentDataset(
        dataset_sha256="a" * 64,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=hash_phase5_corpus(chunks),
        examples=(example,),
    )


def test_phase5_corpus_hash_is_order_invariant_and_content_sensitive() -> None:
    first = make_chunk("chunk_a")
    second = make_chunk("chunk_b")
    changed = make_chunk("chunk_b", content="Changed evidence.")

    assert hash_phase5_corpus((first, second)) == hash_phase5_corpus((second, first))
    assert hash_phase5_corpus((first, second)) != hash_phase5_corpus((first, changed))


def test_phase5_corpus_hash_rejects_duplicate_chunk_identities() -> None:
    first = make_chunk("chunk_a")
    conflicting = make_chunk("chunk_a", content="Conflicting evidence.")

    with pytest.raises(EvaluationDatasetError, match="duplicate chunk IDs"):
        hash_phase5_corpus((first, conflicting))


def test_development_corpus_validation_resolves_every_gold_reference() -> None:
    chunks = (make_chunk("chunk_a"), make_chunk("chunk_b"))
    dataset = make_dataset(chunks, support_chunk_ids=("chunk_a", "chunk_b"))

    first = validate_phase5_development_corpus(dataset, chunks)
    second = validate_phase5_development_corpus(dataset, tuple(reversed(chunks)))
    restored = type(first).model_validate_json(first.model_dump_json())

    assert first == second
    assert restored == first
    assert first.validator_version == "phase5-development-corpus-v1"
    assert first.corpus_hash_policy == CORPUS_HASH_POLICY
    assert first.corpus_sha256 == hash_phase5_corpus(chunks)
    assert first.corpus_chunk_count == 2
    assert first.query_count == 1
    assert first.answerable_query_count == 1
    assert first.gold_claim_count == 1
    assert first.gold_support_set_count == 1
    assert first.referenced_chunk_ids == ("chunk_a", "chunk_b")
    assert first.referenced_chunk_count == 2


def test_development_corpus_validation_revalidates_derived_counts() -> None:
    chunks = (make_chunk("chunk_a"),)
    report = validate_phase5_development_corpus(make_dataset(chunks), chunks)
    tampered = report.model_copy(update={"referenced_chunk_count": 0})

    with pytest.raises(ValidationError, match="must match referenced_chunk_ids"):
        type(report).model_validate(tampered)


def test_development_corpus_validation_rejects_a_hash_mismatch() -> None:
    chunks = (make_chunk("chunk_a"),)
    original = make_dataset(chunks)
    mismatched_examples = tuple(
        example.model_copy(update={"corpus_sha256": "d" * 64}) for example in original.examples
    )
    dataset = original.model_copy(
        update={"corpus_sha256": "d" * 64, "examples": mismatched_examples}
    )

    with pytest.raises(EvaluationDatasetError, match="SHA-256 mismatch"):
        validate_phase5_development_corpus(dataset, chunks)


def test_development_corpus_validation_rejects_missing_gold_chunks() -> None:
    chunks = (make_chunk("chunk_a"),)
    dataset = make_dataset(chunks, support_chunk_ids=("missing_chunk",))

    with pytest.raises(EvaluationDatasetError, match="references missing chunk"):
        validate_phase5_development_corpus(dataset, chunks)


@pytest.mark.parametrize(
    ("library", "library_version"),
    [("pytensor", "6.1.0"), ("pymc", "6.2.0")],
)
def test_development_corpus_validation_rejects_cross_namespace_gold_chunks(
    library: str,
    library_version: str,
) -> None:
    chunks = (
        make_chunk(
            "chunk_a",
            library=library,
            library_version=library_version,
        ),
    )
    dataset = make_dataset(chunks)

    with pytest.raises(EvaluationDatasetError, match="different library or version"):
        validate_phase5_development_corpus(dataset, chunks)


def test_development_corpus_validation_rejects_an_empty_corpus() -> None:
    chunks = (make_chunk("chunk_a"),)
    dataset = make_dataset(chunks)

    with pytest.raises(EvaluationDatasetError, match="at least one chunk"):
        validate_phase5_development_corpus(dataset, ())
