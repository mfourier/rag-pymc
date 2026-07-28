# rag-pymc

`rag-pymc` is an evidence-grounded expert assistant foundation for Bayesian statistics and
PyMC. It targets engineers, data scientists, and researchers who need technically precise,
version-aware help with model design, implementation, diagnostics, and scientific communication.

The current MVP is deliberately narrow: it ingests controlled official PyMC API pages, retrieves
evidence with deterministic BM25, builds bounded context, evaluates evidence sufficiency, and
validates provider-neutral grounded-answer contracts. It does not yet call an LLM or generate an
answer.

## Product boundary

The assistant adapts retrieval and response structure to the technical task. It does not maintain
learner profiles, estimate mastery, sequence curricula, track progress, or optimize pedagogical
behavior. Those tutoring capabilities are permanent non-goals.

Official, versioned PyMC, ArviZ, and PyTensor sources are authoritative for library behavior. A
future scientific-literature layer will support statistical methods, diagnostics, and research
findings without being allowed to establish API compatibility. See the
[scientific literature policy](docs/corpus/scientific-literature-policy.md).

## Implemented capabilities

- hash-verified local ingestion of official PyMC 6.1.0 generated API pages;
- structure-aware Sphinx HTML parsing and deterministic chunking;
- content-addressed JSONL persistence with stable document and chunk identities;
- BM25 retrieval with library, version, source-type, and API-symbol filters;
- deterministic, whole-item context construction under an explicit technical-token budget;
- a fail-closed evidence policy that currently always abstains;
- immutable answer, claim, section, citation, generator-input, and generator-output contracts;
- structural response and citation-traceability evaluation;
- strict development-dataset, corpus-freeze, and gold-evidence evaluation contracts; and
- reproducible CLI workflows with offline tests.

The default controlled corpus contains four PyMC 6.1.0 API pages and 15 chunks covering
`pymc.sample`, `pymc.Data`, `pymc.model.core.set_data`, and
`pymc.sample_posterior_predictive`.

The repository also contains agent-facing specialist workflows under `.agents/skills/` for
developing and auditing PyMC models, priors, simulation validation, causal inference, imperfect
data, study design, deployment, and communication. They are curated expert instructions and small
analysis utilities; they are not extra retrieval strategies or dependencies of the Python runtime.

## Why BM25 is the selected policy

Dense retrieval, equal-weight Reciprocal Rank Fusion, and cross-encoder reranking were implemented
and measured before the MVP was simplified. Their reports remain versioned as historical research
artifacts.

On the 30-query Phase 4 dataset at `k=3`:

| Policy | Recall@3 | MRR | nDCG@3 | Mean latency |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.925926 | 0.771605 | 0.811723 | 0.079583 ms |
| Dense BGE | 0.814815 | 0.685185 | 0.718251 | 9.241087 ms |
| Hybrid RRF | 0.925926 | 0.783951 | 0.820543 | 9.395983 ms |
| Cross-encoder | 0.888889 | 0.777778 | 0.806873 | 287.972640 ms |

Hybrid retrieval did not improve BM25 recall and changed MRR by only `+0.012346`; the tested
cross-encoder reduced quality and added substantial CPU latency. BM25 therefore remains the sole
runtime policy for the MVP. This decision removed learned-model downloads, truncation behavior,
Torch and Transformers dependencies, and four parallel command families while preserving the
measured evidence in the [Phase 4 report](docs/evaluation/phase4-hybrid-baseline.md) and
[ADR-0014](docs/adr/0014-select-bm25-and-retire-learned-retrieval-from-the-mvp.md). The selected
path was rebuilt and remeasured after the cleanup; see the
[MVP BM25 revalidation](docs/evaluation/mvp-bm25-revalidation.md).

Learned retrieval may return only after a new corpus and held-out dataset demonstrate a
predeclared, material benefit.

## Requirements and installation

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) 0.11.30 or newer recommended
- Git for installing pre-commit hooks

```bash
uv sync --all-groups
uv run pre-commit install
uv run rag-pymc doctor
```

The compatibility baseline is pinned to PyMC 6.1.0, ArviZ 1.2.0, and PyTensor 3.1.3. Exact
transitive versions are recorded in `uv.lock`. The HDF5 backend remains explicit because the
agent-facing inference audit reads standard ArviZ NetCDF artifacts.

## Build the controlled corpus

All ingestion is offline. The checked-in fixtures are exact, hash-verified snapshots.

```bash
for symbol in \
  pymc.sample \
  pymc.Data \
  pymc.model.core.set_data \
  pymc.sample_posterior_predictive
do
  uv run rag-pymc ingest \
    --manifest "datasets/raw/manifests/pymc/6.1.0/$symbol.json" \
    --source "datasets/fixtures/pymc/6.1.0/$symbol.html" \
    --output-dir datasets/processed/phase4
done
```

A successful build writes four documents and 15 deterministic chunks. Repeating the commands
upserts the same records.

## Search and inspect context

```bash
uv run rag-pymc search \
  "How do I update predictors for posterior prediction?" \
  --corpus-dir datasets/processed/phase4 \
  --library pymc \
  --library-version 6.1.0 \
  --top-k 3

uv run rag-pymc inspect-context \
  "How do I update predictors for posterior prediction?" \
  --corpus-dir datasets/processed/phase4 \
  --token-budget 2048
```

`inspect-context` writes only the indented `ConstructedContext` JSON to standard output. Its
`technical-v1` budget is deterministic but is not an LLM tokenizer. An empty context is valid and
does not imply that the question itself is invalid.

## Reproduce the selected retrieval baseline

```bash
uv run rag-pymc evaluate \
  --dataset datasets/evaluation/phase4/pymc_core_queries.jsonl \
  --corpus-dir datasets/processed/phase4 \
  --output /tmp/rag-pymc-bm25-evaluation.json \
  --top-k 3 \
  --seed 20260720 \
  --k1 1.5 \
  --b 0.75
```

The stored baseline is [phase4-bm25-expanded.json](reports/evaluation/phase4-bm25-expanded.json).
Latency is machine-specific; ranking and non-latency metrics are reproducible from the frozen
inputs.

## Internal research-data commands

Annotation preparation is intentionally separated from the product CLI:

```bash
uv run rag-pymc-research validate-development-data --help
uv run rag-pymc-research freeze-annotation-corpus --help
uv run rag-pymc-research export-development-review --help
```

The prepared 24-example packet remains an agent-authored draft awaiting one genuine human review.
These commands do not generate answers or fabricate human annotation.

## Development checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run rag-pymc doctor
```

Pre-commit runs the same non-mutating validation sequence. Tests enforce branch coverage at or
above the measured 84% project floor. CI executes the checks on Python 3.12 and 3.13 from locked,
clean environments and builds the distribution artifacts.

## Repository layout

```text
src/rag_pymc/
├── abstention/        # Evidence-sufficiency policy boundary
├── application/       # Retrieval-to-context use cases
├── chunking/          # Official API chunking
├── context/           # Deterministic context construction
├── domain/            # Evidence and grounded-answer contracts
├── evaluation/        # Retrieval, evidence, and response evaluation
├── indexing/          # Explicit BM25 index
├── ingestion/         # Integrity checks and orchestration
├── parsing/           # Official Sphinx API parser
├── persistence/       # Deterministic JSONL corpus
├── retrieval/         # Selected sparse retriever
├── cli.py             # Product CLI
└── research_cli.py    # Internal annotation-data CLI
```

Agent expertise lives outside the installable runtime in `.agents/skills/`; immutable research
inputs and outputs live under `datasets/` and `reports/`.

Historical dense, hybrid, reranking, repository-code, and notebook experiments remain documented
under `docs/adr/`, `docs/evaluation/`, and `reports/evaluation/`. They are evidence for decisions,
not active runtime capabilities. ADR-0015 records the decision to retain only the official API
ingestion path.

## Near-term roadmap

1. Complete one real human review of the prepared Phase 5 development packet and freeze the
   resulting single-review dataset.
2. Record the conservative-policy baseline before selecting any answer-permitting rule.
3. Add prompt-safe serialization, one project-owned generator protocol, one deterministic fake,
   and one end-to-end `ask` use case.
4. Evaluate semantic claim support, citation correctness, completeness, and technical usefulness
   before selecting an LLM provider.
5. Add a small, curated and versioned scientific-paper slice under the adoption gate in the
   literature policy.
6. Expand official PyMC API coverage through the existing parser instead of adding source formats.

PostgreSQL, vector databases, arbitrary code execution, web APIs, user interfaces, learner state,
and additional retrieval strategies remain outside the MVP.
