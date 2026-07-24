# Causal Sensitivity, Transport, and Validation

## Unmeasured Confounding

Represent the missing causal information with interpretable quantities, such as:

- association of an unmeasured confounder with treatment and outcome;
- residual correlation between treatment and potential outcomes;
- bias function or treatment-effect shift;
- prevalence imbalance of a binary confounder;
- negative-control calibration parameters.

Vary them over ranges grounded in domain knowledge or benchmarked against observed covariates. Report the causal estimand across the full range and identify values that change the decision.

Do not claim a universal robustness value without matching its assumptions and scale to the analysis.

## Negative Controls

Negative-control outcomes or exposures can reveal certain residual biases if their causal structure is justified. They do not prove absence of confounding when null, and a non-null result can arise from measurement, selection, or model misspecification. Draw their causal graph explicitly.

## Positivity and Extrapolation

Assess:

- treatment probabilities by relevant covariate regions;
- counts and uncertainty in extreme-propensity strata;
- distance of counterfactual predictions from observed treatment support;
- target-population mass requiring extrapolation;
- sensitivity to trimming, overlap weights, or target redefinition;
- posterior dependence on priors in unsupported regions.

Prefer redefining an estimand for the overlap population when the original target is not supportable, and state the change.

## Missingness and Measurement

Sensitivity analysis should include:

- differential treatment or outcome misclassification;
- measurement error in confounders;
- informative outcome missingness or censoring;
- selection into the analytic sample;
- treatment-version or adherence uncertainty.

Route detailed observation-process models to `$model-imperfect-data`. An error-prone confounder may leave residual confounding even when included in a regression.

## Interference

When units affect one another, define:

- clusters or networks;
- exposure mapping from others' treatments;
- direct, spillover, total, or overall effect;
- partial-interference assumptions;
- assignment and observation mechanism.

Stress-test alternative network boundaries or exposure mappings. Individual-level SUTVA language is insufficient when spillovers are plausible.

## Mediation

Define whether the target is:

- controlled direct effect;
- natural direct or indirect effect;
- interventional direct or indirect effect;
- path-specific effect.

State assumptions about treatment-mediator interaction, mediator-outcome confounding, post-treatment confounders, consistency, and cross-world quantities where applicable. Use interventional estimands when they better match feasible interventions and defensible identification.

## Transportability and Generalizability

Distinguish:

- sample average effect;
- trial-eligible population effect;
- external target-population effect;
- future-policy population effect.

Model or weight selection into the study using effect modifiers required for transport. Check target-population overlap and propagate uncertainty in external margins or weights. A representative sample is not required for internal validity, but population inference needs a transport argument.

## Validation by Simulation

Construct causal generators with known estimands and vary:

- confounding strength;
- overlap;
- outcome and treatment nonlinearities;
- treatment-effect heterogeneity;
- measurement and missingness;
- selection and censoring;
- interference or time-varying treatment;
- generator-fitter mismatch.

Report bias, coverage, regret, fit failures, and performance by scenario. Recovery under the exact fitted causal model supports implementation, not the truth of identification assumptions in observed data.

## Claim Calibration

Report causal conclusions in layers:

1. design facts, such as randomization or eligibility;
2. causal graph and identification assumptions;
3. observed-data model and diagnostics;
4. posterior causal estimate conditional on those assumptions;
5. sensitivity to unverified assumptions;
6. transport scope and excluded populations;
7. decision implication and remaining uncertainty.

When sensitivity scenarios reverse the conclusion, lead with that dependence rather than the primary-model point estimate.
