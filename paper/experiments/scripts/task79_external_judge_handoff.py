#!/usr/bin/env python3
"""Prepare or import Task79 GLM/MiniMax external-judge artifacts.

Preparation is offline and emits one fixed request per new LLMLingua-2 answer.
Import validates request IDs, schemas, model names, and duplicate keys before
merging responses into the resumable Task79 judgment file.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "paper" / "experiments" / "results"
DEFAULT_INPUT_DIR = RESULTS_DIR / "task79_llmlingua2_downstream_evaluation"
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_DIR / "external_judge_handoff"
EXTERNAL_JUDGES = ("glm-5.2", "minimax-m3")
NEW_METHODS = (
    "dense_llmlingua2_matched_sent_mmr",
    "intentroute_llmlingua2_matched_sent_mmr_seed19",
)


def load_task63_module():
    path = SCRIPT_DIR / "task63_downstream_llm_evaluation.py"
    spec = importlib.util.spec_from_file_location("task79_task63_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Task63 contract: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def answer_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("query_id")), str(row.get("method_label"))


def judgment_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("query_id")),
        str(row.get("method_label")),
        str(row.get("judge_model")),
    )


def request_id(query_id: str, method_label: str) -> str:
    digest = hashlib.sha256(f"Task79\0{query_id}\0{method_label}".encode("utf-8")).hexdigest()
    return f"task79-{digest[:24]}"


def method_records(sample_records: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    flattened: dict[tuple[str, str], dict[str, Any]] = {}
    for record in sample_records:
        for method in record["methods"]:
            row = {
                "query_id": record["query_id"],
                "query_text": record["query_text"],
                "ground_truth_chunk_ids": record["ground_truth_chunk_ids"],
                "reference_evidence": record["reference_evidence"],
                **method,
            }
            key = answer_key(row)
            if key in flattened:
                raise ValueError(f"Duplicate sample method key: {key}")
            flattened[key] = row
    return flattened


def prepare(args: argparse.Namespace) -> int:
    task63 = load_task63_module()
    sample_path = args.input_dir / "sample_records.jsonl"
    answer_path = args.input_dir / "answers.jsonl"
    sample_records = read_jsonl(sample_path)
    answers = read_jsonl(answer_path)
    if len(sample_records) != 300:
        raise ValueError(f"Expected 300 Task79 sample records, got {len(sample_records)}")
    answers_by_key = {answer_key(row): row for row in answers}
    if len(answers_by_key) != len(answers) or len(answers_by_key) != 1200:
        raise ValueError("External judging requires exactly 1,200 unique Task79 answers")
    methods_by_key = method_records(sample_records)

    requests: list[dict[str, Any]] = []
    for query_id, method_label in sorted(answers_by_key):
        if method_label not in NEW_METHODS:
            continue
        answer = answers_by_key[(query_id, method_label)]
        source = methods_by_key[(query_id, method_label)]
        prompt = task63.judge_prompt(
            source,
            str(answer.get("answer_text") or ""),
            answer.get("answer_json"),
        )
        requests.append(
            {
                "request_id": request_id(query_id, method_label),
                "query_id": query_id,
                "method_label": method_label,
                "requested_judges": list(EXTERNAL_JUDGES),
                "system_prompt": task63.JUDGE_INSTRUCTIONS,
                "user_prompt": prompt,
                "answer_sha256": canonical_sha256(answer),
                "source_record_sha256": canonical_sha256(source),
                "required_output_keys": sorted(task63.JUDGE_REQUIRED_KEYS),
                "response_contract": {
                    "request_id": "copy from request",
                    "judge_model": "glm-5.2 or minimax-m3",
                    "judge_text": "raw model response",
                    "judge_json": "parsed strict JSON object",
                    "judge_usage": "provider usage object, or empty object",
                },
            }
        )
    if len(requests) != 600:
        raise ValueError(f"Expected 600 external-judge requests, got {len(requests)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    request_path = args.output_dir / "requests.jsonl"
    write_jsonl(request_path, requests)
    payload = {
        "status": "READY_FOR_TWO_EXTERNAL_JUDGES",
        "request_count": len(requests),
        "requested_judges": list(EXTERNAL_JUDGES),
        "expected_response_count": len(requests) * len(EXTERNAL_JUDGES),
        "input_sha256": {
            "sample_records.jsonl": sha256_file(sample_path),
            "answers.jsonl": sha256_file(answer_path),
        },
        "requests_sha256": sha256_file(request_path),
        "prompt_contract": "exact Task63 JUDGE_INSTRUCTIONS and judge_prompt",
        "missing_response_policy": "report provider failures; never impute",
        "import_command": (
            "python paper/experiments/scripts/task79_external_judge_handoff.py "
            "--responses <responses.jsonl>"
        ),
    }
    write_json(args.output_dir / "manifest.json", payload)
    (args.output_dir / "README.md").write_text(
        "\n".join(
            [
                "# Task79 External Judge Handoff",
                "",
                "Run every `requests.jsonl` prompt independently with `glm-5.2` and `minimax-m3`.",
                "Do not alter the system prompt, user prompt, answer, context, or schema.",
                "Return one response row per request/model using the embedded response contract.",
                "Provider rejections must be returned as explicit error rows and are not imputed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def import_responses(args: argparse.Namespace) -> int:
    task63 = load_task63_module()
    request_path = args.output_dir / "requests.jsonl"
    requests = read_jsonl(request_path)
    requests_by_id = {str(row["request_id"]): row for row in requests}
    if len(requests_by_id) != 600:
        raise ValueError("Prepare the fixed 600-request handoff before importing")
    responses = read_jsonl(args.responses)
    existing_path = args.input_dir / "judgments.jsonl"
    existing = read_jsonl(existing_path)
    existing_by_key = {judgment_key(row): row for row in existing}
    if len(existing_by_key) != len(existing):
        raise ValueError("Existing Task79 judgments contain duplicate keys")

    imported: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    seen_response_keys: set[tuple[str, str]] = set()
    for response in responses:
        rid = str(response.get("request_id") or "")
        judge = str(response.get("judge_model") or "")
        request = requests_by_id.get(rid)
        response_key = (rid, judge)
        if response_key in seen_response_keys:
            raise ValueError(f"Duplicate external response key: {response_key}")
        seen_response_keys.add(response_key)
        if request is None or judge not in EXTERNAL_JUDGES:
            failures.append({**response, "import_failure": "unknown request_id or judge_model"})
            continue
        if response.get("error"):
            failures.append(
                {
                    "request_id": rid,
                    "query_id": request["query_id"],
                    "method_label": request["method_label"],
                    "judge_model": judge,
                    "provider_error": response["error"],
                    "import_failure": "provider rejection",
                }
            )
            continue
        judge_text = str(response.get("judge_text") or "")
        parsed = response.get("judge_json")
        if not isinstance(parsed, Mapping):
            parsed = task63.try_parse_json(judge_text)
        row = {
            "query_id": request["query_id"],
            "method_label": request["method_label"],
            "judge_model": judge,
            "judge_text": judge_text,
            "judge_json": parsed,
            "judge_usage": response.get("judge_usage") or {},
        }
        if not task63.valid_judgment(row):
            failures.append({**row, "request_id": rid, "import_failure": "invalid judgment schema"})
            continue
        key = judgment_key(row)
        if key in existing_by_key and canonical_sha256(existing_by_key[key]) != canonical_sha256(row):
            raise ValueError(f"External response conflicts with existing judgment: {key}")
        existing_by_key[key] = row
        imported.append(row)

    merged = sorted(existing_by_key.values(), key=judgment_key)
    write_jsonl(existing_path, merged)
    failure_path = args.input_dir / "external_judgment_failures.jsonl"
    prior_failures = read_jsonl(failure_path)
    write_jsonl(failure_path, [*prior_failures, *failures])
    payload = {
        "status": "IMPORTED",
        "response_rows": len(responses),
        "valid_rows_imported_or_confirmed": len(imported),
        "invalid_or_rejected_rows": len(failures),
        "total_task79_judgments": len(merged),
        "judgments_sha256": sha256_file(existing_path),
    }
    write_json(args.output_dir / "last_import_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--responses",
        type=Path,
        default=None,
        help="Import external response JSONL instead of preparing requests.",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    return import_responses(args) if args.responses else prepare(args)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
