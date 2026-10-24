"""Reconcile prices and five Greeks with QuantLib on an explicit market grid."""

import argparse
import itertools
import json
import math
import platform
from dataclasses import asdict
from pathlib import Path

import QuantLib as ql

from quant_pricing_lab import EuropeanOption, black_scholes_greeks, black_scholes_price


def reconcile() -> dict:
    today = ql.Date(15, 1, 2025)
    previous_date = ql.Settings.instance().evaluationDate
    day_count = ql.Actual365Fixed()
    rows = []
    try:
        ql.Settings.instance().evaluationDate = today
        for kind, spot, days, rate, volatility, dividend in itertools.product(
            ("call", "put"),
            (80.0, 100.0, 120.0),
            (7, 183, 730),
            (-0.01, 0.05),
            (0.1, 0.3),
            (0.0, 0.025),
        ):
            expiry = today + days
            maturity = day_count.yearFraction(today, expiry)
            option = EuropeanOption(spot, 100, maturity, rate, volatility, dividend, kind)
            process = ql.BlackScholesMertonProcess(
                ql.QuoteHandle(ql.SimpleQuote(spot)),
                ql.YieldTermStructureHandle(ql.FlatForward(today, dividend, day_count)),
                ql.YieldTermStructureHandle(ql.FlatForward(today, rate, day_count)),
                ql.BlackVolTermStructureHandle(
                    ql.BlackConstantVol(today, ql.NullCalendar(), volatility, day_count)
                ),
            )
            reference = ql.VanillaOption(
                ql.PlainVanillaPayoff(ql.Option.Call if kind == "call" else ql.Option.Put, 100),
                ql.EuropeanExercise(expiry),
            )
            reference.setPricingEngine(ql.AnalyticEuropeanEngine(process))
            ours = {"price": black_scholes_price(option), **asdict(black_scholes_greeks(option))}
            theirs = {
                "price": reference.NPV(),
                **{
                    name: getattr(reference, name)()
                    for name in ("delta", "gamma", "vega", "theta", "rho")
                },
            }
            errors = {name: abs(ours[name] - theirs[name]) for name in ours}
            passed = all(
                math.isclose(ours[name], theirs[name], rel_tol=1e-10, abs_tol=1e-8) for name in ours
            )
            rows.append(
                {
                    "inputs": asdict(option),
                    "ours": ours,
                    "quantlib": theirs,
                    "absolute_errors": errors,
                    "passed": passed,
                }
            )
    finally:
        ql.Settings.instance().evaluationDate = previous_date
    return {
        "python": platform.python_version(),
        "quantlib": ql.__version__,
        "day_count": "Actual/365 (Fixed)",
        "evaluation_date": "2025-01-15",
        "relative_tolerance": 1e-10,
        "absolute_tolerance": 1e-8,
        "cases": len(rows),
        "comparisons": len(rows) * 6,
        "passed": all(row["passed"] for row in rows),
        "maximum_absolute_errors": {
            name: max(row["absolute_errors"][name] for row in rows) for name in rows[0]["ours"]
        },
        "results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/quantlib-validation.json"))
    args = parser.parse_args()
    result = reconcile()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "results"}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
