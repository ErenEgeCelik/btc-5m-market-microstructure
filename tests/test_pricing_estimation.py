import math
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btc5m_research.pricing_estimation import (
    audit_feature_table, fit_ols, fit_transformed_schedule, leave_one_group_out, r_squared,
    variance_inflation_factors,
)
from btc5m_research.quote_model import (
    lagged_reference, predicted_mid, range_scale, synchronized_reference,
    transformed_quote_target, time_ema, hybrid_probability,
)


class PricingEstimationTests(unittest.TestCase):
    def test_archived_feature_recheck_matches_identified_report(self):
        fixture = Path(__file__).resolve().parents[1] / "data/pricing/slot_features.json"
        result = audit_feature_table(json.loads(fixture.read_text(encoding="utf-8")))
        self.assertEqual(result["n"], 358)
        self.assertEqual(result["selected_features"], ["range2", "dvol_per_sqrt_s"])
        # Rounded external checkpoints from the archived June16 report, not generated expectations.
        self.assertAlmostEqual(result["models"][0]["logo_r_squared"], 0.271, delta=0.0005)
        self.assertAlmostEqual(result["models"][2]["logo_r_squared"], 0.321, delta=0.0005)
        fit = result["models"][2]["full_fit"]
        self.assertAlmostEqual(fit["intercept"], -24.05, delta=0.005)
        self.assertAlmostEqual(fit["coefficients"][1], 5.425, delta=0.0005)

    def test_schedule_anchor_and_scale_are_distinct(self):
        x = [-30, -10, 0, 20, 40]
        tau = [270, 230, 180, 100, 40]
        mids = [predicted_mid(value + 7.5, 5, t) for value, t in zip(x, tau)]
        fit = fit_transformed_schedule(x, mids, tau)
        self.assertAlmostEqual(fit["sigma_usd_per_sqrt_s"], 5)
        self.assertAlmostEqual(fit["anchor_offset_usd"], 7.5)
        self.assertAlmostEqual(fit["transformed_r_squared"], 1)

    def test_negative_schedule_slope_is_not_a_positive_volatility(self):
        with self.assertRaises(ValueError):
            fit_transformed_schedule([-1, 0, 1], [0.8, 0.5, 0.2], [100] * 3)

    def test_intercept_regression_is_invariant_to_feature_units(self):
        design = [[1, 2], [3, 1], [7, 4], [2, 9], [6, 3]]
        target = [7 + 2 * a - 0.3 * b for a, b in design]
        fit = fit_ols([[a * 1e5, b / 100] for a, b in design], target)
        self.assertAlmostEqual(fit.intercept, 7)
        self.assertAlmostEqual(fit.coefficients[0], 2e-5)
        self.assertAlmostEqual(fit.coefficients[1], -30)
        self.assertAlmostEqual(fit.predict([4e5, 0.06]), 13.2)

    def test_rank_deficiency_is_rejected(self):
        with self.assertRaises(ValueError):
            fit_ols([[1, 2], [2, 4], [3, 6]], [1, 2, 3])

    def test_invalid_regression_shapes_and_values_are_rejected(self):
        for design, target in [([], []), ([[1], [2]], [1]),
                               ([[1], [math.nan]], [1, 2]), ([[1], [2]], [1, math.inf])]:
            with self.subTest(design=design), self.assertRaises(ValueError):
                fit_ols(design, target)

    def test_held_out_targets_cannot_change_their_fold_fit(self):
        rows = [{"source_group": group, "x": x, "sigma_hat": 1 + 2 * x}
                for group in ["A", "B", "C"] for x in [1, 2, 4]]
        first = leave_one_group_out(rows, ["x"])
        changed = [{**row, "sigma_hat": row["sigma_hat"] +
                    (100 if row["source_group"] == "C" else 0)} for row in rows]
        second = leave_one_group_out(changed, ["x"])
        before = next(fold for fold in first["folds"] if fold["held_out_group"] == "C")
        after = next(fold for fold in second["folds"] if fold["held_out_group"] == "C")
        self.assertEqual(before, after)
        self.assertLess(second["logo_r_squared"], first["logo_r_squared"])
        self.assertEqual(sum(f["n_test"] for f in first["folds"]), len(rows))

    def test_log_wise_validation_requires_multiple_groups(self):
        rows = [{"source_group": "A", "x": x, "sigma_hat": x} for x in [1, 2, 3]]
        with self.assertRaises(ValueError):
            leave_one_group_out(rows, ["x"])

    def test_negative_r_squared_is_retained(self):
        self.assertLess(r_squared([0, 1], [10, 10]), 0)
        with self.assertRaises(ValueError):
            r_squared([1, 1], [1, 1])

    def test_orthogonal_features_have_unit_vif(self):
        rows = [{"a": a, "b": b} for a, b in [(-1, -1), (-1, 1), (1, -1), (1, 1)]]
        self.assertEqual(variance_inflation_factors(rows, ["a", "b"]), {"a": 1, "b": 1})

    def test_asof_composite_ignores_future_and_keeps_membership(self):
        streams = {"cb": [(9.0, 110), (10.0, 150)], "bn": [(9.2, 90), (10.1, 1000)]}
        self.assertEqual(synchronized_reference(streams, 10.2, 0.3, 2), 100)
        self.assertIsNone(synchronized_reference(streams, 10.2, 0.3, 0.8))

    def test_missing_member_does_not_become_a_single_feed(self):
        self.assertIsNone(synchronized_reference({"cb": [(1, 100)], "bn": []}, 1))

    def test_reference_lookup_rejects_out_of_order_data(self):
        with self.assertRaises(ValueError):
            lagged_reference([(2, 100), (1, 50)], 2, 0)

    def test_probability_boundaries_and_nonfinite_values(self):
        for mid, tau in [(0, 1), (1, 1), (0.5, math.nan), (0.5, math.inf)]:
            with self.subTest(mid=mid, tau=tau), self.assertRaises(ValueError):
                transformed_quote_target(mid, tau)
        with self.assertRaises(ValueError):
            predicted_mid(math.nan, 3, 100)

    def test_range_rule_is_named_historical_arithmetic(self):
        self.assertAlmostEqual(range_scale(60), 5.22)
        with self.assertRaises(ValueError):
            range_scale(-1)

    def test_time_ema_decay_is_independent_of_sampling_frequency(self):
        once = time_ema(0, 10, 2, 20)
        repeated = 0
        for _ in range(20):
            repeated = time_ema(repeated, 10, 0.1, 20)
        self.assertAlmostEqual(once, repeated, places=12)
        self.assertEqual(time_ema(3, 10, 0, 20), 3)
        with self.assertRaises(ValueError):
            time_ema(3, 10, -1, 20)

    def test_hybrid_level_removes_basis_and_keeps_feed_movement(self):
        self.assertAlmostEqual(hybrid_probability(70050, -50, 70000, 4, 120), 0.5)
        self.assertGreater(hybrid_probability(70060, -50, 70000, 4, 120), 0.5)


if __name__ == "__main__":
    unittest.main()
