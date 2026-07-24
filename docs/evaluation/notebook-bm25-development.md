# Notebook BM25 development baseline

## Scope

This experiment evaluates the first controlled PyMC 6.1.0 conceptual-notebook corpus. The
corpus contains three normalized documents and 34 section- and cell-aware chunks from:

- Distribution Dimensionality;
- PyMC and PyTensor;
- Model comparison.

The development dataset contains eight answerable conceptual questions and two deliberately
unanswerable PyMC questions outside the selected notebook scope. It is not held out and cannot
support broad notebook-retrieval claims.

The machine-readable report is
`reports/evaluation/notebook-bm25-development.json`.

## Configuration

- PyMC version: `6.1.0`
- PyMC source commit: `56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`
- Source type: `notebook`
- Parser: `jupyter-notebook-inputs-v1`
- Chunker: `notebook-cells-v1`
- Corpus: 3 documents, 34 chunks
- Retriever: `bm25-v1`
- Tokenizer: `technical-v1`
- `k1`: 1.5
- `b`: 0.75
- `top_k`: 3
- Seed: 20260724

## Results

| Metric | Value |
| --- | ---: |
| Recall@3 | 1.000000 |
| Hit rate@3 | 1.000000 |
| MRR | 1.000000 |
| nDCG@3 | 1.000000 |
| Precision@3 | 0.333333 |
| Correct abstention | 0.000000 |
| Version correctness | 1.000000 |
| Mean retrieved technical tokens | 880.30 |

Every answerable query retrieved its judged chunk at rank one. The questions cover support and
batch dimensions, implicit parameter broadcasting, shape debugging, symbolic compilation,
PyTensor graph structure, transformed value variables, pointwise log likelihood, and ELPD.

Both unanswerable queries returned three chunks. A posterior-prediction question retrieved model
comparison and dimensionality material; a Gaussian Process question retrieved unrelated
PyTensor material. The current BM25 retriever has no semantic no-answer mechanism, so the
correct-abstention rate is zero.

## Interpretation

The perfect answerable-query ranking is a development-set pipeline result, not a general quality
estimate. The selected notebooks use distinctive vocabulary and the qrels were authored after
the corpus was inspected.

The zero abstention result is more consequential for adoption. Adding conceptual breadth without
a calibrated sufficiency decision increases the amount of superficially related evidence that
can be returned for unsupported questions. The existing conservative policy should continue to
abstain rather than interpreting nonempty retrieval as sufficient evidence.

## Decision

Keep notebooks as an opt-in corpus and retain the Phase 4 default. Before adoption:

1. create a held-out conceptual query set;
2. measure dense and hybrid retrieval with truncation counts;
3. run unfiltered documentation regressions on a mixed corpus;
4. calibrate evidence signals using the separate Phase 5 development process;
5. test cell-level citations and prompt-safe notebook framing.

No threshold, source-routing policy, or default-context change is justified by this development
baseline alone.
