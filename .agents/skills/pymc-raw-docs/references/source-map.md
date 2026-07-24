# Raw PyMC Source Map

This map describes the current contents of `datasets/raw/source`. Treat the directory as mutable because it is ignored by Git and has no complete-tree acquisition manifest.

## Entry points

- `index.md`: top-level MyST/Sphinx navigation.
- `learn.md`: routes beginner, intermediate, and advanced learning material.
- `learn/core_notebooks/index.md`: lists the bundled core notebooks.
- `api.rst`: routes the API index by topic.
- `contributing/index.md`: routes contributor documentation.
- `conf.py`: Sphinx configuration; useful for interpreting documentation mechanics, not PyMC API behavior.

## Conceptual and learning sources

- `learn/core_notebooks/pymc_overview.ipynb`: model construction, sampling, and result containers.
- `learn/core_notebooks/dimensionality.ipynb`: support, batch, shape, coordinate, and dimension concepts.
- `learn/core_notebooks/dims_module.ipynb`: experimental dims-oriented examples; verify availability in the pinned runtime.
- `learn/core_notebooks/model_comparison.ipynb`: predictive model comparison examples.
- `learn/core_notebooks/posterior_predictive.ipynb`: prior/posterior predictive and out-of-sample workflows.
- `learn/core_notebooks/pymc_pytensor.ipynb`: symbolic PyTensor graphs and PyMC integration.
- `learn/core_notebooks/GLM_linear.ipynb`: linear-model walkthrough.
- `learn/core_notebooks/Gaussian_Processes.rst` and `guides/Gaussian_Processes.rst`: overlapping GP narratives; compare and deduplicate before ingestion.
- `guides/Probability_Distributions.rst`: distribution construction, standalone distributions, transforms, and custom distributions.
- `learn/usage_overview.rst`: short usage overview.
- `glossary.md`: terminology, not an exhaustive behavioral specification.

`installation.md`, `learn/books.md`, `learn/videos_and_podcasts.md`, and `learn/consulting.md` are usually weak retrieval sources for a technical tutor.

## API indexes

The `api/` tree contains topic-level RST pages for sampling, data, models, distributions, Gaussian processes, variational inference, SMC, math, log probability, statistics, backends, ODEs, testing, and utilities. These files primarily contain `currentmodule` and `autosummary` directives. They can identify the expected module and symbol spelling, but generated pages under `api/generated/` are absent from this raw tree.

Useful routing examples:

- `api/samplers.rst`: `sample`, predictive samplers, `draw`, NUTS initialization, JAX samplers, and step methods.
- `api/data.rst`: `Data`, `get_data`, and `Minibatch` inventory.
- `api/model/core.rst`: `Model`, context lookup, deterministics, potentials, `set_data`, points, and compilation inventory.
- `api/distributions/*.rst`: distribution families and transforms.
- `api/dims/*.rst`: experimental dims namespace; do not infer pinned-runtime support.

## Contributor sources

Use `contributing/` for questions about developing PyMC itself, building its docs, authoring notebooks, implementing distributions, tests, releases, reviews, and style. Do not include these pages in an end-user modeling corpus by default.

## Version and provenance warning

The tree does not contain an acquisition manifest tying every file to one PyMC release or commit. Stored notebook outputs mention heterogeneous versions, including PyMC 5.15, 5.25 development builds, 5.27 development builds, and 5.28 development builds. Older contributor examples mention PyMC 5.1. These values date individual executions or examples; they do not establish the version of the full source tree.

For exact PyMC 6.1.0 claims, prefer the hash-verified HTML fixtures and manifests under `datasets/fixtures/pymc/6.1.0` and `datasets/raw/manifests/pymc/6.1.0`, then verify behavior in the pinned runtime when code depends on it.
