# Current project status

- Snapshot date: 2026-08-02
- Active branch: `main`
- Product version: `0.1.0`
- Checkpoint: Phase 5 single review + controlled PyMC 6.2.0 migration + agent-hosted MCP evidence slice

## Product boundary

`rag-pymc` is a local evidence system for expert PyMC and Bayesian-statistics assistance. It owns
the controlled corpus, provenance, BM25 retrieval, context construction, evidence sufficiency,
grounding contracts, citations, and offline validation.

The conversational host remains the user's separately installed and authenticated Codex CLI or
Claude Code. `rag-pymc` does not run an LLM, call OpenAI or Anthropic APIs, select providers,
store credentials, or read host authentication files. It is not an adaptive tutor and contains no
learner profile, curriculum, progress, or pedagogical-personalization state.

The current MCP slice exposes evidence but is not yet a complete grounded chatbot. MCP does not
replace RAG and cannot guarantee that a host invokes a tool or uses its output faithfully.

## Active corpus and provenance

The active corpus contains only official, versioned PyMC 6.2.0 generated API documentation:

- four documents and 15 deterministic chunks;
- `pymc.sample`;
- `pymc.Data`;
- `pymc.model.core.set_data`; and
- `pymc.sample_posterior_predictive`.

The provenance-complete corpus identity uses
`canonical-corpus-provenance-json-v2` with SHA-256
`796e7aee3f1fae1423bc04f0478381e6f7338afdd85d2f3a9d1d9cfa692c573a`. It binds the
PyMC `v6.2.0` release, upstream commit, source manifests, raw fixture hashes, normalized
documents, and chunks. The processed corpus is one deterministic, atomically replaced
`corpus.json` snapshot and is rebuilt locally from checked-in fixtures.

PyMC 6.1.0 and 6.2.0 produce equivalent normalized content for these four pages, but retain
distinct raw bytes and release provenance. Historical 6.1.0 artifacts remain immutable.

ArviZ, PyTensor, scientific literature, notebooks, and upstream repository code are not part of
the active retrieval corpus.

## Implemented capabilities

### Offline ingestion and persistence

- Strict source manifests with library/version, official URL, release, upstream commit, license,
  media type, acquisition timestamp, and raw SHA-256.
- Hash-verified local fixture acquisition with no runtime network dependency.
- Structure-aware Sphinx API parsing and deterministic semantic chunking.
- Atomic JSON snapshot persistence with stable document/chunk identities and parent validation.

### Retrieval, context, and sufficiency

- Vectorless `bm25-v1` is the only active retriever.
- `technical-v1` is the only active tokenizer.
- BM25 defaults are fixed at `k1=1.5` and `b=0.75`.
- Retrieval supports exact PyMC library, version, source-type, and API-symbol filtering.
- Context construction preserves complete chunks under an explicit deterministic token budget.
- Context and corpus outputs carry canonical SHA-256 identities.
- `ConservativeAbstentionPolicy` currently abstains on every query because no calibrated
  answer-permitting criterion exists.
- `ExpertAssistantService` does not call an `AnswerGenerator` while the policy abstains.

### Read-only MCP evidence server

`rag-pymc serve-mcp` starts a local STDIO server implemented with the official Python MCP SDK
`mcp==2.0.0`. The SDK is isolated at the presentation boundary; the domain and application
services do not import MCP, Typer, Codex, Claude, subprocess, or agent frameworks.

The server exposes exactly three tools in stable order:

1. `search_pymc_evidence(query, version, top_k)`
2. `inspect_pymc_context(query, version, token_budget)`
3. `get_pymc_chunk(chunk_id, version)`

Tool invariants:

- read-only and closed-world annotations;
- explicit supported version: only `6.2.0`;
- query length: 1–1,000 characters after Unicode NFKC/whitespace normalization;
- hidden control/format characters rejected;
- `top_k`: 1–10;
- context token budget: 1–8,192;
- context retrieval depth fixed at three;
- extra fields rejected;
- no model-supplied filesystem paths, arbitrary URLs, commands, code, or corpus overrides;
- direct lookup resolves only opaque IDs already present in the authorized corpus;
- exact per-tool input and output JSON schemas;
- deterministic ordering and canonical JSON output;
- sanitized, versioned errors without raw exception text or unnecessary local paths;
- stdout reserved for protocol frames and diagnostics sent only to stderr; and
- every successful result explicitly records `generation_permitted=false`.

Tool results include, as applicable, schema/service/server/tool versions, normalized query and
query hash, retriever/tokenizer/BM25 configuration, corpus hash policy and SHA-256, context hash,
chunk IDs, exact authorized text, official provenance URLs, sufficiency, reason codes, and known
limitations.

### Product and research CLI

The product CLI currently exposes:

- `rag-pymc doctor`;
- `rag-pymc ingest`;
- `rag-pymc search`;
- `rag-pymc inspect-context`;
- `rag-pymc serve-mcp`; and
- `rag-pymc evaluate`.

Phase 5 annotation, freezing, migration, and single-review commands remain repository-local under
`python -m tools.research_cli`; they are not installed as product commands.

There is no public `ask` command.

## Evaluation state

The Phase 5 exploratory development checkpoint contains:

- 24 reviewed examples;
- 18 corpus-answerable queries;
- six hard negatives;
- 28 atomic claims; and
- 31 minimal support sets.

All 24 candidates were accepted by one real human reviewer. The dataset has no independent
adjudication, is not held out, is not production-grade, and does not authorize threshold
selection. The preregistered conservative baseline authorizes zero answers. It records evidence
coverage separately from policy behavior and does not treat coverage as semantic answer
validation.

Codex and Claude have not been evaluated as generators. Any future evaluation must treat them as
separate generators and must not implement automatic routing or pool their outcomes.

## Reproducibility and verification

The latest full offline validation on Python 3.13.5 reported:

- Ruff format: 103 files correctly formatted;
- Ruff lint: no findings;
- mypy strict: 103 source files, no issues;
- pytest: 347 passing tests;
- branch-aware coverage: 89.15% against an 84% minimum;
- `rag-pymc doctor`: `status: ok`;
- `uv lock --check --offline`: successful; and
- `git diff --check`: successful.

The tests include strict input bounds, unsupported versions, absent/empty/tampered corpus cases,
unknown chunk IDs, deterministic ordering, hashes and provenance, visible abstention, no generator
dependency, error sanitization, architecture boundaries, exact JSON schemas, an official SDK
in-process client, and a real offline subprocess STDIO exchange.

No live Codex or Claude test is part of the default suite because it would consume network, tokens,
and host-plan quota.

## Operating the current slice

Build the controlled corpus from the repository root using the four checked-in PyMC 6.2.0
manifests and fixtures documented in the README. The MCP server fails closed if the processed
snapshot or its freeze is missing, empty, tampered, or inconsistent.

Host-registration syntax verified against local Codex CLI 0.146.0 and Claude Code 2.1.168 help:

```bash
codex mcp add rag-pymc -- \
  uv --directory /home/mlioi/rag-pymc run rag-pymc serve-mcp

claude mcp add --transport stdio rag-pymc -- \
  uv --directory /home/mlioi/rag-pymc run rag-pymc serve-mcp
```

These snippets are intentionally not executed by the project. The user owns host installation,
authentication, configuration, quotas, and billing. `rag-pymc` never receives or stores those
credentials.

## Current limitations

- Evidence coverage is narrow: four PyMC API pages only.
- Sufficiency remains uncalibrated and all queries abstain.
- The MCP tools retrieve and inspect evidence but do not prepare, generate, validate, or endorse a
  natural-language answer.
- MCP cannot force host tool use, citation completeness, or agreement between a host's final prose
  and a future validated draft.
- No `prepare_pymc_answer` or `validate_pymc_answer` gate exists yet.
- No provider adapter, direct provider API, local model, standalone chat UI, provider routing,
  embeddings, vector database, or learned reranker is active.
- The official MCP SDK introduces a larger transitive HTTP/ASGI/authentication/telemetry stack than
  the STDIO slice itself uses; it remains isolated and locked at the presentation edge.

## Next ordered work

The next concrete package is to preregister user-query families and one small PyMC 6.2.0 official
API expansion. After that, the preserved order is authority metadata, corpus expansion/freeze,
new development and genuinely held-out sets, human review, sufficiency preregistration and
calibration, one-shot held-out evaluation, `prepare_pymc_answer`, structured host drafts,
`validate_pymc_answer`, and separate Codex/Claude generator evaluations. Only after those gates may
the product be presented as a grounded chatbot.
