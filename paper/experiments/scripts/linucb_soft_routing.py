#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Soft-routed manifold LinUCB retrieval experiment.

Task 13.5 keeps the Task 12 manifold-local LinUCB policy, but removes the
irreversible hard-pruning failure mode. LinUCB still selects cluster arms and
receives prequential feedback, while final retrieval fuses three evidence
streams:

1. global dense retrieval over the full selected corpus;
2. global BM25 lexical retrieval over the full selected corpus;
3. dense retrieval inside LinUCB-selected cluster arms.

The extra diagnostics quantify when selected arms contain the GT cluster and
how often the dense/BM25 bypass rescues misses caused by cluster routing.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


global_linucb = _load_script_module("linucb_online_baseline", SCRIPT_DIR / "linucb_online_baseline.py")
manifold_linucb = _load_script_module("linucb_manifold_local", SCRIPT_DIR / "linucb_manifold_local.py")
bm25_baseline = _load_script_module("bm25_baseline", SCRIPT_DIR / "bm25_baseline.py")
dense_baseline = global_linucb.dense_baseline
experiment_guardrails = global_linucb.experiment_guardrails
retrieval_metrics = global_linucb.retrieval_metrics

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DATASETS = global_linucb.DEFAULT_DATASETS
DEFAULT_MODEL = global_linucb.DEFAULT_MODEL


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parse_datasets(value: str) -> tuple[str, ...]:
    if value == "all":
        return DEFAULT_DATASETS
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _chunk_id(chunk: Mapping) -> str:
    return global_linucb._chunk_id(chunk)


def _query_id(query: Mapping) -> str:
    return global_linucb._query_id(query)


def _ground_truth(query: Mapping) -> set[str]:
    return global_linucb._ground_truth(query)


def _has_hit(ranking: Sequence[str], ground_truth: set[str], *, k: int) -> bool:
    if not ground_truth:
        return False
    return any(str(chunk_id) in ground_truth for chunk_id in ranking[:k])


def stable_top_k_indices(scores: Sequence[float], k: int) -> List[int]:
    """Return a stable score-desc/index-asc top-k independent of requested depth."""
    if k <= 0:
        return []
    scores_array = np.asarray(scores)
    if scores_array.size == 0:
        return []
    k = min(k, scores_array.size)
    indices = np.arange(scores_array.size)
    ordered = np.lexsort((indices, -scores_array))
    return ordered[:k].astype(int).tolist()


def top_dense_ranking(
    query_embedding: np.ndarray,
    corpus_embeddings: np.ndarray,
    chunk_ids: Sequence[str],
    *,
    depth: int,
) -> List[str]:
    if depth <= 0:
        return []
    scores = corpus_embeddings @ query_embedding
    indices = stable_top_k_indices(scores, min(depth, len(chunk_ids)))
    return [chunk_ids[idx] for idx in indices]


def top_bm25_ranking(
    query_text: str,
    bm25,
    chunk_ids: Sequence[str],
    *,
    depth: int,
) -> List[str]:
    if depth <= 0:
        return []
    scores = bm25.get_scores(bm25_baseline.tokenize(query_text))
    indices = bm25_baseline.top_k_sparse_indices(scores, min(depth, len(chunk_ids)))
    return [chunk_ids[idx] for idx in indices]


def weighted_reciprocal_rank_fusion(
    weighted_rankings: Sequence[tuple[Sequence[str], float]],
    *,
    rrf_k: int = 60,
    top_k: int = 10,
) -> List[str]:
    """Fuse rankings with deterministic weighted RRF."""
    if rrf_k <= 0:
        raise ValueError(f"rrf_k must be positive, got {rrf_k}")
    if top_k <= 0:
        return []

    scores: Dict[str, float] = {}
    first_seen: Dict[str, int] = {}
    cursor = 0
    for ranking, weight in weighted_rankings:
        if weight <= 0:
            continue
        seen_in_ranking: set[str] = set()
        for rank, chunk_id in enumerate(ranking, start=1):
            chunk_id = str(chunk_id)
            if chunk_id in seen_in_ranking:
                continue
            seen_in_ranking.add(chunk_id)
            if chunk_id not in first_seen:
                first_seen[chunk_id] = cursor
                cursor += 1
            scores[chunk_id] = scores.get(chunk_id, 0.0) + float(weight) / float(rrf_k + rank)

    return [
        chunk_id
        for chunk_id, _ in sorted(
            scores.items(),
            key=lambda item: (-item[1], first_seen[item[0]], item[0]),
        )[:top_k]
    ]


def apply_dense_floor(
    fused_ranking: Sequence[str],
    dense_ranking: Sequence[str],
    *,
    dense_floor_k: int,
    top_k: int,
) -> List[str]:
    """Ensure a minimum number of global dense candidates survive final top-k."""
    if dense_floor_k < 0:
        raise ValueError(f"dense_floor_k must be non-negative, got {dense_floor_k}")
    if top_k <= 0:
        return []
    floor = [str(chunk_id) for chunk_id in dense_ranking[: min(dense_floor_k, top_k)]]
    if not floor:
        return [str(chunk_id) for chunk_id in fused_ranking[:top_k]]

    output: List[str] = []
    seen: set[str] = set()
    for chunk_id in floor:
        if chunk_id not in seen:
            output.append(chunk_id)
            seen.add(chunk_id)
    for chunk_id in fused_ranking:
        chunk_id = str(chunk_id)
        if chunk_id not in seen:
            output.append(chunk_id)
            seen.add(chunk_id)
        if len(output) >= top_k:
            break
    return output[:top_k]


def selected_candidate_count(arm_labels: np.ndarray, selected_arms: Sequence[int]) -> int:
    selected = np.isin(arm_labels, np.asarray(selected_arms, dtype=np.int32))
    return int(np.count_nonzero(selected))


def gt_cluster_hit(
    selected_arms: Sequence[int],
    ground_truth: set[str],
    arm_labels_by_chunk: Mapping[str, int],
) -> bool:
    if not ground_truth:
        return False
    selected = {int(arm) for arm in selected_arms}
    return any(arm_labels_by_chunk.get(str(chunk_id)) in selected for chunk_id in ground_truth)


def run_prequential_seed(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    seed: int,
    top_k: int,
    ks: Sequence[int],
    n_clusters: int,
    context_dim: int,
    candidate_arms: int,
    alpha: float,
    alpha_decay: float,
    alpha_min: float,
    arm_neighbor_k: int,
    arm_decay_sigma: float,
    propagation_strength: float,
    feedback_k: int,
    feedback_tau: float,
    feedback_weight: float,
    dense_depth: int,
    bm25_depth: int,
    cluster_depth: int,
    dense_weight: float,
    bm25_weight: float,
    cluster_weight: float,
    rrf_k: int,
    dense_floor_k: int,
) -> Dict[str, object]:
    if not corpus:
        raise ValueError("corpus must not be empty")
    if not queries:
        raise ValueError("queries must not be empty")
    if min(top_k, dense_depth, bm25_depth, cluster_depth) <= 0:
        raise ValueError("top_k and source depths must be positive")

    _, corpus_context, query_context = global_linucb.fit_context_projection(
        corpus_embeddings,
        query_embeddings,
        context_dim,
    )
    corpus_context = global_linucb.l2_normalize(corpus_context)
    query_context = global_linucb.l2_normalize(query_context)

    arm_labels = global_linucb.cluster_corpus(corpus_context, n_clusters=n_clusters, seed=seed)
    n_effective_arms = int(np.max(arm_labels)) + 1
    centroids = manifold_linucb.arm_centroids(corpus_context, arm_labels, n_effective_arms)
    policy = global_linucb.GlobalLinUCBPolicy(
        n_arms=n_effective_arms,
        context_dim=query_context.shape[1],
        alpha=alpha,
        alpha_decay=alpha_decay,
        alpha_min=alpha_min,
        seed=seed,
    )

    rng = np.random.default_rng(seed)
    stream_indices = np.arange(len(queries))
    rng.shuffle(stream_indices)

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    arm_labels_by_chunk = {chunk_id: int(label) for chunk_id, label in zip(chunk_ids, arm_labels)}
    tokenized_corpus = [bm25_baseline.tokenize(str(chunk.get("text", ""))) for chunk in corpus]
    bm25 = bm25_baseline.SparseBM25(tokenized_corpus)

    rankings: Dict[str, List[str]] = {}
    rewards: List[float] = []
    local_boost_norms: List[float] = []
    selected_candidate_counts: List[int] = []
    union_candidate_counts: List[int] = []
    feedback_contexts: List[np.ndarray] = []
    feedback_arm_rewards: List[Dict[int, float]] = []
    total_update_weight = 0.0
    cross_arm_update_weight = 0.0
    propagated_updates = 0

    diagnostics = {
        "num_gt_diagnostic_queries": 0,
        "selected_cluster_hit_count": 0,
        "selected_cluster_miss_count": 0,
        "cluster_local_hit_count": 0,
        "dense_fallback_hit_count": 0,
        "bm25_fallback_hit_count": 0,
        "soft_fused_hit_count": 0,
        "soft_rescue_on_cluster_miss_count": 0,
        "dense_rescue_on_cluster_miss_count": 0,
        "bm25_rescue_on_cluster_miss_count": 0,
    }

    for query_idx in stream_indices:
        query = queries[int(query_idx)]
        qid = _query_id(query)
        context = query_context[int(query_idx)]
        selected_arms, boosts = manifold_linucb.select_arms_with_local_feedback(
            policy,
            context,
            candidate_arms=candidate_arms,
            feedback_contexts=feedback_contexts,
            feedback_arm_rewards=feedback_arm_rewards,
            feedback_k=feedback_k,
            feedback_tau=feedback_tau,
            feedback_weight=feedback_weight,
        )
        local_boost_norms.append(float(np.linalg.norm(boosts)))
        selected_candidate_counts.append(selected_candidate_count(arm_labels, selected_arms))

        dense_ranking = top_dense_ranking(
            query_embeddings[int(query_idx)],
            corpus_embeddings,
            chunk_ids,
            depth=dense_depth,
        )
        bm25_ranking = top_bm25_ranking(
            str(query.get("text", "")),
            bm25,
            chunk_ids,
            depth=bm25_depth,
        )
        cluster_ranking = global_linucb.retrieve_from_arms(
            query_embeddings[int(query_idx)],
            corpus_embeddings,
            chunk_ids,
            arm_labels,
            selected_arms,
            top_k=cluster_depth,
        )
        union_candidate_counts.append(len(set(dense_ranking) | set(bm25_ranking) | set(cluster_ranking)))
        ranking = weighted_reciprocal_rank_fusion(
            (
                (dense_ranking, dense_weight),
                (bm25_ranking, bm25_weight),
                (cluster_ranking, cluster_weight),
            ),
            rrf_k=rrf_k,
            top_k=top_k,
        )
        ranking = apply_dense_floor(
            ranking,
            dense_ranking,
            dense_floor_k=dense_floor_k,
            top_k=top_k,
        )
        rankings[qid] = ranking

        gt = _ground_truth(query)
        selected_cluster_hit = gt_cluster_hit(selected_arms, gt, arm_labels_by_chunk)
        cluster_hit = _has_hit(cluster_ranking, gt, k=top_k)
        dense_hit = _has_hit(dense_ranking, gt, k=top_k)
        bm25_hit = _has_hit(bm25_ranking, gt, k=top_k)
        soft_hit = _has_hit(ranking, gt, k=top_k)
        if gt:
            diagnostics["num_gt_diagnostic_queries"] += 1
            diagnostics["selected_cluster_hit_count"] += int(selected_cluster_hit)
            diagnostics["selected_cluster_miss_count"] += int(not selected_cluster_hit)
            diagnostics["cluster_local_hit_count"] += int(cluster_hit)
            diagnostics["dense_fallback_hit_count"] += int(dense_hit)
            diagnostics["bm25_fallback_hit_count"] += int(bm25_hit)
            diagnostics["soft_fused_hit_count"] += int(soft_hit)
            if not selected_cluster_hit:
                diagnostics["soft_rescue_on_cluster_miss_count"] += int(soft_hit)
                diagnostics["dense_rescue_on_cluster_miss_count"] += int(dense_hit)
                diagnostics["bm25_rescue_on_cluster_miss_count"] += int(bm25_hit)

        arm_rewards: Dict[int, float] = {}
        selected_rewards = []
        for source_arm in selected_arms:
            reward = global_linucb._arm_reward(ranking, gt, source_arm, arm_labels_by_chunk)
            arm_rewards[int(source_arm)] = reward
            selected_rewards.append(reward)
            for target_arm, weight in manifold_linucb.arm_propagation_weights(
                centroids,
                source_arm,
                sigma=arm_decay_sigma,
                neighbor_k=arm_neighbor_k,
                propagation_strength=propagation_strength,
            ):
                policy.update(target_arm, context, reward, weight=weight)
                total_update_weight += float(weight)
                if target_arm != source_arm:
                    cross_arm_update_weight += float(weight)
                    propagated_updates += 1
        feedback_contexts.append(context.copy())
        feedback_arm_rewards.append(arm_rewards)
        rewards.append(max(selected_rewards) if selected_rewards else 0.0)

    metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    gt_count = int(diagnostics["num_gt_diagnostic_queries"])
    cluster_miss_count = int(diagnostics["selected_cluster_miss_count"])
    extra_metrics = {
        "seed": seed,
        "avg_feedback_reward": float(np.mean(rewards)) if rewards else 0.0,
        "avg_local_boost_norm": float(np.mean(local_boost_norms)) if local_boost_norms else 0.0,
        "avg_selected_candidate_chunks": float(np.mean(selected_candidate_counts)) if selected_candidate_counts else 0.0,
        "avg_union_candidate_chunks": float(np.mean(union_candidate_counts)) if union_candidate_counts else 0.0,
        "selected_cluster_hit_rate": diagnostics["selected_cluster_hit_count"] / gt_count if gt_count else 0.0,
        "selected_cluster_miss_rate": diagnostics["selected_cluster_miss_count"] / gt_count if gt_count else 0.0,
        "cluster_local_hit_rate": diagnostics["cluster_local_hit_count"] / gt_count if gt_count else 0.0,
        "dense_fallback_hit_rate": diagnostics["dense_fallback_hit_count"] / gt_count if gt_count else 0.0,
        "bm25_fallback_hit_rate": diagnostics["bm25_fallback_hit_count"] / gt_count if gt_count else 0.0,
        "soft_fused_hit_rate": diagnostics["soft_fused_hit_count"] / gt_count if gt_count else 0.0,
        "soft_rescue_on_cluster_miss_rate": (
            diagnostics["soft_rescue_on_cluster_miss_count"] / cluster_miss_count
            if cluster_miss_count
            else 0.0
        ),
        "dense_rescue_on_cluster_miss_rate": (
            diagnostics["dense_rescue_on_cluster_miss_count"] / cluster_miss_count
            if cluster_miss_count
            else 0.0
        ),
        "bm25_rescue_on_cluster_miss_rate": (
            diagnostics["bm25_rescue_on_cluster_miss_count"] / cluster_miss_count
            if cluster_miss_count
            else 0.0
        ),
        "final_effective_alpha": float(policy.effective_alpha),
        "n_effective_arms": n_effective_arms,
        "total_feedback_updates": int(policy.total_feedback),
        "total_update_weight": float(total_update_weight),
        "cross_arm_update_weight": float(cross_arm_update_weight),
        "propagated_updates": int(propagated_updates),
    }
    extra_metrics.update(diagnostics)
    metrics.update(extra_metrics)
    return {"rankings": rankings, "metrics": metrics}


def aggregate_seed_metrics(seed_metrics: Sequence[Mapping]) -> Dict[str, object]:
    return global_linucb.aggregate_seed_metrics(seed_metrics)


def run_dataset(
    dataset: str,
    data_dir: Path,
    output_dir: Path,
    encoder,
    *,
    model_name: str,
    top_k: int,
    ks: Sequence[int],
    batch_size: int,
    seeds: Sequence[int],
    n_clusters: int,
    context_dim: int,
    candidate_arms: int,
    alpha: float,
    alpha_decay: float,
    alpha_min: float,
    arm_neighbor_k: int,
    arm_decay_sigma: float,
    propagation_strength: float,
    feedback_k: int,
    feedback_tau: float,
    feedback_weight: float,
    dense_depth: int,
    bm25_depth: int,
    cluster_depth: int,
    dense_weight: float,
    bm25_weight: float,
    cluster_weight: float,
    rrf_k: int,
    dense_floor_k: int,
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
) -> Dict[str, object]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    corpus_all = global_linucb.load_json_list(corpus_path)
    queries_all = global_linucb.load_json_list(queries_path)
    queries = experiment_guardrails.apply_query_controls(queries_all, query_split=query_split, max_queries=max_queries)
    resolved_corpus_sampling = experiment_guardrails.resolve_corpus_sampling(dataset, max_corpus, corpus_sampling)
    corpus = experiment_guardrails.apply_corpus_controls(
        corpus_all,
        max_corpus=max_corpus,
        queries=queries,
        corpus_sampling=resolved_corpus_sampling,
        random_seed=sampling_seed,
    )
    gt_coverage = experiment_guardrails.assert_gt_corpus_coverage(queries, corpus)

    start = time.perf_counter()
    corpus_embeddings = dense_baseline.encode_texts(
        encoder,
        [str(chunk.get("text", "")) for chunk in corpus],
        batch_size=batch_size,
    )
    query_embeddings = dense_baseline.encode_texts(
        encoder,
        [str(query.get("text", "")) for query in queries],
        batch_size=batch_size,
    )

    seed_results = []
    for seed in seeds:
        seed_results.append(run_prequential_seed(
            corpus,
            queries,
            corpus_embeddings,
            query_embeddings,
            seed=seed,
            top_k=top_k,
            ks=ks,
            n_clusters=n_clusters,
            context_dim=context_dim,
            candidate_arms=candidate_arms,
            alpha=alpha,
            alpha_decay=alpha_decay,
            alpha_min=alpha_min,
            arm_neighbor_k=arm_neighbor_k,
            arm_decay_sigma=arm_decay_sigma,
            propagation_strength=propagation_strength,
            feedback_k=feedback_k,
            feedback_tau=feedback_tau,
            feedback_weight=feedback_weight,
            dense_depth=dense_depth,
            bm25_depth=bm25_depth,
            cluster_depth=cluster_depth,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
            cluster_weight=cluster_weight,
            rrf_k=rrf_k,
            dense_floor_k=dense_floor_k,
        ))
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"linucb_soft_{dataset}_prequential_rankings.json"
    metrics_path = output_dir / f"linucb_soft_{dataset}_prequential_metrics.json"

    per_seed_metrics = [result["metrics"] for result in seed_results]
    representative = per_seed_metrics[0]
    aggregated = aggregate_seed_metrics(per_seed_metrics)
    metadata = {
        "dataset": dataset,
        "method": "linucb_soft_manifold",
        "model": model_name,
        "protocol": "prequential",
        "feedback_source": "gt_derived_soft_fused_topk_arm_reward",
        "online_learning_scope": "soft_routing_dense_bm25_manifold_feedback",
        "manifold_neighbor_engine": "cpu_exact_numpy",
        "fusion": "weighted_rrf",
        "top_k": top_k,
        "ks": list(ks),
        "batch_size": batch_size,
        "seeds": list(seeds),
        "n_clusters_requested": n_clusters,
        "context_dim_requested": context_dim,
        "candidate_arms": candidate_arms,
        "alpha": alpha,
        "alpha_decay": alpha_decay,
        "alpha_min": alpha_min,
        "arm_neighbor_k": arm_neighbor_k,
        "arm_decay_sigma": arm_decay_sigma,
        "propagation_strength": propagation_strength,
        "feedback_k": feedback_k,
        "feedback_tau": feedback_tau,
        "feedback_weight": feedback_weight,
        "dense_depth": dense_depth,
        "bm25_depth": bm25_depth,
        "cluster_depth": cluster_depth,
        "dense_weight": dense_weight,
        "bm25_weight": bm25_weight,
        "cluster_weight": cluster_weight,
        "rrf_k": rrf_k,
        "dense_floor_k": dense_floor_k,
        "num_corpus_chunks": len(corpus),
        "num_total_corpus_chunks": len(corpus_all),
        "num_total_queries": len(queries_all),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "elapsed_sec": round(elapsed_sec, 3),
        **experiment_guardrails.build_run_metadata(
            dataset=dataset,
            queries=queries,
            all_queries=queries_all,
            corpus=corpus,
            all_corpus=corpus_all,
            max_queries=max_queries,
            max_corpus=max_corpus,
            corpus_sampling=resolved_corpus_sampling,
            requested_query_split=query_split,
            top_k=top_k,
            ks=ks,
        ),
        **gt_coverage,
    }
    metrics = {
        **metadata,
        **{key: value for key, value in representative.items() if key in {"num_queries", "num_skipped_no_gt"}},
        **aggregated,
        "per_seed": per_seed_metrics,
    }

    rankings = {
        str(result["metrics"]["seed"]): result["rankings"]
        for result in seed_results
    }
    rankings_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def _stringify_csv_value(value: object) -> object:
    return global_linucb._stringify_csv_value(value)


def update_summary(summary_path: Path, rows: Iterable[Mapping]) -> None:
    new_rows = list(rows)
    if not new_rows:
        return
    existing: Dict[tuple[str, str, str], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(row.get("dataset", ""), row.get("method", ""), row.get("model", ""))] = row
    for row in new_rows:
        existing[(str(row["dataset"]), str(row["method"]), str(row.get("model", "")))] = row

    metric_keys = sorted({
        key
        for row in existing.values()
        for key in row
        if "@" in key
        or key.endswith("_reward_mean")
        or key.endswith("_boost_norm_mean")
        or key.endswith("_hit_rate_mean")
        or key.endswith("_miss_rate_mean")
        or key.endswith("_chunks_mean")
    })
    fieldnames = [
        "dataset",
        "method",
        "model",
        "protocol",
        "task_type",
        "scope",
        "query_split",
        "corpus_scope",
        "corpus_sampling",
        "online_learning_scope",
        "manifold_neighbor_engine",
        "fusion",
        "num_queries",
        "num_skipped_no_gt",
        "num_queries_with_gt",
        "num_queries_with_gt_in_corpus",
        "num_queries_gt_missing_from_corpus",
        "num_gt_refs",
        "num_gt_refs_in_corpus",
        "num_gt_refs_missing_from_corpus",
        "gt_query_coverage",
        "gt_ref_coverage",
        "gt_corpus_guardrail",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "num_total_queries",
        "max_queries",
        "max_corpus",
        "top_k",
        "metric_ks",
        "num_seeds",
        "seeds",
        "n_clusters_requested",
        "n_effective_arms_mean",
        "context_dim_requested",
        "candidate_arms",
        "alpha",
        "alpha_decay",
        "alpha_min",
        "arm_neighbor_k",
        "arm_decay_sigma",
        "propagation_strength",
        "feedback_k",
        "feedback_tau",
        "feedback_weight",
        "dense_depth",
        "bm25_depth",
        "cluster_depth",
        "dense_weight",
        "bm25_weight",
        "cluster_weight",
        "rrf_k",
        "dense_floor_k",
        "total_feedback_updates_mean",
        "total_update_weight_mean",
        "cross_arm_update_weight_mean",
        "propagated_updates_mean",
        *metric_keys,
        "elapsed_sec",
        "notes",
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow({
                name: _stringify_csv_value(value)
                for name, value in existing[key].items()
            })


def load_sentence_transformer(model_name: str, *, device: str | None = None, local_files_only: bool = False):
    return dense_baseline.load_sentence_transformer(model_name, device=device, local_files_only=local_files_only)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run soft-routed manifold LinUCB retrieval experiment")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--seeds", default="13,17,19")
    parser.add_argument("--n-clusters", type=int, default=32)
    parser.add_argument("--context-dim", type=int, default=64)
    parser.add_argument("--candidate-arms", type=int, default=3)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--alpha-decay", type=float, default=0.01)
    parser.add_argument("--alpha-min", type=float, default=0.3)
    parser.add_argument("--arm-neighbor-k", type=int, default=4)
    parser.add_argument("--arm-decay-sigma", type=float, default=0.75)
    parser.add_argument("--propagation-strength", type=float, default=0.25)
    parser.add_argument("--feedback-k", type=int, default=16)
    parser.add_argument("--feedback-tau", type=float, default=0.75)
    parser.add_argument("--feedback-weight", type=float, default=0.35)
    parser.add_argument("--dense-depth", type=int, default=100)
    parser.add_argument("--bm25-depth", type=int, default=100)
    parser.add_argument("--cluster-depth", type=int, default=100)
    parser.add_argument("--dense-weight", type=float, default=2.0)
    parser.add_argument("--bm25-weight", type=float, default=0.8)
    parser.add_argument("--cluster-weight", type=float, default=0.8)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument(
        "--dense-floor-k",
        type=int,
        default=5,
        help="Protect this many global dense candidates in the final top-k; 0 disables the floor",
    )
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--max-corpus", type=int, default=None)
    parser.add_argument("--query-split", default=None)
    parser.add_argument(
        "--corpus-sampling",
        default="auto",
        choices=sorted(experiment_guardrails.CORPUS_SAMPLING_STRATEGIES),
        help="Corpus sampling strategy; auto uses GT-anchored CUAD samples when max-corpus is set",
    )
    parser.add_argument("--sampling-seed", type=int, default=13)
    args = parser.parse_args(argv)

    datasets = parse_datasets(args.dataset)
    ks = parse_ints(args.ks)
    seeds = parse_ints(args.seeds)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    rows = []
    for dataset in datasets:
        print(f"Running soft-routed manifold LinUCB experiment: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            top_k=args.top_k,
            ks=ks,
            batch_size=args.batch_size,
            seeds=seeds,
            n_clusters=args.n_clusters,
            context_dim=args.context_dim,
            candidate_arms=args.candidate_arms,
            alpha=args.alpha,
            alpha_decay=args.alpha_decay,
            alpha_min=args.alpha_min,
            arm_neighbor_k=args.arm_neighbor_k,
            arm_decay_sigma=args.arm_decay_sigma,
            propagation_strength=args.propagation_strength,
            feedback_k=args.feedback_k,
            feedback_tau=args.feedback_tau,
            feedback_weight=args.feedback_weight,
            dense_depth=args.dense_depth,
            bm25_depth=args.bm25_depth,
            cluster_depth=args.cluster_depth,
            dense_weight=args.dense_weight,
            bm25_weight=args.bm25_weight,
            cluster_weight=args.cluster_weight,
            rrf_k=args.rrf_k,
            dense_floor_k=args.dense_floor_k,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
        )
        rows.append(metrics)
        print(
            f"  queries={metrics.get('num_queries')} skipped_no_gt={metrics.get('num_skipped_no_gt')} "
            f"gt_query_coverage={metrics.get('gt_query_coverage', 0.0):.4f} "
            f"recall@10_mean={metrics.get('recall@10_mean', 0.0):.4f} "
            f"selected_cluster_hit={metrics.get('selected_cluster_hit_rate_mean', 0.0):.4f} "
            f"soft_rescue_miss={metrics.get('soft_rescue_on_cluster_miss_rate_mean', 0.0):.4f} "
            f"elapsed={metrics['elapsed_sec']}s"
        )

    update_summary(args.output_dir / "linucb_soft_summary.csv", rows)
    print(f"Summary: {args.output_dir / 'linucb_soft_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
