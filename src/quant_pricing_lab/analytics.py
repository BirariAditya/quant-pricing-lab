"""Black-Scholes-Merton closed forms with continuous dividend yield."""

from dataclasses import dataclass
from math import erfc, exp, log, pi, sqrt

from .contracts import EuropeanOption, OptionType


def _cdf(x: float) -> float:
    # erfc preserves the small negative tail that 1 + erf(x) can lose.
    return 0.5 * erfc(-x / sqrt(2.0))


def _density(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)


def _d1_d2(option: EuropeanOption) -> tuple[float, float]:
    sigma_sqrt_t = option.volatility * sqrt(option.maturity)
    d1 = (
        log(option.spot)
        - log(option.strike)
        + (option.rate - option.dividend_yield + 0.5 * option.volatility**2) * option.maturity
    ) / sigma_sqrt_t
    return d1, d1 - sigma_sqrt_t


def black_scholes_price(option: EuropeanOption) -> float:
    """Price a European call or put; support expiry and zero volatility.

    Compute the out-of-the-money side directly, then recover the in-the-money
    side by put-call parity to reduce subtraction of nearly equal large terms.
    """
    s = option.spot * exp(-option.dividend_yield * option.maturity)
    k = option.strike * exp(-option.rate * option.maturity)
    if option.maturity == 0 or option.volatility == 0:
        return max(s - k, 0.0) if option.kind == OptionType.CALL else max(k - s, 0.0)
    d1, d2 = _d1_d2(option)
    if s <= k:
        call = max(s * _cdf(d1) - k * _cdf(d2), 0.0)
        put = call + (k - s)
    else:
        put = max(k * _cdf(-d2) - s * _cdf(-d1), 0.0)
        call = put + (s - k)
    return call if option.kind == OptionType.CALL else put


@dataclass(frozen=True)
class Greeks:
    """Price derivatives: vega/rho per absolute unit; theta per calendar year.

    Multiply vega and rho by 0.01 for a one-percentage-point change.
    Theta is dV/dt with expiry fixed, i.e. minus dV/d(maturity).
    """

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def black_scholes_greeks(option: EuropeanOption) -> Greeks:
    """Analytical Greeks for positive maturity and volatility.

    Degenerate boundaries are rejected because the smooth formulas do not
    provide a consistent definition for every Greek at payoff kinks.
    """
    if option.maturity <= 0 or option.volatility <= 0:
        raise ValueError("Greeks require strictly positive maturity and volatility")
    d1, d2 = _d1_d2(option)
    t = option.maturity
    s, k, r, q, sigma = (
        option.spot,
        option.strike,
        option.rate,
        option.dividend_yield,
        option.volatility,
    )
    dq, dr = exp(-q * t), exp(-r * t)
    density = _density(d1)
    gamma = dq * density / (s * sigma * sqrt(t))
    vega = s * dq * density * sqrt(t)
    diffusion_theta = -s * dq * density * sigma / (2.0 * sqrt(t))
    if option.kind == OptionType.CALL:
        return Greeks(
            delta=dq * _cdf(d1),
            gamma=gamma,
            vega=vega,
            theta=diffusion_theta - r * k * dr * _cdf(d2) + q * s * dq * _cdf(d1),
            rho=k * t * dr * _cdf(d2),
        )
    return Greeks(
        delta=-dq * _cdf(-d1),
        gamma=gamma,
        vega=vega,
        theta=diffusion_theta + r * k * dr * _cdf(-d2) - q * s * dq * _cdf(-d1),
        rho=-k * t * dr * _cdf(-d2),
    )
