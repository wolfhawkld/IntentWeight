#!/usr/bin/env python3
"""Summarize Task69 CPU-only mechanism and boundary evidence rows."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"
OUTPUT = RESULTS / "task69_8_mechanism_boundary_summary"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
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
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def f4(value: Any) -> str:
    if value in (None, ""):
        return "--"
    return f"{float(value):.4f}"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f}"


def trust_row(path: Path, mode: str = "trust_weighted") -> dict[str, Any]:
    rows = load_json(path)
    return next(row for row in rows if row.get("feedback_mode") == mode)


def no_feedback_row(path: Path) -> dict[str, Any]:
    rows = load_json(path)
    return next(row for row in rows if row.get("feedback_mode") == "none")


def baseline_rows(dataset: str, bm25: Path, dense: Path, hybrid: Path) -> list[dict[str, Any]]:
    records = []
    for method, path in (("BM25", bm25), ("Dense", dense), ("Hybrid RRF", hybrid)):
        payload = load_json(path)
        records.append(
            {
                "dataset": dataset,
                "method": method,
                "hit@10": payload.get("recall@10"),
                "mrr@10": payload.get("mrr@10"),
                "ndcg@10": payload.get("ndcg@10"),
                "scope": payload.get("comparable_group", ""),
                "source": str(path.relative_to(ROOT)),
            }
        )
    return records


def dataset_summary(
    *,
    dataset: str,
    role: str,
    dense_path: Path,
    bm25_path: Path,
    hybrid_path: Path,
    trust_path: Path,
    geometry_path: Path,
    caveat: str,
) -> dict[str, Any]:
    dense = load_json(dense_path)
    trust = trust_row(trust_path)
    no_feedback = no_feedback_row(trust_path)
    geometry = load_json(geometry_path)
    dense_hit = float(dense["recall@10"])
    trust_hit = float(trust["recall@10_mean"])
    no_feedback_hit = float(no_feedback["recall@10_mean"])
    selected_gain = (
        float(trust.get("last_epoch_selected_cluster_hit_rate_mean", 0.0))
        - float(no_feedback.get("last_epoch_selected_cluster_hit_rate_mean", 0.0))
    )
    reward_gain = (
        float(trust.get("last_epoch_true_reward_mean", 0.0))
        - float(no_feedback.get("last_epoch_true_reward_mean", 0.0))
    )
    return {
        "dataset": dataset,
        "role": role,
        "queries": int(dense.get("num_queries", 0)),
        "corpus_chunks": int(dense.get("num_corpus_chunks", 0)),
        "dense_hit@10": dense_hit,
        "trust_weighted_hit@10": trust_hit,
        "hit_delta_pp_vs_dense": 100.0 * (trust_hit - dense_hit),
        "no_feedback_hit@10": no_feedback_hit,
        "hit_delta_pp_vs_no_feedback": 100.0 * (trust_hit - no_feedback_hit),
        "selected_cluster_hit_last": trust.get("last_epoch_selected_cluster_hit_rate_mean"),
        "selected_cluster_hit_gain_vs_no_feedback": selected_gain,
        "last_true_reward": trust.get("last_epoch_true_reward_mean"),
        "last_true_reward_gain_vs_no_feedback": reward_gain,
        "nearest_cluster_hit@3": geometry.get("nearest_cluster_hit@3"),
        "cluster_label_purity": geometry.get("cluster_label_purity"),
        "pca_var@64": geometry.get("pca_var@64"),
        "scope": dense.get("comparable_group", ""),
        "pooling_decision": "not pooled with common evidence retrieval",
        "caveat": caveat,
        "source_dense": str(dense_path.relative_to(ROOT)),
        "source_trust": str(trust_path.relative_to(ROOT)),
        "source_geometry": str(geometry_path.relative_to(ROOT)),
    }


def markdown_table(rows: list[dict[str, Any]], fields: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in fields) + " |"
    divider = "|" + "|".join("---" for _ in fields) + "|"
    body = []
    for row in rows:
        cells = []
        for key, _ in fields:
            value = row.get(key, "--")
            if isinstance(value, float):
                value = f"{value:.4f}"
            cells.append(str(value).replace("|", "\\|"))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, divider, *body])


def build_markdown(summary: list[dict[str, Any]], baselines: list[dict[str, Any]]) -> str:
    display = []
    for row in summary:
        display.append(
            {
                "dataset": row["dataset"],
                "role": row["role"],
                "dense_hit": f4(row["dense_hit@10"]),
                "trust_hit": f4(row["trust_weighted_hit@10"]),
                "hit_delta": f"{row['hit_delta_pp_vs_dense']:+.2f}",
                "no_feedback_hit": f4(row["no_feedback_hit@10"]),
                "no_feedback_delta": f"{row['hit_delta_pp_vs_no_feedback']:+.2f}",
                "selected_cluster": f4(row["selected_cluster_hit_last"]),
                "selected_gain": f"{100.0 * row['selected_cluster_hit_gain_vs_no_feedback']:+.2f}",
                "reward": f4(row["last_true_reward"]),
                "reward_gain": f"{row['last_true_reward_gain_vs_no_feedback']:+.4f}",
                "nearest_cluster": f4(row["nearest_cluster_hit@3"]),
                "caveat": row["caveat"],
            }
        )
    baseline_display = [
        {
            "dataset": row["dataset"],
            "method": row["method"],
            "hit": f4(row["hit@10"]),
            "mrr": f4(row["mrr@10"]),
            "ndcg": f4(row["ndcg@10"]),
        }
        for row in baselines
    ]
    lines = [
        "# Task69.8 Mechanism And Boundary Summary",
        "",
        "This CPU-only summary reads existing artifacts for rows that are useful",
        "mechanism or boundary evidence, but are not pooled with the common",
        "evidence-retrieval matrix.",
        "",
        "## Main Summary",
        "",
        markdown_table(
            display,
            [
                ("dataset", "Dataset"),
                ("role", "Role"),
                ("dense_hit", "Dense Hit@10"),
                ("trust_hit", "Trust Hit@10"),
                ("hit_delta", "Delta pp"),
                ("no_feedback_hit", "No-feedback Hit@10"),
                ("no_feedback_delta", "Delta vs no-feedback pp"),
                ("selected_cluster", "Last cluster hit"),
                ("selected_gain", "Cluster gain pp"),
                ("reward", "Last true reward"),
                ("reward_gain", "Reward gain"),
                ("nearest_cluster", "NearestClusterHit@3"),
                ("caveat", "Caveat"),
            ],
        ),
        "",
        "## Static Baselines",
        "",
        markdown_table(
            baseline_display,
            [
                ("dataset", "Dataset"),
                ("method", "Method"),
                ("hit", "Hit@10"),
                ("mrr", "MRR@10"),
                ("ndcg", "nDCG@10"),
            ],
        ),
        "",
        "## Interpretation",
        "",
        "- These rows are intentionally not averaged: Banking77 and CUAD have incompatible tasks, label semantics, and evaluation scopes.",
        "- Banking77 supports route-learning and feedback behavior under an intent-routing proxy. The trust-weighted route has much higher last-epoch cluster hit and true reward than no-feedback, but fused Hit@10 is near ceiling and does not dominate no-feedback or hybrid retrieval.",
        "- CUAD remains a sparse-GT, GT-anchored boundary sample. Its low absolute scores and small evaluated-query count prevent pooling with LoTTE/PubMedQA/CovidQA/eManual.",
        "- The relevant paper-facing claim is mechanism and boundary support, not universal quality-efficiency replication.",
        "",
        "## Traceability",
        "",
    ]
    for row in summary:
        lines.extend(
            [
                f"- {row['dataset']} dense: `{row['source_dense']}`",
                f"- {row['dataset']} trust/feedback: `{row['source_trust']}`",
                f"- {row['dataset']} geometry: `{row['source_geometry']}`",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    baselines = []
    baselines.extend(
        baseline_rows(
            "Banking77",
            RESULTS / "bm25_banking77_metrics.json",
            RESULTS / "dense_banking77_metrics.json",
            RESULTS / "hybrid_banking77_metrics.json",
        )
    )
    baselines.extend(
        baseline_rows(
            "CUAD GT-anchored",
            RESULTS / "bm25_cuad_metrics.json",
            RESULTS / "dense_cuad_metrics.json",
            RESULTS / "hybrid_cuad_metrics.json",
        )
    )
    summary = [
        dataset_summary(
            dataset="Banking77",
            role="intent-routing mechanism",
            bm25_path=RESULTS / "bm25_banking77_metrics.json",
            dense_path=RESULTS / "dense_banking77_metrics.json",
            hybrid_path=RESULTS / "hybrid_banking77_metrics.json",
            trust_path=RESULTS / "linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json",
            geometry_path=RESULTS / "manifold_diagnostics_banking77.json",
            caveat="intent proxy, not evidence retrieval",
        ),
        dataset_summary(
            dataset="CUAD GT-anchored",
            role="sparse-GT boundary",
            bm25_path=RESULTS / "bm25_cuad_metrics.json",
            dense_path=RESULTS / "dense_cuad_metrics.json",
            hybrid_path=RESULTS / "hybrid_cuad_metrics.json",
            trust_path=RESULTS / "linucb_trust_cuad_prequential_metrics.json",
            geometry_path=RESULTS / "manifold_diagnostics_cuad.json",
            caveat="GT-anchored 10k sample; 79 evaluated queries",
        ),
    ]
    payload = {
        "task": "69.8",
        "summary": summary,
        "static_baselines": baselines,
        "guardrail": "mechanism/boundary only; not pooled with common evidence retrieval",
    }
    write_json(OUTPUT.with_suffix(".json"), payload)
    write_csv(OUTPUT.with_suffix(".summary.csv"), summary)
    write_csv(OUTPUT.with_suffix(".baselines.csv"), baselines)
    OUTPUT.with_suffix(".md").write_text(build_markdown(summary, baselines), encoding="utf-8")
    print(OUTPUT.with_suffix(".md").relative_to(ROOT))


if __name__ == "__main__":
    main()
