# -*- coding: utf-8 -*-
"""
PubMedQA 预处理脚本
PubMedQA Preprocessing Script

将 PubMedQA 转换为统一 RAG 实验格式。

PubMedQA 格式特点：
- pqa_labeled: 1K 专家标注 (question + context sections + long_answer + final_decision)
- pqa_artificial: 211.3K 自动生成 (同格式)
- context 是 abstract 的多个 section，每个 section = 1 个 chunk

用法 / Usage:
    python paper/experiments/scripts/preprocess_pubmedqa.py
    python paper/experiments/scripts/preprocess_pubmedqa.py --include-artificial
"""

import json
import os
import argparse
from datasets import load_from_disk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")


def process_pubmedqa_split(dataset_path, prefix, corpus, queries, chunk_text_to_id):
    """处理一个 PubMedQA 子集

    PubMedQA 记录格式：
    - pubid: PubMed ID
    - question: 研究问题（来自论文标题）
    - context: {"contexts": [...], "labels": [...], "meshes": [...]}
      contexts 是 abstract 的各个 section
    - long_answer: 结论段（abstract 的 conclusion）
    - final_decision: yes / no / maybe
    """
    dataset = load_from_disk(dataset_path)

    for split_name in dataset.keys():
        split_data = dataset[split_name]

        for idx, example in enumerate(split_data):
            pubid = str(example.get("pubid", idx))
            question = example.get("question", "")
            context = example.get("context", {})
            long_answer = example.get("long_answer", "")
            final_decision = example.get("final_decision", "")

            # context 结构：{"contexts": ["section1", "section2", ...], "labels": [...]}
            context_sections = []
            if isinstance(context, dict):
                context_sections = context.get("contexts", [])
            elif isinstance(context, list):
                context_sections = context

            # 每个 section → 1 个 corpus chunk
            gt_chunk_ids = []
            for sec_idx, section_text in enumerate(context_sections):
                if not section_text or not section_text.strip():
                    continue

                if section_text not in chunk_text_to_id:
                    chunk_id = f"{prefix}_c{len(chunk_text_to_id):06d}"
                    chunk_text_to_id[section_text] = chunk_id
                    corpus.append({
                        "chunk_id": chunk_id,
                        "text": section_text,
                        "doc_id": f"pmid_{pubid}",
                        "metadata": {
                            "source": "pubmedqa",
                            "pubid": pubid,
                            "section_idx": sec_idx,
                        },
                    })
                gt_chunk_ids.append(chunk_text_to_id[section_text])

            # long_answer (conclusion) 也加入 corpus
            if long_answer and long_answer.strip():
                if long_answer not in chunk_text_to_id:
                    chunk_id = f"{prefix}_c{len(chunk_text_to_id):06d}"
                    chunk_text_to_id[long_answer] = chunk_id
                    corpus.append({
                        "chunk_id": chunk_id,
                        "text": long_answer,
                        "doc_id": f"pmid_{pubid}",
                        "metadata": {
                            "source": "pubmedqa",
                            "pubid": pubid,
                            "is_conclusion": True,
                        },
                    })

            query_id = f"{prefix}_q{len(queries):06d}"
            queries.append({
                "query_id": query_id,
                "text": question,
                "ground_truth_chunk_ids": gt_chunk_ids,
                "answer": final_decision,
                "split": split_name,
                "metadata": {
                    "source": "pubmedqa",
                    "pubid": pubid,
                    "long_answer": long_answer,
                    "final_decision": final_decision,
                },
            })


def process_pubmedqa(include_artificial=False):
    """处理 PubMedQA 数据集"""
    print("=" * 60)
    print("预处理 PubMedQA 数据集...")
    if include_artificial:
        print("  (含 artificial 子集, 211K)")
    print("=" * 60)

    corpus = []
    queries = []
    chunk_text_to_id = {}

    # labeled 子集（必须）
    labeled_path = os.path.join(RAW_DIR, "pubmedqa_labeled")
    if os.path.exists(labeled_path):
        print("  处理 pqa_labeled...")
        process_pubmedqa_split(
            labeled_path, "pqa_l", corpus, queries, chunk_text_to_id
        )
        print(f"    chunks: {len(corpus)}, queries: {len(queries)}")
    else:
        print(f"  未找到: {labeled_path}")
        return

    # artificial 子集（可选，用于大规模在线学习模拟）
    if include_artificial:
        artificial_path = os.path.join(RAW_DIR, "pubmedqa_artificial")
        if os.path.exists(artificial_path):
            print("  处理 pqa_artificial (可能需要几分钟)...")
            process_pubmedqa_split(
                artificial_path, "pqa_a", corpus, queries, chunk_text_to_id
            )
            print(f"    chunks: {len(corpus)}, queries: {len(queries)}")
        else:
            print(f"  未找到 artificial 子集: {artificial_path}")

    # 保存
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    suffix = "_full" if include_artificial else ""
    corpus_path = os.path.join(PROCESSED_DIR, f"pubmedqa{suffix}_corpus.json")
    queries_path = os.path.join(PROCESSED_DIR, f"pubmedqa{suffix}_queries.json")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)

    with_gt = sum(1 for q in queries if q["ground_truth_chunk_ids"])
    unique_docs = len(set(c["doc_id"] for c in corpus))
    print(f"\n  Corpus chunks: {len(corpus)}")
    print(f"  Unique documents: {unique_docs}")
    print(f"  Queries: {len(queries)} (with GT: {with_gt})")
    print(f"  已保存到: {PROCESSED_DIR}/pubmedqa{suffix}_*.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="预处理 PubMedQA")
    parser.add_argument(
        "--include-artificial",
        action="store_true",
        help="包含 pqa_artificial 子集 (211K, 用于大规模在线学习模拟)",
    )
    args = parser.parse_args()
    process_pubmedqa(include_artificial=args.include_artificial)
