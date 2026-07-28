# Architecture overview

## Purpose and boundary

`rag-pymc` is an expert assistant foundation for Bayesian statistics and PyMC grounded in
versioned evidence. The active MVP supports official API ingestion, BM25 retrieval, deterministic
context construction, conservative evidence assessment, and grounded-response evaluation.

The runtime does not contain learner models, multiple retrieval strategies, code execution,
provider-specific generation, a database server, or a presentation layer. Internal annotation
tools are exposed through a separate research CLI.

Official library evidence and scientific literature have different authority. Official PyMC,
ArviZ, and PyTensor sources support API and compatibility claims. Papers may support statistical
methods, assumptions, diagnostics, and empirical findings but cannot establish pinned runtime
behavior.

## Dependency direction

```text
Product CLI                 Internal research CLI
    |                               |
    v                               v
Application use cases       Evaluation-data workflows
    |                               |
    +---------------+---------------+
                    v
          Domain models and protocols
                    ^
                    |
        Infrastructure implementations
```

The domain does not import Typer, persistence, retrieval implementations, model providers, or
orchestration frameworks. Presentation boundaries call project-owned services. Infrastructure
implements project-owned protocols and converts external values at the edge.

## Active evidence pipeline

```text
hash-verified API fixture + manifest
                |
                v
        SphinxApiParser
                |
                v
       ApiReferenceChunker
                |
                v
     JsonDocumentRepository
                |
                v
       BM25Index / SparseRetriever
                |
                v
       RankedContextBuilder
                |
                v
 ConservativeAbstentionPolicy
                |
                v
 grounded-answer contracts and evaluators
```

### Acquisition and ingestion

`SourceManifest` records source identity, library and version, URL, release metadata, acquisition
time, license, media type, and raw SHA-256. `LocalFileSourceFetcher` verifies bytes before parsing.

The active parser accepts only controlled generated API HTML. `SphinxApiParser` normalizes the
signature, overview, parameters, returns, notes, and examples. `ApiReferenceChunker` preserves
complete semantic sections and code blocks. The current corpus contains four documents and 15
chunks.

Repository-code and notebook parsers were retired from the installed package. Their exact source
snapshots, manifests, datasets, reports, and ADRs remain historical evidence. Reintroducing a
source type requires a working vertical slice and an adoption gate.

### Persistence

`JsonDocumentRepository` stores documents and chunks in one deterministic `corpus.json` snapshot.
Each upsert replaces that snapshot atomically, so readers cannot observe a new document set paired
with stale chunks. PostgreSQL, pgvector, migrations, and vector stores have no active contract.

### Retrieval

`TechnicalTokenizer`, `BM25Index`, and `SparseRetriever` implement the only active ranking policy.
BM25 uses fixed defaults `k1=1.5` and `b=0.75`; evaluation records the exact values, seed, corpus
hash, dataset hash, per-query rankings, and limitations.

Dense retrieval, RRF, and cross-encoder reranking were measured and retired from the runtime by
ADR-0014. Their stored reports are immutable research artifacts, not supported command surfaces.

### Context and evidence assessment

`RankedContextBuilder` sorts by retrieval rank and chunk ID, rejects conflicting duplicates,
preserves complete chunks, and admits only a rank prefix under the deterministic `technical-v1`
budget. Context v1 rejects mixed normalized libraries before budgeting.

`ConservativeAbstentionPolicy` is fail-closed. Empty evidence is insufficient; nonempty evidence is
not assessed because no calibrated criterion exists. Every current outcome abstains. This avoids
authorizing an answer before the human development dataset and loss rule exist.

### Grounded responses

Provider-neutral domain models represent citations, atomic claims, answer sections, answers,
generator inputs, and generator outputs. Positive generation requires an explicitly sufficient,
non-abstaining assessment bound to the exact query and context. Citations must resolve to included
context items with exact provenance.

`ExpertAssistantService` is the sole retrieval-to-generation application boundary. It retrieves,
builds context, applies the evidence policy, and returns a claim-free abstention without invoking
the `AnswerGenerator` whenever authorization fails. No provider adapter or public answer command is
selected yet.

`structural-citation-v1` validates JSON shape, domain contracts, citation resolution, and provenance
traceability. It does not establish semantic support, answer correctness, citation completeness, or
technical usefulness.

### Evaluation and research tooling

The installed `evaluation` package contains retrieval metrics, strict development-data contracts,
gold chunk-support evaluation, and structural response evaluation. The product CLI exposes only
operational corpus, search, context, and evaluation commands.

One-time annotation preparation lives in the repository-local `tools.research_cli` module. It is
not packaged as a product command. Its artifacts remain content-addressed and reproducible without
enlarging the assistant's public command surface.

### Agent expertise assets

The `.agents/skills/` tree contains specialist operating procedures and narrowly scoped analysis
utilities for Bayesian and PyMC work. These assets enrich an agent that is able to load them, but
they do not import into `rag_pymc`, alter retrieval ranking, or enlarge the installed dependency
graph. Keeping this boundary explicit prevents expert workflow knowledge from becoming hidden
runtime coupling.

## Historical experiments

The repository retains these decisions and reports:

- Phase 2 BM25 on one API page;
- Phase 3 dense BGE comparison;
- Phase 4 expanded BM25, dense, RRF, and cross-encoder comparison;
- experimental repository-code ingestion and BM25 evaluation; and
- experimental conceptual-notebook ingestion and BM25 evaluation.

Historical documents describe code that existed when the experiment ran. The current runtime need
not retain that code once the result has answered its decision question. Git history, exact input
snapshots, manifests, datasets, and stored reports preserve the audit trail.

## Current non-goals

- learner profiles, curricula, progress tracking, exercises, and pedagogical adaptation;
- dense retrieval, rank fusion, and learned reranking without a new adoption experiment;
- generic PDF ingestion, OCR, or indiscriminate paper crawling;
- PostgreSQL, vector databases, and distributed retrieval;
- FastAPI, authentication, React, and other presentation work;
- arbitrary execution of generated code;
- graph retrieval, multi-query retrieval, and query rewriting; and
- LangChain or LlamaIndex as core dependencies.

## Decisions still required

- the accepted single-review development-dataset contract;
- an answer-permitting evidence signal, loss, threshold rule, and calibration experiment;
- prompt-safe serialization and one LLM provider boundary;
- semantic answer and citation-support evaluation;
- cross-library compatibility for PyMC, ArviZ, and PyTensor context; and
- paper acquisition, licensing, normalization, freshness, and mixed-authority routing.
