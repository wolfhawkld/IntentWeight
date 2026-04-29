#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build paper-ready retrieval baseline tables from guarded comparison rows."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_COMPARISON = DEFAULT_RESULTS_DIR / "retrieval_baseline_comparison.csv"

TABLE_COLUMNS = [
    "dataset",
    "method",
    "task_type",
    "scope",
    "query_split",
    "corpus_scope",
    "corpus_sampling",
    "num_corpus_chunks",
    "num_queries",
    "num_skipped_no_gt",
    "num_queries_with_gt_in_corpus",
    "gt_query_coverage",
    "recall@1",
    "recall@5",
    "recall@10",
    "mrr@10",
    "ndcg@10",
    "elapsed_sec",
    "notes",
]

METHOD_LABELS = {
    "bm25": "BM25",
    "dense": "Dense",
    "hybrid_rrf": "Hybrid RRF",
}


def load_rows(path: Path) -> List[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _format_metric(value: object) -> str:
    number = _float_or_none(value)
    return "" if number is None else f"{number:.4f}"


def _format_elapsed(value: object) -> str:
    number = _float_or_none(value)
    return "" if number is None else f"{number:.3f}"


def _row_sort_key(row: Mapping[str, str]) -> tuple[str, int]:
    method_order = {"bm25": 0, "dense": 1, "hybrid_rrf": 2}
    return (row.get("dataset", ""), method_order.get(row.get("method", ""), 99))


def select_main_evidence_rows(rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    """Rows eligible for the evidence retrieval main table.

    Excludes intent proxy tasks, smoke/sample rows, non-comparable rows, and
    partial-corpus rows. PubMedQA remains included with its section-level GT
    caveat in notes.
    """
    selected = []
    for row in rows:
        if row.get("method") not in METHOD_LABELS:
            continue
        if row.get("task_type") != "evidence_retrieval":
            continue
        if not _truthy(row.get("is_comparable")):
            continue
        if row.get("scope") not in {"full", "heldout_test"}:
            continue
        if row.get("corpus_scope") != "full":
            continue
        selected.append(dict(row))
    return sorted(selected, key=_row_sort_key)


def select_intent_proxy_rows(rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    selected = [
        dict(row)
        for row in rows
        if row.get("method") in METHOD_LABELS
        and row.get("task_type") == "intent_retrieval_proxy"
        and _truthy(row.get("is_comparable"))
    ]
    return sorted(selected, key=_row_sort_key)


def select_smoke_rows(rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    selected = [
        dict(row)
        for row in rows
        if row.get("method") in METHOD_LABELS
        and row.get("scope") == "smoke_only"
        and _truthy(row.get("is_comparable"))
    ]
    return sorted(selected, key=_row_sort_key)


def compact_row(row: Mapping[str, str]) -> dict[str, str]:
    output = {key: row.get(key, "") for key in TABLE_COLUMNS}
    output["method"] = METHOD_LABELS.get(row.get("method", ""), row.get("method", ""))
    for metric in ("recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10"):
        output[metric] = _format_metric(row.get(metric, ""))
    output["elapsed_sec"] = _format_elapsed(row.get("elapsed_sec", ""))
    return output


def write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TABLE_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(compact_row(row))


def markdown_table(rows: Sequence[Mapping[str, str]]) -> str:
    compacted = [compact_row(row) for row in rows]
    md_columns = [
        "dataset",
        "method",
        "scope",
        "query_split",
        "corpus_scope",
        "num_queries",
        "num_skipped_no_gt",
        "num_queries_with_gt_in_corpus",
        "gt_query_coverage",
        "recall@1",
        "recall@5",
        "recall@10",
        "mrr@10",
        "ndcg@10",
        "notes",
    ]
    if not compacted:
        return "_No eligible rows._"
    lines = [
        "| " + " | ".join(md_columns) + " |",
        "| " + " | ".join("---" for _ in md_columns) + " |",
    ]
    for row in compacted:
        lines.append("| " + " | ".join(_escape_markdown(row.get(column, "")) for column in md_columns) + " |")
    return "\n".join(lines)


def _escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(
    path: Path,
    *,
    main_rows: Sequence[Mapping[str, str]],
    intent_rows: Sequence[Mapping[str, str]],
    smoke_rows: Sequence[Mapping[str, str]],
) -> None:
    content = "\n\n".join(
        [
            "# Retrieval Baseline Tables",
            "## Evidence Retrieval Main Table",
            markdown_table(main_rows),
            "## Intent Retrieval Proxy",
            markdown_table(intent_rows),
            "## Smoke / Sample Results",
            markdown_table(smoke_rows),
            "## Notes",
            (
                "- Main evidence table excludes `smoke_only`, non-comparable, and intent proxy rows.\n"
                "- CUAD is reported only as a smoke/sample result; sampled CUAD corpora must pass GT-in-corpus coverage.\n"
                "- Dense rows use `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine unless noted otherwise."
            ),
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def build_tables(comparison_path: Path, output_dir: Path) -> dict[str, List[dict[str, str]]]:
    rows = load_rows(comparison_path)
    tables = {
        "main": select_main_evidence_rows(rows),
        "intent_proxy": select_intent_proxy_rows(rows),
        "smoke": select_smoke_rows(rows),
    }

    write_csv(output_dir / "retrieval_baseline_main_table.csv", tables["main"])
    write_csv(output_dir / "retrieval_baseline_intent_proxy_table.csv", tables["intent_proxy"])
    write_csv(output_dir / "retrieval_baseline_smoke_table.csv", tables["smoke"])
    write_markdown(
        output_dir / "retrieval_baseline_tables.md",
        main_rows=tables["main"],
        intent_rows=tables["intent_proxy"],
        smoke_rows=tables["smoke"],
    )
    return tables


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build paper-ready retrieval baseline tables")
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args(argv)

    tables = build_tables(args.comparison, args.output_dir)
    print(
        "Wrote retrieval tables: "
        f"main={len(tables['main'])}, "
        f"intent_proxy={len(tables['intent_proxy'])}, "
        f"smoke={len(tables['smoke'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
