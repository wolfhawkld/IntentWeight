#!/usr/bin/env python3
"""
Phase 2: 评估意图-簇关联 (优化版)

预先构建所有映射表，避免嵌套循环查找

输入:
  - results/knowledge_base_{dataset}.json
  - results/clusters_{dataset}.json
  - results/test_queries_{dataset}.json
  - results/test_embeddings_{dataset}.npy

输出:
  - results/evaluation_{dataset}.json
"""

import json
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_data(dataset: str):
    """加载所有数据"""
    with open(RESULTS_DIR / f"knowledge_base_{dataset}.json", "r") as f:
        knowledge_base = json.load(f)
    
    with open(RESULTS_DIR / f"clusters_{dataset}.json", "r") as f:
        clusters = json.load(f)
    
    with open(RESULTS_DIR / f"test_queries_{dataset}.json", "r") as f:
        test_queries = json.load(f)
    
    test_embeddings = np.load(RESULTS_DIR / f"test_embeddings_{dataset}.npy")
    train_embeddings = np.load(RESULTS_DIR / f"train_embeddings_{dataset}.npy")
    
    print(f"✓ 知识库: {len(knowledge_base['chunks'])} chunks")
    print(f"✓ 聚类: {clusters['metadata']['num_clusters']} 簇")
    print(f"✓ 测试查询: {len(test_queries['queries'])} 条")
    
    return knowledge_base, clusters, test_queries, test_embeddings, train_embeddings


def build_all_mappings(knowledge_base, clusters):
    """预先构建所有映射表"""
    # chunk_id -> embedding_index
    chunk_id_to_idx = {}
    for i, chunk in enumerate(knowledge_base["chunks"]):
        chunk_id_to_idx[chunk["chunk_id"]] = i
    
    # intent -> chunk_indices
    intent_to_chunk_indices = defaultdict(list)
    for i, chunk in enumerate(knowledge_base["chunks"]):
        intent_to_chunk_indices[chunk["intent"]].append(i)
    
    # cluster_id -> chunk_indices
    cluster_to_chunk_indices = {}
    for cluster in clusters["clusters"]:
        cluster_id = cluster["cluster_id"]
        indices = [chunk_id_to_idx[cid] for cid in cluster["chunk_ids"] if cid in chunk_id_to_idx]
        cluster_to_chunk_indices[cluster_id] = indices
    
    # intent -> cluster_ids (基于 dominant_intent)
    intent_to_clusters = defaultdict(list)
    for cluster in clusters["clusters"]:
        intent_to_clusters[cluster["dominant_intent"]].append(cluster["cluster_id"])
    
    # chunk_id -> cluster_id
    chunk_to_cluster = {}
    for cluster in clusters["clusters"]:
        for chunk_id in cluster["chunk_ids"]:
            chunk_to_cluster[chunk_id] = cluster["cluster_id"]
    
    return {
        "chunk_id_to_idx": chunk_id_to_idx,
        "intent_to_chunk_indices": dict(intent_to_chunk_indices),
        "cluster_to_chunk_indices": cluster_to_chunk_indices,
        "intent_to_clusters": dict(intent_to_clusters),
        "chunk_to_cluster": chunk_to_cluster
    }


def evaluate_cluster_mapping(test_queries, mappings, knowledge_base, top_n_clusters=3):
    """评估簇召回"""
    correct_hits = 0
    total = len(test_queries["queries"])
    
    for query in test_queries["queries"]:
        query_intent = query["intent"]
        predicted_clusters = mappings["intent_to_clusters"].get(query_intent, [])[:top_n_clusters]
        
        # 正确 chunks 所在的簇
        correct_indices = mappings["intent_to_chunk_indices"].get(query_intent, [])
        correct_clusters = set()
        for idx in correct_indices:
            chunk_id = knowledge_base["chunks"][idx]["chunk_id"]
            if chunk_id in mappings["chunk_to_cluster"]:
                correct_clusters.add(mappings["chunk_to_cluster"][chunk_id])
        
        if set(predicted_clusters) & correct_clusters:
            correct_hits += 1
    
    recall = correct_hits / total if total > 0 else 0
    avg_chunks = sum(len(mappings["intent_to_chunk_indices"].get(q["intent"], [])) 
                     for q in test_queries["queries"]) / total
    
    print(f"\n簇召回评估:")
    print(f"  簇召回率: {recall:.2%}")
    print(f"  平均每查询正确chunks: {avg_chunks:.1f}")
    
    return {"cluster_recall": recall, "avg_correct_chunks": avg_chunks}


def evaluate_retrieval(test_embeddings, train_embeddings, test_queries, 
                       knowledge_base, mappings, use_cluster_filter=False, top_n_clusters=3):
    """评估语义检索"""
    method = "cluster_filter" if use_cluster_filter else "pure_semantic"
    
    # 归一化 embeddings
    train_norm = train_embeddings / np.linalg.norm(train_embeddings, axis=1, keepdims=True)
    test_norm = test_embeddings / np.linalg.norm(test_embeddings, axis=1, keepdims=True)
    
    top_k_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    mrr_sum = 0.0
    total = len(test_queries["queries"])
    
    for i, query in enumerate(test_queries["queries"]):
        query_intent = query["intent"]
        query_emb = test_norm[i:i+1]
        
        # 确定搜索范围
        if use_cluster_filter:
            predicted_clusters = mappings["intent_to_clusters"].get(query_intent, [])[:top_n_clusters]
            if predicted_clusters:
                candidate_indices = []
                for cid in predicted_clusters:
                    candidate_indices.extend(mappings["cluster_to_chunk_indices"].get(cid, []))
                if not candidate_indices:
                    candidate_indices = list(range(len(train_embeddings)))
            else:
                candidate_indices = list(range(len(train_embeddings)))
        else:
            candidate_indices = list(range(len(train_embeddings)))
        
        # 计算相似度
        candidate_embeddings = train_norm[candidate_indices]
        similarities = np.dot(query_emb, candidate_embeddings.T)[0]
        
        # Top-K
        top_indices = np.argsort(similarities)[::-1][:10]
        retrieved_indices = [candidate_indices[idx] for idx in top_indices]
        
        # 正确答案
        correct_indices = set(mappings["intent_to_chunk_indices"].get(query_intent, []))
        
        # 计算命中
        for k in top_k_hits.keys():
            if any(idx in correct_indices for idx in retrieved_indices[:k]):
                top_k_hits[k] += 1
        
        # MRR
        for rank, idx in enumerate(retrieved_indices, 1):
            if idx in correct_indices:
                mrr_sum += 1.0 / rank
                break
    
    metrics = {
        "total_queries": total,
        **{f"top_{k}_accuracy": top_k_hits[k] / total for k in top_k_hits},
        "mrr": mrr_sum / total
    }
    
    print(f"\n语义检索评估 ({method}):")
    for k in [1, 3, 5, 10]:
        print(f"  Top-{k} 准确率: {metrics[f'top_{k}_accuracy']:.2%}")
    print(f"  MRR: {metrics['mrr']:.3f}")
    
    return {"method": method, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=["banking77", "clinc150"])
    parser.add_argument("--top_n_clusters", type=int, default=3)
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Phase 2 Step 3: 评估意图-簇关联 - {args.dataset}")
    print("=" * 60)
    
    # 加载
    knowledge_base, clusters, test_queries, test_embeddings, train_embeddings = load_data(args.dataset)
    
    # 预构建映射
    print("\n构建映射表...")
    mappings = build_all_mappings(knowledge_base, clusters)
    print(f"✓ chunk_id_to_idx: {len(mappings['chunk_id_to_idx'])}")
    print(f"✓ intent_to_chunk_indices: {len(mappings['intent_to_chunk_indices'])}")
    print(f"✓ cluster_to_chunk_indices: {len(mappings['cluster_to_chunk_indices'])}")
    
    # 评估
    cluster_results = evaluate_cluster_mapping(test_queries, mappings, knowledge_base, args.top_n_clusters)
    
    semantic_results = evaluate_retrieval(
        test_embeddings, train_embeddings, test_queries, 
        knowledge_base, mappings, use_cluster_filter=False
    )
    
    fusion_results = evaluate_retrieval(
        test_embeddings, train_embeddings, test_queries, 
        knowledge_base, mappings, use_cluster_filter=True, top_n_clusters=args.top_n_clusters
    )
    
    # 保存
    results = {
        "dataset": args.dataset,
        "cluster_mapping": {"metrics": cluster_results},
        "semantic_retrieval": semantic_results,
        "cluster_semantic_fusion": fusion_results
    }
    
    output_path = RESULTS_DIR / f"evaluation_{args.dataset}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 保存到: {output_path}")
    
    # 对比
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