# -*- coding: utf-8 -*-
"""
CUAD 预处理脚本
CUAD Preprocessing Script

将 CUAD (SQuAD-like 格式) 转换为统一 RAG 实验格式：
- {name}_corpus.json: chunk 语料库
- {name}_queries.json: 查询 + GT 映射

用法 / Usage:
    python paper/experiments/scripts/preprocess_cuad.py
"""

import json
import os
from datasets import load_from_disk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")


def process_cuad():
    """处理 CUAD 数据集

    CUAD 是 SQuAD 2.0 格式：
    - 每个 contract 被分成多个 paragraphs (context)
    - 每个 paragraph 有多个 QA pairs
    - answer 包含 text + start position (可能为空 = unanswerable)

    转换逻辑：
    - paragraphs → corpus chunks (每个 paragraph = 1 chunk)
    - questions → queries
    - answer 所在的 paragraph → ground truth chunk
    """
    print("=" * 60)
    print("预处理 CUAD 数据集...")
    print("=" * 60)

    raw_path = os.path.join(RAW_DIR, "cuad")
    dataset = load_from_disk(raw_path)

    corpus = []  # 语料库 chunks
    queries = []  # 查询 + GT
    chunk_text_to_id = {}  # 去重用

    for split_name in dataset.keys():
        split_data = dataset[split_name]

        for idx, example in enumerate(split_data):
            context = example["context"]
            question = example["question"]
            answers = example["answers"]
            title = example.get("title", f"doc_{idx}")

            # 构建 chunk（按 context 去重）
            if context not in chunk_text_to_id:
                chunk_id = f"cuad_c{len(chunk_text_to_id):05d}"
                chunk_text_to_id[context] = chunk_id
                corpus.append({
                    "chunk_id": chunk_id,
                    "text": context,
                    "doc_id": title,
                    "metadata": {
                        "source": "cuad",
                        "split": split_name,
                    },
                })

            # 构建 query
            gt_chunk_ids = []
            answer_text = ""

            if answers and len(answers["text"]) > 0 and answers["text"][0]:
                answer_text = answers["text"][0]
                gt_chunk_ids = [chunk_text_to_id[context]]

            query_id = f"cuad_q{len(queries):05d}"
            queries.append({
                "query_id": query_id,
                "text": question,
                "ground_truth_chunk_ids": gt_chunk_ids,
                "answer": answer_text,
                "split": split_name,
                "metadata": {
                    "title": title,
                    "answerable": len(gt_chunk_ids) > 0,
                },
            })

    # 保存
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    corpus_path = os.path.join(PROCESSED_DIR, "cuad_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, "cuad_queries.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    # 统计
    answerable = sum(1 for q in queries if q["metadata"]["answerable"])
    print(f"\n  Corpus chunks: {len(corpus)}")
    print(f"  Queries: {len(queries)} (answerable: {answerable})")
    print(f"  Unique documents: {len(set(c['doc_id'] for c in corpus))}")
    print(f"  已保存到: {PROCESSED_DIR}/cuad_*.json")


if __name__ == "__main__":
    process_cuad()
