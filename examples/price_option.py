"""Run after installation: python examples/price_option.py."""

from dataclasses import asdict
from json import dumps

from quant_pricing_lab import (
    EuropeanOption,
    black_scholes_greeks,
    black_scholes_price,
    monte_carlo_price,
)

option = EuropeanOption(
    spot=100, strike=100, maturity=1, rate=0.05, volatility=0.20, dividend_yield=0.02
)
print(
    dumps(
        {
            "analytical_price": black_scholes_price(option),
            "greeks": asdict(black_scholes_greeks(option)),
            "monte_carlo": asdict(monte_carlo_price(option, paths=100_000, seed=42)),
        },
        indent=2,
    )
)
