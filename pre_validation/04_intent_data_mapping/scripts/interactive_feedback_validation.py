#!/usr/bin/env python3
"""
交互式反馈优化验证

您可以直接参与验证：
1. 输入查询
2. 查看检索结果
3. 给出反馈
4. 观察优化效果
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split
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
domains = [s["domain"] for s in samples]

# 划分
train_idx, test_idx = train_test_split(range(len(samples)), test_size=0.2, random_state=42)
train_idx, test_idx = list(train_idx), list(test_idx)

train_emb = embeddings[train_idx]
test_emb = embeddings[test_idx]
train_labels = [labels[i] for i in train_idx]
test_labels = [labels[i] for i in test_idx]
train_texts = [texts[i] for i in train_idx]
test_texts = [texts[i] for i in test_idx]
train_domains = [domains[i] for i in train_idx]

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

# 簇纯度
print("\n簇分析:")
for c, label_list in sorted(cluster_to_labels.items(), key=lambda x: -len(x[1]))[:5]:
    counter = Counter(label_list)
    purity = counter.most_common(1)[0][1] / len(label_list)
    dominant = counter.most_common(1)[0][0]
    print(f"  簇 #{c}: {len(label_list)} 样本, 主导意图: {dominant} ({purity:.0%})")

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
    return [candidates[i] for i in top_local], top_clusters

def interactive_mode():
    """交互式验证"""
    print("\n" + "=" * 80)
    print("交互式反馈验证")
    print("=" * 80)
    print("""
说明:
  - 输入查询编号 (1-516) 或输入文本
  - 系统返回 Top-3 结果
  - 您给出反馈: 1=正确, 0=错误
  - 观察优化效果
  
命令:
  - 输入数字: 选择测试集样本
  - 输入文本: 自定义查询
  - 'stats': 查看统计
  - 'test': 批量测试效果
  - 'quit': 退出
    """)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            elif user_input.lower() == 'stats':
                print(f"\n当前统计:")
                print(f"  反馈数: {len(feedback_history)}")
                pos = sum(1 for f in feedback_history if f['correct'])
                neg = len(feedback_history) - pos
                print(f"  正反馈: {pos}, 负反馈: {neg}")
                print(f"  簇权重范围: {min(cluster_weights.values()):.2f} - {max(cluster_weights.values()):.2f}")
                
                # 测试当前效果
                correct = 0
                for i, query_label in enumerate(test_labels):
                    query_emb = test_norm[i:i+1]
                    top_indices, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
                    if train_labels[top_indices[0]] == query_label:
                        correct += 1
                acc = correct / len(test_idx)
                print(f"  当前 Top-1 准确率: {acc:.1%}")
            
            elif user_input.lower() == 'test':
                # 批量测试
                print("\n批量测试中...")
                correct = 0
                for i, query_label in enumerate(test_labels):
                    query_emb = test_norm[i:i+1]
                    top_indices, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
                    if train_labels[top_indices[0]] == query_label:
                        correct += 1
                acc = correct / len(test_idx)
                print(f"当前 Top-1 准确率: {acc:.1%}")
            
            elif user_input.isdigit():
                idx = int(user_input)
                if 1 <= idx <= len(test_idx):
                    idx -= 1  # 转为0索引
                    query_text = test_texts[idx]
                    query_label = test_labels[idx]
                    query_emb = test_norm[idx:idx+1]
                    
                    print(f"\n查询: \"{query_text}\"")
                    print(f"真实意图: {query_label}")
                    
                    # 检索
                    top_indices, top_clusters = retrieve(query_emb, top_k=3, weights=cluster_weights)
                    
                    print(f"\n召回簇: {[c for c, _, _ in top_clusters]}")
                    print(f"Top-3 结果:")
                    for i, idx2 in enumerate(top_indices, 1):
                        print(f"  {i}. [{train_labels[idx2]}] \"{train_texts[idx2][:40]}...\"")
                    
                    # 获取反馈
                    fb = input("\n反馈 (1=正确, 0=错误, Enter=跳过): ").strip()
                    
                    if fb == '1':
                        # 正反馈
                        for c, _, _ in top_clusters:
                            cluster_weights[c] = min(1.5, cluster_weights[c] + 0.05)
                        feedback_history.append({
                            "query_idx": idx,
                            "correct": True,
                            "clusters": [c for c, _, _ in top_clusters]
                        })
                        print("✓ 正反馈已记录，簇权重已提升")
                        
                    elif fb == '0':
                        # 负反馈
                        for c, _, _ in top_clusters:
                            cluster_weights[c] = max(0.5, cluster_weights[c] - 0.05)
                        feedback_history.append({
                            "query_idx": idx,
                            "correct": False,
                            "clusters": [c for c, _, _ in top_clusters]
                        })
                        print("✓ 负反馈已记录，簇权重已降低")
                        
                        # 提示正确意图
                        print(f"正确意图应该是: {query_label}")
                else:
                    print(f"请输入 1-{len(test_idx)} 之间的数字")
            
            else:
                # 文本查询
                print(f"\n查询: \"{user_input}\"")
                # 这里需要用BGE生成embedding，暂时用测试集中最相似的
                query_text = user_input
                
                # 在测试集中找相似的
                test_sims = []
                for i, t in enumerate(test_texts):
                    if len(t) > 3:
                        # 简单字符重叠
                        overlap = len(set(query_text) & set(t))
                        test_sims.append((i, overlap))
                
                if test_sims:
                    best_idx = max(test_sims, key=lambda x: x[1])[0]
                    query_emb = test_norm[best_idx:best_idx+1]
                    
                    top_indices, top_clusters = retrieve(query_emb, top_k=3, weights=cluster_weights)
                    
                    print(f"\n召回簇: {[c for c, _, _ in top_clusters]}")
                    print(f"Top-3 结果:")
                    for i, idx2 in enumerate(top_indices, 1):
                        print(f"  {i}. [{train_labels[idx2]}] \"{train_texts[idx2][:40]}...\"")
                    
                    fb = input("\n反馈 (1=正确, 0=错误): ").strip()
                    if fb in ['1', '0']:
                        if fb == '1':
                            for c, _, _ in top_clusters:
                                cluster_weights[c] = min(1.5, cluster_weights[c] + 0.05)
                        else:
                            for c, _, _ in top_clusters:
                                cluster_weights[c] = max(0.5, cluster_weights[c] - 0.05)
                        print("✓ 反馈已记录")
        
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
        top_indices, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
    initial_acc = correct / len(test_idx)
    print(f"  初始 Top-1 准确率: {initial_acc:.1%}")
    
    # 启动交互模式
    interactive_mode()
    
    # 最终效果
    print("\n最终效果:")
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
    final_acc = correct / len(test_idx)
    print(f"  最终 Top-1 准确率: {final_acc:.1%}")
    print(f"  变化: {(final_acc - initial_acc) * 100:+.1f}%")
    print(f"  总反馈数: {len(feedback_history)}")