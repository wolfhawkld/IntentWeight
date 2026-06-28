#!/usr/bin/env python3
"""Compare Dense and IntentRoute on independently calibrated budget frontiers."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cost = load_module("task65_4_cost", SCRIPT_DIR / "context_token_cost.py")
budget = load_module("task65_4_budget", SCRIPT_DIR / "task37_context_budget_search.py")
calibration = load_module("task65_4_calibration", SCRIPT_DIR / "task38_calibrated_context_budget.py")
paired = load_module("task65_4_paired", SCRIPT_DIR / "task37_paired_significance.py")


RATIOS = tuple(round(1.0 - 0.01 * step, 2) for step in range(21))
MIN_KEEPS = (4, 5, 6, 7, 8)
QUALITY_MARGINS_PP = (0.0, 0.5, 1.0, 2.0)
SAVING_TARGETS_PCT = (5.0, 10.0, 15.0, 20.0)


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def source_variants(rankings: Mapping[str, object]):
    dynamic = [
        cost.RankingVariant(
            run_id=f"task65_3:dynamic_gated:seed{seed}",
            source_label="task65_3",
            method="dynamic_gated",
            seed=str(seed),
            rankings=seed_rankings,
        )
        for seed, seed_rankings in sorted(rankings["dynamic_gated"].items())
    ]
    dense_seed, dense_rankings = sorted(rankings["dense"].items())[0]
    dense = cost.RankingVariant(
        run_id=f"task65_3:dense:seed{dense_seed}",
        source_label="task65_3",
        method="dense",
        seed="",
        rankings=dense_rankings,
    )
    return dynamic, dense


def evaluate_grid(
    *,
    dynamic_sources: Sequence,
    dense_source,
    queries_by_split: Mapping[str, Sequence[Mapping]],
    chunk_tokens: Mapping[str, int],
):
    policy_sets = {
        "intentroute": budget.build_policy_variants(
            dynamic_sources,
            chunk_tokens,
            top_k=10,
            budget_ratios=RATIOS,
            min_keeps=MIN_KEEPS,
            fixed_keeps=(),
        ),
        "dense": budget.build_policy_variants(
            [dense_source],
            chunk_tokens,
            top_k=10,
            budget_ratios=RATIOS,
            min_keeps=MIN_KEEPS,
            fixed_keeps=(),
        ),
    }
    rows: list[dict[str, object]] = []
    policy_lookup: dict[str, dict[tuple[str, str], object]] = defaultdict(dict)
    for method, variants in policy_sets.items():
        for variant in variants:
            policy_lookup[method][(variant.policy, str(variant.seed))] = variant

    for split, split_queries in queries_by_split.items():
        baseline = cost.evaluate_variant(
            dense_source, split_queries, chunk_tokens, ks=(10,), skip_empty_gt=True
        )
        baseline_hit = float(baseline["hit@10"])
        baseline_tokens = float(baseline["avg_context_tokens@10"])
        for method, variants in policy_sets.items():
            for variant in variants:
                metrics = cost.evaluate_variant(
                    variant, split_queries, chunk_tokens, ks=(10,), skip_empty_gt=True
                )
                hit = float(metrics["hit@10"])
                tokens = float(metrics["avg_context_tokens@10"])
                rows.append({
                    "split": split,
                    "method": method,
                    "policy": variant.policy,
                    "seed": str(variant.seed),
                    "queries": int(metrics["num_queries"]),
                    "hit@10": hit,
                    "hit_delta_vs_dense_pp": (hit - baseline_hit) * 100.0,
                    "tokens": tokens,
                    "token_saving_vs_dense_pct": (1.0 - tokens / baseline_tokens) * 100.0,
                })
    return rows, policy_lookup


def aggregate(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["split"]), str(row["method"]), str(row["policy"]))].append(row)
    output = []
    for (split, method, policy), group in sorted(groups.items()):
        output.append({
            "split": split,
            "method": method,
            "policy": policy,
            "seed_rows": len(group),
            "hit@10": mean(float(row["hit@10"]) for row in group),
            "hit_delta_vs_dense_pp": mean(float(row["hit_delta_vs_dense_pp"]) for row in group),
            "tokens": mean(float(row["tokens"]) for row in group),
            "token_saving_vs_dense_pct": mean(
                float(row["token_saving_vs_dense_pct"]) for row in group
            ),
        })
    return output


def choose_quality(rows: Sequence[Mapping[str, object]], method: str, margin_pp: float):
    candidates = [
        row for row in rows
        if row["split"] == "calibration" and row["method"] == method
    ]
    eligible = [row for row in candidates if float(row["hit_delta_vs_dense_pp"]) >= -margin_pp]
    pool = eligible or candidates
    return max(
        pool,
        key=lambda row: (
            float(row["token_saving_vs_dense_pct"]) if eligible else float(row["hit_delta_vs_dense_pp"]),
            float(row["hit_delta_vs_dense_pp"]),
        ),
    ), bool(eligible)


def choose_saving(rows: Sequence[Mapping[str, object]], method: str, target: float):
    candidates = [
        row for row in rows
        if row["split"] == "calibration" and row["method"] == method
    ]
    return min(
        candidates,
        key=lambda row: (
            abs(float(row["token_saving_vs_dense_pct"]) - target),
            -float(row["hit_delta_vs_dense_pp"]),
        ),
    )


def row_for(rows, *, split: str, method: str, policy: str):
    return next(
        row for row in rows
        if row["split"] == split and row["method"] == method and row["policy"] == policy
    )


def quality_matches(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for margin in QUALITY_MARGINS_PP:
        selected = {}
        for method in ("intentroute", "dense"):
            selected[method] = choose_quality(rows, method, margin)
        ir_cal, ir_eligible = selected["intentroute"]
        dense_cal, dense_eligible = selected["dense"]
        ir_test = row_for(rows, split="test", method="intentroute", policy=str(ir_cal["policy"]))
        dense_test = row_for(rows, split="test", method="dense", policy=str(dense_cal["policy"]))
        output.append({
            "quality_margin_pp": margin,
            "intentroute_policy": ir_cal["policy"],
            "intentroute_calibration_eligible": ir_eligible,
            "intentroute_test_hit_delta_pp": ir_test["hit_delta_vs_dense_pp"],
            "intentroute_test_saving_pct": ir_test["token_saving_vs_dense_pct"],
            "dense_policy": dense_cal["policy"],
            "dense_calibration_eligible": dense_eligible,
            "dense_test_hit_delta_pp": dense_test["hit_delta_vs_dense_pp"],
            "dense_test_saving_pct": dense_test["token_saving_vs_dense_pct"],
            "intentroute_minus_dense_hit_pp": (
                float(ir_test["hit_delta_vs_dense_pp"]) - float(dense_test["hit_delta_vs_dense_pp"])
            ),
            "intentroute_minus_dense_saving_pp": (
                float(ir_test["token_saving_vs_dense_pct"])
                - float(dense_test["token_saving_vs_dense_pct"])
            ),
        })
    return output


def saving_matches(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for target in SAVING_TARGETS_PCT:
        selected = {
            method: choose_saving(rows, method, target)
            for method in ("intentroute", "dense")
        }
        ir_test = row_for(
            rows, split="test", method="intentroute", policy=str(selected["intentroute"]["policy"])
        )
        dense_test = row_for(
            rows, split="test", method="dense", policy=str(selected["dense"]["policy"])
        )
        output.append({
            "target_calibration_saving_pct": target,
            "intentroute_policy": selected["intentroute"]["policy"],
            "intentroute_calibration_saving_pct": selected["intentroute"]["token_saving_vs_dense_pct"],
            "intentroute_test_saving_pct": ir_test["token_saving_vs_dense_pct"],
            "intentroute_test_hit_delta_pp": ir_test["hit_delta_vs_dense_pp"],
            "dense_policy": selected["dense"]["policy"],
            "dense_calibration_saving_pct": selected["dense"]["token_saving_vs_dense_pct"],
            "dense_test_saving_pct": dense_test["token_saving_vs_dense_pct"],
            "dense_test_hit_delta_pp": dense_test["hit_delta_vs_dense_pp"],
            "intentroute_minus_dense_hit_pp": (
                float(ir_test["hit_delta_vs_dense_pp"]) - float(dense_test["hit_delta_vs_dense_pp"])
            ),
            "test_saving_gap_pp": abs(
                float(ir_test["token_saving_vs_dense_pct"])
                - float(dense_test["token_saving_vs_dense_pct"])
            ),
        })
    return output


def pareto_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    test_rows = [row for row in rows if row["split"] == "test"]
    output = []
    for method in ("intentroute", "dense"):
        candidates = [row for row in test_rows if row["method"] == method]
        for row in candidates:
            dominated = any(
                other is not row
                and float(other["hit_delta_vs_dense_pp"]) >= float(row["hit_delta_vs_dense_pp"])
                and float(other["token_saving_vs_dense_pct"]) >= float(row["token_saving_vs_dense_pct"])
                and (
                    float(other["hit_delta_vs_dense_pp"]) > float(row["hit_delta_vs_dense_pp"])
                    or float(other["token_saving_vs_dense_pct"]) > float(row["token_saving_vs_dense_pct"])
                )
                for other in candidates
            )
            if not dominated:
                output.append(dict(row))
    return sorted(output, key=lambda row: (str(row["method"]), float(row["token_saving_vs_dense_pct"])))


def interpolate_hit(frontier: Sequence[Mapping[str, object]], method: str, target: float) -> float:
    points_by_saving: dict[float, float] = {}
    for row in frontier:
        if row["method"] != method:
            continue
        saving = float(row["token_saving_vs_dense_pct"])
        hit = float(row["hit_delta_vs_dense_pp"])
        points_by_saving[saving] = max(hit, points_by_saving.get(saving, float("-inf")))
    points = sorted(points_by_saving.items())
    if not points or target < points[0][0] or target > points[-1][0]:
        return float("nan")
    for saving, hit in points:
        if abs(saving - target) < 1e-12:
            return hit
    for (left_saving, left_hit), (right_saving, right_hit) in zip(points, points[1:]):
        if left_saving <= target <= right_saving:
            weight = (target - left_saving) / (right_saving - left_saving)
            return left_hit + weight * (right_hit - left_hit)
    raise RuntimeError(f"Could not interpolate target {target}")


def interpolated_saving_matches(frontier: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for target in SAVING_TARGETS_PCT:
        ir_hit = interpolate_hit(frontier, "intentroute", target)
        dense_hit = interpolate_hit(frontier, "dense", target)
        output.append({
            "target_test_saving_pct": target,
            "intentroute_interpolated_hit_delta_pp": ir_hit,
            "dense_interpolated_hit_delta_pp": dense_hit,
            "intentroute_minus_dense_hit_pp": ir_hit - dense_hit,
            "analysis_role": "post_hoc_frontier_diagnostic",
        })
    return output


def paired_quality_rows(
    *,
    quality_rows: Sequence[Mapping[str, object]],
    policy_lookup,
    test_queries,
    chunk_tokens,
    bootstrap: int,
):
    output = []
    for index, selected in enumerate(quality_rows):
        dense_policy = str(selected["dense_policy"])
        dense_variant = policy_lookup["dense"][(dense_policy, "")]
        baseline = paired.Variant(
            label="dense_independent_budget",
            run_id=dense_variant.run_id,
            seed="",
            rankings=dense_variant.rankings,
        )
        ir_policy = str(selected["intentroute_policy"])
        for seed in ("13", "17", "19"):
            variant = policy_lookup["intentroute"][(ir_policy, seed)]
            row = paired.compare_variant(
                scale="100k",
                queries=test_queries,
                baseline=baseline,
                variant=paired.Variant(
                    label="intentroute_independent_budget",
                    run_id=variant.run_id,
                    seed=seed,
                    rankings=variant.rankings,
                ),
                chunk_tokens=chunk_tokens,
                k=10,
                noninferiority_margin=0.01,
                n_bootstrap=bootstrap,
                confidence=0.95,
                rng=np.random.default_rng(65400 + index * 100 + int(seed)),
            )
            row["quality_margin_pp"] = selected["quality_margin_pp"]
            row["intentroute_policy"] = ir_policy
            row["dense_policy"] = dense_policy
            output.append(row)
    return output


def markdown(path: Path, quality_rows, saving_rows, interpolated_rows, paired_rows) -> None:
    lines = [
        "# Task65.4 Independently Calibrated Matched Frontier",
        "",
        "Dense and IntentRoute independently select actions on the same calibration split and budget grid.",
        "",
        "## Quality-Constrained Selection",
        "",
        "| Margin | IntentRoute policy | IR test hit | IR saving | Dense policy | Dense test hit | Dense saving | IR-Dense hit |",
        "|---:|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in quality_rows:
        lines.append(
            f"| {float(row['quality_margin_pp']):.1f} pp | `{row['intentroute_policy']}` | "
            f"{float(row['intentroute_test_hit_delta_pp']):+.2f} pp | {float(row['intentroute_test_saving_pct']):.2f}% | "
            f"`{row['dense_policy']}` | {float(row['dense_test_hit_delta_pp']):+.2f} pp | "
            f"{float(row['dense_test_saving_pct']):.2f}% | {float(row['intentroute_minus_dense_hit_pp']):+.2f} pp |"
        )
    lines.extend([
        "",
        "## Calibration-Targeted Actions",
        "",
        "| Target | IR test saving | IR test hit | Dense test saving | Dense test hit | Saving gap | IR-Dense hit |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in saving_rows:
        lines.append(
            f"| {float(row['target_calibration_saving_pct']):.0f}% | "
            f"{float(row['intentroute_test_saving_pct']):.2f}% | {float(row['intentroute_test_hit_delta_pp']):+.2f} pp | "
            f"{float(row['dense_test_saving_pct']):.2f}% | {float(row['dense_test_hit_delta_pp']):+.2f} pp | "
            f"{float(row['test_saving_gap_pp']):.2f} pp | {float(row['intentroute_minus_dense_hit_pp']):+.2f} pp |"
        )
    lines.extend([
        "",
        "The test saving gaps above are distribution-shift diagnostics; they are not same-saving comparisons.",
        "",
        "## Same-Saving Held-Out Frontier (Post-Hoc Diagnostic)",
        "",
        "| Test saving | IntentRoute interpolated hit | Dense interpolated hit | IR-Dense hit |",
        "|---:|---:|---:|---:|",
    ])
    for row in interpolated_rows:
        lines.append(
            f"| {float(row['target_test_saving_pct']):.0f}% | "
            f"{float(row['intentroute_interpolated_hit_delta_pp']):+.2f} pp | "
            f"{float(row['dense_interpolated_hit_delta_pp']):+.2f} pp | "
            f"{float(row['intentroute_minus_dense_hit_pp']):+.2f} pp |"
        )
    grouped = defaultdict(list)
    for row in paired_rows:
        grouped[float(row["quality_margin_pp"])].append(row)
    lines.extend(["", "## Paired Check", ""])
    for margin, rows in sorted(grouped.items()):
        lines.append(
            f"- Margin {margin:.1f} pp: mean IntentRoute-minus-Dense Hit "
            f"{mean(float(row['hit_delta_mean']) for row in rows) * 100:+.2f} pp; "
            f"strict NI {sum(bool(row['noninferior_by_ci']) for row in rows)}/3 seeds."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rankings",
        type=Path,
        default=RESULTS / "task65_3_dynamic_route_mediation.rankings.json",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task65_4_matched_frontier",
    )
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))

    corpus = cost.load_json_list(DATA / "processed" / "lotte_technology_search_100k_corpus.json")
    queries = cost.load_json_list(DATA / "processed" / "lotte_technology_search_100k_queries.json")
    count_tokens = cost.build_token_counter("tiktoken", "cl100k_base")
    chunk_tokens = {cost.chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}
    calibration_queries, test_queries = calibration.split_queries(
        queries,
        calibration_fraction=0.30,
        salt="task38_lotte_calibration_v1:100k",
    )
    dynamic_sources, dense_source = source_variants(read_json(args.rankings))
    rows, policy_lookup = evaluate_grid(
        dynamic_sources=dynamic_sources,
        dense_source=dense_source,
        queries_by_split={"calibration": calibration_queries, "test": test_queries},
        chunk_tokens=chunk_tokens,
    )
    aggregated = aggregate(rows)
    quality = quality_matches(aggregated)
    saving = saving_matches(aggregated)
    pareto = pareto_rows(aggregated)
    interpolated = interpolated_saving_matches(pareto)
    paired_rows = paired_quality_rows(
        quality_rows=quality,
        policy_lookup=policy_lookup,
        test_queries=test_queries,
        chunk_tokens=chunk_tokens,
        bootstrap=args.bootstrap,
    )

    output = args.output_prefix
    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output.with_suffix(".grid.csv"), rows)
    write_csv(output.with_suffix(".aggregate.csv"), aggregated)
    write_csv(output.with_suffix(".quality_matched.csv"), quality)
    write_csv(output.with_suffix(".saving_matched.csv"), saving)
    write_csv(output.with_suffix(".pareto.csv"), pareto)
    write_csv(output.with_suffix(".interpolated.csv"), interpolated)
    write_csv(output.with_suffix(".paired.csv"), paired_rows)
    output.with_suffix(".json").write_text(
        json.dumps({
            "protocol": {
                "scale": "100k",
                "split_salt": "task38_lotte_calibration_v1:100k",
                "ratios": RATIOS,
                "min_keeps": MIN_KEEPS,
                "quality_margins_pp": QUALITY_MARGINS_PP,
                "saving_targets_pct": SAVING_TARGETS_PCT,
            },
            "quality_matched": quality,
            "saving_matched": saving,
            "pareto": pareto,
            "interpolated_same_saving": interpolated,
            "paired": paired_rows,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown(output.with_suffix(".md"), quality, saving, interpolated, paired_rows)
    print(json.dumps({
        "grid_rows": len(rows),
        "aggregate_rows": len(aggregated),
        "quality_rows": len(quality),
        "saving_rows": len(saving),
        "pareto_rows": len(pareto),
        "interpolated_rows": len(interpolated),
        "paired_rows": len(paired_rows),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
