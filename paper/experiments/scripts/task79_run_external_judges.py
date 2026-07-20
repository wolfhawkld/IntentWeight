#!/usr/bin/env python3
"""Run the frozen Task79 GLM/MiniMax handoff with resumable checkpoints.

Only the 600 new LLMLingua-2 answer prompts in the frozen handoff are eligible.
Existing valid judgment keys are skipped, and each newly valid judgment is
appended immediately to the canonical Task79 judgment artifact.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "paper" / "experiments" / "results"
DEFAULT_INPUT_DIR = RESULTS_DIR / "task79_llmlingua2_downstream_evaluation"
DEFAULT_HANDOFF_DIR = DEFAULT_INPUT_DIR / "external_judge_handoff"
DEFAULT_SUMMARY = DEFAULT_HANDOFF_DIR / "direct_run_summary.json"
ALLOWED_JUDGES = ("glm-5.2", "minimax-m3")
THREAD_LOCAL = threading.local()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


task63 = load_module(
    "task79_task63_runtime",
    SCRIPT_DIR / "task63_downstream_llm_evaluation.py",
)
handoff = load_module(
    "task79_external_handoff_runtime",
    SCRIPT_DIR / "task79_external_judge_handoff.py",
)


def parse_csv(value: str) -> list[str]:
    values = [item.strip() for item in value.split(",") if item.strip()]
    unknown = sorted(set(values) - set(ALLOWED_JUDGES))
    if unknown:
        raise ValueError(f"Unsupported Task79 judges: {unknown}")
    if not values:
        raise ValueError("At least one judge is required")
    return values


def client_for_thread(args: argparse.Namespace):
    client = getattr(THREAD_LOCAL, "client", None)
    if client is None:
        from openai import OpenAI

        client = OpenAI(
            api_key=args.api_key,
            base_url=args.base_url,
            timeout=args.timeout,
            max_retries=0,
        )
        THREAD_LOCAL.client = client
    return client


def usage_dict(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    return dict(usage)


def call_judge(
    request: Mapping[str, Any],
    judge_model: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    last_error: BaseException | None = None
    last_text = ""
    last_usage: dict[str, Any] = {}
    for attempt in range(args.retries + 1):
        try:
            response = client_for_thread(args).chat.completions.create(
                model=judge_model,
                messages=[
                    {"role": "system", "content": str(request["system_prompt"])},
                    {"role": "user", "content": str(request["user_prompt"])},
                ],
                max_tokens=args.max_output_tokens,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            last_text = str(response.choices[0].message.content or "")
            last_usage = usage_dict(response)
            parsed = task63.try_parse_json(last_text)
            row = {
                "query_id": str(request["query_id"]),
                "method_label": str(request["method_label"]),
                "judge_model": judge_model,
                "judge_text": last_text,
                "judge_json": parsed,
                "judge_usage": last_usage,
            }
            if task63.valid_judgment(row):
                return {"ok": True, "row": row, "request_id": request["request_id"]}
            last_error = ValueError("response did not satisfy the frozen Task79 judge schema")
        except Exception as exc:  # Provider errors are retained without prompts or credentials.
            last_error = exc
        if attempt < args.retries:
            time.sleep(args.retry_sleep)
    return {
        "ok": False,
        "failure": {
            "request_id": str(request["request_id"]),
            "query_id": str(request["query_id"]),
            "method_label": str(request["method_label"]),
            "judge_model": judge_model,
            "failure_stage": "external_judgment",
            "error_type": type(last_error).__name__ if last_error else "InvalidJudgment",
            "error_message": str(last_error or "invalid judgment")[:2000],
            "response_chars": len(last_text),
            "judge_usage": last_usage,
        },
    }


def run(args: argparse.Namespace) -> int:
    if args.provider_config:
        import yaml

        config = yaml.safe_load(args.provider_config.read_text(encoding="utf-8"))
        provider = (config.get("providers") or {}).get(args.provider_name) or {}
        args.api_key = args.api_key or provider.get("api_key")
        args.base_url = args.base_url or provider.get("base_url")
    args.api_key = args.api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY")
    args.base_url = args.base_url or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
    if not args.api_key or not args.base_url:
        raise RuntimeError(
            "Set OPENAI_COMPATIBLE_API_KEY and OPENAI_COMPATIBLE_BASE_URL "
            "or pass --api-key/--base-url"
        )

    requests = handoff.read_jsonl(args.handoff_dir / "requests.jsonl")
    if len(requests) != 600:
        raise ValueError(f"Expected the frozen 600-request handoff, got {len(requests)}")
    judgments_path = args.input_dir / "judgments.jsonl"
    failures_path = args.input_dir / "external_judgment_failures.jsonl"
    task63.sanitize_judgments(judgments_path, args.input_dir / "judgment_failures.jsonl")
    existing = task63.read_jsonl(judgments_path)
    existing_keys = {
        (str(row.get("query_id")), str(row.get("method_label")), str(row.get("judge_model")))
        for row in existing
        if task63.valid_judgment(row)
    }
    judges = parse_csv(args.judges)
    pending = [
        (request, judge)
        for request in requests
        for judge in judges
        if (str(request["query_id"]), str(request["method_label"]), judge) not in existing_keys
    ]
    initial_pending = len(pending)
    if args.max_pending > 0:
        pending = pending[: args.max_pending]

    valid = 0
    failed = 0
    if pending:
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
            futures = {
                executor.submit(call_judge, request, judge, args): (request, judge)
                for request, judge in pending
            }
            for processed, future in enumerate(as_completed(futures), 1):
                result = future.result()
                if result["ok"]:
                    row = result["row"]
                    key = (str(row["query_id"]), str(row["method_label"]), str(row["judge_model"]))
                    if key not in existing_keys:
                        task63.append_jsonl(judgments_path, row)
                        existing_keys.add(key)
                    valid += 1
                else:
                    task63.append_jsonl(failures_path, result["failure"])
                    failed += 1
                if args.progress_every > 0 and (
                    processed % args.progress_every == 0 or processed == len(pending)
                ):
                    print(
                        f"[task79 external processed={processed}/{len(pending)} "
                        f"valid={valid} failed={failed}]",
                        flush=True,
                    )

    remaining_by_judge = {
        judge: sum(
            (str(request["query_id"]), str(request["method_label"]), judge) not in existing_keys
            for request in requests
        )
        for judge in judges
    }
    summary = {
        "status": "COMPLETE" if not any(remaining_by_judge.values()) else "RESUMABLE_INCOMPLETE",
        "frozen_request_count": len(requests),
        "judges": judges,
        "initial_pending": initial_pending,
        "scheduled_this_run": len(pending),
        "valid_this_run": valid,
        "failed_this_run": failed,
        "remaining_by_judge": remaining_by_judge,
        "credential_material_recorded": False,
    }
    task63.write_json(args.summary, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failed else 2


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--handoff-dir", type=Path, default=DEFAULT_HANDOFF_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--judges", default=",".join(ALLOWED_JUDGES))
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--provider-config", type=Path, default=None)
    parser.add_argument("--provider-name", default="volcengine-agent-plan")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-pending", type=int, default=0)
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-sleep", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--progress-every", type=int, default=25)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
