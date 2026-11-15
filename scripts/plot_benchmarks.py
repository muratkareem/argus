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


if __name__ == "__main__":
    main()
