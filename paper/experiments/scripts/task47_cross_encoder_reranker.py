#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-encoder reranker same-budget baseline for Task47.

This diagnostic baseline starts from a dense candidate pool, reranks each
query-chunk pair with a cross-encoder, and then evaluates both reranked top-k
and same-budget final contexts against dense top-k and IntentWeight budget
artifacts.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


task46 = _load_script_module("task46_sentence_mmr_baseline", SCRIPT_DIR / "task46_sentence_mmr_baseline.py")
context_token_cost = task46.context_token_cost
retrieval_metrics = task46.retrieval_metrics


DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class RerankVariant(NamedTuple):
    run_id: str
    method_label: str
    budget_target_run_id: str
    rankings: Dict[str, List[str]]
    context_tokens: Dict[str, int]
    budget_tokens: Dict[str, int]


def query_id(record: Mapping) -> str:
    return task46.query_id(record)


def chunk_id(record: Mapping) -> str:
    return task46.chunk_id(record)


def parse_seed(run_id: str) -> str:
    match = re.search(r"seed(\d+)", str(run_id))
    return match.group(1) if match else ""


def load_single_variant(raw: str):
    label, path = context_token_cost.parse_ranking_arg(raw)
    variants = context_token_cost.load_ranking_variants(label, path)
    if len(variants) != 1:
        raise ValueError(f"Expected one variant from {raw!r}, got {len(variants)}")
    return variants[0]


def load_target_variants(raw: str, include: str | None):
    label, path = context_token_cost.parse_ranking_arg(raw)
    variants = []
    for variant in context_token_cost.load_ranking_variants(label, path):
        if include and include not in variant.run_id:
            continue
        variants.append(variant)
    if not variants:
        raise ValueError(f"No target variants loaded from {raw!r} include={include!r}")
    return variants


def context_tokens_for_ranking(
    rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
) -> Dict[str, int]:
    return {
        str(qid): int(sum(chunk_tokens.get(str(item), 0) for item in ranking[:top_k]))
        for qid, ranking in rankings.items()
    }


def truncate_rankings(rankings: Mapping[str, Sequence[str]], *, top_k: int) -> Dict[str, List[str]]:
    return {
        str(qid): [str(item) for item in ranking[:top_k]]
        for qid, ranking in rankings.items()
    }


def select_same_budget(
    ranking: Sequence[str],
    chunk_tokens: Mapping[str, int],
    *,
    budget_tokens: int,
    min_keep: int,
) -> List[str]:
    original = [str(item) for item in ranking]
    if not original:
        return []
    safe_prefix = original[: min(min_keep, len(original))]
    selected = list(safe_prefix)
    total = sum(chunk_tokens.get(item, 0) for item in selected)
    budget = max(int(budget_tokens), total)
    for item in original[len(safe_prefix):]:
        item_tokens = chunk_tokens.get(item, 0)
        if total + item_tokens <= budget:
            selected.append(item)
            total += item_tokens
    return selected


def rerank_candidates(
    *,
    queries: Sequence[Mapping],
    candidate_rankings: Mapping[str, Sequence[str]],
    corpus_by_id: Mapping[str, Mapping],
    model_name: str,
    device: str | None,
    local_files_only: bool,
    batch_size: int,
    candidate_depth: int,
    max_length: int | None,
) -> tuple[Dict[str, List[str]], Dict[str, List[Dict[str, object]]], Dict[str, object]]:
    from sentence_transformers import CrossEncoder

    kwargs = {}
    if device:
        kwargs["device"] = device
    if local_files_only:
        kwargs["local_files_only"] = True
    if max_length:
        kwargs["max_length"] = max_length

    start_load = time.perf_counter()
    model = CrossEncoder(model_name, **kwargs)
    load_elapsed = time.perf_counter() - start_load

    pairs: List[tuple[str, str]] = []
    pair_meta: List[tuple[str, str, int]] = []
    for query in queries:
        qid = query_id(query)
        qtext = str(query.get("text", ""))
        for rank, cid in enumerate(candidate_rankings.get(qid, [])[:candidate_depth], start=1):
            chunk = corpus_by_id.get(str(cid))
            if chunk is None:
                continue
            pairs.append((qtext, str(chunk.get("text", ""))))
            pair_meta.append((qid, str(cid), rank))

    start_predict = time.perf_counter()
    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=True)
    predict_elapsed = time.perf_counter() - start_predict
    scores_array = np.asarray(scores, dtype=np.float32)

    scored_by_qid: Dict[str, List[Dict[str, object]]] = {}
    for (qid, cid, dense_rank), score in zip(pair_meta, scores_array):
        scored_by_qid.setdefault(qid, []).append({
            "chunk_id": cid,
            "score": float(score),
            "dense_rank": dense_rank,
        })

    reranked: Dict[str, List[str]] = {}
    for qid, items in scored_by_qid.items():
        ordered = sorted(
            items,
            key=lambda item: (-float(item["score"]), int(item["dense_rank"]), str(item["chunk_id"])),
        )
        reranked[qid] = [str(item["chunk_id"]) for item in ordered]
        scored_by_qid[qid] = ordered

    metadata = {
        "model_name": model_name,
        "device": device or "",
        "local_files_only": local_files_only,
        "batch_size": batch_size,
        "candidate_depth": candidate_depth,
        "max_length": max_length or "",
        "num_pairs": len(pairs),
        "load_elapsed_sec": round(load_elapsed, 3),
        "predict_elapsed_sec": round(predict_elapsed, 3),
    }
    return reranked, scored_by_qid, metadata


def as_context_variant(raw, *, method_label: str, chunk_tokens: Mapping[str, int], top_k: int) -> RerankVariant:
    rankings = truncate_rankings(raw.rankings, top_k=top_k)
    tokens = context_tokens_for_ranking(rankings, chunk_tokens, top_k=top_k)
    return RerankVariant(
        run_id=str(raw.run_id),
        method_label=method_label,
        budget_target_run_id="",
        rankings=rankings,
        context_tokens=tokens,
        budget_tokens=tokens,
    )


def evaluate_variant(
    variant: RerankVariant,
    queries: Sequence[Mapping],
    *,
    ks: Sequence[int],
    k: int,
) -> Dict[str, object]:
    ranking_metrics = retrieval_metrics.evaluate_rankings(
        queries,
        variant.rankings,
        ks=ks,
        skip_empty_gt=True,
    )
    token_values: List[float] = []
    budget_values: List[float] = []
    chunk_values: List[float] = []
    for query in queries:
        if not retrieval_metrics._ground_truth(query):
            continue
        qid = query_id(query)
        token_values.append(float(variant.context_tokens.get(qid, 0)))
        budget_values.append(float(variant.budget_tokens.get(qid, 0)))
        chunk_values.append(float(len(variant.rankings.get(qid, [])[:k])))
    token_mean = float(np.mean(token_values)) if token_values else 0.0
    budget_mean = float(np.mean(budget_values)) if budget_values else 0.0
    return {
        "run_id": variant.run_id,
        "method_label": variant.method_label,
        "budget_target_run_id": variant.budget_target_run_id,
        **ranking_metrics,
        f"avg_context_tokens@{k}": token_mean,
        f"avg_budget_tokens@{k}": budget_mean,
        f"budget_fill_ratio@{k}": token_mean / budget_mean if budget_mean > 0 else 0.0,
        f"avg_context_chunks@{k}": float(np.mean(chunk_values)) if chunk_values else 0.0,
    }


def compare_variant(
    *,
    scale: str,
    queries: Sequence[Mapping],
    baseline: RerankVariant,
    variant: RerankVariant,
    k: int,
    noninferiority_margin: float,
    n_bootstrap: int,
    confidence: float,
    rng: np.random.Generator,
) -> Dict[str, object]:
    baseline_context = task46.ContextVariant(
        baseline.run_id,
        baseline.method_label,
        baseline.budget_target_run_id,
        baseline.rankings,
        baseline.context_tokens,
        baseline.budget_tokens,
        {qid: 0 for qid in baseline.rankings},
        {qid: len(ranking[:k]) for qid, ranking in baseline.rankings.items()},
    )
    variant_context = task46.ContextVariant(
        variant.run_id,
        variant.method_label,
        variant.budget_target_run_id,
        variant.rankings,
        variant.context_tokens,
        variant.budget_tokens,
        {qid: 0 for qid in variant.rankings},
        {qid: len(ranking[:k]) for qid, ranking in variant.rankings.items()},
    )
    return task46.compare_context_variant(
        scale=scale,
        queries=queries,
        baseline=baseline_context,
        variant=variant_context,
        k=k,
        noninferiority_margin=noninferiority_margin,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
        rng=rng,
    )


def add_dense_ratios(rows: List[Dict[str, object]], *, dense_row: Mapping[str, object], k: int) -> None:
    baseline_hit = float(dense_row.get(f"hit@{k}", 0.0))
    baseline_tokens = float(dense_row.get(f"avg_context_tokens@{k}", 0.0))
    for row in rows:
        row[f"hit_delta_vs_dense@{k}"] = float(row.get(f"hit@{k}", 0.0)) - baseline_hit
        tokens = float(row.get(f"avg_context_tokens@{k}", 0.0))
        row[f"context_token_ratio_vs_dense@{k}"] = tokens / baseline_tokens if baseline_tokens > 0 else 0.0
        row[f"context_token_saving_percent_vs_dense@{k}"] = (
            (1.0 - row[f"context_token_ratio_vs_dense@{k}"]) * 100.0
        )


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    preferred = [
        "scale",
        "split",
        "method_label",
        "run_id",
        "budget_target_run_id",
        "seed",
        "num_queries",
        "hit@10",
        "hit_delta_vs_dense@10",
        "evidence_recall@10",
        "mrr@10",
        "ndcg@10",
        "avg_context_tokens@10",
        "avg_budget_tokens@10",
        "budget_fill_ratio@10",
        "context_token_saving_percent_vs_dense@10",
        "avg_context_chunks@10",
    ]
    fieldnames = [key for key in preferred if any(key in row for row in rows)]
    fieldnames.extend(sorted({key for row in rows for key in row if key not in set(fieldnames)}))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    path: Path,
    *,
    scale: str,
    split: str,
    rows: Sequence[Mapping[str, object]],
    paired_rows: Sequence[Mapping[str, object]],
    k: int,
    metadata: Mapping[str, object],
) -> None:
    columns = [
        "method_label",
        "seed",
        "budget_target_run_id",
        f"hit@{k}",
        f"hit_delta_vs_dense@{k}",
        f"evidence_recall@{k}",
        f"avg_context_tokens@{k}",
        f"avg_budget_tokens@{k}",
        f"budget_fill_ratio@{k}",
        f"context_token_saving_percent_vs_dense@{k}",
        f"avg_context_chunks@{k}",
    ]
    paired_columns = [
        "method_label",
        "seed",
        "budget_target_run_id",
        f"method_hit@{k}",
        "hit_delta_mean",
        "hit_delta_ci_low",
        "hit_delta_ci_high",
        "noninferior_by_ci",
        "token_ratio",
        "token_saving_percent",
        "mcnemar_p_two_sided",
    ]
    lines = [
        "# Task47 Cross-Encoder Reranker Same-Budget Baseline",
        "",
        f"- Scale: `{scale}`",
        f"- Evaluation split: `{split}`",
        f"- Cross-encoder: `{metadata.get('model_name')}`",
        f"- Candidate depth: `{metadata.get('candidate_depth')}`",
        f"- Reranked pairs: `{metadata.get('num_pairs')}`",
        f"- Predict elapsed seconds: `{metadata.get('predict_elapsed_sec')}`",
        "",
        "## Summary",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:.4g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Paired Dense Comparison",
        "",
        "| " + " | ".join(paired_columns) + " |",
        "| " + " | ".join("---" for _ in paired_columns) + " |",
    ])
    for row in paired_rows:
        values = []
        for column in paired_columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:.4g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- The cross-encoder reranks dense candidates; it does not retrieve over the full corpus.",
        "- Same-budget rows greedily keep reranked chunks under each target IntentWeight per-query token budget, with a one-chunk safety prefix.",
        "- Token metrics count selected chunk text only; they do not include reranker compute or model prompt tokens.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task47 cross-encoder reranker baseline")
    parser.add_argument("--scale", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--dense-candidates", required=True, help="label=path with dense top-N rankings")
    parser.add_argument("--target-ranking", required=True, help="label=path with IntentWeight budget rankings")
    parser.add_argument("--target-include", default=None)
    parser.add_argument("--model", default=DEFAULT_CROSS_ENCODER)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--candidate-depth", type=int, default=50)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--min-keep", type=int, default=1)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--eval-split", default="test", choices=("all", "calibration", "test"))
    parser.add_argument("--calibration-fraction", type=float, default=0.30)
    parser.add_argument("--split-salt", default="task38_lotte_calibration_v1")
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--noninferiority-margin", type=float, default=0.01)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.candidate_depth <= 0:
        raise ValueError("candidate-depth must be positive")
    if args.top_k <= 0:
        raise ValueError("top-k must be positive")
    if args.min_keep <= 0:
        raise ValueError("min-keep must be positive")
    ks = context_token_cost.parse_ks(args.ks)
    if args.top_k not in ks:
        ks = tuple(sorted({*ks, args.top_k}))

    corpus = context_token_cost.load_json_list(args.corpus)
    all_queries = context_token_cost.load_json_list(args.queries)
    eval_queries, split_metadata = task46.choose_eval_queries(
        all_queries,
        scale=args.scale,
        eval_split=args.eval_split,
        calibration_fraction=args.calibration_fraction,
        split_salt=args.split_salt,
        max_queries=args.max_queries,
    )
    eval_qids = {query_id(query) for query in eval_queries}
    corpus_by_id = {chunk_id(chunk): chunk for chunk in corpus}
    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {chunk_id(chunk): int(count_tokens(str(chunk.get("text", "")))) for chunk in corpus}

    dense_candidates_raw = load_single_variant(args.dense_candidates)
    target_variants_raw = load_target_variants(args.target_ranking, args.target_include)

    reranked, scores_by_qid, metadata = rerank_candidates(
        queries=eval_queries,
        candidate_rankings=dense_candidates_raw.rankings,
        corpus_by_id=corpus_by_id,
        model_name=args.model,
        device=args.device,
        local_files_only=args.local_files_only,
        batch_size=args.batch_size,
        candidate_depth=args.candidate_depth,
        max_length=args.max_length,
    )

    dense_topk = as_context_variant(dense_candidates_raw, method_label="dense_top10", chunk_tokens=chunk_tokens, top_k=args.top_k)
    reranker_topk_rankings = truncate_rankings(reranked, top_k=args.top_k)
    reranker_topk_tokens = context_tokens_for_ranking(reranker_topk_rankings, chunk_tokens, top_k=args.top_k)
    reranker_topk = RerankVariant(
        run_id=f"cross_encoder:{args.model}:top{args.top_k}",
        method_label="reranker_top10",
        budget_target_run_id="",
        rankings=reranker_topk_rankings,
        context_tokens=reranker_topk_tokens,
        budget_tokens=reranker_topk_tokens,
    )

    target_variants = [
        as_context_variant(raw, method_label="intentweight_target", chunk_tokens=chunk_tokens, top_k=args.top_k)
        for raw in target_variants_raw
    ]
    same_budget_variants: List[RerankVariant] = []
    for target in target_variants:
        rankings = {
            qid: select_same_budget(
                reranked.get(qid, []),
                chunk_tokens,
                budget_tokens=int(target.context_tokens.get(qid, 0)),
                min_keep=args.min_keep,
            )
            for qid in eval_qids
        }
        context_tokens = context_tokens_for_ranking(rankings, chunk_tokens, top_k=args.candidate_depth)
        same_budget_variants.append(RerankVariant(
            run_id=f"cross_encoder:{args.model}:same_budget:{target.run_id}",
            method_label="reranker_same_budget",
            budget_target_run_id=target.run_id,
            rankings=rankings,
            context_tokens=context_tokens,
            budget_tokens={qid: int(target.context_tokens.get(qid, 0)) for qid in eval_qids},
        ))

    rows: List[Dict[str, object]] = []
    variants = [dense_topk, reranker_topk, *target_variants, *same_budget_variants]
    for variant in variants:
        row = evaluate_variant(variant, eval_queries, ks=ks, k=args.top_k)
        row.update({
            "scale": args.scale,
            "split": args.eval_split,
            "seed": parse_seed(variant.run_id),
        })
        rows.append(row)
    dense_row = rows[0]
    add_dense_ratios(rows, dense_row=dense_row, k=args.top_k)

    rng = np.random.default_rng(args.seed)
    paired_rows = []
    for variant in variants[1:]:
        paired_row = compare_variant(
            scale=args.scale,
            queries=eval_queries,
            baseline=dense_topk,
            variant=variant,
            k=args.top_k,
            noninferiority_margin=args.noninferiority_margin,
            n_bootstrap=args.bootstrap,
            confidence=args.confidence,
            rng=rng,
        )
        paired_row.update({
            "seed": parse_seed(variant.run_id),
            "budget_target_run_id": variant.budget_target_run_id,
        })
        paired_rows.append(paired_row)

    rows.sort(key=lambda row: (
        str(row.get("method_label", "")),
        str(row.get("seed", "")),
        str(row.get("budget_target_run_id", "")),
    ))

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_prefix.with_suffix(".csv"), rows)
    task46.paired.write_csv(output_prefix.with_suffix(".paired.csv"), paired_rows)
    output_prefix.with_suffix(".json").write_text(json.dumps({
        "config": {
            "scale": args.scale,
            "corpus": str(args.corpus),
            "queries": str(args.queries),
            "dense_candidates": args.dense_candidates,
            "target_ranking": args.target_ranking,
            "target_include": args.target_include,
            "model": args.model,
            "device": args.device,
            "local_files_only": args.local_files_only,
            "batch_size": args.batch_size,
            "candidate_depth": args.candidate_depth,
            "top_k": args.top_k,
            "ks": list(ks),
            "max_length": args.max_length,
            "min_keep": args.min_keep,
            "tokenizer": args.tokenizer,
            "encoding": args.encoding,
            "noninferiority_margin": args.noninferiority_margin,
            "bootstrap": args.bootstrap,
            "confidence": args.confidence,
            "seed": args.seed,
            **split_metadata,
        },
        "reranker_metadata": metadata,
        "rows": rows,
        "paired_rows": paired_rows,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_prefix.with_suffix(".rankings.json").write_text(json.dumps({
        variant.run_id: {
            qid: ranking
            for qid, ranking in variant.rankings.items()
            if qid in eval_qids
        }
        for variant in variants
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    output_prefix.with_suffix(".scores.json").write_text(
        json.dumps(scores_by_qid, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(
        output_prefix.with_suffix(".md"),
        scale=args.scale,
        split=args.eval_split,
        rows=rows,
        paired_rows=paired_rows,
        k=args.top_k,
        metadata=metadata,
    )
    print(f"Summary: {output_prefix.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
