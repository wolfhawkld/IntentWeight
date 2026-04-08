#!/usr/bin/env python3
"""
交互式反馈验证 v5 - 融合智能反馈系统

支持:
1. 评分 (1/0)
2. 自然语言建议输入 (如 "这是APP选取相关的问题")
3. 双层语义匹配 (意图标签 + 簇摘要)
4. 智能权重优化
5. 迭代反馈直到正反馈
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan
import re

# ========== 配置 ==========

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
DATA_DIR = PROJECT_ROOT / "data" / "smp2019"

# ========== 数据加载 ==========

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

# ========== 聚类 ==========

print("聚类中...")
clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=3, metric='euclidean')
train_clusters = clusterer.fit_predict(train_emb)

# ========== 基础映射构建 ==========

cluster_to_indices = defaultdict(list)
cluster_to_labels = defaultdict(list)
cluster_to_dominant_intent = {}

for i, (c, label) in enumerate(zip(train_clusters, train_labels)):
    if c != -1:
        cluster_to_indices[c].append(i)
        cluster_to_labels[c].append(label)

for c, label_list in cluster_to_labels.items():
    counter = Counter(label_list)
    cluster_to_dominant_intent[c] = counter.most_common(1)[0][0]

# 簇中心
cluster_centers = {}
for c, indices in cluster_to_indices.items():
    center = np.mean(train_emb[indices], axis=0)
    cluster_centers[c] = center / np.linalg.norm(center)

# 意图到簇的反向映射
intent_to_clusters = defaultdict(list)
for c, label_list in cluster_to_labels.items():
    counter = Counter(label_list)
    dominant_intent = counter.most_common(1)[0][0]
    intent_to_clusters[dominant_intent].append(c)

# ========== 新增: 意图标签 Embedding (方案A) ==========

print("构建意图标签 embedding...")
all_intents = list(set(labels))
intent_embeddings = {}

# 使用句子作为意图语义表示
intent_sample_texts = defaultdict(list)
for text, label in zip(train_texts, train_labels):
    intent_sample_texts[label].append(text)

# 每个意图用Top-3样本的平均embedding作为意图embedding
for intent in all_intents:
    samples_for_intent = intent_sample_texts[intent][:3]
    if samples_for_intent:
        # 找到这些样本的embedding
        indices_for_intent = [i for i, l in enumerate(train_labels) if l == intent][:3]
        if indices_for_intent:
            intent_emb = np.mean(train_emb[indices_for_intent], axis=0)
            intent_embeddings[intent] = intent_emb / np.linalg.norm(intent_emb)

print(f"✓ 意图标签数: {len(intent_embeddings)}")

# ========== 新增: 簇语义摘要 (方案B) ==========

print("构建簇语义摘要...")
cluster_semantic_summary = {}

for c in cluster_to_indices.keys():
    indices = cluster_to_indices[c]
    label_list = cluster_to_labels[c]
    counter = Counter(label_list)

    # 找每个簇最代表性的3个样本 (语义最接近簇中心的)
    cluster_center = cluster_centers[c]
    sample_sims = []
    for idx in indices:
        sim = np.dot(train_emb[idx] / np.linalg.norm(train_emb[idx]), cluster_center)
        sample_sims.append((idx, sim))

    top3_indices = sorted(sample_sims, key=lambda x: -x[1])[:3]
    representative_texts = [train_texts[idx] for idx, _ in top3_indices]

    # 簇摘要embedding (代表样本平均)
    summary_emb = np.mean([train_emb[idx] for idx, _ in top3_indices], axis=0)
    summary_emb = summary_emb / np.linalg.norm(summary_emb)

    cluster_semantic_summary[c] = {
        "dominant_intent": cluster_to_dominant_intent[c],
        "intent_distribution": counter.most_common(3),
        "representative_texts": representative_texts,
        "summary_embedding": summary_emb,
        "sample_count": len(indices)
    }

print(f"✓ 簇语义摘要数: {len(cluster_semantic_summary)}")

# ========== 初始化 ==========

train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

cluster_weights = {c: 1.0 for c in cluster_centers.keys()}
cluster_feedback = {c: {"pos": 0, "neg": 0, "feedbacks": []} for c in cluster_centers.keys()}
feedback_history = []

# 新增: 查询-正确映射表 (反馈驱动的动态学习)
query_correct_mapping = []

# ========== 持久化加载 ==========

PERSISTENCE_FILE = PROJECT_ROOT / "04_intent_data_mapping/results/feedback_v5_persistence.json"

def load_persistence():
    """加载之前保存的权重和映射"""
    if not PERSISTENCE_FILE.exists():
        print("✓ 无历史记录，首次运行")
        return False

    try:
        with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 加载权重
        if "cluster_weights" in data:
            for c, w in data["cluster_weights"].items():
                if int(c) in cluster_weights:
                    cluster_weights[int(c)] = w
            print(f"✓ 加载权重: {len(data['cluster_weights'])} 个簇")

        # 加载反馈计数
        if "cluster_feedback" in data:
            for c, fb in data["cluster_feedback"].items():
                if int(c) in cluster_feedback:
                    cluster_feedback[int(c)]["pos"] = fb.get("pos", 0)
                    cluster_feedback[int(c)]["neg"] = fb.get("neg", 0)
            print(f"✓ 加载反馈计数: {len(data['cluster_feedback'])} 个簇")

        # 加载查询映射
        if "query_correct_mapping" in data:
            query_correct_mapping.extend(data["query_correct_mapping"])
            print(f"✓ 加载查询映射: {len(data['query_correct_mapping'])} 条")

        # 加载反馈历史
        if "feedback_history" in data:
            feedback_history.extend(data["feedback_history"])
            print(f"✓ 加载反馈历史: {len(data['feedback_history'])} 条")

        return True

    except Exception as e:
        print(f"⚠ 加载失败: {e}")
        return False

def save_persistence():
    """保存权重和映射"""
    # 转换 numpy 类型为 Python 基本类型
    def convert_to_native(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(v) for v in obj]
        return obj

    # 清理无效 Unicode 字符
    def clean_unicode(obj):
        if isinstance(obj, str):
            # 移除 surrogate 字符和其他无效字符
            return obj.encode('utf-8', errors='replace').decode('utf-8')
        elif isinstance(obj, dict):
            return {k: clean_unicode(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_unicode(v) for v in obj]
        return obj

    data = {
        "cluster_weights": {str(c): float(w) for c, w in cluster_weights.items()},
        "cluster_feedback": {
            str(c): {"pos": int(fb["pos"]), "neg": int(fb["neg"])}
            for c, fb in cluster_feedback.items()
        },
        "query_correct_mapping": clean_unicode(convert_to_native(query_correct_mapping)),
        "feedback_history": clean_unicode(convert_to_native(feedback_history)),
    }

    with open(PERSISTENCE_FILE, "w", encoding="utf-8", errors='replace') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 持久化保存: {PERSISTENCE_FILE}")

# ========== 双层语义匹配函数 ==========

def match_intent_from_description(description, top_k=3):
    """
    方案A: 从用户描述匹配意图标签

    Args:
        description: 用户自然语言描述 (如 "这是APP选取相关的问题")
        top_k: 返回最相似的top_k个意图

    Returns:
        list of (intent, similarity_score)
    """
    # 用户描述的embedding (使用已有train_emb的平均作为近似)
    # 简化方案: 用关键词匹配 + 意图标签embedding相似度

    # 方法: 用户描述与意图代表样本embedding匹配
    desc_lower = description.lower()

    # 关键词启发式匹配 (扩展版)
    keyword_intent_map = {
        "app": ["app_SELECT", "app_QUERY", "app_PLAY", "app_OPEN"],
        "选取": ["app_SELECT", "radio_SELECT", "tvchannel_SELECT"],
        "选择": ["app_SELECT", "radio_SELECT", "tvchannel_SELECT"],
        "播放": ["music_PLAY", "video_PLAY", "radio_PLAY"],
        "音乐": ["music_PLAY", "music_QUERY"],
        "歌曲": ["music_PLAY", "music_QUERY", "lyric_QUERY"],
        "歌词": ["lyric_QUERY"],
        "视频": ["video_PLAY", "video_QUERY"],
        "查询": ["_QUERY"],
        "操作": ["_PLAY", "_SELECT", "_OPEN"],
        # 新增: 诗歌/诗词相关
        "诗歌": ["poetry_QUERY"],
        "诗": ["poetry_QUERY"],
        "诗词": ["poetry_QUERY"],
        "古诗": ["poetry_QUERY"],
        "接龙": ["poetry_QUERY"],
        "诗句": ["poetry_QUERY"],
        # 新增: 猜谜相关
        "猜谜": ["riddle_QUERY"],
        "谜语": ["riddle_QUERY"],
        "谜": ["riddle_QUERY"],
        # 新增: 天气相关
        "天气": ["weather_QUERY"],
        # 新增: 日期/时间相关
        "日期": ["date_QUERY", "time_QUERY"],
        "时间": ["time_QUERY"],
        "几点": ["time_QUERY"],
        # 新增: 计算/翻译等
        "计算": ["calculate_QUERY"],
        "翻译": ["translation_QUERY"],
        # 新增: 电台/电视
        "电台": ["radio_PLAY", "radio_QUERY"],
        "电视": ["tvchannel_PLAY", "tvchannel_QUERY"],
        "频道": ["tvchannel_PLAY", "tvchannel_QUERY"],
    }

    # 关键词匹配得分
    keyword_scores = defaultdict(float)
    for keyword, related_intents in keyword_intent_map.items():
        if keyword in desc_lower:
            for intent_pattern in related_intents:
                for intent in all_intents:
                    if intent_pattern in intent or intent.endswith(intent_pattern):
                        keyword_scores[intent] += 1.0

    # 语义相似度匹配 (用描述中的关键词组合embedding)
    # 简化: 找train中包含关键词的样本，取平均embedding
    keyword_samples = []
    for keyword in keyword_intent_map.keys():
        if keyword in desc_lower:
            for text, idx in zip(train_texts, range(len(train_texts))):
                if keyword in text.lower():
                    keyword_samples.append(idx)

    if keyword_samples:
        desc_emb = np.mean(train_emb[keyword_samples[:10]], axis=0)
        desc_emb = desc_emb / np.linalg.norm(desc_emb)

        # 与各意图embedding匹配
        semantic_scores = {}
        for intent, intent_emb in intent_embeddings.items():
            sim = np.dot(desc_emb, intent_emb)
            semantic_scores[intent] = sim
    else:
        semantic_scores = {intent: 0.5 for intent in all_intents}

    # 融合关键词匹配和语义匹配
    final_scores = {}
    for intent in all_intents:
        kw_score = keyword_scores.get(intent, 0)
        sem_score = semantic_scores.get(intent, 0)
        # 关键词权重更高
        final_scores[intent] = 0.6 * kw_score + 0.4 * sem_score

    # Top-K
    top_intents = sorted(final_scores.items(), key=lambda x: -x[1])[:top_k]
    return [(intent, score) for intent, score in top_intents if score > 0]


def match_cluster_from_description(description, top_k=3):
    """
    方案B: 从用户描述匹配簇

    Args:
        description: 用户自然语言描述
        top_k: 返回最相似的top_k个簇

    Returns:
        list of (cluster_id, similarity_score, cluster_info)
    """
    # 同上，生成描述embedding
    desc_lower = description.lower()

    keyword_intent_map = {
        "app": ["app_SELECT", "app_QUERY", "app_PLAY", "app_OPEN"],
        "选取": ["app_SELECT", "radio_SELECT", "tvchannel_SELECT"],
        "选择": ["app_SELECT", "radio_SELECT", "tvchannel_SELECT"],
        "播放": ["music_PLAY", "video_PLAY", "radio_PLAY"],
        "音乐": ["music_PLAY", "music_QUERY"],
        "歌曲": ["music_PLAY", "music_QUERY", "lyric_QUERY"],
        "歌词": ["lyric_QUERY"],
        "视频": ["video_PLAY", "video_QUERY"],
        # 新增: 诗歌/诗词相关
        "诗歌": ["poetry_QUERY"],
        "诗": ["poetry_QUERY"],
        "诗词": ["poetry_QUERY"],
        "古诗": ["poetry_QUERY"],
        "接龙": ["poetry_QUERY"],
        "诗句": ["poetry_QUERY"],
        # 新增: 猜谜相关
        "猜谜": ["riddle_QUERY"],
        "谜语": ["riddle_QUERY"],
        "谜": ["riddle_QUERY"],
        # 新增: 天气相关
        "天气": ["weather_QUERY"],
        # 新增: 日期/时间相关
        "日期": ["date_QUERY", "time_QUERY"],
        "时间": ["time_QUERY"],
        "几点": ["time_QUERY"],
        # 新增: 计算/翻译等
        "计算": ["calculate_QUERY"],
        "翻译": ["translation_QUERY"],
        # 新增: 电台/电视
        "电台": ["radio_PLAY", "radio_QUERY"],
        "电视": ["tvchannel_PLAY", "tvchannel_QUERY"],
        "频道": ["tvchannel_PLAY", "tvchannel_QUERY"],
    }

    keyword_samples = []
    for keyword in keyword_intent_map.keys():
        if keyword in desc_lower:
            for text, idx in zip(train_texts, range(len(train_texts))):
                if keyword in text.lower():
                    keyword_samples.append(idx)

    if keyword_samples:
        desc_emb = np.mean(train_emb[keyword_samples[:10]], axis=0)
        desc_emb = desc_emb / np.linalg.norm(desc_emb)
    else:
        # 无法提取关键词时，返回空
        return []

    # 与各簇摘要embedding匹配
    cluster_scores = {}
    for c, summary in cluster_semantic_summary.items():
        sim = np.dot(desc_emb, summary["summary_embedding"])
        cluster_scores[c] = sim

    # Top-K
    top_clusters = sorted(cluster_scores.items(), key=lambda x: -x[1])[:top_k]

    return [
        (c, score, cluster_semantic_summary[c])
        for c, score in top_clusters if score > 0.3
    ]


def fusion_match(description, threshold=0.5):
    """
    融合双层匹配结果

    Args:
        description: 用户描述
        threshold: 置信度阈值

    Returns:
        {
            "confidence": high/medium/low,
            "matched_intent": str,
            "matched_clusters": list,
            "intent_score": float,
            "cluster_scores": list,
            "is_consistent": bool  # 意图和簇是否一致
        }
    """
    # 方案A: 意图匹配
    intent_matches = match_intent_from_description(description, top_k=3)

    # 方案B: 簇匹配
    cluster_matches = match_cluster_from_description(description, top_k=5)  # 扩大候选范围

    if not intent_matches and not cluster_matches:
        return {
            "confidence": "low",
            "matched_intent": None,
            "matched_clusters": [],
            "message": "无法从描述中提取有效信息"
        }

    # 取最佳意图匹配
    best_intent = intent_matches[0] if intent_matches else (None, 0)

    # ===== 关键修复: 只保留意图一致的簇 =====
    final_clusters = []

    if best_intent[0]:
        # 方法1: 优先使用意图对应的簇
        intent_related_clusters = intent_to_clusters.get(best_intent[0], [])
        final_clusters = intent_related_clusters

        # 方法2: 从簇匹配中筛选意图一致的
        if cluster_matches:
            consistent_clusters = []
            for c, score, cluster_info in cluster_matches:
                # 检查簇的主导意图是否与匹配意图一致
                cluster_dominant_intent = cluster_info.get("dominant_intent", "")
                if cluster_dominant_intent == best_intent[0]:
                    consistent_clusters.append(c)

            # 合并：意图映射的簇 + 筛选后一致的簇
            final_clusters = list(set(intent_related_clusters) | set(consistent_clusters))

        confidence = "high" if final_clusters else "medium"
        is_consistent = len(final_clusters) > 0

    else:
        # 无意图匹配时，使用簇匹配结果
        final_clusters = [c for c, _, _ in cluster_matches[:2]]
        confidence = "medium" if final_clusters else "low"
        is_consistent = None

    # 构建返回信息
    cluster_scores = [(c, cluster_semantic_summary[c].get("dominant_intent", "?"))
                      for c in final_clusters[:3] if c in cluster_semantic_summary]

    return {
        "confidence": confidence,
        "matched_intent": best_intent[0],
        "matched_clusters": final_clusters,
        "intent_score": best_intent[1],
        "cluster_scores": cluster_scores,
        "is_consistent": is_consistent,
        "message": f"意图匹配: {best_intent[0]} ({best_intent[1]:.2f}), 一致簇: {len(final_clusters)}个"
    }


# ========== 检索函数 ==========

def retrieve(query_emb, top_k=5, weights=None, preferred_clusters=None, prefer_dominant_intent=True):
    """
    簇召回 + 簇内检索

    Args:
        query_emb: 查询embedding
        top_k: 返回数量
        weights: 簇权重
        preferred_clusters: 优先召回的簇 (来自反馈学习)
        prefer_dominant_intent: 是否优先返回主导意图的样本
    """
    cluster_sims = []
    for c, center in cluster_centers.items():
        sim = np.dot(query_emb, center.reshape(1, -1).T)[0][0]
        w = weights.get(c, 1.0) if weights else 1.0

        # 优先簇大幅加权，确保能排在前面
        if preferred_clusters and c in preferred_clusters:
            w = max(w, 10.0)  # 至少10倍权重，确保优先召回

        score = sim * w
        cluster_sims.append((c, score, sim, w))

    # Top-3 簇
    top_clusters = sorted(cluster_sims, key=lambda x: -x[1])[:3]
    candidates = []
    for item in top_clusters:
        c = item[0]  # 取簇ID
        candidates.extend(cluster_to_indices[c])

    if not candidates:
        candidates = list(range(len(train_idx)))

    candidate_emb = train_norm[candidates]
    sims = np.dot(query_emb, candidate_emb.T)[0]

    # ===== 新增: 混合簇处理 =====
    if prefer_dominant_intent and len(top_clusters) > 0:
        # 获取召回簇的主导意图
        dominant_intents = []
        for item in top_clusters[:1]:  # 只看第一个簇
            c = item[0]
            if c in cluster_to_dominant_intent:
                dominant_intents.append(cluster_to_dominant_intent[c])

        # 如果有主导意图，调整排序：优先返回主导意图的样本
        if dominant_intents:
            # 标记候选样本是否属于主导意图
            candidate_labels = [train_labels[idx] for idx in candidates]

            # 综合评分 = 语义相似度 + 意图一致性加成
            adjusted_scores = []
            for i, (idx, sim, label) in enumerate(zip(candidates, sims, candidate_labels)):
                # 主导意图样本额外加分
                intent_bonus = 0.3 if label in dominant_intents else 0.0
                adjusted_score = sim + intent_bonus
                adjusted_scores.append(adjusted_score)

            # 按调整后的分数排序
            top_local = np.argsort(adjusted_scores)[::-1][:top_k]
        else:
            top_local = np.argsort(sims)[::-1][:top_k]
    else:
        top_local = np.argsort(sims)[::-1][:top_k]

    return [candidates[i] for i in top_local], top_clusters, sims[top_local]


# ========== 智能权重更新 ==========

def update_weights_smart():
    """基于反馈计数的权重更新"""
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


def apply_suggestion_optimization(matched_clusters, wrong_clusters, confidence):
    """
    根据匹配结果优化簇权重

    Args:
        matched_clusters: 用户建议匹配到的正确簇
        wrong_clusters: 当前召回的错误簇
        confidence: 匹配置信度
    """
    # 加大权重调整幅度，确保能扭转召回结果
    multiplier = {
        "high": 5.0,    # 强强化
        "medium": 3.0,  # 中等强化
        "low": 2.0      # 弱强化
    }

    boost_factor = multiplier.get(confidence, 2.0)

    # 强化正确簇
    for c in matched_clusters:
        if c in cluster_weights:
            cluster_weights[c] *= boost_factor
            cluster_feedback[c]["pos"] += 2  # 双倍正反馈计数

    # 大幅降低错误簇
    penalty_factor = 0.1  # 大幅惩罚
    for c in wrong_clusters:
        if c in cluster_weights and c not in matched_clusters:
            cluster_weights[c] *= penalty_factor
            cluster_feedback[c]["neg"] += 2  # 双倍负反馈计数


# ========== 查询特征提取 ==========

def extract_query_feature(query_text, query_emb):
    """
    提取查询特征，用于建立映射

    Returns:
        查询特征的唯一标识 (简化: 用embedding的离散化)
    """
    # 简化方案: 用关键词 + 意图大类
    query_lower = query_text.lower()

    # 提取关键词
    keywords = []
    for kw in ["app", "音乐", "歌曲", "歌词", "视频", "播放", "选择", "选取", "查询"]:
        if kw in query_lower:
            keywords.append(kw)

    return {
        "keywords": keywords,
        "text": query_text,
        "embedding_mean": np.mean(query_emb).item()
    }


def check_query_mapping(query_text, query_emb):
    """
    检查是否有历史映射记录

    改进: 使用文本相似度匹配，而非关键词匹配

    Returns:
        preferred_clusters or None
    """
    if not query_correct_mapping:
        return None

    # 方法1: 精确文本匹配
    for mapping in query_correct_mapping:
        if mapping["query_text"] == query_text:
            return mapping["correct_clusters"]

    # 方法2: 语义相似度匹配
    query_emb_norm = query_emb.flatten() / np.linalg.norm(query_emb.flatten())

    best_match = None
    best_sim = 0.0

    for mapping in query_correct_mapping:
        # 找到原始查询的embedding
        mapping_idx = mapping.get("query_idx")
        if mapping_idx is not None:
            mapping_emb = test_norm[mapping_idx].flatten()
            sim = np.dot(query_emb_norm, mapping_emb)
            if sim > best_sim and sim > 0.85:  # 高相似度阈值
                best_sim = sim
                best_match = mapping["correct_clusters"]

    return best_match


# ========== 交互模式 ==========

def interactive_mode(initial_errors):
    """交互式验证"""
    print("\n" + "=" * 80)
    print("交互式反馈验证 v5 - 融合智能反馈系统")
    print("=" * 80)
    print("""
反馈方式:
─────────────────────────────
1. 先看结果，判断评分
2. 输入评分 (1/0)
3. 输入自然语言建议（可选）

建议示例:
  - "这是APP选取相关的问题"
  - "这是播放音乐的操作"
  - "这是查询歌词的问题"
  - "应该是选择相关的操作"

系统会自动理解你的建议，优化召回!

命令:
  - 输入数字: 选择测试样本
  - 'stats': 查看统计
  - 'clusters': 查看各簇信息
  - 'mappings': 查看查询映射记录
  - 'test': 批量测试
  - 'retest <数字>': 重新测试某样本 (验证迭代效果)
  - 'quit': 退出
    """)

    while True:
        try:
            user_input = input("\n> ").strip()

            if user_input.lower() == 'quit':
                break

            elif user_input.lower() == 'stats':
                print_stats()

            elif user_input.lower() == 'clusters':
                print_clusters_info()

            elif user_input.lower() == 'mappings':
                print_mappings()

            elif user_input.lower() == 'test':
                print_batch_test()

            elif user_input.lower().startswith('retest'):
                parts = user_input.split()
                if len(parts) == 2 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(test_idx):
                        retest_sample(idx)
                else:
                    print("用法: retest <数字>")

            elif user_input.isdigit():
                idx = int(user_input)
                if 1 <= idx <= len(test_idx):
                    process_sample(idx - 1)
                else:
                    print(f"请输入 1-{len(test_idx)} 之间的数字")

        except KeyboardInterrupt:
            print("\n\n退出...")
            break
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()


def print_stats():
    """打印统计信息"""
    print(f"\n{'='*70}")
    print("当前统计")
    print("="*70)

    print(f"\n基本统计:")
    print(f"  反馈数: {len(feedback_history)}")
    pos = sum(1 for f in feedback_history if f['score'] == 1)
    neg = len(feedback_history) - pos
    if pos + neg > 0:
        print(f"  正反馈: {pos}, 负反馈: {neg} (正确率 {pos/(pos+neg)*100:.1f}%)")

    print(f"\n  查询映射记录: {len(query_correct_mapping)}")

    print(f"\n各簇状态 (仅显示有反馈的):")
    print(f"  {'簇':>6} {'主导意图':>20} {'正':>4} {'负':>4} {'权重':>6}")
    print("  " + "-" * 50)

    for c in sorted(cluster_centers.keys()):
        fb = cluster_feedback[c]
        total = fb["pos"] + fb["neg"]
        if total > 0:
            dominant = cluster_to_dominant_intent.get(c, "?")[:18]
            print(f"  {c:>6} {dominant:>20} {fb['pos']:>4} {fb['neg']:>4} {cluster_weights[c]:>6.2f}")

    # 测试当前效果
    correct, errors_fixed = test_current_accuracy(initial_errors)
    acc = correct / len(test_idx)

    print(f"\n当前 Top-1 准确率: {acc:.1%}")
    print(f"初始准确率: {len(test_idx)-len(initial_errors)/len(test_idx):.1%}")
    print(f"\n🎯 错误改善: {errors_fixed}/{len(initial_errors)} ({errors_fixed/len(initial_errors)*100:.1f}%)")


def print_clusters_info():
    """打印簇信息"""
    print(f"\n各簇详细信息:")
    for c in sorted(cluster_centers.keys())[:10]:  # 只显示前10个
        summary = cluster_semantic_summary[c]
        print(f"\n  簇 #{c} ({summary['sample_count']} 样本):")
        print(f"    主导意图: {summary['dominant_intent']}")
        print(f"    代表样本: {summary['representative_texts'][:2]}")


def print_mappings():
    """打印映射记录"""
    print(f"\n查询-正确映射记录 ({len(query_correct_mapping)}条):")
    for i, m in enumerate(query_correct_mapping[-5:], 1):  # 显示最近5条
        print(f"\n  {i}. 查询: \"{m['query_text'][:30]}...\"")
        print(f"     建议描述: \"{m['suggestion']}\"")
        print(f"     匹配意图: {m['matched_intent']}")
        print(f"     正确簇: {m['correct_clusters']}")
        print(f"     置信度: {m['confidence']}")


def print_batch_test():
    """批量测试"""
    print("\n批量测试中...")
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
    acc = correct / len(test_idx)
    print(f"当前 Top-1 准确率: {acc:.1%}")


def test_current_accuracy(initial_errors):
    """测试当前准确率"""
    correct = 0
    errors_fixed = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
            if i in initial_errors:
                errors_fixed += 1
    return correct, errors_fixed


def retest_sample(idx):
    """重新测试某样本，验证迭代效果"""
    query_text = test_texts[idx]
    query_label = test_labels[idx]
    query_emb = test_norm[idx:idx+1]

    # 检查是否有映射
    preferred = check_query_mapping(query_text, query_emb)

    print(f"\n{'='*60}")
    print(f"重新测试样本 #{idx+1}")
    print("="*60)
    print(f"查询: \"{query_text}\"")
    print(f"正确意图: {query_label}")

    if preferred:
        print(f"已有映射 → 优先簇: {preferred}")

    # 检索
    top_indices, top_clusters, top_sims = retrieve(
        query_emb, top_k=3, weights=cluster_weights, preferred_clusters=preferred
    )

    top1_intent = train_labels[top_indices[0]]
    intent_match = (top1_intent == query_label)

    print(f"\nTop-1: [{top1_intent}] {'✓' if intent_match else '✗'}")

    if intent_match:
        print(f"\n✅ 迭代成功! 问题已正确回答")
    else:
        print(f"\n❌ 仍需优化，请继续反馈")


def process_sample(idx):
    """处理单个样本的反馈流程"""
    query_text = test_texts[idx]
    query_label = test_labels[idx]
    query_emb = test_norm[idx:idx+1]

    print(f"\n{'='*70}")
    print(f"查询 #{idx+1}")
    print("="*70)
    print(f"问题: \"{query_text}\"")
    print(f"正确意图: {query_label}")

    # 检查是否有历史映射
    preferred = check_query_mapping(query_text, query_emb)
    if preferred:
        print(f"\n💡 已有优化记录 → 优先召回: {preferred}")

    # 检索
    top_indices, top_clusters, top_sims = retrieve(
        query_emb, top_k=3, weights=cluster_weights, preferred_clusters=preferred
    )

    print(f"\n召回簇: {[item[0] for item in top_clusters]}")
    print(f"\nTop-3 结果:")

    top1_intent = train_labels[top_indices[0]]
    top1_semantic = top_sims[0]
    intent_match = (top1_intent == query_label)

    for i, (idx2, sim) in enumerate(zip(top_indices, top_sims), 1):
        intent = train_labels[idx2]
        match_mark = "✓" if intent == query_label else "✗"
        print(f"\n  {i}. [{intent}] {match_mark} (语义 {sim:.2f})")
        print(f"     \"{train_texts[idx2][:50]}...\"")

    # 判断建议
    print(f"\n{'='*50}")
    print("判断建议")
    print("="*50)
    print(f"  Top-1 意图匹配: {'✓ 是' if intent_match else '✗ 否'}")
    print(f"  Top-1 语义相似度: {top1_semantic:.2f}")

    suggested_score = 1 if intent_match and top1_semantic > 0.7 else 0
    print(f"\n  → 建议评分: {suggested_score}")

    # 获取评分
    score_input = input("\n评分 (1/0): ").strip()

    if score_input not in ['1', '0']:
        print("输入无效，跳过")
        return

    score = int(score_input)

    # 获取反馈建议
    print("\n请输入自然语言建议（描述问题类型，按Enter跳过）:")
    print("  示例: \"这是APP选取相关的问题\" / \"这是播放音乐的操作\"")
    suggestion = input("建议: ").strip()

    # 记录反馈
    recalled_clusters = [item[0] for item in top_clusters]

    feedback_record = {
        "query_idx": idx,
        "query_text": query_text,
        "query_intent": query_label,
        "score": score,
        "suggestion": suggestion,
        "clusters": recalled_clusters,
        "top1_intent": top1_intent,
        "semantic_sim": float(top1_semantic)
    }
    feedback_history.append(feedback_record)

    # 处理反馈
    if score == 1:
        # 正反馈: 强化当前召回的簇
        for c in recalled_clusters:
            cluster_feedback[c]["pos"] += 1
        update_weights_smart()
        print(f"\n✓ 正反馈已记录，权重已更新")
        save_persistence()  # 每次反馈后保存

    else:
        # 负反馈: 记录 + 处理建议
        for c in recalled_clusters:
            cluster_feedback[c]["neg"] += 1

        if suggestion:
            # ===== 核心: 智能建议处理 =====
            print(f"\n{'='*50}")
            print("智能建议分析")
            print("="*50)

            match_result = fusion_match(suggestion)

            print(f"\n  {match_result['message']}")
            print(f"  置信度: {match_result['confidence']}")

            if match_result['matched_intent']:
                print(f"  匹配意图: {match_result['matched_intent']}")

            if match_result['matched_clusters']:
                print(f"  匹配簇: {match_result['matched_clusters']}")

                # 显示匹配簇的信息
                for c in match_result['matched_clusters'][:2]:
                    summary = cluster_semantic_summary.get(c, {})
                    if summary:
                        print(f"\n    簇 #{c}:")
                        print(f"      主导意图: {summary.get('dominant_intent', '?')}")
                        print(f"      代表样本: {summary.get('representative_texts', [])[:1]}")

            # 执行优化
            if match_result['confidence'] in ['high', 'medium']:
                print(f"\n{'='*50}")
                print("执行优化")
                print("="*50)

                apply_suggestion_optimization(
                    match_result['matched_clusters'],
                    recalled_clusters,
                    match_result['confidence']
                )

                # 记录查询映射
                query_feature = extract_query_feature(query_text, query_emb)
                mapping_record = {
                    "query_text": query_text,
                    "keywords": query_feature["keywords"],
                    "correct_intent": match_result['matched_intent'],
                    "correct_clusters": match_result['matched_clusters'],
                    "suggestion": suggestion,
                    "confidence": match_result['confidence'],
                    "wrong_clusters": recalled_clusters
                }
                query_correct_mapping.append(mapping_record)

                print(f"\n✓ 优化完成!")
                print(f"  - 强化簇: {match_result['matched_clusters']}")
                print(f"  - 降低簇: {[c for c in recalled_clusters if c not in match_result['matched_clusters']]}")
                print(f"  - 已建立查询映射")
                save_persistence()  # 优化后保存

                # 提示重新测试
                print(f"\n💡 输入 'retest {idx+1}' 可验证迭代效果")
            else:
                print(f"\n⚠ 置信度较低，建议已记录但未执行优化")
                print(f"  请提供更具体的描述，如包含关键词: app/音乐/播放/选择等")

        else:
            update_weights_smart()
            print(f"\n✓ 负反馈已记录，权重已更新")
            save_persistence()  # 负反馈后保存


# ========== 主程序 ==========

if __name__ == "__main__":
    # 加载历史持久化数据
    print("\n加载持久化数据...")
    has_history = load_persistence()

    # 如果有历史记录，测试学习效果
    if has_history:
        correct = 0
        for i, query_label in enumerate(test_labels):
            query_emb = test_norm[i:i+1]
            preferred = check_query_mapping(test_texts[i], query_emb)
            top_indices, _, _ = retrieve(query_emb, top_k=1, weights=cluster_weights, preferred_clusters=preferred)
            if train_labels[top_indices[0]] == query_label:
                correct += 1
        acc = correct / len(test_idx)
        print(f"✓ 历史学习效果: Top-1 = {acc:.1%}")

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

    # 最终统计
    print("\n" + "=" * 80)
    print("最终统计")
    print("=" * 80)

    correct, errors_fixed = test_current_accuracy(initial_errors)
    final_acc = correct / len(test_idx)

    pos = sum(1 for f in feedback_history if f['score'] == 1)
    neg = len(feedback_history) - pos

    print(f"\n基本统计:")
    print(f"  总反馈数: {len(feedback_history)}")
    print(f"  正反馈: {pos}, 负反馈: {neg}")
    print(f"  查询映射记录: {len(query_correct_mapping)}")
    print(f"\n效果:")
    print(f"  初始 Top-1: {initial_acc:.1%}")
    print(f"  最终 Top-1: {final_acc:.1%}")
    print(f"  变化: {(final_acc - initial_acc) * 100:+.1f}%")

    print(f"\n🎯 错误改善:")
    print(f"  初始错误样本数: {len(initial_errors)}")
    print(f"  被纠正的错误数: {errors_fixed}")
    print(f"  错误改善率: {errors_fixed/len(initial_errors)*100:.1f}%")

    # 保存结果
    if feedback_history:
        output = {
            "feedback_history": feedback_history,
            "query_correct_mapping": query_correct_mapping,
            "final_stats": {
                "initial_acc": initial_acc,
                "final_acc": final_acc,
                "errors_fixed": errors_fixed,
                "total_errors": len(initial_errors)
            }
        }
        output_path = PROJECT_ROOT / "04_intent_data_mapping/results/feedback_v5_history.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已保存到: {output_path}")

    # 最终保存持久化数据
    save_persistence()