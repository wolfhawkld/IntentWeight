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
_GUARDRAILS_PATH = SCRIPT_DIR / "experiment_guardrails.py"
_guardrails_spec = importlib.util.spec_from_file_location("experiment_guardrails", _GUARDRAILS_PATH)
experiment_guardrails = importlib.util.module_from_spec(_guardrails_spec)
_guardrails_spec.loader.exec_module(experiment_guardrails)
_CACHE_PATH = SCRIPT_DIR / "embedding_cache.py"
_cache_spec = importlib.util.spec_from_file_location("embedding_cache", _CACHE_PATH)
embedding_cache = importlib.util.module_from_spec(_cache_spec)
_cache_spec.loader.exec_module(embedding_cache)
_ARTIFACTS_PATH = SCRIPT_DIR / "large_scale_artifacts.py"
_artifacts_spec = importlib.util.spec_from_file_location("large_scale_artifacts", _ARTIFACTS_PATH)
large_scale_artifacts = importlib.util.module_from_spec(_artifacts_spec)
_artifacts_spec.loader.exec_module(large_scale_artifacts)
_LOTTE_SCALE_STORE_PATH = SCRIPT_DIR / "lotte_scale_store.py"
_scale_store_spec = importlib.util.spec_from_file_location("lotte_scale_store", _LOTTE_SCALE_STORE_PATH)
lotte_scale_store = importlib.util.module_from_spec(_scale_store_spec)
_scale_store_spec.loader.exec_module(lotte_scale_store)

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_EMBEDDING_CACHE_DIR = SCRIPT_DIR.parent / "data" / "embeddings"
DEFAULT_ARTIFACT_CACHE_DIR = large_scale_artifacts.DEFAULT_ARTIFACT_CACHE_DIR
DEFAULT_SCALE_STORE_DIR = SCRIPT_DIR.parent / "data" / "scale_store" / "lotte_technology_search"
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


def records_with_text_prefix(records: Sequence[Mapping], prefix: str) -> List[Mapping]:
    """Return shallow record copies with a text prefix applied for encoding."""
    if not prefix:
        return list(records)
    prefixed = []
    for record in records:
        item = dict(record)
        item["text"] = f"{prefix}{record.get('text', '')}"
        prefixed.append(item)
    return prefixed


def encode_records_with_optional_cache(
    records: Sequence[Mapping],
    encoder,
    *,
    dataset: str,
    model_name: str,
    record_kind: str,
    batch_size: int,
    text_prefix: str = "",
    embedding_cache_dir: Path | None = None,
    use_embedding_cache: bool = False,
    force_embedding_cache: bool = False,
) -> tuple[np.ndarray, Dict[str, object]]:
    """Encode records, optionally using the shared on-disk embedding cache."""
    encoding_records = records_with_text_prefix(records, text_prefix)
    if use_embedding_cache:
        if embedding_cache_dir is None:
            raise ValueError("embedding_cache_dir is required when use_embedding_cache=True")
        return embedding_cache.load_or_compute_embeddings(
            encoding_records,
            dataset=dataset,
            model_name=model_name,
            record_kind=record_kind,
            encoder=encoder,
            batch_size=batch_size,
            cache_dir=embedding_cache_dir,
            force=force_embedding_cache,
        )
    embeddings = encode_texts(
        encoder,
        [str(record.get("text", "")) for record in encoding_records],
        batch_size=batch_size,
    )
    return embeddings, {
        "cache_hit": False,
        "cache_enabled": False,
        "record_count": len(encoding_records),
        "record_kind": record_kind,
    }


def load_corpus_embeddings_from_scale_store(
    corpus: Sequence[Mapping],
    *,
    canonical_name: str,
    scale_store_dir: Path,
) -> tuple[np.ndarray, Dict[str, object]]:
    """Load corpus embeddings from a canonical LoTTE scale store."""
    scale_store_dir = Path(scale_store_dir)
    ids_path = scale_store_dir / "canonical_corpus_ids.json"
    embeddings_path = scale_store_dir / "canonical_corpus_embeddings.npy"
    if not ids_path.exists() or not embeddings_path.exists():
        raise FileNotFoundError(f"Missing canonical scale store under {scale_store_dir}")
    with ids_path.open("r", encoding="utf-8") as f:
        ids_data = json.load(f)
    canonical_ids = [str(item) for item in ids_data.get("canonical_ids", [])]
    canonical_index = {cid: idx for idx, cid in enumerate(canonical_ids)}
    row_indices: List[int] = []
    missing_ids: List[str] = []
    for record in corpus:
        cid = lotte_scale_store.canonical_corpus_id(record, canonical_name=canonical_name)
        row_idx = canonical_index.get(cid)
        if row_idx is None:
            missing_ids.append(cid)
        else:
            row_indices.append(row_idx)
    if missing_ids:
        preview = ", ".join(missing_ids[:5])
        raise ValueError(
            f"Scale store is missing {len(missing_ids)} corpus rows; first missing: {preview}"
        )
    canonical_embeddings = np.load(embeddings_path, mmap_mode="r")
    if canonical_embeddings.shape[0] != len(canonical_ids):
        raise ValueError(
            f"Scale store row mismatch: {canonical_embeddings.shape[0]} embeddings "
            f"for {len(canonical_ids)} canonical ids"
        )
    selected = np.asarray(canonical_embeddings[np.asarray(row_indices, dtype=np.int64)], dtype=np.float32)
    return selected, {
        "enabled": True,
        "canonical_name": canonical_name,
        "scale_store_dir": str(scale_store_dir),
        "canonical_embedding_path": str(embeddings_path),
        "canonical_count": len(canonical_ids),
        "selected_rows": len(row_indices),
    }


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
    query_prefix: str = "",
    corpus_prefix: str = "",
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

    corpus_embeddings = encode_texts(
        encoder,
        [f"{corpus_prefix}{chunk.get('text', '')}" for chunk in corpus],
        batch_size=batch_size,
    )
    query_embeddings = encode_texts(
        encoder,
        [f"{query_prefix}{query.get('text', '')}" for query in queries],
        batch_size=batch_size,
    )

    return run_dense_with_embeddings(
        corpus,
        queries,
        corpus_embeddings,
        query_embeddings,
        top_k=top_k,
        ks=ks,
        batch_size=batch_size,
    )


def run_dense_with_embeddings(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    top_k: int = 10,
    ks: Sequence[int] = (1, 5, 10),
    batch_size: int = 64,
) -> Dict[str, object]:
    """Run exact cosine retrieval using precomputed normalized embeddings."""
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if not corpus:
        raise ValueError("corpus must not be empty")
    if len(corpus_embeddings) != len(corpus):
        raise ValueError(f"corpus_embeddings rows={len(corpus_embeddings)} but corpus rows={len(corpus)}")
    if len(query_embeddings) != len(queries):
        raise ValueError(f"query_embeddings rows={len(query_embeddings)} but query rows={len(queries)}")

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    rankings: Dict[str, List[str]] = {}
    effective_top_k = min(top_k, len(corpus))
    for start in range(0, len(queries), batch_size):
        batch_queries = queries[start : start + batch_size]
        scores_batch = query_embeddings[start : start + len(batch_queries)] @ corpus_embeddings.T
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
    query_prefix: str = "",
    corpus_prefix: str = "",
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

    artifact_dir = artifact_cache_dir or DEFAULT_ARTIFACT_CACHE_DIR
    dense_artifact_info: Dict[str, object] = {"cache_hit": False}
    scale_store_info: Dict[str, object] = {"enabled": False}

    start = time.perf_counter()
    if use_scale_store:
        if corpus_prefix:
            raise ValueError("--corpus-prefix is incompatible with --use-scale-store because corpus embeddings are precomputed")
        corpus_embeddings, scale_store_info = load_corpus_embeddings_from_scale_store(
            selected_corpus,
            canonical_name=scale_store_canonical_name,
            scale_store_dir=scale_store_dir or DEFAULT_SCALE_STORE_DIR,
        )
        corpus_cache = {
            "cache_hit": True,
            "cache_enabled": False,
            "embedding_path": scale_store_info.get("canonical_embedding_path", ""),
        }
        query_embeddings, query_cache = encode_records_with_optional_cache(
            selected_queries,
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
        if use_artifact_cache:
            artifact_depth = max(top_k, 100)
            rankings_by_qid, dense_artifact_info = large_scale_artifacts.load_or_compute_dense_rankings(
                selected_corpus,
                selected_queries,
                corpus_embeddings,
                query_embeddings,
                dataset=dataset,
                model_name=model_name,
                depth=artifact_depth,
                cache_dir=artifact_dir,
                batch_size=batch_size,
                force=force_artifact_cache,
            )
            truncated = {qid: ids[:top_k] for qid, ids in rankings_by_qid.items()}
            metrics_result = retrieval_metrics.evaluate_rankings(selected_queries, truncated, ks=ks)
            result = {"rankings": truncated, "metrics": metrics_result}
        else:
            result = run_dense_with_embeddings(
                selected_corpus,
                selected_queries,
                corpus_embeddings,
                query_embeddings,
                top_k=top_k,
                ks=ks,
                batch_size=batch_size,
            )
    elif use_embedding_cache:
        corpus_embeddings, corpus_cache = encode_records_with_optional_cache(
            selected_corpus,
            encoder,
            dataset=dataset,
            model_name=model_name,
            record_kind="corpus",
            batch_size=batch_size,
            text_prefix=corpus_prefix,
            embedding_cache_dir=embedding_cache_dir or DEFAULT_EMBEDDING_CACHE_DIR,
            use_embedding_cache=True,
            force_embedding_cache=force_embedding_cache,
        )
        query_embeddings, query_cache = encode_records_with_optional_cache(
            selected_queries,
            encoder,
            dataset=dataset,
            model_name=model_name,
            record_kind="queries",
            batch_size=batch_size,
            text_prefix=query_prefix,
            embedding_cache_dir=embedding_cache_dir or DEFAULT_EMBEDDING_CACHE_DIR,
            use_embedding_cache=True,
            force_embedding_cache=force_embedding_cache,
        )
        if use_artifact_cache:
            artifact_depth = max(top_k, 100)
            rankings_by_qid, dense_artifact_info = large_scale_artifacts.load_or_compute_dense_rankings(
                selected_corpus,
                selected_queries,
                corpus_embeddings,
                query_embeddings,
                dataset=dataset,
                model_name=model_name,
                depth=artifact_depth,
                cache_dir=artifact_dir,
                batch_size=batch_size,
                force=force_artifact_cache,
            )
            truncated = {qid: ids[:top_k] for qid, ids in rankings_by_qid.items()}
            metrics_result = retrieval_metrics.evaluate_rankings(selected_queries, truncated, ks=ks)
            result = {"rankings": truncated, "metrics": metrics_result}
        else:
            result = run_dense_with_embeddings(
                selected_corpus,
                selected_queries,
                corpus_embeddings,
                query_embeddings,
                top_k=top_k,
                ks=ks,
                batch_size=batch_size,
            )
    else:
        corpus_cache = {"cache_hit": False, "cache_enabled": False}
        query_cache = {"cache_hit": False, "cache_enabled": False}
        result = run_dense(
            selected_corpus,
            selected_queries,
            encoder,
            top_k=top_k,
            ks=ks,
            batch_size=batch_size,
            query_prefix=query_prefix,
            corpus_prefix=corpus_prefix,
        )
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"dense_{dataset}_rankings.json"
    metrics_path = output_dir / f"dense_{dataset}_metrics.json"

    metrics = {
        "dataset": dataset,
        "method": "dense",
        "model": model_name,
        "query_prefix": query_prefix,
        "corpus_prefix": corpus_prefix,
        "top_k": top_k,
        "ks": list(ks),
        "batch_size": batch_size,
        "num_corpus_chunks": len(selected_corpus),
        "num_total_corpus_chunks": len(corpus),
        "num_total_queries": len(queries),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "embedding_cache_enabled": bool(use_embedding_cache),
        "embedding_cache_dir": str(embedding_cache_dir or DEFAULT_EMBEDDING_CACHE_DIR) if use_embedding_cache else "",
        "corpus_embedding_cache_hit": corpus_cache.get("cache_hit", False),
        "query_embedding_cache_hit": query_cache.get("cache_hit", False),
        "corpus_embedding_cache_path": corpus_cache.get("embedding_path", ""),
        "query_embedding_cache_path": query_cache.get("embedding_path", ""),
        "artifact_cache_enabled": bool(use_artifact_cache),
        "artifact_cache_dir": str(artifact_dir) if use_artifact_cache else "",
        "dense_ranking_cache_hit": dense_artifact_info.get("cache_hit", False),
        "dense_ranking_artifact_path": dense_artifact_info.get("artifact_path", ""),
        "scale_store_enabled": bool(use_scale_store),
        "scale_store_dir": str(scale_store_dir or DEFAULT_SCALE_STORE_DIR) if use_scale_store else "",
        "scale_store_canonical_name": scale_store_canonical_name if use_scale_store else "",
        "scale_store_canonical_count": scale_store_info.get("canonical_count", 0),
        "scale_store_selected_rows": scale_store_info.get("selected_rows", 0),
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

    existing: Dict[tuple[str, str, str, str, str], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[
                    (
                        row.get("dataset", ""),
                        row.get("method", ""),
                        row.get("model", ""),
                        row.get("query_prefix", ""),
                        row.get("corpus_prefix", ""),
                    )
                ] = row

    for row in rows:
        existing[
            (
                str(row["dataset"]),
                str(row["method"]),
                str(row.get("model", "")),
                str(row.get("query_prefix", "")),
                str(row.get("corpus_prefix", "")),
            )
        ] = row

    metric_keys = sorted({key for row in existing.values() for key in row if "@" in key})
    fieldnames = [
        "dataset",
        "method",
        "model",
        "query_prefix",
        "corpus_prefix",
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
        "embedding_cache_enabled",
        "corpus_embedding_cache_hit",
        "query_embedding_cache_hit",
        "scale_store_enabled",
        "scale_store_selected_rows",
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
    parser.add_argument("--query-prefix", default="", help="Optional prefix applied only to query text before encoding")
    parser.add_argument("--corpus-prefix", default="", help="Optional prefix applied only to corpus text before encoding")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--embedding-cache-dir", type=Path, default=DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--no-embedding-cache", action="store_true", help="Disable reusable on-disk embeddings")
    parser.add_argument("--force-embedding-cache", action="store_true", help="Recompute embeddings even when cache files exist")
    parser.add_argument("--artifact-cache-dir", type=Path, default=DEFAULT_ARTIFACT_CACHE_DIR)
    parser.add_argument("--no-artifact-cache", action="store_true", help="Disable reusable dense ranking artifacts")
    parser.add_argument("--force-artifact-cache", action="store_true", help="Recompute ranking artifacts even when cache files exist")
    parser.add_argument("--scale-store-dir", type=Path, default=DEFAULT_SCALE_STORE_DIR)
    parser.add_argument("--use-scale-store", action="store_true", help="Load corpus embeddings from canonical LoTTE scale store")
    parser.add_argument("--scale-store-canonical-name", default="lotte_technology_search")
    parser.add_argument("--top-k", type=int, default=10)
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
            query_prefix=args.query_prefix,
            corpus_prefix=args.corpus_prefix,
        )
        metrics_rows.append(metrics)
        metric_text = ", ".join(f"{key}={metrics[key]:.4f}" for key in sorted(metrics) if "@" in key)
        print(
            f"  chunks={metrics['num_corpus_chunks']} queries={metrics['num_queries']} "
            f"skipped_no_gt={metrics['num_skipped_no_gt']} "
            f"gt_query_coverage={metrics['gt_query_coverage']:.4f} elapsed={metrics['elapsed_sec']}s"
        )
        print(f"  {metric_text}")

    update_summary(args.output_dir / "dense_baseline_summary.csv", metrics_rows)
    print(f"Summary: {args.output_dir / 'dense_baseline_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
