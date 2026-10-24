# Quant Pricing Lab

[![CI](https://github.com/BirariAditya/quant-pricing-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/BirariAditya/quant-pricing-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An independent Python library for European option pricing and reproducible Monte Carlo experiments.
The focus is numerical validation: analytical prices and Greeks are reconciled with QuantLib,
and simulation error is measured across seeded replications at equal payoff-evaluation budgets.

## What is implemented

- Black-Scholes-Merton call and put prices with continuous dividends and negative-rate support.
- Analytical delta, gamma, vega, theta, and rho, checked with finite differences.
- Exact terminal geometric Brownian motion sampling, with plain and antithetic estimators.
- Standard errors and approximate confidence intervals using the correct independent sampling units.
- Explicit expiry/zero-volatility behavior, validated inputs, a JSON CLI, and automated CI.
- A QuantLib reconciliation grid and a repeatable convergence/variance-reduction study.

## Quick start

Python 3.10+ is required. From a checkout, preferably in a virtual environment:

```bash
python -m pip install -e .
python -m quant_pricing_lab --kind call --spot 100 --strike 100 --maturity 1 --rate 0.05 --volatility 0.2
python examples/price_option.py
```

The CLI emits JSON with the analytical price, Greeks, simulation estimate, sampling error,
confidence bounds, and absolute pricing error. The equivalent installed command is `quant-pricing-lab`.

```python
from quant_pricing_lab import EuropeanOption, black_scholes_price, monte_carlo_price

option = EuropeanOption(
    spot=100,
    strike=100,
    maturity=1,
    rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)
print(black_scholes_price(option))  # 9.227005508154...
estimate = monte_carlo_price(option, paths=100_000, seed=42)
print(estimate.price, estimate.standard_error)
print(estimate.confidence_low, estimate.confidence_high)
```

## Reproduce the checks and experiments

```bash
python -m pip install -e ".[validation,dev]"
python -m unittest discover -s tests -v
ruff check .
python scripts/validate_quantlib.py
python scripts/convergence_study.py
python -m build
```

The reference grid covers both option types, three spots, three maturities, two rates,
two volatilities, and two dividend yields: **144 contracts and 864 comparisons** (price and
five Greeks). QuantLib is an optional validation dependency; the pricing library only needs NumPy.
The full reference inputs, outputs, tolerances, and version are saved in
[`results/quantlib-validation.json`](results/quantlib-validation.json).

The convergence study uses 40 seeds at each of 1,000, 10,000, and 100,000 total paths,
for plain and antithetic sampling. It records individual estimates, empirical RMSE, standard
errors, interval coverage, and elapsed time in [`results/convergence.json`](results/convergence.json).
See [`docs/RESULTS.md`](docs/RESULTS.md) for the measured results and their limits.

![Monte Carlo precision study](docs/convergence.png)

## Units and model contract

| Input/output | Convention |
| --- | --- |
| Maturity | Year fraction, supplied by the caller |
| Rate and dividend yield | Constant, continuously compounded annual rates |
| Volatility | Annualized; `0.20` means 20% |
| Vega and rho | Per absolute unit; multiply by `0.01` for a one-percentage-point change |
| Theta | Per calendar year, with expiry fixed; `-dV/dT` |
| Paths | Total payoff evaluations; an antithetic pair consumes two |
| Independent samples | `paths / 2` with antithetics, otherwise `paths` |

At zero maturity, pricing returns intrinsic value. At zero volatility, it returns the
discounted deterministic payoff. Analytical Greeks reject these boundaries instead of assigning
potentially misleading values at payoff kinks.

## Why the error calculation matters

With antithetic sampling, the payoffs from `z` and `-z` are correlated. For a pair average
`Y = (payoff(z) + payoff(-z)) / 2`, the estimator standard error is the sample standard
deviation of the independent **pair averages**, divided by the square root of the number of pairs.
Treating all individual paths as independent would give an incorrect uncertainty estimate.

The intervals are normal approximations, not guaranteed bounds. Small samples and rare payoffs
can give poor coverage; observing only zero payoffs can even produce a zero estimated error for
an option with a positive analytical value. See [methodology](docs/METHODOLOGY.md).

## Scope and next work

This release covers constant-parameter European vanilla options. It does not implement early
exercise, discrete dividends, volatility smiles, yield-curve construction, calibration, or
transaction-cost modeling. Conventional floating-point limits apply to extreme inputs.

Planned extensions, each with a separate validation contract:

1. A safeguarded implied-volatility solver with price-bound and convergence diagnostics.
2. Control variates, reporting pilot-estimation costs and independent test-sample errors.
3. Convergence studies across moneyness/maturity regimes, including rare-event failures.
4. A C++ numerical kernel only after a measured Python bottleneck justifies it.

## Contributing and provenance

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and validation expectations. This is an
independent educational engineering project using synthetic market inputs. It contains no
employer systems, code, market feeds, or internal methodologies. The methods are established;
the contribution here is a tested implementation and reproducible experimental record.

References: [Black and Scholes (1973)](https://doi.org/10.1086/260062),
[Merton (1973)](https://doi.org/10.2307/3003143),
[QuantLib analytical European engine](https://github.com/lballabio/QuantLib/blob/master/ql/pricingengines/vanilla/analyticeuropeanengine.cpp).

MIT licensed. QuantLib and other dependencies retain their own licenses.
