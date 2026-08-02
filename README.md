# rag-pymc

`rag-pymc` is an evidence-grounded expert assistant foundation for Bayesian statistics and
PyMC. It targets engineers, data scientists, and researchers who need technically precise,
version-aware help with model design, implementation, diagnostics, and scientific communication.

The current MVP is deliberately narrow: it ingests controlled official PyMC API pages, retrieves
evidence with deterministic BM25, builds bounded context, evaluates evidence sufficiency, and
validates provider-neutral grounded-answer contracts. A read-only evidence service and MCP tool
registry are exposed through an official-SDK local STDIO server for agent-hosted integration. No
LLM adapter or public `ask` command is configured, and the active evidence policy still prevents
generation.

## Product boundary

The assistant adapts retrieval and response structure to the technical task. It does not maintain
learner profiles, estimate mastery, sequence curricula, track progress, or optimize pedagogical
behavior. Those tutoring capabilities are permanent non-goals.

Official, versioned PyMC, ArviZ, and PyTensor sources are authoritative for library behavior. A
future scientific-literature layer will support statistical methods, diagnostics, and research
findings without being allowed to establish API compatibility. See the
[scientific literature policy](docs/corpus/scientific-literature-policy.md).

## Implemented capabilities

- hash-verified local ingestion of official PyMC 6.2.0 generated API pages;
- structure-aware Sphinx HTML parsing and deterministic chunking;
- one atomic JSON corpus snapshot plus a provenance-complete versioned corpus freeze;
- BM25 retrieval over official API evidence with library, version, and API-symbol filters;
- deterministic, whole-item context construction under an explicit technical-token budget;
- a fail-closed evidence policy that currently always abstains;
- retrieval-to-answer orchestration that bypasses the generator unless evidence is authorized;
- immutable answer, claim, section, citation, generator-input, and generator-output contracts;
- structural response and citation-traceability evaluation;
- repository-local contracts for development datasets, corpus freezes, and gold evidence;
- a completed, hash-bound 24-example Phase 5 single-human exploratory review;
- a strict, provider-neutral read-only evidence service with three MCP-facing tool contracts; and
- reproducible CLI workflows with offline tests.

The default controlled corpus contains four PyMC 6.2.0 API pages and 15 chunks covering
`pymc.sample`, `pymc.Data`, `pymc.model.core.set_data`, and
`pymc.sample_posterior_predictive`.

The repository also contains agent-facing specialist workflows under `.agents/skills/` for
developing and auditing PyMC models, priors, simulation validation, causal inference, imperfect
data, study design, deployment, and communication. They are curated expert instructions and small
analysis utilities; they are not extra retrieval strategies or dependencies of the Python runtime.

## Why BM25 is the selected policy

Dense retrieval, equal-weight Reciprocal Rank Fusion, and cross-encoder reranking were implemented
and measured before the MVP was simplified. Their reports remain versioned as historical research
artifacts.

On the 30-query Phase 4 dataset at `k=3`:

| Policy | Recall@3 | MRR | nDCG@3 | Mean latency |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.925926 | 0.771605 | 0.811723 | 0.079583 ms |
| Dense BGE | 0.814815 | 0.685185 | 0.718251 | 9.241087 ms |
| Hybrid RRF | 0.925926 | 0.783951 | 0.820543 | 9.395983 ms |
| Cross-encoder | 0.888889 | 0.777778 | 0.806873 | 287.972640 ms |

Hybrid retrieval did not improve BM25 recall and changed MRR by only `+0.012346`; the tested
cross-encoder reduced quality and added substantial CPU latency. BM25 therefore remains the sole
runtime policy for the MVP. This decision removed learned-model downloads, truncation behavior,
Torch and Transformers dependencies, and four parallel command families while preserving the
measured evidence in the [Phase 4 report](docs/evaluation/phase4-hybrid-baseline.md) and
[ADR-0014](docs/adr/0014-select-bm25-and-retire-learned-retrieval-from-the-mvp.md). The selected
path was rebuilt and remeasured after the cleanup; see the
[MVP BM25 revalidation](docs/evaluation/mvp-bm25-revalidation.md).

Learned retrieval may return only after a new corpus and held-out dataset demonstrate a
predeclared, material benefit.

## Requirements and installation

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) 0.11.30 or newer recommended
- Git for installing pre-commit hooks

```bash
uv sync --all-groups
uv run pre-commit install
uv run rag-pymc doctor
```

The product runtime pins Beautiful Soup, Pydantic, Typer, and the official MCP Python SDK. The SDK
is used only at the STDIO presentation edge; the domain and application services do not import it.
To run the agent-facing scientific utilities as well, install and verify the optional toolchain:

```bash
uv sync --all-groups --extra scientific
uv run rag-pymc doctor --scientific
```

That optional compatibility baseline pins PyMC 6.2.0, ArviZ 1.2.0, and PyTensor 3.2.2. Exact
transitive versions are recorded in `uv.lock`. Its HDF5 backend supports the inference audit's
standard ArviZ NetCDF artifacts.

## Build the controlled corpus

All ingestion is offline. The checked-in fixtures are exact, hash-verified snapshots.

```bash
for symbol in \
  pymc.sample \
  pymc.Data \
  pymc.model.core.set_data \
  pymc.sample_posterior_predictive
do
  uv run rag-pymc ingest \
    --manifest "datasets/raw/manifests/pymc/6.2.0/$symbol.json" \
    --source "datasets/fixtures/pymc/6.2.0/$symbol.html" \
    --output-dir datasets/processed/pymc-6.2.0-api-v1
done
```

A successful build writes four documents and 15 deterministic chunks. Repeating the commands
upserts the same records.

## Search and inspect context

```bash
uv run rag-pymc search \
  "How do I update predictors for posterior prediction?" \
  --corpus-dir datasets/processed/pymc-6.2.0-api-v1 \
  --library pymc \
  --library-version 6.2.0 \
  --top-k 3

uv run rag-pymc inspect-context \
  "How do I update predictors for posterior prediction?" \
  --corpus-dir datasets/processed/pymc-6.2.0-api-v1 \
  --token-budget 2048
```

`inspect-context` writes only the indented `ConstructedContext` JSON to standard output. Its
`technical-v1` budget is deterministic but is not an LLM tokenizer. An empty context is valid and
does not imply that the question itself is invalid.

## Agent-hosted MCP evidence integration

RAG and MCP remain separate layers. `rag-pymc` owns the corpus, provenance, BM25 retrieval,
context, sufficiency and validation. MCP is only the local protocol by which an external host can
call those capabilities; it neither replaces retrieval nor guarantees that a host uses the
evidence in its final message.

The first server surface is local STDIO, read-only and evidence-only:

- `search_pymc_evidence(query, version, top_k)`;
- `inspect_pymc_context(query, version, token_budget)`; and
- `get_pymc_chunk(chunk_id, version)`.

All calls require explicit PyMC 6.2.0 provenance, reject extra inputs, use fixed bounds, and expose
the conservative abstention state. They accept no paths, arbitrary URLs, commands or code. They do
not invoke `AnswerGenerator` and do not produce an answer.

After building the controlled corpus, users can register the STDIO command in their own host. The
following syntax was verified against the locally installed Codex CLI 0.146.0 and Claude Code
2.1.168 help:

```bash
codex mcp add rag-pymc -- \
  uv --directory /home/mlioi/rag-pymc run rag-pymc serve-mcp
claude mcp add --transport stdio rag-pymc -- \
  uv --directory /home/mlioi/rag-pymc run rag-pymc serve-mcp
```

These commands are snippets for the user; this project never runs them automatically or edits
global host configuration. The user installs and authenticates Codex or Claude Code separately,
and any host usage belongs to that user's plan, quotas and limits. `rag-pymc` does not receive,
read or store API keys, OAuth tokens, `~/.codex/auth.json`, or Claude credentials.
The absolute `--directory` keeps corpus and freeze resolution anchored to this repository even when
the host starts the server from another working directory. From the repository root, the shorter
`uv run rag-pymc serve-mcp` command is equivalent.

The official Python MCP SDK is pinned exactly at `mcp==2.0.0`. Both an in-process SDK client and a
real subprocess STDIO client are covered by offline tests; no handwritten JSON-RPC substitute is
used. The server revalidates the authorized corpus and freeze before accepting protocol traffic,
reserves stdout for MCP frames, and sends diagnostics only to stderr.

This vertical slice is not a complete chatbot. Generation remains blocked by
`ConservativeAbstentionPolicy`, there is no public `ask`, and MCP cannot ensure that a host invokes
the tools or makes its final prose match a future validated draft. See
[ADR-0017](docs/adr/0017-use-agent-hosted-read-only-mcp-over-local-stdio.md).

## Reproduce the selected retrieval baseline

```bash
uv run rag-pymc evaluate \
  --dataset datasets/evaluation/migrations/pymc-6.2.0-phase4-exact-projection-v1.jsonl \
  --corpus-dir datasets/processed/pymc-6.2.0-api-v1 \
  --output /tmp/rag-pymc-bm25-evaluation.json \
  --top-k 3 \
  --seed 20260720 \
  --k1 1.5 \
  --b 0.75
```

The active version-migration result is
[pymc-6.2.0-bm25-migration-v1.json](reports/evaluation/pymc-6.2.0-bm25-migration-v1.json).
It exactly preserves the PyMC 6.1.0 ranking and non-latency metrics. The query projection changes
only the PyMC library version after exact normalized document and chunk matching; it is not new
human judgment or held-out evaluation. The historical 6.1.0 baseline remains versioned in
[phase4-bm25-expanded.json](reports/evaluation/phase4-bm25-expanded.json).

## Internal research-data commands

Annotation preparation is intentionally separated from the product CLI:

```bash
uv run python -m tools.research_cli validate-development-data --help
uv run python -m tools.research_cli freeze-annotation-corpus --help
uv run python -m tools.research_cli export-development-review --help
uv run python -m tools.research_cli export-development-single-review-template --help
uv run python -m tools.research_cli finalize-development-single-review --help
uv run python -m tools.research_cli validate-development-single-review --help
uv run python -m tools.research_cli evaluate-development-single-review-baseline --help
uv run python -m tools.research_cli freeze-controlled-api-corpus --help
uv run python -m tools.research_cli compare-pymc-620-migration --help
uv run python -m tools.research_cli project-pymc-620-retrieval-dataset --help
```

The candidate packet remains an agent-authored artifact, while the completed human decisions live
in a separate governed JSONL. The single review accepted all 24 candidates as proposed: 18 are
corpus-answerable and six are hard negatives. The resulting dataset is exploratory development
evidence; it is neither independently adjudicated nor held out and does not authorize a threshold.
See the [single-review workflow](docs/evaluation/phase5-development-single-review-workflow-v1.md)
and its [validation report](reports/evaluation/phase5-development-single-review-v1-validation.json).
These commands do not generate answers, infer acceptance, or fabricate human annotation.

## Development checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov=rag_pymc --cov-branch --cov-report=term-missing:skip-covered
uv run rag-pymc doctor
```

Pre-commit runs the same non-mutating validation sequence. Tests enforce branch coverage at or
above the measured 84% project floor. CI executes the checks on Python 3.12 and 3.13 from locked,
clean environments and builds the distribution artifacts.

## Repository layout

```text
src/rag_pymc/
├── abstention/        # Evidence-sufficiency policy boundary
├── application/       # Retrieval-to-context use cases
├── chunking/          # Official API chunking
├── context/           # Deterministic context construction
├── domain/            # Evidence and grounded-answer contracts
├── evaluation/        # Retrieval, evidence, and response evaluation
├── indexing/          # Explicit BM25 index
├── ingestion/         # Integrity checks and orchestration
├── mcp/               # Read-only MCP presentation boundary
├── parsing/           # Official Sphinx API parser
├── persistence/       # Atomic deterministic JSON corpus
├── retrieval/         # Selected sparse retriever
└── cli.py             # Product CLI
```

Agent expertise lives outside the installable runtime in `.agents/skills/`; immutable research
inputs and outputs live under `datasets/` and `reports/`. Repository-only annotation commands live
under `tools/`.

Historical dense, hybrid, reranking, repository-code, and notebook experiments remain documented
under `docs/adr/`, `docs/evaluation/`, and `reports/evaluation/`. They are evidence for decisions,
not active runtime capabilities. ADR-0015 records the decision to retain only the official API
ingestion path.

## Near-term roadmap

Phase 5 single review is complete. The current ordered plan is maintained in
[docs/roadmap.md](docs/roadmap.md). A consolidated snapshot of implemented capabilities,
operational commands, validation evidence, and current limitations is maintained in
[docs/current-project-status.md](docs/current-project-status.md).

The single-review conservative baseline, controlled PyMC 6.2.0 version migration, and agent-hosted
evidence MCP vertical slice are complete. The next product step is a preregistered PyMC-only
official API expansion. New development and held-out data, sufficiency calibration, structured
draft preparation/validation, and separate Codex/Claude generator evaluation remain later gates.

PostgreSQL, vector databases, arbitrary code execution, web APIs, user interfaces, learner state,
and additional retrieval strategies remain outside the MVP.
