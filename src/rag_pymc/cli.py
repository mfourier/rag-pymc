"""Command-line interface for the selected local rag-pymc workflows."""

import platform
import sys
from collections.abc import Sequence
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from rag_pymc import __version__
from rag_pymc.application.context_inspection import ContextInspectionService
from rag_pymc.application.retrieval_runtime import (
    build_sparse_experiment_config,
    build_sparse_runtime,
)
from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery, SourceManifest, SourceType
from rag_pymc.evaluation.dataset import load_evaluation_queries
from rag_pymc.evaluation.errors import EvaluationError
from rag_pymc.evaluation.evaluator import RetrievalEvaluator, write_experiment_report
from rag_pymc.ingestion import IngestionResult, IngestionService, LocalFileSourceFetcher
from rag_pymc.ingestion.errors import CorpusPersistenceError, IngestionError
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonDocumentRepository

app = typer.Typer(
    add_completion=False,
    help="Evidence-grounded local workflows for the rag-pymc expert assistant.",
    no_args_is_help=True,
)

MINIMUM_PYTHON = (3, 12)
SCIENTIFIC_DISTRIBUTIONS = ("pymc", "arviz", "pytensor")
DEFAULT_CORPUS_DIR = Path("datasets/processed/pymc-6.2.0-api-v1")
DEFAULT_LIBRARY = "pymc"
DEFAULT_LIBRARY_VERSION = "6.2.0"
DEFAULT_SEED = 20260720
DEFAULT_K1 = 1.5
DEFAULT_B = 0.75


def _run_api_ingestion(
    manifest_path: Path,
    source_path: Path,
    output_dir: Path,
) -> tuple[SourceManifest, IngestionResult]:
    manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    result = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=SphinxApiParser(),
        chunker=ApiReferenceChunker(),
        repository=JsonDocumentRepository(output_dir),
    ).run(manifest)
    return manifest, result


def _load_corpus_chunks(corpus_dir: Path) -> tuple[Chunk, ...]:
    chunks = JsonDocumentRepository(corpus_dir).load_chunks()
    if not chunks:
        msg = f"corpus contains no chunks: {corpus_dir}"
        raise CorpusPersistenceError(msg)
    return chunks


def _build_search_query(
    query_text: str,
    top_k: int,
    library: str | None,
    library_version: str | None,
    api_symbols: Sequence[str] | None,
) -> SearchQuery:
    return SearchQuery(
        text=query_text,
        top_k=top_k,
        library=library,
        library_version=library_version,
        source_types=(SourceType.API_REFERENCE,),
        api_symbols=tuple(api_symbols or ()),
    )


def _distribution_version(distribution: str) -> str | None:
    """Return an installed distribution version, or None when unavailable."""
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def _echo_results(query: SearchQuery, results: Sequence[RetrievedChunk]) -> None:
    """Render retrieval results without coupling search to a presentation framework."""
    typer.echo("rag-pymc search")
    typer.echo(f"query: {query.text}")
    typer.echo(f"matches: {len(results)}")
    for retrieved in results:
        chunk = retrieved.chunk
        typer.echo(
            f"{retrieved.rank}. {chunk.title} [{chunk.section or 'Unsectioned'}] "
            f"score={retrieved.score:.6f}"
        )
        typer.echo(
            f"   chunk={chunk.chunk_id} library={chunk.library} version={chunk.library_version}"
        )
        typer.echo(f"   source={chunk.source_url}")
    typer.echo("status: ok")


@app.command()
def doctor(
    scientific: Annotated[
        bool,
        typer.Option("--scientific", help="Also verify the optional scientific toolchain."),
    ] = False,
) -> None:
    """Report the core runtime and optionally verify scientific tooling."""
    typer.echo("rag-pymc doctor")
    typer.echo(f"project: {__version__}")
    typer.echo(f"python: {platform.python_version()}")

    missing: list[str] = []
    if scientific:
        for distribution in SCIENTIFIC_DISTRIBUTIONS:
            installed = _distribution_version(distribution)
            if installed is None:
                missing.append(distribution)
                typer.echo(f"{distribution}: missing")
            else:
                import_module(distribution)
                typer.echo(f"{distribution}: {installed}")

    if sys.version_info < MINIMUM_PYTHON or missing:
        typer.echo("status: failed", err=True)
        raise typer.Exit(code=1)
    typer.echo("status: ok")


@app.command("ingest")
def ingest_api_reference(
    manifest_path: Annotated[
        Path,
        typer.Option("--manifest", exists=True, dir_okay=False, readable=True),
    ],
    source_path: Annotated[
        Path,
        typer.Option("--source", exists=True, dir_okay=False, readable=True),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", file_okay=False),
    ] = DEFAULT_CORPUS_DIR,
) -> None:
    """Ingest one hash-verified official PyMC API page."""
    try:
        manifest, result = _run_api_ingestion(manifest_path, source_path, output_dir)
    except (IngestionError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"API ingestion failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("rag-pymc ingest")
    typer.echo(f"source: {manifest.source_id}")
    typer.echo(f"document: {result.document.document_id}")
    typer.echo(f"chunks: {len(result.chunks)}")
    typer.echo(f"output: {output_dir}")
    typer.echo("status: ok")


@app.command()
def search(
    query_text: Annotated[str, typer.Argument(help="Natural-language or API query.")],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = DEFAULT_CORPUS_DIR,
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 5,
    library: Annotated[str | None, typer.Option("--library")] = DEFAULT_LIBRARY,
    library_version: Annotated[str | None, typer.Option("--library-version")] = (
        DEFAULT_LIBRARY_VERSION
    ),
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
) -> None:
    """Search the selected local corpus with deterministic BM25."""
    try:
        query = _build_search_query(query_text, top_k, library, library_version, api_symbols)
        runtime = build_sparse_runtime(_load_corpus_chunks(corpus_dir))
        results = runtime.retriever.retrieve(query)
    except (CorpusPersistenceError, ValidationError, ValueError) as error:
        typer.echo(f"search failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    _echo_results(query, results)


@app.command("inspect-context")
def inspect_context(
    query_text: Annotated[str, typer.Argument(help="Natural-language retrieval query.")],
    token_budget: Annotated[
        int,
        typer.Option(
            "--token-budget",
            min=1,
            help="Required context budget in deterministic technical-v1 units.",
        ),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = DEFAULT_CORPUS_DIR,
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=10)] = 3,
    library: Annotated[str, typer.Option("--library")] = DEFAULT_LIBRARY,
    library_version: Annotated[str, typer.Option("--library-version")] = DEFAULT_LIBRARY_VERSION,
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
) -> None:
    """Retrieve and print deterministic, budget-bounded BM25 context as JSON."""
    try:
        query = _build_search_query(query_text, top_k, library, library_version, api_symbols)
        runtime = build_sparse_runtime(_load_corpus_chunks(corpus_dir))
        service = ContextInspectionService(
            runtime.retriever,
            RankedContextBuilder(runtime.tokenizer),
        )
        context = service.inspect(query, token_budget=token_budget)
    except (CorpusPersistenceError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"context inspection failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(context.model_dump_json(indent=2))


@app.command("serve-mcp")
def serve_mcp() -> None:
    """Serve the fixed read-only PyMC evidence tools over local MCP STDIO."""
    from rag_pymc.mcp.stdio import McpServerStartupError, serve_stdio

    try:
        serve_stdio()
    except McpServerStartupError as error:
        typer.echo(f"MCP server failed: {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command()
def evaluate(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", exists=True, file_okay=False, readable=True),
    ],
    output_path: Annotated[
        Path,
        typer.Option("--output", dir_okay=False),
    ],
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 3,
    seed: Annotated[int, typer.Option("--seed")] = DEFAULT_SEED,
    k1: Annotated[float, typer.Option("--k1", min=0.000001)] = DEFAULT_K1,
    b: Annotated[float, typer.Option("--b", min=0.0, max=1.0)] = DEFAULT_B,
    experiment_id: Annotated[str, typer.Option("--experiment-id")] = "bm25-mvp-v1",
    limitations: Annotated[list[str] | None, typer.Option("--limitation")] = None,
) -> None:
    """Evaluate the selected BM25 policy against committed query judgments."""
    try:
        chunks = _load_corpus_chunks(corpus_dir)
        queries = load_evaluation_queries(dataset_path)
        runtime = build_sparse_runtime(chunks, k1=k1, b=b)
        config = build_sparse_experiment_config(
            chunks,
            index=runtime.index,
            tokenizer=runtime.tokenizer,
            seed=seed,
            top_k=top_k,
        )
        report = RetrievalEvaluator(
            retriever=runtime.retriever,
            chunks=chunks,
            tokenizer=runtime.tokenizer,
            config=config,
            experiment_id=experiment_id,
            limitations=limitations,
        ).evaluate(queries, dataset_path=dataset_path)
        write_experiment_report(report, output_path)
    except (CorpusPersistenceError, EvaluationError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"evaluation failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    metrics = report.metrics
    typer.echo("rag-pymc evaluate")
    typer.echo(f"dataset: {dataset_path}")
    typer.echo(f"queries: {metrics.query_count}")
    typer.echo(f"recall@{top_k}: {metrics.recall_at_k:.6f}")
    typer.echo(f"mrr: {metrics.mrr:.6f}")
    typer.echo(f"ndcg@{top_k}: {metrics.ndcg_at_k:.6f}")
    typer.echo(f"unanswerable_empty_result_rate: {metrics.correct_abstention_rate:.6f}")
    typer.echo(f"output: {output_path}")
    typer.echo("status: ok")


def main() -> None:
    """Run the command-line application."""
    app()


if __name__ == "__main__":
    main()
