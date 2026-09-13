"""Render three paper figures from the fixed public evidence release.

Requires matplotlib. No downloads, raw-tape processing or new model selection.
Methods: pricing_estimation.audit_feature_table and policy_audit.audit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
sys.path.insert(0, str(ROOT / "src"))
from btc5m_research.pricing_estimation import audit_feature_table, fit_ols


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "legend.fontsize": 8.5, "savefig.dpi": 220})
    output = PAPER / "figures"
    output.mkdir(exist_ok=True)
    publication = json.loads((ROOT / "evidence/publication_manifest.json").read_text(encoding="utf-8"))
    selected = ["data/pricing/slot_features.json", "data/mechanics/links_d4.json",
                "data/policy/w_slot_pnl.csv", "data/policy/frozen_calibration.json",
                "data/policy/w_archive.json"]
    expected = {x["path"]: x["sha256"] for x in publication["public_files"]}
    for name in selected:
        if sha(ROOT / name) != expected[name]:
            raise ValueError("Input differs from evidence release: " + name)
    manifest = {"version": 1, "evidence_revision": "6db010205b3aa3b8b4ee1d5715e06c47de8023b7",
                "scope": "Fixed public-input rechecks and archived-summary plots; no new strategy search or raw-tape reconstruction.",
                "inputs": {name: sha(ROOT / name) for name in selected}, "figures": {}}

    def finish(fig, name, details):
        for ax in fig.axes:
            ax.spines[["top", "right"]].set_visible(False)
            ax.set_axisbelow(True)
        dest = output / (name + ".png")
        fig.savefig(dest, facecolor="white", metadata={"Software": "matplotlib"})
        plt.close(fig)
        manifest["figures"][name] = {"file": "figures/" + dest.name, "sha256": sha(dest), **details}

    rows = json.loads((ROOT / selected[0]).read_text(encoding="utf-8"))
    audit = audit_feature_table(rows)
    colors = {"P01": "#2166ac", "P02": "#238b45", "P03": "#c25420",
              "P04": "#8c61a6", "P05": "#8e7b18"}
    markers = ["o", "s", "^", "D", "v"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.0), sharey=True, layout="constrained")
    for ax, feature, title in zip(axes, ["range2", "range2_pre"],
                                  ["Within-slot range", "Pre-slot range"]):
        for (group, color), marker in zip(colors.items(), markers):
            subset = [row for row in rows if row["source_group"] == group]
            ax.scatter([row[feature] for row in subset], [row["sigma_hat"] for row in subset],
                       color=color, marker=marker, label=group, s=16, alpha=.6, linewidths=0)
        fit = fit_ols([[float(row[feature])] for row in rows], [float(row["sigma_hat"]) for row in rows])
        end = max(float(row[feature]) for row in rows)
        ax.plot([0, end], [fit.predict([0]), fit.predict([end])], color="#17202a", lw=1.3)
        model = next(m for m in audit["models"] if m["features"] == [feature])
        ax.set(title=title, xlabel="Reference range (USD)", xlim=(0, end * 1.04),
               ylim=(0, max(row["sigma_hat"] for row in rows) * 1.08))
        ax.text(.04, .96, f"Full-table $R^2$ = {model['in_sample_r_squared']:.3f}\n"
                f"Log-wise $R^2$ = {model['logo_r_squared']:.3f}", transform=ax.transAxes,
                va="top", fontsize=9, bbox={"facecolor":"white", "alpha":.85, "edgecolor":"none"})
        ax.grid(axis="y", alpha=.17)
    axes[0].set_ylabel("Fitted market scale (USD / sqrt(second))")
    handles, labels = axes[1].get_legend_handles_labels()
    axes[1].legend(handles, labels, loc="lower right", frameon=False, ncol=2)
    finish(fig, "pricing-scale", {"n_slots": len(rows), "n_logs": len(colors),
                                  "lines": "Full-table OLS including intercept; all 358 cached rows.",
                                  "validation": "Leave-one-log-out, not chronological OOS.",
                                  "features": ["range2", "range2_pre"]})

    stats = json.loads((ROOT / selected[1]).read_text(encoding="utf-8"))["stats"]
    real, placebo = stats["5.0"], stats["placebo"]
    horizons = [.2, .4, .7, 1.5, 3.0]
    conditional = [real[f"conf{h}"] for h in horizons]
    unconditional = [(1-real["fizzle"])*(1-real["wrong"])*x for x in conditional]
    control = [(1-placebo["fizzle"])*(1-placebo["wrong"])*placebo[f"conf{h}"] for h in horizons]
    fig, ax = plt.subplots(figsize=(7.2, 3.55), layout="constrained")
    for values, label, color, marker, style in [
        (conditional, "Correct by horizon | eventual correct response", "#2166ac", "o", "-"),
        (unconditional, "Correct by horizon | all qualifying events", "#c25420", "s", "--"),
        (control, "Placebo: correct by horizon | all placebo events", "#666666", "^", ":")]:
        ax.plot(horizons, [100*x for x in values], label=label, color=color,
                marker=marker, linestyle=style, linewidth=1.5, markersize=4)
    ax.set(xlabel="Horizon after qualifying event (seconds)", ylabel="Confirmation probability (%)",
           xlim=(0, 3.1), ylim=(0, 105), yticks=[0, 20, 40, 60, 80, 100])
    ax.grid(axis="y", alpha=.17)
    ax.legend(loc="lower right", frameon=False)
    finish(fig, "book-confirmation", {"n_events": real["n"], "threshold_usd_over_200ms": 5,
                                      "horizons_seconds": horizons, "conditional": conditional,
                                      "unconditional_approximation": unconditional,
                                      "placebo_unconditional_approximation": control,
                                      "uncertainty": "Unavailable in archived summaries; lines join stored points only."})

    spec = importlib.util.spec_from_file_location("paper_policy_audit", ROOT / "estimators/policy_audit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = module.audit()
    pairs = list(policy["paired"])
    labels = ["EVM minus baseline", "EVM minus REB", "EVM minus scrambled EVM", "REB minus baseline"]
    means = [policy["paired"][name]["mean_cents_per_slot"] for name in pairs]
    intervals = [policy["paired"][name]["ci90"] for name in pairs]
    fig, ax = plt.subplots(figsize=(7.2, 3.0), layout="constrained")
    for i, (value, bounds) in enumerate(zip(means, intervals)):
        ax.errorbar(value, i, xerr=[[value-bounds[0]], [bounds[1]-value]],
                    fmt="o", color="#2166ac", capsize=4, markersize=5)
    ax.axvline(0, color="#777777", linewidth=.9, linestyle="--")
    ax.set(yticks=range(len(pairs)), yticklabels=labels, ylim=(-.65, 3.65), xlim=(-12, 107),
           xlabel="Paired mean difference (cents per slot; five-share base clip)")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=.17)
    finish(fig, "policy-comparison", {"n_common_slots": policy["n_slots"],
                                     "ci_method": policy["ci_method"], "paired": policy["paired"],
                                     "interpretation": "Recorded simulator outputs; proxy fills, unequal quantity treatment and retrospective decision availability remain limitations."})
    manifest["generator_sha256"] = sha(Path(__file__))
    (PAPER / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"figures": len(manifest["figures"]), "input_hashes_verified": len(selected),
                      "pricing_rows": len(rows), "policy_slots": policy["n_slots"]}))


if __name__ == "__main__":
    main()
