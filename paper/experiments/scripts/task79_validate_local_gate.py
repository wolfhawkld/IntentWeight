#!/usr/bin/env python3
"""Validate the complete local Task79 gate and explicit external-judge gap."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import task79_multi_judge_analysis as analysis


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS_DIR = REPO_ROOT / "paper" / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
DEFAULT_OUTPUT_PREFIX = RESULTS_DIR / "task79_local_validation"
DEFAULT_PREFLIGHT = RESULTS_DIR / "task79_llmlingua2_preflight.json"
DEFAULT_SEGMENT_AUDIT = RESULTS_DIR / "task79_llmlingua2_segment_audit.json"
DEFAULT_COMPRESSOR_DIR = RESULTS_DIR / "task79_llmlingua2_matched_compressor"
DEFAULT_DOWNSTREAM_DIR = RESULTS_DIR / "task79_llmlingua2_downstream_evaluation"
DEFAULT_ANALYSIS = RESULTS_DIR / "task79_llmlingua2_multi_judge_analysis.json"
DEFAULT_REPRO_DIR = EXPERIMENTS_DIR / "reproducibility" / "task79"
NEW_METHODS = (analysis.DENSE_LLMLINGUA, analysis.INTENT_LLMLINGUA)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--segment-audit", type=Path, default=DEFAULT_SEGMENT_AUDIT)
    parser.add_argument("--compressor-dir", type=Path, default=DEFAULT_COMPRESSOR_DIR)
    parser.add_argument("--downstream-dir", type=Path, default=DEFAULT_DOWNSTREAM_DIR)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--repro-dir", type=Path, default=DEFAULT_REPRO_DIR)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    preflight = read_json(args.preflight)
    segment = read_json(args.segment_audit)
    compressor = read_json(args.compressor_dir / "compression_summary.json")
    compression_rows = read_jsonl(args.compressor_dir / "compression_records.jsonl")
    sample_rows = read_jsonl(args.downstream_dir / "sample_records.jsonl")
    answers = read_jsonl(args.downstream_dir / "answers.jsonl")
    judgments = read_jsonl(args.downstream_dir / "judgments.jsonl")
    execution = read_json(args.downstream_dir / "llm_execution_manifest.json")
    handoff = read_json(args.downstream_dir / "external_judge_handoff" / "manifest.json")
    requests = read_jsonl(args.downstream_dir / "external_judge_handoff" / "requests.jsonl")
    analysis_payload = read_json(args.analysis)
    environment = read_json(args.repro_dir / "environment-rocm.json")
    lock_path = args.repro_dir / "requirements-rocm-lock.txt"

    check("preflight_status", preflight["status"] == "PASS", preflight["status"])
    check(
        "preflight_device",
        preflight["environment"]["device_name"] == "AMD Radeon RX 9070 XT",
        preflight["environment"]["device_name"],
    )
    weight_records = [
        row
        for row in preflight["provenance"]["model_snapshot_files"]
        if row["path"] == "model.safetensors"
    ]
    check(
        "fixed_weight_hash",
        len(weight_records) == 1
        and weight_records[0]["sha256"]
        == "a33a153b2493bff6be06af6921e69de9c0d0bb6ff06fe5bbb68670ba8d980ae2",
        weight_records,
    )
    check("segment_audit_status", segment["status"] == "PASS", segment["status"])
    check(
        "segment_content_not_truncated",
        segment["content_tokens_dropped"] == 0
        and segment["max_classifier_content_tokens"] <= 511,
        {
            "max_content_tokens": segment["max_classifier_content_tokens"],
            "dropped": segment["content_tokens_dropped"],
        },
    )

    compression_keys = {
        (str(row["query_id"]), str(row["method_label"]))
        for row in compression_rows
    }
    check(
        "formal_compression_complete",
        compressor["status"] == "COMPLETE"
        and len(compression_rows) == 600
        and len(compression_keys) == 600,
        {"status": compressor["status"], "rows": len(compression_rows)},
    )
    check(
        "compression_structure",
        all(
            row["membership_order_preserved"]
            and not row["empty_output"]
            and row["official_compressed_tokens"] == row["context_tokens"]
            for row in compression_rows
        ),
        {
            "empty_outputs": sum(bool(row["empty_output"]) for row in compression_rows),
            "order_failures": sum(
                not bool(row["membership_order_preserved"]) for row in compression_rows
            ),
        },
    )

    answer_keys = {
        (str(row["query_id"]), str(row["method_label"]))
        for row in answers
    }
    answer_counts = Counter(str(row["method_label"]) for row in answers)
    check(
        "fixed_sample_and_answers",
        len(sample_rows) == 300
        and len(answers) == 1200
        and len(answer_keys) == 1200
        and all(answer_counts[method] == 300 for method in analysis.METHODS),
        {"sample_rows": len(sample_rows), "answers": len(answers), "counts": answer_counts},
    )
    valid_judgments = [row for row in judgments if analysis.valid_judgment(row)]
    judgment_keys = {analysis.judgment_key(row) for row in valid_judgments}
    judgment_counts = Counter(str(row["judge_model"]) for row in valid_judgments)
    check(
        "judgment_keys_unique",
        len(valid_judgments) == len(judgment_keys),
        {"valid": len(valid_judgments), "unique": len(judgment_keys)},
    )
    check(
        "deepseek_complete",
        judgment_counts["deepseek-v4-flash"] == 1200,
        dict(judgment_counts),
    )
    check(
        "execution_manifest_matches",
        execution["answer_count"] == 1200
        and execution["valid_judgments_by_model"]["deepseek-v4-flash"] == 1200,
        execution["status"],
    )

    request_ids = {str(row["request_id"]) for row in requests}
    check(
        "external_handoff_complete",
        len(requests) == 600
        and len(request_ids) == 600
        and handoff["expected_response_count"] == 1200
        and handoff["requests_sha256"]
        == sha256_file(args.downstream_dir / "external_judge_handoff" / "requests.jsonl"),
        {
            "requests": len(requests),
            "expected_responses": handoff["expected_response_count"],
        },
    )
    new_external_coverage = {
        judge: sum(
            key[1] in NEW_METHODS and key[2] == judge
            for key in judgment_keys
        )
        for judge in ("glm-5.2", "minimax-m3")
    }
    external_pending = 1200 - sum(new_external_coverage.values())
    check(
        "external_gap_explicit",
        analysis_payload["status"]
        in {
            "COMPLETE_ANSWERS_PARTIAL_JUDGE_COVERAGE",
            "COMPLETE_THREE_JUDGE_ANALYSIS",
        },
        {
            "analysis_status": analysis_payload["status"],
            "new_external_coverage": new_external_coverage,
            "external_pending": external_pending,
        },
    )

    check(
        "rocm_environment_lock",
        environment["lock_sha256"] == sha256_file(lock_path)
        and environment["gpu"]["device"] == "AMD Radeon RX 9070 XT",
        {
            "recorded_lock": environment["lock_sha256"],
            "actual_lock": sha256_file(lock_path),
        },
    )

    failed = [row for row in checks if not row["passed"]]
    status = (
        "FAIL"
        if failed
        else (
            "PASS_COMPLETE_WITH_RECORDED_PROVIDER_MISSINGNESS"
            if external_pending == 0
            else "PASS_LOCAL_GATE_EXTERNAL_JUDGES_PENDING"
        )
    )
    payload = {
        "status": status,
        "checks": checks,
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "external_judgments_pending": external_pending,
        "new_external_coverage": new_external_coverage,
    }
    write_json(args.output_prefix.with_suffix(".json"), payload)
    lines = [
        "# Task79 Local Validation",
        "",
        f"Status: **{status}**",
        "",
        f"- Checks passed: `{payload['passed']}/{len(checks)}`",
        f"- New external judgments pending: `{external_pending}/1200`",
        "",
        "| Check | Pass | Detail |",
        "|---|---:|---|",
    ]
    for row in checks:
        detail = json.dumps(row["detail"], ensure_ascii=False, sort_keys=True)
        lines.append(f"| {row['name']} | {'yes' if row['passed'] else 'no'} | `{detail}` |")
    lines.append("")
    args.output_prefix.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
