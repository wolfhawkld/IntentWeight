#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize seed-level stability for matched-backbone experiments.

Task55 intentionally reuses existing Task38/Task53/Task54 artifacts. It does
not rerun retrieval, embedding, LinUCB routing, or context-budget calibration.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS = ROOT / "paper" / "experiments" / "results"
FROZEN_TEST_QUERIES = 417

T_CRIT_95_BY_DF = {
    1: 12.706204736432095,
    2: 4.302652729911275,
    3: 3.182446305284263,
    4: 2.7764451051977987,
    5: 2.570581835636314,
    6: 2.4469118511449692,
    7: 2.3646242510102993,
    8: 2.306004135204166,
    9: 2.2621571627409915,
}

COMPARISONS = (
    {
        "setting": "MiniLM gated",
        "backbone": "MiniLM",
        "route_mode": "gated_cost_aware",
        "role": "matched_backbone",
        "source": RESULTS / "task38_100k_calibrated_context_budget.json",
    },
    {
        "setting": "BGE full",
        "backbone": "BGE-base",
        "route_mode": "full_multi_route",
        "role": "matched_backbone",
        "source": RESULTS / "task53_bge_base_100k_full_context_budget.json",
    },
    {
        "setting": "BGE gated",
        "backbone": "BGE-base",
        "route_mode": "gated_cost_aware",
        "role": "cost_aggressive_boundary",
        "source": RESULTS / "task53_bge_base_100k_matched_context_budget.json",
    },
    {
        "setting": "E5 full",
        "backbone": "E5-base",
        "route_mode": "full_multi_route",
        "role": "matched_backbone",
        "source": RESULTS / "task53_e5_base_100k_full_context_budget.json",
    },
    {
        "setting": "E5 gated",
        "backbone": "E5-base",
        "route_mode": "gated_cost_aware",
        "role": "cost_aggressive_boundary",
        "source": RESULTS / "task53_e5_base_100k_gated_context_budget.json",
    },
    {
        "setting": "BGE positive",
        "backbone": "BGE-base",
        "route_mode": "full_multi_route",
        "role": "quality_first_tuning",
        "source": RESULTS / "task54_bge_base_100k_positive_hit_context_budget.json",
    },
)


def load_json(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError(f"Expected object JSON: {path}")
    return data


def mean_or_zero(values: Sequence[float]) -> float:
    return float(mean(values)) if values else 0.0


def sd_or_zero(values: Sequence[float]) -> float:
    return float(stdev(values)) if len(values) > 1 else 0.0


def seed_ci(values: Sequence[float], confidence: float = 0.95) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) < 2:
        value = float(values[0])
        return value, value
    if confidence != 0.95:
        raise ValueError("Only 95% seed-level CI is supported")
    df = len(values) - 1
    t_crit = T_CRIT_95_BY_DF.get(df, 1.96)
    center = mean_or_zero(values)
    half_width = t_crit * sd_or_zero(values) / math.sqrt(len(values))
    return center - half_width, center + half_width


def fmt_pp(value: float) -> str:
    return f"{value:+.2f} pp"


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def fmt_float(value: float) -> str:
    return f"{value:.4f}"


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    aggregate_rows: list[dict[str, object]] = []
    per_seed_rows: list[dict[str, object]] = []
    for spec in COMPARISONS:
        source = Path(spec["source"])
        payload = load_json(source)
        selected_policy = str(payload.get("selected_policy", {}).get("policy", ""))
        paired_rows = [
            row
            for row in payload.get("test_paired_rows", [])
            if isinstance(row, Mapping) and row.get("method_label") == "task38"
        ]
        if not paired_rows:
            raise ValueError(f"No task38 paired rows in {source}")

        for row in paired_rows:
            hit_delta_pp = float(row.get("hit_delta_mean", 0.0)) * 100.0
            per_seed_rows.append(
                {
                    "setting": spec["setting"],
                    "backbone": spec["backbone"],
                    "route_mode": spec["route_mode"],
                    "role": spec["role"],
                    "source": str(source.relative_to(ROOT)),
                    "selected_policy": selected_policy,
                    "num_queries": FROZEN_TEST_QUERIES,
                    "seed": str(row.get("seed", "")),
                    "baseline_hit@10": float(row.get("baseline_hit@10", 0.0)),
                    "method_hit@10": float(row.get("method_hit@10", 0.0)),
                    "hit_delta_pp": hit_delta_pp,
                    "paired_hit_delta_ci_low_pp": float(row.get("hit_delta_ci_low", 0.0)) * 100.0,
                    "paired_hit_delta_ci_high_pp": float(row.get("hit_delta_ci_high", 0.0)) * 100.0,
                    "noninferior_by_ci": bool(row.get("noninferior_by_ci", False)),
                    "token_saving_percent": float(row.get("token_saving_percent", 0.0)),
                    "token_ratio": float(row.get("token_ratio", 0.0)),
                    "mcnemar_p_two_sided": float(row.get("mcnemar_p_two_sided", 1.0)),
                    "token_down_nonworse_rate": float(row.get("token_down_nonworse_rate", 0.0)),
                }
            )

        group = per_seed_rows[-len(paired_rows):]
        hit_delta_pp = [float(row["hit_delta_pp"]) for row in group]
        token_savings = [float(row["token_saving_percent"]) for row in group]
        ci_low, ci_high = seed_ci(hit_delta_pp)
        aggregate_rows.append(
            {
                "setting": spec["setting"],
                "backbone": spec["backbone"],
                "route_mode": spec["route_mode"],
                "role": spec["role"],
                "source": str(source.relative_to(ROOT)),
                "selected_policy": selected_policy,
                "num_queries": FROZEN_TEST_QUERIES,
                "num_seeds": len(group),
                "seeds": ",".join(str(row["seed"]) for row in group),
                "baseline_hit@10": mean_or_zero([float(row["baseline_hit@10"]) for row in group]),
                "method_hit@10": mean_or_zero([float(row["method_hit@10"]) for row in group]),
                "baseline_hit@10_mean": mean_or_zero([float(row["baseline_hit@10"]) for row in group]),
                "method_hit@10_mean": mean_or_zero([float(row["method_hit@10"]) for row in group]),
                "hit_delta_pp_mean": mean_or_zero(hit_delta_pp),
                "hit_delta_pp_sd": sd_or_zero(hit_delta_pp),
                "hit_delta_pp_seed_ci_low": ci_low,
                "hit_delta_pp_seed_ci_high": ci_high,
                "token_saving_percent_mean": mean_or_zero(token_savings),
                "token_saving_percent_sd": sd_or_zero(token_savings),
                "noninferior_seed_count": sum(1 for row in group if row["noninferior_by_ci"]),
                "paired_hit_delta_ci_low_min_pp": min(float(row["paired_hit_delta_ci_low_pp"]) for row in group),
                "paired_hit_delta_ci_high_max_pp": max(float(row["paired_hit_delta_ci_high_pp"]) for row in group),
                "mcnemar_p_min": min(float(row["mcnemar_p_two_sided"]) for row in group),
                "mcnemar_p_max": max(float(row["mcnemar_p_two_sided"]) for row in group),
            }
        )
    return aggregate_rows, per_seed_rows


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, aggregate_rows: Sequence[Mapping[str, object]], per_seed_rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task55 Backbone Stability Summary",
        "",
        "Task55 is a no-rerun stability summary over existing Task38, Task53, and Task54 artifacts.",
        "It uses the common seeds `13,17,19` and treats paired query-level bootstrap/McNemar",
        "statistics as the primary evidence, with seed-level variance as a stability check.",
        "",
        "The purpose is not to search for a favorable seed. Seeds are fixed replicate",
        "conditions used to test whether the route-and-budget claims remain stable and",
        "statistically checkable under random clustering/order/feedback variation.",
        "",
        "## Aggregate Stability",
        "",
        "| setting | policy | seeds | baseline Hit@10 | method Hit@10 | hit delta mean | hit delta SD | seed 95% CI | token saving mean | token saving SD | NI seeds |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in aggregate_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["setting"]),
                    f"`{row['selected_policy']}`",
                    str(row["seeds"]),
                    fmt_float(float(row["baseline_hit@10_mean"])),
                    fmt_float(float(row["method_hit@10_mean"])),
                    fmt_pp(float(row["hit_delta_pp_mean"])),
                    fmt_pp(float(row["hit_delta_pp_sd"])),
                    f"[{fmt_pp(float(row['hit_delta_pp_seed_ci_low']))}, {fmt_pp(float(row['hit_delta_pp_seed_ci_high']))}]",
                    fmt_pct(float(row["token_saving_percent_mean"])),
                    fmt_pct(float(row["token_saving_percent_sd"])),
                    f"{row['noninferior_seed_count']}/{row['num_seeds']}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Per-Seed Paired Evidence",
            "",
            "| setting | seed | method Hit@10 | baseline Hit@10 | hit delta | paired CI low | paired CI high | token saving | McNemar p |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in per_seed_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["setting"]),
                    str(row["seed"]),
                    fmt_float(float(row["method_hit@10"])),
                    fmt_float(float(row["baseline_hit@10"])),
                    fmt_pp(float(row["hit_delta_pp"])),
                    fmt_pp(float(row["paired_hit_delta_ci_low_pp"])),
                    fmt_pp(float(row["paired_hit_delta_ci_high_pp"])),
                    fmt_pct(float(row["token_saving_percent"])),
                    f"{float(row['mcnemar_p_two_sided']):.4g}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- BGE full multi-route is stable as a near-dense token-saving operating point: mean Hit@10 delta is about -0.08pp with 0.37pp seed SD and about 11.99% token saving.",
            "- BGE positive-hit tuning is stable as a quality-first operating point: mean Hit@10 delta is about +0.88pp with 0.14pp seed SD and about 7.23% token saving.",
            "- E5 full multi-route is stable but slightly below its dense baseline: mean Hit@10 delta is about -0.64pp with 0.14pp seed SD and about 12.20% token saving.",
            "- BGE/E5 gated-cost variants show stable negative Hit@10 deltas, so they should be presented as cost-aggressive boundary evidence rather than the main quality-preserving result.",
            "- Do not describe this as a large multi-repeat experiment or seed search. The defensible wording is fixed three-seed stability plus paired query-level statistical checks.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize backbone seed stability")
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task55_backbone_stability_summary",
    )
    args = parser.parse_args(argv)
    aggregate_rows, per_seed_rows = build_rows()
    output_prefix = args.output_prefix
    write_csv(output_prefix.with_suffix(".csv"), aggregate_rows)
    write_csv(output_prefix.with_suffix(".per_seed.csv"), per_seed_rows)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(
            {
                "aggregate_rows": aggregate_rows,
                "per_seed_rows": per_seed_rows,
                "notes": [
                    "No retrieval rerun; all rows are derived from Task38/Task53/Task54 artifacts.",
                    "Seed-level 95% CI uses a t interval over seeds.",
                    "Paired bootstrap and McNemar statistics are inherited from source artifacts.",
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(output_prefix.with_suffix(".md"), aggregate_rows, per_seed_rows)
    print(f"aggregate_rows={len(aggregate_rows)} per_seed_rows={len(per_seed_rows)}")
    print(
        "outputs="
        f"{output_prefix.with_suffix('.csv')},"
        f"{output_prefix.with_suffix('.per_seed.csv')},"
        f"{output_prefix.with_suffix('.json')},"
        f"{output_prefix.with_suffix('.md')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
