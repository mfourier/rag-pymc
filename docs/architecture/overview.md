# Architecture overview

## Purpose

`rag-pymc` is an adaptive technical tutor grounded in versioned official PyMC, ArviZ, and
PyTensor sources. It must support reproducible retrieval experiments and eventually combine
cited evidence, pedagogical policies, and controlled code execution. The initial architecture
prioritizes explicit contracts and traceability over feature breadth.

## Dependency direction

```text
CLI / future API
        |
        v
Application use cases (introduced with working features)
        |
        v
Domain models and protocols
        ^
        |
Infrastructure adapters
```

The domain does not import CLI, persistence, model providers, vector stores, or orchestration
frameworks. Infrastructure satisfies project-owned protocols and converts external values at
the boundary. Presentation layers call application use cases rather than storage or indexes
directly.

Phases 1 through 4 and the first Phase 5 slice add only packages with exercised behavior. The
CLI calls project-owned services and protocols, while the domain remains independent of
Beautiful Soup, filesystems, JSONL, ranking implementations, embedding providers, and
presentation concerns.

## Architecture through the initial Phase 5 slice

### Phase 0: Foundation

- Immutable Pydantic models define `Document`, `Chunk`, `SearchQuery`, and
  `RetrievedChunk`.
- The `rag-pymc doctor` command verifies the runtime and pinned scientific stack.
- Ruff, mypy, pytest, pre-commit, and `uv.lock` provide a reproducible quality baseline.
- Architecture decisions live in versioned ADRs.

### Phase 1: One-source ingestion slice

The implemented vertical slice ingests the official PyMC 6.1.0 `pymc.sample` API page. It
does not crawl the documentation site. It contains:

- a `SourceManifest` with URL, release, commit, server timestamp, acquisition timestamp,
  license, expected symbol, media type, and raw SHA-256;
- a `SourceFetcher` boundary whose local implementation verifies bytes before parsing;
- a `SphinxApiParser` that emits Overview, Parameters, Returns, Notes, and Examples while
  preserving complete code blocks;
- an `ApiReferenceChunker` that creates one retrieval unit per semantic section;
- deterministic document and chunk IDs plus parser and chunker versions;
- an `IngestionService` that composes the four project-owned protocols;
- a `JsonlDocumentRepository` with deterministic upsert behavior;
- the offline `rag-pymc ingest` command and checked-in fixtures.

The Parameters section remains one chunk. Phase 2 now measures its retrieval-token cost, so
per-parameter child chunks can be evaluated as a controlled experiment instead of assumed.

### Phase 2: Sparse retrieval baseline

The implemented sparse baseline contains:

- a technical tokenizer and explicit Okapi BM25 index behind `SparseIndex`;
- a common `Retriever` boundary returning ranked `RetrievedChunk` values;
- exact pre-ranking filters for library version and source type plus library and API-symbol
  filters;
- a versioned 20-query dataset with binary qrels and unanswerable questions;
- Recall@k, Precision@k, Hit Rate, MRR, nDCG, version correctness, correct abstention,
  latency, and retrieved-token measurements;
- `rag-pymc search` and `rag-pymc evaluate` commands;
- a JSON experiment artifact containing config, hashes, versions, per-query results, and
  declared limitations.

The implementation and metric conventions are fixed in ADR-0004. The stored baseline report
is documented in `docs/evaluation/phase2-sparse-baseline.md`.

### Phase 3: Dense retrieval baseline

The implemented dense baseline contains:

- an `Embedder` protocol that separates query and document encoding;
- a manifest-validated Sentence Transformers adapter for
  `BAAI/bge-small-en-v1.5` at one immutable model revision;
- normalized 384-dimensional embeddings, an explicit retrieval query prefix, CPU execution,
  and external model caching;
- an immutable exact-cosine index behind the project-owned `DenseIndex` protocol;
- shared metadata filtering across sparse and dense retrieval;
- `rag-pymc search-dense` and `rag-pymc evaluate-dense` commands;
- a comparison artifact that verifies common corpus, dataset, queries, and `top_k` before
  computing metric deltas and per-query outcomes;
- recorded setup latency, query latency, model versions, and count of documents exceeding the
  model's input window.

The dense baseline uses the unchanged Phase 2 corpus and qrels. It is not an approximate
vector index and does not persist embeddings. ADR-0005 fixes the model, input policy, CPU
dependency source, and exact-search decision. Measured results and error analysis are in
`docs/evaluation/phase3-dense-baseline.md`.

### Phase 4: Hybrid retrieval and reranking

The implemented retrieval phase contains:

- an expanded controlled corpus with four PyMC 6.1.0 API pages and 15 chunks while retaining
  source-level hashes, release, commit, license, and acquisition metadata;
- a versioned 30-query dataset with 27 answerable and three unanswerable questions;
- weighted Reciprocal Rank Fusion over project-owned retriever interfaces;
- validation of unique components, positive weights, duplicate ranks, and payload conflicts;
- `rag-pymc search-hybrid` and `rag-pymc evaluate-hybrid` commands;
- category-level metrics by intent and difficulty, including zero-answerable slices without
  fabricating retrieval quality;
- pairwise artifacts comparing the hybrid candidate with fresh BM25 and dense controls using
  shared corpus and dataset hashes;
- a project-owned `Reranker` protocol and `RerankedRetriever` candidate adapter;
- a manifest-validated Sentence Transformers cross-encoder at an immutable revision;
- `rag-pymc search-reranked` and `rag-pymc evaluate-reranked` commands;
- a separate comparison between frozen RRF candidates and cross-encoder reranking.

The equal-weight RRF baseline uses candidate depth 10, `rrf_k=60`, and `top_k=3`. It does
not apply score calibration or a threshold. ADR-0006 fixes the fusion policy and experimental
sequence. ADR-0007 fixes and evaluates the cross-encoder, which remains available but is not
adopted as the default because measured quality decreases. Results and error analysis are in
`docs/evaluation/phase4-hybrid-baseline.md`.

### Phase 5: Deterministic context construction

The first grounded-response slice contains:

- immutable `ContextItem` and `ConstructedContext` domain models;
- project-owned `ContextBuilder` and `TokenCounter` protocols;
- canonical ordering by retrieval rank and chunk ID;
- duplicate suppression by chunk ID with explicit conflicting-payload rejection;
- a versioned rendering that preserves source URL, library version, section, API symbols,
  retrieval provenance, and complete chunk content;
- additive per-item budgeting with the deterministic `technical-v1` accounting policy;
- complete-item rank-prefix admission with explicit tail omission and no content truncation;
- fail-closed validation that admits only one normalized library and one version of each
  library before budgeting.

The returned value has no timestamp or latency, so fixed inputs produce a deterministic,
JSON-serializable artifact. `technical-v1` is not an LLM tokenizer, and a nonempty context
does not establish evidence sufficiency. ADR-0008 fixes this initial policy. CLI inspection,
citations, generation, and abstention remain later Phase 5 slices.

The structured `ContextItem` and `ConstructedContext` JSON fields are the authoritative
artifact. `rendered_text` is derived from those fields for deterministic accounting and human
inspection; it is neither a prompt nor trusted framing for a generator. A future provider and
prompt-versioning ADR must define prompt-safe framing and escaping before generation is
implemented.

## Provenance and version boundaries

Every ingested document records its library version and source URL. Chunks repeat the fields
needed for retrieval-time filtering and citation, while `document_id` preserves the parent
relationship. A corpus build must never silently combine incompatible library versions.
Context v1 additionally rejects candidate sets spanning more than one normalized library.
Cross-library compatibility among PyMC, ArviZ, and PyTensor remains a separate decision.

Source manifests, processed artifacts, datasets, and experiment inputs are content-addressed.
Download time, release, commit, license, raw hash, parser version, chunker version, index
configuration, corpus hash, dataset hash, and software versions are recorded. See ADR-0002
for source identity and ADR-0004 for experiment provenance.

## Deferred after the initial context slice

The following are explicitly outside the implemented initial Phase 5 context slice:

- LLM generation and provider-specific prompt APIs;
- prompt-safe framed and escaped serialization for a selected generator;
- learned abstention and score-threshold calibration;
- approximate vector indexes and vector stores;
- PostgreSQL, pgvector, and Alembic;
- FastAPI, authentication, React, and other presentation work;
- arbitrary code execution and sandbox infrastructure;
- learning-progress personalization beyond future-compatible domain planning;
- graph retrieval, multi-query retrieval, and query rewriting;
- LangChain or LlamaIndex as core dependencies.

## Testing and evaluation boundaries

Unit tests exercise domain validation, source integrity, parsing, chunking, BM25 behavior,
exact cosine behavior, weighted RRF behavior, metadata filters, provider-boundary validation,
cross-encoder adapter validation, candidate reranking, metric calculations, category slices,
comparison invariants, deterministic context construction and budgeting, CLI behavior, and
persistence without network access. Integration tests run ingestion, sparse retrieval, dense
retrieval, hybrid fusion, reranking with deterministic fakes, and an offline
fixture-to-retrieval-to-context path. Actual model acquisition and execution remain explicit
experiment steps whose revisions, seeds, software versions, and outputs are recorded.

No retrieval or generation quality claim is valid without a committed dataset, an executable
configuration, and stored per-query results.

## Decisions still requiring ADRs

The following decisions are intentionally deferred until their first implementation phase:

- abstention policy, threshold-selection dataset, and calibration metric;
- cross-library compatibility for mixed PyMC, ArviZ, and PyTensor context;
- LLM provider contracts, prompt versioning, and prompt-safe serialization;
- approximate-index and vector-store adapter contracts;
- criteria and migration path from JSONL to a transactional database.
