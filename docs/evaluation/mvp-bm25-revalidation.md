# MVP BM25 revalidation after simplification

- Date: 2026-07-27
- Status: Passed
- Selected policy: `bm25-v1`

## Purpose

This check verifies that removing dense retrieval, RRF, cross-encoder reranking, notebook parsing,
and repository-code parsing did not change the selected official-API retrieval path. It also
separates the historical policy comparison from validation of the simplified codebase.

“BM85” in the approval discussion is interpreted as BM25, the retrieval algorithm implemented and
measured by this repository.

## Historical policy comparison

The controlled Phase 4 comparison used four PyMC 6.1.0 API pages, 15 chunks, 30 queries, and
`top_k=3`.

| Policy | Recall@3 | MRR | nDCG@3 | Mean latency |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.925926 | 0.771605 | 0.811723 | 0.079583 ms |
| Dense BGE | 0.814815 | 0.685185 | 0.718251 | 9.241087 ms |
| Hybrid RRF | 0.925926 | 0.783951 | 0.820543 | 9.395983 ms |
| Cross-encoder | 0.888889 | 0.777778 | 0.806873 | 287.972640 ms |

Hybrid preserved recall and changed MRR by only `+0.012346` while requiring the complete learned-
embedding path. Dense retrieval regressed every reported ranking-quality aggregate. The tested
cross-encoder regressed recall and nDCG and was orders of magnitude slower on the measured CPU.
These results do not prove that learned retrieval can never help; they establish that the tested
alternatives did not justify MVP complexity on this corpus.

## Clean rebuild and retrieval result

The four checked-in manifests and HTML fixtures were ingested into a new temporary directory with
the current `rag-pymc ingest` command. The build produced four documents and 15 chunks. The current
`rag-pymc evaluate` command was then run with:

- dataset SHA-256
  `5f5eb1f0e42a77759a5a1b33bae26fa43264002238633ed93a3d0d6695aa454b`;
- corpus SHA-256
  `d9a1ab1df0eac3ff0544bd99d4e499c1306151036c82df3789c249c90de07910`;
- tokenizer `technical-v1`;
- `k1=1.5`, `b=0.75`, `top_k=3`, and seed `20260720`.

The post-cleanup report exactly matched every stored identity, configuration value, per-query
ranking, and non-latency aggregate in `reports/evaluation/phase4-bm25-expanded.json`:

| Metric | Revalidated value |
| --- | ---: |
| Recall@3 | 0.925926 |
| Precision@3 | 0.320988 |
| Hit rate@3 | 0.925926 |
| MRR | 0.771605 |
| nDCG@3 | 0.811723 |
| Correct abstention rate | 0.666667 |
| Version correctness | 1.000000 |

Latency was deliberately excluded from the equality assertion because it is machine-specific.

## Software validation

The simplified repository passed:

- Ruff format and lint checks over all active Python and agent utility files;
- strict mypy checks over `src`, `tests`, `scripts`, and `.agents/skills`;
- 296 tests on Python 3.12.13 and Python 3.13.5;
- 84.79% branch coverage, above the enforced 84% floor;
- `rag-pymc doctor` in the development environment and from the built wheel; and
- source-distribution and wheel builds from the locked dependency graph.

CI repeats formatting, linting, typing, coverage-tested tests, CLI smoke testing, and packaging on
Python 3.12 and 3.13.

## Measured scope reduction

Relative to the repository state before this simplification:

| Surface | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| Locked packages | 176 | 67 | 61.9% |
| Product CLI commands | 16 | 5 | 68.8% |
| Product CLI lines | 1,314 | 316 | 75.9% |
| Runtime Python files | 63 | 48 | 23.8% |
| Runtime Python lines | 8,866 | 6,049 | 31.8% |
| Test Python files | 41 | 26 | 36.6% |
| Test Python lines | 8,535 | 5,773 | 32.4% |

Three annotation-data commands remain available through the explicitly internal
`rag-pymc-research` CLI. The runtime-line total includes the new small compatibility facade and the
split evaluation-contract modules, so the reduction does not come from compressing unrelated
contracts into a larger file.

## Interpretation

The simplification preserved the chosen BM25 behavior while deleting unsupported product surface.
The evidence supports keeping BM25 as the MVP baseline, not treating it as a permanent universal
winner. ADR-0014 defines the held-out evidence and material-benefit gate required before another
retrieval policy may be adopted.
