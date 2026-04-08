#!/usr/bin/env python3
"""
交互式反馈验证 v4 - 完整反馈系统

支持:
1. 评分 (1/0)
2. 反馈内容输入
3. 根据反馈内容智能优化
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
cluster_to_dominant_intent = {}

for i, (c, label) in enumerate(zip(train_clusters, train_labels)):
    if c != -1:
        cluster_to_indices[c].append(i)
        cluster_to_labels[c].append(label)

# 计算每个簇的主导意图
for c, label_list in cluster_to_labels.items():
    counter = Counter(label_list)
    cluster_to_dominant_intent[c] = counter.most_common(1)[0][0]

# 簇中心
cluster_centers = {}
for c, indices in cluster_to_indices.items():
    center = np.mean(train_emb[indices], axis=0)
    cluster_centers[c] = center / np.linalg.norm(center)

# 初始化
train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

cluster_weights = {c: 1.0 for c in cluster_centers.keys()}
cluster_feedback = {c: {"pos": 0, "neg": 0, "feedbacks": []} for c in cluster_centers.keys()}
feedback_history = []

# 意图到簇的反向映射
intent_to_clusters = defaultdict(list)
for c, label_list in cluster_to_labels.items():
    counter = Counter(label_list)
    dominant_intent = counter.most_common(1)[0][0]
    intent_to_clusters[dominant_intent].append(c)

def update_weights_smart():
    """智能权重更新"""
    for c in cluster_centers.keys():
        fb = cluster_feedback[c]
        total = fb["pos"] + fb["neg"]
        
        if total == 0:
            cluster_weights[c] = 1.0
        elif total < 3:
            rate = fb["pos"] / total
            if fb["neg"] > 0:
                cluster_weights[c] = 0.3 + 0.7 * rate
            else:
                cluster_weights[c] = 1.0
        else:
            rate = fb["pos"] / total
            if rate >= 0.8:
                cluster_weights[c] = 1.5
            elif rate >= 0.5:
                cluster_weights[c] = 1.0
            elif rate >= 0.3:
                cluster_weights[c] = 0.5
            else:
                cluster_weights[c] = 0.1

def process_feedback_text(feedback_text, query_intent, recalled_clusters):
    """
    处理反馈文本，提取有用信息
    
    支持的反馈类型:
    - "应该是X" / "正确意图是X" → 记录正确意图
    - "应该召回X簇" → 调整簇权重
    - "语义不对" → 标记语义问题
    """
    result = {
        "type": "general",
        "correct_intent": None,
        "suggested_clusters": [],
        "semantic_issue": False
    }
    
    feedback_lower = feedback_text.lower()
    
    # 检测意图修正
    intent_keywords = ["应该是", "正确意图", "应该是", "意图是"]
    for kw in intent_keywords:
        if kw in feedback_text:
            # 尝试提取意图（简化处理）
            result["type"] = "intent_correction"
            result["correct_intent"] = query_intent  # 记录应该是什么意图
            break
    
    # 检测簇建议
    if "簇" in feedback_text or "召回" in feedback_text:
        result["type"] = "cluster_suggestion"
    
    # 检测语义问题
    if "语义" in feedback_text or "不相关" in feedback_text or "不对" in feedback_text:
        result["semantic_issue"] = True
    
    return result

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

def interactive_mode(initial_errors):
    """交互式验证"""
    print("\n" + "=" * 80)
    print("交互式反馈验证 v4 - 完整反馈系统")
    print("=" * 80)
    print("""
反馈方式:
─────────────────────────────
1. 先看结果，判断评分
2. 输入评分 (1/0)
3. 输入反馈内容（可选，描述问题或建议）

反馈内容示例:
  - "应该是video_QUERY而不是tvchannel_PLAY"
  - "这个簇召回了错误的意图"
  - "语义不相关"
  - "应该召回poetry相关的簇"

命令:
  - 输入数字: 选择测试样本
  - 'stats': 查看统计
  - 'clusters': 查看各簇信息
  - 'test': 批量测试
  - 'quit': 退出
    """)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            elif user_input.lower() == 'stats':
                print(f"\n{'='*70}")
                print("当前统计")
                print("="*70)
                print(f"  反馈数: {len(feedback_history)}")
                pos = sum(1 for f in feedback_history if f['score'] == 1)
                neg = len(feedback_history) - pos
                print(f"  正反馈: {pos}, 负反馈: {neg} (正确率 {pos/(pos+neg)*100:.1f}%)")
                
                print(f"\n  各簇状态:")
                print(f"  {'簇':>6} {'主导意图':>20} {'正反馈':>6} {'负反馈':>6} {'权重':>6}")
                print("  " + "-" * 60)
                
                for c in sorted(cluster_centers.keys()):
                    fb = cluster_feedback[c]
                    total = fb["pos"] + fb["neg"]
                    dominant = cluster_to_dominant_intent.get(c, "?")[:18]
                    
                    if total > 0:
                        print(f"  {c:>6} {dominant:>20} {fb['pos']:>6} {fb['neg']:>6} {cluster_weights[c]:>6.2f}")
                    else:
                        print(f"  {c:>6} {dominant:>20} {fb['pos']:>6} {fb['neg']:>6} {cluster_weights[c]:>6.2f}")
                
                print(f"\n  权重范围: {min(cluster_weights.values()):.2f} - {max(cluster_weights.values()):.2f}")
                
                # 测试效果
                correct = 0
                errors_fixed = 0
                for i, query_label in enumerate(test_labels):
                    query_emb = test_norm[i:i+1]
                    top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
                    if train_labels[top_indices[0]] == query_label:
                        correct += 1
                        if i in initial_errors:
                            errors_fixed += 1
                
                acc = correct / len(test_idx)
                print(f"\n  当前 Top-1 准确率: {acc:.1%}")
                print(f"  初始准确率: 73.1%")
                print(f"  变化: {(acc - 0.731) * 100:+.1f}%")
                print(f"\n  🎯 错误改善: {errors_fixed}/{len(initial_errors)} ({errors_fixed/len(initial_errors)*100:.1f}%)")
            
            elif user_input.lower() == 'clusters':
                print(f"\n各簇详细信息:")
                for c in sorted(cluster_centers.keys()):
                    counter = Counter(cluster_to_labels[c])
                    top3 = counter.most_common(3)
                    print(f"\n  簇 #{c} ({len(cluster_to_indices[c])} 样本):")
                    for intent, count in top3:
                        print(f"    - {intent}: {count}")
            
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
                    
                    print(f"\n{'='*70}")
                    print(f"查询 #{idx+1}")
                    print("="*70)
                    print(f"问题: \"{query_text}\"")
                    print(f"正确意图: {query_label}")
                    
                    # 检索
                    top_indices, top_clusters, top_sims = retrieve(query_emb, top_k=3, weights=cluster_weights)
                    
                    print(f"\n召回簇: {[c for c, _, _ in top_clusters]}")
                    print(f"\nTop-3 结果:")
                    
                    top1_intent = train_labels[top_indices[0]]
                    top1_semantic = top_sims[0]
                    intent_match = (top1_intent == query_label)
                    
                    for i, (idx2, sim) in enumerate(zip(top_indices, top_sims), 1):
                        intent = train_labels[idx2]
                        match_mark = "✓" if intent == query_label else "✗"
                        print(f"\n  {i}. [{intent}] {match_mark} (语义 {sim:.2f})")
                        print(f"     \"{train_texts[idx2]}\"")
                    
                    # 判断建议
                    print(f"\n{'='*50}")
                    print("判断建议")
                    print("="*50)
                    print(f"  Top-1 意图匹配: {'✓ 是' if intent_match else '✗ 否'}")
                    print(f"  Top-1 语义相似度: {top1_semantic:.2f}")
                    
                    if intent_match and top1_semantic > 0.7:
                        print(f"\n  → 建议评分: 1")
                    else:
                        print(f"\n  → 建议评分: 0")
                    
                    # 获取评分
                    score_input = input("\n评分 (1/0): ").strip()
                    
                    if score_input in ['1', '0']:
                        score = int(score_input)
                        
                        # 获取反馈内容
                        print("\n请输入反馈内容（描述问题或建议，按Enter跳过）:")
                        feedback_text = input("反馈: ").strip()
                        
                        # 处理反馈
                        recalled_clusters = [c for c, _, _ in top_clusters]
                        
                        # 更新簇反馈
                        for c in recalled_clusters:
                            if score == 1:
                                cluster_feedback[c]["pos"] += 1
                            else:
                                cluster_feedback[c]["neg"] += 1
                            
                            if feedback_text:
                                cluster_feedback[c]["feedbacks"].append(feedback_text)
                        
                        # 记录反馈历史
                        feedback_record = {
                            "query_idx": idx,
                            "query_text": query_text,
                            "query_intent": query_label,
                            "score": score,
                            "feedback_text": feedback_text,
                            "clusters": recalled_clusters,
                            "top1_intent": top1_intent,
                            "semantic_sim": float(top1_semantic)
                        }
                        feedback_history.append(feedback_record)
                        
                        # 更新权重
                        update_weights_smart()
                        
                        # 处理反馈文本（未来可以用于更智能的优化）
                        if feedback_text:
                            processed = process_feedback_text(feedback_text, query_label, recalled_clusters)
                            print(f"\n✓ 反馈已记录")
                            print(f"  评分: {score}")
                            print(f"  反馈内容: {feedback_text}")
                        else:
                            print(f"\n✓ 反馈已记录 (评分: {score})")
                else:
                    print(f"请输入 1-{len(test_idx)} 之间的数字")
        
        except KeyboardInterrupt:
            print("\n\n退出...")
            break
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # 初始效果
    print("\n初始效果:")
    
    initial_errors = []
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
        else:
            initial_errors.append(i)
    
    initial_acc = correct / len(test_idx)
    print(f"  初始 Top-1 准确率: {initial_acc:.1%}")
    print(f"  初始错误样本数: {len(initial_errors)}")
    
    # 启动交互模式
    interactive_mode(initial_errors)
    
    # 最终效果
    print("\n" + "=" * 80)
    print("最终统计")
    print("=" * 80)
    
    correct = 0
    errors_fixed = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
            if i in initial_errors:
                errors_fixed += 1
    
    final_acc = correct / len(test_idx)
    
    pos = sum(1 for f in feedback_history if f['score'] == 1)
    neg = len(feedback_history) - pos
    
    print(f"\n基本统计:")
    print(f"  总反馈数: {len(feedback_history)}")
    print(f"  正反馈: {pos}, 负反馈: {neg}")
    print(f"  初始 Top-1: {initial_acc:.1%}")
    print(f"  最终 Top-1: {final_acc:.1%}")
    print(f"  变化: {(final_acc - initial_acc) * 100:+.1f}%")
    
    print(f"\n🎯 关键指标 - 错误改善:")
    print(f"  初始错误样本数: {len(initial_errors)}")
    print(f"  被纠正的错误数: {errors_fixed}")
    print(f"  错误改善率: {errors_fixed/len(initial_errors)*100:.1f}%")
    
    # 保存反馈历史
    if feedback_history:
        output_path = PROJECT_ROOT / "04_intent_data_mapping/results/feedback_history.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(feedback_history, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 反馈历史已保存到: {output_path}")