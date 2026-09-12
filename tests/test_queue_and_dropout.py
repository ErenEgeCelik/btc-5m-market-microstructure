"""Queue denominators, bracket coherence, and dropout masking.

Covers two release-blocker concerns:

* **queue denominators** -- what a fill probability is divided by, and that the
  pessimist and optimist arms stay ordered rather than crossing;
* **dropout masking** -- that a frozen feed is excluded rather than read as a calm
  market.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btc5m_research import clean_index, queue  # noqa: E402


class TestQueueDenominators(unittest.TestCase):
    def test_depth_ahead_must_be_cleared_before_any_fill(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=200.0, placed_at=0.0)
        self.assertEqual(order.consume(now=1.0, volume=199.0), 0.0)
        self.assertEqual(order.consume(now=1.1, volume=1.0), 0.0)
        self.assertEqual(order.consume(now=1.2, volume=5.0), 5.0)

    def test_fill_never_exceeds_order_size(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=0.0)
        order.consume(now=1.0, volume=10_000.0)
        self.assertEqual(order.filled, 5.0)
        self.assertTrue(order.is_complete)

    def test_partial_fills_accumulate_without_double_counting(self) -> None:
        order = queue.RestingOrder(size=6.0, queue_ahead=10.0, placed_at=0.0)
        self.assertEqual(order.consume(now=1.0, volume=10.0), 0.0)
        self.assertEqual(order.consume(now=1.1, volume=2.0), 2.0)
        self.assertEqual(order.consume(now=1.2, volume=3.0), 3.0)
        self.assertEqual(order.filled, 5.0)

    def test_negative_volume_is_rejected(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=0.0)
        with self.assertRaises(ValueError):
            order.consume(now=1.0, volume=-1.0)

    def test_optimist_bracket_never_fills_later_than_pessimist(self) -> None:
        """The optimist arm sees a superset of the pessimist arm by construction."""
        events = [(1.0, 1.0, 6.0), (2.0, 1.0, 1.0), (3.0, 1.0, 1.0), (4.0, 1.0, 1.0)]
        t_pes, t_opt = queue.fill_time_brackets(events, queue_ahead=4.0, active_from=0.0)
        self.assertIsNotNone(t_pes)
        self.assertIsNotNone(t_opt)
        assert t_pes is not None and t_opt is not None
        self.assertLessEqual(t_opt, t_pes)

    def test_unexplained_size_drops_only_help_the_optimist_arm(self) -> None:
        events = [(1.0, 0.0, 10.0)]
        t_pes, t_opt = queue.fill_time_brackets(events, queue_ahead=5.0, active_from=0.0)
        self.assertIsNone(t_pes, "trades alone never cleared the queue")
        self.assertEqual(t_opt, 1.0, "cancellations ahead of us promoted the optimist arm")


class TestCancellationRace(unittest.TestCase):
    def test_order_remains_fillable_during_the_cancel_window(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=0.0)
        order.request_cancel(now=1.0)
        self.assertEqual(order.consume(now=1.02, volume=5.0), 5.0)

    def test_order_is_dead_after_the_cancel_window(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=0.0)
        order.request_cancel(now=1.0)
        self.assertEqual(order.consume(now=1.2, volume=5.0), 0.0)

    def test_repeated_cancel_requests_do_not_extend_the_window(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=0.0)
        order.request_cancel(now=1.0)
        order.request_cancel(now=1.04)
        self.assertEqual(order.consume(now=1.06, volume=5.0), 0.0)


class TestDropoutMask(unittest.TestCase):
    def setUp(self) -> None:
        self.event_times = [0.0, 0.4, 0.8, 33.0, 33.4, 36.0]
        self.outages = clean_index.detect_outages(self.event_times)
        self.index = clean_index.CleanIndex(self.outages)

    def test_a_long_silence_is_detected_as_an_outage(self) -> None:
        self.assertEqual(len(self.outages), 2)
        self.assertAlmostEqual(self.outages[0].duration_s, 32.2, places=9)

    def test_short_gaps_are_not_outages(self) -> None:
        quiet = clean_index.detect_outages([0.0, 0.4, 0.8, 1.2])
        self.assertEqual(quiet, [])

    def test_timestamps_inside_an_outage_are_not_clean(self) -> None:
        self.assertFalse(self.index.is_clean(15.0))

    def test_outage_endpoints_are_treated_as_observed(self) -> None:
        self.assertTrue(self.index.is_clean(0.8))
        self.assertTrue(self.index.is_clean(33.0))

    def test_filtering_removes_exactly_the_frozen_stretch(self) -> None:
        candidates = [0.5, 10.0, 20.0, 33.2, 35.0]
        self.assertEqual(self.index.filter(candidates), [0.5, 33.2])

    def test_coverage_reports_the_observed_fraction(self) -> None:
        index = clean_index.CleanIndex([clean_index.Outage(10.0, 20.0)])
        self.assertAlmostEqual(index.coverage(0.0, 100.0), 0.9, places=9)

    def test_an_empty_mask_accepts_everything(self) -> None:
        self.assertTrue(clean_index.CleanIndex([]).is_clean(12.3))

    def test_unsorted_event_times_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            clean_index.detect_outages([5.0, 1.0])

    def test_overlapping_outages_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            clean_index.CleanIndex(
                [clean_index.Outage(0.0, 10.0), clean_index.Outage(5.0, 15.0)]
            )


if __name__ == "__main__":
    unittest.main()
