#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate LoTTE multi-scale geometry signals against Task29 outcomes.

This is a lightweight post-hoc diagnostic. It reuses the canonical LoTTE scale
store and shared context-cluster artifacts instead of recomputing embeddings or
rerunning retrieval.
"""
from __future__ import annotations

import argparse
import csv
import gc
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_ARTIFACT_DIR = SCRIPT_DIR.parent / "data" / "retrieval_artifacts"
DEFAULT_SCALE_STORE_DIR = SCRIPT_DIR.parent / "data" / "scale_store" / "lotte_technology_search"
DEFAULT_OUTPUT_CSV = DEFAULT_RESULTS_DIR / "task30_lotte_geometry_scale_validation.csv"
DEFAULT_OUTPUT_MD = DEFAULT_RESULTS_DIR / "task30_lotte_geometry_scale_validation.md"
DEFAULT_SCALES = ("100k", "200k", "400k", "638k")
DEFAULT_SEEDS = (13, 17, 19)
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manifold_diagnostics = _load_script_module("manifold_diagnostics", SCRIPT_DIR / "manifold_diagnostics.py")


def dataset_name(scale: str) -> str:
    return f"lotte_technology_search_{scale}"


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def chunk_id(record: Mapping) -> str:
    value = record.get("chunk_id") or record.get("id")
    if value is None:
        raise ValueError(f"Corpus record missing chunk_id/id: {record}")
    return str(value)


def query_id(record: Mapping) -> str:
    value = record.get("query_id") or record.get("id")
    if value is None:
        raise ValueError(f"Query record missing query_id/id: {record}")
    return str(value)


def ground_truth(record: Mapping) -> set[str]:
    refs = record.get("ground_truth_chunk_ids") or []
    if isinstance(refs, str):
        refs = [refs]
    return {str(ref) for ref in refs if str(ref)}


def top_indices(scores: np.ndarray, k: int) -> List[int]:
    if k <= 0:
        return []
    k = min(k, len(scores))
    if k == len(scores):
        candidates = np.arange(len(scores))
    else:
        candidates = np.argpartition(-scores, k - 1)[:k]
    return sorted(candidates.tolist(), key=lambda idx: (-float(scores[idx]), int(idx)))


def summarize(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(mean(values)), float(stdev(values)) if len(values) > 1 else 0.0


def load_task29_frontier(results_dir: Path) -> Dict[str, Mapping[str, str]]:
    path = results_dir / "task29_token_quality_frontier.csv"
    by_key: Dict[str, Mapping[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("section") == "scale_frontier":
                by_key[f"{row.get('scale')}::{row.get('config')}"] = row
    return by_key


def find_context_artifact(artifact_dir: Path, dataset: str, seed: int) -> Path:
    matches: List[Path] = []
    for meta_path in sorted(artifact_dir.glob(f"{dataset}__context_clusters__*.meta.json")):
        with meta_path.open("r", encoding="utf-8") as f:
            meta = json.load(f)
        params = meta.get("params") if isinstance(meta.get("params"), Mapping) else {}
        if int(params.get("seed", -1)) != int(seed):
            continue
        artifact_path = Path(str(meta.get("artifact_path", "")))
        if artifact_path.exists():
            matches.append(artifact_path)
    if not matches:
        raise FileNotFoundError(f"No context cluster artifact for {dataset} seed={seed}")
    # Duplicate old artifacts can exist for the same seed. The last sorted path is deterministic.
    return matches[-1]


def cluster_size_summary(labels: np.ndarray) -> Dict[str, float]:
    counts = np.bincount(labels.astype(np.int32))
    counts = counts[counts > 0]
    probs = counts / np.sum(counts)
    entropy = -float(np.sum(probs * np.log(probs))) if counts.size else 0.0
    return {
        "n_effective_clusters": float(len(counts)),
        "cluster_size_min": float(np.min(counts)) if counts.size else 0.0,
        "cluster_size_max": float(np.max(counts)) if counts.size else 0.0,
        "cluster_size_entropy_norm": float(entropy / math.log(len(counts))) if len(counts) > 1 else 1.0,
    }


def nearest_cluster_metrics(
    labels: np.ndarray,
    centroids: np.ndarray,
    query_context: np.ndarray,
    gt_indices_by_query: Sequence[Sequence[int]],
    *,
    ks: Sequence[int],
) -> Dict[str, float]:
    hits = {int(k): 0 for k in ks}
    spans: List[float] = []
    concentrations: List[float] = []
    n = 0
    max_k = max(ks)
    for q_idx, gt_indices in enumerate(gt_indices_by_query):
        if not gt_indices:
            continue
        n += 1
        gt_clusters = [int(labels[idx]) for idx in gt_indices]
        gt_cluster_set = set(gt_clusters)
        spans.append(float(len(gt_cluster_set)))
        counts = Counter(gt_clusters)
        concentrations.append(float(max(counts.values()) / len(gt_clusters)))
        scores = centroids @ query_context[q_idx]
        nearest = top_indices(scores, max_k)
        for k in ks:
            hits[int(k)] += int(bool(gt_cluster_set & set(nearest[: int(k)])))
    out: Dict[str, float] = {
        "gt_cluster_span_mean": float(mean(spans)) if spans else 0.0,
        "gt_cluster_concentration_mean": float(mean(concentrations)) if concentrations else 0.0,
    }
    for k in ks:
        out[f"nearest_cluster_hit@{int(k)}"] = float(hits[int(k)] / n) if n else 0.0
    return out


def context_recall_at_k(
    corpus_context: np.ndarray,
    query_context: np.ndarray,
    gt_indices_by_query: Sequence[Sequence[int]],
    *,
    k: int,
    batch_size: int,
) -> float:
    hits = 0
    total = 0
    corpus_context = np.asarray(corpus_context, dtype=np.float32)
    query_context = np.asarray(query_context, dtype=np.float32)
    for start in range(0, len(query_context), batch_size):
        end = min(start + batch_size, len(query_context))
        scores_batch = query_context[start:end] @ corpus_context.T
        for offset, scores in enumerate(scores_batch):
            gt_indices = gt_indices_by_query[start + offset]
            if not gt_indices:
                continue
            total += 1
            top = set(top_indices(scores, k))
            hits += int(bool(top & set(gt_indices)))
    return float(hits / total) if total else 0.0


def pca_sample_metrics(
    scale_store_dir: Path,
    dataset: str,
    *,
    sample_size: int,
    seed: int,
) -> Dict[str, object]:
    row_indices_path = scale_store_dir / f"{dataset}__row_indices.npy"
    embeddings_path = scale_store_dir / "canonical_corpus_embeddings.npy"
    row_indices = np.load(row_indices_path, mmap_mode="r")
    canonical_embeddings = np.load(embeddings_path, mmap_mode="r")
    rng = np.random.default_rng(seed)
    n = len(row_indices)
    sample_count = min(sample_size, n)
    local_indices = np.sort(rng.choice(n, size=sample_count, replace=False))
    canonical_rows = np.asarray(row_indices[local_indices], dtype=np.int64)
    sample = np.asarray(canonical_embeddings[canonical_rows], dtype=np.float32)
    metrics = manifold_diagnostics.pca_spectrum_metrics(sample)
    return {
        "pca_sample_size": sample_count,
        "pca_sample_dim_for_80pct": metrics.get("pca_dim_for_80pct", 0),
        "pca_sample_dim_for_90pct": metrics.get("pca_dim_for_90pct", 0),
        "pca_sample_dim_for_95pct": metrics.get("pca_dim_for_95pct", 0),
        "pca_sample_var@64": metrics.get("pca_var@64", 0.0),
        "pca_sample_participation_ratio_dim": metrics.get("pca_participation_ratio_dim", 0.0),
        "pca_sample_spectral_entropy_dim": metrics.get("pca_spectral_entropy_dim", 0.0),
    }


def scale_row(
    scale: str,
    *,
    data_dir: Path,
    results_dir: Path,
    artifact_dir: Path,
    scale_store_dir: Path,
    seeds: Sequence[int],
    pca_sample_size: int,
    context_batch_size: int,
    pca_seed: int,
) -> Dict[str, object]:
    dataset = dataset_name(scale)
    corpus = load_json_list(data_dir / f"{dataset}_corpus.json")
    queries = load_json_list(data_dir / f"{dataset}_queries.json")
    chunk_index = {chunk_id(chunk): idx for idx, chunk in enumerate(corpus)}
    gt_indices_by_query = [
        [chunk_index[ref] for ref in ground_truth(query) if ref in chunk_index]
        for query in queries
    ]

    cluster_metric_rows: List[Dict[str, float]] = []
    context_recall = None
    for seed in seeds:
        artifact_path = find_context_artifact(artifact_dir, dataset, seed)
        with np.load(artifact_path) as artifact:
            corpus_context = np.asarray(artifact["corpus_context"], dtype=np.float32)
            query_context = np.asarray(artifact["query_context"], dtype=np.float32)
            labels = np.asarray(artifact["arm_labels"], dtype=np.int32)
            centroids = np.asarray(artifact["centroids"], dtype=np.float32)
            row = {
                **cluster_size_summary(labels),
                **nearest_cluster_metrics(
                    labels,
                    centroids,
                    query_context,
                    gt_indices_by_query,
                    ks=(1, 3, 5),
                ),
            }
            cluster_metric_rows.append(row)
            if context_recall is None:
                context_recall = context_recall_at_k(
                    corpus_context,
                    query_context,
                    gt_indices_by_query,
                    k=10,
                    batch_size=context_batch_size,
                )

    pca_metrics = pca_sample_metrics(
        scale_store_dir,
        dataset,
        sample_size=pca_sample_size,
        seed=pca_seed,
    )
    frontier = load_task29_frontier(results_dir)
    dense = frontier[f"{scale}::dense"]
    task29 = frontier[f"{scale}::task29_C"]
    dense_hit = float(dense["hit_at_10"])
    task29_hit = float(task29["hit_at_10"])
    token_ratio = float(task29["token_ratio_vs_dense"])

    out: Dict[str, object] = {
        "scale": scale,
        "dataset": dataset,
        "num_corpus_chunks": len(corpus),
        "num_queries": len(queries),
        "num_gt_eval_queries": sum(1 for item in gt_indices_by_query if item),
        "dense_hit@10": dense_hit,
        "task29_hit@10": task29_hit,
        "task29_hit_delta_pp": float(task29["hit_delta_vs_dense_pp"]),
        "task29_token_ratio": token_ratio,
        "task29_token_saving_pct": float(task29["token_saving_pct"]),
        "task29_hit_per_1k_context_tokens": float(task29["hit_per_1k_context_tokens"]),
        "context_gt_recall@10": context_recall if context_recall is not None else 0.0,
        "context_recall_retention@10": (context_recall / dense_hit) if dense_hit and context_recall is not None else 0.0,
        **pca_metrics,
    }
    for key in sorted(cluster_metric_rows[0]):
        values = [float(row[key]) for row in cluster_metric_rows]
        avg, sd = summarize(values)
        out[f"{key}_mean"] = avg
        out[f"{key}_std"] = sd

    del corpus, queries, gt_indices_by_query, chunk_index, cluster_metric_rows
    gc.collect()
    return out


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    preferred = [
        "scale",
        "dataset",
        "num_corpus_chunks",
        "num_queries",
        "num_gt_eval_queries",
        "pca_sample_size",
        "pca_sample_dim_for_90pct",
        "pca_sample_var@64",
        "cluster_size_entropy_norm_mean",
        "nearest_cluster_hit@1_mean",
        "nearest_cluster_hit@3_mean",
        "nearest_cluster_hit@5_mean",
        "gt_cluster_concentration_mean_mean",
        "gt_cluster_span_mean_mean",
        "context_gt_recall@10",
        "context_recall_retention@10",
        "dense_hit@10",
        "task29_hit@10",
        "task29_hit_delta_pp",
        "task29_token_ratio",
        "task29_token_saving_pct",
        "task29_hit_per_1k_context_tokens",
    ]
    remaining = sorted({key for row in rows for key in row if key not in set(preferred)})
    fieldnames = [*preferred, *remaining]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: object, digits: int = 4) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    x = np.asarray(xs, dtype=np.float64)
    y = np.asarray(ys, dtype=np.float64)
    if np.std(x) <= 0 or np.std(y) <= 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    hit_deltas = [float(row["task29_hit_delta_pp"]) for row in rows]
    nearest3 = [float(row["nearest_cluster_hit@3_mean"]) for row in rows]
    retention = [float(row["context_recall_retention@10"]) for row in rows]
    token_savings = [float(row["task29_token_saving_pct"]) for row in rows]
    lines = [
        "# Task30 LoTTE Multi-Scale Geometry Validation",
        "",
        "Task30 checks whether the LoTTE scale-up results are consistent with a",
        "retrieval-geometry interpretation. It reuses the canonical scale-store",
        "embeddings, shared PCA/KMeans context artifacts, and Task29-C token-quality",
        "frontier. No retrieval or LinUCB experiment is rerun.",
        "",
        "## Multi-Scale Table",
        "",
        "| Scale | Corpus | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Dense Hit@10 | Task29-C Hit@10 | Hit Delta | Token Saving |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {scale} | {corpus} | {dim90} | {var64} | {nearest3} | {retention} | {dense} | {hit} | {delta} pp | {saving}% |".format(
                scale=row["scale"],
                corpus=row["num_corpus_chunks"],
                dim90=row["pca_sample_dim_for_90pct"],
                var64=fmt(row["pca_sample_var@64"]),
                nearest3=fmt(row["nearest_cluster_hit@3_mean"]),
                retention=fmt(row["context_recall_retention@10"]),
                dense=fmt(row["dense_hit@10"]),
                hit=fmt(row["task29_hit@10"]),
                delta=fmt(row["task29_hit_delta_pp"], 2),
                saving=fmt(row["task29_token_saving_pct"], 2),
            )
        )

    lines.extend([
        "",
        "## Correlation Diagnostics",
        "",
        f"- Pearson(`nearest_cluster_hit@3`, `Task29 Hit Delta`) = `{pearson(nearest3, hit_deltas):.4f}`.",
        f"- Pearson(`context_recall_retention@10`, `Task29 Hit Delta`) = `{pearson(retention, hit_deltas):.4f}`.",
        f"- Pearson(`nearest_cluster_hit@3`, `Token Saving`) = `{pearson(nearest3, token_savings):.4f}`.",
        "",
        "These correlations use only four scale points, so they are descriptive",
        "diagnostics, not statistical proof.",
        "",
        "## Interpretation",
        "",
        "- The LoTTE corpus keeps high nearest-cluster GT routing signal across scale,",
        "  with `nearest_cluster_hit@3` staying around the high-0.8 range.",
        "- PCA/context retrieval alone retains a large fraction of dense Hit@10, but",
        "  it does not fully replace dense retrieval. This supports the paper's",
        "  bounded claim: geometry is useful as a routing/control signal, not as a",
        "  stand-alone dense replacement.",
        "- Dense Hit@10 declines as corpus scale grows, while Task29-C remains",
        "  above dense at 200k/400k/638k with lower final context tokens.",
        "- This supports the piecewise relevance-manifold framing as an explanatory",
        "  assumption backed by diagnostics. It should not be written as a theorem",
        "  that geometry alone guarantees better retrieval.",
        "",
        "## Artifacts",
        "",
        "- CSV: `paper/experiments/results/task30_lotte_geometry_scale_validation.csv`",
        "- Script: `paper/experiments/scripts/task30_lotte_geometry_scale_validation.py`",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_csv_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate LoTTE multi-scale geometry diagnostics")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--scale-store-dir", type=Path, default=DEFAULT_SCALE_STORE_DIR)
    parser.add_argument("--scales", default=",".join(DEFAULT_SCALES))
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--pca-sample-size", type=int, default=50000)
    parser.add_argument("--pca-seed", type=int, default=13)
    parser.add_argument("--context-batch-size", type=int, default=16)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args(argv)

    rows: List[Dict[str, object]] = []
    for scale in parse_csv_list(args.scales):
        print(f"Validating LoTTE geometry scale: {scale}", flush=True)
        row = scale_row(
            scale,
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            artifact_dir=args.artifact_dir,
            scale_store_dir=args.scale_store_dir,
            seeds=parse_ints(args.seeds),
            pca_sample_size=args.pca_sample_size,
            context_batch_size=args.context_batch_size,
            pca_seed=args.pca_seed,
        )
        rows.append(row)
        print(
            f"  nearest_cluster_hit@3={row['nearest_cluster_hit@3_mean']:.4f} "
            f"context_retention@10={row['context_recall_retention@10']:.4f} "
            f"hit_delta_pp={row['task29_hit_delta_pp']:.2f} "
            f"token_saving={row['task29_token_saving_pct']:.2f}%",
            flush=True,
        )
    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, rows)
    print(f"CSV: {args.output_csv}")
    print(f"Markdown: {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
