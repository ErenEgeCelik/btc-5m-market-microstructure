"""Causality tests: no future information, and no merged-feed artefact.

Two of the study's corrections were errors of exactly this shape. A fill counted
from the decision instant instead of from order activation reads the future. A
signal built on a merged two-venue series reads an artefact. Both produced
convincing positive results before they were caught.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btc5m_research import queue, quote_model  # noqa: E402


class TestLaggedReferenceIsCausal(unittest.TestCase):
    def setUp(self) -> None:
        self.series = [(0.0, 100.0), (1.0, 101.0), (2.0, 102.0), (3.0, 103.0)]

    def test_never_returns_a_tick_stamped_after_the_cutoff(self) -> None:
        value = quote_model.lagged_reference(self.series, now=2.5, lag_s=0.3)
        self.assertEqual(value, 102.0, "must use the 2.0 tick, not the 3.0 tick")

    def test_returns_none_before_any_tick_is_admissible(self) -> None:
        self.assertIsNone(quote_model.lagged_reference(self.series, now=0.2, lag_s=0.5))

    def test_appending_future_ticks_cannot_change_a_past_answer(self) -> None:
        before = quote_model.lagged_reference(self.series, now=2.5, lag_s=0.3)
        extended = self.series + [(4.0, 900.0), (5.0, 901.0)]
        after = quote_model.lagged_reference(extended, now=2.5, lag_s=0.3)
        self.assertEqual(before, after)

    def test_negative_lag_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            quote_model.lagged_reference(self.series, now=1.0, lag_s=-0.1)


class TestOrderActivationBlocksEarlyPrints(unittest.TestCase):
    def test_a_print_before_activation_cannot_fill(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=10.0)
        self.assertEqual(order.consume(now=10.0 + 0.049, volume=100.0), 0.0)
        self.assertEqual(order.filled, 0.0)

    def test_the_same_print_after_activation_fills(self) -> None:
        order = queue.RestingOrder(size=5.0, queue_ahead=0.0, placed_at=10.0)
        filled = order.consume(now=10.0 + 0.051, volume=100.0)
        self.assertEqual(filled, 5.0)

    def test_activation_uses_the_maker_path_not_the_taker_path(self) -> None:
        """50 ms maker activation, not the 250 ms server-delayed taker path."""
        self.assertEqual(queue.MAKER_POST_LATENCY_S, 0.050)
        self.assertGreater(queue.TAKER_PATH_LATENCY_S, queue.MAKER_POST_LATENCY_S)

    def test_fill_brackets_ignore_pre_activation_events(self) -> None:
        events = [(0.01, 50.0, 50.0), (0.20, 5.0, 5.0)]
        t_pes, t_opt = queue.fill_time_brackets(events, queue_ahead=4.0, active_from=0.05)
        self.assertEqual(t_pes, 0.20)
        self.assertEqual(t_opt, 0.20)


class TestMergedFeedArtefact(unittest.TestCase):
    """A persistent inter-venue level offset makes a merged series saw-tooth."""

    def setUp(self) -> None:
        # Two venues quoting a calm market, separated by a constant level offset.
        self.offset = 49.0
        self.ticks: list[tuple[float, str, float]] = []
        for i in range(10):
            self.ticks.append((2 * i + 0.0, "venue_a", 100_000.0))
            self.ticks.append((2 * i + 1.0, "venue_b", 100_000.0 - self.offset))

    @staticmethod
    def _max_abs_step(series: list[tuple[float, float]]) -> float:
        return max(
            (abs(later - earlier) for (_, earlier), (_, later) in zip(series, series[1:])),
            default=0.0,
        )

    def test_single_venue_series_is_flat_in_a_calm_market(self) -> None:
        single = quote_model.single_feed_series(self.ticks, "venue_a")
        self.assertEqual(self._max_abs_step(single), 0.0)

    def test_merged_series_manufactures_jumps_of_the_offset_size(self) -> None:
        merged = quote_model.merged_last_value_series(self.ticks)
        self.assertAlmostEqual(self._max_abs_step(merged), self.offset, places=9)

    def test_a_spike_detector_fires_on_the_merged_series_only(self) -> None:
        threshold = 5.0
        single = quote_model.single_feed_series(self.ticks, "venue_a")
        merged = quote_model.merged_last_value_series(self.ticks)
        self.assertEqual(self._fires(single, threshold), 0)
        self.assertGreater(self._fires(merged, threshold), 0)

    @staticmethod
    def _fires(series: list[tuple[float, float]], threshold: float) -> int:
        return sum(
            1
            for (_, earlier), (_, later) in zip(series, series[1:])
            if abs(later - earlier) >= threshold
        )


if __name__ == "__main__":
    unittest.main()
