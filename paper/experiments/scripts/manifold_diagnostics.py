#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manifold-structure diagnostics for IntentWeight retrieval datasets.

Task 14 measures whether each dataset has exploitable local structure before
further optimizing feedback or cost-aware routing. The diagnostics are designed
to stay at the retrieval layer:

* PCA spectrum and intrinsic-dimensionality proxies;
* cluster balance and label alignment;
* local neighborhood purity in the PCA context space;
* query-to-GT cluster routing hit rates;
* dense vs PCA-context GT recall preservation.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


global_linucb = _load_script_module("linucb_online_baseline", SCRIPT_DIR / "linucb_online_baseline.py")
dense_baseline = global_linucb.dense_baseline
experiment_guardrails = global_linucb.experiment_guardrails

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


def infer_label(record: Mapping, dataset: str) -> str | None:
    """Infer a corpus label for cluster/local-purity diagnostics."""
    metadata = record.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    if dataset == "banking77":
        label = metadata.get("intent_name") or metadata.get("intent_id")
    elif dataset == "pubmedqa":
        label = metadata.get("pubid") or record.get("doc_id")
    elif dataset in {"emanual", "cuad"}:
        label = metadata.get("record_id") or record.get("doc_id")
    else:
        label = metadata.get("record_id") or metadata.get("source") or record.get("doc_id")
    return None if label in (None, "") else str(label)


def pca_spectrum_metrics(embeddings: np.ndarray, dims: Sequence[int] = (8, 16, 32, 64)) -> Dict[str, object]:
    """Compute PCA spectrum metrics from the embedding covariance eigenvalues."""
    if len(embeddings) < 2:
        return {"pca_num_components": 0}

    x = np.asarray(embeddings, dtype=np.float64)
    x = x - np.mean(x, axis=0, keepdims=True)
    cov = (x.T @ x) / max(1, len(x) - 1)
    eigvals = np.linalg.eigvalsh(cov)[::-1]
    eigvals = np.maximum(eigvals, 0.0)
    total = float(np.sum(eigvals))
    if total <= 0:
        ratios = np.zeros_like(eigvals)
    else:
        ratios = eigvals / total
    cumulative = np.cumsum(ratios)

    metrics: Dict[str, object] = {
        "pca_num_components": int(len(eigvals)),
        "pca_participation_ratio_dim": float((total * total) / np.sum(eigvals * eigvals)) if np.sum(eigvals * eigvals) > 0 else 0.0,
        "pca_spectral_entropy_dim": float(np.exp(-np.sum(ratios[ratios > 0] * np.log(ratios[ratios > 0])))) if total > 0 else 0.0,
    }
    for dim in dims:
        effective_dim = min(int(dim), len(cumulative))
        metrics[f"pca_var@{dim}"] = float(cumulative[effective_dim - 1]) if effective_dim else 0.0
    for target in (0.8, 0.9, 0.95):
        idx = int(np.searchsorted(cumulative, target, side="left"))
        metrics[f"pca_dim_for_{int(target * 100)}pct"] = int(idx + 1) if idx < len(cumulative) else -1
    return metrics


def cluster_size_metrics(labels: np.ndarray) -> Dict[str, object]:
    labels = np.asarray(labels, dtype=np.int32)
    if labels.size == 0:
        return {}
    counts = np.bincount(labels)
    counts = counts[counts > 0]
    probs = counts / np.sum(counts)
    entropy = -float(np.sum(probs * np.log(probs))) if counts.size else 0.0
    normalized_entropy = entropy / math.log(len(counts)) if len(counts) > 1 else 1.0
    return {
        "n_effective_clusters": int(len(counts)),
        "cluster_size_min": int(np.min(counts)),
        "cluster_size_max": int(np.max(counts)),
        "cluster_size_mean": float(np.mean(counts)),
        "cluster_size_std": float(np.std(counts)),
        "cluster_size_entropy_norm": float(normalized_entropy),
        "cluster_singleton_fraction": float(np.mean(counts == 1)),
    }


def label_alignment_metrics(labels: np.ndarray, corpus_labels: Sequence[str | None]) -> Dict[str, object]:
    valid_indices = [idx for idx, label in enumerate(corpus_labels) if label is not None]
    if not valid_indices:
        return {
            "label_coverage": 0.0,
            "cluster_label_purity": 0.0,
            "cluster_label_nmi": 0.0,
            "cluster_label_ari": 0.0,
            "num_unique_labels": 0,
        }

    cluster_labels = np.asarray([int(labels[idx]) for idx in valid_indices], dtype=np.int32)
    text_labels = [str(corpus_labels[idx]) for idx in valid_indices]
    total = len(valid_indices)
    purity_hits = 0
    for cluster_id in sorted(set(cluster_labels.tolist())):
        members = [text_labels[pos] for pos, value in enumerate(cluster_labels) if value == cluster_id]
        if members:
            purity_hits += Counter(members).most_common(1)[0][1]

    return {
        "label_coverage": float(total / len(corpus_labels)) if corpus_labels else 0.0,
        "cluster_label_purity": float(purity_hits / total) if total else 0.0,
        "cluster_label_nmi": float(normalized_mutual_info_score(text_labels, cluster_labels)) if len(set(text_labels)) > 1 else 0.0,
        "cluster_label_ari": float(adjusted_rand_score(text_labels, cluster_labels)) if len(set(text_labels)) > 1 else 0.0,
        "num_unique_labels": int(len(set(text_labels))),
    }


def sampled_silhouette(
    vectors: np.ndarray,
    labels: np.ndarray,
    *,
    sample_size: int,
    seed: int,
) -> float:
    if sample_size <= 1 or len(vectors) <= 2:
        return 0.0
    unique = np.unique(labels)
    if unique.size < 2:
        return 0.0
    rng = np.random.default_rng(seed)
    sample_count = min(sample_size, len(vectors))
    indices = np.sort(rng.choice(len(vectors), size=sample_count, replace=False))
    sample_labels = labels[indices]
    if np.unique(sample_labels).size < 2 or np.unique(sample_labels).size >= len(indices):
        return 0.0
    return float(silhouette_score(vectors[indices], sample_labels, metric="euclidean"))


def local_label_purity(
    vectors: np.ndarray,
    corpus_labels: Sequence[str | None],
    *,
    neighbor_k: int,
    sample_size: int,
    seed: int,
) -> Dict[str, object]:
    if neighbor_k <= 0:
        raise ValueError(f"neighbor_k must be positive, got {neighbor_k}")
    valid_indices = [idx for idx, label in enumerate(corpus_labels) if label is not None]
    if not valid_indices:
        return {"local_label_purity": 0.0, "local_label_hit_rate": 0.0, "local_label_sample_size": 0}

    rng = np.random.default_rng(seed)
    sample_count = min(sample_size, len(valid_indices))
    sampled_positions = rng.choice(len(valid_indices), size=sample_count, replace=False)
    sampled_indices = [valid_indices[int(pos)] for pos in sampled_positions]

    purities: List[float] = []
    hit_rates: List[float] = []
    matrix = np.asarray(vectors, dtype=np.float32)
    for idx in sampled_indices:
        label = corpus_labels[idx]
        scores = matrix @ matrix[idx]
        scores[idx] = -np.inf
        k = min(neighbor_k, len(scores) - 1)
        if k <= 0:
            continue
        if k == len(scores):
            neighbors = np.arange(len(scores))
        else:
            neighbors = np.argpartition(-scores, k - 1)[:k]
        same = [corpus_labels[int(neighbor)] == label for neighbor in neighbors if corpus_labels[int(neighbor)] is not None]
        if not same:
            continue
        purities.append(float(np.mean(same)))
        hit_rates.append(float(any(same)))

    return {
        "local_label_purity": float(np.mean(purities)) if purities else 0.0,
        "local_label_hit_rate": float(np.mean(hit_rates)) if hit_rates else 0.0,
        "local_label_sample_size": int(len(purities)),
    }


def _top_indices(scores: np.ndarray, k: int) -> List[int]:
    if k <= 0:
        return []
    k = min(k, len(scores))
    if k == len(scores):
        candidates = np.arange(len(scores))
    else:
        candidates = np.argpartition(-scores, k - 1)[:k]
    return sorted(candidates.tolist(), key=lambda idx: (-float(scores[idx]), int(idx)))


def query_gt_manifold_metrics(
    queries: Sequence[Mapping],
    query_embeddings: np.ndarray,
    corpus_embeddings: np.ndarray,
    query_context: np.ndarray,
    corpus_context: np.ndarray,
    labels: np.ndarray,
    *,
    chunk_ids: Sequence[str],
    cluster_hit_ks: Sequence[int],
    recall_ks: Sequence[int],
) -> Dict[str, object]:
    chunk_index = {chunk_id: idx for idx, chunk_id in enumerate(chunk_ids)}
    centroids = np.zeros((int(np.max(labels)) + 1, corpus_context.shape[1]), dtype=np.float32)
    for cluster_id in range(len(centroids)):
        members = np.flatnonzero(labels == cluster_id)
        if members.size:
            centroids[cluster_id] = np.mean(corpus_context[members], axis=0)
    centroids = global_linucb.l2_normalize(centroids)

    counts = {
        "num_gt_eval_queries": 0,
        "num_gt_refs_eval": 0,
    }
    cluster_hits = {int(k): 0 for k in cluster_hit_ks}
    dense_hits = {int(k): 0 for k in recall_ks}
    context_hits = {int(k): 0 for k in recall_ks}
    gt_cluster_spans: List[int] = []
    gt_cluster_concentrations: List[float] = []
    best_dense_sims: List[float] = []
    best_context_sims: List[float] = []

    max_recall_k = max(recall_ks)
    max_cluster_k = max(cluster_hit_ks)
    for query_idx, query in enumerate(queries):
        gt = _ground_truth(query)
        gt_indices = [chunk_index[chunk_id] for chunk_id in gt if chunk_id in chunk_index]
        if not gt_indices:
            continue
        counts["num_gt_eval_queries"] += 1
        counts["num_gt_refs_eval"] += len(gt_indices)
        gt_index_set = set(gt_indices)

        gt_clusters = [int(labels[idx]) for idx in gt_indices]
        gt_cluster_set = set(gt_clusters)
        gt_cluster_spans.append(len(gt_cluster_set))
        gt_counts = Counter(gt_clusters)
        gt_cluster_concentrations.append(max(gt_counts.values()) / len(gt_clusters))

        cluster_scores = centroids @ query_context[query_idx]
        nearest_clusters = _top_indices(cluster_scores, max_cluster_k)
        for k in cluster_hit_ks:
            cluster_hits[int(k)] += int(bool(gt_cluster_set & set(nearest_clusters[: int(k)])))

        dense_scores = corpus_embeddings @ query_embeddings[query_idx]
        context_scores = corpus_context @ query_context[query_idx]
        dense_top = _top_indices(dense_scores, max_recall_k)
        context_top = _top_indices(context_scores, max_recall_k)
        for k in recall_ks:
            dense_hits[int(k)] += int(bool(gt_index_set & set(dense_top[: int(k)])))
            context_hits[int(k)] += int(bool(gt_index_set & set(context_top[: int(k)])))
        best_dense_sims.append(float(np.max(dense_scores[gt_indices])))
        best_context_sims.append(float(np.max(context_scores[gt_indices])))

    n = counts["num_gt_eval_queries"]
    metrics: Dict[str, object] = {
        **counts,
        "gt_cluster_span_mean": float(np.mean(gt_cluster_spans)) if gt_cluster_spans else 0.0,
        "gt_cluster_concentration_mean": float(np.mean(gt_cluster_concentrations)) if gt_cluster_concentrations else 0.0,
        "gt_best_dense_similarity_mean": float(np.mean(best_dense_sims)) if best_dense_sims else 0.0,
        "gt_best_context_similarity_mean": float(np.mean(best_context_sims)) if best_context_sims else 0.0,
    }
    for k in cluster_hit_ks:
        metrics[f"nearest_cluster_hit@{int(k)}"] = float(cluster_hits[int(k)] / n) if n else 0.0
    for k in recall_ks:
        metrics[f"dense_gt_recall@{int(k)}"] = float(dense_hits[int(k)] / n) if n else 0.0
        metrics[f"context_gt_recall@{int(k)}"] = float(context_hits[int(k)] / n) if n else 0.0
        dense_value = metrics[f"dense_gt_recall@{int(k)}"]
        metrics[f"context_recall_retention@{int(k)}"] = (
            float(metrics[f"context_gt_recall@{int(k)}"] / dense_value)
            if dense_value
            else 0.0
        )
    return metrics


def run_diagnostics(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    dataset: str,
    n_clusters: int,
    context_dim: int,
    seed: int,
    sample_size: int,
    neighbor_k: int,
    cluster_hit_ks: Sequence[int],
    recall_ks: Sequence[int],
) -> Dict[str, object]:
    _, corpus_context, query_context = global_linucb.fit_context_projection(corpus_embeddings, query_embeddings, context_dim)
    corpus_context = global_linucb.l2_normalize(corpus_context)
    query_context = global_linucb.l2_normalize(query_context)
    labels = global_linucb.cluster_corpus(corpus_context, n_clusters=n_clusters, seed=seed)
    corpus_labels = [infer_label(chunk, dataset) for chunk in corpus]
    chunk_ids = [_chunk_id(chunk) for chunk in corpus]

    metrics: Dict[str, object] = {
        **pca_spectrum_metrics(corpus_embeddings),
        **cluster_size_metrics(labels),
        **label_alignment_metrics(labels, corpus_labels),
        "cluster_silhouette_sample": sampled_silhouette(corpus_context, labels, sample_size=sample_size, seed=seed),
        **local_label_purity(
            corpus_context,
            corpus_labels,
            neighbor_k=neighbor_k,
            sample_size=sample_size,
            seed=seed,
        ),
        **query_gt_manifold_metrics(
            queries,
            query_embeddings,
            corpus_embeddings,
            query_context,
            corpus_context,
            labels,
            chunk_ids=chunk_ids,
            cluster_hit_ks=cluster_hit_ks,
            recall_ks=recall_ks,
        ),
    }
    return metrics


def run_dataset(
    dataset: str,
    data_dir: Path,
    output_dir: Path,
    encoder,
    *,
    model_name: str,
    batch_size: int,
    n_clusters: int,
    context_dim: int,
    seed: int,
    sample_size: int,
    neighbor_k: int,
    cluster_hit_ks: Sequence[int],
    recall_ks: Sequence[int],
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
) -> Dict[str, object]:
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
    diagnostics = run_diagnostics(
        corpus,
        queries,
        corpus_embeddings,
        query_embeddings,
        dataset=dataset,
        n_clusters=n_clusters,
        context_dim=context_dim,
        seed=seed,
        sample_size=sample_size,
        neighbor_k=neighbor_k,
        cluster_hit_ks=cluster_hit_ks,
        recall_ks=recall_ks,
    )
    elapsed_sec = time.perf_counter() - start

    metadata = {
        "dataset": dataset,
        "method": "manifold_diagnostics",
        "model": model_name,
        "batch_size": batch_size,
        "n_clusters_requested": n_clusters,
        "context_dim_requested": context_dim,
        "seed": seed,
        "sample_size": sample_size,
        "neighbor_k": neighbor_k,
        "cluster_hit_ks": list(cluster_hit_ks),
        "recall_ks": list(recall_ks),
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
            top_k=max(recall_ks),
            ks=recall_ks,
        ),
        **gt_coverage,
    }
    metrics = {**metadata, **diagnostics}

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / f"manifold_diagnostics_{dataset}.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def _stringify_csv_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


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

    base_fieldnames = [
        "dataset",
        "method",
        "model",
        "task_type",
        "scope",
        "query_split",
        "corpus_scope",
        "corpus_sampling",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "num_total_queries",
        "num_queries_with_gt_in_corpus",
        "gt_query_coverage",
        "max_queries",
        "max_corpus",
        "batch_size",
        "n_clusters_requested",
        "context_dim_requested",
        "seed",
        "sample_size",
        "neighbor_k",
        "cluster_hit_ks",
        "recall_ks",
    ]
    metric_keys = sorted({
        key
        for row in existing.values()
        for key in row
        if key not in set(base_fieldnames)
        and (
            "@" in key
            or key.startswith("pca_")
            or key.startswith("cluster_")
            or key.startswith("local_")
            or key.startswith("nearest_")
            or key.startswith("gt_")
            or key.startswith("context_")
            or key.startswith("dense_")
            or key.startswith("label_")
            or key in {"num_unique_labels", "n_effective_clusters", "num_gt_eval_queries", "num_gt_refs_eval"}
        )
    })
    fieldnames = [*base_fieldnames, *metric_keys, "elapsed_sec", "notes"]
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
    parser = argparse.ArgumentParser(description="Run manifold-structure diagnostics")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--n-clusters", type=int, default=32)
    parser.add_argument("--context-dim", type=int, default=64)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--neighbor-k", type=int, default=10)
    parser.add_argument("--cluster-hit-ks", default="1,3,5")
    parser.add_argument("--recall-ks", default="1,5,10")
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
    cluster_hit_ks = parse_ints(args.cluster_hit_ks)
    recall_ks = parse_ints(args.recall_ks)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    rows = []
    for dataset in datasets:
        print(f"Running manifold diagnostics: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            batch_size=args.batch_size,
            n_clusters=args.n_clusters,
            context_dim=args.context_dim,
            seed=args.seed,
            sample_size=args.sample_size,
            neighbor_k=args.neighbor_k,
            cluster_hit_ks=cluster_hit_ks,
            recall_ks=recall_ks,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
        )
        rows.append(metrics)
        print(
            f"  chunks={metrics['num_corpus_chunks']} queries={metrics.get('num_gt_eval_queries')} "
            f"pca_dim90={metrics.get('pca_dim_for_90pct')} "
            f"cluster_purity={metrics.get('cluster_label_purity', 0.0):.4f} "
            f"local_purity={metrics.get('local_label_purity', 0.0):.4f} "
            f"nearest_cluster_hit@3={metrics.get('nearest_cluster_hit@3', 0.0):.4f} "
            f"context_recall@10={metrics.get('context_gt_recall@10', 0.0):.4f} "
            f"elapsed={metrics['elapsed_sec']}s"
        )

    update_summary(args.output_dir / "manifold_diagnostics_summary.csv", rows)
    print(f"Summary: {args.output_dir / 'manifold_diagnostics_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
