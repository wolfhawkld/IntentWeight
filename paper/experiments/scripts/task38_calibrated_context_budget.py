#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibration/test protocol for Task37 context-budget policies.

Task37 selected a strong token-budget operating point after inspecting the main
LoTTE test results. This script addresses that model-selection concern by
splitting the query stream deterministically into calibration and test queries:

1. select the final-context budget policy only on calibration queries;
2. freeze the selected policy;
3. report paired dense-vs-method tests only on held-out test queries.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")
task37_budget = _load_script_module("task37_context_budget_search", SCRIPT_DIR / "task37_context_budget_search.py")
paired = _load_script_module("task37_paired_significance", SCRIPT_DIR / "task37_paired_significance.py")


class CalibrationChoice(NamedTuple):
    policy: str
    eligible: bool
    mean_hit_delta: float
    mean_token_saving_percent: float
    mean_token_ratio: float
    mean_hit: float
    mean_baseline_hit: float
    num_seed_rows: int


def query_id(record: Mapping) -> str:
    return context_token_cost.query_id(record)


def chunk_id(record: Mapping) -> str:
    return context_token_cost.chunk_id(record)


def parse_seed(run_id: str, seed: str | int | None) -> str:
    if seed is not None and str(seed):
        return str(seed)
    match = re.search(r"seed(\d+)", str(run_id))
    return match.group(1) if match else ""


def split_queries(
    queries: Sequence[Mapping],
    *,
    calibration_fraction: float,
    salt: str,
) -> tuple[List[Mapping], List[Mapping]]:
    if calibration_fraction <= 0.0 or calibration_fraction >= 1.0:
        raise ValueError(f"calibration_fraction must be in (0,1), got {calibration_fraction}")

    scored = []
    for query in queries:
        qid = query_id(query)
        digest = hashlib.sha256(f"{salt}:{qid}".encode("utf-8")).hexdigest()
        scored.append((int(digest, 16), query))
    scored.sort(key=lambda item: item[0])
    split_at = max(1, min(len(scored) - 1, int(round(len(scored) * calibration_fraction))))
    calibration = [query for _, query in scored[:split_at]]
    test = [query for _, query in scored[split_at:]]
    return calibration, test


def load_single_baseline(label: str, path: Path):
    variants = context_token_cost.load_ranking_variants(label, path)
    if len(variants) != 1:
        raise ValueError(f"Expected one baseline variant in {path}, got {len(variants)}")
    return variants[0]


def load_method_variants(label: str, path: Path, include: str | None):
    variants = []
    for variant in context_token_cost.load_ranking_variants(label, path):
        if include and include not in variant.run_id:
            continue
        variants.append(variant)
    if not variants:
        raise ValueError(f"No method variants matched include={include!r} in {path}")
    return variants


def evaluate_rows(
    variants: Sequence,
    queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
    *,
    ks: Sequence[int],
) -> List[Dict[str, object]]:
    rows = []
    for variant in variants:
        row = context_token_cost.evaluate_variant(
            variant,
            queries,
            chunk_tokens,
            ks=ks,
            skip_empty_gt=True,
        )
        if hasattr(variant, "policy"):
            row["policy"] = variant.policy
        rows.append(row)
    return rows


def add_dense_deltas(
    rows: List[Dict[str, object]],
    *,
    baseline_hit: float,
    baseline_tokens: float,
    k: int,
) -> None:
    for row in rows:
        row[f"hit_delta_vs_dense@{k}"] = float(row.get(f"hit@{k}", 0.0)) - baseline_hit
        tokens = float(row.get(f"avg_context_tokens@{k}", 0.0))
        row[f"context_token_ratio_vs_dense@{k}"] = tokens / baseline_tokens if baseline_tokens > 0 else 0.0
        row[f"context_token_saving_percent_vs_dense@{k}"] = (
            (1.0 - row[f"context_token_ratio_vs_dense@{k}"]) * 100.0
        )


def choose_policy(
    rows: Sequence[Mapping[str, object]],
    *,
    margin: float,
    k: int,
) -> CalibrationChoice:
    by_policy: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        policy = str(row.get("policy", ""))
        if policy:
            by_policy[policy].append(row)

    choices: List[CalibrationChoice] = []
    for policy, policy_rows in by_policy.items():
        hit_delta = mean(float(row.get(f"hit_delta_vs_dense@{k}", 0.0)) for row in policy_rows)
        saving = mean(float(row.get(f"context_token_saving_percent_vs_dense@{k}", 0.0)) for row in policy_rows)
        ratio = mean(float(row.get(f"context_token_ratio_vs_dense@{k}", 0.0)) for row in policy_rows)
        hit = mean(float(row.get(f"hit@{k}", 0.0)) for row in policy_rows)
        baseline_hit = mean(float(row.get(f"hit@{k}", 0.0)) - float(row.get(f"hit_delta_vs_dense@{k}", 0.0)) for row in policy_rows)
        choices.append(CalibrationChoice(
            policy=policy,
            eligible=hit_delta >= -margin,
            mean_hit_delta=hit_delta,
            mean_token_saving_percent=saving,
            mean_token_ratio=ratio,
            mean_hit=hit,
            mean_baseline_hit=baseline_hit,
            num_seed_rows=len(policy_rows),
        ))

    eligible = [choice for choice in choices if choice.eligible]
    if eligible:
        return sorted(
            eligible,
            key=lambda choice: (
                choice.mean_token_saving_percent,
                choice.mean_hit_delta,
                -choice.mean_token_ratio,
            ),
            reverse=True,
        )[0]
    return sorted(
        choices,
        key=lambda choice: (
            choice.mean_hit_delta,
            choice.mean_token_saving_percent,
        ),
        reverse=True,
    )[0]


def as_paired_variant(label: str, variant) -> object:
    return paired.Variant(
        label=label,
        run_id=str(variant.run_id),
        seed=parse_seed(str(variant.run_id), getattr(variant, "seed", "")),
        rankings=variant.rankings,
    )


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fieldnames = []
    preferred = [
        "scale",
        "split",
        "source_label",
        "run_id",
        "policy",
        "seed",
        "num_queries",
        "hit@10",
        "hit_delta_vs_dense@10",
        "context_token_ratio_vs_dense@10",
        "context_token_saving_percent_vs_dense@10",
    ]
    for key in preferred:
        if any(key in row for row in rows):
            fieldnames.append(key)
    fieldnames.extend(sorted({key for row in rows for key in row if key not in set(fieldnames)}))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary_md(
    path: Path,
    *,
    scale: str,
    calibration_count: int,
    test_count: int,
    choice: CalibrationChoice,
    calibration_rows: Sequence[Mapping[str, object]],
    test_paired_rows: Sequence[Mapping[str, object]],
    selection_hit_margin: float,
    k: int,
) -> None:
    lines = [
        "# Task38 Calibrated Context Budget",
        "",
        f"- Scale: `{scale}`",
        f"- Calibration queries: `{calibration_count}`",
        f"- Frozen test queries: `{test_count}`",
        f"- Selected policy: `{choice.policy}`",
        f"- Selection hit margin: `{selection_hit_margin:.4f}`",
        f"- Selection eligible: `{choice.eligible}`",
        "",
        "## Calibration Selection",
        "",
        "| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    by_policy = defaultdict(list)
    for row in calibration_rows:
        if row.get("policy"):
            by_policy[str(row["policy"])].append(row)
    policy_summaries = []
    for policy, rows in by_policy.items():
        hit_delta = mean(float(row.get(f"hit_delta_vs_dense@{k}", 0.0)) for row in rows)
        saving = mean(float(row.get(f"context_token_saving_percent_vs_dense@{k}", 0.0)) for row in rows)
        ratio = mean(float(row.get(f"context_token_ratio_vs_dense@{k}", 0.0)) for row in rows)
        policy_summaries.append((policy, hit_delta >= -selection_hit_margin, hit_delta, saving, ratio, len(rows)))
    for policy, eligible, hit_delta, saving, ratio, count in sorted(policy_summaries, key=lambda item: item[3], reverse=True):
        lines.append(f"| {policy} | {eligible} | {hit_delta:.4f} | {saving:.2f} | {ratio:.4f} | {count} |")

    lines.extend([
        "",
        "## Frozen Test Paired Results",
        "",
        "| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for row in test_paired_rows:
        lines.append(
            "| {method_label} | {seed} | {hit:.4f} | {delta:.4f} | {lo:.4f} | {hi:.4f} | {ni} | {ratio:.4f} | {saving:.2f} | {mcnemar:.4g} | {nonworse:.4f} |".format(
                method_label=row.get("method_label", ""),
                seed=row.get("seed", ""),
                hit=float(row.get("method_hit@10", 0.0)),
                delta=float(row.get("hit_delta_mean", 0.0)),
                lo=float(row.get("hit_delta_ci_low", 0.0)),
                hi=float(row.get("hit_delta_ci_high", 0.0)),
                ni=row.get("noninferior_by_ci", ""),
                ratio=float(row.get("token_ratio", 0.0)),
                saving=float(row.get("token_saving_percent", 0.0)),
                mcnemar=float(row.get("mcnemar_p_two_sided", 1.0)),
                nonworse=float(row.get("token_down_nonworse_rate", 0.0)),
            )
        )

    lines.extend([
        "",
        "## Notes",
        "",
        "- Policy selection uses only calibration queries.",
        "- Frozen test evaluation is paired by query against dense top-10.",
        "- Token saving is final LLM evidence-context input token saving.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate and test Task37 context-budget policy")
    parser.add_argument("--scale", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--baseline", required=True, help="label=path")
    parser.add_argument("--method", required=True, help="label=path")
    parser.add_argument("--include", default=None)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--budget-ratios", default="0.98,0.95,0.92,0.90,0.88,0.85")
    parser.add_argument("--min-keeps", default="4,5,6,7,8")
    parser.add_argument("--dense-fixed-keeps", default="8,9")
    parser.add_argument("--calibration-fraction", type=float, default=0.30)
    parser.add_argument("--split-salt", default="task38_lotte_calibration_v1")
    parser.add_argument(
        "--selection-hit-margin",
        type=float,
        default=0.0,
        help="Calibration selection allows mean Hit@k delta >= -margin. Default 0 requires no observed mean hit drop.",
    )
    parser.add_argument("--noninferiority-margin", type=float, default=0.01)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args(argv)

    ks = context_token_cost.parse_ks(args.ks)
    budget_ratios = task37_budget.parse_floats(args.budget_ratios)
    min_keeps = task37_budget.parse_ints(args.min_keeps)
    dense_fixed_keeps = task37_budget.parse_optional_ints(args.dense_fixed_keeps)

    baseline_label, baseline_path = context_token_cost.parse_ranking_arg(args.baseline)
    method_label, method_path = context_token_cost.parse_ranking_arg(args.method)
    baseline_variant = load_single_baseline(baseline_label, baseline_path)
    method_variants = load_method_variants(method_label, method_path, args.include)

    corpus = context_token_cost.load_json_list(args.corpus)
    queries = context_token_cost.load_json_list(args.queries)
    calibration_queries, test_queries = split_queries(
        queries,
        calibration_fraction=args.calibration_fraction,
        salt=f"{args.split_salt}:{args.scale}",
    )

    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}

    calibration_baseline = evaluate_rows([baseline_variant], calibration_queries, chunk_tokens, ks=ks)[0]
    baseline_hit = float(calibration_baseline.get(f"hit@{args.k}", 0.0))
    baseline_tokens = float(calibration_baseline.get(f"avg_context_tokens@{args.k}", 0.0))

    method_policies = task37_budget.build_policy_variants(
        method_variants,
        chunk_tokens,
        top_k=args.top_k,
        budget_ratios=budget_ratios,
        min_keeps=min_keeps,
        fixed_keeps=(),
    )
    calibration_rows = evaluate_rows(method_policies, calibration_queries, chunk_tokens, ks=ks)
    add_dense_deltas(calibration_rows, baseline_hit=baseline_hit, baseline_tokens=baseline_tokens, k=args.k)
    for row in calibration_rows:
        row["scale"] = args.scale
        row["split"] = "calibration"

    choice = choose_policy(calibration_rows, margin=args.selection_hit_margin, k=args.k)
    selected_method = [variant for variant in method_policies if variant.policy == choice.policy]
    if not selected_method:
        raise RuntimeError(f"Selected policy not found: {choice.policy}")

    dense_policies = task37_budget.build_policy_variants(
        [baseline_variant],
        chunk_tokens,
        top_k=args.top_k,
        budget_ratios=budget_ratios,
        min_keeps=min_keeps,
        fixed_keeps=dense_fixed_keeps,
    )
    selected_dense = [variant for variant in dense_policies if variant.policy == choice.policy]
    dense_topk = [variant for variant in dense_policies if variant.policy in {f"fixed_top{keep}" for keep in dense_fixed_keeps}]

    paired_baseline = as_paired_variant(baseline_label, baseline_variant)
    rng = np.random.default_rng(args.seed)
    test_paired_rows: List[Dict[str, object]] = []
    for label, variants in [
        ("dense_adaptive", selected_dense),
        ("dense_fixed", dense_topk),
        ("task38", selected_method),
    ]:
        for variant in variants:
            test_paired_rows.append(paired.compare_variant(
                scale=args.scale,
                queries=test_queries,
                baseline=paired_baseline,
                variant=as_paired_variant(label, variant),
                chunk_tokens=chunk_tokens,
                k=args.k,
                noninferiority_margin=args.noninferiority_margin,
                n_bootstrap=args.bootstrap,
                confidence=args.confidence,
                rng=rng,
            ))

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_prefix.with_suffix(".calibration.csv"), calibration_rows)
    paired.write_csv(output_prefix.with_suffix(".test_paired.csv"), test_paired_rows)
    output_prefix.with_suffix(".json").write_text(json.dumps({
        "scale": args.scale,
        "split_salt": args.split_salt,
        "calibration_fraction": args.calibration_fraction,
        "calibration_query_count": len(calibration_queries),
        "test_query_count": len(test_queries),
        "selected_policy": choice._asdict(),
        "selection_hit_margin": args.selection_hit_margin,
        "noninferiority_margin": args.noninferiority_margin,
        "calibration_rows": calibration_rows,
        "test_paired_rows": test_paired_rows,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_prefix.with_suffix(".rankings.json").write_text(json.dumps({
        variant.run_id: variant.rankings
        for variant in selected_method + selected_dense + dense_topk
    }, ensure_ascii=False), encoding="utf-8")
    write_summary_md(
        output_prefix.with_suffix(".md"),
        scale=args.scale,
        calibration_count=len(calibration_queries),
        test_count=len(test_queries),
        choice=choice,
        calibration_rows=calibration_rows,
        test_paired_rows=test_paired_rows,
        selection_hit_margin=args.selection_hit_margin,
        k=args.k,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
