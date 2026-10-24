"""Measure equal-path-count Monte Carlo error across 40 seeded replications."""

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np

from quant_pricing_lab import EuropeanOption, black_scholes_price, monte_carlo_price


def run() -> dict:
    option = EuropeanOption(100, 100, 1, 0.05, 0.2, dividend_yield=0.02)
    analytical = black_scholes_price(option)
    summaries = []
    runs = []
    for paths in (1_000, 10_000, 100_000):
        for antithetic in (False, True):
            group = []
            for seed in range(40):
                start = perf_counter()
                estimate = monte_carlo_price(option, paths=paths, seed=seed, antithetic=antithetic)
                elapsed = perf_counter() - start
                row = {
                    **asdict(estimate),
                    "error": estimate.price - analytical,
                    "elapsed_seconds": elapsed,
                    "interval_contains_reference": (
                        estimate.confidence_low <= analytical <= estimate.confidence_high
                    ),
                }
                group.append(row)
                runs.append(row)
            summaries.append(
                {
                    "paths": paths,
                    "antithetic": antithetic,
                    "replications": len(group),
                    "rmse": float(np.sqrt(np.mean([row["error"] ** 2 for row in group]))),
                    "mean_error": float(np.mean([row["error"] for row in group])),
                    "mean_standard_error": float(np.mean([row["standard_error"] for row in group])),
                    "coverage_fraction": float(
                        np.mean([row["interval_contains_reference"] for row in group])
                    ),
                    "median_elapsed_seconds": float(
                        np.median([row["elapsed_seconds"] for row in group])
                    ),
                }
            )
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.system(),
        "option": asdict(option),
        "analytical_price": analytical,
        "seeds": list(range(40)),
        "comparison_budget": (
            "equal payoff evaluations (paths); not equal random draws or wall time"
        ),
        "confidence_interval": "asymptotic normal, 95%; pairs are independent sampling units",
        "scope": (
            "one ATM call; empirical RMSE and coverage from 40 replications, "
            "not universal guarantees"
        ),
        "summaries": summaries,
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/convergence.json"))
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result["summaries"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
