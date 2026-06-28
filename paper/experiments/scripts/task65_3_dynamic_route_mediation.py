#!/usr/bin/env python3
"""Replay Task37 route shapes on one frozen LinUCB trajectory.

The Task37 trajectory uses cluster-only reward, so its selected arms and policy
confidence do not depend on the final dense/BM25/cluster fusion weights. This
script reconstructs component rankings from cached artifacts and replays
dynamic, fixed, and shuffled-tier fusion without retraining the policy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS = ROOT / "paper" / "experiments" / "results"
DATA = ROOT / "paper" / "experiments" / "data"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module(
    "task65_3_base",
    SCRIPT_DIR / "task65_1_safe_compression_attribution.py",
)
router = load_module("task65_3_router", SCRIPT_DIR / "linucb_cost_aware_routing.py")

VARIANTS = (
    "dynamic_gated",
    "fixed_full",
    "fixed_cluster_primary",
    "shuffled_tiers",
    "dense",
)
RATIOS = (0.75, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95, 0.98)
MIN_KEEPS = (4, 5, 6, 7, 8)
DIAGNOSTIC_RATIOS = (0.85, 0.95)
COMMON_RATIO = 0.95
COMMON_MIN_KEEP = 4


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def only_file(directory: Path, pattern: str) -> Path:
    paths = sorted(directory.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f"Expected one {pattern} in {directory}, got {len(paths)}")
    return paths[0]


def stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)


def fuse(
    dense: Sequence[str],
    bm25: Sequence[str],
    cluster: Sequence[str],
    *,
    tier: str,
) -> list[str]:
    if tier == "linucb_primary":
        dense_part, bm25_part = [], list(bm25[:20])
        weights = (0.0, 0.5, 2.0)
        floor = 0
    elif tier == "hybrid_lite":
        dense_part, bm25_part = list(dense[:100]), list(bm25[:20])
        weights = (0.8, 0.5, 2.0)
        floor = 5
    elif tier in {"full_dense_fallback", "fixed_full"}:
        dense_part, bm25_part = list(dense[:100]), list(bm25[:100])
        weights = (2.0, 0.8, 0.8)
        floor = 5
    elif tier == "fixed_cluster_primary":
        dense_part, bm25_part = [], list(bm25[:20])
        weights = (0.0, 0.5, 2.0)
        floor = 0
    else:
        raise ValueError(f"Unsupported tier: {tier}")
    ranking = router.linucb_soft.weighted_reciprocal_rank_fusion(
        (
            (dense_part, weights[0]),
            (bm25_part, weights[1]),
            (cluster[:100], weights[2]),
        ),
        rrf_k=60,
        top_k=10,
    )
    return router.linucb_soft.apply_dense_floor(
        ranking,
        dense_part,
        dense_floor_k=floor,
        top_k=10,
    )


def shuffled_tiers(
    traces: Mapping[str, Mapping[str, object]],
    split_ids: Mapping[str, Sequence[str]],
    *,
    seed: str,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for split, query_ids in split_ids.items():
        ordered_ids = sorted(query_ids)
        tiers = np.asarray([str(traces[query_id]["route"]) for query_id in ordered_ids], dtype=object)
        rng = np.random.default_rng(stable_seed("task65.3", seed, split))
        rng.shuffle(tiers)
        result.update({query_id: str(tier) for query_id, tier in zip(ordered_ids, tiers)})
    return result


def reconstruct_variants(
    *,
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    metrics: Mapping[str, object],
    traces_by_seed: Mapping[str, Mapping[str, Mapping[str, object]]],
    saved_dynamic: Mapping[str, Mapping[str, Sequence[str]]],
    split_ids: Mapping[str, Sequence[str]],
) -> tuple[
    dict[str, dict[str, dict[str, list[str]]]],
    dict[str, dict[str, dict[str, list[str]]]],
    list[dict[str, object]],
]:
    dense_rankings = read_json(Path(str(metrics["dense_ranking_artifact_path"])))
    bm25_rankings = read_json(Path(str(metrics["bm25_ranking_artifact_path"])))
    corpus_embeddings = np.load(str(metrics["corpus_embedding_cache_path"]), mmap_mode="r")
    query_embeddings = np.load(str(metrics["query_embedding_cache_path"]), mmap_mode="r")
    chunk_ids = [router._chunk_id(chunk) for chunk in corpus]
    query_index = {router._query_id(query): index for index, query in enumerate(queries)}
    context_paths = {
        str(seed): Path(path)
        for seed, path in zip(metrics["seeds"], metrics["context_cluster_artifact_paths"])
    }

    variants = {variant: {} for variant in VARIANTS}
    components: dict[str, dict[str, dict[str, list[str]]]] = {}
    validation: list[dict[str, object]] = []
    for seed in sorted(traces_by_seed):
        context = np.load(context_paths[seed])
        arm_labels = np.asarray(context["arm_labels"], dtype=np.int32)
        traces = traces_by_seed[seed]
        assigned_shuffled = shuffled_tiers(traces, split_ids, seed=seed)
        components[seed] = {}
        for variant in VARIANTS:
            variants[variant][seed] = {}
        mismatches = 0
        for query_id, trace in traces.items():
            dense = [str(item) for item in dense_rankings[query_id][:100]]
            bm25 = [str(item) for item in bm25_rankings[query_id][:100]]
            cluster = router.global_linucb.retrieve_from_arms(
                np.asarray(query_embeddings[query_index[query_id]], dtype=np.float32),
                corpus_embeddings,
                chunk_ids,
                arm_labels,
                [int(arm) for arm in trace["selected_arms"]],
                top_k=100,
            )
            components[seed][query_id] = {
                "dense": dense,
                "bm25": bm25,
                "cluster": cluster,
            }
            dynamic = fuse(dense, bm25, cluster, tier=str(trace["route"]))
            variants["dynamic_gated"][seed][query_id] = dynamic
            variants["fixed_full"][seed][query_id] = fuse(dense, bm25, cluster, tier="fixed_full")
            variants["fixed_cluster_primary"][seed][query_id] = fuse(
                dense, bm25, cluster, tier="fixed_cluster_primary"
            )
            variants["shuffled_tiers"][seed][query_id] = fuse(
                dense, bm25, cluster, tier=assigned_shuffled[query_id]
            )
            variants["dense"][seed][query_id] = dense[:10]
            if dynamic != [str(item) for item in saved_dynamic[seed][query_id][:10]]:
                mismatches += 1
        validation.append({
            "seed": seed,
            "queries": len(traces),
            "dynamic_replay_mismatches": mismatches,
            "dynamic_replay_exact": mismatches == 0,
            "high_tier_rate": mean(float(trace["route"] == "linucb_primary") for trace in traces.values()),
            "mid_tier_rate": mean(float(trace["route"] == "hybrid_lite") for trace in traces.values()),
            "fallback_rate": mean(float(trace["route"] == "full_dense_fallback") for trace in traces.values()),
        })
    if any(not row["dynamic_replay_exact"] for row in validation):
        raise AssertionError(f"Dynamic replay mismatch: {validation}")
    return variants, components, validation


def ground_truth(query: Mapping) -> set[str]:
    return base.ground_truth(query)


def ranking_hit(ranking: Sequence[str], truth: set[str]) -> int:
    return base.hit(ranking, truth, k=10)


def budgeted_rankings(
    rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    ratio: float,
    min_keep: int,
) -> dict[str, list[str]]:
    return {
        query_id: base.budget.token_budget_ranking(
            ranking,
            chunk_tokens,
            top_k=10,
            budget_ratio=ratio,
            min_keep=min_keep,
        )
        for query_id, ranking in rankings.items()
    }


def evaluate(
    queries: Sequence[Mapping],
    rankings: Mapping[str, Sequence[str]],
    dense_rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
) -> dict[str, float]:
    hits: list[int] = []
    dense_hits: list[int] = []
    tokens: list[float] = []
    dense_tokens: list[float] = []
    relevant_counts: list[float] = []
    first_ranks: list[float] = []
    for query in queries:
        truth = ground_truth(query)
        if not truth:
            continue
        query_id = base.qid(query)
        ranking = [str(item) for item in rankings[query_id][:10]]
        dense = [str(item) for item in dense_rankings[query_id][:10]]
        positions = [index + 1 for index, item in enumerate(ranking) if item in truth]
        hits.append(int(bool(positions)))
        dense_hits.append(ranking_hit(dense, truth))
        tokens.append(float(sum(chunk_tokens.get(item, 0) for item in ranking)))
        dense_tokens.append(float(sum(chunk_tokens.get(item, 0) for item in dense)))
        relevant_counts.append(float(len(positions)))
        if positions:
            first_ranks.append(float(positions[0]))
    hit_mean = float(np.mean(hits))
    dense_hit_mean = float(np.mean(dense_hits))
    token_mean = float(np.mean(tokens))
    dense_token_mean = float(np.mean(dense_tokens))
    return {
        "num_queries": len(hits),
        "hit@10": hit_mean,
        "hit_delta_vs_dense_pp": (hit_mean - dense_hit_mean) * 100.0,
        "tokens": token_mean,
        "token_saving_vs_dense_pct": (1.0 - token_mean / dense_token_mean) * 100.0,
        "relevant_chunks_top10": float(np.mean(relevant_counts)),
        "first_relevant_rank_on_hits": float(np.mean(first_ranks)) if first_ranks else math.nan,
    }


def evidence_survival_rows(
    *,
    variants: Mapping[str, Mapping[str, Mapping[str, Sequence[str]]]],
    components: Mapping[str, Mapping[str, Mapping[str, Sequence[str]]]],
    traces_by_seed: Mapping[str, Mapping[str, Mapping[str, object]]],
    test_queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for variant in VARIANTS:
        for seed, rankings in variants[variant].items():
            for query in test_queries:
                truth = ground_truth(query)
                if not truth:
                    continue
                query_id = base.qid(query)
                ranking = [str(item) for item in rankings[query_id][:10]]
                positions = [index + 1 for index, item in enumerate(ranking) if item in truth]
                total_tokens = sum(chunk_tokens.get(item, 0) for item in ranking)
                first_rank = positions[0] if positions else 0
                first_prefix_tokens = (
                    sum(chunk_tokens.get(item, 0) for item in ranking[:first_rank])
                    if first_rank else 0
                )
                safe_grid: list[tuple[float, float]] = []
                for ratio_step in range(1, 101):
                    ratio = ratio_step / 100.0
                    compressed = base.budget.token_budget_ranking(
                        ranking,
                        chunk_tokens,
                        top_k=10,
                        budget_ratio=ratio,
                        min_keep=4,
                    )
                    if ranking_hit(compressed, truth):
                        compressed_tokens = sum(chunk_tokens.get(item, 0) for item in compressed)
                        actual_saving = 1.0 - compressed_tokens / total_tokens if total_tokens else 0.0
                        safe_grid.append((ratio, actual_saving))
                component = components[seed][query_id]
                route_support = sum(
                    int(bool(set(component[name]) & truth))
                    for name in ("dense", "bm25", "cluster")
                )
                row = {
                    "variant": variant,
                    "seed": seed,
                    "query_id": query_id,
                    "source_hit": int(bool(positions)),
                    "relevant_chunks_top10": len(positions),
                    "multiple_relevant": int(len(positions) >= 2),
                    "first_relevant_rank": first_rank,
                    "total_tokens_top10": total_tokens,
                    "first_relevant_prefix_tokens": first_prefix_tokens,
                    "first_relevant_prefix_ratio": (
                        first_prefix_tokens / total_tokens if total_tokens and first_rank else math.nan
                    ),
                    "minimum_safe_ratio_grid": min(ratio for ratio, _ in safe_grid) if safe_grid else math.nan,
                    "maximum_safe_token_saving": max(saving for _, saving in safe_grid) if safe_grid else math.nan,
                    "route_support_count_at100": route_support,
                    "dense_support_at100": int(bool(set(component["dense"]) & truth)),
                    "bm25_support_at100": int(bool(set(component["bm25"]) & truth)),
                    "cluster_support_at100": int(bool(set(component["cluster"]) & truth)),
                    "route_confidence": float(traces_by_seed[seed][query_id]["confidence"]),
                    "route_tier": str(traces_by_seed[seed][query_id]["route"]),
                }
                for ratio in DIAGNOSTIC_RATIOS:
                    compressed = base.budget.token_budget_ranking(
                        ranking,
                        chunk_tokens,
                        top_k=10,
                        budget_ratio=ratio,
                        min_keep=4,
                    )
                    row[f"safe_r{ratio:.2f}_m4"] = ranking_hit(compressed, truth) if positions else 0
                rows.append(row)
    return rows


def bootstrap_spearman(
    x: np.ndarray,
    y: np.ndarray,
    *,
    rng: np.random.Generator,
    n_bootstrap: int,
) -> tuple[float, float, float]:
    observed = float(spearmanr(x, y).statistic) if len(x) > 1 else math.nan
    samples: list[float] = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(x), size=len(x))
        value = float(spearmanr(x[indices], y[indices]).statistic)
        if math.isfinite(value):
            samples.append(value)
    if not samples:
        return observed, observed, observed
    return observed, float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def feature_metric_rows(
    survival: Sequence[Mapping[str, object]],
    *,
    n_bootstrap: int,
) -> list[dict[str, object]]:
    feature_scores = {
        "route_confidence": lambda row: float(row["route_confidence"]),
        "relevant_count": lambda row: float(row["relevant_chunks_top10"]),
        "first_relevant_rank": lambda row: -float(row["first_relevant_rank"]),
        "first_relevant_token_position": lambda row: -float(row["first_relevant_prefix_ratio"]),
        "route_support_count": lambda row: float(row["route_support_count_at100"]),
    }
    rows: list[dict[str, object]] = []
    for variant in VARIANTS:
        for seed in ("13", "17", "19"):
            group = [
                row for row in survival
                if row["variant"] == variant and row["seed"] == seed and int(row["source_hit"])
            ]
            headroom = np.asarray([float(row["maximum_safe_token_saving"]) for row in group])
            confidence = np.asarray([float(row["route_confidence"]) for row in group])
            rho, rho_lo, rho_hi = bootstrap_spearman(
                confidence,
                headroom,
                rng=np.random.default_rng(stable_seed("rho", variant, seed)),
                n_bootstrap=n_bootstrap,
            )
            rows.append({
                "variant": variant,
                "seed": seed,
                "action": "continuous_headroom",
                "feature": "route_confidence",
                "examples": len(group),
                "spearman": rho,
                "spearman_ci_low": rho_lo,
                "spearman_ci_high": rho_hi,
            })
            for ratio in DIAGNOSTIC_RATIOS:
                labels = np.asarray([int(row[f"safe_r{ratio:.2f}_m4"]) for row in group], dtype=np.int32)
                for feature_index, (feature, getter) in enumerate(feature_scores.items()):
                    scores = np.asarray([getter(row) for row in group], dtype=np.float64)
                    valid = np.isfinite(scores)
                    y, s = labels[valid], scores[valid]
                    prevalence = float(np.mean(y)) if len(y) else math.nan
                    if len(np.unique(y)) < 2:
                        auc = auc_lo = auc_hi = 0.5
                        ap = ap_lo = ap_hi = prevalence
                    else:
                        rng = np.random.default_rng(
                            stable_seed("feature", variant, seed, ratio, feature_index)
                        )
                        auc, auc_lo, auc_hi = base.metric_with_bootstrap(
                            y, s, roc_auc_score, rng=rng, n_bootstrap=n_bootstrap
                        )
                        ap, ap_lo, ap_hi = base.metric_with_bootstrap(
                            y, s, average_precision_score, rng=rng, n_bootstrap=n_bootstrap
                        )
                    rows.append({
                        "variant": variant,
                        "seed": seed,
                        "action": f"r{ratio:.2f}_m4",
                        "feature": feature,
                        "examples": len(y),
                        "safe_prevalence": prevalence,
                        "auroc": auc,
                        "auroc_ci_low": auc_lo,
                        "auroc_ci_high": auc_hi,
                        "average_precision": ap,
                        "average_precision_ci_low": ap_lo,
                        "average_precision_ci_high": ap_hi,
                    })
    return rows


def paired_rows(
    *,
    variants: Mapping[str, Mapping[str, Mapping[str, Sequence[str]]]],
    test_queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
    n_bootstrap: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    contrasts = (
        ("dynamic_gated", "fixed_full"),
        ("dynamic_gated", "shuffled_tiers"),
        ("dynamic_gated", "fixed_cluster_primary"),
    )
    for stage in ("source", "budget_r0.95_m4"):
        for method, reference in contrasts:
            for seed in ("13", "17", "19"):
                method_rankings = variants[method][seed]
                reference_rankings = variants[reference][seed]
                if stage != "source":
                    method_rankings = budgeted_rankings(
                        method_rankings, chunk_tokens, ratio=COMMON_RATIO, min_keep=COMMON_MIN_KEEP
                    )
                    reference_rankings = budgeted_rankings(
                        reference_rankings, chunk_tokens, ratio=COMMON_RATIO, min_keep=COMMON_MIN_KEEP
                    )
                row = base.paired.compare_variant(
                    scale="100k",
                    queries=test_queries,
                    baseline=base.paired.Variant(reference, reference, seed, dict(reference_rankings)),
                    variant=base.paired.Variant(method, method, seed, dict(method_rankings)),
                    chunk_tokens=chunk_tokens,
                    k=10,
                    noninferiority_margin=0.01,
                    n_bootstrap=n_bootstrap,
                    confidence=0.95,
                    rng=np.random.default_rng(stable_seed("paired", stage, method, reference, seed)),
                )
                row.update({
                    "stage": stage,
                    "contrast": f"{method}_vs_{reference}",
                    "method_variant": method,
                    "reference_variant": reference,
                })
                rows.append(row)
    return rows


def tier_analysis_rows(
    *,
    variants: Mapping[str, Mapping[str, Mapping[str, Sequence[str]]]],
    traces_by_seed: Mapping[str, Mapping[str, Mapping[str, object]]],
    test_queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
) -> list[dict[str, object]]:
    query_truth = {
        base.qid(query): ground_truth(query)
        for query in test_queries
        if ground_truth(query)
    }
    rows: list[dict[str, object]] = []
    for stage in ("source", "budget_r0.95_m4"):
        for seed in ("13", "17", "19"):
            stage_rankings = {
                variant: (
                    variants[variant][seed]
                    if stage == "source"
                    else budgeted_rankings(
                        variants[variant][seed],
                        chunk_tokens,
                        ratio=COMMON_RATIO,
                        min_keep=COMMON_MIN_KEEP,
                    )
                )
                for variant in VARIANTS
            }
            for tier in ("linucb_primary", "hybrid_lite", "full_dense_fallback"):
                query_ids = [
                    query_id for query_id in query_truth
                    if traces_by_seed[seed][query_id]["route"] == tier
                ]
                for variant in VARIANTS:
                    hits = [
                        ranking_hit(stage_rankings[variant][query_id], query_truth[query_id])
                        for query_id in query_ids
                    ]
                    rows.append({
                        "stage": stage,
                        "seed": seed,
                        "original_confidence_tier": tier,
                        "variant": variant,
                        "queries": len(query_ids),
                        "hit@10": mean(hits) if hits else math.nan,
                    })
    return rows


def aggregate_survival(survival: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for variant in VARIANTS:
        for seed in ("13", "17", "19"):
            group = [row for row in survival if row["variant"] == variant and row["seed"] == seed]
            hit_group = [row for row in group if int(row["source_hit"])]
            rows.append({
                "variant": variant,
                "seed": seed,
                "queries": len(group),
                "source_hit": mean(float(row["source_hit"]) for row in group),
                "relevant_chunks_top10": mean(float(row["relevant_chunks_top10"]) for row in group),
                "multiple_relevant_rate_on_hits": (
                    mean(float(row["multiple_relevant"]) for row in hit_group) if hit_group else math.nan
                ),
                "first_relevant_rank_on_hits": (
                    mean(float(row["first_relevant_rank"]) for row in hit_group) if hit_group else math.nan
                ),
                "first_relevant_prefix_ratio_on_hits": (
                    mean(float(row["first_relevant_prefix_ratio"]) for row in hit_group) if hit_group else math.nan
                ),
                "maximum_safe_token_saving_on_hits": (
                    mean(float(row["maximum_safe_token_saving"]) for row in hit_group) if hit_group else math.nan
                ),
                "route_support_count_at100": mean(float(row["route_support_count_at100"]) for row in group),
                "safe_r0.85_m4_on_hits": (
                    mean(float(row["safe_r0.85_m4"]) for row in hit_group) if hit_group else math.nan
                ),
                "safe_r0.95_m4_on_hits": (
                    mean(float(row["safe_r0.95_m4"]) for row in hit_group) if hit_group else math.nan
                ),
            })
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    base.write_csv(path, rows)


def write_markdown(
    path: Path,
    fixed_action: Sequence[Mapping[str, object]],
    paired: Sequence[Mapping[str, object]],
    survival_summary: Sequence[Mapping[str, object]],
    feature_metrics: Sequence[Mapping[str, object]],
    tier_analysis: Sequence[Mapping[str, object]],
) -> None:
    lines = [
        "# Task65.3 Dynamic-Route Mediation and Evidence Survival",
        "",
        "The experiment freezes the Task37 selected arms and confidence trajectory,",
        "then replays alternative route shapes before applying the same `r0.95/m4`",
        "final-context budget.",
        "",
        "## Common Frozen Budget",
        "",
        "| Variant | Hit@10 | Hit delta vs dense | Token saving vs dense |",
        "|---|---:|---:|---:|",
    ]
    for variant in VARIANTS:
        rows = [
            row for row in fixed_action
            if row["variant"] == variant and row["split"] == "test" and row["stage"] == "budget_r0.95_m4"
        ]
        lines.append(
            f"| {variant} | {mean(float(row['hit@10']) for row in rows):.4f} | "
            f"{mean(float(row['hit_delta_vs_dense_pp']) for row in rows):+.2f} pp | "
            f"{mean(float(row['token_saving_vs_dense_pct']) for row in rows):.2f}% |"
        )
    lines.extend([
        "",
        "## Dynamic-Gating Mediation",
        "",
        "Positive hit delta favors dynamic gating.",
        "",
        "| Reference | Stage | Hit delta | CI excludes zero |",
        "|---|---|---:|---:|",
    ])
    for reference in ("fixed_full", "shuffled_tiers", "fixed_cluster_primary"):
        for stage in ("source", "budget_r0.95_m4"):
            rows = [
                row for row in paired
                if row["reference_variant"] == reference and row["stage"] == stage
            ]
            excludes = sum(
                float(row["hit_delta_ci_low"]) > 0 or float(row["hit_delta_ci_high"]) < 0
                for row in rows
            )
            lines.append(
                f"| {reference} | {stage} | "
                f"{mean(float(row['hit_delta_mean']) for row in rows) * 100:+.2f} pp | {excludes}/3 |"
            )
    lines.extend([
        "",
        "## Original Confidence-Tier Outcomes",
        "",
        "Rows are grouped by the tier assigned by the original dynamic policy.",
        "",
        "| Tier | Stage | Dynamic | Shuffled | Fixed full | Always cluster-primary |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for tier in ("linucb_primary", "hybrid_lite", "full_dense_fallback"):
        for stage in ("source", "budget_r0.95_m4"):
            def tier_hit(variant: str) -> float:
                rows = [
                    row for row in tier_analysis
                    if row["original_confidence_tier"] == tier
                    and row["stage"] == stage
                    and row["variant"] == variant
                ]
                return mean(float(row["hit@10"]) for row in rows)
            lines.append(
                f"| {tier} | {stage} | {tier_hit('dynamic_gated'):.3f} | "
                f"{tier_hit('shuffled_tiers'):.3f} | {tier_hit('fixed_full'):.3f} | "
                f"{tier_hit('fixed_cluster_primary'):.3f} |"
            )
    lines.extend([
        "",
        "## Evidence Survival",
        "",
        "| Variant | Relevant chunks | First rank | Max safe saving | Safe at r0.85 |",
        "|---|---:|---:|---:|---:|",
    ])
    for variant in VARIANTS:
        rows = [row for row in survival_summary if row["variant"] == variant]
        lines.append(
            f"| {variant} | {mean(float(row['relevant_chunks_top10']) for row in rows):.3f} | "
            f"{mean(float(row['first_relevant_rank_on_hits']) for row in rows):.3f} | "
            f"{mean(float(row['maximum_safe_token_saving_on_hits']) for row in rows) * 100:.2f}% | "
            f"{mean(float(row['safe_r0.85_m4_on_hits']) for row in rows):.3f} |"
        )
    rho_rows = [
        row for row in feature_metrics
        if row["variant"] == "dynamic_gated" and row["action"] == "continuous_headroom"
    ]
    lines.extend([
        "",
        "## Confidence Diagnostic",
        "",
        "Route confidence versus oracle maximum safe saving is diagnostic only.",
        f"Mean Spearman rho across seeds: `{mean(float(row['spearman']) for row in rho_rows):.3f}`.",
        "",
        "## Guardrail",
        "",
        "A dynamic-route advantage would support confidence-mediated candidate-pool",
        "construction. It would not establish route confidence as a direct predictor",
        "of per-query compression safety.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=RESULTS / "task65_1_confidence_trace_100k",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task65_3_dynamic_route_mediation",
    )
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))

    metrics = read_json(only_file(args.trace_dir, "*_prequential_metrics.json"))[0]
    if metrics.get("reward_attribution") != "cluster_only":
        raise ValueError("Task65.3 requires the cluster-only trajectory")
    traces_payload = read_json(only_file(args.trace_dir, "*_prequential_traces.json"))
    rankings_payload = read_json(only_file(args.trace_dir, "*_prequential_rankings.json"))
    traces_by_seed = traces_payload["gated_cost_aware"]
    saved_dynamic = rankings_payload["gated_cost_aware"]

    corpus = base.context_cost.load_json_list(
        DATA / "processed" / "lotte_technology_search_100k_corpus.json"
    )
    queries = base.context_cost.load_json_list(
        DATA / "processed" / "lotte_technology_search_100k_queries.json"
    )
    calibration_queries, test_queries = base.calibration.split_queries(
        queries,
        calibration_fraction=0.30,
        salt="task38_lotte_calibration_v1:100k",
    )
    split_ids = {
        "calibration": [base.qid(query) for query in calibration_queries],
        "test": [base.qid(query) for query in test_queries],
    }
    count_tokens = base.context_cost.build_token_counter("tiktoken", "cl100k_base")
    chunk_tokens = {
        base.context_cost.chunk_id(chunk): count_tokens(str(chunk.get("text", "")))
        for chunk in corpus
    }
    dense_rankings = read_json(Path(str(metrics["dense_ranking_artifact_path"])))
    variants, components, replay_validation = reconstruct_variants(
        corpus=corpus,
        queries=queries,
        metrics=metrics,
        traces_by_seed=traces_by_seed,
        saved_dynamic=saved_dynamic,
        split_ids=split_ids,
    )

    fixed_action: list[dict[str, object]] = []
    for variant in VARIANTS:
        for seed, rankings in variants[variant].items():
            for stage, stage_rankings in (
                ("source", rankings),
                (
                    "budget_r0.95_m4",
                    budgeted_rankings(
                        rankings,
                        chunk_tokens,
                        ratio=COMMON_RATIO,
                        min_keep=COMMON_MIN_KEEP,
                    ),
                ),
            ):
                for split, split_queries in (
                    ("calibration", calibration_queries),
                    ("test", test_queries),
                ):
                    row = evaluate(split_queries, stage_rankings, dense_rankings, chunk_tokens)
                    row.update({
                        "variant": variant,
                        "seed": seed,
                        "stage": stage,
                        "split": split,
                    })
                    fixed_action.append(row)

    survival = evidence_survival_rows(
        variants=variants,
        components=components,
        traces_by_seed=traces_by_seed,
        test_queries=test_queries,
        chunk_tokens=chunk_tokens,
    )
    survival_summary = aggregate_survival(survival)
    feature_metrics = feature_metric_rows(survival, n_bootstrap=args.bootstrap)
    paired = paired_rows(
        variants=variants,
        test_queries=test_queries,
        chunk_tokens=chunk_tokens,
        n_bootstrap=args.bootstrap,
    )
    tier_analysis = tier_analysis_rows(
        variants=variants,
        traces_by_seed=traces_by_seed,
        test_queries=test_queries,
        chunk_tokens=chunk_tokens,
    )

    output = args.output_prefix
    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output.with_suffix(".replay_validation.csv"), replay_validation)
    write_csv(output.with_suffix(".fixed_action.csv"), fixed_action)
    write_csv(output.with_suffix(".survival.csv"), survival)
    write_csv(output.with_suffix(".survival_summary.csv"), survival_summary)
    write_csv(output.with_suffix(".feature_metrics.csv"), feature_metrics)
    write_csv(output.with_suffix(".paired.csv"), paired)
    write_csv(output.with_suffix(".tier_analysis.csv"), tier_analysis)
    output.with_suffix(".rankings.json").write_text(
        json.dumps(variants, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    output.with_suffix(".json").write_text(
        json.dumps({
            "protocol": {
                "trajectory": "Task37 gated_cost_aware cluster_only",
                "seeds": sorted(traces_by_seed),
                "calibration_queries": len(calibration_queries),
                "test_queries": len(test_queries),
                "variants": VARIANTS,
                "common_budget": "token_budget_r0.95_m4",
            },
            "replay_validation": replay_validation,
            "fixed_action": fixed_action,
            "survival_summary": survival_summary,
            "feature_metrics": feature_metrics,
            "paired": paired,
            "tier_analysis": tier_analysis,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(
        output.with_suffix(".md"),
        fixed_action,
        paired,
        survival_summary,
        feature_metrics,
        tier_analysis,
    )
    print(json.dumps({
        "replay_validation_rows": len(replay_validation),
        "fixed_action_rows": len(fixed_action),
        "survival_rows": len(survival),
        "survival_summary_rows": len(survival_summary),
        "feature_metric_rows": len(feature_metrics),
        "paired_rows": len(paired),
        "tier_analysis_rows": len(tier_analysis),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
