"""Repository-local contracts for Phase 5 annotation and gold-evidence evaluation."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import AnyUrl, AwareDatetime, Field, field_validator, model_validator

from rag_pymc.domain import Difficulty, EvidenceSufficiency, SourceType
from rag_pymc.evaluation._model_base import (
    EvaluationModel,
    NonEmptyString,
    Sha256,
    _canonicalize_unique_strings,
)
from rag_pymc.evaluation.errors import EvaluationError

type Phase5SingleReviewGovernanceSha256 = Literal[
    "a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264"
]
type Phase5SingleReviewCandidateSha256 = Literal[
    "832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb"
]
type Phase5SingleReviewCorpusSha256 = Literal[
    "af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2"
]
_PHASE5_SINGLE_REVIEW_GOVERNANCE_DECIDED_AT = datetime(2026, 7, 26, 4, 14, 51, tzinfo=UTC)


class AnnotationProvenance(EvaluationModel):
    """Human annotation provenance without directly identifying annotators."""

    method: Literal["human"] = "human"
    annotator_ids: tuple[NonEmptyString, ...] = Field(min_length=1)
    guideline_version: NonEmptyString
    batch_id: NonEmptyString
    annotated_at: AwareDatetime

    @field_validator("annotator_ids")
    @classmethod
    def canonicalize_annotator_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Store unique opaque annotator identities in canonical order."""
        return _canonicalize_unique_strings(values, label="annotation annotator IDs")


class AdjudicationProvenance(EvaluationModel):
    """Human acceptance provenance for one completed annotation decision."""

    method: Literal["human"] = "human"
    status: Literal["accepted"] = "accepted"
    adjudicator_ids: tuple[NonEmptyString, ...] = Field(min_length=1)
    guideline_version: NonEmptyString
    batch_id: NonEmptyString
    adjudicated_at: AwareDatetime

    @field_validator("adjudicator_ids")
    @classmethod
    def canonicalize_adjudicator_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Store unique opaque adjudicator identities in canonical order."""
        return _canonicalize_unique_strings(values, label="adjudication adjudicator IDs")


class GoldEvidenceSupportSet(EvaluationModel):
    """One minimal set of corpus chunks that jointly supports an atomic gold claim."""

    chunk_ids: tuple[NonEmptyString, ...] = Field(min_length=1)

    @field_validator("chunk_ids")
    @classmethod
    def canonicalize_chunk_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Store one nonredundant support-set identity in canonical order."""
        return _canonicalize_unique_strings(
            values,
            label="gold evidence support-set chunk IDs",
        )


class AtomicGoldClaim(EvaluationModel):
    """One corpus-supported claim with alternative minimal evidence-support sets."""

    claim_id: NonEmptyString
    text: NonEmptyString
    support_sets: tuple[GoldEvidenceSupportSet, ...] = Field(min_length=1)

    @field_validator("support_sets")
    @classmethod
    def canonicalize_support_sets(
        cls,
        values: tuple[GoldEvidenceSupportSet, ...],
    ) -> tuple[GoldEvidenceSupportSet, ...]:
        """Store unique alternative support sets in canonical order."""
        chunk_id_tuples = tuple(support_set.chunk_ids for support_set in values)
        if len(set(chunk_id_tuples)) != len(chunk_id_tuples):
            msg = "atomic gold claim support sets must be unique"
            raise ValueError(msg)
        return tuple(sorted(values, key=lambda support_set: support_set.chunk_ids))

    @model_validator(mode="after")
    def support_sets_must_form_minimal_antichain(self) -> Self:
        """Reject syntactically nonminimal alternative support sets."""
        chunk_id_tuples = tuple(support_set.chunk_ids for support_set in self.support_sets)
        support_id_sets = tuple(set(chunk_ids) for chunk_ids in chunk_id_tuples)
        for index, candidate in enumerate(support_id_sets):
            if any(
                alternative < candidate
                for alternative_index, alternative in enumerate(support_id_sets)
                if alternative_index != index
            ):
                msg = "atomic gold claim support sets must form a minimal antichain"
                raise ValueError(msg)
        return self


class Phase5DevelopmentExample(EvaluationModel):
    """One adjudicated corpus-level Phase 5 development annotation."""

    schema_version: Literal["phase5-development-annotation-v1"] = "phase5-development-annotation-v1"
    query_id: NonEmptyString
    query_text: NonEmptyString
    query_family: NonEmptyString
    template_family: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    corpus_answerable: bool = Field(strict=True)
    intent: NonEmptyString
    difficulty: Difficulty
    hard_negative_category: NonEmptyString | None = None
    expected_api_symbols: tuple[NonEmptyString, ...] = ()
    gold_claims: tuple[AtomicGoldClaim, ...] = ()
    annotation: AnnotationProvenance
    adjudication: AdjudicationProvenance

    @field_validator("expected_api_symbols")
    @classmethod
    def canonicalize_expected_api_symbols(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Store unique expected API symbols in canonical order."""
        return _canonicalize_unique_strings(values, label="Phase 5 expected API symbols")

    @model_validator(mode="after")
    def validate_corpus_annotation(self) -> Self:
        """Separate corpus answerability from runtime inference and preserve identity."""
        claim_ids = tuple(claim.claim_id for claim in self.gold_claims)
        if len(set(claim_ids)) != len(claim_ids):
            msg = "Phase 5 gold claim IDs must be unique within an example"
            raise ValueError(msg)

        if self.corpus_answerable:
            if not self.gold_claims:
                msg = "corpus-answerable Phase 5 examples require at least one gold claim"
                raise ValueError(msg)
            if self.hard_negative_category is not None:
                msg = "corpus-answerable Phase 5 examples cannot be hard negatives"
                raise ValueError(msg)
        elif self.gold_claims:
            msg = "corpus-unanswerable Phase 5 examples cannot contain gold claims"
            raise ValueError(msg)

        if self.adjudication.adjudicated_at < self.annotation.annotated_at:
            msg = "Phase 5 adjudication must not precede annotation"
            raise ValueError(msg)
        if set(self.annotation.annotator_ids) & set(self.adjudication.adjudicator_ids):
            msg = "Phase 5 adjudicators must be independent from annotators"
            raise ValueError(msg)
        return self


class Phase5DevelopmentCandidate(EvaluationModel):
    """One agent-authored proposal awaiting review under the selected governance."""

    schema_version: Literal["phase5-development-candidate-v1"] = "phase5-development-candidate-v1"
    candidate_status: Literal["draft"] = "draft"
    candidate_author: Literal["agent"] = "agent"
    preregistration_id: Literal["phase5-development-batch-preregistration-v1"]
    batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    slot_id: NonEmptyString
    query_id: NonEmptyString
    query_text: NonEmptyString
    query_family: NonEmptyString
    template_family: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    proposed_corpus_answerable: bool = Field(strict=True)
    intent: NonEmptyString
    difficulty: Difficulty
    hard_negative_category: NonEmptyString | None = None
    expected_api_symbols: tuple[NonEmptyString, ...] = ()
    proposed_gold_claims: tuple[AtomicGoldClaim, ...] = ()

    @field_validator("expected_api_symbols")
    @classmethod
    def canonicalize_expected_api_symbols(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Store unique expected symbols in canonical order."""
        return _canonicalize_unique_strings(values, label="Phase 5 candidate expected API symbols")

    @model_validator(mode="after")
    def validate_proposal(self) -> Self:
        """Keep draft proposals distinct from accepted human annotation semantics."""
        claim_ids = tuple(claim.claim_id for claim in self.proposed_gold_claims)
        if len(set(claim_ids)) != len(claim_ids):
            msg = "Phase 5 candidate claim IDs must be unique within an example"
            raise ValueError(msg)

        if self.proposed_corpus_answerable:
            if not self.proposed_gold_claims:
                msg = "answerable Phase 5 candidates require at least one proposed gold claim"
                raise ValueError(msg)
            if self.hard_negative_category is not None:
                msg = "answerable Phase 5 candidates cannot be hard negatives"
                raise ValueError(msg)
        else:
            if self.proposed_gold_claims:
                msg = "unanswerable Phase 5 candidates cannot contain proposed gold claims"
                raise ValueError(msg)
            if self.hard_negative_category is None:
                msg = "unanswerable Phase 5 candidates require a hard-negative category"
                raise ValueError(msg)
        return self


class Phase5DevelopmentCandidateBatch(EvaluationModel):
    """One exact agent-draft JSONL batch kept outside the accepted development dataset."""

    schema_version: Literal["phase5-development-candidate-batch-v1"] = (
        "phase5-development-candidate-batch-v1"
    )
    dataset_role: Literal["candidate-draft"] = "candidate-draft"
    dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    dataset_sha256: Sha256
    preregistration_id: Literal["phase5-development-batch-preregistration-v1"]
    batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    candidates: tuple[Phase5DevelopmentCandidate, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_batch_identity(self) -> Self:
        """Require unique draft identities under one approved preregistration and corpus."""
        slot_ids = tuple(candidate.slot_id for candidate in self.candidates)
        query_ids = tuple(candidate.query_id for candidate in self.candidates)
        claim_ids = tuple(
            claim.claim_id
            for candidate in self.candidates
            for claim in candidate.proposed_gold_claims
        )
        for label, identities in (
            ("slot IDs", slot_ids),
            ("query IDs", query_ids),
            ("claim IDs", claim_ids),
        ):
            if len(set(identities)) != len(identities):
                msg = f"Phase 5 candidate batch requires globally unique {label}"
                raise ValueError(msg)

        if any(
            candidate.preregistration_id != self.preregistration_id
            or candidate.batch_id != self.batch_id
            or candidate.corpus_hash_policy != self.corpus_hash_policy
            or candidate.corpus_sha256 != self.corpus_sha256
            for candidate in self.candidates
        ):
            msg = "Phase 5 candidates must share the batch preregistration and corpus identity"
            raise ValueError(msg)
        return self


class Phase5DevelopmentDataset(EvaluationModel):
    """A loaded Phase 5 development file bound to exact bytes and one corpus."""

    schema_version: Literal["phase5-development-dataset-v1"] = "phase5-development-dataset-v1"
    dataset_role: Literal["development"] = "development"
    dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    dataset_sha256: Sha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    examples: tuple[Phase5DevelopmentExample, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dataset_identity_and_corpus(self) -> Self:
        """Require globally unique identities and a single corpus namespace."""
        query_ids = tuple(example.query_id for example in self.examples)
        if len(set(query_ids)) != len(query_ids):
            msg = "Phase 5 development query IDs must be unique"
            raise ValueError(msg)

        claim_ids = tuple(
            claim.claim_id for example in self.examples for claim in example.gold_claims
        )
        if len(set(claim_ids)) != len(claim_ids):
            msg = "Phase 5 development gold claim IDs must be globally unique"
            raise ValueError(msg)

        if any(example.corpus_sha256 != self.corpus_sha256 for example in self.examples):
            msg = "Phase 5 development examples must share the dataset corpus SHA-256"
            raise ValueError(msg)
        return self


class Phase5DevelopmentCorpusValidation(EvaluationModel):
    """Audit record binding development annotations to an exact available corpus."""

    schema_version: Literal["1"] = "1"
    validator_version: Literal["phase5-development-corpus-v1"] = "phase5-development-corpus-v1"
    dataset_sha256: Sha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    corpus_chunk_count: int = Field(ge=1, strict=True)
    query_count: int = Field(ge=1, strict=True)
    answerable_query_count: int = Field(ge=0, strict=True)
    gold_claim_count: int = Field(ge=0, strict=True)
    gold_support_set_count: int = Field(ge=0, strict=True)
    referenced_chunk_ids: tuple[NonEmptyString, ...] = ()
    referenced_chunk_count: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def validate_counts_and_identity(self) -> Self:
        """Require canonical referenced identities and their derived count."""
        if len(set(self.referenced_chunk_ids)) != len(self.referenced_chunk_ids):
            msg = "development corpus referenced chunk IDs must be unique"
            raise ValueError(msg)
        if self.referenced_chunk_ids != tuple(sorted(self.referenced_chunk_ids)):
            msg = "development corpus referenced chunk IDs must be ordered"
            raise ValueError(msg)
        if self.referenced_chunk_count != len(self.referenced_chunk_ids):
            msg = "referenced_chunk_count must match referenced_chunk_ids"
            raise ValueError(msg)
        if self.answerable_query_count > self.query_count:
            msg = "answerable_query_count cannot exceed query_count"
            raise ValueError(msg)
        if self.gold_claim_count == 0 and self.gold_support_set_count != 0:
            msg = "a development corpus without gold claims cannot have support sets"
            raise ValueError(msg)
        if self.answerable_query_count == 0 and self.gold_claim_count != 0:
            msg = "a development corpus without answerable queries cannot have gold claims"
            raise ValueError(msg)
        if self.gold_claim_count < self.answerable_query_count:
            msg = "every answerable development query requires at least one gold claim"
            raise ValueError(msg)
        if self.gold_support_set_count < self.gold_claim_count:
            msg = "every development gold claim requires at least one support set"
            raise ValueError(msg)
        if self.gold_claim_count > 0 and self.referenced_chunk_count == 0:
            msg = "development gold claims require referenced chunks"
            raise ValueError(msg)
        if self.referenced_chunk_count > self.corpus_chunk_count:
            msg = "referenced chunk count cannot exceed corpus chunk count"
            raise ValueError(msg)
        return self


class Phase5SingleReviewRevisedContent(EvaluationModel):
    """Human-revised semantic fields for one Phase 5 candidate."""

    query_text: NonEmptyString
    corpus_answerable: bool = Field(strict=True)
    hard_negative_category: NonEmptyString | None = None
    gold_claims: tuple[AtomicGoldClaim, ...] = ()

    @model_validator(mode="after")
    def validate_reviewed_content(self) -> Self:
        """Require internally complete claims or an explicit hard-negative category."""
        claim_ids = tuple(claim.claim_id for claim in self.gold_claims)
        if len(set(claim_ids)) != len(claim_ids):
            msg = "Phase 5 single-review gold claim IDs must be unique within an example"
            raise ValueError(msg)
        if self.corpus_answerable:
            if not self.gold_claims:
                msg = "corpus-answerable Phase 5 single-review content requires gold claims"
                raise ValueError(msg)
            if self.hard_negative_category is not None:
                msg = "corpus-answerable Phase 5 single-review content cannot be a hard negative"
                raise ValueError(msg)
        else:
            if self.gold_claims:
                msg = "corpus-unanswerable Phase 5 single-review content cannot contain claims"
                raise ValueError(msg)
            if self.hard_negative_category is None:
                msg = (
                    "corpus-unanswerable Phase 5 single-review content requires a "
                    "hard-negative category"
                )
                raise ValueError(msg)
        return self


class Phase5SingleReviewDecision(EvaluationModel):
    """One pending or completed decision by the governed single human reviewer."""

    schema_version: Literal["phase5-development-single-review-decision-v1"] = (
        "phase5-development-single-review-decision-v1"
    )
    artifact_role: Literal["single-human-review-record"] = "single-human-review-record"
    dataset_role: Literal["development-single-review-exploratory"] = (
        "development-single-review-exploratory"
    )
    governance_id: Literal["phase5-development-single-review-governance-v1"]
    governance_sha256: Phase5SingleReviewGovernanceSha256
    candidate_batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    candidate_batch_sha256: Phase5SingleReviewCandidateSha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Phase5SingleReviewCorpusSha256
    reviewer_id: Literal["sr_001"]
    query_id: NonEmptyString
    query_review: Literal["pending", "accepted", "revised", "rejected", "unresolved"]
    corpus_answerability_review: Literal["pending", "accepted", "revised", "rejected", "unresolved"]
    claims_review: Literal["pending", "accepted", "revised", "rejected", "unresolved"]
    support_sets_review: Literal["pending", "accepted", "revised", "rejected", "unresolved"]
    leakage_review: Literal["pending", "confirmed-distinct", "duplicate", "unresolved"]
    hard_negative_review: Literal[
        "pending", "confirmed", "not-applicable", "revised", "rejected", "unresolved"
    ]
    final_status: Literal[
        "pending", "accepted-as-proposed", "accepted-with-revisions", "rejected", "unresolved"
    ]
    reviewed_at: AwareDatetime | None = None
    review_notes: NonEmptyString | None = None
    revised_content: Phase5SingleReviewRevisedContent | None = None

    @model_validator(mode="after")
    def validate_decision_state(self) -> Self:
        """Keep draft forms and completed human decisions unambiguously separate."""
        component_reviews = (
            self.query_review,
            self.corpus_answerability_review,
            self.claims_review,
            self.support_sets_review,
        )
        all_review_values = (*component_reviews, self.leakage_review, self.hard_negative_review)
        if self.final_status == "pending":
            _validate_pending_single_review_decision(self, all_review_values)
            return self

        _validate_completed_single_review_base(self, all_review_values)
        if self.final_status == "accepted-as-proposed":
            _validate_accepted_as_proposed(self, component_reviews)
        elif self.final_status == "accepted-with-revisions":
            _validate_accepted_with_revisions(self, component_reviews)
        elif self.final_status == "rejected":
            _validate_rejected_single_review(self, component_reviews)
        else:
            _validate_unresolved_single_review(self, component_reviews)
        return self


def _validate_pending_single_review_decision(
    decision: Phase5SingleReviewDecision,
    review_values: tuple[str, ...],
) -> None:
    if any(value != "pending" for value in review_values):
        msg = "pending Phase 5 single-review records require every review field pending"
        raise ValueError(msg)
    if (
        decision.reviewed_at is not None
        or decision.review_notes is not None
        or decision.revised_content is not None
    ):
        msg = "pending Phase 5 single-review records cannot contain human decisions"
        raise ValueError(msg)


def _validate_completed_single_review_base(
    decision: Phase5SingleReviewDecision,
    review_values: tuple[str, ...],
) -> None:
    if "pending" in review_values:
        msg = "completed Phase 5 single-review records cannot contain pending review fields"
        raise ValueError(msg)
    if decision.reviewed_at is None:
        msg = "completed Phase 5 single-review records require a real UTC timestamp"
        raise ValueError(msg)
    if decision.reviewed_at.utcoffset() != timedelta(0):
        msg = "Phase 5 single-review timestamps must use UTC"
        raise ValueError(msg)
    if decision.reviewed_at < _PHASE5_SINGLE_REVIEW_GOVERNANCE_DECIDED_AT:
        msg = "Phase 5 single-review timestamps must not precede the governance decision"
        raise ValueError(msg)


def _validate_accepted_as_proposed(
    decision: Phase5SingleReviewDecision,
    component_reviews: tuple[str, ...],
) -> None:
    if component_reviews != ("accepted",) * 4:
        msg = "accepted-as-proposed records require explicit acceptance of every component"
        raise ValueError(msg)
    if decision.leakage_review != "confirmed-distinct":
        msg = "accepted Phase 5 single-review records require confirmed leakage review"
        raise ValueError(msg)
    if decision.hard_negative_review not in {"confirmed", "not-applicable"}:
        msg = "accepted-as-proposed records require a final hard-negative review"
        raise ValueError(msg)
    if decision.revised_content is not None:
        msg = "accepted-as-proposed records cannot contain revised content"
        raise ValueError(msg)


def _validate_accepted_with_revisions(
    decision: Phase5SingleReviewDecision,
    component_reviews: tuple[str, ...],
) -> None:
    if any(value not in {"accepted", "revised"} for value in component_reviews):
        msg = "accepted-with-revisions records require accepted or revised components"
        raise ValueError(msg)
    if "revised" not in component_reviews:
        msg = "accepted-with-revisions records must identify a revised component"
        raise ValueError(msg)
    if decision.leakage_review != "confirmed-distinct":
        msg = "accepted Phase 5 single-review records require confirmed leakage review"
        raise ValueError(msg)
    if decision.hard_negative_review not in {"confirmed", "not-applicable", "revised"}:
        msg = "accepted-with-revisions records require a final hard-negative review"
        raise ValueError(msg)
    if decision.revised_content is None:
        msg = "accepted-with-revisions records require complete revised content"
        raise ValueError(msg)


def _validate_rejected_single_review(
    decision: Phase5SingleReviewDecision,
    component_reviews: tuple[str, ...],
) -> None:
    rejected = "rejected" in component_reviews or decision.leakage_review == "duplicate"
    rejected = rejected or decision.hard_negative_review == "rejected"
    if not rejected:
        msg = "rejected Phase 5 single-review records require an explicit rejection"
        raise ValueError(msg)
    if decision.review_notes is None:
        msg = "rejected Phase 5 single-review records require concise review notes"
        raise ValueError(msg)
    if decision.revised_content is not None:
        msg = "rejected Phase 5 single-review records cannot enter reviewed content"
        raise ValueError(msg)


def _validate_unresolved_single_review(
    decision: Phase5SingleReviewDecision,
    component_reviews: tuple[str, ...],
) -> None:
    unresolved = "unresolved" in component_reviews
    unresolved = unresolved or decision.leakage_review == "unresolved"
    unresolved = unresolved or decision.hard_negative_review == "unresolved"
    if not unresolved:
        msg = "unresolved Phase 5 single-review records require an unresolved field"
        raise ValueError(msg)
    if decision.review_notes is None:
        msg = "unresolved Phase 5 single-review records require concise review notes"
        raise ValueError(msg)
    if decision.revised_content is not None:
        msg = "unresolved Phase 5 single-review records cannot enter reviewed content"
        raise ValueError(msg)


class Phase5SingleReviewDecisionBatch(EvaluationModel):
    """Exact-byte identity and shared provenance for one single-review decision JSONL."""

    schema_version: Literal["phase5-development-single-review-decision-batch-v1"] = (
        "phase5-development-single-review-decision-batch-v1"
    )
    artifact_role: Literal["single-human-review-records"] = "single-human-review-records"
    dataset_role: Literal["development-single-review-exploratory"] = (
        "development-single-review-exploratory"
    )
    hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    decisions_sha256: Sha256
    governance_id: Literal["phase5-development-single-review-governance-v1"]
    governance_sha256: Phase5SingleReviewGovernanceSha256
    candidate_batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    candidate_batch_sha256: Phase5SingleReviewCandidateSha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Phase5SingleReviewCorpusSha256
    reviewer_id: Literal["sr_001"]
    decisions: tuple[Phase5SingleReviewDecision, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_decision_batch(self) -> Self:
        """Require sorted unique decisions under one fixed governance boundary."""
        query_ids = tuple(decision.query_id for decision in self.decisions)
        if len(set(query_ids)) != len(query_ids):
            msg = "Phase 5 single-review decision query IDs must be unique"
            raise ValueError(msg)
        if query_ids != tuple(sorted(query_ids)):
            msg = "Phase 5 single-review decisions must be ordered by query ID"
            raise ValueError(msg)
        if any(
            decision.dataset_role != self.dataset_role
            or decision.governance_id != self.governance_id
            or decision.governance_sha256 != self.governance_sha256
            or decision.candidate_batch_id != self.candidate_batch_id
            or decision.candidate_batch_sha256 != self.candidate_batch_sha256
            or decision.corpus_hash_policy != self.corpus_hash_policy
            or decision.corpus_sha256 != self.corpus_sha256
            or decision.reviewer_id != self.reviewer_id
            for decision in self.decisions
        ):
            msg = "Phase 5 single-review decisions must share exact governance and corpus identity"
            raise ValueError(msg)
        return self


class Phase5SingleReviewProvenance(EvaluationModel):
    """One-human provenance that never claims independent adjudication."""

    method: Literal["human-single-review"] = "human-single-review"
    outcome: Literal["accepted-as-proposed", "accepted-with-revisions"]
    governance_id: Literal["phase5-development-single-review-governance-v1"]
    governance_sha256: Phase5SingleReviewGovernanceSha256
    candidate_batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    candidate_batch_sha256: Phase5SingleReviewCandidateSha256
    decisions_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    decisions_sha256: Sha256
    reviewer_id: Literal["sr_001"]
    reviewed_at: AwareDatetime

    @model_validator(mode="after")
    def require_utc_timestamp(self) -> Self:
        """Reject local offsets even when they identify an equivalent UTC instant."""
        if self.reviewed_at.utcoffset() != timedelta(0):
            msg = "Phase 5 single-review timestamps must use UTC"
            raise ValueError(msg)
        if self.reviewed_at < _PHASE5_SINGLE_REVIEW_GOVERNANCE_DECIDED_AT:
            msg = "Phase 5 single-review timestamps must not precede the governance decision"
            raise ValueError(msg)
        return self


class Phase5SingleReviewExample(EvaluationModel):
    """One accepted example from a governed single-human exploratory review."""

    schema_version: Literal["phase5-development-single-review-example-v1"] = (
        "phase5-development-single-review-example-v1"
    )
    dataset_role: Literal["development-single-review-exploratory"] = (
        "development-single-review-exploratory"
    )
    slot_id: NonEmptyString
    query_id: NonEmptyString
    query_text: NonEmptyString
    query_family: NonEmptyString
    template_family: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Phase5SingleReviewCorpusSha256
    corpus_answerable: bool = Field(strict=True)
    intent: NonEmptyString
    difficulty: Difficulty
    hard_negative_category: NonEmptyString | None = None
    expected_api_symbols: tuple[NonEmptyString, ...] = ()
    gold_claims: tuple[AtomicGoldClaim, ...] = ()
    review: Phase5SingleReviewProvenance

    @field_validator("expected_api_symbols")
    @classmethod
    def canonicalize_expected_api_symbols(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Store unique expected symbols in canonical order."""
        return _canonicalize_unique_strings(
            values,
            label="Phase 5 single-review expected API symbols",
        )

    @model_validator(mode="after")
    def validate_single_review_example(self) -> Self:
        """Preserve corpus-level annotation invariants without adjudication semantics."""
        Phase5SingleReviewRevisedContent(
            query_text=self.query_text,
            corpus_answerable=self.corpus_answerable,
            hard_negative_category=self.hard_negative_category,
            gold_claims=self.gold_claims,
        )
        return self


class Phase5SingleReviewDataset(EvaluationModel):
    """An exact-byte single-review exploratory dataset and its complete provenance."""

    schema_version: Literal["phase5-development-single-review-dataset-v1"] = (
        "phase5-development-single-review-dataset-v1"
    )
    dataset_id: Literal["development-single-review-v1"] = "development-single-review-v1"
    dataset_role: Literal["development-single-review-exploratory"] = (
        "development-single-review-exploratory"
    )
    dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    dataset_sha256: Sha256
    decisions_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    decisions_sha256: Sha256
    governance_id: Literal["phase5-development-single-review-governance-v1"]
    governance_sha256: Phase5SingleReviewGovernanceSha256
    candidate_batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    candidate_batch_sha256: Phase5SingleReviewCandidateSha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Phase5SingleReviewCorpusSha256
    reviewer_id: Literal["sr_001"]
    examples: tuple[Phase5SingleReviewExample, ...] = ()

    @model_validator(mode="after")
    def validate_dataset_identity(self) -> Self:
        """Require ordered unique examples with provenance matching the dataset envelope."""
        query_ids = tuple(example.query_id for example in self.examples)
        if len(set(query_ids)) != len(query_ids):
            msg = "Phase 5 single-review dataset query IDs must be unique"
            raise ValueError(msg)
        if query_ids != tuple(sorted(query_ids)):
            msg = "Phase 5 single-review dataset examples must be ordered by query ID"
            raise ValueError(msg)
        claim_ids = tuple(
            claim.claim_id for example in self.examples for claim in example.gold_claims
        )
        if len(set(claim_ids)) != len(claim_ids):
            msg = "Phase 5 single-review gold claim IDs must be globally unique"
            raise ValueError(msg)
        if any(
            example.dataset_role != self.dataset_role
            or example.corpus_hash_policy != self.corpus_hash_policy
            or example.corpus_sha256 != self.corpus_sha256
            or example.review.governance_id != self.governance_id
            or example.review.governance_sha256 != self.governance_sha256
            or example.review.candidate_batch_id != self.candidate_batch_id
            or example.review.candidate_batch_sha256 != self.candidate_batch_sha256
            or example.review.decisions_sha256 != self.decisions_sha256
            or example.review.reviewer_id != self.reviewer_id
            for example in self.examples
        ):
            msg = "Phase 5 single-review examples must match the dataset provenance envelope"
            raise ValueError(msg)
        return self


class Phase5SingleReviewValidation(EvaluationModel):
    """Reproducible audit record for one completed single-review decision set."""

    schema_version: Literal["1"] = "1"
    validator_version: Literal["phase5-development-single-review-validation-v1"] = (
        "phase5-development-single-review-validation-v1"
    )
    dataset_id: Literal["development-single-review-v1"] = "development-single-review-v1"
    dataset_role: Literal["development-single-review-exploratory"] = (
        "development-single-review-exploratory"
    )
    independent_adjudication: Literal[False] = False
    held_out: Literal[False] = False
    threshold_selected: Literal[False] = False
    governance_id: Literal["phase5-development-single-review-governance-v1"]
    governance_sha256: Phase5SingleReviewGovernanceSha256
    candidate_batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    candidate_batch_sha256: Phase5SingleReviewCandidateSha256
    decisions_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    decisions_sha256: Sha256
    dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    dataset_sha256: Sha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Phase5SingleReviewCorpusSha256
    corpus_chunk_count: int = Field(ge=1, strict=True)
    reviewer_ids: tuple[Literal["sr_001"], ...] = Field(min_length=1, max_length=1)
    candidate_count: int = Field(ge=1, strict=True)
    decision_count: int = Field(ge=1, strict=True)
    accepted_as_proposed_count: int = Field(ge=0, strict=True)
    accepted_with_revisions_count: int = Field(ge=0, strict=True)
    rejected_count: int = Field(ge=0, strict=True)
    unresolved_count: int = Field(ge=0, strict=True)
    included_query_count: int = Field(ge=0, strict=True)
    answerable_query_count: int = Field(ge=0, strict=True)
    gold_claim_count: int = Field(ge=0, strict=True)
    gold_support_set_count: int = Field(ge=0, strict=True)
    accepted_as_proposed_query_ids: tuple[NonEmptyString, ...] = ()
    accepted_with_revisions_query_ids: tuple[NonEmptyString, ...] = ()
    rejected_query_ids: tuple[NonEmptyString, ...] = ()
    unresolved_query_ids: tuple[NonEmptyString, ...] = ()
    referenced_chunk_ids: tuple[NonEmptyString, ...] = ()
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_report_counts(self) -> Self:
        """Make every decision and accepted-dataset count independently auditable."""
        status_groups = (
            (self.accepted_as_proposed_query_ids, self.accepted_as_proposed_count),
            (self.accepted_with_revisions_query_ids, self.accepted_with_revisions_count),
            (self.rejected_query_ids, self.rejected_count),
            (self.unresolved_query_ids, self.unresolved_count),
        )
        all_status_ids: tuple[str, ...] = ()
        for query_ids, count in status_groups:
            if query_ids != tuple(sorted(query_ids)) or len(set(query_ids)) != len(query_ids):
                msg = "Phase 5 single-review report query IDs must be unique and ordered"
                raise ValueError(msg)
            if len(query_ids) != count:
                msg = "Phase 5 single-review report status counts must match query IDs"
                raise ValueError(msg)
            all_status_ids += query_ids
        if len(set(all_status_ids)) != len(all_status_ids):
            msg = "Phase 5 single-review report status groups must not overlap"
            raise ValueError(msg)
        if (
            len(all_status_ids) != self.decision_count
            or self.decision_count != self.candidate_count
        ):
            msg = "Phase 5 single-review report requires one final decision per candidate"
            raise ValueError(msg)
        if self.included_query_count != (
            self.accepted_as_proposed_count + self.accepted_with_revisions_count
        ):
            msg = "included query count must equal accepted single-review decisions"
            raise ValueError(msg)
        if self.answerable_query_count > self.included_query_count:
            msg = "answerable query count cannot exceed included query count"
            raise ValueError(msg)
        if self.gold_claim_count < self.answerable_query_count:
            msg = "every answerable single-review query requires at least one gold claim"
            raise ValueError(msg)
        if self.gold_support_set_count < self.gold_claim_count:
            msg = "every single-review gold claim requires at least one support set"
            raise ValueError(msg)
        for values, label in (
            (self.referenced_chunk_ids, "referenced chunk IDs"),
            (self.limitations, "limitations"),
        ):
            if values != tuple(sorted(values)) or len(set(values)) != len(values):
                msg = f"Phase 5 single-review report {label} must be unique and ordered"
                raise ValueError(msg)
        return self


class Phase5AnnotationCorpusDocument(EvaluationModel):
    """One normalized source identity in a frozen Phase 5 annotation corpus."""

    document_id: NonEmptyString
    content_sha256: Sha256
    source_url: AnyUrl
    source_type: SourceType
    parser_version: NonEmptyString
    source_commit: NonEmptyString | None = None


class Phase5AnnotationCorpusFreeze(EvaluationModel):
    """Deterministic Gate A record for one corpus annotation namespace."""

    schema_version: Literal["1"] = "1"
    freeze_version: Literal["phase5-annotation-corpus-freeze-v1"] = (
        "phase5-annotation-corpus-freeze-v1"
    )
    corpus_role: Literal["phase5-development-annotation"] = "phase5-development-annotation"
    annotation_namespace: NonEmptyString
    corpus_path: NonEmptyString
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"] = (
        "canonical-chunk-identity-json-v1"
    )
    corpus_sha256: Sha256
    library: NonEmptyString
    library_version: NonEmptyString
    source_types: tuple[SourceType, ...] = Field(min_length=1)
    parser_versions: tuple[NonEmptyString, ...] = Field(min_length=1)
    chunker_versions: tuple[NonEmptyString, ...] = Field(min_length=1)
    api_symbols: tuple[NonEmptyString, ...] = ()
    documents: tuple[Phase5AnnotationCorpusDocument, ...] = Field(min_length=1)
    document_count: int = Field(ge=1, strict=True)
    chunk_count: int = Field(ge=1, strict=True)
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_frozen_corpus_identity(self) -> Self:
        """Require a portable path, canonical aggregates, and exact derived counts."""
        corpus_path = PurePosixPath(self.corpus_path)
        if corpus_path.is_absolute() or ".." in corpus_path.parts:
            msg = "Phase 5 annotation corpus_path must be project-relative without traversal"
            raise ValueError(msg)

        document_ids = tuple(document.document_id for document in self.documents)
        if len(set(document_ids)) != len(document_ids):
            msg = "Phase 5 annotation corpus document IDs must be unique"
            raise ValueError(msg)
        if document_ids != tuple(sorted(document_ids)):
            msg = "Phase 5 annotation corpus documents must be ordered by document ID"
            raise ValueError(msg)
        if self.document_count != len(self.documents):
            msg = "Phase 5 annotation corpus document_count must match documents"
            raise ValueError(msg)

        document_source_types = tuple(
            sorted(
                {document.source_type for document in self.documents}, key=lambda item: item.value
            )
        )
        if self.source_types != document_source_types:
            msg = "Phase 5 annotation corpus source_types must match documents"
            raise ValueError(msg)
        document_parser_versions = tuple(
            sorted({document.parser_version for document in self.documents})
        )
        if self.parser_versions != document_parser_versions:
            msg = "Phase 5 annotation corpus parser_versions must match documents"
            raise ValueError(msg)

        canonical_fields = (
            ("source_types", tuple(sorted(self.source_types, key=lambda item: item.value))),
            ("parser_versions", tuple(sorted(self.parser_versions))),
            ("chunker_versions", tuple(sorted(self.chunker_versions))),
            ("api_symbols", tuple(sorted(self.api_symbols))),
            ("limitations", tuple(sorted(self.limitations))),
        )
        for field_name, canonical_values in canonical_fields:
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                msg = f"Phase 5 annotation corpus {field_name} must be unique"
                raise ValueError(msg)
            if values != canonical_values:
                msg = f"Phase 5 annotation corpus {field_name} must be lexicographically ordered"
                raise ValueError(msg)
        return self


class GoldClaimCoverage(EvaluationModel):
    """Minimal gold support sets present in candidate and budget-admitted evidence."""

    claim_id: NonEmptyString
    matched_context_support_sets: tuple[GoldEvidenceSupportSet, ...] = ()
    matched_candidate_support_sets: tuple[GoldEvidenceSupportSet, ...] = ()
    covered_by_context: bool = Field(strict=True)
    covered_by_candidates: bool = Field(strict=True)

    @model_validator(mode="after")
    def validate_matched_support_sets(self) -> Self:
        """Require canonical matches and monotonic candidate coverage."""
        context_sets = tuple(item.chunk_ids for item in self.matched_context_support_sets)
        candidate_sets = tuple(item.chunk_ids for item in self.matched_candidate_support_sets)
        for name, support_sets in (
            ("context", context_sets),
            ("candidate", candidate_sets),
        ):
            if len(set(support_sets)) != len(support_sets):
                msg = f"matched {name} support sets must be unique"
                raise ValueError(msg)
            if support_sets != tuple(sorted(support_sets)):
                msg = f"matched {name} support sets must be lexicographically ordered"
                raise ValueError(msg)

        if not set(context_sets).issubset(candidate_sets):
            msg = "matched context support sets must also match candidate evidence"
            raise ValueError(msg)
        if self.covered_by_context is not bool(context_sets):
            msg = "context claim coverage must match its support-set evidence"
            raise ValueError(msg)
        if self.covered_by_candidates is not bool(candidate_sets):
            msg = "candidate claim coverage must match its support-set evidence"
            raise ValueError(msg)
        return self


class GoldEvidenceCaseEvaluation(EvaluationModel):
    """Gold-backed context coverage and abstention result for one development query."""

    schema_version: Literal["1"] = "1"
    evaluator_version: Literal["phase5-gold-evidence-v1"] = "phase5-gold-evidence-v1"
    query_id: NonEmptyString
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    context_hash_policy: Literal["canonical-constructed-context-json-v1"] = (
        "canonical-constructed-context-json-v1"
    )
    context_sha256: Sha256
    policy_version: NonEmptyString
    sufficiency: EvidenceSufficiency
    assessment_reason_codes: tuple[NonEmptyString, ...] = Field(min_length=1)
    context_chunk_ids: tuple[NonEmptyString, ...] = ()
    omitted_chunk_ids: tuple[NonEmptyString, ...] = ()
    corpus_answerable: bool = Field(strict=True)
    gold_claim_count: int = Field(ge=0, strict=True)
    context_covered_claim_count: int = Field(ge=0, strict=True)
    candidate_covered_claim_count: int = Field(ge=0, strict=True)
    context_claim_coverage_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
    )
    candidate_claim_coverage_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        strict=True,
        allow_inf_nan=False,
    )
    gold_context_answerable: bool = Field(strict=True)
    gold_candidate_answerable: bool = Field(strict=True)
    should_abstain: bool = Field(strict=True)
    decision_correct: bool = Field(strict=True)
    unsupported_answer_authorized: bool = Field(strict=True)
    unnecessary_abstention: bool = Field(strict=True)
    budget_prevented_answerability: bool = Field(strict=True)
    claim_coverage: tuple[GoldClaimCoverage, ...] = ()

    @model_validator(mode="after")
    def validate_gold_evaluation(self) -> Self:
        """Keep coverage counts, decisions, and error categories internally consistent."""
        _validate_gold_identifiers(self)
        _validate_gold_support_references(self)
        expected_context_count = sum(result.covered_by_context for result in self.claim_coverage)
        expected_candidate_count = sum(
            result.covered_by_candidates for result in self.claim_coverage
        )
        _validate_gold_coverage_metrics(self, expected_context_count, expected_candidate_count)
        _validate_gold_answerability(self, expected_context_count, expected_candidate_count)
        _validate_gold_decision(self)
        return self


def _validate_gold_identifiers(evaluation: GoldEvidenceCaseEvaluation) -> None:
    if len(set(evaluation.assessment_reason_codes)) != len(evaluation.assessment_reason_codes):
        raise ValueError("gold evaluation assessment reason codes must be unique")
    if evaluation.assessment_reason_codes != tuple(sorted(evaluation.assessment_reason_codes)):
        raise ValueError("gold evaluation assessment reason codes must be ordered")
    if len(set(evaluation.context_chunk_ids)) != len(evaluation.context_chunk_ids):
        raise ValueError("gold evaluation context chunk IDs must be unique")
    if len(set(evaluation.omitted_chunk_ids)) != len(evaluation.omitted_chunk_ids):
        raise ValueError("gold evaluation omitted chunk IDs must be unique")
    if set(evaluation.context_chunk_ids) & set(evaluation.omitted_chunk_ids):
        raise ValueError("gold evaluation context and omitted chunk IDs must not overlap")

    claim_ids = tuple(result.claim_id for result in evaluation.claim_coverage)
    if len(set(claim_ids)) != len(claim_ids):
        raise ValueError("gold evaluation claim IDs must be unique")
    if claim_ids != tuple(sorted(claim_ids)):
        raise ValueError("gold evaluation claim results must be ordered by claim ID")
    if evaluation.gold_claim_count != len(evaluation.claim_coverage):
        raise ValueError("gold_claim_count must match claim_coverage")
    if evaluation.corpus_answerable is not bool(evaluation.claim_coverage):
        raise ValueError("corpus answerability must match the presence of gold claims")


def _validate_gold_support_references(evaluation: GoldEvidenceCaseEvaluation) -> None:
    context_ids = set(evaluation.context_chunk_ids)
    candidate_ids = context_ids | set(evaluation.omitted_chunk_ids)
    for result in evaluation.claim_coverage:
        if any(
            not set(support_set.chunk_ids).issubset(context_ids)
            for support_set in result.matched_context_support_sets
        ):
            raise ValueError("matched context support sets must be present in recorded context IDs")
        if any(
            not set(support_set.chunk_ids).issubset(candidate_ids)
            for support_set in result.matched_candidate_support_sets
        ):
            raise ValueError(
                "matched candidate support sets must be present in recorded candidate IDs"
            )


def _validate_gold_coverage_metrics(
    evaluation: GoldEvidenceCaseEvaluation,
    expected_context_count: int,
    expected_candidate_count: int,
) -> None:
    if evaluation.context_covered_claim_count != expected_context_count:
        raise ValueError("context_covered_claim_count must match claim_coverage")
    if evaluation.candidate_covered_claim_count != expected_candidate_count:
        raise ValueError("candidate_covered_claim_count must match claim_coverage")
    if evaluation.context_covered_claim_count > evaluation.candidate_covered_claim_count:
        raise ValueError("context claim coverage cannot exceed candidate claim coverage")

    denominator = evaluation.gold_claim_count
    expected_context_rate = None if denominator == 0 else expected_context_count / denominator
    expected_candidate_rate = None if denominator == 0 else expected_candidate_count / denominator
    if evaluation.context_claim_coverage_rate != expected_context_rate:
        raise ValueError("context claim coverage rate must use gold claims as its denominator")
    if evaluation.candidate_claim_coverage_rate != expected_candidate_rate:
        raise ValueError("candidate claim coverage rate must use gold claims as its denominator")


def _validate_gold_answerability(
    evaluation: GoldEvidenceCaseEvaluation,
    expected_context_count: int,
    expected_candidate_count: int,
) -> None:
    context_answerable = (
        evaluation.corpus_answerable and expected_context_count == evaluation.gold_claim_count
    )
    candidate_answerable = (
        evaluation.corpus_answerable and expected_candidate_count == evaluation.gold_claim_count
    )
    if evaluation.gold_context_answerable is not context_answerable:
        raise ValueError("gold context answerability must match complete claim coverage")
    if evaluation.gold_candidate_answerable is not candidate_answerable:
        raise ValueError("gold candidate answerability must match complete claim coverage")
    if evaluation.gold_context_answerable and not evaluation.gold_candidate_answerable:
        raise ValueError("gold context answerability requires gold candidate answerability")


def _validate_gold_decision(evaluation: GoldEvidenceCaseEvaluation) -> None:
    should_abstain = evaluation.sufficiency is not EvidenceSufficiency.SUFFICIENT
    if evaluation.should_abstain is not should_abstain:
        raise ValueError("gold evaluation abstention must match evidence sufficiency")
    decision_correct = evaluation.should_abstain is (not evaluation.gold_context_answerable)
    unsupported = not evaluation.should_abstain and not evaluation.gold_context_answerable
    unnecessary = evaluation.should_abstain and evaluation.gold_context_answerable
    budget_loss = evaluation.gold_candidate_answerable and not evaluation.gold_context_answerable
    if evaluation.decision_correct is not decision_correct:
        raise ValueError("decision correctness must match gold context answerability")
    if evaluation.unsupported_answer_authorized is not unsupported:
        raise ValueError("unsupported-answer classification must match the gold decision")
    if evaluation.unnecessary_abstention is not unnecessary:
        raise ValueError("unnecessary-abstention classification must match the gold decision")
    if evaluation.budget_prevented_answerability is not budget_loss:
        raise ValueError(
            "budget-loss classification must match candidate and context answerability"
        )


class AggregateGoldEvidenceMetrics(EvaluationModel):
    """Aggregate Phase 5 evidence coverage and selective-decision metrics."""

    query_count: int = Field(ge=1, strict=True)
    corpus_answerable_query_count: int = Field(ge=0, strict=True)
    corpus_unanswerable_query_count: int = Field(ge=0, strict=True)
    gold_context_answerable_query_count: int = Field(ge=0, strict=True)
    gold_candidate_answerable_query_count: int = Field(ge=0, strict=True)
    authorized_answer_count: int = Field(ge=0, strict=True)
    correct_decision_count: int = Field(ge=0, strict=True)
    unsupported_answer_count: int = Field(ge=0, strict=True)
    unnecessary_abstention_count: int = Field(ge=0, strict=True)
    budget_prevented_answerability_count: int = Field(ge=0, strict=True)
    gold_claim_count: int = Field(ge=0, strict=True)
    context_covered_claim_count: int = Field(ge=0, strict=True)
    candidate_covered_claim_count: int = Field(ge=0, strict=True)
    answer_coverage: float = Field(ge=0.0, le=1.0, strict=True, allow_inf_nan=False)
    selective_risk: float | None = Field(
        default=None, ge=0.0, le=1.0, strict=True, allow_inf_nan=False
    )
    false_answer_rate: float | None = Field(
        default=None, ge=0.0, le=1.0, strict=True, allow_inf_nan=False
    )
    false_abstention_rate: float | None = Field(
        default=None, ge=0.0, le=1.0, strict=True, allow_inf_nan=False
    )
    decision_accuracy: float = Field(ge=0.0, le=1.0, strict=True, allow_inf_nan=False)
    context_claim_coverage_rate: float | None = Field(
        default=None, ge=0.0, le=1.0, strict=True, allow_inf_nan=False
    )
    candidate_claim_coverage_rate: float | None = Field(
        default=None, ge=0.0, le=1.0, strict=True, allow_inf_nan=False
    )

    @classmethod
    def from_evaluations(
        cls,
        evaluations: Sequence[GoldEvidenceCaseEvaluation],
    ) -> Self:
        """Compute rates with explicit, stable denominators."""
        query_count = len(evaluations)
        if query_count == 0:
            msg = "gold evidence aggregation requires at least one evaluation"
            raise EvaluationError(msg)
        corpus_answerable_count = sum(item.corpus_answerable for item in evaluations)
        gold_context_answerable_count = sum(item.gold_context_answerable for item in evaluations)
        gold_candidate_answerable_count = sum(
            item.gold_candidate_answerable for item in evaluations
        )
        authorized_answer_count = sum(not item.should_abstain for item in evaluations)
        unsupported_answer_count = sum(item.unsupported_answer_authorized for item in evaluations)
        unnecessary_abstention_count = sum(item.unnecessary_abstention for item in evaluations)
        gold_claim_count = sum(item.gold_claim_count for item in evaluations)
        context_covered_claim_count = sum(item.context_covered_claim_count for item in evaluations)
        candidate_covered_claim_count = sum(
            item.candidate_covered_claim_count for item in evaluations
        )
        gold_context_unanswerable_count = query_count - gold_context_answerable_count
        return cls(
            query_count=query_count,
            corpus_answerable_query_count=corpus_answerable_count,
            corpus_unanswerable_query_count=query_count - corpus_answerable_count,
            gold_context_answerable_query_count=gold_context_answerable_count,
            gold_candidate_answerable_query_count=gold_candidate_answerable_count,
            authorized_answer_count=authorized_answer_count,
            correct_decision_count=sum(item.decision_correct for item in evaluations),
            unsupported_answer_count=unsupported_answer_count,
            unnecessary_abstention_count=unnecessary_abstention_count,
            budget_prevented_answerability_count=sum(
                item.budget_prevented_answerability for item in evaluations
            ),
            gold_claim_count=gold_claim_count,
            context_covered_claim_count=context_covered_claim_count,
            candidate_covered_claim_count=candidate_covered_claim_count,
            answer_coverage=authorized_answer_count / query_count,
            selective_risk=(
                None
                if authorized_answer_count == 0
                else unsupported_answer_count / authorized_answer_count
            ),
            false_answer_rate=(
                None
                if gold_context_unanswerable_count == 0
                else unsupported_answer_count / gold_context_unanswerable_count
            ),
            false_abstention_rate=(
                None
                if gold_context_answerable_count == 0
                else unnecessary_abstention_count / gold_context_answerable_count
            ),
            decision_accuracy=(sum(item.decision_correct for item in evaluations) / query_count),
            context_claim_coverage_rate=(
                None if gold_claim_count == 0 else context_covered_claim_count / gold_claim_count
            ),
            candidate_claim_coverage_rate=(
                None if gold_claim_count == 0 else candidate_covered_claim_count / gold_claim_count
            ),
        )


class GoldEvidenceEvaluationReport(EvaluationModel):
    """Deterministic aggregate bound to one development dataset and evidence policy."""

    schema_version: Literal["1"] = "1"
    evaluator_version: Literal["phase5-gold-evidence-v1"] = "phase5-gold-evidence-v1"
    dataset_role: Literal["development"] = "development"
    dataset_sha256: Sha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Sha256
    policy_version: NonEmptyString
    evaluations: tuple[GoldEvidenceCaseEvaluation, ...] = Field(min_length=1)
    metrics: AggregateGoldEvidenceMetrics

    @model_validator(mode="after")
    def validate_aggregate(self) -> Self:
        """Require canonical identities, one namespace, and freshly derived metrics."""
        query_ids = tuple(item.query_id for item in self.evaluations)
        if len(set(query_ids)) != len(query_ids):
            msg = "gold evidence report query IDs must be unique"
            raise ValueError(msg)
        if query_ids != tuple(sorted(query_ids)):
            msg = "gold evidence report evaluations must be ordered by query ID"
            raise ValueError(msg)
        if any(item.corpus_sha256 != self.corpus_sha256 for item in self.evaluations):
            msg = "gold evidence report evaluations must share the report corpus"
            raise ValueError(msg)
        if any(item.policy_version != self.policy_version for item in self.evaluations):
            msg = "gold evidence report evaluations must share one policy version"
            raise ValueError(msg)
        expected_metrics = AggregateGoldEvidenceMetrics.from_evaluations(self.evaluations)
        if self.metrics != expected_metrics:
            msg = "gold evidence report metrics must be derived from its evaluations"
            raise ValueError(msg)
        return self


class Phase5SingleReviewGoldEvidenceEvaluationReport(EvaluationModel):
    """Conservative baseline bound to the governed single-human review artifact."""

    schema_version: Literal["1"] = "1"
    evaluator_version: Literal["phase5-single-review-gold-evidence-v1"] = (
        "phase5-single-review-gold-evidence-v1"
    )
    dataset_id: Literal["development-single-review-v1"] = "development-single-review-v1"
    dataset_role: Literal["development-single-review-exploratory"] = (
        "development-single-review-exploratory"
    )
    independent_adjudication: Literal[False] = False
    held_out: Literal[False] = False
    threshold_selected: Literal[False] = False
    dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    dataset_sha256: Sha256
    decisions_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    decisions_sha256: Sha256
    governance_id: Literal["phase5-development-single-review-governance-v1"]
    governance_sha256: Phase5SingleReviewGovernanceSha256
    candidate_batch_id: Literal["pymc-6.1.0-api-phase5-development-batch-v1"]
    candidate_batch_sha256: Phase5SingleReviewCandidateSha256
    corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    corpus_sha256: Phase5SingleReviewCorpusSha256
    corpus_chunk_count: int = Field(ge=1, strict=True)
    retriever_version: NonEmptyString
    tokenizer_version: NonEmptyString
    k1: float = Field(gt=0.0, strict=True, allow_inf_nan=False)
    b: float = Field(ge=0.0, le=1.0, strict=True, allow_inf_nan=False)
    top_k: int = Field(ge=1, le=100, strict=True)
    context_builder_version: NonEmptyString
    context_rendering_policy: NonEmptyString
    context_truncation_policy: NonEmptyString
    token_budget: int = Field(ge=1, strict=True)
    evidence_policy_version: NonEmptyString
    evaluations: tuple[GoldEvidenceCaseEvaluation, ...] = Field(min_length=1)
    metrics: AggregateGoldEvidenceMetrics
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_single_review_baseline(self) -> Self:
        """Require canonical results, exact shared identities, and derived metrics."""
        query_ids = tuple(item.query_id for item in self.evaluations)
        if query_ids != tuple(sorted(query_ids)) or len(set(query_ids)) != len(query_ids):
            msg = "single-review gold evidence evaluations must have unique ordered query IDs"
            raise ValueError(msg)
        if any(item.corpus_sha256 != self.corpus_sha256 for item in self.evaluations):
            msg = "single-review gold evidence evaluations must share the report corpus"
            raise ValueError(msg)
        if any(item.policy_version != self.evidence_policy_version for item in self.evaluations):
            msg = "single-review gold evidence evaluations must share the report policy"
            raise ValueError(msg)
        expected_metrics = AggregateGoldEvidenceMetrics.from_evaluations(self.evaluations)
        if self.metrics != expected_metrics:
            msg = "single-review gold evidence metrics must be derived from evaluations"
            raise ValueError(msg)
        if self.limitations != tuple(sorted(set(self.limitations))):
            msg = "single-review gold evidence limitations must be unique and ordered"
            raise ValueError(msg)
        return self
