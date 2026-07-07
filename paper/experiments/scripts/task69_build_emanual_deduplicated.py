#!/usr/bin/env python3
"""Build the Task69 eManual deduplicated processed dataset."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


emanual = load_module("task69_emanual_failure_analysis", SCRIPT_DIR / "emanual_failure_analysis.py")
guardrails = emanual.experiment_guardrails


def load_json_list(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--query-split", default="test")
    parser.add_argument("--output-name", default="emanual_deduplicated")
    args = parser.parse_args(argv)

    corpus = load_json_list(args.data_dir / "emanual_corpus.json")
    queries_all = load_json_list(args.data_dir / "emanual_queries.json")
    queries = guardrails.apply_query_controls(queries_all, query_split=args.query_split)
    dedup_corpus, dedup_queries, _ = emanual.deduplicate_corpus_and_queries(corpus, queries)

    corpus_path = args.data_dir / f"{args.output_name}_corpus.json"
    queries_path = args.data_dir / f"{args.output_name}_queries.json"
    write_json(corpus_path, dedup_corpus)
    write_json(queries_path, dedup_queries)

    nonempty_gt = sum(1 for query in dedup_queries if query.get("ground_truth_chunk_ids"))
    summary = {
        "dataset": args.output_name,
        "source_dataset": "emanual",
        "query_split": args.query_split,
        "corpus_chunks": len(dedup_corpus),
        "queries": len(dedup_queries),
        "queries_with_gt": nonempty_gt,
        "empty_gt_queries": len(dedup_queries) - nonempty_gt,
        "output_corpus": str(corpus_path),
        "output_queries": str(queries_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
