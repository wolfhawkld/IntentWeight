#!/usr/bin/env python3
"""
LinUCB 冷启动先验初始化验证 - Phase 1F

对比：
1. 随机初始化 LinUCB（传统方法）
2. 关键词先验初始化 LinUCB（Phase 1F 方法）

验证收敛速度和冷启动表现

作者: Damon + Nemesis
日期: 2026-04-13
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

# ========== 配置 ==========

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
RESULTS_DIR = PROJECT_ROOT / "04_intent_data_mapping" / "results"
KEYWORD_DIR = PROJECT_ROOT / "05_keyword_cluster" / "data" / "tagged_chunks"

# LinUCB 参数
ALPHA = 1.0
EMBEDDING_DIM = 64


# ========== LinUCB 实现 ==========

class LinUCB:
    """LinUCB 算法"""

    def __init__(self, n_arms, context_dim, alpha=1.0):
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha

        # 每个臂的参数
        self.A = [np.eye(context_dim) for _ in range(n_arms)]
        self.b = [np.zeros(context_dim) for _ in range(n_arms)]

        # 统计
        self.pull_counts = [0] * n_arms
        self.total_reward = [0.0] * n_arms

    def get_ucb_scores(self, context):
        """计算每个臂的 UCB 分数"""
        ucb_scores = []
        for arm in range(self.n_arms):
            theta = np.linalg.solve(self.A[arm], self.b[arm])
            pred = np.dot(theta, context)
            A_inv = np.linalg.inv(self.A[arm])
            uncertainty = np.sqrt(np.dot(context, np.dot(A_inv, context)))
            ucb = pred + self.alpha * uncertainty
            ucb_scores.append(ucb)
        return np.array(ucb_scores)

    def select_arm(self, context):
        """选择最优臂"""
        ucb_scores = self.get_ucb_scores(context)
        return np.argmax(ucb_scores), ucb_scores

    def update(self, arm, context, reward):
        """更新模型"""
        self.A[arm] += np.outer(context, context)
        self.b[arm] += reward * context
        self.pull_counts[arm] += 1
        self.total_reward[arm] += reward

    def get_arm_stats(self, arm):
        """获取臂统计"""
        theta = np.linalg.solve(self.A[arm], self.b[arm])
        return {
            "pulls": self.pull_counts[arm],
            "total_reward": self.total_reward[arm],
            "avg_reward": self.total_reward[arm] / max(1, self.pull_counts[arm]),
            "theta_norm": np.linalg.norm(theta)
        }


class LinUCBWithPrior(LinUCB):
    """带先验初始化的 LinUCB"""

    def __init__(self, n_arms, context_dim, alpha=1.0, prior_weights=None):
        super().__init__(n_arms, context_dim, alpha)

        # 应用先验初始化
        if prior_weights:
            self._apply_prior(prior_weights)

    def _apply_prior(self, prior_weights):
        """
        应用关键词先验初始化

        将 prior_weights 映射到 LinUCB 参数 A 和 b

        prior_weights: {cluster_id: initial_weight}
        """
        print("[LinUCBWithPrior] 应用先验初始化...")

        for arm_id, weight in prior_weights.items():
            if 0 <= arm_id < self.n_arms:
                # 方法：调整 A 和 b 的初始值
                # A 保持单位矩阵，但 b 增加先验期望
                # b = weight * unit_context (假设初始context是单位向量的一部分)

                # 创建一个代表该簇的先验context特征
                prior_context = np.zeros(self.context_dim)
                prior_context[arm_id % self.context_dim] = 1.0

                # 根据权重调整 b
                self.b[arm_id] = weight * prior_context

                # 可选：根据权重调整 A 的置信度
                # 高权重簇 -> A 更紧凑（置信度高）
                # 低权重簇 -> A 更松散（探索更多）
                scale_factor = 1.0 + (weight - 0.5) * 0.5  # 0.75-1.25
                self.A[arm_id] = scale_factor * np.eye(self.context_dim)

        # 统计
        n_prior = len(prior_weights)
        weights = list(prior_weights.values())
        print(f"  - 应用先验的臂数: {n_prior}")
        print(f"  - 先验权重范围: [{min(weights):.3f}, {max(weights):.3f}]")
        print(f"  - 先验权重均值: {np.mean(weights):.3f}")


# ========== 数据加载 ==========

def load_data():
    """加载BANKING77数据"""
    print("加载数据...")

    # Embeddings
    train_emb = np.load(RESULTS_DIR / "train_embeddings_banking77.npy")
    test_emb = np.load(RESULTS_DIR / "test_embeddings_banking77.npy")

    # 知识库
    with open(RESULTS_DIR / "knowledge_base_banking77.json", 'r') as f:
        kb = json.load(f)
    chunks = kb['chunks']

    # 测试集
    with open(RESULTS_DIR / "test_queries_banking77.json", 'r') as f:
        test_data = json.load(f)
    test_queries = test_data['queries']

    # 聚类
    with open(RESULTS_DIR / "clusters_banking77.json", 'r') as f:
        cluster_data = json.load(f)
    clusters = cluster_data['clusters']

    # 关键词先验（Phase 1F）
    prior_path = KEYWORD_DIR / "banking77_keyword_tagged.json"
    if prior_path.exists():
        with open(prior_path, 'r') as f:
            kw_data = json.load(f)
        prior_weights = kw_data.get('linucb_prior', {})
    else:
        prior_weights = {}
        print("⚠ 关键词先验文件不存在，使用空先验")

    print(f"✓ Train: {len(chunks)}, Test: {len(test_queries)}")
    print(f"✓ 簇数: {len(clusters)}")
    print(f"✓ 先验簇数: {len(prior_weights)}")

    return train_emb, test_emb, chunks, test_queries, clusters, prior_weights


def prepare_mappings(chunks, clusters):
    """准备簇映射"""
    # 构建chunk_id到embedding_idx的映射
    chunk_id_to_emb_idx = {chunk['chunk_id']: chunk['embedding_idx'] for chunk in chunks}

    # 构建embedding_idx到intent的映射
    emb_idx_to_intent = {chunk['embedding_idx']: chunk['intent'] for chunk in chunks}

    # 簇信息
    cluster_to_indices = defaultdict(list)
    cluster_to_dominant_intent = {}

    for cluster in clusters:
        c_id = cluster['cluster_id']
        # 将chunk_id转换为embedding_idx
        c_indices = []
        for chunk_id in cluster['chunk_ids']:
            emb_idx = chunk_id_to_emb_idx.get(chunk_id)
            if emb_idx is not None:
                c_indices.append(emb_idx)
        cluster_to_indices[c_id] = c_indices
        cluster_to_dominant_intent[c_id] = cluster['dominant_intent']

    # 簇列表
    cluster_ids = sorted(cluster_to_indices.keys())
    n_clusters = len(cluster_ids)
    cluster_id_to_idx = {c: i for i, c in enumerate(cluster_ids)}

    # 意图列表（按embedding_idx顺序）
    chunk_intents = [chunk['intent'] for chunk in chunks]

    print(f"✓ 簇映射准备完成: {n_clusters} 个簇")
    print(f"  示例: 簇0包含 {len(cluster_to_indices[0])} 个样本")

    return cluster_to_indices, cluster_to_dominant_intent, cluster_ids, cluster_id_to_idx, chunk_intents, emb_idx_to_intent


# ========== 验证函数 ==========

def simulate_convergence(linucb, train_emb, test_emb, test_queries, chunks,
                         cluster_to_indices, cluster_to_dominant_intent,
                         cluster_ids, cluster_id_to_idx, emb_idx_to_intent,
                         n_feedback=100, report_interval=20):
    """
    模拟收敛过程

    Args:
        linucb: LinUCB模型
        n_feedback: 模拟反馈次数
        report_interval: 报告间隔

    Returns:
        convergence_history: [(feedback_count, accuracy), ...]
    """
    print(f"\n模拟收敛（{n_feedback}次反馈）...")

    # PCA降维
    pca = PCA(n_components=EMBEDDING_DIM)
    all_emb = np.vstack([train_emb, test_emb])
    pca.fit(all_emb)
    train_emb_red = pca.transform(train_emb)
    test_emb_red = pca.transform(test_emb)

    # 归一化
    train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
    test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

    context_dim = EMBEDDING_DIM + len(cluster_ids)
    cluster_onehot_dim = len(cluster_ids)

    convergence_history = []

    # 随机选择反馈样本
    feedback_indices = np.random.choice(len(test_queries), n_feedback, replace=False)

    for i, query_idx in enumerate(feedback_indices):
        query = test_queries[query_idx]
        query_intent = query['intent']
        query_emb = test_norm[query_idx:query_idx+1]
        query_emb_red = test_emb_red[query_idx]

        # 构建context
        context = np.zeros(context_dim)
        context[:EMBEDDING_DIM] = query_emb_red

        # LinUCB选择簇
        arm_idx, ucb_scores = linucb.select_arm(context)
        selected_cluster = cluster_ids[arm_idx]

        # 簇内检索
        candidates = cluster_to_indices[selected_cluster]
        if candidates:
            candidate_emb = train_norm[candidates]
            sims = np.dot(query_emb, candidate_emb.T)[0]
            top_idx = candidates[np.argmax(sims)]
            top_intent = emb_idx_to_intent.get(top_idx, -1)
        else:
            # 簇为空，随机选择
            top_intent = -1

        # 计算奖励
        reward = 1.0 if top_intent == query_intent else 0.0

        # 更新LinUCB
        linucb.update(arm_idx, context, reward)

        # 定期评估
        if (i + 1) % report_interval == 0:
            # 批量测试准确率
            correct = 0
            for j, q in enumerate(test_queries[:min(100, len(test_queries))]):
                q_emb = test_norm[j:j+1]
                q_emb_red = test_emb_red[j]
                ctx = np.zeros(context_dim)
                ctx[:EMBEDDING_DIM] = q_emb_red

                arm, _ = linucb.select_arm(ctx)
                sel_cluster = cluster_ids[arm]

                cand = cluster_to_indices[sel_cluster]
                if cand:
                    cand_emb = train_norm[cand]
                    s = np.dot(q_emb, cand_emb.T)[0]
                    best_idx = cand[np.argmax(s)]
                    ti = emb_idx_to_intent.get(best_idx, -1)
                else:
                    ti = -1

                if ti == q['intent']:
                    correct += 1

            acc = correct / min(100, len(test_queries))
            convergence_history.append((i + 1, acc))

            print(f"  反馈 {i+1}: 准确率 {acc:.1%}")

    return convergence_history


def compare_methods():
    """对比两种初始化方法"""
    print("\n" + "=" * 70)
    print("Phase 1F: LinUCB 冷启动对比验证")
    print("=" * 70)

    # 加载数据
    train_emb, test_emb, chunks, test_queries, clusters, prior_weights = load_data()

    # 准备映射
    cluster_to_indices, cluster_to_dominant_intent, cluster_ids, cluster_id_to_idx, chunk_intents, emb_idx_to_intent = \
        prepare_mappings(chunks, clusters)

    n_clusters = len(cluster_ids)
    context_dim = EMBEDDING_DIM + n_clusters

    # ========== 方法1: 随机初始化 ==========
    print("\n【方法1】随机初始化 LinUCB")
    print("-" * 50)

    linucb_random = LinUCB(n_arms=n_clusters, context_dim=context_dim, alpha=ALPHA)

    history_random = simulate_convergence(
        linucb_random, train_emb, test_emb, test_queries, chunks,
        cluster_to_indices, cluster_to_dominant_intent,
        cluster_ids, cluster_id_to_idx, emb_idx_to_intent,
        n_feedback=100, report_interval=20
    )

    # ========== 方法2: 关键词先验初始化 ==========
    print("\n【方法2】关键词先验初始化 LinUCB")
    print("-" * 50)

    # 将 prior_weights 的 cluster_id 映射到 arm_idx
    prior_by_arm = {}
    for cluster_id, weight in prior_weights.items():
        cluster_id_int = int(cluster_id)
        if cluster_id_int in cluster_id_to_idx:
            arm_idx = cluster_id_to_idx[cluster_id_int]
            prior_by_arm[arm_idx] = weight

    linucb_prior = LinUCBWithPrior(
        n_arms=n_clusters,
        context_dim=context_dim,
        alpha=ALPHA,
        prior_weights=prior_by_arm
    )

    history_prior = simulate_convergence(
        linucb_prior, train_emb, test_emb, test_queries, chunks,
        cluster_to_indices, cluster_to_dominant_intent,
        cluster_ids, cluster_id_to_idx, emb_idx_to_intent,
        n_feedback=100, report_interval=20
    )

    # ========== 结果对比 ==========
    print("\n" + "=" * 70)
    print("收敛对比结果")
    print("=" * 70)

    print("\n反馈数 | 随机初始化 | 关键词先验 | 提升")
    print("-" * 50)

    for i, (r, p) in enumerate(zip(history_random, history_prior)):
        fb_count = r[0]
        acc_random = r[1]
        acc_prior = p[1]
        improvement = (acc_prior - acc_random) * 100
        print(f"{fb_count:>6} | {acc_random:>10.1%} | {acc_prior:>10.1%} | {improvement:>+.1f}%")

    # 最终统计
    final_random = history_random[-1][1]
    final_prior = history_prior[-1][1]
    total_improvement = (final_prior - final_random) * 100

    print("\n" + "-" * 50)
    print(f"最终准确率提升: {total_improvement:+.1f}%")

    # 保存结果
    result = {
        "method_random": {
            "history": history_random,
            "final_accuracy": final_random
        },
        "method_prior": {
            "history": history_prior,
            "final_accuracy": final_prior
        },
        "improvement": {
            "total": total_improvement,
            "convergence_speed": len(history_prior)  # 达到稳定的反馈数
        },
        "config": {
            "n_feedback": 100,
            "n_clusters": n_clusters,
            "alpha": ALPHA,
            "embedding_dim": EMBEDDING_DIM
        }
    }

    output_path = PROJECT_ROOT / "05_keyword_cluster" / "data" / "results" / "cold_start_comparison.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ 结果保存到: {output_path}")

    return result


if __name__ == "__main__":
    compare_methods()
    print("\n✓ Phase 1F 冷启动验证完成!")