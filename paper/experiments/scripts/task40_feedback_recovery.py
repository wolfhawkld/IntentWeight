#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task40 feedback-driven recovery for budget-induced hard cases.

This script studies whether simulated feedback can recover queries harmed by
aggressive final-context budgets. It uses saved dense, fixed-topk LinUCB, and
budgeted LinUCB rankings plus the cached KMeans arm labels.

Two protocols are reported:

1. Same-query retry: affected queries receive simulated corrective feedback
   after a failed answer. The feedback identifies evidence arms from GT evidence
   and re-ranks the fixed LinUCB top-k before reapplying a budget policy.
2. Calibration-to-test generalization: only calibration affected queries are
   used to learn risky query-arm -> evidence-arm boosts. The learned map is
   frozen and evaluated on held-out test queries.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ARTIFACT_DIR = SCRIPT_DIR.parent / "data" / "retrieval_artifacts"


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")
task37_budget = _load_script_module("task37_context_budget_search", SCRIPT_DIR / "task37_context_budget_search.py")


class SeedContext(NamedTuple):
    seed: str
    query_arm: Dict[str, int]
    chunk_arm: Dict[str, int]
    centroids: np.ndarray


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def qid(query: Mapping) -> str:
    return context_token_cost.query_id(query)


def cid(chunk: Mapping) -> str:
    return context_token_cost.chunk_id(chunk)


def gt_set(query: Mapping) -> set[str]:
    return {str(item) for item in query.get("ground_truth_chunk_ids", [])}


def hit(query: Mapping, ranking: Sequence[str], *, top_k: int) -> bool:
    gt = gt_set(query)
    return bool(gt and any(str(item) in gt for item in ranking[:top_k]))


def deterministic_split(
    queries: Sequence[Mapping],
    *,
    calibration_fraction: float,
    salt: str,
) -> tuple[List[Mapping], List[Mapping]]:
    scored = []
    for query in queries:
        digest = hashlib.sha256(f"{salt}:{qid(query)}".encode("utf-8")).hexdigest()
        scored.append((int(digest, 16), query))
    scored.sort(key=lambda item: item[0])
    split_at = max(1, min(len(scored) - 1, int(round(len(scored) * calibration_fraction))))
    return [query for _, query in scored[:split_at]], [query for _, query in scored[split_at:]]


def load_flat_rankings(path: Path) -> Dict[str, List[str]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected ranking object: {path}")
    if not all(isinstance(value, list) for value in data.values()):
        raise ValueError(f"Expected flat query->ranking object: {path}")
    return {str(key): [str(item) for item in value] for key, value in data.items()}


def load_seed_rankings(path: Path, *, method: str) -> Dict[str, Dict[str, List[str]]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if method not in data or not isinstance(data[method], dict):
        raise ValueError(f"Method {method!r} not found in {path}")
    return {
        str(seed): {str(q): [str(item) for item in ranking] for q, ranking in rankings.items()}
        for seed, rankings in data[method].items()
    }


def load_budgeted_seed_rankings(path: Path, *, source_prefix: str) -> Dict[str, Dict[str, List[str]]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected budgeted ranking variants: {path}")
    nested = data.get(source_prefix)
    if isinstance(nested, dict) and all(isinstance(value, dict) for value in nested.values()):
        return {
            str(seed): {str(q): [str(item) for item in ranking] for q, ranking in rankings.items()}
            for seed, rankings in nested.items()
        }
    variants: Dict[str, Dict[str, List[str]]] = {}
    for run_id, rankings in data.items():
        if not str(run_id).startswith(source_prefix):
            continue
        marker = ":seed"
        if marker not in run_id:
            continue
        seed = run_id.split(marker, 1)[1].split(":", 1)[0]
        variants[str(seed)] = {str(q): [str(item) for item in ranking] for q, ranking in rankings.items()}
    if not variants:
        raise ValueError(f"No variants matched prefix {source_prefix!r} in {path}")
    return variants


def discover_context_npz(
    artifact_dir: Path,
    *,
    dataset: str,
    seed: str,
    model_name: str,
    corpus_count: int,
    query_count: int,
    context_dim: int,
    n_clusters: int,
) -> Path:
    matches = []
    for meta_path in artifact_dir.glob(f"{dataset}__context_clusters__*.meta.json"):
        with meta_path.open("r", encoding="utf-8") as f:
            meta = json.load(f)
        params = meta.get("params", {})
        if (
            str(params.get("seed")) == str(seed)
            and int(params.get("context_dim", -1)) == int(context_dim)
            and int(params.get("n_clusters", -1)) == int(n_clusters)
            and str(meta.get("model_name")) == str(model_name)
            and int(meta.get("corpus_count", -1)) == int(corpus_count)
            and int(meta.get("query_count", -1)) == int(query_count)
        ):
            artifact_path = Path(str(meta.get("artifact_path", "")))
            if artifact_path.exists():
                matches.append(artifact_path)
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one context artifact for dataset={dataset}, seed={seed}, "
            f"context_dim={context_dim}, n_clusters={n_clusters}; got {matches}"
        )
    return matches[0]


def load_seed_context(
    artifact_dir: Path,
    *,
    dataset: str,
    seed: str,
    model_name: str,
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    context_dim: int,
    n_clusters: int,
) -> SeedContext:
    path = discover_context_npz(
        artifact_dir,
        dataset=dataset,
        seed=seed,
        model_name=model_name,
        corpus_count=len(corpus),
        query_count=len(queries),
        context_dim=context_dim,
        n_clusters=n_clusters,
    )
    data = np.load(path)
    arm_labels = np.asarray(data["arm_labels"], dtype=np.int32)
    query_context = np.asarray(data["query_context"], dtype=np.float32)
    centroids = np.asarray(data["centroids"], dtype=np.float32)
    if len(arm_labels) != len(corpus) or len(query_context) != len(queries):
        raise ValueError(f"Context artifact shape mismatch for seed {seed}: {path}")
    chunk_arm = {cid(chunk): int(label) for chunk, label in zip(corpus, arm_labels)}
    scores = query_context @ centroids.T
    query_arm_indices = np.argmax(scores, axis=1)
    query_arm = {qid(query): int(arm) for query, arm in zip(queries, query_arm_indices)}
    return SeedContext(str(seed), query_arm, chunk_arm, centroids)


def token_budget(
    ranking: Sequence[str],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
    budget_ratio: float,
    min_keep: int,
) -> List[str]:
    return task37_budget.token_budget_ranking(
        ranking,
        chunk_tokens,
        top_k=top_k,
        budget_ratio=budget_ratio,
        min_keep=min_keep,
    )


def boost_ranking_by_arms(
    ranking: Sequence[str],
    chunk_arm: Mapping[str, int],
    positive_arms: Iterable[int],
) -> List[str]:
    positives = {int(arm) for arm in positive_arms}
    return [
        item
        for _, item in sorted(
            enumerate([str(chunk_id) for chunk_id in ranking]),
            key=lambda pair: (0 if chunk_arm.get(pair[1]) in positives else 1, pair[0]),
        )
    ]


def gt_arms(query: Mapping, chunk_arm: Mapping[str, int]) -> set[int]:
    return {int(chunk_arm[item]) for item in gt_set(query) if item in chunk_arm}


def average_tokens(
    queries: Sequence[Mapping],
    rankings: Mapping[str, Sequence[str]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
) -> float:
    values = []
    for query in queries:
        # Dense artifact caches may retain more than top_k candidates. Recovery
        # comparisons are against the final top-k evidence context.
        values.append(sum(
            chunk_tokens.get(item, 0)
            for item in rankings.get(qid(query), [])[:top_k]
        ))
    return mean(values) if values else 0.0


def evaluate_hit_rate(
    queries: Sequence[Mapping],
    rankings: Mapping[str, Sequence[str]],
    *,
    top_k: int,
) -> float:
    if not queries:
        return 0.0
    return sum(
        1 for query in queries if hit(query, rankings.get(qid(query), []), top_k=top_k)
    ) / len(queries)


def affected_queries(
    queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    fixed_rankings: Mapping[str, Sequence[str]],
    budget_rankings: Mapping[str, Sequence[str]],
    *,
    top_k: int,
) -> tuple[List[Mapping], List[Mapping]]:
    dense_affected = []
    compression_affected = []
    for query in queries:
        query_id = qid(query)
        dense_hit = hit(query, dense_rankings.get(query_id, []), top_k=top_k)
        fixed_hit = hit(query, fixed_rankings.get(query_id, []), top_k=top_k)
        budget_hit = hit(query, budget_rankings.get(query_id, []), top_k=top_k)
        if dense_hit and not budget_hit:
            dense_affected.append(query)
        if fixed_hit and not budget_hit:
            compression_affected.append(query)
    return dense_affected, compression_affected


def merge_retry_rankings(
    queries: Sequence[Mapping],
    base_rankings: Mapping[str, Sequence[str]],
    retry_rankings: Mapping[str, Sequence[str]],
    retry_query_ids: set[str],
) -> Dict[str, List[str]]:
    merged = {}
    for query in queries:
        query_id = qid(query)
        source = retry_rankings if query_id in retry_query_ids else base_rankings
        merged[query_id] = [str(item) for item in source.get(query_id, [])]
    return merged


def same_query_recovery_rows(
    *,
    seed: str,
    queries: Sequence[Mapping],
    affected: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    fixed_rankings: Mapping[str, Sequence[str]],
    budget_rankings: Mapping[str, Sequence[str]],
    context: SeedContext,
    chunk_tokens: Mapping[str, int],
    top_k: int,
    budget_ratio: float,
    min_keep: int,
    conservative_ratio: float,
) -> tuple[List[Dict[str, object]], Dict[str, Dict[str, List[str]]]]:
    retry_rankings: Dict[str, Dict[str, List[str]]] = {
        "same_arm_boost": {},
        "same_arm_boost_conservative": {},
        "same_full_context": {},
    }
    affected_ids = {qid(query) for query in affected}
    for query in affected:
        query_id = qid(query)
        positive_arms = gt_arms(query, context.chunk_arm)
        boosted = boost_ranking_by_arms(fixed_rankings.get(query_id, []), context.chunk_arm, positive_arms)
        retry_rankings["same_arm_boost"][query_id] = token_budget(
            boosted,
            chunk_tokens,
            top_k=top_k,
            budget_ratio=budget_ratio,
            min_keep=min_keep,
        )
        retry_rankings["same_arm_boost_conservative"][query_id] = token_budget(
            boosted,
            chunk_tokens,
            top_k=top_k,
            budget_ratio=conservative_ratio,
            min_keep=min_keep,
        )
        retry_rankings["same_full_context"][query_id] = [str(item) for item in fixed_rankings.get(query_id, [])[:top_k]]

    rows: List[Dict[str, object]] = []
    dense_tokens = average_tokens(affected, dense_rankings, chunk_tokens, top_k=top_k)
    base_tokens = average_tokens(affected, budget_rankings, chunk_tokens, top_k=top_k)
    base_hit = evaluate_hit_rate(affected, budget_rankings, top_k=top_k)
    rows.append({
        "protocol": "same_query_retry",
        "seed": seed,
        "method": "budgeted_before_feedback",
        "affected_count": len(affected),
        "hit_rate": base_hit,
        "recovered_count": 0,
        "regressed_count": 0,
        "avg_context_tokens": base_tokens,
        "token_ratio_vs_dense": base_tokens / dense_tokens if dense_tokens else 0.0,
        "token_saving_percent_vs_dense": (1.0 - base_tokens / dense_tokens) * 100.0 if dense_tokens else 0.0,
    })

    for method, rankings in retry_rankings.items():
        recovered = 0
        regressed = 0
        for query in affected:
            query_id = qid(query)
            before = hit(query, budget_rankings.get(query_id, []), top_k=top_k)
            after = hit(query, rankings.get(query_id, []), top_k=top_k)
            if after and not before:
                recovered += 1
            if before and not after:
                regressed += 1
        tokens = average_tokens(affected, rankings, chunk_tokens, top_k=top_k)
        rows.append({
            "protocol": "same_query_retry",
            "seed": seed,
            "method": method,
            "affected_count": len(affected),
            "hit_rate": evaluate_hit_rate(affected, rankings, top_k=top_k),
            "recovered_count": recovered,
            "regressed_count": regressed,
            "avg_context_tokens": tokens,
            "token_ratio_vs_dense": tokens / dense_tokens if dense_tokens else 0.0,
            "token_saving_percent_vs_dense": (1.0 - tokens / dense_tokens) * 100.0 if dense_tokens else 0.0,
        })

    merged_rankings = {
        method: merge_retry_rankings(queries, budget_rankings, rankings, affected_ids)
        for method, rankings in retry_rankings.items()
    }
    return rows, merged_rankings


def learn_arm_feedback_map(
    calibration_queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    budget_rankings: Mapping[str, Sequence[str]],
    context: SeedContext,
    *,
    min_examples: int,
    top_k: int,
) -> Dict[int, List[int]]:
    counts: Dict[int, Counter] = defaultdict(Counter)
    for query in calibration_queries:
        query_id = qid(query)
        if not hit(query, dense_rankings.get(query_id, []), top_k=top_k) or hit(
            query, budget_rankings.get(query_id, []), top_k=top_k
        ):
            continue
        query_arm = context.query_arm.get(query_id)
        if query_arm is None:
            continue
        for arm in gt_arms(query, context.chunk_arm):
            counts[int(query_arm)][int(arm)] += 1

    learned: Dict[int, List[int]] = {}
    for query_arm, counter in counts.items():
        if sum(counter.values()) >= min_examples:
            learned[int(query_arm)] = [int(arm) for arm, _ in counter.most_common(3)]
    return learned


def generalized_rankings(
    test_queries: Sequence[Mapping],
    fixed_rankings: Mapping[str, Sequence[str]],
    budget_rankings: Mapping[str, Sequence[str]],
    context: SeedContext,
    learned: Mapping[int, Sequence[int]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
    budget_ratio: float,
    min_keep: int,
    conservative_ratio: float,
) -> Dict[str, Dict[str, List[str]]]:
    output = {
        "generalized_arm_boost": {},
        "generalized_arm_boost_conservative": {},
        "generalized_conservative_budget": {},
        "generalized_full_context": {},
    }
    for query in test_queries:
        query_id = qid(query)
        query_arm = context.query_arm.get(query_id)
        if query_arm in learned:
            boosted = boost_ranking_by_arms(
                fixed_rankings.get(query_id, []),
                context.chunk_arm,
                learned[int(query_arm)],
            )
            output["generalized_arm_boost"][query_id] = token_budget(
                boosted,
                chunk_tokens,
                top_k=top_k,
                budget_ratio=budget_ratio,
                min_keep=min_keep,
            )
            output["generalized_arm_boost_conservative"][query_id] = token_budget(
                boosted,
                chunk_tokens,
                top_k=top_k,
                budget_ratio=conservative_ratio,
                min_keep=min_keep,
            )
            output["generalized_conservative_budget"][query_id] = token_budget(
                fixed_rankings.get(query_id, []),
                chunk_tokens,
                top_k=top_k,
                budget_ratio=conservative_ratio,
                min_keep=min_keep,
            )
            output["generalized_full_context"][query_id] = [
                str(item) for item in fixed_rankings.get(query_id, [])[:top_k]
            ]
        else:
            base = [str(item) for item in budget_rankings.get(query_id, [])]
            output["generalized_arm_boost"][query_id] = base
            output["generalized_arm_boost_conservative"][query_id] = base
            output["generalized_conservative_budget"][query_id] = base
            output["generalized_full_context"][query_id] = base
    return output


def all_query_rows(
    *,
    protocol: str,
    seed: str,
    queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    before_rankings: Mapping[str, Sequence[str]],
    variants: Mapping[str, Mapping[str, Sequence[str]]],
    chunk_tokens: Mapping[str, int],
    top_k: int,
    learned_arm_count: int = 0,
) -> List[Dict[str, object]]:
    rows = []
    dense_hit = evaluate_hit_rate(queries, dense_rankings, top_k=top_k)
    dense_tokens = average_tokens(queries, dense_rankings, chunk_tokens, top_k=top_k)
    before_hit = evaluate_hit_rate(queries, before_rankings, top_k=top_k)
    before_tokens = average_tokens(queries, before_rankings, chunk_tokens, top_k=top_k)
    rows.append({
        "protocol": protocol,
        "seed": seed,
        "method": "budgeted_before_feedback",
        "num_queries": len(queries),
        "learned_arm_count": learned_arm_count,
        "hit_rate": before_hit,
        "hit_delta_vs_dense": before_hit - dense_hit,
        "hit_delta_vs_before": 0.0,
        "avg_context_tokens": before_tokens,
        "token_ratio_vs_dense": before_tokens / dense_tokens if dense_tokens else 0.0,
        "token_saving_percent_vs_dense": (1.0 - before_tokens / dense_tokens) * 100.0 if dense_tokens else 0.0,
    })
    for method, rankings in variants.items():
        method_hit = evaluate_hit_rate(queries, rankings, top_k=top_k)
        tokens = average_tokens(queries, rankings, chunk_tokens, top_k=top_k)
        rows.append({
            "protocol": protocol,
            "seed": seed,
            "method": method,
            "num_queries": len(queries),
            "learned_arm_count": learned_arm_count,
            "hit_rate": method_hit,
            "hit_delta_vs_dense": method_hit - dense_hit,
            "hit_delta_vs_before": method_hit - before_hit,
            "avg_context_tokens": tokens,
            "token_ratio_vs_dense": tokens / dense_tokens if dense_tokens else 0.0,
            "token_saving_percent_vs_dense": (1.0 - tokens / dense_tokens) * 100.0 if dense_tokens else 0.0,
        })
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fieldnames = []
    preferred = [
        "protocol",
        "seed",
        "method",
        "num_queries",
        "affected_count",
        "learned_arm_count",
        "hit_rate",
        "hit_delta_vs_dense",
        "hit_delta_vs_before",
        "recovered_count",
        "regressed_count",
        "avg_context_tokens",
        "token_ratio_vs_dense",
        "token_saving_percent_vs_dense",
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


def write_markdown(path: Path, *, summary: Mapping[str, object], rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task40 Feedback Recovery",
        "",
        f"- Dataset: `{summary['dataset']}`",
        f"- Budget policy: `r{summary['budget_ratio']:.2f}_m{summary['min_keep']}`",
        f"- Conservative retry ratio: `{summary['conservative_ratio']:.2f}`",
        f"- Calibration queries: `{summary['calibration_count']}`",
        f"- Test queries: `{summary['test_count']}`",
        "",
        "## Results",
        "",
        "| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {protocol} | {seed} | {method} | {num_queries} | {affected_count} | {learned} | {hit:.4f} | {dense_delta:.4f} | {before_delta:.4f} | {recovered} | {saving:.2f}% |".format(
                protocol=row.get("protocol", ""),
                seed=row.get("seed", ""),
                method=row.get("method", ""),
                num_queries=row.get("num_queries", ""),
                affected_count=row.get("affected_count", ""),
                learned=row.get("learned_arm_count", ""),
                hit=float(row.get("hit_rate", 0.0)),
                dense_delta=float(row.get("hit_delta_vs_dense", 0.0)),
                before_delta=float(row.get("hit_delta_vs_before", 0.0)),
                recovered=row.get("recovered_count", ""),
                saving=float(row.get("token_saving_percent_vs_dense", 0.0)),
            )
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.",
        "- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.",
        "- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task40 feedback-driven recovery analysis")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--dense-rankings", type=Path, required=True)
    parser.add_argument("--fixed-linucb-rankings", type=Path, required=True)
    parser.add_argument("--budgeted-rankings", type=Path, required=True)
    parser.add_argument("--budgeted-prefix", required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--method", default="gated_cost_aware")
    parser.add_argument("--model-name", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--seeds", default="13,17,19")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--budget-ratio", type=float, default=0.85)
    parser.add_argument("--min-keep", type=int, default=4)
    parser.add_argument("--conservative-ratio", type=float, default=0.95)
    parser.add_argument("--context-dim", type=int, default=64)
    parser.add_argument("--n-clusters", type=int, default=32)
    parser.add_argument("--calibration-fraction", type=float, default=0.30)
    parser.add_argument("--split-salt", default="task40_feedback_recovery_v1")
    parser.add_argument("--min-learned-arm-examples", type=int, default=1)
    parser.add_argument("--tokenizer", default="tiktoken", choices=("tiktoken", "simple"))
    parser.add_argument("--encoding", default="cl100k_base")
    args = parser.parse_args(argv)

    seeds = [part.strip() for part in args.seeds.split(",") if part.strip()]
    corpus = load_json_list(args.corpus)
    queries = load_json_list(args.queries)
    calibration_queries, test_queries = deterministic_split(
        queries,
        calibration_fraction=args.calibration_fraction,
        salt=args.split_salt,
    )
    count_tokens = context_token_cost.build_token_counter(args.tokenizer, args.encoding)
    chunk_tokens = {cid(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}

    dense_rankings = load_flat_rankings(args.dense_rankings)
    fixed_by_seed = load_seed_rankings(args.fixed_linucb_rankings, method=args.method)
    budget_by_seed = load_budgeted_seed_rankings(args.budgeted_rankings, source_prefix=args.budgeted_prefix)

    rows: List[Dict[str, object]] = []
    details: Dict[str, object] = {
        "dataset": args.dataset,
        "budget_ratio": args.budget_ratio,
        "min_keep": args.min_keep,
        "conservative_ratio": args.conservative_ratio,
        "calibration_count": len(calibration_queries),
        "test_count": len(test_queries),
        "seeds": seeds,
        "same_query": {},
        "generalization": {},
    }

    for seed in seeds:
        if seed not in fixed_by_seed or seed not in budget_by_seed:
            raise ValueError(f"Missing seed {seed} in fixed or budgeted rankings")
        context = load_seed_context(
            args.artifact_dir,
            dataset=args.dataset,
            seed=seed,
            model_name=args.model_name,
            corpus=corpus,
            queries=queries,
            context_dim=args.context_dim,
            n_clusters=args.n_clusters,
        )
        fixed_rankings = fixed_by_seed[seed]
        budget_rankings = budget_by_seed[seed]

        dense_affected_all, compression_affected_all = affected_queries(
            queries,
            dense_rankings,
            fixed_rankings,
            budget_rankings,
            top_k=args.top_k,
        )
        dense_affected_test, compression_affected_test = affected_queries(
            test_queries,
            dense_rankings,
            fixed_rankings,
            budget_rankings,
            top_k=args.top_k,
        )
        details["same_query"][seed] = {
            "dense_affected_all": [qid(query) for query in dense_affected_all],
            "compression_affected_all": [qid(query) for query in compression_affected_all],
            "dense_affected_test": [qid(query) for query in dense_affected_test],
            "compression_affected_test": [qid(query) for query in compression_affected_test],
        }

        same_rows, same_variants = same_query_recovery_rows(
            seed=seed,
            queries=queries,
            affected=dense_affected_all,
            dense_rankings=dense_rankings,
            fixed_rankings=fixed_rankings,
            budget_rankings=budget_rankings,
            context=context,
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
            budget_ratio=args.budget_ratio,
            min_keep=args.min_keep,
            conservative_ratio=args.conservative_ratio,
        )
        rows.extend(same_rows)
        rows.extend(all_query_rows(
            protocol="same_query_retry_all_queries",
            seed=seed,
            queries=queries,
            dense_rankings=dense_rankings,
            before_rankings=budget_rankings,
            variants=same_variants,
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
        ))

        learned = learn_arm_feedback_map(
            calibration_queries,
            dense_rankings,
            budget_rankings,
            context,
            min_examples=args.min_learned_arm_examples,
            top_k=args.top_k,
        )
        generalized = generalized_rankings(
            test_queries,
            fixed_rankings,
            budget_rankings,
            context,
            learned,
            chunk_tokens,
            top_k=args.top_k,
            budget_ratio=args.budget_ratio,
            min_keep=args.min_keep,
            conservative_ratio=args.conservative_ratio,
        )
        details["generalization"][seed] = {
            "learned": {str(key): value for key, value in learned.items()},
            "test_dense_affected": [qid(query) for query in dense_affected_test],
            "test_compression_affected": [qid(query) for query in compression_affected_test],
        }
        rows.extend(all_query_rows(
            protocol="calibration_to_test",
            seed=seed,
            queries=test_queries,
            dense_rankings=dense_rankings,
            before_rankings=budget_rankings,
            variants=generalized,
            chunk_tokens=chunk_tokens,
            top_k=args.top_k,
            learned_arm_count=len(learned),
        ))

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output_prefix.with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    write_csv(csv_path, rows)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"summary": details, "rows": rows}, f, ensure_ascii=False, indent=2, sort_keys=True)
    write_markdown(md_path, summary=details, rows=rows)

    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
