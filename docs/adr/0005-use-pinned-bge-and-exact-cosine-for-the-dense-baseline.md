# ADR-0005: Use pinned BGE and exact cosine for the dense baseline

- Status: Accepted
- Date: 2026-07-19

## Context

Phase 3 needs a reproducible semantic retrieval baseline that can be compared directly with
the Phase 2 BM25 baseline. The corpus contains only five chunks, so an approximate-nearest-
neighbor service would add operational behavior without providing useful scale benefits.

The embedding model is part of the experiment, not an interchangeable implementation detail.
Its weights, license, input policy, sequence limit, and package version must be explicit. Model
weights are also too large to store in this repository and already have a content-addressed
cache mechanism through Hugging Face.

## Decision

Use `BAAI/bge-small-en-v1.5` at Git revision
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` under its MIT license. Run it through
Sentence Transformers 5.6.0 on CPU with normalized 384-dimensional embeddings, a batch size
of 16, and seed 20260719. Prefix queries with the model card's retrieval instruction:

```text
Represent this sentence for searching relevant passages:
```

The adapter distinguishes document and query encoding, validates the package version,
revision-derived model properties, matrix shape, and finite values, and defaults to local
files only. An explicit CLI flag may download the exact revision. Weights remain in the
external Hugging Face cache; the repository stores a provenance manifest, not model binaries.

Use an immutable in-memory index that computes exact cosine similarity. Filter chunks before
query encoding and ranking, sort equal scores by `chunk_id`, and return project-owned
`RetrievedChunk` models. Record setup and per-query latency separately.

Compare dense retrieval with a newly executed BM25 control using the same corpus, query
dataset, filters, `top_k`, seed, qrels, and metric implementation. Do not tune the embedding
model or add a score threshold after observing this baseline.

Pin the direct CPU-only PyTorch dependency through uv's official PyTorch CPU index. This
prevents CUDA runtime packages from entering the reproducible development environment.

## Alternatives considered

### Use a general sentence-similarity model

Small general-purpose models are inexpensive, but asymmetric technical retrieval is the
actual task. A retrieval-trained model with a documented query policy was selected instead.

### Use an embedding model without explicit license provenance

This would reduce initial selection work but violate the project's source and dependency
provenance requirements. It was rejected.

### Use pgvector or an approximate-nearest-neighbor library

These options become useful with a larger corpus. For five chunks they introduce persistence,
index parameters, and approximation effects that cannot improve the baseline's validity.

### Store model weights in Git

This would make the repository unnecessarily large and duplicate a revision-addressed cache.
The exact model ID and revision are sufficient to retrieve and verify the selected artifact.

## Consequences

- Dense retrieval can be exercised through the same retriever contract as BM25.
- The baseline is deterministic in ranking for the fixed environment, except for measured
  wall-clock latency.
- A first online run requires an explicit model download; later runs can be offline.
- Two current chunks exceed the model's 512-word-piece input limit and are truncated during
  embedding. The report records this count so chunking changes can be tested in a later phase.
- Exact search is intentionally not suitable for a large corpus; the `DenseIndex` boundary
  permits a later replacement based on measured scale and latency.
- Dense scores are not calibrated confidence values. Abstention remains zero until a policy is
  defined and evaluated.
