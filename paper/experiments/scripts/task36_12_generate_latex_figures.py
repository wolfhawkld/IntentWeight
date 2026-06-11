#!/usr/bin/env python3
"""Generate pdflatex-compatible IntentWeight figure assets."""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/intentweight-matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "paper" / "full_draft" / "figures"
TARGET = ROOT / "paper" / "latex" / "figures"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save(fig: plt.Figure, name: str) -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        TARGET / name,
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(fig)


def system_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis("off")
    boxes = {
        "Query": (0.3, 3.1, 1.2, 0.7, "#e8f4fd"),
        "Features": (2.0, 3.1, 1.3, 0.7, "#eefcf6"),
        "LinUCB": (3.9, 3.1, 1.3, 0.7, "#fff7e6"),
        "Dense fallback": (6.0, 4.0, 1.5, 0.55, "#f5f7fa"),
        "BM25 path": (6.0, 3.1, 1.5, 0.55, "#f5f7fa"),
        "Cluster-local": (6.0, 2.2, 1.5, 0.55, "#f5f7fa"),
        "Context budget": (8.4, 3.1, 1.7, 0.7, "#eefcf6"),
        "Generator": (8.4, 1.3, 1.7, 0.65, "#e8f4fd"),
        "Trust feedback": (3.9, 0.7, 1.7, 0.65, "#fff1f2"),
    }
    for label, (x, y, width, height, color) in boxes.items():
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.05",
                facecolor=color,
                edgecolor="#425466",
                linewidth=1.0,
            )
        )
        ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=9)

    def arrow(start: tuple[float, float], end: tuple[float, float]) -> None:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, color="#425466"))

    arrow((1.5, 3.45), (2.0, 3.45))
    arrow((3.3, 3.45), (3.9, 3.45))
    arrow((5.2, 3.45), (6.0, 4.27))
    arrow((5.2, 3.45), (6.0, 3.37))
    arrow((5.2, 3.45), (6.0, 2.47))
    arrow((7.5, 4.27), (8.4, 3.58))
    arrow((7.5, 3.37), (8.4, 3.45))
    arrow((7.5, 2.47), (8.4, 3.32))
    arrow((9.25, 3.1), (9.25, 1.95))
    arrow((8.4, 1.62), (5.6, 1.02))
    arrow((4.75, 1.35), (4.55, 3.1))
    ax.text(0.3, 4.75, "IntentWeight evidence-selection controller", fontsize=13, weight="bold")
    ax.text(
        0.3,
        4.5,
        "Dense remains a recall floor; LinUCB controls local routes and final context budget.",
        fontsize=9,
        color="#52606d",
    )
    save(fig, "figure1_system_diagram.pdf")


def token_quality() -> None:
    rows = read_csv("figure2_token_quality_frontier_data.csv")
    scales = [row["scale"] for row in rows]
    policy_hit_delta = [float(row["policy_hit_delta_pp"]) for row in rows]
    dense_hit_delta = [float(row["dense_adaptive_hit_delta_pp"]) for row in rows]
    policy_saving = [float(row["policy_saving_pct"]) for row in rows]
    dense_saving = [float(row["dense_adaptive_saving_pct"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6))
    axes[0].plot(scales, policy_hit_delta, marker="o", label="IntentWeight budget")
    axes[0].plot(scales, dense_hit_delta, marker="o", label="Dense adaptive truncation")
    axes[0].axhline(0.0, color="#52606d", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Hit@10 delta vs dense (pp)")
    axes[0].set_xlabel("LoTTE corpus scale")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].plot(scales, policy_saving, marker="o", label="IntentWeight budget")
    axes[1].plot(scales, dense_saving, marker="o", label="Dense adaptive truncation")
    axes[1].set_ylabel("Final context token saving (%)")
    axes[1].set_xlabel("LoTTE corpus scale")
    axes[1].grid(alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    save(fig, "figure2_token_quality_frontier.pdf")


def geometry() -> None:
    rows = read_csv("figure3_geometry_diagnostics_data.csv")
    scales = [row["scale"] for row in rows]
    cluster_hit = [float(row["nearest_cluster_hit_at_3"]) for row in rows]
    retention = [float(row["context_retention_at_10"]) for row in rows]
    variance = [float(row["pca_var64"]) for row in rows]

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.plot(scales, cluster_hit, marker="o", label="NearestClusterHit@3")
    ax.plot(scales, retention, marker="o", label="ContextRetention@10")
    ax.plot(scales, variance, marker="o", label="PCAvar@64")
    ax.set_xlabel("LoTTE corpus scale")
    ax.set_ylabel("Diagnostic value")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    save(fig, "figure3_geometry_diagnostics.pdf")


def main() -> None:
    system_diagram()
    token_quality()
    geometry()
    print("figure_assets=3")
    print("latex_figures=passed")


if __name__ == "__main__":
    main()
