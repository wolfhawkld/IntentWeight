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
EMBEDDING_FINGERPRINT_VERSION = "embedding_ndarray_sha256_v1"
FINGERPRINT_CHUNK_BYTES = 16 * 1024 * 1024


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


def embedding_array_fingerprint(array: np.ndarray) -> str:
    """Hash an embedding array's shape, dtype, and exact numeric content."""
    values = np.asarray(array)
    if values.ndim != 2:
        raise ValueError(f"embedding array must be two-dimensional, got shape={values.shape}")
    if values.dtype.hasobject:
        raise ValueError("object-dtype embedding arrays cannot be fingerprinted")

    header = {
        "fingerprint_version": EMBEDDING_FINGERPRINT_VERSION,
        "shape": list(values.shape),
        "dtype": values.dtype.str,
    }
    hasher = hashlib.sha256()
    hasher.update(json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    row_bytes = max(1, int(np.prod(values.shape[1:], dtype=np.int64)) * values.dtype.itemsize)
    chunk_rows = max(1, FINGERPRINT_CHUNK_BYTES // row_bytes)
    for row_start in range(0, len(values), chunk_rows):
        chunk = np.ascontiguousarray(values[row_start : row_start + chunk_rows])
        hasher.update(memoryview(chunk).cast("B"))
    return hasher.hexdigest()


def _write_json_atomic(path: Path, payload: Mapping) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _write_npy_atomic(path: Path, array: np.ndarray) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("wb") as handle:
        np.save(handle, array, allow_pickle=False)
    temporary_path.replace(path)


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
    model_revision: str | None,
) -> bool:
    valid = (
        metadata.get("dataset") == dataset
        and metadata.get("model_name") == model_name
        and metadata.get("record_kind") == record_kind
        and metadata.get("fingerprint") == fingerprint
        and int(metadata.get("record_count", -1)) == count
        and metadata.get("normalized") is True
    )
    if model_revision is not None:
        valid = valid and metadata.get("model_revision") == str(model_revision)
    return valid


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
    model_revision: str | None = None,
) -> tuple[np.ndarray, Dict[str, object]]:
    """Load cached embeddings for records, or compute and persist them.

    The record key includes dataset, model name, record kind, record ids, and
    record text. Supplying ``model_revision`` additionally prevents a cache
    generated by another model revision from being reused under the same model
    name.
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
            model_revision=model_revision,
        ):
            try:
                embeddings = np.load(embedding_path, mmap_mode="r", allow_pickle=False)
            except (EOFError, OSError, ValueError):
                embeddings = None
            expected_shape = metadata.get("embedding_shape")
            shape_valid = (
                embeddings is not None
                and embeddings.ndim == 2
                and embeddings.shape[0] == len(records)
                and (expected_shape is None or list(embeddings.shape) == list(expected_shape))
            )
            if shape_valid:
                content_fingerprint = embedding_array_fingerprint(embeddings)
                stored_fingerprint = metadata.get("embedding_content_fingerprint")
                fingerprint_valid = (
                    stored_fingerprint is None
                    or (
                        metadata.get("embedding_content_fingerprint_version")
                        == EMBEDDING_FINGERPRINT_VERSION
                        and stored_fingerprint == content_fingerprint
                    )
                )
                if fingerprint_valid:
                    if stored_fingerprint is None:
                        metadata = {
                            **metadata,
                            "embedding_content_fingerprint_version": EMBEDDING_FINGERPRINT_VERSION,
                            "embedding_content_fingerprint": content_fingerprint,
                        }
                        _write_json_atomic(metadata_path, metadata)
                    info = dict(metadata)
                    info.update({
                        "cache_hit": True,
                        "embedding_path": str(embedding_path),
                        "metadata_path": str(metadata_path),
                    })
                    return np.asarray(embeddings, dtype=np.float32), info

    texts = [str(record.get("text", "")) for record in records]
    start = time.perf_counter()
    embeddings = encode_texts(encoder, texts, batch_size=batch_size)
    elapsed_sec = time.perf_counter() - start

    cache_dir.mkdir(parents=True, exist_ok=True)
    _write_npy_atomic(embedding_path, embeddings)
    metadata = {
        "dataset": dataset,
        "model_name": model_name,
        "model_revision": str(model_revision) if model_revision is not None else "",
        "record_kind": record_kind,
        "record_count": len(records),
        "fingerprint": fingerprint,
        "embedding_shape": list(embeddings.shape),
        "dtype": str(embeddings.dtype),
        "normalized": True,
        "embedding_content_fingerprint_version": EMBEDDING_FINGERPRINT_VERSION,
        "embedding_content_fingerprint": embedding_array_fingerprint(embeddings),
        "batch_size": batch_size,
        "encode_elapsed_sec": round(elapsed_sec, 3),
        "embedding_path": str(embedding_path),
        "metadata_path": str(metadata_path),
        "cache_hit": False,
    }
    _write_json_atomic(metadata_path, metadata)
    return embeddings, metadata
