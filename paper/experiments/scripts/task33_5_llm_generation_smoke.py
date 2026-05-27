#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task33.5 small end-to-end LLM generation smoke.

This script compares LLM answer quality for two retrieved-context variants,
typically dense top-10 versus Task29-C compressed context. It is designed as a
small, handoff-friendly smoke test and defaults to dry-run mode.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, NamedTuple, Sequence


DEFAULT_DATA_DIR = Path("paper/experiments/data/processed")
DEFAULT_RESULTS_DIR = Path("paper/experiments/results")
DEFAULT_OUTPUT_DIR = DEFAULT_RESULTS_DIR / "task33_5_llm_generation_smoke"


class RankingVariant(NamedTuple):
    label: str
    method: str
    seed: str
    rankings: Dict[str, List[str]]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def query_id(record: Mapping[str, Any]) -> str:
    value = record.get("query_id") or record.get("id")
    if value is None:
        raise ValueError(f"Query missing query_id/id: {record}")
    return str(value)


def chunk_id(record: Mapping[str, Any]) -> str:
    value = record.get("chunk_id") or record.get("id")
    if value is None:
        raise ValueError(f"Corpus record missing chunk_id/id: {record}")
    return str(value)


def ground_truth(query: Mapping[str, Any]) -> set[str]:
    values = (
        query.get("ground_truth_chunk_ids")
        or query.get("ground_truth")
        or query.get("relevant_chunk_ids")
        or []
    )
    return {str(value) for value in values}


def is_ranking_list(value: object) -> bool:
    return isinstance(value, list) and all(not isinstance(item, (dict, list)) for item in value)


def coerce_rankings(value: Mapping[str, Any]) -> Dict[str, List[str]]:
    return {str(qid): [str(item) for item in ranking] for qid, ranking in value.items()}


def load_ranking_variants(label: str, path: Path) -> List[RankingVariant]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"Ranking file must contain a JSON object: {path}")

    if all(is_ranking_list(value) for value in data.values()):
        return [RankingVariant(label, label, "", coerce_rankings(data))]

    variants: List[RankingVariant] = []
    for method, method_value in data.items():
        if not isinstance(method_value, dict):
            raise ValueError(f"Unsupported ranking object under {method!r} in {path}")
        if all(is_ranking_list(value) for value in method_value.values()):
            variants.append(RankingVariant(label, str(method), "", coerce_rankings(method_value)))
            continue
        for seed, seed_value in method_value.items():
            if not isinstance(seed_value, dict) or not all(is_ranking_list(v) for v in seed_value.values()):
                raise ValueError(f"Unsupported ranking object under {method!r}/{seed!r} in {path}")
            variants.append(RankingVariant(label, str(method), str(seed), coerce_rankings(seed_value)))
    return variants


def parse_ranking_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        path = Path(raw)
        return path.stem, path
    label, value = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"Empty ranking label in {raw!r}")
    return label, Path(value)


def pick_variant(variants: Sequence[RankingVariant], *, seed: str | None, method: str | None = None) -> RankingVariant:
    matches = list(variants)
    if method:
        matches = [variant for variant in matches if variant.method == method]
    if seed is not None:
        matches = [variant for variant in matches if variant.seed == seed]
    if not matches:
        available = ", ".join(f"{v.label}:{v.method}:seed{v.seed}" for v in variants)
        raise ValueError(f"No ranking variant matched method={method!r}, seed={seed!r}. Available: {available}")
    return matches[0]


def truncate_text(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: max(0, limit - 15)].rstrip() + " ...[truncated]"


def build_context(
    ranking: Sequence[str],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
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
            "text": truncate_text(str(chunk.get("text", "")), max_chunk_chars),
        })
    return context


def format_context(context: Sequence[Mapping[str, Any]]) -> str:
    blocks = []
    for item in context:
        blocks.append(f"[{item['rank']}] chunk_id={item['chunk_id']}\n{item['text']}")
    return "\n\n".join(blocks)


def format_reference_evidence(
    gt_ids: Sequence[str],
    corpus_by_id: Mapping[str, Mapping[str, Any]],
    *,
    max_refs: int,
    max_chunk_chars: int,
) -> str:
    blocks = []
    for idx, cid in enumerate(gt_ids[:max_refs], start=1):
        chunk = corpus_by_id.get(str(cid))
        if not chunk:
            continue
        blocks.append(f"[GT-{idx}] chunk_id={cid}\n{truncate_text(str(chunk.get('text', '')), max_chunk_chars)}")
    return "\n\n".join(blocks)


def has_hit(ranking: Sequence[str], gt: set[str], top_k: int) -> bool:
    return bool(gt.intersection(str(item) for item in ranking[:top_k]))


def sample_queries(
    queries: Sequence[Mapping[str, Any]],
    dense: RankingVariant,
    treatment: RankingVariant,
    *,
    sample_size: int,
    top_k: int,
    seed: int,
    require_any_hit: bool,
) -> List[Mapping[str, Any]]:
    buckets: Dict[str, List[Mapping[str, Any]]] = {
        "both_hit": [],
        "dense_only_hit": [],
        "treatment_only_hit": [],
        "both_miss": [],
    }
    for query in queries:
        qid = query_id(query)
        gt = ground_truth(query)
        if not gt:
            continue
        dense_hit = has_hit(dense.rankings.get(qid, []), gt, top_k)
        treatment_hit = has_hit(treatment.rankings.get(qid, []), gt, top_k)
        if require_any_hit and not (dense_hit or treatment_hit):
            continue
        if dense_hit and treatment_hit:
            bucket = "both_hit"
        elif dense_hit:
            bucket = "dense_only_hit"
        elif treatment_hit:
            bucket = "treatment_only_hit"
        else:
            bucket = "both_miss"
        buckets[bucket].append(query)

    rng = random.Random(seed)
    for values in buckets.values():
        rng.shuffle(values)

    # Keep the smoke balanced enough to expose degradation cases.
    preferred_order = ["both_hit", "dense_only_hit", "treatment_only_hit", "both_miss"]
    target_each = max(1, sample_size // len(preferred_order))
    selected: List[Mapping[str, Any]] = []
    used: set[str] = set()
    for bucket in preferred_order:
        for query in buckets[bucket][:target_each]:
            selected.append(query)
            used.add(query_id(query))
            if len(selected) >= sample_size:
                return selected
    remainder = [q for bucket in preferred_order for q in buckets[bucket] if query_id(q) not in used]
    rng.shuffle(remainder)
    selected.extend(remainder[: max(0, sample_size - len(selected))])
    return selected[:sample_size]


GENERATION_INSTRUCTIONS = """You answer technology support questions using only the provided retrieved context.

Rules:
- Answer the user question directly and concisely.
- Use only facts supported by the context.
- If the context is insufficient, say that the retrieved context is insufficient.
- Include a short `citations` list of chunk ids that support the answer.
- Return strict JSON with keys: answer, citations, insufficient_context.
"""


JUDGE_INSTRUCTIONS = """You are evaluating two RAG answers for the same question.

Use the reference evidence and each answer's retrieved context. Judge whether the answer is correct, relevant, and grounded.
Return strict JSON with:
- dense_score: integer 1-5
- treatment_score: integer 1-5
- dense_faithfulness: integer 1-5
- treatment_faithfulness: integer 1-5
- dense_answer_relevance: integer 1-5
- treatment_answer_relevance: integer 1-5
- winner: one of dense, treatment, tie
- rationale: short explanation
"""


def generation_prompt(query_text: str, context: Sequence[Mapping[str, Any]]) -> str:
    return (
        f"Question:\n{query_text}\n\n"
        f"Retrieved context:\n{format_context(context)}\n"
    )


def judge_prompt(record: Mapping[str, Any]) -> str:
    return (
        f"Question:\n{record['query_text']}\n\n"
        f"Reference evidence:\n{record['reference_evidence']}\n\n"
        f"Dense retrieved context:\n{format_context(record['dense_context'])}\n\n"
        f"Dense answer:\n{record['dense_answer_text']}\n\n"
        f"Treatment retrieved context:\n{format_context(record['treatment_context'])}\n\n"
        f"Treatment answer:\n{record['treatment_answer_text']}\n"
    )


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


def create_client(args: argparse.Namespace) -> Any:
    from openai import AzureOpenAI, OpenAI

    if args.provider == "azure":
        endpoint = args.azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = args.api_key or os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not endpoint:
            raise RuntimeError("Azure mode requires --azure-endpoint or AZURE_OPENAI_ENDPOINT")
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
        if not base_url:
            raise RuntimeError("Compatible provider requires --base-url or OPENAI_COMPATIBLE_BASE_URL")
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
        "metadata": {"task": "task33_5_llm_generation_smoke"},
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


def call_model(client: Any, *, instructions: str, prompt: str, args: argparse.Namespace) -> tuple[str, Dict[str, Any]]:
    model = args.azure_deployment if args.provider == "azure" and args.azure_deployment else args.model
    if args.api_mode == "chat-completions":
        return call_chat_completions(client, model=model, instructions=instructions, prompt=prompt, args=args)
    return call_responses(client, model=model, instructions=instructions, prompt=prompt, args=args)


def try_parse_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def build_records(args: argparse.Namespace) -> List[Dict[str, Any]]:
    corpus = load_json(args.corpus)
    queries = load_json(args.queries)
    corpus_by_id = {chunk_id(chunk): chunk for chunk in corpus}

    dense_label, dense_path = parse_ranking_arg(args.dense_ranking)
    treatment_label, treatment_path = parse_ranking_arg(args.treatment_ranking)
    dense_variant = pick_variant(load_ranking_variants(dense_label, dense_path), seed=args.dense_seed)
    treatment_variant = pick_variant(
        load_ranking_variants(treatment_label, treatment_path),
        seed=args.treatment_seed,
        method=args.treatment_method,
    )

    selected = sample_queries(
        queries,
        dense_variant,
        treatment_variant,
        sample_size=args.sample_size,
        top_k=args.top_k,
        seed=args.sample_seed,
        require_any_hit=args.require_any_hit,
    )

    rows: List[Dict[str, Any]] = []
    for query in selected:
        qid = query_id(query)
        gt = sorted(ground_truth(query))
        dense_ranking = dense_variant.rankings.get(qid, [])
        treatment_ranking = treatment_variant.rankings.get(qid, [])
        rows.append({
            "query_id": qid,
            "query_text": str(query.get("text", "")),
            "ground_truth_chunk_ids": gt,
            "dense_hit": has_hit(dense_ranking, set(gt), args.top_k),
            "treatment_hit": has_hit(treatment_ranking, set(gt), args.top_k),
            "dense_label": dense_variant.label,
            "treatment_label": treatment_variant.label,
            "treatment_method": treatment_variant.method,
            "treatment_seed": treatment_variant.seed,
            "dense_context": build_context(
                dense_ranking,
                corpus_by_id,
                top_k=args.top_k,
                max_chunk_chars=args.max_chunk_chars,
            ),
            "treatment_context": build_context(
                treatment_ranking,
                corpus_by_id,
                top_k=args.top_k,
                max_chunk_chars=args.max_chunk_chars,
            ),
            "reference_evidence": format_reference_evidence(
                gt,
                corpus_by_id,
                max_refs=args.max_reference_chunks,
                max_chunk_chars=args.max_reference_chunk_chars,
            ),
        })
    return rows


def run(args: argparse.Namespace) -> int:
    rows = build_records(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sample_path = args.output_dir / "sample_records.jsonl"
    write_jsonl(sample_path, rows)

    metadata = {
        "provider": args.provider,
        "api_mode": args.api_mode,
        "model": args.model,
        "base_url": args.base_url,
        "azure_deployment": args.azure_deployment,
        "azure_endpoint": args.azure_endpoint,
        "azure_api_version": args.azure_api_version,
        "thinking": args.thinking,
        "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens,
        "judge_retries": args.judge_retries,
        "sample_size": len(rows),
        "top_k": args.top_k,
        "dry_run": args.dry_run,
        "execute": args.execute,
        "dense_ranking": args.dense_ranking,
        "treatment_ranking": args.treatment_ranking,
        "treatment_seed": args.treatment_seed,
    }
    (args.output_dir / "run_config.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    prompt_previews = []
    for row in rows[: min(args.preview_count, len(rows))]:
        prompt_previews.append({
            "query_id": row["query_id"],
            "dense_generation_prompt": generation_prompt(row["query_text"], row["dense_context"]),
            "treatment_generation_prompt": generation_prompt(row["query_text"], row["treatment_context"]),
        })
    write_jsonl(args.output_dir / "prompt_preview.jsonl", prompt_previews)

    if args.dry_run or not args.execute:
        print(f"Prepared {len(rows)} sample records under {args.output_dir}")
        print("Dry run only. Add --execute to call the configured LLM endpoint.")
        return 0

    client = create_client(args)
    result_rows: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        dense_answer_text, dense_usage = call_model(
            client,
            instructions=GENERATION_INSTRUCTIONS,
            prompt=generation_prompt(row["query_text"], row["dense_context"]),
            args=args,
        )
        time.sleep(args.request_sleep)
        treatment_answer_text, treatment_usage = call_model(
            client,
            instructions=GENERATION_INSTRUCTIONS,
            prompt=generation_prompt(row["query_text"], row["treatment_context"]),
            args=args,
        )
        judge_record = {
            **row,
            "dense_answer_text": dense_answer_text,
            "treatment_answer_text": treatment_answer_text,
        }
        time.sleep(args.request_sleep)
        judge_text = ""
        judge_usage: Dict[str, Any] = {}
        parsed_judge = None
        base_judge_prompt = judge_prompt(judge_record)
        for attempt in range(args.judge_retries + 1):
            retry_suffix = "" if attempt == 0 else "\n\nReturn only one complete JSON object. Do not omit any required key."
            judge_text, judge_usage = call_model(
                client,
                instructions=JUDGE_INSTRUCTIONS,
                prompt=base_judge_prompt + retry_suffix,
                args=args,
            )
            parsed_judge = try_parse_json(judge_text)
            if isinstance(parsed_judge, dict):
                break
            time.sleep(args.request_sleep)
        output = {
            **judge_record,
            "dense_answer_json": try_parse_json(dense_answer_text),
            "treatment_answer_json": try_parse_json(treatment_answer_text),
            "judge_text": judge_text,
            "judge_json": parsed_judge,
            "dense_usage": dense_usage,
            "treatment_usage": treatment_usage,
            "judge_usage": judge_usage,
        }
        result_rows.append(output)
        write_jsonl(args.output_dir / "llm_results.jsonl", result_rows)
        print(f"[{idx}/{len(rows)}] {row['query_id']} complete")
        time.sleep(args.request_sleep)

    write_summary(args.output_dir, result_rows)
    return 0


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def write_summary(output_dir: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    summary: Dict[str, Any] = {"num_queries": len(rows)}
    judge_rows = [row.get("judge_json") for row in rows if isinstance(row.get("judge_json"), dict)]
    summary["valid_judge_count"] = len(judge_rows)
    summary["invalid_judge_count"] = len(rows) - len(judge_rows)
    if judge_rows:
        for key in (
            "dense_score",
            "treatment_score",
            "dense_faithfulness",
            "treatment_faithfulness",
            "dense_answer_relevance",
            "treatment_answer_relevance",
        ):
            values = [as_float(row.get(key)) for row in judge_rows]
            values = [value for value in values if value is not None]
            if values:
                summary[f"{key}_mean"] = mean(values)
        winners: Dict[str, int] = {}
        for row in judge_rows:
            winner = str(row.get("winner", "unknown"))
            winners[winner] = winners.get(winner, 0) + 1
        summary["winner_counts"] = winners

    output_dir.joinpath("summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    md_lines = ["# Task33.5 LLM Generation Smoke Summary", ""]
    for key, value in summary.items():
        md_lines.append(f"- `{key}`: `{value}`")
    output_dir.joinpath("summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_DATA_DIR / "lotte_technology_search_100k_corpus.json")
    parser.add_argument("--queries", type=Path, default=DEFAULT_DATA_DIR / "lotte_technology_search_100k_queries.json")
    parser.add_argument("--dense-ranking", default=str(DEFAULT_RESULTS_DIR / "dense_lotte_technology_search_100k_rankings.json"))
    parser.add_argument(
        "--treatment-ranking",
        default=str(DEFAULT_RESULTS_DIR / "task29_100k_confidence_topk_C_formal" / "linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential_rankings.json"),
    )
    parser.add_argument("--dense-seed", default=None)
    parser.add_argument("--treatment-method", default="gated_cost_aware")
    parser.add_argument("--treatment-seed", default="13")
    parser.add_argument("--sample-size", type=int, default=60)
    parser.add_argument("--sample-seed", type=int, default=33)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--require-any-hit", action="store_true", default=True)
    parser.add_argument("--max-chunk-chars", type=int, default=1400)
    parser.add_argument("--max-reference-chunks", type=int, default=3)
    parser.add_argument("--max-reference-chunk-chars", type=int, default=1200)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--preview-count", type=int, default=3)

    parser.add_argument("--provider", choices=("openai", "azure", "compatible", "deepseek"), default="azure")
    parser.add_argument("--api-mode", choices=("responses", "chat-completions"), default="responses")
    parser.add_argument("--model", default="gpt-5.1")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL, e.g. https://api.deepseek.com")
    parser.add_argument("--azure-deployment", default=None, help="Azure deployment name. Defaults to --model if omitted.")
    parser.add_argument("--azure-endpoint", default=None, help="Azure endpoint, e.g. https://xxx.openai.azure.com")
    parser.add_argument("--azure-api-version", default="2025-04-01-preview")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=512)
    parser.add_argument("--response-format-json", action="store_true", default=True)
    parser.add_argument("--thinking", default="enabled", choices=("enabled", "disabled", ""))
    parser.add_argument("--reasoning-effort", default="high", choices=("minimal", "low", "medium", "high", "max", ""))
    parser.add_argument("--request-sleep", type=float, default=0.2)
    parser.add_argument("--judge-retries", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="Actually call the configured model endpoint.")
    args = parser.parse_args(argv)

    if args.execute:
        args.dry_run = False
    if args.provider == "azure" and not args.azure_deployment:
        args.azure_deployment = args.model
    if args.reasoning_effort == "":
        args.reasoning_effort = None
    return args


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
