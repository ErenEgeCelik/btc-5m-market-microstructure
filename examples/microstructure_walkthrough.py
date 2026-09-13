"""Synthetic examples of temporal alignment, activation and censoring semantics."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from btc5m_research.microstructure import (
    ArrivalSeries, FillObservation, decompose_depth, empirical_fill_table,
    first_book_response, fit_exponential_hazard, normalize_trade,
)
from btc5m_research.queue import RestingOrder


def demonstrate() -> dict:
    book = ArrivalSeries([0.9, 1.1, 1.3], [0.50, 0.49, 0.53])
    order = RestingOrder(size=5, queue_ahead=10, placed_at=1)
    before_activation = order.consume(1.02, 15)
    after_activation = order.consume(1.06, 12)
    order.request_cancel(1.10)
    cancel_race_fill = order.consume(1.12, 3)
    observations = [FillObservation(.2, .1, 10, 100), FillObservation(.2, None, 10, 100),
                    FillObservation(5, 2, 10, 100), FillObservation(5, None, 10, 100)]
    return {
        "input_kind": "synthetic; no empirical estimate",
        "asof_1s": book.at(1.0, .5),
        "up_spike_first_response": first_book_response(book, 1, 1),
        "down_sell_normalized": normalize_trade("down", "SELL", .4, 5),
        "depth_interval": decompose_depth({51: 100, 52: 200}, {51: 40, 53: 80}, {51: 45, 52: 50}),
        "order_fills_sh": {"pre_activation": before_activation, "after_activation": after_activation,
                           "during_cancel": cancel_race_fill, "total": order.filled},
        "five_second_curve": empirical_fill_table(observations, 5),
        "hazard_fit_on_synthetic_observations": fit_exponential_hazard(observations),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = demonstrate()
    if args.json:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        print(result["input_kind"])
        print("First book response:", result["up_spike_first_response"]["status"])
        print("Own-order fills:", result["order_fills_sh"])
        print("Only the two full-capacity observations enter the 5-second curve.")
