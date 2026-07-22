"""Pure staged evaluation of raw structured answers and citation traceability."""

import json
from collections.abc import Sequence
from hashlib import sha256
from typing import Any

from pydantic import ValidationError

from rag_pymc.domain import (
    Citation,
    ContextItem,
    GeneratorInput,
    GeneratorOutput,
    GroundedAnswer,
)
from rag_pymc.evaluation.errors import EvaluationError
from rag_pymc.evaluation.models import (
    AggregateStructuralResponseMetrics,
    CitationTraceabilityReason,
    CitationTraceabilityResult,
    StructuralFailureReason,
    StructuralResponseAggregateReport,
    StructuralResponseEvaluation,
    StructuralValidationFailure,
    StructuralValidationStage,
)

_PROVENANCE_REASON_BY_FIELD = {
    "document_id": CitationTraceabilityReason.DOCUMENT_ID_MISMATCH,
    "source_url": CitationTraceabilityReason.SOURCE_URL_MISMATCH,
    "library": CitationTraceabilityReason.LIBRARY_MISMATCH,
    "library_version": CitationTraceabilityReason.LIBRARY_VERSION_MISMATCH,
    "section": CitationTraceabilityReason.SECTION_MISMATCH,
    "api_symbols": CitationTraceabilityReason.API_SYMBOLS_MISMATCH,
}
_KNOWN_ANSWER_LOCATION_SEGMENTS = frozenset(
    {
        "api_symbols",
        "citation_id",
        "citation_ids",
        "citations",
        "chunk_id",
        "claim_id",
        "claims",
        "document_id",
        "heading",
        "is_abstaining",
        "library",
        "library_version",
        "schema_version",
        "section",
        "section_id",
        "sections",
        "source_url",
        "text",
    }
)


class _DuplicateJsonKeyError(ValueError):
    """Signal an ambiguous JSON object without retaining its user-controlled key."""


class _NonFiniteJsonNumberError(ValueError):
    """Signal a non-standard JSON numeric constant without retaining its value."""


def evaluate_structural_response(
    *,
    response_id: str,
    generator_input: GeneratorInput,
    raw_answer_json: str,
) -> StructuralResponseEvaluation:
    """Return staged diagnostics without retaining claims, headings, or query/context text.

    Opaque caller- and provider-controlled identifiers plus linkable hashes remain in the
    record and therefore require the same sensitivity handling as other evaluation metadata.
    """
    trusted_input = GeneratorInput.model_validate(generator_input)
    raw_output_sha256 = sha256(raw_answer_json.encode("utf-8", errors="surrogatepass")).hexdigest()
    common_values: dict[str, Any] = {
        "response_id": response_id,
        "raw_output_sha256": raw_output_sha256,
        "generator_input_sha256": _hash_generator_input_v1(trusted_input),
        "context_chunk_ids": trusted_input.context.included_chunk_ids,
        "omitted_chunk_ids": trusted_input.context.omitted_chunk_ids,
    }

    try:
        raw_answer_json.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        failure = StructuralValidationFailure(
            stage=StructuralValidationStage.JSON_PARSE,
            reason_code=StructuralFailureReason.JSON_PARSE_FAILED,
            error_type="json_invalid_unicode_error",
        )
        return StructuralResponseEvaluation(
            **common_values,
            json_parse_succeeded=False,
            structurally_valid=False,
            validation_failures=(failure,),
        )

    try:
        raw_answer = json.loads(
            raw_answer_json,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_non_finite_json_number,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as error:
        location: tuple[str, ...]
        if isinstance(error, json.JSONDecodeError):
            location = (f"line:{error.lineno}", f"column:{error.colno}")
            error_type = "json_decode_error"
        elif isinstance(error, _DuplicateJsonKeyError):
            location = ()
            error_type = "json_duplicate_key_error"
        elif isinstance(error, _NonFiniteJsonNumberError):
            location = ()
            error_type = "json_non_finite_number_error"
        elif isinstance(error, RecursionError):
            location = ()
            error_type = "json_recursion_error"
        else:
            location = ()
            error_type = "json_value_error"
        failure = StructuralValidationFailure(
            stage=StructuralValidationStage.JSON_PARSE,
            reason_code=StructuralFailureReason.JSON_PARSE_FAILED,
            location=location,
            error_type=error_type,
        )
        return StructuralResponseEvaluation(
            **common_values,
            json_parse_succeeded=False,
            structurally_valid=False,
            validation_failures=(failure,),
        )

    try:
        answer = GroundedAnswer.model_validate(raw_answer)
    except ValidationError as error:
        return StructuralResponseEvaluation(
            **common_values,
            json_parse_succeeded=True,
            answer_contract_valid=False,
            structurally_valid=False,
            validation_failures=_normalize_validation_failures(
                error,
                stage=StructuralValidationStage.ANSWER_CONTRACT,
                reason_code=StructuralFailureReason.ANSWER_CONTRACT_VALIDATION_FAILED,
            ),
        )

    citation_results = _evaluate_citations(answer, trusted_input)
    try:
        GeneratorOutput(generator_input=trusted_input, answer=answer)
    except ValidationError as error:
        output_contract_valid = False
        validation_failures = _normalize_validation_failures(
            error,
            stage=StructuralValidationStage.GENERATOR_OUTPUT,
            reason_code=StructuralFailureReason.GENERATOR_OUTPUT_CONTRACT_VALIDATION_FAILED,
        )
    else:
        output_contract_valid = True
        validation_failures = ()

    claims = tuple(claim for section in answer.sections for claim in section.claims)
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
    citation_traceability_valid = invalid_citation_count == 0

    return StructuralResponseEvaluation(
        **common_values,
        json_parse_succeeded=True,
        answer_contract_valid=True,
        output_contract_valid=output_contract_valid,
        citation_traceability_valid=citation_traceability_valid,
        structurally_valid=output_contract_valid and citation_traceability_valid,
        is_abstaining=answer.is_abstaining,
        claim_ids=tuple(claim.claim_id for claim in claims),
        claim_count=len(claims),
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


def aggregate_structural_responses(
    responses: Sequence[StructuralResponseEvaluation],
) -> StructuralResponseAggregateReport:
    """Return an order-invariant aggregate over revalidated response records."""
    validated = tuple(
        StructuralResponseEvaluation.model_validate(response) for response in responses
    )
    ordered = tuple(sorted(validated, key=lambda response: response.response_id))
    response_ids = tuple(response.response_id for response in ordered)
    if len(set(response_ids)) != len(response_ids):
        msg = "cannot aggregate duplicate structural response IDs"
        raise EvaluationError(msg)
    return StructuralResponseAggregateReport(
        responses=ordered,
        metrics=AggregateStructuralResponseMetrics.from_responses(ordered),
    )


def _hash_generator_input_v1(generator_input: GeneratorInput) -> str:
    canonical_json = json.dumps(
        generator_input.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_json.encode("ascii")).hexdigest()


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError
        result[key] = value
    return result


def _reject_non_finite_json_number(_: str) -> None:
    raise _NonFiniteJsonNumberError


def _evaluate_citations(
    answer: GroundedAnswer,
    generator_input: GeneratorInput,
) -> tuple[CitationTraceabilityResult, ...]:
    references_by_citation_id: dict[str, list[str]] = {
        citation.citation_id: [] for citation in answer.citations
    }
    for section in answer.sections:
        for claim in section.claims:
            for citation_id in claim.citation_ids:
                references_by_citation_id[citation_id].append(claim.claim_id)

    context = generator_input.context
    items_by_chunk_id = {item.chunk_id: item for item in context.items}
    omitted_chunk_ids = set(context.omitted_chunk_ids)
    return tuple(
        _evaluate_citation(
            citation,
            referenced_claim_ids=tuple(sorted(references_by_citation_id[citation.citation_id])),
            items_by_chunk_id=items_by_chunk_id,
            omitted_chunk_ids=omitted_chunk_ids,
        )
        for citation in answer.citations
    )


def _evaluate_citation(
    citation: Citation,
    *,
    referenced_claim_ids: tuple[str, ...],
    items_by_chunk_id: dict[str, ContextItem],
    omitted_chunk_ids: set[str],
) -> CitationTraceabilityResult:
    if citation.chunk_id in omitted_chunk_ids:
        return CitationTraceabilityResult(
            citation_id=citation.citation_id,
            chunk_id=citation.chunk_id,
            referenced_claim_ids=referenced_claim_ids,
            resolves_to_included_context=False,
            provenance_matches=None,
            is_valid=False,
            reason_codes=(CitationTraceabilityReason.CHUNK_OMITTED,),
        )

    context_item = items_by_chunk_id.get(citation.chunk_id)
    if context_item is None:
        return CitationTraceabilityResult(
            citation_id=citation.citation_id,
            chunk_id=citation.chunk_id,
            referenced_claim_ids=referenced_claim_ids,
            resolves_to_included_context=False,
            provenance_matches=None,
            is_valid=False,
            reason_codes=(CitationTraceabilityReason.CHUNK_NOT_IN_CONTEXT,),
        )

    reasons = tuple(
        sorted(
            (
                reason
                for field, reason in _PROVENANCE_REASON_BY_FIELD.items()
                if getattr(citation, field) != getattr(context_item, field)
            ),
            key=lambda reason: reason.value,
        )
    )
    provenance_matches = not reasons
    return CitationTraceabilityResult(
        citation_id=citation.citation_id,
        chunk_id=citation.chunk_id,
        referenced_claim_ids=referenced_claim_ids,
        context_position=context_item.position,
        resolves_to_included_context=True,
        provenance_matches=provenance_matches,
        is_valid=provenance_matches,
        reason_codes=reasons,
    )


def _normalize_validation_failures(
    error: ValidationError,
    *,
    stage: StructuralValidationStage,
    reason_code: StructuralFailureReason,
) -> tuple[StructuralValidationFailure, ...]:
    diagnostic_counts: dict[tuple[tuple[str, ...], str], int] = {}
    for detail in error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    ):
        key = (
            tuple(_normalize_location_segment(segment) for segment in detail["loc"]),
            str(detail["type"]),
        )
        diagnostic_counts[key] = diagnostic_counts.get(key, 0) + 1
    return tuple(
        StructuralValidationFailure(
            stage=stage,
            reason_code=reason_code,
            location=location,
            error_type=error_type,
            occurrences=diagnostic_counts[(location, error_type)],
        )
        for location, error_type in sorted(diagnostic_counts)
    )


def _normalize_location_segment(segment: str | int) -> str:
    if isinstance(segment, int):
        return f"[{segment}]"
    if segment in _KNOWN_ANSWER_LOCATION_SEGMENTS:
        return segment
    return "<unrecognized-field>"
