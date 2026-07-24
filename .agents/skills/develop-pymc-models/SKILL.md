---
name: develop-pymc-models
description: Design, implement, refactor, debug, and validate probabilistic programs in PyMC for this repository. Use for prior and likelihood design, hierarchical models, coords and dims, mutable data, PyTensor expressions, posterior sampling, convergence and geometry diagnostics, predictive checks, out-of-sample prediction, model comparison, or version-sensitive PyMC code. Route simulation-based calibration methodology to the dedicated SBC skill.
---

# Develop PyMC Models

Build statistically explicit, version-compatible PyMC programs and validate both their scientific assumptions and computational behavior.

## Establish the execution contract

1. Read `references/project-context.md` before changing repository code.
2. Confirm the actual versions from `pyproject.toml`, `uv.lock`, and the active `uv` environment. Treat the installed API and the repository's controlled snapshots as executable authority.
3. State the model's estimand, observations, latent variables, generative assumptions, and intended predictions before selecting distributions.
4. Separate three kinds of statements in explanations:
   - **Documented behavior**: supported by a cited local snapshot or official API page.
   - **Statistical interpretation**: derived from the model and identified as interpretation.
   - **Practical recommendation**: a context-dependent engineering or modeling choice.
5. Surface missing domain information instead of silently supplying scientifically consequential assumptions.

The project is pinned to PyMC 6.1.0, ArviZ 1.2.0, and PyTensor 3.1.3. Do not copy newer `stable` APIs into repository code without runtime verification. In particular, do not use the experimental `pm.dims` module: it is absent from the pinned PyMC runtime. Use `coords=`, `dims=`, and ordinary PyMC distributions.

## Choose the workflow

- For a new or substantially revised model, follow `references/modeling-workflow.md` end to end.
- For API details involving sampling, data mutation, or prediction, read `references/pymc-api-6.1.0.md`.
- For shapes, named dimensions, custom likelihoods, or symbolic expressions, read `references/pytensor-and-dimensions.md`.
- For divergences, poor mixing, uncertainty in Monte Carlo estimates, predictive checks, or model comparison, read `references/diagnostics-and-criticism.md`.
- For the official documentation consulted and its observed version boundary, read `references/official-sources.md`.
- For repository tests, provenance, quality gates, and response requirements, read `references/project-context.md`.
- For prior SBC, posterior SBC, rank/PIT/ECDF calibration, ties, or autocorrelation, invoke `$simulation-based-calibration`. Use both skills when implementing an SBC experiment in PyMC.

## Implement the model

1. Encode the generative process directly. Preserve parameter support and units.
2. Justify priors in the observation scale or another interpretable scale. Test their implications with prior predictive simulation.
3. Use named `coords` and `dims` for nontrivial arrays. Distinguish support dimensions from batch dimensions.
4. Register predictors or replaceable observations with `pm.Data` when prediction requires data updates. Keep the number of dimensions fixed across `pm.set_data` calls.
5. Use `pm.math` or `pytensor.tensor` operations inside symbolic graphs. Do not force symbolic variables through ordinary NumPy functions or Python control flow.
6. Prefer explicit random seeds and independent chains. Preserve the default structured posterior container unless a concrete consumer requires another format.
7. Keep statistical construction separate from expensive inference when doing so improves testing and reuse.
8. Write all code, identifiers, docstrings, comments, and repository artifacts in English. The user-facing explanation may be in Spanish.

## Validate in layers

Run the cheapest checks first and escalate in proportion to risk:

1. Inspect named variables, shapes, coordinates, support, and initial log probability.
2. Draw a small prior predictive sample and verify groups, dimensions, finite values, and plausible scale.
3. Run a small deterministic smoke sample only when it adds evidence; do not interpret it substantively.
4. Run production inference with multiple independent chains and enough draws for the required Monte Carlo precision.
5. Inspect rank-normalized split R-hat, bulk and tail ESS, MCSE, divergences, tree-depth behavior, energy behavior, and trace/rank plots as appropriate.
6. Perform posterior predictive criticism using discrepancies tied to the scientific question. Use `predictions=True` for out-of-sample predictions after updating data.
7. If comparing models, compute pointwise log likelihood and use predictive criteria such as LOO only when the models and observations are comparable.
8. Add focused tests for model construction, dimensions, data replacement, finite log probability, and returned predictive groups. Avoid treating a tiny MCMC test as evidence of model validity.

## Diagnose before tuning

- Treat divergences as evidence that the sampler did not faithfully explore some posterior geometry. Locate the affected parameters and consider reparameterization or a better model before merely increasing `target_accept`.
- Treat R-hat, ESS, and MCSE as complementary diagnostics, not a proof of convergence or model correctness.
- Do not repair weak identification by adding samples alone. Revisit parameterization, prior information, likelihood, and data informativeness.
- Do not interpret successful computation as scientific validation. Sampling diagnostics, predictive adequacy, calibration, and sensitivity answer different questions.
- Record unresolved warnings and limitations in the result.

## Verify the change

Use the repository's `uv` workflow. Run targeted checks first, then the relevant project gates described in `references/project-context.md`. If an API is uncertain, inspect it in the pinned environment before consulting mutable online documentation. Cite the exact source and observed version for version-sensitive claims.

Finish with a concise report covering the model assumptions, implementation choices, diagnostic evidence, tests run, version constraints, and remaining uncertainty.
