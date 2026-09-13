import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from btc5m_research.fair import fair_probability, price_volatility, dynamic_sigma
from btc5m_research.risk import certainty_equivalent, reservation_prices, terminal_moments


class BinaryRiskTests(unittest.TestCase):
    def test_split_inventory_matches_both_terminal_outcomes(self):
        for p in (0.0, 0.1, 0.5, 0.9, 1.0):
            mean, variance = terminal_moments(p, 12.0, 8.0)
            self.assertAlmostEqual(mean, p * 12 + (1 - p) * 8)
            self.assertAlmostEqual(variance, p * (12 - mean) ** 2 + (1 - p) * (8 - mean) ** 2)
            self.assertEqual(terminal_moments(p, 8.0, 8.0), (8.0, 0.0))

    def test_bid_and_ask_preserve_expected_exponential_utility(self):
        for p in (0.05, 0.5, 0.95):
            for q in (-10, 0, 10):
                gamma = 0.13
                bid, ask = reservation_prices(p, q, gamma)
                expected = (1 - p) + p * math.exp(-gamma * q)
                after_buy = (1 - p) * math.exp(gamma * bid) + p * math.exp(-gamma * (q + 1 - bid))
                after_sell = (1 - p) * math.exp(-gamma * ask) + p * math.exp(-gamma * (q - 1 + ask))
                self.assertAlmostEqual(after_buy, expected)
                self.assertAlmostEqual(after_sell, expected)
                self.assertLessEqual(bid, ask)

    def test_long_inventory_lowers_both_values(self):
        left = reservation_prices(0.6, -10, 0.1)
        flat = reservation_prices(0.6, 0, 0.1)
        right = reservation_prices(0.6, 10, 0.1)
        for i in (0, 1):
            self.assertGreater(left[i], flat[i])
            self.assertGreater(flat[i], right[i])

    def test_symmetry_risk_neutral_limit_and_certain_payoffs(self):
        bid, ask = reservation_prices(0.5, 0, 0.1)
        self.assertAlmostEqual(bid + ask, 1.0)
        self.assertAlmostEqual(bid, 0.487505204864)
        for p in (0.0, 0.3, 1.0):
            self.assertEqual(reservation_prices(p, 20, 0), (p, p))
            self.assertAlmostEqual(certainty_equivalent(p, 20, 0), 20 * p)
        for p in (0.0, 1.0):
            self.assertEqual(reservation_prices(p, -20, 0.2), (p, p))
            self.assertEqual(certainty_equivalent(p, -20, 0.2), -20 * p)

    def test_small_gamma_expansion_and_large_inventory_stability(self):
        p, q, gamma = 0.3, 7, 1e-7
        approximate = q * p - 0.5 * gamma * q * q * p * (1 - p)
        self.assertAlmostEqual(certainty_equivalent(p, q, gamma), approximate, places=11)
        for q in (-1e6, 1e6):
            self.assertTrue(math.isfinite(certainty_equivalent(0.3, q, 1.0)))
            bid, ask = reservation_prices(0.3, q, 1.0)
            self.assertTrue(0 <= bid <= ask <= 1)

    def test_invalid_model_inputs_do_not_silently_produce_nan(self):
        for values in ((float('nan'), 0, 1), (0.5, float('inf'), 1), (0.5, 0, -1), (1.1, 0, 0)):
            with self.assertRaises(ValueError):
                reservation_prices(*values)

    def test_large_risk_aversion_keeps_recoverable_tail_mass(self):
        bid, ask = reservation_prices(0.5, 1, 1000)
        self.assertAlmostEqual(bid, 0.0)
        self.assertAlmostEqual(ask, math.log(2) / 1000)
        bid, ask = reservation_prices(0.5, -1, 1000)
        self.assertAlmostEqual(bid, 1.0 - math.log(2) / 1000)
        self.assertAlmostEqual(ask, 1.0)
        self.assertEqual(terminal_moments(0, 1e308, -1e308), (-1e308, 0))
        with self.assertRaises(ValueError):
            terminal_moments(0.5, 1e308, -1e308)

    def test_underlying_delta_times_sigma_equals_binary_diffusion(self):
        for sigma in (2.0, 6.0):
            for tau in (3.0, 100.0):
                p = fair_probability(105, 100, sigma, tau)
                h = 1e-4
                delta = (fair_probability(105 + h, 100, sigma, tau)
                         - fair_probability(105 - h, 100, sigma, tau)) / (2 * h)
                self.assertAlmostEqual(delta * sigma, price_volatility(p, tau), places=8)

    def test_invalid_pricing_scale_is_rejected(self):
        with self.assertRaises(ValueError):
            fair_probability(100, 100, float('nan'), 10)
        with self.assertRaises(ValueError):
            price_volatility(0.5, float('nan'))
        with self.assertRaises(ValueError):
            dynamic_sigma(1, -1, 2)


if __name__ == '__main__':
    unittest.main()
