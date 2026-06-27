#!/usr/bin/env python3
"""Attribute safe final-context compression to query-level selector signals.

The experiment holds the upstream fixed-top-10 ranking constant and changes
only which queries receive the same deterministic token-budget action. Selector
thresholds and action parameters are chosen on the Task38 calibration split and
then frozen for the held-out test split.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Callable, Mapping, Sequence

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS = ROOT / "paper" / "experiments" / "results"
DATA = ROOT / "paper" / "experiments" / "data"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_cost = _load_module("task65_context_cost", SCRIPT_DIR / "context_token_cost.py")
budget = _load_module("task65_budget", SCRIPT_DIR / "task37_context_budget_search.py")
calibration = _load_module("task65_calibration", SCRIPT_DIR / "task38_calibrated_context_budget.py")
paired = _load_module("task65_paired", SCRIPT_DIR / "task37_paired_significance.py")
retrieval_metrics = context_cost.retrieval_metrics


SELECTORS = (
    "learned_confidence",
    "geometry_similarity",
    "shuffled_confidence",
    "random_selector",
    "budget_only",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def qid(query: Mapping) -> str:
    return context_cost.query_id(query)


def ground_truth(query: Mapping) -> set[str]:
    return retrieval_metrics._ground_truth(query)


def hit(ranking: Sequence[str], gt: set[str], k: int = 10) -> int:
    return int(bool(gt.intersection(str(item) for item in ranking[:k])))


def stable_uniform(label: str, seed: str, query_id: str) -> float:
    digest = hashlib.sha256(f"{label}:{seed}:{query_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def shuffled_scores(
    scores: Mapping[str, float],
    query_ids: Sequence[str],
    *,
    seed: int,
) -> dict[str, float]:
    ordered_ids = sorted(query_ids)
    values = np.asarray([scores[item] for item in ordered_ids], dtype=np.float64)
    rng = np.random.default_rng(seed)
    rng.shuffle(values)
    return {item: float(value) for item, value in zip(ordered_ids, values)}


def threshold_for_coverage(scores: Sequence[float], target_coverage: float) -> float:
    if target_coverage >= 1.0:
        return -math.inf
    if target_coverage <= 0.0:
        return math.inf
    ordered = sorted((float(value) for value in scores), reverse=True)
    keep = max(1, min(len(ordered), int(math.ceil(target_coverage * len(ordered)))))
    return ordered[keep - 1]


def ece(y_true: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if y_true.size == 0:
        return 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = float(y_true.size)
    result = 0.0
    for index in range(bins):
        if index == bins - 1:
            mask = (probabilities >= edges[index]) & (probabilities <= edges[index + 1])
        else:
            mask = (probabilities >= edges[index]) & (probabilities < edges[index + 1])
        if np.any(mask):
            result += float(np.sum(mask)) / total * abs(
                float(np.mean(probabilities[mask])) - float(np.mean(y_true[mask]))
            )
    return result


def metric_with_bootstrap(
    y_true: np.ndarray,
    scores: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    rng: np.random.Generator,
    n_bootstrap: int,
) -> tuple[float, float, float]:
    observed = float(metric(y_true, scores))
    samples: list[float] = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y_true), size=len(y_true))
        sampled_y = y_true[indices]
        if len(np.unique(sampled_y)) < 2:
            continue
        samples.append(float(metric(sampled_y, scores[indices])))
    if not samples:
        return observed, observed, observed
    return observed, float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def fit_probabilities(
    calibration_y: np.ndarray,
    calibration_scores: np.ndarray,
    test_scores: np.ndarray,
) -> np.ndarray:
    if len(np.unique(calibration_scores)) < 2 or len(np.unique(calibration_y)) < 2:
        return np.full(len(test_scores), float(np.mean(calibration_y)), dtype=np.float64)
    model = IsotonicRegression(y_min=0.0, y_max=1.0, increasing=True, out_of_bounds="clip")
    model.fit(calibration_scores, calibration_y)
    return np.asarray(model.predict(test_scores), dtype=np.float64)


def evaluate_rankings(
    queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    source_rankings: Mapping[str, Sequence[str]],
    final_rankings: Mapping[str, Sequence[str]],
    selected: Mapping[str, bool],
    chunk_tokens: Mapping[str, int],
) -> dict[str, float]:
    dense_hits: list[int] = []
    source_hits: list[int] = []
    final_hits: list[int] = []
    dense_tokens: list[float] = []
    source_tokens: list[float] = []
    final_tokens: list[float] = []
    selected_source_hits = 0
    selected_source_losses = 0
    selected_dense_hits = 0
    selected_dense_losses = 0
    selected_count = 0

    for query in queries:
        truth = ground_truth(query)
        if not truth:
            continue
        query_id = qid(query)
        dense = [str(item) for item in dense_rankings.get(query_id, [])[:10]]
        source = [str(item) for item in source_rankings.get(query_id, [])[:10]]
        final = [str(item) for item in final_rankings.get(query_id, [])[:10]]
        dense_hit = hit(dense, truth)
        source_hit = hit(source, truth)
        final_hit = hit(final, truth)
        is_selected = bool(selected.get(query_id, False))
        if is_selected:
            selected_count += 1
            if source_hit:
                selected_source_hits += 1
                selected_source_losses += int(not final_hit)
            if dense_hit:
                selected_dense_hits += 1
                selected_dense_losses += int(not final_hit)
        dense_hits.append(dense_hit)
        source_hits.append(source_hit)
        final_hits.append(final_hit)
        dense_tokens.append(float(sum(chunk_tokens.get(item, 0) for item in dense)))
        source_tokens.append(float(sum(chunk_tokens.get(item, 0) for item in source)))
        final_tokens.append(float(sum(chunk_tokens.get(item, 0) for item in final)))

    dense_hit_mean = float(np.mean(dense_hits))
    source_hit_mean = float(np.mean(source_hits))
    final_hit_mean = float(np.mean(final_hits))
    dense_token_mean = float(np.mean(dense_tokens))
    source_token_mean = float(np.mean(source_tokens))
    final_token_mean = float(np.mean(final_tokens))
    count = len(final_hits)
    return {
        "num_queries": count,
        "dense_hit@10": dense_hit_mean,
        "source_hit@10": source_hit_mean,
        "final_hit@10": final_hit_mean,
        "hit_delta_vs_dense_pp": (final_hit_mean - dense_hit_mean) * 100.0,
        "hit_delta_vs_source_pp": (final_hit_mean - source_hit_mean) * 100.0,
        "dense_tokens": dense_token_mean,
        "source_tokens": source_token_mean,
        "final_tokens": final_token_mean,
        "token_saving_vs_dense_pct": (1.0 - final_token_mean / dense_token_mean) * 100.0,
        "token_saving_vs_source_pct": (1.0 - final_token_mean / source_token_mean) * 100.0,
        "actual_coverage": selected_count / count if count else 0.0,
        "source_selective_risk": selected_source_losses / selected_source_hits if selected_source_hits else 0.0,
        "dense_selective_risk": selected_dense_losses / selected_dense_hits if selected_dense_hits else 0.0,
        "selected_source_hit_queries": selected_source_hits,
        "selected_dense_hit_queries": selected_dense_hits,
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    preferred = [
        "selector",
        "margin_pp",
        "split",
        "seed",
        "budget_ratio",
        "min_keep",
        "target_coverage",
        "score_threshold",
        "eligible",
        "final_hit@10",
        "hit_delta_vs_dense_pp",
        "token_saving_vs_dense_pct",
        "actual_coverage",
        "source_selective_risk",
    ]
    fields = [field for field in preferred if any(field in row for row in rows)]
    fields.extend(sorted({field for row in rows for field in row if field not in fields}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def aggregate_candidate_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple, list[Mapping[str, object]]] = defaultdict(list)
    keys = ("selector", "split", "budget_ratio", "min_keep", "target_coverage")
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    result: list[dict[str, object]] = []
    numeric = (
        "final_hit@10",
        "hit_delta_vs_dense_pp",
        "hit_delta_vs_source_pp",
        "token_saving_vs_dense_pct",
        "token_saving_vs_source_pct",
        "actual_coverage",
        "source_selective_risk",
        "dense_selective_risk",
    )
    for key, group in grouped.items():
        row = dict(zip(keys, key))
        row["num_seeds"] = len(group)
        for field in numeric:
            row[field] = mean(float(item[field]) for item in group)
        result.append(row)
    return sorted(
        result,
        key=lambda row: (
            str(row["selector"]),
            str(row["split"]),
            float(row["budget_ratio"]),
            int(row["min_keep"]),
            float(row["target_coverage"]),
        ),
    )


def select_candidates(
    aggregate_rows: Sequence[Mapping[str, object]],
    *,
    margin_pp: float,
    selectors: Sequence[str] = SELECTORS,
) -> list[dict[str, object]]:
    calibration_rows = [row for row in aggregate_rows if row["split"] == "calibration"]
    test_index = {
        (row["selector"], row["budget_ratio"], row["min_keep"], row["target_coverage"]): row
        for row in aggregate_rows
        if row["split"] == "test"
    }
    selected: list[dict[str, object]] = []
    for selector in selectors:
        candidates = [row for row in calibration_rows if row["selector"] == selector]
        eligible = [row for row in candidates if float(row["hit_delta_vs_dense_pp"]) >= -margin_pp]
        pool = eligible or candidates
        choice = max(
            pool,
            key=lambda row: (
                float(row["token_saving_vs_dense_pct"]) if eligible else float(row["hit_delta_vs_dense_pp"]),
                float(row["hit_delta_vs_dense_pp"]),
                float(row["token_saving_vs_dense_pct"]),
            ),
        )
        key = (choice["selector"], choice["budget_ratio"], choice["min_keep"], choice["target_coverage"])
        for split, source in (("calibration", choice), ("test", test_index[key])):
            output = dict(source)
            output["margin_pp"] = margin_pp
            output["eligible"] = bool(eligible)
            output["split"] = split
            selected.append(output)
    return selected


def discrimination_rows(
    *,
    queries_by_split: Mapping[str, Sequence[Mapping]],
    source_by_seed: Mapping[str, Mapping[str, Sequence[str]]],
    score_maps: Mapping[str, Mapping[str, Mapping[str, float]]],
    chunk_tokens: Mapping[str, int],
    ratio: float,
    min_keep: int,
    n_bootstrap: int,
    selectors: Sequence[str] = SELECTORS,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed, source_rankings in source_by_seed.items():
        labels: dict[str, dict[str, int]] = {"calibration": {}, "test": {}}
        for split, queries in queries_by_split.items():
            for query in queries:
                truth = ground_truth(query)
                query_id = qid(query)
                source = [str(item) for item in source_rankings.get(query_id, [])[:10]]
                if not hit(source, truth):
                    continue
                compressed = budget.token_budget_ranking(
                    source,
                    chunk_tokens,
                    top_k=10,
                    budget_ratio=ratio,
                    min_keep=min_keep,
                )
                labels[split][query_id] = hit(compressed, truth)

        for selector_index, selector in enumerate(selectors):
            calibration_ids = sorted(labels["calibration"])
            test_ids = sorted(labels["test"])
            calibration_y = np.asarray([labels["calibration"][item] for item in calibration_ids], dtype=np.int32)
            test_y = np.asarray([labels["test"][item] for item in test_ids], dtype=np.int32)
            calibration_scores = np.asarray(
                [score_maps[selector][seed][item] for item in calibration_ids], dtype=np.float64
            )
            test_scores = np.asarray([score_maps[selector][seed][item] for item in test_ids], dtype=np.float64)
            calibrated = fit_probabilities(calibration_y, calibration_scores, test_scores)
            rng = np.random.default_rng(65100 + int(seed) + selector_index)
            if len(np.unique(test_y)) < 2:
                auc = auc_lo = auc_hi = 0.5
                ap = ap_lo = ap_hi = float(np.mean(test_y))
            else:
                auc, auc_lo, auc_hi = metric_with_bootstrap(
                    test_y,
                    test_scores,
                    roc_auc_score,
                    rng=rng,
                    n_bootstrap=n_bootstrap,
                )
                ap, ap_lo, ap_hi = metric_with_bootstrap(
                    test_y,
                    test_scores,
                    average_precision_score,
                    rng=rng,
                    n_bootstrap=n_bootstrap,
                )
            raw_probabilities = np.clip(test_scores, 0.0, 1.0)
            raw_brier, raw_brier_lo, raw_brier_hi = metric_with_bootstrap(
                test_y,
                raw_probabilities,
                brier_score_loss,
                rng=rng,
                n_bootstrap=n_bootstrap,
            )
            raw_ece, raw_ece_lo, raw_ece_hi = metric_with_bootstrap(
                test_y,
                raw_probabilities,
                ece,
                rng=rng,
                n_bootstrap=n_bootstrap,
            )
            isotonic_brier, isotonic_brier_lo, isotonic_brier_hi = metric_with_bootstrap(
                test_y,
                calibrated,
                brier_score_loss,
                rng=rng,
                n_bootstrap=n_bootstrap,
            )
            isotonic_ece, isotonic_ece_lo, isotonic_ece_hi = metric_with_bootstrap(
                test_y,
                calibrated,
                ece,
                rng=rng,
                n_bootstrap=n_bootstrap,
            )
            rows.append({
                "selector": selector,
                "seed": seed,
                "action": f"token_budget_r{ratio:.2f}_m{min_keep}",
                "calibration_examples": len(calibration_y),
                "test_examples": len(test_y),
                "test_safe_prevalence": float(np.mean(test_y)),
                "auroc": auc,
                "auroc_ci_low": auc_lo,
                "auroc_ci_high": auc_hi,
                "average_precision": ap,
                "average_precision_ci_low": ap_lo,
                "average_precision_ci_high": ap_hi,
                "raw_brier": raw_brier,
                "raw_brier_ci_low": raw_brier_lo,
                "raw_brier_ci_high": raw_brier_hi,
                "raw_ece": raw_ece,
                "raw_ece_ci_low": raw_ece_lo,
                "raw_ece_ci_high": raw_ece_hi,
                "isotonic_brier": isotonic_brier,
                "isotonic_brier_ci_low": isotonic_brier_lo,
                "isotonic_brier_ci_high": isotonic_brier_hi,
                "isotonic_ece": isotonic_ece,
                "isotonic_ece_ci_low": isotonic_ece_lo,
                "isotonic_ece_ci_high": isotonic_ece_hi,
            })
    return rows


def paired_selected_rows(
    *,
    selected_rows: Sequence[Mapping[str, object]],
    calibration_ids: Sequence[str],
    test_queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    source_by_seed: Mapping[str, Mapping[str, Sequence[str]]],
    score_maps: Mapping[str, Mapping[str, Mapping[str, float]]],
    chunk_tokens: Mapping[str, int],
    n_bootstrap: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    choices = [row for row in selected_rows if row["split"] == "test"]
    baseline = paired.Variant("dense", "dense_top10", "", dict(dense_rankings))
    for choice in choices:
        selector = str(choice["selector"])
        ratio = float(choice["budget_ratio"])
        min_keep = int(choice["min_keep"])
        target_coverage = float(choice["target_coverage"])
        margin_pp = float(choice["margin_pp"])
        for seed, source_rankings in source_by_seed.items():
            threshold = threshold_for_coverage(
                [score_maps[selector][seed][item] for item in calibration_ids],
                target_coverage,
            )
            final_rankings = {}
            for query_id, source in source_rankings.items():
                selected = score_maps[selector][seed][query_id] >= threshold
                final_rankings[query_id] = (
                    budget.token_budget_ranking(
                        source,
                        chunk_tokens,
                        top_k=10,
                        budget_ratio=ratio,
                        min_keep=min_keep,
                    )
                    if selected
                    else [str(item) for item in source[:10]]
                )
            row = paired.compare_variant(
                scale="100k",
                queries=test_queries,
                baseline=baseline,
                variant=paired.Variant(
                    selector,
                    f"{selector}:r{ratio:.2f}:m{min_keep}:c{target_coverage:.2f}",
                    seed,
                    final_rankings,
                ),
                chunk_tokens=chunk_tokens,
                k=10,
                noninferiority_margin=margin_pp / 100.0,
                n_bootstrap=n_bootstrap,
                confidence=0.95,
                rng=np.random.default_rng(65200 + int(seed) + int(margin_pp * 10)),
            )
            row.update({
                "selector": selector,
                "margin_pp": margin_pp,
                "budget_ratio": ratio,
                "min_keep": min_keep,
                "target_coverage": target_coverage,
                "score_threshold": threshold,
            })
            rows.append(row)
    return rows


def write_markdown(
    path: Path,
    selected_rows: Sequence[Mapping[str, object]],
    discrimination: Sequence[Mapping[str, object]],
) -> None:
    lines = [
        "# Task65.1 Safe-Compression Attribution",
        "",
        "The upstream fixed-top-10 ranking is held constant. Selector thresholds",
        "and token-budget actions are selected on calibration queries and frozen",
        "before held-out test evaluation.",
    ]
    for margin in (0.0, 1.0):
        lines.extend([
            "",
            f"## Frozen Test Selection (calibration margin: {margin:.0f} pp)",
            "",
            "| Selector | Eligible | Ratio | Min keep | Target coverage | Test hit delta | Test token saving | Actual coverage | Selective risk |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ])
        rows = [row for row in selected_rows if row["margin_pp"] == margin and row["split"] == "test"]
        for row in rows:
            lines.append(
                "| {selector} | {eligible} | {ratio:.2f} | {min_keep} | {target:.2f} | {hit:+.2f} pp | {saving:.2f}% | {coverage:.3f} | {risk:.3f} |".format(
                    selector=row["selector"],
                    eligible=row["eligible"],
                    ratio=float(row["budget_ratio"]),
                    min_keep=row["min_keep"],
                    target=float(row["target_coverage"]),
                    hit=float(row["hit_delta_vs_dense_pp"]),
                    saving=float(row["token_saving_vs_dense_pct"]),
                    coverage=float(row["actual_coverage"]),
                    risk=float(row["source_selective_risk"]),
                )
            )

    lines.extend([
        "",
        "## Safe-Action Discrimination",
        "",
        "The fixed action is `token_budget_r0.85_m4`. Labels are defined only on",
        "queries whose uncompressed source ranking contains relevant evidence.",
        "",
        "| Selector | AUROC | Average precision | Raw Brier | Isotonic Brier |",
        "|---|---:|---:|---:|---:|",
    ])
    for selector in SELECTORS:
        rows = [row for row in discrimination if row["selector"] == selector]
        lines.append(
            "| {selector} | {auc:.3f} | {ap:.3f} | {raw:.3f} | {cal:.3f} |".format(
                selector=selector,
                auc=mean(float(row["auroc"]) for row in rows),
                ap=mean(float(row["average_precision"]) for row in rows),
                raw=mean(float(row["raw_brier"]) for row in rows),
                cal=mean(float(row["isotonic_brier"]) for row in rows),
            )
        )
    lines.extend([
        "",
        "## Guardrails",
        "",
        "- Full-top-10 quality, final budgeted quality, and route metrics are separate layers.",
        "- A selector is useful only if it improves the held-out quality-cost frontier over shuffled/random and budget-only controls.",
        "- The 1 pp margin is a sensitivity analysis; the zero-drop calibration gate is the primary result.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=RESULTS / "task65_1_confidence_trace_100k",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task65_1_safe_compression_attribution",
    )
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()

    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))

    stem = "linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential"
    source_payload = read_json(args.trace_dir / f"{stem}_rankings.json")
    trace_payload = read_json(args.trace_dir / f"{stem}_traces.json")
    source_by_seed = source_payload["gated_cost_aware"]
    traces_by_seed = trace_payload["gated_cost_aware"]

    corpus = context_cost.load_json_list(DATA / "processed" / "lotte_technology_search_100k_corpus.json")
    queries = context_cost.load_json_list(DATA / "processed" / "lotte_technology_search_100k_queries.json")
    calibration_queries, test_queries = calibration.split_queries(
        queries,
        calibration_fraction=0.30,
        salt="task38_lotte_calibration_v1:100k",
    )
    queries_by_split = {"calibration": calibration_queries, "test": test_queries}
    split_ids = {split: [qid(query) for query in items] for split, items in queries_by_split.items()}

    dense_rankings = read_json(
        DATA / "retrieval_artifacts" / "lotte_technology_search_100k__dense_rankings__943110fcc8a19b7c.json"
    )
    count_tokens = context_cost.build_token_counter("tiktoken", "cl100k_base")
    chunk_tokens = {context_cost.chunk_id(chunk): count_tokens(str(chunk.get("text", ""))) for chunk in corpus}

    score_maps: dict[str, dict[str, dict[str, float]]] = {selector: {} for selector in SELECTORS}
    all_ids = split_ids["calibration"] + split_ids["test"]
    for seed, traces in traces_by_seed.items():
        learned = {item: float(traces[item]["confidence"]) for item in all_ids}
        geometry = {item: 1.0 - float(traces[item]["semantic_drift"]) for item in all_ids}
        shuffled: dict[str, float] = {}
        for split_index, split in enumerate(("calibration", "test")):
            shuffled.update(
                shuffled_scores(learned, split_ids[split], seed=65010 + int(seed) + split_index)
            )
        score_maps["learned_confidence"][seed] = learned
        score_maps["geometry_similarity"][seed] = geometry
        score_maps["shuffled_confidence"][seed] = shuffled
        score_maps["random_selector"][seed] = {
            item: stable_uniform("task65.1", seed, item) for item in all_ids
        }
        score_maps["budget_only"][seed] = {item: 1.0 for item in all_ids}

    ratios = (0.75, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95, 0.98)
    min_keeps = (4, 5, 6, 7, 8)
    coverages = tuple(value / 10.0 for value in range(1, 11))
    per_seed_rows: list[dict[str, object]] = []
    ranking_cache: dict[tuple[str, float, int], dict[str, list[str]]] = {}

    for seed, source_rankings in source_by_seed.items():
        for ratio in ratios:
            for min_keep in min_keeps:
                ranking_cache[(seed, ratio, min_keep)] = {
                    query_id: budget.token_budget_ranking(
                        ranking,
                        chunk_tokens,
                        top_k=10,
                        budget_ratio=ratio,
                        min_keep=min_keep,
                    )
                    for query_id, ranking in source_rankings.items()
                }
        for selector in SELECTORS:
            selector_coverages = (1.0,) if selector == "budget_only" else coverages
            calibration_scores = [score_maps[selector][seed][item] for item in split_ids["calibration"]]
            for target_coverage in selector_coverages:
                threshold = threshold_for_coverage(calibration_scores, target_coverage)
                selected = {
                    item: score_maps[selector][seed][item] >= threshold
                    for item in all_ids
                }
                for ratio in ratios:
                    for min_keep in min_keeps:
                        compressed = ranking_cache[(seed, ratio, min_keep)]
                        final_rankings = {
                            item: compressed[item] if selected[item] else source_rankings[item]
                            for item in all_ids
                        }
                        for split, split_queries in queries_by_split.items():
                            row = evaluate_rankings(
                                split_queries,
                                dense_rankings,
                                source_rankings,
                                final_rankings,
                                selected,
                                chunk_tokens,
                            )
                            row.update({
                                "selector": selector,
                                "split": split,
                                "seed": seed,
                                "budget_ratio": ratio,
                                "min_keep": min_keep,
                                "target_coverage": target_coverage,
                                "score_threshold": threshold,
                            })
                            per_seed_rows.append(row)

    aggregate_rows = aggregate_candidate_rows(per_seed_rows)
    selected_rows = select_candidates(aggregate_rows, margin_pp=0.0)
    selected_rows.extend(select_candidates(aggregate_rows, margin_pp=1.0))

    discrimination = discrimination_rows(
        queries_by_split=queries_by_split,
        source_by_seed=source_by_seed,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        ratio=0.85,
        min_keep=4,
        n_bootstrap=args.bootstrap,
    )
    selected_paired = paired_selected_rows(
        selected_rows=selected_rows,
        calibration_ids=split_ids["calibration"],
        test_queries=test_queries,
        dense_rankings=dense_rankings,
        source_by_seed=source_by_seed,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        n_bootstrap=args.bootstrap,
    )

    output = args.output_prefix
    write_csv(output.with_suffix(".per_seed.csv"), per_seed_rows)
    write_csv(output.with_suffix(".frontier.csv"), aggregate_rows)
    write_csv(output.with_suffix(".selected.csv"), selected_rows)
    write_csv(output.with_suffix(".discrimination.csv"), discrimination)
    write_csv(output.with_suffix(".paired.csv"), selected_paired)
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "protocol": {
                    "source_ranking": "Task37 gated_cost_aware fixed top-10",
                    "calibration_queries": len(calibration_queries),
                    "test_queries": len(test_queries),
                    "seeds": sorted(source_by_seed),
                    "selectors": SELECTORS,
                    "ratios": ratios,
                    "min_keeps": min_keeps,
                    "target_coverages": coverages,
                    "safe_action": "token_budget_r0.85_m4",
                },
                "selected_rows": selected_rows,
                "discrimination_rows": discrimination,
                "paired_rows": selected_paired,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(output.with_suffix(".md"), selected_rows, discrimination)
    print(json.dumps({
        "per_seed_rows": len(per_seed_rows),
        "frontier_rows": len(aggregate_rows),
        "selected_rows": len(selected_rows),
        "discrimination_rows": len(discrimination),
        "paired_rows": len(selected_paired),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
