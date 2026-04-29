#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hybrid BM25 + dense retrieval baseline using Reciprocal Rank Fusion."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bm25_baseline = _load_script_module("bm25_baseline", SCRIPT_DIR / "bm25_baseline.py")
dense_baseline = _load_script_module("dense_baseline", SCRIPT_DIR / "dense_baseline.py")
retrieval_metrics = _load_script_module("retrieval_metrics", SCRIPT_DIR / "retrieval_metrics.py")
experiment_guardrails = _load_script_module("experiment_guardrails", SCRIPT_DIR / "experiment_guardrails.py")

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DATASETS = ("pubmedqa", "banking77", "emanual", "cuad")
DEFAULT_MODEL = dense_baseline.DEFAULT_MODEL


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def parse_ks(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parse_datasets(value: str) -> tuple[str, ...]:
    if value == "all":
        return DEFAULT_DATASETS
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _query_id(query: Mapping) -> str:
    query_id = query.get("query_id") or query.get("id")
    if query_id is None:
        raise ValueError(f"Query missing query_id/id: {query}")
    return str(query_id)


def _slice_positive(value: int | None, name: str):
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]],
    *,
    rrf_k: int = 60,
    top_k: int = 10,
) -> List[str]:
    """Fuse ranked chunk-id lists with Reciprocal Rank Fusion.

    The score for a chunk is ``sum(1 / (rrf_k + rank))`` across input
    rankings. Ties are deterministic: higher score, then better best rank,
    then earlier first appearance.
    """
    if rrf_k < 0:
        raise ValueError(f"rrf_k must be non-negative, got {rrf_k}")
    if top_k <= 0:
        return []

    scores: Dict[str, float] = {}
    best_rank: Dict[str, int] = {}
    first_seen: Dict[str, int] = {}

    for ranking in rankings:
        seen_in_ranking: set[str] = set()
        for rank, chunk_id in enumerate(ranking, start=1):
            chunk_id = str(chunk_id)
            if chunk_id in seen_in_ranking:
                continue
            seen_in_ranking.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
            best_rank[chunk_id] = min(best_rank.get(chunk_id, rank), rank)
            if chunk_id not in first_seen:
                first_seen[chunk_id] = len(first_seen)

    ordered = sorted(
        scores,
        key=lambda chunk_id: (-scores[chunk_id], best_rank[chunk_id], first_seen[chunk_id], chunk_id),
    )
    return ordered[:top_k]


def run_hybrid(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    encoder,
    *,
    top_k: int = 10,
    ks: Sequence[int] = (1, 5, 10),
    batch_size: int = 64,
    rrf_k: int = 60,
    fusion_depth: int = 100,
    max_queries: int | None = None,
    max_corpus: int | None = None,
) -> Dict[str, object]:
    """Run BM25 and dense retrieval, fuse rankings with RRF, then evaluate."""
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
    if fusion_depth <= 0:
        raise ValueError(f"fusion_depth must be positive, got {fusion_depth}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if not corpus:
        raise ValueError("corpus must not be empty")

    max_queries = _slice_positive(max_queries, "max_queries")
    max_corpus = _slice_positive(max_corpus, "max_corpus")
    if max_corpus is not None:
        corpus = corpus[:max_corpus]
    if max_queries is not None:
        queries = queries[:max_queries]

    source_top_k = min(max(top_k, fusion_depth), len(corpus))
    bm25_result = bm25_baseline.run_bm25(corpus, queries, top_k=source_top_k, ks=ks)
    dense_result = dense_baseline.run_dense(
        corpus,
        queries,
        encoder,
        top_k=source_top_k,
        ks=ks,
        batch_size=batch_size,
    )

    fused_rankings: Dict[str, List[str]] = {}
    for query in queries:
        qid = _query_id(query)
        fused_rankings[qid] = reciprocal_rank_fusion(
            [
                bm25_result["rankings"].get(qid, []),
                dense_result["rankings"].get(qid, []),
            ],
            rrf_k=rrf_k,
            top_k=top_k,
        )

    metrics = retrieval_metrics.evaluate_rankings(queries, fused_rankings, ks=ks)
    return {"rankings": fused_rankings, "metrics": metrics}


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
    rrf_k: int,
    fusion_depth: int = 100,
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
) -> Dict[str, object]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    corpus = load_json_list(corpus_path)
    queries = load_json_list(queries_path)
    selected_queries = experiment_guardrails.apply_query_controls(
        queries,
        query_split=query_split,
        max_queries=max_queries,
    )
    resolved_corpus_sampling = experiment_guardrails.resolve_corpus_sampling(dataset, max_corpus, corpus_sampling)
    selected_corpus = experiment_guardrails.apply_corpus_controls(
        corpus,
        max_corpus=max_corpus,
        queries=selected_queries,
        corpus_sampling=resolved_corpus_sampling,
        random_seed=sampling_seed,
    )
    gt_coverage = experiment_guardrails.assert_gt_corpus_coverage(selected_queries, selected_corpus)

    start = time.perf_counter()
    result = run_hybrid(
        selected_corpus,
        selected_queries,
        encoder,
        top_k=top_k,
        ks=ks,
        batch_size=batch_size,
        rrf_k=rrf_k,
        fusion_depth=fusion_depth,
    )
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"hybrid_{dataset}_rankings.json"
    metrics_path = output_dir / f"hybrid_{dataset}_metrics.json"

    metrics = {
        "dataset": dataset,
        "method": "hybrid_rrf",
        "model": model_name,
        "top_k": top_k,
        "ks": list(ks),
        "batch_size": batch_size,
        "rrf_k": rrf_k,
        "fusion_depth": fusion_depth,
        "num_corpus_chunks": len(selected_corpus),
        "num_total_corpus_chunks": len(corpus),
        "num_total_queries": len(queries),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "elapsed_sec": round(elapsed_sec, 3),
        **experiment_guardrails.build_run_metadata(
            dataset=dataset,
            queries=selected_queries,
            all_queries=queries,
            corpus=selected_corpus,
            all_corpus=corpus,
            max_queries=max_queries,
            max_corpus=max_corpus,
            corpus_sampling=resolved_corpus_sampling,
            requested_query_split=query_split,
            top_k=top_k,
            ks=ks,
        ),
        **gt_coverage,
        **result["metrics"],
    }

    with rankings_path.open("w", encoding="utf-8") as f:
        json.dump(result["rankings"], f, ensure_ascii=False)
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, sort_keys=True)

    return metrics


def update_summary(summary_path: Path, metrics_rows: Iterable[Mapping]) -> None:
    rows = list(metrics_rows)
    if not rows:
        return

    existing: Dict[tuple[str, str, str], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(row.get("dataset", ""), row.get("method", ""), row.get("model", ""))] = row

    for row in rows:
        existing[(str(row["dataset"]), str(row["method"]), str(row.get("model", "")))] = row

    metric_keys = sorted({key for row in existing.values() for key in row if "@" in key})
    fieldnames = [
        "dataset",
        "method",
        "model",
        "num_queries",
        "num_skipped_no_gt",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "num_total_queries",
        "num_query_candidates",
        "max_queries",
        "max_corpus",
        "corpus_sampling",
        "top_k",
        "task_type",
        "scope",
        "query_split",
        "query_splits",
        "query_scope",
        "corpus_scope",
        "num_queries_with_gt",
        "num_queries_with_gt_in_corpus",
        "num_queries_gt_missing_from_corpus",
        "num_gt_refs",
        "num_gt_refs_in_corpus",
        "num_gt_refs_missing_from_corpus",
        "gt_query_coverage",
        "gt_ref_coverage",
        "gt_corpus_guardrail",
        "comparable_group",
        "is_comparable",
        "metric_ks",
        "fusion_depth",
        "rrf_k",
        *metric_keys,
        "elapsed_sec",
        "notes",
    ]

    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow({
                name: "|".join(str(item) for item in value) if isinstance(value, (list, tuple)) else value
                for name, value in existing[key].items()
            })


def load_sentence_transformer(model_name: str, *, device: str | None = None, local_files_only: bool = False):
    return dense_baseline.load_sentence_transformer(model_name, device=device, local_files_only=local_files_only)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run hybrid BM25 + dense retrieval baseline with RRF")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None, help="SentenceTransformer device, e.g. cpu/cuda")
    parser.add_argument("--local-files-only", action="store_true", help="Load model from local HF cache only")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--fusion-depth", type=int, default=100, help="Per-source ranking depth before RRF")
    parser.add_argument("--rrf-k", type=int, default=60, help="RRF rank constant")
    parser.add_argument("--ks", default="1,5,10", help="Comma-separated metric cutoffs")
    parser.add_argument("--max-queries", type=int, default=None, help="Evaluate only the first N queries")
    parser.add_argument("--max-corpus", type=int, default=None, help="Use only the first N corpus chunks")
    parser.add_argument("--query-split", default=None, help="Evaluate only one query split, e.g. test")
    parser.add_argument(
        "--corpus-sampling",
        default="auto",
        choices=sorted(experiment_guardrails.CORPUS_SAMPLING_STRATEGIES),
        help="Corpus sampling strategy; auto uses GT-anchored CUAD samples when max-corpus is set",
    )
    parser.add_argument("--sampling-seed", type=int, default=13, help="Random seed for sampled distractors")
    args = parser.parse_args(argv)

    datasets = parse_datasets(args.dataset)
    ks = parse_ks(args.ks)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    metrics_rows = []
    for dataset in datasets:
        print(f"Running hybrid RRF baseline: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            top_k=args.top_k,
            ks=ks,
            batch_size=args.batch_size,
            rrf_k=args.rrf_k,
            fusion_depth=args.fusion_depth,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
        )
        metrics_rows.append(metrics)
        metric_text = ", ".join(f"{key}={metrics[key]:.4f}" for key in sorted(metrics) if "@" in key)
        print(
            f"  chunks={metrics['num_corpus_chunks']} queries={metrics['num_queries']} "
            f"skipped_no_gt={metrics['num_skipped_no_gt']} "
            f"gt_query_coverage={metrics['gt_query_coverage']:.4f} elapsed={metrics['elapsed_sec']}s"
        )
        print(f"  {metric_text}")

    update_summary(args.output_dir / "hybrid_baseline_summary.csv", metrics_rows)
    print(f"Summary: {args.output_dir / 'hybrid_baseline_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
