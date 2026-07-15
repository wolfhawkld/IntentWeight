#!/usr/bin/env python3
"""Profile IntentRoute's artifact-backed online path and feedback overhead.

This is an operational measurement harness, not a new retrieval-quality
experiment. It uses the already-evaluated MiniLM artifacts and reports cache
materialization separately from per-interaction routing. Controlled simulated
feedback is timed as a local controller update; this does not claim real-user
RLHF validation.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import pickle
import platform
import resource
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_EMBEDDING_CACHE_DIR = SCRIPT_DIR.parent / "data" / "embeddings"
DEFAULT_ARTIFACT_CACHE_DIR = SCRIPT_DIR.parent / "data" / "retrieval_artifacts"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results" / "task71_2_systems_profile"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing = load_module("task71_2_routing", SCRIPT_DIR / "linucb_cost_aware_routing.py")
artifacts = routing.large_scale_artifacts
embedding_cache = artifacts.embedding_cache
dense_baseline = routing.dense_baseline
global_linucb = routing.global_linucb


def parse_csv(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items:
        raise ValueError("Expected at least one comma-separated value")
    return items


def percentile_ms(values_ns: Sequence[int], percentile: float) -> float | None:
    if not values_ns:
        return None
    return round(float(np.percentile(np.asarray(values_ns, dtype=np.float64), percentile)) / 1_000_000.0, 4)


def summarize_stage_timings(stage_timings: Mapping[str, Sequence[int]]) -> dict[str, dict[str, float | int | None]]:
    summary: dict[str, dict[str, float | int | None]] = {}
    for stage, values in sorted(stage_timings.items()):
        values_list = [int(value) for value in values]
        summary[stage] = {
            "calls": len(values_list),
            "total_ms": round(sum(values_list) / 1_000_000.0, 4),
            "p50_ms": percentile_ms(values_list, 50),
            "p95_ms": percentile_ms(values_list, 95),
            "max_ms": percentile_ms(values_list, 100),
        }
    return summary


def read_cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return platform.processor() or "unknown"
    for line in cpuinfo.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.lower().startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def read_memory_bytes() -> int | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            return int(parts[1]) * 1024
    return None


def current_peak_rss_bytes() -> int:
    # Linux ru_maxrss is KiB. The experiments are run in WSL/Linux.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def hardware_metadata() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "cpu_model": read_cpu_model(),
        "logical_cpus": os.cpu_count(),
        "memory_total_bytes": read_memory_bytes(),
    }


def file_size(path: str | Path | None) -> int:
    if not path:
        return 0
    candidate = Path(path)
    return candidate.stat().st_size if candidate.exists() and candidate.is_file() else 0


def require_embedding_cache(
    records: Sequence[Mapping[str, Any]],
    *,
    dataset: str,
    record_kind: str,
    model_name: str,
    cache_dir: Path,
) -> None:
    fingerprint = embedding_cache.records_fingerprint(records, record_kind)
    embedding_path, metadata_path = embedding_cache.cache_paths(
        cache_dir,
        dataset=dataset,
        model_name=model_name,
        record_kind=record_kind,
        fingerprint=fingerprint,
        count=len(records),
    )
    if not embedding_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing {record_kind} embedding cache for {dataset}. "
            f"Expected {embedding_path}. Build embeddings before systems profiling."
        )


def require_artifact_cache(
    *,
    dataset: str,
    kind: str,
    corpus: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
    model_name: str,
    params: Mapping[str, Any],
    extension: str,
    cache_dir: Path,
) -> None:
    payload = artifacts._artifact_payload(
        dataset=dataset,
        artifact_kind=kind,
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params=params,
    )
    fingerprint = artifacts._payload_fingerprint(payload)
    artifact_path, metadata_path = artifacts._artifact_paths(
        cache_dir,
        dataset=dataset,
        artifact_kind=kind,
        fingerprint=fingerprint,
        extension=extension,
    )
    if not artifact_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing {kind} cache for {dataset}. Expected {artifact_path}. "
            "The profiler will not silently rebuild a large artifact."
        )


def timed_load(name: str, loader: Callable[[], Any], load_timings: dict[str, float]) -> Any:
    started = time.perf_counter_ns()
    value = loader()
    load_timings[name] = round((time.perf_counter_ns() - started) / 1_000_000.0, 4)
    return value


def load_profile_inputs(
    *,
    dataset: str,
    data_dir: Path,
    model_name: str,
    embedding_cache_dir: Path,
    artifact_cache_dir: Path,
    max_queries: int | None,
    seed: int,
    cluster_retrieval_engine: str,
) -> tuple[dict[str, Any], dict[str, float]]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    if not corpus_path.exists() or not queries_path.exists():
        raise FileNotFoundError(
            f"Missing source JSON for {dataset}: corpus={corpus_path.exists()}, queries={queries_path.exists()}."
        )

    load_timings: dict[str, float] = {}
    corpus = timed_load("load_corpus_json", lambda: global_linucb.load_json_list(corpus_path), load_timings)
    all_queries = timed_load("load_queries_json", lambda: global_linucb.load_json_list(queries_path), load_timings)
    queries = list(all_queries if max_queries is None else all_queries[:max_queries])
    if not queries:
        raise ValueError("No queries selected for profile")

    require_embedding_cache(corpus, dataset=dataset, record_kind="corpus", model_name=model_name, cache_dir=embedding_cache_dir)
    require_embedding_cache(queries, dataset=dataset, record_kind="queries", model_name=model_name, cache_dir=embedding_cache_dir)
    corpus_embeddings, corpus_info = timed_load(
        "load_corpus_embeddings",
        lambda: embedding_cache.load_or_compute_embeddings(
            corpus,
            dataset=dataset,
            model_name=model_name,
            record_kind="corpus",
            encoder=None,
            batch_size=64,
            cache_dir=embedding_cache_dir,
        ),
        load_timings,
    )
    query_embeddings, query_info = timed_load(
        "load_query_embeddings",
        lambda: embedding_cache.load_or_compute_embeddings(
            queries,
            dataset=dataset,
            model_name=model_name,
            record_kind="queries",
            encoder=None,
            batch_size=64,
            cache_dir=embedding_cache_dir,
        ),
        load_timings,
    )
    if not corpus_info.get("cache_hit") or not query_info.get("cache_hit"):
        raise RuntimeError("Systems profiling requires existing embedding caches; an unexpected build was attempted")

    dense_depth = 100
    bm25_depth = 100
    context_dim = 64
    n_clusters = 32
    require_artifact_cache(
        dataset=dataset,
        kind="dense_rankings",
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params={"depth": dense_depth, "ranking_engine": "exact_cosine_numpy_lexsort_v1"},
        extension="json",
        cache_dir=artifact_cache_dir,
    )
    require_artifact_cache(
        dataset=dataset,
        kind="bm25_rankings",
        corpus=corpus,
        queries=queries,
        model_name="sparse-bm25",
        params={"depth": bm25_depth, "ranking_engine": "query_term_bounded_bm25_v1"},
        extension="json",
        cache_dir=artifact_cache_dir,
    )
    require_artifact_cache(
        dataset=dataset,
        kind="context_clusters",
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params={
            "context_dim": context_dim,
            "n_clusters": n_clusters,
            "seed": seed,
            "projection_engine": "pca_corpus_fit_v1",
            "cluster_engine": "minibatch_kmeans_v1",
        },
        extension="npz",
        cache_dir=artifact_cache_dir,
    )
    if cluster_retrieval_engine == "cached_exact_scores":
        require_artifact_cache(
            dataset=dataset,
            kind="query_corpus_scores",
            corpus=corpus,
            queries=queries,
            model_name=model_name,
            params={"score_engine": "exact_numpy_rowwise_matvec_v1", "dtype": "float32"},
            extension="npy",
            cache_dir=artifact_cache_dir,
        )

    dense_rankings, dense_info = timed_load(
        "load_dense_rankings",
        lambda: artifacts.load_or_compute_dense_rankings(
            corpus, queries, corpus_embeddings, query_embeddings,
            dataset=dataset, model_name=model_name, depth=dense_depth, cache_dir=artifact_cache_dir,
        ),
        load_timings,
    )
    bm25_rankings, bm25_info = timed_load(
        "load_bm25_rankings",
        lambda: artifacts.load_or_compute_bm25_rankings(
            corpus, queries, dataset=dataset, depth=bm25_depth, cache_dir=artifact_cache_dir,
        ),
        load_timings,
    )
    context_artifacts, context_info = timed_load(
        "load_context_clusters",
        lambda: artifacts.load_or_compute_context_clusters(
            corpus, queries, corpus_embeddings, query_embeddings,
            dataset=dataset, model_name=model_name, context_dim=context_dim,
            n_clusters=n_clusters, seed=seed, cache_dir=artifact_cache_dir,
        ),
        load_timings,
    )
    if not all(info.get("cache_hit") for info in (dense_info, bm25_info, context_info)):
        raise RuntimeError("Systems profiling requires existing retrieval artifacts; an unexpected build was attempted")

    arm_row_indices = None
    query_corpus_scores = None
    score_info: Mapping[str, Any] = {"cache_hit": False}
    if cluster_retrieval_engine == "cached_exact_scores":
        query_corpus_scores, score_info = timed_load(
            "load_query_corpus_scores",
            lambda: artifacts.load_or_compute_query_corpus_scores(
                corpus, queries, corpus_embeddings, query_embeddings,
                dataset=dataset, model_name=model_name, cache_dir=artifact_cache_dir,
            ),
            load_timings,
        )
        if not score_info.get("cache_hit"):
            raise RuntimeError("Systems profiling requires an existing exact-score cache")
        arm_row_indices = global_linucb.build_arm_row_indices(
            context_artifacts["arm_labels"], n_arms=len(context_artifacts["centroids"]),
        )

    return {
        "corpus": corpus,
        "queries": queries,
        "corpus_embeddings": corpus_embeddings,
        "query_embeddings": query_embeddings,
        "dense_rankings": dense_rankings,
        "bm25_rankings": bm25_rankings,
        "context_artifacts": context_artifacts,
        "arm_row_indices": arm_row_indices,
        "query_corpus_scores": query_corpus_scores,
        "cache_info": {
            "corpus_embeddings": corpus_info,
            "query_embeddings": query_info,
            "dense_rankings": dense_info,
            "bm25_rankings": bm25_info,
            "context_clusters": context_info,
            "query_corpus_scores": score_info,
        },
    }, load_timings


def route_kwargs(inputs: Mapping[str, Any], *, seed: int, feedback_mode: str, epochs: int, cluster_retrieval_engine: str) -> dict[str, Any]:
    return {
        "seed": seed,
        "routing_mode": "full_multi_route",
        "feedback_mode": feedback_mode,
        "reward_attribution": "final_fused",
        "confidence_mode": "value",
        "epochs": epochs,
        "top_k": 10,
        "ks": (1, 5, 10),
        "n_clusters": 32,
        "context_dim": 64,
        "candidate_arms": 3,
        "alpha": 1.0,
        "alpha_decay": 0.01,
        "alpha_min": 0.3,
        "arm_neighbor_k": 4,
        "arm_decay_sigma": 0.75,
        "propagation_strength": 0.25,
        "feedback_k": 16,
        "feedback_tau": 0.75,
        "feedback_weight": 0.35,
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
        "shared_context_artifacts": inputs["context_artifacts"],
        "dense_rankings_by_qid": inputs["dense_rankings"],
        "bm25_rankings_by_qid": inputs["bm25_rankings"],
        "cluster_retrieval_engine": cluster_retrieval_engine,
        "arm_row_indices": inputs["arm_row_indices"],
        "query_corpus_scores": inputs["query_corpus_scores"],
        "return_state": True,
    }


def feedback_state_profile(runtime_state: Mapping[str, Any]) -> dict[str, Any]:
    policy = runtime_state["policy"]
    in_memory_bytes = int(
        sum(array.nbytes for array in policy.A)
        + sum(array.nbytes for array in policy.b)
        + sum(context.nbytes for context in runtime_state["feedback_contexts"])
    )
    snapshot = {
        "A": policy.A,
        "b": policy.b,
        "pull_counts": policy.pull_counts,
        "total_rewards": policy.total_rewards,
        "feedback_contexts": runtime_state["feedback_contexts"],
        "feedback_arm_rewards": runtime_state["feedback_arm_rewards"],
        "route_reward_sums": runtime_state["route_reward_sums"],
        "route_pull_counts": runtime_state["route_pull_counts"],
        "observed_rewards": runtime_state["observed_rewards"],
    }
    started = time.perf_counter_ns()
    serialized = pickle.dumps(snapshot, protocol=pickle.HIGHEST_PROTOCOL)
    serialize_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    started = time.perf_counter_ns()
    pickle.loads(serialized)
    deserialize_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    return {
        "feedback_context_count": len(runtime_state["feedback_contexts"]),
        "feedback_reward_record_count": len(runtime_state["feedback_arm_rewards"]),
        "in_memory_numeric_bytes": in_memory_bytes,
        "snapshot_pickle_bytes": len(serialized),
        "snapshot_serialize_ms": round(serialize_ms, 4),
        "snapshot_deserialize_ms": round(deserialize_ms, 4),
        "persistence_note": "pickle snapshot is a sizing microbenchmark, not a production persistence protocol",
    }


def profile_query_encoding(
    queries: Sequence[Mapping[str, Any]],
    *,
    model_name: str,
    sample_count: int,
) -> dict[str, Any]:
    if sample_count <= 0:
        return {"enabled": False}
    encoder_started = time.perf_counter_ns()
    encoder = dense_baseline.load_sentence_transformer(model_name, device="cpu", local_files_only=True)
    load_ms = (time.perf_counter_ns() - encoder_started) / 1_000_000.0
    durations: list[int] = []
    for query in queries[:sample_count]:
        started = time.perf_counter_ns()
        embedding_cache.encode_texts(encoder, [str(query.get("text", ""))], batch_size=1)
        durations.append(time.perf_counter_ns() - started)
    return {
        "enabled": True,
        "model_load_ms": round(load_ms, 4),
        "samples": len(durations),
        "p50_ms": percentile_ms(durations, 50),
        "p95_ms": percentile_ms(durations, 95),
        "max_ms": percentile_ms(durations, 100),
        "note": "single-query CPU encoding after model load; retrieval artifacts are profiled separately",
    }


def cache_disk_bytes(cache_info: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for name, info in cache_info.items():
        result[name] = file_size(info.get("artifact_path") or info.get("embedding_path"))
    result["total_selected_artifacts"] = sum(result.values())
    return result


def write_csv(path: Path, profile: Mapping[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for mode, mode_profile in profile["online_profiles"].items():
        for stage, stats in mode_profile["stage_timings"].items():
            rows.append({"feedback_mode": mode, "stage": stage, **stats})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["feedback_mode", "stage", "calls", "total_ms", "p50_ms", "p95_ms", "max_ms"])
        writer.writeheader()
        writer.writerows(rows)


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_markdown(path: Path, profile: Mapping[str, Any]) -> None:
    lines = [
        "# Task71.2 Systems and Feedback Operational Profile",
        "",
        f"Dataset: `{profile['dataset']}`. Corpus: {profile['num_corpus_chunks']:,}; queries: {profile['num_queries']:,}.",
        "",
        "This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.",
        "",
        "## Cache Materialization",
        "",
        "| Stage | ms |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {value:.2f} |" for name, value in profile["cold_artifact_load_ms"].items())
    lines.extend(["", "## Warm Online Stages", ""])
    for mode, mode_profile in profile["online_profiles"].items():
        lines.extend([
            f"### Feedback mode: `{mode}`",
            "",
            f"Stream wall time: {mode_profile['stream_elapsed_ms']:.2f} ms; throughput: {mode_profile['interactions_per_sec']:.2f} interactions/s.",
            "",
            "| Stage | Calls | p50 ms | p95 ms | Total ms |",
            "|---|---:|---:|---:|---:|",
        ])
        for stage, stats in mode_profile["stage_timings"].items():
            lines.append(
                f"| {stage} | {stats['calls']} | {stats['p50_ms'] or 0:.4f} | "
                f"{stats['p95_ms'] or 0:.4f} | {stats['total_ms']:.4f} |"
            )
        state = mode_profile["feedback_state"]
        lines.extend([
            "",
            f"Feedback state: {state['feedback_context_count']} contexts; "
            f"{state['in_memory_numeric_bytes']:,} numeric bytes; "
            f"snapshot {state['snapshot_pickle_bytes']:,} bytes.",
            "",
        ])
    lines.extend([
        "## Interpretation Boundary",
        "",
        "- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.",
        "- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.",
        "- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="lotte_technology_search_100k")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--embedding-cache-dir", type=Path, default=DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--artifact-cache-dir", type=Path, default=DEFAULT_ARTIFACT_CACHE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--feedback-modes", default="trust_weighted,none")
    parser.add_argument("--cluster-retrieval-engine", choices=("on_demand", "cached_exact_scores"), default="on_demand")
    parser.add_argument("--query-encode-samples", type=int, default=64)
    parser.add_argument("--query-encoding-only", action="store_true", help="Benchmark MiniLM query encoding without loading retrieval artifacts")
    args = parser.parse_args()

    if args.epochs <= 0 or args.repetitions <= 0:
        raise ValueError("epochs and repetitions must be positive")
    if args.max_queries is not None and args.max_queries <= 0:
        raise ValueError("max-queries must be positive")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.query_encoding_only:
        queries_path = args.data_dir / f"{args.dataset}_queries.json"
        if not queries_path.exists():
            raise FileNotFoundError(f"Missing query source JSON: {queries_path}")
        queries = global_linucb.load_json_list(queries_path)
        if args.max_queries is not None:
            queries = queries[:args.max_queries]
        profile = {
            "task": "Task71.2",
            "purpose": "MiniLM single-query encoding microbenchmark",
            "dataset": args.dataset,
            "model": args.model,
            "hardware": hardware_metadata(),
            "query_encoding": profile_query_encoding(
                queries, model_name=args.model, sample_count=args.query_encode_samples,
            ),
            "boundary": "This profile excludes retrieval, routing, feedback, and generation.",
        }
        path = args.output_dir / f"{args.dataset.replace('/', '_')}_query_encoding_profile.json"
        write_json_atomic(path, profile)
        print(f"query_encoding_profile={path}")
        return 0

    progress_path = args.output_dir / f"{args.dataset.replace('/', '_')}_systems_profile.progress.json"
    write_json_atomic(progress_path, {
        "status": "loading_artifacts",
        "dataset": args.dataset,
        "epochs": args.epochs,
        "repetitions": args.repetitions,
        "feedback_modes": list(parse_csv(args.feedback_modes)),
    })
    inputs, cold_load_ms = load_profile_inputs(
        dataset=args.dataset,
        data_dir=args.data_dir,
        model_name=args.model,
        embedding_cache_dir=args.embedding_cache_dir,
        artifact_cache_dir=args.artifact_cache_dir,
        max_queries=args.max_queries,
        seed=args.seed,
        cluster_retrieval_engine=args.cluster_retrieval_engine,
    )
    query_encoding = profile_query_encoding(
        inputs["queries"], model_name=args.model, sample_count=args.query_encode_samples,
    )
    online_profiles: dict[str, Any] = {}
    for feedback_mode in parse_csv(args.feedback_modes):
        if feedback_mode not in routing.FEEDBACK_MODES:
            raise ValueError(f"Unsupported feedback mode: {feedback_mode}")
        all_timings: dict[str, list[int]] = {}
        elapsed_ns: list[int] = []
        final_state: Mapping[str, Any] | None = None
        for repetition in range(args.repetitions):
            write_json_atomic(progress_path, {
                "status": "running_online_profile",
                "dataset": args.dataset,
                "feedback_mode": feedback_mode,
                "repetition_completed": repetition,
                "repetitions": args.repetitions,
                "epochs": args.epochs,
                "completed_feedback_modes": sorted(online_profiles),
            })
            started = time.perf_counter_ns()
            result = routing.run_prequential_seed(
                inputs["corpus"], inputs["queries"], inputs["corpus_embeddings"], inputs["query_embeddings"],
                stage_timings=all_timings,
                **route_kwargs(
                    inputs,
                    seed=args.seed,
                    feedback_mode=feedback_mode,
                    epochs=args.epochs,
                    cluster_retrieval_engine=args.cluster_retrieval_engine,
                ),
            )
            elapsed_ns.append(time.perf_counter_ns() - started)
            final_state = result["runtime_state"]
            write_json_atomic(progress_path, {
                "status": "running_online_profile",
                "dataset": args.dataset,
                "feedback_mode": feedback_mode,
                "repetition_completed": repetition + 1,
                "repetitions": args.repetitions,
                "epochs": args.epochs,
                "completed_feedback_modes": sorted(online_profiles),
                "partial_stream_elapsed_ms": round(sum(elapsed_ns) / 1_000_000.0, 4),
                "partial_stage_timings": summarize_stage_timings(all_timings),
            })
        interactions = len(inputs["queries"]) * args.epochs * args.repetitions
        stream_elapsed_ms = sum(elapsed_ns) / 1_000_000.0
        online_profiles[feedback_mode] = {
            "stream_elapsed_ms": round(stream_elapsed_ms, 4),
            "stream_p50_ms": percentile_ms(elapsed_ns, 50),
            "stream_p95_ms": percentile_ms(elapsed_ns, 95),
            "interactions": interactions,
            "interactions_per_sec": round(interactions / (stream_elapsed_ms / 1000.0), 4),
            "stage_timings": summarize_stage_timings(all_timings),
            "feedback_state": feedback_state_profile(final_state or {}),
        }

    profile = {
        "task": "Task71.2",
        "purpose": "systems and feedback operational profile",
        "dataset": args.dataset,
        "model": args.model,
        "num_corpus_chunks": len(inputs["corpus"]),
        "num_queries": len(inputs["queries"]),
        "seed": args.seed,
        "epochs": args.epochs,
        "repetitions": args.repetitions,
        "cluster_retrieval_engine": args.cluster_retrieval_engine,
        "hardware": hardware_metadata(),
        "peak_rss_bytes": current_peak_rss_bytes(),
        "cold_artifact_load_ms": cold_load_ms,
        "cache_disk_bytes": cache_disk_bytes(inputs["cache_info"]),
        "historical_offline_metadata": {
            name: {
                key: info.get(key)
                for key in ("compute_elapsed_sec", "encode_elapsed_sec", "cache_hit", "artifact_path", "embedding_path")
                if key in info
            }
            for name, info in inputs["cache_info"].items()
        },
        "query_encoding": query_encoding,
        "online_profiles": online_profiles,
        "interpretation_boundary": [
            "Cache materialization and warm routing are measured separately.",
            "Final-context token savings remain a generation-input measure, not total system cost.",
            "Simulated-feedback update timing is an operational feasibility measurement, not real-user RLHF evidence.",
            "Historical artifact build times may originate from earlier runs and are not reported as current hardware benchmarks.",
        ],
    }
    prefix = args.dataset.replace("/", "_")
    json_path = args.output_dir / f"{prefix}_systems_profile.json"
    csv_path = args.output_dir / f"{prefix}_systems_profile.csv"
    markdown_path = args.output_dir / f"{prefix}_systems_profile.md"
    write_json_atomic(json_path, profile)
    write_csv(csv_path, profile)
    write_markdown(markdown_path, profile)
    write_json_atomic(progress_path, {
        "status": "completed",
        "dataset": args.dataset,
        "profile_json": str(json_path),
        "profile_csv": str(csv_path),
        "profile_markdown": str(markdown_path),
    })
    print(f"profile_json={json_path}")
    print(f"profile_csv={csv_path}")
    print(f"profile_markdown={markdown_path}")
    print(f"peak_rss_bytes={profile['peak_rss_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
