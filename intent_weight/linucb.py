# -*- coding: utf-8 -*-
"""
LinUCB 上下文 Bandit 实现（文件级聚类 arms）
LinUCB Contextual Bandit Implementation (file-level cluster arms)

参考 / Reference:
- Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article Recommendation"
- IntentWeight 项目 contextual_bandit.py + interactive_feedback_v6.py
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger


class LinUCB:
    """
    LinUCB 算法实现
    LinUCB Algorithm Implementation

    每个 arm 对应一个文件级聚类。
    Each arm corresponds to a file-level cluster.

    UCB_score = theta^T x + alpha * sqrt(x^T A^{-1} x)
    """

    def __init__(self, n_arms: int, context_dim: int, alpha: float = 1.0,
                 alpha_decay: float = 0.01, alpha_min: float = 0.3):
        """
        初始化 LinUCB

        Args:
            n_arms: 聚类数量（arm 数量）
            context_dim: 上下文特征维度（PCA 降维后）
            alpha: 初始探索参数
            alpha_decay: 探索衰减率（每次反馈后 α 递减）
            alpha_min: 最小探索参数（防止完全停止探索）
        """
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha
        self.alpha_decay = alpha_decay
        self.alpha_min = alpha_min

        # 每个 arm 的参数
        # A: d x d 矩阵，初始化为单位阵
        # b: d 维向量，初始化为 0
        self.A: List[np.ndarray] = [np.eye(context_dim) for _ in range(n_arms)]
        self.b: List[np.ndarray] = [np.zeros(context_dim) for _ in range(n_arms)]

        # 统计信息
        self.pull_counts: List[int] = [0] * n_arms
        self.total_rewards: List[float] = [0.0] * n_arms

        # 反馈历史
        self.history: List[Dict] = []

    @property
    def effective_alpha(self) -> float:
        """
        动态探索参数（随反馈积累衰减）
        Dynamic exploration parameter (decays with feedback)

        α(t) = max(α_min, α_0 / (1 + decay * total_feedback))
        """
        return max(self.alpha_min, self.alpha / (1 + self.alpha_decay * self.total_feedback))

    def get_ucb_scores(self, context: np.ndarray) -> np.ndarray:
        """
        计算所有 arm 的 UCB 分数
        Compute UCB scores for all arms

        Args:
            context: 上下文特征向量 (context_dim,)

        Returns:
            scores: 每个 arm 的 UCB 分数 (n_arms,)
        """
        alpha = self.effective_alpha
        scores = np.zeros(self.n_arms)
        for i in range(self.n_arms):
            # theta = A^{-1} b
            theta = np.linalg.solve(self.A[i], self.b[i])
            # 点估计 / point estimate
            p = np.dot(theta, context)
            # 不确定性项 / uncertainty term
            A_inv = np.linalg.inv(self.A[i])
            uncertainty = np.sqrt(np.dot(context, np.dot(A_inv, context)))
            scores[i] = p + alpha * uncertainty
        return scores

    def select_arms(self, context: np.ndarray, top_k: int = 3) -> Tuple[List[int], np.ndarray]:
        """
        选择 top-k 个 arm（聚类）
        Select top-k arms (clusters)

        Args:
            context: 上下文特征向量
            top_k: 返回的 arm 数量

        Returns:
            (selected_arm_indices, ucb_scores)
        """
        scores = self.get_ucb_scores(context)
        top_k = min(top_k, self.n_arms)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return top_indices.tolist(), scores

    def update(self, arm_idx: int, context: np.ndarray, reward: float):
        """
        根据反馈更新指定 arm 的参数
        Update arm parameters based on feedback

        A <- A + x x^T
        b <- b + r * x

        Args:
            arm_idx: arm 索引
            context: 上下文特征向量
            reward: 奖励值 [0, 1]
        """
        if arm_idx < 0 or arm_idx >= self.n_arms:
            logger.warning(f"Invalid arm index: {arm_idx}")
            return

        self.A[arm_idx] += np.outer(context, context)
        self.b[arm_idx] += reward * context
        self.pull_counts[arm_idx] += 1
        self.total_rewards[arm_idx] += reward

        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "arm_idx": arm_idx,
            "reward": reward,
            "pull_count": self.pull_counts[arm_idx],
        })

    def init_from_priors(self, priors: Dict[int, float]):
        """
        用冷启动先验初始化 arm 权重
        Initialize arm weights from cold-start priors

        通过在 b 向量中注入先验信息，使 theta = A^{-1} b 倾向于高先验的 arm。
        Inject prior information into b vectors so theta = A^{-1} b favors
        high-prior arms.

        Args:
            priors: {arm_idx: prior_weight} 先验权重 (0~1)
        """
        for arm_idx, weight in priors.items():
            if 0 <= arm_idx < self.n_arms:
                # 用一个小的伪观测来设置先验
                # 先验越高，初始 b 越大，theta 的期望值越高
                pseudo_context = np.ones(self.context_dim) / np.sqrt(self.context_dim)
                self.b[arm_idx] = weight * pseudo_context
                self.pull_counts[arm_idx] = 1
                self.total_rewards[arm_idx] = weight

    @property
    def total_feedback(self) -> int:
        return sum(self.pull_counts)

    def get_state(self) -> Dict:
        """序列化为可存储格式 / Serialize to storable format"""
        return {
            "n_arms": self.n_arms,
            "context_dim": self.context_dim,
            "alpha": self.alpha,
            "alpha_decay": self.alpha_decay,
            "alpha_min": self.alpha_min,
            "A": [a.tolist() for a in self.A],
            "b": [b.tolist() for b in self.b],
            "pull_counts": self.pull_counts,
            "total_rewards": self.total_rewards,
            "history": self.history[-100:],  # 只保留最近 100 条
        }

    @classmethod
    def from_state(cls, state: Dict) -> "LinUCB":
        """从存储格式恢复 / Restore from stored state"""
        obj = cls(
            n_arms=state["n_arms"],
            context_dim=state["context_dim"],
            alpha=state.get("alpha", 1.0),
            alpha_decay=state.get("alpha_decay", 0.01),
            alpha_min=state.get("alpha_min", 0.3),
        )
        obj.A = [np.array(a) for a in state["A"]]
        obj.b = [np.array(b) for b in state["b"]]
        obj.pull_counts = state.get("pull_counts", [0] * obj.n_arms)
        obj.total_rewards = state.get("total_rewards", [0.0] * obj.n_arms)
        obj.history = state.get("history", [])
        return obj
