#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill final context-token metrics for historical Task16-25 artifacts.

Task28 corrected the cost interpretation for a focused set of LoTTE 100k runs.
This script extends that correction across saved historical rankings without
rerunning retrieval experiments. It keeps source-candidate cost as a separate
retrieval-stage proxy and recomputes final retrieved context tokens from the
saved final rankings.
"""
from __future__ import annotations

import argparse
import csv
import gc
import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List, Mapping, NamedTuple, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_KS = (1, 5, 10)


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")


class RankingSpec(NamedTuple):
    task: str
    label: str
    dataset: str
    ranking_path: Path
    metrics_path: Path | None


def parse_ks(value: str) -> tuple[int, ...]:
    return context_token_cost.parse_ks(value)


def _dataset_from_rankings_filename(path: Path) -> str | None:
    match = re.search(r"linucb_cost_(.+?)_(?:heldout|sample|full|smoke)-", path.name)
    if not match:
        return None
    dataset = match.group(1).replace("-", "_")
    return dataset


def _task_from_path(path: Path) -> str:
    parent = path.parent.name
    if parent.startswith("task"):
        return parent
    name = path.name
    dataset = _dataset_from_rankings_filename(path) or "unknown"
    if dataset in {"pubmedqa", "banking77", "emanual", "cuad"}:
        return "task16"
    if dataset in {"lotte_technology_search", "lotte_technology_search_100k"}:
        return "task18"
    return "historical"


def _label_from_path(path: Path) -> str:
    parent = path.parent.name
    if parent.startswith("task"):
        return parent
    return path.stem.replace("_prequential_rankings", "")


def discover_specs(results_dir: Path, data_dir: Path) -> List[RankingSpec]:
    allowed_parent_prefixes = (
        "task19_",
        "task20_",
        "task22_",
        "task24_",
        "task25_",
    )
    excluded_parent_prefixes = (
        "task26_",
        "task27_",
        "task28_",
        "task29_",
    )
    specs: List[RankingSpec] = []
    seen: set[Path] = set()
    for path in sorted(results_dir.rglob("linucb_cost_*_prequential_rankings.json")):
        if any(part.startswith(excluded_parent_prefixes) for part in path.parts):
            continue
        parent = path.parent.name
        is_root_history = path.parent == results_dir
        is_allowed_task = parent.startswith(allowed_parent_prefixes)
        if not (is_root_history or is_allowed_task):
            continue
        dataset = _dataset_from_rankings_filename(path)
        if not dataset:
            continue
        corpus_path = data_dir / f"{dataset}_corpus.json"
        queries_path = data_dir / f"{dataset}_queries.json"
        if not corpus_path.exists() or not queries_path.exists():
            continue
        metrics_path = path.with_name(path.name.replace("_prequential_rankings.json", "_prequential_metrics.json"))
        specs.append(RankingSpec(
            task=_task_from_path(path),
            label=_label_from_path(path),
            dataset=dataset,
            ranking_path=path,
            metrics_path=metrics_path if metrics_path.exists() else None,
        ))
        seen.add(path)
    return specs


def dense_ranking_path(dataset: str, results_dir: Path) -> Path | None:
    candidates = [
        results_dir / f"dense_{dataset}_rankings.json",
        results_dir / "task22_3c_lotte_400k" / f"dense_{dataset}_rankings.json",
        results_dir / "task22_7_lotte_638k_dense" / f"dense_{dataset}_rankings.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def load_metrics_index(path: Path | None) -> Dict[tuple[str, str], Mapping]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    rows = data if isinstance(data, list) else [data]
    index: Dict[tuple[str, str], Mapping] = {}
    for row in rows:
        routing_mode = str(row.get("routing_mode", row.get("method", "")))
        index[(routing_mode, "")] = row
        for seed_row in row.get("per_seed", []) or []:
            seed = str(seed_row.get("seed", ""))
            index[(routing_mode, seed)] = {**row, **seed_row}
    return index


def add_source_cost_metadata(row: Dict[str, object], metrics_index: Mapping[tuple[str, str], Mapping]) -> None:
    metrics = metrics_index.get((str(row.get("method", "")), str(row.get("seed", ""))))
    if metrics is None:
        metrics = metrics_index.get((str(row.get("method", "")), ""))
    if metrics is None:
        return
    for key in (
        "avg_source_candidate_cost",
        "avg_source_candidate_cost_mean",
        "dense_query_rate",
        "dense_query_rate_mean",
        "dense_saved_rate",
        "dense_saved_rate_mean",
        "avg_dense_candidates",
        "avg_dense_candidates_mean",
        "avg_bm25_candidates",
        "avg_bm25_candidates_mean",
        "avg_cluster_candidates",
        "avg_cluster_candidates_mean",
        "routing_mode",
        "reward_attribution",
        "confidence_mode",
        "final_context_policy",
    ):
        if key in metrics:
            row[key] = metrics[key]


def evaluate_dataset_group(
    dataset: str,
    specs: Sequence[RankingSpec],
    *,
    data_dir: Path,
    results_dir: Path,
    ks: Sequence[int],
    tokenizer: str,
    encoding: str,
) -> List[Dict[str, object]]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    dense_path = dense_ranking_path(dataset, results_dir)
    if dense_path is None:
        raise FileNotFoundError(f"Dense ranking baseline not found for {dataset}")

    corpus = context_token_cost.load_json_list(corpus_path)
    queries = context_token_cost.load_json_list(queries_path)
    count_tokens = context_token_cost.build_token_counter(tokenizer, encoding)
    chunk_tokens = {
        context_token_cost.chunk_id(chunk): count_tokens(str(chunk.get("text", "")))
        for chunk in corpus
    }

    rows: List[Dict[str, object]] = []
    dense_variant = context_token_cost.load_ranking_variants(f"{dataset}:dense", dense_path)[0]
    dense_row = context_token_cost.evaluate_variant(
        dense_variant,
        queries,
        chunk_tokens,
        ks=ks,
        skip_empty_gt=True,
    )
    dense_row.update({
        "task": "baseline",
        "dataset": dataset,
        "ranking_path": str(dense_path),
        "metrics_path": "",
        "cost_interpretation": "final_context_tokens",
    })
    rows.append(dense_row)

    for spec in specs:
        metrics_index = load_metrics_index(spec.metrics_path)
        for variant in context_token_cost.load_ranking_variants(spec.label, spec.ranking_path):
            row = context_token_cost.evaluate_variant(
                variant,
                queries,
                chunk_tokens,
                ks=ks,
                skip_empty_gt=True,
            )
            row.update({
                "task": spec.task,
                "dataset": dataset,
                "ranking_path": str(spec.ranking_path),
                "metrics_path": str(spec.metrics_path or ""),
                "cost_interpretation": "source_candidate_proxy_and_final_context_tokens",
            })
            add_source_cost_metadata(row, metrics_index)
            rows.append(row)

    context_token_cost.add_baseline_ratios(rows, dense_row["run_id"], ks)
    del corpus, queries, chunk_tokens
    gc.collect()
    return rows


def aggregate_rows(rows: Sequence[Mapping[str, object]], *, ks: Sequence[int]) -> List[Dict[str, object]]:
    k = max(ks)
    groups: Dict[tuple[str, str, str, str], List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(
            str(row.get("dataset", "")),
            str(row.get("task", "")),
            str(row.get("source_label", "")),
            str(row.get("method", "")),
        )].append(row)
    aggregated: List[Dict[str, object]] = []
    numeric_keys = [
        f"hit@{k}",
        f"evidence_recall@{k}",
        f"mrr@{k}",
        f"ndcg@{k}",
        f"avg_context_tokens@{k}",
        f"context_token_ratio_vs_baseline@{k}",
        f"hit_delta_vs_baseline@{k}",
        "avg_source_candidate_cost",
        "avg_source_candidate_cost_mean",
        "dense_query_rate",
        "dense_query_rate_mean",
        "dense_saved_rate",
        "dense_saved_rate_mean",
    ]
    for (dataset, task, source_label, method), group_rows in sorted(groups.items()):
        out: Dict[str, object] = {
            "dataset": dataset,
            "task": task,
            "source_label": source_label,
            "method": method,
            "runs": len(group_rows),
        }
        for key in numeric_keys:
            values = [float(row[key]) for row in group_rows if key in row and row[key] not in ("", None)]
            if not values:
                continue
            out[f"{key}_mean"] = mean(values)
            out[f"{key}_std"] = stdev(values) if len(values) > 1 else 0.0
        ratio_key = f"context_token_ratio_vs_baseline@{k}_mean"
        if ratio_key in out:
            out[f"context_token_saving_pct@{k}"] = (1.0 - float(out[ratio_key])) * 100.0
        aggregated.append(out)
    return aggregated


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]], *, ks: Sequence[int]) -> None:
    k = max(ks)
    columns = [
        "dataset",
        "task",
        "source_label",
        "method",
        "runs",
        f"hit@{k}_mean",
        f"avg_context_tokens@{k}_mean",
        f"context_token_ratio_vs_baseline@{k}_mean",
        f"context_token_saving_pct@{k}",
        f"hit_delta_vs_baseline@{k}_mean",
        "avg_source_candidate_cost_mean_mean",
        "dense_query_rate_mean_mean",
    ]
    lines = [
        "# Task28.1 Historical Context Token Backfill",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:.4f}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- `avg_source_candidate_cost*` columns are retrieval-stage candidate-count proxies.",
        "- `avg_context_tokens@k` columns are final retrieved context token measurements.",
        "- Token metrics count retrieved chunk text only, not prompts, generated output, or reranker internals.",
        "- Dense-only rankings are included as the baseline for each dataset/scale.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    context_token_cost.write_csv(path, rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill final context token metrics for historical runs")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--datasets", default="", help="Optional comma-separated dataset filter")
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_RESULTS_DIR / "task28_1_context_token_backfill.csv")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_RESULTS_DIR / "task28_1_context_token_backfill.json")
    parser.add_argument(
        "--output-aggregated-csv",
        type=Path,
        default=DEFAULT_RESULTS_DIR / "task28_1_context_token_backfill_aggregated.csv",
    )
    parser.add_argument("--output-md", type=Path, default=DEFAULT_RESULTS_DIR / "task28_1_context_token_backfill.md")
    args = parser.parse_args(argv)

    ks = parse_ks(args.ks)
    requested = {part.strip() for part in args.datasets.split(",") if part.strip()}
    specs = discover_specs(args.results_dir, args.data_dir)
    by_dataset: Dict[str, List[RankingSpec]] = defaultdict(list)
    for spec in specs:
        if requested and spec.dataset not in requested:
            continue
        by_dataset[spec.dataset].append(spec)

    all_rows: List[Dict[str, object]] = []
    for dataset in sorted(by_dataset):
        print(f"Backfilling final context tokens: {dataset} ({len(by_dataset[dataset])} ranking files)")
        all_rows.extend(evaluate_dataset_group(
            dataset,
            by_dataset[dataset],
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            ks=ks,
            tokenizer=args.tokenizer,
            encoding=args.encoding,
        ))

    aggregated = aggregate_rows(all_rows, ks=ks)
    write_csv(args.output_csv, all_rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(all_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(args.output_aggregated_csv, aggregated)
    write_markdown(args.output_md, aggregated, ks=ks)
    print(f"Wrote {len(all_rows)} per-run rows: {args.output_csv}")
    print(f"Wrote {len(aggregated)} aggregate rows: {args.output_aggregated_csv}")
    print(f"Markdown: {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
