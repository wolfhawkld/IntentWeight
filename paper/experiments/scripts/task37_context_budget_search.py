#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search token-budget final-context policies over saved rankings.

The policies in this script are post-retrieval final context controls. They do
not use ground-truth labels when deciding what to keep. Each query keeps a fixed
prefix for safety, then admits additional chunks only while the final context
stays within a per-query token budget derived from that query's original
top-k context.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, NamedTuple, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")


class PolicyVariant(NamedTuple):
    run_id: str
    source_label: str
    method: str
    seed: str
    policy: str
    rankings: Dict[str, List[str]]


def parse_floats(value: str) -> tuple[float, ...]:
    items = tuple(float(part.strip()) for part in value.split(",") if part.strip())
    if not items or any(item <= 0.0 or item > 1.0 for item in items):
        raise ValueError(f"ratios must be in (0, 1], got {value!r}")
    return items


def parse_ints(value: str) -> tuple[int, ...]:
    items = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if not items or any(item <= 0 for item in items):
        raise ValueError(f"values must be positive integers, got {value!r}")
    return items


def parse_optional_ints(value: str) -> tuple[int, ...]:
    if not value.strip():
        return ()
    return parse_ints(value)


def chunk_id(record: Mapping) -> str:
    return context_token_cost.chunk_id(record)


def query_id(record: Mapping) -> str:
    return context_token_cost.query_id(record)


def token_budget_ranking(
    ranking: Sequence[str],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
    budget_ratio: float,
    min_keep: int,
) -> List[str]:
    original = [str(item) for item in ranking[:top_k]]
    if not original:
        return []
    safe_prefix = original[: min(min_keep, len(original))]
    safe_tokens = sum(chunk_tokens.get(item, 0) for item in safe_prefix)
    original_tokens = sum(chunk_tokens.get(item, 0) for item in original)
    budget = max(safe_tokens, int(math.floor(original_tokens * budget_ratio)))

    selected = list(safe_prefix)
    total = safe_tokens
    for item in original[len(safe_prefix):]:
        item_tokens = chunk_tokens.get(item, 0)
        if total + item_tokens <= budget:
            selected.append(item)
            total += item_tokens
    return selected


def build_policy_variants(
    ranking_variants: Sequence,
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
    budget_ratios: Sequence[float],
    min_keeps: Sequence[int],
    fixed_keeps: Sequence[int],
) -> List[PolicyVariant]:
    policies: List[PolicyVariant] = []
    for variant in ranking_variants:
        for fixed_keep in fixed_keeps:
            policy_name = f"fixed_top{fixed_keep}"
            rankings = {
                str(qid): [str(item) for item in ranking[:fixed_keep]]
                for qid, ranking in variant.rankings.items()
            }
            policies.append(PolicyVariant(
                run_id=f"{variant.run_id}:{policy_name}",
                source_label=variant.source_label,
                method=variant.method,
                seed=variant.seed,
                policy=policy_name,
                rankings=rankings,
            ))
        for ratio in budget_ratios:
            for min_keep in min_keeps:
                policy_name = f"token_budget_r{ratio:.2f}_m{min_keep}"
                rankings = {
                    str(qid): token_budget_ranking(
                        ranking,
                        chunk_tokens,
                        top_k=top_k,
                        budget_ratio=ratio,
                        min_keep=min_keep,
                    )
                    for qid, ranking in variant.rankings.items()
                }
                policies.append(PolicyVariant(
                    run_id=f"{variant.run_id}:{policy_name}",
                    source_label=variant.source_label,
                    method=variant.method,
                    seed=variant.seed,
                    policy=policy_name,
                    rankings=rankings,
                ))
    return policies


def evaluate_policy(
    variant: PolicyVariant,
    queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
    *,
    ks: Sequence[int],
    skip_empty_gt: bool,
) -> Dict[str, object]:
    row = context_token_cost.evaluate_variant(
        context_token_cost.RankingVariant(
            variant.run_id,
            variant.source_label,
            variant.method,
            variant.seed,
            variant.rankings,
        ),
        queries,
        chunk_tokens,
        ks=ks,
        skip_empty_gt=skip_empty_gt,
    )
    row["policy"] = variant.policy
    return row


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    preferred = ["run_id", "source_label", "method", "seed", "policy", "num_queries", "num_skipped_no_gt"]
    fieldnames = [key for key in preferred if any(key in row for row in rows)]
    fieldnames.extend(sorted({key for row in rows for key in row if key not in set(fieldnames)}))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]], *, k: int) -> None:
    columns = [
        "run_id",
        "policy",
        "seed",
        f"hit@{k}",
        f"evidence_recall@{k}",
        f"mrr@{k}",
        f"ndcg@{k}",
        f"avg_context_chunks@{k}",
        f"avg_context_tokens@{k}",
        f"context_token_ratio_vs_baseline@{k}",
        f"hit_delta_vs_baseline@{k}",
    ]
    lines = [
        "# Task37 Context Budget Search",
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
        "- Policies keep a safe prefix and then prune tail chunks by per-query token budget.",
        "- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.",
        "- This is a final-context policy search; it does not claim lower dense embedding compute.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search token-budget final context policies")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--ranking", action="append", required=True, help="label=path, may be repeated")
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--budget-ratios", default="0.95,0.90,0.85,0.80")
    parser.add_argument("--min-keeps", default="5,6,7,8")
    parser.add_argument(
        "--fixed-keeps",
        default="",
        help="Optional comma-separated fixed prefix sizes to evaluate, e.g. 5,6,7,8.",
    )
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--baseline-run-id", required=True)
    parser.add_argument("--include-empty-gt", action="store_true")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-rankings", type=Path, default=None)
    args = parser.parse_args(argv)

    ks = context_token_cost.parse_ks(args.ks)
    budget_ratios = parse_floats(args.budget_ratios)
    min_keeps = parse_ints(args.min_keeps)
    fixed_keeps = parse_optional_ints(args.fixed_keeps)
    corpus = context_token_cost.load_json_list(args.corpus)
    queries = context_token_cost.load_json_list(args.queries)
    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}

    original_rows: List[Dict[str, object]] = []
    policy_variants: List[PolicyVariant] = []
    ranking_dump: Dict[str, Dict[str, List[str]]] = {}
    for raw in args.ranking:
        label, path = context_token_cost.parse_ranking_arg(raw)
        variants = context_token_cost.load_ranking_variants(label, path)
        for variant in variants:
            original_rows.append(context_token_cost.evaluate_variant(
                variant,
                queries,
                chunk_tokens,
                ks=ks,
                skip_empty_gt=not args.include_empty_gt,
            ))
        policy_variants.extend(build_policy_variants(
            variants,
            chunk_tokens,
            top_k=args.top_k,
            budget_ratios=budget_ratios,
            min_keeps=min_keeps,
            fixed_keeps=fixed_keeps,
        ))

    policy_rows = [
        evaluate_policy(
            variant,
            queries,
            chunk_tokens,
            ks=ks,
            skip_empty_gt=not args.include_empty_gt,
        )
        for variant in policy_variants
    ]
    rows = original_rows + policy_rows
    context_token_cost.add_baseline_ratios(rows, args.baseline_run_id, ks)
    rows.sort(key=lambda row: (
        str(row.get("source_label", "")),
        str(row.get("seed", "")),
        float(row.get(f"context_token_ratio_vs_baseline@{max(ks)}", 0.0)),
    ))

    write_csv(args.output_csv, rows)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, rows, k=max(ks))
    if args.output_rankings:
        for variant in policy_variants:
            ranking_dump[variant.run_id] = variant.rankings
        args.output_rankings.parent.mkdir(parents=True, exist_ok=True)
        args.output_rankings.write_text(json.dumps(ranking_dump, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
