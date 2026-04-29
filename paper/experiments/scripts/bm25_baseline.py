#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BM25 retrieval baseline for processed IntentWeight experiment datasets."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
_METRICS_PATH = SCRIPT_DIR / "retrieval_metrics.py"
_spec = importlib.util.spec_from_file_location("retrieval_metrics", _METRICS_PATH)
retrieval_metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(retrieval_metrics)
_GUARDRAILS_PATH = SCRIPT_DIR / "experiment_guardrails.py"
_guardrails_spec = importlib.util.spec_from_file_location("experiment_guardrails", _GUARDRAILS_PATH)
experiment_guardrails = importlib.util.module_from_spec(_guardrails_spec)
_guardrails_spec.loader.exec_module(experiment_guardrails)

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DATASETS = ("pubmedqa", "banking77", "emanual", "cuad")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> List[str]:
    """Simple deterministic tokenizer for lexical BM25 baselines."""
    return TOKEN_RE.findall((text or "").lower())


def top_k_indices(scores: Sequence[float], k: int) -> List[int]:
    """Return top-k score indices, sorted by score desc and index asc for ties."""
    if k <= 0:
        return []
    scores_array = np.asarray(scores)
    if scores_array.size == 0:
        return []
    k = min(k, scores_array.size)
    if k == scores_array.size:
        candidates = np.arange(scores_array.size)
    else:
        candidates = np.argpartition(-scores_array, k - 1)[:k]
    ordered = sorted((int(idx) for idx in candidates), key=lambda idx: (-float(scores_array[idx]), idx))
    return ordered


class SparseBM25:
    """Sparse inverted-index BM25 scorer.

    rank_bm25 is fine for small corpora but its ``get_scores`` scans all
    documents for each query term. CUAD has 675k chunks, so this scorer only
    visits postings for query terms that actually occur.
    """

    def __init__(self, tokenized_corpus: Sequence[Sequence[str]], *, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.n_docs = len(tokenized_corpus)
        self.doc_lens = np.array([len(doc) for doc in tokenized_corpus], dtype=np.float32)
        self.avgdl = float(np.mean(self.doc_lens)) if self.n_docs else 0.0
        self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self.idf: dict[str, float] = {}

        dfs: Counter[str] = Counter()
        for doc_idx, tokens in enumerate(tokenized_corpus):
            counts = Counter(tokens)
            for term, freq in counts.items():
                self.postings[term].append((doc_idx, int(freq)))
                dfs[term] += 1

        for term, df in dfs.items():
            self.idf[term] = float(np.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0))

    def get_scores(self, query_tokens: Sequence[str]) -> Dict[int, float]:
        scores: Dict[int, float] = {}
        if not query_tokens or not self.n_docs or self.avgdl == 0.0:
            return scores

        for term in set(query_tokens):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for doc_idx, freq in self.postings.get(term, []):
                denom = freq + self.k1 * (1.0 - self.b + self.b * float(self.doc_lens[doc_idx]) / self.avgdl)
                score = idf * (freq * (self.k1 + 1.0) / denom)
                scores[doc_idx] = scores.get(doc_idx, 0.0) + score
        return scores


def top_k_sparse_indices(scores: Mapping[int, float], k: int) -> List[int]:
    """Return top-k sparse score indices, sorted by score desc and index asc."""
    if k <= 0 or not scores:
        return []
    return [idx for idx, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]]


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def parse_ks(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def parse_datasets(value: str) -> tuple[str, ...]:
    if value == "all":
        return DEFAULT_DATASETS
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _chunk_id(chunk: Mapping) -> str:
    chunk_id = chunk.get("chunk_id") or chunk.get("id")
    if chunk_id is None:
        raise ValueError(f"Corpus chunk missing chunk_id/id: {chunk}")
    return str(chunk_id)


def _query_id(query: Mapping) -> str:
    query_id = query.get("query_id") or query.get("id")
    if query_id is None:
        raise ValueError(f"Query missing query_id/id: {query}")
    return str(query_id)


def run_bm25(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    *,
    top_k: int = 10,
    ks: Sequence[int] = (1, 5, 10),
    max_queries: int | None = None,
    max_corpus: int | None = None,
) -> Dict[str, object]:
    """Run BM25 over corpus chunks and evaluate processed queries."""
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
    if not corpus:
        raise ValueError("corpus must not be empty")
    if max_corpus is not None:
        if max_corpus <= 0:
            raise ValueError(f"max_corpus must be positive, got {max_corpus}")
        corpus = corpus[:max_corpus]
    if max_queries is not None:
        if max_queries <= 0:
            raise ValueError(f"max_queries must be positive, got {max_queries}")
        queries = queries[:max_queries]

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    tokenized_corpus = [tokenize(str(chunk.get("text", ""))) for chunk in corpus]
    bm25 = SparseBM25(tokenized_corpus)

    rankings: Dict[str, List[str]] = {}
    effective_top_k = min(top_k, len(corpus))
    for query in queries:
        qid = _query_id(query)
        query_tokens = tokenize(str(query.get("text", "")))
        scores = bm25.get_scores(query_tokens)
        top_indices = top_k_sparse_indices(scores, effective_top_k)
        rankings[qid] = [chunk_ids[idx] for idx in top_indices]

    metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    return {"rankings": rankings, "metrics": metrics}


def run_dataset(
    dataset: str,
    data_dir: Path,
    output_dir: Path,
    top_k: int,
    ks: Sequence[int],
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
) -> Dict[str, object]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    corpus = load_json_list(corpus_path)
    queries = load_json_list(queries_path)
    selected_queries = experiment_guardrails.apply_query_controls(
        queries,
        query_split=query_split,
        max_queries=max_queries,
    )
    resolved_corpus_sampling = experiment_guardrails.resolve_corpus_sampling(dataset, max_corpus, corpus_sampling)
    selected_corpus = experiment_guardrails.apply_corpus_controls(
        corpus,
        max_corpus=max_corpus,
        queries=selected_queries,
        corpus_sampling=resolved_corpus_sampling,
        random_seed=sampling_seed,
    )
    gt_coverage = experiment_guardrails.assert_gt_corpus_coverage(selected_queries, selected_corpus)

    start = time.perf_counter()
    result = run_bm25(selected_corpus, selected_queries, top_k=top_k, ks=ks)
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"bm25_{dataset}_rankings.json"
    metrics_path = output_dir / f"bm25_{dataset}_metrics.json"

    metrics = {
        "dataset": dataset,
        "method": "bm25",
        "top_k": top_k,
        "ks": list(ks),
        "num_corpus_chunks": len(selected_corpus),
        "num_total_corpus_chunks": len(corpus),
        "num_total_queries": len(queries),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "elapsed_sec": round(elapsed_sec, 3),
        **experiment_guardrails.build_run_metadata(
            dataset=dataset,
            queries=selected_queries,
            all_queries=queries,
            corpus=selected_corpus,
            all_corpus=corpus,
            max_queries=max_queries,
            max_corpus=max_corpus,
            corpus_sampling=resolved_corpus_sampling,
            requested_query_split=query_split,
            top_k=top_k,
            ks=ks,
        ),
        **gt_coverage,
        **result["metrics"],
    }

    with rankings_path.open("w", encoding="utf-8") as f:
        json.dump(result["rankings"], f, ensure_ascii=False)
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, sort_keys=True)

    return metrics


def update_summary(summary_path: Path, metrics_rows: Iterable[Mapping]) -> None:
    rows = list(metrics_rows)
    if not rows:
        return

    existing: Dict[tuple[str, str], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(row.get("dataset", ""), row.get("method", ""))] = row

    for row in rows:
        existing[(str(row["dataset"]), str(row["method"]))] = row

    metric_keys = sorted({key for row in existing.values() for key in row if "@" in key})
    fieldnames = [
        "dataset",
        "method",
        "num_queries",
        "num_skipped_no_gt",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "num_total_queries",
        "num_query_candidates",
        "max_queries",
        "max_corpus",
        "corpus_sampling",
        "top_k",
        "task_type",
        "scope",
        "query_split",
        "query_splits",
        "query_scope",
        "corpus_scope",
        "num_queries_with_gt",
        "num_queries_with_gt_in_corpus",
        "num_queries_gt_missing_from_corpus",
        "num_gt_refs",
        "num_gt_refs_in_corpus",
        "num_gt_refs_missing_from_corpus",
        "gt_query_coverage",
        "gt_ref_coverage",
        "gt_corpus_guardrail",
        "comparable_group",
        "is_comparable",
        "metric_ks",
        *metric_keys,
        "elapsed_sec",
        "notes",
    ]

    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow({
                name: "|".join(str(item) for item in value) if isinstance(value, (list, tuple)) else value
                for name, value in existing[key].items()
            })


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run BM25 retrieval baseline")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10", help="Comma-separated metric cutoffs")
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="Evaluate only the first N queries; useful for reproducible CUAD smoke/sample runs",
    )
    parser.add_argument("--max-corpus", type=int, default=None, help="Use only the first N corpus chunks")
    parser.add_argument("--query-split", default=None, help="Evaluate only one query split, e.g. test")
    parser.add_argument(
        "--corpus-sampling",
        default="auto",
        choices=sorted(experiment_guardrails.CORPUS_SAMPLING_STRATEGIES),
        help="Corpus sampling strategy; auto uses GT-anchored CUAD samples when max-corpus is set",
    )
    parser.add_argument("--sampling-seed", type=int, default=13, help="Random seed for sampled distractors")
    args = parser.parse_args(argv)

    datasets = parse_datasets(args.dataset)
    ks = parse_ks(args.ks)
    metrics_rows = []
    for dataset in datasets:
        print(f"Running BM25 baseline: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            args.top_k,
            ks,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
        )
        metrics_rows.append(metrics)
        metric_text = ", ".join(
            f"{key}={metrics[key]:.4f}" for key in sorted(metrics) if "@" in key
        )
        print(
            f"  chunks={metrics['num_corpus_chunks']} queries={metrics['num_queries']} "
            f"skipped_no_gt={metrics['num_skipped_no_gt']} "
            f"gt_query_coverage={metrics['gt_query_coverage']:.4f} elapsed={metrics['elapsed_sec']}s"
        )
        print(f"  {metric_text}")

    update_summary(args.output_dir / "bm25_baseline_summary.csv", metrics_rows)
    print(f"Summary: {args.output_dir / 'bm25_baseline_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
