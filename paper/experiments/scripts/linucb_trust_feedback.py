#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 15: trust-weighted feedback LinUCB experiment.

Task 15 tests whether feedback can make the LinUCB retrieval policy improve
over repeated interactions, and whether trust-weighted noisy feedback is more
robust than equal-weight noisy feedback.

The retrieval surface stays close to Task 13.5:

* global dense retrieval remains a stable recall floor;
* global BM25 provides lexical coverage;
* LinUCB selects cluster-local dense arms;
* weighted RRF fuses the three routes.

The new variable is the feedback signal used to update cluster arms:

* ``none``: no online update;
* ``oracle``: GT-derived reward without user noise;
* ``equal_noisy``: simulated user feedback with equal update weight;
* ``trust_weighted``: the same noisy feedback model, but update weight and
  local feedback memory are scaled by simulated user trust.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


linucb_soft = _load_script_module("linucb_soft_routing", SCRIPT_DIR / "linucb_soft_routing.py")
global_linucb = linucb_soft.global_linucb
manifold_linucb = linucb_soft.manifold_linucb
bm25_baseline = linucb_soft.bm25_baseline
dense_baseline = linucb_soft.dense_baseline
experiment_guardrails = linucb_soft.experiment_guardrails
retrieval_metrics = linucb_soft.retrieval_metrics

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DATASETS = global_linucb.DEFAULT_DATASETS
DEFAULT_MODEL = global_linucb.DEFAULT_MODEL
FEEDBACK_MODES = ("none", "oracle", "equal_noisy", "trust_weighted")


class FeedbackObservation(NamedTuple):
    true_reward: float
    observed_reward: float
    trust: float
    user_group: str
    aligned: bool


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parse_modes(value: str) -> tuple[str, ...]:
    modes = tuple(part.strip() for part in value.split(",") if part.strip())
    invalid = [mode for mode in modes if mode not in FEEDBACK_MODES]
    if invalid:
        raise ValueError(f"Unsupported feedback modes: {invalid}. Choices: {FEEDBACK_MODES}")
    return modes


def _slug_part(value: object) -> str:
    raw = str(value or "na").strip().lower()
    chars = [char if char.isalnum() else "-" for char in raw]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or "na"


def build_artifact_slug(dataset: str, run_metadata: Mapping[str, object]) -> str:
    return "_".join([
        _slug_part(dataset),
        _slug_part(run_metadata.get("scope", "full")),
        _slug_part(run_metadata.get("query_split", "all")),
        f"corpus-{_slug_part(run_metadata.get('corpus_scope', 'full'))}",
        f"q{_slug_part(run_metadata.get('num_queries', 'all'))}",
    ])


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
    return linucb_soft._has_hit(ranking, ground_truth, k=k)


def simulate_user_feedback(
    true_reward: float,
    rng: np.random.Generator,
    *,
    mode: str,
    high_trust_prob: float,
    high_trust: float,
    low_trust: float,
    high_accuracy: float,
    low_accuracy: float,
) -> FeedbackObservation:
    """Return a simulated feedback observation for one selected arm."""
    if mode == "none":
        return FeedbackObservation(true_reward=true_reward, observed_reward=0.0, trust=0.0, user_group="none", aligned=True)
    if mode == "oracle":
        return FeedbackObservation(true_reward=true_reward, observed_reward=true_reward, trust=1.0, user_group="oracle", aligned=True)

    if not 0.0 <= high_trust_prob <= 1.0:
        raise ValueError(f"high_trust_prob must be in [0, 1], got {high_trust_prob}")
    is_high = bool(rng.random() < high_trust_prob)
    trust = float(high_trust if is_high else low_trust)
    accuracy = float(high_accuracy if is_high else low_accuracy)
    if not 0.0 <= accuracy <= 1.0:
        raise ValueError(f"feedback accuracy must be in [0, 1], got {accuracy}")

    true_binary = 1.0 if true_reward > 0 else 0.0
    aligned = bool(rng.random() < accuracy)
    observed = true_binary if aligned else 1.0 - true_binary
    return FeedbackObservation(
        true_reward=true_binary,
        observed_reward=float(observed),
        trust=trust,
        user_group="high_trust" if is_high else "low_trust",
        aligned=aligned,
    )


def update_weight_for_mode(mode: str, observation: FeedbackObservation) -> float:
    if mode == "none":
        return 0.0
    if mode in {"oracle", "equal_noisy"}:
        return 1.0
    if mode == "trust_weighted":
        return float(observation.trust)
    raise ValueError(f"Unsupported feedback mode: {mode}")


def memory_reward_for_mode(mode: str, observation: FeedbackObservation) -> float:
    if mode == "trust_weighted":
        return float(observation.trust * observation.observed_reward)
    if mode == "none":
        return 0.0
    return float(observation.observed_reward)


def _window_mean(values: Sequence[float], window: int, *, tail: bool) -> float:
    if not values:
        return 0.0
    if window <= 0:
        raise ValueError(f"window must be positive, got {window}")
    sample = list(values[-window:] if tail else values[:window])
    return float(np.mean(sample)) if sample else 0.0


def build_source_rankings(
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    chunk_ids: Sequence[str],
    bm25,
    *,
    dense_depth: int,
    bm25_depth: int,
) -> tuple[List[List[str]], List[List[str]]]:
    dense_rankings: List[List[str]] = []
    bm25_rankings: List[List[str]] = []
    for query_idx, query in enumerate(queries):
        dense_rankings.append(linucb_soft.top_dense_ranking(
            query_embeddings[int(query_idx)],
            corpus_embeddings,
            chunk_ids,
            depth=dense_depth,
        ))
        bm25_rankings.append(linucb_soft.top_bm25_ranking(
            str(query.get("text", "")),
            bm25,
            chunk_ids,
            depth=bm25_depth,
        ))
    return dense_rankings, bm25_rankings


def run_prequential_seed(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    seed: int,
    feedback_mode: str,
    epochs: int,
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
    high_trust_prob: float,
    high_trust: float,
    low_trust: float,
    high_accuracy: float,
    low_accuracy: float,
    window_size: int,
) -> Dict[str, object]:
    if feedback_mode not in FEEDBACK_MODES:
        raise ValueError(f"Unsupported feedback_mode: {feedback_mode}")
    if epochs <= 0:
        raise ValueError(f"epochs must be positive, got {epochs}")
    if min(top_k, dense_depth, bm25_depth, cluster_depth) <= 0:
        raise ValueError("top_k and source depths must be positive")
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
    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    arm_labels_by_chunk = {chunk_id: int(label) for chunk_id, label in zip(chunk_ids, arm_labels)}
    tokenized_corpus = [bm25_baseline.tokenize(str(chunk.get("text", ""))) for chunk in corpus]
    bm25 = bm25_baseline.SparseBM25(tokenized_corpus)
    dense_rankings, bm25_rankings = build_source_rankings(
        queries,
        corpus_embeddings,
        query_embeddings,
        chunk_ids,
        bm25,
        dense_depth=dense_depth,
        bm25_depth=bm25_depth,
    )

    rankings: Dict[str, List[str]] = {}
    feedback_contexts: List[np.ndarray] = []
    feedback_arm_rewards: List[Dict[int, float]] = []
    total_update_weight = 0.0
    cross_arm_update_weight = 0.0
    propagated_updates = 0

    true_rewards: List[float] = []
    observed_rewards: List[float] = []
    memory_rewards: List[float] = []
    user_trusts: List[float] = []
    feedback_alignment: List[float] = []
    selected_cluster_hits: List[float] = []
    cluster_local_hits: List[float] = []
    soft_hits: List[float] = []
    dense_hits: List[float] = []
    bm25_hits: List[float] = []
    local_boost_norms: List[float] = []
    selected_candidate_counts: List[int] = []
    union_candidate_counts: List[int] = []
    epoch_rows: List[Dict[str, float]] = []

    for epoch in range(epochs):
        epoch_indices = np.arange(len(queries))
        rng.shuffle(epoch_indices)
        epoch_true_rewards: List[float] = []
        epoch_observed_rewards: List[float] = []
        epoch_memory_rewards: List[float] = []
        epoch_user_trusts: List[float] = []
        epoch_feedback_alignment: List[float] = []
        epoch_selected_cluster_hits: List[float] = []
        epoch_cluster_local_hits: List[float] = []
        epoch_soft_hits: List[float] = []
        epoch_dense_hits: List[float] = []
        epoch_bm25_hits: List[float] = []

        for query_idx in epoch_indices:
            query_idx = int(query_idx)
            query = queries[query_idx]
            qid = _query_id(query)
            context = query_context[query_idx]
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
            selected_candidate_counts.append(linucb_soft.selected_candidate_count(arm_labels, selected_arms))

            dense_ranking = dense_rankings[query_idx]
            bm25_ranking = bm25_rankings[query_idx]
            cluster_ranking = global_linucb.retrieve_from_arms(
                query_embeddings[query_idx],
                corpus_embeddings,
                chunk_ids,
                arm_labels,
                selected_arms,
                top_k=cluster_depth,
            )
            union_candidate_counts.append(len(set(dense_ranking) | set(bm25_ranking) | set(cluster_ranking)))
            ranking = linucb_soft.weighted_reciprocal_rank_fusion(
                (
                    (dense_ranking, dense_weight),
                    (bm25_ranking, bm25_weight),
                    (cluster_ranking, cluster_weight),
                ),
                rrf_k=rrf_k,
                top_k=top_k,
            )
            ranking = linucb_soft.apply_dense_floor(
                ranking,
                dense_ranking,
                dense_floor_k=dense_floor_k,
                top_k=top_k,
            )
            rankings[qid] = ranking

            gt = _ground_truth(query)
            selected_cluster_hit = linucb_soft.gt_cluster_hit(selected_arms, gt, arm_labels_by_chunk)
            cluster_hit = _has_hit(cluster_ranking, gt, k=top_k)
            dense_hit = _has_hit(dense_ranking, gt, k=top_k)
            bm25_hit = _has_hit(bm25_ranking, gt, k=top_k)
            soft_hit = _has_hit(ranking, gt, k=top_k)

            arm_memory_rewards: Dict[int, float] = {}
            selected_true_rewards: List[float] = []
            selected_observed_rewards: List[float] = []
            selected_memory_rewards: List[float] = []
            selected_user_trusts: List[float] = []
            selected_alignment: List[float] = []
            for source_arm in selected_arms:
                true_reward = global_linucb._arm_reward(ranking, gt, source_arm, arm_labels_by_chunk)
                observation = simulate_user_feedback(
                    true_reward,
                    rng,
                    mode=feedback_mode,
                    high_trust_prob=high_trust_prob,
                    high_trust=high_trust,
                    low_trust=low_trust,
                    high_accuracy=high_accuracy,
                    low_accuracy=low_accuracy,
                )
                update_weight = update_weight_for_mode(feedback_mode, observation)
                memory_reward = memory_reward_for_mode(feedback_mode, observation)
                arm_memory_rewards[int(source_arm)] = memory_reward
                selected_true_rewards.append(float(true_reward))
                selected_observed_rewards.append(float(observation.observed_reward))
                selected_memory_rewards.append(float(memory_reward))
                selected_user_trusts.append(float(observation.trust))
                selected_alignment.append(1.0 if observation.aligned else 0.0)
                if update_weight > 0:
                    for target_arm, propagation_weight in manifold_linucb.arm_propagation_weights(
                        centroids,
                        source_arm,
                        sigma=arm_decay_sigma,
                        neighbor_k=arm_neighbor_k,
                        propagation_strength=propagation_strength,
                    ):
                        weight = float(update_weight * propagation_weight)
                        policy.update(target_arm, context, observation.observed_reward, weight=weight)
                        total_update_weight += weight
                        if target_arm != source_arm:
                            cross_arm_update_weight += weight
                            propagated_updates += 1

            if feedback_mode != "none":
                feedback_contexts.append(context.copy())
                feedback_arm_rewards.append(arm_memory_rewards)

            interaction_true = max(selected_true_rewards) if selected_true_rewards else 0.0
            interaction_observed = max(selected_observed_rewards) if selected_observed_rewards else 0.0
            interaction_memory = max(selected_memory_rewards) if selected_memory_rewards else 0.0
            interaction_trust = float(np.mean(selected_user_trusts)) if selected_user_trusts else 0.0
            interaction_alignment = float(np.mean(selected_alignment)) if selected_alignment else 1.0

            for target, value in (
                (true_rewards, interaction_true),
                (observed_rewards, interaction_observed),
                (memory_rewards, interaction_memory),
                (user_trusts, interaction_trust),
                (feedback_alignment, interaction_alignment),
                (selected_cluster_hits, float(selected_cluster_hit)),
                (cluster_local_hits, float(cluster_hit)),
                (soft_hits, float(soft_hit)),
                (dense_hits, float(dense_hit)),
                (bm25_hits, float(bm25_hit)),
                (epoch_true_rewards, interaction_true),
                (epoch_observed_rewards, interaction_observed),
                (epoch_memory_rewards, interaction_memory),
                (epoch_user_trusts, interaction_trust),
                (epoch_feedback_alignment, interaction_alignment),
                (epoch_selected_cluster_hits, float(selected_cluster_hit)),
                (epoch_cluster_local_hits, float(cluster_hit)),
                (epoch_soft_hits, float(soft_hit)),
                (epoch_dense_hits, float(dense_hit)),
                (epoch_bm25_hits, float(bm25_hit)),
            ):
                target.append(float(value))

        epoch_rows.append({
            "epoch": float(epoch + 1),
            "true_reward": float(np.mean(epoch_true_rewards)) if epoch_true_rewards else 0.0,
            "observed_reward": float(np.mean(epoch_observed_rewards)) if epoch_observed_rewards else 0.0,
            "memory_reward": float(np.mean(epoch_memory_rewards)) if epoch_memory_rewards else 0.0,
            "user_trust": float(np.mean(epoch_user_trusts)) if epoch_user_trusts else 0.0,
            "feedback_alignment": float(np.mean(epoch_feedback_alignment)) if epoch_feedback_alignment else 0.0,
            "selected_cluster_hit_rate": float(np.mean(epoch_selected_cluster_hits)) if epoch_selected_cluster_hits else 0.0,
            "cluster_local_hit_rate": float(np.mean(epoch_cluster_local_hits)) if epoch_cluster_local_hits else 0.0,
            "soft_hit_rate": float(np.mean(epoch_soft_hits)) if epoch_soft_hits else 0.0,
            "dense_hit_rate": float(np.mean(epoch_dense_hits)) if epoch_dense_hits else 0.0,
            "bm25_hit_rate": float(np.mean(epoch_bm25_hits)) if epoch_bm25_hits else 0.0,
        })

    metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    first_epoch = epoch_rows[0] if epoch_rows else {}
    last_epoch = epoch_rows[-1] if epoch_rows else {}
    first_window_true = _window_mean(true_rewards, window_size, tail=False)
    last_window_true = _window_mean(true_rewards, window_size, tail=True)
    first_window_cluster = _window_mean(selected_cluster_hits, window_size, tail=False)
    last_window_cluster = _window_mean(selected_cluster_hits, window_size, tail=True)
    first_window_soft = _window_mean(soft_hits, window_size, tail=False)
    last_window_soft = _window_mean(soft_hits, window_size, tail=True)

    metrics.update({
        "seed": seed,
        "feedback_mode": feedback_mode,
        "epochs": epochs,
        "num_interactions": int(len(true_rewards)),
        "avg_true_feedback_reward": float(np.mean(true_rewards)) if true_rewards else 0.0,
        "avg_observed_feedback_reward": float(np.mean(observed_rewards)) if observed_rewards else 0.0,
        "avg_memory_feedback_reward": float(np.mean(memory_rewards)) if memory_rewards else 0.0,
        "avg_user_trust": float(np.mean(user_trusts)) if user_trusts else 0.0,
        "feedback_alignment_rate": float(np.mean(feedback_alignment)) if feedback_alignment else 0.0,
        "avg_local_boost_norm": float(np.mean(local_boost_norms)) if local_boost_norms else 0.0,
        "avg_selected_candidate_chunks": float(np.mean(selected_candidate_counts)) if selected_candidate_counts else 0.0,
        "avg_union_candidate_chunks": float(np.mean(union_candidate_counts)) if union_candidate_counts else 0.0,
        "selected_cluster_hit_rate": float(np.mean(selected_cluster_hits)) if selected_cluster_hits else 0.0,
        "cluster_local_hit_rate": float(np.mean(cluster_local_hits)) if cluster_local_hits else 0.0,
        "dense_fallback_hit_rate": float(np.mean(dense_hits)) if dense_hits else 0.0,
        "bm25_fallback_hit_rate": float(np.mean(bm25_hits)) if bm25_hits else 0.0,
        "soft_fused_hit_rate": float(np.mean(soft_hits)) if soft_hits else 0.0,
        "first_epoch_true_reward": float(first_epoch.get("true_reward", 0.0)),
        "last_epoch_true_reward": float(last_epoch.get("true_reward", 0.0)),
        "epoch_true_reward_gain": float(last_epoch.get("true_reward", 0.0) - first_epoch.get("true_reward", 0.0)),
        "first_epoch_selected_cluster_hit_rate": float(first_epoch.get("selected_cluster_hit_rate", 0.0)),
        "last_epoch_selected_cluster_hit_rate": float(last_epoch.get("selected_cluster_hit_rate", 0.0)),
        "epoch_selected_cluster_hit_gain": float(
            last_epoch.get("selected_cluster_hit_rate", 0.0) - first_epoch.get("selected_cluster_hit_rate", 0.0)
        ),
        "first_epoch_soft_hit_rate": float(first_epoch.get("soft_hit_rate", 0.0)),
        "last_epoch_soft_hit_rate": float(last_epoch.get("soft_hit_rate", 0.0)),
        "epoch_soft_hit_gain": float(last_epoch.get("soft_hit_rate", 0.0) - first_epoch.get("soft_hit_rate", 0.0)),
        "first_window_true_reward": first_window_true,
        "last_window_true_reward": last_window_true,
        "window_true_reward_gain": float(last_window_true - first_window_true),
        "first_window_selected_cluster_hit_rate": first_window_cluster,
        "last_window_selected_cluster_hit_rate": last_window_cluster,
        "window_selected_cluster_hit_gain": float(last_window_cluster - first_window_cluster),
        "first_window_soft_hit_rate": first_window_soft,
        "last_window_soft_hit_rate": last_window_soft,
        "window_soft_hit_gain": float(last_window_soft - first_window_soft),
        "final_effective_alpha": float(policy.effective_alpha),
        "n_effective_arms": n_effective_arms,
        "total_feedback_updates": int(policy.total_feedback),
        "total_update_weight": float(total_update_weight),
        "cross_arm_update_weight": float(cross_arm_update_weight),
        "propagated_updates": int(propagated_updates),
        "epoch_metrics": epoch_rows,
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
    feedback_modes: Sequence[str],
    top_k: int,
    ks: Sequence[int],
    batch_size: int,
    seeds: Sequence[int],
    epochs: int,
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
    high_trust_prob: float,
    high_trust: float,
    low_trust: float,
    high_accuracy: float,
    low_accuracy: float,
    window_size: int,
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
) -> List[Dict[str, object]]:
    corpus_all = global_linucb.load_json_list(data_dir / f"{dataset}_corpus.json")
    queries_all = global_linucb.load_json_list(data_dir / f"{dataset}_queries.json")
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
    run_metadata = {
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
        "num_queries": len(queries),
    }
    artifact_slug = build_artifact_slug(dataset, run_metadata)

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

    rows: List[Dict[str, object]] = []
    all_rankings: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
    for feedback_mode in feedback_modes:
        seed_results = []
        for seed in seeds:
            seed_results.append(run_prequential_seed(
                corpus,
                queries,
                corpus_embeddings,
                query_embeddings,
                seed=seed,
                feedback_mode=feedback_mode,
                epochs=epochs,
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
                high_trust_prob=high_trust_prob,
                high_trust=high_trust,
                low_trust=low_trust,
                high_accuracy=high_accuracy,
                low_accuracy=low_accuracy,
                window_size=window_size,
            ))

        elapsed_sec = time.perf_counter() - start
        per_seed_metrics = [result["metrics"] for result in seed_results]
        representative = per_seed_metrics[0]
        aggregated = aggregate_seed_metrics(per_seed_metrics)
        metadata = {
            "dataset": dataset,
            "method": f"linucb_trust_{feedback_mode}",
            "model": model_name,
            "protocol": "prequential_repeated_feedback",
            "feedback_mode": feedback_mode,
            "feedback_source": "simulated_user_feedback_from_gt_reward",
            "online_learning_scope": "trust_weighted_soft_routing_feedback",
            "manifold_neighbor_engine": "cpu_exact_numpy",
            "fusion": "weighted_rrf",
            "top_k": top_k,
            "ks": list(ks),
            "batch_size": batch_size,
            "seeds": list(seeds),
            "epochs": epochs,
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
            "high_trust_prob": high_trust_prob,
            "high_trust": high_trust,
            "low_trust": low_trust,
            "high_accuracy": high_accuracy,
            "low_accuracy": low_accuracy,
            "window_size": window_size,
            "num_corpus_chunks": len(corpus),
            "num_total_corpus_chunks": len(corpus_all),
            "num_total_queries": len(queries_all),
            "max_queries": max_queries,
            "max_corpus": max_corpus,
            "artifact_slug": artifact_slug,
            "elapsed_sec": round(elapsed_sec, 3),
            **run_metadata,
            **gt_coverage,
        }
        metrics = {
            **metadata,
            **{key: value for key, value in representative.items() if key in {"num_queries", "num_skipped_no_gt"}},
            **aggregated,
            "per_seed": per_seed_metrics,
        }
        rows.append(metrics)
        all_rankings[feedback_mode] = {
            str(result["metrics"]["seed"]): result["rankings"]
            for result in seed_results
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / f"linucb_trust_{artifact_slug}_prequential_metrics.json"
    rankings_path = output_dir / f"linucb_trust_{artifact_slug}_prequential_rankings.json"
    metrics_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rankings_path.write_text(json.dumps(all_rankings, ensure_ascii=False), encoding="utf-8")
    return rows


def _stringify_csv_value(value: object) -> object:
    return global_linucb._stringify_csv_value(value)


def update_summary(summary_path: Path, rows: Iterable[Mapping]) -> None:
    new_rows = list(rows)
    if not new_rows:
        return
    existing: Dict[tuple[str, str, str, str, str, str, str], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(
                    row.get("dataset", ""),
                    row.get("method", ""),
                    row.get("model", ""),
                    row.get("feedback_mode", ""),
                    row.get("scope", ""),
                    row.get("query_split", ""),
                    row.get("num_queries", ""),
                )] = row
    for row in new_rows:
        existing[(
            str(row["dataset"]),
            str(row["method"]),
            str(row.get("model", "")),
            str(row.get("feedback_mode", "")),
            str(row.get("scope", "")),
            str(row.get("query_split", "")),
            str(row.get("num_queries", "")),
        )] = row

    preferred_fieldnames = [
        "dataset",
        "method",
        "feedback_mode",
        "model",
        "protocol",
        "task_type",
        "scope",
        "query_split",
        "corpus_scope",
        "corpus_sampling",
        "num_queries",
        "num_skipped_no_gt",
        "num_queries_with_gt",
        "num_queries_with_gt_in_corpus",
        "gt_query_coverage",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "top_k",
        "metric_ks",
        "num_seeds",
        "seeds",
        "epochs",
        "n_clusters_requested",
        "n_effective_arms_mean",
        "context_dim_requested",
        "candidate_arms",
        "high_trust_prob",
        "high_trust",
        "low_trust",
        "high_accuracy",
        "low_accuracy",
        "window_size",
        "dense_depth",
        "bm25_depth",
        "cluster_depth",
        "dense_weight",
        "bm25_weight",
        "cluster_weight",
        "dense_floor_k",
        "total_feedback_updates_mean",
        "total_update_weight_mean",
        "cross_arm_update_weight_mean",
        "propagated_updates_mean",
    ]
    preferred_set = set(preferred_fieldnames) | {"elapsed_sec", "notes"}
    metric_keys = sorted({
        key
        for row in existing.values()
        for key in row
        if key not in preferred_set
        and (
            "@" in key
            or key.endswith("_mean")
            or key.endswith("_gain_mean")
            or key.endswith("_rate_mean")
            or key.endswith("_chunks_mean")
        )
    })
    fieldnames = [
        *preferred_fieldnames,
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


def write_markdown_table(summary_path: Path, markdown_path: Path) -> None:
    with summary_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    columns = [
        "dataset",
        "feedback_mode",
        "scope",
        "query_split",
        "corpus_scope",
        "num_queries",
        "epochs",
        "recall@10_mean",
        "last_epoch_true_reward_mean",
        "epoch_true_reward_gain_mean",
        "last_epoch_selected_cluster_hit_rate_mean",
        "epoch_selected_cluster_hit_gain_mean",
        "feedback_alignment_rate_mean",
        "avg_user_trust_mean",
    ]
    lines = [
        "# Trust-Weighted Feedback LinUCB Tables",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in sorted(rows, key=lambda item: (item.get("dataset", ""), item.get("feedback_mode", ""))):
        values = []
        for column in columns:
            value = row.get(column, "")
            if value not in ("", None) and (column.endswith("_mean") or column.endswith("_gain_mean")):
                value = f"{float(value):.4f}"
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- Protocol is repeated prequential feedback: each interaction is evaluated before its simulated feedback update.",
        "- `none` is the no-feedback control; `oracle` uses clean GT-derived feedback; `equal_noisy` and `trust_weighted` use simulated noisy user feedback.",
        "- Trust weighting scales both LinUCB updates and local feedback memory by simulated user trust.",
    ])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_sentence_transformer(model_name: str, *, device: str | None = None, local_files_only: bool = False):
    return dense_baseline.load_sentence_transformer(model_name, device=device, local_files_only=local_files_only)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run trust-weighted feedback LinUCB experiment")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--feedback-modes", default="none,oracle,equal_noisy,trust_weighted")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--seeds", default="13,17,19")
    parser.add_argument("--epochs", type=int, default=3)
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
    parser.add_argument("--dense-floor-k", type=int, default=5)
    parser.add_argument("--high-trust-prob", type=float, default=0.7)
    parser.add_argument("--high-trust", type=float, default=1.0)
    parser.add_argument("--low-trust", type=float, default=0.25)
    parser.add_argument("--high-accuracy", type=float, default=0.9)
    parser.add_argument("--low-accuracy", type=float, default=0.55)
    parser.add_argument("--window-size", type=int, default=50)
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
    feedback_modes = parse_modes(args.feedback_modes)
    ks = parse_ints(args.ks)
    seeds = parse_ints(args.seeds)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    all_rows: List[Dict[str, object]] = []
    for dataset in datasets:
        print(f"Running trust-weighted feedback LinUCB: {dataset}")
        rows = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            feedback_modes=feedback_modes,
            top_k=args.top_k,
            ks=ks,
            batch_size=args.batch_size,
            seeds=seeds,
            epochs=args.epochs,
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
            high_trust_prob=args.high_trust_prob,
            high_trust=args.high_trust,
            low_trust=args.low_trust,
            high_accuracy=args.high_accuracy,
            low_accuracy=args.low_accuracy,
            window_size=args.window_size,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
        )
        all_rows.extend(rows)
        for row in rows:
            print(
                f"  mode={row['feedback_mode']} queries={row.get('num_queries')} "
                f"recall@10={row.get('recall@10_mean', 0.0):.4f} "
                f"last_true_reward={row.get('last_epoch_true_reward_mean', 0.0):.4f} "
                f"gain={row.get('epoch_true_reward_gain_mean', 0.0):+.4f} "
                f"selected_hit_gain={row.get('epoch_selected_cluster_hit_gain_mean', 0.0):+.4f}"
            )

    summary_path = args.output_dir / "linucb_trust_summary.csv"
    update_summary(summary_path, all_rows)
    write_markdown_table(summary_path, args.output_dir / "linucb_trust_tables.md")
    print(f"Summary: {summary_path}")
    print(f"Markdown: {args.output_dir / 'linucb_trust_tables.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
