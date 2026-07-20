# ADR-0006: Use weighted RRF before cross-encoder reranking

- Status: Accepted
- Date: 2026-07-20

## Context

Phase 4 expands the controlled corpus from one to four official PyMC 6.1.0 API pages and
from five to 15 chunks. The sparse and dense retrievers already expose the same project-owned
contract, but their scores are not directly comparable: BM25 scores are unbounded lexical
relevance values, while exact cosine scores belong to a different scale.

The phase must determine whether combining the two ranked lists provides value before adding a
learned reranker. Introducing fusion and reranking in the same experiment would prevent the
observed change from being attributed to either component. The current 15-chunk corpus also
does not justify an approximate index or an external vector store.

## Decision

Implement weighted Reciprocal Rank Fusion behind the project-owned `Retriever` protocol.
Each component has a unique name and a finite positive weight. For a chunk at one-based rank
`r` in component `i`, its fused score is:

```text
sum_i weight_i / (rrf_k + r)
```

The Phase 4 baseline fixes:

- sparse and dense weights to 1.0;
- `rrf_k=60`;
- `candidate_k=10` per component;
- `top_k=3`;
- seed 20260720;
- deterministic ties by `chunk_id`.

The fusion adapter propagates every query filter to both retrievers, deduplicates a chunk
within each component ranking, and rejects conflicting chunk payloads for the same ID. It
fuses ranks rather than raw scores and returns the common `RetrievedChunk` model.

Evaluate fresh BM25, dense, and hybrid arms on the same content-addressed corpus and 30-query
dataset. Store overall metrics, intent and difficulty slices, per-query rankings, versions,
latencies, errors, and limitations. Do not tune weights or RRF parameters after observing the
baseline.

Cross-encoder reranking is deferred to a separate controlled experiment. That experiment must
start from this frozen hybrid candidate set and report its own latency and category-level
effects. Score thresholds and learned abstention are also separate decisions.

## Alternatives considered

### Normalize and add raw retrieval scores

Min-max or z-score normalization would add a calibration choice whose behavior depends on the
candidate set. Rank fusion avoids claiming that BM25 and cosine values have a shared meaning.

### Tune fusion weights on the evaluation dataset

This could improve the reported metric while overfitting the only labeled dataset. Equal
weights provide a transparent baseline. Future tuning requires a distinct development set.

### Add a cross-encoder in the same implementation

A reranker may improve ordering, but a combined change would obscure whether gains came from
candidate fusion or learned pair scoring. It is postponed until RRF has a measured baseline.

### Use LangChain or LlamaIndex fusion components

The algorithms are small and central to the experiment. Keeping them explicit preserves
filter behavior, deterministic ordering, metric provenance, and framework independence.

## Consequences

- Sparse and dense retrieval can be combined without calibrating their raw scores.
- Fusion behavior is deterministic for fixed component rankings.
- The stored experiment shows equal-weight RRF improves MRR over both individual retrievers,
  but does not improve Recall@3 over BM25.
- Hybrid query latency includes dense query encoding and is substantially higher than BM25.
- Equal weights and `rrf_k=60` are baseline choices, not validated optima.
- ADR-0007 uses this frozen candidate generator for a separate cross-encoder experiment. The
  measured reranker reduces aggregate quality, so equal-weight RRF remains the selected
  Phase 4 ranking policy.
