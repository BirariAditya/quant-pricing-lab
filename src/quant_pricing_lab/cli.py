"""JSON command-line interface for repeatable experiments."""

import argparse
import json
from dataclasses import asdict

from .analytics import black_scholes_greeks, black_scholes_price
from .contracts import EuropeanOption
from .monte_carlo import monte_carlo_price


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Price a European option under constant-parameter GBM"
    )
    parser.add_argument("--kind", choices=["call", "put"], default="call")
    parser.add_argument("--spot", type=float, default=100.0)
    parser.add_argument("--strike", type=float, default=100.0)
    parser.add_argument("--maturity", type=float, default=1.0, help="year fraction")
    parser.add_argument("--rate", type=float, default=0.05, help="continuous annual rate")
    parser.add_argument("--volatility", type=float, default=0.20, help="annualized volatility")
    parser.add_argument("--dividend-yield", type=float, default=0.0)
    parser.add_argument("--paths", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--plain", action="store_true", help="disable antithetic sampling")
    args = parser.parse_args(argv)
    try:
        option = EuropeanOption(
            spot=args.spot,
            strike=args.strike,
            maturity=args.maturity,
            rate=args.rate,
            volatility=args.volatility,
            dividend_yield=args.dividend_yield,
            kind=args.kind,
        )
        price = black_scholes_price(option)
        estimate = monte_carlo_price(
            option, paths=args.paths, seed=args.seed, antithetic=not args.plain
        )
        greeks = (
            asdict(black_scholes_greeks(option))
            if option.maturity > 0 and option.volatility > 0
            else None
        )
    except (ValueError, OverflowError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "option": asdict(option),
                "analytical_price": price,
                "greeks": greeks,
                "monte_carlo": asdict(estimate),
                "mc_absolute_error": abs(estimate.price - price),
            },
            indent=2,
            allow_nan=False,
        )
    )
    return 0
