# ADR-0004: Use explicit BM25 and versioned evaluation artifacts

- Status: Accepted
- Date: 2026-07-19

## Context

Phase 2 needs an inspectable lexical baseline before adding embeddings. The implementation must
make tokenization, filtering, ranking, and metric conventions visible. A generic retrieval
framework or an opaque search service would make it harder to attribute changes in later
experiments.

The corpus currently contains five semantic chunks from one PyMC 6.1.0 API page. This scale
does not justify a persistent index service, but it is sufficient to test the complete
ingestion-to-evaluation path and expose initial failure modes.

## Decision

Implement Okapi BM25 directly as an immutable in-memory index behind the project-owned
`SparseIndex` protocol. Use:

- `k1=1.5` and `b=0.75`;
- `log(1 + (N - df + 0.5) / (df + 0.5))` for inverse document frequency;
- document length normalization over the metadata-filtered candidate set;
- exact filters for library version and source type, case-insensitive filters for library and
  API symbol;
- positive-score results only;
- descending score followed by `chunk_id` for deterministic ties.

The `technical-v1` tokenizer case-folds terms while preserving dotted Python symbols,
underscores, and decimal values. It does not remove stopwords or apply stemming.

Version a manual JSONL dataset containing 20 questions: 18 answerable questions with binary
chunk qrels and two intentionally unanswerable questions. Store each experiment as a
machine-validated JSON report with configuration, seed, dataset hash, corpus hash, software
versions, aggregate metrics, per-query rankings, errors, and limitations.

Use Recall@k, Precision@k, Hit Rate@k, MRR, binary nDCG@k, correct abstention, version
correctness, latency, and retrieved token count. Precision@k uses the configured `k` as its
denominator. Token counts use `technical-v1`, not a future LLM tokenizer. No retrieval score
threshold is applied in the baseline.

## Alternatives considered

### Use an external BM25 package

This reduces formula code but leaves little implementation to validate and teach. It may be
reconsidered when corpus scale requires an optimized inverted index.

### Use PostgreSQL full-text search

This adds operational state before corpus size or query load warrants it and would couple the
first baseline to persistence infrastructure.

### Implement explicit in-memory BM25

The formula and ranking inputs remain testable with hand calculations, and the implementation
can later serve as the reference baseline. This alternative was selected.

## Consequences

- The baseline is deterministic except for wall-clock latency and report generation time.
- The corpus is loaded and tokenized per process; this is unsuitable for a large corpus.
- Stopwords may generate false-positive matches and the absence of a threshold prevents useful
  abstention. Both behaviors are measured rather than tuned after seeing the baseline.
- Scores are only comparable within one filtered corpus and one configuration.
- The large Parameters chunk can inflate context size; its granularity is now an experimental
  variable for a later controlled comparison.
- Dense and hybrid retrievers must use the same evaluation contracts and qrels where valid.
