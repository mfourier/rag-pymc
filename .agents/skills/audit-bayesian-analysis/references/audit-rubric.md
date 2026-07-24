# Bayesian Audit Rubric

## Contents

1. Finding structure
2. Severity scale
3. Evidence strength
4. Audit domains
5. Dependency-aware triage
6. Verification and closure

## 1. Finding Structure

Every finding should include:

- **ID and title:** stable, concise identifier;
- **domain:** target, data, model, prior, computation, prediction, validation, decision, reporting, or operations;
- **observation:** what was directly seen;
- **evidence:** file, line, artifact, metric, plot, or reproducible command;
- **interpretation:** why it may be problematic;
- **consequence:** what estimate, prediction, decision, or claim is at risk;
- **severity:** critical, high, medium, low, or informational;
- **confidence:** high, medium, or low confidence in the finding;
- **remediation:** the smallest credible corrective action;
- **verification:** evidence required to close the finding;
- **dependencies:** findings that must be resolved first.

Keep observation separate from interpretation. For example, “37 divergent transitions after tuning” is an observation; “the reported tail probability may be unreliable because the sampler did not explore the posterior geometry adequately” is an interpretation.

## 2. Severity Scale

### Critical

The result is unsafe or invalid for its intended use, or the analysis cannot be reproduced sufficiently to establish what was run. Examples include data leakage into a prospective prediction, an impossible likelihood support, a causal claim without a defensible identification strategy, or a decision implementation using the wrong outcome.

Recommended action: stop the affected use until corrected or explicitly accepted by an authorized owner.

### High

There is a material risk that central estimates, tail probabilities, predictions, or decisions are misleading. Examples include unresolved severe sampling pathologies, substantial unmodeled selection, weak identification hidden by strong priors, or a validation design that does not match deployment.

Recommended action: correct before publication, release, or consequential use.

### Medium

The issue can alter interpretation, calibration, uncertainty, or maintainability but does not clearly invalidate the main use. Examples include insufficient sensitivity analysis, poor tail ESS for a secondary quantity, or incomplete reporting of prior influence.

Recommended action: address in the current analysis cycle or explicitly document residual risk.

### Low

The issue has limited immediate consequence but improves clarity, robustness, or reproducibility. Examples include an unlabeled operational threshold or an avoidable hard-coded coordinate.

Recommended action: fix opportunistically and track if recurring.

### Informational

No defect is asserted. Record a strength, context, design choice, or future enhancement.

Severity describes consequence, not how easy the fix is. Confidence describes strength of evidence and must be reported separately.

## 3. Evidence Strength

Use the following hierarchy as a guide:

1. reproducible failure or exact artifact inconsistency;
2. repeated quantitative diagnostic across runs or data slices;
3. single quantitative diagnostic with known interpretation;
4. code-level risk supported by the model structure;
5. undocumented or unavailable evidence;
6. stylistic preference.

A low-threshold warning can justify investigation without justifying a high-severity conclusion. Conversely, a conceptual mismatch can be critical even when all computational diagnostics look good.

## 4. Audit Domains

### Target and estimand

- Is the target defined before results are interpreted?
- Does it match the decision and population?
- Are causal, descriptive, and predictive targets distinguished?
- Are transformations and aggregation levels explicit?

### Data process

- Is the sampling frame understood?
- Could selection, missingness, leakage, or time ordering distort the target?
- Are units, exclusions, duplicates, and preprocessing reproducible?
- Is the observation process represented when necessary?

### Generative model

- Are support, link functions, and dependence plausible?
- Are latent and observed quantities separated?
- Are exchangeability assumptions defensible?
- Are identifiability limitations acknowledged?

### Priors

- Are priors justified on an interpretable scale?
- Are joint prior implications plausible?
- Were prior predictive checks used?
- Is sensitivity concentrated on decision-relevant quantities?

### Computation

- Are multiple chains and sufficient post-tuning draws available?
- Are R-hat, bulk ESS, tail ESS, MCSE, divergences, tree depth, and warnings interpreted together?
- Do traces or rank plots reveal non-mixing?
- Was geometry repaired rather than hidden by extra draws?

### Predictive adequacy

- Do checks target scientific and operational failure modes?
- Are groups, tails, zeroes, extremes, time, and dependence represented?
- Are held-out or future predictions evaluated when required?
- Is calibration distinguished from sharpness and usefulness?

### Validation and robustness

- Can the implementation recover known simulated quantities?
- Is formal SBC used only with its required generative experiment?
- Are priors, likelihoods, exclusions, and observation assumptions stress-tested?
- Are influential observations and misspecification examined?

### Comparison and decision

- Does the comparison unit match future generalization?
- Are ELPD differences reported with uncertainty?
- Are Pareto-k diagnostics addressed?
- Are actions evaluated under an explicit loss or utility where consequential?

### Communication and operations

- Are uncertainty sources named correctly?
- Are assumptions and limitations visible near claims?
- Can every output be traced to a model and data version?
- Are monitoring, updates, and rollback defined for deployment?

## 5. Dependency-Aware Triage

Resolve upstream issues before downstream polishing:

1. target and data leakage;
2. observation process and model support;
3. identifiability and prior implications;
4. computation and implementation correctness;
5. predictive adequacy and validation;
6. comparison, decision, reporting, and deployment.

For example, do not optimize LOO performance while a target leakage finding remains unresolved. Do not interpret posterior predictive fit as evidence for causal identification.

## 6. Verification and Closure

A finding is closed only when its verification criterion is met. Valid closure evidence may include:

- a regression test reproducing the corrected calculation;
- a rerun with clean diagnostic evidence;
- a revised generative model plus targeted predictive checks;
- a sensitivity analysis showing the decision is robust;
- corrected documentation and traceable output;
- formal risk acceptance by the responsible owner when correction is not feasible.

Do not close a computational finding merely because a warning disappeared. Verify the affected quantities and downstream claims.
