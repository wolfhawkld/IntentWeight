#!/usr/bin/env python3
"""Task79 official LLMLingua-2 ROCm preflight.

This command never calls an answer or judge API. It loads the provenance-pinned
official compressor, exercises fixed Task63 contexts twice, and records device,
determinism, token-accounting, latency, and peak-memory evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import tiktoken
import torch
from huggingface_hub import snapshot_download
from llmlingua import PromptCompressor


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SAMPLE_RECORDS = (
    REPO_ROOT
    / "paper"
    / "experiments"
    / "results"
    / "task63_downstream_llm_evaluation"
    / "sample_records.jsonl"
)
DEFAULT_OUTPUT_PREFIX = (
    REPO_ROOT
    / "paper"
    / "experiments"
    / "results"
    / "task79_llmlingua2_preflight"
)
DEFAULT_CACHE_DIR = REPO_ROOT / "paper" / "experiments" / "data" / "hf_cache"
DEFAULT_TIKTOKEN_CACHE_DIR = REPO_ROOT / "paper" / "experiments" / "data" / "tiktoken_cache"
DEFAULT_MODEL = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
DEFAULT_MODEL_REVISION = "ebaba9b0e874dadd3003ffcff828e4397e568089"
OFFICIAL_REPOSITORY = "https://github.com/microsoft/LLMLingua"
OFFICIAL_COMMIT = "e0e9d99beb94098bbd924aa53c2c112eac41c758"
MODEL_LICENSE = "MIT"
OFFICIAL_FORCE_TOKENS = ["\n", ".", "!", "?", ","]
SOURCE_METHOD = "minilm_dense_top10"


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


def snapshot_file_records(snapshot: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(item for item in snapshot.rglob("*") if item.is_file()):
        records.append(
            {
                "path": path.relative_to(snapshot).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def aggregate_checksum(records: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(str(record["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(record["sha256"]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def method_record(record: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    matches = [item for item in record["methods"] if str(item.get("method_label")) == label]
    if len(matches) != 1:
        raise ValueError(f"Expected one {label!r} record for query {record.get('query_id')}")
    return matches[0]


def select_fixed_cases(records: Sequence[Mapping[str, Any]], count: int) -> list[Mapping[str, Any]]:
    if count < 1:
        raise ValueError("pilot case count must be positive")
    ordered = sorted(
        records,
        key=lambda record: (
            int(method_record(record, SOURCE_METHOD)["context_tokens"]),
            str(record["query_id"]),
        ),
    )
    if count == 1:
        indices = [len(ordered) // 2]
    else:
        indices = [round(index * (len(ordered) - 1) / (count - 1)) for index in range(count)]
    return [ordered[index] for index in dict.fromkeys(indices)]


def compress_once(
    compressor: PromptCompressor,
    texts: Sequence[str],
    *,
    rate: float,
) -> tuple[dict[str, Any], float]:
    start = time.perf_counter()
    result = compressor.compress_prompt_llmlingua2(
        list(texts),
        rate=rate,
        use_context_level_filter=False,
        use_token_level_filter=True,
        force_tokens=OFFICIAL_FORCE_TOKENS,
        force_reserve_digit=True,
        drop_consecutive=True,
        chunk_end_tokens=[".", "\n"],
    )
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return result, time.perf_counter() - start


def render_markdown(payload: Mapping[str, Any]) -> str:
    status = payload["status"]
    device = payload["environment"]
    lines = [
        "# Task79 LLMLingua-2 ROCm Preflight",
        "",
        f"Status: **{status}**",
        "",
        f"- Official repository commit: `{payload['provenance']['repository_commit']}`",
        f"- Model revision: `{payload['provenance']['model_revision']}`",
        f"- Model aggregate SHA256: `{payload['provenance']['model_aggregate_sha256']}`",
        f"- Device: `{device['device_name']}`",
        f"- PyTorch / HIP: `{device['torch_version']}` / `{device['hip_version']}`",
        f"- Model load time: `{payload['model_load_seconds']:.3f}s`",
        f"- Peak allocated VRAM: `{payload['peak_allocated_vram_bytes'] / (1024 ** 3):.3f} GiB`",
        "",
        "| Query | Source tokens | Compressed tokens | Saving | First run | Repeat exact |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["cases"]:
        lines.append(
            f"| {row['query_id']} | {row['source_tokens']} | {row['compressed_tokens']} | "
            f"{row['saving_percent']:.2f}% | {row['first_seconds']:.3f}s | "
            f"{'yes' if row['repeat_exact'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "No answer generation or LLM judging is performed by this preflight.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-records", type=Path, default=DEFAULT_SAMPLE_RECORDS)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--tiktoken-cache-dir", type=Path, default=DEFAULT_TIKTOKEN_CACHE_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-revision", default=DEFAULT_MODEL_REVISION)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--rate", type=float, default=0.85)
    parser.add_argument("--pilot-cases", type=int, default=3)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    if not 0.0 < args.rate <= 1.0:
        raise ValueError("rate must be in (0, 1]")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("ROCm/CUDA-compatible torch device is unavailable")
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(args.tiktoken_cache_dir.resolve()))

    snapshot = Path(
        snapshot_download(
            repo_id=args.model,
            revision=args.model_revision,
            cache_dir=args.cache_dir,
            local_files_only=True,
        )
    ).resolve()
    model_files = snapshot_file_records(snapshot)
    if not model_files:
        raise RuntimeError(f"Pinned model snapshot is empty: {snapshot}")

    records = read_jsonl(args.sample_records)
    cases = select_fixed_cases(records, args.pilot_cases)
    encoding = tiktoken.get_encoding("cl100k_base")

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
    load_start = time.perf_counter()
    compressor = PromptCompressor(
        model_name=args.model,
        device_map=args.device,
        use_llmlingua2=True,
        model_config={
            "revision": args.model_revision,
            "cache_dir": str(args.cache_dir),
            "local_files_only": True,
            "trust_remote_code": False,
        },
    )
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    load_seconds = time.perf_counter() - load_start
    model_device = str(next(compressor.model.parameters()).device)

    output_rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for record in cases:
        source = method_record(record, SOURCE_METHOD)
        texts = [str(item["text"]) for item in source["context"]]
        source_tokens = sum(len(encoding.encode(text)) for text in texts)
        first, first_seconds = compress_once(compressor, texts, rate=args.rate)
        second, second_seconds = compress_once(compressor, texts, rate=args.rate)
        first_list = [str(item) for item in first.get("compressed_prompt_list", [])]
        second_list = [str(item) for item in second.get("compressed_prompt_list", [])]
        compressed_tokens = sum(len(encoding.encode(text)) for text in first_list)
        repeat_exact = first_list == second_list and first.get("compressed_prompt") == second.get("compressed_prompt")
        list_length_ok = len(first_list) == len(texts)
        token_accounting_exact = compressed_tokens == int(first.get("compressed_tokens", -1))
        if not repeat_exact:
            failures.append(f"non-deterministic output for {record['query_id']}")
        if not list_length_ok:
            failures.append(f"context-list length changed for {record['query_id']}")
        if not token_accounting_exact:
            failures.append(f"cl100k token accounting mismatch for {record['query_id']}")
        output_rows.append(
            {
                "query_id": str(record["query_id"]),
                "source_contexts": len(texts),
                "source_tokens": source_tokens,
                "compressed_contexts": len(first_list),
                "compressed_tokens": compressed_tokens,
                "official_reported_compressed_tokens": int(first.get("compressed_tokens", -1)),
                "saving_percent": 100.0 * (1.0 - compressed_tokens / source_tokens),
                "first_seconds": first_seconds,
                "repeat_seconds": second_seconds,
                "repeat_exact": repeat_exact,
                "context_list_length_preserved": list_length_ok,
                "token_accounting_exact": token_accounting_exact,
                "compressed_sha256": hashlib.sha256(
                    json.dumps(first_list, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
        )

    peak_allocated = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0
    peak_reserved = int(torch.cuda.max_memory_reserved()) if torch.cuda.is_available() else 0
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "provenance": {
            "repository": OFFICIAL_REPOSITORY,
            "repository_commit": OFFICIAL_COMMIT,
            "package_version": importlib.metadata.version("llmlingua"),
            "code_license": "MIT",
            "model": args.model,
            "model_revision": args.model_revision,
            "model_license": MODEL_LICENSE,
            "model_snapshot_files": model_files,
            "model_aggregate_sha256": aggregate_checksum(model_files),
        },
        "environment": {
            "python": platform.python_version(),
            "torch_version": torch.__version__,
            "hip_version": torch.version.hip,
            "transformers_version": importlib.metadata.version("transformers"),
            "accelerate_version": importlib.metadata.version("accelerate"),
            "nltk_version": importlib.metadata.version("nltk"),
            "tiktoken_version": importlib.metadata.version("tiktoken"),
            "device_requested": args.device,
            "model_device": model_device,
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        },
        "protocol": {
            "source_sample_records": str(args.sample_records),
            "source_method": SOURCE_METHOD,
            "rate": args.rate,
            "force_tokens": OFFICIAL_FORCE_TOKENS,
            "force_reserve_digit": True,
            "drop_consecutive": True,
            "chunk_end_tokens": [".", "\n"],
            "tiktoken_cache_files": snapshot_file_records(args.tiktoken_cache_dir.resolve()),
            "pilot_case_selection": "source-token quantiles with query-id tie break",
        },
        "model_load_seconds": load_seconds,
        "peak_allocated_vram_bytes": peak_allocated,
        "peak_reserved_vram_bytes": peak_reserved,
        "cases": output_rows,
    }
    json_path = args.output_prefix.with_suffix(".json")
    md_path = args.output_prefix.with_suffix(".md")
    write_json(json_path, payload)
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
