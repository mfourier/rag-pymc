#!/usr/bin/env python3
"""Summarize design-simulation operating characteristics from CSV."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean, stdev
from typing import Any

REQUIRED = {"design", "replicate", "success"}
OK_STATUSES = {"", "ok", "success", "succeeded", "complete", "completed"}
TRUE_VALUES = {"1", "true", "yes", "y", "success"}
FALSE_VALUES = {"0", "false", "no", "n", "failure"}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Design-simulation CSV")
    parser.add_argument("--output", default="-", help="JSON path or '-' for stdout")
    return parser.parse_args()


def mean_and_mcse(values: list[float]) -> tuple[float | None, float | None]:
    """Return a mean and its ordinary Monte Carlo standard error."""
    if not values:
        return None, None
    return fmean(values), stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None


def finite_optional(row: dict[str, str], column: str) -> float | None:
    """Read an optional finite numeric value from a CSV row."""
    raw = row.get(column, "").strip()
    if not raw:
        return None
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"{column} is not finite")
    return value


def parse_success(raw: str) -> float:
    """Convert a supported success label to a binary float."""
    normalized = raw.strip().lower()
    if normalized in TRUE_VALUES:
        return 1.0
    if normalized in FALSE_VALUES:
        return 0.0
    raise ValueError(f"unrecognized success value: {raw!r}")


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Summarize operating characteristics for one candidate design."""
    attempted = len(rows)
    failures: dict[str, int] = defaultdict(int)
    successes: list[float] = []
    metrics: dict[str, list[float]] = {name: [] for name in ("utility", "cost", "interval_width")}

    for row in rows:
        status = row.get("status", "").strip().lower()
        if status not in OK_STATUSES:
            failures[status or "unspecified_failure"] += 1
            continue
        try:
            success = parse_success(row["success"])
            parsed_metrics: dict[str, float] = {}
            for name in metrics:
                value = finite_optional(row, name)
                if value is not None:
                    parsed_metrics[name] = value
        except (TypeError, ValueError) as error:
            failures[f"invalid_success_row: {error}"] += 1
            continue
        successes.append(success)
        for name, value in parsed_metrics.items():
            metrics[name].append(value)

    completed = len(successes)
    success_mean, success_mcse = mean_and_mcse(successes)
    result: dict[str, Any] = {
        "attempted": attempted,
        "completed": completed,
        "failed_or_invalid": attempted - completed,
        "failure_rate": (attempted - completed) / attempted if attempted else None,
        "failure_reasons": dict(sorted(failures.items())),
        "success_rate": success_mean,
        "success_rate_mcse": success_mcse,
    }
    for name, values in metrics.items():
        mean, mcse = mean_and_mcse(values)
        result[f"mean_{name}"] = mean
        result[f"mean_{name}_mcse"] = mcse
        result[f"{name}_observations"] = len(values)
    return result


def main() -> int:
    """Run the design-simulation summary command."""
    args = parse_args()
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.input.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - columns)
        if missing:
            raise SystemExit(f"missing required CSV columns: {missing}")
        for row in reader:
            grouped[row["design"]].append(row)

    report = {
        "input": str(args.input.resolve()),
        "designs": [
            {"design": design, **summarize(rows)} for design, rows in sorted(grouped.items())
        ],
        "interpretation_note": (
            "Results are conditional on the simulated design-stage distribution and workflow. "
            "Failed or invalid replications remain in attempted counts."
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
