#!/usr/bin/env python3
"""
Phase 1F: 关键词先验验证（Intent-Context版）

关键改进：
- LinUCB context 包含 query_intent 信息
- LinUCB 学习 "query_intent -> 正确簇" 的映射
- 关键词先验用于初始化正确簇的权重

作者: Damon + Nemesis
日期: 2026-04-13
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
RESULTS_DIR = PROJECT_ROOT / "04_intent_data_mapping" / "results"
KEYWORD_DIR = PROJECT_ROOT / "05_keyword_cluster" / "data" / "tagged_chunks"

ALPHA = 1.0
EMBEDDING_DIM = 64


class LinUCBIntentContext:
    """
    LinUCB with Intent Context

    Context = [query_emb_reduced, intent_onehot]
    学习：给定query_intent，选择哪个簇
    """

    def __init__(self, n_arms, context_dim, n_intents, alpha=1.0, prior=None):
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.n_intents = n_intents
        self.alpha = alpha

        self.A = [np.eye(context_dim) for _ in range(n_arms)]
        self.b = [np.zeros(context_dim) for _ in range(n_arms)]

        self.pull_counts = [0] * n_arms
        self.total_reward = [0.0] * n_arms

        if prior:
            self._apply_prior(prior)

    def _apply_prior(self, prior):
        """应用关键词先验"""
        print("[LinUCB] 应用先验初始化...")
        for arm_idx, weight in prior.items():
            if 0 <= arm_idx < self.n_arms:
                # 方法：调整 A 的初始值
                # 高权重簇 -> A 更小（初始置信度更高）
                scale = 1.0 / (weight + 0.1)  # 权重越高，scale越小
                self.A[arm_idx] = scale * np.eye(self.context_dim)
                # b 增加正向期望
                unit_vec = np.ones(self.context_dim) * weight
                self.b[arm_idx] = unit_vec

    def build_context(self, query_emb_red, query_intent):
        """构建context：embedding + intent onehot"""
        context = np.zeros(self.context_dim)
        context[:EMBEDDING_DIM] = query_emb_red
        # intent one-hot
        intent_idx = query_intent % (self.context_dim - EMBEDDING_DIM)
        context[EMBEDDING_DIM + intent_idx] = 1.0
        return context

    def select_arm(self, context):
        """选择最优臂"""
        ucb_scores = []
        for arm in range(self.n_arms):
            theta = np.linalg.solve(self.A[arm], self.b[arm])
            pred = np.dot(theta, context)
            A_inv = np.linalg.inv(self.A[arm])
            uncertainty = np.sqrt(np.dot(context, np.dot(A_inv, context)))
            ucb = pred + self.alpha * uncertainty
            ucb_scores.append(ucb)
        return np.argmax(ucb_scores), np.array(ucb_scores)

    def update(self, arm, context, reward):
        """更新模型"""
        self.A[arm] += np.outer(context, context)
        self.b[arm] += reward * context
        self.pull_counts[arm] += 1
        self.total_reward[arm] += reward


def load_data():
    """加载数据"""
    print("加载数据...")

    train_emb = np.load(RESULTS_DIR / "train_embeddings_banking77.npy")
    test_emb = np.load(RESULTS_DIR / "test_embeddings_banking77.npy")

    with open(RESULTS_DIR / "knowledge_base_banking77.json", 'r') as f:
        kb = json.load(f)
    with open(RESULTS_DIR / "test_queries_banking77.json", 'r') as f:
        test_data = json.load(f)
    with open(RESULTS_DIR / "clusters_banking77.json", 'r') as f:
        cluster_data = json.load(f)

    chunks = kb['chunks']
    test_queries = test_data['queries']
    clusters = cluster_data['clusters']

    # 关键词先验
    prior_path = KEYWORD_DIR / "banking77_keyword_tagged.json"
    if prior_path.exists():
        with open(prior_path, 'r') as f:
            kw_data = json.load(f)
        linucb_prior = kw_data.get('linucb_prior', {})
    else:
        linucb_prior = {}

    # 映射
    chunk_id_to_emb_idx = {c['chunk_id']: c['embedding_idx'] for c in chunks}
    emb_idx_to_intent = {c['embedding_idx']: c['intent'] for c in chunks}

    cluster_to_indices = {}
    cluster_to_dominant_intent = {}
    for cluster in clusters:
        c_id = cluster['cluster_id']
        indices = [chunk_id_to_emb_idx.get(cid) for cid in cluster['chunk_ids']
                   if chunk_id_to_emb_idx.get(cid) is not None]
        cluster_to_indices[c_id] = indices
        cluster_to_dominant_intent[c_id] = cluster['dominant_intent']

    cluster_ids = sorted(cluster_to_indices.keys())
    n_clusters = len(cluster_ids)
    cluster_id_to_idx = {c: i for i, c in enumerate(cluster_ids)}

    # intent空间
    n_intents = max(c['intent'] for c in chunks) + 1

    # 先验映射
    prior_by_arm = {}
    for c_id, weight in linucb_prior.items():
        c_id_int = int(c_id)
        if c_id_int in cluster_id_to_idx:
            prior_by_arm[cluster_id_to_idx[c_id_int]] = weight

    print(f"✓ Train: {len(chunks)}, Test: {len(test_queries)}")
    print(f"✓ 簇数: {n_clusters}, 意图数: {n_intents}")
    print(f"✓ 先验簇数: {len(prior_by_arm)}")

    return train_emb, test_emb, chunks, test_queries, clusters, \
           cluster_to_indices, cluster_to_dominant_intent, cluster_ids, \
           cluster_id_to_idx, emb_idx_to_intent, prior_by_arm, n_clusters, n_intents


def simulate_and_compare():
    """对比验证"""
    print("\n" + "=" * 70)
    print("Phase 1F: 关键词先验验证（Intent-Context版）")
    print("=" * 70)

    # 加载
    train_emb, test_emb, chunks, test_queries, clusters, \
    cluster_to_indices, cluster_to_dominant_intent, cluster_ids, \
    cluster_id_to_idx, emb_idx_to_intent, prior_by_arm, n_clusters, n_intents = load_data()

    # PCA
    pca = PCA(n_components=EMBEDDING_DIM)
    pca.fit(np.vstack([train_emb, test_emb]))
    train_emb_red = pca.transform(train_emb)
    test_emb_red = pca.transform(test_emb)

    # 归一化
    train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
    test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

    context_dim = EMBEDDING_DIM + min(n_intents, 128)  # intent one-hot最多128维

    # ========== 方法1: 随机初始化 ==========
    print("\n【方法1】随机初始化")
    print("-" * 50)

    linucb_random = LinUCBIntentContext(
        n_arms=n_clusters, context_dim=context_dim,
        n_intents=n_intents, alpha=ALPHA
    )

    history_random = []
    for i in range(100):
        query_idx = np.random.randint(len(test_queries))
        query = test_queries[query_idx]
        query_intent = query['intent']
        query_emb_red = test_emb_red[query_idx]
        query_emb = test_norm[query_idx:query_idx+1]

        # context包含intent
        context = linucb_random.build_context(query_emb_red, query_intent)

        # LinUCB选择簇
        arm_idx, _ = linucb_random.select_arm(context)
        selected_cluster = cluster_ids[arm_idx]

        # 簇内检索（带意图加成）
        indices = cluster_to_indices[selected_cluster]
        if indices:
            cand_emb = train_norm[indices]
            sims = np.dot(query_emb, cand_emb.T)[0]
            # 意图加成
            intent_bonus = np.array([
                0.15 if emb_idx_to_intent.get(idx) == query_intent else 0.0
                for idx in indices
            ])
            adjusted = sims + intent_bonus
            top_idx = indices[np.argmax(adjusted)]
            top_intent = emb_idx_to_intent.get(top_idx)
        else:
            top_intent = -1

        reward = 1.0 if top_intent == query_intent else 0.0
        linucb_random.update(arm_idx, context, reward)

        if (i + 1) % 20 == 0:
            acc = evaluate(linucb_random, test_emb_red, test_norm, test_queries[:100],
                           cluster_ids, cluster_to_indices, emb_idx_to_intent)
            history_random.append((i + 1, acc))
            print(f"  反馈 {i+1}: 准确率 {acc:.1%}")

    # ========== 方法2: 关键词先验初始化 ==========
    print("\n【方法2】关键词先验初始化")
    print("-" * 50)

    linucb_prior = LinUCBIntentContext(
        n_arms=n_clusters, context_dim=context_dim,
        n_intents=n_intents, alpha=ALPHA, prior=prior_by_arm
    )

    history_prior = []
    for i in range(100):
        query_idx = np.random.randint(len(test_queries))
        query = test_queries[query_idx]
        query_intent = query['intent']
        query_emb_red = test_emb_red[query_idx]
        query_emb = test_norm[query_idx:query_idx+1]

        context = linucb_prior.build_context(query_emb_red, query_intent)

        arm_idx, _ = linucb_prior.select_arm(context)
        selected_cluster = cluster_ids[arm_idx]

        indices = cluster_to_indices[selected_cluster]
        if indices:
            cand_emb = train_norm[indices]
            sims = np.dot(query_emb, cand_emb.T)[0]
            intent_bonus = np.array([
                0.15 if emb_idx_to_intent.get(idx) == query_intent else 0.0
                for idx in indices
            ])
            adjusted = sims + intent_bonus
            top_idx = indices[np.argmax(adjusted)]
            top_intent = emb_idx_to_intent.get(top_idx)
        else:
            top_intent = -1

        reward = 1.0 if top_intent == query_intent else 0.0
        linucb_prior.update(arm_idx, context, reward)

        if (i + 1) % 20 == 0:
            acc = evaluate(linucb_prior, test_emb_red, test_norm, test_queries[:100],
                           cluster_ids, cluster_to_indices, emb_idx_to_intent)
            history_prior.append((i + 1, acc))
            print(f"  反馈 {i+1}: 准确率 {acc:.1%}")

    # ========== 结果 ==========
    print("\n" + "=" * 70)
    print("收敛对比")
    print("=" * 70)

    print("\n反馈数 | 随机初始化 | 关键词先验 | 提升")
    print("-" * 50)

    for (fb1, acc1), (fb2, acc2) in zip(history_random, history_prior):
        imp = (acc2 - acc1) * 100
        print(f"{fb1:>6} | {acc1:>10.1%} | {acc2:>10.1%} | {imp:>+.1f}%")

    final_imp = (history_prior[-1][1] - history_random[-1][1]) * 100
    print(f"\n最终准确率提升: {final_imp:+.1f}%")

    # 保存
    result = {
        "random": history_random,
        "prior": history_prior,
        "improvement": final_imp
    }
    output_path = PROJECT_ROOT / "05_keyword_cluster" / "data" / "results" / "intent_context_comparison.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ 结果保存到: {output_path}")


def evaluate(linucb, test_emb_red, test_norm, test_queries,
             cluster_ids, cluster_to_indices, emb_idx_to_intent):
    """评估准确率"""
    correct = 0
    n = min(100, len(test_queries))

    for i in range(n):
        query = test_queries[i]
        query_intent = query['intent']
        query_emb_red = test_emb_red[i]
        query_emb = test_norm[i:i+1]

        context = linucb.build_context(query_emb_red, query_intent)
        arm_idx, _ = linucb.select_arm(context)
        selected_cluster = cluster_ids[arm_idx]

        indices = cluster_to_indices[selected_cluster]
        if indices:
            cand_emb = train_norm[indices]
            sims = np.dot(query_emb, cand_emb.T)[0]
            intent_bonus = np.array([
                0.15 if emb_idx_to_intent.get(idx) == query_intent else 0.0
                for idx in indices
            ])
            adjusted = sims + intent_bonus
            top_idx = indices[np.argmax(adjusted)]
            top_intent = emb_idx_to_intent.get(top_idx)
        else:
            top_intent = -1

        if top_intent == query_intent:
            correct += 1

    return correct / n


if __name__ == "__main__":
    # 需要train_norm全局可见
    train_emb, test_emb, chunks, test_queries, clusters, \
    cluster_to_indices, cluster_to_dominant_intent, cluster_ids, \
    cluster_id_to_idx, emb_idx_to_intent, prior_by_arm, n_clusters, n_intents = load_data()
    train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)

    simulate_and_compare()
    print("\n✓ Phase 1F 验证完成!")