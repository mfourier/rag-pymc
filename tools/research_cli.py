"""Repository-local CLI for versioned annotation and evaluation-data workflows."""

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from rag_pymc.domain import SourceType
from rag_pymc.evaluation.errors import EvaluationError
from rag_pymc.ingestion.errors import CorpusPersistenceError
from rag_pymc.persistence import JsonDocumentRepository
from tools.candidate_review import (
    load_phase5_development_candidates,
    load_prior_query_source,
    render_phase5_candidate_review,
    validate_phase5_candidate_batch_v1,
    write_phase5_candidate_review,
)
from tools.corpus_migration import (
    ControlledApiCorpusFreeze,
    build_controlled_api_corpus_freeze,
    build_pymc_620_migration_report,
    build_pymc_620_retrieval_projection,
    write_bytes_atomically,
    write_evaluation_model,
)
from tools.development_dataset import (
    build_phase5_annotation_corpus_freeze,
    load_phase5_development_dataset,
    validate_phase5_development_corpus,
    write_phase5_annotation_corpus_freeze,
)
from tools.single_review import (
    build_phase5_single_review_dataset,
    load_phase5_single_review_dataset,
    load_phase5_single_review_decisions,
    validate_phase5_single_review_dataset,
    write_phase5_single_review_decision_template,
    write_phase5_single_review_outputs,
)
from tools.single_review_baseline import (
    DEFAULT_B,
    DEFAULT_K1,
    DEFAULT_TOKEN_BUDGET,
    DEFAULT_TOP_K,
    build_phase5_single_review_conservative_baseline,
    write_phase5_single_review_conservative_baseline,
)

app = typer.Typer(
    add_completion=False,
    help="Internal research-data commands for rag-pymc.",
    no_args_is_help=True,
)


def _pair_source_artifacts(
    manifests: list[Path],
    fixtures: list[Path],
) -> tuple[tuple[Path, Path], ...]:
    """Pair ordered acquisition inputs without silently dropping an unmatched path."""
    if not manifests or len(manifests) != len(fixtures):
        raise EvaluationError("manifest and fixture inputs must be nonempty and have equal counts")
    return tuple(zip(manifests, fixtures, strict=True))


@app.command("validate-development-data")
def validate_development_data(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
) -> None:
    """Validate development annotations against an exact local corpus."""
    try:
        dataset = load_phase5_development_dataset(dataset_path)
        chunks = JsonDocumentRepository(corpus_dir).load_chunks()
        report = validate_phase5_development_corpus(dataset, chunks)
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"development-data validation failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("freeze-annotation-corpus")
def freeze_annotation_corpus(
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    corpus_path: Annotated[
        str,
        typer.Option(
            "--corpus-path",
            help="Stable project-relative path recorded in the freeze artifact.",
        ),
    ],
    annotation_namespace: Annotated[str, typer.Option("--annotation-namespace")],
    library: Annotated[str, typer.Option("--library")],
    library_version: Annotated[str, typer.Option("--library-version")],
    limitations: Annotated[list[str], typer.Option("--limitation")],
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Freeze a validated corpus before annotation begins."""
    try:
        repository = JsonDocumentRepository(corpus_dir)
        report = build_phase5_annotation_corpus_freeze(
            repository.load_documents(),
            repository.load_chunks(),
            annotation_namespace=annotation_namespace,
            corpus_path=corpus_path,
            library=library,
            library_version=library_version,
            source_types=(SourceType.API_REFERENCE,),
            limitations=limitations,
        )
        write_phase5_annotation_corpus_freeze(report, output_path)
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"annotation-corpus freeze failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("export-development-review")
def export_development_review(
    candidates_path: Annotated[
        Path,
        typer.Option("--candidates", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    prior_dataset_paths: Annotated[
        list[Path],
        typer.Option("--prior-dataset", exists=True, dir_okay=False, readable=True),
    ],
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Export the deterministic single-review packet without creating human labels."""
    try:
        batch = load_phase5_development_candidates(candidates_path)
        validate_phase5_candidate_batch_v1(batch)
        chunks = JsonDocumentRepository(corpus_dir).load_chunks()
        prior_sources = tuple(load_prior_query_source(path) for path in prior_dataset_paths)
        review = render_phase5_candidate_review(batch, chunks, prior_sources)
        write_phase5_candidate_review(review, output_path)
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"development-review export failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("python -m tools.research_cli export-development-review")
    typer.echo(f"candidates: {candidates_path}")
    typer.echo(f"candidate_sha256: {batch.dataset_sha256}")
    typer.echo(f"corpus_sha256: {batch.corpus_sha256}")
    typer.echo(f"queries: {len(batch.candidates)}")
    typer.echo(f"output: {output_path}")
    typer.echo("status: ok")


@app.command("export-development-single-review-template")
def export_development_single_review_template(
    candidates_path: Annotated[
        Path,
        typer.Option("--candidates", exists=True, dir_okay=False, readable=True),
    ],
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Export pending records without manufacturing human decisions or timestamps."""
    try:
        if output_path.resolve() == candidates_path.resolve():
            raise EvaluationError("single-review template must not overwrite candidate drafts")
        batch = load_phase5_development_candidates(candidates_path)
        validate_phase5_candidate_batch_v1(batch)
        write_phase5_single_review_decision_template(batch, output_path)
        decisions = load_phase5_single_review_decisions(output_path)
    except (EvaluationError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"single-review template export failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("python -m tools.research_cli export-development-single-review-template")
    typer.echo(f"candidate_sha256: {batch.dataset_sha256}")
    typer.echo(f"decisions_sha256: {decisions.decisions_sha256}")
    typer.echo(f"queries: {len(decisions.decisions)}")
    typer.echo(f"output: {output_path}")
    typer.echo("status: pending-human-review")


@app.command("finalize-development-single-review")
def finalize_development_single_review(
    candidates_path: Annotated[
        Path,
        typer.Option("--candidates", exists=True, dir_okay=False, readable=True),
    ],
    decisions_path: Annotated[
        Path,
        typer.Option("--decisions", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    dataset_path: Annotated[Path, typer.Option("--dataset-output", dir_okay=False)],
    report_path: Annotated[Path, typer.Option("--report-output", dir_okay=False)],
) -> None:
    """Compile complete explicit human decisions into accepted-only versioned artifacts."""
    try:
        protected_paths = {
            candidates_path.resolve(),
            decisions_path.resolve(),
            (corpus_dir / "corpus.json").resolve(),
        }
        output_paths = {dataset_path.resolve(), report_path.resolve()}
        if output_paths & protected_paths:
            raise EvaluationError("single-review outputs must not overwrite governed inputs")
        candidate_batch = load_phase5_development_candidates(candidates_path)
        decision_batch = load_phase5_single_review_decisions(decisions_path)
        chunks = JsonDocumentRepository(corpus_dir).load_chunks()
        _dataset, report, dataset_bytes = build_phase5_single_review_dataset(
            candidate_batch,
            decision_batch,
            chunks,
        )
        write_phase5_single_review_outputs(
            dataset_bytes,
            report,
            dataset_path=dataset_path,
            report_path=report_path,
        )
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"single-review finalization failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("validate-development-single-review")
def validate_development_single_review(
    candidates_path: Annotated[
        Path,
        typer.Option("--candidates", exists=True, dir_okay=False, readable=True),
    ],
    decisions_path: Annotated[
        Path,
        typer.Option("--decisions", exists=True, dir_okay=False, readable=True),
    ],
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
) -> None:
    """Rebuild a single-review dataset from decisions and emit its canonical audit report."""
    try:
        candidate_batch = load_phase5_development_candidates(candidates_path)
        decision_batch = load_phase5_single_review_decisions(decisions_path)
        dataset = load_phase5_single_review_dataset(dataset_path)
        chunks = JsonDocumentRepository(corpus_dir).load_chunks()
        report = validate_phase5_single_review_dataset(
            dataset,
            candidate_batch,
            decision_batch,
            chunks,
        )
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"single-review validation failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("evaluate-development-single-review-baseline")
def evaluate_development_single_review_baseline(
    candidates_path: Annotated[
        Path,
        typer.Option("--candidates", exists=True, dir_okay=False, readable=True),
    ],
    decisions_path: Annotated[
        Path,
        typer.Option("--decisions", exists=True, dir_okay=False, readable=True),
    ],
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    report_path: Annotated[Path, typer.Option("--report-output", dir_okay=False)],
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = DEFAULT_TOP_K,
    token_budget: Annotated[int, typer.Option("--token-budget", min=1)] = DEFAULT_TOKEN_BUDGET,
    k1: Annotated[float, typer.Option("--k1", min=0.000001)] = DEFAULT_K1,
    b: Annotated[float, typer.Option("--b", min=0.0, max=1.0)] = DEFAULT_B,
) -> None:
    """Record the unchanged conservative policy over the governed single review."""
    try:
        protected_paths = {
            candidates_path.resolve(),
            decisions_path.resolve(),
            dataset_path.resolve(),
            (corpus_dir / "corpus.json").resolve(),
        }
        if report_path.resolve() in protected_paths:
            raise EvaluationError("baseline output must not overwrite governed inputs")
        candidate_batch = load_phase5_development_candidates(candidates_path)
        decision_batch = load_phase5_single_review_decisions(decisions_path)
        dataset = load_phase5_single_review_dataset(dataset_path)
        chunks = JsonDocumentRepository(corpus_dir).load_chunks()
        validate_phase5_single_review_dataset(
            dataset,
            candidate_batch,
            decision_batch,
            chunks,
        )
        report = build_phase5_single_review_conservative_baseline(
            dataset,
            chunks,
            top_k=top_k,
            token_budget=token_budget,
            k1=k1,
            b=b,
        )
        write_phase5_single_review_conservative_baseline(report, report_path)
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"single-review baseline failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("freeze-controlled-api-corpus")
def freeze_controlled_api_corpus(
    manifest_paths: Annotated[
        list[Path],
        typer.Option("--manifest", exists=True, dir_okay=False, readable=True),
    ],
    fixture_paths: Annotated[
        list[Path],
        typer.Option("--fixture", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    corpus_id: Annotated[str, typer.Option("--corpus-id")],
    corpus_path: Annotated[str, typer.Option("--corpus-path")],
    limitations: Annotated[list[str], typer.Option("--limitation")],
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Freeze a versioned API corpus with manifest-level provenance in its hash."""
    try:
        artifacts = _pair_source_artifacts(manifest_paths, fixture_paths)
        protected_paths = {
            *(path.resolve() for path in manifest_paths),
            *(path.resolve() for path in fixture_paths),
            (corpus_dir / "corpus.json").resolve(),
        }
        if output_path.resolve() in protected_paths:
            raise EvaluationError("controlled corpus report must not overwrite source inputs")
        repository = JsonDocumentRepository(corpus_dir)
        report = build_controlled_api_corpus_freeze(
            artifacts,
            repository.load_documents(),
            repository.load_chunks(),
            corpus_id=corpus_id,
            corpus_path=corpus_path,
            limitations=limitations,
        )
        write_evaluation_model(report, output_path)
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"controlled API corpus freeze failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("compare-pymc-620-migration")
def compare_pymc_620_migration(
    old_manifest_paths: Annotated[
        list[Path],
        typer.Option("--old-manifest", exists=True, dir_okay=False, readable=True),
    ],
    old_fixture_paths: Annotated[
        list[Path],
        typer.Option("--old-fixture", exists=True, dir_okay=False, readable=True),
    ],
    old_corpus_dir: Annotated[
        Path,
        typer.Option("--old-corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    new_freeze_path: Annotated[
        Path,
        typer.Option("--new-freeze", exists=True, dir_okay=False, readable=True),
    ],
    new_corpus_dir: Annotated[
        Path,
        typer.Option("--new-corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ],
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Compare 6.1.0 and 6.2.0 evidence without manufacturing migrated human labels."""
    try:
        old_artifacts = _pair_source_artifacts(old_manifest_paths, old_fixture_paths)
        old_repository = JsonDocumentRepository(old_corpus_dir)
        new_repository = JsonDocumentRepository(new_corpus_dir)
        new_freeze = ControlledApiCorpusFreeze.model_validate_json(
            new_freeze_path.read_text(encoding="utf-8")
        )
        dataset = load_phase5_single_review_dataset(dataset_path)
        protected_paths = {
            *(path.resolve() for path in old_manifest_paths),
            *(path.resolve() for path in old_fixture_paths),
            (old_corpus_dir / "corpus.json").resolve(),
            new_freeze_path.resolve(),
            (new_corpus_dir / "corpus.json").resolve(),
            dataset_path.resolve(),
        }
        if output_path.resolve() in protected_paths:
            raise EvaluationError("migration report must not overwrite governed inputs")
        report = build_pymc_620_migration_report(
            old_artifacts,
            old_repository.load_documents(),
            old_repository.load_chunks(),
            new_freeze,
            new_repository.load_documents(),
            new_repository.load_chunks(),
            dataset,
        )
        write_evaluation_model(report, output_path)
    except (
        CorpusPersistenceError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"PyMC 6.2.0 migration comparison failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


@app.command("project-pymc-620-retrieval-dataset")
def project_pymc_620_retrieval_dataset(
    source_dataset_path: Annotated[
        Path,
        typer.Option("--source-dataset", exists=True, dir_okay=False, readable=True),
    ],
    migration_report_path: Annotated[
        Path,
        typer.Option("--migration-report", exists=True, dir_okay=False, readable=True),
    ],
    target_freeze_path: Annotated[
        Path,
        typer.Option("--target-freeze", exists=True, dir_okay=False, readable=True),
    ],
    output_dataset_path: Annotated[
        Path,
        typer.Option("--output-dataset", dir_okay=False),
    ],
    output_report_path: Annotated[
        Path,
        typer.Option("--output-report", dir_okay=False),
    ],
) -> None:
    """Project exact retrieval qrels without claiming new human judgment."""
    try:
        protected_paths = {
            source_dataset_path.resolve(),
            migration_report_path.resolve(),
            target_freeze_path.resolve(),
        }
        outputs = {output_dataset_path.resolve(), output_report_path.resolve()}
        if len(outputs) != 2 or outputs & protected_paths:
            raise EvaluationError("retrieval projection outputs must not overwrite inputs")
        target_freeze = ControlledApiCorpusFreeze.model_validate_json(
            target_freeze_path.read_text(encoding="utf-8")
        )
        dataset_bytes, report = build_pymc_620_retrieval_projection(
            source_dataset_path,
            migration_report_path,
            target_freeze,
        )
        write_bytes_atomically(
            dataset_bytes,
            output_dataset_path,
            label="PyMC 6.2.0 retrieval projection",
        )
        write_evaluation_model(report, output_report_path)
    except (EvaluationError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"PyMC 6.2.0 retrieval projection failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(report.model_dump_json(indent=2))


def main() -> None:
    """Run the internal research command-line application."""
    app()


if __name__ == "__main__":
    main()
