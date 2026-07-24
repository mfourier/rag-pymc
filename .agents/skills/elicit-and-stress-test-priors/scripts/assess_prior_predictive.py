#!/usr/bin/env python3
"""Summarize prior-predictive CSV draws against declared JSON constraints."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Callable
from pathlib import Path
from statistics import fmean
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draws", type=Path, help="CSV with one numeric column per quantity")
    parser.add_argument("constraints", type=Path, help="JSON object keyed by CSV column")
    parser.add_argument("--output", default="-", help="JSON path or '-' for stdout")
    return parser.parse_args()


def quantile(values: list[float], probability: float) -> float:
    """Compute a linearly interpolated empirical quantile."""
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def load_draws(path: Path) -> tuple[dict[str, list[float]], dict[str, int]]:
    """Load finite numeric draws and count invalid cells by column."""
    values: dict[str, list[float]] = {}
    invalid: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("draw CSV has no header")
        values = {name: [] for name in reader.fieldnames}
        invalid = {name: 0 for name in reader.fieldnames}
        for row in reader:
            for name in reader.fieldnames:
                raw = row.get(name, "")
                try:
                    value = float(raw)
                except (TypeError, ValueError):
                    invalid[name] += 1
                    continue
                if math.isfinite(value):
                    values[name].append(value)
                else:
                    invalid[name] += 1
    return values, invalid


def validate_constraint(name: str, constraint: object) -> dict[str, float]:
    """Validate and normalize one quantity's constraint object."""
    if not isinstance(constraint, dict):
        raise ValueError(f"constraint for {name!r} must be a JSON object")
    allowed = {"hard_min", "hard_max", "plausible_min", "plausible_max"}
    unknown = set(constraint) - allowed
    if unknown:
        raise ValueError(f"unknown constraint keys for {name!r}: {sorted(unknown)}")
    result = {key: float(value) for key, value in constraint.items()}
    for lower, upper in (("hard_min", "hard_max"), ("plausible_min", "plausible_max")):
        if lower in result and upper in result and result[lower] > result[upper]:
            raise ValueError(f"{lower} exceeds {upper} for {name!r}")
    return result


def rate(values: list[float], predicate: Callable[[float], bool]) -> float | None:
    """Calculate the share of values satisfying a predicate."""
    return fmean(1.0 if predicate(value) else 0.0 for value in values) if values else None


def summarize(
    values: list[float], invalid_count: int, constraint: dict[str, float]
) -> dict[str, Any]:
    """Summarize draws and evaluate their declared constraints."""
    summary: dict[str, Any] = {
        "valid_draws": len(values),
        "invalid_or_missing_draws": invalid_count,
    }
    if not values:
        summary["error"] = "no valid numeric draws"
        return summary

    summary["distribution"] = {
        "min": min(values),
        "q01": quantile(values, 0.01),
        "q05": quantile(values, 0.05),
        "median": quantile(values, 0.50),
        "mean": fmean(values),
        "q95": quantile(values, 0.95),
        "q99": quantile(values, 0.99),
        "max": max(values),
    }
    checks: dict[str, Any] = {}
    if "hard_min" in constraint:
        checks["below_hard_min_rate"] = rate(values, lambda value: value < constraint["hard_min"])
    if "hard_max" in constraint:
        checks["above_hard_max_rate"] = rate(values, lambda value: value > constraint["hard_max"])
    if "plausible_min" in constraint or "plausible_max" in constraint:
        low = constraint.get("plausible_min", -math.inf)
        high = constraint.get("plausible_max", math.inf)
        checks["outside_central_plausibility_range_rate"] = rate(
            values, lambda value: value < low or value > high
        )
    summary["constraints"] = constraint
    summary["checks"] = checks
    return summary


def main() -> int:
    """Run the prior-predictive assessment command."""
    args = parse_args()
    raw_constraints = json.loads(args.constraints.read_text(encoding="utf-8"))
    if not isinstance(raw_constraints, dict):
        raise SystemExit("constraints JSON must be an object keyed by CSV column")

    draws, invalid = load_draws(args.draws)
    unknown = sorted(set(raw_constraints) - set(draws))
    if unknown:
        raise SystemExit(f"constraints reference missing CSV columns: {unknown}")

    quantities = {
        name: summarize(draws[name], invalid[name], validate_constraint(name, constraint))
        for name, constraint in raw_constraints.items()
    }
    report = {
        "draws_file": str(args.draws.resolve()),
        "constraints_file": str(args.constraints.resolve()),
        "quantities": quantities,
        "interpretation_note": (
            "Constraint rates describe prior-predictive implications; they are not automatic "
            "acceptance or rejection rules."
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    if args.output == "-":
        print(rendered)
    else:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
