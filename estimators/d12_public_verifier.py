"""Reproduce the public D12c policy verdict from the canonical link output.

This is intentionally a verdict-layer reproducer. The event-level estimator remains
``d12_hazard_ev.py`` and requires the private raw tapes plus ``clean_index.json``.
The public verifier uses only Python's standard library and writes a deterministic,
machine-readable claim record.

Usage:
    python tools/mdp3/estimators/d12_public_verifier.py
    python tools/mdp3/estimators/d12_public_verifier.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "evidence" / "links_d12.json"
DEFAULT_OUTPUT = ROOT / "evidence" / "d12_public_verdict.json"


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise ValueError(f"missing {where}.{key}")
    return mapping[key]


def build_verdict(source_path: Path) -> dict[str, Any]:
    raw = source_path.read_bytes()
    source = json.loads(raw.decode("utf-8"))

    if source.get("version") != 1:
        raise ValueError(f"unsupported links_d12 version: {source.get('version')!r}")

    gates = _require(source, "gates", "root")
    oos = _require(_require(gates, "g3_oos", "gates"), "front_calm", "gates.g3_oos")
    blocks = _require(_require(gates, "g5_blocks", "gates"), "front_calm", "gates.g5_blocks")
    fill_placebo = _require(gates, "g2a_lam_perm", "gates")
    regime_placebo = _require(gates, "g2b_reg_shuffle", "gates")
    fflip_rows = _require(source, "fflip", "root")
    fresh = next((row for row in fflip_rows if row.get("label") == "F"), None)
    if fresh is None:
        raise ValueError("missing fflip row for fresh block F")

    discovery_positive = blocks["A"]["ev0"] > 0 and blocks["B"]["ev0"] > 0
    fresh_negative = fresh["ev0"] < 0
    fresh_ci_excludes_zero = fresh["ci90"][1] < 0
    chrono_oos_negative = oos["last30"]["ev0"] < 0
    frozen_model_negative = oos["ana_last30_frozen"]["ev0"] < 0
    trimmed_negative = fresh["ev0_trim_worst"] < 0

    # EV(alpha) = EV(0) - alpha * unmatched-fill weight, with alpha >= 0.
    # A negative EV(0) therefore rejects every non-negative alpha scenario.
    best_case_kill = fresh_negative and fresh_ci_excludes_zero
    rejected = (
        discovery_positive
        and best_case_kill
        and chrono_oos_negative
        and frozen_model_negative
        and trimmed_negative
    )

    verdict = {
        "schema_version": 1,
        "claim_id": "PUBLIC-D12C-STATIC-FRONT",
        "hypothesis": (
            "Static improve-inside-calm-front quoting retains positive expected value "
            "after 50 ms maker activation on fresh chronological OOS data."
        ),
        "decision": "DEAD" if rejected else "REVIEW",
        "external_wording": (
            "A latency-corrected replay rejected static front quoting on fresh OOS data."
            if rejected
            else "No publishable verdict; inspect the failed checks."
        ),
        "domain": "recorded-tape replay; virtual front fills; no live-profit claim",
        "metric": {
            "name": "EV(0)",
            "unit": "cents per eligible decision moment",
            "meaning": (
                "Matched/single-fill income, maker rebate, and observed post-fill drift with "
                "unknown adverse-selection alpha fixed at its favorable lower bound of zero."
            ),
            "monotonicity": "EV(alpha) cannot improve for alpha >= 0 when EV(0) is already negative",
        },
        "sample": {
            "fresh_moments": fresh["n"],
            "fresh_slots": fresh["n_slots"],
            "uncertainty_unit": "slot",
            "interval": "90% slot-cluster bootstrap",
        },
        "chronological_oos": {
            "first_70_ev0": oos["first70"]["ev0"],
            "last_30_ev0": oos["last30"]["ev0"],
            "last_30_frozen_analytic_ev0": oos["ana_last30_frozen"]["ev0"],
            "passed": not chrono_oos_negative,
        },
        "block_stability": {
            "A_ev0": blocks["A"]["ev0"],
            "B_ev0": blocks["B"]["ev0"],
            "F_ev0": blocks["F"]["ev0"],
            "discovery_blocks_positive": discovery_positive,
            "fresh_sign_stable": not fresh_negative,
        },
        "fresh_oos": {
            "ev0": fresh["ev0"],
            "ci90": fresh["ci90"],
            "ev0_after_removing_each_slot_once_worst_case": fresh["ev0_trim_worst"],
            "window_life_median_seconds": fresh["wl_med_s"],
            "components": fresh["comp"],
            "best_case_kill": best_case_kill,
        },
        "artifact_controls": {
            "side_split_fill_mechanism": {
                "ask_real": fill_placebo["ask"]["real"],
                "ask_lambda_permuted": fill_placebo["ask"]["lam_perm"],
                "ask_queue_permuted": fill_placebo["ask"]["r0_perm"],
                "bid_real": fill_placebo["bid"]["real"],
                "bid_lambda_permuted": fill_placebo["bid"]["lam_perm"],
                "bid_queue_permuted": fill_placebo["bid"]["r0_perm"],
                "interpretation": (
                    "Both sides show the same mechanism: queue permutation collapses discrimination; "
                    "trailing-flow permutation largely preserves it."
                ),
            },
            "regime_label_placebo": {
                "real_delta_cents": regime_placebo["real"],
                "shuffled_delta_cents": regime_placebo["plc"],
                "interpretation": "The real regime mapping separates outcomes more than shuffled labels.",
            },
            "promotion_effect": (
                "Controls support parts of the measurement model, but cannot rescue a policy whose "
                "favorable-bound fresh-OOS EV is negative."
            ),
        },
        "economics": {
            "maker_fee_cents": 0,
            "maker_rebate_included": True,
            "maker_activation_ms": 50,
            "unknown_alpha_assumption": 0,
            "capturable": False,
            "reason": "The favorable-bound replay is negative before adding any non-negative alpha cost.",
        },
        "checks": {
            "discovery_A_and_B_positive": discovery_positive,
            "fresh_EV0_negative": fresh_negative,
            "fresh_ci90_below_zero": fresh_ci_excludes_zero,
            "chronological_last30_negative": chrono_oos_negative,
            "frozen_analytic_last30_negative": frozen_model_negative,
            "fresh_leave_worst_out_still_negative": trimmed_negative,
        },
        "verdict_reason": (
            "The apparent discovery-period edge flips negative in fresh data. The 90% slot-cluster "
            "interval is entirely below zero even at alpha=0, and removing the worst slot does not "
            "restore the sign."
        ),
        "coverage": {
            "represented": [
                "50 ms maker activation",
                "book-derived quote prices",
                "maker rebates",
                "observed post-fill drift",
                "chronological and block splits",
            ],
            "not_represented": [
                "counterfactual queue response to our order",
                "exact live queue rank",
                "competitor response to our presence",
            ],
            "effect_on_negative_verdict": (
                "The result is used only to reject the static policy under favorable represented assumptions."
            ),
        },
        "source": {
            "path": source_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "methods": source.get("methods"),
            "estimator": "tools/mdp3/estimators/d12_hazard_ev.py",
        },
    }
    return verdict


def canonical_bytes(verdict: dict[str, Any]) -> bytes:
    return (json.dumps(verdict, indent=2, sort_keys=True) + "\n").encode("utf-8")


def print_summary(verdict: dict[str, Any]) -> None:
    fresh = verdict["fresh_oos"]
    oos = verdict["chronological_oos"]
    print(f"VERDICT: {verdict['decision']}")
    print(f"Metric: {verdict['metric']['name']} ({verdict['metric']['unit']})")
    print(
        "Chronological EV(0): "
        f"first70={oos['first_70_ev0']:+.4f}, last30={oos['last_30_ev0']:+.4f}, "
        f"frozen-last30={oos['last_30_frozen_analytic_ev0']:+.4f}"
    )
    print(
        f"Fresh block: {fresh['ev0']:+.4f}, ci90={fresh['ci90']}, "
        f"n={verdict['sample']['fresh_moments']} moments / "
        f"{verdict['sample']['fresh_slots']} slots"
    )
    print(verdict["verdict_reason"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the computed verdict with the committed output without modifying files.",
    )
    args = parser.parse_args()

    verdict = build_verdict(args.input.resolve())
    rendered = canonical_bytes(verdict)
    print_summary(verdict)

    if args.check:
        if not args.output.exists():
            print(f"CHECK FAILED: missing {args.output}", file=sys.stderr)
            return 2
        if args.output.read_bytes() != rendered:
            print(f"CHECK FAILED: {args.output} is stale", file=sys.stderr)
            return 1
        print("CHECK PASSED: committed verdict matches the canonical source output.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rendered)
    print(f"WROTE: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
