"""Exact terminal GBM sampling and uncertainty-aware payoff estimation."""

from dataclasses import dataclass
from math import exp, isfinite, sqrt
from numbers import Integral, Real
from statistics import NormalDist

import numpy as np

from .analytics import black_scholes_price
from .contracts import EuropeanOption, OptionType


@dataclass(frozen=True)
class MonteCarloEstimate:
    price: float
    standard_error: float
    confidence_low: float
    confidence_high: float
    confidence_level: float
    paths: int
    independent_samples: int
    antithetic: bool
    seed: int | None


def monte_carlo_price(
    option: EuropeanOption,
    *,
    paths: int = 100_000,
    seed: int | None = 42,
    antithetic: bool = True,
    confidence_level: float = 0.95,
) -> MonteCarloEstimate:
    """Estimate a discounted European payoff under risk-neutral terminal GBM.

    Antithetic paths use z and -z. Their *pair averages* are independent
    observations for the standard error, not the individual correlated paths.
    Confidence limits use an asymptotic normal approximation; rare-event
    payoffs and small samples can make them unreliable. No time grid is used.
    """
    if isinstance(paths, bool) or not isinstance(paths, Integral) or paths < 2:
        raise ValueError("paths must be an integer of at least 2")
    if not isinstance(antithetic, bool):
        raise ValueError("antithetic must be a boolean")
    if antithetic and (paths < 4 or paths % 2):
        raise ValueError("antithetic sampling requires an even path count of at least 4")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0):
        raise ValueError("seed must be a nonnegative integer or None")
    if (
        isinstance(confidence_level, bool)
        or not isinstance(confidence_level, Real)
        or not isfinite(confidence_level)
        or not 0 < confidence_level < 1
    ):
        raise ValueError("confidence_level must be a finite number strictly between 0 and 1")
    paths = int(paths)
    seed = None if seed is None else int(seed)
    confidence_level = float(confidence_level)
    count = paths // 2 if antithetic else paths
    if option.maturity == 0 or option.volatility == 0:
        price = black_scholes_price(option)
        return MonteCarloEstimate(
            price, 0.0, price, price, confidence_level, paths, count, antithetic, seed
        )
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(count)
    t = option.maturity
    scale = option.volatility * sqrt(t)
    # Discount before taking payoffs to avoid a needless large exp(r*T).
    base = option.spot * exp((-option.dividend_yield - 0.5 * option.volatility**2) * t)
    discounted_strike = option.strike * exp(-option.rate * t)
    sign = 1.0 if option.kind == OptionType.CALL else -1.0

    def payoff(draws: np.ndarray) -> np.ndarray:
        return np.maximum(sign * (base * np.exp(scale * draws) - discounted_strike), 0.0)

    observations = payoff(z)
    if antithetic:
        observations = (observations + payoff(-z)) * 0.5
    if not np.all(np.isfinite(observations)):
        raise ValueError("sampled payoffs exceed floating-point range")
    price = float(np.mean(observations))
    standard_error = float(np.std(observations, ddof=1) / sqrt(count))
    # PPF of the lower tail avoids rounding (1 + confidence_level)/2 to 1.
    critical = -NormalDist().inv_cdf((1.0 - confidence_level) * 0.5)
    radius = critical * standard_error
    return MonteCarloEstimate(
        price,
        standard_error,
        price - radius,
        price + radius,
        confidence_level,
        paths,
        count,
        antithetic,
        seed,
    )
