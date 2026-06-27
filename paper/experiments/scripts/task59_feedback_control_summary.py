#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize Task59 feedback/static-control ablation artifacts."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"

TRUST_ROUTE_SUMMARY = RESULTS / "task59_feedback_control_100k_trust" / "linucb_cost_summary.csv"
NONE_ROUTE_SUMMARY = RESULTS / "task59_feedback_control_100k_none" / "linucb_cost_summary.csv"
TASK58_ROUTE_SUMMARY = RESULTS / "task58_geometry_random_100k_routes" / "linucb_cost_summary.csv"

OUTPUT_PREFIX = RESULTS / "task59_feedback_control_summary"


SETTINGS = [
    {
        "setting": "learned_full_multi_route",
        "control_role": "feedback-updated LinUCB route selection under the full rescue surface",
        "route_summary": TRUST_ROUTE_SUMMARY,
        "route_mode": "full_multi_route",
        "budget_prefix": RESULTS / "task59_learned_full_100k_context_budget",
    },
    {
        "setting": "learned_gated_cost_aware",
        "control_role": "feedback-updated LinUCB confidence with retrieval-stage dense saving",
        "route_summary": TRUST_ROUTE_SUMMARY,
        "route_mode": "gated_cost_aware",
        "budget_prefix": RESULTS / "task59_learned_gated_100k_context_budget",
    },
    {
        "setting": "static_nearest_gated",
        "control_role": "nearest-centroid confidence without LinUCB policy update",
        "route_summary": TRUST_ROUTE_SUMMARY,
        "route_mode": "static_nearest_gated",
        "budget_prefix": RESULTS / "task59_static_nearest_gated_100k_context_budget",
    },
    {
        "setting": "no_feedback_gated",
        "control_role": "no feedback update; dense/full fallback control",
        "route_summary": NONE_ROUTE_SUMMARY,
        "route_mode": "gated_cost_aware",
        "budget_prefix": RESULTS / "task59_no_feedback_gated_100k_context_budget",
    },
    {
        "setting": "static_nearest_ensemble",
        "control_role": "nearest-centroid arms under the full rescue surface",
        "route_summary": TASK58_ROUTE_SUMMARY,
        "route_mode": "static_nearest_ensemble",
        "budget_prefix": RESULTS / "task59_static_nearest_ensemble_100k_context_budget",
    },
    {
        "setting": "uniform_random_ensemble",
        "control_role": "random cluster arms under the full rescue surface",
        "route_summary": TASK58_ROUTE_SUMMARY,
        "route_mode": "uniform_random_ensemble",
        "budget_prefix": RESULTS / "task59_uniform_random_ensemble_100k_context_budget",
    },
]


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


def summarize_setting(config: Mapping[str, object]) -> dict[str, object]:
    route_summary = Path(str(config["route_summary"]))
    route_rows = [
        row for row in load_csv(route_summary)
        if row.get("routing_mode") == config["route_mode"]
    ]
    if len(route_rows) != 1:
        raise ValueError(f"Expected one route row for {config['route_mode']}, got {len(route_rows)}")
    route = route_rows[0]

    budget_prefix = Path(str(config["budget_prefix"]))
    budget_json = load_json(budget_prefix.with_suffix(".json"))
    selected = budget_json.get("selected_policy", {})
    if not isinstance(selected, Mapping):
        raise ValueError(f"selected_policy is not an object for {config['setting']}")

    paired_rows = [
        row for row in load_csv(budget_prefix.with_suffix(".test_paired.csv"))
        if row.get("method_label") == "task38"
    ]
    if not paired_rows:
        raise ValueError(f"No task38 paired rows for {config['setting']}")

    hit_deltas = [f(row, "hit_delta_mean") for row in paired_rows]
    token_savings = [f(row, "token_saving_percent") for row in paired_rows]
    method_hits = [f(row, "method_hit@10") for row in paired_rows]
    baseline_hits = [f(row, "baseline_hit@10") for row in paired_rows]
    ci_lows = [f(row, "hit_delta_ci_low") for row in paired_rows]
    ci_highs = [f(row, "hit_delta_ci_high") for row in paired_rows]

    return {
        "setting": str(config["setting"]),
        "control_role": str(config["control_role"]),
        "route_mode": str(config["route_mode"]),
        "feedback_mode": str(route.get("feedback_mode", "")),
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
        "total_feedback_updates_mean": f(route, "total_feedback_updates_mean"),
        "total_update_weight_mean": f(route, "total_update_weight_mean"),
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = [
        "setting",
        "control_role",
        "route_mode",
        "feedback_mode",
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
        "total_feedback_updates_mean",
        "total_update_weight_mean",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task59 Feedback-Control Ablation Summary",
        "",
        "Task59 isolates what feedback-updated LinUCB contributes beyond static",
        "geometry and no-feedback fallback controls on LoTTE technology/search 100k.",
        "All final-context token results use the same Task38-style calibration/test",
        "protocol under the `task59_100k` split with fixed seeds `13,17,19`.",
        "",
        "## Route-Control Result",
        "",
        "| Setting | Full Hit@10 | EvidenceRecall@10 | Route Reward | Cluster Hit | Confidence | Dense Rate | Primary Rate | Source Cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {setting} | {hit:.4f} | {er:.4f} | {reward:.4f} | {cluster:.4f} | {conf:.4f} | {dense:.4f} | {primary:.4f} | {cost:.2f} |".format(
                setting=row["setting"],
                hit=float(row["full_top10_hit@10_mean"]),
                er=float(row["full_top10_evidence_recall@10_mean"]),
                reward=float(row["last_route_true_reward_mean"]),
                cluster=float(row["selected_cluster_hit_rate_mean"]),
                conf=float(row["avg_confidence_mean"]),
                dense=float(row["dense_query_rate_mean"]),
                primary=float(row["linucb_primary_rate_mean"]),
                cost=float(row["avg_source_candidate_cost_mean"]),
            )
        )

    lines.extend([
        "",
        "## Frozen Budget Result",
        "",
        "| Setting | Policy | Eligible | Test Hit Delta | Token Saving | NI Seeds |",
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
        "The no-feedback gated control has high final Hit@10 only because it falls",
        "back to the full dense/BM25 surface: dense rate is `1.0000`, LinUCB primary",
        "rate is `0.0000`, and route reward remains low. This prevents the paper",
        "from attributing fallback quality to feedback learning.",
        "",
        "Static-nearest geometry has strong route-control quality, but the gated",
        "version still relies heavily on dense fallback. Learned gated routing saves",
        "more retrieval-stage dense calls, but its final Hit@10 drops under the",
        "current thresholds; it should be treated as a cost-aggressive boundary",
        "rather than the main quality-preserving operating point.",
        "",
        "The learned full multi-route row is the cleaner component-attribution row:",
        "feedback-updated route selection is used inside the full rescue surface, and",
        "external calibrated budget control produces token saving on this split, but",
        "Task59 alone does not establish paired non-inferiority.",
        "",
        "Paper-facing claim: LinUCB is a feedback-adaptive confidence/control",
        "mechanism, not the sole explanation for final fused Hit@10 gains.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = [summarize_setting(config) for config in SETTINGS]

    OUTPUT_PREFIX.parent.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_PREFIX.with_suffix(".csv"), rows)
    payload = {
        "task": "task59_feedback_control_ablation",
        "updated": "2026-06-25",
        "dataset": "lotte_technology_search_100k",
        "split": "task59_100k calibration/test",
        "fixed_seeds": [13, 17, 19],
        "rows": rows,
        "source_files": sorted({
            str(TRUST_ROUTE_SUMMARY.relative_to(ROOT)),
            str(NONE_ROUTE_SUMMARY.relative_to(ROOT)),
            str(TASK58_ROUTE_SUMMARY.relative_to(ROOT)),
            *[
                str(Path(str(config["budget_prefix"])).with_suffix(suffix).relative_to(ROOT))
                for config in SETTINGS
                for suffix in (".json", ".test_paired.csv")
            ],
        }),
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
