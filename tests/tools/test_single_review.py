"""Tests for strict Phase 5 single-human review contracts and decision loading."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from rag_pymc.evaluation.errors import EvaluationDatasetError
from tools.candidate_review import REVIEW_GOVERNANCE_SHA256, load_phase5_development_candidates
from tools.development_models import (
    Phase5DevelopmentExample,
    Phase5SingleReviewDecision,
    Phase5SingleReviewExample,
    Phase5SingleReviewRevisedContent,
)
from tools.single_review import (
    load_phase5_single_review_decisions,
    render_phase5_single_review_decision_template,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = (
    PROJECT_ROOT / "datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl"
)
GOVERNANCE_PATH = PROJECT_ROOT / "docs/evaluation/phase5-development-single-review-governance-v1.md"


def make_pending_payload() -> dict[str, Any]:
    return {
        "schema_version": "phase5-development-single-review-decision-v1",
        "artifact_role": "single-human-review-record",
        "dataset_role": "development-single-review-exploratory",
        "governance_id": "phase5-development-single-review-governance-v1",
        "governance_sha256": "a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264",
        "candidate_batch_id": "pymc-6.1.0-api-phase5-development-batch-v1",
        "candidate_batch_sha256": (
            "832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb"
        ),
        "corpus_hash_policy": "canonical-chunk-identity-json-v1",
        "corpus_sha256": "af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2",
        "reviewer_id": "sr_001",
        "query_id": "p5dev_v1_query_001",
        "query_review": "pending",
        "corpus_answerability_review": "pending",
        "claims_review": "pending",
        "support_sets_review": "pending",
        "leakage_review": "pending",
        "hard_negative_review": "pending",
        "final_status": "pending",
        "reviewed_at": None,
        "revised_content": None,
    }


def make_accepted_payload() -> dict[str, Any]:
    payload = make_pending_payload()
    payload.update(
        {
            "query_review": "accepted",
            "corpus_answerability_review": "accepted",
            "claims_review": "accepted",
            "support_sets_review": "accepted",
            "leakage_review": "confirmed-distinct",
            "hard_negative_review": "not-applicable",
            "final_status": "accepted-as-proposed",
            "reviewed_at": "2026-08-01T15:30:00Z",
        }
    )
    return payload


def test_governance_bytes_match_the_hash_bound_by_review_decisions() -> None:
    assert sha256(GOVERNANCE_PATH.read_bytes()).hexdigest() == REVIEW_GOVERNANCE_SHA256


def test_pending_template_is_deterministic_and_contains_no_human_decisions(
    tmp_path: Path,
) -> None:
    batch = load_phase5_development_candidates(CANDIDATE_PATH)

    first = render_phase5_single_review_decision_template(batch)
    second = render_phase5_single_review_decision_template(batch)
    path = tmp_path / "decisions.jsonl"
    path.write_bytes(first)
    loaded = load_phase5_single_review_decisions(path)

    assert first == second
    assert loaded.decisions_sha256 == sha256(first).hexdigest()
    assert len(loaded.decisions) == 24
    assert tuple(decision.query_id for decision in loaded.decisions) == tuple(
        sorted(decision.query_id for decision in loaded.decisions)
    )
    assert all(decision.final_status == "pending" for decision in loaded.decisions)
    assert all(decision.reviewed_at is None for decision in loaded.decisions)
    assert all(decision.revised_content is None for decision in loaded.decisions)


def test_pending_record_rejects_partial_or_timestamped_human_state() -> None:
    payload = make_pending_payload()
    payload["query_review"] = "accepted"

    with pytest.raises(ValidationError, match="every review field pending"):
        Phase5SingleReviewDecision.model_validate(payload)

    payload = make_pending_payload()
    payload["reviewed_at"] = "2026-08-01T15:30:00Z"
    with pytest.raises(ValidationError, match="cannot contain human decisions"):
        Phase5SingleReviewDecision.model_validate(payload)


def test_acceptance_requires_every_explicit_component_and_utc_timestamp() -> None:
    decision = Phase5SingleReviewDecision.model_validate(make_accepted_payload())

    assert decision.final_status == "accepted-as-proposed"
    assert decision.reviewed_at is not None
    assert decision.reviewed_at.utcoffset() is not None

    payload = make_accepted_payload()
    payload["claims_review"] = "unresolved"
    with pytest.raises(ValidationError, match="explicit acceptance of every component"):
        Phase5SingleReviewDecision.model_validate(payload)

    payload = make_accepted_payload()
    payload["reviewed_at"] = "2026-08-01T16:30:00+01:00"
    with pytest.raises(ValidationError, match="must use UTC"):
        Phase5SingleReviewDecision.model_validate(payload)

    payload = make_accepted_payload()
    payload["reviewed_at"] = "2026-07-26T04:14:50Z"
    with pytest.raises(ValidationError, match="must not precede the governance decision"):
        Phase5SingleReviewDecision.model_validate(payload)


def test_revision_requires_complete_content_and_an_identified_component() -> None:
    payload = make_accepted_payload()
    payload.update(
        {
            "query_review": "revised",
            "final_status": "accepted-with-revisions",
        }
    )

    with pytest.raises(ValidationError, match="require complete revised content"):
        Phase5SingleReviewDecision.model_validate(payload)

    payload["revised_content"] = {
        "query_text": "A human-revised synthetic query?",
        "corpus_answerable": True,
        "hard_negative_category": None,
        "gold_claims": [
            {
                "claim_id": "p5dev_v1_query_001_claim_001",
                "text": "A reviewed synthetic claim.",
                "support_sets": [{"chunk_ids": ["chunk_a"]}],
            }
        ],
    }
    decision = Phase5SingleReviewDecision.model_validate(payload)

    assert isinstance(decision.revised_content, Phase5SingleReviewRevisedContent)

    payload["query_review"] = "accepted"
    with pytest.raises(ValidationError, match="must identify a revised component"):
        Phase5SingleReviewDecision.model_validate(payload)


def test_rejected_and_unresolved_records_cannot_supply_dataset_content() -> None:
    payload = make_accepted_payload()
    payload.update(
        {
            "query_review": "rejected",
            "final_status": "rejected",
            "review_notes": "Synthetic rejection for contract testing.",
            "revised_content": {
                "query_text": "Rejected text",
                "corpus_answerable": False,
                "hard_negative_category": "rejected-query",
                "gold_claims": [],
            },
        }
    )

    with pytest.raises(ValidationError, match="cannot enter reviewed content"):
        Phase5SingleReviewDecision.model_validate(payload)

    payload = make_accepted_payload()
    payload.update(
        {
            "query_review": "unresolved",
            "final_status": "unresolved",
            "review_notes": "Synthetic unresolved state for contract testing.",
        }
    )
    decision = Phase5SingleReviewDecision.model_validate(payload)
    assert decision.revised_content is None


def test_single_review_contract_does_not_impersonate_adjudicated_contract() -> None:
    assert {"annotation", "adjudication"}.isdisjoint(Phase5SingleReviewExample.model_fields)
    assert {"review", "governance_id", "candidate_batch_sha256"}.isdisjoint(
        Phase5DevelopmentExample.model_fields
    )


def test_decision_loader_rejects_duplicate_keys_with_line_number(tmp_path: Path) -> None:
    payload = json.dumps(make_pending_payload(), separators=(",", ":"))
    malformed = payload.replace(
        '"artifact_role":"single-human-review-record",',
        '"artifact_role":"single-human-review-record",'
        '"artifact_role":"single-human-review-record",',
    )
    path = tmp_path / "decisions.jsonl"
    path.write_text(f"{malformed}\n", encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match=r"single-review decision.*:1"):
        load_phase5_single_review_decisions(path)
