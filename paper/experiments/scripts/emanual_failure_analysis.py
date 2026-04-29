#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 14.5: eManual failure analysis.

The eManual full corpus contains many repeated manual sentences. A strict
chunk-id metric can therefore mark a retrieval as wrong even when the retrieved
sentence text is identical to a ground-truth sentence from another RAGBench
record. This diagnostic keeps the original strict metric, but adds:

* duplicate-text and weak-label statistics;
* text-equivalent evaluation for existing rankings;
* retrieval on a text-deduplicated eManual corpus;
* nearest-centroid local routing and GT-cluster oracle checks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TEXT_RE = re.compile(r"\s+")


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bm25_baseline = _load_script_module("bm25_baseline", SCRIPT_DIR / "bm25_baseline.py")
dense_baseline = _load_script_module("dense_baseline", SCRIPT_DIR / "dense_baseline.py")
hybrid_baseline = _load_script_module("hybrid_baseline", SCRIPT_DIR / "hybrid_baseline.py")
linucb_soft = _load_script_module("linucb_soft_routing", SCRIPT_DIR / "linucb_soft_routing.py")
global_linucb = linucb_soft.global_linucb
manifold_linucb = linucb_soft.manifold_linucb
experiment_guardrails = linucb_soft.experiment_guardrails
retrieval_metrics = linucb_soft.retrieval_metrics


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def load_json_mapping(path: Path) -> Mapping:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, Mapping):
        raise ValueError(f"Expected JSON mapping: {path}")
    return data


def normalize_text(text: str) -> str:
    """Normalize text for exact text-equivalence diagnostics."""
    return TEXT_RE.sub(" ", (text or "").strip().lower())


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def _chunk_id(chunk: Mapping) -> str:
    return str(chunk.get("chunk_id") or chunk.get("id"))


def _query_id(query: Mapping) -> str:
    return str(query.get("query_id") or query.get("id"))


def _ground_truth(query: Mapping) -> set[str]:
    gt = query.get("ground_truth_chunk_ids", [])
    return {str(chunk_id) for chunk_id in gt or []}


def _record_id(record: Mapping) -> str | None:
    metadata = record.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    value = metadata.get("record_id") or record.get("doc_id")
    return None if value in (None, "") else str(value)


def _safe_hash(text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"emanual_text_{digest}"


def duplicate_text_stats(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    *,
    random_neighbor_k: int = 10,
) -> Dict[str, object]:
    chunk_by_id = {_chunk_id(chunk): chunk for chunk in corpus}
    text_counts = Counter(normalize_text(str(chunk.get("text", ""))) for chunk in corpus)
    duplicate_counts = [count for count in text_counts.values() if count > 1]
    gt_duplicate_counts: List[int] = []
    missing_gt = 0
    for query in queries:
        for chunk_id in _ground_truth(query):
            chunk = chunk_by_id.get(chunk_id)
            if chunk is None:
                missing_gt += 1
                continue
            gt_duplicate_counts.append(text_counts[normalize_text(str(chunk.get("text", "")))])

    labels = [_record_id(chunk) for chunk in corpus]
    label_counts = Counter(label for label in labels if label is not None)
    n = len(corpus)
    random_purity = 0.0
    random_hit = 0.0
    if n > 1 and label_counts:
        random_purity = sum(count * (count - 1) for count in label_counts.values()) / float(n * (n - 1))
        for count in label_counts.values():
            no_hit = 1.0
            failures = n - count
            draws = min(random_neighbor_k, n - 1)
            for draw in range(draws):
                denominator = n - 1 - draw
                if denominator <= 0:
                    no_hit = 0.0
                    break
                no_hit *= max(0.0, (failures - draw) / denominator)
            random_hit += (count / n) * (1.0 - no_hit)

    return {
        "num_corpus_chunks": int(len(corpus)),
        "num_unique_texts": int(len(text_counts)),
        "duplicate_text_groups": int(len(duplicate_counts)),
        "chunks_in_duplicate_text_groups": int(sum(duplicate_counts)),
        "duplicate_text_group_max_size": int(max(duplicate_counts) if duplicate_counts else 0),
        "duplicate_text_group_mean_size": float(np.mean(duplicate_counts)) if duplicate_counts else 0.0,
        "num_eval_queries": int(len(queries)),
        "num_gt_refs_eval": int(len(gt_duplicate_counts)),
        "num_gt_refs_missing": int(missing_gt),
        "gt_refs_with_duplicate_text": int(sum(1 for count in gt_duplicate_counts if count > 1)),
        "gt_ref_duplicate_count_mean": float(np.mean(gt_duplicate_counts)) if gt_duplicate_counts else 0.0,
        "gt_ref_duplicate_count_median": float(np.median(gt_duplicate_counts)) if gt_duplicate_counts else 0.0,
        "gt_ref_duplicate_count_max": int(max(gt_duplicate_counts) if gt_duplicate_counts else 0),
        "record_label_unique_count": int(len(label_counts)),
        "random_record_neighbor_purity": float(random_purity),
        f"random_record_neighbor_hit@{random_neighbor_k}": float(random_hit),
    }


def _metric_empty(ks: Sequence[int]) -> Dict[str, object]:
    metrics: Dict[str, object] = {"num_queries": 0, "num_skipped_no_gt": 0}
    for k in ks:
        metrics[f"recall@{int(k)}"] = 0.0
        metrics[f"mrr@{int(k)}"] = 0.0
        metrics[f"ndcg@{int(k)}"] = 0.0
    return metrics


def _dcg_at_ranks(ranks: Sequence[int]) -> float:
    return sum(1.0 / math.log2(rank + 1) for rank in ranks)


def evaluate_text_equivalent_rankings(
    queries: Iterable[Mapping],
    rankings: Mapping[str, Sequence[str]],
    chunk_by_id: Mapping[str, Mapping],
    *,
    ks: Sequence[int],
    skip_empty_gt: bool = True,
) -> Dict[str, object]:
    """Evaluate rankings by normalized sentence text instead of chunk_id."""
    ks = tuple(sorted({int(k) for k in ks}))
    if not ks or any(k <= 0 for k in ks):
        raise ValueError(f"ks must contain positive integers, got {ks}")

    chunk_text = {
        str(chunk_id): normalize_text(str(chunk.get("text", "")))
        for chunk_id, chunk in chunk_by_id.items()
    }
    totals = _metric_empty(ks)
    for query in queries:
        qid = _query_id(query)
        gt_ids = _ground_truth(query)
        gt_texts = {chunk_text[chunk_id] for chunk_id in gt_ids if chunk_id in chunk_text}
        if not gt_texts and skip_empty_gt:
            totals["num_skipped_no_gt"] += 1
            continue

        ranked_texts = [chunk_text[str(chunk_id)] for chunk_id in rankings.get(qid, []) if str(chunk_id) in chunk_text]
        totals["num_queries"] += 1
        for k in ks:
            seen_texts: set[str] = set()
            relevant_ranks: List[int] = []
            first_relevant_rank = 0
            for rank, text in enumerate(ranked_texts[:k], start=1):
                if text in seen_texts:
                    continue
                seen_texts.add(text)
                if text in gt_texts:
                    relevant_ranks.append(rank)
                    if not first_relevant_rank:
                        first_relevant_rank = rank
            totals[f"recall@{k}"] += 1.0 if relevant_ranks else 0.0
            totals[f"mrr@{k}"] += 1.0 / first_relevant_rank if first_relevant_rank else 0.0
            ideal_hits = min(len(gt_texts), k)
            ideal = _dcg_at_ranks(range(1, ideal_hits + 1))
            totals[f"ndcg@{k}"] += (_dcg_at_ranks(relevant_ranks) / ideal) if ideal else 0.0

    n = int(totals["num_queries"])
    if n:
        for k in ks:
            totals[f"recall@{k}"] = float(totals[f"recall@{k}"] / n)
            totals[f"mrr@{k}"] = float(totals[f"mrr@{k}"] / n)
            totals[f"ndcg@{k}"] = float(totals[f"ndcg@{k}"] / n)
    totals["num_queries"] = n
    totals["num_skipped_no_gt"] = int(totals["num_skipped_no_gt"])
    return totals


def load_ranking_sets(path: Path) -> Dict[str, Dict[str, List[str]]]:
    """Load a ranking JSON that may be single-run or seed-nested."""
    data = load_json_mapping(path)
    if not data:
        return {}
    if all(isinstance(value, list) for value in data.values()):
        return {
            "single": {
                str(query_id): [str(chunk_id) for chunk_id in ranking]
                for query_id, ranking in data.items()
            }
        }
    if all(isinstance(value, Mapping) for value in data.values()):
        return {
            str(seed): {
                str(query_id): [str(chunk_id) for chunk_id in ranking]
                for query_id, ranking in rankings.items()
            }
            for seed, rankings in data.items()
        }
    raise ValueError(f"Unsupported ranking JSON shape: {path}")


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(np.mean(values)), float(np.std(values))


def aggregate_metrics(
    method: str,
    evaluation_mode: str,
    metrics_by_seed: Mapping[str, Mapping[str, object]],
    *,
    ks: Sequence[int],
    source: str,
) -> Dict[str, object]:
    row: Dict[str, object] = {
        "method": method,
        "source": source,
        "evaluation_mode": evaluation_mode,
        "num_seeds": int(len(metrics_by_seed)),
    }
    if not metrics_by_seed:
        return row
    row["num_queries"] = int(next(iter(metrics_by_seed.values())).get("num_queries", 0))
    row["num_skipped_no_gt"] = int(next(iter(metrics_by_seed.values())).get("num_skipped_no_gt", 0))
    for k in ks:
        for metric in ("recall", "mrr", "ndcg"):
            values = [float(metrics[f"{metric}@{int(k)}"]) for metrics in metrics_by_seed.values()]
            mean, std = _mean_std(values)
            row[f"{metric}@{int(k)}_mean"] = mean
            row[f"{metric}@{int(k)}_std"] = std
    return row


def evaluate_existing_rankings(
    queries: Sequence[Mapping],
    corpus: Sequence[Mapping],
    ranking_files: Mapping[str, Path],
    *,
    ks: Sequence[int],
) -> List[Dict[str, object]]:
    chunk_by_id = {_chunk_id(chunk): chunk for chunk in corpus}
    rows: List[Dict[str, object]] = []
    for method, path in ranking_files.items():
        if not path.exists():
            continue
        ranking_sets = load_ranking_sets(path)
        strict_by_seed = {
            seed: retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
            for seed, rankings in ranking_sets.items()
        }
        text_by_seed = {
            seed: evaluate_text_equivalent_rankings(queries, rankings, chunk_by_id, ks=ks)
            for seed, rankings in ranking_sets.items()
        }
        rows.append(aggregate_metrics(method, "strict_chunk_id", strict_by_seed, ks=ks, source=path.name))
        rows.append(aggregate_metrics(method, "text_equivalent", text_by_seed, ks=ks, source=path.name))
    return rows


def deduplicate_corpus_and_queries(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
) -> tuple[List[Dict[str, object]], List[Dict[str, object]], Dict[str, str]]:
    """Collapse exact duplicate normalized texts into one synthetic chunk."""
    text_to_chunk_id: Dict[str, str] = {}
    text_counts = Counter(normalize_text(str(chunk.get("text", ""))) for chunk in corpus)
    dedup_corpus: List[Dict[str, object]] = []
    chunk_to_dedup_id: Dict[str, str] = {}
    for chunk in corpus:
        text = normalize_text(str(chunk.get("text", "")))
        dedup_id = text_to_chunk_id.get(text)
        if dedup_id is None:
            dedup_id = _safe_hash(text)
            text_to_chunk_id[text] = dedup_id
            metadata = dict(chunk.get("metadata") or {})
            metadata.update({
                "source": "emanual_deduplicated_text",
                "representative_chunk_id": _chunk_id(chunk),
                "duplicate_count": int(text_counts[text]),
            })
            dedup_corpus.append({
                "chunk_id": dedup_id,
                "text": str(chunk.get("text", "")),
                "doc_id": "emanual_deduplicated_text",
                "metadata": metadata,
            })
        chunk_to_dedup_id[_chunk_id(chunk)] = dedup_id

    dedup_queries: List[Dict[str, object]] = []
    for query in queries:
        mapped_gt = sorted({chunk_to_dedup_id[chunk_id] for chunk_id in _ground_truth(query) if chunk_id in chunk_to_dedup_id})
        query_copy = dict(query)
        metadata = dict(query.get("metadata") or {})
        metadata["source"] = "emanual_deduplicated_text"
        query_copy["metadata"] = metadata
        query_copy["ground_truth_chunk_ids"] = mapped_gt
        dedup_queries.append(query_copy)
    return dedup_corpus, dedup_queries, chunk_to_dedup_id


def run_deduplicated_baselines(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    encoder,
    *,
    top_k: int,
    ks: Sequence[int],
    batch_size: int,
    rrf_k: int,
    fusion_depth: int,
) -> tuple[List[Dict[str, object]], Dict[str, Dict[str, List[str]]]]:
    dedup_corpus, dedup_queries, _ = deduplicate_corpus_and_queries(corpus, queries)
    rows: List[Dict[str, object]] = []
    rankings_by_method: Dict[str, Dict[str, List[str]]] = {}

    bm25_result = bm25_baseline.run_bm25(dedup_corpus, dedup_queries, top_k=top_k, ks=ks)
    dense_result = dense_baseline.run_dense(dedup_corpus, dedup_queries, encoder, top_k=top_k, ks=ks, batch_size=batch_size)
    hybrid_result = hybrid_baseline.run_hybrid(
        dedup_corpus,
        dedup_queries,
        encoder,
        top_k=top_k,
        ks=ks,
        batch_size=batch_size,
        rrf_k=rrf_k,
        fusion_depth=fusion_depth,
    )

    for method, result in (
        ("dedup_bm25", bm25_result),
        ("dedup_dense", dense_result),
        ("dedup_hybrid_rrf", hybrid_result),
    ):
        metrics = result["metrics"]
        row: Dict[str, object] = {
            "method": method,
            "evaluation_mode": "deduplicated_text_corpus",
            "num_corpus_chunks": int(len(dedup_corpus)),
            "num_original_corpus_chunks": int(len(corpus)),
            "num_queries": int(metrics.get("num_queries", 0)),
            "num_skipped_no_gt": int(metrics.get("num_skipped_no_gt", 0)),
        }
        for k in ks:
            for metric in ("recall", "mrr", "ndcg"):
                row[f"{metric}@{int(k)}"] = float(metrics[f"{metric}@{int(k)}"])
        rows.append(row)
        rankings_by_method[method] = result["rankings"]
    return rows, rankings_by_method


def _top_indices(scores: np.ndarray, k: int) -> List[int]:
    if k <= 0:
        return []
    k = min(k, len(scores))
    if k == len(scores):
        candidates = np.arange(len(scores))
    else:
        candidates = np.argpartition(-scores, k - 1)[:k]
    return sorted(candidates.tolist(), key=lambda idx: (-float(scores[idx]), int(idx)))


def _routing_rankings(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    labels: np.ndarray,
    query_context: np.ndarray,
    centroids: np.ndarray,
    *,
    cluster_count: int | str,
    top_k: int,
) -> Dict[str, List[str]]:
    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    chunk_index = {chunk_id: idx for idx, chunk_id in enumerate(chunk_ids)}
    rankings: Dict[str, List[str]] = {}
    for query_idx, query in enumerate(queries):
        if isinstance(cluster_count, int):
            cluster_scores = centroids @ query_context[query_idx]
            selected_clusters = set(_top_indices(cluster_scores, cluster_count))
        elif cluster_count == "gt_clusters":
            gt_indices = [chunk_index[chunk_id] for chunk_id in _ground_truth(query) if chunk_id in chunk_index]
            selected_clusters = {int(labels[idx]) for idx in gt_indices}
        else:
            raise ValueError(f"Unsupported cluster_count: {cluster_count}")

        if not selected_clusters:
            rankings[_query_id(query)] = []
            continue
        scores = corpus_embeddings @ query_embeddings[query_idx]
        mask = np.isin(labels, np.asarray(sorted(selected_clusters), dtype=np.int32))
        masked_scores = np.where(mask, scores, -np.inf)
        top = _top_indices(masked_scores, top_k)
        rankings[_query_id(query)] = [chunk_ids[idx] for idx in top if np.isfinite(masked_scores[idx])]
    return rankings


def run_centroid_routing(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    n_clusters: int,
    context_dim: int,
    seed: int,
    cluster_counts: Sequence[int],
    top_k: int,
    ks: Sequence[int],
) -> List[Dict[str, object]]:
    _, corpus_context, query_context = global_linucb.fit_context_projection(corpus_embeddings, query_embeddings, context_dim)
    corpus_context = global_linucb.l2_normalize(corpus_context)
    query_context = global_linucb.l2_normalize(query_context)
    labels = global_linucb.cluster_corpus(corpus_context, n_clusters=n_clusters, seed=seed)
    centroids = manifold_linucb.arm_centroids(corpus_context, labels, int(np.max(labels)) + 1)
    centroids = global_linucb.l2_normalize(centroids)
    chunk_by_id = {_chunk_id(chunk): chunk for chunk in corpus}

    rows: List[Dict[str, object]] = []
    for cluster_count in [*cluster_counts, "gt_clusters"]:
        rankings = _routing_rankings(
            corpus,
            queries,
            corpus_embeddings,
            query_embeddings,
            labels,
            query_context,
            centroids,
            cluster_count=cluster_count,
            top_k=top_k,
        )
        strict = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
        text_equiv = evaluate_text_equivalent_rankings(queries, rankings, chunk_by_id, ks=ks)
        method = (
            f"nearest_centroid_{cluster_count}_clusters"
            if isinstance(cluster_count, int)
            else "gt_cluster_oracle"
        )
        for mode, metrics in (("strict_chunk_id", strict), ("text_equivalent", text_equiv)):
            row: Dict[str, object] = {
                "method": method,
                "evaluation_mode": mode,
                "n_clusters": int(n_clusters),
                "context_dim": int(context_dim),
                "seed": int(seed),
                "num_queries": int(metrics.get("num_queries", 0)),
                "num_skipped_no_gt": int(metrics.get("num_skipped_no_gt", 0)),
            }
            for k in ks:
                for metric in ("recall", "mrr", "ndcg"):
                    row[f"{metric}@{int(k)}"] = float(metrics[f"{metric}@{int(k)}"])
            rows.append(row)
    return rows


def load_linucb_soft_diagnostics(results_dir: Path) -> Dict[str, object]:
    path = results_dir / "linucb_soft_emanual_prequential_metrics.json"
    if not path.exists():
        return {}
    metrics = dict(load_json_mapping(path))
    keys = [
        "selected_cluster_hit_rate_mean",
        "selected_cluster_miss_rate_mean",
        "cluster_local_hit_rate_mean",
        "dense_fallback_hit_rate_mean",
        "bm25_fallback_hit_rate_mean",
        "soft_fused_hit_rate_mean",
        "soft_rescue_on_cluster_miss_rate_mean",
        "recall@10_mean",
        "mrr@10_mean",
        "num_queries_mean",
        "num_seeds",
    ]
    return {key: metrics[key] for key in keys if key in metrics}


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    preferred = [
        "method",
        "source",
        "evaluation_mode",
        "num_seeds",
        "num_queries",
        "num_skipped_no_gt",
        "num_corpus_chunks",
        "num_original_corpus_chunks",
        "n_clusters",
        "context_dim",
        "seed",
    ]
    fieldnames = [key for key in preferred if key in fieldnames] + [key for key in fieldnames if key not in preferred]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_markdown(
    path: Path,
    *,
    duplicate_stats: Mapping[str, object],
    existing_rows: Sequence[Mapping[str, object]],
    dedup_rows: Sequence[Mapping[str, object]],
    routing_rows: Sequence[Mapping[str, object]],
    linucb_diagnostics: Mapping[str, object],
) -> None:
    def table(rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> List[str]:
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
        for row in rows:
            lines.append("| " + " | ".join(_fmt(row.get(col, "")) for col in columns) + " |")
        return lines

    lines: List[str] = ["# Task 14.5 eManual Failure Analysis", ""]
    lines += table(
        [duplicate_stats],
        [
            "num_corpus_chunks",
            "num_unique_texts",
            "duplicate_text_groups",
            "gt_refs_with_duplicate_text",
            "gt_ref_duplicate_count_mean",
            "random_record_neighbor_purity",
            "random_record_neighbor_hit@10",
        ],
    )
    lines += ["", "## Existing Rankings", ""]
    lines += table(
        existing_rows,
        [
            "method",
            "evaluation_mode",
            "num_seeds",
            "recall@10_mean",
            "mrr@10_mean",
            "ndcg@10_mean",
        ],
    )
    lines += ["", "## Deduplicated Corpus Baselines", ""]
    lines += table(
        dedup_rows,
        [
            "method",
            "evaluation_mode",
            "num_corpus_chunks",
            "recall@10",
            "mrr@10",
            "ndcg@10",
        ],
    )
    lines += ["", "## Centroid Routing", ""]
    lines += table(
        routing_rows,
        [
            "method",
            "evaluation_mode",
            "recall@10",
            "mrr@10",
            "ndcg@10",
        ],
    )
    if linucb_diagnostics:
        lines += ["", "## LinUCB Soft Diagnostics", ""]
        lines += table([linucb_diagnostics], sorted(linucb_diagnostics))
    lines += [
        "",
        "## Interpretation",
        "",
        "- Low record-id purity cannot exclude usable geometry because `record_id` is an instance-level label, not a semantic topic label.",
        "- Strict chunk-id recall is heavily affected by duplicate manual sentences across records.",
        "- Text-equivalent and deduplicated-corpus metrics should be reported as diagnostics, not replacements for the strict main table.",
        "- If nearest-centroid routing is strong while LinUCB-selected-cluster diagnostics are weak, the failure is likely policy/fusion/credit assignment rather than absence of geometry.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 14.5 eManual failure analysis")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--query-split", default="test")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--fusion-depth", type=int, default=100)
    parser.add_argument("--n-clusters", type=int, default=32)
    parser.add_argument("--context-dim", type=int, default=64)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--cluster-counts", default="1,3,5")
    parser.add_argument("--skip-embedding-runs", action="store_true")
    args = parser.parse_args()

    if args.top_k <= 0:
        raise ValueError("--top-k must be positive")
    ks = parse_ints(args.ks)
    cluster_counts = parse_ints(args.cluster_counts)
    corpus_all = load_json_list(args.data_dir / "emanual_corpus.json")
    queries_all = load_json_list(args.data_dir / "emanual_queries.json")
    queries = experiment_guardrails.apply_query_controls(queries_all, query_split=args.query_split)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    duplicate_stats = duplicate_text_stats(corpus_all, queries, random_neighbor_k=args.top_k)
    ranking_files = {
        "bm25": args.results_dir / "bm25_emanual_rankings.json",
        "dense": args.results_dir / "dense_emanual_rankings.json",
        "hybrid_rrf": args.results_dir / "hybrid_emanual_rankings.json",
        "linucb_soft": args.results_dir / "linucb_soft_emanual_prequential_rankings.json",
    }
    existing_rows = evaluate_existing_rankings(queries, corpus_all, ranking_files, ks=ks)
    dedup_rows: List[Dict[str, object]] = []
    routing_rows: List[Dict[str, object]] = []

    if not args.skip_embedding_runs:
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(args.model)
        dedup_rows, dedup_rankings = run_deduplicated_baselines(
            corpus_all,
            queries,
            encoder,
            top_k=args.top_k,
            ks=ks,
            batch_size=args.batch_size,
            rrf_k=args.rrf_k,
            fusion_depth=args.fusion_depth,
        )
        with (args.results_dir / "emanual_deduplicated_rankings.json").open("w", encoding="utf-8") as f:
            json.dump(dedup_rankings, f, ensure_ascii=False)

        corpus_embeddings = dense_baseline.encode_texts(
            encoder,
            [str(chunk.get("text", "")) for chunk in corpus_all],
            batch_size=args.batch_size,
        )
        query_embeddings = dense_baseline.encode_texts(
            encoder,
            [str(query.get("text", "")) for query in queries],
            batch_size=args.batch_size,
        )
        routing_rows = run_centroid_routing(
            corpus_all,
            queries,
            corpus_embeddings,
            query_embeddings,
            n_clusters=args.n_clusters,
            context_dim=args.context_dim,
            seed=args.seed,
            cluster_counts=cluster_counts,
            top_k=args.top_k,
            ks=ks,
        )

    linucb_diagnostics = load_linucb_soft_diagnostics(args.results_dir)
    elapsed_sec = time.perf_counter() - start
    report = {
        "dataset": "emanual",
        "task": "14.5_failure_analysis",
        "query_split": args.query_split,
        "model": args.model,
        "top_k": args.top_k,
        "ks": list(ks),
        "elapsed_sec": round(elapsed_sec, 3),
        "duplicate_text_stats": duplicate_stats,
        "existing_ranking_evaluation": existing_rows,
        "deduplicated_corpus_baselines": dedup_rows,
        "centroid_routing": routing_rows,
        "linucb_soft_diagnostics": linucb_diagnostics,
        "interpretation": [
            "record_id is an instance-level label and should not be treated as a semantic topic label",
            "strict chunk-id recall underestimates evidence retrieval when duplicate manual sentences appear across records",
            "text-equivalent and deduplicated-corpus metrics indicate whether semantic evidence is found even when strict IDs miss",
            "nearest-centroid vs LinUCB-selected routing separates usable geometry from policy/fusion failures",
        ],
    }

    json_path = args.results_dir / "emanual_failure_analysis.json"
    csv_path = args.results_dir / "emanual_failure_analysis_tables.csv"
    md_path = args.results_dir / "emanual_failure_analysis_tables.md"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
    write_csv(csv_path, [*existing_rows, *dedup_rows, *routing_rows])
    write_markdown(
        md_path,
        duplicate_stats=duplicate_stats,
        existing_rows=existing_rows,
        dedup_rows=dedup_rows,
        routing_rows=routing_rows,
        linucb_diagnostics=linucb_diagnostics,
    )

    print(f"Task 14.5 eManual failure analysis written to {json_path}")
    print(f"Tables: {csv_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
