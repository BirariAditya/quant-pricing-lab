"""Contracts and market inputs, with explicit units and validation."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class EuropeanOption:
    """European vanilla option under constant, continuously compounded rates.

    ``maturity`` is a year fraction; ``volatility`` is annualized (0.20 = 20%).
    ``rate`` and ``dividend_yield`` are continuous annual rates (0.05 = 5%).
    Spot and strike must share a currency/unit. Negative rates are permitted.
    """

    spot: float
    strike: float
    maturity: float
    rate: float
    volatility: float
    dividend_yield: float = 0.0
    kind: OptionType = OptionType.CALL

    def __post_init__(self) -> None:
        for name in ("spot", "strike", "maturity", "rate", "volatility", "dividend_yield"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                raise ValueError(f"{name} must be a finite real number")
            object.__setattr__(self, name, float(value))
        if self.spot <= 0 or self.strike <= 0:
            raise ValueError("spot and strike must be strictly positive")
        if self.maturity < 0 or self.volatility < 0:
            raise ValueError("maturity and volatility must be nonnegative")
        try:
            object.__setattr__(self, "kind", OptionType(self.kind))
        except (ValueError, TypeError) as exc:
            raise ValueError("kind must be 'call' or 'put'") from exc
