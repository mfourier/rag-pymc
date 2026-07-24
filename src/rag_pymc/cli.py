"""Command-line interface for local rag-pymc workflows."""

import platform
import sys
from collections.abc import Sequence
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter_ns
from typing import Annotated

import typer
from pydantic import ValidationError

from rag_pymc import __version__
from rag_pymc.application import ContextInspectionService
from rag_pymc.application.retrieval_runtime import (
    build_dense_experiment_config,
    build_hybrid_experiment_config,
    build_hybrid_runtime,
    build_reranking_runtime,
    build_sparse_experiment_config,
)
from rag_pymc.chunking import ApiReferenceChunker, NotebookChunker, RepositoryCodeChunker
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import Chunk, SearchQuery, SourceManifest, SourceType
from rag_pymc.embeddings import (
    EmbeddingError,
    load_embedding_model_spec,
)
from rag_pymc.evaluation import (
    EvaluationError,
    RetrievalEvaluator,
    build_phase5_annotation_corpus_freeze,
    compare_retrieval_reports,
    load_evaluation_queries,
    load_phase5_development_dataset,
    validate_phase5_development_corpus,
    write_comparison_report,
    write_experiment_report,
    write_phase5_annotation_corpus_freeze,
)
from rag_pymc.indexing import BM25Index, DenseIndexError, ExactCosineIndex
from rag_pymc.ingestion import IngestionResult, IngestionService, LocalFileSourceFetcher
from rag_pymc.ingestion.errors import CorpusPersistenceError, IngestionError
from rag_pymc.ingestion.interfaces import Chunker, DocumentParser, ParsedDocument
from rag_pymc.parsing import NotebookParser, PythonRepositoryParser, SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository
from rag_pymc.reranking import (
    RerankingError,
)
from rag_pymc.retrieval import (
    DenseRetriever,
    ReciprocalRankFusionRetriever,
    SparseRetriever,
    TechnicalTokenizer,
    WeightedRetriever,
)

app = typer.Typer(
    add_completion=False,
    help="Local commands for the rag-pymc project.",
    no_args_is_help=True,
)

MINIMUM_PYTHON = (3, 12)
SCIENTIFIC_DISTRIBUTIONS = ("pymc", "arviz", "pytensor")
DEFAULT_EMBEDDING_MANIFEST = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json")


def _run_local_ingestion[ParsedDocumentT: ParsedDocument](
    manifest_path: Path,
    source_path: Path,
    output_dir: Path,
    *,
    parser: DocumentParser[ParsedDocumentT],
    chunker: Chunker[ParsedDocumentT],
) -> tuple[SourceManifest, IngestionResult]:
    manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    result = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=parser,
        chunker=chunker,
        repository=JsonlDocumentRepository(output_dir),
    ).run(manifest)
    return manifest, result


def _echo_ingestion_success(
    command: str,
    manifest: SourceManifest,
    result: IngestionResult,
    output_dir: Path,
) -> None:
    typer.echo(f"rag-pymc {command}")
    typer.echo(f"source: {manifest.source_id}")
    typer.echo(f"document: {result.document.document_id}")
    typer.echo(f"chunks: {len(result.chunks)}")
    typer.echo(f"output: {output_dir}")
    typer.echo("status: ok")


def _load_corpus_chunks(corpus_dir: Path) -> tuple[Chunk, ...]:
    chunks = JsonlDocumentRepository(corpus_dir).load_chunks()
    if not chunks:
        msg = f"corpus contains no chunks: {corpus_dir}"
        raise CorpusPersistenceError(msg)
    return chunks


def _build_search_query(
    query_text: str,
    top_k: int,
    library: str | None,
    library_version: str | None,
    source_types: Sequence[SourceType] | None,
    api_symbols: Sequence[str] | None,
) -> SearchQuery:
    return SearchQuery(
        text=query_text,
        top_k=top_k,
        library=library,
        library_version=library_version,
        source_types=tuple(source_types or ()),
        api_symbols=tuple(api_symbols or ()),
    )


def _distribution_version(distribution: str) -> str | None:
    """Return an installed distribution version, or None when it is unavailable."""
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


@app.callback()
def main() -> None:
    """Run local rag-pymc workflows."""


@app.command()
def doctor() -> None:
    """Verify the Python runtime and import the required scientific stack."""
    typer.echo("rag-pymc doctor")
    typer.echo(f"project: {__version__}")
    typer.echo(f"python: {platform.python_version()}")

    healthy = sys.version_info >= MINIMUM_PYTHON
    for distribution in SCIENTIFIC_DISTRIBUTIONS:
        try:
            import_module(distribution)
        except Exception as error:
            typer.echo(f"{distribution}: import failed ({type(error).__name__})")
            healthy = False
        else:
            installed_version = _distribution_version(distribution)
            typer.echo(f"{distribution}: {installed_version or 'version unknown'}")
            healthy = healthy and installed_version is not None

    typer.echo(f"status: {'ok' if healthy else 'failed'}")
    if not healthy:
        raise typer.Exit(code=1)


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
    ] = Path("datasets/processed/local"),
) -> None:
    """Ingest one verified Sphinx API source into a local JSONL corpus."""
    try:
        manifest, result = _run_local_ingestion(
            manifest_path,
            source_path,
            output_dir,
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
        )
    except (IngestionError, OSError, ValidationError) as error:
        typer.echo(f"ingestion failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    _echo_ingestion_success("ingest", manifest, result, output_dir)


@app.command("ingest-code")
def ingest_repository_code(
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
    ] = Path("datasets/processed/repository-code"),
) -> None:
    """Ingest one verified Python implementation into a local JSONL corpus."""
    try:
        manifest, result = _run_local_ingestion(
            manifest_path,
            source_path,
            output_dir,
            parser=PythonRepositoryParser(),
            chunker=RepositoryCodeChunker(),
        )
    except (IngestionError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"repository-code ingestion failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    _echo_ingestion_success("ingest-code", manifest, result, output_dir)


@app.command("ingest-notebook")
def ingest_notebook(
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
    ] = Path("datasets/processed/notebooks"),
) -> None:
    """Ingest one verified notebook without execution outputs."""
    try:
        manifest, result = _run_local_ingestion(
            manifest_path,
            source_path,
            output_dir,
            parser=NotebookParser(),
            chunker=NotebookChunker(),
        )
    except (IngestionError, OSError, ValidationError, ValueError) as error:
        typer.echo(f"notebook ingestion failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    _echo_ingestion_success("ingest-notebook", manifest, result, output_dir)


@app.command()
def search(
    query_text: Annotated[str, typer.Argument(help="Natural-language or API query.")],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/local"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 5,
    library: Annotated[str | None, typer.Option("--library")] = None,
    library_version: Annotated[str | None, typer.Option("--library-version")] = None,
    source_types: Annotated[
        list[SourceType] | None,
        typer.Option("--source-type"),
    ] = None,
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
) -> None:
    """Search the local corpus with the explicit BM25 baseline."""
    try:
        chunks = _load_corpus_chunks(corpus_dir)
        retriever = SparseRetriever(BM25Index(chunks))
        query = _build_search_query(
            query_text, top_k, library, library_version, source_types, api_symbols
        )
        results = retriever.retrieve(query)
    except (CorpusPersistenceError, ValidationError, ValueError) as error:
        typer.echo(f"search failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("rag-pymc search")
    typer.echo(f"query: {query.text}")
    typer.echo(f"matches: {len(results)}")
    for result in results:
        chunk = result.chunk
        typer.echo(
            f"{result.rank}. {chunk.title} [{chunk.section or 'Unsectioned'}] "
            f"score={result.score:.6f}"
        )
        typer.echo(
            f"   chunk={chunk.chunk_id} library={chunk.library} version={chunk.library_version}"
        )
        typer.echo(f"   source={chunk.source_url}")
    typer.echo("status: ok")


@app.command()
def evaluate(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/evaluation/phase2/pymc_sample_queries.jsonl"),
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/local"),
    output_path: Annotated[
        Path,
        typer.Option("--output", dir_okay=False),
    ] = Path("reports/evaluation/phase2-bm25-baseline.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 3,
    seed: Annotated[int, typer.Option("--seed")] = 20260719,
    k1: Annotated[float, typer.Option("--k1", min=0.000001)] = 1.5,
    b: Annotated[float, typer.Option("--b", min=0.0, max=1.0)] = 0.75,
    experiment_id: Annotated[str, typer.Option("--experiment-id")] = "phase2-bm25-baseline",
    limitations: Annotated[list[str] | None, typer.Option("--limitation")] = None,
) -> None:
    """Evaluate BM25 against committed query judgments."""
    try:
        chunks = _load_corpus_chunks(corpus_dir)
        queries = load_evaluation_queries(dataset_path)
        tokenizer = TechnicalTokenizer()
        index = BM25Index(chunks, tokenizer=tokenizer, k1=k1, b=b)
        config = build_sparse_experiment_config(
            chunks,
            index=index,
            tokenizer=tokenizer,
            seed=seed,
            top_k=top_k,
        )
        evaluator = RetrievalEvaluator(
            retriever=SparseRetriever(index),
            chunks=chunks,
            tokenizer=tokenizer,
            config=config,
            experiment_id=experiment_id,
            limitations=limitations,
        )
        report = evaluator.evaluate(queries, dataset_path=dataset_path)
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
    typer.echo(f"correct_abstention: {metrics.correct_abstention_rate:.6f}")
    typer.echo(f"output: {output_path}")
    typer.echo("status: ok")


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
    """Validate Phase 5 development annotations against an exact local corpus."""
    try:
        dataset = load_phase5_development_dataset(dataset_path)
        chunks = JsonlDocumentRepository(corpus_dir).load_chunks()
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
    source_types: Annotated[list[SourceType], typer.Option("--source-type")],
    limitations: Annotated[list[str], typer.Option("--limitation")],
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Freeze a validated processed corpus before Phase 5 annotation begins."""
    try:
        repository = JsonlDocumentRepository(corpus_dir)
        documents = repository.load_documents()
        chunks = repository.load_chunks()
        report = build_phase5_annotation_corpus_freeze(
            documents,
            chunks,
            annotation_namespace=annotation_namespace,
            corpus_path=corpus_path,
            library=library,
            library_version=library_version,
            source_types=source_types,
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


@app.command("search-dense")
def search_dense(
    query_text: Annotated[str, typer.Argument(help="Natural-language retrieval query.")],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/local"),
    model_manifest: Annotated[
        Path,
        typer.Option("--model-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 5,
    library: Annotated[str | None, typer.Option("--library")] = None,
    library_version: Annotated[str | None, typer.Option("--library-version")] = None,
    source_types: Annotated[
        list[SourceType] | None,
        typer.Option("--source-type"),
    ] = None,
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
    device: Annotated[str, typer.Option("--device")] = "cpu",
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 16,
    seed: Annotated[int, typer.Option("--seed")] = 20260719,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Search the local corpus with the pinned dense baseline."""
    try:
        from rag_pymc.embeddings.sentence_transformer import SentenceTransformerEmbedder

        chunks = _load_corpus_chunks(corpus_dir)
        spec = load_embedding_model_spec(model_manifest)
        setup_started_at = perf_counter_ns()
        embedder = SentenceTransformerEmbedder(
            spec,
            device=device,
            batch_size=batch_size,
            seed=seed,
            local_files_only=local_files_only,
        )
        retriever = DenseRetriever(ExactCosineIndex(chunks, embedder=embedder))
        setup_latency_ms = (perf_counter_ns() - setup_started_at) / 1_000_000
        query = _build_search_query(
            query_text, top_k, library, library_version, source_types, api_symbols
        )
        results = retriever.retrieve(query)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"dense search failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("rag-pymc search-dense")
    typer.echo(f"query: {query.text}")
    typer.echo(f"model: {spec.model_id}@{spec.revision}")
    typer.echo(f"setup_latency_ms: {setup_latency_ms:.6f}")
    typer.echo(f"matches: {len(results)}")
    for result in results:
        chunk = result.chunk
        typer.echo(
            f"{result.rank}. {chunk.title} [{chunk.section or 'Unsectioned'}] "
            f"score={result.score:.6f}"
        )
        typer.echo(
            f"   chunk={chunk.chunk_id} library={chunk.library} version={chunk.library_version}"
        )
        typer.echo(f"   source={chunk.source_url}")
    typer.echo("status: ok")


@app.command("evaluate-dense")
def evaluate_dense(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/evaluation/phase2/pymc_sample_queries.jsonl"),
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/local"),
    model_manifest: Annotated[
        Path,
        typer.Option("--model-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"),
    dense_output: Annotated[
        Path,
        typer.Option("--dense-output", dir_okay=False),
    ] = Path("reports/evaluation/phase3-dense-baseline.json"),
    comparison_output: Annotated[
        Path,
        typer.Option("--comparison-output", dir_okay=False),
    ] = Path("reports/evaluation/phase3-sparse-vs-dense.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 3,
    seed: Annotated[int, typer.Option("--seed")] = 20260719,
    device: Annotated[str, typer.Option("--device")] = "cpu",
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 16,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Evaluate dense retrieval and compare it with the fixed BM25 policy."""
    try:
        from rag_pymc.embeddings.sentence_transformer import SentenceTransformerEmbedder

        chunks = _load_corpus_chunks(corpus_dir)
        queries = load_evaluation_queries(dataset_path)
        spec = load_embedding_model_spec(model_manifest)
        tokenizer = TechnicalTokenizer()

        setup_started_at = perf_counter_ns()
        embedder = SentenceTransformerEmbedder(
            spec,
            device=device,
            batch_size=batch_size,
            seed=seed,
            local_files_only=local_files_only,
        )
        dense_index = ExactCosineIndex(chunks, embedder=embedder)
        setup_latency_ms = (perf_counter_ns() - setup_started_at) / 1_000_000
        truncated_document_count = sum(
            embedder.token_count(chunk.content) > spec.max_sequence_length for chunk in chunks
        )
        dense_config = build_dense_experiment_config(
            chunks,
            index=dense_index,
            spec=spec,
            truncated_document_count=truncated_document_count,
            seed=seed,
            top_k=top_k,
            device=device,
            batch_size=batch_size,
        )
        dense_report = RetrievalEvaluator(
            retriever=DenseRetriever(dense_index),
            chunks=chunks,
            tokenizer=tokenizer,
            config=dense_config,
            experiment_id="phase3-dense-baseline",
            setup_latency_ms=setup_latency_ms,
            limitations=(
                "The corpus contains one PyMC API page and five semantic chunks.",
                "The model truncates inputs beyond 512 word pieces.",
                "The Parameters chunk is longer than the embedding model input window.",
                "No similarity threshold or learned abstention policy is applied.",
                "Model download time is excluded from setup and query latency.",
            ),
        ).evaluate(queries, dataset_path=dataset_path)

        sparse_index = BM25Index(chunks, tokenizer=tokenizer, k1=1.5, b=0.75)
        sparse_config = build_sparse_experiment_config(
            chunks,
            index=sparse_index,
            tokenizer=tokenizer,
            seed=seed,
            top_k=top_k,
        )
        sparse_report = RetrievalEvaluator(
            retriever=SparseRetriever(sparse_index),
            chunks=chunks,
            tokenizer=tokenizer,
            config=sparse_config,
            experiment_id="phase3-bm25-control",
        ).evaluate(queries, dataset_path=dataset_path)
        comparison = compare_retrieval_reports(sparse_report, dense_report)

        write_experiment_report(dense_report, dense_output)
        write_comparison_report(comparison, comparison_output)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"dense evaluation failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    metrics = dense_report.metrics
    typer.echo("rag-pymc evaluate-dense")
    typer.echo(f"dataset: {dataset_path}")
    typer.echo(f"model: {spec.model_id}@{spec.revision}")
    typer.echo(f"queries: {metrics.query_count}")
    typer.echo(f"recall@{top_k}: {metrics.recall_at_k:.6f}")
    typer.echo(f"mrr: {metrics.mrr:.6f}")
    typer.echo(f"ndcg@{top_k}: {metrics.ndcg_at_k:.6f}")
    typer.echo(f"correct_abstention: {metrics.correct_abstention_rate:.6f}")
    typer.echo(f"mrr_delta_vs_bm25: {comparison.metric_deltas['mrr']:.6f}")
    typer.echo(f"dense_output: {dense_output}")
    typer.echo(f"comparison_output: {comparison_output}")
    typer.echo("status: ok")


@app.command("search-hybrid")
def search_hybrid(
    query_text: Annotated[str, typer.Argument(help="Natural-language retrieval query.")],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/phase4"),
    model_manifest: Annotated[
        Path,
        typer.Option("--model-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 5,
    candidate_k: Annotated[int, typer.Option("--candidate-k", min=1, max=100)] = 10,
    rrf_k: Annotated[int, typer.Option("--rrf-k", min=1)] = 60,
    sparse_weight: Annotated[float, typer.Option("--sparse-weight", min=0.000001)] = 1.0,
    dense_weight: Annotated[float, typer.Option("--dense-weight", min=0.000001)] = 1.0,
    library: Annotated[str | None, typer.Option("--library")] = None,
    library_version: Annotated[str | None, typer.Option("--library-version")] = None,
    source_types: Annotated[
        list[SourceType] | None,
        typer.Option("--source-type"),
    ] = None,
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
    device: Annotated[str, typer.Option("--device")] = "cpu",
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 16,
    seed: Annotated[int, typer.Option("--seed")] = 20260720,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Search with weighted Reciprocal Rank Fusion over BM25 and dense retrieval."""
    try:
        chunks = _load_corpus_chunks(corpus_dir)
        runtime = build_hybrid_runtime(
            chunks,
            embedding_manifest=model_manifest,
            candidate_k=candidate_k,
            rrf_k=rrf_k,
            sparse_weight=sparse_weight,
            dense_weight=dense_weight,
            seed=seed,
            device=device,
            batch_size=batch_size,
            local_files_only=local_files_only,
        )
        query = _build_search_query(
            query_text, top_k, library, library_version, source_types, api_symbols
        )
        results = runtime.retriever.retrieve(query)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"hybrid search failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("rag-pymc search-hybrid")
    typer.echo(f"query: {query.text}")
    typer.echo(f"model: {runtime.embedding_spec.model_id}@{runtime.embedding_spec.revision}")
    typer.echo(f"rrf_k: {rrf_k}")
    typer.echo(f"candidate_k: {candidate_k}")
    typer.echo(f"setup_latency_ms: {runtime.setup_latency_ms:.6f}")
    typer.echo(f"matches: {len(results)}")
    for result in results:
        chunk = result.chunk
        typer.echo(
            f"{result.rank}. {chunk.title} [{chunk.section or 'Unsectioned'}] "
            f"score={result.score:.8f}"
        )
        typer.echo(
            f"   chunk={chunk.chunk_id} library={chunk.library} version={chunk.library_version}"
        )
        typer.echo(f"   source={chunk.source_url}")
    typer.echo("status: ok")


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
    ] = Path("datasets/processed/phase4"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=10)] = 3,
    library: Annotated[str, typer.Option("--library")] = "pymc",
    library_version: Annotated[str, typer.Option("--library-version")] = "6.1.0",
    source_types: Annotated[
        list[SourceType] | None,
        typer.Option("--source-type"),
    ] = None,
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Retrieve and print deterministic, budget-bounded context as JSON."""
    try:
        query = _build_search_query(
            query_text, top_k, library, library_version, source_types, api_symbols
        )
        chunks = _load_corpus_chunks(corpus_dir)
        runtime = build_hybrid_runtime(
            chunks,
            embedding_manifest=DEFAULT_EMBEDDING_MANIFEST,
            candidate_k=10,
            rrf_k=60,
            sparse_weight=1.0,
            dense_weight=1.0,
            seed=20260720,
            device="cpu",
            batch_size=16,
            local_files_only=local_files_only,
        )
        service = ContextInspectionService(
            runtime.retriever,
            RankedContextBuilder(runtime.tokenizer),
        )
        context = service.inspect(query, token_budget=token_budget)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"context inspection failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(context.model_dump_json(indent=2))


@app.command("evaluate-hybrid")
def evaluate_hybrid(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/evaluation/phase4/pymc_core_queries.jsonl"),
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/phase4"),
    model_manifest: Annotated[
        Path,
        typer.Option("--model-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"),
    sparse_output: Annotated[
        Path,
        typer.Option("--sparse-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-bm25-expanded.json"),
    dense_output: Annotated[
        Path,
        typer.Option("--dense-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-dense-expanded.json"),
    hybrid_output: Annotated[
        Path,
        typer.Option("--hybrid-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-hybrid-rrf.json"),
    bm25_comparison_output: Annotated[
        Path,
        typer.Option("--bm25-comparison-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-bm25-vs-hybrid.json"),
    dense_comparison_output: Annotated[
        Path,
        typer.Option("--dense-comparison-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-dense-vs-hybrid.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 3,
    candidate_k: Annotated[int, typer.Option("--candidate-k", min=1, max=100)] = 10,
    rrf_k: Annotated[int, typer.Option("--rrf-k", min=1)] = 60,
    sparse_weight: Annotated[float, typer.Option("--sparse-weight", min=0.000001)] = 1.0,
    dense_weight: Annotated[float, typer.Option("--dense-weight", min=0.000001)] = 1.0,
    seed: Annotated[int, typer.Option("--seed")] = 20260720,
    device: Annotated[str, typer.Option("--device")] = "cpu",
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 16,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Evaluate BM25, dense retrieval, and weighted RRF on one benchmark."""
    try:
        from rag_pymc.embeddings.sentence_transformer import SentenceTransformerEmbedder

        chunks = _load_corpus_chunks(corpus_dir)
        queries = load_evaluation_queries(dataset_path)
        spec = load_embedding_model_spec(model_manifest)
        tokenizer = TechnicalTokenizer()
        document_count = len({chunk.document_id for chunk in chunks})

        total_setup_started_at = perf_counter_ns()
        sparse_index = BM25Index(chunks, tokenizer=tokenizer, k1=1.5, b=0.75)
        dense_setup_started_at = perf_counter_ns()
        embedder = SentenceTransformerEmbedder(
            spec,
            device=device,
            batch_size=batch_size,
            seed=seed,
            local_files_only=local_files_only,
        )
        dense_index = ExactCosineIndex(chunks, embedder=embedder)
        dense_setup_latency_ms = (perf_counter_ns() - dense_setup_started_at) / 1_000_000
        sparse_retriever = SparseRetriever(sparse_index)
        dense_retriever = DenseRetriever(dense_index)
        hybrid_retriever = ReciprocalRankFusionRetriever(
            (
                WeightedRetriever("sparse", sparse_retriever, sparse_weight),
                WeightedRetriever("dense", dense_retriever, dense_weight),
            ),
            rrf_k=rrf_k,
            candidate_k=candidate_k,
        )
        hybrid_setup_latency_ms = (perf_counter_ns() - total_setup_started_at) / 1_000_000
        truncated_document_count = sum(
            embedder.token_count(chunk.content) > spec.max_sequence_length for chunk in chunks
        )

        sparse_config = build_sparse_experiment_config(
            chunks,
            index=sparse_index,
            tokenizer=tokenizer,
            seed=seed,
            top_k=top_k,
        )
        dense_config = build_dense_experiment_config(
            chunks,
            index=dense_index,
            spec=spec,
            truncated_document_count=truncated_document_count,
            seed=seed,
            top_k=top_k,
            device=device,
            batch_size=batch_size,
        )
        hybrid_config = build_hybrid_experiment_config(
            chunks,
            retriever_name=hybrid_retriever.name,
            sparse=sparse_config,
            dense=dense_config,
            candidate_k=candidate_k,
            rrf_k=rrf_k,
            sparse_weight=sparse_weight,
            dense_weight=dense_weight,
            seed=seed,
            top_k=top_k,
        )
        common_limitations = (
            f"The corpus contains {document_count} PyMC API pages and {len(chunks)} chunks.",
            "The dataset was curated for this corpus and is not an external benchmark.",
            f"The embedding model truncates {truncated_document_count} chunks beyond "
            f"{spec.max_sequence_length} word pieces.",
            "No score threshold or learned abstention policy is applied.",
            "Model download time is excluded from setup and query latency.",
        )
        sparse_report = RetrievalEvaluator(
            retriever=sparse_retriever,
            chunks=chunks,
            tokenizer=tokenizer,
            config=sparse_config,
            experiment_id="phase4-bm25-expanded",
            limitations=common_limitations,
        ).evaluate(queries, dataset_path=dataset_path)
        dense_report = RetrievalEvaluator(
            retriever=dense_retriever,
            chunks=chunks,
            tokenizer=tokenizer,
            config=dense_config,
            experiment_id="phase4-dense-expanded",
            setup_latency_ms=dense_setup_latency_ms,
            limitations=common_limitations,
        ).evaluate(queries, dataset_path=dataset_path)
        hybrid_report = RetrievalEvaluator(
            retriever=hybrid_retriever,
            chunks=chunks,
            tokenizer=tokenizer,
            config=hybrid_config,
            experiment_id="phase4-hybrid-rrf",
            setup_latency_ms=hybrid_setup_latency_ms,
            limitations=(
                *common_limitations,
                "Sparse and dense ranks are fused with fixed equal weights.",
                "No cross-encoder reranker is applied in this baseline.",
            ),
        ).evaluate(queries, dataset_path=dataset_path)

        comparison_limitations = (
            f"All arms use the same {document_count}-document, {len(chunks)}-chunk corpus.",
            "All arms use the same dataset, qrels, metadata filters, and top-k.",
            "Latency excludes one-time model download and is machine-specific.",
        )
        bm25_comparison = compare_retrieval_reports(
            sparse_report,
            hybrid_report,
            experiment_id="phase4-bm25-vs-hybrid",
            limitations=comparison_limitations,
        )
        dense_comparison = compare_retrieval_reports(
            dense_report,
            hybrid_report,
            experiment_id="phase4-dense-vs-hybrid",
            limitations=comparison_limitations,
        )

        write_experiment_report(sparse_report, sparse_output)
        write_experiment_report(dense_report, dense_output)
        write_experiment_report(hybrid_report, hybrid_output)
        write_comparison_report(bm25_comparison, bm25_comparison_output)
        write_comparison_report(dense_comparison, dense_comparison_output)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        EvaluationError,
        OSError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"hybrid evaluation failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    metrics = hybrid_report.metrics
    typer.echo("rag-pymc evaluate-hybrid")
    typer.echo(f"dataset: {dataset_path}")
    typer.echo(f"model: {spec.model_id}@{spec.revision}")
    typer.echo(f"queries: {metrics.query_count}")
    typer.echo(f"recall@{top_k}: {metrics.recall_at_k:.6f}")
    typer.echo(f"mrr: {metrics.mrr:.6f}")
    typer.echo(f"ndcg@{top_k}: {metrics.ndcg_at_k:.6f}")
    typer.echo(f"correct_abstention: {metrics.correct_abstention_rate:.6f}")
    typer.echo(f"mrr_delta_vs_bm25: {bm25_comparison.metric_deltas['mrr']:.6f}")
    typer.echo(f"mrr_delta_vs_dense: {dense_comparison.metric_deltas['mrr']:.6f}")
    typer.echo(f"hybrid_output: {hybrid_output}")
    typer.echo(f"bm25_comparison_output: {bm25_comparison_output}")
    typer.echo(f"dense_comparison_output: {dense_comparison_output}")
    typer.echo("status: ok")


@app.command("search-reranked")
def search_reranked(
    query_text: Annotated[str, typer.Argument(help="Natural-language retrieval query.")],
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/phase4"),
    embedding_manifest: Annotated[
        Path,
        typer.Option("--embedding-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"),
    reranker_manifest: Annotated[
        Path,
        typer.Option("--reranker-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/rerankers/ms-marco-MiniLM-L6-v2.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 5,
    fusion_candidate_k: Annotated[
        int,
        typer.Option("--fusion-candidate-k", min=1, max=100),
    ] = 10,
    rerank_candidate_k: Annotated[
        int,
        typer.Option("--rerank-candidate-k", min=1, max=100),
    ] = 10,
    library: Annotated[str | None, typer.Option("--library")] = None,
    library_version: Annotated[str | None, typer.Option("--library-version")] = None,
    source_types: Annotated[
        list[SourceType] | None,
        typer.Option("--source-type"),
    ] = None,
    api_symbols: Annotated[
        list[str] | None,
        typer.Option("--api-symbol"),
    ] = None,
    device: Annotated[str, typer.Option("--device")] = "cpu",
    embedding_batch_size: Annotated[
        int,
        typer.Option("--embedding-batch-size", min=1),
    ] = 16,
    reranking_batch_size: Annotated[
        int,
        typer.Option("--reranking-batch-size", min=1),
    ] = 16,
    seed: Annotated[int, typer.Option("--seed")] = 20260720,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Search hybrid candidates and rerank them with a pinned cross-encoder."""
    try:
        chunks = _load_corpus_chunks(corpus_dir)
        runtime = build_reranking_runtime(
            chunks,
            embedding_manifest=embedding_manifest,
            reranking_manifest=reranker_manifest,
            top_k=top_k,
            fusion_candidate_k=fusion_candidate_k,
            rerank_candidate_k=rerank_candidate_k,
            rrf_k=60,
            sparse_weight=1.0,
            dense_weight=1.0,
            seed=seed,
            device=device,
            embedding_batch_size=embedding_batch_size,
            reranking_batch_size=reranking_batch_size,
            local_files_only=local_files_only,
        )
        query = _build_search_query(
            query_text, top_k, library, library_version, source_types, api_symbols
        )
        results = runtime.reranked_retriever.retrieve(query)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        OSError,
        RerankingError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"reranked search failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("rag-pymc search-reranked")
    typer.echo(f"query: {query.text}")
    typer.echo(
        f"embedding_model: {runtime.embedding_spec.model_id}@{runtime.embedding_spec.revision}"
    )
    typer.echo(
        f"reranker_model: {runtime.reranking_spec.model_id}@{runtime.reranking_spec.revision}"
    )
    typer.echo(f"candidate_k: {rerank_candidate_k}")
    typer.echo(f"setup_latency_ms: {runtime.setup_latency_ms:.6f}")
    typer.echo(f"matches: {len(results)}")
    for result in results:
        chunk = result.chunk
        typer.echo(
            f"{result.rank}. {chunk.title} [{chunk.section or 'Unsectioned'}] "
            f"score={result.score:.6f}"
        )
        typer.echo(
            f"   chunk={chunk.chunk_id} library={chunk.library} version={chunk.library_version}"
        )
        typer.echo(f"   source={chunk.source_url}")
    typer.echo("status: ok")


@app.command("evaluate-reranked")
def evaluate_reranked(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/evaluation/phase4/pymc_core_queries.jsonl"),
    corpus_dir: Annotated[
        Path,
        typer.Option("--corpus-dir", file_okay=False),
    ] = Path("datasets/processed/phase4"),
    embedding_manifest: Annotated[
        Path,
        typer.Option("--embedding-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"),
    reranker_manifest: Annotated[
        Path,
        typer.Option("--reranker-manifest", exists=True, dir_okay=False, readable=True),
    ] = Path("datasets/raw/manifests/rerankers/ms-marco-MiniLM-L6-v2.json"),
    candidate_output: Annotated[
        Path,
        typer.Option("--candidate-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-hybrid-reranker-control.json"),
    reranked_output: Annotated[
        Path,
        typer.Option("--reranked-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-cross-encoder-reranked.json"),
    comparison_output: Annotated[
        Path,
        typer.Option("--comparison-output", dir_okay=False),
    ] = Path("reports/evaluation/phase4-hybrid-vs-reranked.json"),
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 3,
    fusion_candidate_k: Annotated[
        int,
        typer.Option("--fusion-candidate-k", min=1, max=100),
    ] = 10,
    rerank_candidate_k: Annotated[
        int,
        typer.Option("--rerank-candidate-k", min=1, max=100),
    ] = 10,
    seed: Annotated[int, typer.Option("--seed")] = 20260720,
    device: Annotated[str, typer.Option("--device")] = "cpu",
    embedding_batch_size: Annotated[
        int,
        typer.Option("--embedding-batch-size", min=1),
    ] = 16,
    reranking_batch_size: Annotated[
        int,
        typer.Option("--reranking-batch-size", min=1),
    ] = 16,
    local_files_only: Annotated[
        bool,
        typer.Option("--local-files-only/--allow-download"),
    ] = True,
) -> None:
    """Evaluate cross-encoder reranking against a fresh hybrid control."""
    try:
        chunks = _load_corpus_chunks(corpus_dir)
        queries = load_evaluation_queries(dataset_path)
        runtime = build_reranking_runtime(
            chunks,
            embedding_manifest=embedding_manifest,
            reranking_manifest=reranker_manifest,
            top_k=top_k,
            fusion_candidate_k=fusion_candidate_k,
            rerank_candidate_k=rerank_candidate_k,
            rrf_k=60,
            sparse_weight=1.0,
            dense_weight=1.0,
            seed=seed,
            device=device,
            embedding_batch_size=embedding_batch_size,
            reranking_batch_size=reranking_batch_size,
            local_files_only=local_files_only,
        )
        document_count = len({chunk.document_id for chunk in chunks})
        common_limitations = (
            f"The corpus contains {document_count} PyMC API pages and {len(chunks)} chunks.",
            "The dataset was curated for this corpus and is not an external benchmark.",
            f"The embedding model truncates {runtime.truncated_document_count} chunks beyond "
            f"{runtime.embedding_spec.max_sequence_length} word pieces.",
            "No score threshold or learned abstention policy is applied.",
            "Model download time is excluded from setup and query latency.",
        )
        candidate_report = RetrievalEvaluator(
            retriever=runtime.candidate_retriever,
            chunks=chunks,
            tokenizer=runtime.tokenizer,
            config=runtime.candidate_config,
            experiment_id="phase4-hybrid-reranker-control",
            setup_latency_ms=runtime.candidate_setup_latency_ms,
            limitations=(
                *common_limitations,
                "Sparse and dense ranks are fused with fixed equal weights.",
                "No cross-encoder is applied in this control arm.",
            ),
        ).evaluate(queries, dataset_path=dataset_path)
        reranked_report = RetrievalEvaluator(
            retriever=runtime.reranked_retriever,
            chunks=chunks,
            tokenizer=runtime.tokenizer,
            config=runtime.reranked_config,
            experiment_id="phase4-cross-encoder-reranked",
            setup_latency_ms=runtime.setup_latency_ms,
            limitations=(
                *common_limitations,
                f"The cross-encoder truncates query-document pairs beyond "
                f"{runtime.reranking_spec.max_sequence_length} word pieces.",
                "The general English MS MARCO model was not trained specifically on PyMC.",
                "Ten equal-weight RRF candidates are reranked with raw relevance logits.",
            ),
        ).evaluate(queries, dataset_path=dataset_path)
        comparison = compare_retrieval_reports(
            candidate_report,
            reranked_report,
            experiment_id="phase4-hybrid-vs-reranked",
            limitations=(
                f"Both arms use the same {document_count}-document, {len(chunks)}-chunk corpus.",
                "Both arms use the same dataset, qrels, metadata filters, and top-k.",
                "The candidate arm returns RRF top-k; the reranked arm scores RRF top-10.",
                "Latency excludes one-time model downloads and is machine-specific.",
            ),
        )

        write_experiment_report(candidate_report, candidate_output)
        write_experiment_report(reranked_report, reranked_output)
        write_comparison_report(comparison, comparison_output)
    except (
        CorpusPersistenceError,
        DenseIndexError,
        EmbeddingError,
        EvaluationError,
        OSError,
        RerankingError,
        ValidationError,
        ValueError,
    ) as error:
        typer.echo(f"reranked evaluation failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    metrics = reranked_report.metrics
    typer.echo("rag-pymc evaluate-reranked")
    typer.echo(f"dataset: {dataset_path}")
    typer.echo(
        f"reranker_model: {runtime.reranking_spec.model_id}@{runtime.reranking_spec.revision}"
    )
    typer.echo(f"queries: {metrics.query_count}")
    typer.echo(f"recall@{top_k}: {metrics.recall_at_k:.6f}")
    typer.echo(f"mrr: {metrics.mrr:.6f}")
    typer.echo(f"ndcg@{top_k}: {metrics.ndcg_at_k:.6f}")
    typer.echo(f"correct_abstention: {metrics.correct_abstention_rate:.6f}")
    typer.echo(f"mrr_delta_vs_hybrid: {comparison.metric_deltas['mrr']:.6f}")
    typer.echo(f"candidate_output: {candidate_output}")
    typer.echo(f"reranked_output: {reranked_output}")
    typer.echo(f"comparison_output: {comparison_output}")
    typer.echo("status: ok")
