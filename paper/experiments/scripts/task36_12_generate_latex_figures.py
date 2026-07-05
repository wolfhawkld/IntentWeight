#!/usr/bin/env python3
"""Generate pdflatex-compatible IntentRoute figure assets."""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/intentroute-matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "paper" / "full_draft" / "figures"
TARGET = ROOT / "paper" / "latex" / "figures"
MM_TO_INCH = 1.0 / 25.4
FULL_WIDTH_INCH = 190.0 * MM_TO_INCH

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 7.0,
        "axes.labelsize": 7.5,
        "axes.titlesize": 8.0,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0,
        "legend.fontsize": 7.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save(fig: plt.Figure, name: str) -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        TARGET / name,
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(fig)


def row_label(row: dict[str, str]) -> str:
    domain = row.get("domain", "technology/search")
    prefix = "tech" if domain == "technology/search" else "sci"
    return f"{prefix}\n{row['scale']}"


def domain_groups(rows: list[dict[str, str]]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        groups.setdefault(row.get("domain", "technology/search"), []).append(idx)
    return groups


def domain_name(domain: str) -> str:
    return "technology" if domain == "technology/search" else "science"


def row_chunks(row: dict[str, str]) -> float:
    if row.get("corpus_chunks"):
        return float(row["corpus_chunks"])
    scale = row["scale"]
    fallback = {
        "20k/q200": 20490.0,
        "100k": 101311.0,
        "200k": 201010.0,
        "400k": 400674.0,
        "638k": 638509.0,
    }
    return fallback[scale]


def set_chunk_axis(ax: plt.Axes) -> None:
    ticks = [20490, 101311, 201010, 400674, 638509]
    labels = ["20k", "100k", "200k", "400k", "638k"]
    ax.set_xticks(ticks, labels)
    ax.set_xlabel("Corpus chunks")


def system_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis("off")
    boxes = {
        "Query": (0.3, 3.1, 1.2, 0.7, "#e8f4fd"),
        "Features": (2.0, 3.1, 1.3, 0.7, "#eefcf6"),
        "Dense global": (4.4, 4.0, 1.5, 0.55, "#f5f7fa"),
        "BM25 global": (4.4, 3.1, 1.5, 0.55, "#f5f7fa"),
        "LinUCB selector": (4.4, 2.15, 1.55, 0.65, "#fff7e6"),
        "Cluster-local": (6.4, 2.15, 1.45, 0.65, "#fff7e6"),
        "Rank fusion": (6.4, 3.35, 1.45, 0.65, "#eefcf6"),
        "Calibrated budget": (8.4, 3.35, 1.7, 0.7, "#eefcf6"),
        "Generator": (8.4, 1.3, 1.7, 0.65, "#e8f4fd"),
        "Trust feedback": (4.4, 0.7, 1.7, 0.65, "#fff1f2"),
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
    arrow((3.3, 3.45), (4.4, 4.27))
    arrow((3.3, 3.45), (4.4, 3.37))
    arrow((3.3, 3.45), (4.4, 2.47))
    arrow((5.95, 2.47), (6.4, 2.47))
    arrow((5.9, 4.27), (6.4, 3.83))
    arrow((5.9, 3.37), (6.4, 3.68))
    arrow((7.85, 2.47), (7.1, 3.35))
    arrow((7.85, 3.68), (8.4, 3.68))
    arrow((5.95, 2.47), (6.4, 3.48))
    arrow((9.25, 3.35), (9.25, 1.95))
    arrow((8.4, 1.62), (6.1, 1.02))
    arrow((5.25, 1.35), (5.15, 2.15))
    ax.text(0.3, 4.75, "IntentRoute evidence-selection controller", fontsize=13, weight="bold")
    ax.text(
        0.3,
        4.5,
        "Confidence gates route fusion and fallback; calibration independently sets the final context budget.",
        fontsize=9,
        color="#52606d",
    )
    save(fig, "figure1_system_diagram.pdf")


def token_quality() -> None:
    rows = read_csv("figure2_token_quality_frontier_data.csv")
    x_values = [row_chunks(row) for row in rows]
    policy_hit_delta = [float(row["policy_hit_delta_pp"]) for row in rows]
    dense_hit_delta = [float(row["dense_adaptive_hit_delta_pp"]) for row in rows]
    policy_saving = [float(row["policy_saving_pct"]) for row in rows]
    dense_saving = [float(row["dense_adaptive_saving_pct"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(FULL_WIDTH_INCH, 76.0 * MM_TO_INCH))
    for domain, indices in domain_groups(rows).items():
        linestyle = "-" if domain == "technology/search" else "--"
        xs = [x_values[idx] for idx in indices]
        axes[0].plot(xs, [policy_hit_delta[idx] for idx in indices], marker="o", linestyle=linestyle, label=f"IntentRoute {domain_name(domain)}")
        axes[0].plot(xs, [dense_hit_delta[idx] for idx in indices], marker="x", linestyle=linestyle, label=f"Dense trunc. {domain_name(domain)}")
    axes[0].axhline(0.0, color="#52606d", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Hit@10 delta vs dense (pp)")
    set_chunk_axis(axes[0])
    axes[0].grid(alpha=0.3)

    for domain, indices in domain_groups(rows).items():
        linestyle = "-" if domain == "technology/search" else "--"
        xs = [x_values[idx] for idx in indices]
        axes[1].plot(xs, [policy_saving[idx] for idx in indices], marker="o", linestyle=linestyle, label=f"IntentRoute {domain_name(domain)}")
        axes[1].plot(xs, [dense_saving[idx] for idx in indices], marker="x", linestyle=linestyle, label=f"Dense trunc. {domain_name(domain)}")
    axes[1].set_ylabel("Final context token saving (%)")
    set_chunk_axis(axes[1])
    axes[1].grid(alpha=0.3)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=4,
        frameon=False,
    )
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.18, top=0.80, wspace=0.28)
    save(fig, "figure2_token_quality_frontier.pdf")


def geometry() -> None:
    rows = read_csv("figure3_geometry_diagnostics_data.csv")
    x_values = [row_chunks(row) for row in rows]
    cluster_hit = [float(row["nearest_cluster_hit_at_3"]) for row in rows]
    retention = [float(row["context_retention_at_10"]) for row in rows]
    variance = [float(row["pca_var64"]) for row in rows]

    fig, ax = plt.subplots(figsize=(FULL_WIDTH_INCH, 76.0 * MM_TO_INCH))
    for domain, indices in domain_groups(rows).items():
        linestyle = "-" if domain == "technology/search" else "--"
        xs = [x_values[idx] for idx in indices]
        suffix = domain_name(domain)
        ax.plot(xs, [cluster_hit[idx] for idx in indices], marker="o", linestyle=linestyle, label=f"NearestClusterHit@3 {suffix}")
        ax.plot(xs, [retention[idx] for idx in indices], marker="s", linestyle=linestyle, label=f"ContextRetention@10 {suffix}")
        ax.plot(xs, [variance[idx] for idx in indices], marker="^", linestyle=linestyle, label=f"PCAvar@64 {suffix}")
    ax.set_ylabel("Diagnostic value")
    set_chunk_axis(ax)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.18, top=0.96)
    save(fig, "figure3_geometry_diagnostics.pdf")


def geometry_to_control() -> None:
    rows = read_csv("figure3_geometry_to_control_data.csv")
    retention = [float(row["context_retention_at_10"]) for row in rows]
    hit_delta = [float(row["policy_hit_delta_pp"]) for row in rows]
    saving = [float(row["policy_saving_pct"]) for row in rows]
    colors = ["#2f855a" if row["domain"] == "technology/search" else "#1f5f8b" for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(FULL_WIDTH_INCH, 76.0 * MM_TO_INCH))
    axes[0].axhline(0.0, color="#52606d", linestyle="--", linewidth=1)
    axes[0].scatter(retention, hit_delta, c=colors, s=42, edgecolors="white", linewidths=0.8)
    for row, x, y in zip(rows, retention, hit_delta):
        axes[0].annotate(row["scale"], (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7)
    axes[0].set_xlabel("ContextRetention@10")
    axes[0].set_ylabel("IntentRoute Hit@10 delta vs dense (pp)")
    axes[0].margins(x=0.08, y=0.18)
    axes[0].grid(alpha=0.3)

    axes[1].scatter(retention, saving, c=colors, s=42, edgecolors="white", linewidths=0.8)
    for row, x, y in zip(rows, retention, saving):
        axes[1].annotate(row["scale"], (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7)
    axes[1].set_xlabel("ContextRetention@10")
    axes[1].set_ylabel("Final context token saving (%)")
    axes[1].margins(x=0.08, y=0.16)
    axes[1].grid(alpha=0.3)

    handles = [
        plt.Line2D([0], [0], marker="o", color="w", label="technology/search", markerfacecolor="#2f855a", markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", label="science/search", markerfacecolor="#1f5f8b", markersize=7),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=2,
        frameon=False,
    )
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.18, top=0.82, wspace=0.28)
    save(fig, "figure3_geometry_to_control.pdf")


def feedback_adaptation() -> None:
    rows = read_csv("figure5_feedback_adaptation_data.csv")
    labels = [row["display_label"] for row in rows]
    x_values = list(range(len(rows)))
    selected_cluster = [float(row["selected_cluster_hit"]) for row in rows]
    last_reward = [float(row["last_true_reward"]) for row in rows]
    dense_rate = [float(row["dense_rate"]) for row in rows]
    linucb_rate = [float(row["linucb_rate"]) for row in rows]
    token_ratio = [float(row["token_ratio_vs_dense"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(FULL_WIDTH_INCH, 76.0 * MM_TO_INCH))
    axes[0].plot(x_values, selected_cluster, marker="o", label="Selected-cluster hit", color="#2f855a")
    axes[0].plot(x_values, last_reward, marker="s", label="Last true reward", color="#9a6b14")
    axes[0].set_ylim(0.0, 1.0)
    axes[0].set_ylabel("Policy metric")
    axes[0].set_xticks(x_values, labels, rotation=20, ha="right")
    axes[0].grid(alpha=0.3)
    axes[0].legend(fontsize=8)

    axes[1].plot(x_values, dense_rate, marker="o", label="Dense rate", color="#1f5f8b")
    axes[1].plot(x_values, linucb_rate, marker="s", label="LinUCB rate", color="#2f855a")
    axes[1].plot(x_values, token_ratio, marker="^", label="Token ratio", color="#b42318")
    axes[1].set_ylim(0.0, 1.1)
    axes[1].set_ylabel("Rate / ratio")
    axes[1].set_xticks(x_values, labels, rotation=20, ha="right")
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.24, top=0.96, wspace=0.28)
    save(fig, "figure5_feedback_adaptation.pdf")


def main() -> None:
    figure1 = TARGET / "figure1_system_diagram.pdf"
    if not figure1.exists():
        raise SystemExit(
            "missing author-supplied Figure 1 placeholder/final asset: "
            f"{figure1.relative_to(ROOT)}"
        )
    token_quality()
    geometry()
    geometry_to_control()
    feedback_adaptation()
    print("author_figure_assets=1")
    print("generated_data_figure_assets=4")
    print("latex_figures=passed")


if __name__ == "__main__":
    main()
