#!/usr/bin/env python3
"""Audit Task69 cross-dataset protocol coverage and current result scope."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROTOCOL = ROOT / "paper" / "experiments" / "task69_common_protocol.json"
DEFAULT_OUTPUT = ROOT / "paper" / "experiments" / "results" / "task69_cross_dataset_consistency"
RESULTS = ROOT / "paper" / "experiments" / "results"

COVERAGE_FIELDS = (
    "bm25",
    "dense",
    "hybrid_rrf",
    "intentroute_top10",
    "geometry",
    "cross_fitted_budget",
    "final_context_tokens",
    "paired_statistics",
    "feedback_control",
    "feedback_recovery",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fmt(value: Any, digits: int = 4) -> str:
    if value in (None, ""):
        return "--"
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return value
    return f"{float(value):.{digits}f}"


def bool_mark(value: Any) -> str:
    return "yes" if bool(value) else "no"


def markdown_table(rows: list[dict[str, Any]], fields: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in fields) + " |"
    divider = "|" + "|".join("---" for _ in fields) + "|"
    body = []
    for row in rows:
        cells = [str(row.get(key, "--")).replace("|", "\\|") for key, _ in fields]
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, divider, *body])


def dataset_inventory(datasets: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in datasets:
        rows.append(
            {
                "dataset": item["display_name"],
                "scale": item["scale"],
                "task_type": item["task_type"],
                "protocol_group": item["protocol_group"],
                "corpus_chunks": item.get("corpus_chunks") or "pending",
                "total_queries": item.get("total_queries") or "pending",
                "eval_queries": item.get("current_eval_queries") or "pending",
                "gt_semantics": item["gt_semantics"],
                "sampling": item["sampling"],
                "paper_role": item["paper_role"],
                "status": item["status"],
            }
        )
    return rows


def coverage_matrix(datasets: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in datasets:
        coverage = item.get("current_coverage", {})
        complete = sum(bool(coverage.get(field)) for field in COVERAGE_FIELDS)
        row = {
            "dataset": item["display_name"],
            "protocol_group": item["protocol_group"],
            **{field: bool_mark(coverage.get(field, False)) for field in COVERAGE_FIELDS},
            "coverage": f"{complete}/{len(COVERAGE_FIELDS)}",
            "status": item["status"],
        }
        rows.append(row)
    return rows


def select_feedback_row(path: Path, mode: str = "trust_weighted") -> Mapping[str, Any]:
    rows = load_json(path)
    return next(row for row in rows if row.get("feedback_mode") == mode)


def paired_snapshot(
    *,
    dataset: str,
    scale: str,
    path: Path,
    role: str,
    source: str,
    method_label: str = "task38",
    scale_filter: str | None = None,
    protocol: str = "fixed 30/70 calibration-test",
    artifact_status: str | None = None,
) -> dict[str, Any]:
    rows = [row for row in read_csv(path) if row["method_label"] == method_label]
    if scale_filter is not None:
        rows = [row for row in rows if row["scale"] == scale_filter]
    if not rows:
        raise ValueError(f"no {method_label} rows in {path}")
    baseline_hit = float(rows[0]["baseline_hit@10"])
    method_hits = [float(row["method_hit@10"]) for row in rows]
    savings = [float(row["token_saving_percent"]) for row in rows]
    evidence_deltas = [float(row["evidence_recall_delta_mean"]) for row in rows]
    ni = sum(row["noninferior_by_ci"].lower() == "true" for row in rows)
    return {
        "dataset": dataset,
        "scale": scale,
        "role": role,
        "protocol": protocol,
        "dense_hit@10": fmt(baseline_hit),
        "intentroute_hit@10": fmt(mean(method_hits)),
        "hit_delta_pp": fmt((mean(method_hits) - baseline_hit) * 100, 2),
        "evidence_recall_delta_pp": fmt(mean(evidence_deltas) * 100, 2),
        "context_saving_percent": fmt(mean(savings), 2),
        "strict_ni_seeds": f"{ni}/{len(rows)}",
        "feedback_route_metric": "--",
        "artifact_status": artifact_status
        or (
            "reusable complete anchor"
            if dataset == "LoTTE technology/search"
            else "partial; missing common endpoints"
        ),
        "source": source,
    }


def feedback_snapshot(
    *,
    dataset: str,
    scale: str,
    dense_path: Path,
    route_path: Path,
    role: str,
) -> dict[str, Any]:
    dense = load_json(dense_path)
    route = select_feedback_row(route_path)
    dense_hit = float(dense["recall@10"])
    route_hit = float(route["recall@10_mean"])
    return {
        "dataset": dataset,
        "scale": scale,
        "role": role,
        "protocol": route.get("comparable_group", "historical matched scope"),
        "dense_hit@10": fmt(dense_hit),
        "intentroute_hit@10": fmt(route_hit),
        "hit_delta_pp": fmt((route_hit - dense_hit) * 100, 2),
        "evidence_recall_delta_pp": "--",
        "context_saving_percent": "--",
        "strict_ni_seeds": "--",
        "feedback_route_metric": fmt(route.get("last_epoch_selected_cluster_hit_rate_mean")),
        "artifact_status": "mechanism/boundary only",
        "source": str(route_path.relative_to(ROOT)),
    }


def current_result_snapshot() -> list[dict[str, Any]]:
    rows = []
    tech_path = RESULTS / "task65_6_cross_scale_cross_fitted_calibration.paired.csv"
    for scale in ("100k", "200k", "400k", "638k"):
        display_scale = "638k full" if scale == "638k" else scale
        rows.append(
            paired_snapshot(
                dataset="LoTTE technology/search",
                scale=display_scale,
                path=tech_path,
                role="scale/full-stack",
                source="paper/experiments/results/task65_6_cross_scale_cross_fitted_calibration.paired.csv",
                method_label="intentroute_crossfit",
                scale_filter=scale,
                protocol="five-fold cross-fitted calibration",
            )
        )

    rows.append(
        paired_snapshot(
            dataset="LoTTE science/search",
            scale="20k/q200",
            path=RESULTS / "task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv",
            role="cross-domain diagnostic",
            source="paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv",
            artifact_status="legacy fixed-split diagnostic",
        )
    )
    rows.append(
        paired_snapshot(
            dataset="LoTTE science/search",
            scale="100k",
            path=RESULTS / "task69_3_science_100k_cross_fitted_calibration.paired.csv",
            role="cross-domain",
            source="paper/experiments/results/task69_3_science_100k_cross_fitted_calibration.paired.csv",
            method_label="intentroute_crossfit",
            scale_filter="lotte_science_search_100k",
            protocol="five-fold cross-fitted calibration",
            artifact_status="reusable complete cross-domain row",
        )
    )

    rows.append(
        feedback_snapshot(
            dataset="PubMedQA",
            scale="native full",
            dense_path=RESULTS / "dense_pubmedqa_metrics.json",
            route_path=RESULTS / "linucb_trust_pubmedqa_prequential_metrics.json",
            role="mechanism transfer",
        )
    )
    rows.append(
        feedback_snapshot(
            dataset="Banking77",
            scale="native full",
            dense_path=RESULTS / "dense_banking77_metrics.json",
            route_path=RESULTS / "linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json",
            role="intent-routing mechanism",
        )
    )
    rows.append(
        feedback_snapshot(
            dataset="CUAD GT-anchored",
            scale="10k sample",
            dense_path=RESULTS / "dense_cuad_metrics.json",
            route_path=RESULTS / "linucb_trust_cuad_prequential_metrics.json",
            role="sparse-GT boundary",
        )
    )

    emanual_rows = read_csv(RESULTS / "emanual_failure_analysis_tables.csv")
    dense = next(
        row
        for row in emanual_rows
        if row["method"] == "dedup_dense" and row["evaluation_mode"] == "deduplicated_text_corpus"
    )
    rows.append(
        {
            "dataset": "eManual deduplicated",
            "scale": "native full",
            "role": "corrected boundary",
            "protocol": "deduplicated text-equivalent evaluation",
            "dense_hit@10": fmt(dense["recall@10"]),
            "intentroute_hit@10": "--",
            "hit_delta_pp": "--",
            "evidence_recall_delta_pp": "--",
            "context_saving_percent": "--",
            "strict_ni_seeds": "--",
            "feedback_route_metric": "--",
            "artifact_status": "partial; corrected Dense only",
            "source": "paper/experiments/results/emanual_failure_analysis_tables.csv",
        }
    )
    return rows


def missing_batches(datasets: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    batches = []
    for item in datasets:
        if item["protocol_group"] != "common_evidence":
            continue
        coverage = item.get("current_coverage", {})
        missing = [field for field in COVERAGE_FIELDS if not coverage.get(field, False)]
        if not missing:
            continue
        batches.append(
            {
                "dataset": item["display_name"],
                "scale": item["scale"],
                "missing": ", ".join(missing),
                "priority": "P0"
                if item["id"] in {"lotte_technology_search_100k", "lotte_science_search_100k"}
                else "P1",
                "action": "run common protocol" if item["status"] == "planned" else "complete missing common-protocol stages",
            }
        )
    return batches


def build_markdown(
    protocol: Mapping[str, Any],
    inventory: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    snapshot: list[dict[str, Any]],
    missing: list[dict[str, str]],
) -> str:
    common = protocol["common_evidence_protocol"]
    lines = [
        "# Task69 Cross-Dataset Consistency Audit",
        "",
        "Generated from `task69_common_protocol.json` and traceable result artifacts.",
        "",
        "## Frozen Common Protocol",
        "",
        f"- primary task: `{common['task_type']}`;",
        f"- top-k: `{common['top_k']}`; encoder: `{common['backbone']}`;",
        f"- route seeds: `{common['route_seeds']}`; clusters: `{common['n_clusters']}`;",
        f"- route evaluation: `{common['route_evaluation']}`;",
        f"- adaptation endpoint: `{common['adaptation_epochs']}` epochs with the non-IID boundary disclosed;",
        f"- context budget: `{common['budget_protocol']}` with `{common['budget_selection']}`;",
        "- Banking77 and CUAD are not pooled into the common evidence-retrieval conclusion.",
        "",
        "## Dataset And Protocol Inventory",
        "",
        markdown_table(
            inventory,
            [
                ("dataset", "Dataset"),
                ("scale", "Scale"),
                ("task_type", "Task"),
                ("corpus_chunks", "Corpus"),
                ("total_queries", "Queries"),
                ("eval_queries", "Current eval"),
                ("gt_semantics", "GT semantics"),
                ("paper_role", "Role"),
                ("status", "Status"),
            ],
        ),
        "",
        "## Evidence Coverage Matrix",
        "",
        markdown_table(
            coverage,
            [
                ("dataset", "Dataset"),
                ("bm25", "BM25"),
                ("dense", "Dense"),
                ("hybrid_rrf", "Hybrid"),
                ("intentroute_top10", "Route"),
                ("geometry", "Geometry"),
                ("cross_fitted_budget", "OOF budget"),
                ("final_context_tokens", "Tokens"),
                ("paired_statistics", "Paired"),
                ("feedback_control", "Feedback"),
                ("feedback_recovery", "Recovery"),
                ("coverage", "Coverage"),
            ],
        ),
        "",
        "## Current Result Snapshot",
        "",
        "Rows below are intentionally not pooled. `--` means the current artifact does not contain that common-protocol endpoint.",
        "",
        markdown_table(
            snapshot,
            [
                ("dataset", "Dataset"),
                ("scale", "Scale"),
                ("dense_hit@10", "Dense Hit@10"),
                ("intentroute_hit@10", "Route Hit@10"),
                ("hit_delta_pp", "Delta pp"),
                ("context_saving_percent", "Token saving"),
                ("strict_ni_seeds", "NI seeds"),
                ("feedback_route_metric", "Feedback route metric"),
                ("artifact_status", "Artifact status"),
            ],
        ),
        "",
        "## Missing Experiment Batches",
        "",
        markdown_table(
            missing,
            [
                ("priority", "Priority"),
                ("dataset", "Dataset"),
                ("scale", "Scale"),
                ("missing", "Missing endpoints"),
                ("action", "Action"),
            ],
        ),
        "",
        "## Interpretation Guardrail",
        "",
        "LoTTE technology/search and science/search 100k now provide complete reusable rows under the common endpoint set. Technology reuses verified Task38/65 artifacts; science uses the Task69.3 standalone baselines, matched feedback control, and five-fold cross-fitted budget result. PubMedQA and corrected eManual can join the common table only after their missing token-budget and paired endpoints are run. Banking77 remains an intent-routing mechanism test, and CUAD remains a sparse-GT boundary case.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    protocol = load_json(args.protocol)
    datasets = protocol["datasets"]
    inventory = dataset_inventory(datasets)
    coverage = coverage_matrix(datasets)
    snapshot = current_result_snapshot()
    missing = missing_batches(datasets)

    output = args.output_prefix
    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output.with_suffix(".inventory.csv"), inventory)
    write_csv(output.with_suffix(".coverage.csv"), coverage)
    write_csv(output.with_suffix(".results.csv"), snapshot)
    write_csv(output.with_suffix(".missing.csv"), missing)
    write_json(
        output.with_suffix(".json"),
        {
            "protocol_version": protocol["version"],
            "dataset_count": len(datasets),
            "common_evidence_count": sum(item["protocol_group"] == "common_evidence" for item in datasets),
            "complete_common_evidence_count": sum(
                item["status"] == "complete_reusable_anchor" for item in datasets
            ),
            "inventory": inventory,
            "coverage": coverage,
            "current_results": snapshot,
            "missing_batches": missing,
        },
    )
    output.with_suffix(".md").write_text(
        build_markdown(protocol, inventory, coverage, snapshot, missing),
        encoding="utf-8",
    )
    print(f"datasets={len(datasets)}")
    print(f"common_evidence={sum(item['protocol_group'] == 'common_evidence' for item in datasets)}")
    print(f"missing_batches={len(missing)}")
    print(output.with_suffix('.md').relative_to(ROOT))


if __name__ == "__main__":
    main()
