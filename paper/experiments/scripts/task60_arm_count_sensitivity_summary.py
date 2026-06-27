#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize Task60 arm-count sensitivity artifacts."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"

ARM_COUNTS = [8, 16, 32, 64, 128]
ROUTE_MODES = [
    ("static_nearest_ensemble", "static"),
    ("full_multi_route", "full"),
    ("gated_cost_aware", "gated"),
]
OUTPUT_PREFIX = RESULTS / "task60_arm_count_sensitivity_summary"


def route_summary_path(arm_count: int) -> Path:
    return RESULTS / f"task60_arm_count_k{arm_count}_100k" / "linucb_cost_summary.csv"


def route_rankings_path(arm_count: int) -> Path:
    return (
        RESULTS
        / f"task60_arm_count_k{arm_count}_100k"
        / "linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential_rankings.json"
    )


def budget_prefix(arm_count: int, short_mode: str) -> Path:
    return RESULTS / f"task60_k{arm_count}_{short_mode}_100k_context_budget"


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


def summarize_row(arm_count: int, route_mode: str, short_mode: str) -> dict[str, object]:
    route_rows = [
        row for row in load_csv(route_summary_path(arm_count))
        if row.get("routing_mode") == route_mode
    ]
    if len(route_rows) != 1:
        raise ValueError(f"Expected one route row for K={arm_count} mode={route_mode}, got {len(route_rows)}")
    route = route_rows[0]

    prefix = budget_prefix(arm_count, short_mode)
    budget_json = load_json(prefix.with_suffix(".json"))
    selected = budget_json.get("selected_policy", {})
    if not isinstance(selected, Mapping):
        raise ValueError(f"selected_policy is not an object for K={arm_count} mode={route_mode}")
    paired_rows = [
        row for row in load_csv(prefix.with_suffix(".test_paired.csv"))
        if row.get("method_label") == "task38"
    ]
    if not paired_rows:
        raise ValueError(f"No task38 paired rows for K={arm_count} mode={route_mode}")

    hit_deltas = [f(row, "hit_delta_mean") for row in paired_rows]
    token_savings = [f(row, "token_saving_percent") for row in paired_rows]
    method_hits = [f(row, "method_hit@10") for row in paired_rows]
    baseline_hits = [f(row, "baseline_hit@10") for row in paired_rows]
    ci_lows = [f(row, "hit_delta_ci_low") for row in paired_rows]
    ci_highs = [f(row, "hit_delta_ci_high") for row in paired_rows]

    return {
        "arm_count": arm_count,
        "route_mode": route_mode,
        "short_mode": short_mode,
        "num_queries": int(f(paired_rows[0], "num_queries")),
        "num_seeds": len(paired_rows),
        "seeds": "|".join(str(row.get("seed", "")) for row in paired_rows),
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
        "test_hit_delta_ci_low_pp_min": min(ci_lows) * 100.0,
        "test_hit_delta_ci_high_pp_max": max(ci_highs) * 100.0,
        "test_token_saving_pct_mean": mean(token_savings),
        "test_token_saving_pct_min": min(token_savings),
        "test_token_saving_pct_max": max(token_savings),
        "noninferior_seeds": sum(1 for row in paired_rows if str(row.get("noninferior_by_ci")) == "True"),
        "full_top10_hit@10_mean": f(route, "hit@10_mean"),
        "full_top10_evidence_recall@10_mean": f(route, "evidence_recall@10_mean"),
        "last_route_true_reward_mean": f(route, "last_epoch_route_true_reward_mean"),
        "selected_cluster_hit_rate_mean": f(route, "selected_cluster_hit_rate_mean"),
        "avg_confidence_mean": f(route, "avg_confidence_mean"),
        "dense_query_rate_mean": f(route, "dense_query_rate_mean"),
        "dense_saved_rate_mean": f(route, "dense_saved_rate_mean"),
        "linucb_primary_rate_mean": f(route, "linucb_primary_rate_mean"),
        "hybrid_lite_rate_mean": f(route, "hybrid_lite_rate_mean"),
        "full_dense_fallback_rate_mean": f(route, "full_dense_fallback_rate_mean"),
        "avg_source_candidate_cost_mean": f(route, "avg_source_candidate_cost_mean"),
        "n_effective_arms_mean": f(route, "n_effective_arms_mean"),
        "run_elapsed_sec_marker": f(route, "elapsed_sec"),
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = [
        "arm_count",
        "route_mode",
        "short_mode",
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
        "test_hit_delta_ci_low_pp_min",
        "test_hit_delta_ci_high_pp_max",
        "test_token_saving_pct_mean",
        "test_token_saving_pct_min",
        "test_token_saving_pct_max",
        "noninferior_seeds",
        "full_top10_hit@10_mean",
        "full_top10_evidence_recall@10_mean",
        "last_route_true_reward_mean",
        "selected_cluster_hit_rate_mean",
        "avg_confidence_mean",
        "dense_query_rate_mean",
        "dense_saved_rate_mean",
        "linucb_primary_rate_mean",
        "hybrid_lite_rate_mean",
        "full_dense_fallback_rate_mean",
        "avg_source_candidate_cost_mean",
        "n_effective_arms_mean",
        "run_elapsed_sec_marker",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def mode_rows(rows: Sequence[Mapping[str, object]], route_mode: str) -> list[Mapping[str, object]]:
    return [row for row in rows if row["route_mode"] == route_mode]


def write_md(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task60 Arm-Count Sensitivity Summary",
        "",
        "Task60 tests whether the fixed `n_clusters=32` arm design is a brittle",
        "assumption. The experiment runs LoTTE technology/search 100k with MiniLM,",
        "fixed seeds `13,17,19`, and arm counts `K in {8,16,32,64,128}`.",
        "",
        "## Route-Level Sensitivity",
        "",
        "| K | Mode | Full Hit@10 | EvidenceRecall@10 | Route Reward | Cluster Hit | Dense Rate | Primary Rate | Source Cost |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {k} | {mode} | {hit:.4f} | {er:.4f} | {reward:.4f} | {cluster:.4f} | {dense:.4f} | {primary:.4f} | {cost:.2f} |".format(
                k=int(row["arm_count"]),
                mode=row["route_mode"],
                hit=float(row["full_top10_hit@10_mean"]),
                er=float(row["full_top10_evidence_recall@10_mean"]),
                reward=float(row["last_route_true_reward_mean"]),
                cluster=float(row["selected_cluster_hit_rate_mean"]),
                dense=float(row["dense_query_rate_mean"]),
                primary=float(row["linucb_primary_rate_mean"]),
                cost=float(row["avg_source_candidate_cost_mean"]),
            )
        )

    lines.extend([
        "",
        "## Frozen Budget Result",
        "",
        "| K | Mode | Policy | Eligible | Test Hit Delta | Token Saving | NI Seeds |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ])
    for row in rows:
        lines.append(
            "| {k} | {mode} | `{policy}` | {eligible} | {delta:+.2f} pp | {saving:.2f}% | {ni}/{n} |".format(
                k=int(row["arm_count"]),
                mode=row["route_mode"],
                policy=row["selected_policy"],
                eligible=bool(int(row["calibration_eligible"])),
                delta=float(row["test_hit_delta_pp_mean"]),
                saving=float(row["test_token_saving_pct_mean"]),
                ni=int(row["noninferior_seeds"]),
                n=int(row["num_seeds"]),
            )
        )

    static_rewards = [float(row["last_route_true_reward_mean"]) for row in mode_rows(rows, "static_nearest_ensemble")]
    full_hits = [float(row["full_top10_hit@10_mean"]) for row in mode_rows(rows, "full_multi_route")]
    gated_rows = mode_rows(rows, "gated_cost_aware")
    gated_dense_rates = [float(row["dense_query_rate_mean"]) for row in gated_rows]
    gated_hit_deltas = [float(row["test_hit_delta_pp_mean"]) for row in gated_rows]

    lines.extend([
        "",
        "## Interpretation",
        "",
        "Static-nearest geometry is not brittle across this arm-count grid. Its route",
        f"reward stays in `{min(static_rewards):.4f}-{max(static_rewards):.4f}`,",
        "which supports using KMeans arms as an engineering route-control surface",
        "rather than a theoretically unique manifold partition.",
        "",
        "Full multi-route retrieval is also stable at the fused-ranking level:",
        f"full-route Hit@10 stays in `{min(full_hits):.4f}-{max(full_hits):.4f}`.",
        "This stability is partly protected by dense/BM25 rescue paths, so it should",
        "not be interpreted as proof that arm count is irrelevant to route learning.",
        "",
        "Learned gated routing is sensitive to arm count. Smaller K values allow more",
        f"dense saving (`dense_rate` as low as `{min(gated_dense_rates):.4f}`),",
        "while finer arms dilute feedback and push the controller back toward dense",
        f"fallback. The frozen-test Hit deltas range from `{min(gated_hit_deltas):+.2f}`",
        f"pp to `{max(gated_hit_deltas):+.2f}` pp, so this setting remains a",
        "cost-aggressive boundary rather than the main quality-preserving claim.",
        "",
        "Paper-facing claim: `n_clusters=32` is a reproducible engineering default,",
        "not a theoretical optimum. The method is robust on the full multi-route",
        "surface, while retrieval-stage gating should be tuned separately if dense",
        "call reduction is the deployment target.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = [
        summarize_row(arm_count, route_mode, short_mode)
        for arm_count in ARM_COUNTS
        for route_mode, short_mode in ROUTE_MODES
    ]

    OUTPUT_PREFIX.parent.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_PREFIX.with_suffix(".csv"), rows)
    source_files = {
        str(route_summary_path(arm_count).relative_to(ROOT))
        for arm_count in ARM_COUNTS
    }
    source_files.update({
        str(route_rankings_path(arm_count).relative_to(ROOT))
        for arm_count in ARM_COUNTS
    })
    source_files.update({
        str(budget_prefix(arm_count, short_mode).with_suffix(suffix).relative_to(ROOT))
        for arm_count in ARM_COUNTS
        for _, short_mode in ROUTE_MODES
        for suffix in (".json", ".test_paired.csv")
    })
    payload = {
        "task": "task60_arm_count_sensitivity",
        "updated": "2026-06-25",
        "dataset": "lotte_technology_search_100k",
        "split": "task60_100k calibration/test",
        "fixed_seeds": [13, 17, 19],
        "arm_counts": ARM_COUNTS,
        "rows": rows,
        "source_files": sorted(source_files),
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
