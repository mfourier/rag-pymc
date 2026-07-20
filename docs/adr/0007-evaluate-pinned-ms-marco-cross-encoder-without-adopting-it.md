# ADR-0007: Evaluate a pinned MS MARCO cross-encoder without adopting it

- Status: Accepted
- Date: 2026-07-20

## Context

ADR-0006 requires rank fusion to be measured before a learned reranker is introduced. The
equal-weight RRF baseline is now frozen at ten candidates, `rrf_k=60`, and final
`top_k=3`. Phase 4 still needs to determine whether pairwise query-document scoring improves
that candidate generator on the controlled PyMC benchmark.

The reranker is an experimental model dependency. Its identity, license, input limit, score
policy, candidate depth, and runtime must be explicit. It must remain behind a project-owned
interface so a negative result does not force the rest of retrieval to depend on one provider.

## Decision

Add a `Reranker` protocol that scores a sequence of domain `Chunk` values for one query.
Use a `RerankedRetriever` adapter to request a bounded candidate set, preserve metadata
filters, remove duplicate IDs, validate finite one-to-one scores, and sort deterministic ties
by upstream rank and then `chunk_id`.

Evaluate `cross-encoder/ms-marco-MiniLM-L6-v2` at immutable revision
`c5ee24cb16019beea0893ab7796b1df96625c6b8` under Apache-2.0. Run Sentence Transformers
5.6.0 on CPU with:

- ten candidates from the frozen equal-weight RRF policy;
- raw identity logits, without softmax or score calibration;
- maximum pair length 512 word pieces;
- batch size 16;
- final `top_k=3`;
- seed 20260720.

Keep weights in the external Hugging Face cache and store a manifest with model ID, revision,
source timestamp, download timestamp, license, package version, backend, and sequence limit.
The default runtime remains local-files-only after an explicit first download.

Compare the reranked arm with a freshly executed RRF control using the same corpus, dataset,
qrels, filters, seed, and metric implementation. Do not tune the model, candidate depth, or a
score threshold after observing the evaluation set.

The measured reranker is not adopted as the default Phase 4 ranking policy. Equal-weight RRF
remains the selected candidate ranking because the cross-encoder reduces aggregate retrieval
quality and materially increases CPU latency.

## Alternatives considered

### MiniLM L4

The model card reports higher throughput but lower ranking quality than L6 on its source
benchmarks. L6 was selected as a moderate compute-quality point for the first experiment.

### MiniLM L12

The model card reports almost the same TREC DL nDCG as L6 with substantially lower throughput
on the published hardware. The larger model was not justified for the first CPU experiment.

### A PyMC-specific fine-tuned reranker

No controlled training set exists yet. Fine-tuning on the 30-query evaluation data would
invalidate the benchmark and overfit the only qrels.

### Tune an abstention threshold from observed logits

The unsupported in-library query receives strongly negative logits, but selecting a threshold
from this evaluation set would be post hoc. Threshold selection requires a separate
development set and its own ADR.

## Consequences

- Reranking can be tested through provider-neutral contracts without changing retrieval,
  evaluation, or domain models.
- The reranker recovers the Beta-Binomial code example but loses two previously retrieved
  version-sensitive or posterior-prediction answers.
- Recall@3 changes from 0.925926 to 0.888889, MRR from 0.783951 to 0.777778, and nDCG@3 from
  0.820543 to 0.806873.
- Mean query latency increases by 278.311295 ms on the recorded CPU run.
- The negative outcome is preserved as a reproducible experiment rather than hidden through
  post-hoc parameter changes.
- Future reranker work requires a development split, more labeled queries, and a model or
  training objective better matched to technical API documentation.
