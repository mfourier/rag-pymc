# Decision and Sequential Bayesian Design

## Decision Structure

Define:

- available actions;
- uncertain states and outcomes;
- utility or loss for each action-state combination;
- constraints and irreversible harms;
- who bears costs and benefits;
- timing and discounting;
- posterior information available when acting.

Choose the action maximizing posterior expected utility or minimizing posterior expected loss, subject to constraints. A posterior probability threshold is a compressed loss function; make its consequences explicit.

## Sequential Looks

At each planned look define possible actions:

- continue unchanged;
- stop for benefit or adoption;
- stop for harm;
- stop for futility;
- modify allocation, measurement, or recruitment;
- collect a targeted validation sample.

The rule must specify data available at the look, lagged outcomes, diagnostic requirements, and maximum resource limits.

## Simulate the Entire Path

For every replication:

1. generate the underlying state and stream of observations;
2. reveal only data available by each look;
3. fit or update the planned model;
4. evaluate diagnostics and decision quantities;
5. apply exactly one prespecified action;
6. propagate adaptations to future enrollment or measurement;
7. record stopping time, action, outcomes, utility, and cost.

Evaluating only the final analysis misses optional stopping behavior, early harm, expected sample size, and selection induced by adaptation.

## Bayesian Optional Stopping

Bayesian updating can be coherent under stopping rules when the likelihood and prior properly represent the data-generating and sampling process. This does not make arbitrary data-dependent behavior harmless. Operational bias, unreported looks, changing measurements, selective reporting, model misspecification, and utility-free thresholds still matter.

Document every planned and unplanned look.

## Futility and Predictive Probability

Predictive probability can summarize the chance a study will satisfy a final criterion after future data. Define:

- future sample size or recruitment distribution;
- outcome delays and missingness;
- final success rule;
- posterior predictive integration;
- futility threshold and consequences.

Low predictive probability can justify stopping only relative to cost, harm, and the value of information.

## Adaptive Allocation

Response-adaptive allocation can improve participant benefit or learning under some regimes but can create imbalance, delay sensitivity, drift vulnerability, and operational complexity. Simulate:

- early random variation;
- delayed outcomes;
- changing baseline risk;
- subgroup heterogeneity;
- allocation floors and ceilings;
- inferential and logistical failures.

Retain enough exploration to identify alternatives when required by the decision objective.

## Multiplicity and Selection

Hierarchical priors can partially pool many outcomes or subgroups, but multiplicity is not solved by vocabulary alone. Define:

- which claims or actions are jointly considered;
- selection rule for reporting or acting;
- loss from false and missed selections;
- posterior quantities after selection;
- confirmatory versus exploratory status.

Simulate the full selection mechanism. Report subgroup effects with shrinkage, uncertainty, and selection context.

## Safety and Diagnostics

For consequential sequential decisions, define what happens when:

- computation fails or diagnostics are poor;
- data feeds are incomplete;
- eligibility or measurement changes;
- adverse outcomes are delayed;
- model predictions conflict with external safety monitoring;
- a threshold is crossed by negligible numerical margin.

Use conservative fallback actions and independent review where domain governance requires it.

## Reporting

Report operating characteristics by true regime:

- stop-for-benefit, harm, and futility probabilities;
- action accuracy and expected regret;
- expected and quantile sample size;
- calendar duration;
- subgroup allocation and outcome distribution;
- probability of diagnostic or operational failure;
- sensitivity to priors, utility, drift, and delay.
