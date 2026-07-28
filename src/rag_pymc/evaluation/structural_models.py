"""Contracts for structural response and citation evaluation."""

from collections.abc import Sequence
from enum import StrEnum
from typing import Any, Literal, Self, cast

from pydantic import Field, model_validator

from rag_pymc.evaluation._model_base import EvaluationModel, NonEmptyString, Sha256
from rag_pymc.evaluation.errors import EvaluationError


class StructuralValidationStage(StrEnum):
    """Ordered boundary at which a raw answer attempt failed validation."""

    JSON_PARSE = "json_parse"
    ANSWER_CONTRACT = "answer_contract"
    GENERATOR_OUTPUT = "generator_output"


class StructuralFailureReason(StrEnum):
    """Stable project-owned reason for a structural validation failure."""

    JSON_PARSE_FAILED = "json_parse_failed"
    ANSWER_CONTRACT_VALIDATION_FAILED = "answer_contract_validation_failed"
    GENERATOR_OUTPUT_CONTRACT_VALIDATION_FAILED = "generator_output_contract_validation_failed"


class CitationTraceabilityReason(StrEnum):
    """Why one declared citation is not traceable to authoritative context."""

    API_SYMBOLS_MISMATCH = "citation_api_symbols_mismatch"
    CHUNK_NOT_IN_CONTEXT = "citation_chunk_not_in_context"
    CHUNK_OMITTED = "citation_chunk_omitted"
    DOCUMENT_ID_MISMATCH = "citation_document_id_mismatch"
    LIBRARY_MISMATCH = "citation_library_mismatch"
    LIBRARY_VERSION_MISMATCH = "citation_library_version_mismatch"
    SECTION_MISMATCH = "citation_section_mismatch"
    SOURCE_URL_MISMATCH = "citation_source_url_mismatch"


class StructuralValidationFailure(EvaluationModel):
    """Sanitized deterministic diagnostics for one failed validation stage."""

    stage: StructuralValidationStage
    reason_code: StructuralFailureReason
    location: tuple[NonEmptyString, ...] = ()
    error_type: NonEmptyString
    occurrences: int = Field(default=1, ge=1, strict=True)

    @model_validator(mode="after")
    def reason_must_match_stage(self) -> Self:
        """Prevent a stable failure code from being assigned to the wrong stage."""
        expected_reasons = {
            StructuralValidationStage.JSON_PARSE: StructuralFailureReason.JSON_PARSE_FAILED,
            StructuralValidationStage.ANSWER_CONTRACT: (
                StructuralFailureReason.ANSWER_CONTRACT_VALIDATION_FAILED
            ),
            StructuralValidationStage.GENERATOR_OUTPUT: (
                StructuralFailureReason.GENERATOR_OUTPUT_CONTRACT_VALIDATION_FAILED
            ),
        }
        if self.reason_code is not expected_reasons[self.stage]:
            msg = "structural validation failure reason must match its stage"
            raise ValueError(msg)
        if self.stage is StructuralValidationStage.JSON_PARSE and self.occurrences != 1:
            msg = "a JSON parse attempt must contain exactly one failure occurrence"
            raise ValueError(msg)
        return self


class CitationTraceabilityResult(EvaluationModel):
    """Structural validity of one citation and every claim reference to it."""

    citation_id: NonEmptyString
    chunk_id: NonEmptyString
    referenced_claim_ids: tuple[NonEmptyString, ...] = Field(min_length=1)
    context_position: int | None = Field(default=None, ge=1, strict=True)
    resolves_to_included_context: bool = Field(strict=True)
    provenance_matches: bool | None = Field(default=None, strict=True)
    is_valid: bool = Field(strict=True)
    reason_codes: tuple[CitationTraceabilityReason, ...] = ()

    @model_validator(mode="after")
    def validate_traceability_state(self) -> Self:
        """Require canonical references and a logically consistent diagnostic state."""
        if len(set(self.referenced_claim_ids)) != len(self.referenced_claim_ids):
            msg = "citation traceability referenced claim IDs must be unique"
            raise ValueError(msg)
        if self.referenced_claim_ids != tuple(sorted(self.referenced_claim_ids)):
            msg = "citation traceability referenced claim IDs must be ordered"
            raise ValueError(msg)

        reason_values = tuple(reason.value for reason in self.reason_codes)
        if len(set(reason_values)) != len(reason_values):
            msg = "citation traceability reason codes must be unique"
            raise ValueError(msg)
        if reason_values != tuple(sorted(reason_values)):
            msg = "citation traceability reason codes must be ordered"
            raise ValueError(msg)

        resolution_reasons = {
            CitationTraceabilityReason.CHUNK_NOT_IN_CONTEXT,
            CitationTraceabilityReason.CHUNK_OMITTED,
        }
        mismatch_reasons = set(CitationTraceabilityReason) - resolution_reasons

        if not self.resolves_to_included_context:
            if self.context_position is not None or self.provenance_matches is not None:
                msg = "unresolved citations cannot have a context position or provenance result"
                raise ValueError(msg)
            if len(self.reason_codes) != 1 or self.reason_codes[0] not in resolution_reasons:
                msg = "unresolved citations require exactly one resolution failure reason"
                raise ValueError(msg)
        elif self.provenance_matches is True:
            if self.context_position is None or self.reason_codes:
                msg = "matching citations require a context position and no failure reasons"
                raise ValueError(msg)
        elif self.provenance_matches is False:
            if (
                self.context_position is None
                or not self.reason_codes
                or any(reason not in mismatch_reasons for reason in self.reason_codes)
            ):
                msg = "provenance mismatches require a context position and mismatch reasons"
                raise ValueError(msg)
        else:
            msg = "resolved citations require an explicit provenance result"
            raise ValueError(msg)

        expected_validity = (
            self.resolves_to_included_context
            and self.provenance_matches is True
            and not self.reason_codes
        )
        if self.is_valid is not expected_validity:
            msg = "citation validity must match resolution and provenance diagnostics"
            raise ValueError(msg)
        return self


class StructuralResponseEvaluation(EvaluationModel):
    """Deterministic structural measurements, excluding semantic support judgments.

    Opaque identifiers and content hashes are retained as linkable metadata; callers must
    not place prose, secrets, or other sensitive payloads in identifiers.
    """

    schema_version: Literal["1"] = "1"
    evaluator_version: Literal["structural-citation-v1"] = "structural-citation-v1"
    response_id: NonEmptyString
    raw_output_hash_policy: Literal["utf-8-surrogatepass-v1"] = "utf-8-surrogatepass-v1"
    raw_output_sha256: Sha256 = Field(
        description=(
            "SHA-256 over exact UTF-8 bytes for well-formed text, with surrogatepass used "
            "only to fingerprint malformed Python strings deterministically."
        )
    )
    generator_input_hash_policy: Literal["canonical-generator-input-json-v1"] = (
        "canonical-generator-input-json-v1"
    )
    generator_input_sha256: Sha256
    context_chunk_ids: tuple[NonEmptyString, ...] = Field(min_length=1)
    omitted_chunk_ids: tuple[NonEmptyString, ...] = ()
    json_parse_succeeded: bool = Field(strict=True)
    answer_contract_valid: bool | None = Field(default=None, strict=True)
    output_contract_valid: bool | None = Field(default=None, strict=True)
    citation_traceability_valid: bool | None = Field(
        default=None,
        strict=True,
        description=(
            "Whether every declared citation is structurally traceable; true with no "
            "citations does not establish citation completeness."
        ),
    )
    structurally_valid: bool = Field(
        strict=True,
        description=(
            "Whether the staged structural contracts pass; this is not answer correctness, "
            "citation correctness, or citation completeness."
        ),
    )
    is_abstaining: bool | None = Field(default=None, strict=True)
    claim_ids: tuple[NonEmptyString, ...] | None = None
    claim_count: int | None = Field(default=None, ge=0, strict=True)
    citation_count: int | None = Field(default=None, ge=0, strict=True)
    valid_citation_count: int | None = Field(default=None, ge=0, strict=True)
    invalid_citation_count: int | None = Field(default=None, ge=0, strict=True)
    citation_reference_count: int | None = Field(default=None, ge=0, strict=True)
    traceable_citation_reference_count: int | None = Field(
        default=None,
        ge=0,
        strict=True,
    )
    untraceable_citation_reference_count: int | None = Field(
        default=None,
        ge=0,
        strict=True,
    )
    citation_validity_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
    )
    citation_reference_traceability_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
    )
    citation_results: tuple[CitationTraceabilityResult, ...] = ()
    validation_failures: tuple[StructuralValidationFailure, ...] = ()

    @model_validator(mode="after")
    def validate_stage_and_metric_consistency(self) -> Self:
        """Keep failed stages, counts, rates, and diagnostics internally consistent."""
        if len(set(self.context_chunk_ids)) != len(self.context_chunk_ids):
            msg = "structural evaluation context chunk IDs must be unique"
            raise ValueError(msg)
        if len(set(self.omitted_chunk_ids)) != len(self.omitted_chunk_ids):
            msg = "structural evaluation omitted chunk IDs must be unique"
            raise ValueError(msg)
        if set(self.context_chunk_ids) & set(self.omitted_chunk_ids):
            msg = "structural evaluation context and omitted chunk IDs must not overlap"
            raise ValueError(msg)

        failure_keys = tuple(
            (
                failure.stage.value,
                failure.reason_code.value,
                failure.location,
                failure.error_type,
            )
            for failure in self.validation_failures
        )
        if len(set(failure_keys)) != len(failure_keys):
            msg = "structural validation failures must be unique"
            raise ValueError(msg)
        if failure_keys != tuple(sorted(failure_keys)):
            msg = "structural validation failures must be canonically ordered"
            raise ValueError(msg)

        required_answer_values = (
            self.is_abstaining,
            self.claim_ids,
            self.claim_count,
            self.citation_count,
            self.valid_citation_count,
            self.invalid_citation_count,
            self.citation_reference_count,
            self.traceable_citation_reference_count,
            self.untraceable_citation_reference_count,
        )
        answer_derived_values = (
            *required_answer_values,
            self.citation_validity_rate,
            self.citation_reference_traceability_rate,
        )
        failure_stages = {failure.stage for failure in self.validation_failures}

        if not self.json_parse_succeeded:
            if (
                self.answer_contract_valid is not None
                or self.output_contract_valid is not None
                or self.citation_traceability_valid is not None
                or any(value is not None for value in answer_derived_values)
                or self.citation_results
                or self.structurally_valid
            ):
                msg = "JSON parse failures cannot contain downstream evaluation values"
                raise ValueError(msg)
            if failure_stages != {StructuralValidationStage.JSON_PARSE}:
                msg = "JSON parse failures require only JSON-parse diagnostics"
                raise ValueError(msg)
            return self

        if self.answer_contract_valid is False:
            if (
                self.output_contract_valid is not None
                or self.citation_traceability_valid is not None
                or any(value is not None for value in answer_derived_values)
                or self.citation_results
                or self.structurally_valid
            ):
                msg = "answer contract failures cannot contain downstream evaluation values"
                raise ValueError(msg)
            if failure_stages != {StructuralValidationStage.ANSWER_CONTRACT}:
                msg = "answer contract failures require only answer-contract diagnostics"
                raise ValueError(msg)
            return self

        if self.answer_contract_valid is not True:
            msg = "successful JSON parsing requires an explicit answer-contract result"
            raise ValueError(msg)
        if self.output_contract_valid is None or self.citation_traceability_valid is None:
            msg = "valid answers require output-contract and citation-traceability results"
            raise ValueError(msg)
        if any(value is None for value in required_answer_values):
            msg = "valid answers require all structural counts and abstention state"
            raise ValueError(msg)
        if self.output_contract_valid:
            if self.validation_failures:
                msg = "valid generator outputs cannot contain validation failures"
                raise ValueError(msg)
        elif failure_stages != {StructuralValidationStage.GENERATOR_OUTPUT}:
            msg = "invalid generator outputs require generator-output diagnostics"
            raise ValueError(msg)

        citation_ids = tuple(result.citation_id for result in self.citation_results)
        chunk_ids = tuple(result.chunk_id for result in self.citation_results)
        if len(set(citation_ids)) != len(citation_ids):
            msg = "structural evaluation citation IDs must be unique"
            raise ValueError(msg)
        if len(set(chunk_ids)) != len(chunk_ids):
            msg = "structural evaluation cited chunk IDs must be unique"
            raise ValueError(msg)

        context_positions = {
            chunk_id: position for position, chunk_id in enumerate(self.context_chunk_ids, start=1)
        }
        omitted_chunk_ids = set(self.omitted_chunk_ids)
        for result in self.citation_results:
            if result.resolves_to_included_context:
                expected_position = context_positions.get(result.chunk_id)
                if expected_position is None:
                    msg = "resolved citation results must identify a recorded context chunk"
                    raise ValueError(msg)
                if result.context_position != expected_position:
                    msg = "resolved citation positions must match recorded context order"
                    raise ValueError(msg)
            elif result.reason_codes == (CitationTraceabilityReason.CHUNK_OMITTED,):
                if result.chunk_id not in omitted_chunk_ids:
                    msg = "omitted citation results must identify a recorded omitted chunk"
                    raise ValueError(msg)
            elif result.chunk_id in context_positions or result.chunk_id in omitted_chunk_ids:
                msg = "unknown citation results must identify an unrecorded chunk"
                raise ValueError(msg)

        assert self.claim_ids is not None
        assert self.claim_count is not None
        assert self.citation_count is not None
        assert self.valid_citation_count is not None
        assert self.invalid_citation_count is not None
        assert self.citation_reference_count is not None
        assert self.traceable_citation_reference_count is not None
        assert self.untraceable_citation_reference_count is not None

        if len(set(self.claim_ids)) != len(self.claim_ids):
            msg = "structural evaluation claim IDs must be unique"
            raise ValueError(msg)
        if self.claim_count != len(self.claim_ids):
            msg = "claim_count must match claim_ids"
            raise ValueError(msg)

        if self.is_abstaining and (
            self.claim_ids or self.claim_count != 0 or self.citation_count != 0
        ):
            msg = "abstaining evaluations cannot contain claims or citations"
            raise ValueError(msg)
        if self.is_abstaining is False and self.claim_count < 1:
            msg = "non-abstaining evaluations require at least one claim"
            raise ValueError(msg)
        if self.citation_count != len(self.citation_results):
            msg = "citation_count must match citation_results"
            raise ValueError(msg)

        expected_valid_citations = sum(result.is_valid for result in self.citation_results)
        expected_invalid_citations = self.citation_count - expected_valid_citations
        if self.valid_citation_count != expected_valid_citations:
            msg = "valid_citation_count must match citation_results"
            raise ValueError(msg)
        if self.invalid_citation_count != expected_invalid_citations:
            msg = "invalid_citation_count must match citation_results"
            raise ValueError(msg)

        expected_references = sum(
            len(result.referenced_claim_ids) for result in self.citation_results
        )
        expected_traceable_references = sum(
            len(result.referenced_claim_ids) for result in self.citation_results if result.is_valid
        )
        expected_untraceable_references = expected_references - expected_traceable_references
        if self.citation_reference_count != expected_references:
            msg = "citation_reference_count must match citation_results"
            raise ValueError(msg)
        if self.traceable_citation_reference_count != expected_traceable_references:
            msg = "traceable citation references must match citation_results"
            raise ValueError(msg)
        if self.untraceable_citation_reference_count != expected_untraceable_references:
            msg = "untraceable citation references must match citation_results"
            raise ValueError(msg)

        referenced_claim_ids = {
            claim_id for result in self.citation_results for claim_id in result.referenced_claim_ids
        }
        if not referenced_claim_ids.issubset(self.claim_ids):
            msg = "citation references must identify recorded claim IDs"
            raise ValueError(msg)

        expected_citation_rate = (
            None if self.citation_count == 0 else self.valid_citation_count / self.citation_count
        )
        expected_reference_rate = (
            None
            if self.citation_reference_count == 0
            else self.traceable_citation_reference_count / self.citation_reference_count
        )
        if self.citation_validity_rate != expected_citation_rate:
            msg = "citation_validity_rate must use declared citations as its denominator"
            raise ValueError(msg)
        if self.citation_reference_traceability_rate != expected_reference_rate:
            msg = "citation reference traceability rate must use claim references as denominator"
            raise ValueError(msg)

        expected_traceability = self.invalid_citation_count == 0
        if self.citation_traceability_valid is not expected_traceability:
            msg = "citation traceability must match invalid citation count"
            raise ValueError(msg)
        if self.output_contract_valid is not self.citation_traceability_valid:
            msg = "structural-citation-v1 output validity must match citation traceability"
            raise ValueError(msg)
        expected_structural_validity = (
            self.output_contract_valid and self.citation_traceability_valid
        )
        if self.structurally_valid is not expected_structural_validity:
            msg = "structural validity must require output and citation validity"
            raise ValueError(msg)
        return self


class AggregateStructuralResponseMetrics(EvaluationModel):
    """Nested structural funnel metrics; zero denominators produce ``None``.

    This is a derived value, not a standalone artifact. ``from_responses`` is its construction
    boundary, and the versioned enclosing report recomputes it from embedded responses when
    loaded. These metrics do not assess answer correctness, citation correctness, or citation
    completeness.
    """

    response_count: int = Field(ge=0, strict=True)
    json_parse_success_count: int = Field(ge=0, strict=True)
    json_parse_failure_count: int = Field(ge=0, strict=True)
    json_parse_success_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description="JSON parse successes divided by all response attempts.",
    )
    answer_contract_evaluated_count: int = Field(ge=0, strict=True)
    answer_contract_valid_count: int = Field(ge=0, strict=True)
    answer_contract_invalid_count: int = Field(ge=0, strict=True)
    answer_contract_valid_given_json_parse_success_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description="Valid answer contracts divided by JSON-parsed responses.",
    )
    output_contract_evaluated_count: int = Field(ge=0, strict=True)
    output_contract_valid_count: int = Field(ge=0, strict=True)
    output_contract_invalid_count: int = Field(ge=0, strict=True)
    output_contract_valid_given_valid_answer_contract_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description="Valid generator outputs divided by answer-contract-valid responses.",
    )
    citation_traceability_evaluated_count: int = Field(ge=0, strict=True)
    citation_traceability_valid_response_count: int = Field(ge=0, strict=True)
    citation_traceability_invalid_response_count: int = Field(ge=0, strict=True)
    citation_traceability_valid_given_valid_answer_contract_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description=(
            "Responses with all declared citations traceable divided by "
            "answer-contract-valid responses; this is not citation completeness."
        ),
    )
    structurally_valid_response_count: int = Field(ge=0, strict=True)
    structurally_invalid_response_count: int = Field(ge=0, strict=True)
    end_to_end_structural_validity_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description="Structurally valid responses divided by all response attempts.",
    )
    abstaining_response_count: int = Field(ge=0, strict=True)
    non_abstaining_response_count: int = Field(ge=0, strict=True)
    citation_bearing_response_count: int = Field(ge=0, strict=True)
    zero_citation_response_count: int = Field(ge=0, strict=True)
    non_abstaining_zero_citation_response_count: int = Field(ge=0, strict=True)
    total_claim_count: int = Field(ge=0, strict=True)
    total_citation_count: int = Field(ge=0, strict=True)
    total_valid_citation_count: int = Field(ge=0, strict=True)
    total_invalid_citation_count: int = Field(ge=0, strict=True)
    micro_citation_validity_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description=(
            "Structurally traceable citations divided by declared citations across all "
            "answer-contract-valid responses."
        ),
    )
    total_citation_reference_count: int = Field(ge=0, strict=True)
    total_traceable_citation_reference_count: int = Field(ge=0, strict=True)
    total_untraceable_citation_reference_count: int = Field(ge=0, strict=True)
    micro_citation_reference_traceability_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
        description=("Traceable claim-to-citation references divided by all declared references."),
    )

    @classmethod
    def from_responses(
        cls,
        responses: Sequence[StructuralResponseEvaluation],
    ) -> Self:
        """Compute micro totals and explicitly conditioned stage rates."""
        responses = tuple(
            StructuralResponseEvaluation.model_validate(response) for response in responses
        )
        response_ids = tuple(response.response_id for response in responses)
        if len(set(response_ids)) != len(response_ids):
            msg = "cannot aggregate duplicate structural response IDs"
            raise EvaluationError(msg)
        parsed = tuple(response for response in responses if response.json_parse_succeeded)
        valid_answers = tuple(
            response for response in parsed if response.answer_contract_valid is True
        )
        valid_outputs = tuple(
            response for response in valid_answers if response.output_contract_valid is True
        )
        traceable_responses = tuple(
            response for response in valid_answers if response.citation_traceability_valid is True
        )
        structurally_valid = tuple(
            response for response in responses if response.structurally_valid
        )
        abstaining = tuple(response for response in valid_answers if response.is_abstaining is True)
        non_abstaining = tuple(
            response for response in valid_answers if response.is_abstaining is False
        )
        citation_bearing = tuple(
            response for response in valid_answers if cast(int, response.citation_count) > 0
        )
        zero_citation = tuple(
            response for response in valid_answers if cast(int, response.citation_count) == 0
        )
        non_abstaining_zero_citation = tuple(
            response for response in non_abstaining if cast(int, response.citation_count) == 0
        )

        response_count = len(responses)
        parsed_count = len(parsed)
        valid_answer_count = len(valid_answers)
        valid_output_count = len(valid_outputs)
        traceable_response_count = len(traceable_responses)
        structurally_valid_count = len(structurally_valid)
        total_citation_count = sum(cast(int, response.citation_count) for response in valid_answers)
        total_valid_citation_count = sum(
            cast(int, response.valid_citation_count) for response in valid_answers
        )
        total_citation_reference_count = sum(
            cast(int, response.citation_reference_count) for response in valid_answers
        )
        total_traceable_citation_reference_count = sum(
            cast(int, response.traceable_citation_reference_count) for response in valid_answers
        )

        return cls(
            response_count=response_count,
            json_parse_success_count=parsed_count,
            json_parse_failure_count=response_count - parsed_count,
            json_parse_success_rate=_ratio_or_none(parsed_count, response_count),
            answer_contract_evaluated_count=parsed_count,
            answer_contract_valid_count=valid_answer_count,
            answer_contract_invalid_count=parsed_count - valid_answer_count,
            answer_contract_valid_given_json_parse_success_rate=_ratio_or_none(
                valid_answer_count,
                parsed_count,
            ),
            output_contract_evaluated_count=valid_answer_count,
            output_contract_valid_count=valid_output_count,
            output_contract_invalid_count=valid_answer_count - valid_output_count,
            output_contract_valid_given_valid_answer_contract_rate=_ratio_or_none(
                valid_output_count,
                valid_answer_count,
            ),
            citation_traceability_evaluated_count=valid_answer_count,
            citation_traceability_valid_response_count=traceable_response_count,
            citation_traceability_invalid_response_count=(
                valid_answer_count - traceable_response_count
            ),
            citation_traceability_valid_given_valid_answer_contract_rate=_ratio_or_none(
                traceable_response_count,
                valid_answer_count,
            ),
            structurally_valid_response_count=structurally_valid_count,
            structurally_invalid_response_count=response_count - structurally_valid_count,
            end_to_end_structural_validity_rate=_ratio_or_none(
                structurally_valid_count,
                response_count,
            ),
            abstaining_response_count=len(abstaining),
            non_abstaining_response_count=len(non_abstaining),
            citation_bearing_response_count=len(citation_bearing),
            zero_citation_response_count=len(zero_citation),
            non_abstaining_zero_citation_response_count=len(non_abstaining_zero_citation),
            total_claim_count=sum(cast(int, response.claim_count) for response in valid_answers),
            total_citation_count=total_citation_count,
            total_valid_citation_count=total_valid_citation_count,
            total_invalid_citation_count=(total_citation_count - total_valid_citation_count),
            micro_citation_validity_rate=_ratio_or_none(
                total_valid_citation_count,
                total_citation_count,
            ),
            total_citation_reference_count=total_citation_reference_count,
            total_traceable_citation_reference_count=(total_traceable_citation_reference_count),
            total_untraceable_citation_reference_count=(
                total_citation_reference_count - total_traceable_citation_reference_count
            ),
            micro_citation_reference_traceability_rate=_ratio_or_none(
                total_traceable_citation_reference_count,
                total_citation_reference_count,
            ),
        )


class StructuralResponseAggregateReport(EvaluationModel):
    """Deterministic aggregate with exact per-response structural records.

    Opaque identifiers and content hashes are retained as linkable metadata; callers must
    not place sensitive payloads in identifiers.
    """

    schema_version: Literal["1"] = "1"
    aggregation_version: Literal["structural-response-aggregate-v1"] = (
        "structural-response-aggregate-v1"
    )
    source_evaluator_version: Literal["structural-citation-v1"] = "structural-citation-v1"
    responses: tuple[StructuralResponseEvaluation, ...] = ()
    metrics: AggregateStructuralResponseMetrics

    @model_validator(mode="after")
    def validate_population_and_metrics(self) -> Self:
        """Require unique canonical inputs and metrics recomputed from those inputs."""
        response_ids = tuple(response.response_id for response in self.responses)
        if len(set(response_ids)) != len(response_ids):
            msg = "structural aggregate response IDs must be unique"
            raise ValueError(msg)
        if response_ids != tuple(sorted(response_ids)):
            msg = "structural aggregate responses must be ordered by response_id"
            raise ValueError(msg)
        expected_metrics = AggregateStructuralResponseMetrics.from_responses(self.responses)
        if self.metrics != expected_metrics:
            msg = "structural aggregate metrics must match embedded responses"
            raise ValueError(msg)
        return self

    def as_json_value(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return self.model_dump(mode="json")


def _ratio_or_none(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator
