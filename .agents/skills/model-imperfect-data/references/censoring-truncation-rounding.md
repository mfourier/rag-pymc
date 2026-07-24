# Censoring, Truncation, Detection, and Coarsening

## Censoring

A censored unit remains in the dataset, but its exact value is only known relative to a limit or interval.

- **right censoring:** value exceeds a known threshold;
- **left censoring:** value is below a known threshold;
- **interval censoring:** value lies between bounds;
- **administrative censoring:** observation ends at a design-defined time;
- **informative censoring:** the censoring process depends on unobserved target behavior after conditioning.

The likelihood contribution is a density for exact observations and an integrated probability over the censored region for coarsened observations.

## Truncation

Truncated units outside an inclusion region are absent from the observed sample. The observed-data likelihood is conditioned on inclusion and requires the appropriate normalization. Examples include:

- only claims above a threshold entering a database;
- samples restricted to detected objects;
- survival cohorts including only those alive at enrollment;
- publications selected by an outcome-dependent rule.

Replacing truncation with censoring incorrectly treats unseen units as known to exist in the sample.

## Detection Limits

Values below or above a device limit may be:

- recorded as a limit symbol;
- absent;
- rounded to the limit;
- detected probabilistically near the threshold;
- subject to batch-specific limits.

Determine the actual laboratory or sensor pipeline. A constant substitution such as half the detection limit distorts distributions and understates uncertainty.

## Rounding

If a continuous latent value is rounded to a grid, an observed value represents an interval. For nearest-unit rounding, a record `y` typically corresponds to latent values in `[y - 0.5, y + 0.5)`, adjusted at boundaries. Integrate the latent distribution over that interval or explicitly model the rounding mechanism.

Rounding can create ties that are expected rather than evidence of discrete latent structure.

## Heaping and Digit Preference

Heaping occurs when respondents or systems preferentially record multiples such as 5, 10, or 100. A model may include:

- probability of exact versus heaped reporting;
- heap size or preferred digits;
- dependence on magnitude, recall interval, group, or respondent;
- asymmetric rounding or threshold effects.

Simple rounding models may not capture recall and reporting behavior.

## Interval-Observed Covariates

Age bands, income brackets, and spatial bins should not automatically be replaced by midpoints. Model the latent value within each interval using population information and propagate uncertainty into the outcome model. Open-ended intervals need defensible tail assumptions.

## Event Times and Competing Risks

For survival or event-history data, distinguish:

- right and interval censoring;
- left truncation or delayed entry;
- competing events;
- recurrent events;
- informative dropout;
- time-dependent observation.

A censored event time is not a zero event. The risk set and time origin must match the estimand.

## Identification and Checks

Check:

- counts at limits and heaping points;
- censoring and inclusion rates by covariates and group;
- batch- or time-specific thresholds;
- distribution immediately around detection limits;
- predicted exact, censored, and truncated counts;
- sensitivity to latent tail assumptions;
- posterior mass near hard boundaries;
- external totals for units omitted by truncation.

When little information exists beyond a censoring boundary, posterior tail behavior may be driven by the likelihood family and prior. Report this explicitly.

## Common Mistakes

- substituting a limit and using an ordinary continuous likelihood;
- discarding censored units;
- failing to condition a truncated likelihood on inclusion;
- assuming administrative censoring is noninformative without checking design and follow-up;
- using interval midpoints as error-free values;
- interpreting heaping as multimodality in the latent process;
- ignoring time-varying limits or inclusion rules.
