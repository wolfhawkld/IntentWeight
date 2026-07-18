#!/usr/bin/env python3
"""Revalidate GPU-generated embeddings against frozen paper artifacts.

Run this script only after sourcing ``.venv-rocm/bin/activate-rocm``. Formal
outputs are isolated under ``data/task78_revalidation``; compact audit reports
are written under ``results/task78_gpu_revalidation``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DEFAULT_DATA_DIR = EXPERIMENT_DIR / "data" / "processed"
DEFAULT_LOCAL_ROOT = EXPERIMENT_DIR / "data" / "task78_revalidation"
DEFAULT_REPORT_DIR = EXPERIMENT_DIR / "results" / "task78_gpu_revalidation"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


embedding_cache = load_module("task78_embedding_cache", SCRIPT_DIR / "embedding_cache.py")
dense_baseline = load_module("task78_dense_baseline", SCRIPT_DIR / "dense_baseline.py")
large_scale_artifacts = load_module("task78_large_scale_artifacts", SCRIPT_DIR / "large_scale_artifacts.py")
retrieval_metrics = load_module("task78_retrieval_metrics", SCRIPT_DIR / "retrieval_metrics.py")


@dataclass(frozen=True)
class ModelSpec:
    model_name: str
    revision: str
    snapshot_path: Path
    query_prefix: str = ""
    corpus_prefix: str = ""
    batch_size: int = 128


@dataclass(frozen=True)
class CaseSpec:
    name: str
    dataset: str
    model_key: str
    reference_corpus: Path
    reference_queries: Path
    reference_rankings: Path
    reference_depth: int
    corpus_row_indices: Path | None = None


MODELS: Dict[str, ModelSpec] = {
    "minilm": ModelSpec(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        revision="c9745ed1d9f207416be6d2e6f8de32d1f16199bf",
        snapshot_path=Path.home()
        / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots"
        / "c9745ed1d9f207416be6d2e6f8de32d1f16199bf",
        batch_size=256,
    ),
    "bge": ModelSpec(
        model_name="BAAI/bge-base-en-v1.5",
        revision="a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
        snapshot_path=EXPERIMENT_DIR
        / "data/hf_cache/hub/models--BAAI--bge-base-en-v1.5/snapshots"
        / "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
        query_prefix="Represent this sentence for searching relevant passages: ",
        batch_size=128,
    ),
    "e5": ModelSpec(
        model_name="intfloat/e5-base-v2",
        revision="f52bf8ec8c7124536f0efb74aca902b2995e5bcd",
        snapshot_path=EXPERIMENT_DIR
        / "data/hf_cache/hub/models--intfloat--e5-base-v2/snapshots"
        / "f52bf8ec8c7124536f0efb74aca902b2995e5bcd",
        query_prefix="query: ",
        corpus_prefix="passage: ",
        batch_size=64,
    ),
}


EMBEDDING_DIR = EXPERIMENT_DIR / "data" / "embeddings"
SCALE_STORE_DIR = EXPERIMENT_DIR / "data" / "scale_store"
RESULTS_DIR = EXPERIMENT_DIR / "results"

CASES: Dict[str, CaseSpec] = {
    "task47_minilm_technology_100k": CaseSpec(
        name="task47_minilm_technology_100k",
        dataset="lotte_technology_search_100k",
        model_key="minilm",
        reference_corpus=EMBEDDING_DIR
        / "lotte_technology_search_100k__sentence-transformers-all-MiniLM-L6-v2__corpus__n101311__60ef5529c079a71e.npy",
        reference_queries=EMBEDDING_DIR
        / "lotte_technology_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n596__6c7ae007c1bcc394.npy",
        reference_rankings=RESULTS_DIR
        / "task47_dense_top50_candidates/dense_lotte_technology_search_100k_rankings.json",
        reference_depth=50,
    ),
    "task52_bge_technology_100k": CaseSpec(
        name="task52_bge_technology_100k",
        dataset="lotte_technology_search_100k",
        model_key="bge",
        reference_corpus=EMBEDDING_DIR
        / "lotte_technology_search_100k__BAAI-bge-base-en-v1.5__corpus__n101311__60ef5529c079a71e.npy",
        reference_queries=EMBEDDING_DIR
        / "lotte_technology_search_100k__BAAI-bge-base-en-v1.5__queries__n596__784629613311b95d.npy",
        reference_rankings=RESULTS_DIR
        / "task52_bge_base_100k_dense/dense_lotte_technology_search_100k_rankings.json",
        reference_depth=50,
    ),
    "task53_e5_technology_100k": CaseSpec(
        name="task53_e5_technology_100k",
        dataset="lotte_technology_search_100k",
        model_key="e5",
        reference_corpus=EMBEDDING_DIR
        / "lotte_technology_search_100k__intfloat-e5-base-v2__corpus__n101311__478578f7f4860e9e.npy",
        reference_queries=EMBEDDING_DIR
        / "lotte_technology_search_100k__intfloat-e5-base-v2__queries__n596__03c27f56825b35cf.npy",
        reference_rankings=RESULTS_DIR
        / "task53_e5_base_100k_dense/dense_lotte_technology_search_100k_rankings.json",
        reference_depth=50,
    ),
    "task73_minilm_recreation_100k": CaseSpec(
        name="task73_minilm_recreation_100k",
        dataset="lotte_recreation_search_100k",
        model_key="minilm",
        reference_corpus=SCALE_STORE_DIR
        / "lotte_recreation_search/canonical_corpus_embeddings.npy",
        reference_queries=EMBEDDING_DIR
        / "lotte_recreation_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n924__599aec869650feb3.npy",
        reference_rankings=RESULTS_DIR
        / "task73_recreation_100k_dense/dense_lotte_recreation_search_100k_rankings.json",
        reference_depth=10,
        corpus_row_indices=SCALE_STORE_DIR
        / "lotte_recreation_search/lotte_recreation_search_100k__row_indices.npy",
    ),
    "task73_minilm_writing_100k": CaseSpec(
        name="task73_minilm_writing_100k",
        dataset="lotte_writing_search_100k",
        model_key="minilm",
        reference_corpus=SCALE_STORE_DIR
        / "lotte_writing_search/canonical_corpus_embeddings.npy",
        reference_queries=EMBEDDING_DIR
        / "lotte_writing_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n1071__58c4703c7d059681.npy",
        reference_rankings=RESULTS_DIR
        / "task73_writing_100k_dense/dense_lotte_writing_search_100k_rankings.json",
        reference_depth=10,
        corpus_row_indices=SCALE_STORE_DIR
        / "lotte_writing_search/lotte_writing_search_100k__row_indices.npy",
    ),
}


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def load_json_list(path: Path) -> list[Mapping]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def load_rankings(path: Path) -> Dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected ranking object: {path}")
    return {str(key): [str(value) for value in values] for key, values in data.items()}


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def portable_tree(value):
    if isinstance(value, str):
        return value.replace(str(Path.home()), "$HOME")
    if isinstance(value, list):
        return [portable_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: portable_tree(item) for key, item in value.items()}
    return value


def snapshot_fingerprint(snapshot_path: Path) -> tuple[str, list[dict[str, object]]]:
    if not snapshot_path.is_dir():
        raise FileNotFoundError(f"Missing model snapshot: {snapshot_path}")
    files = []
    for path in sorted(item for item in snapshot_path.rglob("*") if item.is_file()):
        files.append({
            "path": str(path.relative_to(snapshot_path)),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), files


def git_info() -> dict[str, object]:
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "status", "--short"], cwd=REPO_ROOT, text=True
    ).splitlines()
    return {"commit": commit, "dirty": bool(status), "status": status}


def runtime_info() -> dict[str, object]:
    import sklearn
    import sentence_transformers
    import torch
    import transformers

    available = bool(torch.cuda.is_available())
    device_name = torch.cuda.get_device_name(0) if available else ""
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "torch_hip": torch.version.hip,
        "transformers": transformers.__version__,
        "sentence_transformers": sentence_transformers.__version__,
        "scikit_learn": sklearn.__version__,
        "gpu_available": available,
        "gpu_device": device_name,
        "gpu_count": torch.cuda.device_count() if available else 0,
        "hsa_enable_dxg_detection": os.environ.get("HSA_ENABLE_DXG_DETECTION", ""),
        "rocm_path": os.environ.get("ROCM_PATH", ""),
        "dxg_visible": Path("/dev/dxg").exists(),
        "rocdxg_library_visible": (Path.home() / ".local/rocdxg/lib/librocdxg.so.1").exists(),
    }


def assert_gpu_contract(info: Mapping[str, object]) -> None:
    failures = []
    if not info.get("gpu_available"):
        failures.append("torch.cuda.is_available() is false")
    if "9070 XT" not in str(info.get("gpu_device", "")):
        failures.append(f"unexpected GPU device {info.get('gpu_device')!r}")
    if not info.get("torch_hip"):
        failures.append("PyTorch has no HIP runtime")
    if not info.get("dxg_visible"):
        failures.append("/dev/dxg is not visible")
    if str(info.get("hsa_enable_dxg_detection")) != "1":
        failures.append("HSA_ENABLE_DXG_DETECTION is not 1")
    if not info.get("rocdxg_library_visible"):
        failures.append("external librocdxg is not visible")
    if failures:
        raise RuntimeError("ROCm preflight failed: " + "; ".join(failures))


def load_reference_corpus(case: CaseSpec) -> np.ndarray:
    values = np.load(case.reference_corpus, mmap_mode="r", allow_pickle=False)
    if case.corpus_row_indices is None:
        return values
    row_indices = np.load(case.corpus_row_indices, mmap_mode="r", allow_pickle=False)
    return values[row_indices]


def compare_arrays(
    candidate: np.ndarray,
    reference: np.ndarray,
    *,
    chunk_rows: int = 4096,
) -> dict[str, object]:
    candidate = np.asarray(candidate)
    reference = np.asarray(reference)
    result: dict[str, object] = {
        "candidate_shape": list(candidate.shape),
        "reference_shape": list(reference.shape),
        "candidate_dtype": str(candidate.dtype),
        "reference_dtype": str(reference.dtype),
    }
    if candidate.shape != reference.shape:
        result.update({"pass": False, "reason": "shape_mismatch"})
        return result

    max_abs = 0.0
    min_cosine = 1.0
    cosine_sum = 0.0
    exact_rows = 0
    candidate_norm_min = float("inf")
    candidate_norm_max = 0.0
    reference_norm_min = float("inf")
    reference_norm_max = 0.0
    nonfinite_candidate = 0
    nonfinite_reference = 0
    for start in range(0, len(candidate), chunk_rows):
        end = min(start + chunk_rows, len(candidate))
        left = np.asarray(candidate[start:end], dtype=np.float32)
        right = np.asarray(reference[start:end], dtype=np.float32)
        nonfinite_candidate += int(left.size - np.count_nonzero(np.isfinite(left)))
        nonfinite_reference += int(right.size - np.count_nonzero(np.isfinite(right)))
        max_abs = max(max_abs, float(np.max(np.abs(left - right), initial=0.0)))
        left_norm = np.linalg.norm(left, axis=1)
        right_norm = np.linalg.norm(right, axis=1)
        candidate_norm_min = min(candidate_norm_min, float(np.min(left_norm, initial=np.inf)))
        candidate_norm_max = max(candidate_norm_max, float(np.max(left_norm, initial=0.0)))
        reference_norm_min = min(reference_norm_min, float(np.min(right_norm, initial=np.inf)))
        reference_norm_max = max(reference_norm_max, float(np.max(right_norm, initial=0.0)))
        denominators = left_norm * right_norm
        cosines = np.divide(
            np.sum(left * right, axis=1),
            denominators,
            out=np.zeros_like(denominators),
            where=denominators > 0,
        )
        min_cosine = min(min_cosine, float(np.min(cosines, initial=1.0)))
        cosine_sum += float(np.sum(cosines, dtype=np.float64))
        exact_rows += int(np.count_nonzero(np.all(left == right, axis=1)))

    row_count = len(candidate)
    result.update({
        "row_count": row_count,
        "max_abs_difference": max_abs,
        "min_cosine_similarity": min_cosine,
        "mean_cosine_similarity": cosine_sum / row_count if row_count else 1.0,
        "exact_row_count": exact_rows,
        "exact_row_fraction": exact_rows / row_count if row_count else 1.0,
        "candidate_norm_min": candidate_norm_min if row_count else 0.0,
        "candidate_norm_max": candidate_norm_max,
        "reference_norm_min": reference_norm_min if row_count else 0.0,
        "reference_norm_max": reference_norm_max,
        "candidate_nonfinite_values": nonfinite_candidate,
        "reference_nonfinite_values": nonfinite_reference,
        "pass": (
            nonfinite_candidate == 0
            and nonfinite_reference == 0
            and min_cosine >= 0.99999
            and abs(candidate_norm_min - 1.0) <= 1e-4
            and abs(candidate_norm_max - 1.0) <= 1e-4
        ),
    })
    return result


def compare_rankings(
    candidate: Mapping[str, Sequence[str]],
    reference: Mapping[str, Sequence[str]],
    *,
    reference_depth: int,
) -> dict[str, object]:
    candidate_ids = set(candidate)
    reference_ids = set(reference)
    common = sorted(candidate_ids & reference_ids)

    def ordered_equality_at(depth: int) -> tuple[int, float]:
        equal = sum(
            list(candidate[query_id])[:depth] == list(reference[query_id])[:depth]
            for query_id in common
        )
        return equal, equal / len(common) if common else 0.0

    def membership_equality_at(depth: int) -> tuple[int, float]:
        equal = sum(
            set(candidate[query_id][:depth]) == set(reference[query_id][:depth])
            for query_id in common
        )
        return equal, equal / len(common) if common else 0.0

    top10_depth = min(10, reference_depth)
    top10_ordered_equal, top10_ordered_fraction = ordered_equality_at(top10_depth)
    top10_membership_equal, top10_membership_fraction = membership_equality_at(top10_depth)
    depth_ordered_equal, depth_ordered_fraction = ordered_equality_at(reference_depth)
    depth_membership_equal, depth_membership_fraction = membership_equality_at(reference_depth)
    return {
        "candidate_query_count": len(candidate_ids),
        "reference_query_count": len(reference_ids),
        "query_sets_equal": candidate_ids == reference_ids,
        "top10_ordered_equal_queries": top10_ordered_equal,
        "top10_ordered_equal_fraction": top10_ordered_fraction,
        "top10_membership_equal_queries": top10_membership_equal,
        "top10_membership_equal_fraction": top10_membership_fraction,
        "reference_depth": reference_depth,
        "reference_depth_ordered_equal_queries": depth_ordered_equal,
        "reference_depth_ordered_equal_fraction": depth_ordered_fraction,
        "reference_depth_membership_equal_queries": depth_membership_equal,
        "reference_depth_membership_equal_fraction": depth_membership_fraction,
        "strict_order_pass": candidate_ids == reference_ids and top10_ordered_fraction == 1.0,
        "pass": candidate_ids == reference_ids and top10_membership_fraction == 1.0,
    }


def top10_order_diagnostics(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    candidate_rankings: Mapping[str, Sequence[str]],
    reference_rankings: Mapping[str, Sequence[str]],
    candidate_corpus_embeddings: np.ndarray,
    candidate_query_embeddings: np.ndarray,
    reference_corpus_embeddings: np.ndarray,
    reference_query_embeddings: np.ndarray,
) -> list[dict[str, object]]:
    corpus_ids = [str(record.get("chunk_id") or record.get("id")) for record in corpus]
    corpus_index = {chunk_id: index for index, chunk_id in enumerate(corpus_ids)}
    corpus_text = {chunk_id: str(record.get("text", "")) for chunk_id, record in zip(corpus_ids, corpus)}
    query_index = {
        str(record.get("query_id") or record.get("id")): index
        for index, record in enumerate(queries)
    }
    query_by_id = {
        str(record.get("query_id") or record.get("id")): record
        for record in queries
    }
    diagnostics = []
    for query_id in sorted(reference_rankings):
        candidate_top10 = list(candidate_rankings[query_id])[:10]
        reference_top10 = list(reference_rankings[query_id])[:10]
        if candidate_top10 == reference_top10:
            continue
        changed_ids = sorted(set(candidate_top10) | set(reference_top10))
        query_row = query_index[query_id]
        candidate_scores = np.asarray(candidate_corpus_embeddings) @ np.asarray(
            candidate_query_embeddings[query_row]
        )
        reference_scores = np.asarray(reference_corpus_embeddings) @ np.asarray(
            reference_query_embeddings[query_row]
        )
        changed = []
        for chunk_id in changed_ids:
            row = corpus_index[chunk_id]
            changed.append({
                "chunk_id": chunk_id,
                "text_sha256": hashlib.sha256(corpus_text[chunk_id].encode("utf-8")).hexdigest(),
                "candidate_position": candidate_top10.index(chunk_id) + 1 if chunk_id in candidate_top10 else None,
                "reference_position": reference_top10.index(chunk_id) + 1 if chunk_id in reference_top10 else None,
                "candidate_score": float(candidate_scores[row]),
                "reference_score": float(reference_scores[row]),
            })
        diagnostics.append({
            "query_id": query_id,
            "query_text": str(query_by_id[query_id].get("text", "")),
            "ground_truth_chunk_ids": query_by_id[query_id].get("ground_truth_chunk_ids", []),
            "same_top10_membership": set(candidate_top10) == set(reference_top10),
            "candidate_top10": candidate_top10,
            "reference_top10": reference_top10,
            "changed_chunks": changed,
        })
    return diagnostics


def metric_comparison(
    queries: Sequence[Mapping],
    candidate: Mapping[str, Sequence[str]],
    reference: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    ks = (1, 5, 10)
    candidate_metrics = retrieval_metrics.evaluate_rankings(queries, candidate, ks=ks)
    reference_metrics = retrieval_metrics.evaluate_rankings(queries, reference, ks=ks)
    keys = sorted(key for key in candidate_metrics if "@" in key)
    differences = {
        key: float(candidate_metrics[key]) - float(reference_metrics[key])
        for key in keys
    }
    return {
        "candidate": {key: candidate_metrics[key] for key in keys},
        "reference": {key: reference_metrics[key] for key in keys},
        "differences": differences,
        "pass": all(value == 0.0 for value in differences.values()),
    }


def encode_records(
    records: Sequence[Mapping],
    encoder,
    *,
    case: CaseSpec,
    model: ModelSpec,
    record_kind: str,
    prefix: str,
    cache_dir: Path,
    force: bool,
) -> tuple[np.ndarray, dict[str, object]]:
    encoding_records = dense_baseline.records_with_text_prefix(records, prefix)
    return embedding_cache.load_or_compute_embeddings(
        encoding_records,
        dataset=case.dataset,
        model_name=model.model_name,
        model_revision=model.revision,
        record_kind=record_kind,
        encoder=encoder,
        batch_size=model.batch_size,
        cache_dir=cache_dir,
        force=force,
    )


def case_inputs(case: CaseSpec, data_dir: Path) -> tuple[list[Mapping], list[Mapping]]:
    corpus = load_json_list(data_dir / f"{case.dataset}_corpus.json")
    queries = load_json_list(data_dir / f"{case.dataset}_queries.json")
    return corpus, queries


def load_encoder(model: ModelSpec):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(str(model.snapshot_path), device="cuda", local_files_only=True)


def run_preflight_case(case: CaseSpec, data_dir: Path, sample_size: int) -> dict[str, object]:
    import torch

    model = MODELS[case.model_key]
    corpus, queries = case_inputs(case, data_dir)
    sample_corpus = corpus[: min(sample_size, len(corpus))]
    sample_queries = queries[: min(sample_size, len(queries))]
    encoder = load_encoder(model)
    started = time.perf_counter()
    candidate_corpus = embedding_cache.encode_texts(
        encoder,
        [f"{model.corpus_prefix}{record.get('text', '')}" for record in sample_corpus],
        batch_size=model.batch_size,
    )
    candidate_queries = embedding_cache.encode_texts(
        encoder,
        [f"{model.query_prefix}{record.get('text', '')}" for record in sample_queries],
        batch_size=model.batch_size,
    )
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    reference_corpus = load_reference_corpus(case)[: len(sample_corpus)]
    reference_queries = np.load(case.reference_queries, mmap_mode="r", allow_pickle=False)[: len(sample_queries)]
    corpus_comparison = compare_arrays(candidate_corpus, reference_corpus)
    query_comparison = compare_arrays(candidate_queries, reference_queries)
    del encoder
    torch.cuda.empty_cache()
    return {
        "case": case.name,
        "dataset": case.dataset,
        "model": model.model_name,
        "model_revision": model.revision,
        "sample_corpus": len(sample_corpus),
        "sample_queries": len(sample_queries),
        "elapsed_sec": round(elapsed, 3),
        "corpus_comparison": corpus_comparison,
        "query_comparison": query_comparison,
        "pass": bool(corpus_comparison["pass"] and query_comparison["pass"]),
    }


def run_formal_case(
    case: CaseSpec,
    data_dir: Path,
    local_root: Path,
    *,
    force: bool,
) -> dict[str, object]:
    import torch

    model = MODELS[case.model_key]
    case_root = local_root / case.name
    cache_dir = case_root / "embeddings"
    artifact_dir = case_root / "retrieval_artifacts"
    corpus, queries = case_inputs(case, data_dir)
    encoder = load_encoder(model)
    started = time.perf_counter()
    corpus_embeddings, corpus_cache = encode_records(
        corpus,
        encoder,
        case=case,
        model=model,
        record_kind="corpus",
        prefix=model.corpus_prefix,
        cache_dir=cache_dir,
        force=force,
    )
    query_embeddings, query_cache = encode_records(
        queries,
        encoder,
        case=case,
        model=model,
        record_kind="queries",
        prefix=model.query_prefix,
        cache_dir=cache_dir,
        force=force,
    )
    torch.cuda.synchronize()
    encode_elapsed = time.perf_counter() - started
    del encoder
    torch.cuda.empty_cache()

    reference_corpus = load_reference_corpus(case)
    reference_queries = np.load(case.reference_queries, mmap_mode="r", allow_pickle=False)
    corpus_comparison = compare_arrays(corpus_embeddings, reference_corpus)
    query_comparison = compare_arrays(query_embeddings, reference_queries)

    candidate_rankings, ranking_metadata = large_scale_artifacts.load_or_compute_dense_rankings(
        corpus,
        queries,
        corpus_embeddings,
        query_embeddings,
        dataset=case.dataset,
        model_name=model.model_name,
        depth=case.reference_depth,
        cache_dir=artifact_dir,
        batch_size=model.batch_size,
        force=force,
    )
    reference_rankings = load_rankings(case.reference_rankings)
    ranking_comparison = compare_rankings(
        candidate_rankings,
        reference_rankings,
        reference_depth=case.reference_depth,
    )
    order_diagnostics = top10_order_diagnostics(
        corpus,
        queries,
        candidate_rankings,
        reference_rankings,
        corpus_embeddings,
        query_embeddings,
        reference_corpus,
        reference_queries,
    )
    metrics = metric_comparison(queries, candidate_rankings, reference_rankings)
    snapshot_digest, snapshot_files = snapshot_fingerprint(model.snapshot_path)
    total_elapsed = time.perf_counter() - started
    checks = {
        "corpus_embeddings": bool(corpus_comparison["pass"]),
        "query_embeddings": bool(query_comparison["pass"]),
        "top10_rankings": bool(ranking_comparison["pass"]),
        "retrieval_metrics": bool(metrics["pass"]),
    }
    report = {
        "case": case.name,
        "dataset": case.dataset,
        "model": model.model_name,
        "model_revision": model.revision,
        "model_snapshot_fingerprint": snapshot_digest,
        "model_snapshot_files": snapshot_files,
        "query_prefix": model.query_prefix,
        "corpus_prefix": model.corpus_prefix,
        "batch_size": model.batch_size,
        "corpus_count": len(corpus),
        "query_count": len(queries),
        "reference_depth": case.reference_depth,
        "input_fingerprints": {
            "corpus_records": embedding_cache.records_fingerprint(corpus, "corpus"),
            "query_records": embedding_cache.records_fingerprint(queries, "queries"),
        },
        "candidate_fingerprints": {
            "corpus_embeddings": corpus_cache["embedding_content_fingerprint"],
            "query_embeddings": query_cache["embedding_content_fingerprint"],
            "rankings": ranking_metadata["content_fingerprint"],
        },
        "reference_paths": {
            "corpus_embeddings": repo_relative(case.reference_corpus),
            "query_embeddings": repo_relative(case.reference_queries),
            "rankings": repo_relative(case.reference_rankings),
            "corpus_row_indices": repo_relative(case.corpus_row_indices) if case.corpus_row_indices else "",
        },
        "isolated_paths": {
            "corpus_embeddings": repo_relative(Path(corpus_cache["embedding_path"])),
            "query_embeddings": repo_relative(Path(query_cache["embedding_path"])),
            "rankings": repo_relative(Path(ranking_metadata["artifact_path"])),
        },
        "corpus_comparison": corpus_comparison,
        "query_comparison": query_comparison,
        "ranking_comparison": ranking_comparison,
        "top10_order_diagnostics": order_diagnostics,
        "metric_comparison": metrics,
        "timing": {
            "encode_elapsed_sec": round(encode_elapsed, 3),
            "ranking_elapsed_sec": ranking_metadata.get("compute_elapsed_sec"),
            "total_elapsed_sec": round(total_elapsed, 3),
        },
        "checks": checks,
        "pass": all(checks.values()),
    }
    return report


def render_markdown(payload: Mapping[str, object]) -> str:
    lines = [
        "# Task78 GPU Revalidation",
        "",
        f"- Mode: `{payload['mode']}`",
        f"- Status: **{payload['status']}**",
        f"- Git commit: `{payload['git']['commit']}`",
        f"- GPU: `{payload['runtime']['gpu_device']}`",
        f"- PyTorch/HIP: `{payload['runtime']['torch']}` / `{payload['runtime']['torch_hip']}`",
        "",
        "| Case | Corpus cosine min | Query cosine min | Top-10 members | Top-10 order | Metrics exact | Status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for result in payload["cases"]:
        ranking = result.get("ranking_comparison", {})
        metrics = result.get("metric_comparison", {})
        lines.append(
            "| {case} | {corpus:.8f} | {query:.8f} | {members} | {order} | {metrics} | {status} |".format(
                case=result["case"],
                corpus=float(result["corpus_comparison"]["min_cosine_similarity"]),
                query=float(result["query_comparison"]["min_cosine_similarity"]),
                members=(
                    f"{100.0 * float(ranking.get('top10_membership_equal_fraction', 0.0)):.2f}%"
                    if ranking else "n/a"
                ),
                order=(
                    f"{100.0 * float(ranking.get('top10_ordered_equal_fraction', 0.0)):.2f}%"
                    if ranking else "n/a"
                ),
                metrics="yes" if metrics.get("pass") else ("n/a" if not metrics else "no"),
                status="PASS" if result["pass"] else "FAIL",
            )
        )
    lines.extend([
        "",
        "Formal reruns use isolated local caches. They do not overwrite canonical paper artifacts.",
        "",
    ])
    order_differences = sum(len(result.get("top10_order_diagnostics", [])) for result in payload["cases"])
    if order_differences:
        lines.extend([
            f"Ordered top-10 differences investigated: {order_differences}. Membership and metrics remain the acceptance boundary; details are retained in JSON.",
            "",
        ])
    return "\n".join(lines)


def write_report(report_dir: Path, mode: str, payload: Mapping[str, object]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    stem = f"task78_gpu_{mode}"
    payload = portable_tree(payload)
    (report_dir / f"{stem}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (report_dir / f"{stem}.md").write_text(render_markdown(payload), encoding="utf-8")


def parse_cases(value: str) -> list[CaseSpec]:
    names = list(CASES) if value == "all" else [part.strip() for part in value.split(",") if part.strip()]
    unknown = sorted(set(names) - set(CASES))
    if unknown:
        raise ValueError(f"Unknown cases: {unknown}; choices={sorted(CASES)}")
    return [CASES[name] for name in names]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "formal"), required=True)
    parser.add_argument("--cases", default="all", help="Comma-separated case names or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--local-root", type=Path, default=DEFAULT_LOCAL_ROOT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--sample-size", type=int, default=32)
    parser.add_argument("--reuse-existing", action="store_true", help="Reuse isolated Task78 caches")
    args = parser.parse_args(argv)

    if args.sample_size <= 0:
        raise ValueError("--sample-size must be positive")
    selected_cases = parse_cases(args.cases)
    runtime = runtime_info()
    assert_gpu_contract(runtime)
    for case in selected_cases:
        model = MODELS[case.model_key]
        required = [
            args.data_dir / f"{case.dataset}_corpus.json",
            args.data_dir / f"{case.dataset}_queries.json",
            model.snapshot_path,
            case.reference_corpus,
            case.reference_queries,
            case.reference_rankings,
        ]
        if case.corpus_row_indices:
            required.append(case.corpus_row_indices)
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Missing inputs for {case.name}: {missing}")

    results = []
    for index, case in enumerate(selected_cases, start=1):
        print(f"[{index}/{len(selected_cases)}] {args.mode}: {case.name}", flush=True)
        if args.mode == "preflight":
            result = run_preflight_case(case, args.data_dir, args.sample_size)
        else:
            result = run_formal_case(
                case,
                args.data_dir,
                args.local_root,
                force=not args.reuse_existing,
            )
        print(f"[{case.name}] {'PASS' if result['pass'] else 'FAIL'}", flush=True)
        results.append(result)

    passed = all(result["pass"] for result in results)
    payload = {
        "task": "Task78",
        "mode": args.mode,
        "status": "PASS" if passed else "FAIL",
        "git": git_info(),
        "runtime": runtime,
        "cases": results,
    }
    write_report(args.report_dir, args.mode, payload)
    print(json.dumps({"status": payload["status"], "cases": len(results)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
