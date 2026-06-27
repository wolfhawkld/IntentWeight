#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task62 Selective-Context-style prompt compression baseline.

The baseline starts from already-produced evidence pools, splits chunks into
sentence-like prompt units, scores units with lightweight query-aware lexical
salience, and prunes the prompt to a fixed token ratio. This is a local,
dependency-free proxy for Selective Context / prompt-pruning baselines. It is
not an implementation of LLMLingua.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


task48 = _load_script_module("task48_compressor_normalized_comparison", SCRIPT_DIR / "task48_compressor_normalized_comparison.py")
task46 = task48.task46
context_token_cost = task48.context_token_cost
paired = task48.paired


WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]*")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "has", "have", "how", "in", "into", "is", "it", "its",
    "of", "on", "or", "that", "the", "their", "this", "to", "was", "were",
    "what", "when", "where", "which", "who", "why", "with", "without",
}


def parse_floats(value: str) -> tuple[float, ...]:
    return task48.parse_floats(value)


def query_id(record: Mapping) -> str:
    return task46.query_id(record)


def chunk_id(record: Mapping) -> str:
    return task46.chunk_id(record)


def tokenize_words(text: str) -> list[str]:
    return [
        token.lower()
        for token in WORD_RE.findall(str(text or ""))
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


def query_terms(text: str) -> set[str]:
    return {token for token in tokenize_words(text) if len(token) > 2}


def query_bigrams(terms_in_order: Sequence[str]) -> set[tuple[str, str]]:
    return {
        (terms_in_order[idx], terms_in_order[idx + 1])
        for idx in range(len(terms_in_order) - 1)
    }


def sentence_bigrams(terms_in_order: Sequence[str]) -> set[tuple[str, str]]:
    return query_bigrams(terms_in_order)


def build_idf(candidates_by_run_id: Mapping[str, Mapping[str, Sequence[task46.CandidateSentence]]]) -> dict[str, float]:
    document_frequency: dict[str, int] = defaultdict(int)
    total_sentences = 0
    seen_texts: set[str] = set()
    for candidates_by_qid in candidates_by_run_id.values():
        for candidates in candidates_by_qid.values():
            for candidate in candidates:
                if candidate.text in seen_texts:
                    continue
                seen_texts.add(candidate.text)
                total_sentences += 1
                for term in set(tokenize_words(candidate.text)):
                    document_frequency[term] += 1
    if total_sentences == 0:
        return {}
    return {
        term: math.log((1.0 + total_sentences) / (1.0 + frequency)) + 1.0
        for term, frequency in document_frequency.items()
    }


def score_candidate(
    candidate: task46.CandidateSentence,
    *,
    q_terms: set[str],
    q_bigrams: set[tuple[str, str]],
    idf: Mapping[str, float],
) -> float:
    terms_in_order = tokenize_words(candidate.text)
    sentence_terms = set(terms_in_order)
    overlap = q_terms.intersection(sentence_terms)
    overlap_weight = sum(float(idf.get(term, 1.0)) for term in overlap)
    coverage = len(overlap) / max(len(q_terms), 1)
    bigram_overlap = len(q_bigrams.intersection(sentence_bigrams(terms_in_order)))
    rank_bonus = 1.0 / max(candidate.dense_rank, 1)
    position_bonus = 1.0 / max(candidate.sentence_index + 1, 1)
    compactness_bonus = 1.0 / math.sqrt(max(candidate.token_count, 1))
    return (
        overlap_weight
        + 1.5 * coverage
        + 0.75 * bigram_overlap
        + 0.35 * rank_bonus
        + 0.10 * position_bonus
        + 0.05 * compactness_bonus
    )


def select_prompt_units(
    candidates: Sequence[task46.CandidateSentence],
    *,
    query_text: str,
    idf: Mapping[str, float],
    budget_tokens: int,
) -> list[task46.SelectedSentence]:
    if budget_tokens <= 0 or not candidates:
        return []

    ordered_query_terms = tokenize_words(query_text)
    q_terms = {term for term in ordered_query_terms if len(term) > 2}
    q_bigrams = query_bigrams(ordered_query_terms)

    scored = []
    for idx, candidate in enumerate(candidates):
        score = score_candidate(candidate, q_terms=q_terms, q_bigrams=q_bigrams, idf=idf)
        scored.append((score, idx, candidate))

    best_by_chunk: dict[str, tuple[float, int, task46.CandidateSentence]] = {}
    for score, idx, candidate in scored:
        current = best_by_chunk.get(candidate.chunk_id)
        key = (score, -candidate.token_count, -candidate.sentence_index)
        if current is None or key > (current[0], -current[2].token_count, -current[2].sentence_index):
            best_by_chunk[candidate.chunk_id] = (score, idx, candidate)

    selected_indices: set[int] = set()
    selected: list[task46.SelectedSentence] = []
    used_tokens = 0

    # Preserve source chunk coverage first when the compression budget allows it.
    coverage_candidates = sorted(
        best_by_chunk.values(),
        key=lambda item: (
            item[2].dense_rank,
            -item[0],
            item[2].sentence_index,
            item[2].token_count,
        ),
    )
    for score, idx, candidate in coverage_candidates:
        if used_tokens + candidate.token_count > budget_tokens:
            continue
        selected_indices.add(idx)
        used_tokens += candidate.token_count
        selected.append(task46.SelectedSentence(
            chunk_id=candidate.chunk_id,
            dense_rank=candidate.dense_rank,
            sentence_index=candidate.sentence_index,
            text=candidate.text,
            token_count=candidate.token_count,
            query_score=float(score),
            mmr_score=float(score),
        ))

    # Fill the remaining budget with the most query-salient prompt units.
    for score, idx, candidate in sorted(
        scored,
        key=lambda item: (
            -item[0],
            item[2].dense_rank,
            item[2].sentence_index,
            item[2].token_count,
        ),
    ):
        if idx in selected_indices:
            continue
        if used_tokens + candidate.token_count > budget_tokens:
            continue
        selected_indices.add(idx)
        used_tokens += candidate.token_count
        selected.append(task46.SelectedSentence(
            chunk_id=candidate.chunk_id,
            dense_rank=candidate.dense_rank,
            sentence_index=candidate.sentence_index,
            text=candidate.text,
            token_count=candidate.token_count,
            query_score=float(score),
            mmr_score=float(score),
        ))

    return selected


def compress_base_variant(
    base: task48.BaseMethod,
    *,
    ratio: float,
    queries: Sequence[Mapping],
    candidates_by_qid: Mapping[str, Sequence[task46.CandidateSentence]],
    idf: Mapping[str, float],
) -> task48.BaseMethod:
    support_rankings: Dict[str, list[str]] = {}
    context_tokens: Dict[str, int] = {}
    budget_tokens: Dict[str, int] = {}
    sentence_counts: Dict[str, int] = {}
    supported_counts: Dict[str, int] = {}

    for query in queries:
        qid = query_id(query)
        budget = int(math.floor(float(base.variant.context_tokens.get(qid, 0)) * ratio))
        budget_tokens[qid] = budget
        selected = select_prompt_units(
            candidates_by_qid.get(qid, []),
            query_text=str(query.get("text", "")),
            idf=idf,
            budget_tokens=budget,
        )
        support_rankings[qid] = task46.dedupe_chunk_ranking(selected)
        context_tokens[qid] = int(sum(sentence.token_count for sentence in selected))
        sentence_counts[qid] = len(selected)
        supported_counts[qid] = len(set(support_rankings[qid]))

    run_id = f"{base.variant.run_id}:selective_context_r{ratio:.2f}"
    return task48.BaseMethod(
        variant=task46.ContextVariant(
            run_id=run_id,
            method_label=f"{base.variant.method_label}_selective_context",
            budget_target_run_id=base.variant.run_id,
            support_rankings=support_rankings,
            context_tokens=context_tokens,
            budget_tokens=budget_tokens,
            sentence_counts=sentence_counts,
            supported_chunk_counts=supported_counts,
        ),
        source_group=base.source_group,
        compressor="selective_context_lite",
        budget_ratio=ratio,
    )


def write_rows_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    task48.write_rows_csv(path, rows)


def write_summary_md(
    path: Path,
    *,
    scale: str,
    split: str,
    rows: Sequence[Mapping[str, object]],
    paired_rows: Sequence[Mapping[str, object]],
    sent_mmr_reference: Sequence[Mapping[str, str]],
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
        "compressor",
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

    dense_rows = [
        row for row in rows
        if row.get("source_group") == "dense" and row.get("compressor") == "selective_context_lite"
    ]
    dense_ref_rows = [
        row for row in sent_mmr_reference
        if row.get("source_group") == "dense" and row.get("compressor") == "sent_mmr"
    ]

    lines = [
        "# Task62 Prompt-Compression Baseline",
        "",
        f"- Scale: `{scale}`",
        f"- Evaluation split: `{split}`",
        f"- Dense candidate depth: `{config.get('top_k')}`",
        f"- Budget ratios: `{config.get('budget_ratios')}`",
        f"- Prompt compressor: `selective_context_lite`",
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

    if dense_ref_rows:
        lines.extend([
            "",
            "## SentMMR Reference From Task48",
            "",
            "| Compressor | Ratio | Hit@10 | Token saving vs dense |",
            "| --- | ---: | ---: | ---: |",
        ])
        for row in sorted(dense_ref_rows, key=lambda item: float(item.get("budget_ratio") or 1.0)):
            lines.append(
                "| SentMMR | {ratio} | {hit:.4f} | {saving:.2f}% |".format(
                    ratio=row.get("budget_ratio", ""),
                    hit=float(row.get(f"hit@{k}", 0.0)),
                    saving=float(row.get(f"context_token_saving_percent_vs_dense@{k}", 0.0)),
                )
            )
        for row in sorted(dense_rows, key=lambda item: float(item.get("budget_ratio") or 1.0)):
            lines.append(
                "| SelectiveContext-lite | {ratio} | {hit:.4f} | {saving:.2f}% |".format(
                    ratio=row.get("budget_ratio", ""),
                    hit=float(row.get(f"hit@{k}", 0.0)),
                    saving=float(row.get(f"context_token_saving_percent_vs_dense@{k}", 0.0)),
                )
            )

    lines.extend([
        "",
        "## Notes",
        "",
        "- This is a local Selective Context-style prompt-pruning baseline, not LLMLingua.",
        "- The compressor is applied after each evidence pool is produced, so it is downstream of retrieval.",
        "- `vs_source` compares a compressed row against its own uncompressed evidence pool.",
        "- `vs_dense` compares every row against uncompressed dense top-10.",
        "- Hit and evidence-recall metrics remain chunk-support proxies; answer-level sufficiency still requires downstream generation evaluation.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task62 prompt-compression baseline")
    parser.add_argument("--scale", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--dense-ranking", required=True, help="label=path")
    parser.add_argument("--intent-ranking", required=True, help="label=path")
    parser.add_argument("--intent-include", default=None)
    parser.add_argument("--budget-ratios", default="0.95,0.90,0.85,0.75")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--k", type=int, default=10)
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
    parser.add_argument("--sent-mmr-reference", type=Path, default=None)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args(argv)

    ks = context_token_cost.parse_ks(args.ks)
    if args.k not in ks:
        ks = tuple(sorted({*ks, args.k}))
    ratios = parse_floats(args.budget_ratios)
    if args.max_sentence_tokens <= 0:
        raise ValueError(f"max_sentence_tokens must be positive, got {args.max_sentence_tokens}")

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

    dense_variants = task48.load_variants(args.dense_ranking)
    if len(dense_variants) != 1:
        raise ValueError(f"Expected one dense variant, got {len(dense_variants)}")
    intent_variants = task48.load_variants(args.intent_ranking, include=args.intent_include)

    bases: list[task48.BaseMethod] = [
        task48.make_base_variant(
            dense_variants[0],
            source_group="dense",
            method_label="dense_top10",
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
        )
    ]
    bases.extend(
        task48.make_base_variant(
            variant,
            source_group="intentweight",
            method_label="intentweight",
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
        )
        for variant in intent_variants
    )

    print(f"Collecting prompt units from {len(bases)} evidence pools...")
    sentence_texts = task48.collect_unique_sentence_texts_for_bases(
        bases,
        eval_queries,
        corpus_by_id,
        count_tokens=count_tokens,
        top_k=args.top_k,
        max_sentence_tokens=args.max_sentence_tokens,
    )
    sentence_text_to_index = {text: idx for idx, text in enumerate(sentence_texts)}
    candidates_by_run_id = {
        base.variant.run_id: task48.build_candidates_for_base(
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
    idf = build_idf(candidates_by_run_id)

    compressed: list[task48.BaseMethod] = []
    for base in bases:
        for ratio in ratios:
            compressed.append(compress_base_variant(
                base,
                ratio=ratio,
                queries=eval_queries,
                candidates_by_qid=candidates_by_run_id[base.variant.run_id],
                idf=idf,
            ))

    all_methods = bases + compressed
    rows: list[dict[str, object]] = []
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
    task48.add_source_ratios(rows, k=args.k)

    dense_baseline_variant = bases[0].variant
    base_by_run_id = {base.variant.run_id: base.variant for base in bases}
    rng = np.random.default_rng(args.seed)
    paired_rows: list[dict[str, object]] = []
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
        str(row.get("compressor", "")),
        str(row.get("budget_ratio", "")),
        str(row.get("method_run_id", "")),
    ))

    sent_mmr_reference: list[dict[str, str]] = []
    if args.sent_mmr_reference and args.sent_mmr_reference.exists():
        with args.sent_mmr_reference.open("r", encoding="utf-8", newline="") as handle:
            sent_mmr_reference = list(csv.DictReader(handle))

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
            "compressor": "selective_context_lite",
            "top_k": args.top_k,
            "ks": list(ks),
            "k": args.k,
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
        sent_mmr_reference=sent_mmr_reference,
        k=args.k,
        config={
            "top_k": args.top_k,
            "budget_ratios": ",".join(f"{ratio:.2f}" for ratio in ratios),
            "max_sentence_tokens": args.max_sentence_tokens,
        },
    )

    print(json.dumps({"rows": len(rows), "paired_rows": len(paired_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
