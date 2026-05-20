#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate BM25-only baselines from shared large-scale ranking artifacts."""
from __future__ import annotations

import argparse
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
experiment_guardrails = _load_script_module("experiment_guardrails", SCRIPT_DIR / "experiment_guardrails.py")
large_scale_artifacts = _load_script_module("large_scale_artifacts", SCRIPT_DIR / "large_scale_artifacts.py")
retrieval_metrics = _load_script_module("retrieval_metrics", SCRIPT_DIR / "retrieval_metrics.py")

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_ARTIFACT_CACHE_DIR = large_scale_artifacts.DEFAULT_ARTIFACT_CACHE_DIR


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def parse_ks(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parse_datasets(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _query_id(query: Mapping) -> str:
    query_id = query.get("query_id") or query.get("id")
    if query_id is None:
        raise ValueError(f"Query missing query_id/id: {query}")
    return str(query_id)


def run_dataset(
    dataset: str,
    data_dir: Path,
    output_dir: Path,
    *,
    top_k: int,
    ks: Sequence[int],
    depth: int,
    query_split: str | None = None,
    max_queries: int | None = None,
    max_corpus: int | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
    artifact_cache_dir: Path = DEFAULT_ARTIFACT_CACHE_DIR,
    force_artifact_cache: bool = False,
) -> Dict[str, object]:
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
    if depth < top_k:
        raise ValueError(f"depth must be >= top_k, got depth={depth}, top_k={top_k}")

    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    corpus_all = load_json_list(corpus_path)
    queries_all = load_json_list(queries_path)
    queries = experiment_guardrails.apply_query_controls(
        queries_all,
        query_split=query_split,
        max_queries=max_queries,
    )
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
    bm25_rankings, artifact_info = large_scale_artifacts.load_or_compute_bm25_rankings(
        corpus,
        queries,
        dataset=dataset,
        depth=max(depth, top_k),
        cache_dir=artifact_cache_dir,
        force=force_artifact_cache,
    )
    rankings = {
        _query_id(query): bm25_rankings.get(_query_id(query), [])[:top_k]
        for query in queries
    }
    metrics_result = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"bm25_{dataset}_rankings.json"
    metrics_path = output_dir / f"bm25_{dataset}_metrics.json"

    metrics = {
        "dataset": dataset,
        "method": "bm25",
        "ranking_source": "shared_bm25_artifact",
        "top_k": top_k,
        "ks": list(ks),
        "artifact_depth": max(depth, top_k),
        "num_corpus_chunks": len(corpus),
        "num_total_corpus_chunks": len(corpus_all),
        "num_total_queries": len(queries_all),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "artifact_cache_enabled": True,
        "artifact_cache_dir": str(artifact_cache_dir),
        "bm25_ranking_cache_hit": artifact_info.get("cache_hit", False),
        "bm25_ranking_artifact_path": artifact_info.get("artifact_path", ""),
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
            top_k=top_k,
            ks=ks,
        ),
        **gt_coverage,
        **metrics_result,
    }

    rankings_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate BM25-only baselines from shared ranking artifacts")
    parser.add_argument("--dataset", required=True, help="Dataset name or comma-separated list")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifact-cache-dir", type=Path, default=DEFAULT_ARTIFACT_CACHE_DIR)
    parser.add_argument("--force-artifact-cache", action="store_true")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--depth", type=int, default=100, help="BM25 artifact ranking depth")
    parser.add_argument("--ks", default="1,5,10", help="Comma-separated metric cutoffs")
    parser.add_argument("--query-split", default=None)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--max-corpus", type=int, default=None)
    parser.add_argument(
        "--corpus-sampling",
        default="auto",
        choices=sorted(experiment_guardrails.CORPUS_SAMPLING_STRATEGIES),
    )
    parser.add_argument("--sampling-seed", type=int, default=13)
    args = parser.parse_args(argv)

    metrics_rows = []
    for dataset in parse_datasets(args.dataset):
        print(f"Evaluating BM25 artifact baseline: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            top_k=args.top_k,
            ks=parse_ks(args.ks),
            depth=args.depth,
            query_split=args.query_split,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
            artifact_cache_dir=args.artifact_cache_dir,
            force_artifact_cache=args.force_artifact_cache,
        )
        metrics_rows.append(metrics)
        metric_text = ", ".join(f"{key}={metrics[key]:.4f}" for key in sorted(metrics) if "@" in key)
        print(
            f"  chunks={metrics['num_corpus_chunks']} queries={metrics['num_queries']} "
            f"cache_hit={metrics['bm25_ranking_cache_hit']} elapsed={metrics['elapsed_sec']}s"
        )
        print(f"  {metric_text}")

    bm25_baseline.update_summary(args.output_dir / "bm25_baseline_summary.csv", metrics_rows)
    print(f"Summary: {args.output_dir / 'bm25_baseline_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
