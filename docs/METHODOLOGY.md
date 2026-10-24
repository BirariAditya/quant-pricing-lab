# Model and validation methodology

## Analytical model

Under the risk-neutral measure, spot follows `dS = (r-q) S dt + sigma S dW`.
Rates, continuous dividend yield, and volatility are constant, and exercise is European.

For positive maturity T and volatility sigma:

```text
d1 = (ln(S/K) + (r-q+sigma^2/2)T) / (sigma sqrt(T))
d2 = d1 - sigma sqrt(T)
C  = S exp(-qT) N(d1) - K exp(-rT) N(d2)
P  = K exp(-rT) N(-d2) - S exp(-qT) N(-d1)
```

The implementation uses `erfc` for the normal CDF, calculates the out-of-the-money price
directly, and reconstructs the other side with put-call parity. This reduces common tail
and cancellation problems, but it is not an arbitrary-precision or fully asymptotic implementation.

## Monte Carlo estimator

Terminal GBM is sampled exactly, so this experiment has no time-discretization bias:

```text
S(T) = S(0) exp((r-q-sigma^2/2)T + sigma sqrt(T) Z), Z ~ N(0,1)
X = exp(-rT) max(sign * (S(T)-K), 0)
```

The plain estimator averages independent X values. The antithetic estimator averages
independent `Y_i = (X(Z_i) + X(-Z_i))/2` values. Standard errors use sample standard deviation
with `ddof=1` on the respective independent observations. The 95% interval is the estimate
plus/minus `1.95996398454 * standard_error`; it is an asymptotic normal approximation.

Antithetic comparisons match total payoff evaluations. A 100,000-path antithetic run uses
50,000 random normals and 50,000 independent pair averages. The plain run uses 100,000 random
normals and observations. These are equal-path comparisons, not equal-RNG or equal-time claims.

## Tests and independent reference

- Known call/put reference prices, put-call parity, no-arbitrage bounds, and volatility monotonicity.
- Central finite-difference price derivatives checked against analytical Greeks, including
  dividends and negative rates. Theta uses minus the derivative with respect to remaining maturity.
- Scalar discounted-payoff calculations independently check vectorized sampling and pair-level errors.
- A QuantLib `AnalyticEuropeanEngine` grid checks price and all five Greeks at matching maturities.
  The grid uses Actual/365 Fixed, an explicit evaluation date, flat curves, and constant volatility.
- Absolute tolerance is `1e-8` and relative tolerance is `1e-10`; either permits acceptance.
  Full reference values and absolute differences are retained, including tiny option values.

Reference agreement checks implementation consistency within a shared financial model. It does
not establish that constant-volatility GBM fits observed markets. The expiry and zero-volatility
cases are checked by deterministic unit tests rather than the positive-volatility reference grid.

## Convergence experiment

One at-the-money call is evaluated at 1,000, 10,000, and 100,000 paths. Each configuration uses
40 replications, with seeds 0 through 39. The same seeds are reused across configurations;
cross-configuration observations therefore should not be treated as independent.

RMSE is measured against the analytical price over the 40 replications. The reported interval
coverage is the fraction of those 40 intervals containing the reference. With only 40 trials,
coverage is coarse and variable; it is not a calibrated guarantee. Elapsed times include RNG,
payoff evaluation, and summary calculation; there is no claim of hardware-independent speed.

## Limitations

Normal intervals can fail in rare-event regimes. No positive sampled payoff means no measured
sample variance, not proof that the true price or uncertainty is zero. The unit tests explicitly
demonstrate this failure mode. Antithetic variance reduction measured for the reference call
does not prove a universal improvement for every payoff or parameter combination.

Only terminal payoffs are supported. Binary64 arithmetic can underflow tiny tail values or
overflow with extreme rates, maturities, and volatility. Calendar conversion and market-data
cleaning are the caller's responsibility. No historical data is used in this release.
