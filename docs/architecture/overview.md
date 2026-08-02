# Architecture overview

## Purpose and boundary

`rag-pymc` is an expert assistant foundation for Bayesian statistics and PyMC grounded in
versioned evidence. The active MVP supports official API ingestion, BM25 retrieval, deterministic
context construction, conservative evidence assessment, and grounded-response evaluation.

The runtime does not contain learner models, multiple retrieval strategies, code execution,
provider-specific generation, or a database server. Its first narrow presentation layer is a
local, read-only MCP evidence boundary; internal annotation tools remain separate in the research
CLI.

Official library evidence and scientific literature have different authority. Official PyMC,
ArviZ, and PyTensor sources support API and compatibility claims. Papers may support statistical
methods, assumptions, diagnostics, and empirical findings but cannot establish pinned runtime
behavior.

## Dependency direction

```text
Codex / Claude Code          Product CLI          Internal research CLI
        |                        |                         |
        v                        v                         v
 Local STDIO MCP edge     Application use cases   Evaluation-data workflows
        |                        |                         |
        +------------------------+-------------------------+
                                 v
                       Domain models and protocols
                                 ^
                                 |
                     Infrastructure implementations
```

The domain does not import Typer, persistence, retrieval implementations, model providers, or
orchestration frameworks. It also does not import the MCP SDK, Codex, Claude, or subprocess.
Presentation boundaries call project-owned services. Infrastructure implements project-owned
protocols and converts external values at the edge.

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
chunks from PyMC 6.2.0. The public API index is used for source selection, not ingested as a
monolithic evidence page.

Repository-code and notebook parsers were retired from the installed package. Their exact source
snapshots, manifests, datasets, reports, and ADRs remain historical evidence. Reintroducing a
source type requires a working vertical slice and an adoption gate.

### Persistence

`JsonDocumentRepository` stores documents and chunks in one deterministic `corpus.json` snapshot.
Each upsert replaces that snapshot atomically, so readers cannot observe a new document set paired
with stale chunks. PostgreSQL, pgvector, migrations, and vector stores have no active contract.

The historical `canonical-chunk-identity-json-v1` freeze identifies normalized chunk content but
does not distinguish two releases whose normalized chunks are byte-identical. Active corpus
freezes therefore use `canonical-corpus-provenance-json-v2`, which additionally binds library
version, release tag, upstream commit, exact source manifests and fixture hashes, normalized
documents, and chunks. Historical v1 hashes remain immutable and are never reinterpreted as v2.

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
not assessed because no calibrated criterion exists. Every current outcome abstains. A genuine
single-human exploratory development dataset now exists, but no loss, answer-permitting signal,
threshold rule, or held-out validation authorizes relaxing this boundary.

The preregistered conservative baseline confirms that boundary: zero answers were authorized over
24 reviewed examples. It records 25 of 28 gold claims in the constructed context and 26 of 28 in
the retrieved candidates; those coverage observations do not by themselves authorize answering.

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

### Agent-hosted MCP evidence boundary

`EvidenceInspectionService` is a separate application use case for read-only evidence access. It
loads no generator and does not traverse `AnswerGenerator` with a fake implementation. Runtime
composition checks the atomic 6.2.0 corpus against the provenance-complete v2 freeze before
building the selected BM25 retriever, context builder, and real conservative policy.

The SDK-independent MCP registry exposes exactly three fixed tools: evidence search, bounded
context inspection, and authorized chunk lookup. Inputs require explicit version `6.2.0`, reject
unknown fields, and cap queries at 1,000 characters, `top_k` at 10, and the technical-token budget
at 8,192. Context inspection uses fixed retrieval depth three. Direct lookup accepts only opaque
`chunk_<sha-prefix>` identities already present in the validated corpus; no tool accepts a path,
URL, command, source manifest, or corpus override.

Every result carries schema/service/tool identities, normalized-query hash when applicable,
library/version, BM25/tokenizer parameters, v2 corpus hash, exact authorized text, official URL,
provenance, chunk order, limitations, and a fail-closed authorization projection. Context results
also bind the canonical context hash and exact `EvidenceAssessment`. A positive policy result is
rejected at this evidence-only boundary.

MCP is presentation infrastructure, not the RAG policy. It cannot guarantee that Codex or Claude
calls a tool, preserves the evidence, emits citations, or makes final prose match a future validated
draft. Host installation, authentication and usage accounting remain outside `rag-pymc`.

```text
agent-hosted MCP MVP
        != CLI generation adapter
        != standalone local interface
        != direct provider API
```

STDIO is the selected first transport. The adapter uses the official Python MCP SDK pinned at
`mcp==2.0.0`, while strict input validation and sanitized failures remain owned by the
SDK-independent registry. Offline tests exercise both the SDK's in-memory transport and a real
subprocess STDIO exchange. No handwritten JSON-RPC implementation substitutes for the SDK.

The supported Conda Python 3.13 runtime does not reliably wake AnyIO blocking-file completion
callbacks when the event loop has no other timers. The STDIO adapter therefore keeps one bounded
50 ms scheduler tick while the transport is active. This adds at most 20 idle wake-ups per second,
does not parse or alter protocol frames, and is regression-tested through the subprocess client.

### Evaluation and research tooling

The installed `evaluation` package contains retrieval metrics and structural response evaluation.
Phase 5 annotation contracts, gold chunk-support evaluation, and their CLI live under `tools/` and
are excluded from the wheel. The product CLI exposes only operational corpus, search, context, and
retrieval-evaluation commands.

One-time annotation preparation lives in the repository-local `tools.research_cli` module. It is
not packaged as a product command. Separate single-review contracts record one human without
impersonating an annotator/adjudicator pair. The completed exploratory dataset contains 24 reviewed
examples bound to the 15-chunk corpus and retains `independent_adjudication=false`,
`held_out=false`, and `threshold_selected=false`. These artifacts remain content-addressed and
reproducible without enlarging the assistant's public command surface.

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
- direct provider APIs, credential management, or automatic provider routing;
- arbitrary execution of generated code;
- graph retrieval, multi-query retrieval, and query rewriting; and
- LangChain or LlamaIndex as core dependencies.

## Decisions still required

- an answer-permitting evidence signal, loss, threshold rule, and calibration experiment;
- evidence-layer authority metadata and deterministic mixed-source routing;
- the next PyMC-only official API scope plus chunking and tokenization v2 adoption gates;
- new development and held-out human evaluation on the stabilized corpus;
- prompt-safe serialization plus structured host draft preparation and validation;
- semantic answer and citation-support evaluation;
- cross-library compatibility for PyMC, ArviZ, and PyTensor context; and
- paper acquisition, licensing, normalization, freshness, and mixed-authority routing.
