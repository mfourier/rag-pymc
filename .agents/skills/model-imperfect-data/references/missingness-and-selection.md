# Missingness and Selection

## Express Mechanisms with Variables

Let `Y` be a target variable, `Y_obs` its observed portion, `Y_mis` its missing portion, `X` observed covariates, and `R` an indicator that `Y` is observed.

### MCAR

Missingness does not depend on observed or missing values after accounting for design constants:

```text
R independent of (Y_obs, Y_mis, X)
```

This is strong and often implausible. It may hold by randomized data loss or planned missingness.

### MAR

Missingness may depend on observed information but not on the missing value after conditioning:

```text
R independent of Y_mis given (Y_obs, X)
```

MAR is relative to what is included and observed. Adding auxiliary variables can make an assumption more plausible, but cannot prove it.

### MNAR

Missingness still depends on unobserved values after conditioning on observed information. Observed data generally do not identify this dependence without additional information or restrictions.

Use the labels as summaries after writing the conditional mechanism.

## Missing Outcomes, Covariates, and Predictors

The consequences differ:

- missing outcomes affect likelihood contribution and target-population representation;
- missing covariates require a model for their joint distribution or a defensible marginalization strategy;
- missing group or time identifiers can alter dependence structure;
- missing predictors at deployment require an explicit prediction-time policy.

Model covariate distributions carefully; arbitrary Normal models for mixed or bounded predictors can create implausible imputations.

## Selection Beyond Item Missingness

Selection includes:

- eligibility and sampling-frame inclusion;
- nonresponse or attrition;
- case-control or outcome-dependent sampling;
- referral, testing, or hospitalization;
- publication or recording filters;
- survival to measurement;
- availability in a data system.

Define the target population separately from the observed sample. A perfect model for selected data does not automatically identify a population quantity.

## Modeling Strategies

### Joint modeling under MAR

Specify a joint model for outcomes and incomplete covariates, condition on observed components, and integrate over missing values. Include variables predictive of missingness and the incomplete quantity when defensible.

### Selection models

Factor the joint model as:

```text
p(Y | X) * p(R | Y, X)
```

The response model can include a sensitivity parameter linking `R` to unobserved `Y`. That parameter often requires external information or a sensitivity prior.

### Pattern-mixture models

Factor as:

```text
p(R | X) * p(Y | R, X)
```

Relate unidentified missing-pattern distributions to observed patterns through interpretable offsets or ratios. Explore a defensible sensitivity range.

### Shared-parameter models

Use latent variables that jointly affect the outcome and response or dropout process. The latent structure can be useful but introduces strong identification assumptions.

### Weighting and poststratification

Known inclusion probabilities, sampling weights, or population margins can support population inference. Uncertain weights and estimated response models should propagate uncertainty where material. Positivity and sparse poststratification cells remain concerns.

## Identification Sources

Useful information can come from:

- randomized follow-up of nonrespondents;
- administrative outcomes for otherwise missing cases;
- refreshment samples;
- repeated measurements;
- instrumental or exclusion variables affecting response but not the outcome model, with strong justification;
- external population margins;
- validation subsets;
- informative priors on sensitivity parameters.

No modeling sophistication creates information absent from data and assumptions.

## Diagnostics and Checks

Compare observed and predicted:

- response rates by covariates and group;
- dropout timing;
- patterns of joint missingness;
- distributions before and after weighting or imputation;
- predicted missing values against held-out observed values under artificial masking;
- population margins not used in fitting;
- sensitivity of target quantities to unidentified mechanism parameters.

Artificial masking under an observed-data mechanism tests interpolation, not necessarily the real MNAR process.

## Reporting

State:

- missingness unit and denominator;
- missingness patterns and time order;
- variables in the response model;
- identifying assumptions and external data;
- whether the estimand is sample-conditional or population-level;
- sensitivity parameter meanings and ranges;
- target changes across scenarios;
- limitations that observed data cannot resolve.
