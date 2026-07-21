#!/usr/bin/env python3
"""Build a secret-free Task79 answer/judge execution manifest."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "paper" / "experiments" / "results"
DEFAULT_INPUT_DIR = RESULTS_DIR / "task79_llmlingua2_downstream_evaluation"
JUDGES = ("deepseek-v4-flash", "glm-5.2", "minimax-m3")
REFERENCE_METHODS = (
    "dense_sent_mmr_r0.85_l0.70",
    "intentweight_sent_mmr_r0.85_l0.70_seed19",
)
NEW_METHODS = (
    "dense_llmlingua2_matched_sent_mmr",
    "intentroute_llmlingua2_matched_sent_mmr_seed19",
)
METHODS = (*REFERENCE_METHODS, *NEW_METHODS)


def load_task63_module():
    path = SCRIPT_DIR / "task63_downstream_llm_evaluation.py"
    spec = importlib.util.spec_from_file_location("task79_task63_manifest_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Task63 prompt contract: {path}")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def usage_value(usage: Mapping[str, Any], candidates: Iterable[str]) -> int:
    for key in candidates:
        value = usage.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    return 0


def usage_summary(rows: Iterable[Mapping[str, Any]], usage_key: str) -> dict[str, int]:
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    for row in rows:
        usage = row.get(usage_key)
        if not isinstance(usage, Mapping):
            continue
        input_tokens += usage_value(usage, ("prompt_tokens", "input_tokens"))
        output_tokens += usage_value(usage, ("completion_tokens", "output_tokens"))
        total_tokens += usage_value(usage, ("total_tokens",))
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens or input_tokens + output_tokens,
    }


def failure_code(row: Mapping[str, Any]) -> str:
    message = str(row.get("error_message") or "")
    for code in ("SensitiveContentDetected", "AuthenticationError", "RateLimitError"):
        if code in message:
            return code
    if row.get("provider_error") or row.get("error"):
        return "provider_rejection"
    if not isinstance(row.get("judge_json"), Mapping):
        return "invalid_or_empty_judge_output"
    return str(row.get("error_type") or row.get("import_failure") or "unknown_failure")


def parse_caps(value: str) -> list[int]:
    caps = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not caps or any(cap <= 0 for cap in caps):
        raise ValueError("Judge output caps must be positive comma-separated integers")
    return caps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--judge-output-caps-attempted", default="900,1800")
    parser.add_argument("--answer-output-cap", type=int, default=900)
    parser.add_argument("--concurrency", type=int, default=4)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    task63 = load_task63_module()
    sample_path = args.input_dir / "sample_records.jsonl"
    answer_path = args.input_dir / "answers.jsonl"
    judgment_path = args.input_dir / "judgments.jsonl"
    failure_path = args.input_dir / "judgment_failures.jsonl"
    external_failure_path = args.input_dir / "external_judgment_failures.jsonl"
    sample_records = read_jsonl(sample_path)
    answers = read_jsonl(answer_path)
    judgments = read_jsonl(judgment_path)
    failures = [*read_jsonl(failure_path), *read_jsonl(external_failure_path)]

    answer_keys = {
        (str(row.get("query_id")), str(row.get("method_label")))
        for row in answers
    }
    if len(answer_keys) != len(answers):
        raise ValueError("Duplicate Task79 answer keys")
    valid_judgments = [row for row in judgments if task63.valid_judgment(row)]
    judgment_keys = {
        (
            str(row.get("query_id")),
            str(row.get("method_label")),
            str(row.get("judge_model")),
        )
        for row in valid_judgments
    }
    if len(judgment_keys) != len(valid_judgments):
        raise ValueError("Duplicate valid Task79 judgment keys")

    answer_counts = Counter(str(row.get("method_label")) for row in answers)
    judgment_counts = Counter(str(row.get("judge_model")) for row in valid_judgments)
    usage_by_answer_method = {
        method: usage_summary(
            (row for row in answers if str(row.get("method_label")) == method),
            "generation_usage",
        )
        for method in METHODS
    }
    usage_by_judge: dict[str, dict[str, int]] = {}
    for judge in JUDGES:
        usage_by_judge[judge] = usage_summary(
            (row for row in valid_judgments if str(row.get("judge_model")) == judge),
            "judge_usage",
        )

    failure_keys: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in failures:
        key = (
            str(row.get("query_id")),
            str(row.get("method_label")),
            str(row.get("judge_model")),
        )
        failure_keys[key].append(row)
    recovered = set(failure_keys).intersection(judgment_keys)

    caps = parse_caps(args.judge_output_caps_attempted)
    deepseek_complete = judgment_counts.get("deepseek-v4-flash", 0) == 1200
    new_external_coverage = {
        judge: sum(
            str(row.get("method_label")) in NEW_METHODS
            and str(row.get("judge_model")) == judge
            for row in valid_judgments
        )
        for judge in ("glm-5.2", "minimax-m3")
    }
    new_external_complete = all(count == 600 for count in new_external_coverage.values())
    all_three_judges_complete = all(judgment_counts.get(judge, 0) == 1200 for judge in JUDGES)
    legacy_missing_count = sum(
        (query_id, method, judge) not in judgment_keys
        for query_id, method in answer_keys
        if method in REFERENCE_METHODS
        for judge in JUDGES
    )
    payload = {
        "status": (
            "COMPLETE_ALL_THREE_JUDGE_COVERAGE"
            if all_three_judges_complete
            else "COMPLETE_TASK79_NEW_ENDPOINT_JUDGING_WITH_RECORDED_LEGACY_MISSINGNESS"
            if deepseek_complete and new_external_complete
            else "LOCAL_DEEPSEEK_COMPLETE_EXTERNAL_JUDGES_PENDING"
            if deepseek_complete
            else "LOCAL_DEEPSEEK_IN_PROGRESS"
        ),
        "sample_query_count": len(sample_records),
        "answer_count": len(answers),
        "answer_counts_by_method": dict(sorted(answer_counts.items())),
        "valid_judgment_count": len(valid_judgments),
        "valid_judgments_by_model": dict(sorted(judgment_counts.items())),
        "new_external_coverage": new_external_coverage,
        "new_external_complete": new_external_complete,
        "all_three_judges_complete": all_three_judges_complete,
        "legacy_missing_count": legacy_missing_count,
        "provider": {
            "answer_and_local_judge": "DeepSeek OpenAI-compatible API",
            "base_url": "https://api.deepseek.com",
            "answer_model": "deepseek-v4-flash",
            "local_judge_model": "deepseek-v4-flash",
            "external_judges": ["glm-5.2", "minimax-m3"],
            "credentials_recorded": False,
        },
        "execution_contract": {
            "api_mode": "chat-completions",
            "temperature": 0.0,
            "thinking": "enabled",
            "answer_output_cap": args.answer_output_cap,
            "judge_output_caps_attempted": caps,
            "answer_retries_per_invocation": 1,
            "judge_retries_per_invocation": 1,
            "concurrency": args.concurrency,
            "generation_instructions_sha256": text_sha256(task63.GENERATION_INSTRUCTIONS),
            "judge_instructions_sha256": text_sha256(task63.JUDGE_INSTRUCTIONS),
            "prompt_implementation": (
                "paper/experiments/scripts/task63_downstream_llm_evaluation.py"
            ),
        },
        "artifact_origin": {
            "reused_answer_methods": list(REFERENCE_METHODS),
            "new_answer_methods": list(NEW_METHODS),
            "new_answer_calls_expected": 600,
            "existing_answers_regenerated": False,
        },
        "usage_by_answer_method": usage_by_answer_method,
        "usage_by_judge": usage_by_judge,
        "failure_attempt_count": len(failures),
        "failure_codes": dict(Counter(failure_code(row) for row in failures)),
        "failure_unique_key_count": len(failure_keys),
        "recovered_failure_key_count": len(recovered),
        "source_sha256": {
            "sample_records.jsonl": sha256_file(sample_path),
            "answers.jsonl": sha256_file(answer_path),
            "judgments.jsonl": sha256_file(judgment_path),
            **(
                {"judgment_failures.jsonl": sha256_file(failure_path)}
                if failure_path.exists()
                else {}
            ),
            **(
                {"external_judgment_failures.jsonl": sha256_file(external_failure_path)}
                if external_failure_path.exists()
                else {}
            ),
        },
        "secret_policy": ".env and API keys are excluded from every tracked artifact",
    }
    write_json(args.input_dir / "llm_execution_manifest.json", payload)
    lines = [
        "# Task79 LLM Execution Manifest",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"- Answers: `{len(answers)}/1200`",
        f"- DeepSeek judgments: `{judgment_counts.get('deepseek-v4-flash', 0)}/1200`",
        f"- GLM-5.2 judgments: `{judgment_counts.get('glm-5.2', 0)}/1200`",
        f"- MiniMax-M3 judgments: `{judgment_counts.get('minimax-m3', 0)}/1200`",
        f"- New-endpoint GLM-5.2 coverage: `{new_external_coverage['glm-5.2']}/600`",
        f"- New-endpoint MiniMax-M3 coverage: `{new_external_coverage['minimax-m3']}/600`",
        f"- Failure attempts retained: `{len(failures)}`; recovered keys: `{len(recovered)}`",
        "",
        "The 600 Sentence-MMR answers are reused. Only the 600 LLMLingua-2 answers are newly generated.",
        (
            "Both new LLMLingua-2 endpoints and both reused Sentence-MMR endpoints have complete three-judge coverage."
            if legacy_missing_count == 0
            else (
                "Both new LLMLingua-2 endpoints have complete three-judge coverage. "
                f"Historical Sentence-MMR judgments still missing: {legacy_missing_count}; none are imputed."
            )
        ),
        "Credentials and API keys are not recorded.",
        "",
    ]
    (args.input_dir / "llm_execution_manifest.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "answers": len(answers),
                "deepseek_judgments": judgment_counts.get("deepseek-v4-flash", 0),
                "failure_attempts": len(failures),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
