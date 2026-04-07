#!/usr/bin/env python3
"""
无标签场景验证 - 聚类即意图

核心思路:
1. 不使用数据集的意图标签
2. 只用聚类发现"隐式意图"
3. 查询 → 找相似簇 → 簇内检索
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
DATA_DIR = PROJECT_ROOT / "data" / "cmid"

def main():
    print("=" * 70)
    print("无标签场景验证 - 聚类即意图")
    print("=" * 70)
    
    # 加载 BGE embedding
    embeddings = np.load(EMBEDDINGS_DIR / "cmid_bge_embeddings_2k.npy")
    
    # 加载数据 (只用文本，不用标签)
    with open(DATA_DIR / "cmid_processed.json", "r", encoding="utf-8") as f:
        samples = json.load(f)[:2000]
    
    texts = [s["text"] for s in samples]
    labels = [s["label_4"] for s in samples]  # 只用于评估，不用于训练
    
    print(f"\n✓ 样本数: {len(texts)}")
    print(f"✓ Embedding shape: {embeddings.shape}")
    
    # 划分 train/test
    train_idx, test_idx = train_test_split(range(len(samples)), test_size=0.2, random_state=42)
    train_idx, test_idx = list(train_idx), list(test_idx)
    
    train_emb = embeddings[train_idx]
    test_emb = embeddings[test_idx]
    train_texts = [texts[i] for i in train_idx]
    test_texts = [texts[i] for i in test_idx]
    train_labels = [labels[i] for i in train_idx]
    test_labels = [labels[i] for i in test_idx]
    
    print(f"✓ Train: {len(train_idx)}, Test: {len(test_idx)}")
    
    # Step 1: 无监督聚类
    print("\n" + "=" * 70)
    print("Step 1: 无监督聚类 (发现隐式意图)")
    print("=" * 70)
    
    # 尝试不同参数
    print("\n聚类参数探索:")
    best_purity = 0
    best_min_size = 10
    
    for min_size in [5, 10, 15, 20]:
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_size, min_samples=3, metric='euclidean')
        pred = clusterer.fit_predict(train_emb)
        n_clusters = len(set(pred)) - (1 if -1 in pred else 0)
        noise = list(pred).count(-1) / len(pred)
        
        # 计算簇内一致性 (用标签评估，但不用于训练)
        cluster_labels = defaultdict(list)
        for i, (c, l) in enumerate(zip(pred, train_labels)):
            if c != -1:
                cluster_labels[c].append(l)
        
        purities = []
        for c, label_list in cluster_labels.items():
            counter = Counter(label_list)
            purity = counter.most_common(1)[0][1] / len(label_list)
            purities.append(purity)
        
        avg_purity = np.mean(purities) if purities else 0
        
        print(f"  min_size={min_size}: {n_clusters} 簇, 噪声 {noise:.1%}, 一致性 {avg_purity:.1%}")
        
        if avg_purity > best_purity:
            best_purity = avg_purity
            best_min_size = min_size
    
    # 用最佳参数重新聚类
    print(f"\n选择 min_size={best_min_size}")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=best_min_size, min_samples=3, metric='euclidean')
    train_clusters = clusterer.fit_predict(train_emb)
    
    n_clusters = len(set(train_clusters)) - (1 if -1 in train_clusters else 0)
    noise_ratio = list(train_clusters).count(-1) / len(train_clusters)
    
    print(f"\n最终聚类结果:")
    print(f"  簇数量: {n_clusters}")
    print(f"  噪声点: {noise_ratio:.1%}")
    
    # Step 2: 分析聚类结果
    print("\n" + "=" * 70)
    print("Step 2: 分析聚类发现的隐式意图")
    print("=" * 70)
    
    # 每个簇的内容
    cluster_to_texts = defaultdict(list)
    cluster_to_labels = defaultdict(list)
    
    for i, (c, text, label) in enumerate(zip(train_clusters, train_texts, train_labels)):
        if c != -1:
            cluster_to_texts[c].append(text)
            cluster_to_labels[c].append(label)
    
    # 展示 Top 5 大簇
    sorted_clusters = sorted(cluster_to_texts.items(), key=lambda x: -len(x[1]))[:5]
    
    print("\nTop 5 大簇:")
    for cluster_id, text_list in sorted_clusters:
        label_list = cluster_to_labels[cluster_id]
        counter = Counter(label_list)
        dominant_label = counter.most_common(1)[0][0]
        purity = counter.most_common(1)[0][1] / len(label_list)
        
        print(f"\n  簇 #{cluster_id} ({len(text_list)} 样本):")
        print(f"    主导标签: {dominant_label} ({purity:.0%})")
        print(f"    标签分布: {dict(counter)}")
        print(f"    样本示例:")
        for text in text_list[:3]:
            print(f"      - \"{text[:40]}...\"")
    
    # Step 3: 构建簇中心
    print("\n" + "=" * 70)
    print("Step 3: 构建簇中心 (用于在线召回)")
    print("=" * 70)
    
    cluster_centers = {}
    for cluster_id in set(train_clusters):
        if cluster_id == -1:
            continue
        indices = [i for i, c in enumerate(train_clusters) if c == cluster_id]
        cluster_centers[cluster_id] = np.mean(train_emb[indices], axis=0)
    
    print(f"✓ 簇中心数: {len(cluster_centers)}")
    
    # Step 4: 验证检索效果
    print("\n" + "=" * 70)
    print("Step 4: 检索效果对比")
    print("=" * 70)
    
    # 归一化
    train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
    test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)
    
    # 簇中心归一化
    cluster_center_norm = {}
    for cid, center in cluster_centers.items():
        cluster_center_norm[cid] = center / np.linalg.norm(center)
    
    # 方法1: 纯语义检索
    print("\n[方法1: 纯语义检索 - 基线]")
    top_k_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        similarities = np.dot(query_emb, train_norm.T)[0]
        top_indices = np.argsort(similarities)[::-1][:10]
        
        for k in top_k_hits.keys():
            retrieved_labels = [train_labels[idx] for idx in top_indices[:k]]
            if query_label in retrieved_labels:
                top_k_hits[k] += 1
    
    pure_metrics = {f"top_{k}": v/len(test_idx) for k, v in top_k_hits.items()}
    print(f"  Top-1: {pure_metrics['top_1']:.1%}")
    print(f"  Top-5: {pure_metrics['top_5']:.1%}")
    
    # 方法2: 簇召回 + 簇内检索 (无标签)
    print("\n[方法2: 簇召回 + 簇内检索 (无标签)]")
    
    top_k_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    total_candidates = 0
    
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        
        # 找 Top-3 最相似的簇
        cluster_sims = []
        for cid, center in cluster_center_norm.items():
            sim = np.dot(query_emb, center.reshape(1, -1).T)[0][0]
            cluster_sims.append((cid, sim))
        
        top_clusters = sorted(cluster_sims, key=lambda x: -x[1])[:3]
        
        # 收集这些簇的样本
        candidate_indices = []
        for cid, _ in top_clusters:
            indices = [j for j, c in enumerate(train_clusters) if c == cid]
            candidate_indices.extend(indices)
        
        total_candidates += len(candidate_indices)
        
        if not candidate_indices:
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
    
    cluster_metrics = {f"top_{k}": v/len(test_idx) for k, v in top_k_hits.items()}
    avg_candidates = total_candidates / len(test_idx)
    
    print(f"  Top-1: {cluster_metrics['top_1']:.1%}")
    print(f"  Top-5: {cluster_metrics['top_5']:.1%}")
    print(f"  平均候选数: {avg_candidates:.0f} ({avg_candidates/len(train_idx)*100:.1f}%)")
    
    # 总结
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)
    
    print(f"\n{'方法':<30} {'Top-1':>10} {'Top-5':>10} {'召回范围':>15}")
    print("-" * 70)
    print(f"{'纯语义检索':<30} {pure_metrics['top_1']:>10.1%} {pure_metrics['top_5']:>10.1%} {'100%':>15}")
    print(f"{'簇召回 + 簇内检索':<30} {cluster_metrics['top_1']:>10.1%} {cluster_metrics['top_5']:>10.1%} {f'{avg_candidates/len(train_idx)*100:.1f}%':>15}")
    
    print(f"\n关键发现:")
    if cluster_metrics['top_1'] > pure_metrics['top_1']:
        print(f"  ✅ 簇筛选有效: Top-1 提升 +{(cluster_metrics['top_1']-pure_metrics['top_1'])*100:.1f}%")
    else:
        print(f"  ⚠️ 簇筛选无效: Top-1 下降 {(cluster_metrics['top_1']-pure_metrics['top_1'])*100:.1f}%")
    
    print(f"  📊 召回范围缩小: {100*(1-avg_candidates/len(train_idx)):.0f}%")
    print(f"  🎯 发现 {n_clusters} 个隐式意图簇")
    
    # 验证假设: 聚类发现的意图是否和标签吻合
    print("\n" + "=" * 70)
    print("验证假设: 聚类发现是否和标签吻合?")
    print("=" * 70)
    
    # 计算每个簇的标签一致性
    purities = []
    for cluster_id, label_list in cluster_to_labels.items():
        counter = Counter(label_list)
        purity = counter.most_common(1)[0][1] / len(label_list)
        purities.append(purity)
    
    avg_purity = np.mean(purities)
    high_purity_clusters = sum(1 for p in purities if p > 0.7)
    
    print(f"\n簇标签一致性分析:")
    print(f"  平均一致性: {avg_purity:.1%}")
    print(f"  高一致性簇 (>70%): {high_purity_clusters}/{len(purities)}")
    
    if avg_purity > 0.7:
        print(f"\n✅ 结论: 聚类发现的隐式意图和真实标签高度吻合!")
        print(f"   → 即使没有标签，聚类也能有效发现数据的意图结构")
    else:
        print(f"\n⚠️ 结论: 聚类发现和标签不完全吻合")
        print(f"   → 可能原因: 数据语义结构复杂 / 标签设计不合理")
    
    print("\n✓ 验证完成!")


if __name__ == "__main__":
    main()