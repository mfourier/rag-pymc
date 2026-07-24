#!/usr/bin/env python3
"""Summarize scenario-by-quantity recovery from long-form CSV results."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean, stdev
from typing import Any

REQUIRED_COLUMNS = {"scenario", "replicate", "quantity", "true", "estimate", "lower", "upper"}
SUCCESS_VALUES = {"", "ok", "success", "succeeded", "complete", "completed"}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Long-form recovery CSV")
    parser.add_argument("--output", default="-", help="JSON path or '-' for stdout")
    return parser.parse_args()


def parse_finite(row: dict[str, str], name: str) -> float:
    """Read one required finite numeric value from a CSV row."""
    value = float(row[name])
    if not math.isfinite(value):
        raise ValueError(f"{name} is not finite")
    return value


def standard_error(values: list[float]) -> float | None:
    """Calculate an ordinary Monte Carlo standard error."""
    return stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Summarize recovery and failures for one scenario and quantity."""
    attempted = len(rows)
    failures: dict[str, int] = defaultdict(int)
    errors: list[float] = []
    absolute_errors: list[float] = []
    squared_errors: list[float] = []
    coverages: list[float] = []
    widths: list[float] = []

    for row in rows:
        status = row.get("status", "").strip().lower()
        if status not in SUCCESS_VALUES:
            failures[status or "unspecified_failure"] += 1
            continue
        try:
            truth = parse_finite(row, "true")
            estimate = parse_finite(row, "estimate")
            lower = parse_finite(row, "lower")
            upper = parse_finite(row, "upper")
            if lower > upper:
                raise ValueError("lower exceeds upper")
        except (TypeError, ValueError, KeyError) as error:
            failures[f"invalid_success_row: {error}"] += 1
            continue

        estimation_error = estimate - truth
        errors.append(estimation_error)
        absolute_errors.append(abs(estimation_error))
        squared_errors.append(estimation_error**2)
        coverages.append(1.0 if lower <= truth <= upper else 0.0)
        widths.append(upper - lower)

    successful = len(errors)
    result: dict[str, Any] = {
        "attempted": attempted,
        "successful": successful,
        "failed_or_invalid": attempted - successful,
        "failure_rate": (attempted - successful) / attempted if attempted else None,
        "failure_reasons": dict(sorted(failures.items())),
    }
    if not successful:
        result["metrics"] = None
        return result

    coverage = fmean(coverages)
    result["metrics"] = {
        "bias": fmean(errors),
        "bias_mcse": standard_error(errors),
        "mae": fmean(absolute_errors),
        "rmse": math.sqrt(fmean(squared_errors)),
        "empirical_coverage": coverage,
        "coverage_binomial_mcse": math.sqrt(coverage * (1 - coverage) / successful),
        "mean_interval_width": fmean(widths),
    }
    return result


def main() -> int:
    """Run the recovery-summary command."""
    args = parse_args()
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with args.input.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise SystemExit(f"missing required CSV columns: {missing}")
        for row in reader:
            grouped[(row["scenario"], row["quantity"])].append(row)

    groups = [
        {"scenario": scenario, "quantity": quantity, **summarize(rows)}
        for (scenario, quantity), rows in sorted(grouped.items())
    ]
    report = {
        "input": str(args.input.resolve()),
        "groups": groups,
        "interpretation_note": (
            "Metrics are conditional on the declared scenarios. Failed and invalid fits remain "
            "in attempted counts and are excluded only from numerical recovery metrics."
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
