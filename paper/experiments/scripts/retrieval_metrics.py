#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieval evaluation metrics for IntentRoute baselines.

The processed query files use ``ground_truth_chunk_ids`` as relevance labels.
This module evaluates ranked chunk-id lists against those labels and reports
query-level Hit@k, standard evidence Recall@k, MRR@k, and nDCG@k.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence


DEFAULT_KS = (1, 5, 10)


def _query_id(query: Mapping) -> str:
    query_id = query.get("query_id") or query.get("id")
    if query_id is None:
        raise ValueError(f"Query missing query_id/id: {query}")
    return str(query_id)


def _ground_truth(query: Mapping) -> set[str]:
    gt = query.get("ground_truth_chunk_ids", [])
    if gt is None:
        return set()
    return {str(chunk_id) for chunk_id in gt}


def hit_at_k(ranking: Sequence[str], ground_truth: set[str], k: int) -> float:
    """Query-level Hit@k: 1 if any relevant chunk appears in top-k, else 0."""
    if not ground_truth:
        return 0.0
    return 1.0 if any(str(chunk_id) in ground_truth for chunk_id in ranking[:k]) else 0.0


def evidence_recall_at_k(ranking: Sequence[str], ground_truth: set[str], k: int) -> float:
    """Standard evidence Recall@k over all relevant chunks for a query."""
    if not ground_truth:
        return 0.0
    retrieved = {str(chunk_id) for chunk_id in ranking[:k]}
    return len(retrieved & ground_truth) / len(ground_truth)


def recall_at_k(ranking: Sequence[str], ground_truth: set[str], k: int) -> float:
    """Legacy binary Recall@k alias kept for backward-compatible result files."""
    return hit_at_k(ranking, ground_truth, k)


def mrr_at_k(ranking: Sequence[str], ground_truth: set[str], k: int) -> float:
    """Reciprocal rank of the first relevant chunk within top-k."""
    if not ground_truth:
        return 0.0
    for rank, chunk_id in enumerate(ranking[:k], start=1):
        if str(chunk_id) in ground_truth:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranking: Sequence[str], ground_truth: set[str], k: int) -> float:
    """nDCG@k with binary relevance and multiple relevant chunks."""
    if not ground_truth:
        return 0.0

    dcg = 0.0
    seen: set[str] = set()
    for rank, chunk_id in enumerate(ranking[:k], start=1):
        chunk_id = str(chunk_id)
        if chunk_id in ground_truth and chunk_id not in seen:
            dcg += 1.0 / math.log2(rank + 1)
            seen.add(chunk_id)

    ideal_hits = min(len(ground_truth), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def evaluate_rankings(
    queries: Iterable[Mapping],
    rankings: Mapping[str, Sequence[str]],
    ks: Sequence[int] = DEFAULT_KS,
    *,
    skip_empty_gt: bool = True,
) -> Dict[str, float]:
    """Evaluate ranked retrieval results for a collection of queries.

    ``hit@k`` is the query-level success metric historically stored as
    ``recall@k`` in this project. ``evidence_recall@k`` is the standard IR
    recall over all ground-truth chunks. The legacy ``recall@k`` key remains a
    binary hit-rate alias so existing result readers keep working.

    Args:
        queries: Processed query records containing ``query_id`` and
            ``ground_truth_chunk_ids``.
        rankings: Mapping from query_id to ranked chunk_id list.
        ks: Cutoffs to evaluate.
        skip_empty_gt: Whether to exclude queries with no ground-truth chunks.
            This defaults to True because CUAD/RAGBench contains answerable and
            no-evidence queries; retrieval metrics are only meaningful where a
            positive target exists.
    """
    ks = tuple(sorted({int(k) for k in ks}))
    if not ks or any(k <= 0 for k in ks):
        raise ValueError(f"ks must contain positive integers, got {ks}")

    totals: Dict[str, float] = {"num_queries": 0, "num_skipped_no_gt": 0}
    for k in ks:
        totals[f"hit@{k}"] = 0.0
        totals[f"recall@{k}"] = 0.0
        totals[f"evidence_recall@{k}"] = 0.0
        totals[f"mrr@{k}"] = 0.0
        totals[f"ndcg@{k}"] = 0.0

    for query in queries:
        qid = _query_id(query)
        gt = _ground_truth(query)
        if not gt and skip_empty_gt:
            totals["num_skipped_no_gt"] += 1
            continue

        ranking = [str(chunk_id) for chunk_id in rankings.get(qid, [])]
        totals["num_queries"] += 1
        for k in ks:
            hit = hit_at_k(ranking, gt, k)
            totals[f"hit@{k}"] += hit
            totals[f"recall@{k}"] += hit
            totals[f"evidence_recall@{k}"] += evidence_recall_at_k(ranking, gt, k)
            totals[f"mrr@{k}"] += mrr_at_k(ranking, gt, k)
            totals[f"ndcg@{k}"] += ndcg_at_k(ranking, gt, k)

    n = totals["num_queries"]
    if n:
        for k in ks:
            totals[f"hit@{k}"] /= n
            totals[f"recall@{k}"] /= n
            totals[f"evidence_recall@{k}"] /= n
            totals[f"mrr@{k}"] /= n
            totals[f"ndcg@{k}"] /= n

    totals["num_queries"] = int(totals["num_queries"])
    totals["num_skipped_no_gt"] = int(totals["num_skipped_no_gt"])
    return totals


def load_queries(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Queries file must contain a JSON list: {path}")
    return data


def load_rankings(path: Path) -> Dict[str, List[str]]:
    """Load rankings from JSON mapping or list of per-query records."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return {str(qid): [str(c) for c in ranking] for qid, ranking in data.items()}

    if isinstance(data, list):
        rankings: Dict[str, List[str]] = {}
        for item in data:
            qid = item.get("query_id") or item.get("id")
            ranking = item.get("ranking") or item.get("ranked_chunk_ids") or item.get("chunk_ids")
            if qid is None or ranking is None:
                raise ValueError(f"Ranking record missing query_id/ranking: {item}")
            rankings[str(qid)] = [str(chunk_id) for chunk_id in ranking]
        return rankings

    raise ValueError(f"Rankings file must contain a JSON mapping or list: {path}")


def parse_ks(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval rankings")
    parser.add_argument("--queries", required=True, type=Path, help="Processed queries JSON")
    parser.add_argument("--rankings", required=True, type=Path, help="Ranking JSON")
    parser.add_argument("--ks", default="1,5,10", help="Comma-separated cutoffs")
    parser.add_argument(
        "--include-empty-gt",
        action="store_true",
        help="Include queries with no ground-truth chunks as zero-score examples",
    )
    args = parser.parse_args()

    metrics = evaluate_rankings(
        load_queries(args.queries),
        load_rankings(args.rankings),
        parse_ks(args.ks),
        skip_empty_gt=not args.include_empty_gt,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
