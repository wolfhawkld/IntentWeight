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
    embeddings = np.load(embedding_path)
    if embeddings.shape[0] != len(corpus):
        raise ValueError(
            f"Embedding row mismatch for {dataset}: {embeddings.shape[0]} rows "
            f"for {len(corpus)} corpus records"
        )
    return embeddings.astype(np.float32, copy=False), metadata


def build_scale_store(
    datasets: Sequence[str],
    *,
    canonical_name: str,
    model_name: str,
    data_dir: Path,
    embedding_cache_dir: Path,
    store_dir: Path,
) -> Dict[str, object]:
    if not datasets:
        raise ValueError("At least one dataset is required")

    store_dir.mkdir(parents=True, exist_ok=True)
    canonical_ids: List[str] = []
    canonical_text_sha256: List[str] = []
    canonical_source_datasets: List[List[str]] = []
    canonical_vectors: List[np.ndarray] = []
    canonical_index: Dict[str, int] = {}
    scale_summaries: List[Dict[str, object]] = []

    for dataset in datasets:
        corpus = load_json_list(corpus_path(data_dir, dataset))
        queries = load_json_list(queries_path(data_dir, dataset))
        embeddings, cache_metadata = load_cached_corpus_embeddings(
            dataset,
            corpus,
            model_name=model_name,
            cache_dir=embedding_cache_dir,
        )

        row_indices: List[int] = []
        new_rows = 0
        reused_rows = 0
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
                canonical_vectors.append(embeddings[local_idx])
                new_rows += 1
            row_indices.append(row_idx)

        row_index_path = store_dir / f"{dataset}__row_indices.npy"
        np.save(row_index_path, np.asarray(row_indices, dtype=np.int64))
        manifest = {
            "dataset": dataset,
            "canonical_name": canonical_name,
            "model_name": model_name,
            "corpus_count": len(corpus),
            "query_count": len(queries),
            "ground_truth_ref_count": dataset_gt_ref_count(queries),
            "canonical_row_count": len(canonical_ids),
            "new_canonical_rows": new_rows,
            "reused_canonical_rows": reused_rows,
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
        "datasets": list(datasets),
        "canonical_count": len(canonical_ids),
        "embedding_shape": list(canonical_embeddings.shape),
        "normalized": True,
        "canonical_embedding_path": str(canonical_embedding_path),
        "canonical_ids_path": str(store_dir / "canonical_corpus_ids.json"),
        "scale_manifests": [
            summary["manifest_path"] for summary in scale_summaries
        ],
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
        "store_dir": str(store_dir),
        "canonical_count": len(canonical_ids),
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
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--embedding-cache-dir", type=Path, default=DEFAULT_EMBEDDING_CACHE_DIR)
    parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    args = parser.parse_args()

    summary = build_scale_store(
        parse_datasets(args.datasets),
        canonical_name=args.canonical_name,
        model_name=args.model,
        data_dir=args.data_dir,
        embedding_cache_dir=args.embedding_cache_dir,
        store_dir=args.store_dir,
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
