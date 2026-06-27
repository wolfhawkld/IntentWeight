#!/usr/bin/env python3
"""Run the fixed-dense-pool safe-compression attribution experiment.

All treatments operate on the same dense top-10 ranking, calibration/test
split, token-budget action grid, and seeds. Route experiments provide only the
query-level selector signal; they cannot change the evidence candidate pool.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS = ROOT / "paper" / "experiments" / "results"
DATA = ROOT / "paper" / "experiments" / "data"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_module(
    "task65_1_safe_compression_attribution",
    SCRIPT_DIR / "task65_1_safe_compression_attribution.py",
)

SELECTORS = (
    "geometry_feedback",
    "geometry_no_feedback",
    "random_feedback",
    "random_no_feedback",
    "dense_budget_only",
)
RATIOS = (0.75, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95, 0.98)
MIN_KEEPS = (4, 5, 6, 7, 8)
COVERAGES = tuple(value / 10.0 for value in range(1, 11))
SAVING_TARGETS = (5.0, 10.0, 15.0, 20.0)
PAIRWISE_CONTRASTS = (
    ("geometry_feedback", "geometry_no_feedback", "feedback_effect_geometry"),
    ("geometry_feedback", "random_feedback", "geometry_effect_feedback"),
    ("geometry_no_feedback", "random_no_feedback", "geometry_effect_no_feedback"),
    ("random_feedback", "random_no_feedback", "feedback_effect_random"),
    ("geometry_feedback", "dense_budget_only", "selector_vs_budget_only"),
)


def read_trace_payload(directory: Path) -> Mapping:
    paths = sorted(directory.glob("*_prequential_traces.json"))
    if len(paths) != 1:
        raise ValueError(f"Expected one trace payload in {directory}, got {len(paths)}")
    return base.read_json(paths[0])


def build_score_maps(
    learned_payload: Mapping,
    control_payload: Mapping,
    split_ids: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, dict[str, float]]]:
    learned = learned_payload["gated_cost_aware"]
    static = control_payload["static_nearest_gated"]
    random_feedback = control_payload["random_partition_feedback_ensemble"]
    random_static = control_payload["random_partition_static_ensemble"]
    seeds = sorted(set(learned) & set(static) & set(random_feedback) & set(random_static))
    if seeds != ["13", "17", "19"]:
        raise ValueError(f"Expected fixed seeds 13/17/19, got {seeds}")
    all_ids = list(split_ids["calibration"]) + list(split_ids["test"])
    result = {selector: {} for selector in SELECTORS}
    for seed in seeds:
        missing = [
            query_id
            for query_id in all_ids
            if query_id not in learned[seed]
            or query_id not in static[seed]
            or query_id not in random_feedback[seed]
            or query_id not in random_static[seed]
        ]
        if missing:
            raise ValueError(f"Missing {len(missing)} traces for seed {seed}")
        result["geometry_feedback"][seed] = {
            query_id: float(learned[seed][query_id]["confidence"])
            for query_id in all_ids
        }
        result["geometry_no_feedback"][seed] = {
            query_id: float(static[seed][query_id]["confidence"])
            for query_id in all_ids
        }
        result["random_feedback"][seed] = {
            query_id: float(random_feedback[seed][query_id]["confidence"])
            for query_id in all_ids
        }
        result["random_no_feedback"][seed] = {
            query_id: float(random_static[seed][query_id]["confidence"])
            for query_id in all_ids
        }
        result["dense_budget_only"][seed] = {query_id: 1.0 for query_id in all_ids}
    return result


def matched_saving_rows(
    aggregate_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    calibration_rows = [row for row in aggregate_rows if row["split"] == "calibration"]
    test_index = {
        (row["selector"], row["budget_ratio"], row["min_keep"], row["target_coverage"]): row
        for row in aggregate_rows
        if row["split"] == "test"
    }
    selected: list[dict[str, object]] = []
    for selector in SELECTORS:
        candidates = [row for row in calibration_rows if row["selector"] == selector]
        for target in SAVING_TARGETS:
            choice = min(
                candidates,
                key=lambda row: (
                    abs(float(row["token_saving_vs_dense_pct"]) - target),
                    -float(row["hit_delta_vs_dense_pp"]),
                    -float(row["token_saving_vs_dense_pct"]),
                ),
            )
            key = (choice["selector"], choice["budget_ratio"], choice["min_keep"], choice["target_coverage"])
            for split, source in (("calibration", choice), ("test", test_index[key])):
                row = dict(source)
                row["saving_target_pct"] = target
                row["split"] = split
                selected.append(row)
    return selected


def paired_for_choices(
    *,
    choices: Sequence[Mapping[str, object]],
    calibration_ids: Sequence[str],
    test_queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    score_maps: Mapping[str, Mapping[str, Mapping[str, float]]],
    chunk_tokens: Mapping[str, int],
    n_bootstrap: int,
    choice_label: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    baseline = base.paired.Variant("dense", "dense_top10", "", dict(dense_rankings))
    for choice_index, choice in enumerate(row for row in choices if row["split"] == "test"):
        selector = str(choice["selector"])
        ratio = float(choice["budget_ratio"])
        min_keep = int(choice["min_keep"])
        target_coverage = float(choice["target_coverage"])
        for seed in sorted(score_maps[selector]):
            threshold = base.threshold_for_coverage(
                [score_maps[selector][seed][query_id] for query_id in calibration_ids],
                target_coverage,
            )
            final_rankings = {}
            for query_id, dense in dense_rankings.items():
                selected = score_maps[selector][seed][query_id] >= threshold
                final_rankings[query_id] = (
                    base.budget.token_budget_ranking(
                        dense,
                        chunk_tokens,
                        top_k=10,
                        budget_ratio=ratio,
                        min_keep=min_keep,
                    )
                    if selected
                    else [str(item) for item in dense[:10]]
                )
            row = base.paired.compare_variant(
                scale="100k",
                queries=test_queries,
                baseline=baseline,
                variant=base.paired.Variant(
                    selector,
                    f"{selector}:r{ratio:.2f}:m{min_keep}:c{target_coverage:.2f}",
                    seed,
                    final_rankings,
                ),
                chunk_tokens=chunk_tokens,
                k=10,
                noninferiority_margin=0.0,
                n_bootstrap=n_bootstrap,
                confidence=0.95,
                rng=np.random.default_rng(65220 + int(seed) + choice_index * 101),
            )
            row.update({
                "selector": selector,
                "choice_label": choice_label,
                "budget_ratio": ratio,
                "min_keep": min_keep,
                "target_coverage": target_coverage,
                "score_threshold": threshold,
            })
            if "margin_pp" in choice:
                row["margin_pp"] = float(choice["margin_pp"])
            if "saving_target_pct" in choice:
                row["saving_target_pct"] = float(choice["saving_target_pct"])
            rows.append(row)
    return rows


def final_rankings_for_choice(
    choice: Mapping[str, object],
    *,
    seed: str,
    calibration_ids: Sequence[str],
    dense_rankings: Mapping[str, Sequence[str]],
    score_maps: Mapping[str, Mapping[str, Mapping[str, float]]],
    chunk_tokens: Mapping[str, int],
) -> tuple[dict[str, list[str]], float]:
    selector = str(choice["selector"])
    ratio = float(choice["budget_ratio"])
    min_keep = int(choice["min_keep"])
    target_coverage = float(choice["target_coverage"])
    threshold = base.threshold_for_coverage(
        [score_maps[selector][seed][query_id] for query_id in calibration_ids],
        target_coverage,
    )
    rankings = {}
    for query_id, dense in dense_rankings.items():
        rankings[query_id] = (
            base.budget.token_budget_ranking(
                dense,
                chunk_tokens,
                top_k=10,
                budget_ratio=ratio,
                min_keep=min_keep,
            )
            if score_maps[selector][seed][query_id] >= threshold
            else [str(item) for item in dense[:10]]
        )
    return rankings, threshold


def pairwise_matched_saving_rows(
    *,
    choices: Sequence[Mapping[str, object]],
    calibration_ids: Sequence[str],
    test_queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    score_maps: Mapping[str, Mapping[str, Mapping[str, float]]],
    chunk_tokens: Mapping[str, int],
    n_bootstrap: int,
) -> list[dict[str, object]]:
    choice_index = {
        (str(row["selector"]), float(row["saving_target_pct"])): row
        for row in choices
        if row["split"] == "test"
    }
    rows: list[dict[str, object]] = []
    for contrast_index, (method, reference, contrast) in enumerate(PAIRWISE_CONTRASTS):
        for target_index, target in enumerate(SAVING_TARGETS):
            method_choice = choice_index[(method, target)]
            reference_choice = choice_index[(reference, target)]
            for seed in sorted(score_maps[method]):
                method_rankings, method_threshold = final_rankings_for_choice(
                    method_choice,
                    seed=seed,
                    calibration_ids=calibration_ids,
                    dense_rankings=dense_rankings,
                    score_maps=score_maps,
                    chunk_tokens=chunk_tokens,
                )
                reference_rankings, reference_threshold = final_rankings_for_choice(
                    reference_choice,
                    seed=seed,
                    calibration_ids=calibration_ids,
                    dense_rankings=dense_rankings,
                    score_maps=score_maps,
                    chunk_tokens=chunk_tokens,
                )
                row = base.paired.compare_variant(
                    scale="100k",
                    queries=test_queries,
                    baseline=base.paired.Variant(
                        reference,
                        f"{reference}:target{target:.0f}",
                        seed,
                        reference_rankings,
                    ),
                    variant=base.paired.Variant(
                        method,
                        f"{method}:target{target:.0f}",
                        seed,
                        method_rankings,
                    ),
                    chunk_tokens=chunk_tokens,
                    k=10,
                    noninferiority_margin=0.0,
                    n_bootstrap=n_bootstrap,
                    confidence=0.95,
                    rng=np.random.default_rng(
                        65400 + int(seed) + contrast_index * 1009 + target_index * 10007
                    ),
                )
                row.update({
                    "contrast": contrast,
                    "method_selector": method,
                    "reference_selector": reference,
                    "saving_target_pct": target,
                    "method_score_threshold": method_threshold,
                    "reference_score_threshold": reference_threshold,
                    "method_dense_saving_pct": float(method_choice["token_saving_vs_dense_pct"]),
                    "reference_dense_saving_pct": float(reference_choice["token_saving_vs_dense_pct"]),
                })
                rows.append(row)
    return rows


def bootstrap_risk(
    labels: np.ndarray,
    selected: np.ndarray,
    *,
    rng: np.random.Generator,
    n_bootstrap: int,
) -> tuple[float, float, float]:
    observed = float(np.mean(1 - labels[selected])) if np.any(selected) else 0.0
    samples: list[float] = []
    indices = np.flatnonzero(selected)
    if indices.size == 0:
        return observed, observed, observed
    for _ in range(n_bootstrap):
        sampled = rng.choice(indices, size=indices.size, replace=True)
        samples.append(float(np.mean(1 - labels[sampled])))
    return observed, float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def risk_coverage_rows(
    *,
    calibration_queries: Sequence[Mapping],
    test_queries: Sequence[Mapping],
    dense_rankings: Mapping[str, Sequence[str]],
    score_maps: Mapping[str, Mapping[str, Mapping[str, float]]],
    chunk_tokens: Mapping[str, int],
    ratio: float,
    min_keep: int,
    n_bootstrap: int,
) -> list[dict[str, object]]:
    labels: dict[str, dict[str, int]] = {"calibration": {}, "test": {}}
    for split, queries in (("calibration", calibration_queries), ("test", test_queries)):
        for query in queries:
            query_id = base.qid(query)
            truth = base.ground_truth(query)
            dense = [str(item) for item in dense_rankings[query_id][:10]]
            if not base.hit(dense, truth):
                continue
            compressed = base.budget.token_budget_ranking(
                dense,
                chunk_tokens,
                top_k=10,
                budget_ratio=ratio,
                min_keep=min_keep,
            )
            labels[split][query_id] = base.hit(compressed, truth)

    rows: list[dict[str, object]] = []
    for selector_index, selector in enumerate(SELECTORS):
        for seed in sorted(score_maps[selector]):
            calibration_ids = sorted(labels["calibration"])
            test_ids = sorted(labels["test"])
            calibration_scores = [score_maps[selector][seed][query_id] for query_id in calibration_ids]
            test_scores = np.asarray(
                [score_maps[selector][seed][query_id] for query_id in test_ids],
                dtype=np.float64,
            )
            test_labels = np.asarray([labels["test"][query_id] for query_id in test_ids], dtype=np.int32)
            for coverage_index, target_coverage in enumerate(COVERAGES):
                threshold = base.threshold_for_coverage(calibration_scores, target_coverage)
                selected = test_scores >= threshold
                risk, risk_lo, risk_hi = bootstrap_risk(
                    test_labels,
                    selected,
                    rng=np.random.default_rng(
                        65300 + int(seed) + selector_index * 101 + coverage_index * 1009
                    ),
                    n_bootstrap=n_bootstrap,
                )
                rows.append({
                    "selector": selector,
                    "seed": seed,
                    "action": f"token_budget_r{ratio:.2f}_m{min_keep}",
                    "target_coverage": target_coverage,
                    "score_threshold": threshold,
                    "actual_coverage": float(np.mean(selected)),
                    "selected_examples": int(np.sum(selected)),
                    "test_examples": len(test_ids),
                    "selective_risk": risk,
                    "selective_risk_ci_low": risk_lo,
                    "selective_risk_ci_high": risk_hi,
                })
    return rows


def write_markdown(
    path: Path,
    quality_rows: Sequence[Mapping[str, object]],
    saving_rows: Sequence[Mapping[str, object]],
    discrimination: Sequence[Mapping[str, object]],
    pairwise_saving: Sequence[Mapping[str, object]],
) -> None:
    lines = [
        "# Task65.2 Fixed-Pool Factorial Safe-Compression Attribution",
        "",
        "All five treatments use the same dense top-10 candidate pool, split,",
        "token-budget grid, and seeds. Route signals only select which queries",
        "receive compression.",
        "",
        "## Same Quality Constraint",
        "",
        "| Selector | Calibration margin | Test hit delta | Test token saving |",
        "|---|---:|---:|---:|",
    ]
    for margin in (0.0, 1.0):
        for row in quality_rows:
            if row["split"] == "test" and float(row["margin_pp"]) == margin:
                lines.append(
                    f"| {row['selector']} | {margin:.0f} pp | "
                    f"{float(row['hit_delta_vs_dense_pp']):+.2f} pp | "
                    f"{float(row['token_saving_vs_dense_pct']):.2f}% |"
                )
    lines.extend([
        "",
        "## Same Token-Saving Target",
        "",
        "| Selector | Target | Test hit delta | Test token saving |",
        "|---|---:|---:|---:|",
    ])
    for target in SAVING_TARGETS:
        for row in saving_rows:
            if row["split"] == "test" and float(row["saving_target_pct"]) == target:
                lines.append(
                    f"| {row['selector']} | {target:.0f}% | "
                    f"{float(row['hit_delta_vs_dense_pp']):+.2f} pp | "
                    f"{float(row['token_saving_vs_dense_pct']):.2f}% |"
                )
    lines.extend([
        "",
        "## Fixed-Action Failure Prediction",
        "",
        "The fixed action is `token_budget_r0.85_m4`; higher scores predict safe",
        "compression. Metrics are held-out means across seeds.",
        "",
        "| Selector | AUROC | AUPRC | Isotonic Brier | Isotonic ECE |",
        "|---|---:|---:|---:|---:|",
    ])
    for selector in SELECTORS:
        rows = [row for row in discrimination if row["selector"] == selector]
        lines.append(
            f"| {selector} | {mean(float(row['auroc']) for row in rows):.3f} | "
            f"{mean(float(row['average_precision']) for row in rows):.3f} | "
            f"{mean(float(row['isotonic_brier']) for row in rows):.3f} | "
            f"{mean(float(row['isotonic_ece']) for row in rows):.3f} |"
        )
    lines.extend([
        "",
        "## Pairwise Effects At Matched Saving Targets",
        "",
        "Positive hit delta favors the method named before `vs`; values are",
        "means across seeds. Per-seed bootstrap intervals are in the CSV artifact.",
        "",
        "| Contrast | Target | Hit delta | Method saving | Reference saving |",
        "|---|---:|---:|---:|---:|",
    ])
    for method, reference, contrast in PAIRWISE_CONTRASTS:
        for target in SAVING_TARGETS:
            rows = [
                row for row in pairwise_saving
                if row["contrast"] == contrast and float(row["saving_target_pct"]) == target
            ]
            lines.append(
                f"| {method} vs {reference} | {target:.0f}% | "
                f"{mean(float(row['hit_delta_mean']) for row in rows) * 100:+.2f} pp | "
                f"{mean(float(row['method_dense_saving_pct']) for row in rows):.2f}% | "
                f"{mean(float(row['reference_dense_saving_pct']) for row in rows):.2f}% |"
            )
    lines.extend([
        "",
        "## Interpretation Guardrail",
        "",
        "This experiment tests safe-compression identification only. It does not",
        "replace Task58/59 route-quality evidence because the candidate ranking is",
        "deliberately fixed to dense top-10.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--learned-trace-dir",
        type=Path,
        default=RESULTS / "task65_1_confidence_trace_100k",
    )
    parser.add_argument(
        "--control-trace-dir",
        type=Path,
        default=RESULTS / "task65_2_factorial_signal_traces_100k",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task65_2_factorial_safe_compression",
    )
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()

    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))

    corpus = base.context_cost.load_json_list(
        DATA / "processed" / "lotte_technology_search_100k_corpus.json"
    )
    queries = base.context_cost.load_json_list(
        DATA / "processed" / "lotte_technology_search_100k_queries.json"
    )
    calibration_queries, test_queries = base.calibration.split_queries(
        queries,
        calibration_fraction=0.30,
        salt="task38_lotte_calibration_v1:100k",
    )
    queries_by_split = {"calibration": calibration_queries, "test": test_queries}
    split_ids = {
        split: [base.qid(query) for query in split_queries]
        for split, split_queries in queries_by_split.items()
    }
    dense_rankings = base.read_json(
        DATA / "retrieval_artifacts" / "lotte_technology_search_100k__dense_rankings__943110fcc8a19b7c.json"
    )
    count_tokens = base.context_cost.build_token_counter("tiktoken", "cl100k_base")
    chunk_tokens = {
        base.context_cost.chunk_id(chunk): count_tokens(str(chunk.get("text", "")))
        for chunk in corpus
    }
    score_maps = build_score_maps(
        read_trace_payload(args.learned_trace_dir),
        read_trace_payload(args.control_trace_dir),
        split_ids,
    )
    seeds = sorted(score_maps[SELECTORS[0]])
    source_by_seed = {seed: dense_rankings for seed in seeds}
    all_ids = split_ids["calibration"] + split_ids["test"]

    ranking_cache = {
        (ratio, min_keep): {
            query_id: base.budget.token_budget_ranking(
                ranking,
                chunk_tokens,
                top_k=10,
                budget_ratio=ratio,
                min_keep=min_keep,
            )
            for query_id, ranking in dense_rankings.items()
        }
        for ratio in RATIOS
        for min_keep in MIN_KEEPS
    }
    per_seed_rows: list[dict[str, object]] = []
    for seed in seeds:
        for selector in SELECTORS:
            selector_coverages = (1.0,) if selector == "dense_budget_only" else COVERAGES
            calibration_scores = [
                score_maps[selector][seed][query_id]
                for query_id in split_ids["calibration"]
            ]
            for target_coverage in selector_coverages:
                threshold = base.threshold_for_coverage(calibration_scores, target_coverage)
                selected = {
                    query_id: score_maps[selector][seed][query_id] >= threshold
                    for query_id in all_ids
                }
                for ratio in RATIOS:
                    for min_keep in MIN_KEEPS:
                        compressed = ranking_cache[(ratio, min_keep)]
                        final_rankings = {
                            query_id: compressed[query_id] if selected[query_id] else dense_rankings[query_id]
                            for query_id in all_ids
                        }
                        for split, split_queries in queries_by_split.items():
                            row = base.evaluate_rankings(
                                split_queries,
                                dense_rankings,
                                dense_rankings,
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

    frontier_rows = base.aggregate_candidate_rows(per_seed_rows)
    quality_rows = base.select_candidates(frontier_rows, margin_pp=0.0, selectors=SELECTORS)
    quality_rows.extend(base.select_candidates(frontier_rows, margin_pp=1.0, selectors=SELECTORS))
    saving_rows = matched_saving_rows(frontier_rows)
    discrimination = base.discrimination_rows(
        queries_by_split=queries_by_split,
        source_by_seed=source_by_seed,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        ratio=0.85,
        min_keep=4,
        n_bootstrap=args.bootstrap,
        selectors=SELECTORS,
    )
    risk_coverage = risk_coverage_rows(
        calibration_queries=calibration_queries,
        test_queries=test_queries,
        dense_rankings=dense_rankings,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        ratio=0.85,
        min_keep=4,
        n_bootstrap=args.bootstrap,
    )
    paired_quality = paired_for_choices(
        choices=quality_rows,
        calibration_ids=split_ids["calibration"],
        test_queries=test_queries,
        dense_rankings=dense_rankings,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        n_bootstrap=args.bootstrap,
        choice_label="quality_constraint",
    )
    paired_saving = paired_for_choices(
        choices=saving_rows,
        calibration_ids=split_ids["calibration"],
        test_queries=test_queries,
        dense_rankings=dense_rankings,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        n_bootstrap=args.bootstrap,
        choice_label="saving_target",
    )
    pairwise_saving = pairwise_matched_saving_rows(
        choices=saving_rows,
        calibration_ids=split_ids["calibration"],
        test_queries=test_queries,
        dense_rankings=dense_rankings,
        score_maps=score_maps,
        chunk_tokens=chunk_tokens,
        n_bootstrap=args.bootstrap,
    )

    output = args.output_prefix
    base.write_csv(output.with_suffix(".per_seed.csv"), per_seed_rows)
    base.write_csv(output.with_suffix(".frontier.csv"), frontier_rows)
    base.write_csv(output.with_suffix(".quality_matched.csv"), quality_rows)
    base.write_csv(output.with_suffix(".saving_matched.csv"), saving_rows)
    base.write_csv(output.with_suffix(".discrimination.csv"), discrimination)
    base.write_csv(output.with_suffix(".risk_coverage.csv"), risk_coverage)
    base.write_csv(output.with_suffix(".paired_quality.csv"), paired_quality)
    base.write_csv(output.with_suffix(".paired_saving.csv"), paired_saving)
    base.write_csv(output.with_suffix(".pairwise_saving.csv"), pairwise_saving)
    output.with_suffix(".json").write_text(
        json.dumps({
            "protocol": {
                "candidate_pool": "dense top-10 fixed for every treatment",
                "calibration_queries": len(calibration_queries),
                "test_queries": len(test_queries),
                "seeds": seeds,
                "selectors": SELECTORS,
                "ratios": RATIOS,
                "min_keeps": MIN_KEEPS,
                "coverages": COVERAGES,
                "saving_targets_pct": SAVING_TARGETS,
                "safe_action": "token_budget_r0.85_m4",
            },
            "quality_matched": quality_rows,
            "saving_matched": saving_rows,
            "discrimination": discrimination,
            "risk_coverage": risk_coverage,
            "paired_quality": paired_quality,
            "paired_saving": paired_saving,
            "pairwise_saving": pairwise_saving,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(
        output.with_suffix(".md"),
        quality_rows,
        saving_rows,
        discrimination,
        pairwise_saving,
    )
    print(json.dumps({
        "per_seed_rows": len(per_seed_rows),
        "frontier_rows": len(frontier_rows),
        "quality_rows": len(quality_rows),
        "saving_rows": len(saving_rows),
        "discrimination_rows": len(discrimination),
        "risk_coverage_rows": len(risk_coverage),
        "paired_quality_rows": len(paired_quality),
        "paired_saving_rows": len(paired_saving),
        "pairwise_saving_rows": len(pairwise_saving),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
