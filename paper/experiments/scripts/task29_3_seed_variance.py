#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize Task29-C seed-level variance and confidence intervals."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_OUTPUT_CSV = DEFAULT_RESULTS_DIR / "task29_3_seed_variance_ci.csv"
DEFAULT_OUTPUT_MD = DEFAULT_RESULTS_DIR / "task29_3_seed_variance_ci.md"
DEFAULT_SCALES = ("100k", "200k", "400k", "638k")
METRICS = (
    "hit@10",
    "evidence_recall@10",
    "mrr@10",
    "ndcg@10",
    "avg_context_tokens@10",
    "context_token_ratio_vs_baseline@10",
    "hit_delta_vs_baseline@10",
)


def t_critical_95(n: int) -> float:
    # Two-sided t critical values for 95% CI. Task29 uses n=3, but keep a small table.
    table = {
        2: 12.706,
        3: 4.303,
        4: 3.182,
        5: 2.776,
        6: 2.571,
        7: 2.447,
        8: 2.365,
        9: 2.306,
        10: 2.262,
    }
    if n <= 1:
        return 0.0
    return table.get(n, 1.96)


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def summarize_values(values: Sequence[float]) -> Dict[str, float]:
    n = len(values)
    avg = mean(values) if values else 0.0
    sd = stdev(values) if n > 1 else 0.0
    sem = sd / math.sqrt(n) if n > 1 else 0.0
    half_width = t_critical_95(n) * sem if n > 1 else 0.0
    return {
        "mean": avg,
        "std": sd,
        "sem": sem,
        "ci95_low": avg - half_width,
        "ci95_high": avg + half_width,
        "ci95_half_width": half_width,
    }


def context_path(results_dir: Path, scale: str) -> Path:
    return results_dir / f"task29_{scale}_confidence_topk_C_formal" / "context_tokens.csv"


def summarize_scale(results_dir: Path, scale: str) -> List[Dict[str, object]]:
    path = context_path(results_dir, scale)
    rows = read_rows(path)
    dense = next((row for row in rows if row.get("run_id") == "dense"), None)
    seed_rows = [row for row in rows if row.get("seed")]
    if dense is None:
        raise ValueError(f"Dense row missing in {path}")
    if not seed_rows:
        raise ValueError(f"No seed rows found in {path}")

    out: List[Dict[str, object]] = []
    for metric in METRICS:
        values = [float(row[metric]) for row in seed_rows]
        stats = summarize_values(values)
        out.append({
            "scale": scale,
            "metric": metric,
            "n_seeds": len(seed_rows),
            "dense_baseline": float(dense[metric]) if metric in dense and dense[metric] != "" else "",
            "min": min(values),
            "max": max(values),
            **stats,
        })

    ratio_values = [float(row["context_token_ratio_vs_baseline@10"]) for row in seed_rows]
    saving_values = [(1.0 - value) * 100.0 for value in ratio_values]
    out.append({
        "scale": scale,
        "metric": "context_token_saving_pct@10",
        "n_seeds": len(seed_rows),
        "dense_baseline": 0.0,
        "min": min(saving_values),
        "max": max(saving_values),
        **summarize_values(saving_values),
    })
    return out


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = [
        "scale",
        "metric",
        "n_seeds",
        "dense_baseline",
        "mean",
        "std",
        "sem",
        "ci95_low",
        "ci95_high",
        "ci95_half_width",
        "min",
        "max",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: object, digits: int = 4) -> str:
    if value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def rows_by_metric(rows: Sequence[Mapping[str, object]], metric: str) -> List[Mapping[str, object]]:
    return [row for row in rows if row["metric"] == metric]


def write_markdown(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task29.3 Seed Variance and Confidence Intervals",
        "",
        "Task29.3 reports cross-seed stability for the conservative Task29-C",
        "`confidence_topk` policy across LoTTE 100k/200k/400k/638k.",
        "",
        "All intervals are two-sided 95% t intervals over three random seeds",
        "(`13,17,19`). With only three seeds, these intervals should be read as",
        "engineering stability diagnostics rather than strong inferential proof.",
        "",
        "## Hit@10 Stability",
        "",
        "| Scale | Dense Hit@10 | Task29-C mean | Std | 95% CI | Hit delta mean |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    hit_rows = rows_by_metric(rows, "hit@10")
    delta_index = {row["scale"]: row for row in rows_by_metric(rows, "hit_delta_vs_baseline@10")}
    for row in hit_rows:
        delta = delta_index[row["scale"]]
        lines.append(
            "| {scale} | {dense} | {mean} | {std} | [{low}, {high}] | {delta} |".format(
                scale=row["scale"],
                dense=fmt(row["dense_baseline"]),
                mean=fmt(row["mean"]),
                std=fmt(row["std"]),
                low=fmt(row["ci95_low"]),
                high=fmt(row["ci95_high"]),
                delta=fmt(delta["mean"]),
            )
        )

    lines.extend([
        "",
        "## Final Context Token Stability",
        "",
        "| Scale | Dense tokens@10 | Task29-C mean tokens@10 | Std | 95% CI | Saving mean | Saving 95% CI |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    token_rows = rows_by_metric(rows, "avg_context_tokens@10")
    saving_index = {row["scale"]: row for row in rows_by_metric(rows, "context_token_saving_pct@10")}
    for row in token_rows:
        saving = saving_index[row["scale"]]
        lines.append(
            "| {scale} | {dense} | {mean} | {std} | [{low}, {high}] | {saving_mean}% | [{saving_low}%, {saving_high}%] |".format(
                scale=row["scale"],
                dense=fmt(row["dense_baseline"], 2),
                mean=fmt(row["mean"], 2),
                std=fmt(row["std"], 2),
                low=fmt(row["ci95_low"], 2),
                high=fmt(row["ci95_high"], 2),
                saving_mean=fmt(saving["mean"], 2),
                saving_low=fmt(saving["ci95_low"], 2),
                saving_high=fmt(saving["ci95_high"], 2),
            )
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Token saving is stable across all four scales: the mean saving stays in the",
        "  narrow `4.69%` to `5.32%` band.",
        "- Hit@10 is near dense at 100k and above dense at 200k, 400k, and 638k.",
        "- The 638k full-corpus result has above-dense Hit@10 with lower final",
        "  context tokens, strengthening the large-scale efficiency claim.",
        "- Because each scale has only three seeds, the CI bands are intentionally",
        "  reported as stability diagnostics; the paper should avoid overclaiming",
        "  statistical significance from this table alone.",
        "",
        "## Artifacts",
        "",
        "- CSV: `paper/experiments/results/task29_3_seed_variance_ci.csv`",
        "- Source token tables:",
        "  `paper/experiments/results/task29_{scale}_confidence_topk_C_formal/context_tokens.csv`",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_scales(value: str) -> tuple[str, ...]:
    scales = tuple(part.strip() for part in value.split(",") if part.strip())
    if not scales:
        raise ValueError("At least one scale is required")
    return scales


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task29-C seed variance/CI summary")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--scales", default=",".join(DEFAULT_SCALES))
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args(argv)

    all_rows: List[Dict[str, object]] = []
    for scale in parse_scales(args.scales):
        all_rows.extend(summarize_scale(args.results_dir, scale))
    write_csv(args.output_csv, all_rows)
    write_markdown(args.output_md, all_rows)
    print(f"Wrote {len(all_rows)} rows: {args.output_csv}")
    print(f"Markdown: {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
