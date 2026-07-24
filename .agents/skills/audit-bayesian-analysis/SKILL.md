---
name: audit-bayesian-analysis
description: Audit a Bayesian analysis end to end, from the estimand, data-generating assumptions, priors, likelihood, computation, predictive adequacy, validation, comparison, decisions, and reporting. Use when reviewing an existing analysis, model notebook, PyMC program, inference artifact, scientific report, or production handoff; when triaging suspicious Bayesian results; or when producing a prioritized audit report with evidence, severity, limitations, and routing to specialist skills.
---

# Audit Bayesian Analysis

## Purpose

Determine whether a Bayesian analysis is fit for its stated use and identify the highest-value corrective work. Treat an audit as an evidence inventory and risk assessment, not as a binary certification.

## Required Inputs

Gather as many of these artifacts as are available:

- question, estimand, decision, and intended population;
- data provenance, schema, exclusions, preprocessing, and missing-data handling;
- generative model, prior rationale, likelihood, and observation model;
- model code, package versions, sampler configuration, seeds, and logs;
- posterior, sample statistics, predictive draws, and comparison objects;
- validation results, sensitivity analyses, figures, tables, and claims.

Do not silently treat missing artifacts as evidence of correctness. Record them as audit limitations or findings. Use [artifact-contract.md](references/artifact-contract.md) for the minimum artifact contract.

## Audit Workflow

1. **Fix the target.** Restate the estimand, prediction target, decision, population, and loss or utility. Flag any mismatch between the stated question and modeled quantity.
2. **Trace the data.** Inspect provenance, sampling, exclusions, transformations, leakage, missingness, measurement error, censoring, selection, and time ordering.
3. **Read the model generatively.** Reconstruct how parameters generate latent states and observations. Check support, units, transformations, dependence, identifiability, and whether the likelihood represents the observation process.
4. **Assess priors in observable space.** Review domain rationale, joint implications, prior predictive behavior, weak identification, and sensitivity. Route deep prior work to `$elicit-and-stress-test-priors`.
5. **Assess computation.** Inspect chains, rank-normalized split R-hat, bulk and tail ESS, MCSE, divergences, tree depth, energy behavior, warnings, and repeated fits. Diagnose geometry before increasing draws. Route PyMC implementation work to `$develop-pymc-models`.
6. **Assess predictive adequacy.** Use prior and posterior predictive checks tied to scientific failure modes. Inspect calibration and residual structure at relevant groups, tails, and time horizons.
7. **Assess validation and robustness.** Look for simulation recovery, formal SBC where appropriate, sensitivity to priors and modeling choices, influential observations, and plausible misspecification. Route formal rank/PIT SBC to `$simulation-based-calibration` and broader simulation studies to `$validate-models-by-simulation`.
8. **Assess comparison and decisions.** Check that LOO/PSIS, ELPD, WAIC, stacking, or utilities match the intended predictive task and unit of generalization. Inspect Pareto-k diagnostics and uncertainty in differences.
9. **Audit communication.** Verify that posterior, predictive, Monte Carlo, and model uncertainty are not conflated; that conditioning assumptions are visible; and that claims do not exceed the design.
10. **Triage findings.** Assign severity, evidence, consequence, remediation, owner, and verification criterion using [audit-rubric.md](references/audit-rubric.md).

## Evidence Rules

- Never infer scientific validity from convergence diagnostics alone.
- Never infer convergence from one scalar threshold alone.
- Distinguish a missing check from a failed check.
- Separate observed evidence, technical interpretation, and recommendation.
- Label numerical thresholds as configurable operational heuristics unless a domain contract defines them.
- Prefer reproducible artifacts and exact code locations over general impressions.
- Preserve alternative explanations when evidence is ambiguous.

## Automated Inventory

Use [audit_inference_data.py](scripts/audit_inference_data.py) to inventory NetCDF diagnostics:

```bash
uv run --with h5netcdf --with h5py python \
  .agents/skills/audit-bayesian-analysis/scripts/audit_inference_data.py \
  path/to/inference.nc --output audit-diagnostics.json
```

`h5netcdf` and its `h5py` backend supply optional NetCDF group support without changing the project lock. The script reports available groups, chain and draw counts, per-variable summary metrics, sampler events, and transparent heuristic flags. It does not assess priors, model adequacy, causal identification, or scientific validity.

## Output Contract

Produce:

1. scope and intended use;
2. artifact inventory and reproducibility limits;
3. strengths supported by evidence;
4. findings ordered by severity and dependency;
5. consequence of each finding;
6. concrete remediation and verification test;
7. residual uncertainty and unresolved questions;
8. routing to specialist skills.

Use the report structure and routing matrix in [report-and-routing.md](references/report-and-routing.md). Avoid an unqualified overall pass/fail label.
