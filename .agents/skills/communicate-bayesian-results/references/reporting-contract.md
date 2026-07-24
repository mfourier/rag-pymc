# Bayesian Reporting Contract

## 1. Analysis Identity

Report:

- analysis title and version;
- date and responsible owners;
- data snapshot and provenance;
- model and code version;
- runtime and dependency lock;
- intended audience and use.

## 2. Target Definition

Define:

- estimand, prediction, or decision;
- target population and unit;
- time horizon;
- outcome and effect scale;
- reference condition;
- aggregation or standardization population;
- causal or associational interpretation.

Name transformations. For log odds, standardized coefficients, latent scales, or normalized outcomes, provide a natural-scale interpretation.

## 3. Data Context

Summarize:

- sampling frame and inclusion rules;
- sample size at the relevant unit;
- missingness, censoring, truncation, and measurement issues;
- preprocessing and exclusions;
- train, validation, test, or temporal boundaries;
- known shifts or limitations.

Do not let a large row count obscure a small number of independent groups or events.

## 4. Model and Prior Context

Describe:

- likelihood and link;
- hierarchical, temporal, spatial, mixture, or causal structure;
- prior roles and sources;
- observation process;
- major identifying assumptions;
- alternative models or sensitivity scenarios.

Use equations or diagrams when they clarify the generative structure. Avoid a distribution inventory without meaning.

## 5. Uncertainty Layers

### Posterior parameter uncertainty

Uncertainty about parameters or latent quantities conditional on the model and observed data.

### Outcome variability

Variation among outcomes even if parameters were known.

### Posterior predictive uncertainty

Combines parameter uncertainty and future outcome variability under the predictive setup. State whether new group effects, future covariates, or observation noise are included.

### Monte Carlo error

Numerical uncertainty from finite posterior draws. Report MCSE relative to posterior uncertainty for key quantities. More draws reduce MCSE, not scientific uncertainty.

### Model and assumption uncertainty

Sensitivity to priors, likelihood, functional form, missingness, measurement, selection, causal identification, and population transport. This is not automatically contained in one posterior interval.

### Data uncertainty and quality

Coverage, measurement validity, provenance, and missing records. State when limitations cannot be repaired statistically.

## 6. Posterior Summaries

For each primary quantity include:

- definition and unit;
- posterior median or mean, chosen consistently;
- credible interval with probability and method;
- relevant posterior probabilities;
- practical threshold or ROPE if prespecified;
- natural-scale translation;
- MCSE or evidence that numerical error is negligible for the reported precision.

Example:

> Conditional on the model and data, the median estimated difference is 4.2 units, with 90% of posterior mass from 1.1 to 7.5. The posterior probability that the difference exceeds the prespecified practical threshold of 3 units is 0.68.

Avoid converting this into a binary discovery label unless a decision rule and consequences were defined.

## 7. Predictive Summaries

Specify:

- what is predicted;
- for which population, covariates, groups, and horizon;
- whether prediction concerns latent mean or recorded outcome;
- calibration and sharpness evidence;
- interval coverage and width where validated;
- out-of-sample or prequential design;
- subgroup and tail behavior;
- deployment differences.

## 8. Computation and Model Checking

Report key evidence:

- chains and post-tuning draws;
- rank-normalized split R-hat;
- bulk and tail ESS;
- MCSE for primary quantities;
- divergent transitions and tree-depth events;
- relevant trace or rank-plot review;
- prior and posterior predictive checks;
- influential observations and Pareto-k when using PSIS-LOO;
- fit failures or repeated-run instability.

Do not use “all diagnostics passed” without identifying checks and scope.

## 9. Comparison

For LOO, WAIC, or other predictive comparison report:

- predictive unit and future task;
- score such as ELPD and its uncertainty;
- difference uncertainty;
- Pareto-k or approximation diagnostics;
- substantive size of the difference;
- stacking or averaging rationale;
- models excluded and why.

Ranks alone overstate separation.

## 10. Sensitivity and Limitations

List assumptions that were varied, target changes, and assumptions not varied. Distinguish:

- robust across tested scenarios;
- materially sensitive;
- untested;
- unidentified;
- computationally unresolved.

State the decision or claim that remains supported under sensitivity, not only parameter movement.

## 11. Decision Statement

If action is recommended, report:

- available actions;
- expected utility or loss, or the threshold rule;
- selected action;
- probability and consequence of error;
- value of additional information;
- owner and review trigger.

Separate the statistical result from the policy choice.
