"""Temporal and denominator failure modes from the historical measurement program."""
import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from btc5m_research.clean_index import CleanIndex, Outage, slot_health
from btc5m_research.microstructure import (
    ArrivalSeries, FillObservation, calm_before_spike, decompose_depth,
    empirical_fill_table, first_book_response, fit_exponential_hazard,
    hazard_probability, normalize_trade,
)
from btc5m_research.queue import RestingOrder, fill_time_brackets


class TestArrivalAndResponse(unittest.TestCase):
    def test_asof_does_not_take_nearer_future_tick(self):
        s = ArrivalSeries([0, .99, 1.001], [10, 11, 900])
        self.assertEqual(s.at(1, .1), 11)
        self.assertIsNone(s.at(-1, 1))
        self.assertIsNone(s.at(2, .5))

    def test_same_timestamp_last_observation_is_already_known(self):
        s = ArrivalSeries([0, 0, .2], [.5, .6, .61])
        self.assertAlmostEqual(first_book_response(s, 0, 1)["signed_move_c"], 1)

    def test_wrong_first_move_is_not_rescued_by_later_agreement(self):
        s = ArrivalSeries([0, .1, .2], [.5, .49, .55])
        self.assertEqual(first_book_response(s, 0, 1)["status"], "wrong")

    def test_interrupted_response_is_not_quiet(self):
        s = ArrivalSeries([0, 2], [.5, .6])
        self.assertEqual(first_book_response(s, 0, 1)["status"], "structural_break")

    def test_horizon_is_measured_from_event(self):
        s = ArrivalSeries([0, .1, .5], [.5, .5, .6])
        self.assertEqual(first_book_response(s, .1, 1, horizon=.2)["status"], "fizzle")

    def test_calm_window_ends_before_spike(self):
        s = ArrivalSeries([i / 10 for i in range(31)], [100] * 29 + [108, 108])
        self.assertTrue(calm_before_spike(s, 3))
        self.assertIsNone(calm_before_spike(s, .1))

    def test_empty_or_intermittent_feed_is_unknown(self):
        self.assertIsNone(calm_before_spike(ArrivalSeries([], []), 3))
        self.assertIsNone(calm_before_spike(ArrivalSeries([0, 2.8], [100, 100]), 3))

    def test_series_is_validated_and_detached_from_mutable_inputs(self):
        t, v = [0, 1], [10, 20]
        s = ArrivalSeries(t, v)
        v[0] = 999
        self.assertEqual(s.at(0, 0), 10)
        with self.assertRaises(ValueError): ArrivalSeries([1, 0], [1, 2])
        with self.assertRaises(ValueError): ArrivalSeries([0], [math.nan])

    def test_four_trade_normalizations(self):
        for token, taker, side, price in [("up", "BUY", "ask", .4), ("up", "SELL", "bid", .4),
                                         ("down", "SELL", "ask", .6), ("down", "BUY", "bid", .6)]:
            result = normalize_trade(token, taker, .4, 5)
            self.assertEqual(result["maker_side"], side)
            self.assertAlmostEqual(result["price"], price)


class TestDepthAndFill(unittest.TestCase):
    def test_depth_joins_by_price_not_level_rank(self):
        r = decompose_depth({51: 100, 52: 200}, {51: 40, 53: 80}, {51: 45, 52: 50})
        self.assertEqual(r["unexplained_removal"], 165)
        self.assertEqual(r["net_addition"], 80)

    def test_trades_are_not_counted_again_as_cancels(self):
        self.assertEqual(decompose_depth({50: 100}, {50: 30}, {50: 70})["unexplained_removal"], 0)

    def test_short_capacity_fills_do_not_bias_long_horizon(self):
        samples = [FillObservation(.2, .1, 10, 100), FillObservation(.2, None, 10, 100),
                   FillObservation(5, 2, 10, 100), FillObservation(5, None, 10, 100)]
        cell = empirical_fill_table(samples, 5)[2]
        self.assertEqual((cell["n"], cell["fills"], cell["p"]), (2, 1, .5))

    def test_fill_at_capacity_included_and_later_fill_rejected(self):
        self.assertEqual(empirical_fill_table([FillObservation(2, 2, 0, 1)], 2)[0]["p"], 1)
        with self.assertRaises(ValueError): FillObservation(2, 2.01, 1, 1)

    def test_hazard_uses_exposure_and_excludes_zero_lambda(self):
        r = fit_exponential_hazard([FillObservation(3, 1, 2, 4), FillObservation(3, None, 2, 4),
                                    FillObservation(3, 1, 0, 4)])
        self.assertEqual(r, {"k": .5, "events": 1, "rate_weighted_exposure": 2,
                            "positive_rate_n": 2, "zero_rate_n": 1})
        self.assertEqual(hazard_probability(2, 0, 100, 5), 0)
        self.assertGreater(hazard_probability(1e-12, 1, 1, 1), 0)

    def test_activation_and_cancel_boundaries(self):
        order = RestingOrder(2, 3, 1)
        self.assertEqual(order.consume(1.049, 100), 0)
        self.assertEqual(order.consume(order.active_from, 4), 1)
        order.request_cancel(2)
        self.assertEqual(order.consume(2.05, 100), 0)

    def test_queue_depletion_differs_from_own_clip_completion(self):
        self.assertEqual(fill_time_brackets([(1, 10, 10)], 10, 0), (1, 1))
        self.assertEqual(RestingOrder(5, 10, 0).consume(1, 10), 0)

    def test_out_of_order_or_nonfinite_queue_input_rejected(self):
        with self.assertRaises(ValueError): fill_time_brackets([(2, 2, 0), (1, 2, 0)], 2, 0)
        with self.assertRaises(ValueError): RestingOrder(-5, 10, 0)
        with self.assertRaises(ValueError): RestingOrder(5, 10, 0).consume(1, math.nan)


class TestHealthAndArchive(unittest.TestCase):
    def test_exact_gap_threshold_is_not_over_threshold(self):
        self.assertEqual(slot_health(0, 0, 300, [Outage(10, 11.5)], True, True)["cov15"], 1)

    def test_health_classes_and_missing_tape_edges(self):
        self.assertEqual(slot_health(0, 0, 300, [], True, True)["cls"], "FULL")
        gaps = [Outage(10 + 3*i, 12 + 3*i) for i in range(10)]
        self.assertEqual(slot_health(0, 0, 300, gaps, True, True)["cls"], "OK8")
        self.assertEqual(slot_health(0, 0, 300, [], False, True)["cls"], "NOANC")
        self.assertEqual(slot_health(0, 100, 300, [], True, True)["cls"], "BAD")
        self.assertIsNone(slot_health(0, 200, 300, [], True, True))

    def test_window_checks_interior_outages_not_just_endpoints(self):
        mask = CleanIndex([Outage(10, 20)])
        self.assertTrue(mask.is_clean(0) and mask.is_clean(30))
        self.assertFalse(mask.covers_window(0, 30))
        self.assertTrue(mask.covers_window(20, 30))

    def test_frozen_inputs_and_aggregate_reconciliation(self):
        spec = importlib.util.spec_from_file_location("mechanics_audit", ROOT / "estimators/mechanics_audit.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.audit()
        self.assertEqual(len(result["health_slots"]), 8)
        self.assertTrue(all(c["passed"] for c in result["checks"]))


if __name__ == "__main__":
    unittest.main()
