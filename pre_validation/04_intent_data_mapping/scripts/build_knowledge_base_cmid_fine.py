#!/usr/bin/env python3
"""
构建 CMID 细分类知识库（使用 40 类细分类）
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
    print("=" * 60)
    print("构建 CMID 细分类知识库 (40类)")
    print("=" * 60)
    
    # 加载原始数据
    with open(DATA_DIR / "cmid_processed.json", "r", encoding="utf-8") as f:
        samples = json.load(f)
    print(f"✓ 加载样本: {len(samples)}")
    
    # 加载 embeddings
    embeddings = np.load(EMBEDDINGS_DIR / "cmid_embeddings.npy")
    print(f"✓ 加载 embeddings: {embeddings.shape}")
    
    # 使用细分类作为意图
    labels = [s["label_36"] for s in samples]
    
    # 划分 train/test（不用分层，因为有些类样本太少）
    train_indices, test_indices = train_test_split(
        range(len(samples)), 
        test_size=0.2, 
        random_state=42
    )
    
    train_indices = list(train_indices)
    test_indices = list(test_indices)
    
    print(f"✓ Train: {len(train_indices)}, Test: {len(test_indices)}")
    
    # 构建
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
            "domain": "medical",
            "use_fine_grained": True
        }
    }
    
    for i, sample in enumerate(train_samples):
        chunk = {
            "chunk_id": f"chunk_{i:05d}",
            "text": sample["text"],
            "intent": sample["label_36"],  # 使用细分类
            "intent_coarse": sample["label_4"],
            "embedding_idx": i
        }
        knowledge_base["chunks"].append(chunk)
    
    # 保存
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    kb_path = RESULTS_DIR / "knowledge_base_cmid_fine.json"
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    print(f"✓ 知识库保存到: {kb_path}")
    
    train_emb_path = RESULTS_DIR / "train_embeddings_cmid_fine.npy"
    np.save(train_emb_path, train_embeddings)
    
    test_data = {
        "queries": [
            {
                "query_id": f"query_{i:05d}",
                "text": sample["text"],
                "intent": sample["label_36"],
                "intent_coarse": sample["label_4"],
                "embedding_idx": i
            }
            for i, sample in enumerate(test_samples)
        ],
        "metadata": {"num_queries": len(test_samples)}
    }
    test_path = RESULTS_DIR / "test_queries_cmid_fine.json"
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    test_emb_path = RESULTS_DIR / "test_embeddings_cmid_fine.npy"
    np.save(test_emb_path, test_embeddings)
    
    # 统计
    from collections import Counter
    train_labels = Counter([s["label_36"] for s in train_samples])
    print(f"\n细分类数量: {len(train_labels)}")
    print(f"Top 5: {train_labels.most_common(5)}")
    
    print("\n✓ 完成!")


if __name__ == "__main__":
    main()