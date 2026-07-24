# PyMC source selection and ingestion

## Purpose

Use the PyMC repository as a second evidence layer for implementation questions. Keep it
separate from documentation because source code explains what a pinned release implements,
while public documentation explains supported use and stated behavior.

The available clone is `/home/mlioi/pymc`. Its active checkout is `v6.2.0`; never copy the
working tree into the PyMC 6.1.0 corpus. The immutable `v6.1.0` tag resolves locally to commit
`56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`.

## Evidence layers

| Layer | Best use | Initial selection | Retrieval policy |
| --- | --- | --- | --- |
| Generated API HTML | Signatures, parameters, returns, notes, examples, documented guarantees | Existing four Phase 4 pages | Prefer for public API and usage questions |
| Conceptual notebooks and guides | Modeling workflow, dimensionality, PyTensor concepts, predictive checks, model comparison | Three controlled notebooks in the first conceptual slice | Prefer for conceptual and pedagogical questions |
| Repository implementation | Dispatch, validation, graph mutation, internal data flow, warnings | Four exact source files in this experiment | Prefer for implementation and debugging questions |
| Upstream tests | Asserted edge cases and regression behavior | Deferred | Use as corroborating evidence, never as a public guarantee |
| Release metadata | Compatibility and migration boundaries | Tag, commit, release notes, dependency metadata | Use for version-sensitive routing |

## Current controlled implementation slice

The repository now stores exact files under
`datasets/fixtures/pymc/6.1.0/repository/` and manifests under
`datasets/raw/manifests/pymc/6.1.0/repository/`:

| Public symbol | Upstream file | Why it is useful |
| --- | --- | --- |
| `pymc.sample` | `pymc/sampling/mcmc.py` | Sampler selection, NUTS initialization, chain execution, return conversion, and warnings |
| `pymc.Data` | `pymc/data.py` | Model-context registration, input conversion, dimensions, coordinates, and shared-variable creation |
| `pymc.model.core.set_data` | `pymc/model/core.py` | Mapping-level delegation to per-variable model mutation |
| `pymc.sample_posterior_predictive` | `pymc/sampling/forward.py` | Trace normalization, volatile-variable selection, forward-function compilation, predictive loops, and result groups |

The parser selects only the named implementation. It does not index imports, unrelated symbols,
or full-file text. Long API docstrings are represented by one summary sentence because their
detailed content already exists in the API-reference layer.

The exact upstream Python fixtures are excluded from project Ruff checks. Formatting or fixing
them locally would invalidate their manifest hashes and break byte-for-byte provenance. The
project parser, chunker, script, and tests remain subject to the normal quality gates.

## Current controlled notebook slice

Three exact notebooks are stored under `datasets/fixtures/pymc/6.1.0/notebooks/`, with manifests
under `datasets/raw/manifests/pymc/6.1.0/notebooks/`:

| Notebook | Primary coverage | Raw size |
| --- | --- | ---: |
| `dimensionality.ipynb` | Support, batch, implicit and explicit dimensions; shape debugging | ~60 KB |
| `pymc_pytensor.ipynb` | Symbolic graphs, compilation, graph structure, log probability, value variables | ~112 KB |
| `model_comparison.ipynb` | Pointwise log likelihood, PSIS-LOO, ELPD, model comparison | ~580 KB |

The parser preserves Markdown and code inputs, heading hierarchy, source cell numbers, and PyMC
symbol references. It excludes outputs, execution counts, kernel metadata, all other notebook
metadata, and raw cells. The raw fixture remains unchanged and hash-verified.

This slice produces three documents and 34 chunks. The largest chunk is 3,060 characters because
the chunker does not split an individual authored cell. Exact notebook fixtures are excluded
from Ruff so formatting cannot invalidate their hashes.

## Recommended next documentation sources

Add these sources incrementally after measuring the current slice:

1. `docs/source/learn/core_notebooks/pymc_overview.ipynb`
2. `docs/source/learn/core_notebooks/posterior_predictive.ipynb`
3. `docs/source/learn/core_notebooks/GLM_linear.ipynb`
4. `docs/source/guides/Probability_Distributions.rst`
5. `docs/source/contributing/implementing_distribution.md`
6. `docs/source/contributing/versioning_schemes_explanation.md`

For notebooks, remove stored outputs and execution metadata from retrieval content while
preserving markdown/code-cell order and cell identity. Record the raw notebook hash before
normalization. For RST, resolve headings, directives, autosummary entries, code blocks, notes,
and warnings without treating directive syntax as prose.

The deferred overview, posterior-predictive, and GLM notebooks contain approximately 6.7 MB of
raw data, dominated by stored outputs. Keep exact raw bytes or move them to a content-addressed
artifact store; do not commit output-stripped derivatives as though they were upstream files.

Do not treat `docs/source/api/*.rst` autosummary indexes as replacements for generated API
pages. They are useful for symbol discovery, but generated HTML contains the resolved
signatures and field sections already used by the current parser.

## Exclusions for the next slice

Do not ingest these indiscriminately:

- logos, images, build assets, caches, and generated documentation output;
- every distribution implementation before queries require it;
- the full upstream test suite;
- benchmarks and CI configuration;
- contributor logistics unrelated to PyMC programming;
- files from the active 6.2.0 checkout in a 6.1.0 corpus.

## Reproduce acquisition

The snapshot script reads Git objects directly and refuses a tag resolving to an unexpected
commit:

```bash
uv run python scripts/snapshot_pymc_repository.py \
  --repository /home/mlioi/pymc \
  --project-root /home/mlioi/rag-pymc
```

Re-running it preserves the original acquisition timestamp in existing manifests and rewrites
identical fixture bytes.

## Build the notebook corpus

```bash
uv run rag-pymc ingest-notebook \
  --manifest datasets/raw/manifests/pymc/6.1.0/notebooks/dimensionality.json \
  --source datasets/fixtures/pymc/6.1.0/notebooks/docs/source/learn/core_notebooks/dimensionality.ipynb \
  --output-dir datasets/processed/notebooks

uv run rag-pymc ingest-notebook \
  --manifest datasets/raw/manifests/pymc/6.1.0/notebooks/pymc_pytensor.json \
  --source datasets/fixtures/pymc/6.1.0/notebooks/docs/source/learn/core_notebooks/pymc_pytensor.ipynb \
  --output-dir datasets/processed/notebooks

uv run rag-pymc ingest-notebook \
  --manifest datasets/raw/manifests/pymc/6.1.0/notebooks/model_comparison.json \
  --source datasets/fixtures/pymc/6.1.0/notebooks/docs/source/learn/core_notebooks/model_comparison.ipynb \
  --output-dir datasets/processed/notebooks
```

Evaluate it independently:

```bash
uv run rag-pymc evaluate \
  --dataset datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl \
  --corpus-dir datasets/processed/notebooks \
  --output reports/evaluation/notebook-bm25-development.json \
  --experiment-id notebook-bm25-development \
  --seed 20260724 \
  --top-k 3
```

## Build the implementation corpus

```bash
uv run rag-pymc ingest-code \
  --manifest datasets/raw/manifests/pymc/6.1.0/repository/pymc.sample.json \
  --source datasets/fixtures/pymc/6.1.0/repository/pymc/sampling/mcmc.py \
  --output-dir datasets/processed/repository-code

uv run rag-pymc ingest-code \
  --manifest datasets/raw/manifests/pymc/6.1.0/repository/pymc.Data.json \
  --source datasets/fixtures/pymc/6.1.0/repository/pymc/data.py \
  --output-dir datasets/processed/repository-code

uv run rag-pymc ingest-code \
  --manifest datasets/raw/manifests/pymc/6.1.0/repository/pymc.model.core.set_data.json \
  --source datasets/fixtures/pymc/6.1.0/repository/pymc/model/core.py \
  --output-dir datasets/processed/repository-code

uv run rag-pymc ingest-code \
  --manifest datasets/raw/manifests/pymc/6.1.0/repository/pymc.sample_posterior_predictive.json \
  --source datasets/fixtures/pymc/6.1.0/repository/pymc/sampling/forward.py \
  --output-dir datasets/processed/repository-code
```

The result is four normalized documents and 19 deterministic chunks. Processed output remains
ignored by Git and is reproducible from the checked-in fixtures and manifests.

Evaluate the narrow implementation-query baseline independently:

```bash
uv run rag-pymc evaluate \
  --dataset datasets/evaluation/repository-code/pymc_implementation_queries.jsonl \
  --corpus-dir datasets/processed/repository-code \
  --output reports/evaluation/repository-code-bm25-baseline.json \
  --experiment-id repository-code-bm25-baseline \
  --seed 20260723 \
  --top-k 3 \
  --limitation "The corpus covers four PyMC 6.1.0 public implementations only." \
  --limitation "The eight-query dataset is a development set, not a held-out evaluation." \
  --limitation "One query tests abstention through an out-of-corpus library filter." \
  --limitation "No mixed-corpus documentation regression is measured by this report."
```

## Query the code layer

Filter explicitly when implementation evidence is required:

```bash
uv run rag-pymc search \
  "Where does sample initialize NUTS?" \
  --corpus-dir datasets/processed/repository-code \
  --library pymc \
  --library-version 6.1.0 \
  --source-type repository_code \
  --api-symbol pymc.sample \
  --top-k 3
```

Do not infer a recommendation from an implementation branch. Use API or conceptual
documentation for recommendations, use source code for pinned behavior, and label any
statistical interpretation separately.

## Adoption gate

Before merging these experimental layers into default context construction:

1. Evaluate implementation-specific queries against the repository-code corpus.
2. Build a separate mixed corpus containing the frozen API documents and repository code.
3. Re-run all Phase 4 documentation queries unchanged.
4. Compare recall, MRR, nDCG, retrieved tokens, dense truncation, and latency by intent.
5. Add intent-aware source routing if code displaces documentation on public-API queries.
6. Require semantic insufficiency handling for unsupported conceptual queries.
7. Adopt the mixed corpus only if implementation and conceptual coverage improve without a
   material documentation regression.
