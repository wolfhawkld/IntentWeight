#!/usr/bin/env python3
"""Isolate simulated-feedback learning on a cluster-only retrieval surface.

Task72.1 reuses the predeclared Task72 event streams but removes Dense and
BM25 rescue from both retrieval and reward attribution. It tests a mechanism
ablation, not an end-to-end RAG or real-user RLHF claim.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"
STREAM_CLUSTER_SEED = 13
METHODS = (
    "cluster_static_nearest",
    "cluster_cold_no_feedback",
    "cluster_equal_noisy",
    "cluster_trust_weighted",
    "cluster_oracle",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stream = load_module("task72_stream", SCRIPT_DIR / "task72_recurrent_feedback_stream.py")
routing = stream.routing
task70 = stream.task70


def write_json(path: Path, payload: object) -> None:
    routing.write_json_atomic(path, payload)


def qid(query: Mapping[str, object]) -> str:
    return routing._query_id(query)


def checkpoint_path(output_dir: Path, *, dataset: str, method: str, seed: int) -> Path:
    return output_dir / "checkpoints" / f"{dataset}__{method}__seed{seed}.json"


def checkpoint_signature(args, manifest: Mapping[str, object], *, dataset: str, method: str, seed: int) -> dict[str, object]:
    event_fingerprint = hashlib.sha256(
        json.dumps(manifest["events"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "version": 1,
        "protocol": "task72_1_cluster_only_credit_ablation",
        "dataset": dataset,
        "method": method,
        "seed": int(seed),
        "model": args.model,
        "n_clusters": args.n_clusters,
        "context_dim": args.context_dim,
        "candidate_arms": args.candidate_arms,
        "event_fingerprint": event_fingerprint,
        "num_events": int(manifest["num_events"]),
        "dense_depth": 0,
        "bm25_depth": 0,
        "dense_floor_k": 0,
        "reward_attribution": "cluster_only",
        "final_context_policy": "fixed_topk",
        "answer_cache": False,
        "context_cache": False,
    }


def load_checkpoint(path: Path, signature: Mapping[str, object]) -> tuple[list[dict[str, object]], dict[str, object]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if payload.get("signature") != dict(signature):
        return None
    rows = payload.get("rows")
    metrics = payload.get("run_metrics")
    if not isinstance(rows, list) or not isinstance(metrics, dict) or len(rows) != int(signature["num_events"]):
        return None
    return [dict(row) for row in rows], dict(metrics)


def save_checkpoint(
    path: Path,
    signature: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    run_metrics: Mapping[str, object],
) -> None:
    write_json(path, {"signature": dict(signature), "rows": list(rows), "run_metrics": dict(run_metrics)})


def run_cluster_controller(
    method: str,
    *,
    args,
    corpus: Sequence[Mapping[str, object]],
    queries: Sequence[Mapping[str, object]],
    loaded: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    seed: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    config = {
        "cluster_static_nearest": ("static_nearest_ensemble", "none"),
        "cluster_cold_no_feedback": ("full_multi_route", "none"),
        "cluster_equal_noisy": ("full_multi_route", "equal_noisy"),
        "cluster_trust_weighted": ("full_multi_route", "trust_weighted"),
        "cluster_oracle": ("full_multi_route", "oracle"),
    }
    if method not in config:
        raise ValueError(f"unsupported Task72.1 method: {method}")
    routing_mode, feedback_mode = config[method]
    seed_artifacts = loaded["per_seed"][seed]
    args.dense_rankings_by_qid = loaded["dense_rankings"]
    args.bm25_rankings_by_qid = loaded["bm25_rankings"]
    kwargs = task70.common_run_args(
        args,
        seed=seed,
        routing_mode=routing_mode,
        feedback_mode=feedback_mode,
        epochs=1,
        artifacts=seed_artifacts["artifacts"],
        arm_rows=seed_artifacts["arm_rows"],
        score_rows=loaded["score_rows"],
    )
    kwargs.update({
        "reward_attribution": "cluster_only",
        "confidence_mode": "value",
        "dense_depth": 0,
        "bm25_depth": 0,
        "cluster_depth": 100,
        "dense_weight": 0.0,
        "bm25_weight": 0.0,
        "cluster_weight": 1.0,
        "dense_floor_k": 0,
        "dense_lite_depth": 0,
        "bm25_lite_depth": 0,
        "dense_lite_weight": 0.0,
        "bm25_lite_weight": 0.0,
        "cluster_primary_weight": 1.0,
        "dense_lite_floor_k": 0,
        "event_indices": [int(event["query_index"]) for event in events],
        "event_labels": [str(event["phase"]) for event in events],
        "collect_interaction_records": True,
    })
    result = routing.run_prequential_seed(
        corpus,
        queries,
        loaded["corpus_embeddings"],
        loaded["query_embeddings"],
        **kwargs,
    )
    records = result.get("interaction_records")
    if not isinstance(records, list):
        raise AssertionError("Task72.1 requires interaction records")
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        raise AssertionError("Task72.1 requires run metrics")
    return records, dict(metrics)


def paired_rows(rows: Sequence[Mapping[str, object]], *, bootstrap_samples: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, int, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["dataset"]), str(row["method"]), int(row["seed"]), str(row["condition"]))].append(row)
    comparisons = {
        "cluster_equal_noisy": ("cluster_cold_no_feedback",),
        "cluster_trust_weighted": (
            "cluster_cold_no_feedback",
            "cluster_equal_noisy",
            "cluster_static_nearest",
        ),
        "cluster_oracle": ("cluster_cold_no_feedback",),
    }
    metrics = (
        "hit_at_10",
        "evidence_recall_at_10",
        "mrr_at_10",
        "ndcg_at_10",
        "selected_cluster_hit",
        "route_true_reward",
    )
    output: list[dict[str, object]] = []
    for dataset in sorted({key[0] for key in groups}):
        for seed in sorted({key[2] for key in groups if key[0] == dataset}):
            for condition in sorted({key[3] for key in groups if key[0] == dataset and key[2] == seed}):
                for method, baselines in comparisons.items():
                    learned = groups.get((dataset, method, seed, condition), [])
                    if not learned:
                        continue
                    for baseline in baselines:
                        reference = groups.get((dataset, baseline, seed, condition), [])
                        if not reference:
                            continue
                        for metric_index, metric in enumerate(metrics):
                            interval = stream.block_bootstrap_delta(
                                learned,
                                reference,
                                metric=metric,
                                samples=bootstrap_samples,
                                seed=1_720_000 + seed * 101 + metric_index,
                            )
                            output.append({
                                "dataset": dataset,
                                "seed": seed,
                                "condition": condition,
                                "comparison": f"{method}_minus_{baseline}",
                                **interval,
                            })
    return output


def adaptation_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for dataset in sorted({str(row["dataset"]) for row in rows}):
        for method in METHODS:
            for seed in sorted({int(row["seed"]) for row in rows if str(row["dataset"]) == dataset and str(row["method"]) == method}):
                early = [
                    row for row in rows
                    if str(row["dataset"]) == dataset and str(row["method"]) == method
                    and int(row["seed"]) == seed and str(row["phase"]) == "B_recurrent_shift_1"
                ]
                late = [
                    row for row in rows
                    if str(row["dataset"]) == dataset and str(row["method"]) == method
                    and int(row["seed"]) == seed and str(row["phase"]) == "B_recurrent_shift_2"
                ]
                early_by_query = {str(row["query_id"]): row for row in early}
                late_by_query = {str(row["query_id"]): row for row in late}
                common = sorted(set(early_by_query).intersection(late_by_query))
                if not common:
                    continue
                result: dict[str, object] = {
                    "dataset": dataset,
                    "method": method,
                    "seed": seed,
                    "phase_transition": "B_recurrent_shift_1_to_2",
                    "query_blocks": len(common),
                }
                for metric in ("selected_cluster_hit", "route_true_reward", "hit_at_10", "evidence_recall_at_10"):
                    deltas = [float(late_by_query[key][metric]) - float(early_by_query[key][metric]) for key in common]
                    result[f"{metric}_delta"] = float(mean(deltas)) if deltas else float("nan")
                output.append(result)
    return output


def recovery_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for dataset in sorted({str(row["dataset"]) for row in rows}):
        for method in METHODS:
            for seed in sorted({int(row["seed"]) for row in rows if str(row["dataset"]) == dataset and str(row["method"]) == method}):
                repeated = [
                    row for row in rows
                    if str(row["dataset"]) == dataset and str(row["method"]) == method
                    and int(row["seed"]) == seed and str(row["condition"]) == "repeated"
                ]
                by_query: dict[str, list[Mapping[str, object]]] = defaultdict(list)
                for row in repeated:
                    by_query[str(row["query_id"])].append(row)
                affected = recovered = 0
                for query_rows in by_query.values():
                    ordered = sorted(query_rows, key=lambda row: int(row["event_index"]))
                    if ordered and float(ordered[0]["hit_at_10"]) <= 0:
                        affected += 1
                        if any(float(row["hit_at_10"]) > 0 for row in ordered[1:]):
                            recovered += 1
                output.append({
                    "dataset": dataset,
                    "method": method,
                    "seed": seed,
                    "affected_repeated_queries": affected,
                    "recovered_queries": recovered,
                    "recovery_rate": recovered / affected if affected else float("nan"),
                })
    return output


def write_markdown(
    path: Path,
    *,
    manifests: Mapping[str, Mapping[str, object]],
    grouped: Sequence[Mapping[str, object]],
    paired: Sequence[Mapping[str, object]],
    adaptation: Sequence[Mapping[str, object]],
    recovery: Sequence[Mapping[str, object]],
    run_metrics: Sequence[Mapping[str, object]],
    validation: Mapping[str, object],
) -> None:
    lines = [
        "# Task72.1 Cluster-Credit Feedback Ablation",
        "",
        "## Scope",
        "",
        "This ablation reuses the predeclared Task72 streams but disables Dense and BM25 retrieval, Dense floors, answer caching, and final-context caching. The simulated reward is the selected cluster-route reward (`cluster_only`). It evaluates a route-learning mechanism, not end-to-end RAG, real-user RLHF, or a replacement for the full-fusion Task72 boundary.",
        "",
        "## Stream and Integrity",
        "",
        "| Dataset | Region-A arm | Region-B arm | Events | Unique queries |",
        "|---|---:|---:|---:|---:|",
    ]
    for dataset, manifest in sorted(manifests.items()):
        lines.append(f"| {dataset} | {manifest['region_a_arm']} | {manifest['region_b_arm']} | {manifest['num_events']} | {manifest['num_unique_queries']} |")
    lines.extend([
        "",
        f"- Event coverage: {'passed' if validation['event_coverage_passed'] else 'failed'} ({validation['actual_event_rows']}/{validation['expected_event_rows']}).",
        f"- Cluster-only retrieval invariant: {'passed' if validation['cluster_only_retrieval_passed'] else 'failed'}.",
        f"- Feedback-update invariant: {'passed' if validation['feedback_update_invariant_passed'] else 'failed'}.",
        "",
        "## Per-Seed Outcomes",
        "",
        "`selected_cluster_hit`, route reward, and all retrieval metrics are measured on the same cluster-only ranked top-10. Seed rows are intentionally kept separate; paired block-bootstrap intervals are not pooled across seeds or domains.",
        "",
        "| Dataset | Method | Seed | Condition | Phase | n | Hit@10 | Recall@10 | MRR@10 | nDCG@10 | Cluster hit |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in grouped:
        def cell(key: str) -> str:
            value = float(row[key])
            return "--" if math.isnan(value) else f"{value:.3f}"
        lines.append(
            f"| {row['dataset']} | {row['method']} | {row['seed']} | {row['condition']} | {row['phase']} | {row['event_count']} | "
            f"{cell('hit_at_10')} | {cell('evidence_recall_at_10')} | {cell('mrr_at_10')} | {cell('ndcg_at_10')} | {cell('selected_cluster_hit')} |"
        )
    lines.extend([
        "",
        "## Paired Comparisons",
        "",
        "The 95% intervals bootstrap unique query-ID blocks while retaining all repeated occurrences for an ID. They describe the declared stream only.",
        "",
        "| Dataset | Seed | Condition | Comparison | Metric | Blocks | Delta | 95% CI |",
        "|---|---:|---|---|---|---:|---:|---|",
    ])
    for row in paired:
        low, high, delta = float(row["ci_low"]), float(row["ci_high"]), float(row["delta"])
        interval = "--" if math.isnan(low) or math.isnan(high) else f"[{low:.3f}, {high:.3f}]"
        lines.append(
            f"| {row['dataset']} | {row['seed']} | {row['condition']} | {row['comparison']} | {row['metric']} | "
            f"{row['blocks']} | {'--' if math.isnan(delta) else f'{delta:.3f}'} | {interval} |"
        )
    lines.extend([
        "",
        "## Shift and Recovery Diagnostics",
        "",
        "| Dataset | Method | Seed | B-shift cluster-hit delta | B-shift Hit@10 delta |",
        "|---|---|---:|---:|---:|",
    ])
    for row in adaptation:
        lines.append(
            f"| {row['dataset']} | {row['method']} | {row['seed']} | {float(row['selected_cluster_hit_delta']):.3f} | {float(row['hit_at_10_delta']):.3f} |"
        )
    lines.extend([
        "",
        "| Dataset | Method | Seed | Affected repeated queries | Recovery rate |",
        "|---|---|---:|---:|---:|",
    ])
    for row in recovery:
        rate = float(row["recovery_rate"])
        lines.append(f"| {row['dataset']} | {row['method']} | {row['seed']} | {row['affected_repeated_queries']} | {'--' if math.isnan(rate) else f'{rate:.3f}'} |")
    lines.extend([
        "",
        "## Controller Update Audit",
        "",
        "| Dataset | Method | Seed | Feedback-induced policy updates | Total update weight |",
        "|---|---|---:|---:|---:|",
    ])
    for row in run_metrics:
        lines.append(f"| {row['dataset']} | {row['method']} | {row['seed']} | {row['total_feedback_updates']} | {float(row['total_update_weight']):.3f} |")
    lines.extend([
        "",
        "Interpretation must keep this mechanism result separate from Task72: a positive cluster-only result does not establish an end-to-end full-fusion gain, while a negative result does not revise the already reported Task72 boundary.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_dataset(args, dataset: str, encoder, manifests: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    if dataset not in manifests:
        raise ValueError(f"Task72 manifest missing dataset {dataset}")
    manifest = dict(manifests[dataset])
    events = [dict(event) for event in manifest.get("events", [])]
    if not events:
        raise ValueError(f"Task72 manifest has no events for {dataset}")
    corpus = routing.global_linucb.load_json_list(args.data_dir / f"{dataset}_corpus.json")
    queries = routing.global_linucb.load_json_list(args.data_dir / f"{dataset}_queries.json")
    for event in events:
        index = int(event["query_index"])
        if index < 0 or index >= len(queries) or str(event["query_id"]) != qid(queries[index]):
            raise AssertionError(f"Task72 manifest/query mismatch for {dataset} event={event.get('event_index')}")
    canonical_names = {
        "lotte_technology_search_100k": "lotte_technology_search",
        "lotte_science_search_100k": "lotte_science_search",
    }
    if dataset not in canonical_names:
        raise ValueError(f"no scale-store mapping for {dataset}")
    args.dataset = dataset
    args.scale_store_canonical_name = canonical_names[dataset]
    args.scale_store_dir = Path(args.scale_store_root) / canonical_names[dataset]
    loaded = task70.load_artifacts(args, corpus, queries, encoder)
    token_counter = stream.context_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {routing._chunk_id(chunk): token_counter(str(chunk.get("text", ""))) for chunk in corpus}
    rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    for method in METHODS:
        for seed in args.seeds:
            signature = checkpoint_signature(args, manifest, dataset=dataset, method=method, seed=seed)
            path = checkpoint_path(args.output_dir, dataset=dataset, method=method, seed=seed)
            restored = load_checkpoint(path, signature)
            if restored is not None:
                result_rows, result_metrics = restored
                print(f"[{dataset}] restored {method} seed={seed} from checkpoint", flush=True)
            else:
                print(f"[{dataset}] executing {method} seed={seed} ({len(events)} events)", flush=True)
                records, result_metrics = run_cluster_controller(
                    method,
                    args=args,
                    corpus=corpus,
                    queries=queries,
                    loaded=loaded,
                    events=events,
                    seed=seed,
                )
                result_rows = stream.annotate_records(
                    records,
                    events,
                    queries,
                    chunk_tokens,
                    dataset=dataset,
                    method=method,
                    seed=seed,
                )
                save_checkpoint(path, signature, result_rows, result_metrics)
            if len(result_rows) != len(events):
                raise AssertionError(f"incomplete event coverage for {dataset}/{method}/seed{seed}")
            rows.extend(result_rows)
            metric_rows.append({
                "dataset": dataset,
                "method": method,
                "seed": seed,
                "total_feedback_updates": int(result_metrics["total_feedback_updates"]),
                "total_update_weight": float(result_metrics["total_update_weight"]),
            })
    return {"rows": rows, "run_metrics": metric_rows, "cache_metadata": loaded["cache_metadata"]}


def validate(
    rows: Sequence[Mapping[str, object]],
    run_metrics: Sequence[Mapping[str, object]],
    manifests: Mapping[str, Mapping[str, object]],
    *,
    seeds: Sequence[int],
) -> dict[str, object]:
    expected = sum(int(manifest["num_events"]) for manifest in manifests.values()) * len(METHODS) * len(seeds)
    per_run = Counter((str(row["dataset"]), str(row["method"]), int(row["seed"])) for row in rows)
    coverage = all(
        count == int(manifests[dataset]["num_events"])
        for (dataset, _method, _seed), count in per_run.items()
    ) and len(per_run) == len(manifests) * len(METHODS) * len(seeds)
    cluster_only = all(int(row["dense_queried"]) == 0 and int(row["bm25_queried"]) == 0 for row in rows)
    expected_methods = {str(row["method"]) for row in run_metrics}
    cold_and_static_zero = all(
        int(row["total_feedback_updates"]) == 0 and float(row["total_update_weight"]) == 0.0
        for row in run_metrics if str(row["method"]) in {"cluster_static_nearest", "cluster_cold_no_feedback"}
    )
    learned_positive = all(
        int(row["total_feedback_updates"]) > 0 and float(row["total_update_weight"]) > 0.0
        for row in run_metrics if str(row["method"]) in {"cluster_equal_noisy", "cluster_trust_weighted", "cluster_oracle"}
    )
    return {
        "expected_event_rows": expected,
        "actual_event_rows": len(rows),
        "run_count": len(per_run),
        "event_coverage_passed": bool(coverage and len(rows) == expected),
        "cluster_only_retrieval_passed": bool(cluster_only),
        "feedback_update_invariant_passed": bool(cold_and_static_zero and learned_positive and expected_methods == set(METHODS)),
        "no_answer_or_context_cache": True,
        "reused_task72_manifest": True,
        "methods": list(METHODS),
        "controller_seeds": [int(seed) for seed in seeds],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", default="lotte_technology_search_100k,lotte_science_search_100k")
    parser.add_argument("--data-dir", type=Path, default=DATA / "processed")
    parser.add_argument("--task72-results-dir", type=Path, default=RESULTS / "task72_recurrent_feedback_stream")
    parser.add_argument("--output-dir", type=Path, default=RESULTS / "task72_1_cluster_credit_ablation")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--device", default=None)
    parser.add_argument("--allow-network", action="store_false", dest="local_files_only")
    parser.set_defaults(local_files_only=True)
    parser.add_argument("--embedding-cache-dir", type=Path, default=routing.DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--artifact-cache-dir", type=Path, default=routing.DEFAULT_ARTIFACT_CACHE_DIR)
    parser.add_argument("--scale-store-dir", type=Path, default=routing.DEFAULT_SCALE_STORE_DIR)
    parser.add_argument("--no-scale-store", action="store_false", dest="use_scale_store")
    parser.set_defaults(use_scale_store=True)
    parser.add_argument("--batch-size", type=int, default=64)
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
    parser.add_argument("--bootstrap-samples", type=int, default=5_000)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    args = parser.parse_args(argv)
    args.seeds = tuple(int(part.strip()) for part in args.seeds.split(",") if part.strip())
    datasets = tuple(part.strip() for part in args.datasets.split(",") if part.strip())
    if not datasets or not args.seeds or args.bootstrap_samples <= 0:
        raise ValueError("datasets, seeds, and bootstrap samples must be positive")
    if STREAM_CLUSTER_SEED not in args.seeds:
        raise ValueError(f"Task72.1 requires stream cluster seed {STREAM_CLUSTER_SEED}")
    for field in ("data_dir", "task72_results_dir", "output_dir", "embedding_cache_dir", "artifact_cache_dir", "scale_store_dir"):
        value = getattr(args, field)
        if not value.is_absolute():
            setattr(args, field, (ROOT / value).resolve())
    scale_store_dir = Path(args.scale_store_dir)
    args.scale_store_root = scale_store_dir.parent if scale_store_dir.name in {"lotte_technology_search", "lotte_science_search"} else scale_store_dir
    manifest_path = args.task72_results_dir / "stream_manifests.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Task72 stream manifest is required: {manifest_path}")
    manifests = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifests, dict):
        raise ValueError("Task72 manifests must be a JSON object")
    manifests = {dataset: dict(manifests[dataset]) for dataset in datasets}
    print(f"loading encoder {args.model} (local_files_only={args.local_files_only})", flush=True)
    encoder = routing.load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)
    all_rows: list[dict[str, object]] = []
    all_metrics: list[dict[str, object]] = []
    cache_metadata: dict[str, object] = {}
    for dataset in datasets:
        result = run_dataset(args, dataset, encoder, manifests)
        all_rows.extend(result["rows"])
        all_metrics.extend(result["run_metrics"])
        cache_metadata[dataset] = result["cache_metadata"]
    grouped = stream.grouped_summary(all_rows)
    paired = paired_rows(all_rows, bootstrap_samples=args.bootstrap_samples)
    adaptation = adaptation_rows(all_rows)
    recovery = recovery_rows(all_rows)
    validation = validate(all_rows, all_metrics, manifests, seeds=args.seeds)
    if not validation["event_coverage_passed"] or not validation["cluster_only_retrieval_passed"] or not validation["feedback_update_invariant_passed"]:
        raise AssertionError(f"Task72.1 validation failed: {validation}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "stream_manifests.json", manifests)
    write_json(args.output_dir / "cache_metadata.json", cache_metadata)
    write_json(args.output_dir / "validation.json", validation)
    stream.write_csv(args.output_dir / "event_rows.csv", all_rows)
    stream.write_csv(args.output_dir / "summary.csv", grouped)
    stream.write_csv(args.output_dir / "paired.csv", paired)
    stream.write_csv(args.output_dir / "adaptation.csv", adaptation)
    stream.write_csv(args.output_dir / "recovery.csv", recovery)
    stream.write_csv(args.output_dir / "controller_updates.csv", all_metrics)
    write_markdown(
        args.output_dir / "summary.md",
        manifests=manifests,
        grouped=grouped,
        paired=paired,
        adaptation=adaptation,
        recovery=recovery,
        run_metrics=all_metrics,
        validation=validation,
    )
    print(json.dumps({"event_rows": len(all_rows), "validation": validation, "output_dir": str(args.output_dir)}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
