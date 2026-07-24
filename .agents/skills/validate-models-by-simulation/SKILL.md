---
name: validate-models-by-simulation
description: Design, implement, interpret, and report simulation studies for Bayesian model validation beyond formal simulation-based calibration. Use for parameter or estimand recovery, identifiability probes, design recovery, robustness and misspecification experiments, observation-process stress tests, scenario-based operating characteristics, or debugging a generative model and inference implementation. Route formal prior/posterior SBC ranks, PIT/ECDF uniformity, ties, and MCMC thinning to the dedicated simulation-based-calibration skill.
---

# Validate Models by Simulation

## Purpose

Use controlled generative experiments to determine what a Bayesian analysis can recover, under which conditions, and how it fails. Simulation evidence is conditional on the scenarios and implementation used; it is not universal proof of model validity.

## Choose the Validation Target

State which layer is under test:

- **implementation:** does code recover quantities under the exact fitted model?
- **identifiability:** which parameters or estimands can the design and likelihood learn?
- **design:** do sample size, grouping, timing, or measurement choices support the target?
- **robustness:** how do results change across plausible parameter regimes?
- **misspecification:** what happens when generated data violate fitted assumptions?
- **decision:** how often does the procedure choose a useful action and at what cost?

Use [simulation-study-design.md](references/simulation-study-design.md) to define the experiment before running it.

## Workflow

1. **Define the claim.** Specify the target quantity, intended population, success criteria, and failure modes.
2. **Separate generator and fitter.** Version both. Make their equality or deliberate mismatch explicit.
3. **Construct scenarios.** Cover typical, boundary, weak-information, high-noise, rare-event, imbalanced, and scientifically plausible misspecified regimes.
4. **Predefine quantities.** Include scientific estimands, predictions, decisions, nuisance parameters relevant to geometry, and generated observables.
5. **Choose replication and Monte Carlo precision.** Determine how accurately bias, coverage, failure rates, or utility must be estimated. Increase replications based on the uncertainty of these simulation summaries.
6. **Run reproducibly.** Use deterministic seed derivation, unique simulation IDs, immutable scenario metadata, and separate generation from fitting failures.
7. **Validate each fit.** Record sampler warnings, R-hat, ESS, MCSE, divergences, tree depth, and exceptions. Do not let failed fits disappear from denominators.
8. **Summarize recovery.** Report bias, MAE, RMSE, empirical interval coverage, interval width, failure rate, and scenario heterogeneity using [metrics-and-interpretation.md](references/metrics-and-interpretation.md).
9. **Diagnose failure mechanisms.** Inspect sign errors, boundary bias, multimodality, prior dominance, confounding, weak identification, and observation-model mismatch.
10. **Act and repeat.** Modify design, model, prior, parameterization, or inferential claim; then rerun the same registered scenarios plus any new targeted cases.

## SBC Boundary

Formal SBC has a precise generative experiment and calibration target. Read [boundary-with-sbc.md](references/boundary-with-sbc.md) before using rank, PIT, or ECDF uniformity language. Invoke `$simulation-based-calibration` whenever that formal methodology is required.

## Recovery Summary Utility

[summarize_recovery.py](scripts/summarize_recovery.py) consumes a long-form CSV with columns:

```text
scenario,replicate,quantity,true,estimate,lower,upper,status
```

`status` is optional and defaults to success. The utility keeps failed fits in the report and computes scenario-by-quantity recovery metrics:

```bash
uv run python .agents/skills/validate-models-by-simulation/scripts/summarize_recovery.py \
  recovery.csv --output recovery-summary.json
```

## Guardrails

- Do not simulate only from the fitted posterior and call that parameter recovery.
- Do not use a single convenient parameter point to claim identifiability.
- Do not condition summaries on successful fits without also reporting the full failure rate.
- Do not interpret nominal interval coverage without Monte Carlo uncertainty and scenario context.
- Do not diagnose a failed generator by changing the fitter until both implementations have independent checks.
- Do not equate recovery under the exact model with robustness to real-world misspecification.
- Do not use the same random stream for conceptually independent experimental components without deliberate seed management.

## Routing

- Use `$develop-pymc-models` for PyMC generator/fitter implementation and diagnostics.
- Use `$simulation-based-calibration` for prior SBC, posterior SBC, ranks, PIT/ECDF, ties, and MCMC autocorrelation adjustments.
- Use `$model-imperfect-data` to design missingness, selection, measurement error, censoring, or misclassification scenarios.
- Use `$design-bayesian-studies` when the main goal is prospective sample-size, assurance, utility, or adaptive-design selection.

## Output Contract

Deliver a scenario registry, generator/fitter versions, seed protocol, quantities and success criteria, fit-level diagnostics, aggregate metrics with Monte Carlo uncertainty, failure analysis, scope of supported claims, and reproducible next actions. Use [simulation-study-plan.md](assets/simulation-study-plan.md) as the study record.
