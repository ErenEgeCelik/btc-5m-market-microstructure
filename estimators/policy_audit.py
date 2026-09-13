"""Recheck frozen historical policy-output rows; never invokes trading infrastructure.

Default is a public, stdlib-only audit. --extract-private is a maintainer-only
deterministic source export; see data/policy/README.md for predeclared selection.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/policy"
ARMS = ("base", "reb", "evm", "evmplc")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(source_root: Path):
    sources = {
        "policy_output": "tools/mdp3/links/links_d8.json",
        "calibration": "tools/mdp3/links/links_d12_calib.json",
        "health": "tools/mdp3/links/clean_index.json",
        "policy_source": "tools/mdp3/estimators/d8_unified.py",
        "calibration_source": "tools/mdp3/estimators/d12_hazard_ev.py",
        "methods": "MDP3_METHODS.md", "state": "PROJECT_STATE.md",
        "research_log": "RESEARCH_LOG.md", "mdp2_chain": "tools/mdp2/chain.py",
        "mdp2_links": "tools/mdp2/links.py", "mdp2_spec": "MDP2_SPEC.md",
        "mdp2_audit": "MDP2_AUDIT.md", "derivation": "MDP_EV_MATH.md",
    }
    read = lambda name: json.loads((source_root / sources[name]).read_text(encoding="utf-8"))
    archive, health, cal = read("policy_output"), read("health"), read("calibration")
    by_slot = {}
    for tape, record in health["tapes"].items():
        if tape.startswith("W"):
            for slot, status in record["slots"].items():
                if status["cls"] == "FULL":
                    if slot in by_slot:
                        raise ValueError("ambiguous FULL slot in multiple tapes")
                    by_slot[slot] = tape
    keys = set(archive["slots"]["base|pes"])
    for arm in ARMS:
        if set(archive["slots"][arm + "|pes"]) != keys:
            raise ValueError("variant universes differ; selection must be reviewed")
    if not keys <= set(by_slot):
        raise ValueError("archived policy output includes non-FULL or non-W slots")
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "w_slot_pnl.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["slot_epoch_seconds", "tape", *[a + "_cents" for a in ARMS]])
        for slot in sorted(keys, key=int):
            writer.writerow([slot, by_slot[slot], *[archive["slots"][a + "|pes"][slot] for a in ARMS]])
    cal["source"] = "Frozen blocks A+B only; F excluded. Historical D12 export."
    (DATA / "frozen_calibration.json").write_text(json.dumps(cal, indent=2) + "\n", encoding="utf-8", newline="\n")
    selected = {key: value for key, value in archive["variants"].items()
                if key.endswith("|pes") or key == "reb|opt"}
    record = {"snapshot": "D16 W01-W08, 368 FULL slots, historical simulator output",
              "params": archive["params"], "variants": selected, "paired": archive["d15_evm"],
              "interval_method": "Original NumPy default_rng, 1000 slot bootstrap replicates; means use unrounded P&L.",
              "not_recomputed": ["original fill paths", "rebates by slot", "D11/D15 original A+B+F intervals"]}
    (DATA / "w_archive.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    evidence = {
        "version": 1, "extraction_date": "2026-09-14", "reproduction_level": "recorded simulator-output recheck",
        "sources": {name: {"path": path, "sha256_raw": sha(source_root / path)} for name, path in sources.items()},
        "source_symbols": {"policy_source": ["main EVM branch", "main._tab", "main.reb_walk", "main.reg_at", "boot_ci90"],
                           "calibration_source": ["main calibration export"], "mdp2_chain": ["Chain", "Param", "Chain.simulate"]},
        "producer_version_note": "The available d8 source evolved to add D17 branches after this W snapshot. The retained base/REB/EVM formula is source-mapped; no claim that its current byte hash was the exact historical producer.",
        "selection": "All archived pes base/REB/EVM/EVMPLC slots, matched one-to-one and checked against W FULL status. No P&L filtering.",
        "n_slots": len(keys), "tapes": sorted(set(by_slot[k] for k in keys)),
        "first_slot_utc": datetime.fromtimestamp(min(map(int, keys)), timezone.utc).isoformat(),
        "last_slot_utc": datetime.fromtimestamp(max(map(int, keys)), timezone.utc).isoformat(),
        "historical_reports": [
            {"id": "D11-1013", "source": "PROJECT_STATE.md D11", "n_slots": 1013,
             "metric": "REB minus base cents/slot", "estimate": 10.9, "ci90": [2.5, 19.5],
             "scope": "Historical rounded report. Fresh F=146 slots; three fresh tapes improved. Original per-slot archive not present in this release."},
            {"id": "D15-1013", "source": "PROJECT_STATE.md D15", "n_slots": 1013,
             "metric": "EVM minus REB cents/slot", "estimate": 67.8, "ci90": [53, 82],
             "scope": "Historical rounded A+B+F report; calibration A+B, F held out; scrambled-regime paired difference +16.7 [9,24]."},
            {"id": "D15-grown-F", "source": "PROJECT_STATE.md grown-F", "n_fresh_slots": 371,
             "metric": "EVM minus base cents/slot on F", "estimate": 83.8, "ci90": [56.5, 111.7],
             "scope": "Historical rounded report; separate from both original F=146 and current W=368."},
        ],
        "public_changes": ["Fréchet lower bound added to joint fill weights", "unknown regime held separately", "zero calibration values preserved", "finite and book input validation"],
        "limitations": ["Hypothetical queue access; pes/opt are conventions, not proven bounds", "Full REB quantity credited on proxy fill time without quantity-dependent fill probability", "Retrospective settle-group endpoint availability was not established online", "JOIN drift and joint estimates transfer to front, front-calm rates transfer to other regimes, and 10-second fill probabilities rank variable-duration windows", "W paper harness was defective; no economic inference from its P&L", "Slot bootstrap does not address dependence across neighboring slots", "No current oracle or fee-rule claim"],
        "public_files": {"data/policy/" + name: {"sha256": sha(DATA / name)} for name in
                         ("w_slot_pnl.csv", "frozen_calibration.json", "w_archive.json")},
    }
    (ROOT / "evidence/policy_experiments.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")


def percentile(values, fraction):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * fraction
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def paired_interval(values, n_bootstrap=2000, seed=17):
    if not values or n_bootstrap <= 0:
        raise ValueError("nonempty slot differences and positive bootstrap count required")
    rng = random.Random(seed)
    draws = [mean(rng.choices(values, k=len(values))) for _ in range(n_bootstrap)]
    return {"mean_cents_per_slot": mean(values),
            "ci90": [percentile(draws, .05), percentile(draws, .95)]}


def audit(data=DATA):
    evidence = json.loads((ROOT / "evidence/policy_experiments.json").read_text(encoding="utf-8"))
    for relative, expected in evidence["public_files"].items():
        # Text exports are checked using LF-normalized bytes to tolerate git autocrlf.
        actual = hashlib.sha256((ROOT / relative).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != expected["sha256"]:
            raise ValueError("input hash mismatch: " + relative)
    with (data / "w_slot_pnl.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    slots = [int(row["slot_epoch_seconds"]) for row in rows]
    if slots != sorted(set(slots)) or len(slots) != evidence["n_slots"]:
        raise ValueError("slot order, uniqueness or count mismatch")
    values = {arm: [float(row[arm + "_cents"]) for row in rows] for arm in ARMS}
    split = round(.7 * len(rows))
    out = {"scope": "Historical W simulator-output audit, not live P&L or a corrected-policy rerun",
           "n_slots": len(rows), "ci_method": "paired slot bootstrap; 2000 replicates; seed=17; stdlib RNG",
           "means_cents_per_slot": {arm: mean(value) for arm, value in values.items()},
           "paired": {}, "per_tape": {}, "chronological_descriptive_split": {}, "hashes_verified": True}
    for a, b in (("evm", "base"), ("evm", "reb"), ("evm", "evmplc"), ("reb", "base")):
        out["paired"][a + "-" + b] = paired_interval([x - y for x, y in zip(values[a], values[b])])
    for tape in sorted({row["tape"] for row in rows}):
        subset = [row for row in rows if row["tape"] == tape]
        out["per_tape"][tape] = {"n_slots": len(subset), **{
            arm: mean(float(row[arm + "_cents"]) for row in subset) for arm in ARMS}}
    for arm, numbers in values.items():
        out["chronological_descriptive_split"][arm] = {
            "first70": {"n_slots": split, "mean_cents_per_slot": mean(numbers[:split])},
            "last30": {"n_slots": len(rows) - split, "mean_cents_per_slot": mean(numbers[split:])}}
    archive = json.loads((data / "w_archive.json").read_text(encoding="utf-8"))
    out["max_mean_difference_from_archive_cents"] = max(abs(mean(values[arm]) -
        archive["variants"][arm + "|pes"]["pnl_per_slot"]) for arm in ARMS)
    if out["max_mean_difference_from_archive_cents"] > .001:
        raise ValueError("means differ by more than archived per-slot rounding permits")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print a machine-readable audit")
    parser.add_argument("--extract-private", type=Path, help="maintainer source root, unavailable in public repo")
    args = parser.parse_args()
    if args.extract_private:
        extract(args.extract_private)
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["scope"])
        print(f"{result['n_slots']} matched slots; hashes verified")
        for pair, value in result["paired"].items():
            print(f"{pair}: {value['mean_cents_per_slot']:+.4f} cents/slot; 90% interval {value['ci90']}")


if __name__ == "__main__":
    main()
