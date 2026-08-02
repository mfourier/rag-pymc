"""Reproducible conservative baseline for the governed Phase 5 single review."""

import os
import tempfile
from collections.abc import Sequence
from pathlib import Path

from rag_pymc.abstention import ConservativeAbstentionPolicy
from rag_pymc.application.retrieval_runtime import build_sparse_runtime
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import Chunk, SearchQuery, SourceType
from rag_pymc.evaluation.errors import EvaluationDatasetError
from tools.development_dataset import hash_phase5_corpus
from tools.development_models import (
    Phase5SingleReviewDataset,
    Phase5SingleReviewGoldEvidenceEvaluationReport,
)
from tools.gold_evidence import (
    aggregate_single_review_gold_evidence,
    evaluate_single_review_gold_evidence,
)

DEFAULT_TOP_K = 3
DEFAULT_TOKEN_BUDGET = 2048
DEFAULT_K1 = 1.5
DEFAULT_B = 0.75

_LIMITATIONS = tuple(
    sorted(
        (
            "Accepted labels, claims, and support sets were reviewed by one human and were not "
            "independently adjudicated.",
            "BM25 rank and chunk-identity coverage do not establish semantic support, scientific "
            "correctness, citation correctness, or answer usefulness.",
            "This exploratory development baseline is not held out or production-grade.",
            "This baseline records the unchanged conservative policy and does not select or "
            "authorize an evidence-sufficiency threshold.",
        )
    )
)


def build_phase5_single_review_conservative_baseline(
    dataset: Phase5SingleReviewDataset,
    chunks: Sequence[Chunk],
    *,
    top_k: int = DEFAULT_TOP_K,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    k1: float = DEFAULT_K1,
    b: float = DEFAULT_B,
) -> Phase5SingleReviewGoldEvidenceEvaluationReport:
    """Run BM25, deterministic context construction, and fail-closed assessment."""
    dataset = Phase5SingleReviewDataset.model_validate(dataset)
    validated_chunks = tuple(Chunk.model_validate(chunk) for chunk in chunks)
    _validate_corpus_binding(dataset, validated_chunks)

    runtime = build_sparse_runtime(validated_chunks, k1=k1, b=b)
    context_builder = RankedContextBuilder(runtime.tokenizer)
    policy = ConservativeAbstentionPolicy()
    evaluations = []
    for example in dataset.examples:
        query = SearchQuery(
            text=example.query_text,
            top_k=top_k,
            library=example.library,
            library_version=example.library_version,
            source_types=(SourceType.API_REFERENCE,),
        )
        retrieved = runtime.retriever.retrieve(query)
        context = context_builder.build(query, retrieved, token_budget=token_budget)
        assessment = policy.assess(context)
        evaluations.append(
            evaluate_single_review_gold_evidence(
                example,
                context,
                assessment,
                corpus_sha256=dataset.corpus_sha256,
            )
        )

    return aggregate_single_review_gold_evidence(
        dataset,
        evaluations,
        corpus_chunk_count=len(validated_chunks),
        retriever_version=runtime.index.name,
        tokenizer_version=runtime.tokenizer.name,
        k1=runtime.index.k1,
        b=runtime.index.b,
        top_k=top_k,
        context_builder_version=context_builder.name,
        context_rendering_policy=context_builder.rendering_policy,
        context_truncation_policy=context_builder.truncation_policy,
        token_budget=token_budget,
        limitations=_LIMITATIONS,
    )


def write_phase5_single_review_conservative_baseline(
    report: Phase5SingleReviewGoldEvidenceEvaluationReport,
    path: Path,
) -> None:
    """Atomically persist one completely validated machine-readable baseline."""
    report = Phase5SingleReviewGoldEvidenceEvaluationReport.model_validate(report)
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            text=True,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(report.model_dump_json(indent=2))
            output.write("\n")
        os.replace(temporary_path, path)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        msg = f"unable to write Phase 5 single-review conservative baseline: {path}"
        raise EvaluationDatasetError(msg) from error


def _validate_corpus_binding(
    dataset: Phase5SingleReviewDataset,
    chunks: tuple[Chunk, ...],
) -> None:
    if not chunks:
        raise EvaluationDatasetError("single-review baseline corpus must not be empty")
    observed_hash = hash_phase5_corpus(chunks)
    if observed_hash != dataset.corpus_sha256:
        msg = "single-review baseline corpus SHA-256 does not match the reviewed dataset"
        raise EvaluationDatasetError(msg)
    examples_by_library = {
        (item.library.casefold(), item.library_version) for item in dataset.examples
    }
    if len(examples_by_library) != 1:
        msg = "single-review baseline requires one reviewed library-version boundary"
        raise EvaluationDatasetError(msg)
    expected_library, expected_version = next(iter(examples_by_library))
    if any(
        chunk.library.casefold() != expected_library or chunk.library_version != expected_version
        for chunk in chunks
    ):
        msg = "single-review baseline corpus crosses the reviewed library-version boundary"
        raise EvaluationDatasetError(msg)
    chunk_ids = {chunk.chunk_id for chunk in chunks}
    missing_support = next(
        (
            chunk_id
            for example in dataset.examples
            for claim in example.gold_claims
            for support_set in claim.support_sets
            for chunk_id in support_set.chunk_ids
            if chunk_id not in chunk_ids
        ),
        None,
    )
    if missing_support is not None:
        msg = f"single-review baseline references missing support chunk {missing_support}"
        raise EvaluationDatasetError(msg)
