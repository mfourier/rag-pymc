# Bayesian Visualization and Language Guide

## Match the Graphic to the Quantity

### Posterior distributions

Use density, interval, dot-and-interval, or half-eye plots for parameters and contrasts. Label the interval probability and scale. Show a practical threshold or ROPE only when substantively defined.

### Posterior predictions

Overlay observed data with replicated distributions, intervals, or predictive summaries. Distinguish latent mean from new observed outcomes. Use the same aggregation in observed and predicted summaries.

### Calibration

Use reliability curves, PIT or rank diagnostics appropriate to the predictive object, coverage-by-level plots, and sharpness summaries. Include sample size or uncertainty by bin.

### Hierarchies

Use partial-pooling plots ordered by a meaningful quantity, with group sample size and uncertainty. Avoid interpreting noisy rank order as a stable league table.

### Time and space

Show observed values, latent trends, predictive intervals, and forecast boundaries distinctly. Preserve uncertainty and avoid rainbow scales that imply false ordering.

### Model comparison

Plot ELPD differences with uncertainty and flag influential or high Pareto-k cases. Do not use rank alone.

## Visual Integrity

- use common scales for honest comparisons;
- show zero or a practical reference when relevant;
- avoid truncated axes that magnify trivial changes without annotation;
- display raw data or sufficient context where privacy permits;
- distinguish interval types through labels, not color alone;
- use accessible palettes and direct labels;
- show denominator and uncertainty for subgroup rates;
- avoid visual precision beyond the underlying data and MCSE.

## Language for Credible Intervals

Preferred:

> Conditional on the model and observed data, 90% of posterior mass for the contrast lies between L and U.

Concise when context is already established:

> The 90% credible interval is [L, U].

Avoid:

> There is a 90% probability that repeated intervals contain the fixed parameter.

That is confidence-interval language.

## Language for Predictions

Preferred:

> For a new unit from the stated population, the posterior predictive median is M and the 90% predictive interval is [L, U], conditional on the future covariates and observation process described above.

State whether the interval includes new-group variation, residual outcome variation, and measurement error.

## Language for Posterior Probabilities

Preferred:

> The posterior probability that the effect exceeds the practical threshold is 0.82 under the specified model and prior.

Avoid calling this a p-value or long-run error rate. A posterior probability can inform a decision but is not itself a utility function.

## Language for Diagnostics

Preferred:

> The key quantities had R-hat near 1, adequate bulk and tail ESS for the reported precision, and MCSE small relative to posterior SD. No divergent transitions were recorded in this run. These diagnostics support the numerical summary but do not assess structural model adequacy.

When diagnostics are poor, state which quantities may be unreliable and what remediation is required.

## Language for Predictive Checks

Preferred:

> Replicated data reproduced the central distribution but systematically underrepresented zero counts and upper-tail events, indicating that the observation model is inadequate for those features.

Avoid “the model fits” without naming features and scope.

## Language for Model Comparison

Preferred:

> Model A had a higher estimated ELPD than Model B, but the difference was small relative to its uncertainty. Several observations had elevated Pareto-k values, so the ranking is not decisive without further validation.

Avoid “Model A is true” or “wins” based on a predictive score.

## Language for Causal Claims

Randomized design with remaining caveats:

> Under the randomized assignment and stated assumptions about missing outcomes and adherence, the posterior distribution for the intention-to-treat effect indicates...

Observational analysis:

> Under the stated exchangeability, positivity, consistency, measurement, and selection assumptions, the standardized causal contrast is...

If those assumptions are not justified, use associational language.

## Practical Relevance

Report:

- absolute scale and baseline risk;
- relative scale when useful;
- practical threshold source;
- distribution of individual or group outcomes;
- probability of meaningful benefit and harm;
- decision consequence.

A narrow interval around a negligible effect and a wide interval spanning high benefit and harm require different narratives.

## Decimal Precision

Choose digits using:

- measurement resolution;
- posterior MCSE;
- natural variability;
- practical threshold resolution;
- audience needs.

Keep more digits in machine-readable artifacts than in narrative text. Do not report three decimals when the decision changes only at whole units.
