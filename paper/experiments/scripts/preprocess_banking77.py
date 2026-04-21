# -*- coding: utf-8 -*-
"""
BANKING77 预处理脚本
BANKING77 Preprocessing Script

将 BANKING77 (意图分类数据集) 转换为统一 RAG 实验格式。

转换逻辑（复用 Phase 1D 的方式）：
- train samples → corpus chunks (每条 train 样本 = 1 个可检索的 chunk)
- test samples → queries
- GT: 同 intent 的 train 样本 = 相关 chunks

用法 / Usage:
    python paper/experiments/scripts/preprocess_banking77.py
"""

import json
import os
from collections import defaultdict
from datasets import load_from_disk, load_dataset

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
PRE_VAL_DIR = os.path.join(SCRIPT_DIR, "..", "..", "..", "pre_validation", "data")


def process_banking77():
    """处理 BANKING77 数据集

    BANKING77 格式：
    - text: 用户查询文本
    - label: 意图类别 ID (0-76)

    RAG 转换：
    - train 集每条记录 = 1 个 corpus chunk
    - test 集每条记录 = 1 个 query
    - 同 intent 的 train 记录 = ground truth chunks
    """
    print("=" * 60)
    print("预处理 BANKING77 数据集...")
    print("=" * 60)

    # 尝试从多个位置加载
    dataset = None
    for path in [
        os.path.join(RAW_DIR, "banking77"),
        os.path.join(PRE_VAL_DIR, "banking77"),
    ]:
        if os.path.exists(path):
            print(f"  从本地加载: {path}")
            dataset = load_from_disk(path)
            break

    if dataset is None:
        print("  本地未找到，从 HuggingFace 下载...")
        dataset = load_dataset("PolyAI/banking77")

    # 获取 intent 标签映射
    train_data = dataset["train"]
    test_data = dataset["test"]

    label_names = train_data.features["label"].names

    # 构建 corpus: train samples → chunks
    corpus = []
    intent_to_chunks = defaultdict(list)  # intent_id → [chunk_ids]

    for idx, example in enumerate(train_data):
        chunk_id = f"bank77_c{idx:05d}"
        intent_id = example["label"]

        corpus.append({
            "chunk_id": chunk_id,
            "text": example["text"],
            "doc_id": f"intent_{intent_id}",
            "metadata": {
                "source": "banking77",
                "intent_id": intent_id,
                "intent_name": label_names[intent_id],
                "split": "train",
            },
        })
        intent_to_chunks[intent_id].append(chunk_id)

    # 构建 queries: test samples → queries (GT = 同 intent 的 train chunks)
    queries = []
    for idx, example in enumerate(test_data):
        intent_id = example["label"]
        gt_chunk_ids = intent_to_chunks.get(intent_id, [])

        query_id = f"bank77_q{idx:05d}"
        queries.append({
            "query_id": query_id,
            "text": example["text"],
            "ground_truth_chunk_ids": gt_chunk_ids,
            "answer": label_names[intent_id],
            "split": "test",
            "metadata": {
                "source": "banking77",
                "intent_id": intent_id,
                "intent_name": label_names[intent_id],
            },
        })

    # 保存
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    corpus_path = os.path.join(PROCESSED_DIR, "banking77_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, "banking77_queries.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    print(f"\n  Corpus chunks (train): {len(corpus)}")
    print(f"  Queries (test): {len(queries)}")
    print(f"  Intent classes: {len(label_names)}")
    print(f"  Avg GT chunks per query: {sum(len(q['ground_truth_chunk_ids']) for q in queries) / len(queries):.1f}")
    print(f"  已保存到: {PROCESSED_DIR}/banking77_*.json")


if __name__ == "__main__":
    process_banking77()
