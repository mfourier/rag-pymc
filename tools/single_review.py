"""Strict single-human review workflow for the Phase 5 development candidate batch."""

import json
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ValidationError

from rag_pymc.domain import Chunk
from rag_pymc.evaluation.errors import EvaluationDatasetError
from rag_pymc.serialization import canonical_json_bytes
from tools.candidate_review import (
    REVIEW_GOVERNANCE_ID,
    REVIEW_GOVERNANCE_SHA256,
    SINGLE_REVIEWER_ID,
    validate_phase5_candidate_batch_v1,
    validate_phase5_candidate_corpus,
)
from tools.development_models import (
    AtomicGoldClaim,
    Phase5DevelopmentCandidate,
    Phase5DevelopmentCandidateBatch,
    Phase5SingleReviewCandidateSha256,
    Phase5SingleReviewCorpusSha256,
    Phase5SingleReviewDataset,
    Phase5SingleReviewDecision,
    Phase5SingleReviewDecisionBatch,
    Phase5SingleReviewExample,
    Phase5SingleReviewProvenance,
    Phase5SingleReviewRevisedContent,
    Phase5SingleReviewValidation,
)

_DATASET_ROLE = "development-single-review-exploratory"
_AcceptedOutcome = Literal["accepted-as-proposed", "accepted-with-revisions"]
_LIMITATIONS = tuple(
    sorted(
        (
            "Accepted labels, claims, and support sets were reviewed by one human and were not "
            "independently adjudicated.",
            "Chunk-identity validation does not establish semantic support or scientific "
            "correctness.",
            "Rejected and unresolved candidates are excluded from the dataset and remain visible "
            "only as counts and query IDs in this report.",
            "The dataset is exploratory development evidence, not a held-out or production-grade "
            "evaluation set.",
            "This workflow does not select or authorize an evidence-sufficiency threshold.",
        )
    )
)


def render_phase5_single_review_decision_template(
    batch: Phase5DevelopmentCandidateBatch,
) -> bytes:
    """Render pending-only records that cannot be mistaken for completed human review."""
    batch = Phase5DevelopmentCandidateBatch.model_validate(batch)
    validate_phase5_candidate_batch_v1(batch)
    decisions = tuple(
        Phase5SingleReviewDecision(
            governance_id="phase5-development-single-review-governance-v1",
            governance_sha256=("a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264"),
            candidate_batch_id=batch.batch_id,
            candidate_batch_sha256=cast(
                Phase5SingleReviewCandidateSha256,
                batch.dataset_sha256,
            ),
            corpus_hash_policy=batch.corpus_hash_policy,
            corpus_sha256=cast(Phase5SingleReviewCorpusSha256, batch.corpus_sha256),
            reviewer_id="sr_001",
            query_id=candidate.query_id,
            query_review="pending",
            corpus_answerability_review="pending",
            claims_review="pending",
            support_sets_review="pending",
            leakage_review="pending",
            hard_negative_review="pending",
            final_status="pending",
        )
        for candidate in sorted(batch.candidates, key=lambda item: item.query_id)
    )
    return _render_jsonl(decisions)


def write_phase5_single_review_decision_template(
    batch: Phase5DevelopmentCandidateBatch,
    path: Path,
) -> None:
    """Write a deterministic pending form without adding labels or timestamps."""
    raw_bytes = render_phase5_single_review_decision_template(batch)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw_bytes)
    except OSError as error:
        msg = f"unable to write Phase 5 single-review decision template: {path}"
        raise EvaluationDatasetError(msg) from error


def load_phase5_single_review_decisions(path: Path) -> Phase5SingleReviewDecisionBatch:
    """Load strict pending or completed single-review records and hash exact bytes."""
    raw_bytes = _read_bytes(path, label="Phase 5 single-review decisions")
    decisions = _load_jsonl_models(
        raw_bytes,
        path,
        Phase5SingleReviewDecision,
        item_label="Phase 5 single-review decision",
    )
    if not decisions:
        msg = f"Phase 5 single-review decision file is empty: {path}"
        raise EvaluationDatasetError(msg)
    first = decisions[0]
    try:
        return Phase5SingleReviewDecisionBatch(
            decisions_sha256=sha256(raw_bytes).hexdigest(),
            governance_id=first.governance_id,
            governance_sha256=first.governance_sha256,
            candidate_batch_id=first.candidate_batch_id,
            candidate_batch_sha256=first.candidate_batch_sha256,
            corpus_hash_policy=first.corpus_hash_policy,
            corpus_sha256=first.corpus_sha256,
            reviewer_id=first.reviewer_id,
            decisions=tuple(decisions),
        )
    except ValidationError as error:
        msg = f"invalid Phase 5 single-review decision batch: {path}"
        raise EvaluationDatasetError(msg) from error


def build_phase5_single_review_dataset(
    candidate_batch: Phase5DevelopmentCandidateBatch,
    decision_batch: Phase5SingleReviewDecisionBatch,
    chunks: Sequence[Chunk],
) -> tuple[Phase5SingleReviewDataset, Phase5SingleReviewValidation, bytes]:
    """Compile explicit completed decisions into an accepted-only exploratory dataset."""
    candidate_batch = Phase5DevelopmentCandidateBatch.model_validate(candidate_batch)
    decision_batch = Phase5SingleReviewDecisionBatch.model_validate(decision_batch)
    validate_phase5_candidate_batch_v1(candidate_batch)
    validated_chunks = validate_phase5_candidate_corpus(candidate_batch, chunks)
    _validate_review_batch_binding(candidate_batch, decision_batch)

    candidates_by_id = {candidate.query_id: candidate for candidate in candidate_batch.candidates}
    accepted_examples: list[Phase5SingleReviewExample] = []
    for decision in decision_batch.decisions:
        if decision.final_status == "pending":
            msg = f"Phase 5 single-review decision remains pending for {decision.query_id}"
            raise EvaluationDatasetError(msg)
        candidate = candidates_by_id[decision.query_id]
        if decision.final_status in {"accepted-as-proposed", "accepted-with-revisions"}:
            accepted_examples.append(
                _build_accepted_example(candidate, decision, decision_batch.decisions_sha256)
            )

    if not accepted_examples:
        msg = "cannot create a Phase 5 single-review dataset without an accepted example"
        raise EvaluationDatasetError(msg)

    ordered_examples = tuple(sorted(accepted_examples, key=lambda item: item.query_id))
    dataset_bytes = _render_jsonl(ordered_examples)
    dataset = Phase5SingleReviewDataset(
        dataset_sha256=sha256(dataset_bytes).hexdigest(),
        decisions_sha256=decision_batch.decisions_sha256,
        governance_id=decision_batch.governance_id,
        governance_sha256=decision_batch.governance_sha256,
        candidate_batch_id=decision_batch.candidate_batch_id,
        candidate_batch_sha256=decision_batch.candidate_batch_sha256,
        corpus_hash_policy=decision_batch.corpus_hash_policy,
        corpus_sha256=decision_batch.corpus_sha256,
        reviewer_id=decision_batch.reviewer_id,
        examples=ordered_examples,
    )
    _validate_single_review_corpus(dataset, validated_chunks)
    report = _build_validation_report(candidate_batch, decision_batch, dataset, validated_chunks)
    return dataset, report, dataset_bytes


def load_phase5_single_review_dataset(path: Path) -> Phase5SingleReviewDataset:
    """Load an accepted-only single-review JSONL and bind its exact raw bytes."""
    raw_bytes = _read_bytes(path, label="Phase 5 single-review dataset")
    examples = _load_jsonl_models(
        raw_bytes,
        path,
        Phase5SingleReviewExample,
        item_label="Phase 5 single-review example",
    )
    if not examples:
        msg = f"Phase 5 single-review dataset is empty: {path}"
        raise EvaluationDatasetError(msg)
    first = examples[0]
    try:
        return Phase5SingleReviewDataset(
            dataset_sha256=sha256(raw_bytes).hexdigest(),
            decisions_sha256=first.review.decisions_sha256,
            governance_id=first.review.governance_id,
            governance_sha256=first.review.governance_sha256,
            candidate_batch_id=first.review.candidate_batch_id,
            candidate_batch_sha256=first.review.candidate_batch_sha256,
            corpus_hash_policy=first.corpus_hash_policy,
            corpus_sha256=first.corpus_sha256,
            reviewer_id=first.review.reviewer_id,
            examples=tuple(examples),
        )
    except ValidationError as error:
        msg = f"invalid Phase 5 single-review dataset: {path}"
        raise EvaluationDatasetError(msg) from error


def validate_phase5_single_review_dataset(
    dataset: Phase5SingleReviewDataset,
    candidate_batch: Phase5DevelopmentCandidateBatch,
    decision_batch: Phase5SingleReviewDecisionBatch,
    chunks: Sequence[Chunk],
) -> Phase5SingleReviewValidation:
    """Rebuild and compare a persisted single-review dataset and validation report."""
    dataset = Phase5SingleReviewDataset.model_validate(dataset)
    rebuilt, report, _ = build_phase5_single_review_dataset(
        candidate_batch,
        decision_batch,
        chunks,
    )
    if dataset != rebuilt:
        msg = "persisted Phase 5 single-review dataset does not match its human decisions"
        raise EvaluationDatasetError(msg)
    return report


def write_phase5_single_review_outputs(
    dataset_bytes: bytes,
    report: Phase5SingleReviewValidation,
    *,
    dataset_path: Path,
    report_path: Path,
) -> None:
    """Write validated dataset and report only after compilation succeeds completely."""
    if dataset_path.resolve() == report_path.resolve():
        msg = "Phase 5 single-review dataset and report paths must differ"
        raise EvaluationDatasetError(msg)
    validated_report = Phase5SingleReviewValidation.model_validate(report)
    if sha256(dataset_bytes).hexdigest() != validated_report.dataset_sha256:
        msg = "Phase 5 single-review dataset bytes do not match the validation report"
        raise EvaluationDatasetError(msg)
    try:
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        dataset_path.write_bytes(dataset_bytes)
        report_path.write_text(f"{validated_report.model_dump_json(indent=2)}\n", encoding="utf-8")
    except OSError as error:
        msg = "unable to write Phase 5 single-review dataset outputs"
        raise EvaluationDatasetError(msg) from error


def _validate_review_batch_binding(
    candidate_batch: Phase5DevelopmentCandidateBatch,
    decision_batch: Phase5SingleReviewDecisionBatch,
) -> None:
    expected = (
        _DATASET_ROLE,
        REVIEW_GOVERNANCE_ID,
        REVIEW_GOVERNANCE_SHA256,
        candidate_batch.batch_id,
        candidate_batch.dataset_sha256,
        candidate_batch.corpus_hash_policy,
        candidate_batch.corpus_sha256,
        SINGLE_REVIEWER_ID,
    )
    observed = (
        decision_batch.dataset_role,
        decision_batch.governance_id,
        decision_batch.governance_sha256,
        decision_batch.candidate_batch_id,
        decision_batch.candidate_batch_sha256,
        decision_batch.corpus_hash_policy,
        decision_batch.corpus_sha256,
        decision_batch.reviewer_id,
    )
    if observed != expected:
        msg = "Phase 5 single-review decisions do not match the governed candidate batch"
        raise EvaluationDatasetError(msg)

    expected_ids = {candidate.query_id for candidate in candidate_batch.candidates}
    observed_ids = {decision.query_id for decision in decision_batch.decisions}
    if observed_ids != expected_ids:
        missing = tuple(sorted(expected_ids - observed_ids))
        unexpected = tuple(sorted(observed_ids - expected_ids))
        msg = (
            "Phase 5 single-review decisions must exactly cover the candidate batch; "
            f"missing={missing}, unexpected={unexpected}"
        )
        raise EvaluationDatasetError(msg)


def _build_accepted_example(
    candidate: Phase5DevelopmentCandidate,
    decision: Phase5SingleReviewDecision,
    decisions_sha256: str,
) -> Phase5SingleReviewExample:
    proposed = _candidate_content(candidate)
    if decision.final_status == "accepted-as-proposed":
        content = proposed
    else:
        assert decision.revised_content is not None
        content = decision.revised_content
        _validate_declared_revisions(candidate, decision, proposed, content)

    expected_hard_negative_review = _expected_hard_negative_review(candidate, content)
    if decision.hard_negative_review != expected_hard_negative_review:
        msg = (
            f"Phase 5 single-review hard-negative decision is inconsistent for {candidate.query_id}"
        )
        raise EvaluationDatasetError(msg)

    assert decision.reviewed_at is not None
    outcome = cast(_AcceptedOutcome, decision.final_status)

    return Phase5SingleReviewExample(
        slot_id=candidate.slot_id,
        query_id=candidate.query_id,
        query_text=content.query_text,
        query_family=candidate.query_family,
        template_family=candidate.template_family,
        library=candidate.library,
        library_version=candidate.library_version,
        corpus_hash_policy=candidate.corpus_hash_policy,
        corpus_sha256=cast(Phase5SingleReviewCorpusSha256, candidate.corpus_sha256),
        corpus_answerable=content.corpus_answerable,
        intent=candidate.intent,
        difficulty=candidate.difficulty,
        hard_negative_category=content.hard_negative_category,
        expected_api_symbols=candidate.expected_api_symbols,
        gold_claims=content.gold_claims,
        review=Phase5SingleReviewProvenance(
            outcome=outcome,
            governance_id=decision.governance_id,
            governance_sha256=decision.governance_sha256,
            candidate_batch_id=decision.candidate_batch_id,
            candidate_batch_sha256=decision.candidate_batch_sha256,
            decisions_sha256=decisions_sha256,
            reviewer_id=decision.reviewer_id,
            reviewed_at=decision.reviewed_at,
        ),
    )


def _candidate_content(candidate: Phase5DevelopmentCandidate) -> Phase5SingleReviewRevisedContent:
    return Phase5SingleReviewRevisedContent(
        query_text=candidate.query_text,
        corpus_answerable=candidate.proposed_corpus_answerable,
        hard_negative_category=candidate.hard_negative_category,
        gold_claims=candidate.proposed_gold_claims,
    )


def _validate_declared_revisions(
    candidate: Phase5DevelopmentCandidate,
    decision: Phase5SingleReviewDecision,
    proposed: Phase5SingleReviewRevisedContent,
    reviewed: Phase5SingleReviewRevisedContent,
) -> None:
    expected_reviews = (
        "accepted" if reviewed.query_text == proposed.query_text else "revised",
        "accepted"
        if (
            reviewed.corpus_answerable,
            reviewed.hard_negative_category,
        )
        == (
            proposed.corpus_answerable,
            proposed.hard_negative_category,
        )
        else "revised",
        "accepted"
        if _claim_text_projection(reviewed.gold_claims)
        == _claim_text_projection(proposed.gold_claims)
        else "revised",
        "accepted"
        if _support_projection(reviewed.gold_claims) == _support_projection(proposed.gold_claims)
        else "revised",
    )
    declared_reviews = (
        decision.query_review,
        decision.corpus_answerability_review,
        decision.claims_review,
        decision.support_sets_review,
    )
    if declared_reviews != expected_reviews:
        msg = (
            "Phase 5 single-review declared revisions do not match content for "
            f"{candidate.query_id}"
        )
        raise EvaluationDatasetError(msg)


def _expected_hard_negative_review(
    candidate: Phase5DevelopmentCandidate,
    content: Phase5SingleReviewRevisedContent,
) -> str:
    if content.corpus_answerable:
        return "not-applicable"
    if (
        not candidate.proposed_corpus_answerable
        and content.hard_negative_category == candidate.hard_negative_category
    ):
        return "confirmed"
    return "revised"


def _claim_text_projection(claims: Sequence[AtomicGoldClaim]) -> tuple[tuple[str, str], ...]:
    return tuple((claim.claim_id, claim.text) for claim in claims)


def _support_projection(
    claims: Sequence[AtomicGoldClaim],
) -> tuple[tuple[str, tuple[tuple[str, ...], ...]], ...]:
    return tuple(
        (claim.claim_id, tuple(support_set.chunk_ids for support_set in claim.support_sets))
        for claim in claims
    )


def _validate_single_review_corpus(
    dataset: Phase5SingleReviewDataset,
    chunks: Sequence[Chunk],
) -> None:
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for example in dataset.examples:
        for claim in example.gold_claims:
            for support_set in claim.support_sets:
                for chunk_id in support_set.chunk_ids:
                    chunk = chunks_by_id.get(chunk_id)
                    if chunk is None:
                        msg = (
                            f"Phase 5 single-review claim {claim.claim_id} references missing "
                            f"chunk {chunk_id}"
                        )
                        raise EvaluationDatasetError(msg)
                    if (
                        chunk.library.casefold() != example.library.casefold()
                        or chunk.library_version != example.library_version
                    ):
                        msg = (
                            f"Phase 5 single-review claim {claim.claim_id} references chunk "
                            f"{chunk_id} from another library or version"
                        )
                        raise EvaluationDatasetError(msg)


def _build_validation_report(
    candidate_batch: Phase5DevelopmentCandidateBatch,
    decision_batch: Phase5SingleReviewDecisionBatch,
    dataset: Phase5SingleReviewDataset,
    chunks: Sequence[Chunk],
) -> Phase5SingleReviewValidation:
    by_status = {
        status: tuple(
            sorted(
                decision.query_id
                for decision in decision_batch.decisions
                if decision.final_status == status
            )
        )
        for status in (
            "accepted-as-proposed",
            "accepted-with-revisions",
            "rejected",
            "unresolved",
        )
    }
    referenced_chunk_ids = tuple(
        sorted(
            {
                chunk_id
                for example in dataset.examples
                for claim in example.gold_claims
                for support_set in claim.support_sets
                for chunk_id in support_set.chunk_ids
            }
        )
    )
    return Phase5SingleReviewValidation(
        governance_id=decision_batch.governance_id,
        governance_sha256=decision_batch.governance_sha256,
        candidate_batch_id=decision_batch.candidate_batch_id,
        candidate_batch_sha256=decision_batch.candidate_batch_sha256,
        decisions_sha256=decision_batch.decisions_sha256,
        dataset_sha256=dataset.dataset_sha256,
        corpus_hash_policy=dataset.corpus_hash_policy,
        corpus_sha256=dataset.corpus_sha256,
        corpus_chunk_count=len(chunks),
        reviewer_ids=(decision_batch.reviewer_id,),
        candidate_count=len(candidate_batch.candidates),
        decision_count=len(decision_batch.decisions),
        accepted_as_proposed_count=len(by_status["accepted-as-proposed"]),
        accepted_with_revisions_count=len(by_status["accepted-with-revisions"]),
        rejected_count=len(by_status["rejected"]),
        unresolved_count=len(by_status["unresolved"]),
        included_query_count=len(dataset.examples),
        answerable_query_count=sum(example.corpus_answerable for example in dataset.examples),
        gold_claim_count=sum(len(example.gold_claims) for example in dataset.examples),
        gold_support_set_count=sum(
            len(claim.support_sets) for example in dataset.examples for claim in example.gold_claims
        ),
        accepted_as_proposed_query_ids=by_status["accepted-as-proposed"],
        accepted_with_revisions_query_ids=by_status["accepted-with-revisions"],
        rejected_query_ids=by_status["rejected"],
        unresolved_query_ids=by_status["unresolved"],
        referenced_chunk_ids=referenced_chunk_ids,
        limitations=_LIMITATIONS,
    )


def _render_jsonl(models: Sequence[BaseModel]) -> bytes:
    return b"".join(canonical_json_bytes(model.model_dump(mode="json")) + b"\n" for model in models)


def _read_bytes(path: Path, *, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        msg = f"unable to read {label}: {path}"
        raise EvaluationDatasetError(msg) from error


def _load_jsonl_models[
    ModelT: (Phase5SingleReviewDecision, Phase5SingleReviewExample),
](
    raw_bytes: bytes,
    path: Path,
    model_type: type[ModelT],
    *,
    item_label: str,
) -> list[ModelT]:
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        line_number = raw_bytes[: error.start].count(b"\n") + 1
        msg = f"invalid UTF-8 in {item_label} file at {path}:{line_number}"
        raise EvaluationDatasetError(msg) from error

    models: list[ModelT] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(
                line,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_non_finite_json_number,
            )
            models.append(model_type.model_validate(payload))
        except (json.JSONDecodeError, RecursionError, ValidationError, ValueError) as error:
            msg = f"invalid {item_label} at {path}:{line_number}"
            raise EvaluationDatasetError(msg) from error
    return models


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_non_finite_json_number(_: str) -> None:
    raise ValueError("non-finite JSON number")
