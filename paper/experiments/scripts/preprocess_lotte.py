#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preprocess LoTTE into the unified IntentWeight RAG experiment schema.

LoTTE on HuggingFace MTEB is exposed as three configs per domain/mode:
- {domain}_{mode}-corpus
- {domain}_{mode}-queries
- {domain}_{mode}-qrels

The output follows the project convention:
- {dataset}_corpus.json
- {dataset}_queries.json

Small samples are GT-anchored: all positive corpus chunks for selected queries
are kept, then background corpus chunks are added as distractors.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

import pyarrow.ipc as arrow_ipc
from datasets import load_dataset


SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_REPO = "mteb/LoTTE"
DEFAULT_DOMAIN = "technology"
DEFAULT_MODE = "search"
DEFAULT_SPLIT = "test"
DEFAULT_HF_DATASETS_CACHE = Path.home() / ".cache" / "huggingface" / "datasets"


def dataset_name(domain: str, mode: str) -> str:
    """Return the processed dataset slug for a LoTTE domain/mode pair."""
    return f"lotte_{slug_part(domain)}_{slug_part(mode)}"


def hf_config(domain: str, mode: str, part: str) -> str:
    """Return the HuggingFace config name for one LoTTE part."""
    return f"{domain}_{mode}-{part}"


def slug_part(value: object) -> str:
    raw = str(value or "").strip().lower()
    chars = [char if char.isalnum() else "_" for char in raw]
    return "_".join(part for part in "".join(chars).split("_") if part)


def processed_corpus_id(name: str, original_id: object) -> str:
    return f"{name}_c{original_id}"


def processed_query_id(name: str, original_id: object) -> str:
    return f"{name}_q{original_id}"


def combine_title_text(title: object, text: object) -> str:
    title_text = str(title or "").strip()
    body_text = str(text or "").strip()
    if title_text and body_text:
        return f"{title_text}\n{body_text}"
    return title_text or body_text


def positive_qrels(qrel_rows: Iterable[Mapping]) -> Dict[str, List[str]]:
    """Group qrels into query-id -> positive corpus-id list."""
    grouped: Dict[str, List[str]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for row in qrel_rows:
        score = float(row.get("score", 0) or 0)
        if score <= 0:
            continue
        query_id = str(row.get("query-id"))
        corpus_id = str(row.get("corpus-id"))
        key = (query_id, corpus_id)
        if query_id and corpus_id and key not in seen:
            grouped[query_id].append(corpus_id)
            seen.add(key)
    return dict(grouped)


def select_query_ids(qrels_by_query: Mapping[str, Sequence[str]], max_queries: int | None) -> List[str]:
    query_ids = sorted(qrels_by_query, key=lambda value: int(value) if str(value).isdigit() else str(value))
    if max_queries is not None:
        query_ids = query_ids[:max_queries]
    return query_ids


def cached_arrow_dir(repo: str, config: str) -> Path | None:
    repo_slug = repo.replace("/", "___").lower()
    config_root = DEFAULT_HF_DATASETS_CACHE / repo_slug / config
    if not config_root.exists():
        matches = sorted(DEFAULT_HF_DATASETS_CACHE.glob(f"*{repo_slug.split('___')[-1].replace('tte', '_tte')}*/{config}"))
        if matches:
            config_root = matches[-1]
    if not config_root.exists():
        return None
    candidates = sorted(config_root.glob("*/*"))
    if not candidates:
        return None
    return candidates[-1]


def load_cached_arrow_rows(repo: str, config: str, split: str) -> Iterable[Mapping]:
    cache_dir = cached_arrow_dir(repo, config)
    if cache_dir is None:
        raise FileNotFoundError(f"No cached LoTTE Arrow directory found for config={config!r}")
    arrow_paths = sorted(cache_dir.glob(f"*{split}*.arrow"))
    if not arrow_paths:
        raise FileNotFoundError(f"No cached LoTTE Arrow files found for config={config!r}, split={split!r}")
    for arrow_path in arrow_paths:
        with arrow_ipc.open_stream(arrow_path) as reader:
            for batch in reader:
                for row in batch.to_pylist():
                    yield row


def load_part(repo: str, config: str, split: str, *, streaming: bool, local_arrow_cache: bool = False):
    if local_arrow_cache:
        return load_cached_arrow_rows(repo, config, split)
    try:
        return load_dataset(repo, config, split=split, streaming=streaming)
    except OSError as exc:
        if streaming:
            raise
        print(f"Falling back to cached LoTTE Arrow files for {config}/{split}: {exc}")
        return load_cached_arrow_rows(repo, config, split)


def load_qrels_by_query(
    repo: str,
    domain: str,
    mode: str,
    split: str,
    *,
    streaming: bool,
    local_arrow_cache: bool,
) -> Dict[str, List[str]]:
    rows = load_part(
        repo,
        hf_config(domain, mode, "qrels"),
        split,
        streaming=streaming,
        local_arrow_cache=local_arrow_cache,
    )
    return positive_qrels(rows)


def load_queries_by_id(
    repo: str,
    domain: str,
    mode: str,
    split: str,
    query_ids: set[str],
    *,
    streaming: bool,
    local_arrow_cache: bool,
) -> Dict[str, Mapping]:
    rows = load_part(
        repo,
        hf_config(domain, mode, "queries"),
        split,
        streaming=streaming,
        local_arrow_cache=local_arrow_cache,
    )
    selected: Dict[str, Mapping] = {}
    for row in rows:
        query_id = str(row.get("_id"))
        if query_id in query_ids:
            selected[query_id] = row
            if len(selected) == len(query_ids):
                break
    return selected


def select_corpus_rows(
    repo: str,
    domain: str,
    mode: str,
    split: str,
    *,
    needed_corpus_ids: set[str],
    max_corpus: int | None,
    streaming: bool,
    local_arrow_cache: bool,
) -> List[Mapping]:
    if max_corpus is not None and max_corpus < len(needed_corpus_ids):
        raise ValueError(
            f"max_corpus={max_corpus} is smaller than required GT chunks={len(needed_corpus_ids)}; "
            "increase max_corpus or reduce max_queries."
        )

    target_size = max_corpus or len(needed_corpus_ids)
    rows = load_part(
        repo,
        hf_config(domain, mode, "corpus"),
        split,
        streaming=streaming,
        local_arrow_cache=local_arrow_cache,
    )
    selected: MutableMapping[str, Mapping] = {}

    for row in rows:
        corpus_id = str(row.get("_id"))
        if corpus_id in selected:
            continue
        if corpus_id in needed_corpus_ids:
            selected[corpus_id] = row
        elif len(selected) < target_size:
            selected[corpus_id] = row

        if needed_corpus_ids.issubset(selected.keys()) and len(selected) >= target_size:
            break

    missing = sorted(needed_corpus_ids - set(selected))
    if missing:
        preview = ", ".join(missing[:5])
        raise ValueError(f"Could not find {len(missing)} GT corpus rows in LoTTE stream; first missing: {preview}")

    def sort_key(item: tuple[str, Mapping]) -> tuple[int, object]:
        corpus_id, _ = item
        if corpus_id.isdigit():
            return (0, int(corpus_id))
        return (1, corpus_id)

    return [row for _, row in sorted(selected.items(), key=sort_key)]


def build_corpus_records(
    rows: Iterable[Mapping],
    *,
    name: str,
    domain: str,
    mode: str,
    split: str,
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for row in rows:
        original_id = str(row.get("_id"))
        text = combine_title_text(row.get("title"), row.get("text"))
        records.append(
            {
                "chunk_id": processed_corpus_id(name, original_id),
                "text": text,
                "doc_id": f"{name}_doc_{original_id}",
                "metadata": {
                    "source": "lotte",
                    "domain": domain,
                    "mode": mode,
                    "split": split,
                    "original_corpus_id": original_id,
                },
            }
        )
    return records


def build_query_records(
    rows_by_id: Mapping[str, Mapping],
    *,
    selected_query_ids: Sequence[str],
    qrels_by_query: Mapping[str, Sequence[str]],
    name: str,
    domain: str,
    mode: str,
    split: str,
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    missing = [query_id for query_id in selected_query_ids if query_id not in rows_by_id]
    if missing:
        preview = ", ".join(missing[:5])
        raise ValueError(f"Could not find {len(missing)} selected query rows in LoTTE stream; first missing: {preview}")

    for query_id in selected_query_ids:
        row = rows_by_id[query_id]
        gt_ids = [processed_corpus_id(name, corpus_id) for corpus_id in qrels_by_query[query_id]]
        records.append(
            {
                "query_id": processed_query_id(name, query_id),
                "text": str(row.get("text", "")).strip(),
                "ground_truth_chunk_ids": gt_ids,
                "answer": "",
                "split": split,
                "metadata": {
                    "source": "lotte",
                    "domain": domain,
                    "mode": mode,
                    "original_query_id": query_id,
                },
            }
        )
    return records


def write_json(path: Path, data: Sequence[Mapping]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, separators=(",", ":"))


def preprocess_lotte(
    *,
    repo: str,
    domain: str,
    mode: str,
    split: str,
    max_queries: int | None,
    max_corpus: int | None,
    output_name: str | None,
    output_dir: Path,
    streaming: bool,
    local_arrow_cache: bool,
) -> tuple[Path, Path, Dict[str, object]]:
    name = output_name or dataset_name(domain, mode)
    qrels_by_query = load_qrels_by_query(
        repo,
        domain,
        mode,
        split,
        streaming=streaming,
        local_arrow_cache=local_arrow_cache,
    )
    selected_query_ids = select_query_ids(qrels_by_query, max_queries)
    if not selected_query_ids:
        raise ValueError(f"No positive LoTTE qrels found for domain={domain!r}, mode={mode!r}, split={split!r}")

    needed_corpus_ids = {
        corpus_id for query_id in selected_query_ids for corpus_id in qrels_by_query.get(query_id, [])
    }
    query_rows = load_queries_by_id(
        repo,
        domain,
        mode,
        split,
        set(selected_query_ids),
        streaming=streaming,
        local_arrow_cache=local_arrow_cache,
    )
    corpus_rows = select_corpus_rows(
        repo,
        domain,
        mode,
        split,
        needed_corpus_ids=needed_corpus_ids,
        max_corpus=max_corpus,
        streaming=streaming,
        local_arrow_cache=local_arrow_cache,
    )
    corpus = build_corpus_records(corpus_rows, name=name, domain=domain, mode=mode, split=split)
    queries = build_query_records(
        query_rows,
        selected_query_ids=selected_query_ids,
        qrels_by_query=qrels_by_query,
        name=name,
        domain=domain,
        mode=mode,
        split=split,
    )

    corpus_path = output_dir / f"{name}_corpus.json"
    queries_path = output_dir / f"{name}_queries.json"
    write_json(corpus_path, corpus)
    write_json(queries_path, queries)

    summary = {
        "dataset": name,
        "domain": domain,
        "mode": mode,
        "split": split,
        "corpus_chunks": len(corpus),
        "queries": len(queries),
        "gt_refs": sum(len(query["ground_truth_chunk_ids"]) for query in queries),
        "max_queries": max_queries,
        "max_corpus": max_corpus,
        "streaming": streaming,
        "local_arrow_cache": local_arrow_cache,
    }
    return corpus_path, queries_path, summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preprocess LoTTE for IntentWeight experiments")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--mode", default=DEFAULT_MODE)
    parser.add_argument("--split", default=DEFAULT_SPLIT)
    parser.add_argument("--max-queries", type=int, default=20)
    parser.add_argument("--max-corpus", type=int, default=5000)
    parser.add_argument("--output-name", default=None)
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--streaming", action="store_true", help="Use HF streaming; default false for stable CLI exit")
    parser.add_argument("--local-arrow-cache", action="store_true", help="Read LoTTE from local HF Arrow cache")
    args = parser.parse_args(argv)

    corpus_path, queries_path, summary = preprocess_lotte(
        repo=args.repo,
        domain=args.domain,
        mode=args.mode,
        split=args.split,
        max_queries=args.max_queries,
        max_corpus=args.max_corpus,
        output_name=args.output_name,
        output_dir=args.output_dir,
        streaming=args.streaming,
        local_arrow_cache=args.local_arrow_cache,
    )

    print("=" * 80)
    print("LoTTE preprocessing complete")
    print("=" * 80)
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"corpus_path: {os.fspath(corpus_path)}")
    print(f"queries_path: {os.fspath(queries_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
