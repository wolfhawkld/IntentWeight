#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 16: confidence-gated cost-aware LinUCB routing.

Task 16 converts the Task15 self-evolving LinUCB policy into a cost-aware
retrieval controller. The control group keeps the Task13.5/15 full multi-route
surface. The gated variant lets LinUCB become the primary route when its learned
policy confidence is high and the selected cluster is semantically close to the
query; otherwise global dense remains a fallback.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import time
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


linucb_soft = _load_script_module("linucb_soft_routing", SCRIPT_DIR / "linucb_soft_routing.py")
linucb_trust = _load_script_module("linucb_trust_feedback", SCRIPT_DIR / "linucb_trust_feedback.py")
global_linucb = linucb_soft.global_linucb
manifold_linucb = linucb_soft.manifold_linucb
bm25_baseline = linucb_soft.bm25_baseline
dense_baseline = linucb_soft.dense_baseline
experiment_guardrails = linucb_soft.experiment_guardrails
retrieval_metrics = linucb_soft.retrieval_metrics
large_scale_artifacts = _load_script_module("large_scale_artifacts", SCRIPT_DIR / "large_scale_artifacts.py")

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_EMBEDDING_CACHE_DIR = dense_baseline.DEFAULT_EMBEDDING_CACHE_DIR
DEFAULT_ARTIFACT_CACHE_DIR = large_scale_artifacts.DEFAULT_ARTIFACT_CACHE_DIR
DEFAULT_SCALE_STORE_DIR = dense_baseline.DEFAULT_SCALE_STORE_DIR
DEFAULT_DATASETS = global_linucb.DEFAULT_DATASETS
DEFAULT_MODEL = global_linucb.DEFAULT_MODEL
ROUTING_MODES = (
    "full_multi_route",
    "gated_cost_aware",
    "static_nearest_ensemble",
    "static_nearest_gated",
    "uniform_random_ensemble",
    "random_partition_feedback_ensemble",
    "random_partition_static_ensemble",
    "epsilon_greedy_ensemble",
)
REWARD_ATTRIBUTIONS = (
    "final_fused",
    "cluster_only",
)
CONFIDENCE_MODES = (
    "value",
    "route_quality",
)
FINAL_CONTEXT_POLICIES = (
    "fixed_topk",
    "confidence_topk",
)
FEEDBACK_MODES = linucb_trust.FEEDBACK_MODES
CLUSTER_RETRIEVAL_ENGINES = (
    "on_demand",
    "cached_exact_scores",
)
CHECKPOINT_FORMAT_VERSION = "linucb_cost_seed_checkpoint_v2"
ROUTING_SOURCE_FILES = (
    "linucb_cost_aware_routing.py",
    "linucb_soft_routing.py",
    "linucb_trust_feedback.py",
    "linucb_online_baseline.py",
    "linucb_manifold_local.py",
    "large_scale_artifacts.py",
    "dense_baseline.py",
    "bm25_baseline.py",
    "experiment_guardrails.py",
    "retrieval_metrics.py",
)


class RoutingDecision(NamedTuple):
    route: str
    route_reason: str
    dense_depth: int
    bm25_depth: int
    cluster_depth: int
    dense_weight: float
    bm25_weight: float
    cluster_weight: float
    dense_floor_k: int
    confidence: float
    semantic_drift: float


class FinalContextDecision(NamedTuple):
    final_k: int
    reason: str


def routing_source_fingerprint() -> str:
    """Fingerprint the executable routing implementation without relying on Git state."""
    hasher = hashlib.sha256()
    for filename in ROUTING_SOURCE_FILES:
        path = SCRIPT_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing routing source dependency: {path}")
        encoded_name = filename.encode("utf-8")
        hasher.update(len(encoded_name).to_bytes(8, "little"))
        hasher.update(encoded_name)
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def runtime_dependency_versions() -> Dict[str, str]:
    versions = {"python": platform.python_version(), "numpy": np.__version__}
    for distribution in ("scikit-learn", "scipy"):
        try:
            versions[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            versions[distribution] = "unavailable"
    return versions


def validate_arm_row_indices(
    arm_labels: np.ndarray,
    arm_row_indices: Sequence[np.ndarray],
    *,
    n_arms: int,
) -> None:
    """Require cached arm rows to be an exact partition of the active labels."""
    labels = np.asarray(arm_labels, dtype=np.int32)
    if len(arm_row_indices) != n_arms:
        raise ValueError(f"expected {n_arms} arm row arrays, got {len(arm_row_indices)}")
    seen = np.zeros(len(labels), dtype=bool)
    for arm, row_indices in enumerate(arm_row_indices):
        rows = np.asarray(row_indices, dtype=np.int64)
        if rows.ndim != 1:
            raise ValueError(f"arm {arm} row indices must be one-dimensional")
        if np.any(rows < 0) or np.any(rows >= len(labels)):
            raise ValueError(f"arm {arm} contains an out-of-range corpus row")
        if len(np.unique(rows)) != len(rows):
            raise ValueError(f"arm {arm} contains duplicate corpus rows")
        if np.any(seen[rows]):
            raise ValueError(f"arm {arm} contains a duplicate corpus row")
        if np.any(labels[rows] != arm):
            raise ValueError(f"arm {arm} row indices do not match the active arm labels")
        seen[rows] = True
    if not np.all(seen):
        raise ValueError("arm row indices do not cover the full corpus")


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parse_list(value: str, choices: Sequence[str], *, label: str) -> tuple[str, ...]:
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    invalid = [item for item in items if item not in choices]
    if invalid:
        raise ValueError(f"Unsupported {label}: {invalid}. Choices: {tuple(choices)}")
    return items


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
        f"cluster-{_slug_part(run_metadata.get('cluster_retrieval_engine', 'on_demand'))}",
    ])


def arm_point_estimates(policy, context: np.ndarray) -> np.ndarray:
    values = np.zeros(policy.n_arms, dtype=np.float64)
    for arm in range(policy.n_arms):
        theta = np.linalg.solve(policy.A[arm], policy.b[arm])
        values[arm] = float(np.dot(theta, context))
    return values


def policy_confidence(
    policy,
    context: np.ndarray,
    selected_arms: Sequence[int],
    boosts: np.ndarray,
    *,
    confidence_feedback_floor: float,
) -> tuple[float, float, float]:
    """Return confidence, best value estimate, and top-vs-rest margin."""
    if confidence_feedback_floor <= 0:
        raise ValueError(f"confidence_feedback_floor must be positive, got {confidence_feedback_floor}")
    values = arm_point_estimates(policy, context) + boosts
    if values.size == 0 or not selected_arms:
        return 0.0, 0.0, 0.0
    selected = [int(arm) for arm in selected_arms]
    selected_values = np.asarray([values[arm] for arm in selected], dtype=np.float64)
    best_value = float(np.max(selected_values))
    unselected = [arm for arm in range(policy.n_arms) if arm not in set(selected)]
    next_best = float(np.max(values[unselected])) if unselected else 0.0
    margin = best_value - next_best
    mean_pulls = float(np.mean([policy.pull_counts[arm] for arm in selected]))
    maturity = min(1.0, mean_pulls / float(confidence_feedback_floor))
    bounded_value = min(1.0, max(0.0, best_value))
    bounded_margin = min(1.0, max(0.0, margin))
    confidence = maturity * (0.85 * bounded_value + 0.15 * bounded_margin)
    return float(min(1.0, max(0.0, confidence))), best_value, margin


def route_quality_confidence(
    selected_arms: Sequence[int],
    reward_sums: np.ndarray,
    pull_counts: np.ndarray,
    *,
    confidence_feedback_floor: float,
) -> float:
    """Estimate confidence from historical cluster-route reward of selected arms."""
    if confidence_feedback_floor <= 0:
        raise ValueError(f"confidence_feedback_floor must be positive, got {confidence_feedback_floor}")
    if not selected_arms:
        return 0.0
    selected = np.asarray([int(arm) for arm in selected_arms], dtype=np.int32)
    counts = pull_counts[selected]
    values = np.zeros(len(selected), dtype=np.float64)
    observed = counts > 0
    if np.any(observed):
        values[observed] = reward_sums[selected[observed]] / counts[observed]
    mean_value = float(np.mean(values)) if values.size else 0.0
    mean_pulls = float(np.mean(counts)) if counts.size else 0.0
    maturity = min(1.0, mean_pulls / float(confidence_feedback_floor))
    return float(min(1.0, max(0.0, mean_value * maturity)))


def selected_semantic_drift(context: np.ndarray, centroids: np.ndarray, selected_arms: Sequence[int]) -> float:
    if not selected_arms:
        return 1.0
    selected_centroids = centroids[np.asarray(selected_arms, dtype=np.int32)]
    similarities = selected_centroids @ context
    best_similarity = float(np.max(similarities)) if similarities.size else 0.0
    return float(1.0 - best_similarity)


def centroid_similarity_confidence(context: np.ndarray, centroids: np.ndarray, selected_arms: Sequence[int]) -> float:
    """Use nearest selected-centroid similarity as a static confidence proxy."""
    if not selected_arms:
        return 0.0
    selected_centroids = centroids[np.asarray(selected_arms, dtype=np.int32)]
    similarities = selected_centroids @ context
    best_similarity = float(np.max(similarities)) if similarities.size else 0.0
    return float(min(1.0, max(0.0, best_similarity)))


def nearest_centroid_arms(context: np.ndarray, centroids: np.ndarray, candidate_arms: int) -> List[int]:
    """Select fixed cluster arms by nearest centroid without policy learning."""
    if candidate_arms <= 0:
        raise ValueError(f"candidate_arms must be positive, got {candidate_arms}")
    if centroids.size == 0:
        return []
    similarities = centroids @ context
    order = np.lexsort((np.arange(len(similarities)), -similarities))
    return [int(arm) for arm in order[: min(candidate_arms, len(order))]]


def uniform_random_arms(rng: np.random.Generator, n_arms: int, candidate_arms: int) -> List[int]:
    """Select cluster arms uniformly without replacement."""
    if candidate_arms <= 0:
        raise ValueError(f"candidate_arms must be positive, got {candidate_arms}")
    if n_arms <= 0:
        return []
    size = min(candidate_arms, n_arms)
    return [int(arm) for arm in rng.choice(n_arms, size=size, replace=False).tolist()]


def empirical_arm_values(reward_sums: np.ndarray, pull_counts: np.ndarray) -> np.ndarray:
    values = np.zeros_like(reward_sums, dtype=np.float64)
    observed = pull_counts > 0
    values[observed] = reward_sums[observed] / pull_counts[observed]
    return values


def epsilon_greedy_arms(
    rng: np.random.Generator,
    reward_sums: np.ndarray,
    pull_counts: np.ndarray,
    candidate_arms: int,
    epsilon: float,
) -> List[int]:
    """Select arms with a non-contextual epsilon-greedy baseline."""
    if candidate_arms <= 0:
        raise ValueError(f"candidate_arms must be positive, got {candidate_arms}")
    if not 0.0 <= epsilon <= 1.0:
        raise ValueError(f"epsilon must be in [0, 1], got {epsilon}")
    n_arms = int(len(reward_sums))
    if n_arms <= 0:
        return []
    size = min(candidate_arms, n_arms)
    cold = np.flatnonzero(pull_counts <= 0)
    if cold.size >= size:
        return [int(arm) for arm in rng.choice(cold, size=size, replace=False).tolist()]
    if rng.random() < epsilon:
        return uniform_random_arms(rng, n_arms, candidate_arms)
    values = empirical_arm_values(reward_sums, pull_counts)
    order = np.lexsort((np.arange(n_arms), -values))
    return [int(arm) for arm in order[:size]]


def decide_route(
    routing_mode: str,
    *,
    confidence: float,
    semantic_drift: float,
    recent_reward_delta: float,
    dense_depth: int,
    bm25_depth: int,
    cluster_depth: int,
    dense_weight: float,
    bm25_weight: float,
    cluster_weight: float,
    dense_floor_k: int,
    dense_lite_depth: int,
    bm25_lite_depth: int,
    dense_lite_weight: float,
    bm25_lite_weight: float,
    cluster_primary_weight: float,
    dense_lite_floor_k: int,
    high_confidence_threshold: float,
    mid_confidence_threshold: float,
    drift_threshold: float,
    reward_drop_threshold: float,
) -> RoutingDecision:
    if routing_mode == "full_multi_route":
        return RoutingDecision(
            "full_multi_route",
            "full_multi_route",
            dense_depth,
            bm25_depth,
            cluster_depth,
            dense_weight,
            bm25_weight,
            cluster_weight,
            dense_floor_k,
            confidence,
            semantic_drift,
        )
    if routing_mode in {
        "static_nearest_ensemble",
        "uniform_random_ensemble",
        "random_partition_feedback_ensemble",
        "random_partition_static_ensemble",
        "epsilon_greedy_ensemble",
    }:
        return RoutingDecision(
            routing_mode,
            routing_mode,
            dense_depth,
            bm25_depth,
            cluster_depth,
            dense_weight,
            bm25_weight,
            cluster_weight,
            dense_floor_k,
            confidence,
            semantic_drift,
        )
    if routing_mode not in {"gated_cost_aware", "static_nearest_gated"}:
        raise ValueError(f"Unsupported routing_mode: {routing_mode}")

    reward_drop = reward_drop_threshold > 0 and recent_reward_delta < -reward_drop_threshold
    if confidence >= high_confidence_threshold and semantic_drift <= drift_threshold and not reward_drop:
        return RoutingDecision(
            "linucb_primary",
            "linucb_primary_ready",
            0,
            bm25_lite_depth,
            cluster_depth,
            0.0,
            bm25_lite_weight,
            cluster_primary_weight,
            0,
            confidence,
            semantic_drift,
        )
    if confidence >= mid_confidence_threshold and semantic_drift <= drift_threshold and not reward_drop:
        return RoutingDecision(
            "hybrid_lite",
            "hybrid_lite_ready",
            dense_lite_depth,
            bm25_lite_depth,
            cluster_depth,
            dense_lite_weight,
            bm25_lite_weight,
            cluster_primary_weight,
            dense_lite_floor_k,
            confidence,
            semantic_drift,
        )
    if reward_drop:
        route_reason = "fallback_reward_drop"
    elif semantic_drift > drift_threshold:
        route_reason = "fallback_high_drift"
    else:
        route_reason = "fallback_low_confidence"
    return RoutingDecision(
        "full_dense_fallback",
        route_reason,
        dense_depth,
        bm25_depth,
        cluster_depth,
        dense_weight,
        bm25_weight,
        cluster_weight,
        dense_floor_k,
        confidence,
        semantic_drift,
    )


def decide_final_context(
    final_context_policy: str,
    *,
    confidence: float,
    semantic_drift: float,
    route: str,
    top_k: int,
    final_context_high_k: int,
    final_context_mid_k: int,
    high_confidence_threshold: float,
    mid_confidence_threshold: float,
    drift_threshold: float,
) -> FinalContextDecision:
    """Choose how many final ranked chunks are sent to the generation context."""
    if final_context_policy not in FINAL_CONTEXT_POLICIES:
        raise ValueError(f"Unsupported final_context_policy: {final_context_policy}")
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
    if min(final_context_high_k, final_context_mid_k) <= 0:
        raise ValueError("final context k values must be positive")
    if final_context_policy == "fixed_topk":
        return FinalContextDecision(top_k, "fixed_topk")

    route_is_lite = route in {"linucb_primary", "hybrid_lite"}
    drift_ok = semantic_drift <= drift_threshold
    if route_is_lite and drift_ok and confidence >= high_confidence_threshold:
        return FinalContextDecision(min(top_k, final_context_high_k), "high_confidence_compact")
    if route_is_lite and drift_ok and confidence >= mid_confidence_threshold:
        return FinalContextDecision(min(top_k, final_context_mid_k), "mid_confidence_compact")
    return FinalContextDecision(top_k, "fallback_full_topk")


def source_cost(dense_ranking: Sequence[str], bm25_ranking: Sequence[str], cluster_ranking: Sequence[str]) -> int:
    return int(len(dense_ranking) + len(bm25_ranking) + len(cluster_ranking))


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _window_mean(values: Sequence[float], window_size: int, *, tail: bool) -> float:
    return linucb_trust._window_mean(values, window_size, tail=tail)


def _recent_window_delta(values: Sequence[float], window_size: int) -> float:
    if window_size <= 0 or len(values) < window_size * 2:
        return 0.0
    recent = values[-window_size:]
    previous = values[-window_size * 2:-window_size]
    return float(_mean(recent) - _mean(previous))


def _record_stage_timing(
    stage_timings: Dict[str, List[int]] | None,
    stage: str,
    started_ns: int,
) -> None:
    """Append an optional stage duration without changing normal experiment output."""
    if stage_timings is not None:
        stage_timings.setdefault(stage, []).append(max(0, time.perf_counter_ns() - started_ns))


def run_prequential_seed(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    seed: int,
    routing_mode: str,
    feedback_mode: str,
    reward_attribution: str,
    confidence_mode: str,
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
    dense_lite_depth: int,
    bm25_lite_depth: int,
    dense_lite_weight: float,
    bm25_lite_weight: float,
    cluster_primary_weight: float,
    dense_lite_floor_k: int,
    high_confidence_threshold: float,
    mid_confidence_threshold: float,
    drift_threshold: float,
    reward_drop_threshold: float,
    confidence_feedback_floor: float,
    final_context_policy: str,
    final_context_high_k: int,
    final_context_mid_k: int,
    high_trust_prob: float,
    high_trust: float,
    low_trust: float,
    high_accuracy: float,
    low_accuracy: float,
    window_size: int,
    epsilon_greedy_rate: float = 0.1,
    shared_context_artifacts: Mapping[str, np.ndarray] | None = None,
    dense_rankings_by_qid: Mapping[str, Sequence[str]] | None = None,
    bm25_rankings_by_qid: Mapping[str, Sequence[str]] | None = None,
    cluster_retrieval_engine: str = "on_demand",
    arm_row_indices: Sequence[np.ndarray] | None = None,
    query_corpus_scores: np.ndarray | None = None,
    progress_callback: Callable[[Mapping[str, object]], None] | None = None,
    initial_state: Mapping[str, object] | None = None,
    freeze_updates: bool = False,
    return_state: bool = False,
    stage_timings: Dict[str, List[int]] | None = None,
    event_indices: Sequence[int] | None = None,
    event_labels: Sequence[str] | None = None,
    collect_interaction_records: bool = False,
) -> Dict[str, object]:
    if routing_mode not in ROUTING_MODES:
        raise ValueError(f"Unsupported routing_mode: {routing_mode}")
    if feedback_mode not in FEEDBACK_MODES:
        raise ValueError(f"Unsupported feedback_mode: {feedback_mode}")
    if reward_attribution not in REWARD_ATTRIBUTIONS:
        raise ValueError(f"Unsupported reward_attribution: {reward_attribution}")
    if confidence_mode not in CONFIDENCE_MODES:
        raise ValueError(f"Unsupported confidence_mode: {confidence_mode}")
    if final_context_policy not in FINAL_CONTEXT_POLICIES:
        raise ValueError(f"Unsupported final_context_policy: {final_context_policy}")
    if cluster_retrieval_engine not in CLUSTER_RETRIEVAL_ENGINES:
        raise ValueError(f"Unsupported cluster_retrieval_engine: {cluster_retrieval_engine}")
    if epochs <= 0:
        raise ValueError(f"epochs must be positive, got {epochs}")
    if min(top_k, cluster_depth) <= 0:
        raise ValueError("top_k and cluster_depth must be positive")
    if min(dense_depth, bm25_depth, dense_lite_depth, bm25_lite_depth, dense_floor_k, dense_lite_floor_k) < 0:
        raise ValueError("dense/BM25 depths and dense floors must be non-negative")
    stream_indices: List[int] | None = None
    stream_labels: List[str] | None = None
    if event_indices is not None:
        if epochs != 1:
            raise ValueError("event_indices requires epochs=1 because it defines the full interaction stream")
        stream_indices = [int(index) for index in event_indices]
        if not stream_indices:
            raise ValueError("event_indices must not be empty")
        if any(index < 0 or index >= len(queries) for index in stream_indices):
            raise ValueError("event_indices contains an out-of-range query index")
        if event_labels is None:
            stream_labels = ["stream" for _ in stream_indices]
        else:
            stream_labels = [str(label) for label in event_labels]
            if len(stream_labels) != len(stream_indices):
                raise ValueError("event_labels must have the same length as event_indices")
    if cluster_retrieval_engine == "cached_exact_scores":
        if arm_row_indices is None or query_corpus_scores is None:
            raise ValueError("cached_exact_scores requires arm_row_indices and query_corpus_scores")
        if len(arm_row_indices) == 0:
            raise ValueError("cached_exact_scores requires at least one arm index")
        if query_corpus_scores.shape != (len(queries), len(corpus)):
            raise ValueError(
                "query_corpus_scores shape must match selected queries and corpus: "
                f"expected={(len(queries), len(corpus))}, got={query_corpus_scores.shape}"
            )

    if shared_context_artifacts is not None:
        corpus_context = np.asarray(shared_context_artifacts["corpus_context"], dtype=np.float32)
        query_context = np.asarray(shared_context_artifacts["query_context"], dtype=np.float32)
        arm_labels = np.asarray(shared_context_artifacts["arm_labels"], dtype=np.int32)
        centroids = np.asarray(shared_context_artifacts["centroids"], dtype=np.float32)
        n_effective_arms = int(len(centroids))
    else:
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
    active_arm_row_indices = arm_row_indices
    if routing_mode in {"random_partition_feedback_ensemble", "random_partition_static_ensemble"}:
        partition_rng = np.random.default_rng(65020 + int(seed))
        arm_labels = partition_rng.permutation(arm_labels)
        centroids = manifold_linucb.arm_centroids(corpus_context, arm_labels, n_effective_arms)
        if cluster_retrieval_engine == "cached_exact_scores":
            active_arm_row_indices = global_linucb.build_arm_row_indices(
                arm_labels,
                n_arms=n_effective_arms,
            )
    if cluster_retrieval_engine == "cached_exact_scores":
        validate_arm_row_indices(
            arm_labels,
            active_arm_row_indices,
            n_arms=n_effective_arms,
        )
    if initial_state is None:
        policy = global_linucb.GlobalLinUCBPolicy(
            n_arms=n_effective_arms,
            context_dim=query_context.shape[1],
            alpha=alpha,
            alpha_decay=alpha_decay,
            alpha_min=alpha_min,
            seed=seed,
        )
    else:
        policy = initial_state.get("policy")
        if not isinstance(policy, global_linucb.GlobalLinUCBPolicy):
            raise ValueError("initial_state must contain a GlobalLinUCBPolicy under 'policy'")
        if policy.n_arms != n_effective_arms or policy.context_dim != query_context.shape[1]:
            raise ValueError("initial policy dimensions do not match the current routing artifacts")
    linucb_learning_enabled = routing_mode in {
        "full_multi_route",
        "gated_cost_aware",
        "random_partition_feedback_ensemble",
    }
    simple_bandit_enabled = routing_mode == "epsilon_greedy_ensemble"
    simple_reward_sums = np.zeros(n_effective_arms, dtype=np.float64)
    simple_pull_counts = np.zeros(n_effective_arms, dtype=np.float64)
    simple_bandit_updates = 0
    route_reward_sums = np.zeros(n_effective_arms, dtype=np.float64)
    route_pull_counts = np.zeros(n_effective_arms, dtype=np.float64)
    decision_observed_rewards: List[float] = []
    if initial_state is not None:
        initial_route_rewards = np.asarray(initial_state.get("route_reward_sums", route_reward_sums), dtype=np.float64)
        initial_route_pulls = np.asarray(initial_state.get("route_pull_counts", route_pull_counts), dtype=np.float64)
        if initial_route_rewards.shape != route_reward_sums.shape or initial_route_pulls.shape != route_pull_counts.shape:
            raise ValueError("initial route statistics do not match the current arm count")
        route_reward_sums = initial_route_rewards.copy()
        route_pull_counts = initial_route_pulls.copy()
        decision_observed_rewards = [float(value) for value in initial_state.get("observed_rewards", [])]

    rng = np.random.default_rng(seed)
    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    arm_labels_by_chunk = {chunk_id: int(label) for chunk_id, label in zip(chunk_ids, arm_labels)}
    max_bm25_depth_needed = max(bm25_depth, bm25_lite_depth)
    bm25 = None
    if bm25_rankings_by_qid is None and max_bm25_depth_needed > 0:
        tokenized_corpus = [bm25_baseline.tokenize(str(chunk.get("text", ""))) for chunk in corpus]
        bm25 = bm25_baseline.SparseBM25(tokenized_corpus)

    rankings: Dict[str, List[str]] = {}
    query_traces: Dict[str, Dict[str, object]] = {}
    feedback_contexts: List[np.ndarray] = []
    feedback_arm_rewards: List[Dict[int, float]] = []
    if initial_state is not None:
        feedback_contexts = [
            np.asarray(context, dtype=np.float32).copy()
            for context in initial_state.get("feedback_contexts", [])
        ]
        feedback_arm_rewards = [
            {int(arm): float(reward) for arm, reward in rewards.items()}
            for rewards in initial_state.get("feedback_arm_rewards", [])
        ]
        if len(feedback_contexts) != len(feedback_arm_rewards):
            raise ValueError("initial feedback contexts and rewards must have matching lengths")
    total_update_weight = 0.0
    cross_arm_update_weight = 0.0
    propagated_updates = 0

    true_rewards: List[float] = []
    observed_rewards: List[float] = []
    final_true_rewards: List[float] = []
    route_true_rewards: List[float] = []
    selected_cluster_hits: List[float] = []
    final_hits: List[float] = []
    confidences: List[float] = []
    semantic_drifts: List[float] = []
    source_costs: List[float] = []
    union_candidate_counts: List[float] = []
    dense_candidates: List[float] = []
    bm25_candidates: List[float] = []
    cluster_candidates: List[float] = []
    dense_query_flags: List[float] = []
    bm25_query_flags: List[float] = []
    final_context_ks: List[float] = []
    final_context_reason_counts = {
        "fixed_topk": 0,
        "high_confidence_compact": 0,
        "mid_confidence_compact": 0,
        "fallback_full_topk": 0,
    }
    route_counts = {
        "full_multi_route": 0,
        "static_nearest_ensemble": 0,
        "uniform_random_ensemble": 0,
        "random_partition_feedback_ensemble": 0,
        "random_partition_static_ensemble": 0,
        "epsilon_greedy_ensemble": 0,
        "full_dense_fallback": 0,
        "hybrid_lite": 0,
        "linucb_primary": 0,
    }
    route_reason_counts = {
        "full_multi_route": 0,
        "static_nearest_ensemble": 0,
        "uniform_random_ensemble": 0,
        "random_partition_feedback_ensemble": 0,
        "random_partition_static_ensemble": 0,
        "epsilon_greedy_ensemble": 0,
        "linucb_primary_ready": 0,
        "hybrid_lite_ready": 0,
        "fallback_low_confidence": 0,
        "fallback_high_drift": 0,
        "fallback_reward_drop": 0,
    }
    epoch_rows: List[Dict[str, float]] = []
    interaction_records: List[Dict[str, object]] = []

    for epoch in range(epochs):
        if stream_indices is None:
            epoch_indices = np.arange(len(queries))
            rng.shuffle(epoch_indices)
        else:
            epoch_indices = np.asarray(stream_indices, dtype=np.int64)
        epoch_true_rewards: List[float] = []
        epoch_final_true_rewards: List[float] = []
        epoch_route_true_rewards: List[float] = []
        epoch_hits: List[float] = []
        epoch_costs: List[float] = []
        epoch_confidences: List[float] = []
        epoch_lite_routes: List[float] = []

        for event_offset, query_idx in enumerate(epoch_indices):
            query_idx = int(query_idx)
            query = queries[query_idx]
            qid = _query_id(query)
            event_label = stream_labels[event_offset] if stream_labels is not None else "prequential"
            context = query_context[query_idx]
            stage_started_ns = time.perf_counter_ns()
            if linucb_learning_enabled:
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
                if confidence_mode == "route_quality":
                    confidence = route_quality_confidence(
                        selected_arms,
                        route_reward_sums,
                        route_pull_counts,
                        confidence_feedback_floor=confidence_feedback_floor,
                    )
                else:
                    confidence, _, _ = policy_confidence(
                        policy,
                        context,
                        selected_arms,
                        boosts,
                        confidence_feedback_floor=confidence_feedback_floor,
                    )
            elif routing_mode in {
                "static_nearest_ensemble",
                "static_nearest_gated",
                "random_partition_static_ensemble",
            }:
                selected_arms = nearest_centroid_arms(context, centroids, candidate_arms)
                confidence = 0.0
            elif routing_mode == "uniform_random_ensemble":
                selected_arms = uniform_random_arms(rng, n_effective_arms, candidate_arms)
                confidence = 0.0
            elif routing_mode == "epsilon_greedy_ensemble":
                selected_arms = epsilon_greedy_arms(
                    rng,
                    simple_reward_sums,
                    simple_pull_counts,
                    candidate_arms,
                    epsilon_greedy_rate,
                )
                values = empirical_arm_values(simple_reward_sums, simple_pull_counts)
                confidence = float(np.mean([values[int(arm)] for arm in selected_arms])) if selected_arms else 0.0
            else:
                raise ValueError(f"Unsupported routing_mode: {routing_mode}")
            semantic_drift = selected_semantic_drift(context, centroids, selected_arms)
            if routing_mode in {"static_nearest_gated", "random_partition_static_ensemble"}:
                confidence = centroid_similarity_confidence(context, centroids, selected_arms)
            recent_reward_delta = _recent_window_delta(decision_observed_rewards, window_size)
            decision = decide_route(
                routing_mode,
                confidence=confidence,
                semantic_drift=semantic_drift,
                recent_reward_delta=recent_reward_delta,
                dense_depth=dense_depth,
                bm25_depth=bm25_depth,
                cluster_depth=cluster_depth,
                dense_weight=dense_weight,
                bm25_weight=bm25_weight,
                cluster_weight=cluster_weight,
                dense_floor_k=dense_floor_k,
                dense_lite_depth=dense_lite_depth,
                bm25_lite_depth=bm25_lite_depth,
                dense_lite_weight=dense_lite_weight,
                bm25_lite_weight=bm25_lite_weight,
                cluster_primary_weight=cluster_primary_weight,
                dense_lite_floor_k=dense_lite_floor_k,
                high_confidence_threshold=high_confidence_threshold,
                mid_confidence_threshold=mid_confidence_threshold,
                drift_threshold=drift_threshold,
                reward_drop_threshold=reward_drop_threshold,
            )
            _record_stage_timing(stage_timings, "routing_and_gating", stage_started_ns)
            route_counts[decision.route] += 1
            route_reason_counts[decision.route_reason] += 1

            stage_started_ns = time.perf_counter_ns()
            if dense_rankings_by_qid is not None:
                dense_ranking = [str(chunk_id) for chunk_id in dense_rankings_by_qid.get(qid, [])[: decision.dense_depth]]
            else:
                dense_ranking = linucb_soft.top_dense_ranking(
                    query_embeddings[query_idx],
                    corpus_embeddings,
                    chunk_ids,
                    depth=decision.dense_depth,
                )
            _record_stage_timing(stage_timings, "dense_route", stage_started_ns)
            stage_started_ns = time.perf_counter_ns()
            if bm25_rankings_by_qid is not None:
                bm25_ranking = [str(chunk_id) for chunk_id in bm25_rankings_by_qid.get(qid, [])[: decision.bm25_depth]]
            else:
                bm25_ranking = linucb_soft.top_bm25_ranking(
                    str(query.get("text", "")),
                    bm25,
                    chunk_ids,
                    depth=decision.bm25_depth,
                )
            _record_stage_timing(stage_timings, "bm25_route", stage_started_ns)
            stage_started_ns = time.perf_counter_ns()
            if cluster_retrieval_engine == "cached_exact_scores":
                cluster_ranking = global_linucb.retrieve_from_arm_score_cache(
                    query_corpus_scores[query_idx],
                    chunk_ids,
                    active_arm_row_indices,
                    selected_arms,
                    top_k=decision.cluster_depth,
                )
            else:
                cluster_ranking = global_linucb.retrieve_from_arms(
                    query_embeddings[query_idx],
                    corpus_embeddings,
                    chunk_ids,
                    arm_labels,
                    selected_arms,
                    top_k=decision.cluster_depth,
                )
            _record_stage_timing(stage_timings, "cluster_route", stage_started_ns)
            stage_started_ns = time.perf_counter_ns()
            ranking = linucb_soft.weighted_reciprocal_rank_fusion(
                (
                    (dense_ranking, decision.dense_weight),
                    (bm25_ranking, decision.bm25_weight),
                    (cluster_ranking, decision.cluster_weight),
                ),
                rrf_k=rrf_k,
                top_k=top_k,
            )
            ranking = linucb_soft.apply_dense_floor(
                ranking,
                dense_ranking,
                dense_floor_k=decision.dense_floor_k,
                top_k=top_k,
            )
            _record_stage_timing(stage_timings, "fusion_and_dense_floor", stage_started_ns)
            stage_started_ns = time.perf_counter_ns()
            final_context_decision = decide_final_context(
                final_context_policy,
                confidence=confidence,
                semantic_drift=semantic_drift,
                route=decision.route,
                top_k=top_k,
                final_context_high_k=final_context_high_k,
                final_context_mid_k=final_context_mid_k,
                high_confidence_threshold=high_confidence_threshold,
                mid_confidence_threshold=mid_confidence_threshold,
                drift_threshold=drift_threshold,
            )
            ranking = ranking[: final_context_decision.final_k]
            _record_stage_timing(stage_timings, "final_context_budget", stage_started_ns)
            rankings[qid] = ranking
            final_context_ks.append(float(final_context_decision.final_k))
            final_context_reason_counts[final_context_decision.reason] += 1

            gt = _ground_truth(query)
            final_hit = _has_hit(ranking, gt, k=top_k)
            selected_cluster_hit = linucb_soft.gt_cluster_hit(selected_arms, gt, arm_labels_by_chunk)
            interaction_cost = float(source_cost(dense_ranking, bm25_ranking, cluster_ranking))
            source_costs.append(interaction_cost)
            union_candidate_counts.append(float(len(set(dense_ranking) | set(bm25_ranking) | set(cluster_ranking))))
            dense_candidates.append(float(len(dense_ranking)))
            bm25_candidates.append(float(len(bm25_ranking)))
            cluster_candidates.append(float(len(cluster_ranking)))
            dense_query_flags.append(float(decision.dense_depth > 0))
            bm25_query_flags.append(float(decision.bm25_depth > 0))
            confidences.append(float(confidence))
            semantic_drifts.append(float(semantic_drift))
            selected_cluster_hits.append(float(selected_cluster_hit))
            final_hits.append(float(final_hit))

            arm_memory_rewards: Dict[int, float] = {}
            selected_update_true_rewards: List[float] = []
            selected_final_true_rewards: List[float] = []
            selected_route_true_rewards: List[float] = []
            selected_observed_rewards: List[float] = []
            for source_arm in selected_arms:
                stage_started_ns = time.perf_counter_ns()
                final_true_reward = global_linucb._arm_reward(ranking, gt, source_arm, arm_labels_by_chunk)
                route_true_reward = global_linucb._arm_reward(cluster_ranking, gt, source_arm, arm_labels_by_chunk)
                true_reward = route_true_reward if reward_attribution == "cluster_only" else final_true_reward
                _record_stage_timing(stage_timings, "feedback_reward_measurement", stage_started_ns)

                stage_started_ns = time.perf_counter_ns()
                observation = linucb_trust.simulate_user_feedback(
                    true_reward,
                    rng,
                    mode=feedback_mode,
                    high_trust_prob=high_trust_prob,
                    high_trust=high_trust,
                    low_trust=low_trust,
                    high_accuracy=high_accuracy,
                    low_accuracy=low_accuracy,
                )
                _record_stage_timing(stage_timings, "feedback_observation", stage_started_ns)

                stage_started_ns = time.perf_counter_ns()
                update_weight = linucb_trust.update_weight_for_mode(feedback_mode, observation)
                memory_reward = linucb_trust.memory_reward_for_mode(feedback_mode, observation)
                arm_memory_rewards[int(source_arm)] = memory_reward
                selected_update_true_rewards.append(float(true_reward))
                selected_final_true_rewards.append(float(final_true_reward))
                selected_route_true_rewards.append(float(route_true_reward))
                selected_observed_rewards.append(float(observation.observed_reward))
                _record_stage_timing(stage_timings, "feedback_trust_weighting", stage_started_ns)

                stage_started_ns = time.perf_counter_ns()
                if not freeze_updates:
                    route_reward_sums[int(source_arm)] += float(route_true_reward)
                    route_pull_counts[int(source_arm)] += 1.0
                if simple_bandit_enabled and update_weight > 0 and not freeze_updates:
                    simple_reward_sums[int(source_arm)] += float(update_weight * observation.observed_reward)
                    simple_pull_counts[int(source_arm)] += float(update_weight)
                    simple_bandit_updates += 1
                if linucb_learning_enabled and update_weight > 0 and not freeze_updates:
                    for target_arm, propagation_weight in manifold_linucb.arm_propagation_weights(
                        centroids,
                        source_arm,
                        sigma=arm_decay_sigma,
                        neighbor_k=arm_neighbor_k,
                        propagation_strength=propagation_strength,
                    ):
                        weight = float(update_weight * propagation_weight)
                        update_started_ns = time.perf_counter_ns()
                        policy.update(target_arm, context, observation.observed_reward, weight=weight)
                        _record_stage_timing(stage_timings, "linucb_update", update_started_ns)
                        total_update_weight += weight
                        if target_arm != source_arm:
                            cross_arm_update_weight += weight
                            propagated_updates += 1
                _record_stage_timing(stage_timings, "feedback_state_update", stage_started_ns)

            stage_started_ns = time.perf_counter_ns()
            if linucb_learning_enabled and feedback_mode != "none" and not freeze_updates:
                feedback_contexts.append(context.copy())
                feedback_arm_rewards.append(arm_memory_rewards)
            _record_stage_timing(stage_timings, "feedback_memory_append", stage_started_ns)

            interaction_true = max(selected_update_true_rewards) if selected_update_true_rewards else 0.0
            interaction_final_true = max(selected_final_true_rewards) if selected_final_true_rewards else 0.0
            interaction_route_true = max(selected_route_true_rewards) if selected_route_true_rewards else 0.0
            interaction_observed = max(selected_observed_rewards) if selected_observed_rewards else 0.0
            if epoch == epochs - 1:
                query_traces[qid] = {
                    "epoch": epoch + 1,
                    "confidence": float(confidence),
                    "semantic_drift": float(semantic_drift),
                    "route": decision.route,
                    "route_reason": decision.route_reason,
                    "dense_queried": bool(decision.dense_depth > 0),
                    "selected_arms": [int(arm) for arm in selected_arms],
                    "selected_cluster_hit": float(selected_cluster_hit),
                    "final_hit": int(final_hit),
                    "final_context_k": int(final_context_decision.final_k),
                    "route_true_reward": float(interaction_route_true),
                    "final_true_reward": float(interaction_final_true),
                    "source_candidate_cost": float(interaction_cost),
                }
            if collect_interaction_records:
                interaction_records.append({
                    "event_index": int(len(interaction_records)),
                    "event_label": event_label,
                    "query_index": query_idx,
                    "query_id": qid,
                    "ranking": [str(chunk_id) for chunk_id in ranking],
                    "route": decision.route,
                    "route_reason": decision.route_reason,
                    "dense_queried": bool(decision.dense_depth > 0),
                    "bm25_queried": bool(decision.bm25_depth > 0),
                    "selected_arms": [int(arm) for arm in selected_arms],
                    "selected_cluster_hit": float(selected_cluster_hit),
                    "final_hit": float(final_hit),
                    "final_context_k": int(final_context_decision.final_k),
                    "confidence": float(confidence),
                    "semantic_drift": float(semantic_drift),
                    "route_true_reward": float(interaction_route_true),
                    "final_true_reward": float(interaction_final_true),
                    "observed_reward": float(interaction_observed),
                    "source_candidate_cost": float(interaction_cost),
                })
            true_rewards.append(float(interaction_true))
            final_true_rewards.append(float(interaction_final_true))
            route_true_rewards.append(float(interaction_route_true))
            observed_rewards.append(float(interaction_observed))
            if not freeze_updates:
                decision_observed_rewards.append(float(interaction_observed))
            epoch_true_rewards.append(float(interaction_true))
            epoch_final_true_rewards.append(float(interaction_final_true))
            epoch_route_true_rewards.append(float(interaction_route_true))
            epoch_hits.append(float(final_hit))
            epoch_costs.append(interaction_cost)
            epoch_confidences.append(float(confidence))
            epoch_lite_routes.append(float(decision.route in {"hybrid_lite", "linucb_primary"}))

        epoch_rows.append({
            "epoch": float(epoch + 1),
            "true_reward": _mean(epoch_true_rewards),
            "final_true_reward": _mean(epoch_final_true_rewards),
            "route_true_reward": _mean(epoch_route_true_rewards),
            "hit_rate": _mean(epoch_hits),
            "source_cost": _mean(epoch_costs),
            "confidence": _mean(epoch_confidences),
            "lite_route_rate": _mean(epoch_lite_routes),
        })
        if progress_callback is not None:
            progress_callback({
                "seed": int(seed),
                "routing_mode": routing_mode,
                "epoch": int(epoch + 1),
                "epochs": int(epochs),
                "interactions_completed": int((epoch + 1) * len(queries)),
                "interactions_total": int(epochs * len(queries)),
                "last_epoch": epoch_rows[-1],
            })

    metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    first_epoch = epoch_rows[0] if epoch_rows else {}
    last_epoch = epoch_rows[-1] if epoch_rows else {}
    num_interactions = max(1, len(source_costs))
    avg_source_cost = _mean(source_costs)
    recall_at_top_k = float(metrics.get(f"recall@{top_k}", 0.0))
    metrics.update({
        "seed": seed,
        "routing_mode": routing_mode,
        "feedback_mode": feedback_mode,
        "reward_attribution": reward_attribution,
        "confidence_mode": confidence_mode,
        "final_context_policy": final_context_policy,
        "cluster_retrieval_engine": cluster_retrieval_engine,
        "epochs": epochs,
        "num_interactions": len(source_costs),
        "avg_true_feedback_reward": _mean(true_rewards),
        "avg_observed_feedback_reward": _mean(observed_rewards),
        "avg_final_true_reward": _mean(final_true_rewards),
        "avg_route_true_reward": _mean(route_true_rewards),
        "last_epoch_true_reward": float(last_epoch.get("true_reward", 0.0)),
        "epoch_true_reward_gain": float(last_epoch.get("true_reward", 0.0) - first_epoch.get("true_reward", 0.0)),
        "last_epoch_final_true_reward": float(last_epoch.get("final_true_reward", 0.0)),
        "epoch_final_true_reward_gain": float(
            last_epoch.get("final_true_reward", 0.0) - first_epoch.get("final_true_reward", 0.0)
        ),
        "last_epoch_route_true_reward": float(last_epoch.get("route_true_reward", 0.0)),
        "epoch_route_true_reward_gain": float(
            last_epoch.get("route_true_reward", 0.0) - first_epoch.get("route_true_reward", 0.0)
        ),
        "last_epoch_hit_rate": float(last_epoch.get("hit_rate", 0.0)),
        "epoch_hit_rate_gain": float(last_epoch.get("hit_rate", 0.0) - first_epoch.get("hit_rate", 0.0)),
        "last_epoch_source_cost": float(last_epoch.get("source_cost", 0.0)),
        "epoch_source_cost_delta": float(last_epoch.get("source_cost", 0.0) - first_epoch.get("source_cost", 0.0)),
        "last_epoch_confidence": float(last_epoch.get("confidence", 0.0)),
        "epoch_confidence_gain": float(last_epoch.get("confidence", 0.0) - first_epoch.get("confidence", 0.0)),
        "last_epoch_lite_route_rate": float(last_epoch.get("lite_route_rate", 0.0)),
        "avg_source_candidate_cost": avg_source_cost,
        f"quality_cost_ratio@{top_k}": recall_at_top_k / avg_source_cost if avg_source_cost > 0 else 0.0,
        "avg_union_candidate_chunks": _mean(union_candidate_counts),
        "avg_dense_candidates": _mean(dense_candidates),
        "avg_bm25_candidates": _mean(bm25_candidates),
        "avg_cluster_candidates": _mean(cluster_candidates),
        "dense_query_rate": _mean(dense_query_flags),
        "bm25_query_rate": _mean(bm25_query_flags),
        "avg_confidence": _mean(confidences),
        "avg_final_context_k": _mean(final_context_ks),
        "compact_context_rate": (
            (
                final_context_reason_counts["high_confidence_compact"]
                + final_context_reason_counts["mid_confidence_compact"]
            )
            / num_interactions
        ),
        "high_confidence_compact_rate": final_context_reason_counts["high_confidence_compact"] / num_interactions,
        "mid_confidence_compact_rate": final_context_reason_counts["mid_confidence_compact"] / num_interactions,
        "fallback_full_topk_context_rate": final_context_reason_counts["fallback_full_topk"] / num_interactions,
        "avg_semantic_drift": _mean(semantic_drifts),
        "selected_cluster_hit_rate": _mean(selected_cluster_hits),
        "soft_fused_hit_rate": _mean(final_hits),
        "full_multi_route_rate": route_counts["full_multi_route"] / num_interactions,
        "static_nearest_ensemble_rate": route_counts["static_nearest_ensemble"] / num_interactions,
        "uniform_random_ensemble_rate": route_counts["uniform_random_ensemble"] / num_interactions,
        "random_partition_feedback_ensemble_rate": (
            route_counts["random_partition_feedback_ensemble"] / num_interactions
        ),
        "random_partition_static_ensemble_rate": (
            route_counts["random_partition_static_ensemble"] / num_interactions
        ),
        "epsilon_greedy_ensemble_rate": route_counts["epsilon_greedy_ensemble"] / num_interactions,
        "full_dense_fallback_rate": route_counts["full_dense_fallback"] / num_interactions,
        "hybrid_lite_rate": route_counts["hybrid_lite"] / num_interactions,
        "linucb_primary_rate": route_counts["linucb_primary"] / num_interactions,
        "static_nearest_ensemble_reason_rate": route_reason_counts["static_nearest_ensemble"] / num_interactions,
        "uniform_random_ensemble_reason_rate": route_reason_counts["uniform_random_ensemble"] / num_interactions,
        "random_partition_feedback_ensemble_reason_rate": (
            route_reason_counts["random_partition_feedback_ensemble"] / num_interactions
        ),
        "random_partition_static_ensemble_reason_rate": (
            route_reason_counts["random_partition_static_ensemble"] / num_interactions
        ),
        "epsilon_greedy_ensemble_reason_rate": route_reason_counts["epsilon_greedy_ensemble"] / num_interactions,
        "fallback_low_confidence_rate": route_reason_counts["fallback_low_confidence"] / num_interactions,
        "fallback_high_drift_rate": route_reason_counts["fallback_high_drift"] / num_interactions,
        "fallback_reward_drop_rate": route_reason_counts["fallback_reward_drop"] / num_interactions,
        "dense_saved_rate": 1.0 - _mean(dense_query_flags),
        "first_window_true_reward": _window_mean(true_rewards, window_size, tail=False),
        "last_window_true_reward": _window_mean(true_rewards, window_size, tail=True),
        "window_true_reward_gain": float(
            _window_mean(true_rewards, window_size, tail=True) - _window_mean(true_rewards, window_size, tail=False)
        ),
        "first_window_final_true_reward": _window_mean(final_true_rewards, window_size, tail=False),
        "last_window_final_true_reward": _window_mean(final_true_rewards, window_size, tail=True),
        "window_final_true_reward_gain": float(
            _window_mean(final_true_rewards, window_size, tail=True)
            - _window_mean(final_true_rewards, window_size, tail=False)
        ),
        "first_window_route_true_reward": _window_mean(route_true_rewards, window_size, tail=False),
        "last_window_route_true_reward": _window_mean(route_true_rewards, window_size, tail=True),
        "window_route_true_reward_gain": float(
            _window_mean(route_true_rewards, window_size, tail=True)
            - _window_mean(route_true_rewards, window_size, tail=False)
        ),
        "first_window_source_cost": _window_mean(source_costs, window_size, tail=False),
        "last_window_source_cost": _window_mean(source_costs, window_size, tail=True),
        "window_source_cost_delta": float(
            _window_mean(source_costs, window_size, tail=True) - _window_mean(source_costs, window_size, tail=False)
        ),
        "final_effective_alpha": float(policy.effective_alpha),
        "n_effective_arms": n_effective_arms,
        "total_feedback_updates": int(policy.total_feedback),
        "simple_bandit_updates": int(simple_bandit_updates),
        "total_update_weight": float(total_update_weight),
        "cross_arm_update_weight": float(cross_arm_update_weight),
        "propagated_updates": int(propagated_updates),
        "epoch_metrics": epoch_rows,
    })
    result: Dict[str, object] = {"rankings": rankings, "metrics": metrics, "query_traces": query_traces}
    if collect_interaction_records:
        result["interaction_records"] = interaction_records
    if return_state:
        # This in-memory state is intentionally excluded from normal checkpoints.
        result["runtime_state"] = {
            "policy": policy,
            "feedback_contexts": feedback_contexts,
            "feedback_arm_rewards": feedback_arm_rewards,
            "route_reward_sums": route_reward_sums,
            "route_pull_counts": route_pull_counts,
            "observed_rewards": decision_observed_rewards,
        }
    return result


def aggregate_seed_metrics(seed_metrics: Sequence[Mapping]) -> Dict[str, object]:
    return global_linucb.aggregate_seed_metrics(seed_metrics)


def write_json_atomic(path: Path, payload: object) -> None:
    """Write JSON through a temp file so interrupted runs do not corrupt outputs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def seed_checkpoint_path(output_dir: Path, artifact_slug: str, routing_mode: str, seed: int) -> Path:
    return output_dir / "checkpoints" / f"linucb_cost_{artifact_slug}__{routing_mode}__seed{seed}.json"


def load_seed_checkpoint(
    path: Path,
    signature: Mapping[str, object],
    *,
    expected_query_ids: Sequence[str],
    expected_ranking_depths: Sequence[int],
    diagnostics: Dict[str, object] | None = None,
) -> Dict[str, object] | None:
    def reject(reason: str) -> None:
        if diagnostics is not None:
            diagnostics.update({"status": "rejected", "reason": reason})

    if not path.exists():
        reject("missing")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        reject("unreadable_json")
        return None
    if not isinstance(data, dict):
        reject("invalid_payload_type")
        return None
    if data.get("checkpoint_format_version") != CHECKPOINT_FORMAT_VERSION:
        reject("format_version_mismatch")
        return None
    if data.get("signature") != dict(signature):
        reject("signature_mismatch")
        return None
    metrics = data.get("metrics")
    rankings = data.get("rankings")
    if not isinstance(metrics, dict) or not isinstance(rankings, dict):
        reject("missing_metrics_or_rankings")
        return None

    expected_ids = {str(query_id) for query_id in expected_query_ids}
    try:
        expected_query_count = int(signature.get("expected_query_count", len(expected_ids)))
    except (TypeError, ValueError):
        reject("invalid_expected_query_count")
        return None
    if len(expected_ids) != expected_query_count:
        reject("expected_query_id_count_mismatch")
        return None
    if {str(query_id) for query_id in rankings} != expected_ids:
        reject("query_coverage_mismatch")
        return None
    allowed_depths = {int(depth) for depth in expected_ranking_depths}
    if not allowed_depths or any(depth <= 0 for depth in allowed_depths):
        raise ValueError("expected_ranking_depths must contain positive values")
    signature_depths = signature.get("expected_ranking_depths")
    if signature_depths is not None and {int(depth) for depth in signature_depths} != allowed_depths:
        reject("expected_ranking_depth_signature_mismatch")
        return None
    normalized_rankings: Dict[str, List[str]] = {}
    for query_id, ranking in rankings.items():
        if not isinstance(ranking, list):
            reject("invalid_ranking_type")
            return None
        normalized = [str(chunk_id) for chunk_id in ranking]
        if len(normalized) not in allowed_depths:
            reject("ranking_depth_mismatch")
            return None
        if len(set(normalized)) != len(normalized):
            reject("duplicate_ranking_ids")
            return None
        normalized_rankings[str(query_id)] = normalized

    try:
        metrics_valid = (
            int(metrics.get("seed", -1)) == int(signature["seed"])
            and str(metrics.get("routing_mode", "")) == str(signature["routing_mode"])
            and int(metrics.get("epochs", -1)) == int(signature["epochs"])
            and int(metrics.get("num_interactions", -1)) == int(signature["expected_num_interactions"])
        )
    except (KeyError, TypeError, ValueError):
        metrics_valid = False
    if not metrics_valid:
        reject("metrics_protocol_mismatch")
        return None
    epoch_metrics = metrics.get("epoch_metrics")
    if not isinstance(epoch_metrics, list) or len(epoch_metrics) != int(signature["epochs"]):
        reject("epoch_metrics_mismatch")
        return None

    query_traces = data.get("query_traces", {})
    if not isinstance(query_traces, dict):
        reject("invalid_query_traces")
        return None
    if bool(signature.get("write_query_traces")) and {str(query_id) for query_id in query_traces} != expected_ids:
        reject("query_trace_coverage_mismatch")
        return None
    if diagnostics is not None:
        diagnostics.update({"status": "hit", "reason": "validated"})
    return {"metrics": metrics, "rankings": normalized_rankings, "query_traces": query_traces}


def save_seed_checkpoint(
    path: Path,
    *,
    signature: Mapping[str, object],
    result: Mapping[str, object],
    write_query_traces: bool,
) -> None:
    payload = {
        "checkpoint_format_version": CHECKPOINT_FORMAT_VERSION,
        "signature": dict(signature),
        "metrics": result["metrics"],
        "rankings": result["rankings"],
    }
    if write_query_traces:
        payload["query_traces"] = result.get("query_traces", {})
    write_json_atomic(path, payload)


def run_dataset(
    dataset: str,
    data_dir: Path,
    output_dir: Path,
    encoder,
    *,
    model_name: str,
    routing_modes: Sequence[str],
    feedback_mode: str,
    reward_attribution: str,
    confidence_mode: str,
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
    dense_lite_depth: int,
    bm25_lite_depth: int,
    dense_lite_weight: float,
    bm25_lite_weight: float,
    cluster_primary_weight: float,
    dense_lite_floor_k: int,
    high_confidence_threshold: float,
    mid_confidence_threshold: float,
    drift_threshold: float,
    reward_drop_threshold: float,
    confidence_feedback_floor: float,
    final_context_policy: str = "fixed_topk",
    final_context_high_k: int = 5,
    final_context_mid_k: int = 7,
    high_trust_prob: float,
    high_trust: float,
    low_trust: float,
    high_accuracy: float,
    low_accuracy: float,
    window_size: int,
    epsilon_greedy_rate: float = 0.1,
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
    embedding_cache_dir: Path | None = None,
    use_embedding_cache: bool = False,
    force_embedding_cache: bool = False,
    artifact_cache_dir: Path | None = None,
    use_artifact_cache: bool = False,
    force_artifact_cache: bool = False,
    scale_store_dir: Path | None = None,
    use_scale_store: bool = False,
    scale_store_canonical_name: str = "lotte_technology_search",
    cluster_retrieval_engine: str = "cached_exact_scores",
    query_prefix: str = "",
    corpus_prefix: str = "",
    write_query_traces: bool = False,
    resume_checkpoints: bool = True,
) -> List[Dict[str, object]]:
    if reward_attribution not in REWARD_ATTRIBUTIONS:
        raise ValueError(f"Unsupported reward_attribution: {reward_attribution}")
    if confidence_mode not in CONFIDENCE_MODES:
        raise ValueError(f"Unsupported confidence_mode: {confidence_mode}")
    if final_context_policy not in FINAL_CONTEXT_POLICIES:
        raise ValueError(f"Unsupported final_context_policy: {final_context_policy}")
    if cluster_retrieval_engine not in CLUSTER_RETRIEVAL_ENGINES:
        raise ValueError(f"Unsupported cluster_retrieval_engine: {cluster_retrieval_engine}")
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
        "cluster_retrieval_engine": cluster_retrieval_engine,
    }
    artifact_slug = build_artifact_slug(dataset, run_metadata)

    start = time.perf_counter()
    scale_store_info: Dict[str, object] = {"enabled": False}
    if use_scale_store:
        if corpus_prefix:
            raise ValueError("--corpus-prefix is incompatible with --use-scale-store because corpus embeddings are precomputed")
        corpus_embeddings, scale_store_info = dense_baseline.load_corpus_embeddings_from_scale_store(
            corpus,
            canonical_name=scale_store_canonical_name,
            scale_store_dir=scale_store_dir or DEFAULT_SCALE_STORE_DIR,
        )
        corpus_cache = {
            "cache_hit": True,
            "cache_enabled": False,
            "embedding_path": scale_store_info.get("canonical_embedding_path", ""),
        }
    else:
        corpus_embeddings, corpus_cache = dense_baseline.encode_records_with_optional_cache(
            corpus,
            encoder,
            dataset=dataset,
            model_name=model_name,
            record_kind="corpus",
            batch_size=batch_size,
            text_prefix=corpus_prefix,
            embedding_cache_dir=embedding_cache_dir or DEFAULT_EMBEDDING_CACHE_DIR,
            use_embedding_cache=use_embedding_cache,
            force_embedding_cache=force_embedding_cache,
        )
    query_embeddings, query_cache = dense_baseline.encode_records_with_optional_cache(
        queries,
        encoder,
        dataset=dataset,
        model_name=model_name,
        record_kind="queries",
        batch_size=batch_size,
        text_prefix=query_prefix,
        embedding_cache_dir=embedding_cache_dir or DEFAULT_EMBEDDING_CACHE_DIR,
        use_embedding_cache=use_embedding_cache,
        force_embedding_cache=force_embedding_cache,
    )
    corpus_record_fingerprint = dense_baseline.embedding_cache.records_fingerprint(corpus, "corpus")
    query_record_fingerprint = dense_baseline.embedding_cache.records_fingerprint(queries, "queries")
    corpus_embedding_fingerprint = large_scale_artifacts.embedding_array_fingerprint(corpus_embeddings)
    query_embedding_fingerprint = large_scale_artifacts.embedding_array_fingerprint(query_embeddings)
    code_fingerprint = routing_source_fingerprint()
    dependency_versions = runtime_dependency_versions()
    run_metadata.update({
        "corpus_record_fingerprint": corpus_record_fingerprint,
        "query_record_fingerprint": query_record_fingerprint,
        "corpus_embedding_fingerprint": corpus_embedding_fingerprint,
        "query_embedding_fingerprint": query_embedding_fingerprint,
        "routing_source_fingerprint": code_fingerprint,
        "runtime_dependency_versions": dependency_versions,
    })

    max_dense_artifact_depth = max(dense_depth, dense_lite_depth)
    max_bm25_artifact_depth = max(bm25_depth, bm25_lite_depth)
    artifact_dir = artifact_cache_dir or DEFAULT_ARTIFACT_CACHE_DIR
    dense_rankings_by_qid = None
    bm25_rankings_by_qid = None
    dense_ranking_cache: Dict[str, object] = {"cache_hit": False, "cache_enabled": False}
    bm25_ranking_cache: Dict[str, object] = {"cache_hit": False, "cache_enabled": False}
    context_cache_by_seed: Dict[int, Dict[str, object]] = {}
    context_artifacts_by_seed: Dict[int, Mapping[str, np.ndarray]] = {}
    arm_row_indices_by_seed: Dict[int, tuple[np.ndarray, ...]] = {}
    query_corpus_scores: np.ndarray | None = None
    query_corpus_score_cache: Dict[str, object] = {"cache_hit": False, "cache_enabled": False}
    if use_artifact_cache:
        if max_dense_artifact_depth > 0:
            dense_rankings_by_qid, dense_ranking_cache = large_scale_artifacts.load_or_compute_dense_rankings(
                corpus,
                queries,
                corpus_embeddings,
                query_embeddings,
                dataset=dataset,
                model_name=model_name,
                depth=max_dense_artifact_depth,
                cache_dir=artifact_dir,
                batch_size=batch_size,
                force=force_artifact_cache,
                corpus_embedding_fingerprint=corpus_embedding_fingerprint,
                query_embedding_fingerprint=query_embedding_fingerprint,
            )
        else:
            dense_rankings_by_qid = {}
            dense_ranking_cache = {"cache_hit": False, "cache_enabled": False, "disabled": True}
        if max_bm25_artifact_depth > 0:
            bm25_rankings_by_qid, bm25_ranking_cache = large_scale_artifacts.load_or_compute_bm25_rankings(
                corpus,
                queries,
                dataset=dataset,
                depth=max_bm25_artifact_depth,
                cache_dir=artifact_dir,
                force=force_artifact_cache,
            )
        else:
            bm25_rankings_by_qid = {}
            bm25_ranking_cache = {"cache_hit": False, "cache_enabled": False, "disabled": True}
        for seed in seeds:
            artifacts, context_cache = large_scale_artifacts.load_or_compute_context_clusters(
                corpus,
                queries,
                corpus_embeddings,
                query_embeddings,
                dataset=dataset,
                model_name=model_name,
                context_dim=context_dim,
                n_clusters=n_clusters,
                seed=seed,
                cache_dir=artifact_dir,
                force=force_artifact_cache,
                corpus_embedding_fingerprint=corpus_embedding_fingerprint,
                query_embedding_fingerprint=query_embedding_fingerprint,
            )
            context_artifacts_by_seed[int(seed)] = artifacts
            context_cache_by_seed[int(seed)] = context_cache
            arm_row_indices_by_seed[int(seed)] = global_linucb.build_arm_row_indices(
                artifacts["arm_labels"],
                n_arms=len(artifacts["centroids"]),
            )
        if cluster_retrieval_engine == "cached_exact_scores":
            query_corpus_scores, query_corpus_score_cache = large_scale_artifacts.load_or_compute_query_corpus_scores(
                corpus,
                queries,
                corpus_embeddings,
                query_embeddings,
                dataset=dataset,
                model_name=model_name,
                cache_dir=artifact_dir,
                force=force_artifact_cache,
                corpus_embedding_fingerprint=corpus_embedding_fingerprint,
                query_embedding_fingerprint=query_embedding_fingerprint,
            )
    elif cluster_retrieval_engine == "cached_exact_scores":
        raise ValueError("cached_exact_scores requires artifact caching; omit --no-artifact-cache")

    preparation_elapsed_sec = time.perf_counter() - start
    artifact_hit_flags: List[bool] = []
    if use_artifact_cache:
        if max_dense_artifact_depth > 0:
            artifact_hit_flags.append(bool(dense_ranking_cache.get("cache_hit", False)))
        if max_bm25_artifact_depth > 0:
            artifact_hit_flags.append(bool(bm25_ranking_cache.get("cache_hit", False)))
        artifact_hit_flags.extend(
            bool(context_cache_by_seed.get(int(seed), {}).get("cache_hit", False))
            for seed in seeds
        )
        if cluster_retrieval_engine == "cached_exact_scores":
            artifact_hit_flags.append(bool(query_corpus_score_cache.get("cache_hit", False)))
    if not use_artifact_cache:
        artifact_cache_state = "disabled"
    elif not artifact_hit_flags:
        artifact_cache_state = "no_required_artifacts"
    elif all(artifact_hit_flags):
        artifact_cache_state = "all_hit"
    elif any(artifact_hit_flags):
        artifact_cache_state = "partial_hit"
    else:
        artifact_cache_state = "all_miss"

    expected_query_ids = {_query_id(query) for query in queries}
    expected_ranking_depths = {min(top_k, len(corpus))}
    if final_context_policy == "confidence_topk":
        expected_ranking_depths.update({
            min(final_context_high_k, top_k, len(corpus)),
            min(final_context_mid_k, top_k, len(corpus)),
        })
    expected_ranking_depths.discard(0)

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / f"linucb_cost_{artifact_slug}_prequential_metrics.json"
    rankings_path = output_dir / f"linucb_cost_{artifact_slug}_prequential_rankings.json"
    traces_path = output_dir / f"linucb_cost_{artifact_slug}_prequential_traces.json"
    checkpoint_signature_base: Dict[str, object] = {
        "checkpoint_format_version": CHECKPOINT_FORMAT_VERSION,
        "routing_source_fingerprint": code_fingerprint,
        "runtime_dependency_versions": dependency_versions,
        "dataset": dataset,
        "artifact_slug": artifact_slug,
        "model": model_name,
        "corpus_record_fingerprint": corpus_record_fingerprint,
        "query_record_fingerprint": query_record_fingerprint,
        "corpus_embedding_fingerprint": corpus_embedding_fingerprint,
        "query_embedding_fingerprint": query_embedding_fingerprint,
        "dense_ranking_artifact_fingerprint": dense_ranking_cache.get("fingerprint", ""),
        "bm25_ranking_artifact_fingerprint": bm25_ranking_cache.get("fingerprint", ""),
        "query_corpus_score_artifact_fingerprint": query_corpus_score_cache.get("fingerprint", ""),
        "dense_ranking_content_fingerprint": dense_ranking_cache.get("content_fingerprint", ""),
        "bm25_ranking_content_fingerprint": bm25_ranking_cache.get("content_fingerprint", ""),
        "query_corpus_score_content_fingerprint": query_corpus_score_cache.get("content_fingerprint", ""),
        "expected_query_count": len(queries),
        "expected_corpus_count": len(corpus),
        "expected_num_interactions": len(queries) * epochs,
        "expected_ranking_depths": sorted(expected_ranking_depths),
        "query_prefix": query_prefix,
        "corpus_prefix": corpus_prefix,
        "feedback_mode": feedback_mode,
        "reward_attribution": reward_attribution,
        "confidence_mode": confidence_mode,
        "final_context_policy": final_context_policy,
        "top_k": top_k,
        "ks": list(ks),
        "epochs": epochs,
        "n_clusters": n_clusters,
        "context_dim": context_dim,
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
        "dense_lite_depth": dense_lite_depth,
        "bm25_lite_depth": bm25_lite_depth,
        "dense_lite_weight": dense_lite_weight,
        "bm25_lite_weight": bm25_lite_weight,
        "cluster_primary_weight": cluster_primary_weight,
        "dense_lite_floor_k": dense_lite_floor_k,
        "high_confidence_threshold": high_confidence_threshold,
        "mid_confidence_threshold": mid_confidence_threshold,
        "drift_threshold": drift_threshold,
        "reward_drop_threshold": reward_drop_threshold,
        "confidence_feedback_floor": confidence_feedback_floor,
        "final_context_high_k": final_context_high_k,
        "final_context_mid_k": final_context_mid_k,
        "high_trust_prob": high_trust_prob,
        "high_trust": high_trust,
        "low_trust": low_trust,
        "high_accuracy": high_accuracy,
        "low_accuracy": low_accuracy,
        "window_size": window_size,
        "epsilon_greedy_rate": epsilon_greedy_rate,
        "run_metadata": run_metadata,
        "gt_coverage": gt_coverage,
        "write_query_traces": write_query_traces,
        "cluster_retrieval_engine": cluster_retrieval_engine,
        "scale_store_canonical_name": scale_store_canonical_name if use_scale_store else "",
    }

    rows: List[Dict[str, object]] = []
    all_rankings: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
    all_query_traces: Dict[str, Dict[str, Dict[str, Dict[str, object]]]] = {}
    for routing_mode in routing_modes:
        routing_mode_started = time.perf_counter()
        checkpoint_hits = 0
        checkpoint_misses = 0
        checkpoint_bypassed = 0
        checkpoint_restore_elapsed_sec = 0.0
        checkpoint_write_elapsed_sec = 0.0
        seed_compute_elapsed_sec = 0.0
        checkpoint_miss_reasons: Dict[str, int] = {}
        seed_results = []
        for seed in seeds:
            signature = {
                **checkpoint_signature_base,
                "routing_mode": routing_mode,
                "seed": int(seed),
                "context_cluster_artifact_fingerprint": context_cache_by_seed.get(int(seed), {}).get(
                    "fingerprint", ""
                ),
                "context_cluster_content_fingerprint": context_cache_by_seed.get(int(seed), {}).get(
                    "content_fingerprint", ""
                ),
            }
            checkpoint_path = seed_checkpoint_path(output_dir, artifact_slug, routing_mode, int(seed))
            checkpoint_result = None
            if resume_checkpoints:
                checkpoint_diagnostics: Dict[str, object] = {}
                checkpoint_restore_started = time.perf_counter()
                checkpoint_result = load_seed_checkpoint(
                    checkpoint_path,
                    signature,
                    expected_query_ids=expected_query_ids,
                    expected_ranking_depths=expected_ranking_depths,
                    diagnostics=checkpoint_diagnostics,
                )
                checkpoint_restore_elapsed_sec += time.perf_counter() - checkpoint_restore_started
                if checkpoint_result is None:
                    checkpoint_misses += 1
                    miss_reason = str(checkpoint_diagnostics.get("reason", "unknown"))
                    checkpoint_miss_reasons[miss_reason] = checkpoint_miss_reasons.get(miss_reason, 0) + 1
            else:
                checkpoint_bypassed += 1
            if checkpoint_result is not None:
                checkpoint_hits += 1
                print(f"  checkpoint hit: mode={routing_mode} seed={seed}")
                seed_results.append(checkpoint_result)
                continue

            progress_path = output_dir / "progress" / (
                f"linucb_cost_{artifact_slug}__{routing_mode}__seed{seed}.json"
            )

            def write_progress(progress: Mapping[str, object], *, path: Path = progress_path) -> None:
                write_json_atomic(path, {
                    "status": "running",
                    "signature": signature,
                    "progress": dict(progress),
                })

            seed_compute_started = time.perf_counter()
            result = run_prequential_seed(
                corpus,
                queries,
                corpus_embeddings,
                query_embeddings,
                seed=seed,
                routing_mode=routing_mode,
                feedback_mode=feedback_mode,
                reward_attribution=reward_attribution,
                confidence_mode=confidence_mode,
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
                dense_lite_depth=dense_lite_depth,
                bm25_lite_depth=bm25_lite_depth,
                dense_lite_weight=dense_lite_weight,
                bm25_lite_weight=bm25_lite_weight,
                cluster_primary_weight=cluster_primary_weight,
                dense_lite_floor_k=dense_lite_floor_k,
                high_confidence_threshold=high_confidence_threshold,
                mid_confidence_threshold=mid_confidence_threshold,
                drift_threshold=drift_threshold,
                reward_drop_threshold=reward_drop_threshold,
                confidence_feedback_floor=confidence_feedback_floor,
                final_context_policy=final_context_policy,
                final_context_high_k=final_context_high_k,
                final_context_mid_k=final_context_mid_k,
                high_trust_prob=high_trust_prob,
                high_trust=high_trust,
                low_trust=low_trust,
                high_accuracy=high_accuracy,
                low_accuracy=low_accuracy,
                window_size=window_size,
                epsilon_greedy_rate=epsilon_greedy_rate,
                shared_context_artifacts=context_artifacts_by_seed.get(int(seed)),
                dense_rankings_by_qid=dense_rankings_by_qid,
                bm25_rankings_by_qid=bm25_rankings_by_qid,
                cluster_retrieval_engine=cluster_retrieval_engine,
                arm_row_indices=arm_row_indices_by_seed.get(int(seed)),
                query_corpus_scores=query_corpus_scores,
                progress_callback=write_progress,
            )
            seed_compute_elapsed_sec += time.perf_counter() - seed_compute_started
            checkpoint_write_started = time.perf_counter()
            save_seed_checkpoint(
                checkpoint_path,
                signature=signature,
                result=result,
                write_query_traces=write_query_traces,
            )
            checkpoint_write_elapsed_sec += time.perf_counter() - checkpoint_write_started
            print(f"  checkpoint wrote: mode={routing_mode} seed={seed} -> {checkpoint_path}")
            write_json_atomic(progress_path, {
                "status": "completed",
                "signature": signature,
                "checkpoint_path": str(checkpoint_path),
            })
            seed_results.append(result)
        routing_mode_elapsed_sec = time.perf_counter() - routing_mode_started
        elapsed_sec = time.perf_counter() - start
        per_seed_metrics = [result["metrics"] for result in seed_results]
        representative = per_seed_metrics[0]
        aggregated = aggregate_seed_metrics(per_seed_metrics)
        if checkpoint_hits == len(seeds):
            runtime_measurement_class = "checkpoint_restore"
        elif checkpoint_hits > 0:
            runtime_measurement_class = "mixed_checkpoint_restore_and_compute"
        elif artifact_cache_state == "all_hit":
            runtime_measurement_class = "warm_artifact_cache_compute"
        elif use_artifact_cache:
            runtime_measurement_class = "artifact_build_or_partial_cache_compute"
        else:
            runtime_measurement_class = "uncached_compute"
        metadata = {
            "dataset": dataset,
            "method": f"linucb_cost_{routing_mode}",
            "model": model_name,
            "query_prefix": query_prefix,
            "corpus_prefix": corpus_prefix,
            "protocol": "prequential_cost_aware_feedback",
            "routing_mode": routing_mode,
            "feedback_mode": feedback_mode,
            "reward_attribution": reward_attribution,
            "confidence_mode": confidence_mode,
            "final_context_policy": final_context_policy,
            "cluster_retrieval_engine": cluster_retrieval_engine,
            "feedback_source": (
                "simulated_feedback_recorded_no_policy_update"
                if routing_mode in {
                    "static_nearest_ensemble",
                    "static_nearest_gated",
                    "uniform_random_ensemble",
                    "random_partition_static_ensemble",
                }
                else "trust_weighted_simulated_user_feedback"
            ),
            "online_learning_scope": (
                {
                    "static_nearest_ensemble": "static_nearest_centroid_multiroute_no_policy_update",
                    "static_nearest_gated": "static_nearest_centroid_cost_gated_no_policy_update",
                    "uniform_random_ensemble": "uniform_random_multiroute_no_policy_update",
                    "random_partition_feedback_ensemble": (
                        "randomized_partition_with_contextual_feedback_policy"
                    ),
                    "random_partition_static_ensemble": (
                        "randomized_partition_nearest_centroid_no_policy_update"
                    ),
                    "epsilon_greedy_ensemble": "non_contextual_epsilon_greedy_multiroute",
                }.get(routing_mode, "confidence_gated_cost_aware_routing")
            ),
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
            "epsilon_greedy_rate": epsilon_greedy_rate,
            "dense_depth": dense_depth,
            "bm25_depth": bm25_depth,
            "cluster_depth": cluster_depth,
            "dense_weight": dense_weight,
            "bm25_weight": bm25_weight,
            "cluster_weight": cluster_weight,
            "rrf_k": rrf_k,
            "dense_floor_k": dense_floor_k,
            "dense_lite_depth": dense_lite_depth,
            "bm25_lite_depth": bm25_lite_depth,
            "dense_lite_weight": dense_lite_weight,
            "bm25_lite_weight": bm25_lite_weight,
            "cluster_primary_weight": cluster_primary_weight,
            "dense_lite_floor_k": dense_lite_floor_k,
            "high_confidence_threshold": high_confidence_threshold,
            "mid_confidence_threshold": mid_confidence_threshold,
            "drift_threshold": drift_threshold,
            "reward_drop_threshold": reward_drop_threshold,
            "confidence_feedback_floor": confidence_feedback_floor,
            "final_context_high_k": final_context_high_k,
            "final_context_mid_k": final_context_mid_k,
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
            "embedding_cache_enabled": bool(use_embedding_cache),
            "embedding_cache_dir": str(embedding_cache_dir or DEFAULT_EMBEDDING_CACHE_DIR) if use_embedding_cache else "",
            "corpus_embedding_cache_hit": corpus_cache.get("cache_hit", False),
            "query_embedding_cache_hit": query_cache.get("cache_hit", False),
            "corpus_embedding_cache_path": corpus_cache.get("embedding_path", ""),
            "query_embedding_cache_path": query_cache.get("embedding_path", ""),
            "corpus_record_fingerprint": corpus_record_fingerprint,
            "query_record_fingerprint": query_record_fingerprint,
            "corpus_embedding_fingerprint": corpus_embedding_fingerprint,
            "query_embedding_fingerprint": query_embedding_fingerprint,
            "routing_source_fingerprint": code_fingerprint,
            "runtime_dependency_versions": dependency_versions,
            "artifact_cache_enabled": bool(use_artifact_cache),
            "artifact_cache_dir": str(artifact_dir) if use_artifact_cache else "",
            "artifact_cache_state": artifact_cache_state,
            "dense_ranking_cache_hit": dense_ranking_cache.get("cache_hit", False),
            "bm25_ranking_cache_hit": bm25_ranking_cache.get("cache_hit", False),
            "context_cluster_cache_hits": [
                bool(context_cache_by_seed.get(int(seed), {}).get("cache_hit", False))
                for seed in seeds
            ],
            "scale_store_enabled": bool(use_scale_store),
            "scale_store_dir": str(scale_store_dir or DEFAULT_SCALE_STORE_DIR) if use_scale_store else "",
            "scale_store_canonical_name": scale_store_canonical_name if use_scale_store else "",
            "scale_store_canonical_count": scale_store_info.get("canonical_count", 0),
            "scale_store_selected_rows": scale_store_info.get("selected_rows", 0),
            "dense_ranking_artifact_path": dense_ranking_cache.get("artifact_path", ""),
            "bm25_ranking_artifact_path": bm25_ranking_cache.get("artifact_path", ""),
            "context_cluster_artifact_paths": [
                context_cache_by_seed.get(int(seed), {}).get("artifact_path", "")
                for seed in seeds
            ],
            "query_corpus_score_cache_hit": query_corpus_score_cache.get("cache_hit", False),
            "query_corpus_score_artifact_path": query_corpus_score_cache.get("artifact_path", ""),
            "dense_ranking_artifact_fingerprint": dense_ranking_cache.get("fingerprint", ""),
            "bm25_ranking_artifact_fingerprint": bm25_ranking_cache.get("fingerprint", ""),
            "context_cluster_artifact_fingerprints": [
                context_cache_by_seed.get(int(seed), {}).get("fingerprint", "")
                for seed in seeds
            ],
            "query_corpus_score_artifact_fingerprint": query_corpus_score_cache.get("fingerprint", ""),
            "dense_ranking_content_fingerprint": dense_ranking_cache.get("content_fingerprint", ""),
            "bm25_ranking_content_fingerprint": bm25_ranking_cache.get("content_fingerprint", ""),
            "context_cluster_content_fingerprints": [
                context_cache_by_seed.get(int(seed), {}).get("content_fingerprint", "")
                for seed in seeds
            ],
            "query_corpus_score_content_fingerprint": query_corpus_score_cache.get("content_fingerprint", ""),
            "checkpoint_format_version": CHECKPOINT_FORMAT_VERSION,
            "checkpoint_resume_enabled": bool(resume_checkpoints),
            "checkpoint_hits": checkpoint_hits,
            "checkpoint_misses": checkpoint_misses,
            "checkpoint_bypassed": checkpoint_bypassed,
            "checkpoint_miss_reasons": checkpoint_miss_reasons,
            "runtime_measurement_class": runtime_measurement_class,
            "preparation_elapsed_sec": round(preparation_elapsed_sec, 3),
            "routing_mode_elapsed_sec": round(routing_mode_elapsed_sec, 3),
            "seed_compute_elapsed_sec": round(seed_compute_elapsed_sec, 3),
            "checkpoint_restore_elapsed_sec": round(checkpoint_restore_elapsed_sec, 3),
            "checkpoint_write_elapsed_sec": round(checkpoint_write_elapsed_sec, 3),
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
        all_rankings[routing_mode] = {
            str(result["metrics"]["seed"]): result["rankings"]
            for result in seed_results
        }
        if write_query_traces:
            all_query_traces[routing_mode] = {
                str(result["metrics"]["seed"]): result["query_traces"]
                for result in seed_results
            }
        write_json_atomic(metrics_path, rows)
        write_json_atomic(rankings_path, all_rankings)
        if write_query_traces:
            write_json_atomic(traces_path, all_query_traces)

    write_json_atomic(metrics_path, rows)
    write_json_atomic(rankings_path, all_rankings)
    if write_query_traces:
        write_json_atomic(traces_path, all_query_traces)
    return rows


def _stringify_csv_value(value: object) -> object:
    return global_linucb._stringify_csv_value(value)


def update_summary(summary_path: Path, rows: Iterable[Mapping]) -> None:
    new_rows = list(rows)
    if not new_rows:
        return
    existing: Dict[tuple[str, ...], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(
                    row.get("dataset", ""),
                    row.get("method", ""),
                    row.get("model", ""),
                    row.get("query_prefix", ""),
                    row.get("corpus_prefix", ""),
                    row.get("routing_mode", ""),
                    row.get("cluster_retrieval_engine", "on_demand"),
                    row.get("reward_attribution", ""),
                    row.get("confidence_mode", ""),
                    row.get("final_context_policy", ""),
                    row.get("scope", ""),
                    row.get("query_split", ""),
                    row.get("num_queries", ""),
                )] = row
    for row in new_rows:
        existing[(
            str(row["dataset"]),
            str(row["method"]),
            str(row.get("model", "")),
            str(row.get("query_prefix", "")),
            str(row.get("corpus_prefix", "")),
            str(row.get("routing_mode", "")),
            str(row.get("cluster_retrieval_engine", "on_demand")),
            str(row.get("reward_attribution", "")),
            str(row.get("confidence_mode", "")),
            str(row.get("final_context_policy", "")),
            str(row.get("scope", "")),
            str(row.get("query_split", "")),
            str(row.get("num_queries", "")),
        )] = row

    preferred = [
        "dataset",
        "method",
        "routing_mode",
        "cluster_retrieval_engine",
        "feedback_mode",
        "reward_attribution",
        "confidence_mode",
        "final_context_policy",
        "model",
        "query_prefix",
        "corpus_prefix",
        "protocol",
        "task_type",
        "scope",
        "query_split",
        "corpus_scope",
        "corpus_sampling",
        "num_queries",
        "num_skipped_no_gt",
        "gt_query_coverage",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "top_k",
        "metric_ks",
        "num_seeds",
        "seeds",
        "epochs",
        "dense_depth",
        "bm25_depth",
        "cluster_depth",
        "dense_lite_depth",
        "bm25_lite_depth",
        "dense_floor_k",
        "dense_lite_floor_k",
        "high_confidence_threshold",
        "mid_confidence_threshold",
        "drift_threshold",
        "reward_drop_threshold",
        "confidence_feedback_floor",
        "final_context_high_k",
        "final_context_mid_k",
        "epsilon_greedy_rate",
        "embedding_cache_enabled",
        "corpus_embedding_cache_hit",
        "query_embedding_cache_hit",
        "artifact_cache_enabled",
        "artifact_cache_state",
        "dense_ranking_cache_hit",
        "bm25_ranking_cache_hit",
        "context_cluster_cache_hits",
        "query_corpus_score_cache_hit",
        "scale_store_enabled",
        "scale_store_selected_rows",
        "checkpoint_resume_enabled",
        "checkpoint_hits",
        "checkpoint_misses",
        "checkpoint_bypassed",
        "runtime_measurement_class",
        "preparation_elapsed_sec",
        "routing_mode_elapsed_sec",
        "seed_compute_elapsed_sec",
        "checkpoint_restore_elapsed_sec",
        "checkpoint_write_elapsed_sec",
    ]
    preferred_set = set(preferred) | {"elapsed_sec", "notes"}
    metric_keys = sorted({
        key
        for row in existing.values()
        for key in row
        if key not in preferred_set
        and (
            "@" in key
            or key.endswith("_mean")
            or key.endswith("_rate_mean")
            or key.endswith("_gain_mean")
            or key.endswith("_delta_mean")
            or key.endswith("_cost_mean")
            or key.endswith("_candidates_mean")
        )
    })
    fieldnames = [*preferred, *metric_keys, "elapsed_sec", "notes"]
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow({
                name: _stringify_csv_value(value)
                for name, value in existing[key].items()
            })


def write_markdown_table(summary_path: Path, markdown_path: Path) -> None:
    if not summary_path.exists():
        return
    with summary_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    columns = [
        "dataset",
        "routing_mode",
        "reward_attribution",
        "confidence_mode",
        "final_context_policy",
        "scope",
        "query_split",
        "num_queries",
        "hit@10_mean",
        "recall@10_mean",
        "evidence_recall@10_mean",
        "quality_cost_ratio@10_mean",
        "last_epoch_true_reward_mean",
        "last_epoch_final_true_reward_mean",
        "last_epoch_route_true_reward_mean",
        "avg_source_candidate_cost_mean",
        "avg_final_context_k_mean",
        "compact_context_rate_mean",
        "high_confidence_compact_rate_mean",
        "mid_confidence_compact_rate_mean",
        "fallback_full_topk_context_rate_mean",
        "dense_query_rate_mean",
        "dense_saved_rate_mean",
        "static_nearest_ensemble_rate_mean",
        "uniform_random_ensemble_rate_mean",
        "random_partition_feedback_ensemble_rate_mean",
        "random_partition_static_ensemble_rate_mean",
        "epsilon_greedy_ensemble_rate_mean",
        "linucb_primary_rate_mean",
        "hybrid_lite_rate_mean",
        "full_dense_fallback_rate_mean",
        "fallback_low_confidence_rate_mean",
        "fallback_high_drift_rate_mean",
        "fallback_reward_drop_rate_mean",
    ]
    lines = [
        "# Cost-Aware LinUCB Routing Tables",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in sorted(rows, key=lambda item: (item.get("dataset", ""), item.get("scope", ""), item.get("routing_mode", ""))):
        values = []
        for column in columns:
            value = row.get(column, "")
            if value not in ("", None):
                if column == "num_queries":
                    try:
                        value = str(int(float(value)))
                    except ValueError:
                        pass
                elif column.endswith("_mean") or column.startswith("recall@") or column.startswith("hit@"):
                    try:
                        value = f"{float(value):.4f}"
                    except ValueError:
                        pass
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.",
        "- `static_nearest_ensemble` uses the same dense/BM25/cluster fusion surface but selects cluster arms by nearest centroid and applies no feedback policy update.",
        "- `static_nearest_gated` uses nearest-centroid arm selection plus the same cost-aware route shapes, with centroid similarity as a non-learned confidence proxy.",
        "- `uniform_random_ensemble` and `epsilon_greedy_ensemble` are non-contextual arm-selection baselines over the same multi-route retrieval surface.",
        "- `random_partition_feedback_ensemble` preserves the contextual LinUCB feedback estimator but shuffles geometry-derived cluster membership before learning.",
        "- `random_partition_static_ensemble` applies nearest-centroid selection to the same shuffled partition without policy updates.",
        "- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.",
        "- `reward_attribution=cluster_only` updates LinUCB from the selected cluster route alone, separating policy credit from dense/BM25 rescue hits.",
        "- `confidence_mode=route_quality` gates from historical cluster-route reward instead of the LinUCB value estimate.",
        "- `final_context_policy=confidence_topk` reduces final context chunk count only when the selected LinUCB route is confident; it is measured separately from retrieval-stage source cost.",
        "- `hit@k` is the query-level success metric historically reported as `recall@k`; `evidence_recall@k` reports the fraction of all ground-truth chunks retrieved.",
        "- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.",
    ])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_sentence_transformer(model_name: str, *, device: str | None = None, local_files_only: bool = False):
    return dense_baseline.load_sentence_transformer(model_name, device=device, local_files_only=local_files_only)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run confidence-gated cost-aware LinUCB routing experiment")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--query-prefix", default="", help="Optional prefix applied only to query text before encoding")
    parser.add_argument("--corpus-prefix", default="", help="Optional prefix applied only to corpus text before encoding")
    parser.add_argument("--embedding-cache-dir", type=Path, default=DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--no-embedding-cache", action="store_true", help="Disable reusable on-disk embeddings")
    parser.add_argument("--force-embedding-cache", action="store_true", help="Recompute embeddings even when cache files exist")
    parser.add_argument("--artifact-cache-dir", type=Path, default=DEFAULT_ARTIFACT_CACHE_DIR)
    parser.add_argument("--no-artifact-cache", action="store_true", help="Disable reusable dense/BM25/context retrieval artifacts")
    parser.add_argument("--force-artifact-cache", action="store_true", help="Recompute retrieval artifacts even when cache files exist")
    parser.add_argument("--scale-store-dir", type=Path, default=DEFAULT_SCALE_STORE_DIR)
    parser.add_argument("--use-scale-store", action="store_true", help="Load corpus embeddings from canonical LoTTE scale store")
    parser.add_argument("--scale-store-canonical-name", default="lotte_technology_search")
    parser.add_argument(
        "--cluster-retrieval-engine",
        default="cached_exact_scores",
        choices=CLUSTER_RETRIEVAL_ENGINES,
        help="Use cached exact query-corpus scores or legacy on-demand arm retrieval",
    )
    parser.add_argument("--routing-modes", default="full_multi_route,gated_cost_aware")
    parser.add_argument("--feedback-mode", default="trust_weighted", choices=FEEDBACK_MODES)
    parser.add_argument("--reward-attribution", default="final_fused", choices=REWARD_ATTRIBUTIONS)
    parser.add_argument("--confidence-mode", default="value", choices=CONFIDENCE_MODES)
    parser.add_argument("--final-context-policy", default="fixed_topk", choices=FINAL_CONTEXT_POLICIES)
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
    parser.add_argument("--dense-lite-depth", type=int, default=20)
    parser.add_argument("--bm25-lite-depth", type=int, default=20)
    parser.add_argument("--dense-lite-weight", type=float, default=0.8)
    parser.add_argument("--bm25-lite-weight", type=float, default=0.5)
    parser.add_argument("--cluster-primary-weight", type=float, default=2.0)
    parser.add_argument("--dense-lite-floor-k", type=int, default=2)
    parser.add_argument("--high-confidence-threshold", type=float, default=0.65)
    parser.add_argument("--mid-confidence-threshold", type=float, default=0.35)
    parser.add_argument("--drift-threshold", type=float, default=1.0)
    parser.add_argument("--reward-drop-threshold", type=float, default=0.0)
    parser.add_argument("--confidence-feedback-floor", type=float, default=8.0)
    parser.add_argument("--final-context-high-k", type=int, default=5)
    parser.add_argument("--final-context-mid-k", type=int, default=7)
    parser.add_argument("--high-trust-prob", type=float, default=0.7)
    parser.add_argument("--high-trust", type=float, default=1.0)
    parser.add_argument("--low-trust", type=float, default=0.25)
    parser.add_argument("--high-accuracy", type=float, default=0.9)
    parser.add_argument("--low-accuracy", type=float, default=0.55)
    parser.add_argument("--window-size", type=int, default=50)
    parser.add_argument("--epsilon-greedy-rate", type=float, default=0.1)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--max-corpus", type=int, default=None)
    parser.add_argument("--query-split", default=None)
    parser.add_argument(
        "--corpus-sampling",
        default="auto",
        choices=sorted(experiment_guardrails.CORPUS_SAMPLING_STRATEGIES),
    )
    parser.add_argument("--sampling-seed", type=int, default=13)
    parser.add_argument(
        "--write-query-traces",
        action="store_true",
        help="Write final-epoch per-query confidence and route traces for attribution audits.",
    )
    parser.add_argument(
        "--no-resume-checkpoints",
        action="store_true",
        help="Disable per-routing-mode/per-seed checkpoint reuse.",
    )
    args = parser.parse_args(argv)

    datasets = parse_datasets(args.dataset)
    routing_modes = parse_list(args.routing_modes, ROUTING_MODES, label="routing modes")
    ks = parse_ints(args.ks)
    seeds = parse_ints(args.seeds)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    all_rows: List[Dict[str, object]] = []
    for dataset in datasets:
        print(f"Running cost-aware LinUCB routing: {dataset}")
        rows = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            routing_modes=routing_modes,
            feedback_mode=args.feedback_mode,
            reward_attribution=args.reward_attribution,
            confidence_mode=args.confidence_mode,
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
            dense_lite_depth=args.dense_lite_depth,
            bm25_lite_depth=args.bm25_lite_depth,
            dense_lite_weight=args.dense_lite_weight,
            bm25_lite_weight=args.bm25_lite_weight,
            cluster_primary_weight=args.cluster_primary_weight,
            dense_lite_floor_k=args.dense_lite_floor_k,
            high_confidence_threshold=args.high_confidence_threshold,
            mid_confidence_threshold=args.mid_confidence_threshold,
            drift_threshold=args.drift_threshold,
            reward_drop_threshold=args.reward_drop_threshold,
            confidence_feedback_floor=args.confidence_feedback_floor,
            final_context_policy=args.final_context_policy,
            final_context_high_k=args.final_context_high_k,
            final_context_mid_k=args.final_context_mid_k,
            high_trust_prob=args.high_trust_prob,
            high_trust=args.high_trust,
            low_trust=args.low_trust,
            high_accuracy=args.high_accuracy,
            low_accuracy=args.low_accuracy,
            window_size=args.window_size,
            epsilon_greedy_rate=args.epsilon_greedy_rate,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
            embedding_cache_dir=args.embedding_cache_dir,
            use_embedding_cache=not args.no_embedding_cache,
            force_embedding_cache=args.force_embedding_cache,
            artifact_cache_dir=args.artifact_cache_dir,
            use_artifact_cache=not args.no_artifact_cache,
            force_artifact_cache=args.force_artifact_cache,
            scale_store_dir=args.scale_store_dir,
            use_scale_store=args.use_scale_store,
            scale_store_canonical_name=args.scale_store_canonical_name,
            cluster_retrieval_engine=args.cluster_retrieval_engine,
            query_prefix=args.query_prefix,
            corpus_prefix=args.corpus_prefix,
            write_query_traces=args.write_query_traces,
            resume_checkpoints=not args.no_resume_checkpoints,
        )
        all_rows.extend(rows)
        for row in rows:
            print(
                f"  mode={row['routing_mode']} queries={row.get('num_queries')} "
                f"reward_attr={row.get('reward_attribution')} "
                f"confidence={row.get('confidence_mode')} "
                f"recall@10={row.get('recall@10_mean', 0.0):.4f} "
                f"last_reward={row.get('last_epoch_true_reward_mean', 0.0):.4f} "
                f"avg_cost={row.get('avg_source_candidate_cost_mean', 0.0):.2f} "
                f"avg_final_k={row.get('avg_final_context_k_mean', 0.0):.2f} "
                f"dense_rate={row.get('dense_query_rate_mean', 0.0):.4f} "
                f"primary_rate={row.get('linucb_primary_rate_mean', 0.0):.4f}"
            )

    summary_path = args.output_dir / "linucb_cost_summary.csv"
    update_summary(summary_path, all_rows)
    write_markdown_table(summary_path, args.output_dir / "linucb_cost_tables.md")
    print(f"Summary: {summary_path}")
    print(f"Markdown: {args.output_dir / 'linucb_cost_tables.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
