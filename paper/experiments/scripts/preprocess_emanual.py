# -*- coding: utf-8 -*-
"""
eManual (RAGBench) 预处理脚本
eManual Preprocessing Script

将 RAGBench eManual 数据转换为统一 RAG 实验格式。

RAGBench 格式特点：
- 每条记录包含 question, context (多个 chunks), response
- context 是列表，每个 chunk 有 ID 标注
- 提供 TRACe 评估标签 (relevance, utilization, completeness 等)

用法 / Usage:
    python paper/experiments/scripts/preprocess_emanual.py
"""

import json
import os
from datasets import load_from_disk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")


def process_emanual():
    """处理 eManual (RAGBench) 数据集

    RAGBench 记录格式 (每条)：
    - question: 用户问题
    - contexts: 检索到的 context chunks 列表
    - context_ids: 每个 chunk 的 ID 列表 (如 ["0a", "0b", "1a", ...])
    - relevant_context_ids: 相关 chunk 的 ID 列表 (ground truth)
    - response: LLM 生成的回答
    - TRACe scores: relevance, utilization, completeness 等

    转换逻辑：
    - 所有 context chunks → corpus (按 text 去重)
    - questions → queries
    - relevant_context_ids → ground truth chunk IDs
    """
    print("=" * 60)
    print("预处理 eManual (RAGBench) 数据集...")
    print("=" * 60)

    raw_path = os.path.join(RAW_DIR, "emanual")
    dataset = load_from_disk(raw_path)

    corpus = []
    queries = []
    chunk_text_to_id = {}

    for split_name in dataset.keys():
        split_data = dataset[split_name]

        # 检查字段名（RAGBench 格式可能有变化）
        if len(split_data) > 0:
            sample = split_data[0]
            print(f"  {split_name} 字段: {list(sample.keys())}")

        for idx, example in enumerate(split_data):
            question = example.get("question", "")
            contexts = example.get("contexts", [])
            context_ids = example.get("context_ids", [])
            relevant_ids = example.get("relevant_context_ids", [])
            response = example.get("response", "")

            # 处理 contexts 格式：可能是嵌套列表 [[id, text], ...]
            chunk_id_map = {}
            if contexts and isinstance(contexts[0], list):
                for item in contexts:
                    cid, text = item[0], item[1]
                    if text not in chunk_text_to_id:
                        unified_id = f"emanual_c{len(chunk_text_to_id):05d}"
                        chunk_text_to_id[text] = unified_id
                        corpus.append({
                            "chunk_id": unified_id,
                            "text": text,
                            "doc_id": f"emanual_doc",
                            "metadata": {
                                "source": "emanual",
                                "original_id": cid,
                                "split": split_name,
                            },
                        })
                    chunk_id_map[cid] = chunk_text_to_id[text]
            elif contexts and isinstance(contexts[0], str):
                for i, text in enumerate(contexts):
                    cid = context_ids[i] if i < len(context_ids) else f"{i}"
                    if text not in chunk_text_to_id:
                        unified_id = f"emanual_c{len(chunk_text_to_id):05d}"
                        chunk_text_to_id[text] = unified_id
                        corpus.append({
                            "chunk_id": unified_id,
                            "text": text,
                            "doc_id": f"emanual_doc",
                            "metadata": {
                                "source": "emanual",
                                "original_id": cid,
                                "split": split_name,
                            },
                        })
                    chunk_id_map[cid] = chunk_text_to_id[text]

            # 映射 relevant_context_ids 到统一 ID
            gt_chunk_ids = []
            if relevant_ids:
                for rid in relevant_ids:
                    if rid in chunk_id_map:
                        gt_chunk_ids.append(chunk_id_map[rid])

            query_id = f"emanual_q{len(queries):05d}"
            queries.append({
                "query_id": query_id,
                "text": question,
                "ground_truth_chunk_ids": gt_chunk_ids,
                "answer": response,
                "split": split_name,
                "metadata": {
                    "source": "emanual",
                    "has_relevant": len(gt_chunk_ids) > 0,
                },
            })

    # 保存
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    corpus_path = os.path.join(PROCESSED_DIR, "emanual_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, "emanual_queries.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    with_gt = sum(1 for q in queries if q["ground_truth_chunk_ids"])
    print(f"\n  Corpus chunks: {len(corpus)}")
    print(f"  Queries: {len(queries)} (with GT: {with_gt})")
    print(f"  已保存到: {PROCESSED_DIR}/emanual_*.json")


if __name__ == "__main__":
    process_emanual()
