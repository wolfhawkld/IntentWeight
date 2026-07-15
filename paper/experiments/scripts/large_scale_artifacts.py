#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared retrieval artifacts for large-scale IntentRoute experiments."""
from __future__ import annotations

import hashlib
import heapq
import importlib.util
import json
import time
from collections import Counter, defaultdict
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
NDARRAY_FINGERPRINT_VERSION = "ndarray_sha256_v1"
ARTIFACT_CONTENT_FINGERPRINT_VERSION = "logical_content_sha256_v1"
FINGERPRINT_CHUNK_BYTES = 16 * 1024 * 1024


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


def _ndarray_content_fingerprint(array: np.ndarray, *, chunk_rows: int = 4096) -> str:
    if chunk_rows <= 0:
        raise ValueError(f"chunk_rows must be positive, got {chunk_rows}")
    values = np.asarray(array)
    if values.ndim <= 0:
        raise ValueError(f"array must have at least one dimension, got shape={values.shape}")
    if values.dtype.hasobject:
        raise ValueError("object-dtype arrays cannot be fingerprinted")

    header = {
        "fingerprint_version": NDARRAY_FINGERPRINT_VERSION,
        "shape": list(values.shape),
        "dtype": values.dtype.str,
    }
    hasher = hashlib.sha256()
    hasher.update(json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    row_width = int(np.prod(values.shape[1:], dtype=np.int64)) if values.ndim > 1 else 1
    row_bytes = max(1, row_width * values.dtype.itemsize)
    effective_chunk_rows = max(1, min(chunk_rows, FINGERPRINT_CHUNK_BYTES // row_bytes))
    for row_start in range(0, len(values), effective_chunk_rows):
        row_chunk = np.ascontiguousarray(values[row_start : row_start + effective_chunk_rows])
        hasher.update(memoryview(row_chunk).cast("B"))
    return hasher.hexdigest()


def embedding_array_fingerprint(array: np.ndarray, *, chunk_rows: int = 4096) -> str:
    """Hash an embedding array's identity and exact numeric content."""
    embeddings = np.asarray(array)
    if embeddings.ndim != 2:
        raise ValueError(f"embedding array must be two-dimensional, got shape={embeddings.shape}")
    return _ndarray_content_fingerprint(embeddings, chunk_rows=chunk_rows)


def rankings_content_fingerprint(rankings: Mapping[str, Sequence[str]]) -> str:
    normalized = {
        str(query_id): [str(chunk_id) for chunk_id in ranking]
        for query_id, ranking in rankings.items()
    }
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hasher = hashlib.sha256()
    hasher.update(ARTIFACT_CONTENT_FINGERPRINT_VERSION.encode("utf-8"))
    hasher.update(encoded)
    return hasher.hexdigest()


def arrays_content_fingerprint(arrays: Mapping[str, np.ndarray]) -> str:
    payload = {
        str(name): _ndarray_content_fingerprint(np.asarray(array))
        for name, array in sorted(arrays.items())
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hasher = hashlib.sha256()
    hasher.update(ARTIFACT_CONTENT_FINGERPRINT_VERSION.encode("utf-8"))
    hasher.update(encoded)
    return hasher.hexdigest()


def _artifact_payload(
    *,
    dataset: str,
    artifact_kind: str,
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    model_name: str,
    params: Mapping[str, object],
    corpus_embedding_fingerprint: str | None = None,
    query_embedding_fingerprint: str | None = None,
) -> Dict[str, object]:
    if (corpus_embedding_fingerprint is None) != (query_embedding_fingerprint is None):
        raise ValueError("corpus and query embedding fingerprints must be supplied together")
    payload: Dict[str, object] = {
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
    if corpus_embedding_fingerprint is not None:
        payload.update({
            "embedding_fingerprint_version": NDARRAY_FINGERPRINT_VERSION,
            "corpus_embedding_fingerprint": corpus_embedding_fingerprint,
            "query_embedding_fingerprint": query_embedding_fingerprint,
        })
    return payload


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
    return metadata.get("fingerprint") == fingerprint and all(
        metadata.get(key) == value for key, value in payload.items()
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


def _rankings_structurally_valid(
    rankings: Mapping[str, Sequence[str]],
    queries: Sequence[Mapping],
    *,
    depth: int,
    require_exact_depth: bool,
) -> bool:
    if set(rankings) != {_query_id(query) for query in queries}:
        return False
    for ranking in rankings.values():
        normalized = [str(chunk_id) for chunk_id in ranking]
        if len(normalized) > depth or (require_exact_depth and len(normalized) != depth):
            return False
        if len(set(normalized)) != len(normalized):
            return False
    return True


def _write_metadata(path: Path, metadata: Mapping[str, object]) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _verified_content_metadata(
    metadata: Mapping[str, object],
    *,
    content_fingerprint: str,
    metadata_path: Path,
    allow_missing_migration: bool = False,
) -> Dict[str, object] | None:
    stored = metadata.get("content_fingerprint")
    if stored is None and allow_missing_migration:
        migrated = {
            **metadata,
            "content_fingerprint_version": ARTIFACT_CONTENT_FINGERPRINT_VERSION,
            "content_fingerprint": content_fingerprint,
        }
        _write_metadata(metadata_path, migrated)
        return migrated
    if (
        metadata.get("content_fingerprint_version") != ARTIFACT_CONTENT_FINGERPRINT_VERSION
        or stored != content_fingerprint
    ):
        return None
    return dict(metadata)


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
    corpus_embedding_fingerprint: str | None = None,
    query_embedding_fingerprint: str | None = None,
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
    corpus_embedding_fingerprint = corpus_embedding_fingerprint or embedding_array_fingerprint(corpus_embeddings)
    query_embedding_fingerprint = query_embedding_fingerprint or embedding_array_fingerprint(query_embeddings)
    payload = _artifact_payload(
        dataset=dataset,
        artifact_kind="dense_rankings",
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params={"depth": effective_depth, "ranking_engine": "exact_cosine_numpy_lexsort_v1"},
        corpus_embedding_fingerprint=corpus_embedding_fingerprint,
        query_embedding_fingerprint=query_embedding_fingerprint,
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
            cached_rankings = _load_json_rankings(ranking_path)
            if _rankings_structurally_valid(
                cached_rankings,
                queries,
                depth=effective_depth,
                require_exact_depth=True,
            ):
                info = _verified_content_metadata(
                    metadata,
                    content_fingerprint=rankings_content_fingerprint(cached_rankings),
                    metadata_path=metadata_path,
                )
                if info is not None:
                    info["cache_hit"] = True
                    return cached_rankings, info

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
        "content_fingerprint_version": ARTIFACT_CONTENT_FINGERPRINT_VERSION,
        "content_fingerprint": rankings_content_fingerprint(rankings),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
    }
    _write_metadata(metadata_path, metadata)
    return rankings, metadata


def _compute_query_term_bounded_bm25_rankings(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    *,
    depth: int,
    dataset: str,
    progress_every: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> Dict[str, List[str]]:
    """Compute exact BM25 rankings for selected queries without a full index.

    The scorer only keeps statistics for terms that occur in the selected
    queries. This is equivalent to full-corpus BM25 for those queries because
    all other corpus terms contribute zero to their scores.
    """
    query_tokens_by_idx: List[set[str]] = [
        set(bm25_baseline.tokenize(str(query.get("text", "")))) for query in queries
    ]
    query_terms = set().union(*query_tokens_by_idx) if query_tokens_by_idx else set()
    term_to_query_indices: dict[str, list[int]] = defaultdict(list)
    for query_idx, query_terms_for_query in enumerate(query_tokens_by_idx):
        for term in query_terms_for_query:
            term_to_query_indices[term].append(query_idx)

    doc_lens: List[int] = []
    dfs: Counter[str] = Counter()
    for doc_idx, chunk in enumerate(corpus, start=1):
        tokens = bm25_baseline.tokenize(str(chunk.get("text", "")))
        doc_lens.append(len(tokens))
        if query_terms:
            dfs.update(set(tokens).intersection(query_terms))
        if doc_idx == 1 or doc_idx % 100000 == 0 or doc_idx == len(corpus):
            print(f"[{dataset}] BM25 term stats {doc_idx}/{len(corpus)}", flush=True)

    n_docs = len(doc_lens)
    avgdl = float(np.mean(np.asarray(doc_lens, dtype=np.float32))) if n_docs else 0.0
    idf = {
        term: float(np.log((n_docs - df + 0.5) / (df + 0.5) + 1.0))
        for term, df in dfs.items()
    }

    heaps: list[list[tuple[float, int]]] = [[] for _ in queries]
    print(f"[{dataset}] bounded BM25 scoring pass for {len(queries)} queries", flush=True)
    for doc_idx, chunk in enumerate(corpus):
        tokens = bm25_baseline.tokenize(str(chunk.get("text", "")))
        counts = Counter(token for token in tokens if token in query_terms)
        if counts and avgdl > 0.0:
            doc_scores: dict[int, float] = {}
            doc_len = float(doc_lens[doc_idx])
            for term, freq in counts.items():
                term_idf = idf.get(term)
                if term_idf is None:
                    continue
                denom = freq + k1 * (1.0 - b + b * doc_len / avgdl)
                contribution = term_idf * (freq * (k1 + 1.0) / denom)
                for query_idx in term_to_query_indices.get(term, []):
                    doc_scores[query_idx] = doc_scores.get(query_idx, 0.0) + contribution

            for query_idx, score in doc_scores.items():
                heap_entry = (float(score), -doc_idx)
                heap = heaps[query_idx]
                if len(heap) < depth:
                    heapq.heappush(heap, heap_entry)
                elif heap_entry > heap[0]:
                    heapq.heapreplace(heap, heap_entry)

        scanned = doc_idx + 1
        if scanned == 1 or scanned % 100000 == 0 or scanned == len(corpus):
            print(f"[{dataset}] BM25 scoring {scanned}/{len(corpus)}", flush=True)

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    rankings: Dict[str, List[str]] = {}
    for query_idx, query in enumerate(queries, start=1):
        ordered = sorted(heaps[query_idx - 1], key=lambda item: (-item[0], -item[1]))
        rankings[_query_id(query)] = [chunk_ids[-neg_doc_idx] for _, neg_doc_idx in ordered]
        if query_idx == 1 or query_idx % progress_every == 0 or query_idx == len(queries):
            print(f"[{dataset}] BM25 rankings materialized {query_idx}/{len(queries)}", flush=True)
    return rankings


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
        params={"depth": effective_depth, "ranking_engine": "query_term_bounded_bm25_v1"},
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
            cached_rankings = _load_json_rankings(ranking_path)
            if _rankings_structurally_valid(
                cached_rankings,
                queries,
                depth=effective_depth,
                require_exact_depth=False,
            ):
                info = _verified_content_metadata(
                    metadata,
                    content_fingerprint=rankings_content_fingerprint(cached_rankings),
                    metadata_path=metadata_path,
                    allow_missing_migration=True,
                )
                if info is not None:
                    info["cache_hit"] = True
                    return cached_rankings, info

    if progress_every <= 0:
        raise ValueError(f"progress_every must be positive, got {progress_every}")

    start = time.perf_counter()
    print(
        f"[{dataset}] bounded BM25 term-stat pass for {len(corpus)} chunks",
        flush=True,
    )
    rankings = _compute_query_term_bounded_bm25_rankings(
        corpus,
        queries,
        depth=effective_depth,
        dataset=dataset,
        progress_every=progress_every,
    )
    elapsed_sec = time.perf_counter() - start

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    ranking_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
    metadata = {
        **_base_metadata(payload, fingerprint, ranking_path, metadata_path),
        "content_fingerprint_version": ARTIFACT_CONTENT_FINGERPRINT_VERSION,
        "content_fingerprint": rankings_content_fingerprint(rankings),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
    }
    _write_metadata(metadata_path, metadata)
    return rankings, metadata


def load_or_compute_query_corpus_scores(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    dataset: str,
    model_name: str,
    cache_dir: Path = DEFAULT_ARTIFACT_CACHE_DIR,
    force: bool = False,
    progress_every: int = 50,
    corpus_embedding_fingerprint: str | None = None,
    query_embedding_fingerprint: str | None = None,
) -> tuple[np.ndarray, Dict[str, object]]:
    """Load or compute exact static query-to-corpus dot-product scores.

    Cluster-local retrieval changes only the selected arms, not the underlying
    query/corpus scores. Persisting these scores removes repeated CPU matrix
    products while preserving the legacy candidate union, top-k, and tie-break
    operations at route time.
    """
    if len(corpus_embeddings) != len(corpus):
        raise ValueError(f"corpus embedding rows={len(corpus_embeddings)} but corpus rows={len(corpus)}")
    if len(query_embeddings) != len(queries):
        raise ValueError(f"query embedding rows={len(query_embeddings)} but query rows={len(queries)}")
    if corpus_embeddings.ndim != 2 or query_embeddings.ndim != 2:
        raise ValueError("corpus_embeddings and query_embeddings must be two-dimensional")
    if corpus_embeddings.shape[1] != query_embeddings.shape[1]:
        raise ValueError(
            f"embedding dimension mismatch: corpus={corpus_embeddings.shape[1]} "
            f"queries={query_embeddings.shape[1]}"
        )

    corpus_embedding_fingerprint = corpus_embedding_fingerprint or embedding_array_fingerprint(corpus_embeddings)
    query_embedding_fingerprint = query_embedding_fingerprint or embedding_array_fingerprint(query_embeddings)
    payload = _artifact_payload(
        dataset=dataset,
        artifact_kind="query_corpus_scores",
        corpus=corpus,
        queries=queries,
        model_name=model_name,
        params={"score_engine": "exact_numpy_rowwise_matvec_v1", "dtype": "float32"},
        corpus_embedding_fingerprint=corpus_embedding_fingerprint,
        query_embedding_fingerprint=query_embedding_fingerprint,
    )
    fingerprint = _payload_fingerprint(payload)
    scores_path, metadata_path = _artifact_paths(
        Path(cache_dir),
        dataset=dataset,
        artifact_kind="query_corpus_scores",
        fingerprint=fingerprint,
        extension="npy",
    )
    expected_shape = (len(queries), len(corpus))
    if not force and scores_path.exists() and metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        if _valid_metadata(metadata, payload, fingerprint):
            scores = np.load(scores_path, mmap_mode="r")
            if scores.shape == expected_shape and scores.dtype == np.float32:
                info = _verified_content_metadata(
                    metadata,
                    content_fingerprint=embedding_array_fingerprint(scores),
                    metadata_path=metadata_path,
                )
                if info is not None:
                    info["cache_hit"] = True
                    return scores, info
            del scores

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = scores_path.with_suffix(scores_path.suffix + ".tmp")
    start = time.perf_counter()
    scores = np.lib.format.open_memmap(
        temporary_path,
        mode="w+",
        dtype=np.float32,
        shape=expected_shape,
    )
    for query_idx, query_embedding in enumerate(query_embeddings):
        # Match the legacy retrieval orientation: corpus rows multiplied by one query.
        scores[query_idx] = corpus_embeddings @ query_embedding
        completed = query_idx + 1
        if completed == 1 or completed % progress_every == 0 or completed == len(queries):
            print(f"[{dataset}] query-corpus scores {completed}/{len(queries)}", flush=True)
    scores.flush()
    del scores
    temporary_path.replace(scores_path)
    elapsed_sec = time.perf_counter() - start
    persisted_scores = np.load(scores_path, mmap_mode="r")
    metadata = {
        **_base_metadata(payload, fingerprint, scores_path, metadata_path),
        "content_fingerprint_version": ARTIFACT_CONTENT_FINGERPRINT_VERSION,
        "content_fingerprint": embedding_array_fingerprint(persisted_scores),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
        "score_shape": list(expected_shape),
        "dtype": "float32",
    }
    _write_metadata(metadata_path, metadata)
    return persisted_scores, metadata


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
    corpus_embedding_fingerprint: str | None = None,
    query_embedding_fingerprint: str | None = None,
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

    corpus_embedding_fingerprint = corpus_embedding_fingerprint or embedding_array_fingerprint(corpus_embeddings)
    query_embedding_fingerprint = query_embedding_fingerprint or embedding_array_fingerprint(query_embeddings)
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
        corpus_embedding_fingerprint=corpus_embedding_fingerprint,
        query_embedding_fingerprint=query_embedding_fingerprint,
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
            arrays_valid = (
                arrays["corpus_context"].ndim == 2
                and arrays["query_context"].ndim == 2
                and arrays["arm_labels"].shape == (len(corpus),)
                and arrays["centroids"].ndim == 2
                and len(arrays["corpus_context"]) == len(corpus)
                and len(arrays["query_context"]) == len(queries)
                and arrays["corpus_context"].shape[1] == arrays["query_context"].shape[1]
                and arrays["corpus_context"].shape[1] == arrays["centroids"].shape[1]
            )
            if arrays_valid:
                info = _verified_content_metadata(
                    metadata,
                    content_fingerprint=arrays_content_fingerprint(arrays),
                    metadata_path=metadata_path,
                )
                if info is not None:
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
        "content_fingerprint_version": ARTIFACT_CONTENT_FINGERPRINT_VERSION,
        "content_fingerprint": arrays_content_fingerprint({
            "corpus_context": corpus_context,
            "query_context": query_context,
            "arm_labels": arm_labels.astype(np.int32, copy=False),
            "centroids": centroids.astype(np.float32, copy=False),
        }),
        "cache_hit": False,
        "compute_elapsed_sec": round(elapsed_sec, 3),
        "corpus_context_shape": list(corpus_context.shape),
        "query_context_shape": list(query_context.shape),
        "n_effective_arms": n_effective_arms,
    }
    _write_metadata(metadata_path, metadata)
    return {
        "corpus_context": corpus_context,
        "query_context": query_context,
        "arm_labels": arm_labels.astype(np.int32, copy=False),
        "centroids": centroids.astype(np.float32, copy=False),
    }, metadata
