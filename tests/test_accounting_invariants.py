"""Accounting identities and the expected-value algebra.

These are the claims that must hold exactly, not approximately. If one of them
breaks, every downstream number in the study is meaningless.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btc5m_research import accounting, ev_chain  # noqa: E402


class TestFeeSchedule(unittest.TestCase):
    def test_rebate_is_exactly_twenty_percent_of_taker_fee(self) -> None:
        for price in (0.05, 0.2, 0.5, 0.73, 0.95):
            self.assertAlmostEqual(
                accounting.maker_rebate_cents(price),
                0.20 * accounting.taker_fee_cents(price),
                places=12,
                msg="the rebate is a fixed fraction of the fee schedule, not a fitted constant",
            )

    def test_both_schedules_peak_at_one_half(self) -> None:
        peak = accounting.taker_fee_cents(0.5)
        for price in (0.1, 0.3, 0.45, 0.55, 0.7, 0.9):
            self.assertLess(accounting.taker_fee_cents(price), peak)

    def test_maker_fee_is_zero(self) -> None:
        self.assertEqual(accounting.maker_fee_cents(0.4), 0.0)

    def test_schedules_scale_linearly_in_size(self) -> None:
        self.assertAlmostEqual(
            accounting.taker_fee_cents(0.4, size=7.0),
            7.0 * accounting.taker_fee_cents(0.4, size=1.0),
            places=12,
        )

    def test_prices_outside_the_open_interval_are_rejected(self) -> None:
        for bad in (0.0, 1.0, -0.1, 1.4):
            with self.assertRaises(ValueError):
                accounting.taker_fee_cents(bad)


class TestMatchedPairInvariant(unittest.TestCase):
    def test_matched_round_trip_equals_spread_plus_both_rebates(self) -> None:
        yes, no = 0.55, 0.47
        expected_spread_cents = (yes + no - 1.0) * 100.0
        expected = (
            expected_spread_cents
            + accounting.maker_rebate_cents(yes)
            + accounting.maker_rebate_cents(no)
        )
        self.assertAlmostEqual(accounting.matched_round_trip_cents(yes, no), expected, places=12)

    def test_matched_pair_is_direction_free(self) -> None:
        """The pair settles at $1 whatever happens, so the result carries no outcome term."""
        self.assertEqual(accounting.pair_settlement_value_dollars(3.0), 3.0)

    def test_selling_both_halves_at_one_dollar_earns_only_the_rebates(self) -> None:
        result = accounting.matched_round_trip_cents(0.5, 0.5)
        self.assertAlmostEqual(result, 2 * accounting.maker_rebate_cents(0.5), places=12)


class TestExpectedValueAlgebra(unittest.TestCase):
    def test_both_fill_branch_has_no_drift_term(self) -> None:
        """A flat book position cannot be hurt by subsequent drift.

        With both fill probabilities at 1 and rho at 1, the decision is certain to
        end matched, so the EV must equal spread plus both rebates no matter what
        drift is passed in.
        """
        quiet = ev_chain.slot_ev_cents(
            fill_a=1.0, fill_b=1.0, rho=1.0,
            spread_cents=2.0, rebate_a_cents=0.35, rebate_b_cents=0.35,
            drift_a_cents=0.0, drift_b_cents=0.0,
            edge_a_cents=1.0, edge_b_cents=1.0,
        )
        violent = ev_chain.slot_ev_cents(
            fill_a=1.0, fill_b=1.0, rho=1.0,
            spread_cents=2.0, rebate_a_cents=0.35, rebate_b_cents=0.35,
            drift_a_cents=40.0, drift_b_cents=-40.0,
            edge_a_cents=1.0, edge_b_cents=1.0,
        )
        self.assertAlmostEqual(quiet, violent, places=12)
        self.assertAlmostEqual(quiet, 2.0 + 0.35 + 0.35, places=12)

    def test_joint_fill_is_clipped_to_remain_coherent(self) -> None:
        """rho may exceed 1 numerically; P(both) can never exceed either marginal."""
        joint = ev_chain.joint_fill_probability(0.4, 0.6, rho=9.0)
        self.assertLessEqual(joint, 0.4)

    def test_anticorrelation_reduces_the_earning_branch(self) -> None:
        independent = ev_chain.joint_fill_probability(0.5, 0.5, rho=1.0)
        measured = ev_chain.joint_fill_probability(0.5, 0.5, rho=0.36 / 0.45)
        self.assertLess(measured, independent)

    def test_ev_is_linear_and_decreasing_in_alpha(self) -> None:
        weight = ev_chain.unmatched_weight(0.5, 0.5, rho=0.8)
        base = 0.6
        previous = math.inf
        for alpha in (0.0, 0.25, 0.5, 1.0, 2.0):
            value = ev_chain.ev_at_alpha_cents(base, weight, alpha)
            self.assertAlmostEqual(value, base - weight * alpha, places=12)
            self.assertLess(value, previous)
            previous = value

    def test_negative_ev_at_zero_admits_no_breakeven_alpha(self) -> None:
        """The core decision rule: a negative best case rejects every alpha >= 0."""
        weight = ev_chain.unmatched_weight(0.5, 0.5, rho=0.8)
        self.assertIsNone(ev_chain.breakeven_alpha_cents(-0.98, weight))

    def test_positive_ev_at_zero_yields_a_usable_threshold(self) -> None:
        weight = ev_chain.unmatched_weight(0.5, 0.5, rho=0.8)
        threshold = ev_chain.breakeven_alpha_cents(0.6, weight)
        self.assertIsNotNone(threshold)
        assert threshold is not None
        self.assertAlmostEqual(ev_chain.ev_at_alpha_cents(0.6, weight, threshold), 0.0, places=12)

    def test_alpha_cannot_be_negative(self) -> None:
        with self.assertRaises(ValueError):
            ev_chain.leg_value_cents(1.0, 0.35, 0.2, alpha_cents=-0.5)


if __name__ == "__main__":
    unittest.main()
