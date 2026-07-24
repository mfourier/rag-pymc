# Bayesian Deployment Contract

## 1. Operational Use

Define:

- prediction, ranking, estimate, or action;
- target population and eligibility;
- prediction and outcome horizon;
- batch, streaming, or interactive use;
- latency and availability target;
- downstream consumer and action owner;
- utility, loss, or threshold;
- prohibited uses and unsupported populations.

## 2. Input Contract

For every field record:

- name and semantic definition;
- type, unit, support, and valid range;
- coordinate or category vocabulary;
- time at which the value is known;
- source system and freshness;
- missing-value meaning and policy;
- transformation and version;
- privacy or access classification;
- fallback or rejection behavior.

Treat category novelty, unit changes, sentinel values, duplicate identifiers, and time leakage as explicit contract cases.

## 3. Output Contract

Define whether outputs contain:

- posterior mean, median, or quantiles of a latent quantity;
- predictive mean, median, quantiles, or draws for a new observation;
- event probability or rate;
- interval and its probability level;
- subgroup or new-group uncertainty;
- action recommendation and expected utility;
- model, data, and scoring versions;
- warning, out-of-domain, or failure status.

Every probability must name its event and horizon. Every interval must name the random quantity and whether observation noise is included.

## 4. Model Artifact Contract

Version:

- model code and graph;
- prior and likelihood specification;
- training or conditioning data snapshot;
- posterior or approximate artifact;
- coordinates, dimensions, and transformations;
- software environment and numerical backend;
- seeds or randomness policy;
- predictive function and decision rule;
- validation and approval record;
- artifact checksum and storage policy.

Do not reconstruct a model at serving time from undocumented defaults.

## 5. Serving Representations

### Full posterior draws

Maximizes flexibility for nonlinear targets and decisions but can increase storage, latency, and privacy risk.

### Thinned or subsampled draws

May be appropriate for serving after validating target-specific numerical accuracy. Do not use thinning to repair sampling autocorrelation or convergence.

### Parametric approximation

Can reduce cost but may lose skewness, multimodality, dependence, or tail behavior. Validate on every operational quantity, not only marginal moments.

### Precomputed predictive summaries

Useful for fixed cohorts or grids but limited under new covariates and model updates. Version the population and horizon.

### Decision lookup or policy

Fast but embeds a utility function, threshold, and target population. Treat changes as governed model changes.

## 6. Prediction Semantics

Specify whether scoring integrates over:

- posterior parameter uncertainty;
- outcome variability;
- new random effects or existing group effects;
- uncertain future covariates;
- measurement or recording error;
- missing predictors;
- model ensemble weights;
- intervention or policy scenarios.

Existing-group and new-group predictions are different contracts in hierarchical models.

## 7. Reproducibility and Idempotence

For deterministic endpoints, identical validated inputs and artifact versions should produce identical outputs. If predictive sampling is exposed, define seed handling, draw count, concurrency behavior, and whether exact repeatability is guaranteed.

Persist request or batch identifiers, feature version, model version, output schema, and status without logging prohibited sensitive data.

## 8. Failure Contract

Define behavior for:

- schema mismatch;
- missing or stale features;
- unseen categories;
- unsupported covariate ranges;
- numerical overflow or invalid probabilities;
- unavailable model artifact;
- latency timeout;
- partial batch failure;
- monitoring or label pipeline outage.

Fallbacks may reject, defer, use a conservative rule, or invoke a prior model. Never silently substitute zero, population mean, or last value without an approved semantic meaning.

## 9. Release Validation

Require:

- unit and schema tests;
- golden predictions against the analysis environment;
- posterior-summary equivalence within declared tolerance;
- support and invariant tests;
- missingness and category tests;
- latency and load tests;
- time-ordered and subgroup validation;
- privacy and security review;
- rollback rehearsal;
- owner approval.
