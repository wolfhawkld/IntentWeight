#!/usr/bin/env python3
"""Generate paper-facing draft figures for Task36.6.

The script intentionally uses only the Python standard library so the draft
figures can be regenerated in the project virtual environment without adding
plotting dependencies.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"
FIGURES = ROOT / "paper" / "full_draft" / "figures"


SCALES = ["100k", "200k", "400k", "638k"]


@dataclass(frozen=True)
class TokenRow:
    scale: str
    policy_hit_delta_pp: float
    policy_saving_pct: float
    dense_adaptive_hit_delta_pp: float
    dense_adaptive_saving_pct: float


@dataclass(frozen=True)
class GeometryRow:
    scale: str
    pca_dim90: float
    pca_var64: float
    cluster_hit3: float
    context_retention10: float


def read_token_rows() -> list[TokenRow]:
    # Frozen calibration/test values from the calibrated token-budget validation.
    # Kept explicit here so Figure 2 reflects the main paper table rather than
    # the older confidence-only frontier.
    return [
        TokenRow("100k", 0.00, 6.18, -1.44, 13.83),
        TokenRow("200k", 1.20, 16.00, -2.40, 21.95),
        TokenRow("400k", 2.32, 6.57, -0.24, 11.44),
        TokenRow("638k", -0.08, 17.53, -3.84, 21.90),
    ]


def read_geometry_rows() -> list[GeometryRow]:
    path = RESULTS / "task30_lotte_geometry_scale_validation.csv"
    by_scale: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_scale[row["scale"]] = row

    rows: list[GeometryRow] = []
    for scale in SCALES:
        row = by_scale[scale]
        rows.append(
            GeometryRow(
                scale=scale,
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


def svg_header(width: int, height: int) -> list[str]:
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
        ".title { font-size: 22px; font-weight: 700; }",
        ".subtitle { font-size: 13px; fill: #52606d; }",
        ".axis { stroke: #9aa5b1; stroke-width: 1; }",
        ".grid { stroke: #e4e7eb; stroke-width: 1; }",
        ".label { font-size: 12px; fill: #52606d; }",
        ".tick { font-size: 11px; fill: #616e7c; }",
        ".legend { font-size: 12px; fill: #323f4b; }",
        ".box-title { font-size: 13px; font-weight: 700; }",
        ".box-text { font-size: 11px; fill: #52606d; }",
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


def polyline(points: list[tuple[float, float]], color: str, width: float = 2.8) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width:.1f}" />'


def circle(x: float, y: float, color: str) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}" stroke="#ffffff" stroke-width="1.5" />'


def chart_points(values: list[float], x0: float, y0: float, width: float, height: float, y_min: float, y_max: float) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for idx, value in enumerate(values):
        x = x0 + idx * (width / (len(values) - 1))
        y = y0 + height - ((value - y_min) / (y_max - y_min)) * height
        points.append((x, y))
    return points


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


def generate_system_diagram() -> None:
    parts = svg_header(1120, 520)
    parts.append(text(40, 42, "Figure 1. IntentWeight evidence-selection controller", "title"))
    parts.append(text(40, 64, "Dense/BM25 are global recall routes; LinUCB selects cluster-local arms and budget confidence.", "subtitle"))

    boxes = [
        (40, 120, 150, 88, "#e8f4fd", "#1f5f8b", "Query", ["user/session", "context"]),
        (230, 120, 165, 88, "#eefcf6", "#2f855a", "Feature builder", ["query embedding", "route signals"]),
        (455, 78, 175, 58, "#f5f7fa", "#425466", "Dense global", ["semantic recall floor"]),
        (455, 154, 175, 58, "#f5f7fa", "#425466", "BM25 global", ["lexical anchors"]),
        (455, 230, 175, 72, "#fff7e6", "#9a6b14", "LinUCB selector", ["fixed cluster arms", "confidence scores"]),
        (690, 230, 175, 72, "#fff7e6", "#9a6b14", "Cluster-local dense", ["search selected arms", "local evidence"]),
        (690, 130, 175, 76, "#eefcf6", "#2f855a", "Rank fusion", ["merge route", "candidates"]),
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
        (630, 266, 905, 206),
        (992, 206, 992, 300),
        (905, 338, 645, 388),
        (550, 350, 550, 302),
    ]
    for x1, y1, x2, y2 in arrows:
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#425466" '
            'stroke-width="1.8" marker-end="url(#arrow)" />'
        )

    parts.append(text(40, 470, "Figure boundary: the current experiments evaluate retrieval/context tokens; broader agent-memory carriers remain future work.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure1_system_diagram.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")

    mermaid = """flowchart LR
    Q[Query and user/session context] --> F[Feature construction]
    F --> D[Dense global recall floor]
    F --> B[BM25 lexical recall]
    F --> P[LinUCB cluster-arm selector]
    P --> C[Cluster-local dense search]
    D --> R[Rank fusion]
    B --> R
    C --> R
    P --> G[Confidence-based final context budget]
    R --> G
    G --> A[Generator or downstream agent response]
    A --> T[Trust-weighted feedback]
    T --> P
"""
    (FIGURES / "figure1_system_diagram.mmd").write_text(mermaid, encoding="utf-8")


def generate_token_quality_figure(rows: list[TokenRow]) -> None:
    write_csv(
        FIGURES / "figure2_token_quality_frontier_data.csv",
        [
            "scale",
            "policy_hit_delta_pp",
            "policy_saving_pct",
            "dense_adaptive_hit_delta_pp",
            "dense_adaptive_saving_pct",
        ],
        [
            {
                "scale": row.scale,
                "policy_hit_delta_pp": f"{row.policy_hit_delta_pp:.2f}",
                "policy_saving_pct": f"{row.policy_saving_pct:.2f}",
                "dense_adaptive_hit_delta_pp": f"{row.dense_adaptive_hit_delta_pp:.2f}",
                "dense_adaptive_saving_pct": f"{row.dense_adaptive_saving_pct:.2f}",
            }
            for row in rows
        ],
    )

    parts = svg_header(1060, 520)
    parts.append(text(40, 42, "Figure 2. Calibrated token-quality frontier across LoTTE scale", "title"))
    parts.append(text(40, 64, "IntentWeight saves final LLM evidence-context tokens while avoiding dense-truncation Hit@10 loss.", "subtitle"))

    labels = [row.scale for row in rows]
    x0, y0, width, height = 80, 118, 420, 290
    draw_axes(parts, x0, y0, width, height, -4.0, 3.0, [-4.0, -2.0, 0.0, 2.0], labels, "Hit@10 delta vs dense (pp)")
    policy_points = chart_points([row.policy_hit_delta_pp for row in rows], x0, y0, width, height, -4.0, 3.0)
    dense_points = chart_points([row.dense_adaptive_hit_delta_pp for row in rows], x0, y0, width, height, -4.0, 3.0)
    zero_y = y0 + height - ((0.0 - -4.0) / 7.0) * height
    parts.append(line(x0, zero_y, x0 + width, zero_y, "#b8c2cc", 1.2))
    parts.append(polyline(policy_points, "#2f855a"))
    parts.append(polyline(dense_points, "#1f5f8b"))
    for point in policy_points:
        parts.append(circle(*point, "#2f855a"))
    for point in dense_points:
        parts.append(circle(*point, "#1f5f8b"))
    parts.append(f'<rect x="260" y="92" width="12" height="12" fill="#2f855a" />')
    parts.append(text(278, 103, "IntentWeight budget", "legend"))
    parts.append(f'<rect x="410" y="92" width="12" height="12" fill="#1f5f8b" />')
    parts.append(text(428, 103, "Dense adaptive truncation", "legend"))

    x1, y1, w1, h1 = 600, 118, 360, 290
    draw_axes(parts, x1, y1, w1, h1, 0.0, 24.0, [0.0, 8.0, 16.0, 24.0], labels, "Final context token saving (%)")
    saving_points = chart_points([row.policy_saving_pct for row in rows], x1, y1, w1, h1, 0.0, 24.0)
    dense_saving_points = chart_points([row.dense_adaptive_saving_pct for row in rows], x1, y1, w1, h1, 0.0, 24.0)
    parts.append(polyline(saving_points, "#2f855a"))
    parts.append(polyline(dense_saving_points, "#1f5f8b"))
    for row, (x, y) in zip(rows, saving_points):
        parts.append(circle(x, y, "#2f855a"))
        parts.append(text(x, y - 12, f"{row.policy_saving_pct:.1f}%", "tick", "middle"))
    for row, (x, y) in zip(rows, dense_saving_points):
        parts.append(circle(x, y, "#1f5f8b"))
        parts.append(text(x, y + 18, f"{row.dense_adaptive_saving_pct:.1f}%", "tick", "middle"))

    parts.append(text(80, 468, "Caption boundary: dense truncation saves more tokens but loses Hit@10; IntentWeight targets the safer frontier.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure2_token_quality_frontier.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def generate_geometry_figure(rows: list[GeometryRow]) -> None:
    write_csv(
        FIGURES / "figure3_geometry_diagnostics_data.csv",
        ["scale", "pca_dim90", "pca_var64", "nearest_cluster_hit_at_3", "context_retention_at_10"],
        [
            {
                "scale": row.scale,
                "pca_dim90": f"{row.pca_dim90:.0f}",
                "pca_var64": f"{row.pca_var64:.4f}",
                "nearest_cluster_hit_at_3": f"{row.cluster_hit3:.4f}",
                "context_retention_at_10": f"{row.context_retention10:.4f}",
            }
            for row in rows
        ],
    )

    parts = svg_header(1060, 520)
    parts.append(text(40, 42, "Figure 3. Geometry diagnostics across LoTTE scale", "title"))
    parts.append(text(40, 64, "Local cluster geometry remains useful, while context retention and PCA concentration decline with scale.", "subtitle"))

    labels = [row.scale for row in rows]
    x0, y0, width, height = 90, 118, 790, 290
    draw_axes(parts, x0, y0, width, height, 0.55, 0.95, [0.55, 0.65, 0.75, 0.85, 0.95], labels, "Diagnostic value")
    series = [
        ("NearestClusterHit@3", [row.cluster_hit3 for row in rows], "#2f855a"),
        ("ContextRetention@10", [row.context_retention10 for row in rows], "#1f5f8b"),
        ("PCAvar@64", [row.pca_var64 for row in rows], "#9a6b14"),
    ]
    for name, values, color in series:
        points = chart_points(values, x0, y0, width, height, 0.55, 0.95)
        parts.append(polyline(points, color))
        for point in points:
            parts.append(circle(*point, color))

    legend_x = 760
    for idx, (name, _, color) in enumerate(series):
        y = 88 + idx * 22
        parts.append(f'<rect x="{legend_x}" y="{y - 10}" width="12" height="12" fill="{color}" />')
        parts.append(text(legend_x + 18, y, name, "legend"))

    for row, idx in zip(rows, range(len(rows))):
        x = x0 + idx * (width / (len(rows) - 1))
        parts.append(text(x, 438, f"PCAdim90={row.pca_dim90:.0f}", "tick", "middle"))

    parts.append(text(90, 468, "Caption boundary: diagnostics support local-structure routing; they are not theorem-level manifold proof.", "subtitle"))
    parts.append("</svg>")
    (FIGURES / "figure3_geometry_diagnostics.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_readme() -> None:
    readme = """# Draft Figure Assets

Updated: 2026-05-31

These assets are draft paper figures generated from existing experiment
artifacts. They are intended for writing and review, not as final camera-ready
venue artwork.

## Files

- `figure1_system_diagram.svg`: method/system diagram.
- `figure1_system_diagram.mmd`: Mermaid source for the system diagram.
- `figure2_token_quality_frontier.svg`: LoTTE Hit@10 and final context-token
  frontier.
- `figure2_token_quality_frontier_data.csv`: source data for Figure 2.
- `figure3_geometry_diagnostics.svg`: LoTTE geometry diagnostic trend.
- `figure3_geometry_diagnostics_data.csv`: source data for Figure 3.

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
    generate_system_diagram()
    generate_token_quality_figure(token_rows)
    generate_geometry_figure(geometry_rows)
    write_readme()


if __name__ == "__main__":
    main()
