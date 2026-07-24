# Monitoring Bayesian Models

## Monitoring Layers

Monitor the system in dependency order:

1. data availability and schema;
2. input validity and population coverage;
3. scoring health and latency;
4. predictive distributions and uncertainty;
5. actions and resource use;
6. outcomes after maturation;
7. calibration, loss, and subgroup performance;
8. structural assumptions and external regime changes.

An outcome metric can look stable while an upstream pipeline is silently excluding cases.

## Data Quality Metrics

Track by source and relevant subgroup:

- row or event count;
- freshness and lag;
- missingness and sentinel rates;
- support and unit violations;
- duplicate and join failure rates;
- category novelty;
- distribution quantiles;
- target eligibility and exclusion rates;
- measurement-device or policy version.

Use contractual checks for invalid inputs and statistical summaries for distribution changes.

## Covariate Shift

Compare production inputs with the relevant reference period using:

- univariate distribution distances;
- standardized mean or quantile differences;
- categorical frequency changes;
- multivariate domain-classification or density-ratio approaches;
- support and extrapolation diagnostics;
- target-population reweighting summaries.

Thresholds must account for volume, seasonality, repeated testing, and operational relevance. Drift can be benign, harmful, or expected.

## Prediction and Uncertainty Shift

Track:

- predictive mean or probability distribution;
- interval width and tail probabilities;
- new-group or out-of-domain rate;
- posterior-draw dispersion for decision quantities;
- selected action frequency;
- fraction near decision thresholds;
- fallback and abstention rates.

A sudden narrowing of uncertainty can be a defect, not an improvement, especially after a missing variance component or prediction-path change.

## Outcome Maturity

Define when an outcome is observable and final. Track cohorts by prediction time and maturity date. Separate:

- not yet observable;
- missing after maturity;
- censored;
- delayed but expected;
- invalid or revised;
- observed final outcome.

Never score immature outcomes as negatives or omit them without denominators. Model delay or censoring when it depends on risk.

## Prequential Evaluation

Score each outcome using the predictive distribution issued before that outcome became available. Retain prediction timestamp, artifact version, covariate snapshot, horizon, and later outcome revision.

Prequential evaluation avoids re-scoring history with a model that already conditioned on those outcomes. Separate frozen retrospective benchmarks from live prequential metrics.

## Proper and Operational Scores

### Binary outcomes

- Brier score;
- log loss with transparent numerical clipping;
- calibration intercept and slope;
- reliability curve;
- decision loss at operational thresholds.

### Continuous outcomes

- log predictive density when a full density is available;
- MAE and RMSE for point prediction;
- predictive interval coverage and width;
- quantile or asymmetric loss;
- tail-event performance.

### Count, survival, and structured outcomes

Use likelihood-appropriate proper scores, time-dependent evaluation, censoring-aware methods, and aggregation matching the decision unit.

## Calibration and Sharpness

Calibration asks whether events or outcomes occur at advertised probabilities or intervals. Sharpness asks how concentrated predictions are. Evaluate them together: very wide intervals can cover well but provide little value.

Report uncertainty in calibration metrics, especially for rare events and small subgroups. Avoid bins with unstable or hidden denominators.

## Subgroup Monitoring

Choose groups based on intended use, known risk, legal or ethical requirements, and model structure. Track data quality, support, calibration, loss, interval coverage, action rates, and harm.

Correct for repeated monitoring where formal alert rates matter, but do not use multiplicity to suppress clear safety signals. Protect privacy and avoid publishing identifiable small cells.

## Alert Design

For every alert define:

- metric and denominator;
- reference window and seasonality adjustment;
- warning and critical thresholds;
- persistence rule;
- minimum sample size or maturity;
- owner and response time;
- diagnostic drill-down;
- allowed actions;
- resolution and audit trail.

Use several signals to diagnose cause. One drift threshold should not automatically trigger an unreviewed refit.
