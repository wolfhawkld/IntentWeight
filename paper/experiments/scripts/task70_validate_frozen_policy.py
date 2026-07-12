#!/usr/bin/env python3
"""Validate Task70 formal frozen-policy artifacts and protocol invariants."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data" / "processed"
RESULTS = ROOT / "paper" / "experiments" / "results"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


task70 = load_module("task70_validator_source", SCRIPT_DIR / "task70_frozen_policy_generalization.py")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def query_ids(dataset: str) -> set[str]:
    queries = read_json(DATA / f"{dataset}_queries.json")
    return {str(query["query_id"]) for query in queries}


def validate_prefix(prefix: Path) -> dict[str, object]:
    required = [
        prefix.with_suffix(suffix)
        for suffix in (".json", ".folds.csv", ".seeds.csv", ".summary.csv", ".paired.csv", ".paired_summary.csv", ".md")
    ]
    for path in required:
        require(path.exists(), f"missing Task70 artifact: {path}")

    payload = read_json(prefix.with_suffix(".json"))
    protocol = payload["protocol"]
    dataset = str(protocol["dataset"])
    expected_queries = query_ids(dataset)
    seeds = [int(seed) for seed in protocol["route_seeds"]]
    require(protocol["folds"] == 5, f"expected five folds: {prefix}")
    require(protocol["history_epochs"] == 8, f"expected eight history epochs: {prefix}")
    require(seeds == [13, 17, 19], f"unexpected route seeds: {prefix}")
    require(protocol["test_feedback_rule"] == "rank_test_queries_once_with_freeze_updates_true", f"bad freeze rule: {prefix}")
    require(protocol["cluster_retrieval_engine"] == "cached_exact_scores", f"unexpected retrieval engine: {prefix}")
    require(protocol["bootstrap_samples"] == 10_000, f"unexpected bootstrap count: {prefix}")
    require(protocol["paired_comparisons"] == [f"{method}_vs_{baseline}" for method, baseline in task70.PAIRWISE_COMPARISONS], f"unexpected paired comparisons: {prefix}")

    expected_cells = {(fold, method, str(seed)) for fold in range(5) for method in task70.METHODS for seed in seeds}
    rows = payload["fold_rows"]
    actual_cells = {(int(row["fold"]), str(row["method"]), str(row["seed"])) for row in rows}
    require(actual_cells == expected_cells, f"incomplete or duplicate fold/method/seed grid: {prefix}")
    require(all(int(row["test_feedback_updates"]) == 0 for row in rows), f"held-out updates detected: {prefix}")
    require(all(int(row["history_epochs"]) == 8 for row in rows if str(row["method"]).startswith("learned_")), f"wrong learned history epochs: {prefix}")
    require(all(int(row["history_epochs"]) == 0 for row in rows if not str(row["method"]).startswith("learned_")), f"nonlearned methods updated history: {prefix}")

    rankings = payload["rankings"]
    for method in task70.METHODS:
        for seed in seeds:
            require(set(rankings[method][str(seed)]) == expected_queries, f"incomplete rankings for {method} seed={seed}: {prefix}")
    require(set(payload["dense_rankings"]) == expected_queries, f"incomplete Dense rankings: {prefix}")

    paired_rows = payload["paired_rows"]
    expected_pairs = {(method, baseline, str(seed)) for method, baseline in task70.PAIRWISE_COMPARISONS for seed in seeds}
    actual_pairs = {(str(row["method"]), str(row["baseline"]), str(row["seed"])) for row in paired_rows}
    require(actual_pairs == expected_pairs, f"incomplete paired-comparison grid: {prefix}")
    for row in paired_rows:
        require(int(row["queries"]) == len(expected_queries), f"wrong paired query count: {prefix}")
        require(float(row["hit_delta_ci_low"]) <= float(row["hit_delta_mean"]) <= float(row["hit_delta_ci_high"]), f"invalid Hit CI: {prefix}")
        require(0.0 <= float(row["mcnemar_p_two_sided"]) <= 1.0, f"invalid McNemar p-value: {prefix}")

    seed_rows = payload["seed_rows"]
    summary_rows = {str(row["method"]): row for row in payload["summary_rows"]}
    for method in task70.METHODS:
        values = [float(row["hit@10"]) for row in seed_rows if str(row["method"]) == method]
        require(len(values) == len(seeds), f"missing seed summary for {method}: {prefix}")
        summary = summary_rows[method]
        require(math.isclose(float(summary["hit@10_mean"]), mean(values), rel_tol=0.0, abs_tol=1e-12), f"Hit mean mismatch for {method}: {prefix}")
        require(math.isclose(float(summary["hit@10_std"]), pstdev(values), rel_tol=0.0, abs_tol=1e-12), f"Hit SD mismatch for {method}: {prefix}")

    checkpoints = prefix.parent / f"{prefix.name}.checkpoints"
    checkpoint_files = sorted(checkpoints.glob("fold*.json"))
    require(len(checkpoint_files) == 5, f"expected five fold checkpoints: {prefix}")
    for path in checkpoint_files:
        checkpoint = read_json(path)
        require(checkpoint.get("complete") is True, f"incomplete checkpoint: {path}")
        require(checkpoint.get("signature", {}).get("history_epochs") == 8, f"bad checkpoint signature: {path}")

    return {
        "dataset": dataset,
        "prefix": str(prefix.relative_to(ROOT)),
        "queries": len(expected_queries),
        "fold_method_seed_cells": len(actual_cells),
        "paired_rows": len(paired_rows),
        "checks": 16,
        "status": "pass",
    }


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task70 Formal Artifact Validation",
        "",
        "| Dataset | Queries | Fold-method-seed cells | Paired rows | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f"| {row['dataset']} | {row['queries']} | {row['fold_method_seed_cells']} | {row['paired_rows']} | {row['status']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", action="append", required=True, type=Path)
    parser.add_argument("--output-prefix", type=Path, default=RESULTS / "task70_formal_validation")
    args = parser.parse_args()
    prefixes = [path if path.is_absolute() else (ROOT / path).resolve() for path in args.prefix]
    output = args.output_prefix if args.output_prefix.is_absolute() else (ROOT / args.output_prefix).resolve()
    rows = [validate_prefix(prefix) for prefix in prefixes]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(output.with_suffix(".md"), rows)
    print(json.dumps(rows, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
