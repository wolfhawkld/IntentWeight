#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compressor-normalized Dense vs IntentWeight comparison for Task48.

This script applies the same sentence-level MMR final-context compressor to
multiple evidence pools. It is intended to separate retrieval/controller quality
from generic final-context compression:

    Dense top-k evidence pool -> SentMMR
    IntentWeight evidence pool -> SentMMR
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
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
dense_baseline = task46.dense_baseline
paired = task46.paired


class BaseMethod(NamedTuple):
    variant: task46.ContextVariant
    source_group: str
    compressor: str
    budget_ratio: float | None


def parse_floats(value: str) -> tuple[float, ...]:
    items = tuple(float(part.strip()) for part in value.split(",") if part.strip())
    if not items or any(item <= 0.0 or item > 1.0 for item in items):
        raise ValueError(f"ratios must be in (0,1], got {value!r}")
    return items


def query_id(record: Mapping) -> str:
    return task46.query_id(record)


def chunk_id(record: Mapping) -> str:
    return task46.chunk_id(record)


def load_variants(raw: str, include: str | None = None) -> List:
    label, path = context_token_cost.parse_ranking_arg(raw)
    variants = []
    for variant in context_token_cost.load_ranking_variants(label, path):
        if include and include not in variant.run_id:
            continue
        variants.append(variant)
    if not variants:
        raise ValueError(f"No variants loaded from {raw!r} with include={include!r}")
    return variants


def context_tokens_for_variant(
    rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
) -> Dict[str, int]:
    return task46.context_tokens_for_ranking(rankings, chunk_tokens, top_k=top_k)


def make_base_variant(
    raw_variant,
    *,
    source_group: str,
    method_label: str,
    chunk_tokens: Mapping[str, int],
    top_k: int,
) -> BaseMethod:
    support_rankings = {
        str(qid): [str(item) for item in ranking[:top_k]]
        for qid, ranking in raw_variant.rankings.items()
    }
    context_tokens = context_tokens_for_variant(support_rankings, chunk_tokens, top_k=top_k)
    return BaseMethod(
        variant=task46.ContextVariant(
            run_id=str(raw_variant.run_id),
            method_label=method_label,
            budget_target_run_id="",
            support_rankings=support_rankings,
            context_tokens=context_tokens,
            budget_tokens=context_tokens,
            sentence_counts=task46.sentence_count_zeros(support_rankings),
            supported_chunk_counts=task46.supported_chunk_counts(support_rankings, top_k=top_k),
        ),
        source_group=source_group,
        compressor="none",
        budget_ratio=None,
    )


def collect_unique_sentence_texts_for_bases(
    bases: Sequence[BaseMethod],
    queries: Sequence[Mapping],
    corpus_by_id: Mapping[str, Mapping],
    *,
    count_tokens,
    top_k: int,
    max_sentence_tokens: int,
) -> List[str]:
    seen: Dict[str, None] = {}
    for base in bases:
        sentence_texts = task46.collect_unique_sentence_texts(
            queries,
            base.variant.support_rankings,
            corpus_by_id,
            count_tokens=count_tokens,
            top_k=top_k,
            max_sentence_tokens=max_sentence_tokens,
        )
        for text in sentence_texts:
            seen.setdefault(text, None)
    return list(seen)


def build_candidates_for_base(
    base: BaseMethod,
    queries: Sequence[Mapping],
    corpus_by_id: Mapping[str, Mapping],
    sentence_text_to_index: Mapping[str, int],
    *,
    count_tokens,
    top_k: int,
    max_sentence_tokens: int,
) -> Dict[str, List[task46.CandidateSentence]]:
    return task46.build_candidates(
        queries,
        base.variant.support_rankings,
        corpus_by_id,
        sentence_text_to_index,
        count_tokens=count_tokens,
        top_k=top_k,
        max_sentence_tokens=max_sentence_tokens,
    )


def compress_base_variant(
    base: BaseMethod,
    *,
    ratio: float,
    queries: Sequence[Mapping],
    candidates_by_qid: Mapping[str, Sequence[task46.CandidateSentence]],
    query_embeddings_by_qid: Mapping[str, np.ndarray],
    sentence_embeddings: np.ndarray,
    mmr_lambda: float,
) -> BaseMethod:
    support_rankings: Dict[str, List[str]] = {}
    context_tokens: Dict[str, int] = {}
    budget_tokens: Dict[str, int] = {}
    sentence_counts: Dict[str, int] = {}
    supported_counts: Dict[str, int] = {}

    for query in queries:
        qid = query_id(query)
        budget = int(math.floor(float(base.variant.context_tokens.get(qid, 0)) * ratio))
        budget_tokens[qid] = budget
        selected = task46.select_mmr_sentences(
            candidates_by_qid.get(qid, []),
            query_embeddings_by_qid[qid],
            sentence_embeddings,
            budget_tokens=budget,
            mmr_lambda=mmr_lambda,
        )
        support_rankings[qid] = task46.dedupe_chunk_ranking(selected)
        context_tokens[qid] = int(sum(sentence.token_count for sentence in selected))
        sentence_counts[qid] = len(selected)
        supported_counts[qid] = len(set(support_rankings[qid]))

    run_id = f"{base.variant.run_id}:sent_mmr_r{ratio:.2f}_l{mmr_lambda:.2f}"
    return BaseMethod(
        variant=task46.ContextVariant(
            run_id=run_id,
            method_label=f"{base.variant.method_label}_sent_mmr",
            budget_target_run_id=base.variant.run_id,
            support_rankings=support_rankings,
            context_tokens=context_tokens,
            budget_tokens=budget_tokens,
            sentence_counts=sentence_counts,
            supported_chunk_counts=supported_counts,
        ),
        source_group=base.source_group,
        compressor="sent_mmr",
        budget_ratio=ratio,
    )


def add_source_ratios(rows: List[Dict[str, object]], *, k: int) -> None:
    source_rows = {
        str(row["run_id"]): row
        for row in rows
        if row.get("compressor") == "none"
    }
    for row in rows:
        source_run_id = str(row.get("source_run_id") or row.get("run_id"))
        source = source_rows.get(source_run_id)
        if source is None:
            continue
        source_hit = float(source.get(f"hit@{k}", 0.0))
        source_tokens = float(source.get(f"avg_context_tokens@{k}", 0.0))
        current_hit = float(row.get(f"hit@{k}", 0.0))
        current_tokens = float(row.get(f"avg_context_tokens@{k}", 0.0))
        row[f"hit_delta_vs_source@{k}"] = current_hit - source_hit
        row[f"context_token_ratio_vs_source@{k}"] = current_tokens / source_tokens if source_tokens > 0 else 0.0
        row[f"context_token_saving_percent_vs_source@{k}"] = (
            (1.0 - row[f"context_token_ratio_vs_source@{k}"]) * 100.0
        )


def write_rows_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    preferred = [
        "scale",
        "split",
        "source_group",
        "compressor",
        "budget_ratio",
        "method_label",
        "run_id",
        "source_run_id",
        "num_queries",
        "hit@10",
        "hit_delta_vs_dense@10",
        "hit_delta_vs_source@10",
        "evidence_recall@10",
        "avg_context_tokens@10",
        "context_token_saving_percent_vs_dense@10",
        "context_token_saving_percent_vs_source@10",
        "avg_selected_sentences@10",
        "avg_supported_chunks@10",
    ]
    fieldnames = [key for key in preferred if any(key in row for row in rows)]
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
    split: str,
    rows: Sequence[Mapping[str, object]],
    paired_rows: Sequence[Mapping[str, object]],
    k: int,
    config: Mapping[str, object],
) -> None:
    columns = [
        "source_group",
        "compressor",
        "budget_ratio",
        f"hit@{k}",
        f"hit_delta_vs_dense@{k}",
        f"hit_delta_vs_source@{k}",
        f"evidence_recall@{k}",
        f"avg_context_tokens@{k}",
        f"context_token_saving_percent_vs_dense@{k}",
        f"context_token_saving_percent_vs_source@{k}",
        f"avg_selected_sentences@{k}",
        f"avg_supported_chunks@{k}",
    ]
    paired_columns = [
        "comparison",
        "method_label",
        "source_group",
        "budget_ratio",
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
        "# Task48 Compressor-Normalized Comparison",
        "",
        f"- Scale: `{scale}`",
        f"- Evaluation split: `{split}`",
        f"- Dense candidate depth: `{config.get('top_k')}`",
        f"- Budget ratios: `{config.get('budget_ratios')}`",
        f"- MMR lambda: `{float(config.get('mmr_lambda', 0.0)):.2f}`",
        f"- Sentence unit cap: `{config.get('max_sentence_tokens')}` tokens",
        "",
        "## Main Table",
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
        "## Paired Comparisons",
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
        "- The same sentence-level MMR compressor is applied after each evidence pool is produced.",
        "- `vs_source` compares a compressed row against its own uncompressed evidence pool.",
        "- `vs_dense` compares every row against uncompressed dense top-10.",
        "- Hit and evidence-recall metrics remain chunk-support proxies; they do not prove sentence-level answer sufficiency.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task48 compressor-normalized comparison")
    parser.add_argument("--scale", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--dense-ranking", required=True, help="label=path")
    parser.add_argument("--intent-ranking", required=True, help="label=path")
    parser.add_argument("--intent-include", default=None)
    parser.add_argument("--budget-ratios", default="0.95,0.90,0.85")
    parser.add_argument("--model", default=task46.DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--mmr-lambda", type=float, default=0.70)
    parser.add_argument("--max-sentence-tokens", type=int, default=128)
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

    ks = context_token_cost.parse_ks(args.ks)
    if args.k not in ks:
        ks = tuple(sorted({*ks, args.k}))
    ratios = parse_floats(args.budget_ratios)

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

    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    corpus_by_id = {chunk_id(chunk): chunk for chunk in corpus}
    chunk_tokens = {chunk_id(chunk): int(count_tokens(str(chunk.get("text", "")))) for chunk in corpus}

    dense_variants = load_variants(args.dense_ranking)
    if len(dense_variants) != 1:
        raise ValueError(f"Expected one dense variant, got {len(dense_variants)}")
    intent_variants = load_variants(args.intent_ranking, include=args.intent_include)

    bases: List[BaseMethod] = [
        make_base_variant(
            dense_variants[0],
            source_group="dense",
            method_label="dense_top10",
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
        )
    ]
    bases.extend(
        make_base_variant(
            variant,
            source_group="intentweight",
            method_label="intentweight",
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
        )
        for variant in intent_variants
    )

    print(f"Collecting sentence units from {len(bases)} evidence pools...")
    sentence_texts = collect_unique_sentence_texts_for_bases(
        bases,
        eval_queries,
        corpus_by_id,
        count_tokens=count_tokens,
        top_k=args.top_k,
        max_sentence_tokens=args.max_sentence_tokens,
    )
    sentence_text_to_index = {text: idx for idx, text in enumerate(sentence_texts)}
    candidates_by_run_id = {
        base.variant.run_id: build_candidates_for_base(
            base,
            eval_queries,
            corpus_by_id,
            sentence_text_to_index,
            count_tokens=count_tokens,
            top_k=args.top_k,
            max_sentence_tokens=args.max_sentence_tokens,
        )
        for base in bases
    }

    print(f"Encoding {len(sentence_texts)} unique sentence units and {len(eval_queries)} queries...")
    encoder = dense_baseline.load_sentence_transformer(
        args.model,
        device=args.device,
        local_files_only=args.local_files_only,
    )
    sentence_embeddings = dense_baseline.encode_texts(
        encoder,
        sentence_texts,
        batch_size=args.batch_size,
    ) if sentence_texts else np.zeros((0, 1), dtype=np.float32)
    query_embeddings = dense_baseline.encode_texts(
        encoder,
        [str(query.get("text", "")) for query in eval_queries],
        batch_size=args.batch_size,
    )
    query_embeddings_by_qid = {
        query_id(query): query_embeddings[idx]
        for idx, query in enumerate(eval_queries)
    }

    compressed: List[BaseMethod] = []
    for base in bases:
        for ratio in ratios:
            compressed.append(compress_base_variant(
                base,
                ratio=ratio,
                queries=eval_queries,
                candidates_by_qid=candidates_by_run_id[base.variant.run_id],
                query_embeddings_by_qid=query_embeddings_by_qid,
                sentence_embeddings=sentence_embeddings,
                mmr_lambda=args.mmr_lambda,
            ))

    all_methods = bases + compressed
    rows: List[Dict[str, object]] = []
    for method in all_methods:
        row = task46.evaluate_context_variant(method.variant, eval_queries, ks=ks, k=args.k)
        row.update({
            "scale": args.scale,
            "split": args.eval_split,
            "source_group": method.source_group,
            "compressor": method.compressor,
            "budget_ratio": method.budget_ratio if method.budget_ratio is not None else "",
            "source_run_id": method.variant.budget_target_run_id if method.compressor != "none" else method.variant.run_id,
        })
        rows.append(row)

    dense_row = next(row for row in rows if row["source_group"] == "dense" and row["compressor"] == "none")
    task46.add_dense_ratios(rows, baseline_row=dense_row, k=args.k)
    add_source_ratios(rows, k=args.k)

    dense_baseline_variant = bases[0].variant
    base_by_run_id = {base.variant.run_id: base.variant for base in bases}
    rng = np.random.default_rng(args.seed)
    paired_rows: List[Dict[str, object]] = []
    for method in all_methods:
        if method.variant.run_id == dense_baseline_variant.run_id:
            continue
        dense_comp = task46.compare_context_variant(
            scale=args.scale,
            queries=eval_queries,
            baseline=dense_baseline_variant,
            variant=method.variant,
            k=args.k,
            noninferiority_margin=args.noninferiority_margin,
            n_bootstrap=args.bootstrap,
            confidence=args.confidence,
            rng=rng,
        )
        dense_comp.update({
            "comparison": "vs_dense",
            "source_group": method.source_group,
            "compressor": method.compressor,
            "budget_ratio": method.budget_ratio if method.budget_ratio is not None else "",
        })
        paired_rows.append(dense_comp)

        if method.compressor != "none":
            source_variant = base_by_run_id[method.variant.budget_target_run_id]
            source_comp = task46.compare_context_variant(
                scale=args.scale,
                queries=eval_queries,
                baseline=source_variant,
                variant=method.variant,
                k=args.k,
                noninferiority_margin=args.noninferiority_margin,
                n_bootstrap=args.bootstrap,
                confidence=args.confidence,
                rng=rng,
            )
            source_comp.update({
                "comparison": "vs_source",
                "source_group": method.source_group,
                "compressor": method.compressor,
                "budget_ratio": method.budget_ratio if method.budget_ratio is not None else "",
            })
            paired_rows.append(source_comp)

    rows.sort(key=lambda row: (
        str(row.get("source_group", "")),
        str(row.get("source_run_id", "")),
        str(row.get("compressor", "")),
        float(row.get("budget_ratio") or 1.0),
    ))
    paired_rows.sort(key=lambda row: (
        str(row.get("comparison", "")),
        str(row.get("source_group", "")),
        str(row.get("budget_ratio", "")),
        str(row.get("method_run_id", "")),
    ))

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    write_rows_csv(output_prefix.with_suffix(".csv"), rows)
    paired.write_csv(output_prefix.with_suffix(".paired.csv"), paired_rows)
    output_prefix.with_suffix(".json").write_text(json.dumps({
        "config": {
            "scale": args.scale,
            "corpus": str(args.corpus),
            "queries": str(args.queries),
            "dense_ranking": args.dense_ranking,
            "intent_ranking": args.intent_ranking,
            "intent_include": args.intent_include,
            "budget_ratios": list(ratios),
            "model": args.model,
            "device": args.device,
            "local_files_only": args.local_files_only,
            "batch_size": args.batch_size,
            "top_k": args.top_k,
            "ks": list(ks),
            "k": args.k,
            "mmr_lambda": args.mmr_lambda,
            "max_sentence_tokens": args.max_sentence_tokens,
            "tokenizer": args.tokenizer,
            "encoding": args.encoding,
            "noninferiority_margin": args.noninferiority_margin,
            "bootstrap": args.bootstrap,
            "confidence": args.confidence,
            "seed": args.seed,
            **split_metadata,
        },
        "rows": rows,
        "paired_rows": paired_rows,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output_rankings = {
        method.variant.run_id: {
            qid: ranking
            for qid, ranking in method.variant.support_rankings.items()
            if qid in eval_qids
        }
        for method in all_methods
    }
    output_prefix.with_suffix(".rankings.json").write_text(
        json.dumps(output_rankings, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_summary_md(
        output_prefix.with_suffix(".md"),
        scale=args.scale,
        split=args.eval_split,
        rows=rows,
        paired_rows=paired_rows,
        k=args.k,
        config={
            "top_k": args.top_k,
            "budget_ratios": ",".join(f"{ratio:.2f}" for ratio in ratios),
            "mmr_lambda": args.mmr_lambda,
            "max_sentence_tokens": args.max_sentence_tokens,
        },
    )

    print(f"Summary: {output_prefix.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
