#!/usr/bin/env python3
"""
Phase 2: 构建知识库

将 Train 样本作为 RAG 知识库，生成结构化知识库文件

输入:
  - processed/{dataset}_processed.json
  - embeddings/{dataset}_embeddings.npy

输出:
  - results/knowledge_base_{dataset}.json
"""

import os
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
PRE_VALIDATION_DIR = PROJECT_ROOT / "pre_validation"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_processed_data(dataset: str) -> Tuple[List[Dict], np.ndarray]:
    """
    加载预处理数据和 embedding
    
    Args:
        dataset: 数据集名称
    
    Returns:
        (samples, embeddings)
    """
    # 加载预处理数据
    processed_path = PRE_VALIDATION_DIR / "processed" / f"{dataset}_processed.json"
    with open(processed_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
    
    # 加载 embedding
    embedding_path = PRE_VALIDATION_DIR / "embeddings" / f"{dataset}_embeddings.npy"
    embeddings = np.load(embedding_path)
    
    print(f"✓ 加载 {dataset}: {len(samples)} 样本, embedding shape: {embeddings.shape}")
    
    return samples, embeddings


def split_train_test(
    samples: List[Dict],
    embeddings: np.ndarray,
    dataset: str
) -> Tuple[List[Dict], np.ndarray, List[Dict], np.ndarray]:
    """
    划分训练集（知识库）和测试集（问题）
    
    Args:
        samples: 样本列表
        embeddings: embedding 矩阵
        dataset: 数据集名称
    
    Returns:
        (train_samples, train_embeddings, test_samples, test_embeddings)
    """
    # 根据数据集划分
    train_indices = []
    test_indices = []
    
    for i, sample in enumerate(samples):
        if sample.get("split") == "train":
            train_indices.append(i)
        else:
            test_indices.append(i)
    
    # 提取
    train_samples = [samples[i] for i in train_indices]
    train_embeddings = embeddings[train_indices]
    test_samples = [samples[i] for i in test_indices]
    test_embeddings = embeddings[test_indices]
    
    print(f"  Train (知识库): {len(train_samples)} 样本")
    print(f"  Test (问题): {len(test_samples)} 样本")
    
    return train_samples, train_embeddings, test_samples, test_embeddings


def build_knowledge_base(
    train_samples: List[Dict],
    train_embeddings: np.ndarray
) -> Dict:
    """
    构建知识库结构
    
    Args:
        train_samples: 训练样本
        train_embeddings: 训练 embedding
    
    Returns:
        知识库字典
    """
    knowledge_base = {
        "chunks": [],
        "metadata": {
            "num_chunks": len(train_samples),
            "embedding_dim": train_embeddings.shape[1]
        }
    }
    
    for i, sample in enumerate(train_samples):
        chunk = {
            "chunk_id": f"chunk_{i:05d}",
            "text": sample["text"],
            "intent": sample["label"],
            "embedding_idx": i
        }
        knowledge_base["chunks"].append(chunk)
    
    return knowledge_base


def save_knowledge_base(
    knowledge_base: Dict,
    train_embeddings: np.ndarray,
    test_samples: List[Dict],
    test_embeddings: np.ndarray,
    dataset: str
):
    """
    保存知识库和测试数据
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存知识库
    kb_path = RESULTS_DIR / f"knowledge_base_{dataset}.json"
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    print(f"✓ 知识库保存到: {kb_path}")
    
    # 保存训练 embedding
    train_emb_path = RESULTS_DIR / f"train_embeddings_{dataset}.npy"
    np.save(train_emb_path, train_embeddings)
    print(f"✓ Train embedding 保存到: {train_emb_path}")
    
    # 保存测试数据
    test_data = {
        "queries": [
            {
                "query_id": f"query_{i:05d}",
                "text": sample["text"],
                "intent": sample["label"],
                "embedding_idx": i
            }
            for i, sample in enumerate(test_samples)
        ],
        "metadata": {
            "num_queries": len(test_samples)
        }
    }
    test_path = RESULTS_DIR / f"test_queries_{dataset}.json"
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 测试数据保存到: {test_path}")
    
    # 保存测试 embedding
    test_emb_path = RESULTS_DIR / f"test_embeddings_{dataset}.npy"
    np.save(test_emb_path, test_embeddings)
    print(f"✓ Test embedding 保存到: {test_emb_path}")


def main():
    parser = argparse.ArgumentParser(description="构建知识库")
    parser.add_argument("--dataset", type=str, required=True,
                        choices=["banking77", "clinc150"],
                        help="数据集名称")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Phase 2 Step 1: 构建知识库 - {args.dataset}")
    print("=" * 60)
    
    # 加载数据
    samples, embeddings = load_processed_data(args.dataset)
    
    # 划分训练集和测试集
    train_samples, train_embeddings, test_samples, test_embeddings = \
        split_train_test(samples, embeddings, args.dataset)
    
    # 构建知识库
    knowledge_base = build_knowledge_base(train_samples, train_embeddings)
    
    # 保存
    save_knowledge_base(
        knowledge_base,
        train_embeddings,
        test_samples,
        test_embeddings,
        args.dataset
    )
    
    print("\n✓ 知识库构建完成!")


if __name__ == "__main__":
    main()