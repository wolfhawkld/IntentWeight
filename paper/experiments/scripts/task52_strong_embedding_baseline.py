#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task52 strong embedding baseline comparison.

This script compares a stronger dense embedding baseline against the current
MiniLM dense floor and Task38 IntentWeight target policies on the same frozen
Task38 held-out query split. It consumes saved ranking artifacts; it does not
recompute embeddings.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
from pathlib import Path
from typing import Dict, List, Mapping, NamedTuple, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS = ROOT / "paper" / "experiments" / "results"
PROCESSED = ROOT / "paper" / "experiments" / "data" / "processed"


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")
paired = _load_script_module("task37_paired_significance", SCRIPT_DIR / "task37_paired_significance.py")
task38 = _load_script_module("task38_calibrated_context_budget", SCRIPT_DIR / "task38_calibrated_context_budget.py")


class Variant(NamedTuple):
    label: str
    run_id: str
    seed: str
    rankings: Dict[str, List[str]]


def load_flat_rankings(path: Path) -> Dict[str, List[str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Ranking file must be a JSON object: {path}")
    if not all(isinstance(value, list) for value in data.values()):
        raise ValueError(f"Expected flat query->ranking mapping: {path}")
    return {str(qid): [str(item) for item in ranking] for qid, ranking in data.items()}


def load_json_list(path: Path) -> list[Mapping]:
    return context_token_cost.load_json_list(path)


def query_id(record: Mapping) -> str:
    return context_token_cost.query_id(record)


def chunk_id(record: Mapping) -> str:
    return context_token_cost.chunk_id(record)


def parse_seed(run_id: str) -> str:
    match = re.search(r"seed(\d+)", str(run_id))
    return match.group(1) if match else ""


def load_task38_targets(path: Path, include: str) -> list[Variant]:
    variants = []
    for variant in context_token_cost.load_ranking_variants("task38", path):
        if include not in variant.run_id:
            continue
        variants.append(Variant(
            label="intentweight_target",
            run_id=str(variant.run_id),
            seed=parse_seed(str(variant.run_id)),
            rankings=variant.rankings,
        ))
    if not variants:
        raise ValueError(f"No Task38 target variants matched {include!r}")
    return variants


def evaluate_variant(
    variant: Variant,
    queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
    *,
    ks: Sequence[int],
) -> dict[str, object]:
    row = context_token_cost.evaluate_variant(
        context_token_cost.RankingVariant(
            run_id=variant.run_id,
            source_label=variant.label,
            method=variant.label,
            seed=variant.seed,
            rankings=variant.rankings,
        ),
        queries,
        chunk_tokens,
        ks=ks,
        skip_empty_gt=True,
    )
    row["method_label"] = variant.label
    return row


def add_pairwise_deltas(rows: list[dict[str, object]], baselines: Mapping[str, Mapping[str, object]], k: int) -> None:
    for row in rows:
        for label, baseline in baselines.items():
            baseline_hit = float(baseline.get(f"hit@{k}", 0.0))
            baseline_tokens = float(baseline.get(f"avg_context_tokens@{k}", 0.0))
            row[f"hit_delta_vs_{label}@{k}"] = float(row.get(f"hit@{k}", 0.0)) - baseline_hit
            tokens = float(row.get(f"avg_context_tokens@{k}", 0.0))
            row[f"context_token_ratio_vs_{label}@{k}"] = tokens / baseline_tokens if baseline_tokens else 0.0
            row[f"context_token_saving_percent_vs_{label}@{k}"] = (
                1.0 - float(row[f"context_token_ratio_vs_{label}@{k}"])
            ) * 100.0


def paired_compare(
    *,
    scale: str,
    baseline: Variant,
    methods: Sequence[Variant],
    queries: Sequence[Mapping],
    chunk_tokens: Mapping[str, int],
    k: int,
    noninferiority_margin: float,
    bootstrap: int,
    confidence: float,
    seed: int,
    comparison: str,
) -> list[dict[str, object]]:
    import numpy as np

    rng = np.random.default_rng(seed)
    baseline_paired = paired.Variant(
        label=baseline.label,
        run_id=baseline.run_id,
        seed=baseline.seed,
        rankings=baseline.rankings,
    )
    rows = []
    for method in methods:
        method_paired = paired.Variant(
            label=method.label,
            run_id=method.run_id,
            seed=method.seed,
            rankings=method.rankings,
        )
        row = paired.compare_variant(
            scale=scale,
            queries=queries,
            baseline=baseline_paired,
            variant=method_paired,
            chunk_tokens=chunk_tokens,
            k=k,
            noninferiority_margin=noninferiority_margin,
            n_bootstrap=bootstrap,
            confidence=confidence,
            rng=rng,
        )
        row["comparison"] = comparison
        rows.append(row)
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    preferred = [
        "comparison",
        "method_label",
        "method_run_id",
        "seed",
        "num_queries",
        "hit@10",
        "method_hit@10",
        "baseline_hit@10",
        "hit_delta_mean",
        "hit_delta_ci_low",
        "hit_delta_ci_high",
        "noninferior_by_ci",
        "evidence_recall@10",
        "evidence_recall_delta_mean",
        "mrr@10",
        "ndcg@10",
        "avg_context_tokens@10",
        "token_ratio",
        "token_saving_percent",
        "mcnemar_p_two_sided",
    ]
    fieldnames = [key for key in preferred if any(key in row for row in rows)]
    fieldnames.extend(sorted({key for row in rows for key in row if key not in set(fieldnames)}))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def f4(value: object) -> str:
    return f"{float(value):.4f}"


def f2(value: object) -> str:
    return f"{float(value):.2f}"


def pp(value: object) -> str:
    return f"{float(value) * 100:+.2f} pp"


def write_markdown(
    path: Path,
    *,
    config: Mapping[str, object],
    summary_rows: Sequence[Mapping[str, object]],
    paired_rows: Sequence[Mapping[str, object]],
) -> None:
    lines = [
        "# Task52 Strong Embedding Baseline",
        "",
        f"- Model: `{config['strong_model']}`",
        f"- Query prefix: `{config['query_prefix']}`",
        f"- Scale: `{config['scale']}`",
        f"- Evaluation split: Task38 frozen test split, `{config['test_query_count']}` queries",
        f"- Corpus chunks: `{config['corpus_chunks']}`",
        f"- Dense ranking depth: `{config['strong_top_k']}`",
        "",
        "## Summary",
        "",
        "| method_label | seed | hit@10 | evidence_recall@10 | avg_context_tokens@10 | hit delta vs MiniLM | hit delta vs BGE | token saving vs MiniLM | token saving vs BGE |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("method_label", "")),
                    str(row.get("seed", "")),
                    f4(row.get("hit@10", 0.0)),
                    f4(row.get("evidence_recall@10", 0.0)),
                    f"{float(row.get('avg_context_tokens@10', 0.0)):.0f}",
                    pp(row.get("hit_delta_vs_minilm@10", 0.0)),
                    pp(row.get("hit_delta_vs_bge@10", 0.0)),
                    f"{float(row.get('context_token_saving_percent_vs_minilm@10', 0.0)):.2f}%",
                    f"{float(row.get('context_token_saving_percent_vs_bge@10', 0.0)):.2f}%",
                ]
            )
            + " |"
        )

    lines.extend([
        "",
        "## Paired Comparisons",
        "",
        "| comparison | method_label | seed | method_hit@10 | baseline_hit@10 | hit_delta | CI low | CI high | token_saving | McNemar p |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for row in paired_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("comparison", "")),
                    str(row.get("method_label", "")),
                    str(row.get("seed", "")),
                    f4(row.get("method_hit@10", 0.0)),
                    f4(row.get("baseline_hit@10", 0.0)),
                    pp(row.get("hit_delta_mean", 0.0)),
                    pp(row.get("hit_delta_ci_low", 0.0)),
                    pp(row.get("hit_delta_ci_high", 0.0)),
                    f"{float(row.get('token_saving_percent', 0.0)):.2f}%",
                    f"{float(row.get('mcnemar_p_two_sided', 0.0)):.4g}",
                ]
            )
            + " |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- BGE-base raises the dense quality floor on the Task38 held-out split.",
        "- BGE also selects longer chunks on average, so stronger dense retrieval is not automatically a final-context cost reduction.",
        "- The current MiniLM-branch IntentWeight policies remain token-saving relative to BGE dense, but they do not match BGE dense quality on this split.",
        "- This is a claim-tightening result: future strong-encoder experiments should test whether the IntentWeight controller still provides a useful token-quality frontier when its dense branch also uses BGE.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare BGE dense baseline on Task38 held-out split")
    parser.add_argument("--scale", default="100k")
    parser.add_argument("--calibration-fraction", type=float, default=0.3)
    parser.add_argument("--split-salt", default="task38_lotte_calibration_v1")
    parser.add_argument("--corpus", type=Path, default=PROCESSED / "lotte_technology_search_100k_corpus.json")
    parser.add_argument("--queries", type=Path, default=PROCESSED / "lotte_technology_search_100k_queries.json")
    parser.add_argument("--minilm-ranking", type=Path, default=RESULTS / "dense_lotte_technology_search_100k_rankings.json")
    parser.add_argument("--bge-ranking", type=Path, default=RESULTS / "task52_bge_base_100k_dense" / "dense_lotte_technology_search_100k_rankings.json")
    parser.add_argument("--intentweight-ranking", type=Path, default=RESULTS / "task38_100k_calibrated_context_budget.rankings.json")
    parser.add_argument("--intentweight-include", default="task37_source:gated_cost_aware")
    parser.add_argument("--strong-model", default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--query-prefix", default="Represent this sentence for searching relevant passages: ")
    parser.add_argument("--strong-top-k", type=int, default=50)
    parser.add_argument("--ks", default="1,5,10,50")
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--noninferiority-margin", type=float, default=0.01)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output-prefix", type=Path, default=RESULTS / "task52_bge_base_100k_strong_embedding")
    args = parser.parse_args(argv)

    ks = context_token_cost.parse_ks(args.ks)
    corpus = load_json_list(args.corpus)
    queries = load_json_list(args.queries)
    _, test_queries = task38.split_queries(
        queries,
        calibration_fraction=args.calibration_fraction,
        salt=f"{args.split_salt}:{args.scale}",
    )
    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}

    minilm = Variant("minilm_dense", "minilm_dense_top10", "", load_flat_rankings(args.minilm_ranking))
    bge = Variant("bge_base_dense", "bge_base_top50", "", load_flat_rankings(args.bge_ranking))
    intentweight = load_task38_targets(args.intentweight_ranking, args.intentweight_include)
    variants = [minilm, bge, *intentweight]

    summary_rows = [
        evaluate_variant(variant, test_queries, chunk_tokens, ks=ks)
        for variant in variants
    ]
    baseline_rows = {
        "minilm": next(row for row in summary_rows if row["run_id"] == minilm.run_id),
        "bge": next(row for row in summary_rows if row["run_id"] == bge.run_id),
    }
    add_pairwise_deltas(summary_rows, baseline_rows, k=10)

    paired_rows: list[dict[str, object]] = []
    paired_rows.extend(paired_compare(
        scale=args.scale,
        baseline=minilm,
        methods=[bge],
        queries=test_queries,
        chunk_tokens=chunk_tokens,
        k=10,
        noninferiority_margin=args.noninferiority_margin,
        bootstrap=args.bootstrap,
        confidence=args.confidence,
        seed=args.seed,
        comparison="bge_vs_minilm_dense",
    ))
    paired_rows.extend(paired_compare(
        scale=args.scale,
        baseline=bge,
        methods=[minilm, *intentweight],
        queries=test_queries,
        chunk_tokens=chunk_tokens,
        k=10,
        noninferiority_margin=args.noninferiority_margin,
        bootstrap=args.bootstrap,
        confidence=args.confidence,
        seed=args.seed,
        comparison="vs_bge_dense",
    ))

    config = {
        "scale": args.scale,
        "calibration_fraction": args.calibration_fraction,
        "split_salt": args.split_salt,
        "test_query_count": len(test_queries),
        "corpus_chunks": len(corpus),
        "strong_model": args.strong_model,
        "query_prefix": args.query_prefix,
        "strong_top_k": args.strong_top_k,
        "ks": list(ks),
        "minilm_ranking": str(args.minilm_ranking),
        "bge_ranking": str(args.bge_ranking),
        "intentweight_ranking": str(args.intentweight_ranking),
        "bootstrap": args.bootstrap,
        "confidence": args.confidence,
        "noninferiority_margin": args.noninferiority_margin,
    }

    output_prefix = args.output_prefix
    write_csv(output_prefix.with_suffix(".csv"), summary_rows)
    write_csv(output_prefix.with_suffix(".paired.csv"), paired_rows)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(
            {
                "config": config,
                "summary_rows": summary_rows,
                "paired_rows": paired_rows,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(output_prefix.with_suffix(".md"), config=config, summary_rows=summary_rows, paired_rows=paired_rows)
    print(f"summary_rows={len(summary_rows)} paired_rows={len(paired_rows)} test_queries={len(test_queries)}")
    print(f"outputs={output_prefix.with_suffix('.csv')},{output_prefix.with_suffix('.paired.csv')},{output_prefix.with_suffix('.json')},{output_prefix.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
