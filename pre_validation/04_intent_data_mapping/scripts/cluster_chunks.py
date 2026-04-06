#!/usr/bin/env python3
"""
Phase 2: Chunk 聚类

对知识库 chunks 进行聚类，生成数据簇

输入:
  - results/knowledge_base_{dataset}.json
  - results/train_embeddings_{dataset}.npy

输出:
  - results/clusters_{dataset}.json
"""

import os
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_knowledge_base(dataset: str) -> tuple:
    """
    加载知识库和 embedding
    
    Returns:
        (knowledge_base, embeddings)
    """
    # 加载知识库
    kb_path = RESULTS_DIR / f"knowledge_base_{dataset}.json"
    with open(kb_path, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
    
    # 加载 embedding
    emb_path = RESULTS_DIR / f"train_embeddings_{dataset}.npy"
    embeddings = np.load(emb_path)
    
    print(f"✓ 加载知识库: {len(knowledge_base['chunks'])} chunks")
    print(f"✓ 加载 embedding: shape={embeddings.shape}")
    
    return knowledge_base, embeddings


def cluster_chunks(
    embeddings: np.ndarray,
    min_cluster_size: int = 10,
    min_samples: int = 5
) -> np.ndarray:
    """
    对 chunks 进行 HDBSCAN 聚类
    
    Args:
        embeddings: chunk embeddings
        min_cluster_size: 最小簇大小
        min_samples: HDBSCAN min_samples
    
    Returns:
        cluster_labels: 每个样本的簇标签 (-1 表示噪声)
    """
    import hdbscan
    
    print(f"\n运行 HDBSCAN 聚类...")
    print(f"  min_cluster_size={min_cluster_size}, min_samples={min_samples}")
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean"
    )
    
    cluster_labels = clusterer.fit_predict(embeddings)
    
    # 统计
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = np.sum(cluster_labels == -1)
    
    print(f"\n聚类结果:")
    print(f"  簇数量: {n_clusters}")
    print(f"  噪声点: {n_noise} ({100*n_noise/len(cluster_labels):.1f}%)")
    
    return cluster_labels


def analyze_clusters(
    knowledge_base: Dict,
    cluster_labels: np.ndarray
) -> Dict:
    """
    分析聚类结果
    
    Returns:
        cluster_info: 簇信息
    """
    chunks = knowledge_base["chunks"]
    
    # 按簇分组
    cluster_chunks = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        if label != -1:  # 排除噪声
            cluster_chunks[int(label)].append(chunks[i])
    
    # 分析每个簇
    cluster_info = {
        "clusters": [],
        "metadata": {
            "num_clusters": len(cluster_chunks),
            "num_noise": int(np.sum(cluster_labels == -1))
        }
    }
    
    for cluster_id, chunk_list in sorted(cluster_chunks.items()):
        # 统计 intent 分布
        intent_counts = defaultdict(int)
        for chunk in chunk_list:
            intent_counts[chunk["intent"]] += 1
        
        # 找到主导 intent
        dominant_intent = max(intent_counts.items(), key=lambda x: x[1])
        purity = dominant_intent[1] / len(chunk_list)
        
        cluster = {
            "cluster_id": cluster_id,
            "size": len(chunk_list),
            "dominant_intent": dominant_intent[0],
            "dominant_intent_count": dominant_intent[1],
            "purity": purity,
            "intent_distribution": dict(intent_counts),
            "chunk_ids": [c["chunk_id"] for c in chunk_list]
        }
        cluster_info["clusters"].append(cluster)
    
    # 计算平均纯度
    avg_purity = np.mean([c["purity"] for c in cluster_info["clusters"]])
    cluster_info["metadata"]["avg_purity"] = avg_purity
    
    print(f"\n簇分析:")
    print(f"  平均纯度: {avg_purity:.2%}")
    print(f"  纯度 > 80%: {sum(1 for c in cluster_info['clusters'] if c['purity'] > 0.8)} 个簇")
    print(f"  纯度 > 90%: {sum(1 for c in cluster_info['clusters'] if c['purity'] > 0.9)} 个簇")
    
    return cluster_info


def save_cluster_results(cluster_info: Dict, dataset: str):
    """
    保存聚类结果
    """
    output_path = RESULTS_DIR / f"clusters_{dataset}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cluster_info, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 聚类结果保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Chunk 聚类")
    parser.add_argument("--dataset", type=str, required=True,
                        choices=["banking77", "clinc150"],
                        help="数据集名称")
    parser.add_argument("--min_cluster_size", type=int, default=10,
                        help="最小簇大小")
    parser.add_argument("--min_samples", type=int, default=5,
                        help="HDBSCAN min_samples")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Phase 2 Step 2: Chunk 聚类 - {args.dataset}")
    print("=" * 60)
    
    # 加载知识库
    knowledge_base, embeddings = load_knowledge_base(args.dataset)
    
    # 聚类
    cluster_labels = cluster_chunks(
        embeddings,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples
    )
    
    # 分析
    cluster_info = analyze_clusters(knowledge_base, cluster_labels)
    
    # 保存
    save_cluster_results(cluster_info, args.dataset)
    
    print("\n✓ 聚类完成!")


if __name__ == "__main__":
    main()