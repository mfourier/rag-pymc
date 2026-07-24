import pytest
from pydantic import ValidationError

from rag_pymc.evaluation import (
    AggregateStructuralResponseMetrics,
    CitationTraceabilityReason,
    CitationTraceabilityResult,
    EvaluationError,
    StructuralFailureReason,
    StructuralResponseAggregateReport,
    StructuralResponseEvaluation,
    StructuralValidationFailure,
    StructuralValidationStage,
    aggregate_structural_responses,
)

RAW_OUTPUT_SHA256 = "a" * 64
GENERATOR_INPUT_SHA256 = "b" * 64
CONTEXT_CHUNK_IDS = ("chunk_a", "chunk_b")
OMITTED_CHUNK_IDS = ("chunk_omitted",)
AGGREGATE_RATE_FIELDS = (
    "json_parse_success_rate",
    "answer_contract_valid_given_json_parse_success_rate",
    "output_contract_valid_given_valid_answer_contract_rate",
    "citation_traceability_valid_given_valid_answer_contract_rate",
    "end_to_end_structural_validity_rate",
    "micro_citation_validity_rate",
    "micro_citation_reference_traceability_rate",
)


def make_valid_citation(
    citation_id: str,
    chunk_id: str,
    *,
    context_position: int,
    referenced_claim_ids: tuple[str, ...],
) -> CitationTraceabilityResult:
    return CitationTraceabilityResult(
        citation_id=citation_id,
        chunk_id=chunk_id,
        referenced_claim_ids=referenced_claim_ids,
        context_position=context_position,
        resolves_to_included_context=True,
        provenance_matches=True,
        is_valid=True,
    )


def make_invalid_citation(
    citation_id: str = "citation_invalid",
    chunk_id: str = "chunk_unknown",
    *,
    referenced_claim_ids: tuple[str, ...] = ("claim_1",),
) -> CitationTraceabilityResult:
    return CitationTraceabilityResult(
        citation_id=citation_id,
        chunk_id=chunk_id,
        referenced_claim_ids=referenced_claim_ids,
        resolves_to_included_context=False,
        provenance_matches=None,
        is_valid=False,
        reason_codes=(CitationTraceabilityReason.CHUNK_NOT_IN_CONTEXT,),
    )


def make_answer_record(
    response_id: str,
    *,
    is_abstaining: bool,
    claim_ids: tuple[str, ...],
    citation_results: tuple[CitationTraceabilityResult, ...] = (),
) -> StructuralResponseEvaluation:
    citation_count = len(citation_results)
    valid_citation_count = sum(result.is_valid for result in citation_results)
    invalid_citation_count = citation_count - valid_citation_count
    citation_reference_count = sum(len(result.referenced_claim_ids) for result in citation_results)
    traceable_citation_reference_count = sum(
        len(result.referenced_claim_ids) for result in citation_results if result.is_valid
    )
    untraceable_citation_reference_count = (
        citation_reference_count - traceable_citation_reference_count
    )
    output_contract_valid = invalid_citation_count == 0
    validation_failures = (
        ()
        if output_contract_valid
        else (
            StructuralValidationFailure(
                stage=StructuralValidationStage.GENERATOR_OUTPUT,
                reason_code=(StructuralFailureReason.GENERATOR_OUTPUT_CONTRACT_VALIDATION_FAILED),
                error_type="value_error",
            ),
        )
    )
    return StructuralResponseEvaluation(
        response_id=response_id,
        raw_output_sha256=RAW_OUTPUT_SHA256,
        generator_input_sha256=GENERATOR_INPUT_SHA256,
        context_chunk_ids=CONTEXT_CHUNK_IDS,
        omitted_chunk_ids=OMITTED_CHUNK_IDS,
        json_parse_succeeded=True,
        answer_contract_valid=True,
        output_contract_valid=output_contract_valid,
        citation_traceability_valid=output_contract_valid,
        structurally_valid=output_contract_valid,
        is_abstaining=is_abstaining,
        claim_ids=claim_ids,
        claim_count=len(claim_ids),
        citation_count=citation_count,
        valid_citation_count=valid_citation_count,
        invalid_citation_count=invalid_citation_count,
        citation_reference_count=citation_reference_count,
        traceable_citation_reference_count=traceable_citation_reference_count,
        untraceable_citation_reference_count=untraceable_citation_reference_count,
        citation_validity_rate=(
            None if citation_count == 0 else valid_citation_count / citation_count
        ),
        citation_reference_traceability_rate=(
            None
            if citation_reference_count == 0
            else traceable_citation_reference_count / citation_reference_count
        ),
        citation_results=citation_results,
        validation_failures=validation_failures,
    )


def make_answer_contract_failure(response_id: str) -> StructuralResponseEvaluation:
    return StructuralResponseEvaluation(
        response_id=response_id,
        raw_output_sha256=RAW_OUTPUT_SHA256,
        generator_input_sha256=GENERATOR_INPUT_SHA256,
        context_chunk_ids=CONTEXT_CHUNK_IDS,
        omitted_chunk_ids=OMITTED_CHUNK_IDS,
        json_parse_succeeded=True,
        answer_contract_valid=False,
        structurally_valid=False,
        validation_failures=(
            StructuralValidationFailure(
                stage=StructuralValidationStage.ANSWER_CONTRACT,
                reason_code=StructuralFailureReason.ANSWER_CONTRACT_VALIDATION_FAILED,
                location=("<unrecognized-field>",),
                error_type="extra_forbidden",
                occurrences=3,
            ),
        ),
    )


def make_json_parse_failure(response_id: str) -> StructuralResponseEvaluation:
    return StructuralResponseEvaluation(
        response_id=response_id,
        raw_output_sha256=RAW_OUTPUT_SHA256,
        generator_input_sha256=GENERATOR_INPUT_SHA256,
        context_chunk_ids=CONTEXT_CHUNK_IDS,
        omitted_chunk_ids=OMITTED_CHUNK_IDS,
        json_parse_succeeded=False,
        structurally_valid=False,
        validation_failures=(
            StructuralValidationFailure(
                stage=StructuralValidationStage.JSON_PARSE,
                reason_code=StructuralFailureReason.JSON_PARSE_FAILED,
                error_type="json_decode_error",
            ),
        ),
    )


def make_mixed_responses() -> tuple[StructuralResponseEvaluation, ...]:
    valid_cited = make_answer_record(
        "r_valid",
        is_abstaining=False,
        claim_ids=("claim_1", "claim_2", "claim_3"),
        citation_results=(
            make_valid_citation(
                "citation_a",
                "chunk_a",
                context_position=1,
                referenced_claim_ids=("claim_1", "claim_2"),
            ),
            make_valid_citation(
                "citation_b",
                "chunk_b",
                context_position=2,
                referenced_claim_ids=("claim_3",),
            ),
        ),
    )
    valid_uncited = make_answer_record(
        "r_uncited",
        is_abstaining=False,
        claim_ids=("claim_1",),
    )
    valid_abstention = make_answer_record(
        "r_abstain",
        is_abstaining=True,
        claim_ids=(),
    )
    invalid_provenance = make_answer_record(
        "r_provenance",
        is_abstaining=False,
        claim_ids=("claim_1",),
        citation_results=(make_invalid_citation(),),
    )
    return (
        valid_cited,
        valid_uncited,
        valid_abstention,
        invalid_provenance,
        make_answer_contract_failure("r_schema"),
        make_json_parse_failure("r_parse"),
    )


def test_aggregate_computes_conditional_funnel_and_micro_rates() -> None:
    responses = make_mixed_responses()
    before = tuple(response.model_dump_json() for response in responses)

    report = aggregate_structural_responses(responses)
    reversed_report = aggregate_structural_responses(tuple(reversed(responses)))
    serialized = report.model_dump_json()
    restored = StructuralResponseAggregateReport.model_validate_json(serialized)
    metrics = report.metrics

    assert report == reversed_report
    assert report.model_dump_json() == reversed_report.model_dump_json()
    assert tuple(response.response_id for response in report.responses) == (
        "r_abstain",
        "r_parse",
        "r_provenance",
        "r_schema",
        "r_uncited",
        "r_valid",
    )
    assert metrics.response_count == 6
    assert metrics.json_parse_success_count == 5
    assert metrics.json_parse_failure_count == 1
    assert metrics.json_parse_success_rate == pytest.approx(5 / 6)
    assert metrics.answer_contract_evaluated_count == 5
    assert metrics.answer_contract_valid_count == 4
    assert metrics.answer_contract_invalid_count == 1
    assert metrics.answer_contract_valid_given_json_parse_success_rate == pytest.approx(4 / 5)
    assert metrics.output_contract_evaluated_count == 4
    assert metrics.output_contract_valid_count == 3
    assert metrics.output_contract_invalid_count == 1
    assert metrics.output_contract_valid_given_valid_answer_contract_rate == pytest.approx(3 / 4)
    assert metrics.citation_traceability_evaluated_count == 4
    assert metrics.citation_traceability_valid_response_count == 3
    assert metrics.citation_traceability_invalid_response_count == 1
    assert metrics.citation_traceability_valid_given_valid_answer_contract_rate == pytest.approx(
        3 / 4
    )
    assert metrics.structurally_valid_response_count == 3
    assert metrics.structurally_invalid_response_count == 3
    assert metrics.end_to_end_structural_validity_rate == pytest.approx(3 / 6)
    assert metrics.abstaining_response_count == 1
    assert metrics.non_abstaining_response_count == 3
    assert metrics.citation_bearing_response_count == 2
    assert metrics.zero_citation_response_count == 2
    assert metrics.non_abstaining_zero_citation_response_count == 1
    assert metrics.total_claim_count == 5
    assert metrics.total_citation_count == 3
    assert metrics.total_valid_citation_count == 2
    assert metrics.total_invalid_citation_count == 1
    assert metrics.micro_citation_validity_rate == pytest.approx(2 / 3)
    assert metrics.total_citation_reference_count == 4
    assert metrics.total_traceable_citation_reference_count == 3
    assert metrics.total_untraceable_citation_reference_count == 1
    assert metrics.micro_citation_reference_traceability_rate == pytest.approx(3 / 4)
    assert restored == report
    assert restored.model_dump_json() == serialized
    assert report.as_json_value() == report.model_dump(mode="json")
    assert tuple(response.model_dump_json() for response in responses) == before
    assert len({response.raw_output_sha256 for response in report.responses}) == 1
    assert len({response.generator_input_sha256 for response in report.responses}) == 1


def test_empty_aggregate_has_zero_counts_and_undefined_rates() -> None:
    report = aggregate_structural_responses(())

    assert report.responses == ()
    for field_name, value in report.metrics.model_dump().items():
        if field_name.endswith("_count"):
            assert value == 0
        elif field_name.endswith("_rate"):
            assert value is None


def test_zero_citation_responses_do_not_invent_micro_rates() -> None:
    responses = (
        make_answer_record(
            "r_uncited",
            is_abstaining=False,
            claim_ids=("claim_1",),
        ),
        make_answer_record("r_abstain", is_abstaining=True, claim_ids=()),
    )

    metrics = aggregate_structural_responses(responses).metrics

    assert metrics.json_parse_success_rate == 1.0
    assert metrics.answer_contract_valid_given_json_parse_success_rate == 1.0
    assert metrics.output_contract_valid_given_valid_answer_contract_rate == 1.0
    assert metrics.citation_traceability_valid_given_valid_answer_contract_rate == 1.0
    assert metrics.end_to_end_structural_validity_rate == 1.0
    assert metrics.zero_citation_response_count == 2
    assert metrics.total_citation_count == 0
    assert metrics.total_citation_reference_count == 0
    assert metrics.micro_citation_validity_rate is None
    assert metrics.micro_citation_reference_traceability_rate is None


def test_pre_answer_failures_keep_later_stage_denominators_undefined() -> None:
    metrics = aggregate_structural_responses(
        (
            make_json_parse_failure("r_parse"),
            make_answer_contract_failure("r_schema"),
        )
    ).metrics

    assert metrics.response_count == 2
    assert metrics.json_parse_success_rate == 0.5
    assert metrics.answer_contract_valid_given_json_parse_success_rate == 0.0
    assert metrics.output_contract_evaluated_count == 0
    assert metrics.output_contract_valid_given_valid_answer_contract_rate is None
    assert metrics.citation_traceability_valid_given_valid_answer_contract_rate is None
    assert metrics.end_to_end_structural_validity_rate == 0.0
    assert metrics.micro_citation_validity_rate is None
    assert metrics.micro_citation_reference_traceability_rate is None


def test_all_parse_failures_have_zero_attempt_rates_and_undefined_later_rates() -> None:
    metrics = aggregate_structural_responses(
        (
            make_json_parse_failure("r_parse_a"),
            make_json_parse_failure("r_parse_b"),
        )
    ).metrics

    assert metrics.response_count == 2
    assert metrics.json_parse_success_count == 0
    assert metrics.json_parse_failure_count == 2
    assert metrics.json_parse_success_rate == 0.0
    assert metrics.answer_contract_evaluated_count == 0
    assert metrics.answer_contract_valid_given_json_parse_success_rate is None
    assert metrics.output_contract_evaluated_count == 0
    assert metrics.output_contract_valid_given_valid_answer_contract_rate is None
    assert metrics.citation_traceability_evaluated_count == 0
    assert metrics.citation_traceability_valid_given_valid_answer_contract_rate is None
    assert metrics.structurally_valid_response_count == 0
    assert metrics.structurally_invalid_response_count == 2
    assert metrics.end_to_end_structural_validity_rate == 0.0
    assert metrics.micro_citation_validity_rate is None
    assert metrics.micro_citation_reference_traceability_rate is None


def test_multiple_invalid_citations_are_micro_counted_once_each() -> None:
    response = make_answer_record(
        "r_two_invalid_citations",
        is_abstaining=False,
        claim_ids=("claim_1",),
        citation_results=(
            make_invalid_citation("citation_invalid_a", "chunk_unknown_a"),
            make_invalid_citation("citation_invalid_b", "chunk_unknown_b"),
        ),
    )

    metrics = aggregate_structural_responses((response,)).metrics

    assert metrics.output_contract_invalid_count == 1
    assert metrics.citation_traceability_invalid_response_count == 1
    assert metrics.total_citation_count == 2
    assert metrics.total_invalid_citation_count == 2
    assert metrics.total_untraceable_citation_reference_count == 2
    assert metrics.micro_citation_validity_rate == 0.0
    assert metrics.micro_citation_reference_traceability_rate == 0.0


@pytest.mark.parametrize("duplicate_kind", ["identical", "conflicting"])
def test_aggregate_rejects_duplicate_response_ids(duplicate_kind: str) -> None:
    first = make_answer_record(
        "duplicate",
        is_abstaining=False,
        claim_ids=("claim_1",),
    )
    second = first if duplicate_kind == "identical" else make_json_parse_failure("duplicate")

    with pytest.raises(EvaluationError, match="duplicate structural response IDs"):
        aggregate_structural_responses((first, second))

    with pytest.raises(EvaluationError, match="duplicate structural response IDs"):
        AggregateStructuralResponseMetrics.from_responses((first, second))


def test_aggregate_revalidates_copied_input_records() -> None:
    valid = make_answer_record(
        "r_valid",
        is_abstaining=False,
        claim_ids=("claim_1",),
    )
    invalid = valid.model_copy(update={"structurally_valid": False})

    with pytest.raises(ValidationError, match="structural validity must require"):
        aggregate_structural_responses((invalid,))

    with pytest.raises(ValidationError, match="structural validity must require"):
        AggregateStructuralResponseMetrics.from_responses((invalid,))


@pytest.mark.parametrize("rate_field", AGGREGATE_RATE_FIELDS)
@pytest.mark.parametrize("invalid_rate", [True, "0.5", float("inf"), float("nan")])
def test_aggregate_rates_are_strict_and_finite(
    rate_field: str,
    invalid_rate: bool | str | float,
) -> None:
    metrics = aggregate_structural_responses(make_mixed_responses()).metrics
    values = metrics.model_dump(mode="python")
    values[rate_field] = invalid_rate

    with pytest.raises(ValidationError):
        AggregateStructuralResponseMetrics.model_validate(values)


def test_rate_validation_matrix_covers_every_aggregate_rate() -> None:
    assert set(AGGREGATE_RATE_FIELDS) == {
        field_name
        for field_name in AggregateStructuralResponseMetrics.model_fields
        if field_name.endswith("_rate")
    }


def test_aggregate_report_rejects_population_and_metric_divergence() -> None:
    report = aggregate_structural_responses(make_mixed_responses())
    values = report.model_dump(mode="python")
    values["responses"] = tuple(reversed(report.responses))
    with pytest.raises(ValidationError, match="ordered by response_id"):
        StructuralResponseAggregateReport.model_validate(values)

    duplicate_responses = (report.responses[0], report.responses[0])
    values = report.model_dump(mode="python")
    values["responses"] = duplicate_responses
    with pytest.raises(ValidationError, match="response IDs must be unique"):
        StructuralResponseAggregateReport.model_validate(values)

    values = report.model_dump(mode="python")
    values["metrics"] = aggregate_structural_responses(()).metrics
    with pytest.raises(ValidationError, match="metrics must match embedded responses"):
        StructuralResponseAggregateReport.model_validate(values)


def test_aggregate_report_revalidates_nested_response_records() -> None:
    report = aggregate_structural_responses(make_mixed_responses())
    values = report.model_dump(mode="python")
    invalid_response = report.responses[0].model_copy(update={"structurally_valid": False})
    values["responses"] = (invalid_response, *report.responses[1:])

    with pytest.raises(ValidationError, match="structural validity must require"):
        StructuralResponseAggregateReport.model_validate(values)


@pytest.mark.parametrize(
    ("field_name", "unsupported_value"),
    [
        ("schema_version", "2"),
        ("aggregation_version", "structural-response-aggregate-v2"),
        ("source_evaluator_version", "structural-citation-v2"),
    ],
)
def test_aggregate_report_rejects_unsupported_versions(
    field_name: str,
    unsupported_value: str,
) -> None:
    values = aggregate_structural_responses(()).model_dump(mode="python")
    values[field_name] = unsupported_value

    with pytest.raises(ValidationError):
        StructuralResponseAggregateReport.model_validate(values)


def nested_field_names(value: object) -> set[str]:
    field_names: set[str] = set()
    if isinstance(value, dict):
        field_names.update(key for key in value if isinstance(key, str))
        for nested_value in value.values():
            field_names.update(nested_field_names(nested_value))
    elif isinstance(value, list):
        for nested_value in value:
            field_names.update(nested_field_names(nested_value))
    return field_names


def assert_excludes_raw_and_semantic_payload_fields(
    report: StructuralResponseAggregateReport,
) -> None:
    forbidden_fields = {
        "raw_answer_json",
        "query",
        "claim_text",
        "source_url",
        "latency_ms",
        "generated_at",
    }
    assert forbidden_fields.isdisjoint(nested_field_names(report.model_dump(mode="json")))


def test_aggregate_contains_no_raw_or_semantic_payload_fields() -> None:
    report = aggregate_structural_responses(make_mixed_responses())

    assert_excludes_raw_and_semantic_payload_fields(report)
    assert any(response.response_id == "r_valid" for response in report.responses)
    assert {response.raw_output_sha256 for response in report.responses} == {RAW_OUTPUT_SHA256}
    assert {response.generator_input_sha256 for response in report.responses} == {
        GENERATOR_INPUT_SHA256
    }
