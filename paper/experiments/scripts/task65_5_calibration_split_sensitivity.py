#!/usr/bin/env python3
"""Audit Task38 policy selection across deterministic calibration splits."""

from __future__ import annotations

import argparse
import csv
import gc
import importlib.util
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"
SCALES = ("100k", "200k", "400k", "638k")
RATIOS = (0.98, 0.95, 0.92, 0.90, 0.88, 0.85)
MIN_KEEPS = (4, 5, 6, 7, 8)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cost = load_module("task65_5_cost", SCRIPT_DIR / "context_token_cost.py")
budget = load_module("task65_5_budget", SCRIPT_DIR / "task37_context_budget_search.py")
calibration = load_module("task65_5_calibration", SCRIPT_DIR / "task38_calibrated_context_budget.py")


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def only_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise ValueError(f"Expected one {pattern!r} in {directory}, found {len(matches)}")
    return matches[0]


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def split_salts(count: int) -> tuple[str, ...]:
    if count < 2:
        raise ValueError("num_splits must be at least 2")
    return (
        "task38_lotte_calibration_v1",
        *(f"task65_5_calibration_sensitivity_v1_{index:02d}" for index in range(1, count)),
    )


def load_sources(scale: str):
    directory = RESULTS / f"task37_{scale}_gated_fixed_top10_formal"
    method_path = only_file(directory, "*_prequential_rankings.json")
    metrics = read_json(only_file(directory, "*_prequential_metrics.json"))[0]
    method_variants = [
        variant
        for variant in cost.load_ranking_variants("task37_source", method_path)
        if variant.method == "gated_cost_aware"
    ]
    if len(method_variants) != 3:
        raise ValueError(f"Expected three gated variants for {scale}, found {len(method_variants)}")
    dense_path = Path(str(metrics["dense_ranking_artifact_path"]))
    if dense_path.exists():
        dense_variants = cost.load_ranking_variants("dense", dense_path)
    else:
        fallback = RESULTS / f"task37_{scale}_dense_adaptive_baseline_rankings.json"
        dense_variants = [
            variant
            for variant in cost.load_ranking_variants("dense_saved", fallback)
            if variant.method == "dense:fixed_top10"
        ]
    if len(dense_variants) != 1:
        raise ValueError(f"Expected one dense variant for {scale}, found {len(dense_variants)}")
    return method_variants, dense_variants[0]


def needed_chunk_ids(method_variants: Sequence, dense_variant) -> set[str]:
    ids: set[str] = set()
    for variant in [*method_variants, dense_variant]:
        for ranking in variant.rankings.values():
            ids.update(str(item) for item in ranking[:10])
    return ids


def load_needed_tokens(scale: str, needed: set[str]) -> dict[str, int]:
    corpus_path = DATA / "processed" / f"lotte_technology_search_{scale}_corpus.json"
    corpus = cost.load_json_list(corpus_path)
    count_tokens = cost.build_token_counter("tiktoken", "cl100k_base")
    tokens = {
        chunk_key: count_tokens(str(chunk.get("text", "")))
        for chunk in corpus
        if (chunk_key := cost.chunk_id(chunk)) in needed
    }
    del corpus
    gc.collect()
    missing = needed - tokens.keys()
    if missing:
        raise ValueError(f"Missing {len(missing)} ranked chunks from {scale} corpus")
    return tokens


def evaluate(variant, queries, chunk_tokens):
    return cost.evaluate_variant(
        variant,
        queries,
        chunk_tokens,
        ks=(10,),
        skip_empty_gt=True,
    )


def audit_scale(scale: str, salts: Sequence[str]) -> list[dict[str, object]]:
    method_sources, dense_source = load_sources(scale)
    needed = needed_chunk_ids(method_sources, dense_source)
    chunk_tokens = load_needed_tokens(scale, needed)
    queries = cost.load_json_list(
        DATA / "processed" / f"lotte_technology_search_{scale}_queries.json"
    )
    method_policies = budget.build_policy_variants(
        method_sources,
        chunk_tokens,
        top_k=10,
        budget_ratios=RATIOS,
        min_keeps=MIN_KEEPS,
        fixed_keeps=(),
    )
    dense_policies = budget.build_policy_variants(
        [dense_source],
        chunk_tokens,
        top_k=10,
        budget_ratios=RATIOS,
        min_keeps=MIN_KEEPS,
        fixed_keeps=(),
    )
    rows = []
    for split_index, base_salt in enumerate(salts):
        calibration_queries, test_queries = calibration.split_queries(
            queries,
            calibration_fraction=0.30,
            salt=f"{base_salt}:{scale}",
        )
        calibration_dense = evaluate(dense_source, calibration_queries, chunk_tokens)
        calibration_rows = []
        for variant in method_policies:
            result = evaluate(variant, calibration_queries, chunk_tokens)
            result["policy"] = variant.policy
            calibration_rows.append(result)
        calibration.add_dense_deltas(
            calibration_rows,
            baseline_hit=float(calibration_dense["hit@10"]),
            baseline_tokens=float(calibration_dense["avg_context_tokens@10"]),
            k=10,
        )
        choice = calibration.choose_policy(calibration_rows, margin=1e-12, k=10)

        test_dense = evaluate(dense_source, test_queries, chunk_tokens)
        baseline_hit = float(test_dense["hit@10"])
        baseline_tokens = float(test_dense["avg_context_tokens@10"])
        selected_method = [variant for variant in method_policies if variant.policy == choice.policy]
        selected_dense = next(variant for variant in dense_policies if variant.policy == choice.policy)
        method_test = [evaluate(variant, test_queries, chunk_tokens) for variant in selected_method]
        dense_test = evaluate(selected_dense, test_queries, chunk_tokens)
        seed_hit_deltas = [
            (float(result["hit@10"]) - baseline_hit) * 100.0 for result in method_test
        ]
        seed_savings = [
            (1.0 - float(result["avg_context_tokens@10"]) / baseline_tokens) * 100.0
            for result in method_test
        ]
        dense_hit_delta = (float(dense_test["hit@10"]) - baseline_hit) * 100.0
        dense_saving = (1.0 - float(dense_test["avg_context_tokens@10"]) / baseline_tokens) * 100.0
        rows.append({
            "scale": scale,
            "split_index": split_index,
            "split_salt": base_salt,
            "is_original_split": split_index == 0,
            "calibration_queries": len(calibration_queries),
            "test_queries": len(test_queries),
            "selected_policy": choice.policy,
            "calibration_eligible": choice.eligible,
            "calibration_hit_delta_pp": choice.mean_hit_delta * 100.0,
            "calibration_saving_pct": choice.mean_token_saving_percent,
            "test_hit_delta_mean_pp": mean(seed_hit_deltas),
            "test_hit_delta_min_seed_pp": min(seed_hit_deltas),
            "test_hit_delta_max_seed_pp": max(seed_hit_deltas),
            "test_saving_mean_pct": mean(seed_savings),
            "test_saving_min_seed_pct": min(seed_savings),
            "test_saving_max_seed_pct": max(seed_savings),
            "test_point_noninferior_seeds_1pp": sum(value >= -1.0 for value in seed_hit_deltas),
            "dense_same_action_test_hit_delta_pp": dense_hit_delta,
            "dense_same_action_test_saving_pct": dense_saving,
        })
    del method_policies, dense_policies, method_sources, dense_source, chunk_tokens, queries
    gc.collect()
    return rows


def safe_stat(values: Sequence[float], fn, default=float("nan")):
    return fn(values) if values else default


def summaries(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for scale in SCALES:
        group = [row for row in rows if row["scale"] == scale]
        if not group:
            continue
        eligible = [row for row in group if bool(row["calibration_eligible"])]
        policies = Counter(str(row["selected_policy"]) for row in group)
        mode_policy, mode_count = policies.most_common(1)[0]
        test_hits = [float(row["test_hit_delta_mean_pp"]) for row in group]
        test_savings = [float(row["test_saving_mean_pct"]) for row in group]
        cal_hits = [float(row["calibration_hit_delta_pp"]) for row in group]
        correlation = float(np.corrcoef(cal_hits, test_hits)[0, 1]) if len(group) > 1 else float("nan")
        output.append({
            "scale": scale,
            "splits": len(group),
            "eligible_splits": len(eligible),
            "eligible_rate": len(eligible) / len(group),
            "unique_selected_policies": len(policies),
            "mode_policy": mode_policy,
            "mode_policy_rate": mode_count / len(group),
            "policy_counts": json.dumps(dict(sorted(policies.items())), sort_keys=True),
            "test_hit_delta_mean_pp": mean(test_hits),
            "test_hit_delta_median_pp": median(test_hits),
            "test_hit_delta_min_pp": min(test_hits),
            "test_hit_delta_max_pp": max(test_hits),
            "test_saving_mean_pct": mean(test_savings),
            "test_saving_median_pct": median(test_savings),
            "test_saving_min_pct": min(test_savings),
            "test_saving_max_pct": max(test_savings),
            "test_nonnegative_hit_rate": sum(value >= -1e-9 for value in test_hits) / len(group),
            "test_within_1pp_rate": sum(value >= -1.0 for value in test_hits) / len(group),
            "eligible_test_hit_mean_pp": safe_stat(
                [float(row["test_hit_delta_mean_pp"]) for row in eligible], mean
            ),
            "eligible_test_saving_mean_pct": safe_stat(
                [float(row["test_saving_mean_pct"]) for row in eligible], mean
            ),
            "calibration_test_hit_correlation": correlation,
        })
    return output


def write_markdown(path: Path, summary_rows, split_rows) -> None:
    split_count = max(int(row["splits"]) for row in summary_rows)
    lines = [
        "# Task65.5 Calibration-Split Sensitivity",
        "",
        f"{split_count} deterministic 30/70 calibration/test splits reuse frozen Task37 rankings.",
        "Splits overlap and are stability diagnostics, not independent experimental seeds.",
        "",
        "| Scale | Eligible | Policies | Mode rate | Test hit range | Mean test hit | Test saving range | Mean saving | Hit >= 0 | Hit >= -1pp |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['scale']} | {int(row['eligible_splits'])}/{int(row['splits'])} | "
            f"{int(row['unique_selected_policies'])} | {float(row['mode_policy_rate']):.0%} | "
            f"[{float(row['test_hit_delta_min_pp']):+.2f}, {float(row['test_hit_delta_max_pp']):+.2f}] pp | "
            f"{float(row['test_hit_delta_mean_pp']):+.2f} pp | "
            f"[{float(row['test_saving_min_pct']):.2f}, {float(row['test_saving_max_pct']):.2f}]% | "
            f"{float(row['test_saving_mean_pct']):.2f}% | "
            f"{float(row['test_nonnegative_hit_rate']):.0%} | {float(row['test_within_1pp_rate']):.0%} |"
        )
    lines.extend(["", "## Original Split", ""])
    for row in split_rows:
        if bool(row["is_original_split"]):
            lines.append(
                f"- {row['scale']}: `{row['selected_policy']}`, eligible={row['calibration_eligible']}, "
                f"test Hit delta {float(row['test_hit_delta_mean_pp']):+.2f} pp, "
                f"saving {float(row['test_saving_mean_pct']):.2f}%."
            )
    lines.extend([
        "",
        "## Guardrail",
        "",
        "This audit measures sensitivity to query partitioning. It does not turn overlapping splits into independent evidence or establish universal non-inferiority.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-splits", type=int, default=20)
    parser.add_argument("--scales", default=",".join(SCALES))
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task65_5_calibration_split_sensitivity",
    )
    args = parser.parse_args()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))
    selected_scales = tuple(part.strip() for part in args.scales.split(",") if part.strip())
    unknown = set(selected_scales) - set(SCALES)
    if unknown:
        raise ValueError(f"Unknown scales: {sorted(unknown)}")

    salts = split_salts(args.num_splits)
    rows: list[dict[str, object]] = []
    output = args.output_prefix
    output.parent.mkdir(parents=True, exist_ok=True)
    for scale in selected_scales:
        rows.extend(audit_scale(scale, salts))
        write_csv(output.with_suffix(".splits.csv"), rows)
        print(json.dumps({"scale": scale, "completed_splits": len(salts)}, sort_keys=True), flush=True)
    summary = summaries(rows)
    write_csv(output.with_suffix(".summary.csv"), summary)
    output.with_suffix(".json").write_text(
        json.dumps({
            "protocol": {
                "num_splits": args.num_splits,
                "calibration_fraction": 0.30,
                "selection_hit_margin": 0.0,
                "selection_numerical_tolerance": 1e-12,
                "ratios": RATIOS,
                "min_keeps": MIN_KEEPS,
                "split_salts": salts,
            },
            "summary": summary,
            "splits": rows,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(output.with_suffix(".md"), summary, rows)
    print(json.dumps({"split_rows": len(rows), "summary_rows": len(summary)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
