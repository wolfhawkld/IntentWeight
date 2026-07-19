#!/usr/bin/env python3
"""Stage Task79 four-endpoint downstream evaluation without API calls.

The two frozen Task63 Sentence-MMR endpoints are copied exactly. Existing
answers and all available judgments for those endpoints are reused; the two
LLMLingua-2 endpoints remain pending for resumable Task63-style execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "paper" / "experiments" / "results"
DEFAULT_COMPRESSOR_DIR = RESULTS_DIR / "task79_llmlingua2_matched_compressor"
DEFAULT_TASK63_DIR = RESULTS_DIR / "task63_downstream_llm_evaluation"
DEFAULT_OUTPUT_DIR = RESULTS_DIR / "task79_llmlingua2_downstream_evaluation"

DENSE_REFERENCE_LABEL = "dense_sent_mmr_r0.85_l0.70"
INTENT_REFERENCE_LABEL = "intentweight_sent_mmr_r0.85_l0.70_seed19"
DENSE_LLMLINGUA_LABEL = "dense_llmlingua2_matched_sent_mmr"
INTENT_LLMLINGUA_LABEL = "intentroute_llmlingua2_matched_sent_mmr_seed19"
REFERENCE_LABELS = (DENSE_REFERENCE_LABEL, INTENT_REFERENCE_LABEL)
ALL_LABELS = (
    DENSE_REFERENCE_LABEL,
    INTENT_REFERENCE_LABEL,
    DENSE_LLMLINGUA_LABEL,
    INTENT_LLMLINGUA_LABEL,
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def answer_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("query_id")), str(row.get("method_label"))


def judgment_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("query_id")),
        str(row.get("method_label")),
        str(row.get("judge_model")),
    )


def merge_unique(
    fixed_rows: Sequence[Mapping[str, Any]],
    existing_rows: Sequence[Mapping[str, Any]],
    *,
    key_fn,
    allowed_query_methods: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    merged: dict[Any, dict[str, Any]] = {}
    for row in fixed_rows:
        key = key_fn(row)
        if key in merged:
            raise ValueError(f"Duplicate fixed artifact key: {key}")
        merged[key] = dict(row)
    for row in existing_rows:
        query_method = answer_key(row)
        if query_method not in allowed_query_methods:
            raise ValueError(f"Existing output contains a non-Task79 endpoint: {query_method}")
        key = key_fn(row)
        if key in merged and canonical_sha256(merged[key]) != canonical_sha256(row):
            raise ValueError(f"Existing output conflicts with frozen artifact: {key}")
        merged[key] = dict(row)
    return list(merged.values())


def format_context(context: Sequence[Mapping[str, Any]]) -> str:
    blocks: list[str] = []
    for index, item in enumerate(context, 1):
        blocks.append(
            f"[{index}] rank={item.get('rank', index)} "
            f"chunk_id={item.get('chunk_id', '')} tokens={int(item.get('token_count') or 0)}\n"
            f"{item.get('text', '')}"
        )
    return "\n\n".join(blocks)


def generation_prompt(query_text: str, context: Sequence[Mapping[str, Any]]) -> str:
    return f"Question:\n{query_text}\n\nRetrieved context:\n{format_context(context)}\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compressor-dir", type=Path, default=DEFAULT_COMPRESSOR_DIR)
    parser.add_argument("--task63-dir", type=Path, default=DEFAULT_TASK63_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--preview-queries", type=int, default=2)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    compressor_summary_path = args.compressor_dir / "compression_summary.json"
    compressor_summary = read_json(compressor_summary_path)
    if compressor_summary.get("status") != "COMPLETE":
        raise RuntimeError(
            f"Task79 compression must be COMPLETE before staging: {compressor_summary_path}"
        )

    source_sample_path = args.compressor_dir / "sample_records.jsonl"
    sample_records = read_jsonl(source_sample_path)
    if len(sample_records) != 300:
        raise ValueError(f"Expected 300 Task79 sample records, got {len(sample_records)}")

    query_order = [str(row["query_id"]) for row in sample_records]
    if len(set(query_order)) != len(query_order):
        raise ValueError("Task79 sample records contain duplicate query IDs")
    allowed_query_methods: set[tuple[str, str]] = set()
    method_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for record in sample_records:
        labels = tuple(str(method["method_label"]) for method in record["methods"])
        if labels != ALL_LABELS:
            raise ValueError(
                f"Unexpected Task79 endpoint order for {record['query_id']}: {labels}"
            )
        for method in record["methods"]:
            key = (str(record["query_id"]), str(method["method_label"]))
            allowed_query_methods.add(key)
            method_by_key[key] = method

    source_answers = [
        row
        for row in read_jsonl(args.task63_dir / "answers.jsonl")
        if str(row.get("method_label")) in REFERENCE_LABELS
    ]
    if len(source_answers) != 600:
        raise ValueError(f"Expected 600 frozen Sentence-MMR answers, got {len(source_answers)}")
    answer_keys = [answer_key(row) for row in source_answers]
    if len(set(answer_keys)) != len(answer_keys):
        raise ValueError("Frozen Sentence-MMR answers contain duplicate keys")

    for answer in source_answers:
        key = answer_key(answer)
        method = method_by_key.get(key)
        if method is None:
            raise ValueError(f"Frozen answer is outside the Task79 query/method set: {key}")
        if int(answer["context_tokens"]) != int(method["context_tokens"]):
            raise ValueError(f"Frozen answer context-token mismatch: {key}")
        if list(answer["context_chunk_ids"]) != list(method["context_chunk_ids"]):
            raise ValueError(f"Frozen answer context-ID mismatch: {key}")

    source_judgments = [
        row
        for row in read_jsonl(args.task63_dir / "judgments.jsonl")
        if str(row.get("method_label")) in REFERENCE_LABELS
    ]
    judgment_keys = [judgment_key(row) for row in source_judgments]
    if len(set(judgment_keys)) != len(judgment_keys):
        raise ValueError("Frozen Sentence-MMR judgments contain duplicate keys")
    source_judgment_failures = [
        row
        for row in read_jsonl(args.task63_dir / "judgment_failures.jsonl")
        if str(row.get("method_label")) in REFERENCE_LABELS
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    answer_path = args.output_dir / "answers.jsonl"
    judgment_path = args.output_dir / "judgments.jsonl"
    judgment_failure_path = args.output_dir / "judgment_failures.jsonl"
    answers = merge_unique(
        source_answers,
        read_jsonl(answer_path),
        key_fn=answer_key,
        allowed_query_methods=allowed_query_methods,
    )
    judgments = merge_unique(
        source_judgments,
        read_jsonl(judgment_path),
        key_fn=judgment_key,
        allowed_query_methods=allowed_query_methods,
    )
    failure_by_hash = {
        canonical_sha256(row): dict(row)
        for row in [
            *source_judgment_failures,
            *read_jsonl(judgment_failure_path),
        ]
    }
    judgment_failures = sorted(
        failure_by_hash.values(),
        key=lambda row: (
            str(row.get("query_id") or ""),
            str(row.get("method_label") or ""),
            str(row.get("judge_model") or ""),
            canonical_sha256(row),
        ),
    )

    method_position = {label: index for index, label in enumerate(ALL_LABELS)}
    query_position = {query_id: index for index, query_id in enumerate(query_order)}
    answers.sort(key=lambda row: (query_position[answer_key(row)[0]], method_position[answer_key(row)[1]]))
    judgments.sort(
        key=lambda row: (
            query_position[answer_key(row)[0]],
            method_position[answer_key(row)[1]],
            judgment_key(row)[2],
        )
    )

    shutil.copyfile(source_sample_path, args.output_dir / "sample_records.jsonl")
    write_jsonl(answer_path, answers)
    write_jsonl(judgment_path, judgments)
    write_jsonl(judgment_failure_path, judgment_failures)

    previews: list[dict[str, Any]] = []
    for record in sample_records[: max(0, args.preview_queries)]:
        for method in record["methods"]:
            previews.append(
                {
                    "query_id": record["query_id"],
                    "method_label": method["method_label"],
                    "generation_prompt": generation_prompt(record["query_text"], method["context"]),
                }
            )
    write_jsonl(args.output_dir / "prompt_preview.jsonl", previews)

    answer_counts = Counter(str(row["method_label"]) for row in answers)
    judgment_counts = Counter(str(row["judge_model"]) for row in judgments)
    judgment_method_counts = Counter(str(row["method_label"]) for row in judgments)
    pending_answers = {
        label: 300 - answer_counts.get(label, 0)
        for label in ALL_LABELS
    }
    pending_answer_count = sum(pending_answers.values())
    staging_status = (
        "STAGED_ANSWERS_COMPLETE_EXTERNAL_JUDGES_MAY_BE_PENDING"
        if pending_answer_count == 0
        else "READY_FOR_RESUMABLE_LLM_EXECUTION"
    )
    payload = {
        "status": staging_status,
        "query_count": len(sample_records),
        "method_labels": list(ALL_LABELS),
        "sample_records_sha256": sha256_file(args.output_dir / "sample_records.jsonl"),
        "compressor_protocol_signature": compressor_summary["protocol_signature"],
        "answers_staged": len(answers),
        "answer_counts_by_method": dict(sorted(answer_counts.items())),
        "pending_answers_by_method": pending_answers,
        "judgments_staged": len(judgments),
        "judgment_counts_by_model": dict(sorted(judgment_counts.items())),
        "judgment_counts_by_method": dict(sorted(judgment_method_counts.items())),
        "judgment_failure_attempts_staged": len(judgment_failures),
        "reuse_validation": {
            "frozen_answer_count": len(source_answers),
            "frozen_judgment_count": len(source_judgments),
            "frozen_judgment_failure_attempts": len(source_judgment_failures),
            "context_tokens_exact": True,
            "context_chunk_ids_exact": True,
        },
        "next_execution": {
            "script": "paper/experiments/scripts/task63_downstream_llm_evaluation.py",
            "resume_llm_only": True,
            "new_answers_expected": pending_answer_count,
            "formal_summary": "use Task79 analyzer; skip legacy single-judge summary",
        },
    }
    write_json(args.output_dir / "staging_summary.json", payload)
    write_json(
        args.output_dir / "run_config.json",
        {
            "task": "Task79",
            "compressor_summary": str(compressor_summary_path),
            "source_task63_dir": str(args.task63_dir),
            "method_labels": list(ALL_LABELS),
            "staging_command_api_calls_made": False,
        },
    )

    lines = [
        "# Task79 Downstream Evaluation Staging",
        "",
        f"Status: **{staging_status}**",
        "",
        f"- Frozen queries: `{len(sample_records)}`",
        f"- Existing answers reused: `{len(source_answers)}`",
        f"- Existing judgments reused: `{len(source_judgments)}`",
        f"- Judgment failure attempts retained: `{len(judgment_failures)}`",
        f"- New LLMLingua-2 answers pending: `{pending_answer_count}`",
        "",
        "| Endpoint | Existing answers | Pending answers | Existing judgments |",
        "|---|---:|---:|---:|",
    ]
    for label in ALL_LABELS:
        lines.append(
            f"| {label} | {answer_counts.get(label, 0)} | {pending_answers[label]} | "
            f"{judgment_method_counts.get(label, 0)} |"
        )
    lines.extend(
        [
            "",
            "This staging command makes no answer or judge API calls.",
            "",
        ]
    )
    (args.output_dir / "staging_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
