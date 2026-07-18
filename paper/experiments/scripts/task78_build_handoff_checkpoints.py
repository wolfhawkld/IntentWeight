#!/usr/bin/env python3
"""Build hardware-independent Task78 MiniLM handoff checkpoints on ROCm."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DEFAULT_DATA_DIR = EXPERIMENT_DIR / "data" / "processed"
DEFAULT_OUTPUT_ROOT = EXPERIMENT_DIR / "data" / "task78_handoff"
DEFAULT_REPORT_DIR = EXPERIMENT_DIR / "results" / "task78_gpu_revalidation"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


embedding_cache = load_module("task78_handoff_embedding_cache", SCRIPT_DIR / "embedding_cache.py")
scale_store = load_module("task78_handoff_scale_store", SCRIPT_DIR / "lotte_scale_store.py")
artifacts = load_module("task78_handoff_artifacts", SCRIPT_DIR / "large_scale_artifacts.py")
gpu_audit = load_module("task78_gpu_audit", SCRIPT_DIR / "task78_gpu_revalidation.py")

MODEL = gpu_audit.MODELS["minilm"]
TECHNOLOGY_SCALES = (
    "lotte_technology_search_100k",
    "lotte_technology_search_200k",
    "lotte_technology_search_400k",
    "lotte_technology_search_638k",
)
REFERENCE_100K_CORPUS = (
    EXPERIMENT_DIR
    / "data/task78_revalidation/task47_minilm_technology_100k/embeddings"
    / "lotte_technology_search_100k__sentence-transformers-all-MiniLM-L6-v2__corpus__n101311__60ef5529c079a71e.npy"
)
REFERENCE_638K_RANKINGS = (
    EXPERIMENT_DIR
    / "results/task22_7_lotte_638k_dense/dense_lotte_technology_search_638k_rankings.json"
)


def load_json_list(path: Path) -> list[Mapping]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def membership_boundary_diagnostics(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    candidate_rankings: Mapping[str, Sequence[str]],
    reference_rankings: Mapping[str, Sequence[str]],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    score_tolerance: float,
) -> list[dict[str, object]]:
    corpus_index = {
        str(record.get("chunk_id") or record.get("id")): index
        for index, record in enumerate(corpus)
    }
    corpus_by_id = {
        str(record.get("chunk_id") or record.get("id")): record
        for record in corpus
    }
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
        if set(candidate_top10) == set(reference_top10):
            continue
        changed_ids = sorted(set(candidate_top10) ^ set(reference_top10))
        query_row = query_index[query_id]
        scores = []
        changed_chunks = []
        for chunk_id in changed_ids:
            corpus_row = corpus_index[chunk_id]
            score = float(corpus_embeddings[corpus_row] @ query_embeddings[query_row])
            scores.append(score)
            record = corpus_by_id[chunk_id]
            text = str(record.get("text", ""))
            changed_chunks.append({
                "chunk_id": chunk_id,
                "candidate_position": candidate_top10.index(chunk_id) + 1 if chunk_id in candidate_top10 else None,
                "reference_position": reference_top10.index(chunk_id) + 1 if chunk_id in reference_top10 else None,
                "candidate_embedding_score": score,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text_preview": text[:240],
            })
        ground_truth = {
            str(chunk_id) for chunk_id in query_by_id[query_id].get("ground_truth_chunk_ids", [])
        }
        score_span = max(scores) - min(scores) if scores else float("inf")
        changed_ground_truth = sorted(ground_truth.intersection(changed_ids))
        diagnostics.append({
            "query_id": query_id,
            "query_text": str(query_by_id[query_id].get("text", "")),
            "candidate_top10": candidate_top10,
            "reference_top10": reference_top10,
            "changed_chunks": changed_chunks,
            "changed_ground_truth_chunk_ids": changed_ground_truth,
            "candidate_score_span": score_span,
            "score_tolerance": score_tolerance,
            "numerical_non_gt_boundary": score_span <= score_tolerance and not changed_ground_truth,
        })
    return diagnostics


def write_report(report_dir: Path, payload: Mapping[str, object]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = gpu_audit.portable_tree(payload)
    json_path = report_dir / "task78_technology_scale_store.json"
    md_path = report_dir / "task78_technology_scale_store.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    comparison = payload["comparisons"]
    ranking = comparison["rankings_638k"]
    metrics = comparison["metrics_638k"]
    md_path.write_text(
        "\n".join([
            "# Task78 Technology Scale-Store Handoff",
            "",
            f"- Status: **{payload['status']}**",
            f"- Model revision: `{payload['model_revision']}`",
            f"- Canonical rows: {payload['canonical_count']:,}",
            f"- 100k minimum cosine vs formal rerun: {comparison['embeddings_100k']['min_cosine_similarity']:.8f}",
            f"- 638k top-10 member equality: {100.0 * ranking['top10_membership_equal_fraction']:.2f}%",
            f"- 638k top-10 ordered equality: {100.0 * ranking['top10_ordered_equal_fraction']:.2f}%",
            f"- Published retrieval metrics exact: {'yes' if metrics['pass'] else 'no'}",
            f"- Investigated numerical member boundaries: {len(comparison['membership_boundary_diagnostics'])}",
            "",
            "All arrays and rankings are stored under the ignored Task78 handoff root.",
            "",
        ]),
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--corpus-batch-size", type=int, default=256)
    parser.add_argument("--query-batch-size", type=int, default=16)
    parser.add_argument("--ranking-batch-size", type=int, default=16)
    parser.add_argument("--encode-chunk-size", type=int, default=10000)
    parser.add_argument("--force-queries", action="store_true")
    parser.add_argument("--force-ranking", action="store_true")
    args = parser.parse_args(argv)

    runtime = gpu_audit.runtime_info()
    gpu_audit.assert_gpu_contract(runtime)
    required = [
        MODEL.snapshot_path,
        REFERENCE_100K_CORPUS,
        REFERENCE_638K_RANKINGS,
        *(args.data_dir / f"{dataset}_{kind}.json" for dataset in TECHNOLOGY_SCALES for kind in ("corpus", "queries")),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Task78 handoff inputs: {missing}")

    from sentence_transformers import SentenceTransformer
    import torch

    encoder = SentenceTransformer(str(MODEL.snapshot_path), device="cuda", local_files_only=True)
    store_dir = args.output_root / "scale_store" / "lotte_technology_search"
    query_cache_dir = args.output_root / "embeddings"
    artifact_dir = args.output_root / "retrieval_artifacts"
    scale_summaries = []
    started = time.perf_counter()
    for index, dataset in enumerate(TECHNOLOGY_SCALES, start=1):
        manifest_path = store_dir / f"{dataset}__manifest.json"
        if args.reuse_existing and manifest_path.exists():
            summary = json.loads((store_dir / "store_summary.json").read_text(encoding="utf-8"))
            print(f"[{index}/{len(TECHNOLOGY_SCALES)}] reuse {dataset}", flush=True)
        else:
            print(f"[{index}/{len(TECHNOLOGY_SCALES)}] append {dataset}", flush=True)
            summary = scale_store.append_scale_store_streaming(
                dataset,
                canonical_name="lotte_technology_search",
                model_name=MODEL.model_name,
                model_revision=MODEL.revision,
                data_dir=args.data_dir,
                store_dir=store_dir,
                encoder=encoder,
                batch_size=args.corpus_batch_size,
                encode_chunk_size=args.encode_chunk_size,
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        scale_summaries.append({
            key: manifest[key]
            for key in (
                "dataset",
                "corpus_count",
                "query_count",
                "canonical_row_count",
                "new_canonical_rows",
                "reused_canonical_rows",
                "encoded_missing_rows",
                "model_name",
                "model_revision",
            )
        })

        queries = load_json_list(args.data_dir / f"{dataset}_queries.json")
        embedding_cache.load_or_compute_embeddings(
            queries,
            dataset=dataset,
            model_name=MODEL.model_name,
            model_revision=MODEL.revision,
            record_kind="queries",
            encoder=encoder,
            batch_size=args.query_batch_size,
            cache_dir=query_cache_dir,
            force=args.force_queries or not args.reuse_existing,
        )
    torch.cuda.synchronize()
    build_elapsed = time.perf_counter() - started
    del encoder
    torch.cuda.empty_cache()

    canonical = np.load(store_dir / "canonical_corpus_embeddings.npy", mmap_mode="r", allow_pickle=False)
    rows_100k = np.load(
        store_dir / "lotte_technology_search_100k__row_indices.npy",
        mmap_mode="r",
        allow_pickle=False,
    )
    reference_100k = np.load(REFERENCE_100K_CORPUS, mmap_mode="r", allow_pickle=False)
    embeddings_100k = gpu_audit.compare_arrays(canonical[rows_100k], reference_100k)

    dataset_638k = TECHNOLOGY_SCALES[-1]
    corpus_638k = load_json_list(args.data_dir / f"{dataset_638k}_corpus.json")
    queries_638k = load_json_list(args.data_dir / f"{dataset_638k}_queries.json")
    rows_638k = np.load(
        store_dir / f"{dataset_638k}__row_indices.npy",
        mmap_mode="r",
        allow_pickle=False,
    )
    corpus_embeddings_638k = canonical[rows_638k]
    query_fingerprint = embedding_cache.records_fingerprint(queries_638k, "queries")
    query_path, _ = embedding_cache.cache_paths(
        query_cache_dir,
        dataset=dataset_638k,
        model_name=MODEL.model_name,
        record_kind="queries",
        fingerprint=query_fingerprint,
        count=len(queries_638k),
    )
    query_embeddings_638k = np.load(query_path, mmap_mode="r", allow_pickle=False)
    candidate_rankings, ranking_metadata = artifacts.load_or_compute_dense_rankings(
        corpus_638k,
        queries_638k,
        corpus_embeddings_638k,
        query_embeddings_638k,
        dataset=dataset_638k,
        model_name=MODEL.model_name,
        depth=10,
        cache_dir=artifact_dir,
        batch_size=args.ranking_batch_size,
        force=args.force_ranking or not args.reuse_existing,
    )
    reference_rankings = gpu_audit.load_rankings(REFERENCE_638K_RANKINGS)
    rankings_638k = gpu_audit.compare_rankings(
        candidate_rankings,
        reference_rankings,
        reference_depth=10,
    )
    metrics_638k = gpu_audit.metric_comparison(
        queries_638k,
        candidate_rankings,
        reference_rankings,
    )
    membership_diagnostics = membership_boundary_diagnostics(
        corpus_638k,
        queries_638k,
        candidate_rankings,
        reference_rankings,
        corpus_embeddings_638k,
        query_embeddings_638k,
        score_tolerance=1e-6,
    )
    numerical_boundary_pass = bool(membership_diagnostics) and all(
        item["numerical_non_gt_boundary"] for item in membership_diagnostics
    )
    canonical_metadata = json.loads(
        (store_dir / "canonical_metadata.json").read_text(encoding="utf-8")
    )
    checks = {
        "embedding_equivalence_100k": bool(embeddings_100k["pass"]),
        "ranking_equivalence_638k": bool(rankings_638k["pass"] or numerical_boundary_pass),
        "strict_ranking_membership_equivalence_638k": bool(rankings_638k["pass"]),
        "metric_equivalence_638k": bool(metrics_638k["pass"]),
        "all_scale_manifests": all(
            (store_dir / f"{dataset}__manifest.json").exists() for dataset in TECHNOLOGY_SCALES
        ),
        "model_revision": canonical_metadata.get("model_revision") == MODEL.revision,
    }
    required_checks = {
        key: value
        for key, value in checks.items()
        if key != "strict_ranking_membership_equivalence_638k"
    }
    passed = all(required_checks.values())
    status = (
        "PASS"
        if passed and checks["strict_ranking_membership_equivalence_638k"]
        else "PASS_WITH_NUMERICAL_BOUNDARY"
        if passed
        else "FAIL"
    )
    payload = {
        "task": "Task78",
        "status": status,
        "model": MODEL.model_name,
        "model_revision": MODEL.revision,
        "runtime": runtime,
        "store_dir": repo_relative(store_dir),
        "canonical_count": int(canonical.shape[0]),
        "canonical_shape": list(canonical.shape),
        "canonical_embedding_fingerprint": canonical_metadata.get("embedding_content_fingerprint"),
        "scale_summaries": scale_summaries,
        "comparisons": {
            "embeddings_100k": embeddings_100k,
            "rankings_638k": rankings_638k,
            "metrics_638k": metrics_638k,
            "membership_boundary_diagnostics": membership_diagnostics,
        },
        "ranking_artifact": repo_relative(Path(ranking_metadata["artifact_path"])),
        "build_elapsed_sec": round(build_elapsed, 3),
        "batch_contract": {
            "corpus_encoding": args.corpus_batch_size,
            "query_encoding": args.query_batch_size,
            "dense_ranking": args.ranking_batch_size,
        },
        "checks": checks,
    }
    write_report(args.report_dir, payload)
    print(json.dumps({"status": payload["status"], "checks": checks}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
