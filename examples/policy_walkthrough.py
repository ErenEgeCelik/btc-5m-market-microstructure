"""Synthetic book states, recorded A+B calibration: one-step EV and REB decisions."""
import argparse
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btc5m_research.policy import DecisionState, choose_action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cal = json.loads((root / "data/policy/frozen_calibration.json").read_text())
    base = DecisionState(49, 52, 225, 225, 4.09, 4.09, 0, 80, "R0")
    states = {"calm": base, "up_move": replace(base, regime="R+"),
              "down_move": replace(base, regime="R-"),
              "long_inventory": replace(base, regime="R+", net_up_shares=10),
              "clamped_long": replace(base, net_up_shares=15),
              "unknown_feed": replace(base, regime=None),
              "flatten_time": replace(base, elapsed_seconds=200)}
    out = {"scope": __doc__, "cases": {name: {"state": asdict(state),
           "decision": asdict(choose_action(state, cal))} for name, state in states.items()}}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(out["scope"])
        for name, case in out["cases"].items():
            d = case["decision"]
            print(f"{name}: {d['action']}, A={d['ask_quantity_shares']} B={d['bid_quantity_shares']} shares")
            ev = {key: round(value, 3) for key, value in d['unit_ev_cents'].items()}
            print(f"  EV cents per unit: {ev}; {d['reason']}")


if __name__ == "__main__":
    main()
