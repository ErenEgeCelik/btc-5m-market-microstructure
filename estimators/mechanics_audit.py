"""Audit compact recorded inputs and archived aggregates, without network access.

Definitions: docs/data-engineering.md, market-response.md, queue-and-fill-mechanics.md.
This does not regenerate event-level estimates, fits or bootstrap intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from btc5m_research.clean_index import Outage, slot_health


def audit(root: Path = ROOT) -> dict:
    manifest = json.loads((root / "evidence/mechanics_experiments.json").read_text(encoding="utf-8"))
    checks = []

    def check(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})
        if not passed:
            raise ValueError(f"Mechanics audit failed: {name}")

    for row in manifest["inputs"]:
        path = (root / row["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("input path escapes repository")
        check("sha256: " + row["path"], hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"])

    def read(name: str) -> dict:
        return json.loads((root / "data/mechanics" / name).read_text(encoding="utf-8"))

    health = read("b05_health_excerpt.json")
    gaps = [Outage(a / 1000, b / 1000) for a, b in health["book_gap_intervals_ms"]]
    health_rows = []
    for start, expected in health["slots"].items():
        actual = slot_health(float(start), health["t0_ms"] / 1000, health["t1_ms"] / 1000,
                             gaps, expected["a0"], expected["a1"])
        check("B05 slot health: " + start, actual == expected)
        health_rows.append({"slot_start": int(start), **actual})

    d4 = read("links_d4.json")["stats"]
    direction = {}
    for label, row in d4.items():
        correct = 1 - row["wrong"]
        direction[label] = {
            "archived_n": row.get("n"), "correct_given_nonfizzle": correct,
            "correct_by_400ms_product_of_rounded_fields": (1-row["fizzle"]) * correct * row["conf0.4"],
            "archived_correct_latency_p50_ms": row["lat"] * 1000,
        }
        check("D4 probability domain: " + label,
              all(0 <= v <= 1 for k, v in row.items() if k.startswith("conf") or k in {"fizzle", "wrong"}))

    d4b = read("links_d4b.json")
    transfers = []
    tol = manifest["audit_tolerance"]["rounded_transfer_ratio"]
    for bucket, row in d4b["buckets"].items():
        ratio = row["b_mean"]["2.0"] / row["s_mean"]
        check("D4b rounded transfer: " + bucket, abs(ratio - row["r"]["2.0"]) <= tol)
        transfers.append({"bucket": bucket, "n_feed": row["n"], "n_book_2s": row["b_n"]["2.0"],
                          "recomputed_from_rounded_means_c_per_usd": ratio})
    check("D4b per-tape raw count", sum(r["raw"] for r in d4b["per_tape"].values()) == d4b["counters"]["raw"])
    check("D4b per-tape bucket count", sum(r["kovali"] for r in d4b["per_tape"].values()) == d4b["buckets"]["ALL_ge3"]["n"])
    counters = d4b["counters"]
    check("D4b selection accounting", counters["raw"] - sum(counters[k] for k in
          ("fizzle", "yanlis_yon", "s_stale", "s_alt3")) == d4b["buckets"]["ALL_ge3"]["n"])

    d7 = read("links_d7.json")
    check("D7 side count", d7["n"]["bid"] + d7["n"]["ask"] == d7["n"]["samples"])
    check("D7 per-tape sample count", sum(r["n"] for r in d7["per_tape"].values()) == d7["n"]["samples"])
    check("D7 per-tape FULL slots", sum(r["n_full"] for r in d7["per_tape"].values()) == d7["n"]["full_slots"])
    for horizon, pes in d7["curves"]["pes"].items():
        opt = d7["curves"]["opt"][horizon]
        check("D7 common denominator and bracket: " + horizon,
              all(p["n"] == o["n"] and (p["n"] == 0 or 0 <= p["p"] <= o["p"] <= 1)
                  for p, o in zip(pes, opt)))
    cells = [c for c in d7["fit"]["cells"].values() if c["n"] >= d7["params"]["min_cell"]]
    mad = sum(c["n"] * abs(c["obs"] - c["mod"]) for c in cells) / sum(c["n"] for c in cells)
    check("D7 weighted MAD from rounded cells", abs(mad - d7["fit"]["mad_w"]) <= manifest["audit_tolerance"]["rounded_probability_or_MAD"])
    # This is an archived diagnostic comparison, not a newly performed permutation.
    delta_discrimination = d7["placebo"]["discrim_placebo"] - d7["placebo"]["discrim_real"]

    d14 = read("links_d14.json")
    for kind, count in d14["n"].items():
        check("D14 event count: " + kind, d14["rows"][kind]["n"] == count)
    check("D14 spike8 block count", sum(d14["rows"]["spike8|" + block]["n"] for block in "ABF") == d14["n"]["spike8"])
    check("D14 placebo block count", sum(d14["rows"]["plc|" + block]["n"] for block in "ABF") == d14["n"]["plc"])
    spike, placebo = d14["rows"]["spike5"], d14["rows"]["plc"]
    flow_ratios = [a / b for a, b in zip(spike["tv_threat"], placebo["tv_threat"])]
    return {
        "scope": "eight recorded health slots plus archived aggregate arithmetic; no event-level rerun",
        "checks": checks, "health_slots": health_rows, "d4": direction, "d4b": transfers,
        "d7": {"samples": d7["n"]["samples"], "full_slots": d7["n"]["full_slots"],
               "weighted_mad_from_rounded_cells": mad,
               "archived_lambda_placebo_minus_real_discrimination": delta_discrimination,
               "verdict": "lambda permutation preserves discrimination; lambda-information hypothesis not supported"},
        "d14": {"event_counts": d14["n"], "spike5_to_calm_trade_ratios_by_bin": flow_ratios,
                "removal_50ms_ratio_of_archived_mean_percentages": spike["canc_threat_pct50"] / placebo["canc_threat_pct50"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the full audit as JSON")
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        print(f"Mechanics audit: {len(result['checks'])} checks passed.")
        print(result["scope"])
        print("D7:", result["d7"]["verdict"])


if __name__ == "__main__":
    main()
