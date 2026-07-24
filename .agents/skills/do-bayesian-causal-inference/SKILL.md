---
name: do-bayesian-causal-inference
description: Design, review, implement, and communicate Bayesian causal analyses. Use for defining potential-outcome or interventional estimands, drawing and interrogating DAGs, assessing identification, choosing adjustment sets, g-computation and standardization, propensity or weighting strategies, heterogeneous effects, mediation, interference, longitudinal treatment, sensitivity to unmeasured confounding, missingness or measurement error in causal variables, and transportability or generalizability.
---

# Do Bayesian Causal Inference

## Purpose

Estimate causal quantities only after defining the intervention, target population, estimand, and identification assumptions. Bayesian inference quantifies uncertainty conditional on a causal model; a posterior distribution does not create causal identification.

## Required Order of Work

1. **Define the causal question.** Specify treatment versions, intervention timing, comparator, outcome, horizon, target population, and unit.
2. **Define the estimand.** Use a potential-outcome or interventional expression for ATE, ATT, CATE, risk ratio, policy value, mediation effect, or another target. Follow [estimands-and-identification.md](references/estimands-and-identification.md).
3. **Map the data-generating structure.** Build a DAG or longitudinal causal graph before selecting predictors. Include causes of treatment, outcome, selection, missingness, measurement, and censoring.
4. **State identification assumptions.** Address consistency, exchangeability, positivity, interference, measurement validity, selection, and time ordering. Distinguish assumptions supported by design from assumptions imposed analytically.
5. **Derive an identification functional.** Establish whether the estimand is expressible using the observed-data distribution. If not, redefine the estimand, obtain additional data, use partial identification, or introduce explicit sensitivity parameters.
6. **Choose an estimator and Bayesian model.** Use outcome regression and g-computation, treatment and weighting models, doubly robust structures, longitudinal g-methods, or design-based analysis as appropriate. See [adjustment-and-gcomputation.md](references/adjustment-and-gcomputation.md).
7. **Diagnose overlap and fit.** Inspect propensity distributions, effective weights, covariate balance, extrapolation, predictive adequacy, posterior computation, and support in target subgroups.
8. **Standardize to the target population.** Generate potential outcomes or interventional predictions under each treatment and average using the correct target covariate distribution.
9. **Stress-test assumptions.** Analyze unmeasured confounding, treatment versions, missingness, measurement error, interference, functional form, positivity, and transport using [sensitivity-transport-and-validation.md](references/sensitivity-transport-and-validation.md).
10. **Report calibrated claims.** Separate design evidence, identification assumptions, statistical model, posterior uncertainty, sensitivity results, and scope of transport.

Use [causal-analysis-contract.md](assets/causal-analysis-contract.md) as the analysis record.

## Guardrails

- Do not infer causality from a posterior association, predictive accuracy, temporal ordering alone, or a treatment coefficient.
- Do not adjust for every available variable. Avoid descendants of treatment, colliders, and variables affected by selection unless a valid strategy requires them.
- Do not condition on post-treatment variables when estimating a total effect.
- Do not interpret overlap as a yes/no property from one threshold; identify where the target estimand requires extrapolation.
- Do not let flexible outcome models substitute for exchangeability or positivity.
- Do not present prior information as resolving unmeasured confounding unless it explicitly models the unidentified causal quantities.
- Do not claim mediation effects without specifying treatment-mediator interaction, cross-world or interventional assumptions, and post-treatment confounding.
- Do not transport results without defining the target population and selection mechanism.

## Routing

- Use `$develop-pymc-models` to implement outcome, treatment, longitudinal, multilevel, or missing-data models in PyMC.
- Use `$model-imperfect-data` for causal-variable measurement error, misclassification, informative missingness, censoring, and selection.
- Use `$elicit-and-stress-test-priors` for sensitivity parameters, weak overlap, and external causal knowledge.
- Use `$validate-models-by-simulation` to test bias, coverage, overlap, misspecification, and estimator behavior under known causal generators.
- Use `$design-bayesian-studies` for randomized assignment, cluster allocation, validation subsamples, adaptive designs, and prospective causal precision or utility.

## Output Contract

Deliver the causal question and estimand, target-trial or intervention specification, DAG and time order, identification functional, assumptions and their evidence, estimator and model, overlap and fit diagnostics, standardized posterior causal quantities, sensitivity and transport analysis, and a claim whose strength matches the design.
