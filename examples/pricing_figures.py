"""Render the frozen pricing audit (optional matplotlib dependency, no downloads)."""

from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btc5m_research.pricing_estimation import audit_feature_table, fit_ols

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "figures/pricing")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw = (ROOT / "data/pricing/slot_features.json").read_bytes()
    manifest = json.loads((ROOT / "data/pricing/manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != manifest["data_sha256"]:
        raise ValueError("pricing fixture hash differs from its manifest")
    rows = json.loads(raw)
    audit = audit_feature_table(rows)
    colors = {"P01": "#39729f", "P02": "#40968e", "P03": "#cf7046",
              "P04": "#9975b5", "P05": "#a39245"}
    fig = plt.figure(figsize=(12, 10), facecolor="white", layout="constrained")
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.08])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    y_max = max(float(row["sigma_hat"]) for row in rows) * 1.08
    for ax, feature, title, subtitle in zip(
        axes, ["range2", "range2_pre"],
        ["Within-slot range", "Pre-slot range"],
        ["Window: slot + 30 to + 150 seconds", "Window: slot - 120 seconds to slot boundary"],
    ):
        for group, color in colors.items():
            subset = [row for row in rows if row["source_group"] == group]
            ax.scatter([row[feature] for row in subset], [row["sigma_hat"] for row in subset],
                       color=color, label=f"{group} (n={len(subset)})", s=19, alpha=0.62,
                       linewidths=0)
        fit = fit_ols([[float(row[feature])] for row in rows], [float(row["sigma_hat"]) for row in rows])
        end = max(float(row[feature]) for row in rows)
        ax.plot([0, end], [fit.predict([0]), fit.predict([end])], color="#273340", lw=1.5,
                label="Full-table OLS")
        model = next(model for model in audit["models"] if model["features"] == [feature])
        ax.set_title(f"{title}\n{subtitle}", fontsize=12, loc="left", pad=12)
        ax.set_xlabel("Reference range (USD)")
        ax.set_ylabel("Fitted market scale (USD / sqrt(second))")
        ax.set_ylim(0, y_max)
        ax.set_xlim(left=0)
        ax.text(0.03, 0.96, f"Full-table R² = {model['in_sample_r_squared']:.3f}\n"
                f"Log-wise R² = {model['logo_r_squared']:.3f}", transform=ax.transAxes,
                va="top", fontsize=10,
                bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})
    axes[1].legend(loc="upper right", fontsize=8, frameon=False)
    comparison = fig.add_subplot(grid[1, :])
    labels = ["Within-slot range", "Pre-slot range", "Within-slot range + DVOL",
              "Within-slot range + |flow 30 s|", "Within-slot range + DVOL + |flow 30 s|",
              "Pre-slot range + DVOL + |flow 30 s|", "Within-slot range + DVOL + |flow 2 min|"]
    scores = [model["logo_r_squared"] for model in audit["models"]]
    bars = comparison.barh(labels, scores, color=["#39729f", "#40968e", "#273340",
                                                "#a4b7c7", "#a4b7c7", "#a4b7c7", "#a4b7c7"])
    comparison.invert_yaxis()
    comparison.set_xlim(0, 0.40)
    comparison.set_xlabel("Pooled leave-one-log-out R² against cached market-implied scale")
    comparison.set_title("Seven fixed historical candidates · 358 slots across five logs",
                         fontsize=12, loc="left", pad=12)
    for bar, score in zip(bars, scores):
        comparison.text(score + 0.006, bar.get_y() + bar.get_height() / 2,
                        f"{score:.3f}", va="center", fontsize=10)
    for ax in [*axes, comparison]:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y" if ax in axes else "x", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle("Explaining the fitted pricing scale", fontsize=17, weight="bold", x=0.05, ha="left")
    fig.supxlabel("Archived-feature recheck, not a raw-tape rerun. Log-wise validation is not chronological OOS.\n"
                  "Within-slot range is contemporaneous; DVOL hourly-close availability is unverified.\n"
                  "Feature feed: median(Coinbase, Bitstamp, Kraken). Source: data/pricing/manifest.json.",
                  fontsize=10, ha="left", x=0.05)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg"]:
        fig.savefig(output / f"scale_feature_audit.{suffix}", dpi=170, facecolor="white")
    plt.close(fig)
    print(f"Rendered scale_feature_audit.png and .svg in {output} from 358 frozen rows.")


if __name__ == "__main__":
    main()
