#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prequential global LinUCB retrieval baseline for processed datasets."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dense_baseline = _load_script_module("dense_baseline", SCRIPT_DIR / "dense_baseline.py")
experiment_guardrails = _load_script_module("experiment_guardrails", SCRIPT_DIR / "experiment_guardrails.py")
retrieval_metrics = _load_script_module("retrieval_metrics", SCRIPT_DIR / "retrieval_metrics.py")

DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DATASETS = ("pubmedqa", "banking77", "emanual", "cuad")
DEFAULT_MODEL = dense_baseline.DEFAULT_MODEL


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def parse_ints(value: str) -> tuple[int, ...]:
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


def _ground_truth(query: Mapping) -> set[str]:
    return {str(chunk_id) for chunk_id in (query.get("ground_truth_chunk_ids") or [])}


def _safe_context_dim(requested: int, n_samples: int, embedding_dim: int) -> int:
    if requested <= 0:
        raise ValueError(f"context_dim must be positive, got {requested}")
    return max(1, min(requested, n_samples, embedding_dim))


def fit_context_projection(corpus_embeddings: np.ndarray, query_embeddings: np.ndarray, context_dim: int):
    """Fit PCA on corpus embeddings only, then transform corpus/query vectors."""
    effective_dim = _safe_context_dim(context_dim, len(corpus_embeddings), corpus_embeddings.shape[1])
    if effective_dim == corpus_embeddings.shape[1]:
        return None, corpus_embeddings.astype(np.float32), query_embeddings.astype(np.float32)
    pca = PCA(n_components=effective_dim, random_state=0)
    corpus_context = pca.fit_transform(corpus_embeddings).astype(np.float32)
    query_context = pca.transform(query_embeddings).astype(np.float32)
    return pca, corpus_context, query_context


def l2_normalize(array: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, norms, out=np.zeros_like(array), where=norms > 0)


class GlobalLinUCBPolicy:
    def __init__(
        self,
        n_arms: int,
        context_dim: int,
        alpha: float = 1.0,
        alpha_decay: float = 0.01,
        alpha_min: float = 0.3,
        seed: int = 42,
        tie_jitter: float = 1e-9,
    ):
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha
        self.alpha_decay = alpha_decay
        self.alpha_min = alpha_min
        self.seed = seed
        self.tie_jitter = tie_jitter
        self.A = [np.eye(self.context_dim, dtype=np.float32) for _ in range(self.n_arms)]
        self.b = [np.zeros(self.context_dim, dtype=np.float32) for _ in range(self.n_arms)]
        self.pull_counts = [0] * self.n_arms
        self.total_rewards = [0.0] * self.n_arms
        self.rng = np.random.default_rng(self.seed)

    @property
    def total_feedback(self) -> int:
        return sum(self.pull_counts)

    @property
    def effective_alpha(self) -> float:
        return max(self.alpha_min, self.alpha / (1.0 + self.alpha_decay * self.total_feedback))

    def scores(self, context: np.ndarray) -> np.ndarray:
        scores = np.zeros(self.n_arms, dtype=np.float64)
        alpha = self.effective_alpha
        for arm in range(self.n_arms):
            theta = np.linalg.solve(self.A[arm], self.b[arm])
            point_estimate = float(np.dot(theta, context))
            a_inv_context = np.linalg.solve(self.A[arm], context)
            uncertainty = float(np.sqrt(max(0.0, np.dot(context, a_inv_context))))
            scores[arm] = point_estimate + alpha * uncertainty
        if self.tie_jitter:
            scores += self.rng.normal(0.0, self.tie_jitter, size=self.n_arms)
        return scores

    def select_arms(self, context: np.ndarray, candidate_arms: int) -> List[int]:
        if candidate_arms <= 0:
            raise ValueError(f"candidate_arms must be positive, got {candidate_arms}")
        scores = self.scores(context)
        k = min(candidate_arms, self.n_arms)
        return np.argsort(scores)[-k:][::-1].astype(int).tolist()

    def update(self, arm: int, context: np.ndarray, reward: float, *, weight: float = 1.0) -> None:
        if arm < 0 or arm >= self.n_arms:
            raise ValueError(f"Invalid arm index: {arm}")
        if weight <= 0:
            return
        self.A[arm] += float(weight) * np.outer(context, context).astype(np.float32)
        self.b[arm] += float(weight * reward) * context.astype(np.float32)
        self.pull_counts[arm] += 1
        self.total_rewards[arm] += float(reward)


def cluster_corpus(corpus_context: np.ndarray, *, n_clusters: int, seed: int) -> np.ndarray:
    if n_clusters <= 0:
        raise ValueError(f"n_clusters must be positive, got {n_clusters}")
    effective_clusters = min(n_clusters, len(corpus_context))
    if effective_clusters == 1:
        return np.zeros(len(corpus_context), dtype=np.int32)
    clusterer = MiniBatchKMeans(
        n_clusters=effective_clusters,
        random_state=seed,
        n_init=10,
        batch_size=min(2048, max(128, len(corpus_context))),
    )
    return clusterer.fit_predict(corpus_context).astype(np.int32)


def retrieve_from_arms(
    query_embedding: np.ndarray,
    corpus_embeddings: np.ndarray,
    chunk_ids: Sequence[str],
    arm_labels: np.ndarray,
    selected_arms: Sequence[int],
    *,
    top_k: int,
) -> List[str]:
    if top_k <= 0:
        return []
    selected = np.isin(arm_labels, np.asarray(selected_arms, dtype=np.int32))
    candidate_indices = np.flatnonzero(selected)
    if candidate_indices.size == 0:
        return []
    candidate_embeddings = corpus_embeddings[candidate_indices]
    scores = candidate_embeddings @ query_embedding
    k = min(top_k, candidate_indices.size)
    if k == candidate_indices.size:
        top_local = np.arange(candidate_indices.size)
    else:
        top_local = np.argpartition(-scores, k - 1)[:k]
    ordered_local = sorted(top_local.tolist(), key=lambda idx: (-float(scores[idx]), int(candidate_indices[idx])))
    return [chunk_ids[int(candidate_indices[idx])] for idx in ordered_local]


def _arm_reward(ranking: Sequence[str], ground_truth: set[str], arm: int, arm_labels_by_chunk: Mapping[str, int]) -> float:
    if not ground_truth:
        return 0.0
    for chunk_id in ranking:
        if arm_labels_by_chunk.get(str(chunk_id)) == arm and str(chunk_id) in ground_truth:
            return 1.0
    return 0.0


def run_prequential_seed(
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    *,
    seed: int,
    top_k: int,
    ks: Sequence[int],
    n_clusters: int,
    context_dim: int,
    candidate_arms: int,
    alpha: float,
    alpha_decay: float,
    alpha_min: float,
) -> Dict[str, object]:
    if not corpus:
        raise ValueError("corpus must not be empty")
    if not queries:
        raise ValueError("queries must not be empty")

    _, corpus_context, query_context = fit_context_projection(corpus_embeddings, query_embeddings, context_dim)
    corpus_context = l2_normalize(corpus_context)
    query_context = l2_normalize(query_context)

    arm_labels = cluster_corpus(corpus_context, n_clusters=n_clusters, seed=seed)
    n_effective_arms = int(np.max(arm_labels)) + 1
    policy = GlobalLinUCBPolicy(
        n_arms=n_effective_arms,
        context_dim=query_context.shape[1],
        alpha=alpha,
        alpha_decay=alpha_decay,
        alpha_min=alpha_min,
        seed=seed,
    )

    rng = np.random.default_rng(seed)
    stream_indices = np.arange(len(queries))
    rng.shuffle(stream_indices)

    chunk_ids = [_chunk_id(chunk) for chunk in corpus]
    arm_labels_by_chunk = {chunk_id: int(label) for chunk_id, label in zip(chunk_ids, arm_labels)}

    rankings: Dict[str, List[str]] = {}
    rewards: List[float] = []
    for query_idx in stream_indices:
        query = queries[int(query_idx)]
        qid = _query_id(query)
        context = query_context[int(query_idx)]
        selected_arms = policy.select_arms(context, candidate_arms)
        ranking = retrieve_from_arms(
            query_embeddings[int(query_idx)],
            corpus_embeddings,
            chunk_ids,
            arm_labels,
            selected_arms,
            top_k=top_k,
        )
        rankings[qid] = ranking

        gt = _ground_truth(query)
        selected_rewards = []
        for arm in selected_arms:
            reward = _arm_reward(ranking, gt, arm, arm_labels_by_chunk)
            policy.update(arm, context, reward)
            selected_rewards.append(reward)
        rewards.append(max(selected_rewards) if selected_rewards else 0.0)

    metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=ks)
    metrics.update({
        "seed": seed,
        "avg_feedback_reward": float(np.mean(rewards)) if rewards else 0.0,
        "final_effective_alpha": float(policy.effective_alpha),
        "n_effective_arms": n_effective_arms,
        "total_feedback_updates": int(policy.total_feedback),
    })
    return {"rankings": rankings, "metrics": metrics}


def aggregate_seed_metrics(seed_metrics: Sequence[Mapping]) -> Dict[str, object]:
    if not seed_metrics:
        return {}
    numeric_keys = sorted({
        key
        for row in seed_metrics
        for key, value in row.items()
        if isinstance(value, (int, float)) and key != "seed"
    })
    aggregated: Dict[str, object] = {"num_seeds": len(seed_metrics)}
    for key in numeric_keys:
        values = np.asarray([float(row[key]) for row in seed_metrics if key in row], dtype=np.float64)
        if values.size:
            aggregated[f"{key}_mean"] = float(np.mean(values))
            aggregated[f"{key}_std"] = float(np.std(values, ddof=0))
    return aggregated


def run_dataset(
    dataset: str,
    data_dir: Path,
    output_dir: Path,
    encoder,
    *,
    model_name: str,
    top_k: int,
    ks: Sequence[int],
    batch_size: int,
    seeds: Sequence[int],
    n_clusters: int,
    context_dim: int,
    candidate_arms: int,
    alpha: float,
    alpha_decay: float,
    alpha_min: float,
    max_queries: int | None = None,
    max_corpus: int | None = None,
    query_split: str | None = None,
    corpus_sampling: str | None = None,
    sampling_seed: int = 13,
) -> Dict[str, object]:
    corpus_path = data_dir / f"{dataset}_corpus.json"
    queries_path = data_dir / f"{dataset}_queries.json"
    corpus_all = load_json_list(corpus_path)
    queries_all = load_json_list(queries_path)
    queries = experiment_guardrails.apply_query_controls(queries_all, query_split=query_split, max_queries=max_queries)
    resolved_corpus_sampling = experiment_guardrails.resolve_corpus_sampling(dataset, max_corpus, corpus_sampling)
    corpus = experiment_guardrails.apply_corpus_controls(
        corpus_all,
        max_corpus=max_corpus,
        queries=queries,
        corpus_sampling=resolved_corpus_sampling,
        random_seed=sampling_seed,
    )
    gt_coverage = experiment_guardrails.assert_gt_corpus_coverage(queries, corpus)

    start = time.perf_counter()
    corpus_embeddings = dense_baseline.encode_texts(
        encoder,
        [str(chunk.get("text", "")) for chunk in corpus],
        batch_size=batch_size,
    )
    query_embeddings = dense_baseline.encode_texts(
        encoder,
        [str(query.get("text", "")) for query in queries],
        batch_size=batch_size,
    )

    seed_results = []
    for seed in seeds:
        seed_results.append(run_prequential_seed(
            corpus,
            queries,
            corpus_embeddings,
            query_embeddings,
            seed=seed,
            top_k=top_k,
            ks=ks,
            n_clusters=n_clusters,
            context_dim=context_dim,
            candidate_arms=candidate_arms,
            alpha=alpha,
            alpha_decay=alpha_decay,
            alpha_min=alpha_min,
        ))
    elapsed_sec = time.perf_counter() - start

    output_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = output_dir / f"linucb_{dataset}_prequential_rankings.json"
    metrics_path = output_dir / f"linucb_{dataset}_prequential_metrics.json"

    per_seed_metrics = [result["metrics"] for result in seed_results]
    representative = per_seed_metrics[0]
    aggregated = aggregate_seed_metrics(per_seed_metrics)
    metadata = {
        "dataset": dataset,
        "method": "linucb_global",
        "model": model_name,
        "protocol": "prequential",
        "feedback_source": "gt_derived_topk_arm_reward",
        "online_learning_scope": "global_arm_updates",
        "top_k": top_k,
        "ks": list(ks),
        "batch_size": batch_size,
        "seeds": list(seeds),
        "n_clusters_requested": n_clusters,
        "context_dim_requested": context_dim,
        "candidate_arms": candidate_arms,
        "alpha": alpha,
        "alpha_decay": alpha_decay,
        "alpha_min": alpha_min,
        "num_corpus_chunks": len(corpus),
        "num_total_corpus_chunks": len(corpus_all),
        "num_total_queries": len(queries_all),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "elapsed_sec": round(elapsed_sec, 3),
        **experiment_guardrails.build_run_metadata(
            dataset=dataset,
            queries=queries,
            all_queries=queries_all,
            corpus=corpus,
            all_corpus=corpus_all,
            max_queries=max_queries,
            max_corpus=max_corpus,
            corpus_sampling=resolved_corpus_sampling,
            requested_query_split=query_split,
            top_k=top_k,
            ks=ks,
        ),
        **gt_coverage,
    }
    metrics = {
        **metadata,
        **{key: value for key, value in representative.items() if key in {"num_queries", "num_skipped_no_gt"}},
        **aggregated,
        "per_seed": per_seed_metrics,
    }

    rankings = {
        str(result["metrics"]["seed"]): result["rankings"]
        for result in seed_results
    }
    rankings_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def _stringify_csv_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def update_summary(summary_path: Path, rows: Iterable[Mapping]) -> None:
    new_rows = list(rows)
    if not new_rows:
        return
    existing: Dict[tuple[str, str, str], Mapping] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(row.get("dataset", ""), row.get("method", ""), row.get("model", ""))] = row
    for row in new_rows:
        existing[(str(row["dataset"]), str(row["method"]), str(row.get("model", "")))] = row

    metric_keys = sorted({key for row in existing.values() for key in row if "@" in key or key.endswith("_reward_mean")})
    fieldnames = [
        "dataset",
        "method",
        "model",
        "protocol",
        "task_type",
        "scope",
        "query_split",
        "corpus_scope",
        "corpus_sampling",
        "num_queries",
        "num_skipped_no_gt",
        "num_queries_with_gt",
        "num_queries_with_gt_in_corpus",
        "num_queries_gt_missing_from_corpus",
        "num_gt_refs",
        "num_gt_refs_in_corpus",
        "num_gt_refs_missing_from_corpus",
        "gt_query_coverage",
        "gt_ref_coverage",
        "gt_corpus_guardrail",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "num_total_queries",
        "max_queries",
        "max_corpus",
        "top_k",
        "metric_ks",
        "num_seeds",
        "seeds",
        "n_clusters_requested",
        "n_effective_arms_mean",
        "context_dim_requested",
        "candidate_arms",
        "alpha",
        "alpha_decay",
        "alpha_min",
        *metric_keys,
        "elapsed_sec",
        "notes",
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow({
                name: _stringify_csv_value(value)
                for name, value in existing[key].items()
            })


def load_sentence_transformer(model_name: str, *, device: str | None = None, local_files_only: bool = False):
    return dense_baseline.load_sentence_transformer(model_name, device=device, local_files_only=local_files_only)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run global LinUCB prequential retrieval baseline")
    parser.add_argument("--dataset", default="all", help="Dataset name, comma list, or all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default=None)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--ks", default="1,5,10")
    parser.add_argument("--seeds", default="13,17,19")
    parser.add_argument("--n-clusters", type=int, default=32)
    parser.add_argument("--context-dim", type=int, default=64)
    parser.add_argument("--candidate-arms", type=int, default=3)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--alpha-decay", type=float, default=0.01)
    parser.add_argument("--alpha-min", type=float, default=0.3)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--max-corpus", type=int, default=None)
    parser.add_argument("--query-split", default=None)
    parser.add_argument(
        "--corpus-sampling",
        default="auto",
        choices=sorted(experiment_guardrails.CORPUS_SAMPLING_STRATEGIES),
        help="Corpus sampling strategy; auto uses GT-anchored CUAD samples when max-corpus is set",
    )
    parser.add_argument("--sampling-seed", type=int, default=13)
    args = parser.parse_args(argv)

    datasets = parse_datasets(args.dataset)
    ks = parse_ints(args.ks)
    seeds = parse_ints(args.seeds)
    encoder = load_sentence_transformer(args.model, device=args.device, local_files_only=args.local_files_only)

    rows = []
    for dataset in datasets:
        print(f"Running global LinUCB prequential baseline: {dataset}")
        metrics = run_dataset(
            dataset,
            args.data_dir,
            args.output_dir,
            encoder,
            model_name=args.model,
            top_k=args.top_k,
            ks=ks,
            batch_size=args.batch_size,
            seeds=seeds,
            n_clusters=args.n_clusters,
            context_dim=args.context_dim,
            candidate_arms=args.candidate_arms,
            alpha=args.alpha,
            alpha_decay=args.alpha_decay,
            alpha_min=args.alpha_min,
            max_queries=args.max_queries,
            max_corpus=args.max_corpus,
            query_split=args.query_split,
            corpus_sampling=args.corpus_sampling,
            sampling_seed=args.sampling_seed,
        )
        rows.append(metrics)
        print(
            f"  queries={metrics.get('num_queries')} skipped_no_gt={metrics.get('num_skipped_no_gt')} "
            f"gt_query_coverage={metrics.get('gt_query_coverage', 0.0):.4f} "
            f"recall@10_mean={metrics.get('recall@10_mean', 0.0):.4f} "
            f"mrr@10_mean={metrics.get('mrr@10_mean', 0.0):.4f} "
            f"elapsed={metrics['elapsed_sec']}s"
        )

    update_summary(args.output_dir / "linucb_online_summary.csv", rows)
    print(f"Summary: {args.output_dir / 'linucb_online_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
