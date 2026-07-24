# Bayesian Analysis Audit Artifact Contract

## Purpose

This contract defines the evidence needed to audit a Bayesian analysis. It is deliberately broader than a posterior sample because model quality depends on the scientific target, data process, implementation, computation, prediction, and decision context.

## Tier 1: Target and Decision

Record:

- the scientific or operational question;
- the estimand or predictive target;
- the population, time horizon, and unit of analysis;
- the action informed by the analysis;
- the loss, utility, or practical consequence of errors;
- the acceptable latency and uncertainty for that use.

If no explicit decision exists, define what conclusions the analysis is intended to support. A posterior parameter is not automatically the estimand.

## Tier 2: Data and Provenance

Request:

- raw-data source and extraction date;
- sampling frame and inclusion or exclusion rules;
- data dictionary with units and valid ranges;
- preprocessing and feature-generation code;
- missingness, censoring, truncation, rounding, and measurement metadata;
- group, location, and time identifiers;
- train, validation, and test boundaries;
- known interventions, policy changes, or acquisition changes;
- row counts before and after every material transformation.

Prefer immutable data identifiers or hashes when available. For confidential data, request reproducible summaries and synthetic fixtures rather than copying restricted records.

## Tier 3: Model Specification

Request:

- a generative description or graphical model;
- prior distributions and their rationale;
- likelihood and link functions;
- observation and missing-data models;
- hierarchical structure and exchangeability assumptions;
- constraints, transformations, and parameterizations;
- deterministic quantities used for decisions;
- alternative models considered and rejected.

Confirm units and support at every stochastic node. Note parameters that are weakly identified or identified mainly by the prior.

## Tier 4: Executable Environment

Request:

- complete model code and entry point;
- dependency lockfile and runtime versions;
- random seeds and chain initialization strategy;
- sampling algorithm and tuning arguments;
- hardware or backend relevant to numerical behavior;
- warnings, exceptions, and sampler logs;
- tests for data transformations and model shapes.

For this repository, verify the active PyMC, ArviZ, PyTensor, Python, and NumPy versions at runtime rather than assuming an API from memory.

## Tier 5: Inference Artifact

The preferred artifact is a NetCDF-serialized xarray DataTree or ArviZ-compatible inference object containing, where applicable:

- `posterior`;
- `sample_stats`;
- `prior` and `prior_predictive`;
- `posterior_predictive`;
- `observed_data` and `constant_data`;
- `log_likelihood`;
- prediction groups for out-of-sample use.

Retain coordinates, dimensions, attributes, observed-data identifiers, and model version. A flat table of posterior means is insufficient for a full audit.

## Tier 6: Checks and Validation

Request:

- prior predictive checks;
- convergence and geometry diagnostics;
- posterior predictive checks tied to model failure modes;
- calibration or validation against held-out or future data;
- simulation recovery or formal SBC results;
- sensitivity to priors, likelihood, exclusions, and parameterization;
- influential-observation analysis;
- LOO/PSIS, ELPD, WAIC, or stacking artifacts when models are compared;
- decision or utility evaluation when results drive action.

Each plot must retain the code and data slice that produced it. Screenshots alone weaken reproducibility.

## Tier 7: Reporting and Governance

Request:

- manuscript, report, dashboard, or model card;
- provenance for every reported number;
- review history and unresolved objections;
- release, monitoring, update, and rollback plan for deployed models;
- privacy, fairness, safety, and domain approval records where relevant.

## Missing-Artifact Classification

Classify a missing artifact as one of:

- **Unavailable:** it should exist but cannot be retrieved.
- **Not produced:** the check or documentation was never created.
- **Not applicable:** the artifact is irrelevant, with a stated reason.
- **Restricted:** it exists but access is limited; describe the substitute evidence.
- **Unknown:** its existence cannot yet be established.

Do not mark an analysis incorrect merely because an artifact is absent. Instead, state which conclusions cannot be audited and how that limitation changes risk.

## Minimal Reproducible Audit Package

At minimum, a technical audit should be able to reconstruct:

1. the target quantity;
2. the analysis dataset from an approved source;
3. the model graph and priors;
4. the inference run or a representative reduced run;
5. diagnostics and predictive checks;
6. the reported estimates or decisions.

If reconstruction is impossible, prioritize restoring provenance before fine-grained statistical review.
