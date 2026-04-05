#!/usr/bin/env python3
"""
真实数据集验证 - BANKING77 / CLINC150

将模拟数据替换为真实数据集，验证 RAG + Bandit 系统的反馈闭环效果。

设计：
1. 知识库：用 train 样本作为 chunks（每个样本 = 一个知识条目）
2. 查询：用 test 样本作为查询，ground_truth = 同 intent 的 train 样本
3. 反馈：正确召回 → 高奖励，错误召回 → 低奖励
4. 验证：Bandit 学习后能否提升召回准确率

与模拟数据验证的区别：
- 嵌入：真实 SBERT 嵌入（已生成）
- 数据规模：13,083 (BANKING77) / 23,850 (CLINC150)
- 意图分布：77 / 151 个意图类别
"""

import json
import csv
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import sys
import random

# 数据集路径
DATA_DIR = Path(__file__).parent.parent.parent / "datasets"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
PROCESSED_DIR = DATA_DIR / "processed"

@dataclass
class Chunk:
    """知识库内容块"""
    chunk_id: str
    content: str
    intent: str
    embedding: np.ndarray = None


class VectorStore:
    """向量存储 - 使用真实嵌入"""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.chunks: Dict[str, Chunk] = {}
        self.embeddings: np.ndarray = None
        self.chunk_ids: List[str] = []
    
    def add_chunk(self, chunk: Chunk):
        """添加 chunk"""
        self.chunks[chunk.chunk_id] = chunk
        self._rebuild_index()
    
    def _rebuild_index(self):
        """重建索引"""
        self.chunk_ids = list(self.chunks.keys())
        embeddings_list = [self.chunks[cid].embedding for cid in self.chunk_ids]
        if embeddings_list:
            self.embeddings = np.vstack(embeddings_list)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """向量检索"""
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # 余弦相似度
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm
        
        # 归一化 embeddings（如果需要）
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normalized = self.embeddings / np.where(norms > 0, norms, 1)
        
        similarities = np.dot(normalized, query_embedding)
        
        # 排序
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            chunk_id = self.chunk_ids[idx]
            sim = float(similarities[idx])
            results.append((chunk_id, sim))
        
        return results
    
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        return self.chunks.get(chunk_id)


class RealDatasetBanditSystem:
    """真实数据集的 RAG + Bandit 系统"""
    
    def __init__(
        self,
        embedding_dim: int = 384,
        exploration_alpha: float = 1.0,
        rag_top_k: int = 10
    ):
        self.embedding_dim = embedding_dim
        self.exploration_alpha = exploration_alpha
        self.rag_top_k = rag_top_k
        
        self.vector_store = VectorStore(embedding_dim)
        self.bandit_params: Dict[str, Dict] = {}
        
        self.stats = {
            "total_queries": 0,
            "rag_correct": 0,
            "bandit_correct": 0,
            "feedback_count": 0,
            "bandit_fixed": 0,
            "bandit_broke": 0
        }
    
    def add_chunk(self, chunk_id: str, content: str, intent: str, embedding: np.ndarray):
        """添加文档"""
        chunk = Chunk(
            chunk_id=chunk_id,
            content=content,
            intent=intent,
            embedding=embedding
        )
        self.vector_store.add_chunk(chunk)
        
        # 初始化 Bandit 参数
        self.bandit_params[chunk_id] = {
            "A": np.eye(self.embedding_dim) * 0.01,  # 小初始值防止溢出
            "b": np.zeros(self.embedding_dim),
            "pull_count": 0,
            "total_reward": 0.0,
            "avg_reward": 0.5
        }
    
    def retrieve(self, query_embedding: np.ndarray, top_k: int = None) -> List[Tuple[str, float]]:
        """RAG 召回"""
        if top_k is None:
            top_k = self.rag_top_k
        return self.vector_store.search(query_embedding, top_k)
    
    def select_with_bandit(
        self,
        query_embedding: np.ndarray,
        candidates: List[Tuple[str, float]]
    ) -> Tuple[str, float, List[Tuple[str, float]]]:
        """Bandit 精排"""
        if not candidates:
            return None, 0.0, []
        
        scored_candidates = []
        for chunk_id, similarity in candidates:
            if chunk_id not in self.bandit_params:
                score = similarity
            else:
                params = self.bandit_params[chunk_id]
                
                try:
                    # LinUCB 计算
                    theta = np.linalg.solve(params["A"], params["b"])
                    p = np.dot(theta, query_embedding)
                    
                    A_inv = np.linalg.inv(params["A"])
                    uncertainty = np.sqrt(np.dot(query_embedding, np.dot(A_inv, query_embedding)))
                    
                    # 防止数值爆炸
                    uncertainty = min(uncertainty, 10.0)
                    p = np.clip(p, -1.0, 1.0)
                    
                    ucb_score = p + self.exploration_alpha * uncertainty
                    
                    # 结合相似度
                    score = 0.4 * similarity + 0.6 * (ucb_score / 2)
                except np.linalg.LinAlgError:
                    score = similarity
            
            scored_candidates.append((chunk_id, float(score)))
        
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return scored_candidates[0][0], scored_candidates[0][1], scored_candidates
    
    def query(
        self,
        query_embedding: np.ndarray,
        ground_truth_intent: str,
        return_stats: bool = True
    ) -> Dict:
        """查询"""
        if return_stats:
            self.stats["total_queries"] += 1
        
        candidates = self.retrieve(query_embedding, top_k=self.rag_top_k)
        
        if not candidates:
            return {
                "rag_top1": None,
                "rag_top1_intent": None,
                "bandit_selected": None,
                "bandit_intent": None,
                "rag_correct": False,
                "bandit_correct": False,
                "candidates": []
            }
        
        # RAG Top-1
        rag_top1 = candidates[0][0]
        rag_top1_intent = self.vector_store.get_chunk(rag_top1).intent
        
        # Bandit 精排
        bandit_selected, bandit_score, ranked = self.select_with_bandit(query_embedding, candidates)
        bandit_intent = self.vector_store.get_chunk(bandit_selected).intent
        
        # 验证（intent 匹配即可）
        rag_correct = (rag_top1_intent == ground_truth_intent)
        bandit_correct = (bandit_intent == ground_truth_intent)
        
        if return_stats:
            if rag_correct:
                self.stats["rag_correct"] += 1
            if bandit_correct:
                self.stats["bandit_correct"] += 1
        
        return {
            "rag_top1": rag_top1,
            "rag_top1_intent": rag_top1_intent,
            "bandit_selected": bandit_selected,
            "bandit_intent": bandit_intent,
            "rag_correct": rag_correct,
            "bandit_correct": bandit_correct,
            "candidates": ranked[:5]
        }
    
    def update_from_feedback(
        self,
        chunk_id: str,
        query_embedding: np.ndarray,
        reward: float
    ):
        """反馈更新"""
        if chunk_id not in self.bandit_params:
            return
        
        params = self.bandit_params[chunk_id]
        
        # LinUCB 更新
        params["A"] += np.outer(query_embedding, query_embedding)
        params["b"] += reward * query_embedding
        
        params["pull_count"] += 1
        params["total_reward"] += reward
        params["avg_reward"] = params["total_reward"] / params["pull_count"]
        
        self.stats["feedback_count"] += 1
    
    def get_stats(self) -> Dict:
        total = self.stats["total_queries"]
        return {
            "total_queries": total,
            "rag_accuracy": self.stats["rag_correct"] / total if total > 0 else 0,
            "bandit_accuracy": self.stats["bandit_correct"] / total if total > 0 else 0,
            "feedback_count": self.stats["feedback_count"],
            "bandit_fixed": self.stats["bandit_fixed"],
            "bandit_broke": self.stats["bandit_broke"]
        }


def load_dataset(dataset_name: str) -> Tuple[List[Dict], np.ndarray, Dict]:
    """
    加载真实数据集
    
    Returns:
        (samples_list, embeddings, meta)
    """
    print(f"\n加载 {dataset_name} 数据集...")
    
    # 加载嵌入
    embeddings_path = EMBEDDINGS_DIR / f"{dataset_name.lower()}_embeddings.npy"
    embeddings = np.load(embeddings_path)
    print(f"  嵌入: {embeddings.shape}")
    
    # 加载元数据
    meta_path = EMBEDDINGS_DIR / f"{dataset_name.lower()}_meta.json"
    with open(meta_path, "r") as f:
        meta = json.load(f)
    
    # 加载处理后的数据（JSON 数组格式）
    processed_path = PROCESSED_DIR / f"{dataset_name.lower()}_processed.json"
    with open(processed_path, "r") as f:
        samples = json.load(f)
    
    print(f"  样本数: {len(samples)}")
    print(f"  意图类别数: {len(set(s['label'] for s in samples))}")
    
    return samples, embeddings, meta


def run_real_dataset_validation(
    dataset_name: str = "BANKING77",
    sample_size: int = 500,
    rag_top_k: int = 10,
    num_rounds: int = 3
):
    """
    真实数据集验证
    
    Args:
        dataset_name: 数据集名称
        sample_size: 每轮测试的样本数
        rag_top_k: RAG 召回数量
        num_rounds: 测试轮数（每轮后 Bandit 学习）
    """
    
    print("=" * 70)
    print(f"真实数据集验证: {dataset_name}")
    print("=" * 70)
    
    # 加载数据
    samples, embeddings, meta = load_dataset(dataset_name)
    
    # 分割 train/test
    train_samples = [s for s in samples if s["split"] == "train"]
    test_samples = [s for s in samples if s["split"] == "test"]
    
    print(f"\n数据分割:")
    print(f"  Train: {len(train_samples)}")
    print(f"  Test: {len(test_samples)}")
    
    # 初始化系统
    print(f"\n[Step 1] 构建知识库...")
    
    system = RealDatasetBanditSystem(
        embedding_dim=embeddings.shape[1],
        exploration_alpha=0.5,  # 较低的探索系数
        rag_top_k=rag_top_k
    )
    
    # 添加 train 样本作为知识库
    for i, s in enumerate(train_samples):
        chunk_id = f"train_{i}"
        embedding = embeddings[i]  # train 样本的嵌入
        system.add_chunk(
            chunk_id=chunk_id,
            content=s["text"],
            intent=str(s["label"]),
            embedding=embedding
        )
    
    print(f"  知识库大小: {len(train_samples)} 个 chunks")
    
    # 选择测试样本（按 intent 分层抽样）
    print(f"\n[Step 2] 选择测试样本 (N={sample_size})...")
    
    # 按 intent 分组
    intent_to_test = {}
    for s in test_samples:
        intent = s["label"]
        if intent not in intent_to_test:
            intent_to_test[intent] = []
        intent_to_test[intent].append(s)
    
    # 分层抽样
    test_selected = []
    intents = list(intent_to_test.keys())
    per_intent = max(1, sample_size // len(intents))
    
    for intent in intents:
        samples_for_intent = intent_to_test[intent]
        n = min(per_intent, len(samples_for_intent))
        test_selected.extend(random.sample(samples_for_intent, n))
    
    # 补足样本数
    while len(test_selected) < sample_size:
        remaining = [s for s in test_samples if s not in test_selected]
        if not remaining:
            break
        test_selected.append(random.choice(remaining))
    
    print(f"  选择了 {len(test_selected)} 个测试样本")
    print(f"  覆盖 {len(set(s['label'] for s in test_selected))} 个意图类别")
    
    # 多轮测试
    all_results = []
    
    for round_idx in range(num_rounds):
        print(f"\n[Step 3.{round_idx+1}] 第 {round_idx+1} 轮测试...")
        
        round_results = []
        
        for i, test_s in enumerate(test_selected):
            # 找到 test_s 在原始 samples 列表中的索引
            # 注意：processed JSON 的顺序与 embeddings 顺序一致
            test_idx = None
            for j, s in enumerate(samples):
                if s["text"] == test_s["text"] and s["label"] == test_s["label"]:
                    test_idx = j
                    break
            
            if test_idx is None:
                print(f"  警告: 找不到测试样本 {i}")
                continue
            
            query_embedding = embeddings[test_idx]
            ground_truth_intent = str(test_s["label"])
            
            # 查询
            result = system.query(query_embedding, ground_truth_intent)
            
            # 显示部分结果
            if i < 5 or (result["rag_correct"] != result["bandit_correct"]):
                status = ""
                if not result["rag_correct"] and result["bandit_correct"]:
                    status = "🎯 Bandit 纠正!"
                    system.stats["bandit_fixed"] += 1
                elif result["rag_correct"] and not result["bandit_correct"]:
                    status = "⚠️ Bandit 选错"
                    system.stats["bandit_broke"] += 1
                
                if i < 5:
                    print(f"  [{i+1}] RAG: {result['rag_correct']} | Bandit: {result['bandit_correct']} {status}")
            
            round_results.append({
                "query_idx": test_idx,
                "query_text": test_s["text"],
                "ground_truth_intent": ground_truth_intent,
                "rag_correct": result["rag_correct"],
                "bandit_correct": result["bandit_correct"],
                "rag_intent": result["rag_top1_intent"],
                "bandit_intent": result["bandit_intent"]
            })
            
            # 模拟反馈
            # 正确 → 奖励 0.8，错误 → 奖励 0.2
            reward = 0.8 if result["bandit_correct"] else 0.2
            
            # 更新 Bandit
            if result["bandit_selected"]:
                chunk = system.vector_store.get_chunk(result["bandit_selected"])
                if chunk:
                    system.update_from_feedback(
                        result["bandit_selected"],
                        query_embedding,
                        reward
                    )
        
        # 统计本轮
        rag_correct = sum(1 for r in round_results if r["rag_correct"])
        bandit_correct = sum(1 for r in round_results if r["bandit_correct"])
        
        print(f"\n第 {round_idx+1} 轮统计:")
        print(f"  RAG 准确率: {rag_correct}/{len(round_results)} ({rag_correct/len(round_results):.1%})")
        print(f"  Bandit 准确率: {bandit_correct}/{len(round_results)} ({bandit_correct/len(round_results):.1%})")
        
        all_results.append({
            "round": round_idx + 1,
            "rag_accuracy": rag_correct / len(round_results),
            "bandit_accuracy": bandit_correct / len(round_results),
            "details": round_results
        })
    
    # 最终报告
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    stats = system.get_stats()
    
    print(f"\n数据集: {dataset_name}")
    print(f"知识库大小: {len(train_samples)}")
    print(f"测试样本数: {len(test_selected)}")
    print(f"RAG Top-K: {rag_top_k}")
    
    print(f"\n各轮准确率:")
    for r in all_results:
        improvement = r["bandit_accuracy"] - r["rag_accuracy"]
        print(f"  Round {r['round']}: RAG={r['rag_accuracy']:.1%}, Bandit={r['bandit_accuracy']:.1%}, Δ={improvement:+.1%}")
    
    # Bandit 学习效果
    if num_rounds > 1:
        r1_bandit = all_results[0]["bandit_accuracy"]
        r_final_bandit = all_results[-1]["bandit_accuracy"]
        learning_gain = r_final_bandit - r1_bandit
        print(f"\nBandit 学习增益: {learning_gain:+.1%}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset": dataset_name,
        "config": {
            "sample_size": sample_size,
            "rag_top_k": rag_top_k,
            "num_rounds": num_rounds
        },
        "stats": stats,
        "rounds": all_results
    }
    
    report_path = Path(__file__).parent.parent / "results" / f"real_dataset_{dataset_name.lower()}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_path}")
    
    return stats, all_results


def compare_datasets():
    """对比多个数据集"""
    
    print("\n" + "=" * 70)
    print("多数据集对比验证")
    print("=" * 70)
    
    datasets = ["BANKING77", "CLINC150"]
    comparison = []
    
    for ds in datasets:
        stats, results = run_real_dataset_validation(
            dataset_name=ds,
            sample_size=300,
            rag_top_k=10,
            num_rounds=2
        )
        comparison.append({
            "dataset": ds,
            "rag_accuracy": stats["rag_accuracy"],
            "bandit_accuracy": stats["bandit_accuracy"],
            "improvement": stats["bandit_accuracy"] - stats["rag_accuracy"]
        })
    
    # 对比报告
    print("\n" + "=" * 70)
    print("数据集对比结果")
    print("=" * 70)
    
    print(f"\n{'数据集':<15} {'RAG准确率':<12} {'Bandit准确率':<12} {'改进':<10}")
    for c in comparison:
        print(f"{c['dataset']:<15} {c['rag_accuracy']:.1%}       {c['bandit_accuracy']:.1%}       {c['improvement']:+.1%}")
    
    return comparison


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="真实数据集验证")
    parser.add_argument("--dataset", default="BANKING77", help="数据集名称")
    parser.add_argument("--sample-size", type=int, default=500, help="测试样本数")
    parser.add_argument("--rag-top-k", type=int, default=10, help="RAG Top-K")
    parser.add_argument("--num-rounds", type=int, default=3, help="测试轮数")
    parser.add_argument("--compare", action="store_true", help="对比多个数据集")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_datasets()
    else:
        run_real_dataset_validation(
            dataset_name=args.dataset,
            sample_size=args.sample_size,
            rag_top_k=args.rag_top_k,
            num_rounds=args.num_rounds
        )