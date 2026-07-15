#!/usr/bin/env python3
"""Summarize and audit the preregistered Task73 LoTTE domain expansion."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "experiments" / "data" / "processed"
RESULTS = ROOT / "paper" / "experiments" / "results"
DEFAULT_OUTPUT = RESULTS / "task73_lotte_domain_expansion"
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
SEEDS = ("13", "17", "19")
ROUTING_MODES = ("full_multi_route", "gated_cost_aware")
BOOTSTRAP_SAMPLES = 10_000
LOTTE_SOURCE_REVISION = "a9006514d20ec3353082b4272bf46a20dd96a195"


DOMAIN_SPECS = {
    "recreation": {
        "dataset": "lotte_recreation_search_100k",
        "display": "LoTTE recreation/search",
    },
    "writing": {
        "dataset": "lotte_writing_search_100k",
        "display": "LoTTE writing/search",
    },
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def only_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise ValueError(f"Expected one {pattern!r} in {directory}, found {len(matches)}")
    return matches[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tokens(text: object) -> set[str]:
    return set(TOKEN_RE.findall(str(text or "").lower()))


def query_hit(query: Mapping[str, Any], ranking: Sequence[str], top_k: int = 10) -> int:
    ground_truth = {str(item) for item in query.get("ground_truth_chunk_ids", [])}
    return int(bool(ground_truth.intersection(str(item) for item in ranking[:top_k])))


def lexical_query_metrics(
    corpus: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
) -> list[dict[str, float]]:
    corpus_tokens = {str(row["chunk_id"]): tokens(row.get("text", "")) for row in corpus}
    rows: list[dict[str, float]] = []
    for query in queries:
        query_tokens = tokens(query.get("text", ""))
        positive_scores = []
        for chunk_id in query.get("ground_truth_chunk_ids", []):
            evidence_tokens = corpus_tokens[str(chunk_id)]
            intersection = len(query_tokens.intersection(evidence_tokens))
            union = len(query_tokens.union(evidence_tokens))
            positive_scores.append({
                "query_token_coverage": intersection / len(query_tokens) if query_tokens else 0.0,
                "jaccard": intersection / union if union else 0.0,
            })
        if not positive_scores:
            raise ValueError(f"Query has no positive evidence: {query.get('query_id')}")
        rows.append({
            "query_token_coverage": max(row["query_token_coverage"] for row in positive_scores),
            "jaccard": max(row["jaccard"] for row in positive_scores),
        })
    return rows


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    seed: int,
    samples: int = BOOTSTRAP_SAMPLES,
) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        raise ValueError("Cannot bootstrap an empty sample")
    rng = np.random.default_rng(seed)
    estimates = np.empty(samples, dtype=np.float64)
    chunk_size = 250
    for start in range(0, samples, chunk_size):
        end = min(start + chunk_size, samples)
        indices = rng.integers(0, array.size, size=(end - start, array.size))
        estimates[start:end] = np.mean(array[indices], axis=1)
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def bootstrap_independent_difference_ci(
    left: Sequence[float],
    right: Sequence[float],
    *,
    seed: int,
    samples: int = BOOTSTRAP_SAMPLES,
) -> tuple[float, float]:
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.size == 0 or right_array.size == 0:
        raise ValueError("Cannot bootstrap an empty domain sample")
    rng = np.random.default_rng(seed)
    estimates = np.empty(samples, dtype=np.float64)
    chunk_size = 200
    for start in range(0, samples, chunk_size):
        end = min(start + chunk_size, samples)
        left_indices = rng.integers(0, left_array.size, size=(end - start, left_array.size))
        right_indices = rng.integers(0, right_array.size, size=(end - start, right_array.size))
        estimates[start:end] = (
            np.mean(left_array[left_indices], axis=1)
            - np.mean(right_array[right_indices], axis=1)
        )
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(f"Task73 audit failed: {name}: {detail}")
    checks.append({"check": name, "status": "PASS", "detail": detail})


def audit_flat_rankings(
    rankings: Mapping[str, Sequence[str]],
    *,
    query_ids: set[str],
    corpus_ids: set[str],
    label: str,
    checks: list[dict[str, str]],
) -> None:
    add_check(checks, f"{label}:query_coverage", set(rankings) == query_ids, f"queries={len(rankings)}")
    invalid = 0
    for ranking in rankings.values():
        top = [str(item) for item in ranking[:10]]
        if len(top) != 10 or len(top) != len(set(top)) or not set(top).issubset(corpus_ids):
            invalid += 1
    add_check(checks, f"{label}:top10_integrity", invalid == 0, f"invalid_queries={invalid}")


def route_row(metrics_rows: Sequence[Mapping[str, Any]], mode: str) -> Mapping[str, Any]:
    matches = [row for row in metrics_rows if row.get("routing_mode") == mode]
    if len(matches) != 1:
        raise ValueError(f"Expected one route row for {mode}, found {len(matches)}")
    return matches[0]


def recovery_extract(payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = payload["rows"]

    def selected(protocol: str, method: str) -> list[Mapping[str, Any]]:
        matches = [row for row in rows if row.get("protocol") == protocol and row.get("method") == method]
        if len(matches) != 3:
            raise ValueError(f"Expected three recovery rows for {protocol}/{method}, found {len(matches)}")
        return matches

    compression_base = selected("same_query_retry_compression_only", "budgeted_before_feedback")
    compression_boost = selected("same_query_retry_compression_only", "same_arm_boost")
    compression_conservative = selected(
        "same_query_retry_compression_only", "same_arm_boost_conservative"
    )
    all_boost = selected("same_query_retry_all_queries", "same_arm_boost")
    all_conservative = selected("same_query_retry_all_queries", "same_arm_boost_conservative")
    return {
        "compression_only_affected_seed_total": sum(int(row["affected_count"]) for row in compression_base),
        "compression_only_arm_boost_recovered_seed_total": sum(
            int(row["recovered_count"]) for row in compression_boost
        ),
        "compression_only_conservative_recovered_seed_total": sum(
            int(row["recovered_count"]) for row in compression_conservative
        ),
        "all_query_arm_boost_hit_delta_vs_before_pp": 100.0 * mean(
            float(row["hit_delta_vs_before"]) for row in all_boost
        ),
        "all_query_arm_boost_saving_pct": mean(
            float(row["token_saving_percent_vs_dense"]) for row in all_boost
        ),
        "all_query_conservative_hit_delta_vs_before_pp": 100.0 * mean(
            float(row["hit_delta_vs_before"]) for row in all_conservative
        ),
        "all_query_conservative_saving_pct": mean(
            float(row["token_saving_percent_vs_dense"]) for row in all_conservative
        ),
    }


def build_domain(domain: str, checks: list[dict[str, str]]) -> dict[str, Any]:
    spec = DOMAIN_SPECS[domain]
    dataset = str(spec["dataset"])
    corpus_path = DATA / f"{dataset}_corpus.json"
    queries_path = DATA / f"{dataset}_queries.json"
    corpus = read_json(corpus_path)
    queries = read_json(queries_path)
    corpus_ids = {str(row["chunk_id"]) for row in corpus}
    query_ids = {str(row["query_id"]) for row in queries}
    gt_refs = [str(item) for query in queries for item in query.get("ground_truth_chunk_ids", [])]
    add_check(checks, f"{domain}:unique_corpus", len(corpus_ids) == len(corpus), f"rows={len(corpus)}")
    add_check(checks, f"{domain}:unique_queries", len(query_ids) == len(queries), f"rows={len(queries)}")
    add_check(checks, f"{domain}:gt_coverage", set(gt_refs).issubset(corpus_ids), f"gt_refs={len(gt_refs)}")

    baseline_metrics: dict[str, Mapping[str, Any]] = {}
    baseline_rankings: dict[str, Mapping[str, Sequence[str]]] = {}
    artifacts: list[Path] = [corpus_path, queries_path]
    for method, suffix in (("dense", "dense"), ("bm25", "bm25"), ("hybrid", "hybrid")):
        directory = RESULTS / f"task73_{domain}_100k_{suffix}"
        metrics_path = only_file(directory, f"{suffix}_*_metrics.json")
        rankings_path = only_file(directory, f"{suffix}_*_rankings.json")
        metrics = read_json(metrics_path)
        rankings = read_json(rankings_path)
        baseline_metrics[method] = metrics
        baseline_rankings[method] = rankings
        artifacts.extend([metrics_path, rankings_path])
        add_check(
            checks,
            f"{domain}:{method}_protocol",
            int(metrics["top_k"]) == 10
            and int(metrics["num_corpus_chunks"]) == len(corpus)
            and int(metrics["num_queries"]) == len(queries),
            f"top_k={metrics['top_k']} corpus={metrics['num_corpus_chunks']} queries={metrics['num_queries']}",
        )
        audit_flat_rankings(
            rankings,
            query_ids=query_ids,
            corpus_ids=corpus_ids,
            label=f"{domain}:{method}",
            checks=checks,
        )
    for method in ("dense", "hybrid"):
        add_check(
            checks,
            f"{domain}:{method}_backbone",
            baseline_metrics[method]["model"] == "sentence-transformers/all-MiniLM-L6-v2",
            str(baseline_metrics[method]["model"]),
        )

    route_summary: dict[str, dict[str, Any]] = {}
    for feedback_key, feedback_mode in (("trust", "trust_weighted"), ("none", "none")):
        directory = RESULTS / f"task73_{domain}_100k_{feedback_key}"
        metrics_path = only_file(directory, "*_prequential_metrics.json")
        rankings_path = only_file(directory, "*_prequential_rankings.json")
        metrics_rows = read_json(metrics_path)
        rankings_payload = read_json(rankings_path)
        artifacts.extend([metrics_path, rankings_path])
        add_check(
            checks,
            f"{domain}:{feedback_key}_route_rows",
            {str(row["routing_mode"]) for row in metrics_rows} == set(ROUTING_MODES),
            f"rows={len(metrics_rows)}",
        )
        for mode in ROUTING_MODES:
            row = route_row(metrics_rows, mode)
            valid_protocol = (
                row["feedback_mode"] == feedback_mode
                and row["model"] == "sentence-transformers/all-MiniLM-L6-v2"
                and int(row["top_k"]) == 10
                and list(map(str, row["seeds"])) == list(SEEDS)
                and int(row["epochs"]) == 8
                and int(row["n_clusters_requested"]) == 32
                and int(row["context_dim_requested"]) == 64
                and row["reward_attribution"] == "final_fused"
                and row["final_context_policy"] == "fixed_topk"
                and row["cluster_retrieval_engine"] == "cached_exact_scores"
                and row["checkpoint_format_version"] == "linucb_cost_seed_checkpoint_v2"
                and int(row["checkpoint_hits"]) == 0
                and int(row["checkpoint_misses"]) == 3
                and row.get("corpus_embedding_fingerprint")
                and row.get("query_embedding_fingerprint")
                and row.get("routing_source_fingerprint")
            )
            add_check(
                checks,
                f"{domain}:{feedback_key}:{mode}_protocol",
                bool(valid_protocol),
                "3 seeds, 8 epochs, K=32, checkpoint v2, fresh computation",
            )
            mode_rankings = rankings_payload.get(mode, {})
            add_check(
                checks,
                f"{domain}:{feedback_key}:{mode}_seeds",
                set(mode_rankings) == set(SEEDS),
                f"seeds={sorted(mode_rankings)}",
            )
            for seed in SEEDS:
                audit_flat_rankings(
                    mode_rankings[seed],
                    query_ids=query_ids,
                    corpus_ids=corpus_ids,
                    label=f"{domain}:{feedback_key}:{mode}:seed{seed}",
                    checks=checks,
                )
            route_summary[f"{feedback_key}_{mode}"] = {
                "hit@10": float(row["hit@10_mean"]),
                "evidence_recall@10": float(row["evidence_recall@10_mean"]),
                "mrr@10": float(row["mrr@10_mean"]),
                "ndcg@10": float(row["ndcg@10_mean"]),
                "dense_query_rate": float(row["dense_query_rate_mean"]),
                "last_epoch_true_reward": float(row["last_epoch_true_reward_mean"]),
            }

    calibrations: dict[str, dict[str, Any]] = {}
    for feedback_key in ("trust", "none"):
        prefix = RESULTS / f"task73_{domain}_100k_{feedback_key}_cross_fitted_budget"
        json_path = prefix.with_suffix(".json")
        paired_path = prefix.with_suffix(".paired.csv")
        rankings_path = prefix.with_suffix(".rankings.json")
        payload = read_json(json_path)
        artifacts.extend([json_path, paired_path, rankings_path])
        summary = payload["summary"]
        paired_rows = [row for row in payload["paired"] if row.get("method_label") == "intentroute_crossfit"]
        add_check(
            checks,
            f"{domain}:{feedback_key}_crossfit_protocol",
            int(payload["protocol"]["num_folds"]) == 5
            and int(payload["protocol"]["bootstrap_samples"]) == BOOTSTRAP_SAMPLES
            and int(summary["queries"]) == len(queries)
            and len(paired_rows) == 3
            and {str(row["seed"]) for row in paired_rows} == set(SEEDS),
            f"folds={summary['folds']} paired_seeds={len(paired_rows)}",
        )
        calibrations[feedback_key] = {
            "eligible_folds": int(summary["intentroute_eligible_folds"]),
            "hit_delta_mean_pp": float(summary["intentroute_hit_delta_mean_pp"]),
            "token_saving_mean_pct": float(summary["intentroute_saving_mean_pct"]),
            "strict_ni_seeds_1pp": int(summary["intentroute_noninferior_seeds_1pp"]),
            "policy_counts": summary["intentroute_policy_counts"],
            "per_seed": [
                {
                    "seed": str(row["seed"]),
                    "hit_delta_pp": 100.0 * float(row["hit_delta_mean"]),
                    "hit_delta_ci_low_pp": 100.0 * float(row["hit_delta_ci_low"]),
                    "hit_delta_ci_high_pp": 100.0 * float(row["hit_delta_ci_high"]),
                    "token_saving_pct": float(row["token_saving_percent"]),
                    "noninferior_by_ci": bool(row["noninferior_by_ci"]),
                    "mcnemar_p_two_sided": float(row["mcnemar_p_two_sided"]),
                }
                for row in paired_rows
            ],
        }

    geometry_dir = RESULTS / f"task73_{domain}_100k_geometry"
    geometry_path = only_file(geometry_dir, "manifold_diagnostics_*.json")
    geometry = read_json(geometry_path)
    artifacts.append(geometry_path)
    add_check(
        checks,
        f"{domain}:geometry_protocol",
        bool(geometry["scale_store_enabled"])
        and int(geometry["scale_store_selected_rows"]) == len(corpus)
        and int(geometry["n_clusters_requested"]) == 32
        and int(geometry["context_dim_requested"]) == 64
        and int(geometry["seed"]) == 13,
        "matched scale store, K=32, seed=13",
    )

    recovery_path = RESULTS / f"task73_{domain}_100k_feedback_recovery.json"
    recovery = read_json(recovery_path)
    artifacts.append(recovery_path)
    crossfit_meta = recovery["summary"].get("cross_fitted_budget")
    add_check(
        checks,
        f"{domain}:recovery_crossfit",
        bool(crossfit_meta)
        and int(crossfit_meta["num_folds"]) == 5
        and len(recovery["summary"]["seeds"]) == 3,
        "per-query cross-fitted policies, 3 seeds",
    )

    lexical_rows = lexical_query_metrics(corpus, queries)
    dense_rankings = baseline_rankings["dense"]
    bm25_rankings = baseline_rankings["bm25"]
    bm25_relative_hits = [
        float(query_hit(query, bm25_rankings[str(query["query_id"])]))
        - float(query_hit(query, dense_rankings[str(query["query_id"])]))
        for query in queries
    ]
    coverage_values = [row["query_token_coverage"] for row in lexical_rows]
    jaccard_values = [row["jaccard"] for row in lexical_rows]
    lexical = {
        "max_query_token_coverage_mean": mean(coverage_values),
        "max_query_token_coverage_ci": bootstrap_mean_ci(coverage_values, seed=7311),
        "max_jaccard_mean": mean(jaccard_values),
        "max_jaccard_ci": bootstrap_mean_ci(jaccard_values, seed=7312),
        "zero_overlap_rate": mean(float(value == 0.0) for value in coverage_values),
        "bm25_minus_dense_hit_pp": 100.0 * mean(bm25_relative_hits),
    }

    artifact_records = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(set(artifacts))
    ]
    return {
        "domain": domain,
        "display_name": spec["display"],
        "dataset": dataset,
        "corpus_chunks": len(corpus),
        "queries": len(queries),
        "gt_refs": len(gt_refs),
        "unique_gt_chunks": len(set(gt_refs)),
        "baseline": {
            method: {
                "hit@10": float(metrics["hit@10"]),
                "evidence_recall@10": float(metrics["evidence_recall@10"]),
                "mrr@10": float(metrics["mrr@10"]),
                "ndcg@10": float(metrics["ndcg@10"]),
            }
            for method, metrics in baseline_metrics.items()
        },
        "route": route_summary,
        "calibration": calibrations,
        "lexical": lexical,
        "lexical_query_values": {
            "query_token_coverage": coverage_values,
            "jaccard": jaccard_values,
            "bm25_relative_hit": bm25_relative_hits,
        },
        "geometry": {
            "pca_dim_for_90pct": int(geometry["pca_dim_for_90pct"]),
            "pca_participation_ratio_dim": float(geometry["pca_participation_ratio_dim"]),
            "cluster_silhouette_sample": float(geometry["cluster_silhouette_sample"]),
            "nearest_cluster_hit@1": float(geometry["nearest_cluster_hit@1"]),
            "nearest_cluster_hit@3": float(geometry["nearest_cluster_hit@3"]),
            "nearest_cluster_hit@5": float(geometry["nearest_cluster_hit@5"]),
            "context_gt_recall@10": float(geometry["context_gt_recall@10"]),
            "dense_gt_recall@10": float(geometry["dense_gt_recall@10"]),
        },
        "feedback_recovery": recovery_extract(recovery),
        "artifacts": artifact_records,
    }


def strip_query_values(domain: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(domain)
    output.pop("lexical_query_values", None)
    return output


def domain_csv_row(domain: Mapping[str, Any]) -> dict[str, Any]:
    baseline = domain["baseline"]
    no_feedback = domain["calibration"]["none"]
    trust = domain["calibration"]["trust"]
    recovery = domain["feedback_recovery"]
    return {
        "dataset": domain["display_name"],
        "corpus_chunks": domain["corpus_chunks"],
        "queries": domain["queries"],
        "gt_refs": domain["gt_refs"],
        "bm25_hit@10": baseline["bm25"]["hit@10"],
        "dense_hit@10": baseline["dense"]["hit@10"],
        "hybrid_hit@10": baseline["hybrid"]["hit@10"],
        "lexical_query_coverage": domain["lexical"]["max_query_token_coverage_mean"],
        "lexical_jaccard": domain["lexical"]["max_jaccard_mean"],
        "no_feedback_eligible_folds": no_feedback["eligible_folds"],
        "no_feedback_hit_delta_pp": no_feedback["hit_delta_mean_pp"],
        "no_feedback_saving_pct": no_feedback["token_saving_mean_pct"],
        "no_feedback_strict_ni_seeds": f"{no_feedback['strict_ni_seeds_1pp']}/3",
        "trust_eligible_folds": trust["eligible_folds"],
        "trust_hit_delta_pp": trust["hit_delta_mean_pp"],
        "trust_saving_pct": trust["token_saving_mean_pct"],
        "nearest_cluster_hit@3": domain["geometry"]["nearest_cluster_hit@3"],
        "compression_failures_seed_total": recovery["compression_only_affected_seed_total"],
        "arm_boost_recovered_seed_total": recovery["compression_only_arm_boost_recovered_seed_total"],
        "post_feedback_all_query_hit_delta_pp": recovery["all_query_arm_boost_hit_delta_vs_before_pp"],
        "post_feedback_all_query_saving_pct": recovery["all_query_arm_boost_saving_pct"],
    }


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def write_markdown(path: Path, payload: Mapping[str, Any]) -> None:
    domains = payload["domains"]
    contrast = payload["lexical_contrast_recreation_minus_writing"]
    lines = [
        "# Task73 LoTTE Domain Expansion Results",
        "",
        "## Protocol",
        "",
        "Two preregistered LoTTE search domains use the frozen Task69 common protocol: GT-anchored 100k corpora, all positive-qrel queries, MiniLM, top-10, K=32, seeds 13/17/19, eight prequential epochs, matched feedback/no-feedback controls, and five-fold cross-fitted context budgets. Domains are reported separately; no pooled p-value is used.",
        "",
        "## Domain Property Check",
        "",
        "| Domain | Corpus | Queries | Query-positive coverage | Jaccard | BM25 Hit@10 | Dense Hit@10 | BM25-Dense |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for domain in domains:
        lines.append(
            f"| {domain['display_name']} | {domain['corpus_chunks']:,} | {domain['queries']:,} | "
            f"{domain['lexical']['max_query_token_coverage_mean']:.4f} | "
            f"{domain['lexical']['max_jaccard_mean']:.4f} | "
            f"{domain['baseline']['bm25']['hit@10']:.4f} | {domain['baseline']['dense']['hit@10']:.4f} | "
            f"{domain['lexical']['bm25_minus_dense_hit_pp']:+.2f}pp |"
        )
    lines.extend([
        "",
        "The preregistered H1 characterization is not supported and is directionally reversed: writing has higher query-positive lexical overlap and a slightly smaller Dense advantage. Recreation-minus-writing differences are "
        f"{contrast['query_token_coverage_difference']:+.4f} (95% CI {contrast['query_token_coverage_ci'][0]:+.4f} to {contrast['query_token_coverage_ci'][1]:+.4f}) for coverage, "
        f"{contrast['jaccard_difference']:+.4f} (95% CI {contrast['jaccard_ci'][0]:+.4f} to {contrast['jaccard_ci'][1]:+.4f}) for Jaccard, and "
        f"{contrast['bm25_relative_hit_difference_pp']:+.2f}pp (95% CI {contrast['bm25_relative_hit_ci_pp'][0]:+.2f} to {contrast['bm25_relative_hit_ci_pp'][1]:+.2f}) for BM25-relative Hit. The domains are retained as preregistered; their frontier contrast cannot be attributed to the originally assumed lexicality ordering.",
        "",
        "## Retrieval And Budget Results",
        "",
        "| Domain | Dense | Hybrid | Trust full | Trust gated | No-feedback route | Feedback | Eligible folds | Hit delta | Token saving | Strict 1pp NI |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ])
    for domain in domains:
        for feedback_key, label in (("trust", "trust"), ("none", "none")):
            calibration = domain["calibration"][feedback_key]
            ni_label = (
                f"{calibration['strict_ni_seeds_1pp']}/3"
                if calibration["eligible_folds"]
                else "n/a (fallback)"
            )
            lines.append(
                f"| {domain['display_name']} | {domain['baseline']['dense']['hit@10']:.4f} | "
                f"{domain['baseline']['hybrid']['hit@10']:.4f} | "
                f"{domain['route']['trust_full_multi_route']['hit@10']:.4f} | "
                f"{domain['route']['trust_gated_cost_aware']['hit@10']:.4f} | "
                f"{domain['route']['none_gated_cost_aware']['hit@10']:.4f} | {label} | "
                f"{calibration['eligible_folds']}/5 | {calibration['hit_delta_mean_pp']:+.2f}pp | "
                f"{calibration['token_saving_mean_pct']:.2f}% | {ni_label} |"
            )
    lines.extend([
        "",
        "Trust-weighted gated routing triggers Dense fallback in all five folds for both domains. The no-feedback frontier is domain-dependent: recreation selects compression in four folds but does not establish seed-level non-inferiority; writing selects compression in all five folds, averages a +0.12pp Hit change with 10.09% token saving, and passes the strict CI rule for two of three seeds. This is useful heterogeneity evidence, not universal strict non-inferiority.",
        "",
        "## Geometry And Recovery",
        "",
        "| Domain | PCA dim 90% | Nearest cluster hit@3 | Context recall@10 | Compression-only failures | Arm-boost recovered | Conservative recovered | All-query retry Hit gain | Saving after arm boost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for domain in domains:
        geometry = domain["geometry"]
        recovery = domain["feedback_recovery"]
        lines.append(
            f"| {domain['display_name']} | {geometry['pca_dim_for_90pct']} | "
            f"{geometry['nearest_cluster_hit@3']:.4f} | {geometry['context_gt_recall@10']:.4f} | "
            f"{recovery['compression_only_affected_seed_total']} | "
            f"{recovery['compression_only_arm_boost_recovered_seed_total']} | "
            f"{recovery['compression_only_conservative_recovered_seed_total']} | "
            f"{recovery['all_query_arm_boost_hit_delta_vs_before_pp']:+.2f}pp | "
            f"{recovery['all_query_arm_boost_saving_pct']:.2f}% |"
        )
    lines.extend([
        "",
        "Both domains expose substantial static nearest-cluster signal, but this does not guarantee a calibrated compression point. Post-failure arm-level retry is also heterogeneous: it is weak on recreation and strong on writing. Recovery is same-query simulated-feedback evidence after an observed failure, not first-pass unseen-query performance.",
        "",
        "## Hypothesis Outcomes",
        "",
        "- H1 (recreation is the more lexical condition): not supported; the observed contrast is reversed.",
        "- H2 (domain-dependent bounded frontier): supported descriptively. Writing admits the stronger no-feedback operating point; recreation is a weaker boundary; trust-weighted calibration safely falls back in both.",
        "- H3 (global feedback advantage): not supported. Trust-weighted prequential feedback does not improve the calibrated frontier here, while post-failure feedback remains a domain-dependent recovery mechanism.",
        "",
        "## Claim Boundary",
        "",
        "Task73 strengthens the paper's bounded external-validity account but does not add a universal positive replication. Geometry can provide route signal, feedback can support repeated-query recovery, and independent calibration can expose a useful context frontier; none of these guarantees savings in every domain or seed. Dense fallback remains a substantive safety outcome rather than a hidden failure.",
        "",
        "## Audit",
        "",
        f"All {payload['audit']['pass_count']} protocol, coverage, ranking-integrity, fingerprint, checkpoint, calibration, geometry, and recovery checks passed. Input and result checksums are recorded in the JSON artifact.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    checks: list[dict[str, str]] = []
    raw_domains = [build_domain(domain, checks) for domain in ("recreation", "writing")]
    recreation, writing = raw_domains
    rec_values = recreation["lexical_query_values"]
    writing_values = writing["lexical_query_values"]
    coverage_ci = bootstrap_independent_difference_ci(
        rec_values["query_token_coverage"], writing_values["query_token_coverage"], seed=7321
    )
    jaccard_ci = bootstrap_independent_difference_ci(
        rec_values["jaccard"], writing_values["jaccard"], seed=7322
    )
    bm25_ci = bootstrap_independent_difference_ci(
        rec_values["bm25_relative_hit"], writing_values["bm25_relative_hit"], seed=7323
    )
    contrast = {
        "orientation": "recreation_minus_writing; positive would support preregistered H1",
        "query_token_coverage_difference": mean(rec_values["query_token_coverage"])
        - mean(writing_values["query_token_coverage"]),
        "query_token_coverage_ci": coverage_ci,
        "jaccard_difference": mean(rec_values["jaccard"]) - mean(writing_values["jaccard"]),
        "jaccard_ci": jaccard_ci,
        "bm25_relative_hit_difference_pp": 100.0
        * (mean(rec_values["bm25_relative_hit"]) - mean(writing_values["bm25_relative_hit"])),
        "bm25_relative_hit_ci_pp": (100.0 * bm25_ci[0], 100.0 * bm25_ci[1]),
        "h1_outcome": "not_supported_direction_reversed",
    }
    payload = {
        "task": "Task73 hypothesis-driven LoTTE domain expansion",
        "generated": "2026-07-15",
        "protocol": {
            "backbone": "sentence-transformers/all-MiniLM-L6-v2",
            "top_k": 10,
            "seeds": list(SEEDS),
            "epochs": 8,
            "n_clusters": 32,
            "feedback_modes": ["none", "trust_weighted"],
            "budget": "five-fold cross-fitted Task38 locked grid",
            "tokenizer": "cl100k_base",
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "pooling": "none",
            "source_dataset": "mteb/LoTTE",
            "source_revision": LOTTE_SOURCE_REVISION,
        },
        "domains": [strip_query_values(domain) for domain in raw_domains],
        "lexical_contrast_recreation_minus_writing": contrast,
        "hypothesis_outcomes": {
            "H1_domain_property": "not_supported_direction_reversed",
            "H2_frontier_heterogeneity": "supported_descriptively_not_pooled",
            "H3_global_feedback_advantage": "not_supported; post-failure recovery remains domain-dependent",
        },
        "audit": {
            "pass_count": len(checks),
            "fail_count": 0,
            "checks": checks,
        },
    }

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    csv_path = output_prefix.with_suffix(".csv")
    md_path = output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = [domain_csv_row(domain) for domain in payload["domains"]]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(md_path, payload)
    print(json.dumps({
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(md_path),
        "audit_passes": len(checks),
        "h1": contrast["h1_outcome"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
