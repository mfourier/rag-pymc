from pathlib import Path

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import SearchQuery, SourceManifest, SourceType
from rag_pymc.indexing import BM25Index
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository
from rag_pymc.retrieval import SparseRetriever, TechnicalTokenizer


def test_real_sparse_retrieval_builds_deterministic_bounded_context(
    source_manifest: SourceManifest,
    source_path: Path,
    tmp_path: Path,
) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    ingestion_result = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=SphinxApiParser(),
        chunker=ApiReferenceChunker(),
        repository=repository,
    ).run(source_manifest)
    chunks = repository.load_chunks()
    tokenizer = TechnicalTokenizer()
    retriever = SparseRetriever(BM25Index(chunks, tokenizer=tokenizer))
    query = SearchQuery(
        text="How do draws and tune configure pymc.sample?",
        top_k=3,
        library="pymc",
        library_version="6.1.0",
        source_types=(SourceType.API_REFERENCE,),
        api_symbols=("pymc.sample",),
    )
    token_budget = 100_000

    retrieved = retriever.retrieve(query)
    first = RankedContextBuilder(tokenizer).build(
        query,
        retrieved,
        token_budget=token_budget,
    )
    repeated = RankedContextBuilder(tokenizer).build(
        query,
        retriever.retrieve(query),
        token_budget=token_budget,
    )

    assert retrieved
    assert first.items
    assert first.included_chunk_ids == tuple(result.chunk.chunk_id for result in retrieved)
    assert first.omitted_chunk_ids == ()
    assert first.used_tokens == sum(item.token_count for item in first.items)
    assert 0 < first.used_tokens <= first.token_budget == token_budget

    for item, result in zip(first.items, retrieved, strict=True):
        chunk = result.chunk
        assert item.chunk_id == chunk.chunk_id
        assert item.document_id == chunk.document_id == ingestion_result.document.document_id
        assert item.source_url == chunk.source_url == source_manifest.source_url
        assert item.library == chunk.library == source_manifest.library
        assert item.library_version == chunk.library_version == source_manifest.library_version
        assert item.source_type == chunk.source_type == source_manifest.source_type
        assert item.section == chunk.section
        assert item.api_symbols == chunk.api_symbols == ("pymc.sample",)
        assert item.token_count == tokenizer.count_tokens(item.rendered_text)

    assert first.model_dump_json() == repeated.model_dump_json()
