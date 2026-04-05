#!/usr/bin/env python3
"""
真实数据集验证 - 可切换策略版

支持策略：
- LinUCB: θᵀx + α√(xᵀA⁻¹x)
- Thompson Sampling: Beta 分布采样

已弃用：ε-greedy（真实数据表现不如 LinUCB/Thompson）
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random
import sys

DATA_DIR = Path(__file__).parent.parent.parent / "datasets"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
PROCESSED_DIR = DATA_DIR / "processed"


class FastVectorStore:
    """向量存储 - 直接使用预计算嵌入矩阵"""
    
    def __init__(self, embeddings: np.ndarray, samples: List[Dict]):
        self.embeddings = embeddings
        self.samples = samples
        self.num_samples = len(samples)
        
        # 预计算归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.normalized = embeddings / np.where(norms > 0, norms, 1)
    
    def search(self, query_idx: int, top_k: int = 5) -> List[Tuple[int, float]]:
        """向量检索"""
        query_embedding = self.normalized[query_idx]
        similarities = np.dot(self.normalized, query_embedding)
        
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
        
        results = []
        for idx in top_indices:
            if idx != query_idx:
                results.append((int(idx), float(similarities[idx])))
        return results[:top_k]
    
    def get_intent(self, idx: int) -> str:
        return str(self.samples[idx]["label"])
    
    def get_text(self, idx: int) -> str:
        return self.samples[idx]["text"]


class LinUCBStrategy:
    """
    LinUCB 策略
    
    公式: UCB = θᵀx + α√(xᵀA⁻¹x)
    
    特点：
    - 利用上下文信息（查询嵌入）
    - 探索-利用平衡可调（α参数）
    - BANKING77 上表现最优 (92%)
    """
    
    def __init__(self, embedding_dim: int = 384, alpha: float = 1.0):
        self.embedding_dim = embedding_dim
        self.alpha = alpha
        self.intent_params: Dict[str, Dict] = {}
    
    def init_intent(self, intent: str):
        if intent not in self.intent_params:
            self.intent_params[intent] = {
                "A": np.eye(self.embedding_dim) * 0.01,
                "b": np.zeros(self.embedding_dim),
                "pull_count": 0,
                "avg_reward": 0.5
            }
    
    def score(self, intent: str, query_embedding: np.ndarray, similarity: float) -> float:
        """计算 UCB 分数"""
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        try:
            theta = np.linalg.solve(params["A"], params["b"])
            p = np.dot(theta, query_embedding)
            
            A_inv = np.linalg.inv(params["A"])
            uncertainty = min(np.sqrt(np.dot(query_embedding, np.dot(A_inv, query_embedding))), 5.0)
            
            ucb = np.clip(p + self.alpha * uncertainty, -1, 1)
            
            return 0.4 * similarity + 0.6 * (ucb / 2)
        except:
            return similarity
    
    def update(self, intent: str, query_embedding: np.ndarray, reward: float):
        """更新 LinUCB 参数"""
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        params["A"] += np.outer(query_embedding, query_embedding)
        params["b"] += reward * query_embedding
        params["pull_count"] += 1
        params["avg_reward"] = (params["avg_reward"] * (params["pull_count"] - 1) + reward) / params["pull_count"]
    
    def get_name(self) -> str:
        return f"LinUCB(α={self.alpha})"
    
    def get_stats(self) -> Dict:
        return {
            "num_intents": len(self.intent_params),
            "avg_pull_count": np.mean([p["pull_count"] for p in self.intent_params.values()]) if self.intent_params else 0,
            "avg_reward": np.mean([p["avg_reward"] for p in self.intent_params.values()]) if self.intent_params else 0.5
        }


class ThompsonSamplingStrategy:
    """
    Thompson Sampling 策略
    
    使用 Beta 分布建模每个 intent 的奖励概率
    
    特点：
    - 不需要嵌入上下文（简化版）
    - 自适应探索（根据历史奖励）
    - CLINC150 上表现最优 (88%)
    """
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.intent_params: Dict[str, Dict] = {}
    
    def init_intent(self, intent: str):
        if intent not in self.intent_params:
            self.intent_params[intent] = {
                "alpha": 1.0,  # Beta 分布参数（成功次数+1）
                "beta": 1.0,   # Beta 分布参数（失败次数+1）
                "pull_count": 0,
                "total_reward": 0.0,
                "avg_reward": 0.5
            }
    
    def score(self, intent: str, query_embedding: np.ndarray, similarity: float) -> float:
        """从 Beta 分布采样计算分数"""
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        # 从 Beta(alpha, beta) 采样
        sample = np.random.beta(params["alpha"], params["beta"])
        
        # 结合相似度
        return 0.3 * similarity + 0.7 * sample
    
    def update(self, intent: str, query_embedding: np.ndarray, reward: float):
        """更新 Beta 分布参数"""
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        # 根据 reward 更新 alpha/beta
        # reward > 0.5 视为成功，增加 alpha
        # reward < 0.5 视为失败，增加 beta
        if reward >= 0.5:
            params["alpha"] += (reward - 0.5) * 2 + 0.5  # 加权更新
        else:
            params["beta"] += (0.5 - reward) * 2 + 0.5
        
        params["pull_count"] += 1
        params["total_reward"] += reward
        params["avg_reward"] = params["total_reward"] / params["pull_count"]
    
    def get_name(self) -> str:
        return "Thompson Sampling"
    
    def get_stats(self) -> Dict:
        return {
            "num_intents": len(self.intent_params),
            "avg_pull_count": np.mean([p["pull_count"] for p in self.intent_params.values()]) if self.intent_params else 0,
            "avg_reward": np.mean([p["avg_reward"] for p in self.intent_params.values()]) if self.intent_params else 0.5
        }


def create_strategy(strategy_name: str, embedding_dim: int = 384, **kwargs):
    """
    创建策略实例
    
    Args:
        strategy_name: "linucb" 或 "thompson"
        embedding_dim: 嵌入维度
        **kwargs: 策略参数（如 alpha for LinUCB）
    
    Returns:
        Strategy 实例
    """
    if strategy_name.lower() == "linucb":
        alpha = kwargs.get("alpha", 1.0)
        return LinUCBStrategy(embedding_dim=embedding_dim, alpha=alpha)
    elif strategy_name.lower() == "thompson":
        return ThompsonSamplingStrategy(embedding_dim=embedding_dim)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}. Use 'linucb' or 'thompson'")


def load_dataset(dataset_name: str) -> Tuple[List[Dict], np.ndarray]:
    """加载真实数据集"""
    print(f"\n加载 {dataset_name} 数据集...")
    
    embeddings_path = EMBEDDINGS_DIR / f"{dataset_name.lower()}_embeddings.npy"
    embeddings = np.load(embeddings_path)
    print(f"  嵌入: {embeddings.shape}")
    
    processed_path = PROCESSED_DIR / f"{dataset_name.lower()}_processed.json"
    with open(processed_path, "r") as f:
        samples = json.load(f)
    
    print(f"  样本数: {len(samples)}")
    intents = set(s["label"] for s in samples)
    print(f"  意图类别数: {len(intents)}")
    
    return samples, embeddings


def run_validation(
    dataset_name: str = "BANKING77",
    strategy_name: str = "linucb",  # "linucb" or "thompson"
    test_size: int = 200,
    top_k: int = 5,
    num_rounds: int = 3,
    seed: int = 42,
    **strategy_kwargs
):
    """
    真实数据集验证
    
    Args:
        dataset_name: 数据集名称
        strategy_name: 策略名称 ("linucb" or "thompson")
        test_size: 测试样本数
        top_k: RAG Top-K
        num_rounds: 测试轮数
        seed: 随机种子
        **strategy_kwargs: 策略参数
    """
    
    print("=" * 70)
    print(f"真实数据集验证: {dataset_name}")
    print(f"策略: {strategy_name}")
    print("=" * 70)
    
    # 加载
    samples, embeddings = load_dataset(dataset_name)
    
    train_indices = [i for i, s in enumerate(samples) if s["split"] == "train"]
    test_indices = [i for i, s in enumerate(samples) if s["split"] == "test"]
    
    print(f"\nTrain: {len(train_indices)}, Test: {len(test_indices)}")
    
    # 初始化
    vector_store = FastVectorStore(embeddings, samples)
    strategy = create_strategy(strategy_name, embeddings.shape[1], **strategy_kwargs)
    
    # 选择测试样本
    random.seed(seed)
    np.random.seed(seed)
    test_selected = random.sample(test_indices, min(test_size, len(test_indices)))
    
    print(f"测试样本: {len(test_selected)}")
    
    # 统计
    round_results = []
    
    for round_idx in range(num_rounds):
        print(f"\n--- Round {round_idx + 1} ---")
        
        round_correct = 0
        round_fixed = 0  # Bandit 纠正 RAG 错误
        
        for i, test_idx in enumerate(test_selected):
            query_intent = str(samples[test_idx]["label"])
            query_embedding = embeddings[test_idx]
            
            # 检索
            candidates = vector_store.search(test_idx, top_k=top_k)
            
            if not candidates:
                continue
            
            # RAG Top-1
            rag_top1_intent = vector_store.get_intent(candidates[0][0])
            rag_correct = (rag_top1_intent == query_intent)
            
            # Bandit 精排
            scored = []
            for cand_idx, sim in candidates:
                intent = vector_store.get_intent(cand_idx)
                score = strategy.score(intent, query_embedding, sim)
                scored.append((cand_idx, score, intent))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            bandit_intent = scored[0][2]
            bandit_correct = (bandit_intent == query_intent)
            
            # 统计
            if bandit_correct:
                round_correct += 1
            if not rag_correct and bandit_correct:
                round_fixed += 1
            
            # 反馈更新
            reward = 0.8 if bandit_correct else 0.2
            strategy.update(bandit_intent, query_embedding, reward)
            
            # 显示关键案例
            if i < 3 or (rag_correct != bandit_correct):
                status = ""
                if not rag_correct and bandit_correct:
                    status = "🎯 纠正"
                elif rag_correct and not bandit_correct:
                    status = "⚠️ 选错"
                if i < 5 or status:
                    print(f"  [{i+1}] RAG:{int(rag_correct)} Bandit:{int(bandit_correct)} {status}")
        
        # 本轮统计
        accuracy = round_correct / len(test_selected)
        fixed_rate = round_fixed / len(test_selected)
        
        print(f"\n  准确率: {accuracy:.1%}, 纠正率: {fixed_rate:.1%}")
        
        round_results.append({
            "round": round_idx + 1,
            "accuracy": accuracy,
            "fixed_count": round_fixed,
            "fixed_rate": fixed_rate,
            "strategy_stats": strategy.get_stats()
        })
    
    # 总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    print(f"\n数据集: {dataset_name}")
    print(f"策略: {strategy.get_name()}")
    print(f"测试样本: {test_size}")
    
    print(f"\n各轮结果:")
    for r in round_results:
        print(f"  Round {r['round']}: {r['accuracy']:.1%} (纠正 {r['fixed_count']} 个)")
    
    # 学习增益
    if num_rounds > 1:
        gain = round_results[-1]["accuracy"] - round_results[0]["accuracy"]
        print(f"\n学习增益: {gain:+.1%}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset": dataset_name,
        "strategy": strategy.get_name(),
        "config": {
            "test_size": test_size,
            "top_k": top_k,
            "num_rounds": num_rounds,
            "seed": seed,
            "strategy_kwargs": strategy_kwargs
        },
        "rounds": round_results,
        "final_accuracy": round_results[-1]["accuracy"],
        "learning_gain": round_results[-1]["accuracy"] - round_results[0]["accuracy"] if num_rounds > 1 else 0
    }
    
    report_path = Path(__file__).parent.parent / "results" / f"{strategy_name}_{dataset_name.lower()}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n报告: {report_path}")
    
    return round_results


def compare_strategies(dataset_name: str = "BANKING77"):
    """对比两种策略"""
    
    print("\n" + "=" * 70)
    print(f"策略对比: {dataset_name}")
    print("=" * 70)
    
    results = {}
    
    for strategy in ["linucb", "thompson"]:
        print(f"\n--- {strategy.upper()} ---")
        r = run_validation(
            dataset_name=dataset_name,
            strategy_name=strategy,
            test_size=150,
            num_rounds=2,
            seed=42
        )
        results[strategy] = r
    
    # 对比
    print("\n" + "=" * 70)
    print("对比结果")
    print("=" * 70)
    
    print(f"\n{'策略':<15} {'Round 1':<10} {'Round 2':<10} {'增益':<10}")
    
    for strategy, rounds in results.items():
        r1 = rounds[0]["accuracy"]
        r2 = rounds[-1]["accuracy"]
        gain = r2 - r1
        print(f"{strategy.upper():<15} {r1:.1%}      {r2:.1%}      {gain:+.1%}")
    
    best = max(results.items(), key=lambda x: x[1][-1]["accuracy"])
    print(f"\n最优: {best[0].upper()} ({best[1][-1]['accuracy']:.1%})")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="真实数据集验证")
    parser.add_argument("--dataset", default="BANKING77", help="数据集名称")
    parser.add_argument("--strategy", default="linucb", choices=["linucb", "thompson"], help="策略名称")
    parser.add_argument("--test-size", type=int, default=200)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--alpha", type=float, default=1.0, help="LinUCB 探索系数")
    parser.add_argument("--compare", action="store_true", help="对比两种策略")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_strategies(args.dataset)
    else:
        run_validation(
            dataset_name=args.dataset,
            strategy_name=args.strategy,
            test_size=args.test_size,
            top_k=args.top_k,
            num_rounds=args.rounds,
            alpha=args.alpha
        )