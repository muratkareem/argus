"""Render published measurements only; optional plotting tool, never trains models.

Run: uv run --with matplotlib==3.11.2 python scripts/plot_benchmarks.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main():
    research = ROOT / "docs/research"
    paths = [research / f"diploma-ulb-{s}.json" for s in ("stratified", "chronological")]
    paths += [research / f"benchmarks/paysim-{s}.json" for s in ("stratified", "chronological")]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), layout="constrained")
    for ax, path in zip(axes.flat, paths):
        report = json.loads(path.read_text())
        models = report["models"]
        labels = [
            m["name"] + (" *" if m["name"] == report["selected_model"] else "") for m in models
        ]
        values = [m["test"]["average_precision"] for m in models]
        prevalence = report["partitions"]["test"]["fraud"] / report["partitions"]["test"]["rows"]
        bars = ax.barh(
            labels,
            values,
            color=[
                "#157a78" if m["name"] == report["selected_model"] else "#7e98a5" for m in models
            ],
        )
        ax.bar_label(bars, fmt="%.4f", padding=4)
        ax.axvline(
            prevalence, color="#b44a28", linestyle="--", label=f"Test prevalence {prevalence:.4%}"
        )
        ax.set_xlim(0, 1.10)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xlabel("Held-out average precision (AP)")
        ax.invert_yaxis()
        dataset = "ULB (real)" if "diploma-ulb" in path.name else "PaySim (synthetic, 200k sample)"
        ax.set_title(
            f"{dataset} · {report['split']}\nTest: {report['partitions']['test']['rows']:,} rows / {report['partitions']['test']['fraud']} fraud",
            fontsize=10,
        )
        ax.legend(fontsize=8, loc="lower right")
        ax.spines[["right", "top"]].set_visible(False)
    fig.suptitle(
        "Independent in-domain experiments; not cross-dataset transfer\n* Model chosen by validation AP, before test evaluation",
        fontsize=13,
    )
    fig.savefig(
        research / "benchmarks/comparison.png",
        dpi=160,
        metadata={
            "Description": "Measured ULB and PaySim AP; independently trained models. PaySim attribution: Lopez-Rojas, Elmir, Axelsson, EMSS 2016; CC BY-SA 4.0. ULB: Worldline/ULB, ODbL/DbCL."
        },
    )
    plt.close(fig)


def full_study_figures():
    """Visualize all preregistered seeds; never select a seed using test scores."""
    research = ROOT / "docs/research"
    summary = json.loads((research / "paysim-full-summary.json").read_text())
    attribution = {
        "Description": "PaySim full-source study; Lopez-Rojas, Elmir, Axelsson, EMSS 2016; dataset CC BY-SA 4.0. Conditional seed/cluster uncertainty; no cross-dataset transfer claim."
    }
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    for ax, group in zip(axes, sorted(summary["groups"], key=lambda g: g["split"], reverse=True)):
        models = group["models"]
        values = [m["test"]["average_precision"]["mean"] for m in models]
        spread = [m["test"]["average_precision"]["sample_std"] for m in models]
        ax.barh([m["name"] for m in models], values, xerr=spread, color="#157a78", capsize=4)
        ax.invert_yaxis()
        for index, (value, std) in enumerate(zip(values, spread)):
            ax.text(value + std + 0.015, index, f"{value:.4f} ± {std:.4f}", va="center", fontsize=9)
        ax.set_xlim(0, 1.1)
        ax.set_xlabel("Test AP · mean ± sample SD across 3 seeds")
        ax.set_title(
            f"Full PaySim · {group['split']}\n{group['rows']:,} rows; seeds 42, 2026, 2027",
            fontsize=10,
        )
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "Repeated-seed sensitivity on one synthetic dataset\nOverlapping/shared test records: SD is descriptive, not a population confidence interval",
        fontsize=12,
    )
    fig.savefig(research / "benchmarks/paysim-full-reliability.png", dpi=160, metadata=attribution)
    plt.close(fig)

    primary = {
        split: json.loads((research / f"benchmarks/paysim-full-{split}-seed42.json").read_text())
        for split in ("stratified", "chronological")
    }
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    daily = {}
    for partition in ("train", "validation", "test"):
        for row in primary["chronological"]["temporal_audit"][partition]:
            day = int((row["hour"] - 1) // 24)
            count, fraud = daily.get(day, (0, 0))
            daily[day] = (count + row["rows"], fraud + row["fraud"])
    days = sorted(daily)
    axes[0, 0].plot(days, [daily[d][0] for d in days], label="All events")
    axes[0, 0].plot(days, [daily[d][1] for d in days], label="Fraud events")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("Full source volume by simulation day")
    axes[0, 0].set_ylabel("Event count (log scale)")
    axes[0, 0].legend()
    axes[0, 1].plot(days, [100 * daily[d][1] / daily[d][0] for d in days], color="#b44a28")
    axes[0, 1].set_title("Full source daily fraud prevalence")
    axes[0, 1].set_ylabel("Observed fraud (%)")
    for ax in axes[0]:
        ax.set_xlabel("Simulation day, floor((step − 1) / 24)")
    for ax, split in zip(axes[1], ("stratified", "chronological")):
        report = primary[split]
        model = next(m for m in report["models"] if m["name"] == report["selected_model"])
        points = sorted(
            model["validation_threshold_analysis"]["points"], key=lambda p: p["threshold"]
        )
        for key in ("precision", "recall", "f1"):
            ax.plot([p["threshold"] for p in points], [p[key] for p in points], label=key)
        ax.axvline(model["threshold"], linestyle="--", color="black", label="Validation F1 choice")
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("Threshold · validation data only")
        ax.set_title(f"{split} · seed 42 · {model['name']}", fontsize=10)
        ax.legend(fontsize=8)
    fig.suptitle(
        "PaySim temporal distribution and validation threshold sensitivity\nTest scores remain fixed at the preselected validation threshold",
        fontsize=12,
    )
    fig.savefig(research / "benchmarks/paysim-full-diagnostics.png", dpi=160, metadata=attribution)
    plt.close(fig)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-study", action="store_true")
    args = parser.parse_args()
    if args.full_study:
        full_study_figures()
    else:
        main()
