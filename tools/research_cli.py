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
from tools.development_dataset import (
    build_phase5_annotation_corpus_freeze,
    load_phase5_development_dataset,
    validate_phase5_development_corpus,
    write_phase5_annotation_corpus_freeze,
)

app = typer.Typer(
    add_completion=False,
    help="Internal research-data commands for rag-pymc.",
    no_args_is_help=True,
)


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


def main() -> None:
    """Run the internal research command-line application."""
    app()


if __name__ == "__main__":
    main()
