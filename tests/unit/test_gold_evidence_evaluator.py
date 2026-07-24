from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal

import pytest
from pydantic import AnyUrl, ValidationError

from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    Difficulty,
    EvidenceAssessment,
    EvidenceSufficiency,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)
from rag_pymc.evaluation import (
    AdjudicationProvenance,
    AnnotationProvenance,
    AtomicGoldClaim,
    EvaluationError,
    GoldEvidenceEvaluationReport,
    GoldEvidenceSupportSet,
    Phase5DevelopmentDataset,
    Phase5DevelopmentExample,
    aggregate_gold_evidence,
    evaluate_gold_evidence,
)
from rag_pymc.retrieval import TechnicalTokenizer

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
CORPUS_SHA256 = "c" * 64
CORPUS_HASH_POLICY: Literal["canonical-chunk-identity-json-v1"] = "canonical-chunk-identity-json-v1"


def make_result(
    chunk_id: str,
    *,
    rank: int,
    library: str = "pymc",
    library_version: str = "6.1.0",
) -> RetrievedChunk:
    content = f"Complete evidence from {chunk_id}."
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=chunk_id,
            document_id=f"document_{chunk_id}",
            library=library,
            library_version=library_version,
            source_type=SourceType.API_REFERENCE,
            source_url=AnyUrl(f"https://docs.example.test/{chunk_id}.html"),
            title="Synthetic evidence",
            section="Details",
            content=content,
            content_hash=sha256(content.encode()).hexdigest(),
            api_symbols=("pymc.sample",),
            created_at=NOW,
        ),
        score=1.0 / rank,
        rank=rank,
        retriever="synthetic-retriever-v1",
    )


def make_context(
    candidate_ids: tuple[str, ...],
    *,
    included_count: int,
    query_text: str = "How do I perform the synthetic workflow?",
    library: str = "pymc",
    library_version: str = "6.1.0",
) -> ConstructedContext:
    query = SearchQuery(
        text=query_text,
        top_k=max(1, len(candidate_ids)),
        library=library,
        library_version=library_version,
    )
    results = tuple(
        make_result(
            chunk_id,
            rank=rank,
            library=library,
            library_version=library_version,
        )
        for rank, chunk_id in enumerate(candidate_ids, start=1)
    )
    builder = RankedContextBuilder(TechnicalTokenizer())
    if not results:
        return builder.build(query, results, token_budget=100)

    complete = builder.build(query, results, token_budget=100_000)
    if included_count == len(results):
        return complete
    if included_count == 0:
        token_budget = complete.items[0].token_count - 1
    else:
        token_budget = sum(item.token_count for item in complete.items[:included_count])
    context = builder.build(query, results, token_budget=token_budget)
    assert len(context.items) == included_count
    return context


def make_example(
    query_id: str = "dev_q_001",
    *,
    corpus_answerable: bool = True,
    query_text: str = "How do I perform the synthetic workflow?",
) -> Phase5DevelopmentExample:
    gold_claims = (
        (
            AtomicGoldClaim(
                claim_id=f"{query_id}_claim_001",
                text="The first synthetic claim.",
                support_sets=(
                    GoldEvidenceSupportSet(chunk_ids=("chunk_a",)),
                    GoldEvidenceSupportSet(chunk_ids=("chunk_b", "chunk_c")),
                ),
            ),
            AtomicGoldClaim(
                claim_id=f"{query_id}_claim_002",
                text="The second synthetic claim.",
                support_sets=(GoldEvidenceSupportSet(chunk_ids=("chunk_d",)),),
            ),
        )
        if corpus_answerable
        else ()
    )
    return Phase5DevelopmentExample(
        query_id=query_id,
        query_text=query_text,
        query_family="synthetic-workflow",
        template_family="synthetic-template",
        library="pymc",
        library_version="6.1.0",
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=CORPUS_SHA256,
        corpus_answerable=corpus_answerable,
        intent="synthetic_intent",
        difficulty=Difficulty.INTERMEDIATE,
        hard_negative_category=None if corpus_answerable else "synthetic-hard-negative",
        expected_api_symbols=("pymc.sample",),
        gold_claims=gold_claims,
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


def make_assessment(
    context: ConstructedContext,
    *,
    authorize_answer: bool,
    policy_version: str = "synthetic-policy-v1",
) -> EvidenceAssessment:
    if authorize_answer:
        sufficiency = EvidenceSufficiency.SUFFICIENT
    elif context.included_chunk_ids:
        sufficiency = EvidenceSufficiency.NOT_ASSESSED
    else:
        sufficiency = EvidenceSufficiency.INSUFFICIENT
    return EvidenceAssessment(
        policy_version=policy_version,
        sufficiency=sufficiency,
        should_abstain=not authorize_answer,
        reason_codes=("synthetic_policy_decision",),
        context_chunk_ids=context.included_chunk_ids,
        omitted_chunk_ids=context.omitted_chunk_ids,
    )


def test_evaluator_accepts_alternative_and_joint_minimal_support_sets() -> None:
    example = make_example()
    context = make_context(("chunk_b", "chunk_c", "chunk_d"), included_count=3)
    assessment = make_assessment(context, authorize_answer=True)

    first = evaluate_gold_evidence(
        example,
        context,
        assessment,
        corpus_sha256=CORPUS_SHA256,
    )
    second = evaluate_gold_evidence(
        example,
        context,
        assessment,
        corpus_sha256=CORPUS_SHA256,
    )
    restored = type(first).model_validate_json(first.model_dump_json())

    assert first == second
    assert restored == first
    assert first.context_sha256 == second.context_sha256
    assert first.gold_context_answerable is True
    assert first.gold_candidate_answerable is True
    assert first.context_covered_claim_count == 2
    assert first.context_claim_coverage_rate == 1.0
    assert first.decision_correct is True
    assert first.claim_coverage[0].matched_context_support_sets == (
        GoldEvidenceSupportSet(chunk_ids=("chunk_b", "chunk_c")),
    )


def test_evaluator_separates_budget_loss_from_retrieval_miss() -> None:
    example = make_example()
    budget_limited = make_context(("chunk_a", "chunk_d"), included_count=1)
    retrieval_miss = make_context(("chunk_a",), included_count=1)

    budget_result = evaluate_gold_evidence(
        example,
        budget_limited,
        make_assessment(budget_limited, authorize_answer=False),
        corpus_sha256=CORPUS_SHA256,
    )
    retrieval_result = evaluate_gold_evidence(
        example,
        retrieval_miss,
        make_assessment(retrieval_miss, authorize_answer=False),
        corpus_sha256=CORPUS_SHA256,
    )

    assert budget_result.context_claim_coverage_rate == 0.5
    assert budget_result.candidate_claim_coverage_rate == 1.0
    assert budget_result.gold_context_answerable is False
    assert budget_result.gold_candidate_answerable is True
    assert budget_result.budget_prevented_answerability is True
    assert budget_result.decision_correct is True

    assert retrieval_result.context_claim_coverage_rate == 0.5
    assert retrieval_result.candidate_claim_coverage_rate == 0.5
    assert retrieval_result.gold_candidate_answerable is False
    assert retrieval_result.budget_prevented_answerability is False


@pytest.mark.parametrize(
    ("candidate_ids", "included_count", "authorize_answer", "unsupported", "unnecessary"),
    [
        (("chunk_a",), 1, True, True, False),
        (("chunk_a", "chunk_d"), 2, False, False, True),
    ],
)
def test_evaluator_classifies_unsafe_answers_and_unnecessary_abstentions(
    candidate_ids: tuple[str, ...],
    included_count: int,
    authorize_answer: bool,
    unsupported: bool,
    unnecessary: bool,
) -> None:
    example = make_example()
    context = make_context(candidate_ids, included_count=included_count)
    result = evaluate_gold_evidence(
        example,
        context,
        make_assessment(context, authorize_answer=authorize_answer),
        corpus_sha256=CORPUS_SHA256,
    )

    assert result.decision_correct is False
    assert result.unsupported_answer_authorized is unsupported
    assert result.unnecessary_abstention is unnecessary


def test_corpus_unanswerable_example_has_no_claim_denominator() -> None:
    example = make_example(corpus_answerable=False)
    context = make_context(("irrelevant_chunk",), included_count=1)
    result = evaluate_gold_evidence(
        example,
        context,
        make_assessment(context, authorize_answer=False),
        corpus_sha256=CORPUS_SHA256,
    )

    assert result.gold_claim_count == 0
    assert result.context_claim_coverage_rate is None
    assert result.candidate_claim_coverage_rate is None
    assert result.gold_context_answerable is False
    assert result.gold_candidate_answerable is False
    assert result.decision_correct is True


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("corpus", "runtime corpus SHA-256"),
        ("query_text", "query text"),
        ("library", "library does not match"),
        ("library_version", "library version"),
        ("assessment_context", "assessment context IDs"),
        ("assessment_omitted", "assessment omitted IDs"),
    ],
)
def test_evaluator_rejects_unbound_runtime_artifacts(mutation: str, match: str) -> None:
    example = make_example()
    context = make_context(("chunk_a", "chunk_d"), included_count=1)
    assessment = make_assessment(context, authorize_answer=False)
    corpus_sha256 = CORPUS_SHA256
    if mutation == "corpus":
        corpus_sha256 = "d" * 64
    elif mutation == "query_text":
        context = make_context(
            ("chunk_a", "chunk_d"),
            included_count=1,
            query_text="A different query",
        )
        assessment = make_assessment(context, authorize_answer=False)
    elif mutation == "library":
        context = make_context(
            ("chunk_a", "chunk_d"),
            included_count=1,
            library="pytensor",
        )
        assessment = make_assessment(context, authorize_answer=False)
    elif mutation == "library_version":
        context = make_context(
            ("chunk_a", "chunk_d"),
            included_count=1,
            library_version="6.2.0",
        )
        assessment = make_assessment(context, authorize_answer=False)
    elif mutation == "assessment_context":
        assessment = assessment.model_copy(update={"context_chunk_ids": ("different",)})
    else:
        assessment = assessment.model_copy(update={"omitted_chunk_ids": ("different",)})

    with pytest.raises(EvaluationError, match=match):
        evaluate_gold_evidence(
            example,
            context,
            assessment,
            corpus_sha256=corpus_sha256,
        )


def test_aggregate_reports_explicit_selective_and_coverage_denominators() -> None:
    full_example = make_example("dev_q_001")
    partial_example = make_example("dev_q_002")
    negative_example = make_example("dev_q_003", corpus_answerable=False)
    dataset = Phase5DevelopmentDataset(
        dataset_sha256="a" * 64,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=CORPUS_SHA256,
        examples=(full_example, partial_example, negative_example),
    )

    full_context = make_context(("chunk_a", "chunk_d"), included_count=2)
    partial_context = make_context(("chunk_a", "chunk_d"), included_count=1)
    negative_context = make_context(("irrelevant_chunk",), included_count=1)
    evaluations = (
        evaluate_gold_evidence(
            partial_example,
            partial_context,
            make_assessment(partial_context, authorize_answer=True),
            corpus_sha256=CORPUS_SHA256,
        ),
        evaluate_gold_evidence(
            negative_example,
            negative_context,
            make_assessment(negative_context, authorize_answer=False),
            corpus_sha256=CORPUS_SHA256,
        ),
        evaluate_gold_evidence(
            full_example,
            full_context,
            make_assessment(full_context, authorize_answer=False),
            corpus_sha256=CORPUS_SHA256,
        ),
    )

    report = aggregate_gold_evidence(dataset, evaluations)
    restored = GoldEvidenceEvaluationReport.model_validate_json(report.model_dump_json())

    assert restored == report
    assert tuple(item.query_id for item in report.evaluations) == (
        "dev_q_001",
        "dev_q_002",
        "dev_q_003",
    )
    assert report.metrics.query_count == 3
    assert report.metrics.corpus_answerable_query_count == 2
    assert report.metrics.corpus_unanswerable_query_count == 1
    assert report.metrics.gold_context_answerable_query_count == 1
    assert report.metrics.gold_candidate_answerable_query_count == 2
    assert report.metrics.authorized_answer_count == 1
    assert report.metrics.correct_decision_count == 1
    assert report.metrics.unsupported_answer_count == 1
    assert report.metrics.unnecessary_abstention_count == 1
    assert report.metrics.budget_prevented_answerability_count == 1
    assert report.metrics.answer_coverage == pytest.approx(1 / 3)
    assert report.metrics.selective_risk == 1.0
    assert report.metrics.false_answer_rate == 0.5
    assert report.metrics.false_abstention_rate == 1.0
    assert report.metrics.decision_accuracy == pytest.approx(1 / 3)
    assert report.metrics.context_claim_coverage_rate == 0.75
    assert report.metrics.candidate_claim_coverage_rate == 1.0


def test_aggregate_preserves_undefined_zero_denominator_rates() -> None:
    example = make_example("dev_q_001", corpus_answerable=False)
    dataset = Phase5DevelopmentDataset(
        dataset_sha256="a" * 64,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=CORPUS_SHA256,
        examples=(example,),
    )
    context = make_context((), included_count=0)
    evaluation = evaluate_gold_evidence(
        example,
        context,
        make_assessment(context, authorize_answer=False),
        corpus_sha256=CORPUS_SHA256,
    )

    metrics = aggregate_gold_evidence(dataset, (evaluation,)).metrics

    assert metrics.answer_coverage == 0.0
    assert metrics.selective_risk is None
    assert metrics.false_answer_rate == 0.0
    assert metrics.false_abstention_rate is None
    assert metrics.context_claim_coverage_rate is None
    assert metrics.candidate_claim_coverage_rate is None


def test_aggregate_rejects_incomplete_duplicate_or_mixed_policy_results() -> None:
    first_example = make_example("dev_q_001")
    second_example = make_example("dev_q_002")
    dataset = Phase5DevelopmentDataset(
        dataset_sha256="a" * 64,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=CORPUS_SHA256,
        examples=(first_example, second_example),
    )
    context = make_context(("chunk_a", "chunk_d"), included_count=2)
    first = evaluate_gold_evidence(
        first_example,
        context,
        make_assessment(context, authorize_answer=True),
        corpus_sha256=CORPUS_SHA256,
    )
    second = evaluate_gold_evidence(
        second_example,
        context,
        make_assessment(
            context,
            authorize_answer=True,
            policy_version="another-policy-v1",
        ),
        corpus_sha256=CORPUS_SHA256,
    )

    with pytest.raises(EvaluationError, match="exactly cover"):
        aggregate_gold_evidence(dataset, (first,))
    with pytest.raises(EvaluationError, match="duplicate"):
        aggregate_gold_evidence(dataset, (first, first))
    with pytest.raises(EvaluationError, match="one evidence policy"):
        aggregate_gold_evidence(dataset, (first, second))


def test_aggregate_recomputes_claim_coverage_from_the_bound_annotation() -> None:
    answerable_example = make_example("dev_q_001")
    negative_example = make_example("dev_q_002", corpus_answerable=False)
    dataset = Phase5DevelopmentDataset(
        dataset_sha256="a" * 64,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=CORPUS_SHA256,
        examples=(answerable_example, negative_example),
    )
    answerable_context = make_context(("chunk_a", "chunk_d"), included_count=2)
    negative_context = make_context(("irrelevant_chunk",), included_count=1)
    answerable_result = evaluate_gold_evidence(
        answerable_example,
        answerable_context,
        make_assessment(answerable_context, authorize_answer=True),
        corpus_sha256=CORPUS_SHA256,
    )
    negative_result = evaluate_gold_evidence(
        negative_example,
        negative_context,
        make_assessment(negative_context, authorize_answer=False),
        corpus_sha256=CORPUS_SHA256,
    )
    swapped_results = (
        answerable_result.model_copy(update={"query_id": "dev_q_002"}),
        negative_result.model_copy(update={"query_id": "dev_q_001"}),
    )

    with pytest.raises(EvaluationError, match="does not match its development annotation"):
        aggregate_gold_evidence(dataset, swapped_results)


def test_report_revalidates_nested_derived_metrics() -> None:
    example = make_example("dev_q_001")
    dataset = Phase5DevelopmentDataset(
        dataset_sha256="a" * 64,
        corpus_hash_policy=CORPUS_HASH_POLICY,
        corpus_sha256=CORPUS_SHA256,
        examples=(example,),
    )
    context = make_context(("chunk_a", "chunk_d"), included_count=2)
    evaluation = evaluate_gold_evidence(
        example,
        context,
        make_assessment(context, authorize_answer=True),
        corpus_sha256=CORPUS_SHA256,
    )
    report = aggregate_gold_evidence(dataset, (evaluation,))
    invalid_metrics = report.metrics.model_copy(update={"answer_coverage": 0.0})
    invalid_report = report.model_copy(update={"metrics": invalid_metrics})

    with pytest.raises(ValidationError, match="metrics must be derived"):
        GoldEvidenceEvaluationReport.model_validate(invalid_report)
