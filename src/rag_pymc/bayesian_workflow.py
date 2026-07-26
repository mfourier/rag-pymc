"""Pure, reusable helpers for the educational Beta--Bernoulli example."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class AnalyticalPosterior:
    """Parameters and mean of the conjugate Beta posterior."""

    alpha: float
    beta: float
    mean: float


def generate_synthetic_data(
    *, n_observations: int, true_probability: float, seed: int
) -> npt.NDArray[np.int8]:
    """Generate deterministic binary outcomes with a local NumPy generator."""
    _validate_positive_integer(n_observations, "n_observations")
    _validate_probability(true_probability, "true_probability")
    _validate_seed(seed)
    generator = np.random.default_rng(seed)
    return generator.binomial(1, true_probability, size=n_observations).astype(np.int8)


def analytical_posterior(
    observations: npt.ArrayLike, *, prior_alpha: float, prior_beta: float
) -> AnalyticalPosterior:
    """Compute the exact conjugate posterior independently of PyMC sampling."""
    y = _validated_observations(observations)
    _validate_prior(prior_alpha, prior_beta)
    successes = int(y.sum())
    posterior_alpha = prior_alpha + successes
    posterior_beta = prior_beta + y.size - successes
    return AnalyticalPosterior(
        alpha=posterior_alpha,
        beta=posterior_beta,
        mean=posterior_alpha / (posterior_alpha + posterior_beta),
    )


def _validated_observations(observations: npt.ArrayLike) -> npt.NDArray[np.int8]:
    array = np.asarray(observations)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("observations must be a nonempty one-dimensional array")
    if not np.all((array == 0) | (array == 1)):
        raise ValueError("observations must contain only binary values 0 and 1")
    return array.astype(np.int8, copy=False)


def _validate_probability(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite probability")
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1 inclusive")


def _validate_prior(alpha: float, beta: float) -> None:
    for name, value in (("prior_alpha", alpha), ("prior_beta", beta)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be finite and strictly positive")
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and strictly positive")


def _validate_seed(seed: int) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")


def _validate_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
