# Prior Elicitation Workflow

## 1. Prepare the Session

Define the model context before asking for numbers:

- target population and time horizon;
- quantity being elicited and its units;
- conditioning information available to the expert;
- whether the quantity describes variation, uncertainty, or both;
- reference group, baseline covariates, and link scale;
- the consequences of overly narrow or overly broad priors.

Use more than one expert when the decision is consequential. Decide in advance whether judgments will be pooled, modeled hierarchically, represented as mixtures, or retained as separate sensitivity scenarios.

## 2. Reduce Cognitive Burden

Prefer concrete observable questions:

- “Out of 100 comparable cases, how many would you expect?”
- “What value would be surprisingly high but still plausible?”
- “How often would this rate double relative to baseline?”
- “For two randomly selected groups, how different could their averages be?”

Avoid starting with requests for means and standard deviations of latent coefficients. Translate observable judgments back to parameters after the session.

## 3. Establish Anchors

Collect at least:

- a central value such as median or most plausible range;
- a lower and upper quantile with stated probability;
- hard physical bounds, if genuine;
- direction or ordering constraints, if scientifically justified;
- cases the expert considers impossible versus merely rare.

Do not convert a practical plausibility bound into zero probability without justification. Bounded distributions can create sharp geometry and overconfidence.

## 4. Use Quantiles Carefully

Ask for one quantile at a time and restate its probability meaning. For example:

> Conditional on the stated context, you believe there is a 90% probability the rate lies below this value.

Check that elicited quantiles are ordered and coherent. If they are not, revisit the scenarios rather than mechanically fitting a distribution.

## 5. Elicit Dependence

Marginal priors alone rarely define the intended joint knowledge. Ask:

- which parameters should move together;
- whether extreme values can occur simultaneously;
- whether totals constrain components;
- whether effects are exchangeable across groups;
- whether monotonicity, ordering, or compositional constraints apply;
- how a baseline changes the plausible scale of an effect.

Use simulated joint draws and observable consequences to validate the dependence structure.

## 6. Handle Expert Disagreement

First determine whether disagreement arises from:

- different conditioning information;
- different target populations or horizons;
- ambiguity in definitions or units;
- genuine scientific disagreement;
- different tolerance for rare events.

Resolve definition problems before pooling. Preserve genuine disagreement through separate scenarios, weighted mixtures with documented weights, or a hierarchical expert model. Do not average incompatible quantities.

## 7. Debias the Process

Mitigate common elicitation biases:

- ask for extremes before revealing external anchors;
- use several plausible scenarios;
- ask experts to generate reasons their central judgment could fail;
- distinguish “never observed” from “impossible”;
- randomize or balance presentation of candidate ranges;
- repeat key questions in a different representation;
- provide feedback using simulated implications.

The facilitator should not steer experts toward a convenient distribution family.

## 8. Validate with Feedback

Return three views to the expert:

1. the fitted marginal distribution;
2. joint draws for related quantities;
3. prior predictive outcomes on familiar scales.

Ask which simulated cases are implausible and why. Revise the elicited statements or distribution only with a recorded rationale.

## 9. Document Provenance

Record:

- expert role and relevant experience;
- date and information set;
- precise wording of every question;
- raw judgments before translation;
- facilitation aids and anchors shown;
- disagreements and revisions;
- pooling or weighting rule;
- conflicts of interest and confidentiality constraints.

External datasets used to construct an empirical prior must be versioned and checked for population or measurement mismatch.

## 10. Separate Prior Roles

### Domain-informed priors

Represent external substantive knowledge and require provenance.

### Regularizing priors

Stabilize weakly identified models and suppress implausible complexity. Their implications still require justification.

### Structural priors

Encode monotonicity, exchangeability, smoothness, sparsity, or conservation constraints. These can be highly informative even when marginal scales look broad.

### Reference priors

Provide a declared baseline analysis. They are parameterization-dependent and not synonymous with absence of information.

### Sensitivity priors

Probe assumptions or represent alternative expert views. They should be plausible enough that differences are scientifically interpretable.
