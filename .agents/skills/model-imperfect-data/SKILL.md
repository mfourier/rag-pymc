---
name: model-imperfect-data
description: Design, review, and explain Bayesian observation-process models for imperfect data. Use for missing data and selection, MCAR/MAR/MNAR assumptions, measurement error and errors-in-variables, misclassification, imperfect tests, censoring, truncation, interval observation, rounding, heaping, detection limits, informative sampling, or sensitivity analysis when the observed record differs systematically from the latent quantity of interest.
---

# Model Imperfect Data

## Purpose

Represent how latent quantities become recorded observations. Separate the scientific process from the observation, selection, and recording processes so uncertainty and bias are propagated rather than hidden in preprocessing.

## Core Decomposition

Write the generative story in layers:

1. target population and latent scientific state;
2. sampling, inclusion, or response mechanism;
3. latent true exposure, outcome, or covariate;
4. measurement or classification mechanism;
5. censoring, truncation, rounding, heaping, or detection;
6. recorded data and metadata.

For each layer, identify which variables are observed, latent, fixed by design, externally calibrated, or unidentified without assumptions.

## Workflow

1. **Define the estimand.** State whether the target concerns latent truth, observed records, a selected population, or a corrected population quantity.
2. **Map the observation process.** Use [observation-process-audit.md](assets/observation-process-audit.md) to trace eligibility, contact, response, measurement, detection, transformation, and storage.
3. **Classify mechanisms cautiously.** For missingness and selection, express conditional independence assumptions rather than relying only on MCAR/MAR/MNAR labels. Follow [missingness-and-selection.md](references/missingness-and-selection.md).
4. **Specify measurement error.** Distinguish classical from Berkson-like error, differential from nondifferential error, continuous error from misclassification, and known from estimated calibration. Follow [measurement-error-and-misclassification.md](references/measurement-error-and-misclassification.md).
5. **Represent coarsening correctly.** Distinguish censoring, truncation, interval observation, detection limits, rounding, and heaping using [censoring-truncation-rounding.md](references/censoring-truncation-rounding.md).
6. **Assess identification.** Determine which parameters require validation data, repeated measurements, gold-standard subsets, exclusion restrictions, informative priors, or sensitivity parameters.
7. **Check prior implications.** Simulate latent and observed data jointly. Validate prevalence, error rates, response patterns, detection rates, and recorded-value distributions.
8. **Fit and diagnose.** Inspect posterior geometry, latent correlations, boundary mass, multimodality, prior dominance, and computational diagnostics.
9. **Check both layers.** Compare posterior predictions with recorded data and inspect implied latent quantities against domain constraints or validation data.
10. **Stress-test unverified assumptions.** Vary sensitivity, specificity, missing-not-at-random parameters, error scales, selection effects, and coarsening rules over defensible ranges.

Use [implementation-patterns.md](references/implementation-patterns.md) for model patterns and route executable PyMC work to `$develop-pymc-models`.

## Guardrails

- Do not impute once and treat imputed values as observed without propagating uncertainty.
- Do not infer an MNAR mechanism from observed data alone when the identifying information is absent.
- Do not assume measurement error only widens intervals; nonlinear models can produce directional bias.
- Do not confuse outcome misclassification with zero inflation or generic overdispersion.
- Do not replace a censored observation with its limit or midpoint and call the likelihood correct.
- Do not confuse truncation, where excluded units are absent from the sample, with censoring, where a coarsened record remains.
- Do not estimate latent truth, error variance, and structural variation freely when the data cannot separate them.
- State which conclusions are driven by priors or sensitivity parameters.

## Routing

- Use `$elicit-and-stress-test-priors` for error-rate, sensitivity, specificity, response, and selection priors.
- Use `$validate-models-by-simulation` to study recoverability and misspecification across observation-process scenarios.
- Use `$design-bayesian-studies` to plan validation subsamples, repeat measurements, follow-up, or richer data collection.
- Use `$do-bayesian-causal-inference` when missingness, selection, or measurement error threatens a causal estimand.
- Use `$develop-pymc-models` for PyMC implementation, censoring likelihoods, latent variables, marginalization, coords/dims, and posterior prediction.

## Output Contract

Deliver the latent target, observation-process diagram, conditional assumptions, identification sources, model equations or generative story, prior and predictive checks, sensitivity scenarios, computational risks, and a plain-language statement of what remains unlearnable from the available data.
