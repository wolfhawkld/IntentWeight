#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize Task58 geometry-vs-random ablation artifacts."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"

ROUTE_SUMMARY = RESULTS / "task58_geometry_random_100k_routes" / "linucb_cost_summary.csv"
STATIC_JSON = RESULTS / "task58_static_nearest_100k_context_budget.json"
STATIC_PAIRED = RESULTS / "task58_static_nearest_100k_context_budget.test_paired.csv"
RANDOM_JSON = RESULTS / "task58_uniform_random_100k_context_budget.json"
RANDOM_PAIRED = RESULTS / "task58_uniform_random_100k_context_budget.test_paired.csv"

OUTPUT_PREFIX = RESULTS / "task58_geometry_random_ablation_summary"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> Mapping:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def f(row: Mapping[str, object], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def summarize_setting(
    *,
    setting: str,
    route_mode: str,
    route_rows: Sequence[Mapping[str, object]],
    budget_json: Mapping,
    paired_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    route_matches = [row for row in route_rows if row.get("routing_mode") == route_mode]
    if len(route_matches) != 1:
        raise ValueError(f"Expected one route row for {route_mode}, got {len(route_matches)}")
    route = route_matches[0]
    method_rows = [row for row in paired_rows if row.get("method_label") == "task38"]
    if not method_rows:
        raise ValueError(f"No task38 paired rows for {setting}")

    selected = budget_json.get("selected_policy", {})
    if not isinstance(selected, Mapping):
        raise ValueError(f"selected_policy is not an object for {setting}")

    hit_deltas = [f(row, "hit_delta_mean") for row in method_rows]
    token_savings = [f(row, "token_saving_percent") for row in method_rows]
    method_hits = [f(row, "method_hit@10") for row in method_rows]
    baseline_hits = [f(row, "baseline_hit@10") for row in method_rows]

    return {
        "setting": setting,
        "route_mode": route_mode,
        "num_queries": int(f(method_rows[0], "num_queries")),
        "num_seeds": len(method_rows),
        "seeds": "|".join(str(row.get("seed", "")) for row in method_rows),
        "selected_policy": str(selected.get("policy", "")),
        "calibration_eligible": int(bool(selected.get("eligible", False))),
        "calibration_hit_delta_pp": f(selected, "mean_hit_delta") * 100.0,
        "calibration_token_saving_pct": f(selected, "mean_token_saving_percent"),
        "test_baseline_hit@10": mean(baseline_hits),
        "test_method_hit@10_mean": mean(method_hits),
        "method_hit@10": mean(method_hits),
        "test_hit_delta_pp_mean": mean(hit_deltas) * 100.0,
        "test_hit_delta_pp_min": min(hit_deltas) * 100.0,
        "test_hit_delta_pp_max": max(hit_deltas) * 100.0,
        "test_token_saving_pct_mean": mean(token_savings),
        "test_token_saving_pct_min": min(token_savings),
        "test_token_saving_pct_max": max(token_savings),
        "noninferior_seeds": sum(1 for row in method_rows if str(row.get("noninferior_by_ci")) == "True"),
        "full_top10_hit@10_mean": f(route, "hit@10_mean"),
        "full_top10_evidence_recall@10_mean": f(route, "evidence_recall@10_mean"),
        "last_route_true_reward_mean": f(route, "last_epoch_route_true_reward_mean"),
        "selected_cluster_hit_rate_mean": f(route, "selected_cluster_hit_rate_mean"),
        "dense_query_rate_mean": f(route, "dense_query_rate_mean"),
        "avg_source_candidate_cost_mean": f(route, "avg_source_candidate_cost_mean"),
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = [
        "setting",
        "route_mode",
        "num_queries",
        "num_seeds",
        "seeds",
        "selected_policy",
        "calibration_eligible",
        "calibration_hit_delta_pp",
        "calibration_token_saving_pct",
        "test_baseline_hit@10",
        "test_method_hit@10_mean",
        "method_hit@10",
        "test_hit_delta_pp_mean",
        "test_hit_delta_pp_min",
        "test_hit_delta_pp_max",
        "test_token_saving_pct_mean",
        "test_token_saving_pct_min",
        "test_token_saving_pct_max",
        "noninferior_seeds",
        "full_top10_hit@10_mean",
        "full_top10_evidence_recall@10_mean",
        "last_route_true_reward_mean",
        "selected_cluster_hit_rate_mean",
        "dense_query_rate_mean",
        "avg_source_candidate_cost_mean",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task58 Geometry Random Ablation Summary",
        "",
        "Task58 compares static nearest-centroid geometry against uniform random",
        "cluster-arm selection on LoTTE technology/search 100k. Both settings keep",
        "the same dense/BM25/cluster multi-route fusion surface and are evaluated",
        "with the same Task38 calibration/test context-budget protocol.",
        "",
        "## Route-Level Result",
        "",
        "| Setting | Full Top-10 Hit@10 | EvidenceRecall@10 | Route Reward | Selected Cluster Hit | Dense Rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {setting} | {hit:.4f} | {er:.4f} | {reward:.4f} | {cluster:.4f} | {dense:.4f} |".format(
                setting=row["setting"],
                hit=float(row["full_top10_hit@10_mean"]),
                er=float(row["full_top10_evidence_recall@10_mean"]),
                reward=float(row["last_route_true_reward_mean"]),
                cluster=float(row["selected_cluster_hit_rate_mean"]),
                dense=float(row["dense_query_rate_mean"]),
            )
        )

    lines.extend([
        "",
        "## Budgeted Frozen-Test Result",
        "",
        "| Setting | Selected Policy | Calibration Eligible | Test Hit Delta | Token Saving | NI Seeds |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ])
    for row in rows:
        lines.append(
            "| {setting} | `{policy}` | {eligible} | {delta:+.2f} pp | {saving:.2f}% | {ni}/{n} |".format(
                setting=row["setting"],
                policy=row["selected_policy"],
                eligible=bool(int(row["calibration_eligible"])),
                delta=float(row["test_hit_delta_pp_mean"]),
                saving=float(row["test_token_saving_pct_mean"]),
                ni=int(row["noninferior_seeds"]),
                n=int(row["num_seeds"]),
            )
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "The full fused ranking is protected by dense/BM25 rescue paths: uniform",
        "random cluster-arm selection does not collapse final Hit@10 under the",
        "full multi-route surface. This means final Hit@10 alone is not a clean",
        "test of whether geometry matters.",
        "",
        "The route-control metrics tell the important story. Static nearest-centroid",
        "geometry has a much higher route reward and selected-cluster hit than the",
        "uniform random control. Therefore geometry should be written as a useful",
        "route-control and confidence signal, not as a standalone replacement for",
        "dense retrieval.",
        "",
        "The random control can still obtain strong budgeted Hit@10 because the",
        "dense/BM25 rescue surface is active. This is boundary evidence that the",
        "paper should not claim geometry alone explains final fused-ranking gains.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    route_rows = load_csv(ROUTE_SUMMARY)
    rows = [
        summarize_setting(
            setting="static_nearest",
            route_mode="static_nearest_ensemble",
            route_rows=route_rows,
            budget_json=load_json(STATIC_JSON),
            paired_rows=load_csv(STATIC_PAIRED),
        ),
        summarize_setting(
            setting="uniform_random",
            route_mode="uniform_random_ensemble",
            route_rows=route_rows,
            budget_json=load_json(RANDOM_JSON),
            paired_rows=load_csv(RANDOM_PAIRED),
        ),
    ]

    OUTPUT_PREFIX.parent.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_PREFIX.with_suffix(".csv"), rows)
    payload = {
        "task": "task58_geometry_random_ablation",
        "updated": "2026-06-25",
        "dataset": "lotte_technology_search_100k",
        "split": "task38 calibration/test",
        "fixed_seeds": [13, 17, 19],
        "rows": rows,
        "source_files": [
            str(ROUTE_SUMMARY.relative_to(ROOT)),
            str(STATIC_JSON.relative_to(ROOT)),
            str(STATIC_PAIRED.relative_to(ROOT)),
            str(RANDOM_JSON.relative_to(ROOT)),
            str(RANDOM_PAIRED.relative_to(ROOT)),
        ],
    }
    OUTPUT_PREFIX.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_md(OUTPUT_PREFIX.with_suffix(".md"), rows)
    print(f"wrote {OUTPUT_PREFIX.with_suffix('.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
