#!/usr/bin/env python3
"""
交互式反馈验证 v2 - 加入语义相似度

反馈标准:
  1 = Top-1 意图匹配 + 内容语义相似 (>0.7)
  0 = 其他情况
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
DATA_DIR = PROJECT_ROOT / "data" / "smp2019"

# 加载数据
print("加载数据...")
embeddings = np.load(EMBEDDINGS_DIR / "smp2019_embeddings.npy")
with open(DATA_DIR / "smp2019_processed.json", "r", encoding="utf-8") as f:
    samples = json.load(f)

texts = [s["text"] for s in samples]
labels = [s["intent"] for s in samples]

# 划分
train_idx, test_idx = train_test_split(range(len(samples)), test_size=0.2, random_state=42)
train_idx, test_idx = list(train_idx), list(test_idx)

train_emb = embeddings[train_idx]
test_emb = embeddings[test_idx]
train_labels = [labels[i] for i in train_idx]
test_labels = [labels[i] for i in test_idx]
train_texts = [texts[i] for i in train_idx]
test_texts = [texts[i] for i in test_idx]

print(f"✓ Train: {len(train_idx)}, Test: {len(test_idx)}")

# 聚类
print("聚类中...")
clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=3, metric='euclidean')
train_clusters = clusterer.fit_predict(train_emb)

# 建立映射
cluster_to_indices = defaultdict(list)
cluster_to_labels = defaultdict(list)
for i, (c, label) in enumerate(zip(train_clusters, train_labels)):
    if c != -1:
        cluster_to_indices[c].append(i)
        cluster_to_labels[c].append(label)

# 簇中心
cluster_centers = {}
for c, indices in cluster_to_indices.items():
    center = np.mean(train_emb[indices], axis=0)
    cluster_centers[c] = center / np.linalg.norm(center)

# 初始化
train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

cluster_weights = {c: 1.0 for c in cluster_centers.keys()}
feedback_history = []

def retrieve(query_emb, top_k=5, weights=None):
    """簇召回 + 簇内检索"""
    cluster_sims = []
    for c, center in cluster_centers.items():
        sim = np.dot(query_emb, center.reshape(1, -1).T)[0][0]
        w = weights.get(c, 1.0) if weights else 1.0
        score = sim * w
        cluster_sims.append((c, score, sim))
    
    top_clusters = sorted(cluster_sims, key=lambda x: -x[1])[:3]
    candidates = []
    for c, _, _ in top_clusters:
        candidates.extend(cluster_to_indices[c])
    
    if not candidates:
        candidates = list(range(len(train_idx)))
    
    candidate_emb = train_norm[candidates]
    sims = np.dot(query_emb, candidate_emb.T)[0]
    top_local = np.argsort(sims)[::-1][:top_k]
    return [candidates[i] for i in top_local], top_clusters, sims[top_local]

def interactive_mode():
    """交互式验证"""
    print("\n" + "=" * 80)
    print("交互式反馈验证 v2 - 语义相似度增强")
    print("=" * 80)
    print("""
反馈标准 (更严格):
─────────────────────────────
  1 = Top-1 意图匹配 AND 语义相似度 > 0.7
  0 = 其他所有情况
      - Top-1 意图不匹配
      - 意图匹配但语义不相似
      - Top-1 错误

显示内容:
─────────────────────────────
  - 意图匹配: ✓ 或 ✗
  - 语义相似度: 0.XX
  - 判断建议: 基于上述两项给出建议

命令:
  - 输入数字: 选择测试样本
  - 'stats': 查看统计
  - 'test': 批量测试
  - 'quit': 退出
    """)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            elif user_input.lower() == 'stats':
                print(f"\n{'='*60}")
                print("当前统计")
                print("="*60)
                print(f"  反馈数: {len(feedback_history)}")
                pos = sum(1 for f in feedback_history if f['correct'])
                neg = len(feedback_history) - pos
                print(f"  正反馈: {pos}, 负反馈: {neg} (正确率 {pos/(pos+neg)*100:.1f}%)")
                print(f"  簇权重范围: {min(cluster_weights.values()):.2f} - {max(cluster_weights.values()):.2f}")
                
                # 统计各簇反馈
                cluster_fb = defaultdict(lambda: {"pos": 0, "neg": 0})
                for f in feedback_history:
                    for c in f.get("clusters", []):
                        if f["correct"]:
                            cluster_fb[c]["pos"] += 1
                        else:
                            cluster_fb[c]["neg"] += 1
                
                print(f"\n  各簇反馈分布:")
                for c in sorted(cluster_fb.keys()):
                    fb = cluster_fb[c]
                    total = fb["pos"] + fb["neg"]
                    if total > 0:
                        rate = fb["pos"] / total
                        print(f"    簇 #{c}: 正反馈 {fb['pos']}, 负反馈 {fb['neg']} (正确率 {rate:.0%})")
                
                # 测试当前效果
                correct = 0
                for i, query_label in enumerate(test_labels):
                    query_emb = test_norm[i:i+1]
                    top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
                    if train_labels[top_indices[0]] == query_label:
                        correct += 1
                acc = correct / len(test_idx)
                print(f"\n  当前 Top-1 准确率: {acc:.1%}")
                print(f"  初始准确率: 73.1%")
                print(f"  变化: {(acc - 0.731) * 100:+.1f}%")
            
            elif user_input.lower() == 'test':
                print("\n批量测试中...")
                correct = 0
                for i, query_label in enumerate(test_labels):
                    query_emb = test_norm[i:i+1]
                    top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
                    if train_labels[top_indices[0]] == query_label:
                        correct += 1
                acc = correct / len(test_idx)
                print(f"当前 Top-1 准确率: {acc:.1%}")
                print(f"变化: {(acc - 0.731) * 100:+.1f}%")
            
            elif user_input.isdigit():
                idx = int(user_input)
                if 1 <= idx <= len(test_idx):
                    idx -= 1
                    query_text = test_texts[idx]
                    query_label = test_labels[idx]
                    query_emb = test_norm[idx:idx+1]
                    
                    print(f"\n{'='*60}")
                    print(f"查询 #{idx+1}")
                    print("="*60)
                    print(f"问题: \"{query_text}\"")
                    print(f"真实意图: {query_label}")
                    
                    # 检索
                    top_indices, top_clusters, top_sims = retrieve(query_emb, top_k=3, weights=cluster_weights)
                    
                    print(f"\n召回簇: {[c for c, _, _ in top_clusters]}")
                    print(f"\nTop-3 结果:")
                    
                    # 判断信息
                    top1_intent = train_labels[top_indices[0]]
                    top1_semantic = top_sims[0]
                    intent_match = (top1_intent == query_label)
                    
                    for i, (idx2, sim) in enumerate(zip(top_indices, top_sims), 1):
                        intent = train_labels[idx2]
                        match_mark = "✓" if intent == query_label else "✗"
                        print(f"\n  {i}. [{intent}] {match_mark}")
                        print(f"     语义相似度: {sim:.2f}")
                        print(f"     \"{train_texts[idx2]}\"")
                    
                    # 自动判断建议
                    print(f"\n{'='*60}")
                    print("判断建议")
                    print("="*60)
                    print(f"  Top-1 意图匹配: {'✓ 是' if intent_match else '✗ 否'}")
                    print(f"  Top-1 语义相似度: {top1_semantic:.2f} {'(>0.7 合格)' if top1_semantic > 0.7 else '(<0.7 不合格)'}")
                    
                    if intent_match and top1_semantic > 0.7:
                        print(f"\n  → 建议反馈: 1 (两项都合格)")
                    else:
                        reasons = []
                        if not intent_match:
                            reasons.append("意图不匹配")
                        if top1_semantic <= 0.7:
                            reasons.append("语义相似度过低")
                        print(f"\n  → 建议反馈: 0 ({', '.join(reasons)})")
                    
                    # 获取反馈
                    fb = input("\n你的反馈 (1/0): ").strip()
                    
                    if fb == '1':
                        for c, _, _ in top_clusters:
                            cluster_weights[c] = min(1.5, cluster_weights[c] + 0.05)
                        feedback_history.append({
                            "query_idx": idx,
                            "correct": True,
                            "clusters": [c for c, _, _ in top_clusters],
                            "intent_match": intent_match,
                            "semantic_sim": float(top1_semantic)
                        })
                        print("✓ 正反馈已记录，簇权重提升")
                        
                    elif fb == '0':
                        for c, _, _ in top_clusters:
                            cluster_weights[c] = max(0.5, cluster_weights[c] - 0.1)  # 负反馈惩罚更大
                        feedback_history.append({
                            "query_idx": idx,
                            "correct": False,
                            "clusters": [c for c, _, _ in top_clusters],
                            "intent_match": intent_match,
                            "semantic_sim": float(top1_semantic)
                        })
                        print("✓ 负反馈已记录，簇权重降低")
                else:
                    print(f"请输入 1-{len(test_idx)} 之间的数字")
        
        except KeyboardInterrupt:
            print("\n\n退出...")
            break
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    # 初始效果
    print("\n初始效果:")
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
    initial_acc = correct / len(test_idx)
    print(f"  初始 Top-1 准确率: {initial_acc:.1%}")
    
    # 启动交互模式
    interactive_mode()
    
    # 最终效果
    print("\n" + "=" * 80)
    print("最终统计")
    print("=" * 80)
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
    final_acc = correct / len(test_idx)
    
    pos = sum(1 for f in feedback_history if f['correct'])
    neg = len(feedback_history) - pos
    
    print(f"  总反馈数: {len(feedback_history)}")
    print(f"  正反馈: {pos}, 负反馈: {neg}")
    print(f"  初始 Top-1: {initial_acc:.1%}")
    print(f"  最终 Top-1: {final_acc:.1%}")
    print(f"  变化: {(final_acc - initial_acc) * 100:+.1f}%")