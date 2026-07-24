# Bayesian Study Design Workflow

## 1. Define the Scientific and Operational Target

Specify:

- estimand, predictive target, or decision;
- target population and recruitment frame;
- unit of intervention and unit of observation;
- follow-up and prediction horizon;
- practical effect scale and harmful outcomes;
- available budget, time, sites, instruments, and personnel;
- acceptable probability and consequence of wrong actions.

A design cannot be optimized until the objective is explicit. Estimating a population mean, detecting a clinically meaningful effect, predicting rare outcomes, and selecting an action require different criteria.

## 2. Distinguish Design and Analysis Models

The **analysis model** is the planned model for observed data. The **design generator** represents uncertainty about how data may actually arise. They may differ deliberately to test robustness.

The **analysis prior** supports posterior inference. The **design-stage distribution** averages operating characteristics over plausible states. It may use external evidence, skeptical scenarios, or a mixture of regimes. Document overlaps and differences.

## 3. Define Candidate Designs

For each candidate, record:

- total sample size and allocation;
- number and size of clusters or groups;
- stratification or blocking;
- recruitment and dropout assumptions;
- measurement times and instruments;
- validation or gold-standard subsample;
- adaptive looks and maximum sample size;
- treatment or action constraints;
- fixed and variable costs;
- analysis latency and computational budget.

Include operationally feasible alternatives, not only a mathematical optimum.

## 4. Simulate the Full Data Path

Each replication should represent:

1. true parameters or states;
2. population and recruitment;
3. treatment assignment or exposure;
4. latent outcome process;
5. measurement, missingness, censoring, and adherence;
6. interim data availability and delays;
7. analysis or approximation;
8. diagnostic and fit status;
9. posterior target and decision;
10. duration, resource use, and utility.

Simplified calculations are useful for screening many designs, but finalist designs should be tested with the planned analysis and realistic observation process.

## 5. Define Operating Characteristics

Choose metrics tied to the objective:

- assurance or probability of meeting a posterior criterion;
- expected interval width or probability width is below a target;
- expected posterior variance or entropy;
- predictive calibration, log score, Brier score, or tail-event loss;
- correct action probability;
- expected utility, expected loss, or regret;
- type and direction of harmful decisions;
- early stopping probability by true regime;
- expected and maximum sample size;
- study duration and cost;
- fit and pipeline failure rate.

Report metric distributions, not only averages, when tail risk matters.

## 6. Plan Simulation Precision

For each critical proportion, choose replications so its Monte Carlo standard error is small relative to design differences. For expected utility or cost, estimate the standard error from replicate values and consider common random numbers across candidate designs to reduce noise in paired comparisons.

If using common random numbers, preserve the same underlying state across comparable designs while keeping within-design stochastic processes valid. Document dependence when computing uncertainty.

## 7. Compare Designs

Use one of:

- constrained optimization: maximize utility subject to budget and safety;
- Pareto frontier: precision, cost, duration, and risk;
- dominance screening: remove designs worse on all important criteria;
- regret analysis across scenarios;
- robust selection under alternative design-stage distributions.

A tiny estimated advantage within simulation error does not establish a unique best design.

## 8. Stress-Test Assumptions

Vary:

- effect size and heterogeneity;
- baseline risk or prevalence;
- within- and between-group variation;
- intracluster correlation;
- recruitment, dropout, adherence, and contamination;
- measurement error and test performance;
- missingness and delayed outcomes;
- prior strength and conflict;
- likelihood tails and nonlinearities;
- analysis or infrastructure failure.

Report which assumptions change the selected design.

## 9. Freeze and Reproduce

Version:

- scenario registry and weights;
- generator and analysis code;
- priors and hyperparameters;
- decision and stopping rules;
- seeds and replication identifiers;
- software environment;
- summary code and selection criterion;
- deviations made after study start.

Prospective locking prevents simulation choices from following preferred conclusions.
