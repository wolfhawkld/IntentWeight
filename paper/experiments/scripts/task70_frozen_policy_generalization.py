#!/usr/bin/env python3
"""Evaluate feedback-trained routing on previously unseen query folds.

Each fold trains a route policy on the other four canonical Task69 folds, then
freezes all feedback-dependent state before evaluating the held-out fold once.
This isolates transfer from repeated-query adaptation: no held-out query label
can change an arm statistic, feedback memory entry, reward history, or later
held-out ranking.
"""
from __future__ import annotations

import argparse
import copy
import csv
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing = load_module("task70_routing", SCRIPT_DIR / "linucb_cost_aware_routing.py")
crossfit = load_module("task70_crossfit", SCRIPT_DIR / "task69_cross_fitted_calibration.py")
paired = load_module("task70_paired", SCRIPT_DIR / "task37_paired_significance.py")

BOOTSTRAP_SAMPLES = 10_000
PAIRWISE_COMPARISONS = (
    ("learned_full_frozen", "dense"),
    ("learned_full_frozen", "static_nearest_full"),
    ("learned_full_frozen", "cold_no_feedback_full"),
    ("learned_gated_frozen", "dense"),
    ("learned_gated_frozen", "static_nearest_gated"),
    ("learned_gated_frozen", "cold_no_feedback_gated"),
)

METHODS = (
    "learned_full_frozen",
    "learned_gated_frozen",
    "static_nearest_full",
    "static_nearest_gated",
    "cold_no_feedback_full",
    "cold_no_feedback_gated",
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def checkpoint_signature(args) -> dict[str, object]:
    """Return the protocol fields that make a fold checkpoint reusable."""
    return {
        "version": 1,
        "dataset": args.dataset,
        "model": args.model,
        "seeds": list(args.seeds),
        "history_epochs": args.history_epochs,
        "n_clusters": args.n_clusters,
        "context_dim": args.context_dim,
        "candidate_arms": args.candidate_arms,
        "alpha": args.alpha,
        "alpha_decay": args.alpha_decay,
        "alpha_min": args.alpha_min,
        "arm_neighbor_k": args.arm_neighbor_k,
        "arm_decay_sigma": args.arm_decay_sigma,
        "propagation_strength": args.propagation_strength,
        "feedback_k": args.feedback_k,
        "feedback_tau": args.feedback_tau,
        "feedback_weight": args.feedback_weight,
        "fold_salt": crossfit.FOLD_SALT,
        "methods": list(METHODS),
        "cluster_retrieval_engine": "cached_exact_scores",
    }


def checkpoint_directory(output_prefix: Path) -> Path:
    return output_prefix.parent / f"{output_prefix.name}.checkpoints"


def merge_rankings(
    target: dict[str, dict[str, dict[str, list[str]]]],
    source: Mapping[str, Mapping[str, Mapping[str, Sequence[str]]]],
) -> None:
    for method, by_seed in source.items():
        for seed, rankings in by_seed.items():
            destination = target.setdefault(str(method), {}).setdefault(str(seed), {})
            duplicate = set(destination).intersection(rankings)
            if duplicate:
                raise AssertionError(f"duplicate checkpoint rankings for {method} seed={seed}: {sorted(duplicate)[:3]}")
            destination.update({str(query): [str(item) for item in ranking] for query, ranking in rankings.items()})


def load_fold_checkpoint(
    path: Path,
    *,
    signature: Mapping[str, object],
    expected_query_ids: set[str],
) -> tuple[list[dict[str, object]], dict[str, dict[str, dict[str, list[str]]]]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("signature") != signature:
        raise ValueError(f"checkpoint signature mismatch: {path}")
    rankings = payload.get("rankings")
    rows = payload.get("fold_rows")
    if not isinstance(rankings, Mapping) or not isinstance(rows, list):
        raise ValueError(f"invalid checkpoint payload: {path}")
    for method, by_seed in rankings.items():
        if method not in METHODS or not isinstance(by_seed, Mapping):
            raise ValueError(f"invalid checkpoint method payload: {path}")
        for seed, by_query in by_seed.items():
            if int(seed) not in signature["seeds"]:
                raise ValueError(f"invalid checkpoint seed payload: {path}")
            actual = set(by_query)
            if actual != expected_query_ids:
                raise AssertionError(f"checkpoint query coverage mismatch for {method} seed={seed}: {path}")
    return [dict(row) for row in rows], {
        str(method): {
            str(seed): {str(query): [str(item) for item in ranking] for query, ranking in by_query.items()}
            for seed, by_query in by_seed.items()
        }
        for method, by_seed in rankings.items()
    }


def qid(query: Mapping[str, object]) -> str:
    return routing._query_id(query)


def subset(values: Sequence, indices: Sequence[int]):
    return [values[index] for index in indices]


def subset_matrix(values: np.ndarray, indices: Sequence[int]) -> np.ndarray:
    return np.asarray(values[np.asarray(indices, dtype=np.int64)], dtype=np.float32)


class ScoreRowSubset:
    """Expose selected score-cache rows without materializing a fold-sized copy."""

    def __init__(self, score_rows: np.ndarray, indices: Sequence[int]):
        if len(score_rows.shape) != 2:
            raise ValueError("score rows must be a two-dimensional matrix")
        self._score_rows = score_rows
        self._indices = np.asarray(indices, dtype=np.int64)
        self.shape = (len(self._indices), int(score_rows.shape[1]))

    def __getitem__(self, index):
        if isinstance(index, (int, np.integer)):
            return self._score_rows[int(self._indices[int(index)])]
        return self._score_rows[self._indices[index]]


def scalar_metrics(metrics: Mapping[str, object]) -> dict[str, float]:
    keys = (
        "hit@10",
        "evidence_recall@10",
        "mrr@10",
        "ndcg@10",
        "dense_query_rate",
        "avg_source_candidate_cost",
        "selected_cluster_hit_rate",
        "avg_confidence",
    )
    return {key: float(metrics.get(key, 0.0)) for key in keys}


def seed_summary(method: str, seed: int, rankings: Mapping[str, Sequence[str]], queries: Sequence[Mapping[str, object]]) -> dict[str, object]:
    metrics = routing.retrieval_metrics.evaluate_rankings(queries, rankings, ks=(1, 5, 10))
    return {
        "method": method,
        "seed": str(seed),
        "queries": len(queries),
        "hit@10": float(metrics["hit@10"]),
        "evidence_recall@10": float(metrics["evidence_recall@10"]),
        "mrr@10": float(metrics["mrr@10"]),
        "ndcg@10": float(metrics["ndcg@10"]),
    }


def mean_std(values: Sequence[float]) -> tuple[float, float]:
    return (mean(values), pstdev(values) if len(values) > 1 else 0.0)


def paired_comparison(
    *,
    queries: Sequence[Mapping[str, object]],
    method: str,
    baseline: str,
    seed: int,
    method_rankings: Mapping[str, Sequence[str]],
    baseline_rankings: Mapping[str, Sequence[str]],
    n_bootstrap: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    """Compute query-paired frozen-policy comparisons without token claims."""
    method_hits: list[float] = []
    baseline_hits: list[float] = []
    evidence_recall_deltas: list[float] = []
    mrr_deltas: list[float] = []
    ndcg_deltas: list[float] = []

    for query in queries:
        query_id = qid(query)
        gt = routing.retrieval_metrics._ground_truth(query)
        if not gt:
            continue
        method_ranking = [str(item) for item in method_rankings.get(query_id, [])]
        baseline_ranking = [str(item) for item in baseline_rankings.get(query_id, [])]
        method_hits.append(routing.retrieval_metrics.hit_at_k(method_ranking, gt, 10))
        baseline_hits.append(routing.retrieval_metrics.hit_at_k(baseline_ranking, gt, 10))
        evidence_recall_deltas.append(
            routing.retrieval_metrics.evidence_recall_at_k(method_ranking, gt, 10)
            - routing.retrieval_metrics.evidence_recall_at_k(baseline_ranking, gt, 10)
        )
        mrr_deltas.append(
            routing.retrieval_metrics.mrr_at_k(method_ranking, gt, 10)
            - routing.retrieval_metrics.mrr_at_k(baseline_ranking, gt, 10)
        )
        ndcg_deltas.append(
            routing.retrieval_metrics.ndcg_at_k(method_ranking, gt, 10)
            - routing.retrieval_metrics.ndcg_at_k(baseline_ranking, gt, 10)
        )

    method_array = np.asarray(method_hits, dtype=np.float64)
    baseline_array = np.asarray(baseline_hits, dtype=np.float64)
    hit_delta_mean, hit_delta_low, hit_delta_high = paired.bootstrap_ci(
        method_array - baseline_array,
        rng=np.random.default_rng(bootstrap_seed),
        n_bootstrap=n_bootstrap,
        confidence=0.95,
    )
    recall_delta_mean, recall_delta_low, recall_delta_high = paired.bootstrap_ci(
        np.asarray(evidence_recall_deltas, dtype=np.float64),
        rng=np.random.default_rng(bootstrap_seed + 1),
        n_bootstrap=n_bootstrap,
        confidence=0.95,
    )
    mrr_delta_mean, mrr_delta_low, mrr_delta_high = paired.bootstrap_ci(
        np.asarray(mrr_deltas, dtype=np.float64),
        rng=np.random.default_rng(bootstrap_seed + 2),
        n_bootstrap=n_bootstrap,
        confidence=0.95,
    )
    ndcg_delta_mean, ndcg_delta_low, ndcg_delta_high = paired.bootstrap_ci(
        np.asarray(ndcg_deltas, dtype=np.float64),
        rng=np.random.default_rng(bootstrap_seed + 3),
        n_bootstrap=n_bootstrap,
        confidence=0.95,
    )
    method_only, baseline_only, mcnemar_p = paired.mcnemar_exact_p(
        [int(value) for value in method_hits],
        [int(value) for value in baseline_hits],
    )
    ties = int(len(method_hits) - method_only - baseline_only)
    return {
        "method": method,
        "baseline": baseline,
        "seed": str(seed),
        "queries": len(method_hits),
        "method_hit@10": float(np.mean(method_array)) if method_array.size else 0.0,
        "baseline_hit@10": float(np.mean(baseline_array)) if baseline_array.size else 0.0,
        "hit_delta_mean": hit_delta_mean,
        "hit_delta_ci_low": hit_delta_low,
        "hit_delta_ci_high": hit_delta_high,
        "method_only_hits": method_only,
        "baseline_only_hits": baseline_only,
        "hit_ties": ties,
        "mcnemar_p_two_sided": mcnemar_p,
        "evidence_recall_delta_mean": recall_delta_mean,
        "evidence_recall_delta_ci_low": recall_delta_low,
        "evidence_recall_delta_ci_high": recall_delta_high,
        "mrr_delta_mean": mrr_delta_mean,
        "mrr_delta_ci_low": mrr_delta_low,
        "mrr_delta_ci_high": mrr_delta_high,
        "ndcg_delta_mean": ndcg_delta_mean,
        "ndcg_delta_ci_low": ndcg_delta_low,
        "ndcg_delta_ci_high": ndcg_delta_high,
    }


def paired_summary(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["method"]), str(row["baseline"]))].append(row)
    summaries = []
    for (method, baseline), group in sorted(grouped.items()):
        summary: dict[str, object] = {
            "method": method,
            "baseline": baseline,
            "seeds": "|".join(str(row["seed"]) for row in group),
            "significant_mcnemar_seeds": sum(float(row["mcnemar_p_two_sided"]) < 0.05 for row in group),
        }
        for metric in (
            "hit_delta_mean",
            "evidence_recall_delta_mean",
            "mrr_delta_mean",
            "ndcg_delta_mean",
        ):
            average, deviation = mean_std([float(row[metric]) for row in group])
            summary[f"{metric}_mean"] = average
            summary[f"{metric}_std"] = deviation
        summaries.append(summary)
    return summaries


def method_config() -> dict[str, dict[str, str]]:
    return {
        "learned_full_frozen": {
            "train_mode": "full_multi_route",
            "test_mode": "full_multi_route",
            "feedback_mode": "trust_weighted",
            "kind": "learned",
        },
        "learned_gated_frozen": {
            "train_mode": "gated_cost_aware",
            "test_mode": "gated_cost_aware",
            "feedback_mode": "trust_weighted",
            "kind": "learned",
        },
        "static_nearest_full": {
            "test_mode": "static_nearest_ensemble",
            "feedback_mode": "none",
            "kind": "static",
        },
        "static_nearest_gated": {
            "test_mode": "static_nearest_gated",
            "feedback_mode": "none",
            "kind": "static",
        },
        "cold_no_feedback_full": {
            "test_mode": "full_multi_route",
            "feedback_mode": "none",
            "kind": "cold",
        },
        "cold_no_feedback_gated": {
            "test_mode": "gated_cost_aware",
            "feedback_mode": "none",
            "kind": "cold",
        },
    }


def common_run_args(args, *, seed: int, routing_mode: str, feedback_mode: str, epochs: int, artifacts, arm_rows, score_rows):
    return {
        "seed": seed,
        "routing_mode": routing_mode,
        "feedback_mode": feedback_mode,
        "reward_attribution": "final_fused",
        "confidence_mode": "value",
        "epochs": epochs,
        "top_k": 10,
        "ks": (1, 5, 10),
        "n_clusters": args.n_clusters,
        "context_dim": args.context_dim,
        "candidate_arms": args.candidate_arms,
        "alpha": args.alpha,
        "alpha_decay": args.alpha_decay,
        "alpha_min": args.alpha_min,
        "arm_neighbor_k": args.arm_neighbor_k,
        "arm_decay_sigma": args.arm_decay_sigma,
        "propagation_strength": args.propagation_strength,
        "feedback_k": args.feedback_k,
        "feedback_tau": args.feedback_tau,
        "feedback_weight": args.feedback_weight,
        "dense_depth": 100,
        "bm25_depth": 100,
        "cluster_depth": 100,
        "dense_weight": 2.0,
        "bm25_weight": 0.8,
        "cluster_weight": 0.8,
        "rrf_k": 60,
        "dense_floor_k": 5,
        "dense_lite_depth": 20,
        "bm25_lite_depth": 20,
        "dense_lite_weight": 0.8,
        "bm25_lite_weight": 0.5,
        "cluster_primary_weight": 2.0,
        "dense_lite_floor_k": 2,
        "high_confidence_threshold": 0.65,
        "mid_confidence_threshold": 0.35,
        "drift_threshold": 1.0,
        "reward_drop_threshold": 0.0,
        "confidence_feedback_floor": 8.0,
        "final_context_policy": "fixed_topk",
        "final_context_high_k": 5,
        "final_context_mid_k": 7,
        "high_trust_prob": 0.7,
        "high_trust": 1.0,
        "low_trust": 0.25,
        "high_accuracy": 0.9,
        "low_accuracy": 0.55,
        "window_size": 50,
        "epsilon_greedy_rate": 0.1,
        "shared_context_artifacts": artifacts,
        "dense_rankings_by_qid": args.dense_rankings_by_qid,
        "bm25_rankings_by_qid": args.bm25_rankings_by_qid,
        "cluster_retrieval_engine": "cached_exact_scores",
        "arm_row_indices": arm_rows,
        "query_corpus_scores": score_rows,
    }


def load_artifacts(args, corpus, queries, encoder):
    print(f"[{args.dataset}] loading retrieval artifacts for {len(corpus)} chunks and {len(queries)} queries", flush=True)
    if args.use_scale_store:
        corpus_embeddings, scale_store_info = routing.dense_baseline.load_corpus_embeddings_from_scale_store(
            corpus,
            canonical_name=args.scale_store_canonical_name,
            scale_store_dir=args.scale_store_dir,
        )
    else:
        corpus_embeddings, _ = routing.dense_baseline.encode_records_with_optional_cache(
            corpus,
            encoder,
            dataset=args.dataset,
            model_name=args.model,
            record_kind="corpus",
            batch_size=args.batch_size,
            embedding_cache_dir=args.embedding_cache_dir,
            use_embedding_cache=True,
        )
        scale_store_info = {"enabled": False}
    query_embeddings, _ = routing.dense_baseline.encode_records_with_optional_cache(
        queries,
        encoder,
        dataset=args.dataset,
        model_name=args.model,
        record_kind="queries",
        batch_size=args.batch_size,
        embedding_cache_dir=args.embedding_cache_dir,
        use_embedding_cache=True,
    )
    corpus_embedding_fingerprint = routing.large_scale_artifacts.embedding_array_fingerprint(corpus_embeddings)
    query_embedding_fingerprint = routing.large_scale_artifacts.embedding_array_fingerprint(query_embeddings)
    dense_rankings, dense_cache = routing.large_scale_artifacts.load_or_compute_dense_rankings(
        corpus,
        queries,
        corpus_embeddings,
        query_embeddings,
        dataset=args.dataset,
        model_name=args.model,
        depth=100,
        cache_dir=args.artifact_cache_dir,
        batch_size=args.batch_size,
        corpus_embedding_fingerprint=corpus_embedding_fingerprint,
        query_embedding_fingerprint=query_embedding_fingerprint,
    )
    bm25_rankings, bm25_cache = routing.large_scale_artifacts.load_or_compute_bm25_rankings(
        corpus,
        queries,
        dataset=args.dataset,
        depth=100,
        cache_dir=args.artifact_cache_dir,
    )
    score_rows, score_cache = routing.large_scale_artifacts.load_or_compute_query_corpus_scores(
        corpus,
        queries,
        corpus_embeddings,
        query_embeddings,
        dataset=args.dataset,
        model_name=args.model,
        cache_dir=args.artifact_cache_dir,
        corpus_embedding_fingerprint=corpus_embedding_fingerprint,
        query_embedding_fingerprint=query_embedding_fingerprint,
    )
    per_seed = {}
    for seed in args.seeds:
        artifacts, cache_info = routing.large_scale_artifacts.load_or_compute_context_clusters(
            corpus,
            queries,
            corpus_embeddings,
            query_embeddings,
            dataset=args.dataset,
            model_name=args.model,
            context_dim=args.context_dim,
            n_clusters=args.n_clusters,
            seed=seed,
            cache_dir=args.artifact_cache_dir,
            corpus_embedding_fingerprint=corpus_embedding_fingerprint,
            query_embedding_fingerprint=query_embedding_fingerprint,
        )
        per_seed[seed] = {
            "artifacts": artifacts,
            "arm_rows": routing.global_linucb.build_arm_row_indices(
                artifacts["arm_labels"], n_arms=len(artifacts["centroids"])
            ),
            "cache": cache_info,
        }
    return {
        "corpus_embeddings": corpus_embeddings,
        "query_embeddings": query_embeddings,
        "dense_rankings": dense_rankings,
        "bm25_rankings": bm25_rankings,
        "score_rows": score_rows,
        "per_seed": per_seed,
        "cache_metadata": {
            "scale_store": scale_store_info,
            "dense": dense_cache,
            "bm25": bm25_cache,
            "query_corpus_scores": score_cache,
        },
    }


def sliced_artifacts(artifacts: Mapping[str, np.ndarray], indices: Sequence[int]) -> dict[str, np.ndarray]:
    return {
        "corpus_context": np.asarray(artifacts["corpus_context"], dtype=np.float32),
        "query_context": subset_matrix(np.asarray(artifacts["query_context"]), indices),
        "arm_labels": np.asarray(artifacts["arm_labels"], dtype=np.int32),
        "centroids": np.asarray(artifacts["centroids"], dtype=np.float32),
    }


def run(args):
    corpus = routing.global_linucb.load_json_list(args.data_dir / f"{args.dataset}_corpus.json")
    queries = routing.global_linucb.load_json_list(args.data_dir / f"{args.dataset}_queries.json")
    print(f"[{args.dataset}] loading encoder and frozen protocol inputs", flush=True)
    encoder = routing.load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)
    loaded = load_artifacts(args, corpus, queries, encoder)
    args.dense_rankings_by_qid = loaded["dense_rankings"]
    args.bm25_rankings_by_qid = loaded["bm25_rankings"]
    assignments, folds = crossfit.query_folds(queries)
    query_indices = {qid(query): index for index, query in enumerate(queries)}
    all_ids = set(query_indices)
    config = method_config()
    signature = checkpoint_signature(args)
    checkpoints = checkpoint_directory(args.output_prefix)
    checkpoints.mkdir(parents=True, exist_ok=True)
    rankings_by_method: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(dict)
    fold_rows: list[dict[str, object]] = []

    for fold_index, test_queries in enumerate(folds):
        print(
            f"[{args.dataset}] fold {fold_index + 1}/{len(folds)}: "
            f"history={len(queries) - len(test_queries)} test={len(test_queries)}",
            flush=True,
        )
        test_ids = {qid(query) for query in test_queries}
        history_queries = [query for query in queries if qid(query) not in test_ids]
        history_indices = [query_indices[qid(query)] for query in history_queries]
        test_indices = [query_indices[qid(query)] for query in test_queries]
        if test_ids & {qid(query) for query in history_queries}:
            raise AssertionError("history/test query overlap")
        checkpoint_path = checkpoints / f"fold{fold_index}.json"
        fold_rankings: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(dict)
        fold_rows_current: list[dict[str, object]] = []
        if checkpoint_path.exists():
            restored_rows, restored_rankings = load_fold_checkpoint(
                checkpoint_path,
                signature=signature,
                expected_query_ids=test_ids,
            )
            merge_rankings(fold_rankings, restored_rankings)
            fold_rows_current.extend(restored_rows)
            print(
                f"[{args.dataset}] fold {fold_index + 1}/{len(folds)} restored "
                f"{len(restored_rows)} method checkpoints",
                flush=True,
            )

        completed_pairs = {(str(row["method"]), str(row["seed"])) for row in fold_rows_current}
        ranking_pairs = {
            (str(method), str(seed))
            for method, by_seed in fold_rankings.items()
            for seed in by_seed
        }
        if completed_pairs != ranking_pairs:
            raise AssertionError(f"checkpoint row/ranking mismatch in fold {fold_index}")

        for seed in args.seeds:
            pending_methods = [method for method in METHODS if (method, str(seed)) not in completed_pairs]
            if not pending_methods:
                continue
            seed_data = loaded["per_seed"][seed]
            history_artifacts = sliced_artifacts(seed_data["artifacts"], history_indices)
            test_artifacts = sliced_artifacts(seed_data["artifacts"], test_indices)
            history_embeddings = subset_matrix(loaded["query_embeddings"], history_indices)
            test_embeddings = subset_matrix(loaded["query_embeddings"], test_indices)
            history_scores = ScoreRowSubset(loaded["score_rows"], history_indices)
            test_scores = ScoreRowSubset(loaded["score_rows"], test_indices)

            for method in METHODS:
                if (method, str(seed)) in completed_pairs:
                    continue
                setting = config[method]
                initial_state = None
                history_updates = 0
                if setting["kind"] == "learned":
                    print(
                        f"[{args.dataset}] fold {fold_index + 1}/{len(folds)} "
                        f"seed={seed} training {method}",
                        flush=True,
                    )
                    train_args = common_run_args(
                        args,
                        seed=seed,
                        routing_mode=setting["train_mode"],
                        feedback_mode=setting["feedback_mode"],
                        epochs=args.history_epochs,
                        artifacts=history_artifacts,
                        arm_rows=seed_data["arm_rows"],
                        score_rows=history_scores,
                    )
                    trained = routing.run_prequential_seed(
                        corpus,
                        history_queries,
                        loaded["corpus_embeddings"],
                        history_embeddings,
                        return_state=True,
                        **train_args,
                    )
                    initial_state = copy.deepcopy(trained["runtime_state"])
                    history_updates = int(initial_state["policy"].total_feedback)

                test_args = common_run_args(
                    args,
                    seed=seed,
                    routing_mode=setting["test_mode"],
                    feedback_mode=setting["feedback_mode"],
                    epochs=1,
                    artifacts=test_artifacts,
                    arm_rows=seed_data["arm_rows"],
                    score_rows=test_scores,
                )
                result = routing.run_prequential_seed(
                    corpus,
                    test_queries,
                    loaded["corpus_embeddings"],
                    test_embeddings,
                    initial_state=initial_state,
                    freeze_updates=True,
                    **test_args,
                )
                if initial_state is not None and int(initial_state["policy"].total_feedback) != history_updates:
                    raise AssertionError("held-out evaluation changed frozen policy feedback count")
                result_rankings = {key: list(value) for key, value in result["rankings"].items()}
                if set(result_rankings) != test_ids:
                    raise AssertionError("held-out rankings do not cover the test fold")
                fold_rankings[method].setdefault(str(seed), {}).update(result_rankings)
                values = scalar_metrics(result["metrics"])
                fold_rows_current.append(
                    {
                        "dataset": args.dataset,
                        "fold": fold_index,
                        "method": method,
                        "seed": seed,
                        "history_queries": len(history_queries),
                        "test_queries": len(test_queries),
                        "history_epochs": args.history_epochs if setting["kind"] == "learned" else 0,
                        "history_feedback_updates": history_updates,
                        "test_feedback_updates": 0,
                        **values,
                    }
                )
                completed_pairs.add((method, str(seed)))
                write_json(
                    checkpoint_path,
                    {
                        "signature": signature,
                        "fold": fold_index,
                        "complete": False,
                        "test_query_ids": sorted(test_ids),
                        "fold_rows": fold_rows_current,
                        "rankings": fold_rankings,
                    },
                )
                print(
                    f"[{args.dataset}] fold {fold_index + 1}/{len(folds)} "
                    f"seed={seed} method={method} checkpointed",
                    flush=True,
                )

        expected_pairs = {(method, str(seed)) for method in METHODS for seed in args.seeds}
        if completed_pairs != expected_pairs:
            raise AssertionError(f"incomplete fold checkpoint after execution: {fold_index}")
        write_json(
            checkpoint_path,
            {
                "signature": signature,
                "fold": fold_index,
                "complete": True,
                "test_query_ids": sorted(test_ids),
                "fold_rows": fold_rows_current,
                "rankings": fold_rankings,
            },
        )
        merge_rankings(rankings_by_method, fold_rankings)
        fold_rows.extend(fold_rows_current)
        print(f"[{args.dataset}] fold {fold_index + 1}/{len(folds)} checkpointed", flush=True)

    dense_rankings = {qid(query): list(loaded["dense_rankings"].get(qid(query), [])[:10]) for query in queries}
    if set(dense_rankings) != all_ids:
        raise AssertionError("dense rankings do not cover every query")
    dense_metrics = routing.retrieval_metrics.evaluate_rankings(queries, dense_rankings, ks=(1, 5, 10))
    seed_rows: list[dict[str, object]] = []
    for method in METHODS:
        for seed in args.seeds:
            method_rankings = rankings_by_method[method].get(str(seed), {})
            if set(method_rankings) != all_ids:
                raise AssertionError(f"incomplete OOF rankings for {method} seed={seed}")
            row = seed_summary(method, seed, method_rankings, queries)
            row["hit_delta_pp_vs_dense"] = (float(row["hit@10"]) - float(dense_metrics["hit@10"])) * 100.0
            seed_rows.append(row)

    summary_rows: list[dict[str, object]] = []
    by_method: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in seed_rows:
        by_method[str(row["method"])].append(row)
    for method in METHODS:
        rows = by_method[method]
        summary = {"method": method, "seeds": "|".join(str(seed) for seed in args.seeds)}
        for metric in ("hit@10", "evidence_recall@10", "mrr@10", "ndcg@10", "hit_delta_pp_vs_dense"):
            average, deviation = mean_std([float(row[metric]) for row in rows])
            summary[f"{metric}_mean"] = average
            summary[f"{metric}_std"] = deviation
        summary_rows.append(summary)
    summary_rows.append(
        {
            "method": "dense",
            "seeds": "",
            "hit@10_mean": float(dense_metrics["hit@10"]),
            "hit@10_std": 0.0,
            "evidence_recall@10_mean": float(dense_metrics["evidence_recall@10"]),
            "evidence_recall@10_std": 0.0,
            "mrr@10_mean": float(dense_metrics["mrr@10"]),
            "mrr@10_std": 0.0,
            "ndcg@10_mean": float(dense_metrics["ndcg@10"]),
            "ndcg@10_std": 0.0,
            "hit_delta_pp_vs_dense_mean": 0.0,
            "hit_delta_pp_vs_dense_std": 0.0,
        }
    )
    paired_rows: list[dict[str, object]] = []
    for comparison_index, (method, baseline) in enumerate(PAIRWISE_COMPARISONS):
        for seed_index, seed in enumerate(args.seeds):
            method_rankings = rankings_by_method[method].get(str(seed), {})
            baseline_rankings = (
                dense_rankings
                if baseline == "dense"
                else rankings_by_method[baseline].get(str(seed), {})
            )
            if set(method_rankings) != all_ids or set(baseline_rankings) != all_ids:
                raise AssertionError(f"incomplete paired rankings for {method} vs {baseline} seed={seed}")
            paired_rows.append(
                paired_comparison(
                    queries=queries,
                    method=method,
                    baseline=baseline,
                    seed=seed,
                    method_rankings=method_rankings,
                    baseline_rankings=baseline_rankings,
                    n_bootstrap=args.bootstrap_samples,
                    bootstrap_seed=args.bootstrap_seed + comparison_index * 100 + seed_index * 10,
                )
            )
    paired_summaries = paired_summary(paired_rows)
    protocol = {
        "dataset": args.dataset,
        "fold_salt": crossfit.FOLD_SALT,
        "folds": len(folds),
        "history_epochs": args.history_epochs,
        "route_seeds": list(args.seeds),
        "feedback_train_mode": "trust_weighted",
        "test_feedback_rule": "rank_test_queries_once_with_freeze_updates_true",
        "main_boundary": "held-out query labels cannot update policy, feedback memory, route statistics, or reward history",
        "cluster_retrieval_engine": "cached_exact_scores",
        "paired_comparisons": [f"{method}_vs_{baseline}" for method, baseline in PAIRWISE_COMPARISONS],
        "bootstrap_samples": args.bootstrap_samples,
        "bootstrap_seed": args.bootstrap_seed,
    }
    return {
        "protocol": protocol,
        "cache_metadata": loaded["cache_metadata"],
        "fold_assignments": assignments,
        "fold_rows": fold_rows,
        "seed_rows": seed_rows,
        "summary_rows": summary_rows,
        "paired_rows": paired_rows,
        "paired_summaries": paired_summaries,
        "rankings": {method: dict(rows) for method, rows in rankings_by_method.items()},
        "dense_rankings": dense_rankings,
    }


def write_markdown(path: Path, result: Mapping[str, object]) -> None:
    rows = result["summary_rows"]
    paired_rows = result["paired_rows"]
    paired_summaries = result["paired_summaries"]
    lines = [
        "# Task70 Frozen-Policy Unseen-Query Evaluation",
        "",
        "Each held-out query is ranked once after training on the other four canonical folds. During test evaluation, no held-out label can update LinUCB parameters, local feedback memory, route statistics, or reward history.",
        "",
        "## Out-of-Fold Retrieval",
        "",
        "| Method | Hit@10 | Delta vs Dense | EvidenceRecall@10 | MRR@10 | nDCG@10 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        hit = f"{float(row['hit@10_mean']):.4f}"
        delta = f"{float(row['hit_delta_pp_vs_dense_mean']):+.2f} pp"
        evidence = f"{float(row['evidence_recall@10_mean']):.4f}"
        mrr = f"{float(row['mrr@10_mean']):.4f}"
        ndcg = f"{float(row['ndcg@10_mean']):.4f}"
        lines.append(f"| {row['method']} | {hit} | {delta} | {evidence} | {mrr} | {ndcg} |")
    lines.extend([
        "",
        "## Paired Frozen-Query Comparisons",
        "",
        "Each row is paired by the same unseen query population within one route seed. Bootstrap intervals apply to query-level deltas; McNemar tests apply to paired Hit@10 outcomes.",
        "",
        "| Method | Baseline | Seeds | Mean Hit delta | Seed SD | Significant McNemar seeds |",
        "|---|---|---|---:|---:|---:|",
    ])
    for row in paired_summaries:
        lines.append(
            f"| {row['method']} | {row['baseline']} | {row['seeds']} | "
            f"{float(row['hit_delta_mean_mean']) * 100.0:+.2f} pp | "
            f"{float(row['hit_delta_mean_std']) * 100.0:.2f} pp | "
            f"{int(row['significant_mcnemar_seeds'])}/3 |"
        )
    lines.extend([
        "",
        "| Method | Baseline | Seed | Hit delta 95% CI | Wins / Losses | McNemar p |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in paired_rows:
        lines.append(
            f"| {row['method']} | {row['baseline']} | {row['seed']} | "
            f"[{float(row['hit_delta_ci_low']) * 100.0:+.2f}, {float(row['hit_delta_ci_high']) * 100.0:+.2f}] pp | "
            f"{int(row['method_only_hits'])} / {int(row['baseline_only_hits'])} | "
            f"{float(row['mcnemar_p_two_sided']):.4g} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Guardrail",
            "",
            "This evaluates route-policy transfer to unseen queries. It is distinct from repeated-query prequential adaptation and does not by itself establish final-context token savings, human-feedback effectiveness, or universal non-inferiority. Paired statistics compare retrieval outcomes only and do not turn a non-significant result into proof of equivalence.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="lotte_technology_search_100k")
    parser.add_argument("--data-dir", type=Path, default=DATA / "processed")
    parser.add_argument("--output-prefix", type=Path, default=RESULTS / "task70_frozen_policy_technology_100k")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--embedding-cache-dir", type=Path, default=routing.DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--artifact-cache-dir", type=Path, default=routing.DEFAULT_ARTIFACT_CACHE_DIR)
    parser.add_argument("--scale-store-dir", type=Path, default=routing.DEFAULT_SCALE_STORE_DIR)
    parser.add_argument("--scale-store-canonical-name", default="lotte_technology_search")
    parser.add_argument(
        "--use-scale-store",
        action="store_true",
        help="Load precomputed corpus embeddings from a canonical scale store when one exists",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seeds", default="13,17,19")
    parser.add_argument("--history-epochs", type=int, default=8)
    parser.add_argument("--bootstrap-samples", type=int, default=BOOTSTRAP_SAMPLES)
    parser.add_argument("--bootstrap-seed", type=int, default=700000)
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
    args = parser.parse_args()
    args.seeds = tuple(int(part.strip()) for part in args.seeds.split(",") if part.strip())
    for field in ("data_dir", "output_prefix", "embedding_cache_dir", "artifact_cache_dir", "scale_store_dir"):
        value = getattr(args, field)
        if not value.is_absolute():
            setattr(args, field, (ROOT / value).resolve())
    if args.history_epochs <= 0:
        raise ValueError("history epochs must be positive")
    if args.bootstrap_samples <= 0:
        raise ValueError("bootstrap samples must be positive")

    result = run(args)
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_prefix.with_suffix(".folds.csv"), result["fold_rows"])
    write_csv(args.output_prefix.with_suffix(".seeds.csv"), result["seed_rows"])
    write_csv(args.output_prefix.with_suffix(".summary.csv"), result["summary_rows"])
    write_csv(args.output_prefix.with_suffix(".paired.csv"), result["paired_rows"])
    write_csv(args.output_prefix.with_suffix(".paired_summary.csv"), result["paired_summaries"])
    write_json(args.output_prefix.with_suffix(".json"), result)
    write_markdown(args.output_prefix.with_suffix(".md"), result)
    print(json.dumps(result["summary_rows"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
