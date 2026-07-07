#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGBench 预处理脚本
RAGBench Preprocessing Script

将 RAGBench 子集（eManual / CUAD）转换为统一 RAG 实验格式：
- {dataset}_corpus.json: sentence-level chunks
- {dataset}_queries.json: question + GT chunk mapping

输入优先使用 HuggingFace Parquet API 下载的 parquet 文件，避免 datasets loading
script / trust_remote_code 问题。

用法 / Usage:
    python paper/experiments/scripts/preprocess_ragbench.py --dataset emanual
    python paper/experiments/scripts/preprocess_ragbench.py --dataset cuad
"""
import argparse
import json
import os
import re
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")

DATASET_FILES = {
    "emanual": {
        "train": "emanual_train.parquet",
        "validation": "emanual_validation.parquet",
        "test": "emanual_test.parquet",
    },
    "cuad": {
        "train": "cuad_ragbench_train.parquet",
        "validation": "cuad_ragbench_validation.parquet",
        "test": "cuad_ragbench_test.parquet",
    },
    "covidqa": {
        "train": "covidqa_train.parquet",
        "validation": "covidqa_validation.parquet",
        "test": "covidqa_test.parquet",
    },
    "finqa": {
        "train": "finqa_train.parquet",
        "validation": "finqa_validation.parquet",
        "test": "finqa_test.parquet",
    },
    "techqa": {
        "train": "techqa_train.parquet",
        "validation": "techqa_validation.parquet",
        "test": "techqa_test.parquet",
    },
}


def _to_python_list(value: Any) -> list:
    """Convert numpy/pyarrow scalar-ish values to plain Python lists."""
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list):
        return value
    return [value]


def _safe_id(text: Any) -> str:
    """Create a stable filesystem/JSON friendly id fragment."""
    s = str(text) if text is not None else "unknown"
    s = re.sub(r"[^0-9A-Za-z_\-]+", "_", s).strip("_")
    return s or "unknown"


def _iter_sentence_chunks(documents_sentences: Any) -> Iterable[Tuple[int, str, str]]:
    """Yield (doc_index, sentence_key, sentence_text) from RAGBench documents_sentences.

    RAGBench stores this as a nested array/list:
        documents_sentences = [
            [["0a", "sentence text"], ["0b", "..."]],
            [["1a", "sentence text"]],
        ]
    """
    docs = _to_python_list(documents_sentences)
    for doc_index, doc in enumerate(docs):
        for pair in _to_python_list(doc):
            pair = _to_python_list(pair)
            if len(pair) < 2:
                continue
            sentence_key = str(pair[0])
            sentence_text = str(pair[1]).strip()
            if not sentence_text:
                continue
            yield doc_index, sentence_key, sentence_text


def _score_value(row: Dict[str, Any], key: str):
    value = row.get(key)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def process_dataset(dataset_name: str) -> Dict[str, int]:
    """Process one RAGBench subset into unified corpus/query JSON files."""
    if dataset_name not in DATASET_FILES:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Choices: {sorted(DATASET_FILES)}")

    print("=" * 60)
    print(f"预处理 RAGBench/{dataset_name} 数据集...")
    print("=" * 60)

    corpus: List[Dict] = []
    queries: List[Dict] = []
    chunk_ids_seen = set()

    for split_name, filename in DATASET_FILES[dataset_name].items():
        parquet_path = os.path.join(RAW_DIR, filename)
        if not os.path.exists(parquet_path):
            print(f"  跳过 {split_name}: 未找到 {parquet_path}")
            continue

        df = pd.read_parquet(parquet_path)
        print(f"  读取 {split_name}: {len(df)} 行, {len(df.columns)} 列")

        for row_idx, row_obj in df.iterrows():
            row = row_obj.to_dict()
            record_id = _safe_id(row.get("id", f"{split_name}_{row_idx}"))
            key_to_chunk_id: Dict[str, str] = {}

            for doc_index, sentence_key, sentence_text in _iter_sentence_chunks(row.get("documents_sentences")):
                safe_key = _safe_id(sentence_key)
                chunk_id = f"{dataset_name}_{record_id}_{safe_key}"
                key_to_chunk_id[sentence_key] = chunk_id

                if chunk_id not in chunk_ids_seen:
                    chunk_ids_seen.add(chunk_id)
                    corpus.append({
                        "chunk_id": chunk_id,
                        "text": sentence_text,
                        "doc_id": f"{dataset_name}_{record_id}_doc{doc_index}",
                        "metadata": {
                            "source": dataset_name,
                            "split": split_name,
                            "record_id": record_id,
                            "doc_index": doc_index,
                            "sentence_key": sentence_key,
                        },
                    })

            relevant_keys = [str(k) for k in _to_python_list(row.get("all_relevant_sentence_keys"))]
            utilized_keys = [str(k) for k in _to_python_list(row.get("all_utilized_sentence_keys"))]
            gt_chunk_ids = [key_to_chunk_id[k] for k in relevant_keys if k in key_to_chunk_id]
            utilized_chunk_ids = [key_to_chunk_id[k] for k in utilized_keys if k in key_to_chunk_id]

            query_id = f"{dataset_name}_q{len(queries):06d}"
            queries.append({
                "query_id": query_id,
                "text": str(row.get("question", "")),
                "ground_truth_chunk_ids": gt_chunk_ids,
                "answer": str(row.get("response", "")),
                "split": split_name,
                "metadata": {
                    "source": dataset_name,
                    "split": split_name,
                    "record_id": record_id,
                    "has_relevant": len(gt_chunk_ids) > 0,
                    "relevant_sentence_keys": relevant_keys,
                    "utilized_sentence_keys": utilized_keys,
                    "utilized_chunk_ids": utilized_chunk_ids,
                    "relevance_score": _score_value(row, "relevance_score"),
                    "utilization_score": _score_value(row, "utilization_score"),
                    "completeness_score": _score_value(row, "completeness_score"),
                    "ragas_faithfulness": _score_value(row, "ragas_faithfulness"),
                    "ragas_context_relevance": _score_value(row, "ragas_context_relevance"),
                },
            })

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    corpus_path = os.path.join(PROCESSED_DIR, f"{dataset_name}_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, f"{dataset_name}_queries.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    with_gt = sum(1 for q in queries if q["ground_truth_chunk_ids"])
    stats = {
        "corpus_chunks": len(corpus),
        "queries": len(queries),
        "queries_with_gt": with_gt,
    }

    print(f"\n  Corpus chunks: {stats['corpus_chunks']}")
    print(f"  Queries: {stats['queries']} (with GT: {stats['queries_with_gt']})")
    print(f"  已保存到: {PROCESSED_DIR}/{dataset_name}_*.json")
    return stats


def main():
    parser = argparse.ArgumentParser(description="预处理 RAGBench parquet 数据集")
    parser.add_argument(
        "--dataset",
        choices=sorted(DATASET_FILES.keys()),
        required=True,
        help="RAGBench 子集名称",
    )
    args = parser.parse_args()
    process_dataset(args.dataset)


if __name__ == "__main__":
    main()
