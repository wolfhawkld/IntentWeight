#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reusable embedding cache for large-scale retrieval experiments."""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, Mapping, Sequence

import numpy as np


ID_FIELDS = {
    "corpus": ("chunk_id", "id"),
    "queries": ("query_id", "id"),
}
SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def slug(value: object) -> str:
    raw = str(value or "").strip()
    cleaned = SLUG_RE.sub("-", raw).strip("-._")
    return cleaned or "unknown"


def normalize_embeddings(embeddings: Sequence[Sequence[float]]) -> np.ndarray:
    array = np.asarray(embeddings, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, norms, out=np.zeros_like(array), where=norms > 0)


def record_id(record: Mapping, record_kind: str) -> str:
    for field in ID_FIELDS.get(record_kind, ("id",)):
        value = record.get(field)
        if value is not None:
            return str(value)
    raise ValueError(f"{record_kind} record missing id field: {record}")


def records_fingerprint(records: Sequence[Mapping], record_kind: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(record_kind.encode("utf-8"))
    hasher.update(str(len(records)).encode("utf-8"))
    for record in records:
        rid = record_id(record, record_kind)
        text = str(record.get("text", ""))
        hasher.update(len(rid).to_bytes(8, "little"))
        hasher.update(rid.encode("utf-8"))
        hasher.update(len(text).to_bytes(8, "little"))
        hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def cache_paths(
    cache_dir: Path,
    *,
    dataset: str,
    model_name: str,
    record_kind: str,
    fingerprint: str,
    count: int,
) -> tuple[Path, Path]:
    prefix = "__".join([
        slug(dataset),
        slug(model_name),
        slug(record_kind),
        f"n{count}",
        fingerprint[:16],
    ])
    return cache_dir / f"{prefix}.npy", cache_dir / f"{prefix}.json"


def encode_texts(encoder, texts: Sequence[str], *, batch_size: int) -> np.ndarray:
    embeddings = encoder.encode(
        list(texts),
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=False,
        show_progress_bar=False,
    )
    return normalize_embeddings(embeddings)


def _valid_metadata(
    metadata: Mapping,
    *,
    dataset: str,
    model_name: str,
    record_kind: str,
    fingerprint: str,
    count: int,
) -> bool:
    return (
        metadata.get("dataset") == dataset
        and metadata.get("model_name") == model_name
        and metadata.get("record_kind") == record_kind
        and metadata.get("fingerprint") == fingerprint
        and int(metadata.get("record_count", -1)) == count
        and metadata.get("normalized") is True
    )


def load_or_compute_embeddings(
    records: Sequence[Mapping],
    *,
    dataset: str,
    model_name: str,
    record_kind: str,
    encoder,
    batch_size: int,
    cache_dir: Path,
    force: bool = False,
) -> tuple[np.ndarray, Dict[str, object]]:
    """Load cached embeddings for records, or compute and persist them.

    The cache key includes dataset, model name, record kind, record ids, and
    record text. Any data or model change naturally creates a new cache file.
    """
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if record_kind not in ID_FIELDS:
        raise ValueError(f"Unsupported record_kind={record_kind!r}; expected one of {sorted(ID_FIELDS)}")

    cache_dir = Path(cache_dir)
    fingerprint = records_fingerprint(records, record_kind)
    embedding_path, metadata_path = cache_paths(
        cache_dir,
        dataset=dataset,
        model_name=model_name,
        record_kind=record_kind,
        fingerprint=fingerprint,
        count=len(records),
    )

    if not force and embedding_path.exists() and metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
        if _valid_metadata(
            metadata,
            dataset=dataset,
            model_name=model_name,
            record_kind=record_kind,
            fingerprint=fingerprint,
            count=len(records),
        ):
            embeddings = np.load(embedding_path)
            if embeddings.shape[0] != len(records):
                raise ValueError(
                    f"Embedding cache row mismatch for {embedding_path}: "
                    f"{embeddings.shape[0]} rows for {len(records)} records"
                )
            info = dict(metadata)
            info.update({
                "cache_hit": True,
                "embedding_path": str(embedding_path),
                "metadata_path": str(metadata_path),
            })
            return embeddings.astype(np.float32, copy=False), info

    texts = [str(record.get("text", "")) for record in records]
    start = time.perf_counter()
    embeddings = encode_texts(encoder, texts, batch_size=batch_size)
    elapsed_sec = time.perf_counter() - start

    cache_dir.mkdir(parents=True, exist_ok=True)
    np.save(embedding_path, embeddings)
    metadata = {
        "dataset": dataset,
        "model_name": model_name,
        "record_kind": record_kind,
        "record_count": len(records),
        "fingerprint": fingerprint,
        "embedding_shape": list(embeddings.shape),
        "dtype": str(embeddings.dtype),
        "normalized": True,
        "batch_size": batch_size,
        "encode_elapsed_sec": round(elapsed_sec, 3),
        "embedding_path": str(embedding_path),
        "metadata_path": str(metadata_path),
        "cache_hit": False,
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2, sort_keys=True)
    return embeddings, metadata
