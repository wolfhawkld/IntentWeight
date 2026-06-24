#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize Task53 matched-backbone IntentWeight comparisons.

This script consumes already-generated Task38/Task53 calibration outputs. It
does not rerun retrieval or embedding. The summary is intentionally framed as a
matched-backbone trade-off table: each IntentWeight variant is compared against
the dense baseline produced by the same embedding backbone.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RESULTS = ROOT / "paper" / "experiments" / "results"


DEFAULT_COMPARISONS = (
    {
        "backbone": "MiniLM",
        "route_mode": "gated_cost_aware",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "source": RESULTS / "task38_100k_calibrated_context_budget.json",
    },
    {
        "backbone": "BGE-base",
        "route_mode": "full_multi_route",
        "embedding_model": "BAAI/bge-base-en-v1.5",
        "source": RESULTS / "task53_bge_base_100k_full_context_budget.json",
    },
    {
        "backbone": "BGE-base",
        "route_mode": "gated_cost_aware",
        "embedding_model": "BAAI/bge-base-en-v1.5",
        "source": RESULTS / "task53_bge_base_100k_matched_context_budget.json",
    },
    {
        "backbone": "E5-base",
        "route_mode": "full_multi_route",
        "embedding_model": "intfloat/e5-base-v2",
        "source": RESULTS / "task53_e5_base_100k_full_context_budget.json",
    },
    {
        "backbone": "E5-base",
        "route_mode": "gated_cost_aware",
        "embedding_model": "intfloat/e5-base-v2",
        "source": RESULTS / "task53_e5_base_100k_gated_context_budget.json",
    },
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def per_seed_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in DEFAULT_COMPARISONS:
        source = Path(spec["source"])
        payload = load_json(source)
        selected = payload["selected_policy"]
        for paired_row in payload.get("test_paired_rows", []):
            if paired_row.get("method_label") != "task38":
                continue
            rows.append(
                {
                    "backbone": spec["backbone"],
                    "embedding_model": spec["embedding_model"],
                    "route_mode": spec["route_mode"],
                    "source": str(source.relative_to(ROOT)),
                    "selected_policy": selected["policy"],
                    "calibration_eligible": bool(selected["eligible"]),
                    "calibration_hit_delta": float(selected["mean_hit_delta"]),
                    "calibration_token_saving_percent": float(selected["mean_token_saving_percent"]),
                    "seed": str(paired_row.get("seed", "")),
                    "baseline_hit@10": float(paired_row.get("baseline_hit@10", 0.0)),
                    "method_hit@10": float(paired_row.get("method_hit@10", 0.0)),
                    "hit_delta_mean": float(paired_row.get("hit_delta_mean", 0.0)),
                    "hit_delta_ci_low": float(paired_row.get("hit_delta_ci_low", 0.0)),
                    "hit_delta_ci_high": float(paired_row.get("hit_delta_ci_high", 0.0)),
                    "noninferior_by_ci": bool(paired_row.get("noninferior_by_ci", False)),
                    "token_ratio": float(paired_row.get("token_ratio", 0.0)),
                    "token_saving_percent": float(paired_row.get("token_saving_percent", 0.0)),
                    "mcnemar_p_two_sided": float(paired_row.get("mcnemar_p_two_sided", 1.0)),
                    "token_down_nonworse_rate": float(paired_row.get("token_down_nonworse_rate", 0.0)),
                }
            )
    return rows


def aggregate_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["backbone"]), str(row["route_mode"]))].append(row)

    aggregates = []
    for (backbone, route_mode), group_rows in sorted(grouped.items()):
        hit_deltas = [float(row["hit_delta_mean"]) for row in group_rows]
        token_savings = [float(row["token_saving_percent"]) for row in group_rows]
        aggregates.append(
            {
                "backbone": backbone,
                "embedding_model": group_rows[0]["embedding_model"],
                "route_mode": route_mode,
                "selected_policy": group_rows[0]["selected_policy"],
                "calibration_eligible": bool(group_rows[0]["calibration_eligible"]),
                "num_seeds": len(group_rows),
                "baseline_hit@10_mean": mean(float(row["baseline_hit@10"]) for row in group_rows),
                "method_hit@10_mean": mean(float(row["method_hit@10"]) for row in group_rows),
                "hit_delta_mean": mean(hit_deltas),
                "hit_delta_min": min(hit_deltas),
                "hit_delta_max": max(hit_deltas),
                "token_saving_percent_mean": mean(token_savings),
                "token_saving_percent_min": min(token_savings),
                "token_saving_percent_max": max(token_savings),
                "noninferior_seed_count": sum(1 for row in group_rows if row["noninferior_by_ci"]),
                "min_hit_delta_ci_low": min(float(row["hit_delta_ci_low"]) for row in group_rows),
                "max_hit_delta_ci_high": max(float(row["hit_delta_ci_high"]) for row in group_rows),
            }
        )
    return aggregates


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pct_points(value: object) -> str:
    return f"{float(value) * 100:+.2f} pp"


def pct(value: object) -> str:
    return f"{float(value):.2f}%"


def f4(value: object) -> str:
    return f"{float(value):.4f}"


def write_markdown(path: Path, *, aggregate: Sequence[Mapping[str, object]], per_seed: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Task53 Embedding Backbone Generalization",
        "",
        "## Aggregate Matched-Backbone Results",
        "",
        "| backbone | route_mode | selected_policy | calib eligible | baseline Hit@10 | method Hit@10 | mean hit delta | mean token saving | NI seeds |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in aggregate:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["backbone"]),
                    str(row["route_mode"]),
                    str(row["selected_policy"]),
                    str(row["calibration_eligible"]),
                    f4(row["baseline_hit@10_mean"]),
                    f4(row["method_hit@10_mean"]),
                    pct_points(row["hit_delta_mean"]),
                    pct(row["token_saving_percent_mean"]),
                    f"{row['noninferior_seed_count']}/{row['num_seeds']}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Per-Seed Frozen Test Results",
            "",
            "| backbone | route_mode | seed | method Hit@10 | baseline Hit@10 | hit delta | CI low | CI high | token saving | McNemar p |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in per_seed:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["backbone"]),
                    str(row["route_mode"]),
                    str(row["seed"]),
                    f4(row["method_hit@10"]),
                    f4(row["baseline_hit@10"]),
                    pct_points(row["hit_delta_mean"]),
                    pct_points(row["hit_delta_ci_low"]),
                    pct_points(row["hit_delta_ci_high"]),
                    pct(row["token_saving_percent"]),
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
            "- Matched-backbone comparison is essential: each IntentWeight row is compared against the dense baseline produced by the same embedding model.",
            "- BGE and E5 full multi-route variants preserve or nearly preserve dense Hit@10 on average while reducing final context tokens by about 12%.",
            "- The gated-cost variants save retrieval-stage dense calls, but they lower Hit@10 under BGE and E5; use them as cost-aggressive boundary points rather than the main quality-preserving result.",
            "- Strict 1pp CI non-inferiority is not established for these 100k single-scale seed rows, so paper wording should say quality-cost trade off rather than universal non-inferiority.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Task53 matched-backbone results")
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=RESULTS / "task53_embedding_backbone_generalization",
    )
    args = parser.parse_args(argv)

    per_seed = per_seed_rows()
    aggregate = aggregate_rows(per_seed)
    output_prefix = args.output_prefix
    write_csv(output_prefix.with_suffix(".per_seed.csv"), per_seed)
    write_csv(output_prefix.with_suffix(".csv"), aggregate)
    output_prefix.with_suffix(".json").write_text(
        json.dumps({"aggregate_rows": aggregate, "per_seed_rows": per_seed}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    write_markdown(output_prefix.with_suffix(".md"), aggregate=aggregate, per_seed=per_seed)
    print(f"aggregate_rows={len(aggregate)} per_seed_rows={len(per_seed)}")
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
