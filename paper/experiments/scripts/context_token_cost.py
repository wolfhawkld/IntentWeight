#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate final RAG context token cost from saved retrieval rankings.

This script measures the tokens that would be placed into the final top-k
context, not the retrieval-stage source candidate count used by earlier tasks.
It accepts flat ranking files, such as dense baselines, and nested ranking files,
such as cost-aware LinUCB outputs with method -> seed -> query rankings.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
from pathlib import Path
from statistics import mean, median
from typing import Dict, Iterable, List, Mapping, NamedTuple, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_KS = (1, 5, 10)


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retrieval_metrics = _load_script_module("retrieval_metrics", SCRIPT_DIR / "retrieval_metrics.py")


class RankingVariant(NamedTuple):
    run_id: str
    source_label: str
    method: str
    seed: str
    rankings: Dict[str, List[str]]


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return data


def chunk_id(record: Mapping) -> str:
    value = record.get("chunk_id") or record.get("id")
    if value is None:
        raise ValueError(f"Corpus record missing chunk_id/id: {record}")
    return str(value)


def query_id(record: Mapping) -> str:
    value = record.get("query_id") or record.get("id")
    if value is None:
        raise ValueError(f"Query record missing query_id/id: {record}")
    return str(value)


def parse_ks(value: str) -> tuple[int, ...]:
    ks = tuple(sorted({int(part.strip()) for part in value.split(",") if part.strip()}))
    if not ks or any(k <= 0 for k in ks):
        raise ValueError(f"ks must contain positive integers, got {value!r}")
    return ks


def parse_ranking_arg(value: str) -> tuple[str, Path]:
    if "=" in value:
        label, raw_path = value.split("=", 1)
        label = label.strip()
        if not label:
            raise ValueError(f"Ranking label is empty: {value!r}")
        return label, Path(raw_path)
    path = Path(value)
    return path.stem, path


def _is_ranking_list(value: object) -> bool:
    return isinstance(value, list) and all(not isinstance(item, (dict, list)) for item in value)


def _coerce_rankings(value: Mapping) -> Dict[str, List[str]]:
    return {str(qid): [str(chunk_id) for chunk_id in ranking] for qid, ranking in value.items()}


def load_ranking_variants(label: str, path: Path) -> List[RankingVariant]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Ranking file must contain a JSON object: {path}")

    if all(_is_ranking_list(value) for value in data.values()):
        return [RankingVariant(label, label, label, "", _coerce_rankings(data))]

    variants: List[RankingVariant] = []
    for method, method_value in data.items():
        if not isinstance(method_value, dict):
            raise ValueError(f"Unsupported ranking object under {method!r} in {path}")
        if all(_is_ranking_list(value) for value in method_value.values()):
            run_id = f"{label}:{method}"
            variants.append(RankingVariant(run_id, label, str(method), "", _coerce_rankings(method_value)))
            continue
        for seed, seed_value in method_value.items():
            if not isinstance(seed_value, dict) or not all(_is_ranking_list(value) for value in seed_value.values()):
                raise ValueError(f"Unsupported ranking object under {method!r}/{seed!r} in {path}")
            run_id = f"{label}:{method}:seed{seed}"
            variants.append(RankingVariant(run_id, label, str(method), str(seed), _coerce_rankings(seed_value)))
    return variants


def build_token_counter(tokenizer: str, encoding_name: str):
    if tokenizer == "simple":
        pattern = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)

        def simple_count(text: str) -> int:
            return len(pattern.findall(text))

        return simple_count

    if tokenizer != "tiktoken":
        raise ValueError(f"Unsupported tokenizer: {tokenizer}")
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError("tiktoken is not installed; use --tokenizer simple") from exc
    encoding = tiktoken.get_encoding(encoding_name)
    return lambda text: len(encoding.encode(text or ""))


def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    if q < 0 or q > 1:
        raise ValueError(f"percentile q must be in [0, 1], got {q}")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lower = int(pos)
    upper = min(lower + 1, len(ordered) - 1)
    weight = pos - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def context_token_metrics(
    queries: Sequence[Mapping],
    rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    ks: Sequence[int],
    skip_empty_gt: bool = True,
) -> Dict[str, float]:
    ks = tuple(sorted({int(k) for k in ks}))
    token_values: Dict[int, List[float]] = {k: [] for k in ks}
    missing_values: Dict[int, List[float]] = {k: [] for k in ks}
    chunk_count_values: Dict[int, List[float]] = {k: [] for k in ks}

    for query in queries:
        gt = retrieval_metrics._ground_truth(query)
        if not gt and skip_empty_gt:
            continue
        ranking = [str(item) for item in rankings.get(query_id(query), [])]
        for k in ks:
            top_ids = ranking[:k]
            token_values[k].append(float(sum(chunk_tokens.get(item, 0) for item in top_ids)))
            missing_values[k].append(float(sum(1 for item in top_ids if item not in chunk_tokens)))
            chunk_count_values[k].append(float(sum(1 for item in top_ids if item in chunk_tokens)))

    metrics: Dict[str, float] = {}
    for k in ks:
        tokens = token_values[k]
        missing = missing_values[k]
        chunk_counts = chunk_count_values[k]
        metrics[f"avg_context_tokens@{k}"] = float(mean(tokens)) if tokens else 0.0
        metrics[f"median_context_tokens@{k}"] = float(median(tokens)) if tokens else 0.0
        metrics[f"p95_context_tokens@{k}"] = percentile(tokens, 0.95)
        metrics[f"max_context_tokens@{k}"] = float(max(tokens)) if tokens else 0.0
        metrics[f"avg_context_chunks@{k}"] = float(mean(chunk_counts)) if chunk_counts else 0.0
        metrics[f"avg_missing_chunks@{k}"] = float(mean(missing)) if missing else 0.0
    return metrics


def evaluate_variant(
    variant: RankingVariant,
    queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
    *,
    ks: Sequence[int],
    skip_empty_gt: bool,
) -> Dict[str, object]:
    ranking_metrics = retrieval_metrics.evaluate_rankings(
        queries,
        variant.rankings,
        ks=ks,
        skip_empty_gt=skip_empty_gt,
    )
    token_metrics = context_token_metrics(
        queries,
        variant.rankings,
        chunk_tokens,
        ks=ks,
        skip_empty_gt=skip_empty_gt,
    )
    return {
        "run_id": variant.run_id,
        "source_label": variant.source_label,
        "method": variant.method,
        "seed": variant.seed,
        **ranking_metrics,
        **token_metrics,
    }


def add_baseline_ratios(rows: List[Dict[str, object]], baseline_run_id: str, ks: Sequence[int]) -> None:
    baseline = next((row for row in rows if row["run_id"] == baseline_run_id), None)
    if baseline is None:
        raise ValueError(f"Baseline run_id not found: {baseline_run_id}")
    for row in rows:
        for k in ks:
            baseline_tokens = float(baseline.get(f"avg_context_tokens@{k}", 0.0))
            current_tokens = float(row.get(f"avg_context_tokens@{k}", 0.0))
            row[f"context_token_ratio_vs_baseline@{k}"] = (
                current_tokens / baseline_tokens if baseline_tokens > 0 else 0.0
            )
            row[f"context_token_delta_vs_baseline@{k}"] = current_tokens - baseline_tokens
            baseline_hit = float(baseline.get(f"hit@{k}", 0.0))
            row[f"hit_delta_vs_baseline@{k}"] = float(row.get(f"hit@{k}", 0.0)) - baseline_hit


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fieldnames = []
    for preferred in ("run_id", "source_label", "method", "seed", "num_queries", "num_skipped_no_gt"):
        if any(preferred in row for row in rows):
            fieldnames.append(preferred)
    remaining = sorted({key for row in rows for key in row if key not in set(fieldnames)})
    fieldnames.extend(remaining)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]], *, ks: Sequence[int]) -> None:
    if not rows:
        return
    k = max(ks)
    columns = [
        "run_id",
        "seed",
        f"hit@{k}",
        f"evidence_recall@{k}",
        f"mrr@{k}",
        f"ndcg@{k}",
        f"avg_context_tokens@{k}",
        f"median_context_tokens@{k}",
        f"p95_context_tokens@{k}",
        f"context_token_ratio_vs_baseline@{k}",
        f"hit_delta_vs_baseline@{k}",
    ]
    lines = [
        "# Final Context Token Cost",
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
        "- Token metrics count final top-k retrieved chunk text only.",
        "- They do not include system prompt, instructions, generated output, or reranker internals.",
        "- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate final context token cost for saved rankings")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--ranking", action="append", required=True, help="label=path, may be repeated")
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--baseline-run-id", default=None)
    parser.add_argument("--include-empty-gt", action="store_true")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args(argv)

    ks = parse_ks(args.ks)
    corpus = load_json_list(args.corpus)
    queries = load_json_list(args.queries)
    count_tokens = build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}

    rows: List[Dict[str, object]] = []
    for raw in args.ranking:
        label, path = parse_ranking_arg(raw)
        for variant in load_ranking_variants(label, path):
            rows.append(evaluate_variant(
                variant,
                queries,
                chunk_tokens,
                ks=ks,
                skip_empty_gt=not args.include_empty_gt,
            ))

    if args.baseline_run_id:
        add_baseline_ratios(rows, args.baseline_run_id, ks)

    write_csv(args.output_csv, rows)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, rows, ks=ks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
