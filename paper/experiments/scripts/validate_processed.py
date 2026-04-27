#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processed dataset validation script for IntentWeight paper experiments.

Checks paired files in paper/experiments/data/processed:
- {dataset}_corpus.json
- {dataset}_queries.json

Validation criteria:
- both files exist and contain JSON lists
- corpus chunks > 0 and query count > 0
- every corpus chunk has a unique chunk_id
- every ground_truth_chunk_id referenced by queries exists in corpus
- report GT coverage and missing references

Usage:
    python paper/experiments/scripts/validate_processed.py --dataset emanual
    python paper/experiments/scripts/validate_processed.py --dataset all
"""
import argparse
import json
import os
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
DEFAULT_DATASETS = ["pubmedqa", "banking77", "emanual", "cuad"]


def _load_json_list(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def validate_dataset(dataset: str) -> Dict[str, Any]:
    """Validate one processed dataset and return a summary dictionary."""
    corpus_path = os.path.join(PROCESSED_DIR, f"{dataset}_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, f"{dataset}_queries.json")
    errors: List[str] = []

    if not os.path.exists(corpus_path):
        errors.append(f"missing_file: {corpus_path}")
    if not os.path.exists(queries_path):
        errors.append(f"missing_file: {queries_path}")

    if errors:
        return {
            "dataset": dataset,
            "valid": False,
            "corpus_chunks": 0,
            "queries": 0,
            "queries_with_gt": 0,
            "gt_coverage": 0.0,
            "missing_gt_chunk_refs": 0,
            "duplicate_chunk_ids": 0,
            "errors": errors,
        }

    try:
        corpus = _load_json_list(corpus_path)
        queries = _load_json_list(queries_path)
    except Exception as exc:
        return {
            "dataset": dataset,
            "valid": False,
            "corpus_chunks": 0,
            "queries": 0,
            "queries_with_gt": 0,
            "gt_coverage": 0.0,
            "missing_gt_chunk_refs": 0,
            "duplicate_chunk_ids": 0,
            "errors": [f"json_load_error: {exc}"],
        }

    chunk_ids = []
    missing_chunk_id_count = 0
    empty_text_count = 0
    for item in corpus:
        chunk_id = item.get("chunk_id") if isinstance(item, dict) else None
        text = item.get("text") if isinstance(item, dict) else None
        if not chunk_id:
            missing_chunk_id_count += 1
        else:
            chunk_ids.append(str(chunk_id))
        if text is None or str(text).strip() == "":
            empty_text_count += 1

    chunk_id_set = set(chunk_ids)
    duplicate_chunk_ids = len(chunk_ids) - len(chunk_id_set)

    queries_with_gt = 0
    missing_gt_refs = 0
    empty_query_text_count = 0
    for query in queries:
        if not isinstance(query, dict):
            empty_query_text_count += 1
            continue
        if str(query.get("text", "")).strip() == "":
            empty_query_text_count += 1
        gt_ids = [str(x) for x in _as_list(query.get("ground_truth_chunk_ids"))]
        if gt_ids:
            queries_with_gt += 1
        missing_gt_refs += sum(1 for chunk_id in gt_ids if chunk_id not in chunk_id_set)

    if len(corpus) == 0:
        errors.append("corpus_chunks=0")
    if len(queries) == 0:
        errors.append("queries=0")
    if missing_chunk_id_count:
        errors.append(f"missing_chunk_id_count={missing_chunk_id_count}")
    if duplicate_chunk_ids:
        errors.append(f"duplicate_chunk_ids={duplicate_chunk_ids}")
    if empty_text_count:
        errors.append(f"empty_chunk_text_count={empty_text_count}")
    if empty_query_text_count:
        errors.append(f"empty_query_text_count={empty_query_text_count}")
    if missing_gt_refs:
        errors.append(f"missing_gt_chunk_refs={missing_gt_refs}")

    gt_coverage = queries_with_gt / len(queries) if queries else 0.0
    return {
        "dataset": dataset,
        "valid": len(errors) == 0,
        "corpus_chunks": len(corpus),
        "queries": len(queries),
        "queries_with_gt": queries_with_gt,
        "gt_coverage": gt_coverage,
        "missing_gt_chunk_refs": missing_gt_refs,
        "duplicate_chunk_ids": duplicate_chunk_ids,
        "errors": errors,
    }


def discover_datasets() -> List[str]:
    """Discover datasets with *_corpus.json files in PROCESSED_DIR."""
    if not os.path.isdir(PROCESSED_DIR):
        return []
    datasets = []
    for filename in sorted(os.listdir(PROCESSED_DIR)):
        if filename.endswith("_corpus.json"):
            datasets.append(filename[: -len("_corpus.json")])
    return datasets


def print_summary(summaries: Iterable[Dict[str, Any]]) -> bool:
    """Print validation results. Return True only if all summaries are valid."""
    summaries = list(summaries)
    print("=" * 80)
    print("Processed dataset validation")
    print("=" * 80)

    all_valid = True
    for summary in summaries:
        all_valid = all_valid and bool(summary["valid"])
        status = "OK" if summary["valid"] else "FAIL"
        print(
            f"[{status}] {summary['dataset']}: "
            f"corpus={summary['corpus_chunks']} "
            f"queries={summary['queries']} "
            f"queries_with_gt={summary['queries_with_gt']} "
            f"gt_coverage={_format_percent(summary['gt_coverage'])} "
            f"missing_gt_refs={summary['missing_gt_chunk_refs']} "
            f"duplicate_chunks={summary['duplicate_chunk_ids']}"
        )
        for error in summary["errors"]:
            print(f"  - {error}")

    print("=" * 80)
    print("ALL VALID" if all_valid else "VALIDATION FAILED")
    return all_valid


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate processed RAG experiment datasets")
    parser.add_argument(
        "--dataset",
        default="all",
        help="Dataset name, comma-separated names, or 'all' (default: all)",
    )
    args = parser.parse_args()

    if args.dataset == "all":
        datasets = discover_datasets() or DEFAULT_DATASETS
    else:
        datasets = [name.strip() for name in args.dataset.split(",") if name.strip()]

    summaries = [validate_dataset(dataset) for dataset in datasets]
    return 0 if print_summary(summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
