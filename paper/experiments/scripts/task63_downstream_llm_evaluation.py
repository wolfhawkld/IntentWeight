#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task63 expanded downstream LLM evaluation.

This script upgrades the Task33.5 60-query smoke test into a reproducible
answer-level RAG evaluation over a frozen Task38 test split. The default mode is
a dry-run preflight: it materializes the 300-query sample, retrieved contexts,
prompt previews, and retrieval/token statistics without calling an LLM endpoint.

Use ``--execute`` only when a valid provider API key is available. Execution is
resumable through ``answers.jsonl`` and ``judgments.jsonl``.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, NamedTuple, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"
DEFAULT_OUTPUT_DIR = DEFAULT_RESULTS_DIR / "task63_downstream_llm_evaluation"


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


context_token_cost = _load_script_module("context_token_cost", SCRIPT_DIR / "context_token_cost.py")
retrieval_metrics = context_token_cost.retrieval_metrics
task38 = _load_script_module("task38_calibrated_context_budget", SCRIPT_DIR / "task38_calibrated_context_budget.py")
task46 = _load_script_module("task46_sentence_mmr_baseline", SCRIPT_DIR / "task46_sentence_mmr_baseline.py")
dense_baseline = task46.dense_baseline
THREAD_LOCAL = threading.local()


class MethodSpec(NamedTuple):
    label: str
    kind: str
    ranking_path: Path
    selector: str | None = None
    ratio: float | None = None
    mmr_lambda: float | None = None
    source_label: str = ""


class LoadedMethod(NamedTuple):
    spec: MethodSpec
    variant: Any


DEFAULT_METHODS: tuple[MethodSpec, ...] = (
    MethodSpec(
        label="minilm_dense_top10",
        kind="chunk",
        ranking_path=DEFAULT_RESULTS_DIR / "dense_lotte_technology_search_100k_rankings.json",
        source_label="MiniLM dense top-10",
    ),
    MethodSpec(
        label="bge_dense_top10",
        kind="chunk",
        ranking_path=DEFAULT_RESULTS_DIR / "task52_bge_base_100k_dense" / "dense_lotte_technology_search_100k_rankings.json",
        source_label="BGE-base dense top-10",
    ),
    MethodSpec(
        label="bge_intentweight_positive_seed19",
        kind="chunk",
        ranking_path=DEFAULT_RESULTS_DIR / "task54_bge_base_100k_positive_hit_context_budget.rankings.json",
        selector="task53_bge:full_multi_route:seed19:token_budget_r0.97_m4",
        source_label="BGE-base positive IntentRoute, seed 19",
    ),
    MethodSpec(
        label="e5_dense_top10",
        kind="chunk",
        ranking_path=DEFAULT_RESULTS_DIR / "task53_e5_base_100k_dense" / "dense_lotte_technology_search_100k_rankings.json",
        source_label="E5-base dense top-10",
    ),
    MethodSpec(
        label="e5_intentweight_full_seed19",
        kind="chunk",
        ranking_path=DEFAULT_RESULTS_DIR / "task53_e5_base_100k_full_context_budget.rankings.json",
        selector="task53_e5:full_multi_route:seed19:token_budget_r0.88_m7",
        source_label="E5-base full multi-route IntentRoute, seed 19",
    ),
    MethodSpec(
        label="dense_sent_mmr_r0.85_l0.70",
        kind="sent_mmr",
        ranking_path=DEFAULT_RESULTS_DIR / "dense_lotte_technology_search_100k_rankings.json",
        ratio=0.85,
        mmr_lambda=0.70,
        source_label="MiniLM dense top-10 plus sentence MMR",
    ),
    MethodSpec(
        label="intentweight_sent_mmr_r0.85_l0.70_seed19",
        kind="sent_mmr",
        ranking_path=DEFAULT_RESULTS_DIR / "task38_100k_calibrated_context_budget.rankings.json",
        selector="task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4",
        ratio=0.85,
        mmr_lambda=0.70,
        source_label="MiniLM IntentRoute seed 19 plus sentence MMR",
    ),
)


GENERATION_INSTRUCTIONS = """You answer technology support questions using only the provided retrieved context.

Rules:
- Answer the user question directly and concisely.
- Use only facts supported by the retrieved context.
- If the context is insufficient, state that the retrieved context is insufficient.
- Cite supporting chunk ids in a `citations` list. Use chunk ids exactly as shown.
- Return one strict JSON object with keys: answer, citations, insufficient_context.
"""


JUDGE_INSTRUCTIONS = """You evaluate one RAG answer for a technology support question.

Use the reference evidence, the retrieved context, and the answer. Do not reward unsupported claims.
Return one strict JSON object with keys:
- correctness_score: integer 1-5
- faithfulness_score: integer 1-5
- relevance_score: integer 1-5
- citation_support_score: integer 1-5
- is_correct: boolean
- is_faithful: boolean
- citations_supported: boolean
- insufficient_context_appropriate: boolean
- unsupported_claims: boolean
- rationale: short explanation
"""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_env_file(path: Path | None) -> None:
    if path is None or not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def query_id(record: Mapping[str, Any]) -> str:
    return context_token_cost.query_id(record)


def chunk_id(record: Mapping[str, Any]) -> str:
    return context_token_cost.chunk_id(record)


def ground_truth(query: Mapping[str, Any]) -> set[str]:
    return retrieval_metrics._ground_truth(query)


def text_of(record: Mapping[str, Any]) -> str:
    return str(record.get("text", ""))


def stable_hash_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def normalize_selector(value: str | None) -> str | None:
    return value.strip() if value and value.strip() else None


def select_variant(spec: MethodSpec):
    variants = context_token_cost.load_ranking_variants(spec.label, spec.ranking_path)
    selector = normalize_selector(spec.selector)
    if selector:
        matches = [
            variant for variant in variants
            if selector == str(variant.method) or selector in str(variant.run_id)
        ]
    else:
        matches = list(variants)
    if len(matches) != 1:
        available = ", ".join(str(variant.run_id) for variant in variants[:20])
        raise ValueError(
            f"Method {spec.label} expected exactly one ranking variant, got {len(matches)}. "
            f"selector={selector!r}; available={available}"
        )
    return matches[0]


def loaded_default_methods() -> List[LoadedMethod]:
    return [LoadedMethod(spec=spec, variant=select_variant(spec)) for spec in DEFAULT_METHODS]


def load_methods_from_json(path: Path) -> List[LoadedMethod]:
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Method config must be a JSON list: {path}")
    methods: List[LoadedMethod] = []
    for item in data:
        spec = MethodSpec(
            label=str(item["label"]),
            kind=str(item["kind"]),
            ranking_path=Path(str(item["ranking_path"])),
            selector=item.get("selector"),
            ratio=float(item["ratio"]) if item.get("ratio") is not None else None,
            mmr_lambda=float(item["mmr_lambda"]) if item.get("mmr_lambda") is not None else None,
            source_label=str(item.get("source_label") or item["label"]),
        )
        methods.append(LoadedMethod(spec=spec, variant=select_variant(spec)))
    return methods


def choose_frozen_test_queries(
    queries: Sequence[Mapping[str, Any]],
    methods: Sequence[LoadedMethod],
    *,
    scale: str,
    calibration_fraction: float,
    split_salt: str,
    sample_salt: str,
    max_queries: int,
) -> tuple[List[Mapping[str, Any]], Dict[str, Any]]:
    calibration, test = task38.split_queries(
        queries,
        calibration_fraction=calibration_fraction,
        salt=f"{split_salt}:{scale}",
    )
    available_by_method = {
        method.spec.label: {str(qid) for qid in method.variant.rankings.keys()}
        for method in methods
    }
    common_qids = set.intersection(*available_by_method.values()) if available_by_method else set()
    eligible = [
        query for query in test
        if ground_truth(query) and query_id(query) in common_qids
    ]
    eligible.sort(key=lambda query: stable_hash_int(f"{sample_salt}:{query_id(query)}"))
    selected = eligible[:max_queries]
    metadata = {
        "scale": scale,
        "calibration_fraction": calibration_fraction,
        "split_salt": split_salt,
        "calibration_query_count": len(calibration),
        "frozen_test_query_count": len(test),
        "eligible_common_frozen_test_queries": len(eligible),
        "selected_query_count": len(selected),
        "max_queries": max_queries,
        "sample_salt": sample_salt,
        "available_query_counts_by_method": {
            label: len(qids) for label, qids in available_by_method.items()
        },
    }
    if len(selected) < max_queries:
        metadata["selection_warning"] = (
            f"Only {len(selected)} eligible frozen-test queries were available for all methods."
        )
    return selected, metadata


def build_token_counter(args: argparse.Namespace):
    return context_token_cost.build_token_counter(args.tokenizer, args.encoding)


def chunk_token_map(corpus: Sequence[Mapping[str, Any]], count_tokens) -> Dict[str, int]:
    return {chunk_id(chunk): int(count_tokens(text_of(chunk))) for chunk in corpus}


def truncate_text(text: str, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if limit <= 0 or len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 15)].rstrip() + " ...[truncated]"


def build_chunk_context(
    ranking: Sequence[str],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
    max_chunk_chars: int,
) -> List[Dict[str, Any]]:
    context: List[Dict[str, Any]] = []
    for rank, cid in enumerate(ranking[:top_k], start=1):
        chunk = corpus_by_id.get(str(cid))
        if not chunk:
            continue
        context.append({
            "rank": rank,
            "chunk_id": str(cid),
            "unit_type": "chunk",
            "token_count": int(chunk_tokens.get(str(cid), 0)),
            "text": truncate_text(text_of(chunk), max_chunk_chars),
        })
    return context


def format_context(context: Sequence[Mapping[str, Any]]) -> str:
    blocks: List[str] = []
    for idx, item in enumerate(context, start=1):
        unit = str(item.get("unit_type") or "chunk")
        chunk = str(item.get("chunk_id") or "")
        token_count = int(item.get("token_count") or 0)
        if unit == "sentence":
            sentence_index = item.get("sentence_index", "")
            blocks.append(
                f"[{idx}] chunk_id={chunk} sentence_index={sentence_index} tokens={token_count}\n"
                f"{item.get('text', '')}"
            )
        else:
            rank = item.get("rank", idx)
            blocks.append(f"[{idx}] rank={rank} chunk_id={chunk} tokens={token_count}\n{item.get('text', '')}")
    return "\n\n".join(blocks)


def reference_evidence(
    gt_ids: Sequence[str],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    *,
    max_refs: int,
    max_chunk_chars: int,
) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for rank, cid in enumerate(gt_ids[:max_refs], start=1):
        chunk = corpus_by_id.get(str(cid))
        if not chunk:
            continue
        refs.append({
            "rank": rank,
            "chunk_id": str(cid),
            "unit_type": "reference_chunk",
            "text": truncate_text(text_of(chunk), max_chunk_chars),
        })
    return refs


def format_reference_evidence(refs: Sequence[Mapping[str, Any]]) -> str:
    blocks = []
    for item in refs:
        blocks.append(f"[GT-{item['rank']}] chunk_id={item['chunk_id']}\n{item['text']}")
    return "\n\n".join(blocks)


def has_hit(ranking: Sequence[str], gt: set[str], k: int) -> bool:
    return bool(gt.intersection(str(item) for item in ranking[:k]))


def evidence_recall(ranking: Sequence[str], gt: set[str], k: int) -> float:
    return retrieval_metrics.evidence_recall_at_k([str(item) for item in ranking], gt, k)


def chunk_ids_from_context(context: Sequence[Mapping[str, Any]]) -> List[str]:
    seen: set[str] = set()
    ids: List[str] = []
    for item in context:
        cid = str(item.get("chunk_id") or "")
        if cid and cid not in seen:
            ids.append(cid)
            seen.add(cid)
    return ids


def context_token_total(context: Sequence[Mapping[str, Any]]) -> int:
    return int(sum(int(item.get("token_count") or 0) for item in context))


def materialize_chunk_methods(
    queries: Sequence[Mapping[str, Any]],
    methods: Sequence[LoadedMethod],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    chunk_tokens: Mapping[str, int],
    *,
    top_k: int,
    max_chunk_chars: int,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    materialized: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for method in methods:
        if method.spec.kind != "chunk":
            continue
        by_qid: Dict[str, Dict[str, Any]] = {}
        for query in queries:
            qid = query_id(query)
            ranking = [str(item) for item in method.variant.rankings.get(qid, [])]
            context = build_chunk_context(
                ranking,
                corpus_by_id,
                chunk_tokens,
                top_k=top_k,
                max_chunk_chars=max_chunk_chars,
            )
            by_qid[qid] = {
                "ranking": chunk_ids_from_context(context),
                "context": context,
                "context_tokens": context_token_total(context),
                "selected_sentences": 0,
            }
        materialized[method.spec.label] = by_qid
    return materialized


def materialize_sent_mmr_methods(
    queries: Sequence[Mapping[str, Any]],
    methods: Sequence[LoadedMethod],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    chunk_tokens: Mapping[str, int],
    count_tokens,
    *,
    top_k: int,
    model_name: str,
    batch_size: int,
    device: str,
    local_files_only: bool,
    max_sentence_tokens: int,
    max_chunk_chars: int,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    sent_methods = [method for method in methods if method.spec.kind == "sent_mmr"]
    if not sent_methods:
        return {}

    sentence_texts_by_method: Dict[str, List[str]] = {}
    all_sentence_texts: Dict[str, None] = {}
    for method in sent_methods:
        texts = task46.collect_unique_sentence_texts(
            queries,
            method.variant.rankings,
            corpus_by_id,
            count_tokens=count_tokens,
            top_k=top_k,
            max_sentence_tokens=max_sentence_tokens,
        )
        sentence_texts_by_method[method.spec.label] = texts
        for text in texts:
            all_sentence_texts.setdefault(text, None)

    sentence_texts = list(all_sentence_texts.keys())
    if sentence_texts:
        encoder = dense_baseline.load_sentence_transformer(
            model_name,
            device=device,
            local_files_only=local_files_only,
        )
        sentence_embeddings = dense_baseline.encode_texts(encoder, sentence_texts, batch_size=batch_size)
        query_embeddings = dense_baseline.encode_texts(
            encoder,
            [text_of(query) for query in queries],
            batch_size=batch_size,
        )
    else:
        sentence_embeddings = np.zeros((0, 1), dtype=np.float32)
        query_embeddings = np.zeros((len(queries), 1), dtype=np.float32)

    sentence_text_to_index = {text: idx for idx, text in enumerate(sentence_texts)}
    query_embeddings_by_qid = {
        query_id(query): query_embeddings[idx]
        for idx, query in enumerate(queries)
    }

    materialized: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for method in sent_methods:
        if method.spec.ratio is None or method.spec.mmr_lambda is None:
            raise ValueError(f"SentMMR method needs ratio and mmr_lambda: {method.spec.label}")
        candidates_by_qid = task46.build_candidates(
            queries,
            method.variant.rankings,
            corpus_by_id,
            sentence_text_to_index,
            count_tokens=count_tokens,
            top_k=top_k,
            max_sentence_tokens=max_sentence_tokens,
        )
        by_qid: Dict[str, Dict[str, Any]] = {}
        for query in queries:
            qid = query_id(query)
            base_ranking = [str(item) for item in method.variant.rankings.get(qid, [])[:top_k]]
            base_tokens = int(sum(chunk_tokens.get(cid, 0) for cid in base_ranking))
            budget = int(math.floor(float(base_tokens) * float(method.spec.ratio)))
            selected = task46.select_mmr_sentences(
                candidates_by_qid.get(qid, []),
                query_embeddings_by_qid[qid],
                sentence_embeddings,
                budget_tokens=budget,
                mmr_lambda=float(method.spec.mmr_lambda),
            )
            context = [
                {
                    "rank": idx,
                    "chunk_id": sentence.chunk_id,
                    "unit_type": "sentence",
                    "dense_rank": int(sentence.dense_rank),
                    "sentence_index": int(sentence.sentence_index),
                    "token_count": int(sentence.token_count),
                    "query_score": float(sentence.query_score),
                    "mmr_score": float(sentence.mmr_score),
                    "text": truncate_text(sentence.text, max_chunk_chars),
                }
                for idx, sentence in enumerate(selected, start=1)
            ]
            by_qid[qid] = {
                "ranking": task46.dedupe_chunk_ranking(selected),
                "context": context,
                "context_tokens": context_token_total(context),
                "selected_sentences": len(selected),
                "budget_tokens": budget,
                "base_context_tokens": base_tokens,
            }
        materialized[method.spec.label] = by_qid
    return materialized


def materialize_records(
    queries: Sequence[Mapping[str, Any]],
    methods: Sequence[LoadedMethod],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    chunk_tokens: Mapping[str, int],
    count_tokens,
    args: argparse.Namespace,
) -> List[Dict[str, Any]]:
    contexts = materialize_chunk_methods(
        queries,
        methods,
        corpus_by_id,
        chunk_tokens,
        top_k=args.top_k,
        max_chunk_chars=args.max_chunk_chars,
    )
    contexts.update(materialize_sent_mmr_methods(
        queries,
        methods,
        corpus_by_id,
        chunk_tokens,
        count_tokens,
        top_k=args.top_k,
        model_name=args.sent_mmr_model,
        batch_size=args.batch_size,
        device=args.device,
        local_files_only=args.local_files_only,
        max_sentence_tokens=args.max_sentence_tokens,
        max_chunk_chars=args.max_chunk_chars,
    ))

    rows: List[Dict[str, Any]] = []
    for query in queries:
        qid = query_id(query)
        gt = sorted(ground_truth(query))
        method_rows: List[Dict[str, Any]] = []
        for method in methods:
            item = contexts[method.spec.label][qid]
            ranking = [str(value) for value in item["ranking"]]
            method_rows.append({
                "method_label": method.spec.label,
                "method_kind": method.spec.kind,
                "source_label": method.spec.source_label or method.spec.label,
                "run_id": str(method.variant.run_id),
                "selector": method.spec.selector,
                "ratio": method.spec.ratio,
                "mmr_lambda": method.spec.mmr_lambda,
                "hit_at_10": has_hit(ranking, set(gt), args.top_k),
                "evidence_recall_at_10": evidence_recall(ranking, set(gt), args.top_k),
                "context_tokens": int(item["context_tokens"]),
                "context_chunk_ids": chunk_ids_from_context(item["context"]),
                "selected_sentence_count": int(item.get("selected_sentences") or 0),
                "budget_tokens": item.get("budget_tokens"),
                "base_context_tokens": item.get("base_context_tokens"),
                "context": item["context"],
            })
        rows.append({
            "query_id": qid,
            "query_text": text_of(query),
            "ground_truth_chunk_ids": gt,
            "reference_evidence": reference_evidence(
                gt,
                corpus_by_id,
                max_refs=args.max_reference_chunks,
                max_chunk_chars=args.max_reference_chunk_chars,
            ),
            "methods": method_rows,
        })
    return rows


def generation_prompt(query_text: str, context: Sequence[Mapping[str, Any]]) -> str:
    return f"Question:\n{query_text}\n\nRetrieved context:\n{format_context(context)}\n"


def judge_prompt(record: Mapping[str, Any], answer_text: str, answer_json: Any) -> str:
    return (
        f"Question:\n{record['query_text']}\n\n"
        f"Reference evidence:\n{format_reference_evidence(record['reference_evidence'])}\n\n"
        f"Retrieved context:\n{format_context(record['context'])}\n\n"
        f"Generated answer text:\n{answer_text}\n\n"
        f"Parsed generated answer JSON:\n{json.dumps(answer_json, ensure_ascii=False, sort_keys=True)}\n"
    )


def try_parse_json(text: str) -> Any:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def response_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)
    parts: List[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            value = getattr(content, "text", None)
            if value:
                parts.append(str(value))
    return "\n".join(parts)


def credential_status(args: argparse.Namespace) -> Dict[str, Any]:
    if args.provider == "azure":
        endpoint = args.azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        key = args.api_key or os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        return {"provider": args.provider, "has_key": bool(key), "has_endpoint": bool(endpoint)}
    if args.provider == "deepseek":
        key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
        base_url = args.base_url or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
        return {"provider": args.provider, "has_key": bool(key), "has_base_url": bool(base_url)}
    if args.provider == "compatible":
        key = args.api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = args.base_url or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
        return {"provider": args.provider, "has_key": bool(key), "has_base_url": bool(base_url)}
    key = args.api_key or os.environ.get("OPENAI_API_KEY")
    return {"provider": args.provider, "has_key": bool(key)}


def validate_credentials(args: argparse.Namespace) -> None:
    status = credential_status(args)
    missing = [key for key, value in status.items() if key.startswith("has_") and not value]
    if missing:
        raise RuntimeError(f"Cannot execute LLM evaluation; missing credential fields: {missing}. status={status}")


def create_client(args: argparse.Namespace) -> Any:
    from openai import AzureOpenAI, OpenAI

    if args.provider == "azure":
        endpoint = args.azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = args.api_key or os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=args.azure_api_version,
        )
    if args.provider in {"compatible", "deepseek"}:
        base_url = args.base_url
        api_key = args.api_key
        if args.provider == "deepseek":
            base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
            api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        else:
            base_url = base_url or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
            api_key = api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY") or os.environ.get("OPENAI_API_KEY")
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=args.api_key or os.environ.get("OPENAI_API_KEY"))


def call_responses(client: Any, *, model: str, instructions: str, prompt: str, args: argparse.Namespace) -> tuple[str, Dict[str, Any]]:
    request: Dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": prompt,
        "max_output_tokens": args.max_output_tokens,
        "temperature": args.temperature,
        "store": False,
        "metadata": {"task": "task63_downstream_llm_evaluation"},
    }
    if args.reasoning_effort:
        request["reasoning"] = {"effort": args.reasoning_effort}
    response = client.responses.create(**request)
    usage = getattr(response, "usage", None)
    usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else dict(usage or {})
    return response_text(response), usage_dict


def call_chat_completions(client: Any, *, model: str, instructions: str, prompt: str, args: argparse.Namespace) -> tuple[str, Dict[str, Any]]:
    request: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
    }
    if args.provider in {"compatible", "deepseek"}:
        request["max_tokens"] = args.max_output_tokens
    else:
        request["max_completion_tokens"] = args.max_output_tokens
    if not (args.provider == "deepseek" and args.thinking == "enabled"):
        request["temperature"] = args.temperature
    if args.response_format_json:
        request["response_format"] = {"type": "json_object"}
    if args.provider == "deepseek" and args.thinking:
        request["extra_body"] = {"thinking": {"type": args.thinking}}
        if args.reasoning_effort:
            request["reasoning_effort"] = args.reasoning_effort
    response = client.chat.completions.create(**request)
    text = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else dict(usage or {})
    return text, usage_dict


def call_model(
    client: Any,
    *,
    model: str,
    instructions: str,
    prompt: str,
    args: argparse.Namespace,
) -> tuple[str, Dict[str, Any]]:
    selected_model = args.azure_deployment if args.provider == "azure" and args.azure_deployment else model
    if args.api_mode == "chat-completions":
        return call_chat_completions(client, model=selected_model, instructions=instructions, prompt=prompt, args=args)
    return call_responses(client, model=selected_model, instructions=instructions, prompt=prompt, args=args)


def normalize_citations(answer_json: Any) -> List[str]:
    if not isinstance(answer_json, Mapping):
        return []
    raw = answer_json.get("citations") or []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, Sequence):
        return []
    citations: List[str] = []
    for item in raw:
        if isinstance(item, Mapping):
            value = item.get("chunk_id") or item.get("id") or item.get("citation")
        else:
            value = item
        if value is not None:
            citations.append(str(value).strip())
    return [value for value in citations if value]


def answer_insufficient(answer_json: Any) -> bool:
    if not isinstance(answer_json, Mapping):
        return False
    return bool(answer_json.get("insufficient_context"))


def strict_citation_check(answer_json: Any, *, context_chunk_ids: Sequence[str], ground_truth_ids: Sequence[str]) -> Dict[str, Any]:
    citations = normalize_citations(answer_json)
    context_set = {str(value) for value in context_chunk_ids}
    gt_set = {str(value) for value in ground_truth_ids}
    in_context = bool(citations) and all(citation in context_set for citation in citations)
    hits_ground_truth = bool(gt_set.intersection(citations))
    return {
        "citation_count": len(citations),
        "citations": citations,
        "citations_all_in_context": in_context,
        "citations_hit_ground_truth": hits_ground_truth,
        "strict_citation_support": bool(in_context and hits_ground_truth),
        "insufficient_context": answer_insufficient(answer_json),
    }


def flatten_method_records(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for row in rows:
        for method in row["methods"]:
            flattened.append({
                "query_id": row["query_id"],
                "query_text": row["query_text"],
                "ground_truth_chunk_ids": row["ground_truth_chunk_ids"],
                "reference_evidence": row["reference_evidence"],
                **method,
            })
    return flattened


def existing_answer_keys(path: Path) -> set[tuple[str, str]]:
    keys = set()
    for row in read_jsonl(path):
        keys.add((str(row.get("query_id")), str(row.get("method_label"))))
    return keys


def existing_judgment_keys(path: Path) -> set[tuple[str, str, str]]:
    keys = set()
    for row in read_jsonl(path):
        if valid_judgment(row):
            keys.add((str(row.get("query_id")), str(row.get("method_label")), str(row.get("judge_model"))))
    return keys


JUDGE_REQUIRED_KEYS = {
    "correctness_score",
    "faithfulness_score",
    "relevance_score",
    "citation_support_score",
    "is_correct",
    "is_faithful",
    "citations_supported",
    "insufficient_context_appropriate",
    "unsupported_claims",
    "rationale",
}


def valid_judgment(row: Mapping[str, Any]) -> bool:
    parsed = row.get("judge_json")
    return isinstance(parsed, Mapping) and JUDGE_REQUIRED_KEYS.issubset(parsed)


def sanitize_judgments(path: Path, failure_path: Path) -> None:
    rows = read_jsonl(path)
    if not rows:
        return
    valid_by_key: Dict[tuple[str, str, str], Dict[str, Any]] = {}
    failures: List[Dict[str, Any]] = []
    for row in rows:
        key = (str(row.get("query_id")), str(row.get("method_label")), str(row.get("judge_model")))
        if valid_judgment(row):
            valid_by_key[key] = row
        else:
            failures.append(row)
    if failures or len(valid_by_key) != len(rows):
        write_jsonl(path, valid_by_key.values())
    if failures:
        write_jsonl(failure_path, [*read_jsonl(failure_path), *failures])


def method_preflight_rows(records: Sequence[Mapping[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    by_method: Dict[str, List[Mapping[str, Any]]] = {}
    for record in flatten_method_records(records):
        by_method.setdefault(str(record["method_label"]), []).append(record)

    baseline_tokens = 0.0
    baseline_hit = 0.0
    if args.baseline_method in by_method:
        baseline_records = by_method[args.baseline_method]
        baseline_tokens = mean(float(record["context_tokens"]) for record in baseline_records)
        baseline_hit = mean(float(bool(record["hit_at_10"])) for record in baseline_records)

    rows: List[Dict[str, Any]] = []
    for label, values in by_method.items():
        avg_tokens = mean(float(record["context_tokens"]) for record in values)
        hit = mean(float(bool(record["hit_at_10"])) for record in values)
        evidence = mean(float(record["evidence_recall_at_10"]) for record in values)
        rows.append({
            "method_label": label,
            "num_queries": len(values),
            "hit@10": hit,
            "hit_delta_vs_baseline@10": hit - baseline_hit,
            "evidence_recall@10": evidence,
            "avg_context_tokens@10": avg_tokens,
            "context_token_ratio_vs_baseline@10": avg_tokens / baseline_tokens if baseline_tokens > 0 else 0.0,
            "context_token_saving_percent_vs_baseline@10": (1.0 - avg_tokens / baseline_tokens) * 100.0 if baseline_tokens > 0 else 0.0,
            "avg_selected_sentences@10": mean(float(record.get("selected_sentence_count") or 0) for record in values),
        })
    return sorted(rows, key=lambda row: str(row["method_label"]))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> List[str]:
    if not rows:
        return []
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values: List[str] = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_preflight_summary(
    output_dir: Path,
    records: Sequence[Mapping[str, Any]],
    sample_metadata: Mapping[str, Any],
    methods: Sequence[LoadedMethod],
    args: argparse.Namespace,
) -> None:
    rows = method_preflight_rows(records, args)
    write_csv(output_dir / "preflight_summary.csv", rows)
    write_json(output_dir / "preflight_summary.json", {
        "status": "preflight_only",
        "credential_status": credential_status(args),
        "sample": dict(sample_metadata),
        "methods": [
            {
                "label": method.spec.label,
                "kind": method.spec.kind,
                "source_label": method.spec.source_label,
                "ranking_path": str(method.spec.ranking_path),
                "selector": method.spec.selector,
                "run_id": str(method.variant.run_id),
                "ratio": method.spec.ratio,
                "mmr_lambda": method.spec.mmr_lambda,
            }
            for method in methods
        ],
        "rows": rows,
    })

    lines = [
        "# Task63 Downstream LLM Evaluation Preflight",
        "",
        "Status: preflight only. No answer generation or LLM judging has been executed in this artifact.",
        "",
        "This file is not paper-facing answer-level evidence. It only verifies the frozen-test sample, method contexts, retrieval support, and context-token cost before the LLM run.",
        "",
        "## Sample",
        "",
        f"- Frozen test queries: `{sample_metadata.get('frozen_test_query_count')}`",
        f"- Eligible common frozen-test queries: `{sample_metadata.get('eligible_common_frozen_test_queries')}`",
        f"- Selected queries: `{sample_metadata.get('selected_query_count')}`",
        f"- Credential status: `{credential_status(args)}`",
        "",
        "## Preflight Retrieval/Token Checks",
        "",
    ]
    lines.extend(markdown_table(rows, [
        "method_label",
        "num_queries",
        "hit@10",
        "hit_delta_vs_baseline@10",
        "evidence_recall@10",
        "avg_context_tokens@10",
        "context_token_saving_percent_vs_baseline@10",
        "avg_selected_sentences@10",
    ]))
    lines.extend([
        "",
        "## Execution Requirement",
        "",
        "To complete Task63, run the same script with `--execute` after configuring a valid LLM provider API key. The formal summary is generated only after `answers.jsonl` and `judgments.jsonl` exist.",
    ])
    (output_dir / "preflight_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_prompt_previews(output_dir: Path, records: Sequence[Mapping[str, Any]], preview_count: int) -> None:
    previews: List[Dict[str, Any]] = []
    for row in records[:preview_count]:
        for method in row["methods"]:
            previews.append({
                "query_id": row["query_id"],
                "method_label": method["method_label"],
                "generation_prompt": generation_prompt(row["query_text"], method["context"]),
            })
    write_jsonl(output_dir / "prompt_preview.jsonl", previews)


def usage_input_tokens(usage: Mapping[str, Any]) -> int:
    for key in ("input_tokens", "prompt_tokens"):
        value = usage.get(key)
        if value is not None:
            try:
                return int(value)
            except Exception:
                pass
    nested = usage.get("prompt_tokens_details")
    if isinstance(nested, Mapping):
        value = nested.get("total_tokens")
        if value is not None:
            try:
                return int(value)
            except Exception:
                pass
    return 0


def bool_from_judge(judge_json: Any, key: str) -> bool | None:
    if not isinstance(judge_json, Mapping) or key not in judge_json:
        return None
    value = judge_json.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


def float_from_judge(judge_json: Any, key: str) -> float | None:
    if not isinstance(judge_json, Mapping):
        return None
    try:
        return float(judge_json.get(key))
    except Exception:
        return None


PAIRED_COMPARISONS: tuple[tuple[str, str, str], ...] = (
    ("bge_intentweight_vs_dense", "bge_dense_top10", "bge_intentweight_positive_seed19"),
    ("e5_intentweight_vs_dense", "e5_dense_top10", "e5_intentweight_full_seed19"),
    (
        "sent_mmr_intentweight_vs_dense",
        "dense_sent_mmr_r0.85_l0.70",
        "intentweight_sent_mmr_r0.85_l0.70_seed19",
    ),
)


def exact_mcnemar_p(baseline_only_correct: int, challenger_only_correct: int) -> float:
    discordant = baseline_only_correct + challenger_only_correct
    if discordant == 0:
        return 1.0
    tail = min(baseline_only_correct, challenger_only_correct)
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2 ** discordant)
    return min(1.0, 2.0 * probability)


def paired_ci(delta: np.ndarray, indices: np.ndarray) -> tuple[float, float]:
    values = np.mean(delta[indices], axis=1)
    low, high = np.quantile(values, [0.025, 0.975])
    return float(low), float(high)


def write_paired_comparisons(
    output_dir: Path,
    answers: Sequence[Mapping[str, Any]],
    judgments: Sequence[Mapping[str, Any]],
) -> None:
    answers_by_key = {
        (str(row.get("query_id")), str(row.get("method_label"))): row
        for row in answers
    }
    judgments_by_key = {
        (str(row.get("query_id")), str(row.get("method_label"))): row
        for row in judgments
        if valid_judgment(row)
    }
    rng = np.random.default_rng(63)
    rows: List[Dict[str, Any]] = []
    for label, baseline, challenger in PAIRED_COMPARISONS:
        query_ids = sorted(
            qid for qid, method in answers_by_key
            if method == baseline
            and (qid, challenger) in answers_by_key
            and (qid, baseline) in judgments_by_key
            and (qid, challenger) in judgments_by_key
        )
        if not query_ids:
            continue
        baseline_correct = np.asarray([
            float(bool_from_judge(judgments_by_key[(qid, baseline)]["judge_json"], "is_correct"))
            for qid in query_ids
        ])
        challenger_correct = np.asarray([
            float(bool_from_judge(judgments_by_key[(qid, challenger)]["judge_json"], "is_correct"))
            for qid in query_ids
        ])
        baseline_faithful = np.asarray([
            float(bool_from_judge(judgments_by_key[(qid, baseline)]["judge_json"], "is_faithful"))
            for qid in query_ids
        ])
        challenger_faithful = np.asarray([
            float(bool_from_judge(judgments_by_key[(qid, challenger)]["judge_json"], "is_faithful"))
            for qid in query_ids
        ])
        baseline_tokens = np.asarray([float(answers_by_key[(qid, baseline)]["context_tokens"]) for qid in query_ids])
        challenger_tokens = np.asarray([float(answers_by_key[(qid, challenger)]["context_tokens"]) for qid in query_ids])
        indices = rng.integers(0, len(query_ids), size=(10_000, len(query_ids)))
        correct_low, correct_high = paired_ci(challenger_correct - baseline_correct, indices)
        faithful_low, faithful_high = paired_ci(challenger_faithful - baseline_faithful, indices)
        bootstrap_baseline_tokens = np.mean(baseline_tokens[indices], axis=1)
        bootstrap_challenger_tokens = np.mean(challenger_tokens[indices], axis=1)
        bootstrap_saving = 100.0 * (bootstrap_baseline_tokens - bootstrap_challenger_tokens) / bootstrap_baseline_tokens
        token_low, token_high = np.quantile(bootstrap_saving, [0.025, 0.975])
        baseline_only = int(np.sum((baseline_correct == 1) & (challenger_correct == 0)))
        challenger_only = int(np.sum((baseline_correct == 0) & (challenger_correct == 1)))
        rows.append({
            "comparison": label,
            "baseline": baseline,
            "challenger": challenger,
            "paired_queries": len(query_ids),
            "baseline_correct_rate": float(np.mean(baseline_correct)),
            "challenger_correct_rate": float(np.mean(challenger_correct)),
            "correct_delta_pp": 100.0 * float(np.mean(challenger_correct - baseline_correct)),
            "correct_delta_ci_low_pp": 100.0 * correct_low,
            "correct_delta_ci_high_pp": 100.0 * correct_high,
            "mcnemar_exact_p": exact_mcnemar_p(baseline_only, challenger_only),
            "baseline_only_correct": baseline_only,
            "challenger_only_correct": challenger_only,
            "faithful_delta_pp": 100.0 * float(np.mean(challenger_faithful - baseline_faithful)),
            "faithful_delta_ci_low_pp": 100.0 * faithful_low,
            "faithful_delta_ci_high_pp": 100.0 * faithful_high,
            "baseline_avg_context_tokens": float(np.mean(baseline_tokens)),
            "challenger_avg_context_tokens": float(np.mean(challenger_tokens)),
            "context_token_saving_percent": 100.0 * float(
                (np.mean(baseline_tokens) - np.mean(challenger_tokens)) / np.mean(baseline_tokens)
            ),
            "context_token_saving_ci_low_percent": float(token_low),
            "context_token_saving_ci_high_percent": float(token_high),
        })
    write_csv(output_dir / "paired_comparisons.csv", rows)
    write_json(output_dir / "paired_comparisons.json", {"bootstrap_samples": 10_000, "rows": rows})
    lines = ["# Task63 Paired Comparisons", ""]
    lines.extend(markdown_table(rows, [
        "comparison",
        "paired_queries",
        "baseline_correct_rate",
        "challenger_correct_rate",
        "correct_delta_pp",
        "correct_delta_ci_low_pp",
        "correct_delta_ci_high_pp",
        "mcnemar_exact_p",
        "context_token_saving_percent",
        "context_token_saving_ci_low_percent",
        "context_token_saving_ci_high_percent",
    ]))
    (output_dir / "paired_comparisons.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_formal_summary(output_dir: Path, args: argparse.Namespace) -> None:
    answers = read_jsonl(output_dir / "answers.jsonl")
    judgments = [row for row in read_jsonl(output_dir / "judgments.jsonl") if valid_judgment(row)]
    judgments_by_answer: Dict[tuple[str, str], List[Mapping[str, Any]]] = {}
    for row in judgments:
        key = (str(row.get("query_id")), str(row.get("method_label")))
        judgments_by_answer.setdefault(key, []).append(row)

    by_method: Dict[str, List[Mapping[str, Any]]] = {}
    for answer in answers:
        by_method.setdefault(str(answer.get("method_label")), []).append(answer)

    rows: List[Dict[str, Any]] = []
    for method_label, method_answers in sorted(by_method.items()):
        judge_rows = [
            judgment
            for answer in method_answers
            for judgment in judgments_by_answer.get((str(answer.get("query_id")), method_label), [])
        ]
        correctness_scores = [
            value for value in (float_from_judge(row.get("judge_json"), "correctness_score") for row in judge_rows)
            if value is not None
        ]
        faithfulness_scores = [
            value for value in (float_from_judge(row.get("judge_json"), "faithfulness_score") for row in judge_rows)
            if value is not None
        ]
        citation_scores = [
            value for value in (float_from_judge(row.get("judge_json"), "citation_support_score") for row in judge_rows)
            if value is not None
        ]
        correct_flags = [
            value for value in (bool_from_judge(row.get("judge_json"), "is_correct") for row in judge_rows)
            if value is not None
        ]
        faithful_flags = [
            value for value in (bool_from_judge(row.get("judge_json"), "is_faithful") for row in judge_rows)
            if value is not None
        ]
        context_cost = sum(float(answer.get("context_tokens") or 0) * args.input_price_per_million / 1_000_000 for answer in method_answers)
        correct_rate = mean(float(value) for value in correct_flags) if correct_flags else 0.0
        estimated_correct_answers = correct_rate * len(method_answers)
        rows.append({
            "method_label": method_label,
            "answer_count": len(method_answers),
            "judgment_count": len(judge_rows),
            "valid_correctness_scores": len(correctness_scores),
            "correctness_score_mean": mean(correctness_scores) if correctness_scores else 0.0,
            "faithfulness_score_mean": mean(faithfulness_scores) if faithfulness_scores else 0.0,
            "citation_support_score_mean": mean(citation_scores) if citation_scores else 0.0,
            "correct_rate": correct_rate,
            "faithful_rate": mean(float(value) for value in faithful_flags) if faithful_flags else 0.0,
            "strict_citation_support_rate": mean(float(answer.get("strict_citation_support", False)) for answer in method_answers),
            "insufficient_context_rate": mean(float(answer.get("insufficient_context", False)) for answer in method_answers),
            "avg_context_tokens": mean(float(answer.get("context_tokens") or 0) for answer in method_answers),
            "total_context_tokens": sum(float(answer.get("context_tokens") or 0) for answer in method_answers),
            "context_tokens_per_correct": (
                sum(float(answer.get("context_tokens") or 0) for answer in method_answers) / estimated_correct_answers
                if estimated_correct_answers else 0.0
            ),
            "estimated_context_cost": context_cost,
            "estimated_context_cost_per_correct": context_cost / estimated_correct_answers if estimated_correct_answers else 0.0,
            "generation_input_tokens": sum(usage_input_tokens(answer.get("generation_usage") or {}) for answer in method_answers),
        })

    write_csv(output_dir / "summary.csv", rows)
    write_json(output_dir / "summary.json", {
        "status": "formal_llm_evaluation",
        "answer_count": len(answers),
        "judgment_count": len(judgments),
        "judge_models": parse_csv_list(args.judge_models or args.judge_model or args.model),
        "rows": rows,
    })
    write_paired_comparisons(output_dir, answers, judgments)
    lines = [
        "# Task63 Downstream LLM Evaluation Summary",
        "",
        "Status: formal LLM execution artifact.",
        "",
    ]
    lines.extend(markdown_table(rows, [
        "method_label",
        "answer_count",
        "judgment_count",
        "correct_rate",
        "faithful_rate",
        "strict_citation_support_rate",
        "insufficient_context_rate",
        "avg_context_tokens",
        "context_tokens_per_correct",
        "estimated_context_cost_per_correct",
    ]))
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_csv_list(value: str | None) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def thread_client(args: argparse.Namespace) -> Any:
    client = getattr(THREAD_LOCAL, "client", None)
    if client is None:
        client = create_client(args)
        THREAD_LOCAL.client = client
    return client


def generate_answer_output(record: Mapping[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    client = thread_client(args)
    answer_text = ""
    usage: Dict[str, Any] = {}
    parsed = None
    prompt = generation_prompt(record["query_text"], record["context"])
    for attempt in range(args.answer_retries + 1):
        retry_suffix = "" if attempt == 0 else "\n\nReturn only one valid JSON object with the required keys."
        answer_text, usage = call_model(
            client,
            model=args.model,
            instructions=GENERATION_INSTRUCTIONS,
            prompt=prompt + retry_suffix,
            args=args,
        )
        parsed = try_parse_json(answer_text)
        if isinstance(parsed, Mapping):
            break
        time.sleep(args.request_sleep)
    citation = strict_citation_check(
        parsed,
        context_chunk_ids=record["context_chunk_ids"],
        ground_truth_ids=record["ground_truth_chunk_ids"],
    )
    time.sleep(args.request_sleep)
    return {
        "query_id": record["query_id"],
        "method_label": record["method_label"],
        "answer_text": answer_text,
        "answer_json": parsed,
        "generation_usage": usage,
        "context_tokens": record["context_tokens"],
        "context_chunk_ids": record["context_chunk_ids"],
        "ground_truth_chunk_ids": record["ground_truth_chunk_ids"],
        **citation,
    }


def generate_judgment_output(
    answer: Mapping[str, Any],
    source_record: Mapping[str, Any],
    judge_model: str,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    client = thread_client(args)
    judge_text = ""
    usage: Dict[str, Any] = {}
    parsed = None
    base_prompt = judge_prompt(source_record, str(answer.get("answer_text") or ""), answer.get("answer_json"))
    for attempt in range(args.judge_retries + 1):
        retry_suffix = "" if attempt == 0 else "\n\nReturn only one complete JSON object."
        judge_text, usage = call_model(
            client,
            model=judge_model,
            instructions=JUDGE_INSTRUCTIONS,
            prompt=base_prompt + retry_suffix,
            args=args,
        )
        parsed = try_parse_json(judge_text)
        if isinstance(parsed, Mapping):
            break
        time.sleep(args.request_sleep)
    time.sleep(args.request_sleep)
    return {
        "query_id": answer["query_id"],
        "method_label": answer["method_label"],
        "judge_model": judge_model,
        "judge_text": judge_text,
        "judge_json": parsed,
        "judge_usage": usage,
    }


def execute_llm(records: Sequence[Mapping[str, Any]], output_dir: Path, args: argparse.Namespace) -> None:
    validate_credentials(args)
    answer_path = output_dir / "answers.jsonl"
    judgment_path = output_dir / "judgments.jsonl"
    sanitize_judgments(judgment_path, output_dir / "judgment_failures.jsonl")
    answer_keys = existing_answer_keys(answer_path)

    flattened = flatten_method_records(records)
    total_answers = len(flattened)
    pending_answers = [
        record for record in flattened
        if (str(record["query_id"]), str(record["method_label"])) not in answer_keys
    ]
    completed_answers = total_answers - len(pending_answers)
    if pending_answers:
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
            futures = [executor.submit(generate_answer_output, record, args) for record in pending_answers]
            for future in as_completed(futures):
                output = future.result()
                append_jsonl(answer_path, output)
                answer_keys.add((str(output["query_id"]), str(output["method_label"])))
                completed_answers += 1
                if args.progress_every > 0 and (
                    completed_answers % args.progress_every == 0 or completed_answers == total_answers
                ):
                    print(f"[answer {completed_answers}/{total_answers}]")

    answers = read_jsonl(answer_path)
    records_by_key = {
        (str(record["query_id"]), str(record["method_label"])): record
        for record in flattened
    }
    answers = [
        answer for answer in answers
        if (str(answer.get("query_id")), str(answer.get("method_label"))) in records_by_key
    ]
    judgment_keys = existing_judgment_keys(judgment_path)
    judge_models = parse_csv_list(args.judge_models or args.judge_model or args.model)
    total_judgments = len(answers) * len(judge_models)
    pending_judgments: List[tuple[Mapping[str, Any], Mapping[str, Any], str]] = []
    for answer in answers:
        key = (str(answer["query_id"]), str(answer["method_label"]))
        source_record = records_by_key.get(key)
        if source_record is None:
            continue
        for judge_model in judge_models:
            judge_key = (key[0], key[1], judge_model)
            if judge_key in judgment_keys:
                continue
            pending_judgments.append((answer, source_record, judge_model))

    completed_judgments = total_judgments - len(pending_judgments)
    if pending_judgments:
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
            futures = [
                executor.submit(generate_judgment_output, answer, source_record, judge_model, args)
                for answer, source_record, judge_model in pending_judgments
            ]
            for future in as_completed(futures):
                output = future.result()
                append_jsonl(judgment_path, output)
                judgment_keys.add((str(output["query_id"]), str(output["method_label"]), str(output["judge_model"])))
                completed_judgments += 1
                if args.progress_every > 0 and (
                    completed_judgments % args.progress_every == 0 or completed_judgments == total_judgments
                ):
                    print(f"[judge {completed_judgments}/{total_judgments}]")

    if not args.skip_formal_summary:
        write_formal_summary(output_dir, args)


def run(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.resume_llm_only:
        records = read_jsonl(output_dir / "sample_records.jsonl")
        if not records:
            raise RuntimeError(f"Cannot resume LLM-only execution; no sample records under {output_dir}")
        execute_llm(records, output_dir, args)
        return 0

    methods = load_methods_from_json(args.methods_json) if args.methods_json else loaded_default_methods()
    corpus = context_token_cost.load_json_list(args.corpus)
    queries = context_token_cost.load_json_list(args.queries)
    corpus_by_id = {chunk_id(chunk): chunk for chunk in corpus}
    count_tokens = build_token_counter(args)
    tokens_by_chunk = chunk_token_map(corpus, count_tokens)

    selected_queries, sample_metadata = choose_frozen_test_queries(
        queries,
        methods,
        scale=args.scale,
        calibration_fraction=args.calibration_fraction,
        split_salt=args.split_salt,
        sample_salt=args.sample_salt,
        max_queries=args.max_queries,
    )
    records = materialize_records(
        selected_queries,
        methods,
        corpus_by_id,
        tokens_by_chunk,
        count_tokens,
        args,
    )

    write_jsonl(output_dir / "sample_records.jsonl", records)
    write_prompt_previews(output_dir, records, args.preview_count)
    write_json(output_dir / "run_config.json", {
        "execute": args.execute,
        "provider": args.provider,
        "api_mode": args.api_mode,
        "model": args.model,
        "judge_model": args.judge_model,
        "judge_models": args.judge_models,
        "top_k": args.top_k,
        "tokenizer": args.tokenizer,
        "encoding": args.encoding,
        "sent_mmr_model": args.sent_mmr_model,
        "local_files_only": args.local_files_only,
        "sample": sample_metadata,
        "credential_status": credential_status(args),
    })
    write_preflight_summary(output_dir, records, sample_metadata, methods, args)

    if not args.execute:
        print(f"Prepared Task63 preflight under {output_dir}")
        print("No LLM calls were made. Add --execute after configuring provider credentials.")
        return 0

    execute_llm(records, output_dir, args)
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_DATA_DIR / "lotte_technology_search_100k_corpus.json")
    parser.add_argument("--queries", type=Path, default=DEFAULT_DATA_DIR / "lotte_technology_search_100k_queries.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--methods-json", type=Path, default=None)
    parser.add_argument("--scale", default="100k")
    parser.add_argument("--calibration-fraction", type=float, default=0.3)
    parser.add_argument("--split-salt", default="task38_lotte_calibration_v1")
    parser.add_argument("--sample-salt", default="task63_downstream_llm_eval_v1")
    parser.add_argument("--max-queries", type=int, default=300)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--baseline-method", default="minilm_dense_top10")
    parser.add_argument("--preview-count", type=int, default=2)
    parser.add_argument("--max-chunk-chars", type=int, default=0)
    parser.add_argument("--max-reference-chunks", type=int, default=3)
    parser.add_argument("--max-reference-chunk-chars", type=int, default=0)
    parser.add_argument("--tokenizer", choices=("tiktoken", "simple"), default="tiktoken")
    parser.add_argument("--encoding", default="cl100k_base")

    parser.add_argument("--sent-mmr-model", default=dense_baseline.DEFAULT_MODEL)
    parser.add_argument("--max-sentence-tokens", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--local-files-only", action="store_true", default=True)

    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume-llm-only", action="store_true")
    parser.add_argument(
        "--skip-formal-summary",
        action="store_true",
        help="Append resumable LLM outputs without rewriting single-judge summary files.",
    )
    parser.add_argument("--provider", choices=("openai", "azure", "compatible", "deepseek"), default="deepseek")
    parser.add_argument("--api-mode", choices=("responses", "chat-completions"), default="chat-completions")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--judge-models", default=None, help="Comma-separated judge models. Defaults to --judge-model or --model.")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--azure-deployment", default=None)
    parser.add_argument("--azure-endpoint", default=None)
    parser.add_argument("--azure-api-version", default="2025-04-01-preview")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument("--thinking", choices=("enabled", "disabled"), default="enabled")
    parser.add_argument("--response-format-json", action="store_true", default=True)
    parser.add_argument("--request-sleep", type=float, default=0.2)
    parser.add_argument("--answer-retries", type=int, default=1)
    parser.add_argument("--judge-retries", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--input-price-per-million", type=float, default=0.0)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
