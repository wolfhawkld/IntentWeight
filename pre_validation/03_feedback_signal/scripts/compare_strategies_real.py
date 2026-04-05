#!/usr/bin/env python3
"""
真实数据集 - 多策略对比验证

对比 LinUCB / Thompson Sampling / ε-greedy 在真实数据集上的表现。

之前的模拟数据结果：
| 策略 | 准确率 | 平均奖励 |
|------|--------|----------|
| LinUCB | 90% | 0.79 |
| Thompson Sampling | 20% | 0.37 |
| ε-greedy | 50% | 0.60 |

现在用 BANKING77/CLINC150 真实数据验证。
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import random

DATA_DIR = Path(__file__).parent.parent.parent / "datasets"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
PROCESSED_DIR = DATA_DIR / "processed"


class FastVectorStore:
    """向量存储"""
    
    def __init__(self, embeddings: np.ndarray, samples: List[Dict]):
        self.embeddings = embeddings
        self.samples = samples
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.normalized = embeddings / np.where(norms > 0, norms, 1)
    
    def search(self, query_idx: int, top_k: int = 5) -> List[Tuple[int, float]]:
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


class LinUCBStrategy:
    """LinUCB 策略"""
    
    def __init__(self, embedding_dim: int = 384, alpha: float = 1.0):
        self.embedding_dim = embedding_dim
        self.alpha = alpha
        self.intent_params: Dict[str, Dict] = {}
    
    def init_intent(self, intent: str):
        if intent not in self.intent_params:
            self.intent_params[intent] = {
                "A": np.eye(self.embedding_dim) * 0.01,
                "b": np.zeros(self.embedding_dim),
                "pull_count": 0
            }
    
    def score(self, intent: str, query_embedding: np.ndarray, similarity: float) -> float:
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
        self.init_intent(intent)
        params = self.intent_params[intent]
        params["A"] += np.outer(query_embedding, query_embedding)
        params["b"] += reward * query_embedding
        params["pull_count"] += 1
    
    def get_name(self):
        return "LinUCB"


class ThompsonSamplingStrategy:
    """Thompson Sampling 策略"""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.intent_params: Dict[str, Dict] = {}
    
    def init_intent(self, intent: str):
        if intent not in self.intent_params:
            self.intent_params[intent] = {
                "alpha": 1.0,  # Beta 分布参数
                "beta": 1.0,
                "pull_count": 0,
                "total_reward": 0.0
            }
    
    def score(self, intent: str, query_embedding: np.ndarray, similarity: float) -> float:
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        # 从 Beta 分布采样
        sample = np.random.beta(params["alpha"], params["beta"])
        
        # 结合相似度
        return 0.3 * similarity + 0.7 * sample
    
    def update(self, intent: str, query_embedding: np.ndarray, reward: float):
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        # 更新 Beta 分布参数
        # reward > 0.5 → 成功，增加 alpha
        # reward < 0.5 → 失败，增加 beta
        if reward > 0.5:
            params["alpha"] += (reward - 0.5) * 2  # 加权更新
        else:
            params["beta"] += (0.5 - reward) * 2
        
        params["pull_count"] += 1
        params["total_reward"] += reward
    
    def get_name(self):
        return "Thompson Sampling"


class EpsilonGreedyStrategy:
    """ε-greedy 策略"""
    
    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon
        self.intent_stats: Dict[str, Dict] = {}
    
    def init_intent(self, intent: str):
        if intent not in self.intent_stats:
            self.intent_stats[intent] = {
                "pull_count": 0,
                "total_reward": 0.0,
                "avg_reward": 0.5
            }
    
    def score(self, intent: str, query_embedding: np.ndarray, similarity: float) -> float:
        self.init_intent(intent)
        
        # ε 概率探索，1-ε 概率利用
        if np.random.random() < self.epsilon:
            # 探索：随机分数
            return np.random.random()
        else:
            # 利用：使用平均奖励 + 相似度
            avg_reward = self.intent_stats[intent]["avg_reward"]
            return 0.4 * similarity + 0.6 * avg_reward
    
    def update(self, intent: str, query_embedding: np.ndarray, reward: float):
        self.init_intent(intent)
        stats = self.intent_stats[intent]
        
        stats["pull_count"] += 1
        stats["total_reward"] += reward
        stats["avg_reward"] = stats["total_reward"] / stats["pull_count"]
    
    def get_name(self):
        return f"ε-greedy (ε={self.epsilon})"


def load_dataset(dataset_name: str) -> Tuple[List[Dict], np.ndarray]:
    embeddings_path = EMBEDDINGS_DIR / f"{dataset_name.lower()}_embeddings.npy"
    embeddings = np.load(embeddings_path)
    
    processed_path = PROCESSED_DIR / f"{dataset_name.lower()}_processed.json"
    with open(processed_path, "r") as f:
        samples = json.load(f)
    
    return samples, embeddings


def run_strategy_comparison(
    dataset_name: str = "BANKING77",
    test_size: int = 150,
    top_k: int = 5,
    num_rounds: int = 2
):
    """多策略对比验证"""
    
    print("=" * 70)
    print(f"真实数据集策略对比: {dataset_name}")
    print("=" * 70)
    
    samples, embeddings = load_dataset(dataset_name)
    
    train_indices = [i for i, s in enumerate(samples) if s["split"] == "train"]
    test_indices = [i for i, s in enumerate(samples) if s["split"] == "test"]
    
    print(f"Train: {len(train_indices)}, Test: {len(test_indices)}")
    
    vector_store = FastVectorStore(embeddings, samples)
    
    # 三种策略
    strategies = [
        LinUCBStrategy(embedding_dim=embeddings.shape[1], alpha=1.0),
        ThompsonSamplingStrategy(embedding_dim=embeddings.shape[1]),
        EpsilonGreedyStrategy(epsilon=0.1)
    ]
    
    # 选择测试样本
    random.seed(42)
    test_selected = random.sample(test_indices, min(test_size, len(test_indices)))
    
    print(f"测试样本: {len(test_selected)}")
    
    # 结果记录
    all_results = {}
    
    for strategy in strategies:
        print(f"\n--- {strategy.get_name()} ---")
        
        strategy_results = []
        
        for round_idx in range(num_rounds):
            round_correct = 0
            
            for test_idx in test_selected:
                query_intent = str(samples[test_idx]["label"])
                query_embedding = embeddings[test_idx]
                
                # 检索
                candidates = vector_store.search(test_idx, top_k=top_k)
                
                if not candidates:
                    continue
                
                # 用策略排序
                scored = []
                for cand_idx, sim in candidates:
                    intent = vector_store.get_intent(cand_idx)
                    score = strategy.score(intent, query_embedding, sim)
                    scored.append((cand_idx, score, intent))
                
                scored.sort(key=lambda x: x[1], reverse=True)
                selected_intent = scored[0][2]
                
                # 判断正确性
                correct = (selected_intent == query_intent)
                if correct:
                    round_correct += 1
                
                # 反馈更新
                reward = 0.8 if correct else 0.2
                strategy.update(selected_intent, query_embedding, reward)
            
            accuracy = round_correct / len(test_selected)
            strategy_results.append({
                "round": round_idx + 1,
                "accuracy": accuracy
            })
            
            print(f"  Round {round_idx+1}: {accuracy:.1%}")
        
        all_results[strategy.get_name()] = strategy_results
    
    # 对比总结
    print("\n" + "=" * 70)
    print("策略对比总结")
    print("=" * 70)
    
    print(f"\n{'策略':<20} {'Round 1':<10} {'Round 2':<10} {'增益':<10}")
    
    comparison = []
    for name, results in all_results.items():
        r1 = results[0]["accuracy"]
        r2 = results[-1]["accuracy"]
        gain = r2 - r1
        print(f"{name:<20} {r1:.1%}      {r2:.1%}      {gain:+.1%}")
        comparison.append({
            "strategy": name,
            "round1": r1,
            "round2": r2,
            "gain": gain
        })
    
    # 排序找最优
    best = max(comparison, key=lambda x: x["round2"])
    print(f"\n最优策略: {best['strategy']} (准确率 {best['round2']:.1%})")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset": dataset_name,
        "config": {"test_size": test_size, "top_k": top_k, "num_rounds": num_rounds},
        "comparison": comparison,
        "details": all_results,
        "best_strategy": best["strategy"]
    }
    
    report_path = Path(__file__).parent.parent / "results" / f"strategy_comparison_{dataset_name.lower()}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n报告: {report_path}")
    
    return comparison


def compare_all_datasets():
    """所有数据集对比"""
    
    datasets = ["BANKING77", "CLINC150"]
    
    print("\n" + "=" * 70)
    print("多数据集策略对比")
    print("=" * 70)
    
    all_comparison = []
    
    for ds in datasets:
        comparison = run_strategy_comparison(ds, test_size=150, top_k=5, num_rounds=2)
        all_comparison.append({"dataset": ds, "strategies": comparison})
    
    # 最终总结
    print("\n" + "=" * 70)
    print("跨数据集总结")
    print("=" * 70)
    
    print(f"\n{'数据集':<12} {'最优策略':<20} {'准确率':<10}")
    for item in all_comparison:
        best = max(item["strategies"], key=lambda x: x["round2"])
        print(f"{item['dataset']:<12} {best['strategy']:<20} {best['round2']:.1%}")
    
    return all_comparison


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="BANKING77")
    parser.add_argument("--test-size", type=int, default=150)
    parser.add_argument("--all", action="store_true", help="对比所有数据集")
    
    args = parser.parse_args()
    
    if args.all:
        compare_all_datasets()
    else:
        run_strategy_comparison(args.dataset, args.test_size)