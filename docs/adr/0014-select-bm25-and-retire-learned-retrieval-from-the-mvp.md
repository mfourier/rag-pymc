# ADR-0014: Select BM25 and retire learned retrieval from the MVP

- Status: Accepted
- Date: 2026-07-27

## Context

Phases 2 through 4 implemented and measured BM25, exact dense retrieval with pinned BGE
embeddings, equal-weight Reciprocal Rank Fusion, and cross-encoder reranking. The experiments
established that every implementation path worked, preserved version filters, and emitted
versioned per-query reports.

The active corpus contains four PyMC 6.1.0 API pages and 15 chunks. On its frozen 30-query dataset,
BM25 and hybrid RRF both achieved Recall@3 `0.925926`. Hybrid changed MRR from `0.771605` to
`0.783951` and nDCG@3 from `0.811723` to `0.820543`, while mean query latency increased from
`0.079583` ms to `9.395983` ms. Dense retrieval alone performed worse on Recall, MRR, and nDCG.

The tested cross-encoder reduced Recall@3 from the fresh RRF control's `0.925926` to `0.888889`,
reduced MRR from `0.783951` to `0.777778`, and increased mean latency from `9.661346` ms to
`287.972640` ms. Five chunks exceeded the embedding model's 512-word-piece window.

The learned paths also required Torch, Transformers, Sentence Transformers, pinned external model
manifests, first-run downloads, local cache state, truncation accounting, device and batch options,
and separate search and evaluation commands.

## Decision

Use explicit in-memory BM25 as the only active retrieval policy for the MVP, with `k1=1.5`,
`b=0.75`, the `technical-v1` tokenizer, and exact metadata filters.

Remove dense, hybrid, and reranking implementations, protocols, model adapters, dependencies,
runtime builders, public CLI commands, configuration models, and feature-specific tests from the
installed project. Retain the exact manifests, frozen inputs, reports, evaluation narratives, and
earlier ADRs as historical evidence.

Context inspection must use the selected BM25 retriever directly and expose `bm25-v1` provenance.
The project must not claim that learned retrieval was never tested; it must report that the tested
alternatives did not provide enough measured benefit for their complexity.

Learned retrieval may be proposed again only after:

1. a materially different corpus, such as a controlled scientific-literature slice, exists;
2. a held-out evaluation dataset and adoption metrics are fixed before observing results;
3. BM25 is rerun as a fresh control on the same corpus and queries;
4. recall and correct abstention do not regress;
5. any MRR, nDCG, or semantic-support improvement is judged material under a predeclared rule; and
6. model size, download behavior, setup cost, query latency, truncation, and offline reproducibility
   are included in the adoption decision.

## Alternatives considered

### Keep hybrid RRF because it had the highest MRR

Rejected because the gain was small, Recall@3 did not improve, and it imposed the entire learned
embedding dependency and runtime path.

### Keep dense and reranking code behind optional extras

Rejected for the MVP because optional code still expands contracts, tests, commands, maintenance,
and architectural decisions. Git history and stored reports are sufficient until a new experiment
has a credible adoption path.

### Keep the cross-encoder as an experimental command

Rejected because its measured result was worse and much slower. A permanent negative-result command
would turn research history into supported product surface.

### Remove the historical reports and manifests

Rejected because the negative and near-neutral results justify the simpler policy. Preserving exact
evidence prevents the same experiment from being repeated without a new hypothesis.

## Consequences

- The base lock no longer includes Torch, Transformers, Sentence Transformers, Jupyter, or learned
  retrieval model dependencies.
- Search, context inspection, and retrieval evaluation are deterministic and fully offline.
- The public CLI has one retrieval vocabulary instead of sparse, dense, hybrid, and reranked
  variants.
- Historical learned-retrieval JSON reports are not guaranteed to validate against current runtime
  models; they are immutable archival artifacts tied to the earlier implementation and Git history.
- Conceptual paper retrieval may eventually require a learned method, but it must earn adoption on
  the actual literature corpus rather than inherit it from the former API experiment.

The post-cleanup revalidation is recorded in
[`docs/evaluation/mvp-bm25-revalidation.md`](../evaluation/mvp-bm25-revalidation.md).
