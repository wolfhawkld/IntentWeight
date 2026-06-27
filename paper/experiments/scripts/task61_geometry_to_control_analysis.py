#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task61 geometry-to-control diagnostic analysis.

This script connects existing geometry diagnostics to route-control and
budget-control outcomes. It is intentionally diagnostic: the sample sizes are
too small for theorem-level or causal claims.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"
FIGURE4_DATA = ROOT / "paper" / "full_draft" / "figures" / "figure4_geometry_to_gain_data.csv"
TASK30_GEOMETRY = RESULTS / "task30_lotte_geometry_scale_validation.csv"
TASK43_GEOMETRY = RESULTS / "task43_lotte_science_geometry_diagnostics.csv"
TASK58_SUMMARY = RESULTS / "task58_geometry_random_ablation_summary.csv"
TASK60_SUMMARY = RESULTS / "task60_arm_count_sensitivity_summary.csv"

OUTPUT_PREFIX = RESULTS / "task61_geometry_to_control_analysis"
POINTS_CSV = RESULTS / "task61_geometry_to_control_points.csv"
TOP_LEVEL_MD = ROOT / "paper" / "experiments" / "task61_geometry_to_control_analysis.md"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def f(row: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = finite_float(row.get(key))
    return default if value is None else value


def canonical_scale(scale: str) -> str:
    return scale.replace("_q", "/q")


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    x_terms = [x - x_mean for x in xs]
    y_terms = [y - y_mean for y in ys]
    x_ss = sum(term * term for term in x_terms)
    y_ss = sum(term * term for term in y_terms)
    if x_ss <= 0.0 or y_ss <= 0.0:
        return None
    return sum(x * y for x, y in zip(x_terms, y_terms)) / math.sqrt(x_ss * y_ss)


def rankdata(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    return pearson(rankdata(xs), rankdata(ys))


def corr_strength(value: float | None) -> str:
    if value is None:
        return "undefined"
    magnitude = abs(value)
    if magnitude >= 0.8:
        label = "very_strong"
    elif magnitude >= 0.5:
        label = "strong"
    elif magnitude >= 0.3:
        label = "moderate"
    else:
        label = "weak"
    direction = "positive" if value > 0 else "negative" if value < 0 else "zero"
    return f"{label}_{direction}"


def load_geometry_sources() -> dict[tuple[str, str], dict[str, str]]:
    sources: dict[tuple[str, str], dict[str, str]] = {}
    for row in load_csv(TASK30_GEOMETRY):
        sources[("technology/search", canonical_scale(row["scale"]))] = row
    for row in load_csv(TASK43_GEOMETRY):
        sources[("science/search", canonical_scale(row["scale"]))] = row
    return sources


def build_figure4_points() -> list[dict[str, object]]:
    geometry_sources = load_geometry_sources()
    points: list[dict[str, object]] = []
    for row in load_csv(FIGURE4_DATA):
        key = (row["domain"], canonical_scale(row["scale"]))
        source = geometry_sources.get(key, {})
        points.append(
            {
                "analysis_group": "figure4_cross_scale",
                "observation_label": f"{row['domain']}:{row['scale']}",
                "domain": row["domain"],
                "scale": row["scale"],
                "num_queries": int(f(source, "num_queries", 0.0)),
                "corpus_chunks": int(f(row, "corpus_chunks")),
                "arm_count": 32,
                "nearest_cluster_hit_at_3": f(row, "nearest_cluster_hit_at_3"),
                "context_retention_at_10": f(row, "context_retention_at_10"),
                "policy_hit_delta_pp": f(row, "policy_hit_delta_pp"),
                "policy_saving_pct": f(row, "policy_saving_pct"),
                "pca_dim_for_90pct": int(f(source, "pca_sample_dim_for_90pct", 0.0)),
                "pca_var_at_64": f(source, "pca_sample_var@64"),
                "static_route_reward": "",
                "static_cluster_hit": "",
                "learned_route_reward": "",
                "learned_cluster_hit": "",
                "full_hit_delta_pp": "",
                "full_token_saving_pct": "",
                "full_hit_at_10": "",
                "gated_dense_rate": "",
                "gated_primary_rate": "",
                "gated_hit_delta_pp": "",
                "gated_token_saving_pct": "",
                "note": "paper_figure_diagnostic",
            }
        )
    return points


def build_task60_points() -> list[dict[str, object]]:
    rows = load_csv(TASK60_SUMMARY)
    by_k: dict[int, dict[str, dict[str, str]]] = {}
    for row in rows:
        by_k.setdefault(int(f(row, "arm_count")), {})[row["route_mode"]] = row

    points: list[dict[str, object]] = []
    for arm_count in sorted(by_k):
        static = by_k[arm_count]["static_nearest_ensemble"]
        full = by_k[arm_count]["full_multi_route"]
        gated = by_k[arm_count]["gated_cost_aware"]
        points.append(
            {
                "analysis_group": "task60_arm_count",
                "observation_label": f"technology/search:100k:K{arm_count}",
                "domain": "technology/search",
                "scale": "100k",
                "num_queries": int(f(full, "num_queries")),
                "corpus_chunks": 101311,
                "arm_count": arm_count,
                "nearest_cluster_hit_at_3": "",
                "context_retention_at_10": "",
                "policy_hit_delta_pp": "",
                "policy_saving_pct": "",
                "pca_dim_for_90pct": "",
                "pca_var_at_64": "",
                "static_route_reward": f(static, "last_route_true_reward_mean"),
                "static_cluster_hit": f(static, "selected_cluster_hit_rate_mean"),
                "learned_route_reward": f(full, "last_route_true_reward_mean"),
                "learned_cluster_hit": f(full, "selected_cluster_hit_rate_mean"),
                "full_hit_delta_pp": f(full, "test_hit_delta_pp_mean"),
                "full_token_saving_pct": f(full, "test_token_saving_pct_mean"),
                "full_hit_at_10": f(full, "full_top10_hit@10_mean"),
                "gated_dense_rate": f(gated, "dense_query_rate_mean"),
                "gated_primary_rate": f(gated, "linucb_primary_rate_mean"),
                "gated_hit_delta_pp": f(gated, "test_hit_delta_pp_mean"),
                "gated_token_saving_pct": f(gated, "test_token_saving_pct_mean"),
                "note": "arm_count_control_diagnostic",
            }
        )
    return points


def paired_values(rows: Sequence[Mapping[str, object]], x_key: str, y_key: str) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        x_value = finite_float(row.get(x_key))
        y_value = finite_float(row.get(y_key))
        if x_value is None or y_value is None:
            continue
        xs.append(x_value)
        ys.append(y_value)
    return xs, ys


def make_correlation(
    *,
    analysis_group: str,
    rows: Sequence[Mapping[str, object]],
    x_key: str,
    y_key: str,
    interpretation: str,
) -> dict[str, object]:
    xs, ys = paired_values(rows, x_key, y_key)
    pearson_r = pearson(xs, ys)
    spearman_r = spearman(xs, ys)
    return {
        "analysis_group": analysis_group,
        "x_metric": x_key,
        "y_metric": y_key,
        "n": len(xs),
        "pearson_r": "" if pearson_r is None else pearson_r,
        "spearman_r": "" if spearman_r is None else spearman_r,
        "pearson_pattern": corr_strength(pearson_r),
        "spearman_pattern": corr_strength(spearman_r),
        "interpretation": interpretation,
    }


def build_correlations(points: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    figure4 = [row for row in points if row["analysis_group"] == "figure4_cross_scale"]
    task60 = [row for row in points if row["analysis_group"] == "task60_arm_count"]

    specs = [
        (
            "figure4_cross_scale",
            figure4,
            "nearest_cluster_hit_at_3",
            "policy_hit_delta_pp",
            "Small-N diagnostic: local GT concentration does not by itself determine final Hit delta.",
        ),
        (
            "figure4_cross_scale",
            figure4,
            "nearest_cluster_hit_at_3",
            "policy_saving_pct",
            "Small-N diagnostic: token saving depends on budget policy and rescue paths, not only geometry.",
        ),
        (
            "figure4_cross_scale",
            figure4,
            "context_retention_at_10",
            "policy_hit_delta_pp",
            "Small-N diagnostic: context retention is a design signal, not a deterministic quality guarantee.",
        ),
        (
            "figure4_cross_scale",
            figure4,
            "context_retention_at_10",
            "policy_saving_pct",
            "Small-N diagnostic: retention and saving expose a quality-cost trade-off surface.",
        ),
        (
            "figure4_cross_scale",
            figure4,
            "pca_dim_for_90pct",
            "context_retention_at_10",
            "Small-N diagnostic: higher effective dimensionality coincides with lower retention in this slice.",
        ),
        (
            "task60_arm_count",
            task60,
            "arm_count",
            "learned_route_reward",
            "Control diagnostic: finer arms dilute feedback and reduce learned route reward.",
        ),
        (
            "task60_arm_count",
            task60,
            "arm_count",
            "learned_cluster_hit",
            "Control diagnostic: finer arms make selected learned clusters less directly reliable.",
        ),
        (
            "task60_arm_count",
            task60,
            "learned_route_reward",
            "gated_dense_rate",
            "Control diagnostic: weaker learned route reward pushes the gate back toward dense retrieval.",
        ),
        (
            "task60_arm_count",
            task60,
            "learned_route_reward",
            "gated_primary_rate",
            "Control diagnostic: stronger route reward allows more LinUCB-primary decisions.",
        ),
        (
            "task60_arm_count",
            task60,
            "learned_route_reward",
            "gated_hit_delta_pp",
            "Control diagnostic: route reliability tracks the quality loss of aggressive gating.",
        ),
        (
            "task60_arm_count",
            task60,
            "static_route_reward",
            "full_hit_delta_pp",
            "Design diagnostic: static geometry is useful, while final Hit is also protected by fusion/rescue.",
        ),
        (
            "task60_arm_count",
            task60,
            "arm_count",
            "gated_dense_rate",
            "Deployment diagnostic: larger K pushes the current learned gate toward dense fallback.",
        ),
    ]

    return [
        make_correlation(
            analysis_group=group,
            rows=rows,
            x_key=x_key,
            y_key=y_key,
            interpretation=interpretation,
        )
        for group, rows, x_key, y_key, interpretation in specs
    ]


def build_task58_contrast() -> dict[str, object]:
    rows = {row["setting"]: row for row in load_csv(TASK58_SUMMARY)}
    static = rows["static_nearest"]
    random = rows["uniform_random"]
    return {
        "static_route_reward": f(static, "last_route_true_reward_mean"),
        "random_route_reward": f(random, "last_route_true_reward_mean"),
        "route_reward_gain_pp": (f(static, "last_route_true_reward_mean") - f(random, "last_route_true_reward_mean")) * 100.0,
        "static_selected_cluster_hit": f(static, "selected_cluster_hit_rate_mean"),
        "random_selected_cluster_hit": f(random, "selected_cluster_hit_rate_mean"),
        "selected_cluster_hit_gain_pp": (f(static, "selected_cluster_hit_rate_mean") - f(random, "selected_cluster_hit_rate_mean")) * 100.0,
        "static_test_hit_delta_pp": f(static, "test_hit_delta_pp_mean"),
        "random_test_hit_delta_pp": f(random, "test_hit_delta_pp_mean"),
        "test_hit_delta_gap_pp": f(static, "test_hit_delta_pp_mean") - f(random, "test_hit_delta_pp_mean"),
        "static_token_saving_pct": f(static, "test_token_saving_pct_mean"),
        "random_token_saving_pct": f(random, "test_token_saving_pct_mean"),
        "token_saving_gap_pct": f(static, "test_token_saving_pct_mean") - f(random, "test_token_saving_pct_mean"),
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object, digits: int = 4) -> str:
    parsed = finite_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}"


def write_result_md(
    path: Path,
    *,
    correlations: Sequence[Mapping[str, object]],
    contrast: Mapping[str, object],
) -> None:
    task60_rows = [row for row in correlations if row["analysis_group"] == "task60_arm_count"]
    figure4_rows = [row for row in correlations if row["analysis_group"] == "figure4_cross_scale"]

    lines = [
        "# Task61 Geometry-To-Control Analysis",
        "",
        "Task61 connects geometry diagnostics to route-control and budget-control",
        "outcomes using already-generated artifacts. It does not rerun retrieval",
        "or claim that the sample size proves a manifold theorem.",
        "",
        "## Figure 4 Cross-Scale Diagnostics",
        "",
        "| X metric | Y metric | n | Pearson r | Spearman r | Pattern |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in figure4_rows:
        lines.append(
            "| {x} | {y} | {n} | {pr} | {sr} | {pattern} |".format(
                x=row["x_metric"],
                y=row["y_metric"],
                n=row["n"],
                pr=fmt(row["pearson_r"]),
                sr=fmt(row["spearman_r"]),
                pattern=row["pearson_pattern"],
            )
        )

    lines.extend(
        [
            "",
            "These cross-scale correlations are mixed and small-N. This is useful",
            "because it prevents an overclaim: geometry diagnostics explain why local",
            "route structure is worth using, but final Hit@10 and token saving are",
            "also shaped by fusion, dense/BM25 rescue, and the calibrated budget",
            "policy.",
            "",
            "## Task60 Route-Control Diagnostics",
            "",
            "| X metric | Y metric | n | Pearson r | Spearman r | Pattern |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in task60_rows:
        lines.append(
            "| {x} | {y} | {n} | {pr} | {sr} | {pattern} |".format(
                x=row["x_metric"],
                y=row["y_metric"],
                n=row["n"],
                pr=fmt(row["pearson_r"]),
                sr=fmt(row["spearman_r"]),
                pattern=row["pearson_pattern"],
            )
        )

    lines.extend(
        [
            "",
            "The control-layer signal is clearer than the final-gain signal. As K",
            "increases, learned route reward and selected-cluster hit decline, and the",
            "current gated controller falls back to dense retrieval more often. This",
            "supports the interpretation that geometry is most defensible as a",
            "route-control surface and confidence signal.",
            "",
            "## Task58 Random-Control Anchor",
            "",
            "| Contrast | Value |",
            "| --- | ---: |",
            f"| Static minus random route reward | {contrast['route_reward_gain_pp']:+.2f} pp |",
            f"| Static minus random selected-cluster hit | {contrast['selected_cluster_hit_gain_pp']:+.2f} pp |",
            f"| Static minus random final test Hit delta | {contrast['test_hit_delta_gap_pp']:+.2f} pp |",
            f"| Static minus random token saving | {contrast['token_saving_gap_pct']:+.2f}% |",
            "",
            "Task58 is the clearest route-level control: static geometry strongly beats",
            "uniform random selection on route reward and selected-cluster hit. The much",
            "smaller final Hit gap is expected because dense/BM25 rescue protects the",
            "fused result.",
            "",
            "## Paper-Facing Conclusion",
            "",
            "Use Task61 to write a bounded claim:",
            "",
            "> Geometry diagnostics are explanatory and design-guiding signals for",
            "> structured route control. They are not standalone proof that a smooth",
            "> manifold governs retrieval, and they do not alone explain final Hit@10.",
            "",
            "This preserves the core method: local geometry defines structured arms,",
            "feedback-updated LinUCB estimates route reliability, and calibrated budget",
            "control converts reliable decisions into final-context savings.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_top_level_md(path: Path, result_md: Path) -> None:
    rel_result = result_md.relative_to(ROOT)
    lines = [
        "# Task61 Geometry-To-Control / Geometry-To-Gain Analysis",
        "",
        "Updated: 2026-06-26",
        "",
        "## Objective",
        "",
        "Task61 connects the existing geometry diagnostics to route-control outcomes",
        "without making a theorem-level manifold claim. The task uses existing",
        "artifacts only:",
        "",
        "- Task30 technology/search geometry diagnostics;",
        "- Task43 science/search geometry diagnostics;",
        "- Task58 geometry-vs-random route control;",
        "- Task60 arm-count sensitivity;",
        "- Figure 4 geometry-to-gain diagnostic data.",
        "",
        "## Artifacts",
        "",
        "- Script: `paper/experiments/scripts/task61_geometry_to_control_analysis.py`",
        f"- Result report: `{rel_result}`",
        "- Correlation CSV: `paper/experiments/results/task61_geometry_to_control_analysis.csv`",
        "- Observation CSV: `paper/experiments/results/task61_geometry_to_control_points.csv`",
        "- JSON payload: `paper/experiments/results/task61_geometry_to_control_analysis.json`",
        "",
        "## Main Interpretation",
        "",
        "The evidence is strongest at the route-control layer. Task58 shows that",
        "static geometry strongly outperforms uniform random route selection on",
        "route reward and selected-cluster hit. Task60 shows that learned route",
        "reward and cluster hit fall as K becomes too fine, and the gated controller",
        "responds by increasing dense fallback.",
        "",
        "The cross-scale Figure 4 correlations are mixed and small-N. That result is",
        "useful: it keeps the paper from overclaiming that geometry alone determines",
        "final Hit@10 or token saving. Final quality-cost behavior is produced by",
        "the full controller: geometry-defined arms, feedback-updated LinUCB route",
        "confidence, dense/BM25 rescue, and calibrated final-context budgeting.",
        "",
        "## Paper-Use Guidance",
        "",
        "Write:",
        "",
        "> Geometry diagnostics provide explanatory and design-guiding signals for",
        "> structured route control, while final quality-cost gains arise from the",
        "> calibrated multi-route controller.",
        "",
        "Do not write:",
        "",
        "> The manifold hypothesis is proven, or geometry alone explains final Hit@10.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    points = build_figure4_points() + build_task60_points()
    correlations = build_correlations(points)
    contrast = build_task58_contrast()

    point_fields = [
        "analysis_group",
        "observation_label",
        "domain",
        "scale",
        "num_queries",
        "corpus_chunks",
        "arm_count",
        "nearest_cluster_hit_at_3",
        "context_retention_at_10",
        "policy_hit_delta_pp",
        "policy_saving_pct",
        "pca_dim_for_90pct",
        "pca_var_at_64",
        "static_route_reward",
        "static_cluster_hit",
        "learned_route_reward",
        "learned_cluster_hit",
        "full_hit_delta_pp",
        "full_token_saving_pct",
        "full_hit_at_10",
        "gated_dense_rate",
        "gated_primary_rate",
        "gated_hit_delta_pp",
        "gated_token_saving_pct",
        "note",
    ]
    corr_fields = [
        "analysis_group",
        "x_metric",
        "y_metric",
        "n",
        "pearson_r",
        "spearman_r",
        "pearson_pattern",
        "spearman_pattern",
        "interpretation",
    ]

    write_csv(POINTS_CSV, points, point_fields)
    write_csv(OUTPUT_PREFIX.with_suffix(".csv"), correlations, corr_fields)

    payload = {
        "task": "Task61 Geometry-To-Control / Geometry-To-Gain Analysis",
        "updated": "2026-06-26",
        "inputs": [
            str(TASK30_GEOMETRY.relative_to(ROOT)),
            str(TASK43_GEOMETRY.relative_to(ROOT)),
            str(TASK58_SUMMARY.relative_to(ROOT)),
            str(TASK60_SUMMARY.relative_to(ROOT)),
            str(FIGURE4_DATA.relative_to(ROOT)),
        ],
        "outputs": {
            "points_csv": str(POINTS_CSV.relative_to(ROOT)),
            "correlations_csv": str(OUTPUT_PREFIX.with_suffix(".csv").relative_to(ROOT)),
            "result_md": str(OUTPUT_PREFIX.with_suffix(".md").relative_to(ROOT)),
            "top_level_md": str(TOP_LEVEL_MD.relative_to(ROOT)),
        },
        "points": points,
        "correlations": correlations,
        "task58_geometry_random_contrast": contrast,
        "paper_claim": (
            "Geometry diagnostics are explanatory and design-guiding signals for "
            "structured route control; final quality-cost gains come from the "
            "calibrated multi-route controller rather than geometry alone."
        ),
    }
    with OUTPUT_PREFIX.with_suffix(".json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    write_result_md(OUTPUT_PREFIX.with_suffix(".md"), correlations=correlations, contrast=contrast)
    write_top_level_md(TOP_LEVEL_MD, OUTPUT_PREFIX.with_suffix(".md"))
    print(json.dumps({"points": len(points), "correlations": len(correlations)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
