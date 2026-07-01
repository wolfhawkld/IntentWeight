#!/usr/bin/env python3
"""Run locked five-fold cross-fitted calibration across LoTTE corpus scales."""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib.util
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"
SCALES = ("100k", "200k", "400k", "638k")
FOLD_SALT = "task65_6_cross_scale_crossfit_v1"
NUM_FOLDS = 5
RATIOS = (0.98, 0.95, 0.92, 0.90, 0.88, 0.85)
MIN_KEEPS = (4, 5, 6, 7, 8)
SELECTION_MARGIN = 1e-12
NI_MARGIN = 0.01
BOOTSTRAP_SAMPLES = 10_000


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cost = load_module("task65_6_cost", SCRIPT_DIR / "context_token_cost.py")
budget = load_module("task65_6_budget", SCRIPT_DIR / "task37_context_budget_search.py")
calibration = load_module("task65_6_calibration", SCRIPT_DIR / "task38_calibrated_context_budget.py")
paired = load_module("task65_6_paired", SCRIPT_DIR / "task37_paired_significance.py")
source_loader = load_module(
    "task65_6_source_loader", SCRIPT_DIR / "task65_5_calibration_split_sensitivity.py"
)


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_query_id(query: Mapping) -> str:
    metadata = query.get("metadata")
    if isinstance(metadata, Mapping) and metadata.get("original_query_id") is not None:
        return str(metadata["original_query_id"])
    return cost.query_id(query)


def query_folds(
    queries: Sequence[Mapping],
) -> tuple[dict[str, int], dict[str, int], list[list[Mapping]]]:
    scored = []
    for query in queries:
        qid = cost.query_id(query)
        canonical_id = canonical_query_id(query)
        digest = hashlib.sha256(f"{FOLD_SALT}:{canonical_id}".encode("utf-8")).hexdigest()
        scored.append((digest, canonical_id, qid, query))
    scored.sort(key=lambda item: (item[0], item[1]))
    folds: list[list[Mapping]] = [[] for _ in range(NUM_FOLDS)]
    assignments: dict[str, int] = {}
    canonical_assignments: dict[str, int] = {}
    for index, (_, canonical_id, qid, query) in enumerate(scored):
        fold = index % NUM_FOLDS
        assignments[qid] = fold
        if canonical_id in canonical_assignments:
            raise ValueError(f"Duplicate canonical query ID: {canonical_id}")
        canonical_assignments[canonical_id] = fold
        folds[fold].append(query)
    return assignments, canonical_assignments, folds


def evaluate(variant, queries, chunk_tokens):
    return cost.evaluate_variant(variant, queries, chunk_tokens, ks=(10,), skip_empty_gt=True)


def policy_lookup(variants: Sequence) -> dict[tuple[str, str], object]:
    lookup = {}
    for variant in variants:
        key = (str(variant.policy), str(variant.seed))
        if key in lookup:
            raise ValueError(f"Duplicate policy/seed variant: {key}")
        lookup[key] = variant
    return lookup


def calibration_choice(variants, dense_source, queries, chunk_tokens):
    dense_metrics = evaluate(dense_source, queries, chunk_tokens)
    rows = []
    for variant in variants:
        row = evaluate(variant, queries, chunk_tokens)
        row["policy"] = variant.policy
        rows.append(row)
    calibration.add_dense_deltas(
        rows,
        baseline_hit=float(dense_metrics["hit@10"]),
        baseline_tokens=float(dense_metrics["avg_context_tokens@10"]),
        k=10,
    )
    return calibration.choose_policy(rows, margin=SELECTION_MARGIN, k=10)


def composite_variant(label: str, seed: str, rankings: Mapping[str, Sequence[str]]):
    return paired.Variant(
        label=label,
        run_id=f"task65_6:{label}:seed{seed}" if seed else f"task65_6:{label}",
        seed=seed,
        rankings={str(qid): [str(item) for item in ranking] for qid, ranking in rankings.items()},
    )


def fold_metrics(variant, dense_source, test_queries, chunk_tokens):
    dense = evaluate(dense_source, test_queries, chunk_tokens)
    result = evaluate(variant, test_queries, chunk_tokens)
    dense_hit = float(dense["hit@10"])
    dense_tokens = float(dense["avg_context_tokens@10"])
    return {
        "hit@10": float(result["hit@10"]),
        "hit_delta_pp": (float(result["hit@10"]) - dense_hit) * 100.0,
        "saving_pct": (
            (1.0 - float(result["avg_context_tokens@10"]) / dense_tokens) * 100.0
            if dense_tokens > 0
            else 0.0
        ),
    }


def audit_scale(scale: str):
    method_sources, dense_source = source_loader.load_sources(scale)
    needed = source_loader.needed_chunk_ids(method_sources, dense_source)
    chunk_tokens = source_loader.load_needed_tokens(scale, needed)
    query_path = DATA / "processed" / f"lotte_technology_search_{scale}_queries.json"
    queries = cost.load_json_list(query_path)
    assignments, canonical_assignments, folds = query_folds(queries)
    if max(len(fold) for fold in folds) - min(len(fold) for fold in folds) > 1:
        raise AssertionError(f"Cross-fit folds are not balanced for {scale}")

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
    method_by_policy_seed = policy_lookup(method_policies)
    dense_by_policy_seed = policy_lookup(dense_policies)
    seeds = sorted(str(source.seed) for source in method_sources)
    method_oof = {seed: {} for seed in seeds}
    dense_oof: dict[str, list[str]] = {}
    fold_rows: list[dict[str, object]] = []
    selections: list[dict[str, object]] = []

    for fold_index, test_queries in enumerate(folds):
        calibration_queries = [
            query for index, fold in enumerate(folds) if index != fold_index for query in fold
        ]
        method_choice = calibration_choice(
            method_policies, dense_source, calibration_queries, chunk_tokens
        )
        dense_choice = calibration_choice(
            dense_policies, dense_source, calibration_queries, chunk_tokens
        )
        method_fallback = not method_choice.eligible
        dense_fallback = not dense_choice.eligible

        for query in test_queries:
            qid = cost.query_id(query)
            for seed in seeds:
                source = dense_source if method_fallback else method_by_policy_seed[
                    (method_choice.policy, seed)
                ]
                method_oof[seed][qid] = list(source.rankings.get(qid, []))[:10]
            dense_policy = (
                dense_source
                if dense_fallback
                else dense_by_policy_seed[(dense_choice.policy, "")]
            )
            dense_oof[qid] = list(dense_policy.rankings.get(qid, []))[:10]

        seed_fold_metrics = []
        for seed in seeds:
            source = dense_source if method_fallback else method_by_policy_seed[
                (method_choice.policy, seed)
            ]
            metrics = fold_metrics(source, dense_source, test_queries, chunk_tokens)
            seed_fold_metrics.append(metrics)
            fold_rows.append({
                "scale": scale,
                "fold": fold_index,
                "method": "intentroute",
                "seed": seed,
                "calibration_queries": len(calibration_queries),
                "test_queries": len(test_queries),
                "selected_policy": (
                    "dense_top10_fallback" if method_fallback else method_choice.policy
                ),
                "calibration_eligible": method_choice.eligible,
                "calibration_hit_delta_pp": method_choice.mean_hit_delta * 100.0,
                "calibration_saving_pct": method_choice.mean_token_saving_percent,
                **metrics,
            })
        dense_test_variant = (
            dense_source
            if dense_fallback
            else dense_by_policy_seed[(dense_choice.policy, "")]
        )
        dense_metrics = fold_metrics(dense_test_variant, dense_source, test_queries, chunk_tokens)
        fold_rows.append({
            "scale": scale,
            "fold": fold_index,
            "method": "dense",
            "seed": "",
            "calibration_queries": len(calibration_queries),
            "test_queries": len(test_queries),
            "selected_policy": (
                "dense_top10_fallback" if dense_fallback else dense_choice.policy
            ),
            "calibration_eligible": dense_choice.eligible,
            "calibration_hit_delta_pp": dense_choice.mean_hit_delta * 100.0,
            "calibration_saving_pct": dense_choice.mean_token_saving_percent,
            **dense_metrics,
        })
        selection = {
            "scale": scale,
            "fold": fold_index,
            "intentroute_policy": (
                "dense_top10_fallback" if method_fallback else method_choice.policy
            ),
            "intentroute_eligible": method_choice.eligible,
            "intentroute_test_hit_delta_mean_pp": mean(
                item["hit_delta_pp"] for item in seed_fold_metrics
            ),
            "intentroute_test_saving_mean_pct": mean(
                item["saving_pct"] for item in seed_fold_metrics
            ),
            "dense_policy": (
                "dense_top10_fallback" if dense_fallback else dense_choice.policy
            ),
            "dense_eligible": dense_choice.eligible,
            "dense_test_hit_delta_pp": dense_metrics["hit_delta_pp"],
            "dense_test_saving_pct": dense_metrics["saving_pct"],
        }
        selections.append(selection)
        print(json.dumps(selection, sort_keys=True), flush=True)

    expected_qids = {cost.query_id(query) for query in queries}
    if set(dense_oof) != expected_qids:
        raise AssertionError(f"Dense OOF rankings do not cover every {scale} query")
    if any(set(rankings) != expected_qids for rankings in method_oof.values()):
        raise AssertionError(f"IntentRoute OOF rankings do not cover every {scale} query")

    baseline = composite_variant("dense_top10", "", dense_source.rankings)
    comparisons = []
    scale_index = SCALES.index(scale)
    for seed_index, seed in enumerate(seeds):
        comparisons.append(paired.compare_variant(
            scale=scale,
            queries=queries,
            baseline=baseline,
            variant=composite_variant("intentroute_crossfit", seed, method_oof[seed]),
            chunk_tokens=chunk_tokens,
            k=10,
            noninferiority_margin=NI_MARGIN,
            n_bootstrap=BOOTSTRAP_SAMPLES,
            confidence=0.95,
            rng=np.random.default_rng(650600 + scale_index * 10 + seed_index),
        ))
    comparisons.append(paired.compare_variant(
        scale=scale,
        queries=queries,
        baseline=baseline,
        variant=composite_variant("dense_crossfit", "", dense_oof),
        chunk_tokens=chunk_tokens,
        k=10,
        noninferiority_margin=NI_MARGIN,
        n_bootstrap=BOOTSTRAP_SAMPLES,
        confidence=0.95,
        rng=np.random.default_rng(650699 + scale_index),
    ))

    intent_rows = [row for row in comparisons if row["method_label"] == "intentroute_crossfit"]
    summary = {
        "scale": scale,
        "queries": len(expected_qids),
        "folds": NUM_FOLDS,
        "fold_sizes": [len(fold) for fold in folds],
        "intentroute_eligible_folds": sum(bool(row["intentroute_eligible"]) for row in selections),
        "intentroute_fallback_folds": sum(not bool(row["intentroute_eligible"]) for row in selections),
        "intentroute_unique_policies": len({row["intentroute_policy"] for row in selections}),
        "intentroute_policy_counts": dict(Counter(row["intentroute_policy"] for row in selections)),
        "intentroute_hit_delta_mean_pp": mean(float(row["hit_delta_mean"]) for row in intent_rows) * 100.0,
        "intentroute_saving_mean_pct": mean(float(row["token_saving_percent"]) for row in intent_rows),
        "intentroute_noninferior_seeds_1pp": sum(bool(row["noninferior_by_ci"]) for row in intent_rows),
        "dense_policy_counts": dict(Counter(row["dense_policy"] for row in selections)),
        "dense_hit_delta_pp": float(comparisons[-1]["hit_delta_mean"]) * 100.0,
        "dense_saving_pct": float(comparisons[-1]["token_saving_percent"]),
        "dense_noninferior_1pp": bool(comparisons[-1]["noninferior_by_ci"]),
    }

    source_directory = RESULTS / f"task37_{scale}_gated_fixed_top10_formal"
    source_ranking_path = source_loader.only_file(source_directory, "*_prequential_rankings.json")
    source_metrics_path = source_loader.only_file(source_directory, "*_prequential_metrics.json")
    dense_path = Path(str(source_loader.read_json(source_metrics_path)[0]["dense_ranking_artifact_path"]))
    if not dense_path.exists():
        dense_path = RESULTS / f"task37_{scale}_dense_adaptive_baseline_rankings.json"
    input_artifacts = {
        "intentroute_rankings": {
            "path": str(source_ranking_path.relative_to(ROOT)),
            "sha256": sha256_file(source_ranking_path),
        },
        "dense_rankings": {
            "path": str(dense_path.relative_to(ROOT)),
            "sha256": sha256_file(dense_path),
        },
        "queries": {
            "path": str(query_path.relative_to(ROOT)),
            "sha256": sha256_file(query_path),
        },
    }
    rankings = {
        "intentroute_crossfit": method_oof,
        "dense_crossfit": dense_oof,
        "fold_assignments": assignments,
        "canonical_fold_assignments": canonical_assignments,
    }
    del method_policies, dense_policies, method_sources, dense_source, chunk_tokens, queries
    gc.collect()
    return fold_rows, selections, comparisons, summary, rankings, input_artifacts


def write_markdown(path: Path, summaries, selections) -> None:
    lines = [
        "# Task65.6 Cross-Scale Cross-Fitted Calibration",
        "",
        "Five balanced, disjoint folds use the same locked grid and selection rule at every scale.",
        "",
        "## Out-of-Fold Results",
        "",
        "| Scale | Eligible folds | IntentRoute Hit delta | IntentRoute saving | NI seeds | Dense Hit delta | Dense saving |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['scale']} | {row['intentroute_eligible_folds']}/{NUM_FOLDS} | "
            f"{float(row['intentroute_hit_delta_mean_pp']):+.2f}pp | "
            f"{float(row['intentroute_saving_mean_pct']):.2f}% | "
            f"{row['intentroute_noninferior_seeds_1pp']}/3 | "
            f"{float(row['dense_hit_delta_pp']):+.2f}pp | "
            f"{float(row['dense_saving_pct']):.2f}% |"
        )
    lines.extend([
        "",
        "## Fold Selections",
        "",
        "| Scale | Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy | Dense saving |",
        "|---|---:|---|---:|---:|---:|---|---:|",
    ])
    for row in selections:
        lines.append(
            f"| {row['scale']} | {row['fold']} | `{row['intentroute_policy']}` | "
            f"{row['intentroute_eligible']} | "
            f"{float(row['intentroute_test_hit_delta_mean_pp']):+.2f}pp | "
            f"{float(row['intentroute_test_saving_mean_pct']):.2f}% | "
            f"`{row['dense_policy']}` | {float(row['dense_test_saving_pct']):.2f}% |"
        )
    lines.extend([
        "",
        "## Guardrail",
        "",
        "This post-hoc cross-fitted audit uses a normalized protocol across all scales. It does not erase the original 400k calibration failure or establish universal non-inferiority.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", default=",".join(SCALES))
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task65_6_cross_scale_cross_fitted_calibration",
    )
    args = parser.parse_args()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))
    selected_scales = tuple(part.strip() for part in args.scales.split(",") if part.strip())
    unknown = set(selected_scales) - set(SCALES)
    if unknown:
        raise ValueError(f"Unknown scales: {sorted(unknown)}")
    output = args.output_prefix
    output.parent.mkdir(parents=True, exist_ok=True)

    all_fold_rows = []
    all_selections = []
    all_comparisons = []
    summaries = []
    rankings = {}
    input_artifacts = {}
    for scale in selected_scales:
        fold_rows, selections, comparisons, summary, scale_rankings, artifacts = audit_scale(scale)
        all_fold_rows.extend(fold_rows)
        all_selections.extend(selections)
        all_comparisons.extend(comparisons)
        summaries.append(summary)
        rankings[scale] = scale_rankings
        input_artifacts[scale] = artifacts
        write_csv(output.with_suffix(".folds.csv"), all_fold_rows)
        write_csv(output.with_suffix(".paired.csv"), all_comparisons)
        print(json.dumps(summary, sort_keys=True), flush=True)

    output.with_suffix(".rankings.json").write_text(
        json.dumps(rankings, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    output.with_suffix(".json").write_text(
        json.dumps({
            "protocol": {
                "fold_salt": FOLD_SALT,
                "num_folds": NUM_FOLDS,
                "ratios": RATIOS,
                "min_keeps": MIN_KEEPS,
                "selection_margin": SELECTION_MARGIN,
                "noninferiority_margin": NI_MARGIN,
                "bootstrap_samples": BOOTSTRAP_SAMPLES,
                "fallback": "dense_top10_when_no_policy_is_eligible",
            },
            "input_artifacts": input_artifacts,
            "summary": summaries,
            "fold_selections": all_selections,
            "paired": all_comparisons,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(output.with_suffix(".md"), summaries, all_selections)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
