"""End-to-end tests for the Phase 5 single-human review artifact workflow."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.evaluation.errors import EvaluationDatasetError
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonDocumentRepository
from rag_pymc.serialization import canonical_json_bytes
from tools.candidate_review import load_phase5_development_candidates
from tools.development_models import (
    Phase5SingleReviewDecision,
    Phase5SingleReviewGoldEvidenceEvaluationReport,
    Phase5SingleReviewValidation,
)
from tools.research_cli import app
from tools.single_review import (
    build_phase5_single_review_dataset,
    load_phase5_single_review_dataset,
    load_phase5_single_review_decisions,
    render_phase5_single_review_decision_template,
    validate_phase5_single_review_dataset,
    write_phase5_single_review_outputs,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = (
    PROJECT_ROOT / "datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl"
)
DECISIONS_PATH = (
    PROJECT_ROOT / "datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl"
)
DATASET_PATH = PROJECT_ROOT / "datasets/evaluation/phase5/development-single-review-v1.jsonl"
BASELINE_REPORT_PATH = (
    PROJECT_ROOT
    / "reports/evaluation/phase5-development-single-review-v1-conservative-baseline.json"
)
SOURCE_NAMES = (
    "pymc.sample",
    "pymc.Data",
    "pymc.model.core.set_data",
    "pymc.sample_posterior_predictive",
)


def build_corpus(path: Path) -> JsonDocumentRepository:
    repository = JsonDocumentRepository(path)
    for source_name in SOURCE_NAMES:
        manifest_path = PROJECT_ROOT / f"datasets/raw/manifests/pymc/6.1.0/{source_name}.json"
        source_path = PROJECT_ROOT / f"datasets/fixtures/pymc/6.1.0/{source_name}.html"
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        IngestionService(
            fetcher=LocalFileSourceFetcher(source_path),
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
            repository=repository,
        ).run(manifest)
    return repository


def write_synthetic_completed_decisions(path: Path) -> None:
    """Create test-only decisions; this helper never writes repository evaluation artifacts."""
    candidate_batch = load_phase5_development_candidates(CANDIDATE_PATH)
    pending_bytes = render_phase5_single_review_decision_template(candidate_batch)
    pending_path = path.with_suffix(".pending.jsonl")
    pending_path.write_bytes(pending_bytes)
    pending = load_phase5_single_review_decisions(pending_path)
    candidates_by_id = {candidate.query_id: candidate for candidate in candidate_batch.candidates}

    completed: list[Phase5SingleReviewDecision] = []
    for decision in pending.decisions:
        candidate = candidates_by_id[decision.query_id]
        payload: dict[str, Any] = decision.model_dump(mode="json")
        payload.update(
            {
                "query_review": "accepted",
                "corpus_answerability_review": "accepted",
                "claims_review": "accepted",
                "support_sets_review": "accepted",
                "leakage_review": "confirmed-distinct",
                "hard_negative_review": (
                    "not-applicable" if candidate.proposed_corpus_answerable else "confirmed"
                ),
                "final_status": "accepted-as-proposed",
                "reviewed_at": "2026-08-01T15:30:00Z",
            }
        )
        if decision.query_id == "p5dev_v1_query_001":
            payload.update(
                {
                    "query_review": "revised",
                    "final_status": "accepted-with-revisions",
                    "revised_content": {
                        "query_text": f"{candidate.query_text} Please answer from PyMC 6.1.0.",
                        "corpus_answerable": candidate.proposed_corpus_answerable,
                        "hard_negative_category": candidate.hard_negative_category,
                        "gold_claims": [
                            claim.model_dump(mode="json")
                            for claim in candidate.proposed_gold_claims
                        ],
                    },
                }
            )
        elif decision.query_id == "p5dev_v1_query_023":
            payload.update(
                {
                    "query_review": "rejected",
                    "final_status": "rejected",
                    "review_notes": "Synthetic test rejection; not a human evaluation artifact.",
                }
            )
        elif decision.query_id == "p5dev_v1_query_024":
            payload.update(
                {
                    "query_review": "unresolved",
                    "final_status": "unresolved",
                    "review_notes": "Synthetic unresolved test state; no human label is implied.",
                }
            )
        completed.append(Phase5SingleReviewDecision.model_validate(payload))

    path.write_bytes(
        b"".join(
            canonical_json_bytes(decision.model_dump(mode="json")) + b"\n" for decision in completed
        )
    )


def test_single_review_build_is_reproducible_and_excludes_nonaccepted_records(
    tmp_path: Path,
) -> None:
    repository = build_corpus(tmp_path / "corpus")
    decisions_path = tmp_path / "decisions.jsonl"
    write_synthetic_completed_decisions(decisions_path)
    candidate_batch = load_phase5_development_candidates(CANDIDATE_PATH)
    decision_batch = load_phase5_single_review_decisions(decisions_path)

    first_dataset, first_report, first_bytes = build_phase5_single_review_dataset(
        candidate_batch,
        decision_batch,
        repository.load_chunks(),
    )
    second_dataset, second_report, second_bytes = build_phase5_single_review_dataset(
        candidate_batch,
        decision_batch,
        tuple(reversed(repository.load_chunks())),
    )

    assert first_dataset == second_dataset
    assert first_report == second_report
    assert first_bytes == second_bytes
    assert len(first_dataset.examples) == 22
    assert first_report.accepted_as_proposed_count == 21
    assert first_report.accepted_with_revisions_count == 1
    assert first_report.rejected_query_ids == ("p5dev_v1_query_023",)
    assert first_report.unresolved_query_ids == ("p5dev_v1_query_024",)
    assert first_report.independent_adjudication is False
    assert first_report.held_out is False
    assert first_report.threshold_selected is False
    assert {"annotation", "adjudication"}.isdisjoint(type(first_dataset.examples[0]).model_fields)

    dataset_path = tmp_path / "development-single-review-v1.jsonl"
    report_path = tmp_path / "phase5-development-single-review-v1-validation.json"
    write_phase5_single_review_outputs(
        first_bytes,
        first_report,
        dataset_path=dataset_path,
        report_path=report_path,
    )
    loaded_dataset = load_phase5_single_review_dataset(dataset_path)
    rebuilt_report = validate_phase5_single_review_dataset(
        loaded_dataset,
        candidate_batch,
        decision_batch,
        repository.load_chunks(),
    )

    assert loaded_dataset == first_dataset
    assert rebuilt_report == first_report
    assert (
        Phase5SingleReviewValidation.model_validate_json(report_path.read_text(encoding="utf-8"))
        == first_report
    )


def test_single_review_cli_exports_pending_and_fails_closed_before_human_review(
    tmp_path: Path,
) -> None:
    repository = build_corpus(tmp_path / "corpus")
    decisions_path = tmp_path / "decisions.pending.jsonl"
    dataset_path = tmp_path / "development-single-review-v1.jsonl"
    report_path = tmp_path / "phase5-development-single-review-v1-validation.json"
    runner = CliRunner()

    exported = runner.invoke(
        app,
        [
            "export-development-single-review-template",
            "--candidates",
            str(CANDIDATE_PATH),
            "--output",
            str(decisions_path),
        ],
    )
    finalized = runner.invoke(
        app,
        [
            "finalize-development-single-review",
            "--candidates",
            str(CANDIDATE_PATH),
            "--decisions",
            str(decisions_path),
            "--corpus-dir",
            str(repository.output_dir),
            "--dataset-output",
            str(dataset_path),
            "--report-output",
            str(report_path),
        ],
    )

    assert exported.exit_code == 0
    assert "queries: 24" in exported.stdout
    assert "status: pending-human-review" in exported.stdout
    assert finalized.exit_code == 1
    assert "remains pending for p5dev_v1_query_001" in finalized.stderr
    assert not dataset_path.exists()
    assert not report_path.exists()


def test_single_review_cli_finalizes_and_revalidates_exact_human_decisions(
    tmp_path: Path,
) -> None:
    repository = build_corpus(tmp_path / "corpus")
    decisions_path = tmp_path / "decisions.jsonl"
    write_synthetic_completed_decisions(decisions_path)
    dataset_path = tmp_path / "development-single-review-v1.jsonl"
    report_path = tmp_path / "phase5-development-single-review-v1-validation.json"
    runner = CliRunner()

    finalized = runner.invoke(
        app,
        [
            "finalize-development-single-review",
            "--candidates",
            str(CANDIDATE_PATH),
            "--decisions",
            str(decisions_path),
            "--corpus-dir",
            str(repository.output_dir),
            "--dataset-output",
            str(dataset_path),
            "--report-output",
            str(report_path),
        ],
    )
    validated = runner.invoke(
        app,
        [
            "validate-development-single-review",
            "--candidates",
            str(CANDIDATE_PATH),
            "--decisions",
            str(decisions_path),
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(repository.output_dir),
        ],
    )

    assert finalized.exit_code == 0
    assert validated.exit_code == 0
    assert finalized.stderr == ""
    assert validated.stderr == ""
    assert Phase5SingleReviewValidation.model_validate_json(finalized.stdout) == (
        Phase5SingleReviewValidation.model_validate_json(validated.stdout)
    )


def test_single_review_cli_never_overwrites_candidate_or_decision_inputs(tmp_path: Path) -> None:
    candidate_copy = tmp_path / "candidates.jsonl"
    candidate_bytes = CANDIDATE_PATH.read_bytes()
    candidate_copy.write_bytes(candidate_bytes)
    decisions_path = tmp_path / "decisions.jsonl"
    decisions_path.write_bytes(
        render_phase5_single_review_decision_template(
            load_phase5_development_candidates(candidate_copy)
        )
    )
    decision_bytes = decisions_path.read_bytes()
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    runner = CliRunner()

    template_result = runner.invoke(
        app,
        [
            "export-development-single-review-template",
            "--candidates",
            str(candidate_copy),
            "--output",
            str(candidate_copy),
        ],
    )
    finalize_result = runner.invoke(
        app,
        [
            "finalize-development-single-review",
            "--candidates",
            str(candidate_copy),
            "--decisions",
            str(decisions_path),
            "--corpus-dir",
            str(corpus_dir),
            "--dataset-output",
            str(decisions_path),
            "--report-output",
            str(tmp_path / "report.json"),
        ],
    )

    assert template_result.exit_code == 1
    assert "must not overwrite candidate drafts" in template_result.stderr
    assert candidate_copy.read_bytes() == candidate_bytes
    assert finalize_result.exit_code == 1
    assert "must not overwrite governed inputs" in finalize_result.stderr
    assert decisions_path.read_bytes() == decision_bytes


def test_single_review_rejects_revision_flags_that_disagree_with_human_content(
    tmp_path: Path,
) -> None:
    repository = build_corpus(tmp_path / "corpus")
    decisions_path = tmp_path / "decisions.jsonl"
    write_synthetic_completed_decisions(decisions_path)
    loaded = load_phase5_single_review_decisions(decisions_path)
    first_payload = loaded.decisions[0].model_dump(mode="json")
    first_payload["claims_review"] = "revised"
    inconsistent = (
        Phase5SingleReviewDecision.model_validate(first_payload),
        *loaded.decisions[1:],
    )
    decisions_path.write_bytes(
        b"".join(
            canonical_json_bytes(decision.model_dump(mode="json")) + b"\n"
            for decision in inconsistent
        )
    )

    with pytest.raises(EvaluationDatasetError, match="declared revisions do not match content"):
        build_phase5_single_review_dataset(
            load_phase5_development_candidates(CANDIDATE_PATH),
            load_phase5_single_review_decisions(decisions_path),
            repository.load_chunks(),
        )


def test_single_review_conservative_baseline_rebuilds_checked_in_report(
    tmp_path: Path,
) -> None:
    repository = build_corpus(tmp_path / "corpus")
    output_path = tmp_path / "baseline.json"

    result = CliRunner().invoke(
        app,
        [
            "evaluate-development-single-review-baseline",
            "--candidates",
            str(CANDIDATE_PATH),
            "--decisions",
            str(DECISIONS_PATH),
            "--dataset",
            str(DATASET_PATH),
            "--corpus-dir",
            str(repository.output_dir),
            "--top-k",
            "3",
            "--token-budget",
            "2048",
            "--k1",
            "1.5",
            "--b",
            "0.75",
            "--report-output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    rebuilt = Phase5SingleReviewGoldEvidenceEvaluationReport.model_validate_json(
        output_path.read_text(encoding="utf-8")
    )
    expected = Phase5SingleReviewGoldEvidenceEvaluationReport.model_validate_json(
        BASELINE_REPORT_PATH.read_text(encoding="utf-8")
    )
    assert rebuilt == expected
    assert output_path.read_bytes() == BASELINE_REPORT_PATH.read_bytes()
    assert rebuilt.metrics.query_count == 24
    assert rebuilt.metrics.answer_coverage == 0.0
    assert rebuilt.metrics.context_claim_coverage_rate == pytest.approx(25 / 28)
    assert rebuilt.metrics.candidate_claim_coverage_rate == pytest.approx(26 / 28)
    assert rebuilt.independent_adjudication is False
    assert rebuilt.held_out is False
    assert rebuilt.threshold_selected is False
