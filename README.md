# rag-pymc

`rag-pymc` is an evidence-grounded adaptive tutor for learning probabilistic programming
with PyMC. The project is designed as an Applied Science system: retrieval quality,
version correctness, pedagogical behavior, and reproducibility are first-class concerns.

The repository has completed **Phase 4: hybrid retrieval and reranking**. It can ingest four
controlled PyMC 6.1.0 API pages, search 15 structure-aware chunks with BM25, exact dense
retrieval, weighted Reciprocal Rank Fusion, or cross-encoder reranking, and compare all methods
on a versioned 30-query dataset. Equal-weight RRF remains the selected ranking policy because
the measured cross-encoder reduces quality and adds substantial CPU latency. Learned
abstention and generation are not yet implemented.

## Design principles

- Keep domain models independent from orchestration frameworks and external providers.
- Preserve source provenance and library versions from ingestion through citation.
- Establish measurable retrieval baselines before adding generation or tuning learned rankers.
- Treat evaluation datasets, seeds, configurations, and per-query results as versioned
  research artifacts.
- Grow the package around working vertical slices instead of creating empty modules.

Architecture decisions are documented in the [architecture overview](docs/architecture/overview.md),
[ADR-0001](docs/adr/0001-keep-the-core-independent-from-langchain.md),
[ADR-0002](docs/adr/0002-version-source-snapshots-and-content-addressed-artifacts.md),
[ADR-0003](docs/adr/0003-use-jsonl-for-the-local-corpus-baseline.md),
[ADR-0004](docs/adr/0004-use-explicit-bm25-and-versioned-evaluation-artifacts.md),
[ADR-0005](docs/adr/0005-use-pinned-bge-and-exact-cosine-for-the-dense-baseline.md),
[ADR-0006](docs/adr/0006-use-weighted-rrf-before-cross-encoder-reranking.md), and
[ADR-0007](docs/adr/0007-evaluate-pinned-ms-marco-cross-encoder-without-adopting-it.md).
Measured behavior is documented in the
[Phase 2 sparse](docs/evaluation/phase2-sparse-baseline.md),
[Phase 3 dense](docs/evaluation/phase3-dense-baseline.md), and
[Phase 4 hybrid](docs/evaluation/phase4-hybrid-baseline.md) reports.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) 0.11.29 or newer recommended
- Git, for installing the pre-commit hooks

The scientific compatibility baseline was checked on 2026-07-19 against the published
releases of [PyMC 6.1.0](https://pypi.org/project/pymc/6.1.0/),
[ArviZ 1.2.0](https://pypi.org/project/arviz/1.2.0/), and
[PyTensor 3.1.3](https://pypi.org/project/pytensor/3.1.3/). Exact resolved transitive
versions are recorded in `uv.lock`.

## Install

```bash
uv sync --all-groups
uv run pre-commit install
uv run rag-pymc doctor
```

`uv sync` creates or updates `.venv` from `pyproject.toml` and `uv.lock`. No separate
`requirements.txt` is maintained; this avoids two competing dependency specifications.
PyTorch is resolved from its official CPU-only package index. Embedding and reranking model
weights are not stored in Git: an explicit `--allow-download` on the first corresponding
command caches each exact revision outside the repository, while later commands default to
local files only.

## Ingest the controlled sources

The checked-in fixtures are hash-verified snapshots of four official PyMC 6.1.0 API pages.
All ingestion commands are offline.

Build the original one-page corpus used by Phases 2 and 3:

```bash
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample.html \
  --output-dir datasets/processed/local
```

Build the expanded Phase 4 corpus:

```bash
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample.html \
  --output-dir datasets/processed/phase4
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.Data.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.Data.html \
  --output-dir datasets/processed/phase4
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.model.core.set_data.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.model.core.set_data.html \
  --output-dir datasets/processed/phase4
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample_posterior_predictive.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample_posterior_predictive.html \
  --output-dir datasets/processed/phase4
```

A successful Phase 4 build writes four documents and 15 deterministic chunks. Repeating the
commands upserts the same records. Local processed output is ignored by Git; source fixtures
and manifests are tracked.

## Search the local corpus with BM25

```bash
uv run rag-pymc search "How do I pass target_accept to NUTS?" \
  --corpus-dir datasets/processed/local \
  --library pymc \
  --library-version 6.1.0 \
  --top-k 3
```

Each result includes its score, chunk ID, section, exact library version, and source URL.

## Search the local corpus with dense retrieval

```bash
# First run only, when the pinned model revision is not cached:
uv run rag-pymc search-dense "How do I pass target_accept to NUTS?" --allow-download

# Reproducible offline run after the model is cached:
uv run rag-pymc search-dense "How do I pass target_accept to NUTS?" \
  --corpus-dir datasets/processed/local \
  --library pymc --library-version 6.1.0 --top-k 3
```

## Search the expanded corpus with hybrid retrieval

```bash
uv run rag-pymc search-hybrid "How do I update predictors for prediction?" \
  --corpus-dir datasets/processed/phase4 \
  --library pymc --library-version 6.1.0 --top-k 3
```

The command fuses ten BM25 and ten dense candidates with equal-weight RRF, then returns the
top three. Use `--allow-download` only when the pinned embedding revision is not cached.

## Search with the experimental reranker

```bash
uv run rag-pymc search-reranked "Where are prediction samples stored?" \
  --corpus-dir datasets/processed/phase4 \
  --library pymc --library-version 6.1.0 --top-k 3
```

This command reranks the frozen RRF top ten with the pinned MS MARCO cross-encoder. It is
available for experimentation but is not the selected default policy.

## Reproduce the sparse baseline

```bash
uv run rag-pymc evaluate \
  --dataset datasets/evaluation/phase2/pymc_sample_queries.jsonl \
  --corpus-dir datasets/processed/local \
  --output reports/evaluation/phase2-bm25-baseline.json \
  --top-k 3 \
  --seed 20260719 \
  --k1 1.5 \
  --b 0.75
```

The first run achieved Recall@3 1.000000, MRR 0.842593, nDCG@3 0.882933, and correct
abstention 0.000000. These values validate this narrow pipeline only; the corpus contains one
page and five chunks. The report preserves all rankings and limitations.

## Reproduce the dense baseline and comparison

```bash
uv run rag-pymc evaluate-dense
```

The command writes `reports/evaluation/phase3-dense-baseline.json` and
`reports/evaluation/phase3-sparse-vs-dense.json`.

At `k=3`, dense retrieval achieved Recall 0.944444, MRR 0.814815, and nDCG 0.847881.
The freshly executed BM25 control achieved Recall 1.000000, MRR 0.842593, and nDCG 0.882933.
Dense improved the first relevant rank for three queries, BM25 did better for two, and 15
tied. Both methods had correct abstention 0.000000 because no threshold policy exists.

The BGE model truncates inputs beyond 512 word pieces. Two of the five current chunks exceed
that limit, and the only answerable dense miss targets evidence late in the Parameters chunk.
The report records this limitation; it does not establish truncation as the cause.

## Reproduce the Phase 4 hybrid baseline

```bash
uv run rag-pymc evaluate-hybrid
```

The command executes fresh BM25, dense, and equal-weight RRF arms on the same 30-query
dataset and writes five JSON artifacts under `reports/evaluation/`. Use
`--allow-download` only for the first model acquisition.

At `k=3`, hybrid retrieval achieved Recall 0.925926, MRR 0.783951, and nDCG 0.820543.
The expanded-corpus BM25 control achieved Recall 0.925926, MRR 0.771605, and nDCG 0.811723;
dense achieved Recall 0.814815, MRR 0.685185, and nDCG 0.718251. Hybrid therefore improves
ordering over BM25 without improving its Recall, while adding 9.316400 ms of mean query
latency in this run.

Correct abstention is 0.666667 for all arms because metadata filters exclude two
out-of-library questions, while one in-library but unsupported question still retrieves PyMC
chunks. See the Phase 4 report for category slices, per-query failures, hashes, and limitations.

## Reproduce the Phase 4 reranking experiment

```bash
uv run rag-pymc evaluate-reranked
```

The command writes a fresh RRF control, the reranked report, and their comparison. The
cross-encoder achieved Recall@3 0.888889, MRR 0.777778, and nDCG@3 0.806873, compared with
0.925926, 0.783951, and 0.820543 for the RRF control. Mean query latency increased from
9.661346 ms to 287.972640 ms.

The reranker recovered the documented Beta-Binomial example but lost two answers previously
inside the RRF top three. It is therefore not adopted. The report preserves all changes by
query and intent without post-hoc threshold tuning.

## Development commands

```bash
uv run ruff format .
uv run ruff check .
uv run mypy
uv run pytest
uv run pre-commit run --all-files
```

The non-mutating validation sequence is:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run rag-pymc doctor
```

## Current structure

```text
datasets/
|-- evaluation/{phase2,phase4}/     # Versioned questions and binary qrels
|-- fixtures/pymc/6.1.0/            # Controlled offline HTML snapshots
`-- raw/manifests/                  # Source, embedding, and reranker provenance
reports/evaluation/                  # Machine-readable experiment results
src/rag_pymc/
|-- domain/                          # Stable source and retrieval contracts
|-- embeddings/                      # Pinned dense embedding adapter
|-- ingestion/                       # Integrity checks and orchestration
|-- parsing/                         # Sphinx API parser
|-- chunking/                        # Structure-aware API chunker
|-- persistence/                     # Deterministic JSONL corpus adapter
|-- indexing/                        # Explicit BM25 and exact cosine indexes
|-- retrieval/                       # Sparse, dense, and RRF retrieval
|-- reranking/                       # Provider-neutral cross-encoder boundary
|-- evaluation/                      # Metrics, category slices, and comparisons
`-- cli.py                           # Reproducible local workflows
tests/
|-- unit/
`-- integration/
docs/
|-- adr/
|-- architecture/
`-- evaluation/
```

## Near-term roadmap

- **Phase 5:** construct bounded context, grounded answers with precise citations, and an
  explicit abstention policy behind provider-neutral interfaces.
- Create a development split before tuning rerankers or abstention thresholds.
- Evaluate truncation-aware parent-child chunking separately from rank fusion.

LLM generation, PostgreSQL, vector databases, code execution, web APIs, and user interfaces
remain outside the current scope.
