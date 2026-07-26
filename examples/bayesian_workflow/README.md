# Bayesian Linear Regression Workflow Example

This directory contains the repository's single educational Bayesian workflow notebook:
`bayesian_workflow_linear_regression.ipynb`. It is independent of the RAG, evaluation, and CLI
layers.

## Statistical contract

- Observation: one fixed reference input and continuous response pair `(x_i, y_i)`.
- Population: comparable conditionally independent measurements over the declared input range,
  assuming a linear mean, constant residual scale, and Gaussian errors.
- Primary estimand: `slope`, the expected response change for a one-unit input increase.
- Secondary estimands: `intercept` at centered `x = 0` and residual standard deviation `sigma`.
- Predictive target: a future response at a fixed input inside the observed range.
- Constructed data: `n = 16`, seed `20260726`, `intercept_true = 1`, `slope_true = 2`,
  `sigma_true = 0.75`, and `x` evenly spaced from `-1.5` to `1.5`.
- Priors: `intercept ~ Normal(0.5, 2.5)`, `slope ~ Normal(1.5, 2)`, and
  `sigma ~ HalfNormal(1)`.
- Likelihood: `y_i | x_i, intercept, slope, sigma ~ Normal(intercept + slope*x_i, sigma)`.

The predictor is fixed and treated as exact. The observations come from the fitted model family,
so recovery demonstrates synthetic self-consistency—not causality, extrapolation, measurement
validity, or adequacy for real data.

## Bayesian workflow projection

The notebook maps its sections directly to the iterative
[`Graphical_Bayesian_Workflow.md`](../../.local-learning/Graphical_Bayesian_Workflow.md):

```text
question and estimands
  -> deterministic fake-data simulation
  -> pick an initial model
  -> prior predictive check
       -> implausible: modify model or priors and repeat
       -> provisionally acceptable: fit with NUTS
  -> validate computation
       -> invalid: address computational issues and refit
       -> provisionally acceptable: evaluate and use the model
  -> posterior predictive check
  -> human scientific review
       -> material problem: return to model or computation
       -> question unsupported: stop or narrow
       -> adequate for this demonstration: persist and report
```

The plots preserve distinct inferential roles:

- fixed-data likelihood over `(intercept, slope, sigma)`;
- joint prior draws and prior-predictive regression implications;
- trace, rank, marginal prior/posterior, and joint posterior geometry views;
- side-by-side joint prior, likelihood, and posterior views of Bayes' rule;
- posterior uncertainty for the conditional mean and wider predictive uncertainty for replicated
  responses.

These plots support inspection; none is an automatic validity gate. Formal SBC, cross-validation,
influence and sensitivity analyses, model comparison, measurement-error models, and extrapolation
are intentionally outside this demonstration.

## Install and run

From the repository root:

```bash
uv sync --extra notebooks
uv run rag-pymc doctor
uv run --extra notebooks jupyter lab examples/bayesian_workflow
```

Clean-execute to a temporary directory so the versioned source remains output-free:

```bash
execution_dir="$(mktemp -d)"
uv run --extra notebooks jupyter nbconvert \
  --to notebook \
  --execute examples/bayesian_workflow/bayesian_workflow_linear_regression.ipynb \
  --ExecutePreprocessor.timeout=600 \
  --output bayesian_workflow_linear_regression.executed.ipynb \
  --output-dir "$execution_dir"
```

For pedagogy, the notebook constructs the PyMC model and calls `pm.sample_prior_predictive`,
`pm.sample`, and `pm.sample_posterior_predictive` directly. Data, priors, seeds, diagnostics, and
persistence are also visible in ordinary cells; no separate configuration file is required.

## Artifacts and verification

The notebook writes ignored artifacts to:

```text
examples/bayesian_workflow/outputs/linear-regression-final/
├── posterior.nc
└── summary.json
```

`posterior.nc` is the sampled `xarray.DataTree`. The notebook reopens it with
`xarray.open_datatree` using `h5netcdf` and compares posterior and posterior-predictive arrays.
`summary.json` records settings, diagnostics, posterior summaries, review status, and limitations.

Focused checks:

```bash
uv run ruff format --check \
  examples/bayesian_workflow/bayesian_workflow_linear_regression.ipynb \
  tests/unit/test_bayesian_linear_regression.py
uv run ruff check \
  examples/bayesian_workflow/bayesian_workflow_linear_regression.ipynb \
  tests/unit/test_bayesian_linear_regression.py
uv run pytest tests/unit/test_bayesian_linear_regression.py
uv run rag-pymc doctor
```

Short unit-test chains verify code paths and shapes, not convergence. Numerical review belongs to
the full notebook run.

## Observed run: 2026-07-26

The exact versioned source executed all 15 code cells without cell errors under Python 3.13.5,
PyMC 6.1.0, ArviZ 1.2.0, PyTensor 3.1.3, and xarray 2026.2.0. The source was then verified to have
zero outputs and null execution counts. Jupyter emitted a transport warning about an unencrypted
local TCP kernel connection; this did not arise from a notebook cell or the statistical model.

The fixed data had response mean `0.8648` and standard deviation `1.9101`. The Gaussian MLE was
`(intercept, slope, sigma) = (0.8648, 1.8753, 0.6569)`. The independent OLS check gave intercept
`0.8648`, slope `1.8753`, and residual standard deviation `0.7022`; its scale uses
`sqrt(RSS/(n - 2))`, whereas the likelihood MLE uses `sqrt(RSS/n)`.

Posterior means and equal-tail 94% intervals were:

| Parameter | Mean | 94% interval | MCSE(mean) |
|---|---:|---:|---:|
| intercept | 0.8606 | [0.4998, 1.2104] | 0.00314 |
| slope | 1.8701 | [1.4700, 2.2620] | 0.00358 |
| sigma | 0.7489 | [0.5228, 1.0813] | 0.00264 |

All three synthetic generating values lay inside these intervals in this one dataset. This is a
recovery observation, not a calibration guarantee.

The largest rank-normalized split R-hat was `1.00170`. Bulk ESS ranged from `3354.10` to `3684.53`,
tail ESS from `2567.87` to `3032.44`, and posterior-mean MCSE from `0.00264` to `0.00358`. The run
recorded zero divergences, maximum tree depth `3`, and per-chain BFMI from `1.042` to `1.209`.
Trace and rank plots showed no visible chain-specific instability. These observations support the
reported numerical precision; they do not prove convergence or scientific adequacy.

The posterior predictive figure is an in-sample visual check at the fixed inputs. It distinguishes
the interval for the latent mean from the wider interval for replicated responses, but it does not
test residual tails, heteroscedasticity, dependence, or out-of-sample prediction. The persisted
DataTree reopened with posterior, sample-statistics, observed-data, and posterior-predictive groups,
and the checked arrays matched the in-memory result.

The human review status is **adequate for this demonstration**. It is conditional on the synthetic
design and inspected evidence, and does not authorize causal language or real-world deployment.
