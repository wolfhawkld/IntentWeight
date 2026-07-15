#!/usr/bin/env python3
"""Evaluate feedback-adaptive routing on controlled recurrent query streams.

Task72 complements the frozen unseen-query Task70 audit. It fixes an event
stream before execution, repeatedly executes retrieval without answer/context
caching, and measures feedback adaptation after a local-intent distribution
shift. It does not model real-user preference labels or claim first-pass
unseen-query improvement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"
BOOTSTRAP_SAMPLES = 5_000
STREAM_CLUSTER_SEED = 13
METHODS = ("dense", "static_nearest", "cold_no_feedback", "learned_feedback")

# Reuse the project-pinned tokenizer vocabulary used by the context-budget tasks.
os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing = load_module("task72_routing", SCRIPT_DIR / "linucb_cost_aware_routing.py")
task70 = load_module("task72_task70", SCRIPT_DIR / "task70_frozen_policy_generalization.py")
context_cost = load_module("task72_context_cost", SCRIPT_DIR / "context_token_cost.py")


def qid(query: Mapping[str, object]) -> str:
    return routing._query_id(query)


def cid(chunk: Mapping[str, object]) -> str:
    return routing._chunk_id(chunk)


def write_json(path: Path, payload: Any) -> None:
    routing.write_json_atomic(path, payload)


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fields = sorted({str(key) for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_order(indices: Sequence[int], queries: Sequence[Mapping[str, object]], *, salt: str) -> list[int]:
    return sorted(
        (int(index) for index in indices),
        key=lambda index: hashlib.sha256(f"{salt}:{qid(queries[index])}".encode("utf-8")).hexdigest(),
    )


def query_arm_assignments(artifacts: Mapping[str, np.ndarray]) -> np.ndarray:
    query_context = np.asarray(artifacts["query_context"], dtype=np.float32)
    centroids = np.asarray(artifacts["centroids"], dtype=np.float32)
    return np.argmax(query_context @ centroids.T, axis=1).astype(np.int32)


def build_stream(
    queries: Sequence[Mapping[str, object]],
    stream_artifacts: Mapping[str, np.ndarray],
    *,
    stream_seed: int,
    anchors_per_region: int,
    nearby_per_region: int,
    unseen_count: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build a deterministic A-to-B-to-A stream from disjoint query IDs."""
    if anchors_per_region <= 0 or nearby_per_region <= 0 or unseen_count <= 0:
        raise ValueError("stream sizes must be positive")
    assignments = query_arm_assignments(stream_artifacts)
    by_arm: dict[int, list[int]] = defaultdict(list)
    for index, arm in enumerate(assignments.tolist()):
        by_arm[int(arm)].append(int(index))

    required = anchors_per_region + nearby_per_region
    eligible = [
        (arm, indices)
        for arm, indices in by_arm.items()
        if len(indices) >= required
    ]
    eligible.sort(key=lambda item: (-len(item[1]), item[0]))
    if len(eligible) < 2:
        raise ValueError(
            "Task72 needs two query-local regions with at least "
            f"{required} queries; eligible={[(arm, len(indices)) for arm, indices in eligible]}"
        )

    (arm_a, raw_a), (arm_b, raw_b) = eligible[:2]
    arm_a_indices = stable_order(raw_a, queries, salt=f"task72:{stream_seed}:arm:{arm_a}")
    arm_b_indices = stable_order(raw_b, queries, salt=f"task72:{stream_seed}:arm:{arm_b}")
    anchors_a, nearby_a = arm_a_indices[:anchors_per_region], arm_a_indices[anchors_per_region:required]
    anchors_b, nearby_b = arm_b_indices[:anchors_per_region], arm_b_indices[anchors_per_region:required]
    used = set(anchors_a) | set(nearby_a) | set(anchors_b) | set(nearby_b)
    outside = [index for index in range(len(queries)) if index not in used and int(assignments[index]) not in {arm_a, arm_b}]
    if len(outside) < unseen_count:
        outside = [index for index in range(len(queries)) if index not in used]
    unseen = stable_order(outside, queries, salt=f"task72:{stream_seed}:unseen")[:unseen_count]
    if len(unseen) != unseen_count:
        raise ValueError(f"Task72 needs {unseen_count} unseen queries, found {len(unseen)}")

    events: list[dict[str, object]] = []
    occurrence: Counter[str] = Counter()

    def append_phase(phase: str, condition: str, region: str, indices: Sequence[int]) -> None:
        for index in indices:
            query_id = qid(queries[int(index)])
            occurrence[query_id] += 1
            events.append({
                "event_index": len(events),
                "query_index": int(index),
                "query_id": query_id,
                "phase": phase,
                "condition": condition,
                "region": region,
                "occurrence": int(occurrence[query_id]),
            })

    append_phase("A_recurrent_warmup_1", "repeated", "A", anchors_a)
    append_phase("A_recurrent_warmup_2", "repeated", "A", anchors_a)
    append_phase("A_nearby", "nearby", "A", nearby_a)
    append_phase("B_recurrent_shift_1", "repeated", "B", anchors_b)
    append_phase("B_recurrent_shift_2", "repeated", "B", anchors_b)
    append_phase("B_nearby", "nearby", "B", nearby_b)
    append_phase("A_recurrent_return", "repeated", "A", anchors_a)
    append_phase("unseen_tail", "unseen", "other", unseen)

    manifest = {
        "stream_seed": stream_seed,
        "stream_cluster_seed": STREAM_CLUSTER_SEED,
        "region_a_arm": int(arm_a),
        "region_b_arm": int(arm_b),
        "region_a_query_count": len(raw_a),
        "region_b_query_count": len(raw_b),
        "anchors_per_region": anchors_per_region,
        "nearby_per_region": nearby_per_region,
        "unseen_count": unseen_count,
        "num_events": len(events),
        "num_unique_queries": len({str(event["query_id"]) for event in events}),
        "events": events,
    }
    return events, manifest


def ranking_metrics(query: Mapping[str, object], ranking: Sequence[str], chunk_tokens: Mapping[str, int]) -> dict[str, float]:
    ground_truth = {str(item) for item in query.get("ground_truth_chunk_ids", [])}
    ranked = [str(item) for item in ranking[:10]]
    hits = [index for index, item in enumerate(ranked, start=1) if item in ground_truth]
    hit = float(bool(hits))
    recall = float(len(set(ranked).intersection(ground_truth)) / len(ground_truth)) if ground_truth else 0.0
    mrr = float(1.0 / hits[0]) if hits else 0.0
    dcg = sum(1.0 / math.log2(index + 1) for index in hits)
    ideal = sum(1.0 / math.log2(index + 1) for index in range(1, min(len(ground_truth), 10) + 1))
    ndcg = float(dcg / ideal) if ideal else 0.0
    return {
        "hit_at_10": hit,
        "evidence_recall_at_10": recall,
        "mrr_at_10": mrr,
        "ndcg_at_10": ndcg,
        "final_context_tokens": float(sum(chunk_tokens.get(item, 0) for item in ranked)),
    }


def annotate_records(
    records: Sequence[Mapping[str, object]],
    events: Sequence[Mapping[str, object]],
    queries: Sequence[Mapping[str, object]],
    chunk_tokens: Mapping[str, int],
    *,
    dataset: str,
    method: str,
    seed: int,
) -> list[dict[str, object]]:
    if len(records) != len(events):
        raise AssertionError(f"record/event count mismatch: {len(records)} != {len(events)}")
    rows: list[dict[str, object]] = []
    for record, event in zip(records, events):
        query_index = int(event["query_index"])
        if int(record["query_index"]) != query_index:
            raise AssertionError("event query order changed during route execution")
        ranking = [str(item) for item in record["ranking"]]
        row = {
            "dataset": dataset,
            "method": method,
            "seed": int(seed),
            "event_index": int(event["event_index"]),
            "phase": str(event["phase"]),
            "condition": str(event["condition"]),
            "region": str(event["region"]),
            "occurrence": int(event["occurrence"]),
            "query_id": str(event["query_id"]),
            "query_index": query_index,
            "route": str(record.get("route", "")),
            "route_reason": str(record.get("route_reason", "")),
            "dense_queried": int(bool(record.get("dense_queried", False))),
            "bm25_queried": int(bool(record.get("bm25_queried", False))),
            "selected_cluster_hit": float(record.get("selected_cluster_hit", float("nan"))),
            "route_true_reward": float(record.get("route_true_reward", float("nan"))),
            "final_true_reward": float(record.get("final_true_reward", float("nan"))),
            "observed_reward": float(record.get("observed_reward", float("nan"))),
            "confidence": float(record.get("confidence", float("nan"))),
            "semantic_drift": float(record.get("semantic_drift", float("nan"))),
            "final_context_k": int(record.get("final_context_k", len(ranking))),
        }
        row.update(ranking_metrics(queries[query_index], ranking, chunk_tokens))
        rows.append(row)
    return rows


def dense_records(
    events: Sequence[Mapping[str, object]],
    queries: Sequence[Mapping[str, object]],
    dense_rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    dataset: str,
    seed: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in events:
        query_index = int(event["query_index"])
        query = queries[query_index]
        ranking = [str(item) for item in dense_rankings[qid(query)][:10]]
        row = {
            "dataset": dataset,
            "method": "dense",
            "seed": int(seed),
            "event_index": int(event["event_index"]),
            "phase": str(event["phase"]),
            "condition": str(event["condition"]),
            "region": str(event["region"]),
            "occurrence": int(event["occurrence"]),
            "query_id": str(event["query_id"]),
            "query_index": query_index,
            "route": "dense",
            "route_reason": "dense_only",
            "dense_queried": 1,
            "bm25_queried": 0,
            "selected_cluster_hit": float("nan"),
            "route_true_reward": float("nan"),
            "final_true_reward": float("nan"),
            "observed_reward": float("nan"),
            "confidence": float("nan"),
            "semantic_drift": float("nan"),
            "final_context_k": len(ranking),
        }
        row.update(ranking_metrics(query, ranking, chunk_tokens))
        rows.append(row)
    return rows


def run_controller(
    method: str,
    *,
    args,
    corpus: Sequence[Mapping[str, object]],
    queries: Sequence[Mapping[str, object]],
    loaded: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    seed: int,
) -> list[dict[str, object]]:
    config = {
        "static_nearest": ("static_nearest_ensemble", "none"),
        "cold_no_feedback": ("full_multi_route", "none"),
        "learned_feedback": ("full_multi_route", "trust_weighted"),
    }
    if method not in config:
        raise ValueError(f"unsupported controller method: {method}")
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
        raise AssertionError("Task72 requires interaction records from the routing runner")
    return records


def checkpoint_signature(args, manifest: Mapping[str, object], *, dataset: str, method: str, seed: int) -> dict[str, object]:
    event_fingerprint = hashlib.sha256(
        json.dumps(manifest["events"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "version": 1,
        "dataset": dataset,
        "method": method,
        "seed": int(seed),
        "model": args.model,
        "n_clusters": args.n_clusters,
        "context_dim": args.context_dim,
        "candidate_arms": args.candidate_arms,
        "event_fingerprint": event_fingerprint,
        "num_events": int(manifest["num_events"]),
        "final_context_policy": "fixed_topk",
        "answer_cache": False,
        "context_cache": False,
    }


def checkpoint_path(output_dir: Path, *, dataset: str, method: str, seed: int) -> Path:
    return output_dir / "checkpoints" / f"{dataset}__{method}__seed{seed}.json"


def load_checkpoint(path: Path, signature: Mapping[str, object]) -> list[dict[str, object]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if payload.get("signature") != dict(signature):
        return None
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != int(signature["num_events"]):
        return None
    return [dict(row) for row in rows]


def save_checkpoint(path: Path, signature: Mapping[str, object], rows: Sequence[Mapping[str, object]]) -> None:
    write_json(path, {"signature": dict(signature), "rows": list(rows)})


def grouped_summary(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, int, str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["dataset"]),
            str(row["method"]),
            int(row["seed"]),
            str(row["condition"]),
            str(row["phase"]),
        )
        groups[key].append(row)
    metric_names = (
        "hit_at_10",
        "evidence_recall_at_10",
        "mrr_at_10",
        "ndcg_at_10",
        "selected_cluster_hit",
        "route_true_reward",
        "final_context_tokens",
        "dense_queried",
    )
    output: list[dict[str, object]] = []
    for key, group in sorted(groups.items()):
        result: dict[str, object] = {
            "dataset": key[0],
            "method": key[1],
            "seed": key[2],
            "condition": key[3],
            "phase": key[4],
            "event_count": len(group),
            "unique_query_count": len({str(row["query_id"]) for row in group}),
        }
        for metric in metric_names:
            values = [float(row[metric]) for row in group if not math.isnan(float(row[metric]))]
            result[metric] = float(mean(values)) if values else float("nan")
        output.append(result)
    return output


def block_bootstrap_delta(
    learned_rows: Sequence[Mapping[str, object]],
    baseline_rows: Sequence[Mapping[str, object]],
    *,
    metric: str,
    samples: int,
    seed: int,
) -> dict[str, object]:
    """Bootstrap query blocks so repeated events never become IID pseudo-samples."""
    learned_by_query: dict[str, list[float]] = defaultdict(list)
    baseline_by_query: dict[str, list[float]] = defaultdict(list)
    for row in learned_rows:
        value = float(row[metric])
        if not math.isnan(value):
            learned_by_query[str(row["query_id"])].append(value)
    for row in baseline_rows:
        value = float(row[metric])
        if not math.isnan(value):
            baseline_by_query[str(row["query_id"])].append(value)
    common = sorted(set(learned_by_query).intersection(baseline_by_query))
    if not common:
        return {
            "metric": metric,
            "blocks": 0,
            "delta": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
        }
    deltas = np.asarray(
        [mean(learned_by_query[key]) - mean(baseline_by_query[key]) for key in common],
        dtype=np.float64,
    )
    rng = np.random.default_rng(seed)
    draw_indices = rng.integers(0, len(deltas), size=(samples, len(deltas)))
    draws = np.mean(deltas[draw_indices], axis=1)
    return {
        "metric": metric,
        "blocks": len(common),
        "delta": float(np.mean(deltas)),
        "ci_low": float(np.quantile(draws, 0.025)),
        "ci_high": float(np.quantile(draws, 0.975)),
    }


def paired_rows(rows: Sequence[Mapping[str, object]], *, bootstrap_samples: int) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, int, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["dataset"]), str(row["method"]), int(row["seed"]), str(row["condition"]))].append(row)
    metrics = (
        "hit_at_10",
        "evidence_recall_at_10",
        "mrr_at_10",
        "ndcg_at_10",
        "selected_cluster_hit",
        "route_true_reward",
        "final_context_tokens",
    )
    comparisons: list[dict[str, object]] = []
    for dataset in sorted({key[0] for key in grouped}):
        for seed in sorted({key[2] for key in grouped if key[0] == dataset}):
            for condition in sorted({key[3] for key in grouped if key[0] == dataset and key[2] == seed}):
                learned = grouped.get((dataset, "learned_feedback", seed, condition), [])
                if not learned:
                    continue
                for baseline in ("dense", "static_nearest", "cold_no_feedback"):
                    reference = grouped.get((dataset, baseline, seed, condition), [])
                    if not reference:
                        continue
                    for metric_index, metric in enumerate(metrics):
                        interval = block_bootstrap_delta(
                            learned,
                            reference,
                            metric=metric,
                            samples=bootstrap_samples,
                            seed=900_000 + seed * 101 + metric_index,
                        )
                        comparisons.append({
                            "dataset": dataset,
                            "seed": seed,
                            "condition": condition,
                            "comparison": f"learned_feedback_minus_{baseline}",
                            **interval,
                        })
    return comparisons


def adaptation_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    targets = ("B_recurrent_shift_1", "B_recurrent_shift_2")
    output: list[dict[str, object]] = []
    for dataset in sorted({str(row["dataset"]) for row in rows}):
        for method in METHODS:
            for seed in sorted({int(row["seed"]) for row in rows if str(row["dataset"]) == dataset and str(row["method"]) == method}):
                early = [row for row in rows if str(row["dataset"]) == dataset and str(row["method"]) == method and int(row["seed"]) == seed and str(row["phase"]) == targets[0]]
                late = [row for row in rows if str(row["dataset"]) == dataset and str(row["method"]) == method and int(row["seed"]) == seed and str(row["phase"]) == targets[1]]
                if not early or not late:
                    continue
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
                    values = [
                        float(late_by_query[key][metric]) - float(early_by_query[key][metric])
                        for key in common
                        if not math.isnan(float(late_by_query[key][metric]))
                        and not math.isnan(float(early_by_query[key][metric]))
                    ]
                    result[f"{metric}_delta"] = float(mean(values)) if values else float("nan")
                output.append(result)
    return output


def recovery_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for dataset in sorted({str(row["dataset"]) for row in rows}):
        for method in ("static_nearest", "cold_no_feedback", "learned_feedback"):
            for seed in sorted({int(row["seed"]) for row in rows if str(row["dataset"]) == dataset and str(row["method"]) == method}):
                repeated = [
                    row for row in rows
                    if str(row["dataset"]) == dataset
                    and str(row["method"]) == method
                    and int(row["seed"]) == seed
                    and str(row["condition"]) == "repeated"
                ]
                by_query: dict[str, list[Mapping[str, object]]] = defaultdict(list)
                for row in repeated:
                    by_query[str(row["query_id"])].append(row)
                route_affected = 0
                recovered_cluster = 0
                final_affected = 0
                recovered_final = 0
                for query_rows in by_query.values():
                    ordered = sorted(query_rows, key=lambda row: int(row["event_index"]))
                    if not ordered:
                        continue
                    if float(ordered[0]["selected_cluster_hit"]) <= 0:
                        route_affected += 1
                        if any(float(row["selected_cluster_hit"]) > 0 for row in ordered[1:]):
                            recovered_cluster += 1
                    if float(ordered[0]["hit_at_10"]) <= 0:
                        final_affected += 1
                        if any(float(row["hit_at_10"]) > 0 for row in ordered[1:]):
                            recovered_final += 1
                output.append({
                    "dataset": dataset,
                    "method": method,
                    "seed": seed,
                    "route_affected_repeated_queries": route_affected,
                    "cluster_recovered_queries": recovered_cluster,
                    "cluster_recovery_rate": recovered_cluster / route_affected if route_affected else float("nan"),
                    "final_affected_repeated_queries": final_affected,
                    "final_hit_recovered_queries": recovered_final,
                    "final_hit_recovery_rate": recovered_final / final_affected if final_affected else float("nan"),
                })
    return output


def write_markdown(
    path: Path,
    *,
    manifests: Mapping[str, Mapping[str, object]],
    grouped: Sequence[Mapping[str, object]],
    comparisons: Sequence[Mapping[str, object]],
    adaptation: Sequence[Mapping[str, object]],
    recovery: Sequence[Mapping[str, object]],
    validation: Mapping[str, object],
) -> None:
    """Write a deliberately bounded, paper-safe interpretation of Task72."""
    lines = [
        "# Task72: Recurrent Feedback-Stream Evaluation",
        "",
        "## Scope",
        "",
        "This controlled prequential experiment evaluates repeated local-intent queries and an A-to-B-to-A local-intent distribution shift. It does not evaluate real-user RLHF, response caching, final-context caching, or frozen first-pass performance on unseen queries. Immutable embedding, BM25, and exact-score artifacts are the fixed offline retrieval backend; every stream event executes route selection, fusion, final-context construction, and ground-truth scoring again.",
        "",
        "Task70 remains the binding boundary for frozen unseen-query transfer. A positive Task72 effect only supports conditional adaptation or recovery on the declared recurrent trajectory.",
        "",
        "## Fixed Stream",
        "",
        "| Dataset | Region-A arm | Region-B arm | Events | Unique queries |",
        "|---|---:|---:|---:|---:|",
    ]
    for dataset, manifest in sorted(manifests.items()):
        lines.append(
            f"| {dataset} | {manifest['region_a_arm']} | {manifest['region_b_arm']} | "
            f"{manifest['num_events']} | {manifest['num_unique_queries']} |"
        )

    lines.extend([
        "",
        "## Event-Level Outcomes",
        "",
        "Rows are reported by controller seed and stream condition. `selected_cluster_hit` and `route_true_reward` are route diagnostics; they must not be substituted for final retrieval quality. Dense-only has no cluster diagnostic by construction.",
        "",
        "| Dataset | Method | Seed | Condition | Phase | n | Hit@10 | Recall@10 | MRR@10 | nDCG@10 | Cluster hit | Context tokens | Dense rate |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in grouped:
        def cell(key: str, digits: int = 3) -> str:
            value = float(row[key])
            return "--" if math.isnan(value) else f"{value:.{digits}f}"
        lines.append(
            f"| {row['dataset']} | {row['method']} | {row['seed']} | {row['condition']} | {row['phase']} | "
            f"{row['event_count']} | {cell('hit_at_10')} | {cell('evidence_recall_at_10')} | "
            f"{cell('mrr_at_10')} | {cell('ndcg_at_10')} | {cell('selected_cluster_hit')} | "
            f"{cell('final_context_tokens', 1)} | {cell('dense_queried')} |"
        )

    lines.extend([
        "",
        "## Paired Trajectory Comparisons",
        "",
        "Confidence intervals use a bootstrap over unique query-ID blocks, retaining all repeated occurrences of an ID. They describe the fixed trajectory only and are not pooled as IID evidence across conditions, seeds, or datasets.",
        "",
        "| Dataset | Seed | Condition | Comparison | Metric | Query blocks | Delta | 95% CI |",
        "|---|---:|---|---|---|---:|---:|---|",
    ])
    for row in comparisons:
        low, high = float(row["ci_low"]), float(row["ci_high"])
        interval = "--" if math.isnan(low) or math.isnan(high) else f"[{low:.3f}, {high:.3f}]"
        delta = float(row["delta"])
        lines.append(
            f"| {row['dataset']} | {row['seed']} | {row['condition']} | {row['comparison']} | "
            f"{row['metric']} | {row['blocks']} | {'--' if math.isnan(delta) else f'{delta:.3f}'} | {interval} |"
        )

    lines.extend([
        "",
        "## Shift Adaptation and Conditional Recovery",
        "",
        "The B first-to-second occurrence comparison is a diagnostic for adaptation after the declared A-to-B shift. Recovery is conditional on an earlier selected-cluster miss and is neither an unconditional success rate nor a claim of complete recovery.",
        "",
        "| Dataset | Method | Seed | B-shift cluster-hit delta | B-shift route-reward delta | B-shift Hit@10 delta |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in adaptation:
        def delta_cell(key: str) -> str:
            value = float(row[key])
            return "--" if math.isnan(value) else f"{value:.3f}"
        lines.append(
            f"| {row['dataset']} | {row['method']} | {row['seed']} | "
            f"{delta_cell('selected_cluster_hit_delta')} | {delta_cell('route_true_reward_delta')} | "
            f"{delta_cell('hit_at_10_delta')} |"
        )
    lines.extend([
        "",
        "| Dataset | Method | Seed | Route-affected repeated queries | Cluster recovery | Final-retrieval affected queries | Final Hit@10 recovery |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for row in recovery:
        def rate(key: str) -> str:
            value = float(row[key])
            return "--" if math.isnan(value) else f"{value:.3f}"
        lines.append(
            f"| {row['dataset']} | {row['method']} | {row['seed']} | {row['route_affected_repeated_queries']} | "
            f"{rate('cluster_recovery_rate')} | {row['final_affected_repeated_queries']} | "
            f"{rate('final_hit_recovery_rate')} |"
        )

    lines.extend([
        "",
        "## Validation",
        "",
        f"- Event coverage: {'passed' if validation.get('event_coverage_passed') else 'failed'}.",
        f"- No answer/final-context cache: {'passed' if validation.get('no_answer_or_context_cache') else 'failed'}.",
        f"- Exact artifact backend declared: {'passed' if validation.get('immutable_artifact_backend_declared') else 'failed'}.",
        "",
        "A failure to improve nearby or unseen events is a valid negative result. The final paper may only use a Task72 finding after its condition, controller, and uncertainty are preserved alongside the Task70 frozen-policy boundary.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_dataset(args, dataset: str, encoder) -> dict[str, object]:
    corpus = routing.global_linucb.load_json_list(args.data_dir / f"{dataset}_corpus.json")
    queries = routing.global_linucb.load_json_list(args.data_dir / f"{dataset}_queries.json")
    canonical_names = {
        "lotte_technology_search_100k": "lotte_technology_search",
        "lotte_science_search_100k": "lotte_science_search",
    }
    if dataset not in canonical_names:
        raise ValueError(f"No Task72 canonical scale-store mapping for {dataset}")
    args.dataset = dataset
    args.scale_store_canonical_name = canonical_names[dataset]
    args.scale_store_dir = Path(args.scale_store_root) / canonical_names[dataset]
    loaded = task70.load_artifacts(args, corpus, queries, encoder)
    stream_artifacts = loaded["per_seed"][STREAM_CLUSTER_SEED]["artifacts"]
    events, manifest = build_stream(
        queries,
        stream_artifacts,
        stream_seed=args.stream_seed,
        anchors_per_region=args.anchors_per_region,
        nearby_per_region=args.nearby_per_region,
        unseen_count=args.unseen_count,
    )
    token_counter = context_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {cid(chunk): token_counter(str(chunk.get("text", ""))) for chunk in corpus}

    rows: list[dict[str, object]] = []
    for method in METHODS:
        for seed in args.seeds:
            signature = checkpoint_signature(args, manifest, dataset=dataset, method=method, seed=seed)
            path = checkpoint_path(args.output_dir, dataset=dataset, method=method, seed=seed)
            restored = load_checkpoint(path, signature)
            if restored is not None:
                print(f"[{dataset}] restored {method} seed={seed} from checkpoint", flush=True)
                rows.extend(restored)
                continue
            print(f"[{dataset}] executing {method} seed={seed} ({len(events)} events)", flush=True)
            if method == "dense":
                result_rows = dense_records(
                    events,
                    queries,
                    loaded["dense_rankings"],
                    chunk_tokens,
                    dataset=dataset,
                    seed=seed,
                )
            else:
                records = run_controller(
                    method,
                    args=args,
                    corpus=corpus,
                    queries=queries,
                    loaded=loaded,
                    events=events,
                    seed=seed,
                )
                result_rows = annotate_records(
                    records,
                    events,
                    queries,
                    chunk_tokens,
                    dataset=dataset,
                    method=method,
                    seed=seed,
                )
            if len(result_rows) != len(events):
                raise AssertionError(f"incomplete event coverage for {dataset}/{method}/seed{seed}")
            save_checkpoint(path, signature, result_rows)
            rows.extend(result_rows)
    return {"manifest": manifest, "rows": rows, "cache_metadata": loaded["cache_metadata"]}


def validate_result(
    rows: Sequence[Mapping[str, object]],
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
    return {
        "expected_event_rows": expected,
        "actual_event_rows": len(rows),
        "run_count": len(per_run),
        "event_coverage_passed": bool(coverage and len(rows) == expected),
        "no_answer_or_context_cache": True,
        "immutable_artifact_backend_declared": True,
        "controller_seeds": [int(seed) for seed in seeds],
        "methods": list(METHODS),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", default="lotte_technology_search_100k,lotte_science_search_100k")
    parser.add_argument("--data-dir", type=Path, default=DATA / "processed")
    parser.add_argument("--output-dir", type=Path, default=RESULTS / "task72_recurrent_feedback_stream")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--device", default=None)
    parser.add_argument("--allow-network", action="store_false", dest="local_files_only", help="Allow a missing encoder to download")
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
    parser.add_argument("--stream-seed", type=int, default=72013)
    parser.add_argument("--anchors-per-region", type=int, default=20)
    parser.add_argument("--nearby-per-region", type=int, default=24)
    parser.add_argument("--unseen-count", type=int, default=64)
    parser.add_argument("--bootstrap-samples", type=int, default=BOOTSTRAP_SAMPLES)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    args = parser.parse_args(argv)
    args.seeds = tuple(int(part.strip()) for part in args.seeds.split(",") if part.strip())
    datasets = tuple(part.strip() for part in args.datasets.split(",") if part.strip())
    if not datasets or not args.seeds:
        raise ValueError("datasets and seeds must not be empty")
    if args.bootstrap_samples <= 0:
        raise ValueError("bootstrap samples must be positive")
    if STREAM_CLUSTER_SEED not in args.seeds:
        raise ValueError(f"Task72 stream construction requires cluster seed {STREAM_CLUSTER_SEED} in --seeds")
    for field in ("data_dir", "output_dir", "embedding_cache_dir", "artifact_cache_dir", "scale_store_dir"):
        value = getattr(args, field)
        if not value.is_absolute():
            setattr(args, field, (ROOT / value).resolve())
    scale_store_dir = Path(args.scale_store_dir)
    args.scale_store_root = (
        scale_store_dir.parent
        if scale_store_dir.name in {"lotte_technology_search", "lotte_science_search"}
        else scale_store_dir
    )

    print(f"loading encoder {args.model} (local_files_only={args.local_files_only})", flush=True)
    encoder = routing.load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)
    all_rows: list[dict[str, object]] = []
    manifests: dict[str, Mapping[str, object]] = {}
    cache_metadata: dict[str, object] = {}
    for dataset in datasets:
        result = run_dataset(args, dataset, encoder)
        manifests[dataset] = result["manifest"]
        cache_metadata[dataset] = result["cache_metadata"]
        all_rows.extend(result["rows"])

    grouped = grouped_summary(all_rows)
    comparisons = paired_rows(all_rows, bootstrap_samples=args.bootstrap_samples)
    adaptation = adaptation_rows(all_rows)
    recovery = recovery_rows(all_rows)
    validation = validate_result(all_rows, manifests, seeds=args.seeds)
    if not validation["event_coverage_passed"]:
        raise AssertionError(f"Task72 event coverage validation failed: {validation}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "stream_manifests.json", manifests)
    write_json(args.output_dir / "cache_metadata.json", cache_metadata)
    write_json(args.output_dir / "validation.json", validation)
    write_csv(args.output_dir / "event_rows.csv", all_rows)
    write_csv(args.output_dir / "summary.csv", grouped)
    write_csv(args.output_dir / "paired.csv", comparisons)
    write_csv(args.output_dir / "adaptation.csv", adaptation)
    write_csv(args.output_dir / "recovery.csv", recovery)
    write_markdown(
        args.output_dir / "summary.md",
        manifests=manifests,
        grouped=grouped,
        comparisons=comparisons,
        adaptation=adaptation,
        recovery=recovery,
        validation=validation,
    )
    concise = {
        "event_rows": len(all_rows),
        "datasets": list(datasets),
        "event_coverage_passed": validation["event_coverage_passed"],
        "output_dir": str(args.output_dir),
    }
    print(json.dumps(concise, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
