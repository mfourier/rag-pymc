import copy
import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from rag_pymc.evaluation import (
    AdjudicationProvenance,
    AnnotationProvenance,
    AtomicGoldClaim,
    EvaluationDatasetError,
    GoldEvidenceSupportSet,
    Phase5DevelopmentDataset,
    Phase5DevelopmentExample,
    load_phase5_development_dataset,
)

CORPUS_SHA256 = "c" * 64
OTHER_CORPUS_SHA256 = "d" * 64


def make_answerable_payload(
    query_id: str = "dev_q_001",
    *,
    claim_id: str = "dev_q_001_claim_001",
) -> dict[str, Any]:
    return {
        "schema_version": "phase5-development-annotation-v1",
        "query_id": query_id,
        "query_text": "How do I update data before posterior prediction?",
        "query_family": "mutable-data-prediction",
        "template_family": "api-workflow-two-stage",
        "library": "pymc",
        "library_version": "6.1.0",
        "corpus_hash_policy": "canonical-chunk-identity-json-v1",
        "corpus_sha256": CORPUS_SHA256,
        "corpus_answerable": True,
        "intent": "posterior_prediction",
        "difficulty": "intermediate",
        "hard_negative_category": None,
        "expected_api_symbols": ["pymc.Data", "pymc.set_data"],
        "gold_claims": [
            {
                "claim_id": claim_id,
                "text": "Update registered data before drawing posterior predictions.",
                "support_sets": [
                    {"chunk_ids": ["chunk_a"]},
                    {"chunk_ids": ["chunk_b", "chunk_c"]},
                ],
            }
        ],
        "annotation": {
            "method": "human",
            "annotator_ids": ["annotator_001", "annotator_002"],
            "guideline_version": "phase5-annotation-guidelines-v1",
            "batch_id": "annotation-batch-001",
            "annotated_at": "2026-07-23T12:00:00Z",
        },
        "adjudication": {
            "method": "human",
            "status": "accepted",
            "adjudicator_ids": ["adjudicator_001"],
            "guideline_version": "phase5-adjudication-guidelines-v1",
            "batch_id": "adjudication-batch-001",
            "adjudicated_at": "2026-07-23T13:00:00Z",
        },
    }


def make_unanswerable_payload(query_id: str = "dev_q_002") -> dict[str, Any]:
    payload = make_answerable_payload(query_id)
    payload.update(
        {
            "query_text": "Can pymc.set_data change a variable's dimensionality?",
            "query_family": "mutable-data-unsupported-operation",
            "template_family": "unsupported-api-capability",
            "corpus_answerable": False,
            "hard_negative_category": "nearby-api-does-not-support-requested-operation",
            "gold_claims": [],
        }
    )
    return payload


def write_jsonl(path: Path, payloads: list[dict[str, Any]]) -> bytes:
    raw_bytes = "".join(
        f"{json.dumps(payload, sort_keys=True, separators=(',', ':'))}\n" for payload in payloads
    ).encode()
    path.write_bytes(raw_bytes)
    return raw_bytes


def test_loader_preserves_file_order_and_hashes_exact_raw_bytes(tmp_path: Path) -> None:
    first = make_unanswerable_payload("dev_q_002")
    second = make_answerable_payload("dev_q_001")
    first_line = json.dumps(first, sort_keys=False, separators=(",", ":"))
    second_line = json.dumps(second, sort_keys=True, separators=(",", ":"))
    raw_bytes = f"\n{first_line}\r\n   \n{second_line}\n".encode()
    path = tmp_path / "development.jsonl"
    path.write_bytes(raw_bytes)

    dataset = load_phase5_development_dataset(path)
    restored = Phase5DevelopmentDataset.model_validate_json(dataset.model_dump_json())

    assert dataset.schema_version == "phase5-development-dataset-v1"
    assert dataset.dataset_role == "development"
    assert dataset.dataset_hash_policy == "sha256-raw-file-bytes-v1"
    assert dataset.corpus_hash_policy == "canonical-chunk-identity-json-v1"
    assert dataset.dataset_sha256 == sha256(raw_bytes).hexdigest()
    assert dataset.corpus_sha256 == CORPUS_SHA256
    assert tuple(example.query_id for example in dataset.examples) == (
        "dev_q_002",
        "dev_q_001",
    )
    assert dataset.examples[1].gold_claims[0].support_sets[0].chunk_ids == ("chunk_a",)
    assert dataset.examples[1].gold_claims[0].support_sets[1].chunk_ids == (
        "chunk_b",
        "chunk_c",
    )
    assert restored == dataset


def test_development_contracts_are_immutable_and_forbid_extra_fields() -> None:
    example = Phase5DevelopmentExample.model_validate(make_answerable_payload())

    with pytest.raises(ValidationError, match="frozen"):
        example.query_text = "Changed"

    payload = make_answerable_payload()
    payload["retrieval_score"] = 0.9
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Phase5DevelopmentExample.model_validate(payload)


def test_corpus_annotation_excludes_runtime_outcome_fields() -> None:
    runtime_fields = {
        "retrieved_chunk_ids",
        "included_chunk_ids",
        "omitted_chunk_ids",
        "token_budget",
        "evidence_sufficiency",
        "should_abstain",
    }

    assert runtime_fields.isdisjoint(Phase5DevelopmentExample.model_fields)


@pytest.mark.parametrize(
    ("chunk_ids", "match"),
    [
        (("chunk_a", "chunk_a"), "chunk IDs must be unique"),
        (("chunk_b", "chunk_a"), "lexicographically ordered"),
    ],
)
def test_support_set_requires_unique_canonical_chunk_ids(
    chunk_ids: tuple[str, ...],
    match: str,
) -> None:
    with pytest.raises(ValidationError, match=match):
        GoldEvidenceSupportSet(chunk_ids=chunk_ids)


@pytest.mark.parametrize(
    ("support_sets", "match"),
    [
        (
            (
                GoldEvidenceSupportSet(chunk_ids=("chunk_a",)),
                GoldEvidenceSupportSet(chunk_ids=("chunk_a",)),
            ),
            "support sets must be unique",
        ),
        (
            (
                GoldEvidenceSupportSet(chunk_ids=("chunk_b",)),
                GoldEvidenceSupportSet(chunk_ids=("chunk_a",)),
            ),
            "lexicographically ordered",
        ),
        (
            (
                GoldEvidenceSupportSet(chunk_ids=("chunk_a",)),
                GoldEvidenceSupportSet(chunk_ids=("chunk_a", "chunk_b")),
            ),
            "minimal antichain",
        ),
    ],
)
def test_atomic_claim_rejects_duplicate_noncanonical_or_nonminimal_alternatives(
    support_sets: tuple[GoldEvidenceSupportSet, ...],
    match: str,
) -> None:
    with pytest.raises(ValidationError, match=match):
        AtomicGoldClaim(
            claim_id="claim_001",
            text="A synthetic claim.",
            support_sets=support_sets,
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("answerable_without_claims", "require at least one gold claim"),
        ("answerable_hard_negative", "cannot be hard negatives"),
        ("unanswerable_with_claims", "cannot contain gold claims"),
        ("non_strict_answerability", "valid boolean"),
    ],
)
def test_example_enforces_corpus_answerability(mutation: str, match: str) -> None:
    payload = make_answerable_payload()
    if mutation == "answerable_without_claims":
        payload["gold_claims"] = []
    elif mutation == "answerable_hard_negative":
        payload["hard_negative_category"] = "synthetic-negative"
    elif mutation == "unanswerable_with_claims":
        payload["corpus_answerable"] = False
    else:
        payload["corpus_answerable"] = 1

    with pytest.raises(ValidationError, match=match):
        Phase5DevelopmentExample.model_validate(payload)


def test_unanswerable_example_may_record_an_adjudicated_hard_negative_category() -> None:
    example = Phase5DevelopmentExample.model_validate(make_unanswerable_payload())

    assert example.corpus_answerable is False
    assert example.gold_claims == ()
    assert example.hard_negative_category == ("nearby-api-does-not-support-requested-operation")
    assert example.annotation.method == "human"
    assert example.adjudication.status == "accepted"


@pytest.mark.parametrize(
    ("symbols", "match"),
    [
        (["pymc.Data", "pymc.Data"], "expected API symbols must be unique"),
        (["pymc.set_data", "pymc.Data"], "lexicographically ordered"),
    ],
)
def test_expected_api_symbols_are_unique_and_canonical(
    symbols: list[str],
    match: str,
) -> None:
    payload = make_answerable_payload()
    payload["expected_api_symbols"] = symbols

    with pytest.raises(ValidationError, match=match):
        Phase5DevelopmentExample.model_validate(payload)


def test_claim_ids_are_unique_within_an_example() -> None:
    payload = make_answerable_payload()
    payload["gold_claims"].append(copy.deepcopy(payload["gold_claims"][0]))

    with pytest.raises(ValidationError, match="gold claim IDs must be unique"):
        Phase5DevelopmentExample.model_validate(payload)


@pytest.mark.parametrize(
    ("provenance", "ids_field", "ids", "match"),
    [
        (
            "annotation",
            "annotator_ids",
            ["annotator_001", "annotator_001"],
            "annotator IDs must be unique",
        ),
        (
            "annotation",
            "annotator_ids",
            ["annotator_002", "annotator_001"],
            "lexicographically ordered",
        ),
        (
            "adjudication",
            "adjudicator_ids",
            ["adjudicator_001", "adjudicator_001"],
            "adjudicator IDs must be unique",
        ),
    ],
)
def test_provenance_reviewer_ids_are_unique_and_canonical(
    provenance: str,
    ids_field: str,
    ids: list[str],
    match: str,
) -> None:
    payload = make_answerable_payload()
    payload[provenance][ids_field] = ids

    with pytest.raises(ValidationError, match=match):
        Phase5DevelopmentExample.model_validate(payload)


def test_adjudication_cannot_precede_annotation() -> None:
    payload = make_answerable_payload()
    payload["adjudication"]["adjudicated_at"] = "2026-07-23T11:59:59Z"

    with pytest.raises(ValidationError, match="must not precede annotation"):
        Phase5DevelopmentExample.model_validate(payload)


def test_adjudicator_must_be_independent_from_annotators() -> None:
    payload = make_answerable_payload()
    payload["adjudication"]["adjudicator_ids"] = ["annotator_001"]

    with pytest.raises(ValidationError, match="independent from annotators"):
        Phase5DevelopmentExample.model_validate(payload)


def test_loader_rejects_duplicate_query_ids_with_second_line_number(tmp_path: Path) -> None:
    path = tmp_path / "development.jsonl"
    write_jsonl(path, [make_answerable_payload(), make_unanswerable_payload("dev_q_001")])

    with pytest.raises(
        EvaluationDatasetError,
        match=r"duplicate Phase 5 development query_id.*development\.jsonl:2: dev_q_001",
    ):
        load_phase5_development_dataset(path)


def test_loader_rejects_globally_duplicate_claim_ids(tmp_path: Path) -> None:
    first = make_answerable_payload("dev_q_001", claim_id="claim_shared")
    second = make_answerable_payload("dev_q_002", claim_id="claim_shared")
    path = tmp_path / "development.jsonl"
    write_jsonl(path, [first, second])

    with pytest.raises(
        EvaluationDatasetError,
        match=r"duplicate Phase 5 development claim_id.*development\.jsonl:2: claim_shared",
    ):
        load_phase5_development_dataset(path)


def test_loader_rejects_mixed_corpus_namespaces(tmp_path: Path) -> None:
    second = make_unanswerable_payload()
    second["corpus_sha256"] = OTHER_CORPUS_SHA256
    path = tmp_path / "development.jsonl"
    write_jsonl(path, [make_answerable_payload(), second])

    with pytest.raises(
        EvaluationDatasetError,
        match=r"inconsistent Phase 5 corpus_sha256.*development\.jsonl:2",
    ):
        load_phase5_development_dataset(path)


@pytest.mark.parametrize(
    "line",
    [
        "{not-json}",
        '{"query_id":"first","query_id":"second"}',
        '{"value":NaN}',
    ],
)
def test_loader_rejects_malformed_ambiguous_or_nonstandard_json_with_line_number(
    tmp_path: Path,
    line: str,
) -> None:
    path = tmp_path / "development.jsonl"
    path.write_text(f"\n{line}\n", encoding="utf-8")

    with pytest.raises(
        EvaluationDatasetError,
        match=r"invalid Phase 5 development example.*development\.jsonl:2",
    ):
        load_phase5_development_dataset(path)


def test_loader_rejects_unsupported_schema_version_with_line_number(tmp_path: Path) -> None:
    payload = make_answerable_payload()
    payload["schema_version"] = "phase5-development-annotation-v2"
    path = tmp_path / "development.jsonl"
    write_jsonl(path, [payload])

    with pytest.raises(
        EvaluationDatasetError,
        match=r"invalid Phase 5 development example.*development\.jsonl:1",
    ):
        load_phase5_development_dataset(path)


def test_loader_rejects_invalid_utf8_with_line_number(tmp_path: Path) -> None:
    first_line = json.dumps(make_answerable_payload()).encode()
    path = tmp_path / "development.jsonl"
    path.write_bytes(first_line + b"\n\xff\n")

    with pytest.raises(
        EvaluationDatasetError,
        match=r"invalid UTF-8.*development\.jsonl:2",
    ):
        load_phase5_development_dataset(path)


@pytest.mark.parametrize("content", [b"", b"\n  \r\n"])
def test_loader_rejects_an_empty_or_blank_only_dataset(
    tmp_path: Path,
    content: bytes,
) -> None:
    path = tmp_path / "development.jsonl"
    path.write_bytes(content)

    with pytest.raises(EvaluationDatasetError, match="development dataset is empty"):
        load_phase5_development_dataset(path)


def test_loader_wraps_missing_file_errors(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"

    with pytest.raises(EvaluationDatasetError, match="unable to read Phase 5"):
        load_phase5_development_dataset(path)


def test_dataset_revalidates_nested_unchecked_model_copies() -> None:
    example = Phase5DevelopmentExample.model_validate(make_answerable_payload())
    invalid_claim = example.gold_claims[0].model_copy(update={"support_sets": ()})
    invalid_example = example.model_copy(update={"gold_claims": (invalid_claim,)})

    with pytest.raises(ValidationError, match="at least 1 item"):
        Phase5DevelopmentDataset(
            dataset_sha256="a" * 64,
            corpus_hash_policy="canonical-chunk-identity-json-v1",
            corpus_sha256=CORPUS_SHA256,
            examples=(invalid_example,),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "phase5-development-dataset-v2"),
        ("dataset_role", "held_out"),
        ("dataset_hash_policy", "canonical-record-json-v1"),
        ("corpus_hash_policy", "sorted-content-only-v1"),
    ],
)
def test_dataset_rejects_unsupported_versions_and_roles(field: str, value: str) -> None:
    example = Phase5DevelopmentExample.model_validate(make_answerable_payload())
    payload: dict[str, Any] = {
        "dataset_sha256": "a" * 64,
        "corpus_hash_policy": "canonical-chunk-identity-json-v1",
        "corpus_sha256": CORPUS_SHA256,
        "examples": [example],
        field: value,
    }

    with pytest.raises(ValidationError):
        Phase5DevelopmentDataset.model_validate(payload)


def test_direct_dataset_construction_rejects_mixed_corpora() -> None:
    first = Phase5DevelopmentExample.model_validate(make_answerable_payload())
    second_payload = make_unanswerable_payload()
    second_payload["corpus_sha256"] = OTHER_CORPUS_SHA256
    second = Phase5DevelopmentExample.model_validate(second_payload)

    with pytest.raises(ValidationError, match="share the dataset corpus SHA-256"):
        Phase5DevelopmentDataset(
            dataset_sha256="a" * 64,
            corpus_hash_policy="canonical-chunk-identity-json-v1",
            corpus_sha256=CORPUS_SHA256,
            examples=(first, second),
        )


def test_provenance_models_reject_non_human_or_unaccepted_values() -> None:
    with pytest.raises(ValidationError):
        AnnotationProvenance(
            method="automatic",  # type: ignore[arg-type]
            annotator_ids=("annotator_001",),
            guideline_version="guidelines-v1",
            batch_id="batch-001",
            annotated_at=datetime(2026, 7, 23, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValidationError):
        AdjudicationProvenance(
            status="pending",  # type: ignore[arg-type]
            adjudicator_ids=("adjudicator_001",),
            guideline_version="guidelines-v1",
            batch_id="batch-001",
            adjudicated_at=datetime(2026, 7, 23, 13, 0, tzinfo=UTC),
        )
