# Recovery Metrics and Interpretation

Let `theta_r` be the true target and `hat_theta_r` its estimate in successful replication `r`.

## Point-Recovery Metrics

### Bias

```text
mean(hat_theta_r - theta_r)
```

Bias identifies systematic direction but can cancel across heterogeneous scenarios. Report it by scenario and relevant parameter regime.

### Mean absolute error

```text
mean(abs(hat_theta_r - theta_r))
```

MAE is interpretable in the target unit and less dominated by rare large errors than RMSE.

### Root mean squared error

```text
sqrt(mean((hat_theta_r - theta_r)^2))
```

RMSE emphasizes large errors. Compare it only for quantities on the same scale or use a declared normalization.

### Relative error

Relative error can be useful for positive quantities far from zero. It is unstable near zero and should not replace absolute-scale summaries there.

## Interval Metrics

### Empirical coverage

For intervals `[L_r, U_r]`, coverage is the proportion satisfying:

```text
L_r <= theta_r <= U_r
```

Compare empirical coverage with nominal probability only under the stated repeated-simulation distribution. Report a binomial Monte Carlo standard error and failure denominator.

### Interval width

Mean or median `U_r - L_r` measures precision. Coverage without width can reward unhelpfully broad intervals; width without coverage can reward overconfidence.

### Boundary and tail coverage

Stratify coverage by true value, information level, and boundary proximity. Aggregate nominal coverage can hide poor performance in consequential regimes.

## Predictive Metrics

Choose metrics matching the data and action:

- log predictive density for full probabilistic accuracy;
- Brier score for binary probabilities;
- calibration curves or PIT diagnostics for predictive distributions;
- interval coverage and width;
- MAE or RMSE for point predictions when operationally relevant;
- tail-event recall or loss for rare high-consequence events.

No single score captures calibration, sharpness, and decision value.

## Decision Metrics

When the analysis selects an action, summarize:

- action selection probability by true regime;
- false-action and missed-action rates;
- expected utility or loss;
- expected regret relative to the best action under known simulated truth;
- probability of exceeding a harmful-loss threshold;
- resource cost and latency.

Define utility before examining favorable results.

## Fit and Pipeline Failures

Report:

- total attempted replications;
- generation failures;
- fit exceptions;
- nonconverged or diagnostically suspect fits;
- post-processing failures;
- successful fits used for numerical metrics;
- retries and final status.

Do not merge technical failure with inferential noncoverage. Both matter but imply different remediation.

## Monte Carlo Uncertainty of the Study

Simulation summaries are estimates. Report:

- standard error for bias from replicate errors;
- binomial standard error or interval for coverage and rates;
- bootstrap or repeated-batch uncertainty for MAE, RMSE, quantiles, and utility when needed;
- effective number of independent simulation units if replications share generated clusters or latent states.

Increasing MCMC draws within each fit reduces posterior Monte Carlo error; increasing simulation replications reduces uncertainty in the validation summary. They address different layers.

## Failure-Pattern Diagnostics

Inspect metric plots against:

- true target value;
- sample size and group count;
- signal-to-noise ratio;
- missingness or measurement-error intensity;
- prior-to-likelihood information balance;
- sampler diagnostics;
- covariate imbalance or extrapolation;
- scenario identifiers.

Patterns are usually more informative than one pooled average.

## Interpreting a Successful Exact-Model Study

Good recovery under a generator identical to the fitter supports implementation consistency and behavior under that model. It does not establish:

- realism of the data-generating assumptions;
- robustness to untested misspecification;
- causal identification;
- external validity;
- correctness of the utility function;
- absence of computational problems in larger or different datasets.

Pair exact-model recovery with predictive checks, real-data diagnostics, sensitivity analysis, and targeted misspecification experiments.
