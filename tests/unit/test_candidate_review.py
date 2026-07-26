import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_pymc.domain import Chunk, Difficulty
from rag_pymc.evaluation import (
    AtomicGoldClaim,
    EvaluationDatasetError,
    EvaluationQuery,
    GoldEvidenceSupportSet,
    Phase5DevelopmentCandidate,
    Phase5DevelopmentCandidateBatch,
    hash_phase5_corpus,
    load_phase5_development_candidates,
    render_phase5_candidate_review,
    validate_phase5_candidate_batch_v1,
)
from rag_pymc.evaluation.candidate_review import PriorQuerySource
from tests.factories import make_chunk

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = (
    PROJECT_ROOT / "datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl"
)


def make_candidate_batch() -> tuple[Phase5DevelopmentCandidateBatch, tuple[Chunk, ...]]:
    chunk = make_chunk("chunk_a", "Complete synthetic support.")
    corpus_sha256 = hash_phase5_corpus((chunk,))
    candidate = Phase5DevelopmentCandidate(
        preregistration_id="phase5-development-batch-preregistration-v1",
        batch_id="pymc-6.1.0-api-phase5-development-batch-v1",
        slot_id="synthetic_slot",
        query_id="synthetic_query",
        query_text="How does the synthetic option behave?",
        query_family="synthetic_family",
        template_family="synthetic_template",
        library="pymc",
        library_version="6.1.0",
        corpus_hash_policy="canonical-chunk-identity-json-v1",
        corpus_sha256=corpus_sha256,
        proposed_corpus_answerable=True,
        intent="api_usage",
        difficulty=Difficulty.BEGINNER,
        expected_api_symbols=("pymc.sample",),
        proposed_gold_claims=(
            AtomicGoldClaim(
                claim_id="synthetic_query_claim_001",
                text="The synthetic option has documented behavior.",
                support_sets=(GoldEvidenceSupportSet(chunk_ids=(chunk.chunk_id,)),),
            ),
        ),
    )
    batch = Phase5DevelopmentCandidateBatch(
        dataset_sha256="a" * 64,
        preregistration_id=candidate.preregistration_id,
        batch_id=candidate.batch_id,
        corpus_hash_policy=candidate.corpus_hash_policy,
        corpus_sha256=corpus_sha256,
        candidates=(candidate,),
    )
    return batch, (chunk,)


def test_checked_in_candidate_batch_matches_every_approved_gate_b_slot() -> None:
    batch = load_phase5_development_candidates(CANDIDATE_PATH)

    validate_phase5_candidate_batch_v1(batch)

    assert len(batch.candidates) == 24
    assert sum(candidate.proposed_corpus_answerable for candidate in batch.candidates) == 18
    assert sum(len(candidate.proposed_gold_claims) for candidate in batch.candidates) == 28
    assert {
        "annotation",
        "adjudication",
        "corpus_answerable",
        "gold_claims",
    }.isdisjoint(Phase5DevelopmentCandidate.model_fields)


def test_candidate_contract_rejects_fabricated_human_provenance() -> None:
    batch = load_phase5_development_candidates(CANDIDATE_PATH)
    payload = batch.candidates[0].model_dump(mode="json")
    payload["annotation"] = {"method": "human"}

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Phase5DevelopmentCandidate.model_validate(payload)


def test_candidate_loader_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    payload = CANDIDATE_PATH.read_text(encoding="utf-8").splitlines()[0]
    malformed = payload.replace(
        '"candidate_status":"draft",',
        '"candidate_status":"draft","candidate_status":"draft",',
    )
    path = tmp_path / "candidates.jsonl"
    path.write_text(f"{malformed}\n", encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match=r"candidate.*:1"):
        load_phase5_development_candidates(path)


def test_review_render_is_deterministic_and_contains_resolved_evidence() -> None:
    batch, raw_chunks = make_candidate_batch()
    chunks = tuple(raw_chunks)
    prior_query = EvaluationQuery(
        question_id="prior_001",
        question="What is an unrelated prior question?",
        intent="api_usage",
        answerable=False,
        difficulty=Difficulty.BEGINNER,
    )
    prior = PriorQuerySource(
        path="datasets/evaluation/prior.jsonl",
        dataset_sha256="b" * 64,
        queries=(prior_query,),
    )

    first = render_phase5_candidate_review(batch, chunks, (prior,))
    second = render_phase5_candidate_review(batch, tuple(reversed(chunks)), (prior,))

    assert first == second
    assert all(line == line.rstrip() for line in first.splitlines())
    assert "Status: Agent-authored draft awaiting one real human review" in first
    assert "No human review is recorded" in first
    assert "phase5-development-single-review-governance-v1" in first
    assert "a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264" in first
    assert "`sr_001` (review not yet performed)" in first
    assert "This review is not independent adjudication" in first
    assert "`chunk_a`" in first
    assert "Complete synthetic support." in first
    assert "Jaccard" in first


def test_review_render_rejects_an_exact_prior_query_duplicate() -> None:
    batch, chunks = make_candidate_batch()
    candidate = batch.candidates[0]
    duplicate = EvaluationQuery(
        question_id="prior_001",
        question=candidate.query_text.upper(),
        intent="api_usage",
        answerable=False,
        difficulty=Difficulty.BEGINNER,
    )
    prior = PriorQuerySource(
        path="datasets/evaluation/prior.jsonl",
        dataset_sha256="b" * 64,
        queries=(duplicate,),
    )

    with pytest.raises(EvaluationDatasetError, match="exactly duplicates"):
        render_phase5_candidate_review(batch, chunks, (prior,))


def test_candidate_jsonl_contains_only_strict_json_objects() -> None:
    for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        assert isinstance(payload, dict)
        assert payload["candidate_status"] == "draft"
        assert payload["candidate_author"] == "agent"
