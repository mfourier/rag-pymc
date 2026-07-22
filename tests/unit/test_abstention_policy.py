from datetime import UTC, datetime
from hashlib import sha256

from pydantic import AnyUrl

from rag_pymc.abstention import AbstentionPolicy, ConservativeAbstentionPolicy
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    EvidenceAssessment,
    EvidenceSufficiency,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)
from rag_pymc.retrieval import TechnicalTokenizer

NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


def make_result(chunk_id: str, *, rank: int) -> RetrievedChunk:
    content = f"Complete evidence for {chunk_id}."
    chunk = Chunk(
        chunk_id=chunk_id,
        document_id=f"document_{chunk_id}",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl(f"https://docs.example.test/{chunk_id}.html"),
        title="pymc.sample",
        section="Overview",
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        api_symbols=("pymc.sample",),
        created_at=NOW,
    )
    return RetrievedChunk(
        chunk=chunk,
        score=1.0 / rank,
        rank=rank,
        retriever="weighted-rrf-v1",
    )


def make_contexts() -> tuple[
    ConstructedContext,
    ConstructedContext,
    ConstructedContext,
    ConstructedContext,
]:
    query = SearchQuery(
        text="How do I sample?",
        top_k=2,
        library="pymc",
        library_version="6.1.0",
    )
    results = (make_result("chunk_a", rank=1), make_result("chunk_b", rank=2))
    builder = RankedContextBuilder(TechnicalTokenizer())
    included_all = builder.build(query, results, token_budget=10_000)
    first_item_cost = included_all.items[0].token_count
    no_evidence = builder.build(query, (), token_budget=100)
    excluded_all = builder.build(query, results, token_budget=first_item_cost - 1)
    included_and_omitted = builder.build(query, results, token_budget=first_item_cost)
    return no_evidence, excluded_all, included_all, included_and_omitted


def assert_fail_closed(assessment: EvidenceAssessment) -> None:
    assert assessment.policy_version == "conservative-no-threshold-v1"
    assert assessment.should_abstain is True
    assert assessment.sufficiency is not EvidenceSufficiency.SUFFICIENT


def test_policy_marks_no_retrieved_evidence_insufficient() -> None:
    no_evidence, _, _, _ = make_contexts()

    assessment = ConservativeAbstentionPolicy().assess(no_evidence)

    assert_fail_closed(assessment)
    assert assessment.sufficiency is EvidenceSufficiency.INSUFFICIENT
    assert assessment.reason_codes == ("no_retrieved_evidence",)
    assert assessment.context_chunk_ids == ()
    assert assessment.omitted_chunk_ids == ()


def test_policy_marks_budget_excluded_evidence_insufficient() -> None:
    _, excluded_all, _, _ = make_contexts()

    assessment = ConservativeAbstentionPolicy().assess(excluded_all)

    assert_fail_closed(assessment)
    assert assessment.sufficiency is EvidenceSufficiency.INSUFFICIENT
    assert assessment.reason_codes == ("budget_excluded_all_evidence",)
    assert assessment.context_chunk_ids == ()
    assert assessment.omitted_chunk_ids == excluded_all.omitted_chunk_ids


def test_policy_does_not_assess_nonempty_context_as_sufficient() -> None:
    _, _, included_all, _ = make_contexts()

    assessment = ConservativeAbstentionPolicy().assess(included_all)

    assert_fail_closed(assessment)
    assert assessment.sufficiency is EvidenceSufficiency.NOT_ASSESSED
    assert assessment.reason_codes == ("no_calibrated_criterion",)
    assert assessment.context_chunk_ids == included_all.included_chunk_ids
    assert assessment.omitted_chunk_ids == ()


def test_policy_reports_sorted_reasons_for_included_and_omitted_evidence() -> None:
    _, _, _, included_and_omitted = make_contexts()

    assessment = ConservativeAbstentionPolicy().assess(included_and_omitted)

    assert_fail_closed(assessment)
    assert assessment.sufficiency is EvidenceSufficiency.NOT_ASSESSED
    assert assessment.reason_codes == (
        "budget_omitted_evidence",
        "no_calibrated_criterion",
    )
    assert assessment.context_chunk_ids == included_and_omitted.included_chunk_ids
    assert assessment.omitted_chunk_ids == included_and_omitted.omitted_chunk_ids


def assess_through_protocol(
    policy: AbstentionPolicy,
    context: ConstructedContext,
) -> EvidenceAssessment:
    return policy.assess(context)


def test_policy_is_deterministic_round_trips_json_and_does_not_mutate_context() -> None:
    _, _, _, context = make_contexts()
    serialized_context = context.model_dump_json()
    policy = ConservativeAbstentionPolicy()

    first = assess_through_protocol(policy, context)
    second = assess_through_protocol(policy, context)
    serialized = first.model_dump_json()
    restored = EvidenceAssessment.model_validate_json(serialized)

    assert first == second
    assert restored == first
    assert restored.model_dump_json() == serialized
    assert context.model_dump_json() == serialized_context


def test_assessment_contains_no_score_threshold_or_runtime_fields() -> None:
    _, _, included_all, _ = make_contexts()

    assessment = ConservativeAbstentionPolicy().assess(included_all)

    assert set(assessment.model_dump(mode="json")) == {
        "schema_version",
        "policy_version",
        "sufficiency",
        "should_abstain",
        "reason_codes",
        "context_chunk_ids",
        "omitted_chunk_ids",
    }
