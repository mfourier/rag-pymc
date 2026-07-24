# Measurement Error and Misclassification

## Continuous Measurement Error

Let `X_true` be a latent quantity and `X_obs` its measurement.

### Classical-like error

```text
X_obs = X_true + error
```

with error independent of `X_true` conditional on relevant factors. In regression, treating `X_obs` as truth often attenuates simple linear associations, but this heuristic does not generalize to nonlinear, multivariable, differential, or heteroskedastic settings.

### Berkson-like error

```text
X_true = X_assigned + error
```

This can arise when an assigned exposure is shared but individual true exposure varies. Its inferential consequences differ from classical error.

### Systematic and differential error

Bias may depend on true value, outcome, group, device, site, time, or covariates. Model calibration curves, offsets, heteroskedastic scales, and batch effects when scientifically justified.

## Outcome and Predictor Error

Error in predictors can confound structural variation with measurement noise. Error in outcomes changes the likelihood and can interact with censoring or selection. When both sides are noisy, the model often needs validation data or strong structural information.

Replicate measurements identify within-unit repeatability under assumptions but may not identify systematic bias relative to truth.

## Misclassification

For a binary latent state `D` and observed classification `T`:

```text
sensitivity = P(T = 1 | D = 1)
specificity = P(T = 0 | D = 0)
```

Observed positive probability is:

```text
P(T = 1) = sensitivity * P(D = 1)
           + (1 - specificity) * (1 - P(D = 1))
```

Prevalence, sensitivity, and specificity may be weakly identified without gold-standard data, repeated tests, multiple populations, conditional-independence assumptions, or informative priors.

For multiclass outcomes, use a confusion matrix whose rows form valid probability simplexes. Consider whether errors vary by true class, covariates, reader, device, or site.

## Differential Misclassification

Sensitivity or specificity can depend on exposure, outcome, covariates, or group. Assuming nondifferential error for convenience can bias contrasts and subgroup comparisons. Define which conditioning variables affect each error process.

## Imperfect Diagnostic Tests

For multiple tests, conditional independence given latent status is a strong assumption. Shared biology, sample quality, reader effects, or device conditions can induce residual dependence. Add dependence only when the data or prior information can support it, and stress-test the assumption.

## Identification and Data Design

Useful designs include:

- gold-standard validation subsets;
- replicate measurements;
- multiple instruments with different error mechanisms;
- calibration samples spanning the target range;
- blinded repeated readers;
- crossover or remeasurement studies;
- external laboratory or device validation;
- known standards or negative and positive controls.

Prefer validation data sampled across relevant groups and ranges. A convenience validation subset can introduce transport assumptions.

## Prior Design

Encode external evidence for:

- sensitivity and specificity;
- calibration intercept and slope;
- measurement-error scale and heteroskedasticity;
- batch or device variation;
- residual dependence among tests;
- prevalence or latent-state dynamics.

Inspect the joint prior predictive distribution of recorded measurements, not only each error parameter.

## Predictive Checks

Check:

- replicate differences and within-unit variation;
- disagreement rates among instruments or readers;
- distributions by device, batch, site, group, and time;
- tails, boundaries, and impossible readings;
- confusion patterns in validation data;
- latent prevalence against credible external ranges;
- posterior predictions for held-out validation measurements.

Good fit to noisy observations does not establish recovery of latent truth.

## Sensitivity Analysis

Vary poorly identified error assumptions over defensible ranges. Report effects on:

- latent prevalence or exposure;
- scientific contrasts;
- subgroup differences;
- posterior predictive calibration;
- decisions or threshold probabilities.

If conclusions depend on a narrow unverified error rate, state that dependency prominently.
