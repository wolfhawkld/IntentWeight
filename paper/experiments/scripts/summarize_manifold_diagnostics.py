#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Join manifold diagnostics with retrieval gains for paper-ready tables."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_DIAGNOSTICS = DEFAULT_RESULTS_DIR / "manifold_diagnostics_summary.csv"
DEFAULT_DENSE = DEFAULT_RESULTS_DIR / "dense_baseline_summary.csv"
DEFAULT_SOFT = DEFAULT_RESULTS_DIR / "linucb_soft_summary.csv"

KEY_FIELDS = ("dataset", "scope", "query_split", "corpus_scope")
OUTPUT_COLUMNS = [
    "dataset",
    "task_type",
    "scope",
    "query_split",
    "corpus_scope",
    "num_corpus_chunks",
    "num_gt_eval_queries",
    "pca_dim_for_90pct",
    "pca_participation_ratio_dim",
    "cluster_size_entropy_norm",
    "cluster_label_purity",
    "cluster_label_nmi",
    "local_label_purity",
    "nearest_cluster_hit@1",
    "nearest_cluster_hit@3",
    "nearest_cluster_hit@5",
    "context_gt_recall@10",
    "context_recall_retention@10",
    "dense_recall@10",
    "soft_recall@10",
    "soft_minus_dense_recall@10",
    "soft_selected_cluster_hit_rate",
    "soft_rescue_on_cluster_miss_rate",
    "interpretation",
    "notes",
]


def load_rows(path: Path) -> List[dict[str, str]]:
    if not path.exists():
        return []
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


def _metric(row: Mapping[str, str] | None, *names: str) -> float | None:
    if row is None:
        return None
    for name in names:
        value = _float_or_none(row.get(name))
        if value is not None:
            return value
    return None


def _interpretation(row: Mapping[str, str], delta: float | None) -> str:
    if delta is None:
        return "missing comparable dense/soft retrieval result"
    nearest3 = _float_or_none(row.get("nearest_cluster_hit@3")) or 0.0
    local_purity = _float_or_none(row.get("local_label_purity")) or 0.0
    retention = _float_or_none(row.get("context_recall_retention@10")) or 0.0
    if abs(delta) <= 0.005 and nearest3 >= 0.9:
        return "strong GT-cluster routing signal; soft routing mainly preserves dense baseline"
    if delta < 0 and nearest3 >= 0.75 and retention >= 0.9:
        return "geometry can route to GT clusters, but learned arm/fusion underuses the signal"
    if delta < 0 and nearest3 < 0.5:
        return "negative case: weak GT-cluster routing signal"
    if delta >= 0 and nearest3 >= 0.7 and local_purity >= 0.5:
        return "strong local routing signal aligns with soft-routing gain"
    if delta >= 0:
        return "soft routing helps despite imperfect cluster routing"
    if retention < 0.8:
        return "PCA/context geometry may lose retrieval evidence"
    if local_purity < 0.3:
        return "available metadata labels weakly align with semantic neighborhoods"
    return "diagnostics do not fully explain retrieval gap"


def build_comparison(
    diagnostics_rows: Iterable[Mapping[str, str]],
    dense_rows: Iterable[Mapping[str, str]],
    soft_rows: Iterable[Mapping[str, str]],
) -> List[dict[str, str]]:
    dense_by_key: Dict[tuple[str, ...], Mapping[str, str]] = {_key(row): row for row in dense_rows}
    soft_by_key: Dict[tuple[str, ...], Mapping[str, str]] = {_key(row): row for row in soft_rows}
    output: List[dict[str, str]] = []
    for diag in diagnostics_rows:
        key = _key(diag)
        dense = dense_by_key.get(key)
        soft = soft_by_key.get(key)
        dense_recall = _metric(dense, "recall@10", "recall@10_mean")
        soft_recall = _metric(soft, "recall@10_mean", "recall@10")
        delta = soft_recall - dense_recall if soft_recall is not None and dense_recall is not None else None
        notes_parts = [diag.get("notes", "")]
        if dense and dense.get("notes"):
            notes_parts.append(dense["notes"])
        if soft and soft.get("notes"):
            notes_parts.append(soft["notes"])
        notes = " ".join(part for part in dict.fromkeys(part.strip() for part in notes_parts) if part)
        output.append({
            "dataset": diag.get("dataset", ""),
            "task_type": diag.get("task_type", ""),
            "scope": diag.get("scope", ""),
            "query_split": diag.get("query_split", ""),
            "corpus_scope": diag.get("corpus_scope", ""),
            "num_corpus_chunks": diag.get("num_corpus_chunks", ""),
            "num_gt_eval_queries": diag.get("num_gt_eval_queries", ""),
            "pca_dim_for_90pct": diag.get("pca_dim_for_90pct", ""),
            "pca_participation_ratio_dim": _fmt(_float_or_none(diag.get("pca_participation_ratio_dim"))),
            "cluster_size_entropy_norm": _fmt(_float_or_none(diag.get("cluster_size_entropy_norm"))),
            "cluster_label_purity": _fmt(_float_or_none(diag.get("cluster_label_purity"))),
            "cluster_label_nmi": _fmt(_float_or_none(diag.get("cluster_label_nmi"))),
            "local_label_purity": _fmt(_float_or_none(diag.get("local_label_purity"))),
            "nearest_cluster_hit@1": _fmt(_float_or_none(diag.get("nearest_cluster_hit@1"))),
            "nearest_cluster_hit@3": _fmt(_float_or_none(diag.get("nearest_cluster_hit@3"))),
            "nearest_cluster_hit@5": _fmt(_float_or_none(diag.get("nearest_cluster_hit@5"))),
            "context_gt_recall@10": _fmt(_float_or_none(diag.get("context_gt_recall@10"))),
            "context_recall_retention@10": _fmt(_float_or_none(diag.get("context_recall_retention@10"))),
            "dense_recall@10": _fmt(dense_recall),
            "soft_recall@10": _fmt(soft_recall),
            "soft_minus_dense_recall@10": _fmt(delta),
            "soft_selected_cluster_hit_rate": _fmt(_metric(soft, "selected_cluster_hit_rate_mean")),
            "soft_rescue_on_cluster_miss_rate": _fmt(_metric(soft, "soft_rescue_on_cluster_miss_rate_mean")),
            "interpretation": _interpretation(diag, delta),
            "notes": notes,
        })
    return sorted(output, key=lambda row: (row["task_type"], row["dataset"]))


def write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _select(rows: Sequence[Mapping[str, str]], section: str) -> List[Mapping[str, str]]:
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


def markdown_table(rows: Sequence[Mapping[str, str]]) -> str:
    columns = [
        "dataset",
        "scope",
        "corpus_scope",
        "pca_dim_for_90pct",
        "cluster_label_purity",
        "local_label_purity",
        "nearest_cluster_hit@3",
        "context_gt_recall@10",
        "dense_recall@10",
        "soft_recall@10",
        "soft_minus_dense_recall@10",
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
        "# Manifold Diagnostics",
        "## Evidence Retrieval Main",
        markdown_table(_select(rows, "main")),
        "## Intent Retrieval Proxy",
        markdown_table(_select(rows, "intent")),
        "## Smoke / Sample Results",
        markdown_table(_select(rows, "smoke")),
        "## Notes",
        (
            "- PCA/context metrics test whether low-dimensional geometry preserves evidence retrieval.\n"
            "- Cluster/local purity metrics test whether the corpus has coherent local neighborhoods under available metadata labels.\n"
            "- nearest_cluster_hit@k tests whether query contexts route toward clusters containing GT chunks without using LinUCB feedback.\n"
            "- soft_minus_dense_recall@10 relates these diagnostics to Task 13.5 soft-routing gains."
        ),
    ])
    path.write_text(content + "\n", encoding="utf-8")


def build_tables(
    diagnostics_path: Path,
    dense_path: Path,
    soft_path: Path,
    output_csv: Path,
    output_markdown: Path,
) -> List[dict[str, str]]:
    rows = build_comparison(load_rows(diagnostics_path), load_rows(dense_path), load_rows(soft_path))
    write_csv(output_csv, rows)
    write_markdown(output_markdown, rows)
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build manifold diagnostics comparison tables")
    parser.add_argument("--diagnostics", type=Path, default=DEFAULT_DIAGNOSTICS)
    parser.add_argument("--dense-summary", type=Path, default=DEFAULT_DENSE)
    parser.add_argument("--soft-summary", type=Path, default=DEFAULT_SOFT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_RESULTS_DIR / "manifold_diagnostics_comparison.csv")
    parser.add_argument("--output-markdown", type=Path, default=DEFAULT_RESULTS_DIR / "manifold_diagnostics_tables.md")
    args = parser.parse_args(argv)

    rows = build_tables(
        args.diagnostics,
        args.dense_summary,
        args.soft_summary,
        args.output_csv,
        args.output_markdown,
    )
    print(f"Wrote manifold diagnostics comparison rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
