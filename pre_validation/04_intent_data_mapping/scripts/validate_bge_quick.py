#!/usr/bin/env python3
"""
BGE embedding 完整验证流程
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan

PROJECT_ROOT = Path(__file__).parent.parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
DATA_DIR = PROJECT_ROOT / "data" / "cmid"
RESULTS_DIR = Path(__file__).parent.parent / "results"

def main():
    print("=" * 70)
    print("BGE-large-zh CMID 完整验证 (2000 样本)")
    print("=" * 70)
    
    # 加载 embedding
    embeddings = np.load(EMBEDDINGS_DIR / "cmid_bge_embeddings_2k.npy")
    
    # 加载原始数据
    with open(DATA_DIR / "cmid_processed.json", "r", encoding="utf-8") as f:
        all_samples = json.load(f)
    
    samples = all_samples[:2000]
    texts = [s["text"] for s in samples]
    labels = [s["label_4"] for s in samples]
    
    print(f"✓ 样本数: {len(samples)}")
    print(f"✓ Embedding shape: {embeddings.shape}")
    
    # 划分 train/test
    train_idx, test_idx = train_test_split(range(len(samples)), test_size=0.2, random_state=42)
    train_idx, test_idx = list(train_idx), list(test_idx)
    
    train_embeddings = embeddings[train_idx]
    test_embeddings = embeddings[test_idx]
    train_labels = [labels[i] for i in train_idx]
    test_labels = [labels[i] for i in test_idx]
    
    print(f"✓ Train: {len(train_idx)}, Test: {len(test_idx)}")
    
    # 训练集聚类
    print("\n" + "=" * 70)
    print("Step 1: HDBSCAN 聚类")
    print("=" * 70)
    
    clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=5, metric='euclidean')
    train_clusters = clusterer.fit_predict(train_embeddings)
    
    n_clusters = len(set(train_clusters)) - (1 if -1 in train_clusters else 0)
    n_noise = list(train_clusters).count(-1)
    
    print(f"簇数量: {n_clusters}")
    print(f"噪声点: {n_noise} ({n_noise/len(train_clusters)*100:.1f}%)")
    
    # 构建映射
    print("\n" + "=" * 70)
    print("Step 2: 构建意图-簇映射")
    print("=" * 70)
    
    # intent -> cluster_ids
    intent_to_clusters = defaultdict(list)
    for i, (label, cluster_id) in enumerate(zip(train_labels, train_clusters)):
        if cluster_id != -1:
            intent_to_clusters[label].append(cluster_id)
    
    # cluster_id -> chunk_indices
    cluster_to_indices = defaultdict(list)
    for i, cluster_id in enumerate(train_clusters):
        if cluster_id != -1:
            cluster_to_indices[cluster_id].append(i)
    
    # 计算每个簇纯度
    cluster_purities = {}
    for cluster_id, indices in cluster_to_indices.items():
        cluster_labels = [train_labels[i] for i in indices]
        counter = Counter(cluster_labels)
        purity = counter.most_common(1)[0][1] / len(cluster_labels)
        cluster_purities[cluster_id] = purity
    
    avg_purity = np.mean(list(cluster_purities.values()))
    print(f"平均聚类纯度: {avg_purity:.2%}")
    
    # 评估
    print("\n" + "=" * 70)
    print("Step 3: 检索评估")
    print("=" * 70)
    
    # 归一化
    train_norm = train_embeddings / np.linalg.norm(train_embeddings, axis=1, keepdims=True)
    test_norm = test_embeddings / np.linalg.norm(test_embeddings, axis=1, keepdims=True)
    
    # 1. 纯语义检索
    print("\n[方法1: 纯语义检索]")
    top_k_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    mrr_sum = 0.0
    
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        similarities = np.dot(query_emb, train_norm.T)[0]
        top_indices = np.argsort(similarities)[::-1][:10]
        
        for k in top_k_hits.keys():
            retrieved_labels = [train_labels[idx] for idx in top_indices[:k]]
            if query_label in retrieved_labels:
                top_k_hits[k] += 1
        
        for rank, idx in enumerate(top_indices, 1):
            if train_labels[idx] == query_label:
                mrr_sum += 1.0 / rank
                break
    
    pure_metrics = {
        "top_1": top_k_hits[1] / len(test_idx),
        "top_5": top_k_hits[5] / len(test_idx),
        "mrr": mrr_sum / len(test_idx)
    }
    
    print(f"  Top-1: {pure_metrics['top_1']:.1%}")
    print(f"  Top-5: {pure_metrics['top_5']:.1%}")
    print(f"  MRR: {pure_metrics['mrr']:.3f}")
    
    # 2. 簇筛选 + 语义检索
    print("\n[方法2: 簇筛选 + 语义检索]")
    top_k_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    mrr_sum = 0.0
    
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        
        # 筛选相关簇
        predicted_clusters = intent_to_clusters.get(query_label, [])[:3]
        if predicted_clusters:
            candidate_indices = []
            for cid in predicted_clusters:
                candidate_indices.extend(cluster_to_indices.get(cid, []))
            if not candidate_indices:
                candidate_indices = list(range(len(train_idx)))
        else:
            candidate_indices = list(range(len(train_idx)))
        
        # 簇内检索
        candidate_embeddings = train_norm[candidate_indices]
        similarities = np.dot(query_emb, candidate_embeddings.T)[0]
        top_local_indices = np.argsort(similarities)[::-1][:10]
        top_indices = [candidate_indices[idx] for idx in top_local_indices]
        
        for k in top_k_hits.keys():
            retrieved_labels = [train_labels[idx] for idx in top_indices[:k]]
            if query_label in retrieved_labels:
                top_k_hits[k] += 1
        
        for rank, idx in enumerate(top_indices, 1):
            if train_labels[idx] == query_label:
                mrr_sum += 1.0 / rank
                break
    
    cluster_metrics = {
        "top_1": top_k_hits[1] / len(test_idx),
        "top_5": top_k_hits[5] / len(test_idx),
        "mrr": mrr_sum / len(test_idx)
    }
    
    print(f"  Top-1: {cluster_metrics['top_1']:.1%}")
    print(f"  Top-5: {cluster_metrics['top_5']:.1%}")
    print(f"  MRR: {cluster_metrics['mrr']:.3f}")
    
    # 对比
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)
    
    print(f"\n{'方法':<30} {'Top-1':>10} {'Top-5':>10} {'MRR':>10}")
    print("-" * 70)
    print(f"{'纯语义检索':<30} {pure_metrics['top_1']:>10.1%} {pure_metrics['top_5']:>10.1%} {pure_metrics['mrr']:>10.3f}")
    print(f"{'簇筛选 + 语义检索':<30} {cluster_metrics['top_1']:>10.1%} {cluster_metrics['top_5']:>10.1%} {cluster_metrics['mrr']:>10.3f}")
    
    print(f"\n提升:")
    print(f"  Top-1: +{(cluster_metrics['top_1'] - pure_metrics['top_1'])*100:.1f}%")
    print(f"  Top-5: +{(cluster_metrics['top_5'] - pure_metrics['top_5'])*100:.1f}%")
    
    # 与 MiniLM 对比
    print("\n" + "=" * 70)
    print("与 all-MiniLM-L6-v2 对比")
    print("=" * 70)
    
    print(f"\n{'指标':<20} {'MiniLM':>15} {'BGE':>15} {'提升':>15}")
    print("-" * 70)
    print(f"{'聚类纯度':<20} {'66.0%':>15} {f'{avg_purity:.1%}':>15} {f'+{(avg_purity-0.66)*100:.1f}%':>15}")
    print(f"{'噪声点':<20} {'76.0%':>15} {f'{n_noise/len(train_clusters):.1%}':>15} {f'{(n_noise/len(train_clusters)-0.76)*100:.1f}%':>15}")
    
    print("\n✓ 验证完成!")


if __name__ == "__main__":
    main()