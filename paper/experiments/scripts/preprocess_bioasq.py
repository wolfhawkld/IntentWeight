# -*- coding: utf-8 -*-
"""
BioASQ 预处理脚本
BioASQ Preprocessing Script

将 BioASQ 数据转换为统一 RAG 实验格式。

BioASQ 格式特点：
- question + type (factoid/list/yesno/summary)
- documents: 相关 PubMed 文档 URL 列表
- snippets: 相关文档的摘录片段 (含 document URI + text + offset)
- exact_answer / ideal_answer

注意: BioASQ 完整数据需注册 (bioasq.org)
HuggingFace 上有 bigbio/bioasq_task_b 子集

用法 / Usage:
    python paper/experiments/scripts/preprocess_bioasq.py
"""

import json
import os
from datasets import load_from_disk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")


def process_bioasq():
    """处理 BioASQ 数据集

    BioASQ Task B 记录格式：
    - body: 问题文本
    - type: factoid / list / yesno / summary
    - documents: 相关文档 PubMed URL 列表
    - snippets: [{"document": url, "text": snippet_text, ...}, ...]
    - exact_answer: 精确答案（factoid/list/yesno）
    - ideal_answer: 理想答案（段落级摘要）
    """
    print("=" * 60)
    print("预处理 BioASQ 数据集...")
    print("=" * 60)

    raw_path = os.path.join(RAW_DIR, "bioasq")
    if not os.path.exists(raw_path):
        print(f"  未找到: {raw_path}")
        print("  BioASQ 需手动下载，或使用 HuggingFace bigbio/bioasq_task_b")
        print("  尝试从 HuggingFace 加载...")
        try:
            from datasets import load_dataset
            dataset = load_dataset("bigbio/bioasq_task_b", "bioasq_task_b_source")
            dataset.save_to_disk(raw_path)
        except Exception as e:
            print(f"  加载失败: {e}")
            print("  请手动下载 BioASQ 数据集后放到: data/raw/bioasq/")
            return

    dataset = load_from_disk(raw_path)

    corpus = []
    queries = []
    chunk_text_to_id = {}

    for split_name in dataset.keys():
        split_data = dataset[split_name]

        if len(split_data) > 0:
            sample = split_data[0]
            print(f"  {split_name} 字段: {list(sample.keys())}")

        for idx, example in enumerate(split_data):
            # 字段名可能因 bigbio 版本不同而变化
            question = (
                example.get("body", "")
                or example.get("question", "")
                or example.get("text", "")
            )
            q_type = example.get("type", "unknown")
            snippets = example.get("snippets", [])
            exact_answer = example.get("exact_answer", "")
            ideal_answer = example.get("ideal_answer", "")

            # 处理 exact_answer 格式（可能是列表）
            if isinstance(exact_answer, list):
                if len(exact_answer) > 0 and isinstance(exact_answer[0], list):
                    exact_answer = "; ".join(
                        a for sublist in exact_answer for a in sublist
                    )
                else:
                    exact_answer = "; ".join(str(a) for a in exact_answer)
            if isinstance(ideal_answer, list):
                ideal_answer = " ".join(str(a) for a in ideal_answer)

            # snippets → corpus chunks
            gt_chunk_ids = []
            for snippet in snippets:
                if isinstance(snippet, dict):
                    text = snippet.get("text", "")
                    doc_uri = snippet.get("document", "")
                elif isinstance(snippet, str):
                    text = snippet
                    doc_uri = ""
                else:
                    continue

                if not text or not text.strip():
                    continue

                if text not in chunk_text_to_id:
                    chunk_id = f"bioasq_c{len(chunk_text_to_id):05d}"
                    chunk_text_to_id[text] = chunk_id
                    corpus.append({
                        "chunk_id": chunk_id,
                        "text": text,
                        "doc_id": doc_uri,
                        "metadata": {
                            "source": "bioasq",
                            "split": split_name,
                        },
                    })
                gt_chunk_ids.append(chunk_text_to_id[text])

            query_id = f"bioasq_q{len(queries):05d}"
            queries.append({
                "query_id": query_id,
                "text": question,
                "ground_truth_chunk_ids": gt_chunk_ids,
                "answer": exact_answer or ideal_answer,
                "split": split_name,
                "metadata": {
                    "source": "bioasq",
                    "type": q_type,
                    "ideal_answer": ideal_answer,
                },
            })

    # 保存
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    corpus_path = os.path.join(PROCESSED_DIR, "bioasq_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, "bioasq_queries.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    with_gt = sum(1 for q in queries if q["ground_truth_chunk_ids"])
    print(f"\n  Corpus chunks: {len(corpus)}")
    print(f"  Queries: {len(queries)} (with GT: {with_gt})")
    print(f"  Question types: {dict(sorted({q['metadata']['type'] for q in queries}))}" if queries else "")
    print(f"  已保存到: {PROCESSED_DIR}/bioasq_*.json")


if __name__ == "__main__":
    process_bioasq()
