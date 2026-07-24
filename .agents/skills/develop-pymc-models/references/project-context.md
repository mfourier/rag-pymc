# Project Context and Evidence Policy

Read this file before modifying probabilistic code in this repository.

## Pinned environment

The repository currently pins:

- Python `>=3.12`
- PyMC `==6.1.0`
- ArviZ `==1.2.0`
- PyTensor `==3.1.3`

Use `uv`; do not introduce `requirements.txt` or an alternative environment workflow. Confirm versions rather than assuming that the lockfile, interpreter, and imported runtime agree:

```bash
uv run python -c "import arviz, pymc, pytensor; print(pymc.__version__, arviz.__version__, pytensor.__version__)"
uv run rag-pymc doctor
```

Do not change dependency versions unless the user requests an upgrade. A version upgrade is a separate migration task that requires API review, tests, and regenerated provenance where applicable.

## Source hierarchy

Use this order for version-sensitive assertions and executable code:

1. The active pinned runtime, inspected with `inspect.signature`, `help`, a minimal compilation, or a minimal execution.
2. Controlled PyMC 6.1.0 snapshots and manifests under:
   - `datasets/fixtures/pymc/6.1.0/`
   - `datasets/raw/manifests/pymc/6.1.0/`
   - processed Phase 4 corpus and evaluation records under `datasets/processed/phase4/` and `datasets/evaluation/phase4/`
3. Official versioned documentation that explicitly matches the installed release.
4. Official mutable `stable` documentation for concepts, after recording the version displayed by the page.

Never infer compatibility from a `stable` URL alone. The repository's provenance policy exists because mutable documentation can change without changing its URL. Keep release, source URL, retrieval metadata, and content hash together when adding controlled evidence.

The local controlled corpus currently covers these PyMC 6.1.0 APIs:

- `pymc.sample`
- `pymc.Data`
- `pymc.set_data`
- `pymc.sample_posterior_predictive`

For uncovered APIs, inspect the runtime and cite official documentation. Do not present local retrieval as support for ArviZ or PyTensor claims when those libraries are not in the local corpus.

## Architectural boundaries

Preserve the repository's architecture:

- Keep domain objects and policies independent of provider SDKs and orchestration frameworks.
- Keep retrieval deterministic, version-aware, and provenance-preserving.
- Fail closed when evidence is insufficient; do not fabricate an answer or silently broaden to another library version.
- Do not mix PyMC, ArviZ, and PyTensor evidence in a single context unless a compatibility policy explicitly permits it.
- Preserve immutable contracts and strict boundary validation where the surrounding code uses them.

Read the relevant architecture records before changing retrieval or evidence behavior:

- `docs/architecture/overview.md`
- `docs/adr/0001-keep-the-core-independent-from-langchain.md`
- `docs/adr/0002-version-source-snapshots-and-content-addressed-artifacts.md`
- `docs/adr/0008-define-deterministic-context-construction.md`
- `docs/adr/0009-fail-closed-with-a-conservative-no-threshold-evidence-policy.md`

## Writing and response contract

- Write code, identifiers, comments, docstrings, tests, prompts, skill files, reports, and project documentation in English.
- Explain decisions to the user in Spanish when that matches the conversation.
- Label unsupported domain choices as assumptions and explain their consequences.
- Distinguish documented facts, model-derived interpretations, and practical recommendations.
- Preserve user changes in a dirty worktree. Do not stage, commit, or push unless explicitly requested.
- Do not trigger uncontrolled network downloads during tests.

## Quality gates

Use targeted checks during iteration. Before handoff, run the relevant subset of the repository gates:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv run rag-pymc doctor
```

The project treats warnings as errors in pytest. Keep tests deterministic and small. For model code, prefer tests that establish:

- expected free, observed, deterministic, and data variables;
- named dimensions, coordinates, and event/batch shapes;
- finite initial log probability for valid fixtures;
- prior predictive and posterior predictive group names and dimensions;
- `pm.set_data` behavior for changed observation count;
- explicit failure for invalid shapes, categories, supports, or missing values.

Do not use short-chain MCMC thresholds as brittle unit tests. A sampling smoke test may establish that a path executes, but it does not establish convergence, calibration, or scientific adequacy.
