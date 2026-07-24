# Bayesian Model Card Schema

## Required Top-Level Fields

The rendering utility requires these JSON keys:

```json
{
  "title": "Model name",
  "version": "1.0.0",
  "status": "development",
  "owners": ["Team or role"],
  "intended_use": "Decision or prediction supported",
  "target": "Estimand or predictive target"
}
```

Values can be strings, numbers, booleans, lists, or nested objects. Prefer strings for narrative fields and arrays for enumerated limitations, owners, metrics, and prohibited uses.

## Recommended Fields

### Identity

- `title`
- `version`
- `status`
- `owners`
- `review_date`
- `model_artifact`
- `code_version`
- `environment`

### Use

- `intended_use`
- `prohibited_uses`
- `users`
- `decision_context`
- `target`
- `target_population`
- `prediction_horizon`

### Data

- `training_data`
- `validation_data`
- `data_provenance`
- `inclusion_exclusion`
- `missingness_measurement`
- `known_shifts`

### Model

- `model_structure`
- `likelihood`
- `priors`
- `observation_process`
- `assumptions`
- `software_versions`

### Validation

- `computational_diagnostics`
- `prior_predictive_checks`
- `posterior_predictive_checks`
- `out_of_sample_validation`
- `simulation_validation`
- `causal_identification`
- `sensitivity_analysis`
- `subgroup_analysis`

### Performance and Uncertainty

- `primary_metrics`
- `calibration`
- `interval_coverage`
- `decision_metrics`
- `monte_carlo_error`
- `model_uncertainty`

### Limitations and Governance

- `limitations`
- `ethical_safety_considerations`
- `privacy_security`
- `monitoring`
- `update_triggers`
- `rollback`
- `approvals`
- `change_history`

## Content Rules

- Define every metric and evaluation population.
- State whether results are in-sample, held-out, temporal, external, or simulated.
- Preserve diagnostic failures and unsupported groups.
- Distinguish latent target from recorded outcome.
- Name priors and causal assumptions that materially affect conclusions.
- State prohibited uses concretely.
- Link or identify reproducible artifacts instead of pasting large logs.
- Assign an owner and review date to operational controls.

## Rendering Behavior

The script preserves input order after required identity fields, converts snake-case keys to headings, renders arrays as bullets, and renders nested objects recursively. It does not infer missing evidence, validate statistical claims, or redact secrets. Do not include confidential values, credentials, or personal data in the JSON.
