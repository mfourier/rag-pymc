# Updating and Rolling Back Bayesian Models

## Types of Change

Classify every proposed update:

- new observations under the same data-generating and measurement process;
- revised labels or backfilled outcomes;
- new population or covariate support;
- changed measurement, policy, intervention, or selection process;
- changed prior, likelihood, hierarchy, or target;
- code, dependency, infrastructure, or output-schema change;
- changed decision threshold or utility.

Only the first category is a straightforward candidate for conditioning under an unchanged model. Other changes may require redesign, revalidation, or a new model lineage.

## Sequential Bayesian Updating

To update a posterior with new data:

- verify that new data were not included previously;
- retain the old data boundary and artifact hash;
- ensure likelihood factorization and independence assumptions support the update;
- preserve sufficient dependence rather than replacing a joint posterior with independent marginal summaries;
- confirm population, measurement, and preprocessing consistency;
- rerun diagnostics and predictive validation;
- compare with a clean fit to combined data when feasible.

Using posterior samples as a prior can require density approximation and may distort tails or dependence. Validate the approximation on operational target quantities.

## Update Triggers

Triggers can include:

- sufficient mature new outcomes;
- calibration or loss degradation;
- population or measurement shift;
- unacceptable uncertainty near decisions;
- prior-data conflict;
- known model limitation becoming operationally relevant;
- dependency or security changes;
- scheduled governance review.

A trigger starts review; it need not authorize automatic deployment.

## Validation Gates

Before promotion, require:

1. data and provenance checks;
2. reproducible fit and environment;
3. computational diagnostics;
4. prior and posterior predictive checks;
5. time-ordered or external validation;
6. comparison with the incumbent on identical mature cohorts;
7. subgroup and tail-risk analysis;
8. decision utility or loss evaluation;
9. shadow or canary behavior when appropriate;
10. signed approval and rollback readiness.

Evaluate whether improvements exceed uncertainty and operational cost. Do not promote solely because average score improved on a reused test set.

## Recalibration

Probability or interval recalibration can be lower risk than full refitting when ranking remains useful but calibration drifts. Still version:

- calibration population and period;
- transformation and uncertainty;
- effect on subgroups and decisions;
- relation to the original posterior semantics;
- expiry and review trigger.

Recalibration can mask structural change. Diagnose the source before relying on it.

## Champion, Challenger, and Shadow Evaluation

Run new artifacts without changing decisions when feasible. Compare predictions on the same timestamped inputs and mature outcomes. Record disagreement, uncertainty, action changes, and failure behavior.

Account for selection feedback: outcomes may only be observed under actions chosen by the incumbent. Off-policy evaluation requires explicit causal assumptions.

## Rollback Plan

Maintain:

- last known good artifact and environment;
- compatible input/output schema;
- decision-rule version;
- rollback command or release procedure;
- data migration reversibility;
- smoke tests after rollback;
- owners and communication path;
- affected-prediction and decision audit.

Rollback can restore technical behavior but cannot undo actions already taken. Define remediation for affected units.

## Incident Classification

Separate:

- upstream data incident;
- scoring service incident;
- artifact or dependency corruption;
- statistical performance degradation;
- population or policy regime change;
- governance or prohibited-use breach;
- privacy or security incident.

This determines whether to repair data, fail closed, recalibrate, refit, redefine the model, or stop the use.

## Change Log

For every release record:

- previous and new version;
- reason and trigger;
- data boundary;
- model and prior changes;
- validation evidence;
- expected prediction and action changes;
- approvers;
- release time;
- rollback state;
- post-release review result.
