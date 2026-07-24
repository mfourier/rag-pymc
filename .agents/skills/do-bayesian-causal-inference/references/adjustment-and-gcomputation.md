# Adjustment, G-Computation, and Bayesian Estimation

## Covariate Selection

Choose adjustment variables from causal structure, not predictive importance alone. A sufficient set blocks noncausal backdoor paths without opening collider paths or conditioning on descendants of treatment for a total-effect estimand.

Include prognostic pretreatment covariates when they improve precision and modeling, but preserve the identification logic. Instrument-like variables can intensify practical positivity problems and bias sensitivity in some settings.

## Bayesian Outcome Regression and G-Computation

Fit a model for the conditional outcome distribution:

```text
p(Y | A, X, parameters)
```

For every posterior draw:

1. set treatment to each intervention value for every target unit or covariate draw;
2. generate or calculate the corresponding conditional potential-outcome expectation or draw;
3. average over the target covariate distribution;
4. contrast interventions on the prespecified scale.

This propagates parameter and outcome uncertainty conditional on the model. Use flexible but regularized structures for nonlinearities and interactions that matter to confounding or effect modification.

## Standardization Population

Choose among:

- observed sample;
- treated population;
- trial-eligible population;
- external target population;
- future deployment population;
- a policy-defined synthetic population.

Store the population weights or covariate draws used for standardization. A fitted treatment coefficient is generally not the marginal causal effect in nonlinear models.

## Treatment and Propensity Models

The propensity score is:

```text
e(X) = P(A = 1 | X)
```

Use it to diagnose overlap, construct weights, subclassify, or support combined estimators. Bayesian uncertainty in the treatment model can be propagated, but naïvely feeding outcome information back into treatment assignment can change the design-stage interpretation. Document modularization or joint modeling choices.

## Weighting

Inverse probability weighting creates a pseudo-population under correct treatment and selection models and positivity. Inspect:

- weight distribution and effective sample size;
- extreme and truncated weights;
- covariate balance after weighting;
- subgroup-specific support;
- sensitivity of estimands to truncation or stabilization;
- uncertainty introduced by estimated weights.

Weight truncation changes the target or introduces bias-variance tradeoffs. Report it as an estimand or estimator choice, not mere preprocessing.

## Doubly Robust Structures

Methods combining outcome and treatment models can be consistent when one nuisance model is correct under their formal conditions. A generic Bayesian joint model is not automatically doubly robust. If claiming double robustness, identify the estimator and theorem conditions precisely.

Bayesian targeted or semiparametric methods may require specialized implementation beyond a standard posterior regression. Do not imply properties that were not established.

## Longitudinal Treatments

Time-varying confounders affected by prior treatment cannot generally be handled by ordinary regression adjustment. Consider:

- longitudinal g-formula;
- marginal structural models with treatment and censoring weights;
- structural nested models;
- sequential decision or dynamic treatment-regime methods.

Specify treatment history, covariate history, dynamic rule, censoring, and sequential exchangeability at every time.

## Heterogeneous Effects

For CATEs or subgroup effects:

- define modifiers before outcome inspection when confirmatory;
- use partial pooling and regularization;
- ensure within-subgroup overlap;
- distinguish predictive heterogeneity from causal interaction;
- evaluate multiplicity and selection;
- standardize within the intended subgroup population;
- report decision relevance and uncertainty.

Do not rank individuals by noisy effect estimates without a loss function and validation.

## Randomized Designs

Randomization supports treatment exchangeability but does not automatically solve:

- nonadherence;
- missing outcomes;
- post-randomization selection;
- interference;
- measurement error;
- limited generalizability;
- treatment-version ambiguity.

Preserve the randomized assignment mechanism and distinguish intention-to-treat, per-protocol, and treatment-received estimands.

## Model Checking

Check outcome predictions by treatment and covariate strata, overlap, extrapolation, influential observations, residual dependence, calibration, and sensitivity to functional form. Predictive fit cannot verify exchangeability, but poor fit can invalidate a chosen estimator.
