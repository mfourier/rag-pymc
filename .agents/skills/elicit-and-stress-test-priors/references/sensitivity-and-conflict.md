# Prior Sensitivity, Influence, and Conflict

## Define the Question First

Prior sensitivity asks whether reasonable alternative prior assumptions materially alter a specified target. Define the target as one or more of:

- posterior location or interval for a scientific contrast;
- predictive distribution for a stated population;
- tail probability or exceedance event;
- ranking or classification;
- expected loss, utility, or selected action;
- qualitative scientific conclusion.

A parameter can be prior-sensitive while the decision is stable, or posterior summaries can look stable while a rare-event decision is sensitive.

## Construct Meaningful Scenarios

Use a small set of interpretable alternatives:

- primary domain-informed prior;
- weaker regularization with plausible wider tails;
- stronger skeptical prior around a reference value;
- enthusiastic or alternative-expert scenario, if defensible;
- alternative dependence or hierarchical-scale structure;
- alternative prior family with similar central mass but different tails.

Do not create arbitrary extremes solely to demonstrate robustness. State what knowledge or concern each scenario represents.

## Compare at Multiple Layers

### Computation

Check whether the alternative changes geometry, divergences, effective sample size, multimodality, or initialization sensitivity. Computational failure is not a substantive sensitivity estimate.

### Posterior inference

Compare medians or means, intervals, probability statements, shrinkage, correlations, and latent structure.

### Prediction

Compare posterior predictive distributions, calibration, tail events, group behavior, and out-of-sample scores when available.

### Decision

Compare expected utility, regret, action probabilities, threshold crossings, and the stability of the selected action.

## Prior Influence

Strong prior influence can be appropriate when data are weak and external information is reliable. Report it rather than hiding it. Useful evidence includes:

- prior and posterior overlays on an interpretable scale;
- likelihood-informed or data-cloning analyses where methodologically justified;
- effective prior-to-posterior contraction summaries;
- sensitivity of the target across prior scenarios;
- comparisons of prior and posterior predictive behavior.

Avoid reducing influence to one universal scalar. Influence is quantity-specific and parameterization-dependent.

## Prior-Data Conflict

Potential conflict appears when observed or likelihood-supported behavior lies in regions receiving little prior predictive probability. Investigate:

1. data errors, unit errors, selection, or measurement changes;
2. whether the elicitation conditioned on the correct population and covariates;
3. likelihood misspecification or omitted heterogeneity;
4. transformation and parameterization mistakes;
5. expert overconfidence or stale external evidence;
6. genuine regime change or surprising data;
7. computational failure.

Do not automatically broaden the prior until the conflict disappears. That can erase useful evidence of a broken model or changed population.

## Sensitivity Reporting Table

For each scenario report:

| Field | Meaning |
|---|---|
| Scenario | Human-readable prior assumption |
| Knowledge basis | Expert, historical data, regularization, or stress test |
| Joint implication | What changes in parameter and observable space |
| Computation | Diagnostics and failures |
| Target estimate | Quantity-specific posterior summary |
| Prediction | Relevant predictive metric or distribution |
| Decision | Selected action and expected utility or loss |
| Interpretation | Material or immaterial change, with rationale |

## Interpreting Stability

Call a result robust only relative to:

- the stated set of plausible prior alternatives;
- the target quantity and decision;
- the observed data and model family;
- satisfactory computation under every compared scenario.

Prior robustness does not imply robustness to the likelihood, missingness, measurement error, selection, or causal assumptions.

## When Sensitivity Is Material

If plausible priors change a decision or core claim:

- report the dependence prominently;
- seek stronger data or external evidence;
- improve the observation or structural model;
- use decision analysis to quantify the value of information;
- preserve multiple scenarios rather than averaging away a contested assumption;
- avoid presenting a single posterior as the unique evidence-based answer.
