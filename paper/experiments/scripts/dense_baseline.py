#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dense embedding retrieval baseline for processed IntentWeight datasets."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
_METRICS_PATH = SCRIPT_DIR / "retrieval_metrics.py"
_spec = importlib.util.spec_from_file_location("retrieval_metrics", _METRICS_PATH)
retrieval_metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(retrieval_metrics)

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DATASETS = ("pubmedqa", "banking77", "emanual", "cuad")
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


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


def _chunk_id(chunk: Mapping) -> str:
    chunk_id = chunk.get("chunk_id") or chunk.get("id")
    if chunk_id is None:
        raise ValueError(f"Corpus chunk missing chunk_id/id: {chunk}")
    return str(chunk_id)


def _query_id(query: Mapping) -> str:
    query_id = query.get("query_id") or query.get("id")
    if query_id is None:
        raise ValueError(f"Query missing query_id/id: {query}")
    return str(query_id)


def normalize_embeddings(embeddings: Sequence[Sequence[float]]) -> np.ndarray:
    """L2-normalize embeddings row-wise while preserving all-zero rows."""
    array = np.asarray(embeddings, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, norms, out=np.zeros_like(array), where=norms > 0)


def top_k_indices(scores: Sequence[float], k: int) -> List[int]:
    """Return top-k score indices, sorted by score desc and index asc for ties."""
    if k <= 0:
        return []
    scores_array = np.asarray(scores)
    if scores_array.size == 0:
        return []
    k = min(k, scores_array.size)
    if k == scores_array.size:
        candidates = np.arange(scores_array.size)
    else:
        candidates = np.argpartition(-scores_array, k - 1)[:k]
    return sorted((int(idx) for idx in candidates), key=lambda idx: (-float(scores_array[idx]), idx))


def encode_texts(encoder, texts: Sequence[str], *, batch_size: int) -> np.ndarray:
    """Encode texts with a SentenceTransformer-like object and normalize output."""
    embeddings = encoder.encode(
        list(texts),
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=False,
        show_progress_bar=False,
    )
    return normalize_embeddings(embeddings)


def _slice_positive(value: int | None, name: str):
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def run_dense(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    encoder,
    *,
    top_k: int = 10,
    ks: Sequence[int] = (1, 5, 10),
    batch_size: int = 64,
    max_queries: int | None = None,
    max_corpus: int | None = None,
) -> Dict[str, object]:
    """Run exact cosine-similarity dense retrieval and evaluate rankings."""
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
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

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    corpus_texts = [str(chunk.get("text", "")) for chunk in corpus]
    corpus_embeddings = encode_texts(encoder, corpus_texts, batch_size=batch_size)

    rankings: Dict[str, List[str]] = {}
    effective_top_k = min(top_k, len(corpus))
    for start in range(0, len(queries), batch_size):
        batch_queries = queries[start : start + batch_size]
        query_texts = [str(query.get("text", "")) for query in batch_queries]
        query_embeddings = encode_texts(encoder, query_texts, batch_size=batch_size)
        scores_batch = query_embeddings @ corpus_embeddings.T
        for query, scores in zip(batch_queries, scores_batch):
            qid = _query_id(query)
            top_indices = top_k_indices(scores, effective_top_k)
            rankings[qid] = [chunk_ids[idx] for idx in top_indices]

    metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    return {"rankings": rankings, "metrics": metrics}


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
    max_queries: int | None = None,
    max_corpus: int | None = None,
) -> Dict[str, object]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    corpus = load_json_list(corpus_path)
    queries = load_json_list(queries_path)

    start = time.perf_counter()
    result = run_dense(
        corpus,
        queries,
        encoder,
        top_k=top_k,
        ks=ks,
        batch_size=batch_size,
        max_queries=max_queries,
        max_corpus=max_corpus,
    )
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"dense_{dataset}_rankings.json"
    metrics_path = output_dir / f"dense_{dataset}_metrics.json"

    metrics = {
        "dataset": dataset,
        "method": "dense",
        "model": model_name,
        "top_k": top_k,
        "ks": list(ks),
        "batch_size": batch_size,
        "num_corpus_chunks": len(corpus[:max_corpus] if max_corpus is not None else corpus),
        "num_total_corpus_chunks": len(corpus),
        "num_total_queries": len(queries),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "elapsed_sec": round(elapsed_sec, 3),
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
        "max_queries",
        "max_corpus",
        "top_k",
        *metric_keys,
        "elapsed_sec",
    ]

    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow(existing[key])


def load_sentence_transformer(model_name: str, *, device: str | None = None, local_files_only: bool = False):
    from sentence_transformers import SentenceTransformer

    kwargs = {}
    if device:
        kwargs["device"] = device
    if local_files_only:
        kwargs["local_files_only"] = True
    return SentenceTransformer(model_name, **kwargs)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run dense embedding retrieval baseline")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None, help="SentenceTransformer device, e.g. cpu/cuda")
    parser.add_argument("--local-files-only", action="store_true", help="Load model from local HF cache only")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10", help="Comma-separated metric cutoffs")
    parser.add_argument("--max-queries", type=int, default=None, help="Evaluate only the first N queries")
    parser.add_argument("--max-corpus", type=int, default=None, help="Use only the first N corpus chunks")
    args = parser.parse_args(argv)

    datasets = parse_datasets(args.dataset)
    ks = parse_ks(args.ks)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    metrics_rows = []
    for dataset in datasets:
        print(f"Running dense baseline: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            top_k=args.top_k,
            ks=ks,
            batch_size=args.batch_size,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
        )
        metrics_rows.append(metrics)
        metric_text = ", ".join(f"{key}={metrics[key]:.4f}" for key in sorted(metrics) if "@" in key)
        print(
            f"  chunks={metrics['num_corpus_chunks']} queries={metrics['num_queries']} "
            f"skipped_no_gt={metrics['num_skipped_no_gt']} elapsed={metrics['elapsed_sec']}s"
        )
        print(f"  {metric_text}")

    update_summary(args.output_dir / "dense_baseline_summary.csv", metrics_rows)
    print(f"Summary: {args.output_dir / 'dense_baseline_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
