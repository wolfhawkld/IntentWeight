#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build paper-ready tables for global LinUCB online baseline results."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_SUMMARY = DEFAULT_RESULTS_DIR / "linucb_online_summary.csv"

TABLE_COLUMNS = [
    "dataset",
    "method",
    "protocol",
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
    "num_seeds",
    "n_effective_arms_mean",
    "candidate_arms",
    "recall@1_mean",
    "recall@1_std",
    "recall@5_mean",
    "recall@5_std",
    "recall@10_mean",
    "recall@10_std",
    "mrr@10_mean",
    "mrr@10_std",
    "ndcg@10_mean",
    "ndcg@10_std",
    "avg_feedback_reward_mean",
    "elapsed_sec",
    "notes",
]


def load_rows(path: Path) -> List[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _format_float(value: object, digits: int = 4) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):.{digits}f}"


def _row_sort_key(row: Mapping[str, str]) -> tuple[str, str]:
    return (row.get("dataset", ""), row.get("method", ""))


def select_main_evidence_rows(rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    selected = []
    for row in rows:
        if row.get("task_type") != "evidence_retrieval":
            continue
        if row.get("scope") not in {"full", "heldout_test"}:
            continue
        if row.get("corpus_scope") != "full":
            continue
        selected.append(dict(row))
    return sorted(selected, key=_row_sort_key)


def select_intent_proxy_rows(rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    selected = [dict(row) for row in rows if row.get("task_type") == "intent_retrieval_proxy"]
    return sorted(selected, key=_row_sort_key)


def select_smoke_rows(rows: Iterable[Mapping[str, str]]) -> List[dict[str, str]]:
    selected = [dict(row) for row in rows if row.get("scope") == "smoke_only"]
    return sorted(selected, key=_row_sort_key)


def compact_row(row: Mapping[str, str]) -> dict[str, str]:
    output = {key: row.get(key, "") for key in TABLE_COLUMNS}
    output["method"] = "Global LinUCB"
    for key in TABLE_COLUMNS:
        if key.endswith("_mean") or key.endswith("_std"):
            output[key] = _format_float(row.get(key, ""))
    output["elapsed_sec"] = _format_float(row.get("elapsed_sec", ""), digits=3)
    return output


def write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TABLE_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(compact_row(row))


def _escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: Sequence[Mapping[str, str]]) -> str:
    compacted = [compact_row(row) for row in rows]
    columns = [
        "dataset",
        "scope",
        "query_split",
        "corpus_scope",
        "num_queries",
        "num_skipped_no_gt",
        "num_queries_with_gt_in_corpus",
        "gt_query_coverage",
        "num_seeds",
        "recall@1_mean",
        "recall@10_mean",
        "mrr@10_mean",
        "ndcg@10_mean",
        "notes",
    ]
    if not compacted:
        return "_No eligible rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in compacted:
        lines.append("| " + " | ".join(_escape_markdown(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def write_markdown(
    path: Path,
    *,
    main_rows: Sequence[Mapping[str, str]],
    intent_rows: Sequence[Mapping[str, str]],
    smoke_rows: Sequence[Mapping[str, str]],
) -> None:
    content = "\n\n".join([
        "# Global LinUCB Online Baseline Tables",
        "## Evidence Retrieval Main Table",
        markdown_table(main_rows),
        "## Intent Retrieval Proxy",
        markdown_table(intent_rows),
        "## Smoke / Sample Results",
        markdown_table(smoke_rows),
        "## Notes",
        (
            "- Protocol is prequential: each query is evaluated before its GT-derived feedback update.\n"
            "- This is the global LinUCB baseline. Manifold-local feedback propagation is reserved for Task 12.\n"
            "- CUAD remains smoke/sample only; sampled CUAD corpora must pass GT-in-corpus coverage."
        ),
    ])
    path.write_text(content + "\n", encoding="utf-8")


def build_tables(summary_path: Path, output_dir: Path) -> dict[str, List[dict[str, str]]]:
    rows = load_rows(summary_path)
    tables = {
        "main": select_main_evidence_rows(rows),
        "intent_proxy": select_intent_proxy_rows(rows),
        "smoke": select_smoke_rows(rows),
    }
    write_csv(output_dir / "linucb_online_main_table.csv", tables["main"])
    write_csv(output_dir / "linucb_online_intent_proxy_table.csv", tables["intent_proxy"])
    write_csv(output_dir / "linucb_online_smoke_table.csv", tables["smoke"])
    write_markdown(
        output_dir / "linucb_online_tables.md",
        main_rows=tables["main"],
        intent_rows=tables["intent_proxy"],
        smoke_rows=tables["smoke"],
    )
    return tables


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build global LinUCB online baseline tables")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args(argv)

    tables = build_tables(args.summary, args.output_dir)
    print(
        "Wrote LinUCB online tables: "
        f"main={len(tables['main'])}, "
        f"intent_proxy={len(tables['intent_proxy'])}, "
        f"smoke={len(tables['smoke'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
