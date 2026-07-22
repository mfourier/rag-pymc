import pytest
from pydantic import ValidationError

from rag_pymc.domain import EvidenceAssessment, EvidenceSufficiency


def make_assessment(**overrides: object) -> EvidenceAssessment:
    values: dict[str, object] = {
        "policy_version": "conservative-no-threshold-v1",
        "sufficiency": EvidenceSufficiency.NOT_ASSESSED,
        "should_abstain": True,
        "reason_codes": (
            "context_budget_omitted_candidates",
            "semantic_sufficiency_not_assessed",
        ),
        "context_chunk_ids": ("chunk_a", "chunk_b"),
        "omitted_chunk_ids": ("chunk_c",),
    }
    values.update(overrides)
    return EvidenceAssessment.model_validate(values)


def test_evidence_assessment_has_stable_status_values_and_json() -> None:
    assessment = make_assessment()
    serialized = assessment.model_dump_json()
    restored = EvidenceAssessment.model_validate_json(serialized)

    assert tuple(EvidenceSufficiency) == (
        EvidenceSufficiency.SUFFICIENT,
        EvidenceSufficiency.INSUFFICIENT,
        EvidenceSufficiency.NOT_ASSESSED,
    )
    assert tuple(status.value for status in EvidenceSufficiency) == (
        "sufficient",
        "insufficient",
        "not_assessed",
    )
    assert assessment.schema_version == "1"
    assert assessment.reason_codes == tuple(sorted(assessment.reason_codes))
    assert restored == assessment
    assert restored.model_dump_json() == serialized


@pytest.mark.parametrize(
    ("sufficiency", "should_abstain", "context_chunk_ids"),
    [
        (EvidenceSufficiency.SUFFICIENT, False, ("chunk_a",)),
        (EvidenceSufficiency.INSUFFICIENT, True, ()),
        (EvidenceSufficiency.NOT_ASSESSED, True, ("chunk_a",)),
    ],
)
def test_evidence_assessment_accepts_the_canonical_abstention_mapping(
    sufficiency: EvidenceSufficiency,
    should_abstain: bool,
    context_chunk_ids: tuple[str, ...],
) -> None:
    assessment = make_assessment(
        sufficiency=sufficiency,
        should_abstain=should_abstain,
        reason_codes=("policy_reason",),
        context_chunk_ids=context_chunk_ids,
        omitted_chunk_ids=(),
    )

    assert assessment.should_abstain is should_abstain


@pytest.mark.parametrize(
    ("sufficiency", "should_abstain"),
    [
        (EvidenceSufficiency.SUFFICIENT, True),
        (EvidenceSufficiency.INSUFFICIENT, False),
        (EvidenceSufficiency.NOT_ASSESSED, False),
    ],
)
def test_evidence_assessment_rejects_inconsistent_abstention_mapping(
    sufficiency: EvidenceSufficiency,
    should_abstain: bool,
) -> None:
    with pytest.raises(ValidationError, match="should_abstain must be true unless"):
        make_assessment(sufficiency=sufficiency, should_abstain=should_abstain)


@pytest.mark.parametrize(
    "sufficiency",
    [EvidenceSufficiency.SUFFICIENT, EvidenceSufficiency.NOT_ASSESSED],
)
def test_evidence_assessment_requires_context_for_sufficient_or_unassessed_statuses(
    sufficiency: EvidenceSufficiency,
) -> None:
    with pytest.raises(ValidationError, match="require context chunk IDs"):
        make_assessment(
            sufficiency=sufficiency,
            should_abstain=sufficiency is not EvidenceSufficiency.SUFFICIENT,
            context_chunk_ids=(),
            omitted_chunk_ids=("chunk_a",),
        )


@pytest.mark.parametrize(
    ("reason_codes", "message"),
    [
        ((), "at least 1 item"),
        (("duplicate", "duplicate"), "reason codes must be unique"),
        (("zeta", "alpha"), "reason codes must be lexicographically ordered"),
        (("",), "reason_codes.0"),
    ],
)
def test_evidence_assessment_rejects_invalid_reason_codes(
    reason_codes: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        make_assessment(reason_codes=reason_codes)


@pytest.mark.parametrize(
    ("context_chunk_ids", "omitted_chunk_ids", "message"),
    [
        (("chunk_a", "chunk_a"), (), "context chunk IDs must be unique"),
        (("chunk_a",), ("chunk_b", "chunk_b"), "omitted chunk IDs must be unique"),
        (("chunk_a",), ("chunk_a",), "must not overlap"),
    ],
)
def test_evidence_assessment_rejects_invalid_chunk_identity(
    context_chunk_ids: tuple[str, ...],
    omitted_chunk_ids: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        make_assessment(
            context_chunk_ids=context_chunk_ids,
            omitted_chunk_ids=omitted_chunk_ids,
        )


@pytest.mark.parametrize("field", ["score", "threshold", "confidence", "generated_at"])
def test_evidence_assessment_forbids_unversioned_decision_signals(field: str) -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        make_assessment(**{field: 0.5})


def test_evidence_assessment_is_immutable() -> None:
    assessment = make_assessment()

    with pytest.raises(ValidationError, match="frozen"):
        assessment.should_abstain = False
