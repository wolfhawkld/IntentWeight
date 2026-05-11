#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared retrieval artifacts for large-scale IntentWeight experiments."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


embedding_cache = _load_script_module("embedding_cache", SCRIPT_DIR / "embedding_cache.py")
bm25_baseline = _load_script_module("bm25_baseline", SCRIPT_DIR / "bm25_baseline.py")

DEFAULT_ARTIFACT_CACHE_DIR = SCRIPT_DIR.parent / "data" / "retrieval_artifacts"
ARTIFACT_VERSION = "large_scale_artifacts_v1"


def _record_id(record: Mapping, record_kind: str) -> str:
    return embedding_cache.record_id(record, record_kind)


def _query_id(query: Mapping) -> str:
    return _record_id(query, "queries")


def _chunk_id(chunk: Mapping) -> str:
    return _record_id(chunk, "corpus")


def _stable_top_k_indices(scores: Sequence[float], k: int) -> List[int]:
    if k <= 0:
        return []
    scores_array = np.asarray(scores)
    if scores_array.size == 0:
        return []
    k = min(k, scores_array.size)
    indices = np.arange(scores_array.size)
    ordered = np.lexsort((indices, -scores_array))
    return ordered[:k].astype(int).tolist()


def _safe_context_dim(requested: int, n_samples: int, embedding_dim: int) -> int:
    if requested <= 0:
        raise ValueError(f"context_dim must be positive, got {requested}")
    return max(1, min(requested, n_samples, embedding_dim))


def _l2_normalize(array: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, norms, out=np.zeros_like(array), where=norms > 0)


def _fit_context_projection(corpus_embeddings: np.ndarray, query_embeddings: np.ndarray, context_dim: int):
    effective_dim = _safe_context_dim(context_dim, len(corpus_embeddings), corpus_embeddings.shape[1])
    if effective_dim == corpus_embeddings.shape[1]:
        return None, corpus_embeddings.astype(np.float32), query_embeddings.astype(np.float32)
    pca = PCA(n_components=effective_dim, random_state=0)
    corpus_context = pca.fit_transform(corpus_embeddings).astype(np.float32)
    query_context = pca.transform(query_embeddings).astype(np.float32)
    return pca, corpus_context, query_context


def _cluster_corpus(corpus_context: np.ndarray, *, n_clusters: int, seed: int) -> np.ndarray:
    if n_clusters <= 0:
        raise ValueError(f"n_clusters must be positive, got {n_clusters}")
    effective_clusters = min(n_clusters, len(corpus_context))
    if effective_clusters == 1:
        return np.zeros(len(corpus_context), dtype=np.int32)
    clusterer = MiniBatchKMeans(
        n_clusters=effective_clusters,
        random_state=seed,
        n_init=10,
        batch_size=min(2048, max(128, len(corpus_context))),
    )
    return clusterer.fit_predict(corpus_context).astype(np.int32)


def _arm_centroids(corpus_context: np.ndarray, arm_labels: np.ndarray, n_arms: int) -> np.ndarray:
    centroids = np.zeros((n_arms, corpus_context.shape[1]), dtype=np.float32)
    for arm in range(n_arms):
        member_indices = np.flatnonzero(arm_labels == arm)
        if member_indices.size:
            centroids[arm] = np.mean(corpus_context[member_indices], axis=0)
    return _l2_normalize(centroids)


def _payload_fingerprint(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _artifact_payload(
    *,
    dataset: str,
    artifact_kind: str,
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    model_name: str,
    params: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "artifact_version": ARTIFACT_VERSION,
        "dataset": dataset,
        "artifact_kind": artifact_kind,
        "model_name": model_name,
        "corpus_count": len(corpus),
        "query_count": len(queries),
        "corpus_fingerprint": embedding_cache.records_fingerprint(corpus, "corpus"),
        "query_fingerprint": embedding_cache.records_fingerprint(queries, "queries"),
        "params": dict(params),
    }


def _artifact_paths(
    cache_dir: Path,
    *,
    dataset: str,
    artifact_kind: str,
    fingerprint: str,
    extension: str,
) -> tuple[Path, Path]:
    prefix = "__".join([
        embedding_cache.slug(dataset),
        embedding_cache.slug(artifact_kind),
        fingerprint[:16],
    ])
    return cache_dir / f"{prefix}.{extension}", cache_dir / f"{prefix}.meta.json"


def _valid_metadata(metadata: Mapping, payload: Mapping[str, object], fingerprint: str) -> bool:
    return (
        metadata.get("artifact_version") == ARTIFACT_VERSION
        and metadata.get("fingerprint") == fingerprint
        and metadata.get("dataset") == payload["dataset"]
        and metadata.get("artifact_kind") == payload["artifact_kind"]
        and metadata.get("model_name") == payload["model_name"]
        and metadata.get("corpus_count") == payload["corpus_count"]
        and metadata.get("query_count") == payload["query_count"]
        and metadata.get("corpus_fingerprint") == payload["corpus_fingerprint"]
        and metadata.get("query_fingerprint") == payload["query_fingerprint"]
        and metadata.get("params") == payload["params"]
    )


def _base_metadata(payload: Mapping[str, object], fingerprint: str, artifact_path: Path, metadata_path: Path) -> Dict[str, object]:
    return {
        **payload,
        "fingerprint": fingerprint,
        "artifact_path": str(artifact_path),
        "metadata_path": str(metadata_path),
    }


def _load_json_rankings(path: Path) -> Dict[str, List[str]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected ranking object in {path}")
    return {str(qid): [str(chunk_id) for chunk_id in ranking] for qid, ranking in data.items()}


def load_or_compute_dense_rankings(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    dataset: str,
    model_name: str,
    depth: int,
    cache_dir: Path = DEFAULT_ARTIFACT_CACHE_DIR,
    batch_size: int = 64,
    force: bool = False,
) -> tuple[Dict[str, List[str]], Dict[str, object]]:
    """Load or compute exact dense top-depth rankings for all selected queries."""
    if depth <= 0:
        raise ValueError(f"depth must be positive, got {depth}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if len(corpus_embeddings) != len(corpus):
        raise ValueError(f"corpus embedding rows={len(corpus_embeddings)} but corpus rows={len(corpus)}")
    if len(query_embeddings) != len(queries):
        raise ValueError(f"query embedding rows={len(query_embeddings)} but query rows={len(queries)}")

    effective_depth = min(depth, len(corpus))
    payload = _artifact_payload(
        dataset=dataset,
        artifact_kind="dense_rankings",
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params={"depth": effective_depth, "ranking_engine": "exact_cosine_numpy_lexsort_v1"},
    )
    fingerprint = _payload_fingerprint(payload)
    ranking_path, metadata_path = _artifact_paths(
        Path(cache_dir),
        dataset=dataset,
        artifact_kind="dense_rankings",
        fingerprint=fingerprint,
        extension="json",
    )
    if not force and ranking_path.exists() and metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        if _valid_metadata(metadata, payload, fingerprint):
            info = dict(metadata)
            info["cache_hit"] = True
            return _load_json_rankings(ranking_path), info

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    rankings: Dict[str, List[str]] = {}
    start = time.perf_counter()
    for batch_start in range(0, len(queries), batch_size):
        batch_queries = queries[batch_start : batch_start + batch_size]
        scores_batch = query_embeddings[batch_start : batch_start + len(batch_queries)] @ corpus_embeddings.T
        for query, scores in zip(batch_queries, scores_batch):
            top_indices = _stable_top_k_indices(scores, effective_depth)
            rankings[_query_id(query)] = [chunk_ids[idx] for idx in top_indices]
    elapsed_sec = time.perf_counter() - start

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    ranking_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
    metadata = {
        **_base_metadata(payload, fingerprint, ranking_path, metadata_path),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rankings, metadata


def load_or_compute_bm25_rankings(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    *,
    dataset: str,
    depth: int,
    cache_dir: Path = DEFAULT_ARTIFACT_CACHE_DIR,
    force: bool = False,
    progress_every: int = 50,
) -> tuple[Dict[str, List[str]], Dict[str, object]]:
    """Load or compute sparse BM25 top-depth rankings for all selected queries."""
    if depth <= 0:
        raise ValueError(f"depth must be positive, got {depth}")

    effective_depth = min(depth, len(corpus))
    payload = _artifact_payload(
        dataset=dataset,
        artifact_kind="bm25_rankings",
        corpus=corpus,
        queries=queries,
        model_name="sparse-bm25",
        params={"depth": effective_depth, "ranking_engine": "sparse_bm25_v1"},
    )
    fingerprint = _payload_fingerprint(payload)
    ranking_path, metadata_path = _artifact_paths(
        Path(cache_dir),
        dataset=dataset,
        artifact_kind="bm25_rankings",
        fingerprint=fingerprint,
        extension="json",
    )
    if not force and ranking_path.exists() and metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        if _valid_metadata(metadata, payload, fingerprint):
            info = dict(metadata)
            info["cache_hit"] = True
            return _load_json_rankings(ranking_path), info

    if progress_every <= 0:
        raise ValueError(f"progress_every must be positive, got {progress_every}")

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    print(
        f"[{dataset}] building BM25 tokenized corpus for {len(corpus)} chunks",
        flush=True,
    )
    tokenized_corpus = [bm25_baseline.tokenize(str(chunk.get("text", ""))) for chunk in corpus]
    start = time.perf_counter()
    print(f"[{dataset}] fitting BM25 index", flush=True)
    bm25 = bm25_baseline.SparseBM25(tokenized_corpus)
    rankings: Dict[str, List[str]] = {}
    for query_idx, query in enumerate(queries, start=1):
        if query_idx == 1 or query_idx % progress_every == 0 or query_idx == len(queries):
            print(
                f"[{dataset}] computing BM25 rankings {query_idx}/{len(queries)}",
                flush=True,
            )
        scores = bm25.get_scores(bm25_baseline.tokenize(str(query.get("text", ""))))
        top_indices = bm25_baseline.top_k_sparse_indices(scores, effective_depth)
        rankings[_query_id(query)] = [chunk_ids[idx] for idx in top_indices]
    elapsed_sec = time.perf_counter() - start

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    ranking_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
    metadata = {
        **_base_metadata(payload, fingerprint, ranking_path, metadata_path),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rankings, metadata


def load_or_compute_context_clusters(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    dataset: str,
    model_name: str,
    context_dim: int,
    n_clusters: int,
    seed: int,
    cache_dir: Path = DEFAULT_ARTIFACT_CACHE_DIR,
    force: bool = False,
) -> tuple[Dict[str, np.ndarray], Dict[str, object]]:
    """Load or compute PCA context vectors plus KMeans cluster labels."""
    if context_dim <= 0:
        raise ValueError(f"context_dim must be positive, got {context_dim}")
    if n_clusters <= 0:
        raise ValueError(f"n_clusters must be positive, got {n_clusters}")
    if len(corpus_embeddings) != len(corpus):
        raise ValueError(f"corpus embedding rows={len(corpus_embeddings)} but corpus rows={len(corpus)}")
    if len(query_embeddings) != len(queries):
        raise ValueError(f"query embedding rows={len(query_embeddings)} but query rows={len(queries)}")

    payload = _artifact_payload(
        dataset=dataset,
        artifact_kind="context_clusters",
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params={
            "context_dim": int(context_dim),
            "n_clusters": int(n_clusters),
            "seed": int(seed),
            "projection_engine": "pca_corpus_fit_v1",
            "cluster_engine": "minibatch_kmeans_v1",
        },
    )
    fingerprint = _payload_fingerprint(payload)
    arrays_path, metadata_path = _artifact_paths(
        Path(cache_dir),
        dataset=dataset,
        artifact_kind="context_clusters",
        fingerprint=fingerprint,
        extension="npz",
    )
    if not force and arrays_path.exists() and metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        if _valid_metadata(metadata, payload, fingerprint):
            with np.load(arrays_path) as data:
                arrays = {
                    "corpus_context": data["corpus_context"].astype(np.float32, copy=False),
                    "query_context": data["query_context"].astype(np.float32, copy=False),
                    "arm_labels": data["arm_labels"].astype(np.int32, copy=False),
                    "centroids": data["centroids"].astype(np.float32, copy=False),
                }
            info = dict(metadata)
            info["cache_hit"] = True
            return arrays, info

    start = time.perf_counter()
    _, corpus_context, query_context = _fit_context_projection(
        corpus_embeddings,
        query_embeddings,
        context_dim,
    )
    corpus_context = _l2_normalize(corpus_context).astype(np.float32, copy=False)
    query_context = _l2_normalize(query_context).astype(np.float32, copy=False)
    arm_labels = _cluster_corpus(corpus_context, n_clusters=n_clusters, seed=seed)
    n_effective_arms = int(np.max(arm_labels)) + 1 if len(arm_labels) else 0
    centroids = _arm_centroids(corpus_context, arm_labels, n_effective_arms)
    elapsed_sec = time.perf_counter() - start

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez(
        arrays_path,
        corpus_context=corpus_context,
        query_context=query_context,
        arm_labels=arm_labels.astype(np.int32, copy=False),
        centroids=centroids.astype(np.float32, copy=False),
    )
    metadata = {
        **_base_metadata(payload, fingerprint, arrays_path, metadata_path),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
        "corpus_context_shape": list(corpus_context.shape),
        "query_context_shape": list(query_context.shape),
        "n_effective_arms": n_effective_arms,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "corpus_context": corpus_context,
        "query_context": query_context,
        "arm_labels": arm_labels.astype(np.int32, copy=False),
        "centroids": centroids.astype(np.float32, copy=False),
    }, metadata
