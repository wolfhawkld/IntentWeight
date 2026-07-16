#!/usr/bin/env python3
"""Generate paper-facing draft figures for Task36.6.

The script intentionally uses only the Python standard library so the draft
figures can be regenerated in the project virtual environment without adding
plotting dependencies.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from html import escape
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"
FIGURES = ROOT / "paper" / "full_draft" / "figures"


SCALES = ["100k", "200k", "400k", "638k"]


@dataclass(frozen=True)
class TokenRow:
    domain: str
    scale: str
    corpus_chunks: int
    policy_hit_delta_pp: float
    policy_saving_pct: float
    dense_adaptive_hit_delta_pp: float
    dense_adaptive_saving_pct: float


@dataclass(frozen=True)
class GeometryRow:
    domain: str
    scale: str
    corpus_chunks: int
    pca_dim90: float
    pca_var64: float
    cluster_hit3: float
    context_retention10: float


@dataclass(frozen=True)
class RouteControlRow:
    setting: str
    route_reward: float
    selected_cluster_hit: float
    final_fused_hit10: float


@dataclass(frozen=True)
class ArmControlRow:
    arm_count: int
    static_route_reward: float
    gated_dense_rate: float
    gated_hit_delta_pp: float


@dataclass(frozen=True)
class FeedbackRow:
    setting: str
    display_label: str
    hit10: float
    token_ratio: float
    dense_rate: float
    linucb_rate: float
    selected_cluster_hit: float
    last_true_reward: float


def read_token_rows() -> list[TokenRow]:
    # Frozen calibration/test values from the calibrated token-budget validation.
    # Kept explicit here so Figure 2 reflects the main paper table rather than
    # the older confidence-only frontier.
    rows = [
        TokenRow("technology/search", "100k", 101311, 0.00, 6.18, -1.44, 13.83),
        TokenRow("technology/search", "200k", 201010, 1.20, 16.00, -2.40, 21.95),
        TokenRow("technology/search", "400k", 400674, 2.32, 6.57, -0.24, 11.44),
        TokenRow("technology/search", "638k", 638509, -0.08, 17.53, -3.84, 21.90),
    ]
    rows.extend(read_science_token_rows())
    return rows


def read_route_control_rows() -> list[RouteControlRow]:
    path = RESULTS / "task58_geometry_random_ablation_summary.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        by_setting = {row["setting"]: row for row in csv.DictReader(handle)}
    labels = [
        ("static_nearest", "Static-nearest geometry"),
        ("uniform_random", "Uniform-random arms"),
    ]
    return [
        RouteControlRow(
            setting=label,
            route_reward=float(by_setting[key]["last_route_true_reward_mean"]),
            selected_cluster_hit=float(by_setting[key]["selected_cluster_hit_rate_mean"]),
            final_fused_hit10=float(by_setting[key]["full_top10_hit@10_mean"]),
        )
        for key, label in labels
    ]


def read_arm_control_rows() -> list[ArmControlRow]:
    path = RESULTS / "task60_arm_count_sensitivity_summary.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        source = list(csv.DictReader(handle))
    by_key = {(int(row["arm_count"]), row["short_mode"]): row for row in source}
    return [
        ArmControlRow(
            arm_count=arm_count,
            static_route_reward=float(by_key[(arm_count, "static")]["last_route_true_reward_mean"]),
            gated_dense_rate=float(by_key[(arm_count, "gated")]["dense_query_rate_mean"]),
            gated_hit_delta_pp=float(by_key[(arm_count, "gated")]["test_hit_delta_pp_mean"]),
        )
        for arm_count in (8, 16, 32, 64, 128)
    ]


def read_feedback_rows() -> list[FeedbackRow]:
    path = RESULTS / "task33_3_clean_ablation_table.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        by_component = {row["component"]: row for row in csv.DictReader(handle)}
    order = [
        ("No feedback gated routing", "No feedback"),
        ("Equal noisy feedback", "Equal noisy"),
        ("Trust-weighted feedback", "Trust-weighted"),
        ("Trust-weighted mild noise", "Trust mild"),
        ("Oracle feedback", "Oracle"),
    ]
    rows: list[FeedbackRow] = []
    for component, label in order:
        row = by_component[component]
        rows.append(
            FeedbackRow(
                setting=component,
                display_label=label,
                hit10=float(row["hit@10"]),
                token_ratio=float(row["token_ratio_vs_dense"]),
                dense_rate=float(row["dense_rate"]),
                linucb_rate=float(row["linucb_primary_rate"]),
                selected_cluster_hit=float(row["selected_cluster_hit"]),
                last_true_reward=float(row["last_true_reward"]),
            )
        )
    strong_summary_path = RESULTS / "task33_2_feedback_trust_strong" / "linucb_cost_summary.csv"
    with strong_summary_path.open(newline="", encoding="utf-8") as handle:
        strong_summary = next(csv.DictReader(handle))
    with (RESULTS / "task33_2_feedback_sensitivity_context_tokens.csv").open(newline="", encoding="utf-8") as handle:
        context_rows = [row for row in csv.DictReader(handle) if row["source_label"] == "trust_strong"]
    rows.insert(
        4,
        FeedbackRow(
            setting="Trust-weighted strong noise",
            display_label="Strong noise",
            hit10=float(strong_summary["hit@10_mean"]),
            token_ratio=mean(float(row["context_token_ratio_vs_baseline@10"]) for row in context_rows),
            dense_rate=float(strong_summary["dense_query_rate_mean"]),
            linucb_rate=float(strong_summary["linucb_primary_rate_mean"]),
            selected_cluster_hit=float(strong_summary["selected_cluster_hit_rate_mean"]),
            last_true_reward=float(strong_summary["last_epoch_true_reward_mean"]),
        ),
    )
    return rows


def read_science_token_rows() -> list[TokenRow]:
    sources = [
        ("20k/q200", 20490, RESULTS / "task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv"),
        ("100k", 101187, RESULTS / "task39_lotte_science_100k_calibrated_context_budget.test_paired.csv"),
    ]
    rows: list[TokenRow] = []
    for scale, corpus_chunks, path in sources:
        with path.open(newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        policy = [row for row in records if row["method_label"] == "task38"]
        dense = [row for row in records if row["method_label"] == "dense_adaptive"]
        if not policy or len(dense) != 1:
            raise ValueError(f"Unexpected Task39 token rows in {path}")
        rows.append(
            TokenRow(
                "science/search",
                scale,
                corpus_chunks,
                mean(float(row["hit_delta_mean"]) * 100.0 for row in policy),
                mean(float(row["token_saving_percent"]) for row in policy),
                float(dense[0]["hit_delta_mean"]) * 100.0,
                float(dense[0]["token_saving_percent"]),
            )
        )
    return rows


def read_geometry_rows() -> list[GeometryRow]:
    rows: list[GeometryRow] = []
    rows.extend(read_geometry_csv("technology/search", RESULTS / "task30_lotte_geometry_scale_validation.csv", SCALES))
    rows.extend(
        read_geometry_csv(
            "science/search",
            RESULTS / "task43_lotte_science_geometry_diagnostics.csv",
            ["20k_q200", "100k"],
        )
    )
    return rows


def read_geometry_csv(domain: str, path: Path, scales: list[str]) -> list[GeometryRow]:
    by_scale: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_scale[row["scale"]] = row

    rows: list[GeometryRow] = []
    for scale in scales:
        row = by_scale[scale]
        rows.append(
            GeometryRow(
                domain=domain,
                scale="20k/q200" if scale == "20k_q200" else scale,
                corpus_chunks=int(row["num_corpus_chunks"]),
                pca_dim90=float(row["pca_sample_dim_for_90pct"]),
                pca_var64=float(row["pca_sample_var@64"]),
                cluster_hit3=float(row["nearest_cluster_hit@3_mean"]),
                context_retention10=float(row["context_recall_retention@10"]),
            )
        )
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def svg_header(width: int, height: int, *, publication_scale: bool = False) -> list[str]:
    sizes = (
        {"title": 32, "subtitle": 21, "label": 20, "tick": 20, "legend": 20, "box_title": 22, "box_text": 20}
        if publication_scale
        else {"title": 22, "subtitle": 13, "label": 12, "tick": 11, "legend": 12, "box_title": 13, "box_text": 11}
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" '
        'orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L9,3 z" fill="#425466" />',
        "</marker>",
        '<style><![CDATA[',
        "text { font-family: Arial, Helvetica, sans-serif; fill: #1f2933; }",
        f".title {{ font-size: {sizes['title']}px; font-weight: 700; }}",
        f".subtitle {{ font-size: {sizes['subtitle']}px; fill: #52606d; }}",
        ".axis { stroke: #9aa5b1; stroke-width: 1; }",
        ".grid { stroke: #e4e7eb; stroke-width: 1; }",
        f".label {{ font-size: {sizes['label']}px; fill: #52606d; }}",
        f".tick {{ font-size: {sizes['tick']}px; fill: #616e7c; }}",
        f".legend {{ font-size: {sizes['legend']}px; fill: #323f4b; }}",
        f".box-title {{ font-size: {sizes['box_title']}px; font-weight: 700; }}",
        f".box-text {{ font-size: {sizes['box_text']}px; fill: #52606d; }}",
        "]]></style>",
        "</defs>",
        '<rect width="100%" height="100%" fill="#ffffff" />',
    ]


def text(x: float, y: float, value: str, cls: str = "label", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{escape(value)}</text>'


def line(x1: float, y1: float, x2: float, y2: float, color: str = "#9aa5b1", width: float = 1.5) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width:.1f}" />'
    )


def polyline(points: list[tuple[float, float]], color: str, width: float = 2.8, dash: str | None = None) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width:.1f}"{dash_attr} />'


def circle(x: float, y: float, color: str) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}" stroke="#ffffff" stroke-width="1.5" />'


def chart_points(values: list[float], x0: float, y0: float, width: float, height: float, y_min: float, y_max: float) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for idx, value in enumerate(values):
        x = x0 + idx * (width / (len(values) - 1))
        y = y0 + height - ((value - y_min) / (y_max - y_min)) * height
        points.append((x, y))
    return points


def chunk_axis_bounds(rows: list[TokenRow] | list[GeometryRow]) -> tuple[float, float]:
    max_chunks = max(row.corpus_chunks for row in rows)
    return 0.0, max_chunks * 1.03


def chunk_ticks(rows: list[TokenRow] | list[GeometryRow]) -> list[tuple[float, str]]:
    ticks = [
        (20490.0, "20k"),
        (101311.0, "100k"),
        (201010.0, "200k"),
        (400674.0, "400k"),
        (638509.0, "638k"),
    ]
    x_min, x_max = chunk_axis_bounds(rows)
    return [(value, label) for value, label in ticks if x_min <= value <= x_max]


def chart_points_by_chunks(
    rows: list[TokenRow] | list[GeometryRow],
    values: list[float],
    x0: float,
    y0: float,
    width: float,
    height: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for row, value in zip(rows, values):
        x = x0 + ((row.corpus_chunks - x_min) / (x_max - x_min)) * width
        y = y0 + height - ((value - y_min) / (y_max - y_min)) * height
        points.append((x, y))
    return points


def scatter_points(
    rows: list[GeometryGainRow],
    x_values: list[float],
    y_values: list[float],
    x0: float,
    y0: float,
    width: float,
    height: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for x_value, y_value in zip(x_values, y_values):
        x = x0 + ((x_value - x_min) / (x_max - x_min)) * width
        y = y0 + height - ((y_value - y_min) / (y_max - y_min)) * height
        points.append((x, y))
    return points


def category_points(
    values: list[float],
    x0: float,
    y0: float,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for idx, value in enumerate(values):
        x = x0 + idx * (width / (len(values) - 1))
        y = y0 + height - ((value - y_min) / (y_max - y_min)) * height
        points.append((x, y))
    return points


def short_label(row: TokenRow | GeometryRow) -> str:
    prefix = "tech" if row.domain == "technology/search" else "sci"
    return f"{prefix} {row.scale}"


def grouped_polylines(parts: list[str], rows: list[TokenRow] | list[GeometryRow], points: list[tuple[float, float]], color: str) -> None:
    current_domain = None
    current_points: list[tuple[float, float]] = []
    for row, point in zip(rows, points):
        if current_domain is None:
            current_domain = row.domain
        if row.domain != current_domain:
            if len(current_points) > 1:
                dash = "7 5" if current_domain == "science/search" else None
                parts.append(polyline(current_points, color, dash=dash))
            current_points = []
            current_domain = row.domain
        current_points.append(point)
    if len(current_points) > 1:
        dash = "7 5" if current_domain == "science/search" else None
        parts.append(polyline(current_points, color, dash=dash))


def draw_axes(parts: list[str], x0: float, y0: float, width: float, height: float, y_min: float, y_max: float, ticks: list[float], labels: list[str], title: str) -> None:
    parts.append(line(x0, y0, x0, y0 + height, "#9aa5b1", 1.2))
    parts.append(line(x0, y0 + height, x0 + width, y0 + height, "#9aa5b1", 1.2))
    parts.append(text(x0, y0 - 16, title, "subtitle"))
    for tick_value in ticks:
        y = y0 + height - ((tick_value - y_min) / (y_max - y_min)) * height
        parts.append(line(x0, y, x0 + width, y, "#e4e7eb", 1.0))
        parts.append(text(x0 - 8, y + 4, f"{tick_value:.2f}", "tick", "end"))
    for idx, label in enumerate(labels):
        x = x0 + idx * (width / (len(labels) - 1))
        parts.append(text(x, y0 + height + 22, label, "tick", "middle"))


def draw_chunk_axes(
    parts: list[str],
    rows: list[TokenRow] | list[GeometryRow],
    x0: float,
    y0: float,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
    y_ticks: list[float],
    title: str,
) -> tuple[float, float]:
    x_min, x_max = chunk_axis_bounds(rows)
    parts.append(line(x0, y0, x0, y0 + height, "#9aa5b1", 1.2))
    parts.append(line(x0, y0 + height, x0 + width, y0 + height, "#9aa5b1", 1.2))
    parts.append(text(x0, y0 - 16, title, "subtitle"))
    for tick_value in y_ticks:
        y = y0 + height - ((tick_value - y_min) / (y_max - y_min)) * height
        parts.append(line(x0, y, x0 + width, y, "#e4e7eb", 1.0))
        parts.append(text(x0 - 8, y + 4, f"{tick_value:.2f}", "tick", "end"))
    for tick_value, label in chunk_ticks(rows):
        x = x0 + ((tick_value - x_min) / (x_max - x_min)) * width
        parts.append(line(x, y0 + height, x, y0 + height + 5, "#9aa5b1", 1.0))
        parts.append(text(x, y0 + height + 22, label, "tick", "middle"))
    parts.append(text(x0 + width / 2, y0 + height + 44, "Corpus chunks", "label", "middle"))
    return x_min, x_max


def draw_scatter_axes(
    parts: list[str],
    x0: float,
    y0: float,
    width: float,
    height: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    x_ticks: list[float],
    y_ticks: list[float],
    title: str,
    x_label: str,
) -> None:
    parts.append(line(x0, y0, x0, y0 + height, "#9aa5b1", 1.2))
    parts.append(line(x0, y0 + height, x0 + width, y0 + height, "#9aa5b1", 1.2))
    parts.append(text(x0, y0 - 16, title, "subtitle"))
    for tick_value in y_ticks:
        y = y0 + height - ((tick_value - y_min) / (y_max - y_min)) * height
        parts.append(line(x0, y, x0 + width, y, "#e4e7eb", 1.0))
        parts.append(text(x0 - 8, y + 4, f"{tick_value:.1f}", "tick", "end"))
    for tick_value in x_ticks:
        x = x0 + ((tick_value - x_min) / (x_max - x_min)) * width
        parts.append(line(x, y0 + height, x, y0 + height + 5, "#9aa5b1", 1.0))
        parts.append(text(x, y0 + height + 22, f"{tick_value:.2f}", "tick", "middle"))
    parts.append(text(x0 + width / 2, y0 + height + 44, x_label, "label", "middle"))


def draw_category_axes(
    parts: list[str],
    labels: list[str],
    x0: float,
    y0: float,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
    y_ticks: list[float],
    title: str,
) -> None:
    parts.append(line(x0, y0, x0, y0 + height, "#9aa5b1", 1.2))
    parts.append(line(x0, y0 + height, x0 + width, y0 + height, "#9aa5b1", 1.2))
    parts.append(text(x0, y0 - 16, title, "subtitle"))
    for tick_value in y_ticks:
        y = y0 + height - ((tick_value - y_min) / (y_max - y_min)) * height
        parts.append(line(x0, y, x0 + width, y, "#e4e7eb", 1.0))
        parts.append(text(x0 - 8, y + 4, f"{tick_value:.2f}", "tick", "end"))
    for idx, label in enumerate(labels):
        x = x0 + idx * (width / (len(labels) - 1))
        parts.append(text(x, y0 + height + 22, label, "tick", "middle"))


def generate_system_diagram() -> None:
    parts = svg_header(1120, 520)
    parts.append(text(40, 42, "Figure 1. IntentRoute evidence-selection controller", "title"))
    parts.append(text(40, 64, "Dense/BM25 rescue, adaptive local routing, and frozen context calibration remain separate control layers.", "subtitle"))

    boxes = [
        (40, 120, 150, 88, "#e8f4fd", "#1f5f8b", "Query", ["user/session", "context"]),
        (230, 120, 165, 88, "#eefcf6", "#2f855a", "Feature builder", ["query embedding", "route signals"]),
        (455, 78, 175, 58, "#f5f7fa", "#425466", "Dense global", ["semantic recall floor"]),
        (455, 154, 175, 58, "#f5f7fa", "#425466", "BM25 global", ["lexical anchors"]),
        (455, 230, 175, 72, "#fff7e6", "#9a6b14", "LinUCB selector", ["fixed cluster arms", "confidence scores"]),
        (690, 230, 175, 72, "#fff7e6", "#9a6b14", "Cluster-local dense", ["search selected arms", "local evidence"]),
        (690, 130, 175, 76, "#eefcf6", "#2f855a", "Route gate + fusion", ["confidence / mismatch", "dense fallback"]),
        (905, 130, 175, 76, "#eefcf6", "#2f855a", "Context budget", ["LLM input context", "compact if safe"]),
        (905, 300, 175, 76, "#e8f4fd", "#1f5f8b", "Generator / agent", ["answer from selected", "evidence context"]),
        (455, 350, 190, 76, "#fff1f2", "#b42318", "Trust-weighted feedback", ["simulated feedback", "future updates only"]),
    ]

    for x, y, w, h, fill, stroke, title, lines in boxes:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5" />')
        parts.append(text(x + 14, y + 27, title, "box-title"))
        for idx, item in enumerate(lines):
            parts.append(text(x + 14, y + 50 + idx * 17, item, "box-text"))

    arrows = [
        (190, 164, 230, 164),
        (395, 164, 455, 107),
        (395, 164, 455, 183),
        (395, 164, 455, 266),
        (630, 266, 690, 266),
        (630, 107, 690, 154),
        (630, 183, 690, 168),
        (865, 266, 735, 206),
        (865, 168, 905, 168),
        (630, 266, 690, 185),
        (992, 206, 992, 300),
        (905, 338, 645, 388),
        (550, 350, 550, 302),
    ]
    for index, (x1, y1, x2, y2) in enumerate(arrows):
        dash = ' stroke-dasharray="6 5"' if index >= len(arrows) - 2 else ""
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#425466" '
            f'stroke-width="1.8"{dash} marker-end="url(#arrow)" />'
        )

    parts.append(text(40, 470, "Feedback updates q(t+1) route state; only the independently frozen policy sets the final context budget.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure1_system_diagram.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")

    mermaid = """flowchart LR
    Q[Query and user/session context] --> F[PCA query controller context]
    F --> D[Dense global recall floor]
    F --> B[BM25 lexical recall]
    F --> P[LinUCB cluster-arm selector]
    P --> C[Cluster-local dense search]
    P --> GATE[Confidence and centroid-mismatch gate]
    D --> R[Rank fusion]
    B --> R
    C --> R
    GATE --> R
    K[Calibrated budget policy] --> G[Final context budget]
    R --> G
    G --> A[Generator or downstream agent response]
    A -. observed outcome .-> T[Controlled trust-weighted simulated feedback]
    T -. update route state for q(t+1) .-> P
"""
    (FIGURES / "figure1_system_diagram.mmd").write_text(mermaid, encoding="utf-8")


def generate_token_quality_figure(rows: list[TokenRow]) -> None:
    write_csv(
        FIGURES / "figure2_token_quality_frontier_data.csv",
        [
            "domain",
            "scale",
            "corpus_chunks",
            "policy_hit_delta_pp",
            "policy_saving_pct",
            "dense_adaptive_hit_delta_pp",
            "dense_adaptive_saving_pct",
        ],
        [
            {
                "domain": row.domain,
                "scale": row.scale,
                "corpus_chunks": row.corpus_chunks,
                "policy_hit_delta_pp": f"{row.policy_hit_delta_pp:.2f}",
                "policy_saving_pct": f"{row.policy_saving_pct:.2f}",
                "dense_adaptive_hit_delta_pp": f"{row.dense_adaptive_hit_delta_pp:.2f}",
                "dense_adaptive_saving_pct": f"{row.dense_adaptive_saving_pct:.2f}",
            }
            for row in rows
        ],
    )

    parts = svg_header(1120, 520)
    parts.append(text(40, 42, "Figure 2. Calibrated token-quality frontier by corpus chunk count", "title"))
    parts.append(text(40, 64, "IntentRoute saves final LLM evidence-context tokens while avoiding dense-truncation Hit@10 loss.", "subtitle"))

    x0, y0, width, height = 80, 118, 420, 290
    x_min, x_max = draw_chunk_axes(parts, rows, x0, y0, width, height, -4.0, 3.0, [-4.0, -2.0, 0.0, 2.0], "Hit@10 delta vs dense (pp)")
    policy_points = chart_points_by_chunks(rows, [row.policy_hit_delta_pp for row in rows], x0, y0, width, height, x_min, x_max, -4.0, 3.0)
    dense_points = chart_points_by_chunks(rows, [row.dense_adaptive_hit_delta_pp for row in rows], x0, y0, width, height, x_min, x_max, -4.0, 3.0)
    zero_y = y0 + height - ((0.0 - -4.0) / 7.0) * height
    parts.append(line(x0, zero_y, x0 + width, zero_y, "#b8c2cc", 1.2))
    grouped_polylines(parts, rows, policy_points, "#2f855a")
    grouped_polylines(parts, rows, dense_points, "#1f5f8b")
    for point in policy_points:
        parts.append(circle(*point, "#2f855a"))
    for point in dense_points:
        parts.append(circle(*point, "#1f5f8b"))
    parts.append(f'<rect x="260" y="92" width="12" height="12" fill="#2f855a" />')
    parts.append(text(278, 103, "IntentRoute budget", "legend"))
    parts.append(f'<rect x="410" y="92" width="12" height="12" fill="#1f5f8b" />')
    parts.append(text(428, 103, "Dense adaptive truncation", "legend"))
    parts.append(text(80, 444, "solid=technology/search; dashed=science/search", "tick"))

    x1, y1, w1, h1 = 630, 118, 400, 290
    x_min, x_max = draw_chunk_axes(parts, rows, x1, y1, w1, h1, 0.0, 24.0, [0.0, 8.0, 16.0, 24.0], "Final context token saving (%)")
    saving_points = chart_points_by_chunks(rows, [row.policy_saving_pct for row in rows], x1, y1, w1, h1, x_min, x_max, 0.0, 24.0)
    dense_saving_points = chart_points_by_chunks(rows, [row.dense_adaptive_saving_pct for row in rows], x1, y1, w1, h1, x_min, x_max, 0.0, 24.0)
    grouped_polylines(parts, rows, saving_points, "#2f855a")
    grouped_polylines(parts, rows, dense_saving_points, "#1f5f8b")
    for row, (x, y) in zip(rows, saving_points):
        parts.append(circle(x, y, "#2f855a"))
        parts.append(text(x, y - 12, f"{row.policy_saving_pct:.1f}%", "tick", "middle"))
    for row, (x, y) in zip(rows, dense_saving_points):
        parts.append(circle(x, y, "#1f5f8b"))
        parts.append(text(x, y + 18, f"{row.dense_adaptive_saving_pct:.1f}%", "tick", "middle"))

    parts.append(text(80, 468, "Caption boundary: dense truncation saves more tokens but loses Hit@10; IntentRoute targets the safer frontier.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure2_token_quality_frontier.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def generate_geometry_figure(rows: list[GeometryRow]) -> None:
    write_csv(
        FIGURES / "figure3_geometry_diagnostics_data.csv",
        ["domain", "scale", "corpus_chunks", "pca_dim90", "pca_var64", "nearest_cluster_hit_at_3", "context_retention_at_10"],
        [
            {
                "domain": row.domain,
                "scale": row.scale,
                "corpus_chunks": row.corpus_chunks,
                "pca_dim90": f"{row.pca_dim90:.0f}",
                "pca_var64": f"{row.pca_var64:.4f}",
                "nearest_cluster_hit_at_3": f"{row.cluster_hit3:.4f}",
                "context_retention_at_10": f"{row.context_retention10:.4f}",
            }
            for row in rows
        ],
    )

    parts = svg_header(1120, 520)
    parts.append(text(40, 42, "Figure 3. Geometry diagnostics by corpus chunk count", "title"))
    parts.append(text(40, 64, "Local cluster geometry remains useful, while context retention and PCA concentration vary with scale.", "subtitle"))

    x0, y0, width, height = 90, 118, 850, 290
    x_min, x_max = draw_chunk_axes(parts, rows, x0, y0, width, height, 0.55, 0.95, [0.55, 0.65, 0.75, 0.85, 0.95], "Diagnostic value")
    series = [
        ("NearestClusterHit@3", [row.cluster_hit3 for row in rows], "#2f855a"),
        ("ContextRetention@10", [row.context_retention10 for row in rows], "#1f5f8b"),
        ("PCAvar@64", [row.pca_var64 for row in rows], "#9a6b14"),
    ]
    for name, values, color in series:
        points = chart_points_by_chunks(rows, values, x0, y0, width, height, x_min, x_max, 0.55, 0.95)
        grouped_polylines(parts, rows, points, color)
        for point in points:
            parts.append(circle(*point, color))

    legend_x = 780
    for idx, (name, _, color) in enumerate(series):
        y = 88 + idx * 22
        parts.append(f'<rect x="{legend_x}" y="{y - 10}" width="12" height="12" fill="{color}" />')
        parts.append(text(legend_x + 18, y, name, "legend"))

    for row, idx in zip(rows, range(len(rows))):
        x = x0 + ((row.corpus_chunks - x_min) / (x_max - x_min)) * width
        parts.append(text(x, 438, f"PCAdim90={row.pca_dim90:.0f}", "tick", "middle"))
    parts.append(text(90, 444, "solid=technology/search; dashed=science/search", "tick"))

    parts.append(text(90, 468, "Caption boundary: diagnostics support local-structure routing; they are not theorem-level manifold proof.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure3_geometry_diagnostics.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def generate_geometry_control_figure(
    geometry_rows: list[GeometryRow],
    route_rows: list[RouteControlRow],
    arm_rows: list[ArmControlRow],
) -> None:
    csv_rows: list[dict[str, object]] = []
    for row in geometry_rows:
        csv_rows.append(
            {
                "panel": "A_geometry_profile",
                "domain": row.domain,
                "scale": row.scale,
                "corpus_chunks": row.corpus_chunks,
                "pca_var64": f"{row.pca_var64:.4f}",
                "nearest_cluster_hit_at_3": f"{row.cluster_hit3:.4f}",
                "context_retention_at_10": f"{row.context_retention10:.4f}",
            }
        )
    for row in route_rows:
        csv_rows.append(
            {
                "panel": "B_geometry_random",
                "setting": row.setting,
                "route_reward": f"{row.route_reward:.4f}",
                "selected_cluster_hit": f"{row.selected_cluster_hit:.4f}",
                "final_fused_hit_at_10": f"{row.final_fused_hit10:.4f}",
            }
        )
    for row in arm_rows:
        csv_rows.append(
            {
                "panel": "C_arm_fallback",
                "arm_count": row.arm_count,
                "static_route_reward": f"{row.static_route_reward:.4f}",
                "gated_dense_rate": f"{row.gated_dense_rate:.4f}",
                "gated_hit_delta_pp": f"{row.gated_hit_delta_pp:.2f}",
            }
        )
    write_csv(
        FIGURES / "figure3_geometry_to_control_data.csv",
        [
            "panel",
            "domain",
            "scale",
            "corpus_chunks",
            "pca_var64",
            "nearest_cluster_hit_at_3",
            "context_retention_at_10",
            "setting",
            "route_reward",
            "selected_cluster_hit",
            "final_fused_hit_at_10",
            "arm_count",
            "static_route_reward",
            "gated_dense_rate",
            "gated_hit_delta_pp",
        ],
        csv_rows,
    )

    parts = svg_header(1500, 680, publication_scale=True)
    parts.append(text(45, 44, "Figure 3. From local geometry to route-control behavior", "title"))
    parts.append(text(45, 76, "Local structure supports routing; rescue and calibration remain separate determinants of final quality and context cost.", "subtitle"))

    panel_specs = [(45, 108, 445, 510), (525, 108, 430, 510), (990, 108, 465, 510)]
    for x, y, width, height in panel_specs:
        parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="#fbfcfd" stroke="#d9e2ec" stroke-width="1.5" />')

    # Panel A: shared-scale profile, with a common 0.55-0.95 y-axis to avoid
    # exaggerating the six-point trends through metric-specific rescaling.
    ax, ay, aw, ah = 105.0, 180.0, 345.0, 330.0
    parts.append(text(65, 145, "A  Cross-scale geometry profile", "box-title"))
    for tick_value in (0.6, 0.7, 0.8, 0.9):
        y = ay + ah - ((tick_value - 0.55) / 0.40) * ah
        parts.append(line(ax, y, ax + aw, y, "#e4e7eb", 1.0))
        parts.append(text(ax - 12, y + 7, f"{tick_value:.1f}", "tick", "end"))
    parts.append(line(ax, ay, ax, ay + ah, "#9aa5b1", 1.4))
    parts.append(line(ax, ay + ah, ax + aw, ay + ah, "#9aa5b1", 1.4))
    log_min, log_max = 4.25, 5.85
    for chunks, label in ((20000, "20k"), (100000, "100k"), (200000, "200k"), (400000, "400k"), (640000, "640k")):
        x = ax + ((math.log10(chunks) - log_min) / (log_max - log_min)) * aw
        parts.append(line(x, ay + ah, x, ay + ah + 7, "#9aa5b1", 1.0))
        parts.append(text(x, ay + ah + 30, label, "tick", "middle"))
    parts.append(text(ax + aw / 2, ay + ah + 60, "Corpus chunks (log scale)", "label", "middle"))
    metric_specs = [
        ("Nearest-cluster Hit@3", "cluster_hit3", "#2f855a", "o"),
        ("Context retention@10", "context_retention10", "#1f5f8b", "s"),
        ("PCA variance@64", "pca_var64", "#9a6b14", "t"),
    ]
    for metric_label, attribute, color, marker in metric_specs:
        for domain in ("technology/search", "science/search"):
            domain_rows = [row for row in geometry_rows if row.domain == domain]
            points: list[tuple[float, float]] = []
            for row in domain_rows:
                x = ax + ((math.log10(row.corpus_chunks) - log_min) / (log_max - log_min)) * aw
                value = float(getattr(row, attribute))
                y = ay + ah - ((value - 0.55) / 0.40) * ah
                points.append((x, y))
                if marker == "s":
                    parts.append(f'<rect x="{x - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" fill="{color}" stroke="#ffffff" stroke-width="1.5" />')
                elif marker == "t":
                    parts.append(f'<path d="M{x:.1f},{y - 7:.1f} L{x - 7:.1f},{y + 6:.1f} L{x + 7:.1f},{y + 6:.1f} Z" fill="{color}" stroke="#ffffff" stroke-width="1.5" />')
                else:
                    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}" stroke="#ffffff" stroke-width="1.5" />')
            parts.append(polyline(points, color, 2.6, "8 6" if domain == "science/search" else None))
    for idx, (label, _, color, _) in enumerate(metric_specs):
        y = 542 + idx * 25
        parts.append(f'<rect x="70" y="{y - 13}" width="14" height="14" fill="{color}" />')
        parts.append(text(93, y, label, "legend"))
    parts.append(line(310, 548, 350, 548, "#52606d", 2.5))
    parts.append(text(360, 555, "technology", "legend"))
    parts.append(f'<line x1="310" y1="580" x2="350" y2="580" stroke="#52606d" stroke-width="2.5" stroke-dasharray="8 6" />')
    parts.append(text(360, 587, "science", "legend"))

    # Panel B: route-level separation is large even though Dense/BM25 rescue
    # keeps the final fused endpoint high for both controls.
    bx, by, bw, bh = 580.0, 190.0, 330.0, 330.0
    parts.append(text(545, 145, "B  Geometry versus random routing", "box-title"))
    for tick_value in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = by + bh - tick_value * bh
        parts.append(line(bx, y, bx + bw, y, "#e4e7eb", 1.0))
        parts.append(text(bx - 12, y + 7, f"{tick_value:.2f}", "tick", "end"))
    parts.append(line(bx, by, bx, by + bh, "#9aa5b1", 1.4))
    parts.append(line(bx, by + bh, bx + bw, by + bh, "#9aa5b1", 1.4))
    bar_colors = ["#2f855a", "#9a6b14", "#1f5f8b"]
    bar_labels = ["Route reward", "Cluster hit", "Final fused Hit@10"]
    for group_index, row in enumerate(route_rows):
        center = bx + 92 + group_index * 175
        values = [row.route_reward, row.selected_cluster_hit, row.final_fused_hit10]
        for metric_index, (value, color) in enumerate(zip(values, bar_colors)):
            x = center - 50 + metric_index * 40
            y = by + bh - value * bh
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="30" height="{value * bh:.1f}" fill="{color}" opacity="0.90" />')
            parts.append(text(x + 15, y - 9, f"{value:.2f}", "tick", "middle"))
        parts.append(text(center - 10, by + bh + 31, "Static geometry" if group_index == 0 else "Uniform random", "tick", "middle"))
    for idx, (label, color) in enumerate(zip(bar_labels, bar_colors)):
        y = 560 + idx * 27
        parts.append(f'<rect x="575" y="{y - 13}" width="15" height="15" fill="{color}" />')
        parts.append(text(600, y, label, "legend"))

    # Panel C: K changes route granularity and the fallback operating point.
    cx, cy, cw, ch = 1050.0, 185.0, 350.0, 220.0
    parts.append(text(1010, 145, "C  Arm granularity and fallback", "box-title"))
    for tick_value in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = cy + ch - tick_value * ch
        parts.append(line(cx, y, cx + cw, y, "#e4e7eb", 1.0))
        parts.append(text(cx - 12, y + 7, f"{tick_value:.2f}", "tick", "end"))
    parts.append(line(cx, cy, cx, cy + ch, "#9aa5b1", 1.4))
    parts.append(line(cx, cy + ch, cx + cw, cy + ch, "#9aa5b1", 1.4))
    reward_points: list[tuple[float, float]] = []
    dense_points: list[tuple[float, float]] = []
    for idx, row in enumerate(arm_rows):
        x = cx + idx * (cw / 4)
        reward_y = cy + ch - row.static_route_reward * ch
        dense_y = cy + ch - row.gated_dense_rate * ch
        reward_points.append((x, reward_y))
        dense_points.append((x, dense_y))
        parts.append(f'<circle cx="{x:.1f}" cy="{reward_y:.1f}" r="6" fill="#2f855a" stroke="#ffffff" stroke-width="1.5" />')
        parts.append(f'<rect x="{x - 6:.1f}" y="{dense_y - 6:.1f}" width="12" height="12" fill="#1f5f8b" stroke="#ffffff" stroke-width="1.5" />')
    parts.append(polyline(reward_points, "#2f855a", 2.8))
    parts.append(polyline(dense_points, "#1f5f8b", 2.8))
    parts.append(text(1060, 438, "Gated Hit@10 delta vs Dense (pp)", "label"))
    delta_top, delta_height = 460.0, 85.0
    parts.append(line(cx, delta_top, cx + cw, delta_top, "#9aa5b1", 1.2))
    parts.append(line(cx, delta_top, cx, delta_top + delta_height, "#9aa5b1", 1.2))
    for idx, row in enumerate(arm_rows):
        x = cx + idx * (cw / 4)
        height = abs(row.gated_hit_delta_pp) / 5.0 * delta_height
        parts.append(f'<rect x="{x - 14:.1f}" y="{delta_top:.1f}" width="28" height="{height:.1f}" fill="#b42318" opacity="0.82" />')
        parts.append(text(x, delta_top + height + 23, f"{row.gated_hit_delta_pp:.2f}", "tick", "middle"))
        parts.append(text(x, 588, str(row.arm_count), "tick", "middle"))
    parts.append(text(cx + cw / 2, 614, "Number of arms K (log2 steps)", "label", "middle"))
    parts.append(f'<rect x="1050" y="158" width="14" height="14" fill="#2f855a" />')
    parts.append(text(1073, 172, "Static route reward", "legend"))
    parts.append(f'<rect x="1255" y="158" width="14" height="14" fill="#1f5f8b" />')
    parts.append(text(1278, 172, "Gated Dense rate", "legend"))

    parts.append(text(45, 655, "Panel B separates route quality from rescued final quality; Panel C treats K=32 as an engineering point, not a geometric optimum.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure3_geometry_to_control.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def generate_feedback_adaptation_figure(rows: list[FeedbackRow]) -> None:
    write_csv(
        FIGURES / "figure5_feedback_adaptation_data.csv",
        [
            "setting",
            "display_label",
            "hit_at_10",
            "token_ratio_vs_dense",
            "dense_rate",
            "linucb_rate",
            "selected_cluster_hit",
            "last_true_reward",
        ],
        [
            {
                "setting": row.setting,
                "display_label": row.display_label,
                "hit_at_10": f"{row.hit10:.4f}",
                "token_ratio_vs_dense": f"{row.token_ratio:.4f}",
                "dense_rate": f"{row.dense_rate:.4f}",
                "linucb_rate": f"{row.linucb_rate:.4f}",
                "selected_cluster_hit": f"{row.selected_cluster_hit:.4f}",
                "last_true_reward": f"{row.last_true_reward:.4f}",
            }
            for row in rows
        ],
    )

    parts = svg_header(1120, 520)
    parts.append(text(40, 42, "Figure 5. Feedback-driven route adaptation", "title"))
    parts.append(text(40, 64, "Trust-weighted feedback improves route-policy metrics and can reduce dense reliance under controlled simulation.", "subtitle"))
    labels = [row.display_label for row in rows]

    x0, y0, width, height = 80, 118, 430, 285
    draw_category_axes(parts, labels, x0, y0, width, height, 0.0, 1.0, [0.0, 0.25, 0.50, 0.75, 1.0], "Policy learning signal")
    cluster_points = category_points([row.selected_cluster_hit for row in rows], x0, y0, width, height, 0.0, 1.0)
    reward_points = category_points([row.last_true_reward for row in rows], x0, y0, width, height, 0.0, 1.0)
    parts.append(polyline(cluster_points, "#2f855a"))
    parts.append(polyline(reward_points, "#9a6b14"))
    for point in cluster_points:
        parts.append(circle(*point, "#2f855a"))
    for point in reward_points:
        parts.append(circle(*point, "#9a6b14"))

    x1, y1, w1, h1 = 625, 118, 430, 285
    draw_category_axes(parts, labels, x1, y1, w1, h1, 0.0, 1.1, [0.0, 0.25, 0.50, 0.75, 1.0], "Route usage and context cost")
    dense_points = category_points([row.dense_rate for row in rows], x1, y1, w1, h1, 0.0, 1.1)
    linucb_points = category_points([row.linucb_rate for row in rows], x1, y1, w1, h1, 0.0, 1.1)
    token_points = category_points([row.token_ratio for row in rows], x1, y1, w1, h1, 0.0, 1.1)
    parts.append(polyline(dense_points, "#1f5f8b"))
    parts.append(polyline(linucb_points, "#2f855a"))
    parts.append(polyline(token_points, "#b42318"))
    for point in dense_points:
        parts.append(circle(*point, "#1f5f8b"))
    for point in linucb_points:
        parts.append(circle(*point, "#2f855a"))
    for point in token_points:
        parts.append(circle(*point, "#b42318"))

    legend = [
        (130, 92, "#2f855a", "Selected-cluster hit / LinUCB rate"),
        (365, 92, "#9a6b14", "Last true reward"),
        (690, 92, "#1f5f8b", "Dense rate"),
        (820, 92, "#b42318", "Token ratio"),
    ]
    for x, y, color, label in legend:
        parts.append(f'<rect x="{x}" y="{y - 10}" width="12" height="12" fill="{color}" />')
        parts.append(text(x + 18, y, label, "legend"))
    parts.append(text(80, 468, "Caption boundary: strong-noise feedback is a failure boundary; oracle feedback is an upper bound.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure5_feedback_adaptation.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_readme() -> None:
    readme = """# Draft Figure Assets

Updated: 2026-07-17

These assets are paper figures generated from tracked experiment artifacts.
Figure 1 remains an author-owned structural placeholder; Figures 2 and 3 are
deterministic vector data figures.

## Files

- `figure1_system_diagram.svg`: method/system diagram.
- `figure1_system_diagram.mmd`: Mermaid source for the system diagram.
- `figure2_token_quality_frontier.svg`: LoTTE technology/search and
  science/search Hit@10 and final context-token frontier plotted by corpus
  chunk count.
- `figure2_token_quality_frontier_data.csv`: source data for Figure 2.
- `figure3_geometry_to_control.svg`: three-panel main-paper geometry-to-control
  figure covering scale diagnostics, random-route attribution, and arm
  granularity/fallback.
- `figure3_geometry_to_control_data.csv`: panel-keyed source data for Figure 3.

The geometry scale trend and feedback-adaptation assets are retained as
supplementary review material:

- `figure3_geometry_diagnostics.svg` and its source CSV;
- `figure5_feedback_adaptation.svg` and its source CSV.

## Regeneration

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py
```

The script uses only the Python standard library.
"""
    (FIGURES / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    token_rows = read_token_rows()
    geometry_rows = read_geometry_rows()
    route_control_rows = read_route_control_rows()
    arm_control_rows = read_arm_control_rows()
    feedback_rows = read_feedback_rows()
    generate_system_diagram()
    generate_token_quality_figure(token_rows)
    generate_geometry_figure(geometry_rows)
    generate_geometry_control_figure(
        geometry_rows,
        route_control_rows,
        arm_control_rows,
    )
    generate_feedback_adaptation_figure(feedback_rows)
    write_readme()


if __name__ == "__main__":
    main()
