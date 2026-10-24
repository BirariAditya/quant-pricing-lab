import math
import unittest
from dataclasses import replace
from statistics import NormalDist, mean, stdev

import numpy as np

from quant_pricing_lab import EuropeanOption, black_scholes_price, monte_carlo_price


class MonteCarloTests(unittest.TestCase):
    def setUp(self):
        self.option = EuropeanOption(100, 100, 1, 0.05, 0.2, dividend_yield=0.02)

    def test_seed_reproduces_full_result(self):
        self.assertEqual(monte_carlo_price(self.option), monte_carlo_price(self.option))

    def test_seed_does_not_change_global_numpy_state(self):
        before = np.random.get_state()
        monte_carlo_price(self.option, paths=100)
        after = np.random.get_state()
        self.assertEqual(before[0], after[0])
        np.testing.assert_array_equal(before[1], after[1])
        self.assertEqual(before[2:], after[2:])

    def test_plain_sampling_matches_scalar_discounted_payoffs(self):
        result = monte_carlo_price(self.option, paths=20, seed=7, antithetic=False)
        z = np.random.default_rng(7).standard_normal(20)
        payoffs = [
            math.exp(-0.05) * max(100 * math.exp((0.05 - 0.02 - 0.2**2 / 2) + 0.2 * x) - 100, 0)
            for x in z
        ]
        self.assertAlmostEqual(result.price, mean(payoffs), places=12)
        self.assertAlmostEqual(result.standard_error, stdev(payoffs) / math.sqrt(20), places=12)
        self.assertEqual(result.independent_samples, 20)

    def test_antithetic_error_uses_independent_pair_averages(self):
        result = monte_carlo_price(self.option, paths=20, seed=7)
        z = np.random.default_rng(7).standard_normal(10)

        def payoff(x):
            terminal = 100 * math.exp(0.05 - 0.02 - 0.2**2 / 2 + 0.2 * x)
            return math.exp(-0.05) * max(terminal - 100, 0)

        pairs = [(payoff(x) + payoff(-x)) / 2 for x in z]
        self.assertAlmostEqual(result.price, mean(pairs), places=12)
        self.assertAlmostEqual(result.standard_error, stdev(pairs) / math.sqrt(10), places=12)
        self.assertEqual(result.paths, 20)
        self.assertEqual(result.independent_samples, 10)

    def test_confidence_interval_uses_requested_level(self):
        result = monte_carlo_price(self.option, paths=1000, confidence_level=0.90)
        half_width = NormalDist().inv_cdf(0.95) * result.standard_error
        self.assertAlmostEqual(result.confidence_low, result.price - half_width)
        self.assertAlmostEqual(result.confidence_high, result.price + half_width)

    def test_monte_carlo_agrees_with_analytical_prices(self):
        for kind in ("call", "put"):
            for rate in (-0.02, 0.05):
                for antithetic in (False, True):
                    option = replace(self.option, kind=kind, rate=rate)
                    estimate = monte_carlo_price(
                        option, paths=40_000, seed=123, antithetic=antithetic
                    )
                    with self.subTest(kind=kind, rate=rate, antithetic=antithetic):
                        self.assertLess(
                            abs(estimate.price - black_scholes_price(option)),
                            6 * estimate.standard_error,
                        )

    def test_antithetic_reduces_measured_error_for_reference_call(self):
        plain = monte_carlo_price(self.option, paths=100_000, seed=3, antithetic=False)
        paired = monte_carlo_price(self.option, paths=100_000, seed=3)
        self.assertLess(paired.standard_error, plain.standard_error)

    def test_deterministic_boundaries_have_zero_sampling_error(self):
        for kind in ("call", "put"):
            for field in ("maturity", "volatility"):
                option = replace(self.option, kind=kind, **{field: 0})
                estimate = monte_carlo_price(option, paths=10)
                with self.subTest(kind=kind, field=field):
                    self.assertEqual(estimate.price, black_scholes_price(option))
                    self.assertEqual(estimate.standard_error, 0)
                    self.assertEqual(estimate.confidence_low, estimate.confidence_high)

    def test_no_observed_payoff_does_not_prove_zero_option_value(self):
        option = replace(self.option, strike=1000)
        estimate = monte_carlo_price(option, paths=100)
        self.assertEqual(estimate.standard_error, 0)
        self.assertGreater(black_scholes_price(option), 0)

    def test_rejects_invalid_sampling_parameters(self):
        for kwargs in (
            {"paths": 0},
            {"paths": 2},
            {"paths": 11},
            {"paths": True},
            {"paths": 10.5},
            {"seed": -1},
            {"seed": True},
            {"seed": 1.2},
            {"antithetic": "yes"},
            {"confidence_level": 0},
            {"confidence_level": 1},
            {"confidence_level": float("nan")},
            {"confidence_level": True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                monte_carlo_price(self.option, **kwargs)


if __name__ == "__main__":
    unittest.main()
