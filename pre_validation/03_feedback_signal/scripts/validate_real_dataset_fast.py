#!/usr/bin/env python3
"""
真实数据集验证 - 优化版

优化：
1. 批量添加 chunks，避免频繁重建索引
2. 使用预计算的嵌入矩阵，避免重复拷贝
3. 减少内存占用
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random
import sys

# 数据集路径
DATA_DIR = Path(__file__).parent.parent.parent / "datasets"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
PROCESSED_DIR = DATA_DIR / "processed"


class FastVectorStore:
    """优化版向量存储 - 直接使用嵌入矩阵"""
    
    def __init__(self, embeddings: np.ndarray, samples: List[Dict]):
        """
        Args:
            embeddings: 预计算的嵌入矩阵 [N, D]
            samples: 样本列表，与 embeddings 顺序一致
        """
        self.embeddings = embeddings
        self.samples = samples
        self.num_samples = len(samples)
        
        # 预计算归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.normalized = embeddings / np.where(norms > 0, norms, 1)
    
    def search(self, query_idx: int, top_k: int = 5, exclude_indices: set = None) -> List[Tuple[int, float]]:
        """
        向量检索
        
        Args:
            query_idx: 查询样本的索引
            top_k: 返回数量
            exclude_indices: 要排除的索引（避免返回自己）
        """
        query_embedding = self.normalized[query_idx]
        
        # 计算相似度
        similarities = np.dot(self.normalized, query_embedding)
        
        # 排除自己
        if exclude_indices is None:
            exclude_indices = {query_idx}
        
        # 排序（获取 top_k）
        # 使用 argpartition 加速
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        
        # 进一步排序
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
        
        results = []
        for idx in top_indices:
            if idx not in exclude_indices:
                results.append((int(idx), float(similarities[idx])))
        
        # 如果排除后不够，补充更多
        while len(results) < top_k:
            # 找下一个最高的
            remaining_indices = np.argsort(similarities)[::-1]
            for idx in remaining_indices:
                if idx not in exclude_indices and not any(r[0] == idx for r in results):
                    results.append((int(idx), float(similarities[idx])))
                    if len(results) >= top_k:
                        break
        
        return results[:top_k]
    
    def get_intent(self, idx: int) -> str:
        return str(self.samples[idx]["label"])
    
    def get_text(self, idx: int) -> str:
        return self.samples[idx]["text"]


class BanditLayer:
    """Bandit 精排层 - 轻量版"""
    
    def __init__(self, embedding_dim: int = 384, alpha: float = 0.5):
        self.embedding_dim = embedding_dim
        self.alpha = alpha
        
        # 每个 intent 的 Bandit 参数（简化：按 intent 而非 chunk）
        self.intent_params: Dict[str, Dict] = {}
    
    def init_intent(self, intent: str):
        """初始化 intent 的 Bandit 参数"""
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
        """更新 Bandit"""
        self.init_intent(intent)
        params = self.intent_params[intent]
        
        params["A"] += np.outer(query_embedding, query_embedding)
        params["b"] += reward * query_embedding
        params["pull_count"] += 1


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


def run_fast_validation(
    dataset_name: str = "BANKING77",
    test_size: int = 200,
    top_k: int = 5,
    num_rounds: int = 3
):
    """快速验证"""
    
    print("=" * 70)
    print(f"真实数据集验证（优化版）: {dataset_name}")
    print("=" * 70)
    
    # 加载
    samples, embeddings = load_dataset(dataset_name)
    
    # 分割 train/test
    train_indices = [i for i, s in enumerate(samples) if s["split"] == "train"]
    test_indices = [i for i, s in enumerate(samples) if s["split"] == "test"]
    
    print(f"\nTrain: {len(train_indices)}, Test: {len(test_indices)}")
    
    # 初始化
    vector_store = FastVectorStore(embeddings, samples)
    bandit = BanditLayer(embedding_dim=embeddings.shape[1], alpha=0.5)
    
    # 选择测试样本
    random.seed(42)
    test_selected = random.sample(test_indices, min(test_size, len(test_indices)))
    
    print(f"测试样本: {len(test_selected)}")
    
    # 统计
    stats = {"rag_correct": 0, "bandit_correct": 0, "total": 0}
    round_results = []
    
    for round_idx in range(num_rounds):
        print(f"\n--- Round {round_idx + 1} ---")
        
        round_stats = {"rag_correct": 0, "bandit_correct": 0}
        
        for i, test_idx in enumerate(test_selected):
            query_intent = str(samples[test_idx]["label"])
            
            # 检索（排除自己）
            candidates = vector_store.search(test_idx, top_k=top_k, exclude_indices={test_idx})
            
            if not candidates:
                continue
            
            # RAG Top-1
            rag_top1_intent = vector_store.get_intent(candidates[0][0])
            rag_correct = (rag_top1_intent == query_intent)
            
            # Bandit 精排
            query_embedding = embeddings[test_idx]
            
            scored = []
            for cand_idx, sim in candidates:
                intent = vector_store.get_intent(cand_idx)
                score = bandit.score(intent, query_embedding, sim)
                scored.append((cand_idx, score, intent))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            bandit_intent = scored[0][2]
            bandit_correct = (bandit_intent == query_intent)
            
            # 更新统计
            stats["total"] += 1
            if rag_correct:
                stats["rag_correct"] += 1
                round_stats["rag_correct"] += 1
            if bandit_correct:
                stats["bandit_correct"] += 1
                round_stats["bandit_correct"] += 1
            
            # 反馈更新
            reward = 0.8 if bandit_correct else 0.2
            bandit.update(bandit_intent, query_embedding, reward)
            
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
        rag_acc = round_stats["rag_correct"] / len(test_selected)
        bandit_acc = round_stats["bandit_correct"] / len(test_selected)
        print(f"\n  RAG: {rag_acc:.1%}, Bandit: {bandit_acc:.1%}, Δ: {bandit_acc - rag_acc:+.1%}")
        
        round_results.append({
            "round": round_idx + 1,
            "rag_accuracy": rag_acc,
            "bandit_accuracy": bandit_acc
        })
    
    # 总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    print(f"\n数据集: {dataset_name}")
    print(f"测试样本: {test_size}")
    print(f"Top-K: {top_k}")
    
    print(f"\n各轮结果:")
    for r in round_results:
        print(f"  Round {r['round']}: RAG={r['rag_accuracy']:.1%}, Bandit={r['bandit_accuracy']:.1%}, Δ={r['bandit_accuracy']-r['rag_accuracy']:+.1%}")
    
    # 学习效果
    if num_rounds > 1:
        gain = round_results[-1]["bandit_accuracy"] - round_results[0]["bandit_accuracy"]
        print(f"\nBandit 学习增益: {gain:+.1%}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset": dataset_name,
        "config": {"test_size": test_size, "top_k": top_k, "num_rounds": num_rounds},
        "rounds": round_results,
        "final_stats": {
            "rag_accuracy": stats["rag_correct"] / stats["total"],
            "bandit_accuracy": stats["bandit_correct"] / stats["total"]
        }
    }
    
    report_path = Path(__file__).parent.parent / "results" / f"fast_{dataset_name.lower()}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n报告: {report_path}")
    
    return round_results


def compare_datasets():
    """对比数据集"""
    
    print("\n" + "=" * 70)
    print("多数据集对比")
    print("=" * 70)
    
    datasets = ["BANKING77", "CLINC150"]
    results = []
    
    for ds in datasets:
        r = run_fast_validation(ds, test_size=150, top_k=5, num_rounds=2)
        results.append({
            "dataset": ds,
            "rag": r[0]["rag_accuracy"],
            "bandit_final": r[-1]["bandit_accuracy"],
            "gain": r[-1]["bandit_accuracy"] - r[0]["bandit_accuracy"]
        })
    
    print("\n对比:")
    print(f"{'数据集':<12} {'RAG':<8} {'Bandit':<8} {'增益':<8}")
    for r in results:
        print(f"{r['dataset']:<12} {r['rag']:.1%}    {r['bandit_final']:.1%}    {r['gain']:+.1%}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="BANKING77")
    parser.add_argument("--test-size", type=int, default=200)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--compare", action="store_true")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_datasets()
    else:
        run_fast_validation(args.dataset, args.test_size, args.top_k, args.rounds)