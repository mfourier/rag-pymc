# Causal Estimands and Identification

## Define the Intervention

Specify:

- treatment variable and allowed values;
- intervention that sets or modifies treatment;
- timing, duration, adherence, and treatment versions;
- comparator or reference policy;
- outcome and measurement horizon;
- population and unit of intervention;
- interference or spillover structure.

“Effect of X on Y” is incomplete when X has multiple versions or cannot be intervened on as stated.

## Potential Outcomes

Let `Y(a)` denote the outcome that would occur under intervention `A = a`.

Common estimands include:

### Average treatment effect

```text
ATE = E[Y(1) - Y(0)]
```

in a declared target population.

### Average treatment effect among the treated

```text
ATT = E[Y(1) - Y(0) | A = 1]
```

### Conditional average treatment effect

```text
CATE(x) = E[Y(1) - Y(0) | X = x]
```

### Policy value

```text
E[Y(d(X))]
```

for a treatment rule `d`. Define utility rather than outcome alone when actions have costs or harms.

Effects can be expressed as differences, ratios, odds ratios, survival contrasts, quantiles, or utility. Nonlinear scales yield different averages; select the scale before analysis.

## Core Identification Assumptions

### Consistency

For units receiving `A = a`, observed outcome equals the corresponding potential outcome, subject to well-defined treatment versions and measurement.

### Conditional exchangeability

```text
Y(a) independent of A given X
```

for a sufficient pretreatment adjustment set `X`. Randomization can support exchangeability by design; observational analyses require substantive justification.

### Positivity

Every treatment needed for the estimand has positive probability within relevant covariate strata. Practical positivity problems create extrapolation even when theoretical probability is nonzero.

### No relevant interference or specified interference

One unit's outcome is unaffected by other units' treatment, or the exposure mapping and estimand explicitly represent spillovers.

### Measurement and observation assumptions

Treatment, outcome, covariates, selection, and censoring must be observed or modeled adequately for the identification claim.

## DAG Workflow

1. order variables in time;
2. include common causes before looking at associations;
3. include selection and measurement nodes when relevant;
4. identify backdoor paths;
5. find sufficient adjustment sets;
6. avoid conditioning on colliders and treatment descendants for total effects;
7. compare plausible alternative graphs;
8. record edges that are uncertain or contested.

A DAG encodes assumptions; data cannot generally select the correct causal graph without additional restrictions.

## Identification Functional

Under consistency, conditional exchangeability given `X`, and positivity, the g-formula identifies:

```text
E[Y(a)] = integral E[Y | A = a, X = x] p_target(x) dx
```

The target covariate distribution matters. For ATT, trial transport, or selected populations, the averaging distribution changes.

## Target-Trial Emulation

For longitudinal observational data, specify:

- eligibility criteria;
- treatment strategies;
- assignment time and time zero;
- follow-up;
- outcome;
- causal contrast;
- analysis plan.

Align eligibility, assignment, and follow-up to avoid immortal-time and selection biases. Address treatment switching, adherence, time-varying confounding, and censoring explicitly.

## Nonidentification and Partial Identification

If observed data and assumptions do not point-identify the estimand:

- report bounds under weaker assumptions;
- introduce an interpretable sensitivity parameter;
- seek validation or design information;
- redefine the intervention or target population;
- avoid presenting a prior-driven point estimate as data-identified.

Bayesian priors can express uncertainty over unidentified parameters, but posterior learning about them may be limited or absent. State that dependence.
