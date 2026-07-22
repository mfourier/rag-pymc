import json
from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl, ValidationError

from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import (
    AtomicClaim,
    Chunk,
    Citation,
    ConstructedContext,
    ContextItem,
    EvidenceAssessment,
    EvidenceSufficiency,
    GeneratorInput,
    GroundedAnswer,
    GroundedAnswerSection,
    RetrievedChunk,
    SearchQuery,
    SourceType,
    render_context_item_v1,
)
from rag_pymc.evaluation import (
    CitationTraceabilityReason,
    CitationTraceabilityResult,
    StructuralFailureReason,
    StructuralResponseEvaluation,
    StructuralValidationFailure,
    StructuralValidationStage,
    aggregate_structural_responses,
    evaluate_structural_response,
)
from rag_pymc.retrieval import TechnicalTokenizer

NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


def make_result(
    chunk_id: str,
    *,
    rank: int,
    section: str | None,
    api_symbols: tuple[str, ...],
) -> RetrievedChunk:
    content = f"Evidence content for {chunk_id}."
    chunk = Chunk(
        chunk_id=chunk_id,
        document_id=f"document_{chunk_id}",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl(f"https://docs.example.test/{chunk_id}.html"),
        title=f"Title for {chunk_id}",
        section=section,
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        api_symbols=api_symbols,
        created_at=NOW,
    )
    return RetrievedChunk(
        chunk=chunk,
        score=1.0 / rank,
        rank=rank,
        retriever="weighted-rrf-v1",
    )


def make_context() -> tuple[ConstructedContext, tuple[RetrievedChunk, ...]]:
    query = SearchQuery(
        text="How do I configure and run sampling?",
        top_k=3,
        library="pymc",
        library_version="6.1.0",
    )
    results = (
        make_result("chunk_a", rank=1, section=None, api_symbols=()),
        make_result(
            "chunk_b",
            rank=2,
            section="Parameters",
            api_symbols=("pymc.sample", "pymc.sampling.mcmc.sample"),
        ),
        make_result(
            "chunk_c",
            rank=3,
            section="Returns",
            api_symbols=("pymc.sample",),
        ),
    )
    builder = RankedContextBuilder(TechnicalTokenizer())
    complete = builder.build(query, results, token_budget=100_000)
    two_item_budget = sum(item.token_count for item in complete.items[:2])
    context = builder.build(query, results, token_budget=two_item_budget)
    assert context.included_chunk_ids == ("chunk_a", "chunk_b")
    assert context.omitted_chunk_ids == ("chunk_c",)
    return context, results


def make_generator_input(context: ConstructedContext) -> GeneratorInput:
    assessment = EvidenceAssessment(
        policy_version="explicit-sufficient-test-stub-v1",
        sufficiency=EvidenceSufficiency.SUFFICIENT,
        should_abstain=False,
        reason_codes=("synthetic_contract_test",),
        context_chunk_ids=context.included_chunk_ids,
        omitted_chunk_ids=context.omitted_chunk_ids,
    )
    return GeneratorInput(
        query=context.query,
        context=context,
        assessment=assessment,
    )


def make_citation(source: ContextItem | Chunk, citation_id: str) -> Citation:
    return Citation(
        citation_id=citation_id,
        chunk_id=source.chunk_id,
        document_id=source.document_id,
        source_url=source.source_url,
        library=source.library,
        library_version=source.library_version,
        section=source.section,
        api_symbols=source.api_symbols,
    )


def make_answer(
    citations: tuple[Citation, ...],
    claim_references: tuple[tuple[str, ...], ...],
) -> GroundedAnswer:
    claims = tuple(
        AtomicClaim(
            claim_id=f"claim_{index}",
            text=f"Synthetic claim {index}.",
            citation_ids=references,
        )
        for index, references in enumerate(claim_references, start=1)
    )
    return GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="answer",
                heading="Answer",
                claims=claims,
            ),
        ),
        citations=citations,
    )


def evaluate(
    answer: GroundedAnswer, generator_input: GeneratorInput
) -> StructuralResponseEvaluation:
    return evaluate_structural_response(
        response_id="response_001",
        generator_input=generator_input,
        raw_answer_json=answer.model_dump_json(),
    )


def test_evaluator_returns_a_deterministic_record_for_valid_raw_answer() -> None:
    context, _ = make_context()
    generator_input = make_generator_input(context)
    citation_a = make_citation(context.items[0], "citation_a")
    citation_b = make_citation(context.items[1], "citation_b")
    answer = make_answer(
        (citation_b, citation_a),
        (("citation_a",), ("citation_a",), ("citation_b",)),
    )
    raw_answer_json = answer.model_dump_json()
    input_before = generator_input.model_dump_json()

    first = evaluate_structural_response(
        response_id="response_001",
        generator_input=generator_input,
        raw_answer_json=raw_answer_json,
    )
    second = evaluate_structural_response(
        response_id="response_001",
        generator_input=generator_input,
        raw_answer_json=raw_answer_json,
    )
    serialized = first.model_dump_json()
    restored = StructuralResponseEvaluation.model_validate_json(serialized)
    canonical_generator_input = json.dumps(
        generator_input.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert first == second
    assert first.raw_output_hash_policy == "utf-8-surrogatepass-v1"
    assert first.raw_output_sha256 == sha256(raw_answer_json.encode()).hexdigest()
    assert first.generator_input_hash_policy == "canonical-generator-input-json-v1"
    assert (
        first.generator_input_sha256
        == sha256(canonical_generator_input.encode("ascii")).hexdigest()
    )
    assert first.context_chunk_ids == context.included_chunk_ids
    assert first.omitted_chunk_ids == context.omitted_chunk_ids
    assert first.json_parse_succeeded is True
    assert first.answer_contract_valid is True
    assert first.output_contract_valid is True
    assert first.citation_traceability_valid is True
    assert first.structurally_valid is True
    assert first.claim_ids == ("claim_1", "claim_2", "claim_3")
    assert first.claim_count == 3
    assert first.citation_count == 2
    assert first.valid_citation_count == 2
    assert first.invalid_citation_count == 0
    assert first.citation_reference_count == 3
    assert first.traceable_citation_reference_count == 3
    assert first.untraceable_citation_reference_count == 0
    assert first.citation_validity_rate == 1.0
    assert first.citation_reference_traceability_rate == 1.0
    assert tuple(result.citation_id for result in first.citation_results) == (
        "citation_b",
        "citation_a",
    )
    assert first.citation_results[1].referenced_claim_ids == ("claim_1", "claim_2")
    assert first.validation_failures == ()
    assert restored == first
    assert restored.model_dump_json() == serialized
    assert generator_input.model_dump_json() == input_before
    assert "raw_answer_json" not in first.model_dump()
    assert "latency_ms" not in first.model_dump()
    assert "generated_at" not in first.model_dump()


def test_real_evaluator_record_feeds_the_aggregate_without_reinterpretation() -> None:
    context, _ = make_context()
    generator_input = make_generator_input(context)
    citation = make_citation(context.items[0], "citation_a")
    answer = make_answer((citation,), (("citation_a",),))
    response = evaluate_structural_response(
        response_id="response_001",
        generator_input=generator_input,
        raw_answer_json=answer.model_dump_json(),
    )

    report = aggregate_structural_responses((response,))

    assert report.responses == (response,)
    assert report.metrics.response_count == 1
    assert report.metrics.structurally_valid_response_count == 1
    assert report.metrics.total_claim_count == 1
    assert report.metrics.total_citation_count == 1
    assert report.metrics.total_citation_reference_count == 1
    assert report.metrics.end_to_end_structural_validity_rate == 1.0
    assert report.metrics.micro_citation_validity_rate == 1.0
    assert report.metrics.micro_citation_reference_traceability_rate == 1.0


def test_generator_input_hash_changes_with_policy_or_context_provenance() -> None:
    context, _ = make_context()
    generator_input = make_generator_input(context)
    answer = GroundedAnswer(is_abstaining=True)
    baseline = evaluate(answer, generator_input)

    assessment_values = generator_input.assessment.model_dump(mode="python")
    assessment_values["policy_version"] = "different-sufficient-test-stub-v1"
    changed_policy_input = GeneratorInput(
        query=generator_input.query,
        context=context,
        assessment=EvidenceAssessment.model_validate(assessment_values),
    )
    changed_policy = evaluate(answer, changed_policy_input)

    item_values = context.items[0].model_dump(mode="python")
    item_values["source_url"] = AnyUrl("https://docs.example.test/chunk_z.html")
    item_values["rendered_text"] = render_context_item_v1(
        position=item_values["position"],
        retrieval_rank=item_values["retrieval_rank"],
        retriever=item_values["retriever"],
        chunk_id=item_values["chunk_id"],
        document_id=item_values["document_id"],
        source_url=item_values["source_url"],
        library=item_values["library"],
        library_version=item_values["library_version"],
        source_type=item_values["source_type"],
        title=item_values["title"],
        section=item_values["section"],
        api_symbols=item_values["api_symbols"],
        content=item_values["content"],
    )
    changed_item = ContextItem.model_validate(item_values)
    context_values = context.model_dump(mode="python")
    context_values["items"] = (changed_item, *context.items[1:])
    changed_context = ConstructedContext.model_validate(context_values)
    changed_context_result = evaluate(answer, make_generator_input(changed_context))

    assert baseline.context_chunk_ids == changed_policy.context_chunk_ids
    assert baseline.context_chunk_ids == changed_context_result.context_chunk_ids
    assert baseline.omitted_chunk_ids == changed_policy.omitted_chunk_ids
    assert baseline.omitted_chunk_ids == changed_context_result.omitted_chunk_ids
    assert baseline.raw_output_sha256 == changed_policy.raw_output_sha256
    assert baseline.raw_output_sha256 == changed_context_result.raw_output_sha256
    assert baseline.generator_input_sha256 != changed_policy.generator_input_sha256
    assert baseline.generator_input_sha256 != changed_context_result.generator_input_sha256


@pytest.mark.parametrize("answer_kind", ["abstention", "uncited"])
def test_zero_citation_answers_are_structurally_valid_with_undefined_rates(
    answer_kind: str,
) -> None:
    context, _ = make_context()
    generator_input = make_generator_input(context)
    if answer_kind == "abstention":
        answer = GroundedAnswer(is_abstaining=True)
        expected_claim_count = 0
    else:
        answer = make_answer((), ((),))
        expected_claim_count = 1

    result = evaluate(answer, generator_input)

    assert result.structurally_valid is True
    assert result.output_contract_valid is True
    assert result.citation_traceability_valid is True
    assert result.is_abstaining is (answer_kind == "abstention")
    assert result.claim_ids == (() if answer_kind == "abstention" else ("claim_1",))
    assert result.claim_count == expected_claim_count
    assert result.citation_count == 0
    assert result.valid_citation_count == 0
    assert result.invalid_citation_count == 0
    assert result.citation_reference_count == 0
    assert result.citation_validity_rate is None
    assert result.citation_reference_traceability_rate is None
    assert result.citation_results == ()


def test_evaluator_records_malformed_json_without_raising() -> None:
    context, _ = make_context()
    generator_input = make_generator_input(context)
    raw_answer_json = '{"is_abstaining":'

    result = evaluate_structural_response(
        response_id="malformed",
        generator_input=generator_input,
        raw_answer_json=raw_answer_json,
    )

    assert result.raw_output_sha256 == sha256(raw_answer_json.encode()).hexdigest()
    assert result.json_parse_succeeded is False
    assert result.answer_contract_valid is None
    assert result.output_contract_valid is None
    assert result.citation_traceability_valid is None
    assert result.structurally_valid is False
    assert result.claim_ids is None
    assert result.claim_count is None
    assert result.citation_count is None
    assert result.citation_validity_rate is None
    assert result.citation_results == ()
    assert len(result.validation_failures) == 1
    failure = result.validation_failures[0]
    assert failure.stage is StructuralValidationStage.JSON_PARSE
    assert failure.reason_code is StructuralFailureReason.JSON_PARSE_FAILED
    assert failure.error_type == "json_decode_error"

    invalid_failure = failure.model_copy(update={"occurrences": 2})
    with pytest.raises(ValidationError, match="exactly one failure occurrence"):
        StructuralValidationFailure.model_validate(invalid_failure)


def test_evaluator_records_ill_formed_python_unicode_without_raising() -> None:
    context, _ = make_context()
    raw_answer_json = "\ud800"

    result = evaluate_structural_response(
        response_id="invalid_unicode",
        generator_input=make_generator_input(context),
        raw_answer_json=raw_answer_json,
    )

    expected_hash = sha256(raw_answer_json.encode("utf-8", errors="surrogatepass")).hexdigest()
    assert result.raw_output_sha256 == expected_hash
    assert result.json_parse_succeeded is False
    assert result.answer_contract_valid is None
    assert result.structurally_valid is False
    assert result.validation_failures == (
        StructuralValidationFailure(
            stage=StructuralValidationStage.JSON_PARSE,
            reason_code=StructuralFailureReason.JSON_PARSE_FAILED,
            error_type="json_invalid_unicode_error",
        ),
    )


@pytest.mark.parametrize(
    ("raw_answer_json", "expected_error_type"),
    [
        (
            '{"is_abstaining":false,"is_abstaining":true}',
            "json_duplicate_key_error",
        ),
        (
            '{"is_abstaining":false,"sections":[{"section_id":"answer",'
            '"heading":"Answer","claims":[{"claim_id":"claim","text":"first",'
            '"text":"second"}]}],"citations":[]}',
            "json_duplicate_key_error",
        ),
        (
            '{"is_abstaining":true,"unexpected":NaN}',
            "json_non_finite_number_error",
        ),
        (
            '{"is_abstaining":true,"unexpected":Infinity}',
            "json_non_finite_number_error",
        ),
    ],
)
def test_evaluator_rejects_ambiguous_or_non_standard_json(
    raw_answer_json: str,
    expected_error_type: str,
) -> None:
    context, _ = make_context()

    result = evaluate_structural_response(
        response_id="strict_json",
        generator_input=make_generator_input(context),
        raw_answer_json=raw_answer_json,
    )

    assert result.json_parse_succeeded is False
    assert result.answer_contract_valid is None
    assert result.structurally_valid is False
    assert result.validation_failures == (
        StructuralValidationFailure(
            stage=StructuralValidationStage.JSON_PARSE,
            reason_code=StructuralFailureReason.JSON_PARSE_FAILED,
            error_type=expected_error_type,
        ),
    )


@pytest.mark.parametrize(
    "raw_answer_json",
    [
        json.dumps({"schema_version": "2", "is_abstaining": True}),
        json.dumps({"is_abstaining": True, "text": "untracked prose"}),
        json.dumps({"is_abstaining": True, "generator_input": {"spoofed": True}}),
        "null",
    ],
)
def test_evaluator_records_answer_contract_failures_without_downstream_metrics(
    raw_answer_json: str,
) -> None:
    context, _ = make_context()

    result = evaluate_structural_response(
        response_id="invalid_schema",
        generator_input=make_generator_input(context),
        raw_answer_json=raw_answer_json,
    )

    assert result.json_parse_succeeded is True
    assert result.answer_contract_valid is False
    assert result.output_contract_valid is None
    assert result.citation_traceability_valid is None
    assert result.structurally_valid is False
    assert result.claim_ids is None
    assert result.claim_count is None
    assert result.citation_count is None
    assert result.citation_results == ()
    assert result.validation_failures
    assert all(
        failure.stage is StructuralValidationStage.ANSWER_CONTRACT
        for failure in result.validation_failures
    )
    assert all(
        failure.reason_code is StructuralFailureReason.ANSWER_CONTRACT_VALIDATION_FAILED
        for failure in result.validation_failures
    )
    failure_keys = tuple(
        (failure.location, failure.error_type) for failure in result.validation_failures
    )
    assert failure_keys == tuple(sorted(failure_keys))


def test_unknown_claim_reference_is_an_answer_failure_not_a_context_failure() -> None:
    context, _ = make_context()
    raw_answer_json = json.dumps(
        {
            "is_abstaining": False,
            "sections": [
                {
                    "section_id": "answer",
                    "heading": "Answer",
                    "claims": [
                        {
                            "claim_id": "claim",
                            "text": "Claim text.",
                            "citation_ids": ["missing"],
                        }
                    ],
                }
            ],
            "citations": [],
        }
    )

    result = evaluate_structural_response(
        response_id="unknown_reference",
        generator_input=make_generator_input(context),
        raw_answer_json=raw_answer_json,
    )

    assert result.answer_contract_valid is False
    assert result.output_contract_valid is None
    assert result.citation_results == ()
    assert {failure.stage for failure in result.validation_failures} == {
        StructuralValidationStage.ANSWER_CONTRACT
    }


def test_schema_failures_do_not_retain_unknown_field_names_or_values() -> None:
    context, _ = make_context()
    raw_answer_json = json.dumps(
        {
            "schema_version": "2",
            "is_abstaining": "not-a-boolean",
            "private_customer_token": "sensitive-value",
        }
    )

    result = evaluate_structural_response(
        response_id="sanitized_failure",
        generator_input=make_generator_input(context),
        raw_answer_json=raw_answer_json,
    )
    serialized = result.model_dump_json()

    assert result.answer_contract_valid is False
    assert len(result.validation_failures) == 3
    assert tuple(failure.location for failure in result.validation_failures) == (
        ("<unrecognized-field>",),
        ("is_abstaining",),
        ("schema_version",),
    )
    assert "private_customer_token" not in serialized
    assert "sensitive-value" not in serialized


def test_sanitized_failures_preserve_duplicate_diagnostic_multiplicity() -> None:
    context, _ = make_context()
    raw_answer_json = json.dumps(
        {
            "is_abstaining": True,
            "first_private_field": "first-sensitive-value",
            "second_private_field": "second-sensitive-value",
        }
    )

    result = evaluate_structural_response(
        response_id="sanitized_multiplicity",
        generator_input=make_generator_input(context),
        raw_answer_json=raw_answer_json,
    )
    serialized = result.model_dump_json()

    assert result.validation_failures == (
        StructuralValidationFailure(
            stage=StructuralValidationStage.ANSWER_CONTRACT,
            reason_code=StructuralFailureReason.ANSWER_CONTRACT_VALIDATION_FAILED,
            location=("<unrecognized-field>",),
            error_type="extra_forbidden",
            occurrences=2,
        ),
    )
    assert "first_private_field" not in serialized
    assert "second_private_field" not in serialized
    assert "first-sensitive-value" not in serialized
    assert "second-sensitive-value" not in serialized


@pytest.mark.parametrize(
    ("citation_kind", "expected_reason"),
    [
        ("omitted", CitationTraceabilityReason.CHUNK_OMITTED),
        ("unknown", CitationTraceabilityReason.CHUNK_NOT_IN_CONTEXT),
    ],
)
def test_evaluator_distinguishes_omitted_and_unknown_citation_chunks(
    citation_kind: str,
    expected_reason: CitationTraceabilityReason,
) -> None:
    context, results = make_context()
    if citation_kind == "omitted":
        citation = make_citation(results[2].chunk, "citation")
    else:
        values = make_citation(context.items[0], "citation").model_dump(mode="python")
        values["chunk_id"] = "chunk_unknown"
        citation = Citation.model_validate(values)
    answer = make_answer((citation,), (("citation",),))

    result = evaluate(answer, make_generator_input(context))

    assert result.answer_contract_valid is True
    assert result.output_contract_valid is False
    assert result.citation_traceability_valid is False
    assert result.structurally_valid is False
    assert result.citation_count == 1
    assert result.valid_citation_count == 0
    assert result.invalid_citation_count == 1
    assert result.citation_validity_rate == 0.0
    assert result.citation_reference_traceability_rate == 0.0
    citation_result = result.citation_results[0]
    assert citation_result.resolves_to_included_context is False
    assert citation_result.provenance_matches is None
    assert citation_result.context_position is None
    assert citation_result.reason_codes == (expected_reason,)
    assert {failure.stage for failure in result.validation_failures} == {
        StructuralValidationStage.GENERATOR_OUTPUT
    }


def test_evaluator_reports_every_mismatched_citation_provenance_field() -> None:
    context, _ = make_context()
    values = make_citation(context.items[1], "citation").model_dump(mode="python")
    values.update(
        {
            "document_id": "wrong_document",
            "source_url": "https://docs.example.test/wrong.html",
            "library": "arviz",
            "library_version": "0.0.0",
            "section": "Wrong section",
            "api_symbols": ("pymc.sampling.mcmc.sample", "pymc.sample"),
        }
    )
    citation = Citation.model_validate(values)
    answer = make_answer((citation,), (("citation",),))

    result = evaluate(answer, make_generator_input(context))

    citation_result = result.citation_results[0]
    assert citation_result.resolves_to_included_context is True
    assert citation_result.context_position == 2
    assert citation_result.provenance_matches is False
    assert citation_result.is_valid is False
    assert citation_result.reason_codes == tuple(
        sorted(
            (
                CitationTraceabilityReason.API_SYMBOLS_MISMATCH,
                CitationTraceabilityReason.DOCUMENT_ID_MISMATCH,
                CitationTraceabilityReason.LIBRARY_MISMATCH,
                CitationTraceabilityReason.LIBRARY_VERSION_MISMATCH,
                CitationTraceabilityReason.SECTION_MISMATCH,
                CitationTraceabilityReason.SOURCE_URL_MISMATCH,
            ),
            key=lambda reason: reason.value,
        )
    )
    assert result.output_contract_valid is False
    assert result.structurally_valid is False


def test_evaluator_counts_all_valid_and_invalid_citations_and_references() -> None:
    context, _ = make_context()
    valid = make_citation(context.items[0], "valid")
    invalid_values = make_citation(context.items[1], "invalid").model_dump(mode="python")
    invalid_values["document_id"] = "wrong_document"
    invalid = Citation.model_validate(invalid_values)
    answer = make_answer(
        (valid, invalid),
        (("valid",), ("valid",), ("invalid",)),
    )

    result = evaluate(answer, make_generator_input(context))

    assert tuple(citation.is_valid for citation in result.citation_results) == (True, False)
    assert result.citation_count == 2
    assert result.valid_citation_count == 1
    assert result.invalid_citation_count == 1
    assert result.citation_validity_rate == 0.5
    assert result.citation_reference_count == 3
    assert result.traceable_citation_reference_count == 2
    assert result.untraceable_citation_reference_count == 1
    assert result.citation_reference_traceability_rate == pytest.approx(2 / 3)
    assert result.output_contract_valid is False
    assert result.structurally_valid is False


def test_evaluator_reports_all_citations_after_authoritative_output_failure() -> None:
    context, results = make_context()
    omitted = make_citation(results[2].chunk, "omitted")
    unknown_values = make_citation(context.items[0], "unknown").model_dump(mode="python")
    unknown_values["chunk_id"] = "chunk_unknown"
    unknown = Citation.model_validate(unknown_values)
    answer = make_answer(
        (omitted, unknown),
        (("omitted",), ("unknown",)),
    )

    result = evaluate(answer, make_generator_input(context))

    assert result.output_contract_valid is False
    assert result.citation_count == 2
    assert result.invalid_citation_count == 2
    assert tuple(citation.reason_codes for citation in result.citation_results) == (
        (CitationTraceabilityReason.CHUNK_OMITTED,),
        (CitationTraceabilityReason.CHUNK_NOT_IN_CONTEXT,),
    )


def test_structural_evaluation_binds_resolved_citations_to_context_order() -> None:
    context, _ = make_context()
    citation = make_citation(context.items[0], "citation")
    result = evaluate(
        make_answer((citation,), (("citation",),)),
        make_generator_input(context),
    )

    unknown_chunk = result.citation_results[0].model_copy(update={"chunk_id": "chunk_unknown"})
    values = result.model_dump(mode="python")
    values["citation_results"] = (unknown_chunk,)
    with pytest.raises(ValidationError, match="recorded context chunk"):
        StructuralResponseEvaluation.model_validate(values)

    wrong_position = result.citation_results[0].model_copy(update={"context_position": 2})
    values = result.model_dump(mode="python")
    values["citation_results"] = (wrong_position,)
    with pytest.raises(ValidationError, match="recorded context order"):
        StructuralResponseEvaluation.model_validate(values)


def test_structural_evaluation_binds_unresolved_citations_to_chunk_class() -> None:
    context, results = make_context()
    omitted_result = evaluate(
        make_answer(
            (make_citation(results[2].chunk, "omitted"),),
            (("omitted",),),
        ),
        make_generator_input(context),
    )
    mislabeled_omitted = omitted_result.citation_results[0].model_copy(
        update={"chunk_id": "chunk_unknown"}
    )
    values = omitted_result.model_dump(mode="python")
    values["citation_results"] = (mislabeled_omitted,)
    with pytest.raises(ValidationError, match="recorded omitted chunk"):
        StructuralResponseEvaluation.model_validate(values)

    mislabeled_unknown = CitationTraceabilityResult(
        citation_id="unknown",
        chunk_id="chunk_c",
        referenced_claim_ids=("claim_1",),
        resolves_to_included_context=False,
        provenance_matches=None,
        is_valid=False,
        reason_codes=(CitationTraceabilityReason.CHUNK_NOT_IN_CONTEXT,),
    )
    values = omitted_result.model_dump(mode="python")
    values["citation_results"] = (mislabeled_unknown,)
    with pytest.raises(ValidationError, match="unrecorded chunk"):
        StructuralResponseEvaluation.model_validate(values)


def test_structural_evaluation_requires_output_and_traceability_parity() -> None:
    context, results = make_context()
    valid = evaluate(
        make_answer(
            (make_citation(context.items[0], "citation"),),
            (("citation",),),
        ),
        make_generator_input(context),
    )
    values = valid.model_dump(mode="python")
    values.update(
        {
            "output_contract_valid": False,
            "structurally_valid": False,
            "validation_failures": (
                StructuralValidationFailure(
                    stage=StructuralValidationStage.GENERATOR_OUTPUT,
                    reason_code=(
                        StructuralFailureReason.GENERATOR_OUTPUT_CONTRACT_VALIDATION_FAILED
                    ),
                    error_type="value_error",
                ),
            ),
        }
    )
    with pytest.raises(ValidationError, match="must match citation traceability"):
        StructuralResponseEvaluation.model_validate(values)

    invalid = evaluate(
        make_answer(
            (make_citation(results[2].chunk, "citation"),),
            (("citation",),),
        ),
        make_generator_input(context),
    )
    values = invalid.model_dump(mode="python")
    values.update(
        {
            "output_contract_valid": True,
            "validation_failures": (),
        }
    )
    with pytest.raises(ValidationError, match="must match citation traceability"):
        StructuralResponseEvaluation.model_validate(values)


def test_evaluator_preserves_claim_order_across_sections_and_shared_citations() -> None:
    context, _ = make_context()
    citation = make_citation(context.items[0], "citation")
    answer = GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="first",
                heading="First",
                claims=(
                    AtomicClaim(
                        claim_id="claim_z",
                        text="First traversal claim.",
                        citation_ids=("citation",),
                    ),
                ),
            ),
            GroundedAnswerSection(
                section_id="second",
                heading="Second",
                claims=(
                    AtomicClaim(
                        claim_id="claim_a",
                        text="Second traversal claim.",
                        citation_ids=("citation",),
                    ),
                ),
            ),
        ),
        citations=(citation,),
    )

    result = evaluate(answer, make_generator_input(context))

    assert result.claim_ids == ("claim_z", "claim_a")
    assert result.citation_results[0].referenced_claim_ids == ("claim_a", "claim_z")


def test_structural_evaluation_binds_reference_ids_to_recorded_claims() -> None:
    context, _ = make_context()
    citation = make_citation(context.items[0], "citation")
    result = evaluate(
        make_answer((citation,), (("citation",), ("citation",))),
        make_generator_input(context),
    )
    values = result.model_dump(mode="python")
    values["claim_count"] = 1

    with pytest.raises(ValidationError, match="claim_count must match claim_ids"):
        StructuralResponseEvaluation.model_validate(values)

    fabricated_reference = result.citation_results[0].model_copy(
        update={"referenced_claim_ids": ("fabricated_claim",)}
    )
    values = result.model_dump(mode="python")
    values["citation_results"] = (fabricated_reference,)
    values["citation_reference_count"] = 1
    values["traceable_citation_reference_count"] = 1
    values["citation_reference_traceability_rate"] = 1.0
    with pytest.raises(ValidationError, match="identify recorded claim IDs"):
        StructuralResponseEvaluation.model_validate(values)


@pytest.mark.parametrize(
    "rate_field",
    ["citation_validity_rate", "citation_reference_traceability_rate"],
)
@pytest.mark.parametrize("invalid_value", [True, "1.0", float("inf"), float("nan")])
def test_structural_evaluation_rates_are_strict_and_finite(
    rate_field: str,
    invalid_value: bool | str | float,
) -> None:
    context, _ = make_context()
    citation = make_citation(context.items[0], "citation")
    result = evaluate(
        make_answer((citation,), (("citation",),)),
        make_generator_input(context),
    )
    values = result.model_dump(mode="python")
    values[rate_field] = invalid_value

    with pytest.raises(ValidationError):
        StructuralResponseEvaluation.model_validate(values)


def test_structural_evaluation_revalidates_nested_copied_results() -> None:
    context, _ = make_context()
    citation = make_citation(context.items[0], "citation")
    result = evaluate(
        make_answer((citation,), (("citation",),)),
        make_generator_input(context),
    )
    invalid_citation_result = result.citation_results[0].model_copy(update={"is_valid": False})
    values = result.model_dump(mode="python")
    values["citation_results"] = (invalid_citation_result,)

    with pytest.raises(ValidationError, match="citation validity must match"):
        StructuralResponseEvaluation.model_validate(values)


def test_invalid_trusted_generator_input_raises_as_an_orchestration_error() -> None:
    context, _ = make_context()
    generator_input = make_generator_input(context)
    invalid_input = generator_input.model_copy(
        update={"query": SearchQuery(text="Different query")}
    )

    with pytest.raises(ValidationError, match="query must exactly match"):
        evaluate_structural_response(
            response_id="invalid_input",
            generator_input=invalid_input,
            raw_answer_json=GroundedAnswer(is_abstaining=True).model_dump_json(),
        )
