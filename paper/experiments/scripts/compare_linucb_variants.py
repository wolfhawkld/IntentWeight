#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare global LinUCB and manifold-local LinUCB results."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_GLOBAL_SUMMARY = DEFAULT_RESULTS_DIR / "linucb_online_summary.csv"
DEFAULT_MANIFOLD_SUMMARY = DEFAULT_RESULTS_DIR / "linucb_manifold_summary.csv"

KEY_FIELDS = [
    "dataset",
    "task_type",
    "scope",
    "query_split",
    "corpus_scope",
    "top_k",
    "metric_ks",
]

OUTPUT_COLUMNS = [
    "dataset",
    "task_type",
    "scope",
    "query_split",
    "corpus_scope",
    "num_queries",
    "num_skipped_no_gt",
    "gt_query_coverage",
    "num_seeds",
    "global_recall@1_mean",
    "manifold_recall@1_mean",
    "delta_recall@1_mean",
    "global_recall@5_mean",
    "manifold_recall@5_mean",
    "delta_recall@5_mean",
    "global_recall@10_mean",
    "manifold_recall@10_mean",
    "delta_recall@10_mean",
    "relative_recall@10_pct",
    "global_mrr@10_mean",
    "manifold_mrr@10_mean",
    "delta_mrr@10_mean",
    "relative_mrr@10_pct",
    "global_ndcg@10_mean",
    "manifold_ndcg@10_mean",
    "delta_ndcg@10_mean",
    "global_avg_feedback_reward_mean",
    "manifold_avg_feedback_reward_mean",
    "delta_avg_feedback_reward_mean",
    "avg_local_boost_norm_mean",
    "cross_arm_update_weight_mean",
    "winner_recall@10",
    "winner_mrr@10",
    "interpretation",
    "notes",
]


def load_rows(path: Path) -> List[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _key(row: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in KEY_FIELDS)


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _fmt(value: float | None, digits: int = 4) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def _delta(manifold_row: Mapping[str, str], global_row: Mapping[str, str], metric: str) -> float | None:
    manifold_value = _float_or_none(manifold_row.get(metric))
    global_value = _float_or_none(global_row.get(metric))
    if manifold_value is None or global_value is None:
        return None
    return manifold_value - global_value


def _relative_pct(delta: float | None, baseline: float | None) -> float | None:
    if delta is None or baseline in (None, 0.0):
        return None
    return 100.0 * delta / baseline


def _winner(delta: float | None, *, tolerance: float = 1e-12) -> str:
    if delta is None:
        return ""
    if delta > tolerance:
        return "manifold_local"
    if delta < -tolerance:
        return "global"
    return "tie"


def _interpretation(row: Mapping[str, str], recall_delta: float | None, mrr_delta: float | None) -> str:
    dataset = row.get("dataset", "")
    if recall_delta is None:
        return "missing comparable metric"
    if recall_delta > 0 and (mrr_delta or 0.0) >= 0:
        return "manifold-local improves both recall and MRR"
    if recall_delta > 0:
        return "manifold-local improves recall but not MRR"
    if recall_delta < 0 and (mrr_delta or 0.0) <= 0:
        if dataset == "cuad":
            return "global remains stronger on CUAD smoke sample"
        return "global remains stronger under current manifold parameters"
    if recall_delta < 0:
        return "global has better recall; manifold has offsetting rank-quality signal"
    return "no recall change"


def compare_rows(global_rows: Iterable[Mapping[str, str]], manifold_rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    global_by_key: Dict[tuple[str, ...], Mapping[str, str]] = {_key(row): row for row in global_rows}
    comparisons: List[dict[str, str]] = []
    for manifold_row in manifold_rows:
        key = _key(manifold_row)
        global_row = global_by_key.get(key)
        if global_row is None:
            continue

        recall1_delta = _delta(manifold_row, global_row, "recall@1_mean")
        recall5_delta = _delta(manifold_row, global_row, "recall@5_mean")
        recall10_delta = _delta(manifold_row, global_row, "recall@10_mean")
        mrr10_delta = _delta(manifold_row, global_row, "mrr@10_mean")
        ndcg10_delta = _delta(manifold_row, global_row, "ndcg@10_mean")
        reward_delta = _delta(manifold_row, global_row, "avg_feedback_reward_mean")
        global_recall10 = _float_or_none(global_row.get("recall@10_mean"))
        global_mrr10 = _float_or_none(global_row.get("mrr@10_mean"))

        notes_parts: List[str] = []
        for part in [str(global_row.get("notes", "")).strip(), str(manifold_row.get("notes", "")).strip()]:
            if part and part not in notes_parts:
                notes_parts.append(part)
        notes = " ".join(notes_parts)
        comparisons.append({
            "dataset": str(manifold_row.get("dataset", "")),
            "task_type": str(manifold_row.get("task_type", "")),
            "scope": str(manifold_row.get("scope", "")),
            "query_split": str(manifold_row.get("query_split", "")),
            "corpus_scope": str(manifold_row.get("corpus_scope", "")),
            "num_queries": str(manifold_row.get("num_queries", "")),
            "num_skipped_no_gt": str(manifold_row.get("num_skipped_no_gt", "")),
            "gt_query_coverage": str(manifold_row.get("gt_query_coverage", global_row.get("gt_query_coverage", ""))),
            "num_seeds": str(manifold_row.get("num_seeds", "")),
            "global_recall@1_mean": _fmt(_float_or_none(global_row.get("recall@1_mean"))),
            "manifold_recall@1_mean": _fmt(_float_or_none(manifold_row.get("recall@1_mean"))),
            "delta_recall@1_mean": _fmt(recall1_delta),
            "global_recall@5_mean": _fmt(_float_or_none(global_row.get("recall@5_mean"))),
            "manifold_recall@5_mean": _fmt(_float_or_none(manifold_row.get("recall@5_mean"))),
            "delta_recall@5_mean": _fmt(recall5_delta),
            "global_recall@10_mean": _fmt(global_recall10),
            "manifold_recall@10_mean": _fmt(_float_or_none(manifold_row.get("recall@10_mean"))),
            "delta_recall@10_mean": _fmt(recall10_delta),
            "relative_recall@10_pct": _fmt(_relative_pct(recall10_delta, global_recall10), digits=2),
            "global_mrr@10_mean": _fmt(global_mrr10),
            "manifold_mrr@10_mean": _fmt(_float_or_none(manifold_row.get("mrr@10_mean"))),
            "delta_mrr@10_mean": _fmt(mrr10_delta),
            "relative_mrr@10_pct": _fmt(_relative_pct(mrr10_delta, global_mrr10), digits=2),
            "global_ndcg@10_mean": _fmt(_float_or_none(global_row.get("ndcg@10_mean"))),
            "manifold_ndcg@10_mean": _fmt(_float_or_none(manifold_row.get("ndcg@10_mean"))),
            "delta_ndcg@10_mean": _fmt(ndcg10_delta),
            "global_avg_feedback_reward_mean": _fmt(_float_or_none(global_row.get("avg_feedback_reward_mean"))),
            "manifold_avg_feedback_reward_mean": _fmt(_float_or_none(manifold_row.get("avg_feedback_reward_mean"))),
            "delta_avg_feedback_reward_mean": _fmt(reward_delta),
            "avg_local_boost_norm_mean": _fmt(_float_or_none(manifold_row.get("avg_local_boost_norm_mean"))),
            "cross_arm_update_weight_mean": _fmt(_float_or_none(manifold_row.get("cross_arm_update_weight_mean"))),
            "winner_recall@10": _winner(recall10_delta),
            "winner_mrr@10": _winner(mrr10_delta),
            "interpretation": _interpretation(manifold_row, recall10_delta, mrr10_delta),
            "notes": notes,
        })
    return sorted(comparisons, key=lambda row: (row["task_type"], row["dataset"]))


def write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _select_rows(rows: Iterable[Mapping[str, str]], section: str) -> List[Mapping[str, str]]:
    if section == "main":
        return [
            row for row in rows
            if row.get("task_type") == "evidence_retrieval"
            and row.get("scope") in {"full", "heldout_test"}
            and row.get("corpus_scope") == "full"
        ]
    if section == "intent":
        return [row for row in rows if row.get("task_type") == "intent_retrieval_proxy"]
    if section == "smoke":
        return [row for row in rows if row.get("scope") == "smoke_only"]
    return list(rows)


def _escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: Sequence[Mapping[str, str]]) -> str:
    columns = [
        "dataset",
        "scope",
        "corpus_scope",
        "global_recall@10_mean",
        "manifold_recall@10_mean",
        "delta_recall@10_mean",
        "global_mrr@10_mean",
        "manifold_mrr@10_mean",
        "delta_mrr@10_mean",
        "winner_recall@10",
        "interpretation",
    ]
    if not rows:
        return "_No eligible rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_escape_markdown(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def write_markdown(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    content = "\n\n".join([
        "# LinUCB Variant Comparison",
        "## Evidence Retrieval Main",
        markdown_table(_select_rows(rows, "main")),
        "## Intent Retrieval Proxy",
        markdown_table(_select_rows(rows, "intent")),
        "## Smoke / Sample Results",
        markdown_table(_select_rows(rows, "smoke")),
        "## Notes",
        (
            "- Global LinUCB is the Task 11 baseline.\n"
            "- Manifold-local LinUCB is the Task 12 variant with query-neighborhood feedback attention and cross-arm distance-decay propagation.\n"
            "- Positive delta means manifold-local is better than global under the same query/corpus/protocol scope.\n"
            "- CUAD remains smoke/sample only and should not be treated as full-corpus held-out evidence."
        ),
    ])
    path.write_text(content + "\n", encoding="utf-8")


def build_comparison(
    global_summary: Path,
    manifold_summary: Path,
    output_csv: Path,
    output_markdown: Path,
) -> List[dict[str, str]]:
    rows = compare_rows(load_rows(global_summary), load_rows(manifold_summary))
    write_csv(output_csv, rows)
    write_markdown(output_markdown, rows)
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare global and manifold-local LinUCB variants")
    parser.add_argument("--global-summary", type=Path, default=DEFAULT_GLOBAL_SUMMARY)
    parser.add_argument("--manifold-summary", type=Path, default=DEFAULT_MANIFOLD_SUMMARY)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_RESULTS_DIR / "linucb_variant_comparison.csv")
    parser.add_argument("--output-markdown", type=Path, default=DEFAULT_RESULTS_DIR / "linucb_variant_comparison.md")
    args = parser.parse_args(argv)

    rows = build_comparison(args.global_summary, args.manifold_summary, args.output_csv, args.output_markdown)
    print(f"Wrote LinUCB variant comparison rows={len(rows)}: {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
