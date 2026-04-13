#!/usr/bin/env python3
"""
Phase 1F: 关键词先验直接验证

验证方式：对比三种簇选择策略的检索准确率
1. 随机选择簇
2. 基于先验权重选择簇（Phase 1F核心）
3. Oracle选择（选择正确簇）

作者: Damon + Nemesis
日期: 2026-04-13
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
RESULTS_DIR = PROJECT_ROOT / "04_intent_data_mapping" / "results"
KEYWORD_DIR = PROJECT_ROOT / "05_keyword_cluster" / "data" / "tagged_chunks"


def load_data():
    """加载数据"""
    train_emb = np.load(RESULTS_DIR / "train_embeddings_banking77.npy")
    test_emb = np.load(RESULTS_DIR / "test_embeddings_banking77.npy")

    with open(RESULTS_DIR / "knowledge_base_banking77.json", 'r') as f:
        kb = json.load(f)
    with open(RESULTS_DIR / "test_queries_banking77.json", 'r') as f:
        test_data = json.load(f)
    with open(RESULTS_DIR / "clusters_banking77.json", 'r') as f:
        cluster_data = json.load(f)

    # 关键词先验
    with open(KEYWORD_DIR / "banking77_keyword_tagged.json", 'r') as f:
        kw_data = json.load(f)
    linucb_prior = kw_data.get('linucb_prior', {})

    chunks = kb['chunks']
    test_queries = test_data['queries']
    clusters = cluster_data['clusters']

    # 映射
    chunk_id_to_emb_idx = {c['chunk_id']: c['embedding_idx'] for c in chunks}
    emb_idx_to_intent = {c['embedding_idx']: c['intent'] for c in chunks}

    cluster_to_indices = {}
    cluster_to_dominant_intent = {}
    cluster_to_purity = {}
    for cluster in clusters:
        c_id = cluster['cluster_id']
        indices = [chunk_id_to_emb_idx.get(cid) for cid in cluster['chunk_ids']
                   if chunk_id_to_emb_idx.get(cid) is not None]
        cluster_to_indices[c_id] = indices
        cluster_to_dominant_intent[c_id] = cluster['dominant_intent']
        cluster_to_purity[c_id] = cluster['purity']

    cluster_ids = sorted(cluster_to_indices.keys())
    n_clusters = len(cluster_ids)

    train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
    test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

    print(f"✓ 数据加载完成")
    print(f"  Train: {len(chunks)}, Test: {len(test_queries)}")
    print(f"  簇数: {n_clusters}")
    print(f"  先验簇数: {len(linucb_prior)}")

    return train_norm, test_norm, test_queries, cluster_to_indices, \
           cluster_to_dominant_intent, cluster_to_purity, cluster_ids, \
           emb_idx_to_intent, linucb_prior, n_clusters


def retrieve_in_cluster(query_emb, query_intent, cluster_id,
                        cluster_to_indices, train_norm, emb_idx_to_intent):
    """簇内检索"""
    indices = cluster_to_indices[cluster_id]
    if not indices:
        return -1

    cand_emb = train_norm[indices]
    sims = np.dot(query_emb, cand_emb.T)[0]

    # 意图加成
    intent_bonus = np.array([
        0.15 if emb_idx_to_intent.get(idx) == query_intent else 0.0
        for idx in indices
    ])
    adjusted = sims + intent_bonus
    top_idx = indices[np.argmax(adjusted)]
    return emb_idx_to_intent.get(top_idx, -1)


def select_cluster_random(cluster_ids):
    """策略1: 随机选择"""
    return np.random.choice(cluster_ids)


def select_cluster_by_prior(query_intent, cluster_ids, cluster_to_dominant_intent,
                            cluster_to_purity, linucb_prior, top_k=3):
    """策略2: 基于先验权重选择

    逻辑：
    1. 找到dominant_intent匹配query_intent的候选簇
    2. 在候选簇中，按先验权重排序选择
    """
    # 找intent匹配的簇
    matching_clusters = [
        c for c in cluster_ids
        if cluster_to_dominant_intent[c] == query_intent
    ]

    if not matching_clusters:
        # 无匹配簇，退化为全局选择高权重簇
        sorted_clusters = sorted(
            cluster_ids,
            key=lambda c: linucb_prior.get(str(c), 0),
            reverse=True
        )
        return sorted_clusters[:top_k]

    # 按先验权重排序匹配簇
    sorted_matching = sorted(
        matching_clusters,
        key=lambda c: linucb_prior.get(str(c), 0),
        reverse=True
    )

    return sorted_matching[:top_k]


def select_cluster_oracle(query_intent, cluster_ids, cluster_to_dominant_intent,
                          cluster_to_purity):
    """策略3: Oracle选择（选择最高纯度的正确簇）"""
    matching_clusters = [
        c for c in cluster_ids
        if cluster_to_dominant_intent[c] == query_intent
    ]

    if not matching_clusters:
        return [np.random.choice(cluster_ids)]

    # 按纯度排序
    sorted_by_purity = sorted(
        matching_clusters,
        key=lambda c: cluster_to_purity[c],
        reverse=True
    )
    return [sorted_by_purity[0]]


def evaluate_strategies():
    """对比三种策略"""
    print("\n" + "=" * 70)
    print("Phase 1F: 关键词先验直接验证")
    print("=" * 70)

    # 加载
    train_norm, test_norm, test_queries, cluster_to_indices, \
    cluster_to_dominant_intent, cluster_to_purity, cluster_ids, \
    emb_idx_to_intent, linucb_prior, n_clusters = load_data()

    n_test = min(200, len(test_queries))

    # ========== 策略1: 随机选择 ==========
    print("\n【策略1】随机选择簇")
    correct_random = 0
    for i in range(n_test):
        query = test_queries[i]
        query_intent = query['intent']
        query_emb = test_norm[i:i+1]

        cluster_id = select_cluster_random(cluster_ids)
        top_intent = retrieve_in_cluster(
            query_emb, query_intent, cluster_id,
            cluster_to_indices, train_norm, emb_idx_to_intent
        )
        if top_intent == query_intent:
            correct_random += 1

    acc_random = correct_random / n_test
    print(f"  准确率: {acc_random:.1%}")

    # ========== 策略2: 基于先验权重选择 ==========
    print("\n【策略2】基于先验权重选择簇")
    correct_prior = 0
    for i in range(n_test):
        query = test_queries[i]
        query_intent = query['intent']
        query_emb = test_norm[i:i+1]

        # 选择Top-3高先验权重的匹配簇
        top_clusters = select_cluster_by_prior(
            query_intent, cluster_ids, cluster_to_dominant_intent,
            cluster_to_purity, linucb_prior, top_k=3
        )

        # 在多个簇中检索，取最佳
        best_intent = -1
        best_sim = -1
        for c_id in top_clusters:
            indices = cluster_to_indices[c_id]
            if indices:
                cand_emb = train_norm[indices]
                sims = np.dot(query_emb, cand_emb.T)[0]
                top_idx = indices[np.argmax(sims)]
                if sims[np.argmax(sims)] > best_sim:
                    best_intent = emb_idx_to_intent.get(top_idx)
                    best_sim = sims[np.argmax(sims)]

        if best_intent == query_intent:
            correct_prior += 1

    acc_prior = correct_prior / n_test
    print(f"  准确率: {acc_prior:.1%}")

    # ========== 策略3: Oracle选择 ==========
    print("\n【策略3】Oracle选择（最高纯度正确簇）")
    correct_oracle = 0
    for i in range(n_test):
        query = test_queries[i]
        query_intent = query['intent']
        query_emb = test_norm[i:i+1]

        top_clusters = select_cluster_oracle(
            query_intent, cluster_ids, cluster_to_dominant_intent,
            cluster_to_purity
        )

        best_intent = -1
        best_sim = -1
        for c_id in top_clusters:
            indices = cluster_to_indices[c_id]
            if indices:
                cand_emb = train_norm[indices]
                sims = np.dot(query_emb, cand_emb.T)[0]
                top_idx = indices[np.argmax(sims)]
                if sims[np.argmax(sims)] > best_sim:
                    best_intent = emb_idx_to_intent.get(top_idx)
                    best_sim = sims[np.argmax(sims)]

        if best_intent == query_intent:
            correct_oracle += 1

    acc_oracle = correct_oracle / n_test
    print(f"  准确率: {acc_oracle:.1%}")

    # ========== 结果对比 ==========
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)

    print(f"\n策略         | 准确率 | 提升(vs随机)")
    print("-" * 50)
    print(f"随机选择     | {acc_random:>6.1%} | +0.0%")
    print(f"先验权重选择 | {acc_prior:>6.1%} | {(acc_prior-acc_random)*100:>+.1f}%")
    print(f"Oracle选择   | {acc_oracle:>6.1%} | {(acc_oracle-acc_random)*100:>+.1f}%")

    print(f"\n关键指标:")
    print(f"  先验策略 vs Oracle差距: {(acc_oracle-acc_prior)*100:.1f}%")
    print(f"  先验策略达到Oracle比例: {acc_prior/acc_oracle*100:.1f}%")

    # 保存
    result = {
        "random": acc_random,
        "prior": acc_prior,
        "oracle": acc_oracle,
        "improvement_prior_vs_random": (acc_prior - acc_random) * 100,
        "prior_oracle_ratio": acc_prior / acc_oracle
    }

    output_path = PROJECT_ROOT / "05_keyword_cluster" / "data" / "results" / "prior_direct_comparison.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ 结果保存到: {output_path}")
    return result


if __name__ == "__main__":
    evaluate_strategies()
    print("\n✓ Phase 1F 关键词先验验证完成!")