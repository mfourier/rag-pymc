# Assurance, Precision, and Information Criteria

## Assurance

Assurance is the design-stage probability that a future study will meet a specified success criterion, averaging over uncertainty in data-generating states and future data:

```text
P_design(success) = integral P(success | theta, design) p_design(theta) d theta
```

The exact integration can include nuisance parameters, recruitment, missingness, and observation error. State the design-stage distribution and success rule whenever reporting assurance.

## Conditional Operating Curves

Alongside assurance, report success probability conditional on interpretable regimes such as effect size, prevalence, heterogeneity, or measurement quality. An average can hide poor performance in high-consequence regions.

Avoid calling assurance classical power. Power usually conditions on a fixed parameter value and a frequentist rejection rule; assurance averages a declared Bayesian criterion over design-stage uncertainty.

## Posterior-Probability Criteria

Examples include:

```text
P(theta > clinically_relevant_value | data) > decision_threshold
```

or

```text
P(theta is inside equivalence_region | data) > threshold
```

Define the practical threshold and posterior threshold separately. Evaluate false and missed actions across true regimes, not only the average probability of success.

## Expected Precision

Possible criteria include:

- expected credible-interval width;
- probability interval width is below a target;
- expected posterior standard deviation;
- expected entropy or information gain;
- precision of a predictive contrast;
- precision for a population aggregate after poststratification.

Precision must be measured for the actual estimand. Narrow intervals can still be biased under misspecification or selection.

## Interval Exclusion and Equivalence

Designs can target the probability that a credible interval excludes a null or lies within a region of practical equivalence. State:

- interval probability and construction;
- null or ROPE definition;
- whether the criterion supports discovery, equivalence, noninferiority, or decision;
- behavior at boundary values;
- multiplicity and subgroup policy.

An interval criterion is a decision rule only after consequences and thresholds are declared.

## Predictive Design Criteria

For prediction, use expected out-of-sample measures aligned with deployment:

- log predictive density;
- Brier score;
- calibration and sharpness;
- interval coverage and width;
- rare-event or tail loss;
- subgroup performance;
- value of collecting predictors or repeated measurements.

Simulate the future covariate distribution and any shift that is part of the intended use.

## Expected Value of Perfect Information

EVPI compares the expected utility with perfect knowledge of the uncertain state to the best action under current information:

```text
EVPI = E_theta[max_a U(a, theta)] - max_a E_theta[U(a, theta)]
```

It is an upper bound on the value of additional information under the chosen model and utility.

## Expected Value of Sample Information

EVSI compares expected utility after a proposed study with current expected utility:

```text
EVSI = E_y[max_a E[U(a, theta) | y]] - max_a E_theta[U(a, theta)]
```

Subtract expected study and implementation cost for net value. Include timing when delayed information reduces value.

## Sensitivity and Robustness

Assurance, EVPI, and EVSI are sensitive to:

- design-stage prior;
- utility or loss function;
- analysis model;
- observation process;
- implementation and adoption assumptions;
- future population distribution.

Report alternative plausible inputs. A precise simulation under an arbitrary utility is not a reliable decision analysis.
