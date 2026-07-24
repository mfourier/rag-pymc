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

Phases 1 through 4 and the implemented Phase 5 foundations add only packages with exercised
behavior. The CLI calls project-owned services and protocols, while the domain remains
independent of Beautiful Soup, filesystems, JSONL, ranking implementations, embedding
providers, generator providers, and presentation concerns.

## Architecture through deterministic Phase 5 structural response evaluation

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

### Experimental repository-code evidence layer

An orthogonal ingestion slice snapshots complete Python files from the exact PyMC `v6.1.0`
Git object and selects four public implementations with the standard-library AST. Manifests add
the repository-relative path and require the expected symbol and source commit. Definition
chunks retain signatures and one docstring summary; implementation chunks group complete
top-level statements under a bounded character policy. The current slice produces four
documents and 19 chunks under `source_type=repository_code`.

This corpus is not part of the Phase 4 baseline or default context inspection. It supports a
separate implementation-query evaluation and must pass a mixed-corpus regression experiment
before adoption. ADR-0010 records the source/version boundary, AST policy, and decision to defer
upstream tests until evidence roles can distinguish implementation from asserted test behavior.

### Experimental conceptual-notebook evidence layer

A second ingestion slice snapshots three complete notebooks from the exact PyMC `v6.1.0` Git
object. The notebook parser normalizes only nonempty Markdown and code inputs while preserving
one-based cell identity and heading hierarchy. Outputs, execution counters, kernel information,
other metadata, and raw cells do not enter retrieval content. The cell-aware chunker groups only
adjacent cells in the same section and never splits one cell. It extracts conservative PyMC
symbol metadata from code inputs.

The current notebook corpus contains three documents and 34 chunks under
`source_type=notebook`. It is evaluated independently and is not part of default context
inspection. ADR-0012 fixes the raw-acquisition, normalization, chunking, and large-artifact
boundaries.

### Phase 5: Grounded response foundations

The implemented Phase 5 slices contain:

- immutable `ContextItem` and `ConstructedContext` domain models;
- project-owned `ContextBuilder` and `TokenCounter` protocols;
- canonical ordering by retrieval rank and chunk ID;
- duplicate suppression by chunk ID with explicit conflicting-payload rejection;
- a versioned rendering that preserves source URL, library version, section, API symbols,
  retrieval provenance, and complete chunk content;
- additive per-item budgeting with the deterministic `technical-v1` accounting policy;
- complete-item rank-prefix admission with explicit tail omission and no content truncation;
- fail-closed validation that admits only one normalized library and one version of each
  library before budgeting;
- a `ContextInspectionService` application use case that composes any project-owned
  `Retriever` and `ContextBuilder` without depending on Typer or model providers;
- `rag-pymc inspect-context`, which combines fixed BM25 (`k1=1.5`, `b=0.75`) and pinned BGE
  exact cosine retrieval through equal-weight RRF with component candidate depth 10,
  `rrf_k=60`, and default `top_k=3` over the Phase 4 corpus;
- a required `technical-v1` budget and pure indented `ConstructedContext` JSON on stdout,
  without timestamps, latency, status text, or an implicit output file;
- `EvidenceSufficiency` and immutable `EvidenceAssessment` domain contracts that preserve the
  policy version, abstention decision, deterministic reason codes, and exact included and
  omitted chunk IDs;
- a project-owned `AbstentionPolicy` protocol and `ConservativeAbstentionPolicy` identified
  as `conservative-no-threshold-v1`;
- immutable provider-neutral `Citation`, `AtomicClaim`, `GroundedAnswerSection`,
  `GroundedAnswer`, `GeneratorInput`, and `GeneratorOutput` contracts;
- exact binding among the generation query, constructed context, and sufficient evidence
  assessment, followed by exact citation resolution and provenance validation against
  included context items;
- organizational headings treated as untrusted metadata rather than factual answer content;
- the pure `structural-citation-v1` evaluator, which strictly parses raw answer JSON and
  records staged contract failures plus per-citation traceability diagnostics;
- content hashes and sanitized structural records that omit claim text, headings, query text,
  context content, and arbitrary unknown field values, while retaining opaque identifiers;
- deterministic aggregate metrics and `StructuralResponseAggregateReport`, with canonical
  response ordering, duplicate-ID rejection, embedded revalidated records, explicit
  conditional denominators, and `None` for undefined rates.
- immutable corpus-relative Phase 5 development annotations with atomic gold claims,
  alternative minimal chunk-support sets, query/template families, hard-negative categories,
  and mandatory human annotation and adjudication provenance;
- strict deterministic JSONL loading that hashes exact bytes, rejects duplicate keys and
  non-finite values, preserves record order, and requires globally unique identities in one
  corpus namespace;
- canonical Phase 5 corpus hashing over sorted chunk ID/content-hash records plus validation
  that resolves every gold support reference against the exact library/version corpus before
  a dataset is evaluated;
- a deterministic `phase5-annotation-corpus-freeze-v1` Gate A record and CLI that bind the
  intended annotation namespace to its logical corpus path, exact corpus identity, admitted
  library/version and source layers, normalized document identities, parser/chunker versions,
  API-symbol coverage, and declared limitations before any examples are authored;
- `rag-pymc validate-development-data`, which requires explicit dataset and corpus paths and
  emits the deterministic corpus-validation JSON without partial standard output on failure;
- the pure `phase5-gold-evidence-v1` evaluator, which binds corpus, query, context, and
  assessment identities, then measures gold claim support in admitted context and in the
  admitted-plus-budget-omitted candidate set;
- deterministic gold-evidence aggregation with exact development-dataset coverage,
  annotation revalidation, one evidence-policy version, canonical query ordering, and fixed
  coverage, selective-risk, false-answer, false-abstention, decision, and claim-coverage
  denominators.

The constructed context artifact has no timestamp or latency, so fixed inputs produce a
deterministic, JSON-serializable value. `technical-v1` is not an LLM tokenizer, and a
nonempty context does not establish evidence sufficiency. ADR-0008 fixes this initial policy.
The inspection command requires an explicit token budget, defaults to PyMC 6.1.0 and three
final results, and permits at most ten. Its embedding adapter remains local-files-only unless
the user explicitly selects `--allow-download`.

The conservative policy classifies an empty context without omissions as
`no_retrieved_evidence` and an empty context with omitted candidates as
`budget_excluded_all_evidence`; both are `insufficient`. Every nonempty context is
`not_assessed` with `no_calibrated_criterion`, adding `budget_omitted_evidence` for a partial
context. All four paths abstain, and the policy never emits `sufficient`. It therefore has
zero answer coverage by design and makes no abstention-quality claim. ADR-0009 fixes these
conservative semantics and the prerequisites for any future threshold selection.

Citation contracts, structural traceability, development-annotation contracts, and gold
chunk-support evaluation are implemented. A `Generator` protocol and fake, generation
orchestration, semantic support, correctness, and completeness evaluation, authored Phase 5
development and held-out datasets, and an answer-permitting evidence policy remain later
slices. Gold chunk-identity coverage does not establish that a claim is semantically true or
supported, that every generated claim is cited, or that an answer is useful. Opaque
identifiers and linkable hashes remain potentially sensitive evaluation metadata; callers
must not encode prose or secrets in identifiers.

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

## Deferred after the implemented Phase 5 slices

The following are explicitly outside the implemented Phase 5 slices:

- a `Generator` protocol, deterministic fake, end-to-end response orchestration, and
  provider-specific generation APIs;
- prompt-safe framed and escaped serialization for a selected generator;
- an answer-permitting evidence policy, richer inference signals, and score-threshold
  calibration;
- semantic claim support, citation correctness, citation completeness, answer correctness,
  and pedagogical-usefulness evaluation;
- human-authored Phase 5 development and held-out response datasets;
- persistence or automatic report writing for constructed context artifacts;
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
persistence without network access. Evidence-assessment tests cover every conservative reason
path and verify that the policy always abstains without scores or thresholds. CLI tests
validate pure context JSON with deterministic retrieval substitutes. Grounded-response tests
cover authorization, answer invariants, abstentions, exact provenance, and rejection of
omitted evidence. Structural-evaluation tests cover staged validation, strict JSON and
diagnostic sanitization, citation traceability, aggregation arithmetic, explicit
denominators, canonical ordering, and nested revalidation. Integration tests run ingestion,
sparse retrieval, dense retrieval, hybrid fusion, reranking with deterministic fakes, and an
offline fixture-to-retrieval-to-context path. Actual model acquisition and execution remain
explicit experiment steps whose revisions, seeds, software versions, and outputs are
recorded.

No retrieval or generation quality claim is valid without a committed dataset, an executable
configuration, and stored per-query results.

`structural-citation-v1` establishes only syntax, contract validity, and provenance
traceability. A structurally valid response is not evidence of semantic correctness,
citation support or completeness, or answer usefulness.

## Decisions still requiring ADRs

The following decisions are intentionally deferred until their first implementation phase:

- an answer-permitting evidence signal, threshold-selection experiment, and calibration
  metric;
- cross-library compatibility for mixed PyMC, ArviZ, and PyTensor context;
- LLM provider contracts, prompt versioning, and prompt-safe serialization;
- approximate-index and vector-store adapter contracts;
- criteria and migration path from JSONL to a transactional database.
