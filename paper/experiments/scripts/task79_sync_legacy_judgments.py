#!/usr/bin/env python3
"""Sync recovered Task79 legacy Sentence-MMR judgments to Task63.

Only valid MiniMax judgments for the two byte-preserved Sentence-MMR endpoints
are eligible. The corresponding answer payloads must match before a missing
Task63 key is appended. Existing Task63 judgments are never overwritten.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS = ROOT / "paper" / "experiments" / "results"
DEFAULT_SOURCE = RESULTS / "task79_llmlingua2_downstream_evaluation"
DEFAULT_TARGET = RESULTS / "task63_downstream_llm_evaluation"
DEFAULT_REPORT = RESULTS / "task79_legacy_judgment_recovery.json"
METHODS = {
    "dense_sent_mmr_r0.85_l0.70",
    "intentweight_sent_mmr_r0.85_l0.70_seed19",
}
JUDGE = "minimax-m3"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


task63 = load_module("task79_sync_task63_runtime", SCRIPT_DIR / "task63_downstream_llm_evaluation.py")


def answer_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("query_id")), str(row.get("method_label"))


def judgment_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (*answer_key(row), str(row.get("judge_model")))


def comparable_answer(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "answer_text": row.get("answer_text"),
        "answer_json": row.get("answer_json"),
        "context_chunk_ids": row.get("context_chunk_ids"),
        "ground_truth_chunk_ids": row.get("ground_truth_chunk_ids"),
    }


def run(args: argparse.Namespace) -> int:
    source_answers = {answer_key(row): row for row in task63.read_jsonl(args.source / "answers.jsonl")}
    target_answers = {answer_key(row): row for row in task63.read_jsonl(args.target / "answers.jsonl")}
    source_judgments = {
        judgment_key(row): row
        for row in task63.read_jsonl(args.source / "judgments.jsonl")
        if task63.valid_judgment(row)
        and str(row.get("method_label")) in METHODS
        and str(row.get("judge_model")) == JUDGE
    }
    target_path = args.target / "judgments.jsonl"
    target_rows = task63.read_jsonl(target_path)
    target_keys = {judgment_key(row) for row in target_rows if task63.valid_judgment(row)}

    appended: list[tuple[str, str, str]] = []
    for key, row in sorted(source_judgments.items()):
        if key in target_keys:
            continue
        pair_key = key[:2]
        if pair_key not in source_answers or pair_key not in target_answers:
            raise ValueError(f"Missing answer payload for recovered judgment: {key}")
        if comparable_answer(source_answers[pair_key]) != comparable_answer(target_answers[pair_key]):
            raise ValueError(f"Task63/Task79 answer payload mismatch: {key}")
        task63.append_jsonl(target_path, row)
        target_keys.add(key)
        appended.append(key)

    report = {
        "status": "COMPLETE" if len(appended) == 7 else "NOOP" if not appended else "PARTIAL",
        "source": str(args.source.relative_to(ROOT)),
        "target": str(args.target.relative_to(ROOT)),
        "eligible_source_judgments": len(source_judgments),
        "appended_count": len(appended),
        "appended_keys": [list(key) for key in appended],
        "existing_judgments_preserved": True,
        "answer_payload_match_required": True,
        "credential_material_recorded": False,
    }
    task63.write_json(args.report, report)
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
