# Phase 3 dense retrieval baseline

## Scope

This experiment evaluates exact dense retrieval over the same controlled PyMC 6.1.0 corpus
and 20-query dataset used by Phase 2. It compares the dense candidate with a freshly executed
BM25 control. No model, query, qrel, threshold, or chunk was changed after observing results.

The machine-readable artifacts are:

- `reports/evaluation/phase3-dense-baseline.json`;
- `reports/evaluation/phase3-sparse-vs-dense.json`.

## Reproduction

The first command may access Hugging Face to cache the exact pinned model revision:

```bash
uv run rag-pymc evaluate-dense --allow-download
```

Once cached, the default is offline:

```bash
uv run rag-pymc evaluate-dense
```

The experiment used:

- `BAAI/bge-small-en-v1.5` at revision
  `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`;
- Sentence Transformers 5.6.0 and CPU-only PyTorch 2.13.0;
- normalized 384-dimensional embeddings and exact cosine similarity;
- the documented BGE retrieval query prefix;
- batch size 16, `top_k=3`, and seed 20260719;
- five chunks from the official `pymc.sample` page for PyMC 6.1.0;
- 18 answerable and two unanswerable queries.

The dataset SHA-256 is
`5df8628e7c22042784cf5361cafbbbc204b8cdc7313f43508dec6e7a8c6eba87`; the corpus
SHA-256 is `8f1329ac43e8b4c93667c96f87094ac114be87a6b99f99b489cab32b017bf21e`.

## Results

| Metric | BM25 control | Dense | Dense minus BM25 |
|---|---:|---:|---:|
| Recall@3 | 1.000000 | 0.944444 | -0.055556 |
| Precision@3 | 0.351852 | 0.333333 | -0.018519 |
| Hit Rate@3 | 1.000000 | 0.944444 | -0.055556 |
| MRR | 0.842593 | 0.814815 | -0.027778 |
| nDCG@3 | 0.882933 | 0.847881 | -0.035052 |
| Correct abstention | 0.000000 | 0.000000 | 0.000000 |
| Version correctness | 1.000000 | 1.000000 | 0.000000 |
| Mean query latency, ms | 0.044216 | 9.708342 | +9.664126 |
| Mean retrieved tokens | 1460.30 | 1100.15 | -360.15 |

Dense setup took 412.091749 ms, excluding download. Dense query latency had a 9.669636 ms
median and 10.572260 ms p95 in this run. These wall-clock measurements describe this machine
and corpus only.

Dense placed the first relevant chunk earlier for three queries (`q_002`, `q_012`, and
`q_014`). BM25 did better for two (`q_016` and `q_018`); the other 15 tied. The aggregate
result therefore does not justify replacing BM25 with dense retrieval.

## Error analysis

The only answerable dense miss was `q_018`: "Which computational backend values are
recommended by pymc.sample in PyMC 6.1.0?" Its relevant evidence is in the Parameters chunk,
which was outside the top three dense results but ranked first under BM25.

The embedding model accepts at most 512 word pieces. Measured without truncation, Parameters
contains 1945 word pieces and Notes contains 611; both are truncated during document
embedding. The missed `backend` entry occurs late in Parameters, so truncation is a plausible
explanation for `q_018`, but this experiment does not isolate causality. A structure-aware
parent-child chunking comparison is required to test it.

Neither retriever abstained on the two unanswerable questions because no score threshold or
abstention classifier exists. Correct abstention therefore remains 0.0 by design.

## Interpretation

The dense retriever captures useful semantic matches and improves three individual ranks,
but BM25 remains stronger on this narrow API-lookup dataset. Dense retrieval also reduces
retrieved context size, while increasing query latency by roughly 9.7 ms. The small corpus,
dataset construction, and one-page subject matter prevent broader quality claims.

Phase 4 should preserve both baselines and test hybrid rank fusion. Before attributing gains
to fusion, the benchmark should also expand beyond one API symbol. Truncation-aware chunking
must be evaluated as a separate experimental variable rather than silently changing this
baseline.
