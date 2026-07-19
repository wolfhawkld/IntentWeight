#!/usr/bin/env python3
"""Audit Task79 LLMLingua-2 classifier segments for content truncation.

This reproduces the official ``__chunk_context`` boundary logic and the
``TokenClfDataset`` 512-token packing rule without loading model weights or
calling any API.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

import tiktoken
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

import task79_llmlingua2_matched_compressor as task79


DEFAULT_OUTPUT_PREFIX = (
    task79.RESULTS_DIR / "task79_llmlingua2_segment_audit"
)
MAX_SEQUENCE_TOKENS = 512
SPECIAL_TOKEN_COUNT = 2
MAX_NOMINAL_CONTENT_TOKENS = MAX_SEQUENCE_TOKENS - SPECIAL_TOKEN_COUNT
MAX_CONTENT_RETAINED_BY_DATASET = MAX_SEQUENCE_TOKENS - 1


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def force_token_map(tokenizer) -> dict[str, str]:
    added_tokens = [f"[NEW{index}]" for index in range(100)]
    tokenizer.add_special_tokens({"additional_special_tokens": added_tokens})
    return {
        token: added_tokens[index]
        for index, token in enumerate(task79.OFFICIAL_FORCE_TOKENS)
        if len(tokenizer.tokenize(token)) != 1
    }


def official_segments(
    text: str,
    tokenizer,
    token_map: Mapping[str, str],
) -> list[list[str]]:
    mapped = text
    for original, replacement in token_map.items():
        mapped = mapped.replace(original, replacement)
    chunk_end_tokens = [".", "\n"]
    for token in list(chunk_end_tokens):
        if token in token_map:
            chunk_end_tokens.append(token_map[token])
    boundaries = set(chunk_end_tokens)

    tokens = tokenizer.tokenize(mapped)
    segments: list[list[str]] = []
    start = 0
    while start < len(tokens):
        if start + MAX_NOMINAL_CONTENT_TOKENS > len(tokens) - 1:
            segments.append(tokens[start:])
            break
        end = start + MAX_NOMINAL_CONTENT_TOKENS
        for offset in range(end - start):
            if tokens[end - offset] in boundaries:
                end -= offset
                break
        segments.append(tokens[start : end + 1])
        start = end + 1
    return segments


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-records", type=Path, default=task79.DEFAULT_SAMPLE_RECORDS)
    parser.add_argument("--corpus", type=Path, default=task79.DEFAULT_CORPUS)
    parser.add_argument("--rankings", type=Path, default=task79.DEFAULT_RANKINGS)
    parser.add_argument("--cache-dir", type=Path, default=task79.DEFAULT_CACHE_DIR)
    parser.add_argument("--tiktoken-cache-dir", type=Path, default=task79.DEFAULT_TIKTOKEN_CACHE_DIR)
    parser.add_argument("--model", default=task79.MODEL_NAME)
    parser.add_argument("--model-revision", default=task79.MODEL_REVISION)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(args.tiktoken_cache_dir.resolve()))
    snapshot = Path(
        snapshot_download(
            repo_id=args.model,
            revision=args.model_revision,
            cache_dir=args.cache_dir,
            local_files_only=True,
        )
    ).resolve()
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot,
        local_files_only=True,
        trust_remote_code=False,
    )
    token_map = force_token_map(tokenizer)
    encoding = tiktoken.get_encoding("cl100k_base")

    frozen_records = task79.read_jsonl(args.sample_records)
    corpus = task79.read_json(args.corpus)
    corpus_by_id = {str(row["chunk_id"]): row for row in corpus}
    ranking_payload = task79.read_json(args.rankings)
    rankings = ranking_payload[task79.RANKING_SELECTOR]

    rows: list[dict[str, Any]] = []
    segment_lengths: list[int] = []
    for frozen in frozen_records:
        for endpoint in task79.ENDPOINT_LABELS:
            source, reference, _ = task79.source_and_target(
                frozen,
                endpoint,
                rankings,
                corpus_by_id,
                encoding,
            )
            context_segment_lengths: list[int] = []
            for item in source:
                context_segment_lengths.extend(
                    len(segment)
                    for segment in official_segments(str(item["text"]), tokenizer, token_map)
                )
            dropped_content_tokens = sum(
                max(0, length - MAX_CONTENT_RETAINED_BY_DATASET)
                for length in context_segment_lengths
            )
            segment_lengths.extend(context_segment_lengths)
            rows.append(
                {
                    "query_id": str(frozen["query_id"]),
                    "method_label": endpoint,
                    "source_context_tokens_cl100k": int(reference["base_context_tokens"]),
                    "classifier_segments": len(context_segment_lengths),
                    "max_classifier_content_tokens": max(context_segment_lengths, default=0),
                    "content_tokens_dropped_by_dataset": dropped_content_tokens,
                }
            )

    drop_rows = [row for row in rows if row["content_tokens_dropped_by_dataset"] > 0]
    endpoint_summary: dict[str, Any] = {}
    for endpoint in task79.ENDPOINT_LABELS:
        endpoint_rows = [row for row in rows if row["method_label"] == endpoint]
        endpoint_summary[endpoint] = {
            "queries": len(endpoint_rows),
            "segments": sum(int(row["classifier_segments"]) for row in endpoint_rows),
            "mean_segments_per_query": mean(int(row["classifier_segments"]) for row in endpoint_rows),
            "max_classifier_content_tokens": max(
                int(row["max_classifier_content_tokens"]) for row in endpoint_rows
            ),
            "queries_with_content_truncation": sum(
                int(row["content_tokens_dropped_by_dataset"]) > 0 for row in endpoint_rows
            ),
            "content_tokens_dropped": sum(
                int(row["content_tokens_dropped_by_dataset"]) for row in endpoint_rows
            ),
        }

    payload = {
        "status": "PASS" if not drop_rows else "FAIL",
        "model": args.model,
        "model_revision": args.model_revision,
        "official_repository_commit": task79.OFFICIAL_COMMIT,
        "protocol": {
            "classifier_sequence_limit": MAX_SEQUENCE_TOKENS,
            "official_nominal_content_limit": MAX_NOMINAL_CONTENT_TOKENS,
            "dataset_content_capacity_after_leading_special_token": MAX_CONTENT_RETAINED_BY_DATASET,
            "force_token_map": token_map,
            "chunk_end_tokens": [".", "\n"],
        },
        "contexts_audited": len(rows),
        "segments_audited": len(segment_lengths),
        "max_classifier_content_tokens": max(segment_lengths),
        "segment_length_histogram": dict(sorted(Counter(segment_lengths).items())),
        "contexts_with_content_truncation": len(drop_rows),
        "content_tokens_dropped": sum(
            int(row["content_tokens_dropped_by_dataset"]) for row in rows
        ),
        "endpoints": endpoint_summary,
        "failures": drop_rows,
    }
    write_json(args.output_prefix.with_suffix(".json"), payload)
    lines = [
        "# Task79 LLMLingua-2 Segment Audit",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"- Contexts audited: `{payload['contexts_audited']}`",
        f"- Classifier segments audited: `{payload['segments_audited']}`",
        f"- Maximum classifier content length: `{payload['max_classifier_content_tokens']}` tokens",
        f"- Content tokens dropped at the 512-token dataset boundary: `{payload['content_tokens_dropped']}`",
        "",
        "The Transformers warning concerns full-text token counting. The official compressor "
        "splits each context before classifier inference; this audit verifies the actual packed "
        "segments.",
        "",
    ]
    args.output_prefix.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "contexts": len(rows),
                "segments": len(segment_lengths),
                "max_content_tokens": max(segment_lengths),
                "content_tokens_dropped": payload["content_tokens_dropped"],
            },
            indent=2,
        )
    )
    return 0 if not drop_rows else 1


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
