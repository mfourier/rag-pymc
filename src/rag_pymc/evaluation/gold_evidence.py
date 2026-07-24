"""Gold-backed context coverage and abstention evaluation for Phase 5 development data."""

import json
from collections.abc import Sequence
from hashlib import sha256

from rag_pymc.domain import ConstructedContext, EvidenceAssessment
from rag_pymc.evaluation.errors import EvaluationError
from rag_pymc.evaluation.models import (
    AggregateGoldEvidenceMetrics,
    AtomicGoldClaim,
    GoldClaimCoverage,
    GoldEvidenceCaseEvaluation,
    GoldEvidenceEvaluationReport,
    Phase5DevelopmentDataset,
    Phase5DevelopmentExample,
)


def evaluate_gold_evidence(
    example: Phase5DevelopmentExample,
    context: ConstructedContext,
    assessment: EvidenceAssessment,
    *,
    corpus_sha256: str,
) -> GoldEvidenceCaseEvaluation:
    """Measure gold support coverage and score one evidence-policy decision.

    Coverage is syntactic over adjudicated chunk identities. It does not establish that a
    generated claim is correct or that cited prose semantically supports that claim.
    """
    example = Phase5DevelopmentExample.model_validate(example)
    context = ConstructedContext.model_validate(context)
    assessment = EvidenceAssessment.model_validate(assessment)
    _validate_runtime_binding(
        example,
        context,
        assessment,
        corpus_sha256=corpus_sha256,
    )

    context_chunk_ids = set(context.included_chunk_ids)
    candidate_chunk_ids = context_chunk_ids | set(context.omitted_chunk_ids)
    claim_coverage = tuple(
        _evaluate_claim_coverage(
            claim,
            context_chunk_ids=context_chunk_ids,
            candidate_chunk_ids=candidate_chunk_ids,
        )
        for claim in sorted(example.gold_claims, key=lambda item: item.claim_id)
    )
    context_covered_claim_count = sum(item.covered_by_context for item in claim_coverage)
    candidate_covered_claim_count = sum(item.covered_by_candidates for item in claim_coverage)
    gold_claim_count = len(claim_coverage)
    gold_context_answerable = (
        example.corpus_answerable and context_covered_claim_count == gold_claim_count
    )
    gold_candidate_answerable = (
        example.corpus_answerable and candidate_covered_claim_count == gold_claim_count
    )
    unsupported_answer_authorized = not assessment.should_abstain and not gold_context_answerable
    unnecessary_abstention = assessment.should_abstain and gold_context_answerable

    return GoldEvidenceCaseEvaluation(
        query_id=example.query_id,
        corpus_hash_policy=example.corpus_hash_policy,
        corpus_sha256=example.corpus_sha256,
        context_sha256=_hash_context(context),
        policy_version=assessment.policy_version,
        sufficiency=assessment.sufficiency,
        assessment_reason_codes=assessment.reason_codes,
        context_chunk_ids=context.included_chunk_ids,
        omitted_chunk_ids=context.omitted_chunk_ids,
        corpus_answerable=example.corpus_answerable,
        gold_claim_count=gold_claim_count,
        context_covered_claim_count=context_covered_claim_count,
        candidate_covered_claim_count=candidate_covered_claim_count,
        context_claim_coverage_rate=(
            None if gold_claim_count == 0 else context_covered_claim_count / gold_claim_count
        ),
        candidate_claim_coverage_rate=(
            None if gold_claim_count == 0 else candidate_covered_claim_count / gold_claim_count
        ),
        gold_context_answerable=gold_context_answerable,
        gold_candidate_answerable=gold_candidate_answerable,
        should_abstain=assessment.should_abstain,
        decision_correct=(assessment.should_abstain is (not gold_context_answerable)),
        unsupported_answer_authorized=unsupported_answer_authorized,
        unnecessary_abstention=unnecessary_abstention,
        budget_prevented_answerability=(gold_candidate_answerable and not gold_context_answerable),
        claim_coverage=claim_coverage,
    )


def aggregate_gold_evidence(
    dataset: Phase5DevelopmentDataset,
    evaluations: Sequence[GoldEvidenceCaseEvaluation],
) -> GoldEvidenceEvaluationReport:
    """Aggregate exactly one evaluation for every example in a development dataset."""
    dataset = Phase5DevelopmentDataset.model_validate(dataset)
    validated = tuple(GoldEvidenceCaseEvaluation.model_validate(item) for item in evaluations)
    ordered = tuple(sorted(validated, key=lambda item: item.query_id))
    observed_ids = tuple(item.query_id for item in ordered)
    if len(set(observed_ids)) != len(observed_ids):
        msg = "cannot aggregate duplicate gold evidence query IDs"
        raise EvaluationError(msg)

    expected_ids = {example.query_id for example in dataset.examples}
    observed_id_set = set(observed_ids)
    if observed_id_set != expected_ids:
        missing_ids = tuple(sorted(expected_ids - observed_id_set))
        unexpected_ids = tuple(sorted(observed_id_set - expected_ids))
        msg = (
            "gold evidence evaluations must exactly cover the development dataset; "
            f"missing={missing_ids}, unexpected={unexpected_ids}"
        )
        raise EvaluationError(msg)
    if any(item.corpus_sha256 != dataset.corpus_sha256 for item in ordered):
        msg = "gold evidence evaluation corpus does not match the development dataset"
        raise EvaluationError(msg)

    examples_by_id = {example.query_id: example for example in dataset.examples}
    for item in ordered:
        example = examples_by_id[item.query_id]
        expected_claim_coverage = tuple(
            _evaluate_claim_coverage(
                claim,
                context_chunk_ids=set(item.context_chunk_ids),
                candidate_chunk_ids=set(item.context_chunk_ids) | set(item.omitted_chunk_ids),
            )
            for claim in sorted(example.gold_claims, key=lambda claim: claim.claim_id)
        )
        if (
            item.corpus_answerable is not example.corpus_answerable
            or item.claim_coverage != expected_claim_coverage
        ):
            msg = (
                f"gold evidence evaluation for {item.query_id} does not match its "
                "development annotation"
            )
            raise EvaluationError(msg)

    policy_versions = {item.policy_version for item in ordered}
    if len(policy_versions) != 1:
        msg = "gold evidence aggregation requires one evidence policy version"
        raise EvaluationError(msg)
    policy_version = next(iter(policy_versions))
    return GoldEvidenceEvaluationReport(
        dataset_sha256=dataset.dataset_sha256,
        corpus_hash_policy=dataset.corpus_hash_policy,
        corpus_sha256=dataset.corpus_sha256,
        policy_version=policy_version,
        evaluations=ordered,
        metrics=AggregateGoldEvidenceMetrics.from_evaluations(ordered),
    )


def _evaluate_claim_coverage(
    claim: AtomicGoldClaim,
    *,
    context_chunk_ids: set[str],
    candidate_chunk_ids: set[str],
) -> GoldClaimCoverage:
    validated_claim = AtomicGoldClaim.model_validate(claim)
    matched_context = tuple(
        support_set
        for support_set in validated_claim.support_sets
        if set(support_set.chunk_ids).issubset(context_chunk_ids)
    )
    matched_candidates = tuple(
        support_set
        for support_set in validated_claim.support_sets
        if set(support_set.chunk_ids).issubset(candidate_chunk_ids)
    )
    return GoldClaimCoverage(
        claim_id=validated_claim.claim_id,
        matched_context_support_sets=matched_context,
        matched_candidate_support_sets=matched_candidates,
        covered_by_context=bool(matched_context),
        covered_by_candidates=bool(matched_candidates),
    )


def _validate_runtime_binding(
    example: Phase5DevelopmentExample,
    context: ConstructedContext,
    assessment: EvidenceAssessment,
    *,
    corpus_sha256: str,
) -> None:
    if corpus_sha256 != example.corpus_sha256:
        msg = "runtime corpus SHA-256 does not match the Phase 5 annotation"
        raise EvaluationError(msg)
    if context.query.text != example.query_text:
        msg = "constructed-context query text does not match the Phase 5 annotation"
        raise EvaluationError(msg)
    if (
        context.query.library is None
        or context.query.library.casefold() != example.library.casefold()
    ):
        msg = "constructed-context library does not match the Phase 5 annotation"
        raise EvaluationError(msg)
    if context.query.library_version != example.library_version:
        msg = "constructed-context library version does not match the Phase 5 annotation"
        raise EvaluationError(msg)
    if any(
        item.library.casefold() != example.library.casefold()
        or item.library_version != example.library_version
        for item in context.items
    ):
        msg = "constructed-context items do not match the Phase 5 library and version"
        raise EvaluationError(msg)
    if assessment.context_chunk_ids != context.included_chunk_ids:
        msg = "evidence assessment context IDs do not match the constructed context"
        raise EvaluationError(msg)
    if assessment.omitted_chunk_ids != context.omitted_chunk_ids:
        msg = "evidence assessment omitted IDs do not match the constructed context"
        raise EvaluationError(msg)


def _hash_context(context: ConstructedContext) -> str:
    canonical_json = json.dumps(
        context.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_json.encode("ascii")).hexdigest()
