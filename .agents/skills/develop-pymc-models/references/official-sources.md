# Official Source Ledger

This ledger records the official documentation used to create the skill. Re-check mutable pages when making version-sensitive claims.

## Version warning

On 2026-07-23, official pages under the same PyMC `stable` documentation tree did not present a uniform release boundary: the Learn landing page displayed PyMC 6.1.0 while several linked notebook and API pages displayed PyMC 6.2.0. Some executed notebook watermarks also reflected an older runtime than the rendered documentation. This is direct evidence that a `stable` URL is not an immutable compatibility identifier.

Use the installed PyMC 6.1.0 runtime and the repository's controlled 6.1.0 snapshots for executable claims. Use the sources below for concepts or after verifying an API locally.

## PyMC sources

- [Learning PyMC](https://www.pymc.io/projects/docs/en/stable/learn.html): official learning index and documentation entry point.
- [Introductory overview](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_overview.html): model contexts, random variables, observations, sampling, and structured results.
- [Distribution dimensionality](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/dimensionality.html): support dimensions, batch dimensions, shapes, coordinates, and named dimensions.
- [PyMC and PyTensor](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_pytensor.html): symbolic graphs, compilation, evaluation, and model log-probability functions.
- [Posterior predictive sampling](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/posterior_predictive.html): prior predictive checks, posterior predictive checks, and prediction workflows.
- [Model comparison](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/model_comparison.html): pointwise log likelihood, LOO, ELPD, and uncertainty in predictive comparison.
- [`Model` and data APIs](https://www.pymc.io/projects/docs/en/stable/api/model/core.html): model context, coordinates, data registration, and data updates.
- [`sample_posterior_predictive`](https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample_posterior_predictive.html): posterior variable matching, predictive groups, and sampling controls.
- [Diagnosing biased inference with divergences](https://www.pymc.io/projects/examples/en/latest/diagnostics_and_criticism/Diagnosing_biased_Inference_with_Divergences.html): divergence localization, posterior geometry, and reparameterization.
- [API quickstart](https://www.pymc.io/projects/examples/en/latest/introductory/api_quickstart.html): compact model construction and inference examples.

## ArviZ sources

- [ArviZ 1.2.0 user guide](https://python.arviz.org/en/stable/user_guide/index.html): diagnostics, plots, data structures, and model comparison entry points.
- [ArviZ data schema](https://python.arviz.org/en/stable/schema/schema.html): posterior, sample-statistics, predictive, and log-likelihood groups; `chain` and `draw` conventions.
- [`arviz.summary`](https://python.arviz.org/en/stable/api/generated/arviz.summary.html): summary statistics and diagnostic outputs. Verify the installed 1.2.0 signature before selecting options because the live API can evolve.

## Evidence classification

When using these sources in an answer or code review, label claims as follows:

- **Official documented behavior**: directly supported by one of the pages, with the displayed version recorded.
- **Pinned-runtime behavior**: observed from PyMC 6.1.0, ArviZ 1.2.0, or PyTensor 3.1.3 in this repository.
- **Controlled local evidence**: supported by a snapshot and manifest under `datasets/`.
- **Statistical interpretation**: reasoned from an explicitly stated probabilistic model.
- **Practical recommendation**: a context-dependent choice that requires validation for the user's model and data.

If these sources disagree with the pinned runtime, report the mismatch and follow the pinned runtime for repository implementation. Do not silently combine APIs from different releases.
