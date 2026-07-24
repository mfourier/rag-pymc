# Audit Report and Routing Guide

## Report Template

### 1. Scope

- analysis and version audited;
- intended scientific or operational use;
- target population and time horizon;
- artifacts included and excluded;
- audit date and environment.

### 2. Executive Assessment

Summarize the most consequential evidence, the uses currently supported, the uses not supported, and the next dependency to resolve. Avoid an unqualified “valid” or “invalid” label.

### 3. Artifact Inventory

List available, missing, restricted, and non-applicable artifacts. State which conclusions cannot be evaluated because of gaps.

### 4. Supported Strengths

Record strengths only when tied to evidence, such as reproducible data construction, plausible prior predictive behavior, clean repeated-run diagnostics, or calibrated held-out predictions.

### 5. Findings

For each finding use:

```text
ID:
Title:
Domain:
Severity:
Confidence:
Observation:
Evidence:
Interpretation:
Consequence:
Remediation:
Verification:
Dependencies:
Owner:
```

### 6. Residual Risk

Describe uncertainty that remains after proposed remediation, including structural assumptions that data cannot verify.

### 7. Reproduction Instructions

Provide exact environment, commands, artifact locations, seeds, and expected outputs. Keep expensive full runs separate from reduced smoke tests.

## Specialist Routing Matrix

### `$bayesian-statistics-foundations`

Use for explaining Bayesian concepts and interpreting R-hat, ESS, MCSE, divergences, predictive checks, calibration, LOO/PSIS, WAIC, ELPD, model averaging, sensitivity, or the full Bayesian workflow.

### `$develop-pymc-models`

Use for implementing, refactoring, or debugging PyMC models; coords and dims; PyTensor expressions; sampling; posterior prediction; or version-sensitive APIs.

### `$simulation-based-calibration`

Use for formal prior or posterior SBC, rank histograms, PIT or ECDF diagnostics, ties, discrete parameters, MCMC autocorrelation, and thinning within SBC.

### `$elicit-and-stress-test-priors`

Use when prior knowledge must be elicited, translated into distributions, checked jointly in observable space, or stress-tested for conflict and decision sensitivity.

### `$validate-models-by-simulation`

Use for parameter recovery, design recovery, identifiability probes, scenario simulation, misspecification experiments, and robustness studies that are broader than formal SBC.

### `$model-imperfect-data`

Use for missingness, selection, measurement error, misclassification, censoring, truncation, rounding, heaping, and explicit observation-process models.

### `$design-bayesian-studies`

Use for assurance, expected precision, decision-based sample size, adaptive rules, prospective design simulation, and value of information.

### `$do-bayesian-causal-inference`

Use for causal estimands, DAGs, identification, adjustment, g-computation, mediation, sensitivity to unmeasured confounding, and transportability.

### `$communicate-bayesian-results`

Use for reports, model cards, visual language, uncertainty communication, decision summaries, and claim calibration.

### `$deploy-and-monitor-bayesian-models`

Use for model and data contracts, prediction artifacts, prequential evaluation, calibration and drift monitoring, update triggers, rollback, and production governance.

## Routing Principles

- Route by the work required, not merely by vocabulary in the request.
- Keep orchestration in the audit skill and detailed remediation in the specialist skill.
- Use several skills when risks span domains, but state the sequence and dependency.
- Do not use an audit to bypass the stronger methodological contract of a specialist skill.
