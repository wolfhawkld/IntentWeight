#!/usr/bin/env python3
"""Task79 official LLMLingua-2 matched-token context materialization.

The script reuses the frozen Task63 query sample and tracked Task38 rankings.
It performs local compression only; it never calls an answer or judge API.
Each result is checkpointed so the 600-context ROCm run can resume safely.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import time
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

import tiktoken
import torch
from huggingface_hub import snapshot_download
from llmlingua import PromptCompressor


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS_DIR = REPO_ROOT / "paper" / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
DATA_DIR = EXPERIMENTS_DIR / "data"

DEFAULT_TASK63_DIR = RESULTS_DIR / "task63_downstream_llm_evaluation"
DEFAULT_SAMPLE_RECORDS = DEFAULT_TASK63_DIR / "sample_records.jsonl"
DEFAULT_CORPUS = DATA_DIR / "processed" / "lotte_technology_search_100k_corpus.json"
DEFAULT_RANKINGS = RESULTS_DIR / "task38_100k_calibrated_context_budget.rankings.json"
DEFAULT_OUTPUT_DIR = RESULTS_DIR / "task79_llmlingua2_matched_compressor"
DEFAULT_CACHE_DIR = DATA_DIR / "hf_cache"
DEFAULT_TIKTOKEN_CACHE_DIR = DATA_DIR / "tiktoken_cache"

MODEL_NAME = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
MODEL_REVISION = "ebaba9b0e874dadd3003ffcff828e4397e568089"
OFFICIAL_REPOSITORY = "https://github.com/microsoft/LLMLingua"
OFFICIAL_COMMIT = "e0e9d99beb94098bbd924aa53c2c112eac41c758"
OFFICIAL_FORCE_TOKENS = ["\n", ".", "!", "?", ","]
RANKING_SELECTOR = "task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4"

DENSE_SOURCE_LABEL = "minilm_dense_top10"
DENSE_REFERENCE_LABEL = "dense_sent_mmr_r0.85_l0.70"
INTENT_REFERENCE_LABEL = "intentweight_sent_mmr_r0.85_l0.70_seed19"
DENSE_ENDPOINT_LABEL = "dense_llmlingua2_matched_sent_mmr"
INTENT_ENDPOINT_LABEL = "intentroute_llmlingua2_matched_sent_mmr_seed19"
REFERENCE_LABELS = (DENSE_REFERENCE_LABEL, INTENT_REFERENCE_LABEL)
ENDPOINT_LABELS = (DENSE_ENDPOINT_LABEL, INTENT_ENDPOINT_LABEL)


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


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def snapshot_file_records(snapshot: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in snapshot.rglob("*") if item.is_file()):
        rows.append(
            {
                "path": path.relative_to(snapshot).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def aggregate_checksum(records: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(str(record["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(record["sha256"]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def method_record(record: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    matches = [method for method in record["methods"] if str(method.get("method_label")) == label]
    if len(matches) != 1:
        raise ValueError(f"Expected one {label!r} method for query {record.get('query_id')}")
    return matches[0]


def context_tokens(context: Sequence[Mapping[str, Any]], encoding: tiktoken.Encoding) -> int:
    return sum(len(encoding.encode(str(item.get("text") or ""))) for item in context)


def context_sha256(context: Sequence[Mapping[str, Any]]) -> str:
    return canonical_sha256(
        [
            {
                "rank": int(item.get("rank") or index),
                "chunk_id": str(item.get("chunk_id") or ""),
                "text": str(item.get("text") or ""),
            }
            for index, item in enumerate(context, 1)
        ]
    )


def build_intent_source(
    query_id: str,
    rankings: Mapping[str, Sequence[str]],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    encoding: tiktoken.Encoding,
) -> list[dict[str, Any]]:
    if query_id not in rankings:
        raise ValueError(f"IntentRoute ranking missing query {query_id}")
    context: list[dict[str, Any]] = []
    for rank, chunk_id in enumerate(rankings[query_id][:10], 1):
        chunk = corpus_by_id.get(str(chunk_id))
        if chunk is None:
            raise ValueError(f"Corpus missing ranked chunk {chunk_id} for {query_id}")
        text = normalize_text(str(chunk.get("text") or ""))
        context.append(
            {
                "rank": rank,
                "chunk_id": str(chunk_id),
                "unit_type": "chunk",
                "token_count": len(encoding.encode(text)),
                "text": text,
            }
        )
    if not context:
        raise ValueError(f"IntentRoute ranking is empty for {query_id}")
    return context


def source_and_target(
    record: Mapping[str, Any],
    endpoint_label: str,
    rankings: Mapping[str, Sequence[str]],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    encoding: tiktoken.Encoding,
) -> tuple[list[dict[str, Any]], Mapping[str, Any], str]:
    if endpoint_label == DENSE_ENDPOINT_LABEL:
        source = [dict(item) for item in method_record(record, DENSE_SOURCE_LABEL)["context"]]
        reference = method_record(record, DENSE_REFERENCE_LABEL)
        source_label = DENSE_SOURCE_LABEL
    elif endpoint_label == INTENT_ENDPOINT_LABEL:
        source = build_intent_source(
            str(record["query_id"]), rankings, corpus_by_id, encoding
        )
        reference = method_record(record, INTENT_REFERENCE_LABEL)
        source_label = RANKING_SELECTOR
    else:
        raise ValueError(f"Unknown endpoint {endpoint_label}")

    measured = context_tokens(source, encoding)
    tracked = int(reference["base_context_tokens"])
    if measured != tracked:
        raise ValueError(
            f"Source-token mismatch for {record['query_id']} / {endpoint_label}: "
            f"measured={measured}, tracked={tracked}"
        )
    target = int(reference["context_tokens"])
    if not 0 < target <= measured:
        raise ValueError(
            f"Invalid matched target for {record['query_id']} / {endpoint_label}: "
            f"target={target}, source={measured}"
        )
    return source, reference, source_label


def protocol_payload(args: argparse.Namespace, model_checksum: str) -> dict[str, Any]:
    return {
        "task": "Task79",
        "sample_records_sha256": sha256_file(args.sample_records),
        "corpus_sha256": sha256_file(args.corpus),
        "rankings_sha256": sha256_file(args.rankings),
        "ranking_selector": RANKING_SELECTOR,
        "model": args.model,
        "model_revision": args.model_revision,
        "model_aggregate_sha256": model_checksum,
        "repository_commit": OFFICIAL_COMMIT,
        "dense_source_label": DENSE_SOURCE_LABEL,
        "dense_reference_label": DENSE_REFERENCE_LABEL,
        "intent_reference_label": INTENT_REFERENCE_LABEL,
        "endpoint_labels": list(ENDPOINT_LABELS),
        "target_policy": "per-query exact tracked Sentence-MMR context_tokens",
        "use_context_level_filter": False,
        "use_token_level_filter": True,
        "force_tokens": OFFICIAL_FORCE_TOKENS,
        "force_reserve_digit": True,
        "drop_consecutive": True,
        "chunk_end_tokens": [".", "\n"],
        "encoding": "cl100k_base",
    }


def load_checkpoints(
    path: Path,
    *,
    signature: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    completed: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_jsonl(path):
        if str(row.get("protocol_signature")) != signature:
            raise ValueError(
                f"Checkpoint protocol mismatch in {path}; use a fresh output directory"
            )
        key = (str(row.get("query_id")), str(row.get("method_label")))
        if key in completed:
            raise ValueError(f"Duplicate checkpoint key in {path}: {key}")
        completed[key] = row
    return completed


def validate_checkpoint(
    row: Mapping[str, Any],
    source: Sequence[Mapping[str, Any]],
    target_tokens: int,
) -> None:
    if str(row.get("source_context_sha256")) != context_sha256(source):
        raise ValueError(
            f"Checkpoint source mismatch for {row.get('query_id')} / {row.get('method_label')}"
        )
    if int(row.get("target_context_tokens") or -1) != target_tokens:
        raise ValueError(
            f"Checkpoint target mismatch for {row.get('query_id')} / {row.get('method_label')}"
        )
    compressed = row.get("context") or []
    source_ids = [str(item.get("chunk_id") or "") for item in source]
    output_ids = [str(item.get("chunk_id") or "") for item in compressed]
    if source_ids != output_ids or len(source) != len(compressed):
        raise ValueError(
            f"Checkpoint context membership/order mismatch for {row.get('query_id')} / "
            f"{row.get('method_label')}"
        )


def compress_context(
    compressor: PromptCompressor,
    record: Mapping[str, Any],
    endpoint_label: str,
    source: Sequence[Mapping[str, Any]],
    reference: Mapping[str, Any],
    source_label: str,
    encoding: tiktoken.Encoding,
    protocol_signature: str,
) -> dict[str, Any]:
    texts = [str(item.get("text") or "") for item in source]
    source_token_total = context_tokens(source, encoding)
    target_token_total = int(reference["context_tokens"])

    start = time.perf_counter()
    with torch.inference_mode():
        result = compressor.compress_prompt_llmlingua2(
            texts,
            rate=1.0,
            target_token=target_token_total,
            use_context_level_filter=False,
            use_token_level_filter=True,
            force_tokens=OFFICIAL_FORCE_TOKENS,
            force_reserve_digit=True,
            drop_consecutive=True,
            chunk_end_tokens=[".", "\n"],
        )
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    compressed_texts = [str(text) for text in result.get("compressed_prompt_list", [])]
    if len(compressed_texts) != len(source):
        raise RuntimeError(
            f"LLMLingua-2 changed context-list length for {record['query_id']} / "
            f"{endpoint_label}: {len(source)} -> {len(compressed_texts)}"
        )

    compressed_context: list[dict[str, Any]] = []
    for source_item, text in zip(source, compressed_texts):
        compressed_context.append(
            {
                "rank": int(source_item["rank"]),
                "chunk_id": str(source_item["chunk_id"]),
                "unit_type": "llmlingua2_chunk",
                "source_token_count": int(source_item["token_count"]),
                "token_count": len(encoding.encode(text)),
                "text": text,
            }
        )

    output_tokens = context_tokens(compressed_context, encoding)
    official_origin = int(result.get("origin_tokens", -1))
    official_output = int(result.get("compressed_tokens", -1))
    if official_origin != source_token_total:
        raise RuntimeError(
            f"Official source-token mismatch for {record['query_id']} / {endpoint_label}: "
            f"official={official_origin}, cl100k={source_token_total}"
        )
    if official_output != output_tokens:
        raise RuntimeError(
            f"Official output-token mismatch for {record['query_id']} / {endpoint_label}: "
            f"official={official_output}, cl100k={output_tokens}"
        )

    source_ids = [str(item["chunk_id"]) for item in source]
    output_ids = [str(item["chunk_id"]) for item in compressed_context]
    return {
        "protocol_signature": protocol_signature,
        "query_id": str(record["query_id"]),
        "method_label": endpoint_label,
        "source_label": source_label,
        "matched_reference_method": str(reference["method_label"]),
        "source_context_sha256": context_sha256(source),
        "source_context_tokens": source_token_total,
        "tracked_base_context_tokens": int(reference["base_context_tokens"]),
        "target_context_tokens": target_token_total,
        "context_tokens": output_tokens,
        "target_error_tokens": output_tokens - target_token_total,
        "target_absolute_error_tokens": abs(output_tokens - target_token_total),
        "retained_percent": 100.0 * output_tokens / source_token_total,
        "saving_percent": 100.0 * (1.0 - output_tokens / source_token_total),
        "compression_seconds": elapsed,
        "source_context_count": len(source),
        "compressed_context_count": len(compressed_context),
        "empty_compressed_contexts": sum(not item["text"].strip() for item in compressed_context),
        "empty_output": output_tokens == 0,
        "source_chunk_ids": source_ids,
        "context_chunk_ids": output_ids,
        "membership_order_preserved": source_ids == output_ids,
        "compressed_context_sha256": context_sha256(compressed_context),
        "official_origin_tokens": official_origin,
        "official_compressed_tokens": official_output,
        "context": compressed_context,
    }


def evidence_recall(ranking: Sequence[str], ground_truth: set[str]) -> float:
    if not ground_truth:
        return 0.0
    return len(ground_truth.intersection(ranking[:10])) / len(ground_truth)


def materialize_sample_records(
    frozen_records: Sequence[Mapping[str, Any]],
    compressed: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for frozen in frozen_records:
        query_id = str(frozen["query_id"])
        ground_truth = {str(item) for item in frozen["ground_truth_chunk_ids"]}
        methods = [dict(method_record(frozen, label)) for label in REFERENCE_LABELS]
        for endpoint in ENDPOINT_LABELS:
            item = compressed[(query_id, endpoint)]
            ranking = [str(value) for value in item["context_chunk_ids"]]
            methods.append(
                {
                    "method_label": endpoint,
                    "method_kind": "llmlingua2",
                    "source_label": (
                        "MiniLM Dense top-10 plus official LLMLingua-2"
                        if endpoint == DENSE_ENDPOINT_LABEL
                        else "MiniLM IntentRoute seed 19 plus official LLMLingua-2"
                    ),
                    "run_id": f"task79:{endpoint}:{item['protocol_signature'][:12]}",
                    "selector": RANKING_SELECTOR if endpoint == INTENT_ENDPOINT_LABEL else None,
                    "ratio": float(item["context_tokens"]) / float(item["source_context_tokens"]),
                    "mmr_lambda": None,
                    "hit_at_10": bool(ground_truth.intersection(ranking[:10])),
                    "evidence_recall_at_10": evidence_recall(ranking, ground_truth),
                    "context_tokens": int(item["context_tokens"]),
                    "context_chunk_ids": ranking,
                    "selected_sentence_count": 0,
                    "budget_tokens": int(item["target_context_tokens"]),
                    "base_context_tokens": int(item["source_context_tokens"]),
                    "matched_reference_method": str(item["matched_reference_method"]),
                    "target_error_tokens": int(item["target_error_tokens"]),
                    "compression_seconds": float(item["compression_seconds"]),
                    "compressor": {
                        "name": MODEL_NAME,
                        "revision": MODEL_REVISION,
                        "repository_commit": OFFICIAL_COMMIT,
                    },
                    "context": item["context"],
                }
            )
        rows.append(
            {
                "query_id": query_id,
                "query_text": frozen["query_text"],
                "ground_truth_chunk_ids": frozen["ground_truth_chunk_ids"],
                "reference_evidence": frozen["reference_evidence"],
                "methods": methods,
            }
        )
    return rows


def summarize_endpoint(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    source_tokens = [int(row["source_context_tokens"]) for row in rows]
    targets = [int(row["target_context_tokens"]) for row in rows]
    outputs = [int(row["context_tokens"]) for row in rows]
    errors = [output - target for output, target in zip(outputs, targets)]
    relative_errors = [
        100.0 * error / target for error, target in zip(errors, targets)
    ]
    seconds = [float(row["compression_seconds"]) for row in rows]
    return {
        "queries": len(rows),
        "source_context_tokens_total": sum(source_tokens),
        "target_context_tokens_total": sum(targets),
        "actual_context_tokens_total": sum(outputs),
        "mean_source_context_tokens": mean(source_tokens),
        "mean_target_context_tokens": mean(targets),
        "mean_actual_context_tokens": mean(outputs),
        "actual_saving_percent_vs_source": 100.0 * (1.0 - sum(outputs) / sum(source_tokens)),
        "target_saving_percent_vs_source": 100.0 * (1.0 - sum(targets) / sum(source_tokens)),
        "mean_target_error_tokens": mean(errors),
        "mean_absolute_target_error_tokens": mean(abs(value) for value in errors),
        "max_absolute_target_error_tokens": max(abs(value) for value in errors),
        "mean_absolute_target_error_percent": mean(
            abs(value) for value in relative_errors
        ),
        "max_absolute_target_error_percent": max(
            abs(value) for value in relative_errors
        ),
        "exact_target_matches": sum(value == 0 for value in errors),
        "within_5_tokens": sum(abs(value) <= 5 for value in errors),
        "within_1_percent_of_target": sum(
            abs(error) / target <= 0.01 for error, target in zip(errors, targets)
        ),
        "within_5_percent_of_target": sum(
            abs(error) / target <= 0.05 for error, target in zip(errors, targets)
        ),
        "compression_seconds_total": sum(seconds),
        "mean_compression_seconds": mean(seconds),
        "empty_outputs": sum(bool(row["empty_output"]) for row in rows),
        "empty_compressed_contexts": sum(int(row["empty_compressed_contexts"]) for row in rows),
        "membership_order_preserved": all(bool(row["membership_order_preserved"]) for row in rows),
    }


def render_summary(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Task79 LLMLingua-2 Matched Compressor",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"- Fixed queries: `{payload['query_count']}`",
        f"- Completed compressed contexts: `{payload['completed_contexts']}/{payload['expected_contexts']}`",
        f"- Device: `{payload['environment']['device_name']}`",
        f"- Peak allocated VRAM: `{payload['environment']['peak_allocated_vram_bytes'] / 2**30:.3f} GiB`",
        f"- Protocol signature: `{payload['protocol_signature']}`",
        "",
        "| Endpoint | Queries | Source tokens | Target tokens | Actual tokens | "
        "Saving | Mean abs target error | Mean latency |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ENDPOINT_LABELS:
        row = payload["endpoints"].get(label)
        if not row:
            continue
        lines.append(
            f"| {label} | {row['queries']} | {row['source_context_tokens_total']} | "
            f"{row['target_context_tokens_total']} | {row['actual_context_tokens_total']} | "
            f"{row['actual_saving_percent_vs_source']:.2f}% | "
            f"{row['mean_absolute_target_error_tokens']:.2f} | "
            f"{row['mean_compression_seconds']:.3f}s |"
        )
    lines.extend(
        [
            "",
            "The matched targets are frozen Task63 Sentence-MMR token counts. No answer or judge API is called here.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-records", type=Path, default=DEFAULT_SAMPLE_RECORDS)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--rankings", type=Path, default=DEFAULT_RANKINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--tiktoken-cache-dir", type=Path, default=DEFAULT_TIKTOKEN_CACHE_DIR)
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--model-revision", default=MODEL_REVISION)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument(
        "--max-contexts",
        type=int,
        default=0,
        help="Optional smoke limit. Zero runs all 600 frozen contexts.",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    if args.model != MODEL_NAME or args.model_revision != MODEL_REVISION:
        raise ValueError(
            "Task79 formal execution is provenance-frozen to "
            f"{MODEL_NAME}@{MODEL_REVISION}"
        )
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("ROCm/CUDA-compatible torch device is unavailable")
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(args.tiktoken_cache_dir.resolve()))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    previous_summary_path = args.output_dir / "compression_summary.json"
    previous_summary = read_json(previous_summary_path) if previous_summary_path.exists() else {}

    snapshot = Path(
        snapshot_download(
            repo_id=args.model,
            revision=args.model_revision,
            cache_dir=args.cache_dir,
            local_files_only=True,
        )
    ).resolve()
    model_files = snapshot_file_records(snapshot)
    model_checksum = aggregate_checksum(model_files)
    protocol = protocol_payload(args, model_checksum)
    signature = canonical_sha256(protocol)

    frozen_records = read_jsonl(args.sample_records)
    if len(frozen_records) != 300:
        raise ValueError(f"Expected the fixed 300 Task63 records, got {len(frozen_records)}")
    query_ids = [str(row["query_id"]) for row in frozen_records]
    if len(set(query_ids)) != len(query_ids):
        raise ValueError("Task63 sample contains duplicate query IDs")

    corpus = read_json(args.corpus)
    corpus_by_id = {str(row["chunk_id"]): row for row in corpus}
    ranking_payload = read_json(args.rankings)
    rankings = ranking_payload.get(RANKING_SELECTOR)
    if not isinstance(rankings, Mapping):
        raise ValueError(f"Ranking selector missing: {RANKING_SELECTOR}")
    encoding = tiktoken.get_encoding("cl100k_base")

    checkpoint_path = args.output_dir / "compression_records.jsonl"
    completed = load_checkpoints(checkpoint_path, signature=signature)
    expected_keys = {(query_id, label) for query_id in query_ids for label in ENDPOINT_LABELS}
    unexpected = set(completed) - expected_keys
    if unexpected:
        raise ValueError(f"Unexpected checkpoint keys: {sorted(unexpected)[:3]}")

    pending: list[tuple[Mapping[str, Any], str, list[dict[str, Any]], Mapping[str, Any], str]] = []
    for frozen in frozen_records:
        for endpoint in ENDPOINT_LABELS:
            source, reference, source_label = source_and_target(
                frozen, endpoint, rankings, corpus_by_id, encoding
            )
            key = (str(frozen["query_id"]), endpoint)
            if key in completed:
                validate_checkpoint(completed[key], source, int(reference["context_tokens"]))
            else:
                pending.append((frozen, endpoint, source, reference, source_label))

    if args.max_contexts > 0:
        pending = pending[: args.max_contexts]

    model_load_seconds = 0.0
    if pending:
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
        compressor.model.eval()
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        model_load_seconds = time.perf_counter() - load_start

        for index, (frozen, endpoint, source, reference, source_label) in enumerate(pending, 1):
            row = compress_context(
                compressor,
                frozen,
                endpoint,
                source,
                reference,
                source_label,
                encoding,
                signature,
            )
            append_jsonl(checkpoint_path, row)
            completed[(str(frozen["query_id"]), endpoint)] = row
            if args.progress_every > 0 and (index % args.progress_every == 0 or index == len(pending)):
                print(
                    f"[compressed {index}/{len(pending)}; "
                    f"total {len(completed)}/{len(expected_keys)}]",
                    flush=True,
                )

    complete = set(completed) == expected_keys
    if complete:
        sample_records = materialize_sample_records(frozen_records, completed)
        write_jsonl(args.output_dir / "sample_records.jsonl", sample_records)

    endpoint_summaries: dict[str, Any] = {}
    for endpoint in ENDPOINT_LABELS:
        endpoint_rows = [
            completed[(query_id, endpoint)]
            for query_id in query_ids
            if (query_id, endpoint) in completed
        ]
        if endpoint_rows:
            endpoint_summaries[endpoint] = summarize_endpoint(endpoint_rows)

    current_peak_allocated = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0
    current_peak_reserved = int(torch.cuda.max_memory_reserved()) if torch.cuda.is_available() else 0
    previous_environment = previous_summary.get("environment", {})
    previous_peak_allocated = int(previous_environment.get("peak_allocated_vram_bytes") or 0)
    previous_peak_reserved = int(previous_environment.get("peak_reserved_vram_bytes") or 0)
    previous_load_seconds = float(
        previous_environment.get("model_load_seconds_max_observed")
        or previous_environment.get("model_load_seconds_this_run")
        or 0.0
    )
    payload = {
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "query_count": len(frozen_records),
        "expected_contexts": len(expected_keys),
        "completed_contexts": len(completed),
        "protocol_signature": signature,
        "protocol": protocol,
        "provenance": {
            "repository": OFFICIAL_REPOSITORY,
            "repository_commit": OFFICIAL_COMMIT,
            "package_version": importlib.metadata.version("llmlingua"),
            "model": args.model,
            "model_revision": args.model_revision,
            "model_license": "MIT",
            "model_snapshot_files": model_files,
            "model_aggregate_sha256": model_checksum,
        },
        "environment": {
            "python": platform.python_version(),
            "torch_version": torch.__version__,
            "hip_version": torch.version.hip,
            "transformers_version": importlib.metadata.version("transformers"),
            "device_requested": args.device,
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
            "model_load_seconds_this_run": model_load_seconds,
            "model_load_seconds_max_observed": max(model_load_seconds, previous_load_seconds),
            "peak_allocated_vram_bytes": max(current_peak_allocated, previous_peak_allocated),
            "peak_reserved_vram_bytes": max(current_peak_reserved, previous_peak_reserved),
        },
        "endpoints": endpoint_summaries,
    }
    write_json(args.output_dir / "compression_summary.json", payload)
    (args.output_dir / "compression_summary.md").write_text(
        render_summary(payload), encoding="utf-8"
    )
    write_json(args.output_dir / "run_config.json", payload["protocol"])
    print(
        json.dumps(
            {
                "status": payload["status"],
                "completed_contexts": len(completed),
                "expected_contexts": len(expected_keys),
                "output_dir": str(args.output_dir),
            },
            indent=2,
        )
    )
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
