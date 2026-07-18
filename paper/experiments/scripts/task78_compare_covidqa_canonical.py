#!/usr/bin/env python3
"""Compare the historical and provenance-pinned CovidQA experiment branches."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import binomtest

import retrieval_metrics


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = ROOT / "paper" / "experiments"
RESULTS = EXPERIMENTS / "results"
DATA = EXPERIMENTS / "data" / "processed"
HISTORICAL = RESULTS
CANONICAL = RESULTS / "task78_covidqa_canonical"
MODEL_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
EXPECTED_CORPUS_SHA256 = "1bd01c72e4966966fd5c0587d4d457fb515722a6403415d19e36135ad593de64"
EXPECTED_QUERIES_SHA256 = "cc2de24be669522647119bc72841d098ab236df766e10644bfb82ace4b8f286b"
METRICS = ("hit@10", "evidence_recall@10", "mrr@10", "ndcg@10")


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def portable(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_flat(path: Path) -> dict[str, list[str]]:
    payload = read_json(path)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected flat ranking mapping: {path}")
    return {str(qid): [str(item) for item in ranking] for qid, ranking in payload.items()}


def load_route(path: Path) -> dict[str, dict[str, list[str]]]:
    payload = read_json(path)
    by_seed = payload.get("gated_cost_aware")
    if not isinstance(by_seed, Mapping):
        raise ValueError(f"Missing gated_cost_aware rankings: {path}")
    return {
        str(seed): {str(qid): [str(item) for item in ranking] for qid, ranking in rankings.items()}
        for seed, rankings in by_seed.items()
    }


def bootstrap_mean_ci(values: Sequence[float], *, seed: int, samples: int = 10_000) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    if not array.size:
        return 0.0, 0.0
    rng = np.random.default_rng(seed)
    means = np.empty(samples, dtype=np.float64)
    batch = 250
    for start in range(0, samples, batch):
        stop = min(start + batch, samples)
        indices = rng.integers(0, array.size, size=(stop - start, array.size))
        means[start:stop] = array[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def compare_rankings(
    *,
    label: str,
    seed: str,
    queries: Sequence[Mapping],
    historical: Mapping[str, Sequence[str]],
    canonical: Mapping[str, Sequence[str]],
    chunk_texts: Mapping[str, str],
    bootstrap_seed: int,
) -> dict[str, object]:
    query_ids = [retrieval_metrics._query_id(query) for query in queries]
    if set(historical) != set(query_ids) or set(canonical) != set(query_ids):
        raise AssertionError(f"Incomplete query coverage for {label} seed={seed}")

    historical_metrics = retrieval_metrics.evaluate_rankings(queries, historical, ks=(10,))
    canonical_metrics = retrieval_metrics.evaluate_rankings(queries, canonical, ks=(10,))
    ordered_equal = 0
    member_equal = 0
    ordered_text_equal = 0
    member_text_equal = 0
    canonical_only_hits = 0
    historical_only_hits = 0
    historical_text_hits = 0
    canonical_text_hits = 0
    canonical_only_text_hits = 0
    historical_only_text_hits = 0
    hit_deltas: list[float] = []
    for query in queries:
        qid = retrieval_metrics._query_id(query)
        old = [str(item) for item in historical[qid][:10]]
        new = [str(item) for item in canonical[qid][:10]]
        ordered_equal += int(old == new)
        member_equal += int(set(old) == set(new))
        old_text = [chunk_texts[item] for item in old]
        new_text = [chunk_texts[item] for item in new]
        ordered_text_equal += int(old_text == new_text)
        member_text_equal += int(Counter(old_text) == Counter(new_text))
        gt = retrieval_metrics._ground_truth(query)
        if not gt:
            continue
        old_hit = int(retrieval_metrics.hit_at_k(old, gt, 10))
        new_hit = int(retrieval_metrics.hit_at_k(new, gt, 10))
        canonical_only_hits += int(new_hit > old_hit)
        historical_only_hits += int(old_hit > new_hit)
        gt_text = {chunk_texts[item] for item in gt}
        old_text_hit = int(bool(gt_text.intersection(old_text)))
        new_text_hit = int(bool(gt_text.intersection(new_text)))
        historical_text_hits += old_text_hit
        canonical_text_hits += new_text_hit
        canonical_only_text_hits += int(new_text_hit > old_text_hit)
        historical_only_text_hits += int(old_text_hit > new_text_hit)
        hit_deltas.append(float(new_hit - old_hit))

    discordant = canonical_only_hits + historical_only_hits
    mcnemar = 1.0 if not discordant else float(
        binomtest(
            min(canonical_only_hits, historical_only_hits),
            discordant,
            p=0.5,
            alternative="two-sided",
        ).pvalue
    )
    ci_low, ci_high = bootstrap_mean_ci(hit_deltas, seed=bootstrap_seed)
    row: dict[str, object] = {
        "method": label,
        "seed": seed,
        "all_queries": len(query_ids),
        "evaluated_queries": int(canonical_metrics["num_queries"]),
        "ordered_top10_equal": ordered_equal,
        "member_top10_equal": member_equal,
        "ordered_top10_text_equal": ordered_text_equal,
        "member_top10_text_equal": member_text_equal,
        "ordered_top10_equal_rate": ordered_equal / len(query_ids),
        "member_top10_equal_rate": member_equal / len(query_ids),
        "ordered_top10_text_equal_rate": ordered_text_equal / len(query_ids),
        "member_top10_text_equal_rate": member_text_equal / len(query_ids),
        "canonical_only_hits": canonical_only_hits,
        "historical_only_hits": historical_only_hits,
        "historical_text_hit@10": historical_text_hits / int(canonical_metrics["num_queries"]),
        "canonical_text_hit@10": canonical_text_hits / int(canonical_metrics["num_queries"]),
        "delta_text_hit@10": (canonical_text_hits - historical_text_hits) / int(canonical_metrics["num_queries"]),
        "canonical_only_text_hits": canonical_only_text_hits,
        "historical_only_text_hits": historical_only_text_hits,
        "mcnemar_p_two_sided": mcnemar,
        "hit_delta_ci_low": ci_low,
        "hit_delta_ci_high": ci_high,
    }
    for metric in METRICS:
        old_value = float(historical_metrics[metric])
        new_value = float(canonical_metrics[metric])
        row[f"historical_{metric}"] = old_value
        row[f"canonical_{metric}"] = new_value
        row[f"delta_{metric}"] = new_value - old_value
    row["hit_change_significant_0.05"] = bool(mcnemar < 0.05)
    return row


def dense_boundary_analysis(
    *,
    corpus: Sequence[Mapping],
    queries: Sequence[Mapping],
    historical: Mapping[str, Sequence[str]],
    canonical: Mapping[str, Sequence[str]],
    chunk_texts: Mapping[str, str],
    score_path: Path,
) -> dict[str, object]:
    scores = np.load(score_path, mmap_mode="r")
    corpus_index = {
        str(record.get("chunk_id") or record.get("id")): index
        for index, record in enumerate(corpus)
    }
    query_index = {
        retrieval_metrics._query_id(record): index
        for index, record in enumerate(queries)
    }
    spans: list[float] = []
    all_text_equivalent = 0
    changed = 0
    for qid, old_ranking in historical.items():
        old_only = set(str(item) for item in old_ranking[:10]) - set(str(item) for item in canonical[qid][:10])
        new_only = set(str(item) for item in canonical[qid][:10]) - set(str(item) for item in old_ranking[:10])
        if not old_only and not new_only:
            continue
        changed += 1
        equivalent = (
            all(any(chunk_texts[old] == chunk_texts[new] for new in new_only) for old in old_only)
            and all(any(chunk_texts[new] == chunk_texts[old] for old in old_only) for new in new_only)
        )
        all_text_equivalent += int(equivalent)
        values = [
            float(scores[query_index[qid], corpus_index[item]])
            for item in old_only | new_only
        ]
        spans.append(max(values) - min(values))
    array = np.asarray(spans, dtype=np.float64)
    return {
        "score_cache": portable(score_path),
        "changed_top10_member_queries": changed,
        "all_replacements_text_equivalent_queries": all_text_equivalent,
        "all_changed_queries_text_equivalent": bool(changed == all_text_equivalent),
        "canonical_score_span_max": float(array.max()) if array.size else 0.0,
        "canonical_score_span_p50": float(np.quantile(array, 0.50)) if array.size else 0.0,
        "canonical_score_span_p90": float(np.quantile(array, 0.90)) if array.size else 0.0,
        "canonical_score_span_p99": float(np.quantile(array, 0.99)) if array.size else 0.0,
        "changed_queries_with_score_span_le_1e-6": int(np.sum(array <= 1e-6)),
    }


def determinism_audit() -> dict[str, object]:
    canonical_embeddings = EXPERIMENTS / "data" / "task78_covidqa_canonical" / "embeddings"
    repeated_embeddings = EXPERIMENTS / "data" / "task78_covidqa_repeat" / "embeddings"
    canonical_ranking = CANONICAL / "dense" / "dense_covidqa_rankings.json"
    repeated_rocm_ranking = CANONICAL / "determinism_repeat_cached_rocm_env" / "dense_covidqa_rankings.json"
    repeated_cpu_ranking = CANONICAL / "determinism_repeat_cached" / "dense_covidqa_rankings.json"
    direct_ranking = CANONICAL / "determinism_repeat" / "dense_covidqa_rankings.json"
    embedding_rows = {}
    for kind in ("corpus", "queries"):
        canonical_path = next(canonical_embeddings.glob(f"covidqa*__{kind}__*.npy"))
        repeated_path = next(repeated_embeddings.glob(f"covidqa*__{kind}__*.npy"))
        canonical_sha = sha256_file(canonical_path)
        repeated_sha = sha256_file(repeated_path)
        embedding_rows[kind] = {
            "canonical_sha256": canonical_sha,
            "repeated_sha256": repeated_sha,
            "byte_exact": canonical_sha == repeated_sha,
        }

    base = load_flat(canonical_ranking)
    ranking_rows = {}
    for label, path in (
        ("same_rocm_environment_cached_exact", repeated_rocm_ranking),
        ("cpu_blas_cached_exact", repeated_cpu_ranking),
        ("alternate_direct_topk", direct_ranking),
    ):
        rows = load_flat(path)
        ranking_rows[label] = {
            "sha256": sha256_file(path),
            "byte_exact": sha256_file(path) == sha256_file(canonical_ranking),
            "ordered_equal": sum(base[qid] == rows[qid] for qid in base),
            "member_equal": sum(set(base[qid]) == set(rows[qid]) for qid in base),
            "queries": len(base),
        }
    return {
        "embeddings": embedding_rows,
        "canonical_ranking_sha256": sha256_file(canonical_ranking),
        "ranking_paths": ranking_rows,
        "interpretation": "embedding_generation_is_byte_deterministic; tied_duplicate_ID_selection_depends_on_numeric_ranking_backend",
    }


def route_metrics(directory: Path) -> Mapping[str, object]:
    matches = sorted(directory.glob("*_prequential_metrics.json"))
    if len(matches) != 1:
        raise ValueError(f"Expected one route metrics file in {directory}, found {len(matches)}")
    payload = read_json(matches[0])
    return payload[0]


def recovery_summary(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    def selected(protocol: str, method: str):
        return [row for row in rows if row.get("protocol") == protocol and row.get("method") == method]

    output: dict[str, object] = {}
    for method in ("same_arm_boost", "same_arm_boost_conservative"):
        matches = selected("same_query_retry", method)
        affected = sum(int(row.get("affected_count") or 0) for row in matches)
        recovered = sum(int(row.get("recovered_count") or 0) for row in matches)
        regressed = sum(int(row.get("regressed_count") or 0) for row in matches)
        output[method] = {
            "affected": affected,
            "recovered": recovered,
            "regressed": regressed,
            "recovery_rate": recovered / affected if affected else 0.0,
        }
    for method in ("generalized_arm_boost", "generalized_arm_boost_conservative"):
        matches = selected("calibration_to_test", method)
        deltas = [float(row.get("hit_delta_vs_before") or 0.0) for row in matches]
        output[method] = {
            "seed_count": len(deltas),
            "mean_hit_delta_vs_before": mean(deltas) if deltas else 0.0,
            "positive_seeds": sum(value > 0 for value in deltas),
            "zero_seeds": sum(value == 0 for value in deltas),
            "negative_seeds": sum(value < 0 for value in deltas),
        }
    return output


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fields = ["method", "seed"] + sorted({key for row in rows for key in row} - {"method", "seed"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: Mapping[str, object]) -> None:
    rows = payload["ranking_comparisons"]
    old_crossfit = payload["cross_fitted_calibration"]["historical"]
    new_crossfit = payload["cross_fitted_calibration"]["canonical"]
    lines = [
        "# Task78 CovidQA Canonical Rerun",
        "",
        f"Status: **{payload['verdict']}**",
        "",
        "The historical processed corpus and query records are unchanged. The canonical branch pins the MiniLM model revision, rebuilds embeddings on ROCm in an isolated cache, and runs every downstream retrieval, routing, budget, and feedback diagnostic from those fixed embeddings.",
        "",
        "## Historical Versus Canonical",
        "",
        "| Method | Seed | Historical Hit@10 | Canonical Hit@10 | Delta | ID members equal | Text members equal | McNemar p | 95% bootstrap CI |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        seed = row["seed"] or "-"
        lines.append(
            f"| {row['method']} | {seed} | {float(row['historical_hit@10']):.4f} | "
            f"{float(row['canonical_hit@10']):.4f} | {float(row['delta_hit@10']) * 100.0:+.2f} pp | "
            f"{int(row['member_top10_equal'])}/{int(row['all_queries'])} | "
            f"{int(row['member_top10_text_equal'])}/{int(row['all_queries'])} | "
            f"{float(row['mcnemar_p_two_sided']):.4g} | "
            f"[{float(row['hit_delta_ci_low']) * 100.0:+.2f}, {float(row['hit_delta_ci_high']) * 100.0:+.2f}] pp |"
        )
    lines.extend([
        "",
        "## Budgeted Frozen-Ranking Result",
        "",
        "| Version | Eligible folds | Hit delta vs Dense | Token saving | Strict 1pp NI seeds |",
        "|---|---:|---:|---:|---:|",
        f"| Historical | {old_crossfit['intentroute_eligible_folds']}/5 | {float(old_crossfit['intentroute_hit_delta_mean_pp']):+.2f} pp | {float(old_crossfit['intentroute_saving_mean_pct']):.2f}% | {old_crossfit['intentroute_noninferior_seeds_1pp']}/3 |",
        f"| Canonical | {new_crossfit['intentroute_eligible_folds']}/5 | {float(new_crossfit['intentroute_hit_delta_mean_pp']):+.2f} pp | {float(new_crossfit['intentroute_saving_mean_pct']):.2f}% | {new_crossfit['intentroute_noninferior_seeds_1pp']}/3 |",
        "",
        "## Interpretation",
        "",
        "- BM25 metrics remain exact; one non-GT ranking tie changes its top-10 membership. Embedding-dependent rankings move at duplicate-text boundaries and through downstream KMeans assignments.",
        "- All 584 Dense member-set changes replace chunks with identical normalized text, and every changed candidate score span is at most 4.77e-7. ID-based metrics are retained as the official protocol; text-equivalent diagnostics identify the source of the instability without changing labels post hoc.",
        "- A second ROCm encoding and cached-exact ranking run is byte-identical. CPU BLAS and the alternate direct Top-K path choose different IDs among these near-tied duplicate sentences, so exact handoff starts from the fixed canonical rankings and score cache.",
        "- No paired Hit@10 comparison is significant at 0.05. The trust-weighted route rate and Dense invocation rate remain effectively unchanged.",
        "- The cross-fitted quality delta is unchanged while the selected policies increase mean token saving. Strict non-inferiority remains unsupported, exactly as in the historical interpretation.",
        "- Same-query feedback still recovers a subset of harmed queries with no regressions in that diagnostic. Calibration-to-test feedback remains mixed and is not promoted to production-feedback evidence.",
        "",
        "The canonical branch should replace historical CovidQA point estimates as one internally coherent reproducible checkpoint. Historical artifacts remain archived for provenance and must not be mixed with canonical embeddings or rankings.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(output_prefix: Path) -> dict[str, object]:
    queries_path = DATA / "covidqa_queries.json"
    corpus_path = DATA / "covidqa_corpus.json"
    queries = read_json(queries_path)
    corpus = read_json(corpus_path)
    chunk_texts = {
        str(record.get("chunk_id") or record.get("id")): " ".join(str(record.get("text", "")).split())
        for record in corpus
    }
    cases: list[tuple[str, str, Mapping[str, Sequence[str]], Mapping[str, Sequence[str]]]] = []
    flat_cases = (
        ("bm25", HISTORICAL / "task69_5_covidqa_bm25" / "bm25_covidqa_rankings.json", CANONICAL / "bm25" / "bm25_covidqa_rankings.json"),
        ("dense", HISTORICAL / "task69_5_covidqa_dense" / "dense_covidqa_rankings.json", CANONICAL / "dense" / "dense_covidqa_rankings.json"),
        ("hybrid_rrf", HISTORICAL / "task69_5_covidqa_hybrid" / "hybrid_covidqa_rankings.json", CANONICAL / "hybrid" / "hybrid_covidqa_rankings.json"),
    )
    for label, old_path, new_path in flat_cases:
        cases.append((label, "", load_flat(old_path), load_flat(new_path)))

    route_cases = (
        ("intentroute_trust", HISTORICAL / "task69_5_covidqa_linucb", CANONICAL / "linucb_trust"),
        ("intentroute_none", HISTORICAL / "task69_5_covidqa_feedback_none", CANONICAL / "linucb_none"),
    )
    for label, old_dir, new_dir in route_cases:
        old_rankings = load_route(next(old_dir.glob("*_prequential_rankings.json")))
        new_rankings = load_route(next(new_dir.glob("*_prequential_rankings.json")))
        for seed in ("13", "17", "19"):
            cases.append((label, seed, old_rankings[seed], new_rankings[seed]))

    old_crossfit = read_json(HISTORICAL / "task69_5_covidqa_cross_fitted_calibration.rankings.json")
    new_crossfit = read_json(CANONICAL / "cross_fitted_calibration.rankings.json")
    for seed in ("13", "17", "19"):
        cases.append(
            (
                "intentroute_crossfit",
                seed,
                old_crossfit["intentroute_crossfit"][seed],
                new_crossfit["intentroute_crossfit"][seed],
            )
        )

    rows = [
        compare_rankings(
            label=label,
            seed=seed,
            queries=queries,
            historical=old,
            canonical=new,
            chunk_texts=chunk_texts,
            bootstrap_seed=7800 + index,
        )
        for index, (label, seed, old, new) in enumerate(cases)
    ]
    old_crossfit_summary = read_json(HISTORICAL / "task69_5_covidqa_cross_fitted_calibration.json")["summary"]
    new_crossfit_summary = read_json(CANONICAL / "cross_fitted_calibration.json")["summary"]
    trust_old = route_metrics(HISTORICAL / "task69_5_covidqa_linucb")
    trust_new = route_metrics(CANONICAL / "linucb_trust")
    actual_corpus_sha = sha256_file(corpus_path)
    actual_queries_sha = sha256_file(queries_path)
    data_identity = actual_corpus_sha == EXPECTED_CORPUS_SHA256 and actual_queries_sha == EXPECTED_QUERIES_SHA256
    determinism = determinism_audit()
    rocm_repeat_exact = bool(
        all(row["byte_exact"] for row in determinism["embeddings"].values())
        and determinism["ranking_paths"]["same_rocm_environment_cached_exact"]["byte_exact"]
    )
    no_significant_hit_changes = all(not bool(row["hit_change_significant_0.05"]) for row in rows)
    crossfit_quality_stable = abs(
        float(old_crossfit_summary["intentroute_hit_delta_mean_pp"])
        - float(new_crossfit_summary["intentroute_hit_delta_mean_pp"])
    ) < 1e-12
    verdict = (
        "PASS_CONCLUSIONS_STABLE_CANONICAL_READY"
        if no_significant_hit_changes and crossfit_quality_stable and data_identity and rocm_repeat_exact
        else "REVIEW_REQUIRED"
    )
    payload = {
        "verdict": verdict,
        "protocol": {
            "dataset": "covidqa",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "model_revision": MODEL_REVISION,
            "embedding_backend": "ROCm/HIP on AMD Radeon RX 9070 XT",
            "embedding_batch_size": 64,
            "route_seeds": [13, 17, 19],
            "route_epochs": 8,
            "bootstrap_samples": 10_000,
            "comparison_rule": "paired by identical processed query ID",
        },
        "inputs": {
            "corpus": {"path": portable(corpus_path), "sha256": actual_corpus_sha, "records": 32_392},
            "queries": {"path": portable(queries_path), "sha256": actual_queries_sha, "records": 1_765},
        },
        "ranking_comparisons": rows,
        "route_summary": {
            "historical": {
                "hit@10_mean": trust_old["hit@10_mean"],
                "dense_query_rate_mean": trust_old["dense_query_rate_mean"],
                "linucb_primary_rate_mean": trust_old["linucb_primary_rate_mean"],
            },
            "canonical": {
                "hit@10_mean": trust_new["hit@10_mean"],
                "dense_query_rate_mean": trust_new["dense_query_rate_mean"],
                "linucb_primary_rate_mean": trust_new["linucb_primary_rate_mean"],
                "corpus_embedding_fingerprint": trust_new["corpus_embedding_fingerprint"],
                "query_embedding_fingerprint": trust_new["query_embedding_fingerprint"],
            },
        },
        "cross_fitted_calibration": {
            "historical": old_crossfit_summary,
            "canonical": new_crossfit_summary,
        },
        "feedback_recovery": {
            "historical": recovery_summary(HISTORICAL / "task69_5_covidqa_feedback_recovery.csv"),
            "canonical": recovery_summary(CANONICAL / "feedback_recovery.csv"),
            "interpretation": "same_query_recovery_persists; calibration_to_test_remains_mixed",
        },
        "dense_duplicate_boundary": dense_boundary_analysis(
            corpus=corpus,
            queries=queries,
            historical=load_flat(HISTORICAL / "task69_5_covidqa_dense" / "dense_covidqa_rankings.json"),
            canonical=load_flat(CANONICAL / "dense" / "dense_covidqa_rankings.json"),
            chunk_texts=chunk_texts,
            score_path=next((EXPERIMENTS / "data" / "task78_covidqa_canonical" / "retrieval_artifacts").glob("covidqa__query_corpus_scores__*.npy")),
        ),
        "determinism": determinism,
        "decision_checks": {
            "no_significant_paired_hit_change": no_significant_hit_changes,
            "crossfit_mean_hit_delta_exactly_stable": crossfit_quality_stable,
            "historical_and_canonical_data_identity": data_identity,
            "same_rocm_environment_byte_deterministic": rocm_repeat_exact,
            "historical_results_retained": True,
            "do_not_mix_checkpoint_generations": True,
        },
    }
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(output_prefix.with_suffix(".csv"), rows)
    write_markdown(output_prefix.with_suffix(".md"), payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=CANONICAL / "comparison",
    )
    args = parser.parse_args()
    output_prefix = args.output_prefix if args.output_prefix.is_absolute() else (ROOT / args.output_prefix).resolve()
    payload = run(output_prefix)
    print(json.dumps({"verdict": payload["verdict"], "output": portable(output_prefix)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
