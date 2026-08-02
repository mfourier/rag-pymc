# Current development roadmap

## Status boundary

The Phase 5 single-human review is complete and reproducible. It produced 24 exploratory examples:
18 corpus-answerable queries and six hard negatives, with 28 atomic claims and 31 minimal support
sets. The dataset is not independently adjudicated, held out, or production-grade, and no
evidence-sufficiency threshold has been selected.

The active runtime remains vectorless BM25 over four controlled PyMC 6.2.0 API documents and 15
chunks. `ConservativeAbstentionPolicy` still abstains on every query. There is no provider adapter
or public `ask` command. The first agent-hosted integration is an evidence-only MCP boundary, not a
provider router or chatbot.

Two follow-up baselines are complete:

- the conservative policy was evaluated without changing it against all 24 single-review
  examples, authorizing zero answers and selecting no threshold; and
- the same four-page source slice was migrated from PyMC 6.1.0 to 6.2.0. All four normalized
  documents and all 15 normalized chunks match exactly, while distinct raw bytes and release
  provenance remain visible through the v2 corpus freeze. Retrieval ranking and non-latency
  metrics are unchanged.

## Ordered work packages

### Completed: single-review conservative baseline

Adapt the gold-evidence evaluation boundary to consume `Phase5SingleReviewDataset` without
weakening the independently adjudicated contract. Record the unchanged conservative-policy result
against all 24 reviewed examples. Expected answer coverage is zero; that expectation is a baseline,
not a target to optimize post hoc.

Completed evidence:

- exact decision, dataset, candidate, governance, corpus, context-policy, and evidence-policy
  identities appear in the report;
- all 24 examples are evaluated, including the six hard negatives;
- gold context coverage and policy decisions are reported separately;
- the report records the single-review limitation and selects no threshold.

See
[`phase5-development-single-review-v1-conservative-baseline.json`](../reports/evaluation/phase5-development-single-review-v1-conservative-baseline.json).

### Completed: controlled PyMC 6.2.0 migration

The active defaults and optional scientific dependency pins now target PyMC 6.2.0. The migration
preserves the historical PyMC 6.1.0 Phase 5 dataset as a single-review artifact; exact normalized
mapping is mechanical evidence, not a new human review for 6.2.0. Neither the projected retrieval
dataset nor its report is held out or suitable for sufficiency calibration.

See the [migration record](evaluation/pymc-6.2.0-controlled-migration-v1.md).

### Completed: agent-hosted evidence MCP

ADR-0017 selects one local, read-only STDIO MCP server used by external Codex CLI and Claude Code
hosts. The project-owned evidence service, strict application contracts, authorized-corpus checks,
three-tool registry, error sanitization and offline in-process tests are implemented without a
generator. The official Python SDK is pinned at `mcp==2.0.0`; offline tests exercise both its
in-memory client and a subprocess STDIO exchange. No handwritten JSON-RPC fallback is present.

This compatibility is not multi-provider routing. `rag-pymc` does not choose a provider, read host
credentials, call provider APIs, or guarantee that a host uses tool output in its final message.

### 1. Query-family and PyMC API expansion preregistration

Define the user-query families and exact generated API pages for the next small PyMC-only batch.
Use the official API index as a discovery catalog, never as a monolithic evidence page. Record each
page as an exact fixture with its own strict manifest and require the v2 provenance freeze.

Exit criteria:

- page inclusion is justified by declared query families rather than indiscriminate crawling;
- retrieval/context metrics and maximum corpus/context costs are fixed before acquisition;
- expected release tag, upstream commit, source URL, license, timestamp, and raw hash are bound;
- changed normalized documents or chunks invalidate support-set reuse; and
- no ArviZ, PyTensor, guide, notebook, repository-code, or paper source is added in this package.

### 2. Authority metadata and claim-type routing

Write an ADR before changing domain schemas. Define a minimal evidence-layer vocabulary for
official API, official guides, repository code, and scientific papers, plus claim kinds that those
layers may support. Keep routing deterministic and prevent papers from establishing pinned API
behavior.

### 3. Official PyMC corpus expansion and freeze

Execute the preregistered PyMC-only batch. Compare structural chunking and Unicode-aware technical
tokenization before freezing the next corpus. Any changed chunk identity requires new support-set
validation and separate baselines.

### 4. New development and held-out sets on the stabilized corpus

Create a larger development set and a genuinely separate held-out set organized by query family and
template rather than random paraphrase splitting.

### 5. Human review of queries, answerability, claims, and support sets

Review corpus-relative answerability, atomic claims, and minimal support sets. Preserve query and
template-family separation. Independently review a declared fraction when another reviewer is
available; never invent adjudication or silently cross the human boundary.

### 6. Sufficiency design preregistration

Freeze inference signals, asymmetric loss, metrics, equality behavior, and a deterministic
calibration rule before examining held-out outcomes.

### 7. Sufficiency calibration on development

Calibrate only on the new development data. Any corpus, chunker, tokenizer, retriever, or
context-policy change invalidates the calibration boundary.

### 8. One-shot held-out evaluation

Evaluate the frozen policy once on the untouched held-out set and retain all outcomes. Do not tune
again from held-out results.

### 9. `prepare_pymc_answer`

Prepare prompt-safe, structured evidence only after the evidence policy authorizes generation.

### 10. Structured host draft

Allow Codex or Claude to produce one declared structured draft from prepared evidence. This remains
generator behavior, not evidence-policy behavior.

### 11. `validate_pymc_answer`

Validate schema, semantic claim support, citations, completeness, and provenance against the exact
prepared context before accepting a draft.

### 12. Separate generator evaluations

Evaluate Codex and Claude as distinct generators with separate reports. Do not route automatically,
pool provider outcomes, or infer equivalence from shared MCP compatibility.

### 13. Grounded chatbot claim

Only after the preceding gates may the system be described as a grounded chatbot or expose a public
answer workflow.

### 14. Optional standalone local interface

Only then consider a separate UI with `CodexCliGenerator` using `codex exec` and
`ClaudeCodeCliGenerator` using `claude -p`. Keep explicit user choice and separate generator
evaluation; automatic routing remains out of scope. Live checks stay opt-in because they consume
network, tokens, and host-plan quota.

## Retention and cleanup policy

Keep candidate drafts, decision records, accepted datasets, validation reports, corpus freezes,
preregistrations, governance records, ADRs, and historical retrieval reports. They are provenance or
decision evidence, not obsolete runtime code. Remove an artifact only when a newer governed record
explicitly supersedes it and the audit trail remains reconstructible from versioned inputs.

Repository-code and notebook experiments, dense retrieval, RRF, and cross-encoder reports remain
historical evidence but are not active capabilities. Do not reintroduce their runtime dependencies
without a new preregistered adoption experiment.

## Persistent non-goals

Adaptive tutoring, learner models, vector databases, arbitrary code execution, direct provider
APIs, automatic multi-provider routing, generic crawling, and additional retrieval strategies
remain outside the current MVP. A standalone web UI is deferred until the final ordered package.
