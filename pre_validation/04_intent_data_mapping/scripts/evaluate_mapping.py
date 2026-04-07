#!/usr/bin/env python3
"""
Phase 2: 评估意图-簇关联

验证问题意图能否正确映射到相关数据簇

输入:
  - results/knowledge_base_{dataset}.json
  - results/clusters_{dataset}.json
  - results/test_queries_{dataset}.json
  - results/test_embeddings_{dataset}.npy

输出:
  - results/evaluation_{dataset}.json
"""

import os
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# 项目根目录 (scripts -> 04 -> pre_validation -> IntentWeight)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_data(dataset: str) -> tuple:
    """
    加载所有数据
    
    Returns:
        (knowledge_base, clusters, test_queries, test_embeddings, train_embeddings)
    """
    # 知识库
    with open(RESULTS_DIR / f"knowledge_base_{dataset}.json", "r") as f:
        knowledge_base = json.load(f)
    
    # 聚类结果
    with open(RESULTS_DIR / f"clusters_{dataset}.json", "r") as f:
        clusters = json.load(f)
    
    # 测试查询
    with open(RESULTS_DIR / f"test_queries_{dataset}.json", "r") as f:
        test_queries = json.load(f)
    
    # Embeddings
    test_embeddings = np.load(RESULTS_DIR / f"test_embeddings_{dataset}.npy")
    train_embeddings = np.load(RESULTS_DIR / f"train_embeddings_{dataset}.npy")
    
    print(f"✓ 知识库: {len(knowledge_base['chunks'])} chunks")
    print(f"✓ 聚类: {clusters['metadata']['num_clusters']} 簇")
    print(f"✓ 测试查询: {len(test_queries['queries'])} 条")
    
    return knowledge_base, clusters, test_queries, test_embeddings, train_embeddings


def build_intent_to_clusters(clusters: Dict) -> Dict[str, List[int]]:
    """
    构建 intent → clusters 映射
    
    Returns:
        {intent: [cluster_id_1, cluster_id_2, ...]}
    """
    intent_to_clusters = defaultdict(list)
    
    for cluster in clusters["clusters"]:
        dominant_intent = cluster["dominant_intent"]
        intent_to_clusters[dominant_intent].append(cluster["cluster_id"])
    
    return dict(intent_to_clusters)


def build_chunk_to_cluster(clusters: Dict) -> Dict[str, int]:
    """
    构建 chunk_id → cluster_id 映射
    
    Returns:
        {chunk_id: cluster_id}
    """
    chunk_to_cluster = {}
    
    for cluster in clusters["clusters"]:
        cluster_id = cluster["cluster_id"]
        for chunk_id in cluster["chunk_ids"]:
            chunk_to_cluster[chunk_id] = cluster_id
    
    return chunk_to_cluster


def predict_cluster_by_intent(
    query_intent: str,
    intent_to_clusters: Dict[str, List[int]]
) -> List[int]:
    """
    根据查询 intent 预测相关簇
    
    Args:
        query_intent: 查询的 intent
        intent_to_clusters: intent → clusters 映射
    
    Returns:
        预测的簇列表
    """
    return intent_to_clusters.get(query_intent, [])


def find_correct_chunks(
    query_intent: str,
    knowledge_base: Dict
) -> List[str]:
    """
    找到查询正确答案对应的 chunks
    
    Args:
        query_intent: 查询的 intent
        knowledge_base: 知识库
    
    Returns:
        正确的 chunk_id 列表
    """
    correct_chunks = []
    for chunk in knowledge_base["chunks"]:
        if chunk["intent"] == query_intent:
            correct_chunks.append(chunk["chunk_id"])
    return correct_chunks


def evaluate_cluster_mapping(
    test_queries: Dict,
    knowledge_base: Dict,
    clusters: Dict,
    intent_to_clusters: Dict,
    chunk_to_cluster: Dict,
    top_n_clusters: int = 3
) -> Dict:
    """
    评估意图-簇映射效果
    
    Returns:
        评估结果
    """
    results = {
        "queries": [],
        "metrics": {}
    }
    
    total_queries = len(test_queries["queries"])
    correct_cluster_hits = 0
    total_correct_chunks = 0
    
    for query in test_queries["queries"]:
        query_id = query["query_id"]
        query_intent = query["intent"]
        
        # 预测簇
        predicted_clusters = predict_cluster_by_intent(query_intent, intent_to_clusters)[:top_n_clusters]
        
        # 正确 chunks
        correct_chunks = find_correct_chunks(query_intent, knowledge_base)
        total_correct_chunks += len(correct_chunks)
        
        # 正确簇（正确 chunks 所在的簇）
        correct_cluster_set = set()
        for chunk_id in correct_chunks:
            if chunk_id in chunk_to_cluster:
                correct_cluster_set.add(chunk_to_cluster[chunk_id])
        
        # 计算命中
        hit = bool(set(predicted_clusters) & correct_cluster_set)
        if hit:
            correct_cluster_hits += 1
        
        results["queries"].append({
            "query_id": query_id,
            "query_intent": query_intent,
            "predicted_clusters": predicted_clusters,
            "correct_clusters": list(correct_cluster_set),
            "correct_chunks": correct_chunks,
            "cluster_hit": hit
        })
    
    # 指标
    cluster_recall = correct_cluster_hits / total_queries if total_queries > 0 else 0
    
    results["metrics"] = {
        "total_queries": total_queries,
        "cluster_recall": cluster_recall,
        "avg_correct_chunks_per_query": total_correct_chunks / total_queries if total_queries > 0 else 0
    }
    
    print(f"\n簇召回评估:")
    print(f"  总查询数: {total_queries}")
    print(f"  簇召回率: {cluster_recall:.2%}")
    print(f"  平均每查询正确chunks: {results['metrics']['avg_correct_chunks_per_query']:.1f}")
    
    return results


def evaluate_semantic_retrieval(
    test_embeddings: np.ndarray,
    train_embeddings: np.ndarray,
    test_queries: Dict,
    knowledge_base: Dict,
    clusters: Dict,
    chunk_to_cluster: Dict,
    top_k: int = 10,
    use_cluster_filter: bool = False,
    intent_to_clusters: Dict = None,
    top_n_clusters: int = 3
) -> Dict:
    """
    评估语义检索效果
    
    Args:
        use_cluster_filter: 是否使用簇筛选
    
    Returns:
        评估结果
    """
    from sklearn.metrics.pairwise import cosine_similarity
    
    results = {
        "method": "cluster_filter" if use_cluster_filter else "pure_semantic",
        "queries": [],
        "metrics": {}
    }
    
    total_queries = len(test_queries["queries"])
    top_k_hits = {k: 0 for k in [1, 3, 5, 10]}
    mrr_sum = 0.0
    
    for i, query in enumerate(test_queries["queries"]):
        query_intent = query["intent"]
        query_emb = test_embeddings[i:i+1]
        
        # 确定搜索范围
        if use_cluster_filter and intent_to_clusters:
            # 簇筛选
            predicted_clusters = intent_to_clusters.get(query_intent, [])[:top_n_clusters]
            candidate_indices = []
            for cluster_id in predicted_clusters:
                for cluster in clusters["clusters"]:
                    if cluster["cluster_id"] == cluster_id:
                        for chunk_id in cluster["chunk_ids"]:
                            # 找到 chunk 在 train_embeddings 中的索引
                            for j, chunk in enumerate(knowledge_base["chunks"]):
                                if chunk["chunk_id"] == chunk_id:
                                    candidate_indices.append(j)
                                    break
            
            if not candidate_indices:
                # 没有候选，使用全部
                candidate_embeddings = train_embeddings
                candidate_indices = list(range(len(train_embeddings)))
            else:
                candidate_embeddings = train_embeddings[candidate_indices]
        else:
            # 无筛选，使用全部
            candidate_embeddings = train_embeddings
            candidate_indices = list(range(len(train_embeddings)))
        
        # 计算相似度
        similarities = cosine_similarity(query_emb, candidate_embeddings)[0]
        
        # Top-K
        top_k_indices = np.argsort(similarities)[::-1][:max(top_k_hits.keys())]
        
        # 正确答案
        correct_chunks = find_correct_chunks(query_intent, knowledge_base)
        
        # 计算 Top-K 命中
        retrieved_chunks = [knowledge_base["chunks"][candidate_indices[idx]]["chunk_id"] 
                           for idx in top_k_indices]
        
        for k in top_k_hits.keys():
            if any(chunk in retrieved_chunks[:k] for chunk in correct_chunks):
                top_k_hits[k] += 1
        
        # MRR
        for rank, chunk_id in enumerate(retrieved_chunks, 1):
            if chunk_id in correct_chunks:
                mrr_sum += 1.0 / rank
                break
        
        results["queries"].append({
            "query_id": query["query_id"],
            "retrieved_chunks": retrieved_chunks[:top_k],
            "correct_chunks": correct_chunks
        })
    
    # 指标
    results["metrics"] = {
        "total_queries": total_queries,
        **{f"top_{k}_accuracy": top_k_hits[k] / total_queries for k in top_k_hits},
        "mrr": mrr_sum / total_queries
    }
    
    print(f"\n语义检索评估 ({results['method']}):")
    for k in [1, 3, 5, 10]:
        print(f"  Top-{k} 准确率: {results['metrics'][f'top_{k}_accuracy']:.2%}")
    print(f"  MRR: {results['metrics']['mrr']:.3f}")
    
    return results


def save_evaluation_results(results: Dict, dataset: str):
    """保存评估结果"""
    output_path = RESULTS_DIR / f"evaluation_{dataset}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 评估结果保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="评估意图-簇关联")
    parser.add_argument("--dataset", type=str, required=True,
                        choices=["banking77", "clinc150"],
                        help="数据集名称")
    parser.add_argument("--top_n_clusters", type=int, default=3,
                        help="召回 Top-N 簇")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Phase 2 Step 3: 评估意图-簇关联 - {args.dataset}")
    print("=" * 60)
    
    # 加载数据
    knowledge_base, clusters, test_queries, test_embeddings, train_embeddings = \
        load_data(args.dataset)
    
    # 构建映射
    intent_to_clusters = build_intent_to_clusters(clusters)
    chunk_to_cluster = build_chunk_to_cluster(clusters)
    
    # 评估簇召回
    cluster_results = evaluate_cluster_mapping(
        test_queries, knowledge_base, clusters,
        intent_to_clusters, chunk_to_cluster,
        top_n_clusters=args.top_n_clusters
    )
    
    # 评估纯语义检索
    semantic_results = evaluate_semantic_retrieval(
        test_embeddings, train_embeddings,
        test_queries, knowledge_base, clusters, chunk_to_cluster,
        use_cluster_filter=False
    )
    
    # 评估簇筛选 + 语义检索
    fusion_results = evaluate_semantic_retrieval(
        test_embeddings, train_embeddings,
        test_queries, knowledge_base, clusters, chunk_to_cluster,
        use_cluster_filter=True,
        intent_to_clusters=intent_to_clusters,
        top_n_clusters=args.top_n_clusters
    )
    
    # 汇总结果
    results = {
        "dataset": args.dataset,
        "cluster_mapping": cluster_results,
        "semantic_retrieval": semantic_results,
        "cluster_semantic_fusion": fusion_results
    }
    
    # 保存
    save_evaluation_results(results, args.dataset)
    
    # 打印对比
    print("\n" + "=" * 60)
    print("对比结果:")
    print("=" * 60)
    print(f"{'方法':<25} {'Top-1':>10} {'Top-5':>10} {'MRR':>10}")
    print("-" * 60)
    print(f"{'纯语义检索':<25} {semantic_results['metrics']['top_1_accuracy']:>10.1%} "
          f"{semantic_results['metrics']['top_5_accuracy']:>10.1%} "
          f"{semantic_results['metrics']['mrr']:>10.3f}")
    print(f"{'簇筛选 + 语义检索':<25} {fusion_results['metrics']['top_1_accuracy']:>10.1%} "
          f"{fusion_results['metrics']['top_5_accuracy']:>10.1%} "
          f"{fusion_results['metrics']['mrr']:>10.3f}")
    
    print("\n✓ 评估完成!")


if __name__ == "__main__":
    main()