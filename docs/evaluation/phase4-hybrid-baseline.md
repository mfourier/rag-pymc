# Phase 4 hybrid retrieval and reranking

## Scope

This experiment expands the controlled PyMC 6.1.0 corpus to four official API pages and 15
structure-aware chunks. It evaluates fresh BM25 and exact-dense controls, then combines their
rankings with equal-weight Reciprocal Rank Fusion. No source, qrel, fusion weight, or RRF
parameter was changed after observing the results.

The machine-readable artifacts are:

- `reports/evaluation/phase4-bm25-expanded.json`;
- `reports/evaluation/phase4-dense-expanded.json`;
- `reports/evaluation/phase4-hybrid-rrf.json`;
- `reports/evaluation/phase4-bm25-vs-hybrid.json`;
- `reports/evaluation/phase4-dense-vs-hybrid.json`;
- `reports/evaluation/phase4-hybrid-reranker-control.json`;
- `reports/evaluation/phase4-cross-encoder-reranked.json`;
- `reports/evaluation/phase4-hybrid-vs-reranked.json`.

## Corpus and dataset

The corpus contains `pymc.sample`, `pymc.Data`, `pymc.set_data`, and
`pymc.sample_posterior_predictive` from the official PyMC 6.1.0 documentation. Source
manifests fix release `v6.1.0`, source commit
`56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`, Apache-2.0 license, acquisition metadata,
URLs, and raw SHA-256 values.

The evaluation dataset contains 30 queries: 27 answerable and three unanswerable. It covers
API lookup, code lookup, conceptual explanation, posterior prediction, shape and dimensions,
version-sensitive lookup, and out-of-corpus questions. The dataset is manually curated for
this corpus and is not an external benchmark.

The dataset SHA-256 is
`5f5eb1f0e42a77759a5a1b33bae26fa43264002238633ed93a3d0d6695aa454b`; the corpus
SHA-256 is `d9a1ab1df0eac3ff0544bd99d4e499c1306151036c82df3789c249c90de07910`.

## Reproduction

Build `datasets/processed/phase4` with the four hash-verified ingestion commands documented
in the README. The pinned BGE model revision must already be cached, or the first run needs
the explicit `--allow-download` flag.

```bash
uv run rag-pymc evaluate-hybrid
uv run rag-pymc evaluate-reranked
```

The experiment fixes:

- BM25 `k1=1.5` and `b=0.75`;
- `BAAI/bge-small-en-v1.5` revision
  `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`;
- normalized 384-dimensional embeddings and exact cosine retrieval;
- equal sparse and dense weights, `rrf_k=60`, and `candidate_k=10`;
- `top_k=3`, batch size 16, CPU execution, and seed 20260720.

## Results

| Metric | BM25 | Dense | Hybrid RRF |
|---|---:|---:|---:|
| Recall@3 | 0.925926 | 0.814815 | 0.925926 |
| Precision@3 | 0.320988 | 0.283951 | 0.320988 |
| Hit Rate@3 | 0.925926 | 0.814815 | 0.925926 |
| MRR | 0.771605 | 0.685185 | 0.783951 |
| nDCG@3 | 0.811723 | 0.718251 | 0.820543 |
| Correct abstention | 0.666667 | 0.666667 | 0.666667 |
| Version correctness | 1.000000 | 1.000000 | 1.000000 |
| Mean query latency, ms | 0.079583 | 9.241087 | 9.395983 |
| Mean retrieved tokens | 1601.00 | 1152.20 | 1609.97 |

Relative to BM25, hybrid changes MRR by +0.012346 and nDCG@3 by +0.008820 while Recall@3,
Precision@3, and Hit Rate@3 remain unchanged. Mean query latency increases by 9.316400 ms.

Relative to dense retrieval, hybrid changes Recall@3 and Hit Rate@3 by +0.111111, MRR by
+0.098765, and nDCG@3 by +0.102291. Mean query latency increases by 0.154896 ms.

Dense setup took 1116.193559 ms and hybrid setup took 1117.876364 ms, excluding model
download. Five of the 15 chunks exceed the model's 512-word-piece input window. Latency is
machine-specific and should not be generalized.

## Category analysis

Hybrid improves API-lookup MRR from 0.750000 under BM25 to 0.833333 and recovers the
shape-and-dimensions hit rate from 0.500000 to 1.000000. It reduces code-lookup Hit Rate from
1.000000 to 0.500000 and posterior-prediction MRR from 1.000000 to 0.666667 relative to BM25.

Several slices contain very few examples: conceptual explanation has one query, code lookup
and shape/dimensions have two each, and posterior prediction and version-sensitive lookup have
three each. These values identify hypotheses for the next dataset revision; they are not
stable estimates of category performance.

## Error analysis

Hybrid misses two answerable questions:

- `q_010` asks what changes when `return_inferencedata` is false. Neither relevant
  `pymc.sample` chunk enters the fused top three.
- `q_016` asks for the documented minimal Beta-Binomial example. BM25 retrieves it, but its
  dense rank lowers it outside the fused top three.

BM25 also misses two questions, but its second miss is `q_024`, about shape changes under
`pymc.set_data`. Hybrid recovers `q_024` while losing `q_016`; aggregate Recall is
therefore unchanged.

All methods correctly return no results for the ArviZ and PyTensor out-of-corpus questions
because library filters exclude the PyMC-only corpus. All incorrectly retrieve PyMC chunks
for `q_020`, an ArviZ-divergence question labeled with library `pymc`. Correct abstention
is consequently 2/3. This baseline has no threshold or learned abstention policy.

## Cross-encoder reranking

After freezing the RRF baseline, a second experiment reranks its top ten candidates with
`cross-encoder/ms-marco-MiniLM-L6-v2` at revision
`c5ee24cb16019beea0893ab7796b1df96625c6b8`. The model is Apache-2.0, runs through
Sentence Transformers 5.6.0 on CPU, consumes at most 512 word pieces per query-document pair,
and returns raw identity logits. No threshold or parameter was selected after observing the
results.

| Metric | Fresh RRF control | Cross-encoder | Delta |
|---|---:|---:|---:|
| Recall@3 | 0.925926 | 0.888889 | -0.037037 |
| Precision@3 | 0.320988 | 0.308642 | -0.012346 |
| Hit Rate@3 | 0.925926 | 0.888889 | -0.037037 |
| MRR | 0.783951 | 0.777778 | -0.006173 |
| nDCG@3 | 0.820543 | 0.806873 | -0.013669 |
| Correct abstention | 0.666667 | 0.666667 | 0.000000 |
| Version correctness | 1.000000 | 1.000000 | 0.000000 |
| Mean query latency, ms | 9.661346 | 287.972640 | +278.311295 |
| Mean retrieved tokens | 1609.97 | 1166.10 | -443.87 |

RRF setup took 1179.920772 ms and total setup with the cached cross-encoder took 1242.408483
ms. Model download is excluded. Reranked p50 query latency was 302.903065 ms and p95 was
322.670864 ms on this machine.

The reranker and control each win four question-level first-relevant-rank comparisons; 22
queries tie. The reranker:

- improves `q_002`, `q_016`, `q_021`, and `q_024`;
- degrades `q_008`, `q_018`, `q_023`, and `q_028`;
- recovers the Beta-Binomial code example in `q_016`;
- loses the backend-version answer in `q_018` and prediction-group answer in `q_028`;
- keeps the existing `q_010` miss.

Category slices show code-lookup Hit Rate increasing by 0.500000, while posterior-prediction
and version-sensitive Hit Rate each decrease by 0.333333. These slices contain only two or
three questions, so they are diagnostic examples rather than stable estimates.

The unsupported `q_020` still returns three chunks, although all three logits are strongly
negative. This suggests a threshold experiment, but selecting one from the evaluation set
would be post-hoc tuning. A separate development set is required.

## Interpretation

Equal-weight RRF remains the selected Phase 4 ranking policy. It improves ranking quality over
dense retrieval and slightly improves first-relevant ordering over BM25, although it does not
improve BM25 Recall and carries dense-encoding latency.

The tested general-domain cross-encoder is not adopted. It reduces Recall, MRR, and nDCG while
adding about 278 ms per query on CPU. The implementation remains behind the `Reranker`
protocol for future models, but another reranker experiment requires a development split and
more labeled technical queries.

Phase 4 is complete at the retrieval-policy level: expanded corpus, metadata filtering,
sparse/dense fusion, category evaluation, and a measured reranker are present. Parent-child
chunking and learned abstention remain separate experiments; grounded response construction
is the next roadmap phase.
