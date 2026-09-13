import importlib.util
import json
import math
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btc5m_research.ev_chain import fill_branches, joint_fill_probability, slot_ev_cents
from btc5m_research.policy import (
    DecisionState, adverse_side, choose_action, fill_lookup,
    fill_precedes_cancel, regime_from_move,
)

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.cal = json.loads((ROOT / "data/policy/frozen_calibration.json").read_text())
        self.state = DecisionState(49, 52, 225, 225, 4.09, 4.09, 0, 80, "R0")

    def test_frechet_partition_over_probability_grid(self):
        for a in (0, .1, .4, .8, 1):
            for b in (0, .1, .4, .8, 1):
                for rho in (0, .1, 1, 2, 10):
                    out = fill_branches(a, b, rho)
                    self.assertTrue(all(p >= -1e-14 for p in vars(out).values()))
                    self.assertAlmostEqual(sum(vars(out).values()), 1)
                    self.assertAlmostEqual(out.both + out.only_a, a)
                    self.assertAlmostEqual(out.both + out.only_b, b)

    def test_historical_joint_error_is_material_when_marginals_large(self):
        historical = min(.9 * .8 * .1, .9, .8)
        self.assertLess(1 - .9 - .8 + historical, 0)
        self.assertAlmostEqual(joint_fill_probability(.9, .8, .1), .7)

    def test_pair_reward_has_no_unmatched_drift_or_hidden_cost(self):
        # Two shares sold as a split pair: Up=51c, Down=50c => 1c trading.
        out = slot_ev_cents(1, 1, 1, 1, .3, .3, 999, 999, .5, .5, 99)
        self.assertAlmostEqual(out, 1.6)
        self.assertAlmostEqual(5 * out / 100, .08)  # five paired units, dollars

    def test_one_leg_uses_one_rebate_and_one_drift_cost(self):
        out = slot_ev_cents(.4, 0, 1, 1, .3, .3, 2, 999, .5, .5, .2)
        self.assertAlmostEqual(out, .4 * (.5 + .3 - 2 - .2))

    def test_both_then_correct_favorable_side_during_moves(self):
        self.assertEqual(choose_action(self.state, self.cal).action, "both")
        self.assertEqual(choose_action(replace(self.state, regime="R+"), self.cal).action, "B")
        self.assertEqual(choose_action(replace(self.state, regime="R-"), self.cal).action, "A")

    def test_book_prices_do_not_change_with_regime(self):
        for regime in ("R0", "R+", "R-", "NEUT"):
            out = choose_action(replace(self.state, regime=regime), self.cal)
            self.assertEqual((out.ask_up_cents, out.bid_up_cents), (51, 50))

    def test_two_cent_book_stays_at_touch(self):
        out = choose_action(replace(self.state, bid_cents=50), self.cal)
        self.assertEqual((out.ask_up_cents, out.bid_up_cents), (52, 50))

    def test_reb_forces_reducing_side_even_when_negative_ev(self):
        out = choose_action(replace(self.state, regime="R+", net_up_shares=10), self.cal)
        self.assertLess(out.unit_ev_cents["A"], 0)
        self.assertEqual(out.ask_quantity_shares, 10)
        self.assertEqual(out.bid_quantity_shares, 5)

    def test_clamp_blocks_inventory_increase_but_not_reduction(self):
        long = choose_action(replace(self.state, net_up_shares=15), self.cal)
        short = choose_action(replace(self.state, net_up_shares=-15), self.cal)
        self.assertEqual((long.ask_quantity_shares, long.bid_quantity_shares), (15, 0))
        self.assertEqual((short.ask_quantity_shares, short.bid_quantity_shares), (0, 15))

    def test_unknown_is_not_calm_or_neutral(self):
        self.assertIsNone(regime_from_move(None))
        self.assertIsNone(regime_from_move(math.nan))
        self.assertEqual(choose_action(replace(self.state, regime=None), self.cal).action, "none")

    def test_time_boundary_and_regime_thresholds(self):
        self.assertEqual(choose_action(replace(self.state, elapsed_seconds=200), self.cal).action, "flatten")
        self.assertEqual(choose_action(replace(self.state, elapsed_seconds=9), self.cal).action, "none")
        self.assertEqual([regime_from_move(x) for x in (2.99, 3, 7.99, 8, -8)],
                         ["R0", "NEUT", "NEUT", "R+", "R-"])

    def test_scrambled_brain_changes_label_only(self):
        out = choose_action(self.state, self.cal, scrambled=True)
        equivalent = choose_action(replace(self.state, regime="R+"), self.cal)
        self.assertEqual(out, equivalent)

    def test_zero_front_probability_preserved(self):
        self.cal["front_pfill"] = {"A": 0.0, "B": 0.0}
        out = choose_action(self.state, self.cal)
        self.assertEqual(out.action, "none")
        self.assertEqual(out.unit_ev_cents, {"none": 0, "A": 0, "B": 0, "both": 0})

    def test_lookup_boundary_matches_digitize_right_false(self):
        self.assertEqual(fill_lookup(self.cal, "A", 2.5, 100),
                         self.cal["tables"]["A"]["0.25-0.5"]["p"])
        self.assertEqual(fill_lookup(self.cal, "A", 4, 0), 0)

    def test_no_pre_activation_credit_and_conservative_cancel_tie(self):
        self.assertFalse(fill_precedes_cancel(10.049, 10, None, 11))
        self.assertTrue(fill_precedes_cancel(10.05, 10, None, 11))
        self.assertTrue(fill_precedes_cancel(10.25, 10, 10.2, 11))
        self.assertFalse(fill_precedes_cancel(10.251, 10, 10.2, 11))
        self.assertFalse(fill_precedes_cancel(11.01, 10, None, 11))
        self.assertEqual(adverse_side(1), "A")
        self.assertEqual(adverse_side(-1), "B")

    def test_bad_inputs_are_rejected(self):
        for changes in ({"bid_cents": 52}, {"ask_flow_shares_per_second": -1},
                        {"net_up_shares": math.inf}, {"regime": "calm"}):
            with self.assertRaises(ValueError): replace(self.state, **changes)
        with self.assertRaises(ValueError): joint_fill_probability(.5, .5, math.nan)
        self.cal["delta"]["ask"]["R0"] = math.nan
        with self.assertRaises(ValueError): choose_action(self.state, self.cal)


class PairedAuditTests(unittest.TestCase):
    def test_paired_bootstrap_keeps_common_slot_noise_paired(self):
        spec = importlib.util.spec_from_file_location("policy_audit", ROOT / "estimators/policy_audit.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        baseline = [1000, -1000, 20, -20]
        treatment = [x + 3 for x in baseline]
        out = module.paired_interval([a - b for a, b in zip(treatment, baseline)], 100)
        self.assertEqual(out, {"mean_cents_per_slot": 3, "ci90": [3, 3]})


if __name__ == "__main__":
    unittest.main()
