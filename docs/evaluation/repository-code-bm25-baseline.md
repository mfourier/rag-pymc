# Repository-code BM25 development baseline

## Scope

This experiment measures the first PyMC 6.1.0 implementation corpus independently from the
frozen Phase 4 documentation corpus. It contains four normalized documents and 19 AST-aware
chunks for `pymc.sample`, `pymc.Data`, `pymc.model.core.set_data`, and
`pymc.sample_posterior_predictive`.

The development dataset contains seven answerable implementation questions and one
out-of-corpus ArviZ question. It is not a held-out evaluation and cannot support broad claims
about source-code retrieval.

The machine-readable report is
`reports/evaluation/repository-code-bm25-baseline.json`.

## Configuration

- PyMC version: `6.1.0`
- PyMC source commit: `56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`
- Source type: `repository_code`
- Parser: `python-repository-ast-v1`
- Chunker: `repository-code-ast-v1`
- Corpus: 4 documents, 19 chunks
- Retriever: `bm25-v1`
- Tokenizer: `technical-v1`
- `k1`: 1.5
- `b`: 0.75
- `top_k`: 3
- Seed: 20260723

## Results

| Metric | Value |
| --- | ---: |
| Recall@3 | 0.714286 |
| Hit rate@3 | 0.714286 |
| MRR | 0.476190 |
| nDCG@3 | 0.537409 |
| Precision@3 | 0.238095 |
| Correct abstention | 1.000000 |
| Version correctness | 1.000000 |
| Mean retrieved technical tokens | 375.25 |

Five of seven answerable queries retrieved their judged implementation chunk in the first
three results. The single unanswerable query returned no results because its ArviZ library
filter does not match the PyMC corpus. This does not measure semantic abstention.

## Error analysis

`code_001`, which asks where the exclusive-NUTS path initializes NUTS, retrieved three other
`pymc.sample` implementation chunks. The relevant initialization block was not in the first
three results. Lexical BM25 identifies the correct symbol but has insufficient block-level
resolution for this wording.

`code_003`, which asks how top-level `pymc.set_data` processes `new_data`, retrieved the
function definition first but not its short implementation chunk in the first three. Other
chunks mentioning data mutation displaced the exact delegation body. Symbol-aware query
routing or a definition-to-implementation adjacency policy is a plausible experiment; it is
not adopted by this result.

The strongest results use distinctive implementation vocabulary: automatic nutpie selection,
list conversion in `pymc.Data`, the Potentials warning, `freeze_vars`, and conflicting DataTree
groups.

## Decision

Keep repository code as an opt-in evidence layer. The baseline establishes that the pipeline,
provenance, AST chunking, and source-type filtering work, but Recall@3 is not sufficient to
merge code into default retrieval without further experiments.

Next experiments should compare:

1. BM25 with extracted API-symbol filters;
2. definition-to-implementation adjacency expansion;
3. dense and hybrid retrieval on the same frozen development set;
4. a mixed API/code corpus on an unfiltered copy of the Phase 4 queries;
5. a new held-out implementation dataset before adopting a routing policy.

No threshold, learned reranker, or default-context change is justified by this development
baseline.
