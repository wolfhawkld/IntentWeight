#!/usr/bin/env python3
"""
构建 CMID 中文医学数据集知识库

数据格式：
- text: 问题文本
- label_4: 4类粗分类 (病症/药物/治疗方案/其他)
- label_36: 36类细分类

需要手动划分 train/test
"""

import json
import argparse
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = Path(__file__).parent.parent / "results"
DATA_DIR = PROJECT_ROOT / "pre_validation" / "data" / "cmid"
EMBEDDINGS_DIR = PROJECT_ROOT / "pre_validation" / "embeddings"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_size", type=float, default=0.2, help="测试集比例")
    args = parser.parse_args()
    
    print("=" * 60)
    print("构建 CMID 中文医学数据集知识库")
    print("=" * 60)
    
    # 加载原始数据
    with open(DATA_DIR / "cmid_processed.json", "r", encoding="utf-8") as f:
        samples = json.load(f)
    print(f"✓ 加载样本: {len(samples)}")
    
    # 加载 embeddings
    embeddings = np.load(EMBEDDINGS_DIR / "cmid_embeddings.npy")
    print(f"✓ 加载 embeddings: {embeddings.shape}")
    
    # 提取标签（使用 label_4 作为意图）
    texts = [s["text"] for s in samples]
    labels = [s["label_4"] for s in samples]
    
    # 划分 train/test
    train_indices, test_indices = train_test_split(
        range(len(samples)), 
        test_size=args.test_size, 
        random_state=42,
        stratify=labels  # 保持类别分布
    )
    
    train_indices = list(train_indices)
    test_indices = list(test_indices)
    
    print(f"✓ Train: {len(train_indices)}, Test: {len(test_indices)}")
    
    # 构建知识库
    train_samples = [samples[i] for i in train_indices]
    train_embeddings = embeddings[train_indices]
    test_samples = [samples[i] for i in test_indices]
    test_embeddings = embeddings[test_indices]
    
    knowledge_base = {
        "chunks": [],
        "metadata": {
            "num_chunks": len(train_samples),
            "embedding_dim": train_embeddings.shape[1],
            "language": "chinese",
            "domain": "medical"
        }
    }
    
    for i, sample in enumerate(train_samples):
        chunk = {
            "chunk_id": f"chunk_{i:05d}",
            "text": sample["text"],
            "intent": sample["label_4"],  # 使用 4 分类
            "intent_fine": sample["label_36"],  # 细分类
            "embedding_idx": i
        }
        knowledge_base["chunks"].append(chunk)
    
    # 保存
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    kb_path = RESULTS_DIR / "knowledge_base_cmid.json"
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    print(f"✓ 知识库保存到: {kb_path}")
    
    train_emb_path = RESULTS_DIR / "train_embeddings_cmid.npy"
    np.save(train_emb_path, train_embeddings)
    print(f"✓ Train embedding: {train_emb_path}")
    
    test_data = {
        "queries": [
            {
                "query_id": f"query_{i:05d}",
                "text": sample["text"],
                "intent": sample["label_4"],
                "intent_fine": sample["label_36"],
                "embedding_idx": i
            }
            for i, sample in enumerate(test_samples)
        ],
        "metadata": {
            "num_queries": len(test_samples)
        }
    }
    test_path = RESULTS_DIR / "test_queries_cmid.json"
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 测试数据: {test_path}")
    
    test_emb_path = RESULTS_DIR / "test_embeddings_cmid.npy"
    np.save(test_emb_path, test_embeddings)
    print(f"✓ Test embedding: {test_emb_path}")
    
    # 统计
    from collections import Counter
    train_labels = Counter([s["label_4"] for s in train_samples])
    test_labels = Counter([s["label_4"] for s in test_samples])
    
    print("\n标签分布:")
    print("Train:", dict(train_labels))
    print("Test:", dict(test_labels))
    
    print("\n✓ CMID 知识库构建完成!")


if __name__ == "__main__":
    main()