#!/usr/bin/env python3
"""
Contextual Bandit 实现

将 chunk 选择问题建模为 Contextual Bandit：
- Context (状态): 查询嵌入 + 历史上下文
- Action (动作): 选择返回哪个 chunk
- Reward (奖励): 用户反馈信号

算法选择：
- LinUCB: 线性 UCB，适合稀疏特征
- Neural ε-greedy: 神经网络 + ε 探索
- Thompson Sampling: 贝叶斯采样

参考：
- Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article Recommendation"
- Agrawal & Goyal (2013) "Thompson Sampling for Contextual Bandits"
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import pickle


@dataclass
class BanditArm:
    """Bandit 的一个臂（动作）"""
    chunk_id: str
    intent_label: str
    
    # LinUCB 参数
    A: np.ndarray = None  # d x d 矩阵，初始为单位阵
    b: np.ndarray = None  # d 维向量，初始为 0
    
    # 统计信息
    pull_count: int = 0
    total_reward: float = 0.0
    avg_reward: float = 0.0
    
    # Thompson Sampling 参数
    alpha: float = 1.0  # Beta 分布参数
    beta: float = 1.0   # Beta 分布参数
    
    def __post_init__(self):
        if self.A is None:
            self.A = None  # 延迟初始化，需要知道特征维度
        if self.b is None:
            self.b = None
    
    def init_linucb(self, d: int):
        """初始化 LinUCB 参数"""
        self.A = np.eye(d)
        self.b = np.zeros(d)
    
    def get_ucb_score(self, context: np.ndarray, alpha: float = 1.0) -> float:
        """
        计算 UCB 分数
        
        UCB = θᵀx + α × √(xᵀA⁻¹x)
        
        Args:
            context: 上下文特征向量 x
            alpha: 探索参数
        
        Returns:
            UCB 分数
        """
        if self.A is None:
            return 0.0
        
        # θ = A⁻¹b
        theta = np.linalg.solve(self.A, self.b)
        
        # 点估计
        p = np.dot(theta, context)
        
        # 不确定性项
        A_inv = np.linalg.inv(self.A)
        uncertainty = np.sqrt(np.dot(context, np.dot(A_inv, context)))
        
        return p + alpha * uncertainty
    
    def update_linucb(self, context: np.ndarray, reward: float):
        """
        更新 LinUCB 参数
        
        A ← A + xxᵀ
        b ← b + r × x
        
        Args:
            context: 上下文特征向量 x
            reward: 奖励值
        """
        if self.A is None:
            return
        
        self.A += np.outer(context, context)
        self.b += reward * context
        
        self.pull_count += 1
        self.total_reward += reward
        self.avg_reward = self.total_reward / self.pull_count
    
    def sample_thompson(self) -> float:
        """
        Thompson Sampling: 从后验分布采样
        
        Returns:
            采样的平均奖励
        """
        return np.random.beta(self.alpha, self.beta)
    
    def update_thompson(self, reward: float):
        """
        更新 Thompson Sampling 参数
        
        Beta 分布共轭先验：
        - 正反馈 (R > 0.5): α += R
        - 负反馈 (R < 0.5): β += (1 - R)
        """
        if reward > 0.5:
            self.alpha += reward
        else:
            self.beta += (1 - reward)
        
        self.pull_count += 1
        self.total_reward += reward
        self.avg_reward = self.total_reward / self.pull_count


@dataclass
class ContextualBandit:
    """Contextual Bandit 模型"""
    
    # 特征维度
    context_dim: int = 384  # 默认 SBERT 嵌入维度
    
    # 探索策略
    exploration: str = "linucb"  # "linucb", "thompson", "epsilon_greedy"
    alpha: float = 1.0  # UCB 探索参数
    epsilon: float = 0.1  # ε-greedy 探索率
    
    # 臂集合 {chunk_id: BanditArm}
    arms: Dict[str, BanditArm] = field(default_factory=dict)
    
    # chunk_id 到意图的映射
    chunk_to_intents: Dict[str, List[str]] = field(default_factory=dict)
    
    # 历史记录
    history: List[Dict] = field(default_factory=list)
    
    def add_arm(self, chunk_id: str, intent_label: str):
        """添加一个臂"""
        if chunk_id not in self.arms:
            arm = BanditArm(chunk_id=chunk_id, intent_label=intent_label)
            arm.init_linucb(self.context_dim)
            self.arms[chunk_id] = arm
        
        # 记录意图
        if chunk_id not in self.chunk_to_intents:
            self.chunk_to_intents[chunk_id] = []
        if intent_label not in self.chunk_to_intents[chunk_id]:
            self.chunk_to_intents[chunk_id].append(intent_label)
    
    def get_context_embedding(self, query: str, history_context: List[str] = None) -> np.ndarray:
        """
        获取上下文嵌入
        
        Args:
            query: 当前查询
            history_context: 历史对话上下文
        
        Returns:
            上下文特征向量
        """
        # 简化版：直接返回查询嵌入
        # 实际应该用 embedding 模型
        # 这里用一个随机向量模拟（实际使用时替换）
        
        # 如果有嵌入模型：
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # embedding = model.encode(query)
        
        # 模拟：用 hash 生成稳定的随机向量
        np.random.seed(hash(query) % (2**32))
        embedding = np.random.randn(self.context_dim)
        embedding = embedding / np.linalg.norm(embedding)  # 归一化
        
        return embedding
    
    def select_action(
        self, 
        context: np.ndarray, 
        candidate_chunks: List[str] = None,
        top_k: int = 5
    ) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        选择动作（chunk）
        
        Args:
            context: 上下文特征
            candidate_chunks: 候选 chunk 列表（None 表示全部）
            top_k: 返回 top-k 候选
        
        Returns:
            (选择的 chunk_id, 分数, [(chunk_id, 分数), ...])
        """
        if not self.arms:
            return None, 0.0, []
        
        # 确定候选集合
        candidates = candidate_chunks if candidate_chunks else list(self.arms.keys())
        candidates = [c for c in candidates if c in self.arms]
        
        if not candidates:
            return None, 0.0, []
        
        # 计算每个候选的分数
        scores = []
        for chunk_id in candidates:
            arm = self.arms[chunk_id]
            
            if self.exploration == "linucb":
                score = arm.get_ucb_score(context, self.alpha)
            elif self.exploration == "thompson":
                score = arm.sample_thompson()
            elif self.exploration == "epsilon_greedy":
                score = arm.avg_reward
            else:
                score = arm.avg_reward
            
            scores.append((chunk_id, score))
        
        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # ε-greedy 探索
        if self.exploration == "epsilon_greedy" and np.random.random() < self.epsilon:
            # 随机探索
            selected_idx = np.random.randint(0, min(len(scores), top_k))
            selected_chunk = scores[selected_idx][0]
            selected_score = scores[selected_idx][1]
        else:
            # 选择最优
            selected_chunk = scores[0][0]
            selected_score = scores[0][1]
        
        return selected_chunk, selected_score, scores[:top_k]
    
    def update(
        self, 
        chunk_id: str, 
        context: np.ndarray, 
        reward: float
    ):
        """
        根据反馈更新模型
        
        Args:
            chunk_id: 被选择的 chunk
            context: 上下文特征
            reward: 奖励值
        """
        if chunk_id not in self.arms:
            return
        
        arm = self.arms[chunk_id]
        
        if self.exploration in ["linucb", "epsilon_greedy"]:
            arm.update_linucb(context, reward)
        elif self.exploration == "thompson":
            arm.update_thompson(reward)
        
        # 记录历史
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "chunk_id": chunk_id,
            "reward": reward,
            "pull_count": arm.pull_count,
            "avg_reward": arm.avg_reward
        })
    
    def batch_update(
        self, 
        updates: List[Tuple[str, np.ndarray, float]]
    ):
        """
        批量更新
        
        Args:
            updates: [(chunk_id, context, reward), ...]
        """
        for chunk_id, context, reward in updates:
            self.update(chunk_id, context, reward)
    
    def get_chunk_confidence(self, chunk_id: str) -> float:
        """获取 chunk 的置信度"""
        if chunk_id not in self.arms:
            return 0.0
        return self.arms[chunk_id].avg_reward
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_pulls = sum(arm.pull_count for arm in self.arms.values())
        avg_reward = np.mean([arm.avg_reward for arm in self.arms.values()]) if self.arms else 0.0
        
        return {
            "num_arms": len(self.arms),
            "total_pulls": total_pulls,
            "avg_reward": avg_reward,
            "exploration": self.exploration,
            "history_size": len(self.history)
        }
    
    def save(self, path: str):
        """保存模型"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为可序列化格式
        data = {
            "context_dim": self.context_dim,
            "exploration": self.exploration,
            "alpha": self.alpha,
            "epsilon": self.epsilon,
            "chunk_to_intents": self.chunk_to_intents,
            "arms_data": {},
            "history": self.history
        }
        
        for chunk_id, arm in self.arms.items():
            data["arms_data"][chunk_id] = {
                "chunk_id": arm.chunk_id,
                "intent_label": arm.intent_label,
                "A": arm.A.tolist() if arm.A is not None else None,
                "b": arm.b.tolist() if arm.b is not None else None,
                "pull_count": arm.pull_count,
                "total_reward": arm.total_reward,
                "avg_reward": arm.avg_reward,
                "alpha_ts": arm.alpha,
                "beta_ts": arm.beta
            }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, path: str):
        """加载模型"""
        path = Path(path)
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.context_dim = data.get("context_dim", 384)
        self.exploration = data.get("exploration", "linucb")
        self.alpha = data.get("alpha", 1.0)
        self.epsilon = data.get("epsilon", 0.1)
        self.chunk_to_intents = data.get("chunk_to_intents", {})
        self.history = data.get("history", [])
        
        self.arms = {}
        for chunk_id, arm_data in data.get("arms_data", {}).items():
            arm = BanditArm(
                chunk_id=arm_data["chunk_id"],
                intent_label=arm_data["intent_label"]
            )
            
            if arm_data.get("A"):
                arm.A = np.array(arm_data["A"])
            if arm_data.get("b"):
                arm.b = np.array(arm_data["b"])
            
            arm.pull_count = arm_data.get("pull_count", 0)
            arm.total_reward = arm_data.get("total_reward", 0.0)
            arm.avg_reward = arm_data.get("avg_reward", 0.0)
            arm.alpha = arm_data.get("alpha_ts", 1.0)
            arm.beta = arm_data.get("beta_ts", 1.0)
            
            self.arms[chunk_id] = arm


class DialogueSession:
    """对话会话（兼容之前的设计）"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: List[Dict] = []
        self.start_time = datetime.now()
        self.end_time = None
        self.is_complete = False
    
    def add_turn(self, turn: Dict):
        """添加对话轮次"""
        self.turns.append(turn)
    
    def close(self):
        """关闭会话"""
        self.end_time = datetime.now()
        self.is_complete = True
    
    def get_final_chunk(self) -> Optional[str]:
        """获取最终匹配的 chunk"""
        if not self.turns:
            return None
        return self.turns[-1].get("matched_chunk")
    
    def get_final_intent(self) -> Optional[str]:
        """获取最终意图"""
        if not self.turns:
            return None
        return self.turns[-1].get("matched_intent")
    
    def get_final_reward(self) -> float:
        """获取最终奖励"""
        if not self.turns:
            return 0.0
        return self.turns[-1].get("reward", 0.0)


class ContextualBanditRLUpdater:
    """
    基于 Contextual Bandit 的 RL 更新器
    
    结合了：
    1. Contextual Bandit 选择策略
    2. 批量更新机制
    3. 与现有奖励计算模块集成
    """
    
    def __init__(
        self,
        context_dim: int = 384,
        exploration: str = "linucb",
        batch_size: int = 5,
        storage_path: str = "data/contextual_bandit_model.json"
    ):
        self.bandit = ContextualBandit(
            context_dim=context_dim,
            exploration=exploration
        )
        self.batch_size = batch_size
        self.storage_path = Path(storage_path)
        
        # 待处理的会话
        self.pending_sessions: List[Dict] = []
        
        # 加载模型
        self.load()
    
    def init_from_clustering(self, clustering_result: Dict):
        """
        从聚类结果初始化
        
        Args:
            clustering_result: {
                "clusters": [
                    {
                        "cluster_id": "c001",
                        "intent_label": "医疗试验用药申请",
                        "chunks": ["chunk_001", "chunk_002"],
                        "confidence": 0.85
                    },
                    ...
                ]
            }
        """
        for cluster in clustering_result.get("clusters", []):
            intent_label = cluster["intent_label"]
            initial_confidence = cluster.get("confidence", 0.5)
            
            for chunk_id in cluster.get("chunks", []):
                self.bandit.add_arm(chunk_id, intent_label)
                
                # 设置初始平均奖励
                if chunk_id in self.bandit.arms:
                    self.bandit.arms[chunk_id].avg_reward = initial_confidence
                    self.bandit.arms[chunk_id].total_reward = initial_confidence
                    self.bandit.arms[chunk_id].pull_count = 1
        
        self.save()
    
    def get_context(self, query: str, history: List[str] = None) -> np.ndarray:
        """获取上下文嵌入"""
        return self.bandit.get_context_embedding(query, history)
    
    def select_chunks(
        self, 
        query: str, 
        candidate_chunks: List[str] = None,
        top_k: int = 5
    ) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        为查询选择 chunks
        
        Args:
            query: 用户查询
            candidate_chunks: 候选 chunks（来自检索）
            top_k: 返回数量
        
        Returns:
            (最佳chunk, 分数, 候选列表)
        """
        context = self.get_context(query)
        return self.bandit.select_action(context, candidate_chunks, top_k)
    
    def add_session(self, session: DialogueSession) -> bool:
        """
        添加会话到待处理队列
        
        Returns:
            是否触发批量更新
        """
        self.pending_sessions.append({
            "session_id": session.session_id,
            "turns": session.turns,
            "is_complete": session.is_complete
        })
        
        if len(self.pending_sessions) >= self.batch_size:
            self.batch_update()
            return True
        
        return False
    
    def batch_update(self) -> Dict:
        """
        批量更新模型
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "processed_sessions": len(self.pending_sessions),
            "updates": []
        }
        
        for session_data in self.pending_sessions:
            turns = session_data["turns"]
            
            for turn in turns:
                chunk_id = turn.get("matched_chunk")
                query = turn.get("query", "")
                reward = turn.get("reward", 0.0)
                
                if not chunk_id or chunk_id not in self.bandit.arms:
                    continue
                
                # 获取上下文
                context = self.get_context(query)
                
                # 更新 Bandit
                self.bandit.update(chunk_id, context, reward)
                
                results["updates"].append({
                    "chunk_id": chunk_id,
                    "reward": reward,
                    "query": query[:50] + "..." if len(query) > 50 else query
                })
        
        # 清空待处理队列
        self.pending_sessions = []
        
        # 保存模型
        self.save()
        
        return results
    
    def get_chunk_confidence(self, chunk_id: str) -> float:
        """获取 chunk 置信度"""
        return self.bandit.get_chunk_confidence(chunk_id)
    
    def get_top_intents(self, chunk_id: str) -> List[str]:
        """获取 chunk 关联的意图"""
        return self.bandit.chunk_to_intents.get(chunk_id, [])
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.bandit.get_stats()
        stats["pending_sessions"] = len(self.pending_sessions)
        return stats
    
    def save(self):
        """保存模型"""
        self.bandit.save(self.storage_path)
    
    def load(self):
        """加载模型"""
        self.bandit.load(self.storage_path)


def demo():
    """演示 Contextual Bandit"""
    
    print("=" * 60)
    print("Contextual Bandit 演示")
    print("=" * 60)
    
    # 初始化
    updater = ContextualBanditRLUpdater(
        context_dim=384,
        exploration="linucb",
        batch_size=3,
        storage_path="data/contextual_bandit_model.json"
    )
    
    # 从聚类初始化
    clustering_result = {
        "clusters": [
            {
                "cluster_id": "c001",
                "intent_label": "医疗试验用药原材料申请审批",
                "chunks": ["chunk_001"],
                "confidence": 0.70
            },
            {
                "cluster_id": "c002",
                "intent_label": "药物研发CRO流程",
                "chunks": ["chunk_002"],
                "confidence": 0.65
            },
            {
                "cluster_id": "c003",
                "intent_label": "原料制备流程",
                "chunks": ["chunk_003"],
                "confidence": 0.60
            }
        ]
    }
    
    updater.init_from_clustering(clustering_result)
    print(f"\n初始化完成: {updater.get_stats()}")
    
    # 模拟查询
    print("\n--- 模拟查询 ---")
    
    queries = [
        ("试验用药原材料申请怎么走？", ["chunk_001", "chunk_002"]),
        ("CRO流程是什么？", ["chunk_002", "chunk_003"]),
        ("原料制备要注意什么？", ["chunk_001", "chunk_003"]),
    ]
    
    for query, candidates in queries:
        selected, score, top_k = updater.select_chunks(query, candidates, top_k=3)
        print(f"\n查询: {query}")
        print(f"  选择: {selected} (分数: {score:.3f})")
        print(f"  候选: {[(c, f'{s:.3f}') for c, s in top_k]}")
    
    # 模拟反馈更新
    print("\n--- 模拟反馈更新 ---")
    
    sessions = [
        {
            "session_id": "s001",
            "turns": [{
                "query": "试验用药原材料申请怎么走？",
                "matched_chunk": "chunk_001",
                "matched_intent": "医疗试验用药原材料申请审批",
                "reward": 0.85
            }]
        },
        {
            "session_id": "s002",
            "turns": [{
                "query": "CRO流程是什么？",
                "matched_chunk": "chunk_002",
                "matched_intent": "药物研发CRO流程",
                "reward": 0.30
            }]
        },
        {
            "session_id": "s003",
            "turns": [{
                "query": "原料制备要注意什么？",
                "matched_chunk": "chunk_003",
                "matched_intent": "原料制备流程",
                "reward": 0.75
            }]
        }
    ]
    
    for session_data in sessions:
        session = DialogueSession(session_data["session_id"])
        session.turns = session_data["turns"]
        session.is_complete = True
        
        triggered = updater.add_session(session)
        print(f"添加 {session_data['session_id']}: 触发更新={triggered}")
    
    # 查看更新后的状态
    print("\n--- 更新后状态 ---")
    
    for chunk_id in ["chunk_001", "chunk_002", "chunk_003"]:
        conf = updater.get_chunk_confidence(chunk_id)
        intents = updater.get_top_intents(chunk_id)
        print(f"{chunk_id}: 置信度={conf:.3f}, 意图={intents}")
    
    print(f"\n最终统计: {updater.get_stats()}")


if __name__ == "__main__":
    demo()