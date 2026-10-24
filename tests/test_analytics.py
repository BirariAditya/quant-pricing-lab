import math
import unittest
from dataclasses import replace

from quant_pricing_lab import EuropeanOption, black_scholes_greeks, black_scholes_price


class AnalyticalTests(unittest.TestCase):
    def setUp(self):
        self.option = EuropeanOption(100, 100, 1, 0.05, 0.2)

    def test_standard_call_reference(self):
        self.assertAlmostEqual(black_scholes_price(self.option), 10.450583572185565, places=11)

    def test_standard_put_reference(self):
        self.assertAlmostEqual(
            black_scholes_price(replace(self.option, kind="put")), 5.57352602225697, places=11
        )

    def test_continuous_dividend_references(self):
        option = replace(self.option, dividend_yield=0.02)
        self.assertAlmostEqual(black_scholes_price(option), 9.227005508154036, places=11)
        self.assertAlmostEqual(
            black_scholes_price(replace(option, kind="put")), 6.330080627549918, places=11
        )

    def test_put_call_parity_across_market_regimes(self):
        for spot in (50, 100, 200):
            for rate in (-0.03, 0.0, 0.07):
                for volatility in (0.01, 0.2, 0.8):
                    option = replace(
                        self.option,
                        spot=spot,
                        rate=rate,
                        volatility=volatility,
                        dividend_yield=0.025,
                    )
                    with self.subTest(spot=spot, rate=rate, volatility=volatility):
                        difference = black_scholes_price(option) - black_scholes_price(
                            replace(option, kind="put")
                        )
                        expected = spot * math.exp(-0.025) - 100 * math.exp(-rate)
                        self.assertAlmostEqual(difference, expected, places=11)

    def test_expiry_returns_intrinsic_value(self):
        for kind, spot, expected in (("call", 120, 20), ("put", 80, 20), ("call", 80, 0)):
            with self.subTest(kind=kind, spot=spot):
                self.assertEqual(
                    black_scholes_price(replace(self.option, kind=kind, spot=spot, maturity=0)),
                    expected,
                )

    def test_zero_volatility_discounted_forward_payoff(self):
        for kind in ("call", "put"):
            option = replace(self.option, volatility=0, rate=-0.02, dividend_yield=0.03, kind=kind)
            difference = 100 * math.exp(-0.03) - 100 * math.exp(0.02)
            expected = max(difference if kind == "call" else -difference, 0)
            self.assertAlmostEqual(black_scholes_price(option), expected, places=12)

    def test_price_bounds(self):
        for kind in ("call", "put"):
            for spot in (20, 100, 500):
                option = replace(self.option, kind=kind, spot=spot, dividend_yield=0.02)
                s, k = spot * math.exp(-0.02), 100 * math.exp(-0.05)
                low, high = (max(s - k, 0), s) if kind == "call" else (max(k - s, 0), k)
                with self.subTest(kind=kind, spot=spot):
                    self.assertGreaterEqual(black_scholes_price(option), low - 1e-12)
                    self.assertLessEqual(black_scholes_price(option), high + 1e-12)

    def test_volatility_increases_call_and_put_values(self):
        for kind in ("call", "put"):
            low = replace(self.option, kind=kind, volatility=0.1)
            high = replace(low, volatility=0.4)
            self.assertGreater(black_scholes_price(high), black_scholes_price(low))

    def test_deep_out_of_money_price_preserves_small_tail(self):
        price = black_scholes_price(replace(self.option, spot=10, rate=0))
        self.assertGreater(price, 0)
        self.assertLess(price, 1e-20)

    def test_greeks_match_independent_finite_differences(self):
        for kind in ("call", "put"):
            for rate in (-0.02, 0.05):
                option = replace(self.option, kind=kind, rate=rate, dividend_yield=0.025)
                greeks = black_scholes_greeks(option)
                for field, name, step, sign in (
                    ("spot", "delta", 1e-3, 1),
                    ("volatility", "vega", 1e-5, 1),
                    ("rate", "rho", 1e-5, 1),
                    ("maturity", "theta", 1e-5, -1),
                ):
                    value = getattr(option, field)
                    up = black_scholes_price(replace(option, **{field: value + step}))
                    down = black_scholes_price(replace(option, **{field: value - step}))
                    with self.subTest(kind=kind, rate=rate, greek=name):
                        self.assertAlmostEqual(
                            getattr(greeks, name), sign * (up - down) / (2 * step), delta=2e-6
                        )
                step = 0.01
                gamma = (
                    black_scholes_price(replace(option, spot=option.spot + step))
                    - 2 * black_scholes_price(option)
                    + black_scholes_price(replace(option, spot=option.spot - step))
                ) / step**2
                self.assertAlmostEqual(greeks.gamma, gamma, delta=1e-8)

    def test_call_put_greek_identities(self):
        option = replace(self.option, dividend_yield=0.02)
        call = black_scholes_greeks(option)
        put = black_scholes_greeks(replace(option, kind="put"))
        self.assertAlmostEqual(call.delta - put.delta, math.exp(-0.02))
        self.assertAlmostEqual(call.gamma, put.gamma)
        self.assertAlmostEqual(call.vega, put.vega)
        self.assertAlmostEqual(call.rho - put.rho, 100 * math.exp(-0.05))

    def test_boundary_greeks_are_explicitly_unsupported(self):
        for field in ("maturity", "volatility"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                black_scholes_greeks(replace(self.option, **{field: 0}))

    def test_rejects_invalid_contracts(self):
        for field, value in (
            ("spot", 0),
            ("strike", -1),
            ("maturity", -1),
            ("volatility", -0.1),
            ("spot", float("nan")),
            ("rate", float("inf")),
            ("dividend_yield", True),
            ("volatility", "0.2"),
            ("kind", "straddle"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                replace(self.option, **{field: value})


if __name__ == "__main__":
    unittest.main()
