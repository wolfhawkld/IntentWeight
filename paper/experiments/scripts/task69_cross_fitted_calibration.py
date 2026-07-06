#!/usr/bin/env python3
"""Run the Task69 five-fold context-budget protocol on frozen rankings."""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib.util
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DATA = ROOT / "paper" / "experiments" / "data"
RESULTS = ROOT / "paper" / "experiments" / "results"
NUM_FOLDS = 5
RATIOS = (0.98, 0.95, 0.92, 0.90, 0.88, 0.85)
MIN_KEEPS = (4, 5, 6, 7, 8)
SELECTION_MARGIN = 1e-12
NI_MARGIN = 0.01
BOOTSTRAP_SAMPLES = 10_000
FOLD_SALT = "task65_6_cross_scale_crossfit_v1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cost = load_module("task69_cost", SCRIPT_DIR / "context_token_cost.py")
budget = load_module("task69_budget", SCRIPT_DIR / "task37_context_budget_search.py")
calibration = load_module("task69_calibration", SCRIPT_DIR / "task38_calibrated_context_budget.py")
paired = load_module("task69_paired", SCRIPT_DIR / "task37_paired_significance.py")


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def only_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise ValueError(f"Expected one {pattern!r} in {directory}, found {len(matches)}")
    return matches[0]


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_query_id(query: Mapping) -> str:
    metadata = query.get("metadata")
    if isinstance(metadata, Mapping) and metadata.get("original_query_id") is not None:
        return str(metadata["original_query_id"])
    return cost.query_id(query)


def query_folds(queries: Sequence[Mapping]):
    scored = []
    for query in queries:
        qid = cost.query_id(query)
        canonical_id = canonical_query_id(query)
        digest = hashlib.sha256(f"{FOLD_SALT}:{canonical_id}".encode()).hexdigest()
        scored.append((digest, canonical_id, qid, query))
    scored.sort(key=lambda item: (item[0], item[1]))
    folds: list[list[Mapping]] = [[] for _ in range(NUM_FOLDS)]
    assignments: dict[str, int] = {}
    canonical_ids: set[str] = set()
    for index, (_, canonical_id, qid, query) in enumerate(scored):
        if canonical_id in canonical_ids:
            raise ValueError(f"Duplicate canonical query ID: {canonical_id}")
        canonical_ids.add(canonical_id)
        fold = index % NUM_FOLDS
        assignments[qid] = fold
        folds[fold].append(query)
    return assignments, folds


def load_sources(source_dir: Path):
    ranking_path = only_file(source_dir, "*_prequential_rankings.json")
    metrics_path = only_file(source_dir, "*_prequential_metrics.json")
    metrics = read_json(metrics_path)[0]
    method_sources = [
        variant
        for variant in cost.load_ranking_variants("task69_source", ranking_path)
        if variant.method == "gated_cost_aware"
    ]
    if len(method_sources) != 3:
        raise ValueError(f"Expected three route seeds, found {len(method_sources)}")

    dense_path = Path(str(metrics["dense_ranking_artifact_path"]))
    if not dense_path.exists():
        dense_path = DATA / "retrieval_artifacts" / dense_path.name
    dense_sources = cost.load_ranking_variants("dense", dense_path)
    if len(dense_sources) != 1:
        raise ValueError(f"Expected one Dense ranking variant, found {len(dense_sources)}")
    return method_sources, dense_sources[0], ranking_path, metrics_path, dense_path


def needed_chunk_ids(method_sources: Sequence, dense_source) -> set[str]:
    chunk_ids: set[str] = set()
    for variant in [*method_sources, dense_source]:
        for ranking in variant.rankings.values():
            chunk_ids.update(str(item) for item in ranking[:10])
    return chunk_ids


def load_needed_tokens(corpus_path: Path, needed: set[str]) -> dict[str, int]:
    corpus = cost.load_json_list(corpus_path)
    count_tokens = cost.build_token_counter("tiktoken", "cl100k_base")
    tokens = {
        chunk_key: count_tokens(str(chunk.get("text", "")))
        for chunk in corpus
        if (chunk_key := cost.chunk_id(chunk)) in needed
    }
    del corpus
    gc.collect()
    missing = needed - tokens.keys()
    if missing:
        raise ValueError(f"Missing {len(missing)} ranked chunks from {corpus_path}")
    return tokens


def evaluate(variant, queries, chunk_tokens):
    return cost.evaluate_variant(variant, queries, chunk_tokens, ks=(10,), skip_empty_gt=True)


def policy_lookup(variants: Sequence) -> dict[tuple[str, str], object]:
    lookup = {}
    for variant in variants:
        key = (str(variant.policy), str(variant.seed))
        if key in lookup:
            raise ValueError(f"Duplicate policy/seed variant: {key}")
        lookup[key] = variant
    return lookup


def calibration_choice(variants, dense_source, queries, chunk_tokens):
    dense_metrics = evaluate(dense_source, queries, chunk_tokens)
    rows = []
    for variant in variants:
        row = evaluate(variant, queries, chunk_tokens)
        row["policy"] = variant.policy
        rows.append(row)
    calibration.add_dense_deltas(
        rows,
        baseline_hit=float(dense_metrics["hit@10"]),
        baseline_tokens=float(dense_metrics["avg_context_tokens@10"]),
        k=10,
    )
    return calibration.choose_policy(rows, margin=SELECTION_MARGIN, k=10)


def fold_metrics(variant, dense_source, queries, chunk_tokens):
    dense = evaluate(dense_source, queries, chunk_tokens)
    result = evaluate(variant, queries, chunk_tokens)
    dense_tokens = float(dense["avg_context_tokens@10"])
    return {
        "hit@10": float(result["hit@10"]),
        "hit_delta_pp": (float(result["hit@10"]) - float(dense["hit@10"])) * 100.0,
        "saving_pct": (1.0 - float(result["avg_context_tokens@10"]) / dense_tokens) * 100.0,
    }


def composite_variant(label: str, seed: str, rankings: Mapping[str, Sequence[str]]):
    return paired.Variant(
        label=label,
        run_id=f"task69:{label}:seed{seed}" if seed else f"task69:{label}",
        seed=seed,
        rankings={str(qid): [str(item) for item in ranking] for qid, ranking in rankings.items()},
    )


def run(args):
    query_path = args.data_dir / f"{args.dataset}_queries.json"
    corpus_path = args.data_dir / f"{args.dataset}_corpus.json"
    method_sources, dense_source, route_path, metrics_path, dense_path = load_sources(args.source_dir)
    needed = needed_chunk_ids(method_sources, dense_source)
    chunk_tokens = load_needed_tokens(corpus_path, needed)
    queries = cost.load_json_list(query_path)
    assignments, folds = query_folds(queries)
    if max(map(len, folds)) - min(map(len, folds)) > 1:
        raise AssertionError("Unbalanced folds")

    method_policies = budget.build_policy_variants(
        method_sources,
        chunk_tokens,
        top_k=10,
        budget_ratios=RATIOS,
        min_keeps=MIN_KEEPS,
        fixed_keeps=(),
    )
    dense_policies = budget.build_policy_variants(
        [dense_source],
        chunk_tokens,
        top_k=10,
        budget_ratios=RATIOS,
        min_keeps=MIN_KEEPS,
        fixed_keeps=(),
    )
    method_lookup = policy_lookup(method_policies)
    dense_lookup = policy_lookup(dense_policies)
    seeds = sorted(str(source.seed) for source in method_sources)
    method_oof = {seed: {} for seed in seeds}
    dense_oof = {}
    fold_rows = []
    selections = []

    for fold_index, test_queries in enumerate(folds):
        calibration_queries = [
            query for index, fold in enumerate(folds) if index != fold_index for query in fold
        ]
        method_choice = calibration_choice(method_policies, dense_source, calibration_queries, chunk_tokens)
        dense_choice = calibration_choice(dense_policies, dense_source, calibration_queries, chunk_tokens)
        method_fallback = not method_choice.eligible
        dense_fallback = not dense_choice.eligible

        for query in test_queries:
            qid = cost.query_id(query)
            for seed in seeds:
                variant = dense_source if method_fallback else method_lookup[(method_choice.policy, seed)]
                method_oof[seed][qid] = list(variant.rankings.get(qid, []))[:10]
            dense_variant = dense_source if dense_fallback else dense_lookup[(dense_choice.policy, "")]
            dense_oof[qid] = list(dense_variant.rankings.get(qid, []))[:10]

        seed_metrics = []
        for seed in seeds:
            variant = dense_source if method_fallback else method_lookup[(method_choice.policy, seed)]
            metrics = fold_metrics(variant, dense_source, test_queries, chunk_tokens)
            seed_metrics.append(metrics)
            fold_rows.append(
                {
                    "dataset": args.dataset,
                    "fold": fold_index,
                    "method": "intentroute",
                    "seed": seed,
                    "calibration_queries": len(calibration_queries),
                    "test_queries": len(test_queries),
                    "selected_policy": "dense_top10_fallback" if method_fallback else method_choice.policy,
                    "calibration_eligible": method_choice.eligible,
                    "calibration_hit_delta_pp": method_choice.mean_hit_delta * 100.0,
                    "calibration_saving_pct": method_choice.mean_token_saving_percent,
                    **metrics,
                }
            )

        dense_test = dense_source if dense_fallback else dense_lookup[(dense_choice.policy, "")]
        dense_metrics = fold_metrics(dense_test, dense_source, test_queries, chunk_tokens)
        fold_rows.append(
            {
                "dataset": args.dataset,
                "fold": fold_index,
                "method": "dense",
                "seed": "",
                "calibration_queries": len(calibration_queries),
                "test_queries": len(test_queries),
                "selected_policy": "dense_top10_fallback" if dense_fallback else dense_choice.policy,
                "calibration_eligible": dense_choice.eligible,
                "calibration_hit_delta_pp": dense_choice.mean_hit_delta * 100.0,
                "calibration_saving_pct": dense_choice.mean_token_saving_percent,
                **dense_metrics,
            }
        )
        selection = {
            "dataset": args.dataset,
            "fold": fold_index,
            "intentroute_policy": "dense_top10_fallback" if method_fallback else method_choice.policy,
            "intentroute_eligible": method_choice.eligible,
            "intentroute_test_hit_delta_mean_pp": mean(row["hit_delta_pp"] for row in seed_metrics),
            "intentroute_test_saving_mean_pct": mean(row["saving_pct"] for row in seed_metrics),
            "dense_policy": "dense_top10_fallback" if dense_fallback else dense_choice.policy,
            "dense_eligible": dense_choice.eligible,
            "dense_test_hit_delta_pp": dense_metrics["hit_delta_pp"],
            "dense_test_saving_pct": dense_metrics["saving_pct"],
        }
        selections.append(selection)
        print(json.dumps(selection, sort_keys=True), flush=True)

    expected = {cost.query_id(query) for query in queries}
    if set(dense_oof) != expected or any(set(rows) != expected for rows in method_oof.values()):
        raise AssertionError("OOF rankings do not cover every query")

    baseline = composite_variant("dense_top10", "", dense_source.rankings)
    comparisons = []
    for index, seed in enumerate(seeds):
        comparisons.append(
            paired.compare_variant(
                scale=args.dataset,
                queries=queries,
                baseline=baseline,
                variant=composite_variant("intentroute_crossfit", seed, method_oof[seed]),
                chunk_tokens=chunk_tokens,
                k=10,
                noninferiority_margin=NI_MARGIN,
                n_bootstrap=BOOTSTRAP_SAMPLES,
                confidence=0.95,
                rng=np.random.default_rng(args.bootstrap_seed + index),
            )
        )
    comparisons.append(
        paired.compare_variant(
            scale=args.dataset,
            queries=queries,
            baseline=baseline,
            variant=composite_variant("dense_crossfit", "", dense_oof),
            chunk_tokens=chunk_tokens,
            k=10,
            noninferiority_margin=NI_MARGIN,
            n_bootstrap=BOOTSTRAP_SAMPLES,
            confidence=0.95,
            rng=np.random.default_rng(args.bootstrap_seed + 99),
        )
    )

    intent_rows = [row for row in comparisons if row["method_label"] == "intentroute_crossfit"]
    summary = {
        "dataset": args.dataset,
        "queries": len(expected),
        "folds": NUM_FOLDS,
        "fold_sizes": [len(fold) for fold in folds],
        "intentroute_eligible_folds": sum(bool(row["intentroute_eligible"]) for row in selections),
        "intentroute_policy_counts": dict(Counter(row["intentroute_policy"] for row in selections)),
        "intentroute_hit_delta_mean_pp": mean(float(row["hit_delta_mean"]) for row in intent_rows) * 100.0,
        "intentroute_saving_mean_pct": mean(float(row["token_saving_percent"]) for row in intent_rows),
        "intentroute_noninferior_seeds_1pp": sum(bool(row["noninferior_by_ci"]) for row in intent_rows),
        "dense_policy_counts": dict(Counter(row["dense_policy"] for row in selections)),
        "dense_hit_delta_pp": float(comparisons[-1]["hit_delta_mean"]) * 100.0,
        "dense_saving_pct": float(comparisons[-1]["token_saving_percent"]),
    }
    artifacts = {
        "intentroute_rankings": {"path": str(route_path.relative_to(ROOT)), "sha256": sha256_file(route_path)},
        "intentroute_metrics": {"path": str(metrics_path.relative_to(ROOT)), "sha256": sha256_file(metrics_path)},
        "dense_rankings": {"path": str(dense_path.relative_to(ROOT)), "sha256": sha256_file(dense_path)},
        "queries": {"path": str(query_path.relative_to(ROOT)), "sha256": sha256_file(query_path)},
        "corpus": {"path": str(corpus_path.relative_to(ROOT)), "sha256": sha256_file(corpus_path)},
    }
    return fold_rows, selections, comparisons, summary, method_oof, dense_oof, assignments, artifacts


def write_markdown(path: Path, summary: Mapping, selections: Sequence[Mapping]) -> None:
    lines = [
        f"# Task69 Cross-Fitted Calibration: {summary['dataset']}",
        "",
        "Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.",
        "",
        "## Result",
        "",
        "| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {summary['queries']} | {summary['intentroute_eligible_folds']}/{NUM_FOLDS} | "
        f"{summary['intentroute_hit_delta_mean_pp']:+.2f} pp | "
        f"{summary['intentroute_saving_mean_pct']:.2f}% | "
        f"{summary['intentroute_noninferior_seeds_1pp']}/3 | "
        f"{summary['dense_saving_pct']:.2f}% |",
        "",
        "## Fold Selections",
        "",
        "| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for row in selections:
        lines.append(
            f"| {row['fold']} | `{row['intentroute_policy']}` | {row['intentroute_eligible']} | "
            f"{row['intentroute_test_hit_delta_mean_pp']:+.2f} pp | "
            f"{row['intentroute_test_saving_mean_pct']:.2f}% | `{row['dense_policy']}` |"
        )
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=DATA / "processed")
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=690300)
    args = parser.parse_args()
    if not args.source_dir.is_absolute():
        args.source_dir = (ROOT / args.source_dir).resolve()
    if not args.data_dir.is_absolute():
        args.data_dir = (ROOT / args.data_dir).resolve()
    if not args.output_prefix.is_absolute():
        args.output_prefix = (ROOT / args.output_prefix).resolve()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(DATA / "tiktoken_cache"))
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)

    folds, selections, comparisons, summary, method_oof, dense_oof, assignments, artifacts = run(args)
    write_csv(args.output_prefix.with_suffix(".folds.csv"), folds)
    write_csv(args.output_prefix.with_suffix(".paired.csv"), comparisons)
    args.output_prefix.with_suffix(".rankings.json").write_text(
        json.dumps(
            {
                "intentroute_crossfit": method_oof,
                "dense_crossfit": dense_oof,
                "fold_assignments": assignments,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    args.output_prefix.with_suffix(".json").write_text(
        json.dumps(
            {
                "protocol": {
                    "fold_salt": FOLD_SALT,
                    "num_folds": NUM_FOLDS,
                    "ratios": RATIOS,
                    "min_keeps": MIN_KEEPS,
                    "selection_margin": SELECTION_MARGIN,
                    "noninferiority_margin": NI_MARGIN,
                    "bootstrap_samples": BOOTSTRAP_SAMPLES,
                    "fallback": "dense_top10_when_no_policy_is_eligible",
                },
                "input_artifacts": artifacts,
                "summary": summary,
                "fold_selections": selections,
                "paired": comparisons,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(args.output_prefix.with_suffix(".md"), summary, selections)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
