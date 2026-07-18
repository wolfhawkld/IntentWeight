#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build canonical LoTTE scale manifests over reusable embedding caches.

The large-scale LoTTE checkpoints are nested slices of the same corpus. This
script turns per-dataset embedding caches such as 100k and 200k into one
canonical, original-corpus-id keyed store plus per-scale row-index manifests.
Future larger slices can append only missing corpus rows instead of recomputing
embeddings already present in smaller checkpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_EMBEDDING_CACHE_DIR = SCRIPT_DIR.parent / "data" / "embeddings"
DEFAULT_STORE_DIR = SCRIPT_DIR.parent / "data" / "scale_store" / "lotte_technology_search"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_CACHE_PATH = SCRIPT_DIR / "embedding_cache.py"
_cache_spec = importlib.util.spec_from_file_location("embedding_cache", _CACHE_PATH)
embedding_cache = importlib.util.module_from_spec(_cache_spec)
_cache_spec.loader.exec_module(embedding_cache)


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def corpus_path(data_dir: Path, dataset: str) -> Path:
    return data_dir / f"{dataset}_corpus.json"


def queries_path(data_dir: Path, dataset: str) -> Path:
    return data_dir / f"{dataset}_queries.json"


def canonical_corpus_id(record: Mapping, *, canonical_name: str) -> str:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), Mapping) else {}
    original_id = metadata.get("original_corpus_id")
    if original_id is not None and str(original_id) != "":
        return f"{canonical_name}_orig_{original_id}"
    return str(embedding_cache.record_id(record, "corpus"))


def text_fingerprint(text: object) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def dataset_gt_ref_count(queries: Sequence[Mapping]) -> int:
    total = 0
    for query in queries:
        refs = query.get("ground_truth_chunk_ids")
        if refs is None:
            continue
        if isinstance(refs, list):
            total += len(refs)
        else:
            total += 1
    return total


def load_cached_corpus_embeddings(
    dataset: str,
    corpus: Sequence[Mapping],
    *,
    model_name: str,
    cache_dir: Path,
    model_revision: str | None = None,
) -> tuple[np.ndarray, Mapping]:
    fingerprint = embedding_cache.records_fingerprint(corpus, "corpus")
    embedding_path, metadata_path = embedding_cache.cache_paths(
        cache_dir,
        dataset=dataset,
        model_name=model_name,
        record_kind="corpus",
        fingerprint=fingerprint,
        count=len(corpus),
    )
    if not embedding_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing corpus embedding cache for {dataset}: {embedding_path.name}"
        )
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    if model_revision is not None and metadata.get("model_revision") != str(model_revision):
        raise FileNotFoundError(
            f"Embedding cache revision mismatch for {dataset}: expected {model_revision}"
        )
    embeddings = np.load(embedding_path, mmap_mode="r", allow_pickle=False)
    if embeddings.shape[0] != len(corpus):
        raise ValueError(
            f"Embedding row mismatch for {dataset}: {embeddings.shape[0]} rows "
            f"for {len(corpus)} corpus records"
        )
    stored_fingerprint = metadata.get("embedding_content_fingerprint")
    if stored_fingerprint is not None:
        actual_fingerprint = embedding_cache.embedding_array_fingerprint(embeddings)
        if (
            metadata.get("embedding_content_fingerprint_version")
            != embedding_cache.EMBEDDING_FINGERPRINT_VERSION
            or stored_fingerprint != actual_fingerprint
        ):
            raise ValueError(f"Embedding content fingerprint mismatch for {dataset}")
    return np.asarray(embeddings, dtype=np.float32), metadata


def load_sentence_transformer(
    model_name: str,
    *,
    device: str | None = None,
    local_files_only: bool = False,
    revision: str | None = None,
):
    from sentence_transformers import SentenceTransformer

    kwargs = {}
    if device:
        kwargs["device"] = device
    if local_files_only:
        kwargs["local_files_only"] = True
    if revision:
        kwargs["revision"] = revision
    return SentenceTransformer(model_name, **kwargs)


def validate_store_provenance(
    store_dir: Path,
    *,
    model_name: str | None = None,
    model_revision: str | None,
) -> None:
    metadata_path = store_dir / "canonical_metadata.json"
    if not metadata_path.exists():
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if model_name is not None and metadata.get("model_name") != model_name:
        raise ValueError(
            f"Canonical store model mismatch: {metadata.get('model_name')!r} != {model_name!r}"
        )
    if model_revision is not None and metadata.get("model_revision") != str(model_revision):
        raise ValueError(
            "Canonical store model revision mismatch: "
            f"{metadata.get('model_revision')!r} != {model_revision!r}"
        )
    stored_fingerprint = metadata.get("embedding_content_fingerprint")
    if stored_fingerprint is None:
        return
    embeddings_path = store_dir / "canonical_corpus_embeddings.npy"
    embeddings = np.load(embeddings_path, mmap_mode="r", allow_pickle=False)
    if list(embeddings.shape) != list(metadata.get("embedding_shape", [])):
        raise ValueError("Canonical store embedding shape mismatch")
    actual_fingerprint = embedding_cache.embedding_array_fingerprint(embeddings)
    if (
        metadata.get("embedding_content_fingerprint_version")
        != embedding_cache.EMBEDDING_FINGERPRINT_VERSION
        or stored_fingerprint != actual_fingerprint
    ):
        raise ValueError("Canonical store embedding content fingerprint mismatch")


def load_existing_canonical_store(
    store_dir: Path,
    *,
    model_name: str,
    model_revision: str | None = None,
) -> tuple[List[str], List[str], List[List[str]], List[np.ndarray]]:
    ids_path = store_dir / "canonical_corpus_ids.json"
    embeddings_path = store_dir / "canonical_corpus_embeddings.npy"
    if not ids_path.exists() or not embeddings_path.exists():
        return [], [], [], []
    validate_store_provenance(
        store_dir,
        model_name=model_name,
        model_revision=model_revision,
    )

    with ids_path.open("r", encoding="utf-8") as f:
        ids_data = json.load(f)
    canonical_ids = [str(item) for item in ids_data.get("canonical_ids", [])]
    text_sha256 = [str(item) for item in ids_data.get("text_sha256", [])]
    source_datasets = [
        [str(value) for value in item]
        for item in ids_data.get("source_datasets", [])
    ]
    embeddings = np.load(embeddings_path).astype(np.float32, copy=False)
    if embeddings.shape[0] != len(canonical_ids):
        raise ValueError(
            f"Existing canonical store row mismatch: {embeddings.shape[0]} embedding rows "
            f"for {len(canonical_ids)} ids"
        )
    if len(text_sha256) != len(canonical_ids) or len(source_datasets) != len(canonical_ids):
        raise ValueError("Existing canonical id metadata length mismatch")
    return canonical_ids, text_sha256, source_datasets, [embeddings[idx] for idx in range(embeddings.shape[0])]


def write_json_atomic(path: Path, payload: Mapping) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    tmp_path.replace(path)


def append_scale_store_streaming(
    dataset: str,
    *,
    canonical_name: str,
    model_name: str,
    data_dir: Path,
    store_dir: Path,
    encoder,
    batch_size: int,
    encode_chunk_size: int,
    copy_chunk_size: int = 50000,
    model_revision: str | None = None,
) -> Dict[str, object]:
    """Append one scale using mmap-backed arrays to keep memory bounded."""
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if encode_chunk_size <= 0:
        raise ValueError(f"encode_chunk_size must be positive, got {encode_chunk_size}")
    if copy_chunk_size <= 0:
        raise ValueError(f"copy_chunk_size must be positive, got {copy_chunk_size}")

    store_dir.mkdir(parents=True, exist_ok=True)

    ids_path = store_dir / "canonical_corpus_ids.json"
    embeddings_path = store_dir / "canonical_corpus_embeddings.npy"
    if ids_path.exists() and embeddings_path.exists():
        validate_store_provenance(
            store_dir,
            model_name=model_name,
            model_revision=model_revision,
        )
        with ids_path.open("r", encoding="utf-8") as f:
            ids_data = json.load(f)
        canonical_ids = [str(item) for item in ids_data.get("canonical_ids", [])]
        canonical_text_sha256 = [str(item) for item in ids_data.get("text_sha256", [])]
        canonical_source_datasets = [
            [str(value) for value in item]
            for item in ids_data.get("source_datasets", [])
        ]
        existing_embeddings = np.load(embeddings_path, mmap_mode="r")
        if existing_embeddings.shape[0] != len(canonical_ids):
            raise ValueError(
                f"Existing canonical store row mismatch: {existing_embeddings.shape[0]} embedding rows "
                f"for {len(canonical_ids)} ids"
            )
        if len(canonical_text_sha256) != len(canonical_ids) or len(canonical_source_datasets) != len(canonical_ids):
            raise ValueError("Existing canonical id metadata length mismatch")
        dim = int(existing_embeddings.shape[1])
    elif not ids_path.exists() and not embeddings_path.exists():
        canonical_ids = []
        canonical_text_sha256 = []
        canonical_source_datasets = []
        existing_embeddings = None
        dim = int(encoder.get_sentence_embedding_dimension())
        if dim <= 0:
            raise ValueError("Could not determine encoder embedding dimension for empty streaming store")
    else:
        raise FileNotFoundError(
            f"Incomplete canonical store under {store_dir}; expected both ids and embeddings or neither"
        )

    canonical_index = {cid: row_idx for row_idx, cid in enumerate(canonical_ids)}
    corpus = load_json_list(corpus_path(data_dir, dataset))
    queries = load_json_list(queries_path(data_dir, dataset))
    row_indices = np.empty(len(corpus), dtype=np.int64)
    missing_local_indices: List[int] = []
    initial_count = len(canonical_ids)
    reused_rows = 0

    for local_idx, record in enumerate(corpus):
        cid = canonical_corpus_id(record, canonical_name=canonical_name)
        fp = text_fingerprint(record.get("text", ""))
        row_idx = canonical_index.get(cid)
        if row_idx is not None:
            if canonical_text_sha256[row_idx] != fp:
                raise ValueError(f"Text fingerprint mismatch for canonical id {cid} in {dataset}")
            if dataset not in canonical_source_datasets[row_idx]:
                canonical_source_datasets[row_idx].append(dataset)
            row_indices[local_idx] = row_idx
            reused_rows += 1
            continue

        row_idx = len(canonical_ids)
        canonical_index[cid] = row_idx
        canonical_ids.append(cid)
        canonical_text_sha256.append(fp)
        canonical_source_datasets.append([dataset])
        row_indices[local_idx] = row_idx
        missing_local_indices.append(local_idx)

    missing_count = len(missing_local_indices)
    new_embeddings_path = store_dir / f"{dataset}__new_embeddings.tmp.npy"
    combined_tmp_path = store_dir / "canonical_corpus_embeddings.tmp.npy"

    start = time.perf_counter()
    new_embeddings = None
    if missing_count:
        new_embeddings = np.lib.format.open_memmap(
            new_embeddings_path,
            mode="w+",
            dtype=np.float32,
            shape=(missing_count, dim),
        )
        for start_idx in range(0, missing_count, encode_chunk_size):
            end_idx = min(start_idx + encode_chunk_size, missing_count)
            print(
                f"[{dataset}] encoding missing rows {start_idx + 1}-{end_idx} "
                f"of {missing_count}",
                flush=True,
            )
            texts = [
                str(corpus[missing_local_indices[idx]].get("text", ""))
                for idx in range(start_idx, end_idx)
            ]
            new_embeddings[start_idx:end_idx] = embedding_cache.encode_texts(
                encoder,
                texts,
                batch_size=batch_size,
            )
            new_embeddings.flush()
    encode_elapsed_sec = time.perf_counter() - start

    final_count = len(canonical_ids)
    if missing_count:
        combined = np.lib.format.open_memmap(
            combined_tmp_path,
            mode="w+",
            dtype=np.float32,
            shape=(final_count, dim),
        )
        if initial_count:
            print(f"[{dataset}] copying existing canonical rows 1-{initial_count}", flush=True)
            for start_idx in range(0, initial_count, copy_chunk_size):
                end_idx = min(start_idx + copy_chunk_size, initial_count)
                combined[start_idx:end_idx] = existing_embeddings[start_idx:end_idx]
        print(f"[{dataset}] copying new canonical rows {initial_count + 1}-{final_count}", flush=True)
        for start_idx in range(0, missing_count, copy_chunk_size):
            end_idx = min(start_idx + copy_chunk_size, missing_count)
            combined[initial_count + start_idx : initial_count + end_idx] = new_embeddings[start_idx:end_idx]
        combined.flush()

    row_index_path = store_dir / f"{dataset}__row_indices.npy"
    np.save(row_index_path, row_indices)
    manifest_path = store_dir / f"{dataset}__manifest.json"
    manifest = {
        "dataset": dataset,
        "canonical_name": canonical_name,
        "model_name": model_name,
        "model_revision": str(model_revision or ""),
        "corpus_count": len(corpus),
        "query_count": len(queries),
        "ground_truth_ref_count": dataset_gt_ref_count(queries),
        "canonical_row_count": final_count,
        "new_canonical_rows": missing_count,
        "reused_canonical_rows": reused_rows,
        "dataset_embedding_cache_hit": False,
        "encoded_missing_rows": missing_count,
        "encode_elapsed_sec": round(encode_elapsed_sec, 3),
        "row_index_path": str(row_index_path),
        "embedding_cache_path": None,
        "embedding_cache_fingerprint": None,
    }
    write_json_atomic(manifest_path, manifest)

    existing_manifest_paths = sorted(str(path) for path in store_dir.glob("*__manifest.json"))
    canonical_ids_payload = {
        "canonical_ids": canonical_ids,
        "text_sha256": canonical_text_sha256,
        "source_datasets": canonical_source_datasets,
    }
    if missing_count:
        combined_tmp_path.replace(embeddings_path)
    canonical_embedding_fingerprint = embedding_cache.embedding_array_fingerprint(
        np.load(embeddings_path, mmap_mode="r", allow_pickle=False)
    )
    canonical_metadata = {
        "canonical_name": canonical_name,
        "model_name": model_name,
        "model_revision": str(model_revision or ""),
        "datasets": sorted({
            *(Path(path).name.split("__manifest.json")[0] for path in existing_manifest_paths),
            dataset,
        }),
        "canonical_count": final_count,
        "embedding_shape": [final_count, dim],
        "normalized": True,
        "embedding_content_fingerprint_version": embedding_cache.EMBEDDING_FINGERPRINT_VERSION,
        "embedding_content_fingerprint": canonical_embedding_fingerprint,
        "canonical_embedding_path": str(embeddings_path),
        "canonical_ids_path": str(ids_path),
        "scale_manifests": sorted({*existing_manifest_paths, str(manifest_path)}),
    }
    summary = {
        "canonical_name": canonical_name,
        "model_name": model_name,
        "model_revision": str(model_revision or ""),
        "store_dir": str(store_dir),
        "initial_canonical_count": initial_count,
        "canonical_count": final_count,
        "new_canonical_rows": missing_count,
        "embedding_shape": [final_count, dim],
        "datasets": [{**manifest, "manifest_path": str(manifest_path)}],
    }

    write_json_atomic(ids_path, canonical_ids_payload)
    write_json_atomic(store_dir / "canonical_metadata.json", canonical_metadata)
    write_json_atomic(store_dir / "store_summary.json", summary)
    if missing_count:
        try:
            new_embeddings_path.unlink()
        except FileNotFoundError:
            pass
    return summary


def build_scale_store(
    datasets: Sequence[str],
    *,
    canonical_name: str,
    model_name: str,
    data_dir: Path,
    embedding_cache_dir: Path,
    store_dir: Path,
    append_existing_store: bool = False,
    compute_missing: bool = False,
    encoder=None,
    batch_size: int = 64,
    encode_chunk_size: int = 10000,
    model_revision: str | None = None,
) -> Dict[str, object]:
    if not datasets:
        raise ValueError("At least one dataset is required")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if encode_chunk_size <= 0:
        raise ValueError(f"encode_chunk_size must be positive, got {encode_chunk_size}")

    store_dir.mkdir(parents=True, exist_ok=True)
    if append_existing_store:
        (
            canonical_ids,
            canonical_text_sha256,
            canonical_source_datasets,
            canonical_vectors,
        ) = load_existing_canonical_store(
            store_dir,
            model_name=model_name,
            model_revision=model_revision,
        )
    else:
        canonical_ids = []
        canonical_text_sha256 = []
        canonical_source_datasets = []
        canonical_vectors = []
    canonical_index: Dict[str, int] = {}
    for row_idx, cid in enumerate(canonical_ids):
        if cid in canonical_index:
            raise ValueError(f"Duplicate canonical id in existing store: {cid}")
        canonical_index[cid] = row_idx
    scale_summaries: List[Dict[str, object]] = []
    initial_canonical_count = len(canonical_ids)
    existing_manifest_paths = sorted(
        str(path) for path in store_dir.glob("*__manifest.json")
    )

    for dataset in datasets:
        corpus = load_json_list(corpus_path(data_dir, dataset))
        queries = load_json_list(queries_path(data_dir, dataset))
        try:
            embeddings, cache_metadata = load_cached_corpus_embeddings(
                dataset,
                corpus,
                model_name=model_name,
                cache_dir=embedding_cache_dir,
                model_revision=model_revision,
            )
            dataset_cache_hit = True
        except FileNotFoundError:
            embeddings = None
            cache_metadata = {}
            dataset_cache_hit = False

        row_indices: List[int] = []
        new_rows = 0
        reused_rows = 0
        missing_local_indices: List[int] = []
        missing_canonical_ids: List[str] = []
        missing_text_fps: List[str] = []
        for local_idx, record in enumerate(corpus):
            cid = canonical_corpus_id(record, canonical_name=canonical_name)
            fp = text_fingerprint(record.get("text", ""))
            if cid in canonical_index:
                row_idx = canonical_index[cid]
                if canonical_text_sha256[row_idx] != fp:
                    raise ValueError(
                        f"Text fingerprint mismatch for canonical id {cid} in {dataset}"
                    )
                if dataset not in canonical_source_datasets[row_idx]:
                    canonical_source_datasets[row_idx].append(dataset)
                reused_rows += 1
            else:
                row_idx = len(canonical_ids)
                canonical_index[cid] = row_idx
                canonical_ids.append(cid)
                canonical_text_sha256.append(fp)
                canonical_source_datasets.append([dataset])
                if embeddings is not None:
                    canonical_vectors.append(embeddings[local_idx])
                else:
                    missing_local_indices.append(local_idx)
                    missing_canonical_ids.append(cid)
                    missing_text_fps.append(fp)
                new_rows += 1
            row_indices.append(row_idx)

        encoded_missing_rows = len(missing_local_indices)
        encode_elapsed_sec = 0.0
        if missing_local_indices:
            if not compute_missing:
                raise FileNotFoundError(
                    f"Missing corpus embedding cache for {dataset} and "
                    f"{len(missing_local_indices)} canonical rows are not in the existing store"
                )
            if encoder is None:
                raise ValueError("encoder is required when compute_missing=True")
            texts = [str(corpus[idx].get("text", "")) for idx in missing_local_indices]
            start = time.perf_counter()
            chunks: List[np.ndarray] = []
            for start_idx in range(0, len(texts), encode_chunk_size):
                end_idx = min(start_idx + encode_chunk_size, len(texts))
                print(
                    f"[{dataset}] encoding missing rows {start_idx + 1}-{end_idx} "
                    f"of {len(texts)}",
                    flush=True,
                )
                chunks.append(
                    embedding_cache.encode_texts(
                        encoder,
                        texts[start_idx:end_idx],
                        batch_size=batch_size,
                    )
                )
            missing_embeddings = np.vstack(chunks).astype(np.float32, copy=False)
            encode_elapsed_sec = time.perf_counter() - start
            for offset, vector in enumerate(missing_embeddings):
                expected_idx = canonical_index[missing_canonical_ids[offset]]
                if expected_idx != len(canonical_vectors):
                    raise ValueError("Internal canonical vector append order mismatch")
                canonical_vectors.append(vector)
                if canonical_text_sha256[expected_idx] != missing_text_fps[offset]:
                    raise ValueError("Internal missing text fingerprint mismatch")

        row_index_path = store_dir / f"{dataset}__row_indices.npy"
        np.save(row_index_path, np.asarray(row_indices, dtype=np.int64))
        manifest = {
            "dataset": dataset,
            "canonical_name": canonical_name,
            "model_name": model_name,
            "model_revision": str(model_revision or ""),
            "corpus_count": len(corpus),
            "query_count": len(queries),
            "ground_truth_ref_count": dataset_gt_ref_count(queries),
            "canonical_row_count": len(canonical_ids),
            "new_canonical_rows": new_rows,
            "reused_canonical_rows": reused_rows,
            "dataset_embedding_cache_hit": dataset_cache_hit,
            "encoded_missing_rows": encoded_missing_rows,
            "encode_elapsed_sec": round(encode_elapsed_sec, 3),
            "row_index_path": str(row_index_path),
            "embedding_cache_path": cache_metadata.get("embedding_path"),
            "embedding_cache_fingerprint": cache_metadata.get("fingerprint"),
        }
        manifest_path = store_dir / f"{dataset}__manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        manifest["manifest_path"] = str(manifest_path)
        scale_summaries.append(manifest)

    canonical_embeddings = np.vstack(canonical_vectors).astype(np.float32, copy=False)
    canonical_embedding_path = store_dir / "canonical_corpus_embeddings.npy"
    np.save(canonical_embedding_path, canonical_embeddings)
    canonical_metadata = {
        "canonical_name": canonical_name,
        "model_name": model_name,
        "model_revision": str(model_revision or ""),
        "datasets": sorted({
            *datasets,
            *(Path(path).name.split("__manifest.json")[0] for path in existing_manifest_paths),
        }),
        "canonical_count": len(canonical_ids),
        "embedding_shape": list(canonical_embeddings.shape),
        "normalized": True,
        "embedding_content_fingerprint_version": embedding_cache.EMBEDDING_FINGERPRINT_VERSION,
        "embedding_content_fingerprint": embedding_cache.embedding_array_fingerprint(canonical_embeddings),
        "canonical_embedding_path": str(canonical_embedding_path),
        "canonical_ids_path": str(store_dir / "canonical_corpus_ids.json"),
        "scale_manifests": sorted({
            *existing_manifest_paths,
            *(str(summary["manifest_path"]) for summary in scale_summaries),
        }),
    }
    with (store_dir / "canonical_corpus_ids.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "canonical_ids": canonical_ids,
                "text_sha256": canonical_text_sha256,
                "source_datasets": canonical_source_datasets,
            },
            f,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    with (store_dir / "canonical_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(canonical_metadata, f, ensure_ascii=False, indent=2, sort_keys=True)

    summary = {
        "canonical_name": canonical_name,
        "model_name": model_name,
        "model_revision": str(model_revision or ""),
        "store_dir": str(store_dir),
        "initial_canonical_count": initial_canonical_count,
        "canonical_count": len(canonical_ids),
        "new_canonical_rows": len(canonical_ids) - initial_canonical_count,
        "embedding_shape": list(canonical_embeddings.shape),
        "datasets": scale_summaries,
    }
    with (store_dir / "store_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, sort_keys=True)
    return summary


def parse_datasets(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets",
        default="lotte_technology_search_100k,lotte_technology_search_200k",
        help="Comma-separated processed dataset names in nesting order",
    )
    parser.add_argument("--canonical-name", default="lotte_technology_search")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-revision", default=None, help="Pinned Hugging Face model revision")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--embedding-cache-dir", type=Path, default=DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    parser.add_argument("--append-existing-store", action="store_true")
    parser.add_argument("--compute-missing", action="store_true", help="Encode canonical rows missing from cache/store")
    parser.add_argument("--streaming-append", action="store_true", help="Append one scale using mmap-backed arrays")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--encode-chunk-size", type=int, default=10000)
    parser.add_argument("--device", default=None, help="SentenceTransformer device, e.g. cpu/cuda")
    parser.add_argument("--local-files-only", action="store_true", help="Load model from local HF cache only")
    args = parser.parse_args()

    encoder = None
    if args.compute_missing:
        encoder = load_sentence_transformer(
            args.model,
            device=args.device,
            local_files_only=args.local_files_only,
            revision=args.model_revision,
        )

    datasets = parse_datasets(args.datasets)
    if args.streaming_append:
        if len(datasets) != 1:
            raise ValueError("--streaming-append requires exactly one dataset")
        if encoder is None:
            raise ValueError("--streaming-append requires --compute-missing")
        summary = append_scale_store_streaming(
            datasets[0],
            canonical_name=args.canonical_name,
            model_name=args.model,
            data_dir=args.data_dir,
            store_dir=args.store_dir,
            encoder=encoder,
            batch_size=args.batch_size,
            encode_chunk_size=args.encode_chunk_size,
            model_revision=args.model_revision,
        )
    else:
        summary = build_scale_store(
            datasets,
            canonical_name=args.canonical_name,
            model_name=args.model,
            data_dir=args.data_dir,
            embedding_cache_dir=args.embedding_cache_dir,
            store_dir=args.store_dir,
            append_existing_store=args.append_existing_store,
            compute_missing=args.compute_missing,
            encoder=encoder,
            batch_size=args.batch_size,
            encode_chunk_size=args.encode_chunk_size,
            model_revision=args.model_revision,
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
