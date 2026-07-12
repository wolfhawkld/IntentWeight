#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manifold-local LinUCB prequential retrieval experiment.

This is the Task 12 variant of the Task 11 global LinUCB baseline. It keeps the
same no-leakage prequential protocol, but makes feedback local in the fixed
semantic geometry:

1. query-local feedback attention boosts arms rewarded by nearby historical
   query contexts;
2. arm-level feedback propagates from a selected cluster to nearby clusters with
   distance decay.
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


def arm_centroids(corpus_context: np.ndarray, arm_labels: np.ndarray, n_arms: int) -> np.ndarray:
    """Compute normalized arm centroids in context space."""
    centroids = np.zeros((n_arms, corpus_context.shape[1]), dtype=np.float32)
    for arm in range(n_arms):
        member_indices = np.flatnonzero(arm_labels == arm)
        if member_indices.size:
            centroids[arm] = np.mean(corpus_context[member_indices], axis=0)
    return global_linucb.l2_normalize(centroids)


def arm_propagation_weights(
    centroids: np.ndarray,
    source_arm: int,
    *,
    sigma: float,
    neighbor_k: int,
    propagation_strength: float,
) -> List[tuple[int, float]]:
    """Return target arm update weights for source-arm feedback."""
    if sigma <= 0:
        raise ValueError(f"sigma must be positive, got {sigma}")
    if neighbor_k <= 0:
        raise ValueError(f"neighbor_k must be positive, got {neighbor_k}")
    if propagation_strength < 0:
        raise ValueError(f"propagation_strength must be non-negative, got {propagation_strength}")
    if source_arm < 0 or source_arm >= len(centroids):
        raise ValueError(f"Invalid source arm: {source_arm}")

    distances = np.linalg.norm(centroids - centroids[source_arm], axis=1)
    ordered = sorted(range(len(centroids)), key=lambda arm: (float(distances[arm]), arm))
    targets: List[tuple[int, float]] = []
    for arm in ordered[: min(neighbor_k, len(ordered))]:
        if arm == source_arm:
            targets.append((arm, 1.0))
        else:
            decay = float(np.exp(-float(distances[arm]) / sigma))
            weight = propagation_strength * decay
            if weight > 0:
                targets.append((arm, weight))
    if not any(arm == source_arm for arm, _ in targets):
        targets.insert(0, (source_arm, 1.0))
    return targets


def local_feedback_boosts(
    context: np.ndarray,
    feedback_contexts: Sequence[np.ndarray],
    feedback_arm_rewards: Sequence[Mapping[int, float]],
    *,
    n_arms: int,
    feedback_k: int,
    tau: float,
    feedback_weight: float,
) -> np.ndarray:
    """Compute arm score boosts from nearby historical feedback."""
    if feedback_k <= 0:
        raise ValueError(f"feedback_k must be positive, got {feedback_k}")
    if tau <= 0:
        raise ValueError(f"tau must be positive, got {tau}")
    if feedback_weight < 0:
        raise ValueError(f"feedback_weight must be non-negative, got {feedback_weight}")
    boosts = np.zeros(n_arms, dtype=np.float64)
    if not feedback_contexts or feedback_weight == 0:
        return boosts

    contexts = np.asarray(feedback_contexts, dtype=np.float32)
    distances = np.linalg.norm(contexts - context.astype(np.float32), axis=1)
    indices = np.arange(len(distances), dtype=np.int64)
    nearest = np.lexsort((indices, distances))[:feedback_k].tolist()
    reward_sums = np.zeros(n_arms, dtype=np.float64)
    total_neighbor_weight = 0.0
    for idx in nearest:
        weight = float(np.exp(-float(distances[idx]) / tau))
        total_neighbor_weight += weight
        for arm, reward in feedback_arm_rewards[idx].items():
            if 0 <= int(arm) < n_arms:
                reward_sums[int(arm)] += weight * float(reward)
    if total_neighbor_weight > 0:
        boosts = reward_sums / total_neighbor_weight
    return feedback_weight * boosts


def select_arms_with_local_feedback(
    policy,
    context: np.ndarray,
    *,
    candidate_arms: int,
    feedback_contexts: Sequence[np.ndarray],
    feedback_arm_rewards: Sequence[Mapping[int, float]],
    feedback_k: int,
    feedback_tau: float,
    feedback_weight: float,
) -> tuple[List[int], np.ndarray]:
    if candidate_arms <= 0:
        raise ValueError(f"candidate_arms must be positive, got {candidate_arms}")
    base_scores = policy.scores(context)
    boosts = local_feedback_boosts(
        context,
        feedback_contexts,
        feedback_arm_rewards,
        n_arms=policy.n_arms,
        feedback_k=feedback_k,
        tau=feedback_tau,
        feedback_weight=feedback_weight,
    )
    scores = base_scores + boosts
    k = min(candidate_arms, policy.n_arms)
    selected = np.argsort(scores)[-k:][::-1].astype(int).tolist()
    return selected, boosts


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
) -> Dict[str, object]:
    if not corpus:
        raise ValueError("corpus must not be empty")
    if not queries:
        raise ValueError("queries must not be empty")

    _, corpus_context, query_context = global_linucb.fit_context_projection(
        corpus_embeddings,
        query_embeddings,
        context_dim,
    )
    corpus_context = global_linucb.l2_normalize(corpus_context)
    query_context = global_linucb.l2_normalize(query_context)

    arm_labels = global_linucb.cluster_corpus(corpus_context, n_clusters=n_clusters, seed=seed)
    n_effective_arms = int(np.max(arm_labels)) + 1
    centroids = arm_centroids(corpus_context, arm_labels, n_effective_arms)
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

    rankings: Dict[str, List[str]] = {}
    rewards: List[float] = []
    local_boost_norms: List[float] = []
    feedback_contexts: List[np.ndarray] = []
    feedback_arm_rewards: List[Dict[int, float]] = []
    total_update_weight = 0.0
    cross_arm_update_weight = 0.0
    propagated_updates = 0

    for query_idx in stream_indices:
        query = queries[int(query_idx)]
        qid = _query_id(query)
        context = query_context[int(query_idx)]
        selected_arms, boosts = select_arms_with_local_feedback(
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
        ranking = global_linucb.retrieve_from_arms(
            query_embeddings[int(query_idx)],
            corpus_embeddings,
            chunk_ids,
            arm_labels,
            selected_arms,
            top_k=top_k,
        )
        rankings[qid] = ranking

        gt = _ground_truth(query)
        arm_rewards: Dict[int, float] = {}
        selected_rewards = []
        for source_arm in selected_arms:
            reward = global_linucb._arm_reward(ranking, gt, source_arm, arm_labels_by_chunk)
            arm_rewards[int(source_arm)] = reward
            selected_rewards.append(reward)
            for target_arm, weight in arm_propagation_weights(
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
    metrics.update({
        "seed": seed,
        "avg_feedback_reward": float(np.mean(rewards)) if rewards else 0.0,
        "avg_local_boost_norm": float(np.mean(local_boost_norms)) if local_boost_norms else 0.0,
        "final_effective_alpha": float(policy.effective_alpha),
        "n_effective_arms": n_effective_arms,
        "total_feedback_updates": int(policy.total_feedback),
        "total_update_weight": float(total_update_weight),
        "cross_arm_update_weight": float(cross_arm_update_weight),
        "propagated_updates": int(propagated_updates),
    })
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
        ))
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"linucb_manifold_{dataset}_prequential_rankings.json"
    metrics_path = output_dir / f"linucb_manifold_{dataset}_prequential_metrics.json"

    per_seed_metrics = [result["metrics"] for result in seed_results]
    representative = per_seed_metrics[0]
    aggregated = aggregate_seed_metrics(per_seed_metrics)
    metadata = {
        "dataset": dataset,
        "method": "linucb_manifold_local",
        "model": model_name,
        "protocol": "prequential",
        "feedback_source": "gt_derived_topk_arm_reward",
        "online_learning_scope": "manifold_local_feedback_propagation",
        "manifold_neighbor_engine": "cpu_exact_numpy",
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
        if "@" in key or key.endswith("_reward_mean") or key.endswith("_boost_norm_mean")
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
    parser = argparse.ArgumentParser(description="Run manifold-local LinUCB prequential retrieval experiment")
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
        print(f"Running manifold-local LinUCB prequential experiment: {dataset}")
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
            f"mrr@10_mean={metrics.get('mrr@10_mean', 0.0):.4f} "
            f"cross_arm_weight_mean={metrics.get('cross_arm_update_weight_mean', 0.0):.3f} "
            f"elapsed={metrics['elapsed_sec']}s"
        )

    update_summary(args.output_dir / "linucb_manifold_summary.csv", rows)
    print(f"Summary: {args.output_dir / 'linucb_manifold_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
