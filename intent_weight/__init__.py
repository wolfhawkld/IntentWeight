# -*- coding: utf-8 -*-
"""
IntentWeight 模块 - 基于 LinUCB 的意图驱动检索优化
IntentWeight Module - LinUCB-based Intent-driven Retrieval Optimization

核心流程 / Core Flow:
1. 文件级语义聚类 → 将文档组织为 ~10-20 个聚类
2. LinUCB 根据 query 选择目标聚类 → 圈定文档检索范围
3. 在目标文档的 chunks 中执行混合检索
4. 用户反馈 → 更新 LinUCB 权重

参考 / Reference:
- IntentWeight 研究项目 (LinUCB Contextual Bandit)
"""
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from .linucb import LinUCB
from .reward import calculate_reward
from .persistence import save_state, load_state
from .clustering import load_pca_model
from .models import FeedbackRequest, IntentWeightStats


class IntentWeightManager:
    """
    IntentWeight 编排器
    IntentWeight Orchestrator

    封装 LinUCB + PCA + 聚类数据，提供检索过滤和反馈更新接口。
    Encapsulates LinUCB + PCA + cluster data, provides retrieval filtering
    and feedback update interfaces.
    """

    def __init__(self, state_dir: str,
                 pca_dim: int = 64,
                 alpha: float = 1.0, cold_start_threshold: int = 10,
                 top_k_clusters: int = 3):
        """
        Args:
            state_dir: 状态文件根目录 (data/intent_weight/)
            platform: 平台标识，PCA/聚类/LinUCB 按 platform 隔离
            pca_dim: PCA 降维维度
            alpha: LinUCB 探索参数
            cold_start_threshold: 冷启动阈值（累计反馈数 < 此值时 fallback）
            top_k_clusters: 每次选择的目标聚类数量
        """
        # 按 platform 隔离：data/intent_weight/azure/ 或 data/intent_weight/tencent/
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.pca_dim = pca_dim
        self.alpha = alpha
        self.cold_start_threshold = cold_start_threshold
        self.top_k_clusters = top_k_clusters

        self.linucb: Optional[LinUCB] = None
        self.pca_model = None
        self.clusters: Dict[int, Dict] = {}
        self.chunk_to_cluster: Dict[str, int] = {}

        # 消息追踪：message_id -> {query_embedding, chunk_ids, cluster_ids}
        self._message_cache: Dict[str, Dict] = {}

        # 用户信誉评分（基于 user_id）
        from .user_credibility import UserCredibilityStore
        self.user_credibility = UserCredibilityStore(
            str(self.state_dir.parent / "user_credibility.db")
        )

        self._load()

    def _load(self):
        """加载所有持久化状态 / Load all persisted state"""
        # 加载聚类数据
        clusters_state = load_state(self.state_dir / "clusters.json")
        if clusters_state:
            self.clusters = {int(k): v for k, v in clusters_state.items()}
            # 构建 chunk -> cluster 反向映射
            for cid, cdata in self.clusters.items():
                for chunk_id in cdata.get("chunk_ids", []):
                    self.chunk_to_cluster[chunk_id] = cid
            logger.info(f"Loaded {len(self.clusters)} clusters, "
                        f"{len(self.chunk_to_cluster)} chunk mappings")

        # 加载 PCA 模型
        self.pca_model = load_pca_model(self.state_dir / "pca_model.pkl")

        # 加载 LinUCB 状态
        linucb_state = load_state(self.state_dir / "linucb_state.json")
        if linucb_state:
            self.linucb = LinUCB.from_state(linucb_state)
            # 检查 context_dim 是否匹配丰富特征维度
            expected_dim = self._rich_context_dim
            if self.linucb.context_dim != expected_dim:
                logger.warning(
                    f"LinUCB context_dim mismatch: stored={self.linucb.context_dim}, "
                    f"expected={expected_dim}. Reinitializing."
                )
                self.linucb = LinUCB(
                    n_arms=self.linucb.n_arms,
                    context_dim=expected_dim,
                    alpha=self.alpha,
                )
            else:
                logger.info(f"Loaded LinUCB: {self.linucb.n_arms} arms, "
                            f"{self.linucb.total_feedback} feedback, "
                            f"effective_α={self.linucb.effective_alpha:.3f}")
        elif self.clusters:
            # 有聚类数据但无 LinUCB 状态 → 新建
            n_arms = len(self.clusters)
            self.linucb = LinUCB(n_arms=n_arms, context_dim=self._rich_context_dim, alpha=self.alpha)
            logger.info(f"Created new LinUCB with {n_arms} arms, context_dim={self._rich_context_dim}")

    def _save_linucb(self):
        """保存 LinUCB 状态 / Save LinUCB state"""
        if self.linucb:
            save_state(self.linucb.get_state(), self.state_dir / "linucb_state.json")

    @property
    def _rich_context_dim(self) -> int:
        """丰富特征的总维度 / Total dimension of rich context"""
        n_arms = len(self.clusters) if self.clusters else 0
        return self.pca_dim + n_arms * 2  # query_pca + arm_rewards + arm_ratios

    @property
    def is_ready(self) -> bool:
        """模块是否可用（有聚类数据和 PCA 模型）"""
        return (
            self.linucb is not None
            and self.pca_model is not None
            and len(self.clusters) > 0
        )

    @property
    def is_cold_start(self) -> bool:
        """是否处于冷启动阶段"""
        if not self.linucb:
            return True
        return self.linucb.total_feedback < self.cold_start_threshold

    def _pca_transform(self, embedding: np.ndarray) -> np.ndarray:
        """PCA 降维 query embedding / PCA transform query embedding"""
        if self.pca_model is None:
            raise RuntimeError("PCA model not loaded")
        return self.pca_model.transform(embedding.reshape(1, -1)).flatten()

    def _build_rich_context(self, query_embedding_pca: np.ndarray) -> np.ndarray:
        """
        构建丰富的上下文特征向量
        Build rich context feature vector

        组成 / Components:
        - query embedding PCA (64d): 查询语义
        - arm history reward (n_arms d): 各聚类历史平均 reward
        - arm pull ratio (n_arms d): 各聚类被选择的频率

        总维度 / Total dim: 64 + n_arms + n_arms = 64 + 30 = ~94d
        """
        # 各 arm 的历史平均 reward
        arm_rewards = np.array([
            self.linucb.total_rewards[i] / max(1, self.linucb.pull_counts[i])
            for i in range(self.linucb.n_arms)
        ])

        # 各 arm 的选择频率（归一化）
        total_pulls = max(1, self.linucb.total_feedback)
        arm_ratios = np.array([
            self.linucb.pull_counts[i] / total_pulls
            for i in range(self.linucb.n_arms)
        ])

        return np.concatenate([query_embedding_pca, arm_rewards, arm_ratios])

    def get_cluster_filter(self, query_embedding: np.ndarray) -> Optional[List[str]]:
        """
        获取聚类过滤条件
        Get cluster filter for retrieval

        LinUCB 选择 top-k 聚类 → 返回这些聚类包含的文档 source_file 列表

        Args:
            query_embedding: 原始 query embedding (高维，如 3072-dim)

        Returns:
            目标文档的 source_file 列表，或 None（冷启动/不可用时）
        """
        if not self.is_ready:
            return None

        # 冷启动阶段：仍然使用 LinUCB（有先验），但如果完全无数据则 fallback
        if self.linucb.total_feedback == 0 and not any(
            sum(self.linucb.pull_counts) > 0 for _ in [1]
        ):
            # 检查是否有冷启动先验（pull_counts > 0 说明有先验初始化）
            if sum(self.linucb.pull_counts) == 0:
                return None

        # PCA 降维 + 丰富特征
        query_pca = self._pca_transform(query_embedding)
        context = self._build_rich_context(query_pca)

        # LinUCB 选择 top-k 聚类
        selected_indices, scores = self.linucb.select_arms(context, self.top_k_clusters)

        # 收集目标文档
        source_files = []
        cluster_id_map = sorted(self.clusters.keys())
        for arm_idx in selected_indices:
            if arm_idx < len(cluster_id_map):
                cid = cluster_id_map[arm_idx]
                source_files.extend(self.clusters[cid].get("source_files", []))

        if not source_files:
            return None

        logger.debug(f"LinUCB selected clusters: {[cluster_id_map[i] for i in selected_indices]}, "
                     f"{len(source_files)} source files")
        return source_files

    def record_feedback(
        self,
        message_id: str,
        feedback: FeedbackRequest,
        query_embedding: Optional[np.ndarray] = None,
        embedding_engine=None,
        reward_override: Optional[float] = None,
        user_id: Optional[str] = None,
    ):
        """
        记录用户反馈并更新 LinUCB
        Record user feedback and update LinUCB

        Args:
            message_id: 消息 ID
            feedback: 反馈数据
            query_embedding: query 的原始 embedding（如果之前缓存了可以不传）
            embedding_engine: embedding 引擎，用于在无缓存时重新编码 query
        """
        if not self.is_ready:
            logger.warning("IntentWeight not ready, skipping feedback")
            return

        # 获取 query embedding：缓存 → 重新编码 → 放弃
        cached = self._message_cache.get(message_id, {})
        if query_embedding is None:
            if "query_embedding" in cached:
                query_embedding = cached["query_embedding"]
            elif feedback.query and embedding_engine:
                logger.info(f"Re-encoding query for feedback: {feedback.query[:50]}...")
                query_embedding = embedding_engine.encode_single(feedback.query)
            else:
                logger.warning(f"No query embedding for message {message_id}, skipping")
                return

        # 计算奖励（支持外部覆盖，用于上下文奖励）
        if reward_override is not None:
            reward = reward_override
        else:
            reward = calculate_reward(
                explicit=feedback.explicit,
                implicit=feedback.implicit,
            )

        # 用户信誉评估 + reward 加权
        if user_id:
            credibility = self.user_credibility.get_credibility(user_id)

            # === 方案 2: LinUCB 预期 vs 实际偏差 ===
            # 计算 LinUCB 对该 query 的预期 reward（当前 arm 的平均 reward）
            feedback_aligned = True
            try:
                query_pca_tmp = self._pca_transform(query_embedding)
                context_tmp = self._build_rich_context(query_pca_tmp)
                top_arms, scores = self.linucb.select_arms(context_tmp, top_k=1)
                if top_arms:
                    expected_reward = self.linucb.total_rewards[top_arms[0]] / max(1, self.linucb.pull_counts[top_arms[0]])
                    # 如果用户反馈与 LinUCB 预期偏差 > 0.4 → 标记异常
                    if abs(reward - expected_reward) > 0.4:
                        feedback_aligned = False
            except Exception:
                pass

            # === 方案 3: 隐式信号交叉验证 ===
            # 显式反馈和隐式行为矛盾检测
            engagement_depth = 0.5
            if feedback.explicit is not None:
                engagement_depth = 0.8  # 有显式反馈 = 高参与度
                if feedback.implicit:
                    dwell = feedback.implicit.get("dwell_time", 0)
                    copied = feedback.implicit.get("copy_action", False)
                    # 矛盾 1: 点赞但 dwell < 3s（没看就点）
                    if feedback.explicit == "like" and dwell < 3:
                        feedback_aligned = False
                        engagement_depth = 0.2
                    # 矛盾 2: 点踩但有复制行为（觉得有用但点踩）
                    if feedback.explicit == "dislike" and copied:
                        feedback_aligned = False
                        engagement_depth = 0.3
            elif feedback.implicit:
                engagement_depth = 0.3  # 仅隐式 = 低参与度

            # reward 按信誉加权：向中性 (0.5) 收缩
            reward = 0.5 + (reward - 0.5) * credibility

            # 更新用户信誉
            self.user_credibility.update_credibility(
                user_id=user_id,
                feedback_aligned=feedback_aligned,
                engagement_depth=engagement_depth,
            )

        # PCA 降维 + 丰富特征
        query_pca = self._pca_transform(query_embedding)
        context = self._build_rich_context(query_pca)

        # 找到反馈对应的聚类（通过 chunk_ids 推断）
        cluster_id_map = sorted(self.clusters.keys())
        updated_arms = set()

        for chunk_id in feedback.chunk_ids:
            cid = self.chunk_to_cluster.get(chunk_id)
            if cid is not None and cid in cluster_id_map:
                arm_idx = cluster_id_map.index(cid)
                if arm_idx not in updated_arms:
                    self.linucb.update(arm_idx, context, reward)
                    updated_arms.add(arm_idx)

        # 如果没有匹配到任何聚类，用缓存的 selected_arms 或重新推断
        if not updated_arms:
            # 先尝试缓存
            for arm_idx in cached.get("selected_arms", []):
                self.linucb.update(arm_idx, context, reward)
                updated_arms.add(arm_idx)

        # 仍然没有 → 用 LinUCB 自身推断最相关的聚类
        if not updated_arms:
            top_arms, _ = self.linucb.select_arms(context, top_k=self.top_k_clusters)
            for arm_idx in top_arms:
                self.linucb.update(arm_idx, context, reward)
                updated_arms.add(arm_idx)
            logger.info(f"Inferred arms from LinUCB for feedback: {top_arms}")

        if updated_arms:
            self._save_linucb()
            logger.info(f"Feedback recorded: message={message_id}, reward={reward:.2f}, "
                        f"updated arms={updated_arms}")

        # 清理缓存
        self._message_cache.pop(message_id, None)

    def cache_message(self, message_id: str, query_embedding: np.ndarray,
                      chunk_ids: List[str], selected_arms: List[int] = None):
        """
        缓存消息信息，供后续反馈使用
        Cache message info for later feedback processing
        """
        self._message_cache[message_id] = {
            "query_embedding": query_embedding,
            "chunk_ids": chunk_ids,
            "selected_arms": selected_arms or [],
        }
        # 限制缓存大小
        if len(self._message_cache) > 1000:
            oldest = list(self._message_cache.keys())[:500]
            for key in oldest:
                del self._message_cache[key]

    def get_stats(self) -> IntentWeightStats:
        """获取统计信息 / Get statistics"""
        arm_stats = []
        if self.linucb:
            cluster_id_map = sorted(self.clusters.keys())
            for i, cid in enumerate(cluster_id_map):
                if i < self.linucb.n_arms:
                    avg_r = (self.linucb.total_rewards[i] / self.linucb.pull_counts[i]
                             if self.linucb.pull_counts[i] > 0 else 0.0)
                    arm_stats.append({
                        "cluster_id": cid,
                        "pull_count": self.linucb.pull_counts[i],
                        "avg_reward": round(avg_r, 3),
                        "doc_count": self.clusters[cid].get("doc_count", 0),
                    })

        return IntentWeightStats(
            enabled=self.is_ready,
            num_clusters=len(self.clusters),
            num_documents=sum(c.get("doc_count", 0) for c in self.clusters.values()),
            total_feedback=self.linucb.total_feedback if self.linucb else 0,
            cold_start=self.is_cold_start,
            linucb_alpha=self.alpha,
            arm_stats=arm_stats,
        )
