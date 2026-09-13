"""Recompute archived scale-feature fits and show synthetic schedule construction."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btc5m_research.pricing_estimation import audit_feature_table, fit_transformed_schedule
from btc5m_research.quote_model import (
    hybrid_probability, predicted_mid, range_scale, synchronized_reference, time_ema,
)

def run() -> dict[str, object]:
    data_path = ROOT / "data/pricing/slot_features.json"
    manifest = json.loads((ROOT / "data/pricing/manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if digest != manifest["data_sha256"]:
        raise ValueError("pricing fixture hash differs from its manifest")
    rows = json.loads(data_path.read_text(encoding="utf-8"))
    if len(rows) != manifest["n_rows"]:
        raise ValueError("pricing fixture count differs from its manifest")
    audit = audit_feature_table(rows)
    displacement = [-20.0, -8.0, -1.0, 4.0, 17.0, 25.0]
    tau_s = [240.0, 210.0, 170.0, 130.0, 90.0, 50.0]
    mids = [predicted_mid(x + 3.0, 4.0, tau) for x, tau in zip(displacement, tau_s)]
    synthetic = {
        "label": "synthetic arithmetic demonstration; no empirical performance claim",
        "input_sigma": 4.0, "input_anchor_offset_usd": 3.0,
        "fitted_schedule": fit_transformed_schedule(displacement, mids, tau_s),
        "range_rule_at_60_usd": range_scale(60.0),
        "hybrid_step": {
            "label": "synthetic offset/gap arithmetic, already aligned observations",
            "old_offset_usd": -50.0, "observed_oracle_minus_feed_usd": -46.0,
            "updated_offset_usd": time_ema(-50.0, -46.0, 1.0, 20.0),
            "fair": hybrid_probability(70060, time_ema(-50, -46, 1, 20), 70000, 4, 120),
            "gap_cents": 100 * (0.06 - time_ema(0.02, 0.06, 1, 15)),
        },
        "as_of_composite": synchronized_reference(
            {"coinbase": [(9.0, 70020.0), (10.0, 70060.0)],
             "binance": [(9.2, 69980.0), (10.1, 70100.0)]},
            now=10.2, lag_s=0.3, max_age_s=2.0,
        ),
    }
    return {"data_sha256": digest, "synthetic": synthetic, "archived_feature_audit": audit}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit full audit including fitted folds")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, allow_nan=False))
        return
    fit = result["synthetic"]["fitted_schedule"]
    print("Pricing construction and archived feature audit")
    print(f"Synthetic schedule: recovered sigma {fit['sigma_usd_per_sqrt_s']:.3f} USD/sqrt(s), "
          f"anchor offset {fit['anchor_offset_usd']:+.3f} USD.")
    hybrid = result["synthetic"]["hybrid_step"]
    print(f"Synthetic hybrid update: offset {hybrid['updated_offset_usd']:.3f} USD; "
          f"separate high-pass example {hybrid['gap_cents']:.3f} cents/share.")
    audit = result["archived_feature_audit"]
    print(f"Recorded derived inputs: {audit['n']} slots, 5 logs. Fixture hash verified.")
    print(f"{'Features':49} {'In-sample R2':>12} {'Log-wise R2':>12}")
    for model in audit["models"]:
        label = " + ".join(model["features"])
        print(f"{label:49} {model['in_sample_r_squared']:12.3f} {model['logo_r_squared']:12.3f}")
    print("Archived selection: " + " + ".join(audit["selected_features"] or ["none"]))
    print("Log-wise validation; within-slot features and DVOL timing limits apply.")
    print("No chronological final test or trading performance is established. See docs/pricing-estimation.md.")


if __name__ == "__main__":
    main()
