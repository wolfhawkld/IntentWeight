#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query-level paired significance tests for Task37 policies."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
from pathlib import Path
from statistics import mean
from typing import Dict, List, Mapping, NamedTuple, Sequence

import numpy as np
from scipy.stats import binomtest, wilcoxon


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")
retrieval_metrics = context_token_cost.retrieval_metrics


class Variant(NamedTuple):
    label: str
    run_id: str
    seed: str
    rankings: Dict[str, List[str]]


def load_variants(label: str, path: Path, include: str | None) -> List[Variant]:
    variants = []
    for variant in context_token_cost.load_ranking_variants(label, path):
        if include and include not in variant.run_id:
            continue
        seed = str(variant.seed or "")
        if not seed:
            match = re.search(r"seed(\d+)", str(variant.run_id))
            if match:
                seed = match.group(1)
        variants.append(Variant(
            label=label,
            run_id=variant.run_id,
            seed=seed,
            rankings=variant.rankings,
        ))
    return variants


def chunk_id(record: Mapping) -> str:
    return context_token_cost.chunk_id(record)


def query_id(record: Mapping) -> str:
    return context_token_cost.query_id(record)


def ground_truth(record: Mapping) -> set[str]:
    return retrieval_metrics._ground_truth(record)


def has_hit(ranking: Sequence[str], gt: set[str], k: int) -> int:
    return int(bool(gt.intersection(str(item) for item in ranking[:k])))


def evidence_recall(ranking: Sequence[str], gt: set[str], k: int) -> float:
    if not gt:
        return 0.0
    return len(gt.intersection(str(item) for item in ranking[:k])) / len(gt)


def mcnemar_exact_p(method_hits: Sequence[int], baseline_hits: Sequence[int]) -> tuple[int, int, float]:
    method_only = 0
    baseline_only = 0
    for method_hit, baseline_hit in zip(method_hits, baseline_hits):
        if method_hit and not baseline_hit:
            method_only += 1
        elif baseline_hit and not method_hit:
            baseline_only += 1
    discordant = method_only + baseline_only
    if discordant == 0:
        return method_only, baseline_only, 1.0
    p_value = float(binomtest(min(method_only, baseline_only), discordant, p=0.5, alternative="two-sided").pvalue)
    return method_only, baseline_only, p_value


def bootstrap_ci(
    values: np.ndarray,
    *,
    rng: np.random.Generator,
    n_bootstrap: int,
    confidence: float,
) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=np.float64)
    observed = float(np.mean(values)) if values.size else 0.0
    if values.size == 0 or n_bootstrap <= 0:
        return observed, observed, observed
    indices = rng.integers(0, values.size, size=(n_bootstrap, values.size))
    samples = values[indices].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    lo = float(np.quantile(samples, alpha))
    hi = float(np.quantile(samples, 1.0 - alpha))
    return observed, lo, hi


def safe_wilcoxon_p(values: Sequence[float], *, alternative: str) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0 or np.allclose(arr, 0.0):
        return 1.0
    try:
        return float(wilcoxon(arr, alternative=alternative, zero_method="zsplit").pvalue)
    except ValueError:
        return 1.0


def compare_variant(
    *,
    scale: str,
    queries: Sequence[Mapping],
    baseline: Variant,
    variant: Variant,
    chunk_tokens: Mapping[str, int],
    k: int,
    noninferiority_margin: float,
    n_bootstrap: int,
    confidence: float,
    rng: np.random.Generator,
) -> Dict[str, object]:
    baseline_hits: List[int] = []
    method_hits: List[int] = []
    baseline_tokens: List[float] = []
    method_tokens: List[float] = []
    recall_deltas: List[float] = []
    mrr_deltas: List[float] = []
    ndcg_deltas: List[float] = []

    wins = losses = ties = 0
    token_down_hit_same = 0
    token_down_hit_worse = 0
    token_down_hit_better = 0
    evaluated = 0

    for query in queries:
        gt = ground_truth(query)
        if not gt:
            continue
        qid = query_id(query)
        baseline_ranking = [str(item) for item in baseline.rankings.get(qid, [])]
        method_ranking = [str(item) for item in variant.rankings.get(qid, [])]
        base_hit = has_hit(baseline_ranking, gt, k)
        method_hit = has_hit(method_ranking, gt, k)
        base_tokens = float(sum(chunk_tokens.get(str(item), 0) for item in baseline_ranking[:k]))
        method_tok = float(sum(chunk_tokens.get(str(item), 0) for item in method_ranking[:k]))

        baseline_hits.append(base_hit)
        method_hits.append(method_hit)
        baseline_tokens.append(base_tokens)
        method_tokens.append(method_tok)
        recall_deltas.append(evidence_recall(method_ranking, gt, k) - evidence_recall(baseline_ranking, gt, k))

        base_mrr = retrieval_metrics.mrr_at_k(baseline_ranking, gt, k)
        method_mrr = retrieval_metrics.mrr_at_k(method_ranking, gt, k)
        base_ndcg = retrieval_metrics.ndcg_at_k(baseline_ranking, gt, k)
        method_ndcg = retrieval_metrics.ndcg_at_k(method_ranking, gt, k)
        mrr_deltas.append(method_mrr - base_mrr)
        ndcg_deltas.append(method_ndcg - base_ndcg)

        if method_hit > base_hit:
            wins += 1
        elif method_hit < base_hit:
            losses += 1
        else:
            ties += 1
        if method_tok < base_tokens:
            if method_hit == base_hit:
                token_down_hit_same += 1
            elif method_hit > base_hit:
                token_down_hit_better += 1
            else:
                token_down_hit_worse += 1
        evaluated += 1

    baseline_hits_arr = np.asarray(baseline_hits, dtype=np.float64)
    method_hits_arr = np.asarray(method_hits, dtype=np.float64)
    baseline_tokens_arr = np.asarray(baseline_tokens, dtype=np.float64)
    method_tokens_arr = np.asarray(method_tokens, dtype=np.float64)
    hit_delta = method_hits_arr - baseline_hits_arr
    token_delta = method_tokens_arr - baseline_tokens_arr
    token_saving = baseline_tokens_arr - method_tokens_arr

    hit_mean, hit_lo, hit_hi = bootstrap_ci(
        hit_delta,
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    token_delta_mean, token_delta_lo, token_delta_hi = bootstrap_ci(
        token_delta,
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    saving_mean, saving_lo, saving_hi = bootstrap_ci(
        token_saving,
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    recall_delta_mean, recall_delta_lo, recall_delta_hi = bootstrap_ci(
        np.asarray(recall_deltas, dtype=np.float64),
        rng=rng,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
    )
    method_only, baseline_only, mcnemar_p = mcnemar_exact_p(method_hits, baseline_hits)
    token_wilcoxon_p = safe_wilcoxon_p(token_saving, alternative="greater")

    baseline_token_mean = float(np.mean(baseline_tokens_arr)) if baseline_tokens_arr.size else 0.0
    method_token_mean = float(np.mean(method_tokens_arr)) if method_tokens_arr.size else 0.0
    token_ratio = method_token_mean / baseline_token_mean if baseline_token_mean > 0 else 0.0

    return {
        "scale": scale,
        "baseline_run_id": baseline.run_id,
        "method_label": variant.label,
        "method_run_id": variant.run_id,
        "seed": variant.seed,
        "num_queries": evaluated,
        "baseline_hit@10": float(np.mean(baseline_hits_arr)) if evaluated else 0.0,
        "method_hit@10": float(np.mean(method_hits_arr)) if evaluated else 0.0,
        "hit_delta_mean": hit_mean,
        "hit_delta_ci_low": hit_lo,
        "hit_delta_ci_high": hit_hi,
        "noninferior_margin": noninferiority_margin,
        "noninferior_by_ci": bool(hit_lo >= -noninferiority_margin),
        "method_only_hits": method_only,
        "baseline_only_hits": baseline_only,
        "hit_ties": ties,
        "hit_wins": wins,
        "hit_losses": losses,
        "mcnemar_p_two_sided": mcnemar_p,
        "baseline_tokens_mean": baseline_token_mean,
        "method_tokens_mean": method_token_mean,
        "token_ratio": token_ratio,
        "token_saving_percent": (1.0 - token_ratio) * 100.0,
        "token_delta_mean": token_delta_mean,
        "token_delta_ci_low": token_delta_lo,
        "token_delta_ci_high": token_delta_hi,
        "token_saving_mean": saving_mean,
        "token_saving_ci_low": saving_lo,
        "token_saving_ci_high": saving_hi,
        "token_saving_wilcoxon_p_greater": token_wilcoxon_p,
        "token_down_hit_same": token_down_hit_same,
        "token_down_hit_better": token_down_hit_better,
        "token_down_hit_worse": token_down_hit_worse,
        "token_down_nonworse_rate": (token_down_hit_same + token_down_hit_better) / evaluated if evaluated else 0.0,
        "evidence_recall_delta_mean": recall_delta_mean,
        "evidence_recall_delta_ci_low": recall_delta_lo,
        "evidence_recall_delta_ci_high": recall_delta_hi,
        "mrr_delta_mean": float(mean(mrr_deltas)) if mrr_deltas else 0.0,
        "ndcg_delta_mean": float(mean(ndcg_deltas)) if ndcg_deltas else 0.0,
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    preferred = [
        "scale",
        "method_label",
        "method_run_id",
        "seed",
        "num_queries",
        "method_hit@10",
        "baseline_hit@10",
        "hit_delta_mean",
        "hit_delta_ci_low",
        "hit_delta_ci_high",
        "noninferior_by_ci",
        "token_ratio",
        "token_saving_percent",
        "token_saving_ci_low",
        "token_saving_ci_high",
        "token_saving_wilcoxon_p_greater",
        "method_only_hits",
        "baseline_only_hits",
        "mcnemar_p_two_sided",
    ]
    fieldnames = [key for key in preferred if any(key in row for row in rows)]
    fieldnames.extend(sorted({key for row in rows for key in row if key not in set(fieldnames)}))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    columns = [
        "scale",
        "method_label",
        "seed",
        "method_hit@10",
        "hit_delta_mean",
        "hit_delta_ci_low",
        "hit_delta_ci_high",
        "noninferior_by_ci",
        "token_ratio",
        "token_saving_percent",
        "token_saving_ci_low",
        "token_saving_ci_high",
        "method_only_hits",
        "baseline_only_hits",
        "mcnemar_p_two_sided",
        "token_down_nonworse_rate",
    ]
    lines = [
        "# Task37 Paired Significance",
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
        "## Notes",
        "",
        "- Hit tests are paired by query against dense top-10.",
        "- `noninferior_by_ci` uses the bootstrap CI lower bound and the configured Hit@10 margin.",
        "- Token saving is final evidence-context token saving, not corpus indexing or dense retrieval compute.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run query-level paired significance tests")
    parser.add_argument("--scale", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--baseline", required=True, help="label=path")
    parser.add_argument("--method", action="append", required=True, help="label=path, may be repeated")
    parser.add_argument("--include", action="append", default=[], help="Optional run_id substring filter per method")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--noninferiority-margin", type=float, default=0.01)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args(argv)

    baseline_label, baseline_path = context_token_cost.parse_ranking_arg(args.baseline)
    baseline_variants = load_variants(baseline_label, baseline_path, include=None)
    if len(baseline_variants) != 1:
        raise ValueError(f"Expected exactly one baseline variant, got {len(baseline_variants)}")
    baseline = baseline_variants[0]

    queries = context_token_cost.load_json_list(args.queries)
    corpus = context_token_cost.load_json_list(args.corpus)
    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}
    rng = np.random.default_rng(args.seed)

    rows: List[Dict[str, object]] = []
    includes = list(args.include)
    for index, raw_method in enumerate(args.method):
        label, path = context_token_cost.parse_ranking_arg(raw_method)
        include = includes[index] if index < len(includes) else None
        variants = load_variants(label, path, include=include)
        for variant in variants:
            rows.append(compare_variant(
                scale=args.scale,
                queries=queries,
                baseline=baseline,
                variant=variant,
                chunk_tokens=chunk_tokens,
                k=args.k,
                noninferiority_margin=args.noninferiority_margin,
                n_bootstrap=args.bootstrap,
                confidence=args.confidence,
                rng=rng,
            ))

    write_csv(args.output_csv, rows)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
