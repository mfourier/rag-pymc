# Implementation Patterns for Imperfect Data Models

## Generative Pattern

Organize the model conceptually as:

```text
latent scientific state
    -> true covariates and outcomes
    -> selection or response
    -> measurement or classification
    -> censoring, truncation, or rounding
    -> recorded data
```

Not every application needs every layer. Include only mechanisms that matter to the estimand and are supported by data or defensible assumptions.

## Explicit Latent Variables versus Marginalization

Use explicit latent variables when they are scientifically meaningful, needed for prediction, or computationally manageable. Marginalize discrete states or nuisance variables when it improves geometry and the integrated likelihood is available.

Discrete latent variables cannot be sampled by gradient-based NUTS directly. In PyMC, consider analytic marginalization, a mixture likelihood, or an appropriate compound step method. Route concrete implementation to `$develop-pymc-models` and verify against the pinned runtime.

## Missing Continuous Values

A coherent joint model defines a distribution for incomplete covariates and the outcome conditional on them. Preserve dimensions and coordinate alignment. Check whether automatic missing-value handling implements the intended generative model; explicit modeling is often clearer for complex dependence.

Predictions for new rows require a policy for which covariates will be available. Training-time imputation alone does not solve deployment-time missingness.

## Measurement-Error Pattern

Typical structure:

```text
X_true ~ population model
X_obs ~ measurement model(X_true, calibration parameters)
Y_obs ~ outcome model(X_true, other predictors)
```

With validation data, indicate which rows observe a gold-standard or replicate measure. Share calibration parameters only when exchangeability across devices, groups, and time is defensible.

## Misclassification Pattern

For a latent binary state, marginalize over the latent state when possible:

```text
P(test = 1 | predictors)
  = sensitivity * prevalence
  + (1 - specificity) * (1 - prevalence)
```

When individual latent classifications are required, derive them from posterior probabilities with the relevant loss function rather than using a fixed 0.5 rule by default.

## Censoring and Interval Likelihoods

Use log-CDF or log-survival terms for censored contributions and probability differences for interval observations. Prefer numerically stable distribution functions. Verify signs and boundaries with simulated unit tests.

For truncation, subtract the log probability of inclusion from each observed log-density contribution, respecting individual-specific limits.

## Selection Models

Jointly specify the outcome and inclusion mechanism. Parameters linking response to unobserved outcomes are often weakly identified. Use named sensitivity parameters, informative priors or fixed scenarios, and direct target-quantity comparisons.

## Computational Geometry

Imperfect-data models commonly produce:

- funnels from latent states and small scale parameters;
- strong correlations between truth and error;
- prevalence-sensitivity-specificity ridges;
- label symmetries in latent classes;
- boundary mass near perfect tests or zero error;
- multimodality under weak validation information.

Use noncentered parameterizations where appropriate, informative regularization, marginalization, identifiable constraints, and smaller independently checked prototypes. Never interpret a posterior before resolving serious computational pathologies.

## Predictive Groups

Retain separate predictive quantities for:

- latent true values;
- replicated recorded observations;
- missingness or inclusion indicators;
- validation measurements;
- decision-relevant corrected outcomes.

Checks against observed records assess the full observation process. Checks against validation truth assess latent recovery. They answer different questions.

## Testing Checklist

- simulate zero-error and perfect-classification limiting cases;
- verify censored and truncated likelihood contributions analytically on small examples;
- test dimension alignment under missing patterns;
- recover known values with validation data;
- test weak-identification scenarios intentionally;
- confirm predictive draws respect support and recording rules;
- retain failures and diagnostic warnings in simulation summaries;
- compare explicit-latent and marginalized implementations when both are feasible.
