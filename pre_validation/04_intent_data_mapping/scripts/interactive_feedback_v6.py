#!/usr/bin/env python3
"""
交互式反馈验证 v6 - LinUCB 集成版本

支持:
1. 评分 (1/0)
2. 自然语言建议输入
3. LinUCB 算法优化簇选择
4. 建议 embedding 作为上下文特征
5. 持久化学习
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import hdbscan

# ========== 配置 ==========

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
DATA_DIR = PROJECT_ROOT / "data" / "smp2019"

# LinUCB 参数
ALPHA = 1.0  # 探索参数，越大越倾向探索
EMBEDDING_DIM = 64  # 降维后的特征维度

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

# 意图到簇的反向映射（主导簇）
intent_to_clusters = defaultdict(list)
for c, label_list in cluster_to_labels.items():
    counter = Counter(label_list)
    dominant_intent = counter.most_common(1)[0][0]
    intent_to_clusters[dominant_intent].append(c)

# ===== 新增: 意图到簇的完整映射（包含该意图样本的所有簇）=====
intent_to_all_clusters = defaultdict(list)  # 意图 -> [(簇ID, 样本数, 占比), ...]
for c, label_list in cluster_to_labels.items():
    counter = Counter(label_list)
    total = len(label_list)
    for intent, count in counter.items():
        # 记录包含该意图的簇，以及样本数和占比
        intent_to_all_clusters[intent].append((c, count, count/total))

# 按样本数排序
for intent in intent_to_all_clusters:
    intent_to_all_clusters[intent].sort(key=lambda x: -x[1])

# 统计没有主导簇的意图
all_intents = set(train_labels)
intents_without_dominant = all_intents - set(intent_to_clusters.keys())
print(f"  意图数: {len(all_intents)}")
print(f"  有主导簇的意图: {len(intent_to_clusters)}")
print(f"  无主导簇的意图: {len(intents_without_dominant)}")

# 簇列表（有序）
cluster_ids = sorted(cluster_centers.keys())
n_clusters = len(cluster_ids)
cluster_id_to_idx = {c: i for i, c in enumerate(cluster_ids)}

print(f"✓ 簇数量: {n_clusters}")

# ========== 簇语义摘要 ==========

print("构建簇语义摘要...")
cluster_semantic_summary = {}

for c in cluster_to_indices.keys():
    indices = cluster_to_indices[c]
    label_list = cluster_to_labels[c]
    counter = Counter(label_list)

    cluster_center = cluster_centers[c]
    sample_sims = []
    for idx in indices:
        sim = np.dot(train_emb[idx] / np.linalg.norm(train_emb[idx]), cluster_center)
        sample_sims.append((idx, sim))

    top3_indices = sorted(sample_sims, key=lambda x: -x[1])[:3]
    representative_texts = [train_texts[idx] for idx, _ in top3_indices]

    summary_emb = np.mean([train_emb[idx] for idx, _ in top3_indices], axis=0)
    summary_emb = summary_emb / np.linalg.norm(summary_emb)

    cluster_semantic_summary[c] = {
        "dominant_intent": cluster_to_dominant_intent[c],
        "intent_distribution": counter.most_common(3),
        "representative_texts": representative_texts,
        "summary_embedding": summary_emb,
        "sample_count": len(indices)
    }

# ========== PCA 降维（用于 LinUCB 特征） ==========

print("训练 PCA 降维...")
pca = PCA(n_components=EMBEDDING_DIM)
all_embeddings = np.vstack([train_emb, test_emb])
pca.fit(all_embeddings)

train_emb_reduced = pca.transform(train_emb)
test_emb_reduced = pca.transform(test_emb)

print(f"✓ PCA 降维: {embeddings.shape[1]} → {EMBEDDING_DIM}")

# ========== 初始化 ==========

train_norm = train_emb / np.linalg.norm(train_emb, axis=1, keepdims=True)
test_norm = test_emb / np.linalg.norm(test_emb, axis=1, keepdims=True)

cluster_weights = {c: 1.0 for c in cluster_centers.keys()}
cluster_feedback = {c: {"pos": 0, "neg": 0} for c in cluster_centers.keys()}
feedback_history = []
query_correct_mapping = []

# ========== LinUCB 类 ==========

class LinUCB:
    """
    LinUCB 算法实现

    特征设计:
    - 查询 embedding (降维后, 64维)
    - 建议内容 embedding (降维后, 64维) - 如果有建议
    - 召回簇 one-hot (n_clusters 维)

    动作: 选择哪个簇
    奖励: 用户评分 1/0
    """

    def __init__(self, n_arms, context_dim, alpha=1.0):
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha

        # 每个臂（簇）的参数
        # A: d x d 矩阵，初始为单位矩阵
        # b: d x 1 向量，初始为0
        self.A = [np.eye(context_dim) for _ in range(n_arms)]
        self.b = [np.zeros(context_dim) for _ in range(n_arms)]

        # 统计
        self.pull_counts = [0] * n_arms
        self.total_reward = [0.0] * n_arms

    def get_ucb_scores(self, context):
        """
        计算每个臂的 UCB 分数

        Args:
            context: 上下文特征向量 (context_dim,)

        Returns:
            ucb_scores: 每个臂的 UCB 分数
        """
        ucb_scores = []

        for arm in range(self.n_arms):
            # 计算 θ = A^{-1} b
            theta = np.linalg.solve(self.A[arm], self.b[arm])

            # 计算 UCB = θ^T x + α * sqrt(x^T A^{-1} x)
            pred = np.dot(theta, context)

            # 置信区间宽度
            A_inv = np.linalg.inv(self.A[arm])
            uncertainty = np.sqrt(np.dot(context, np.dot(A_inv, context)))

            ucb = pred + self.alpha * uncertainty
            ucb_scores.append(ucb)

        return np.array(ucb_scores)

    def select_arm(self, context):
        """
        选择最优臂（簇）

        Args:
            context: 上下文特征向量

        Returns:
            selected_arm: 选中的臂索引
            ucb_scores: 所有臂的 UCB 分数
        """
        ucb_scores = self.get_ucb_scores(context)
        selected_arm = np.argmax(ucb_scores)
        return selected_arm, ucb_scores

    def update(self, arm, context, reward):
        """
        更新模型参数

        Args:
            arm: 选择的臂
            context: 上下文特征向量
            reward: 奖励值 (0 或 1)
        """
        # A = A + x x^T
        self.A[arm] += np.outer(context, context)

        # b = b + r * x
        self.b[arm] += reward * context

        # 统计
        self.pull_counts[arm] += 1
        self.total_reward[arm] += reward

    def get_arm_stats(self, arm):
        """获取某个臂的统计信息"""
        theta = np.linalg.solve(self.A[arm], self.b[arm])
        return {
            "pulls": self.pull_counts[arm],
            "total_reward": self.total_reward[arm],
            "avg_reward": self.total_reward[arm] / max(1, self.pull_counts[arm]),
            "theta_norm": np.linalg.norm(theta)
        }

    def get_state(self):
        """获取模型状态（用于持久化）"""
        return {
            "A": [A.tolist() for A in self.A],
            "b": [b.tolist() for b in self.b],
            "pull_counts": self.pull_counts,
            "total_reward": self.total_reward,
            "alpha": self.alpha
        }

    def load_state(self, state):
        """加载模型状态"""
        self.A = [np.array(A) for A in state["A"]]
        self.b = [np.array(b) for b in state["b"]]
        self.pull_counts = state["pull_counts"]
        self.total_reward = state["total_reward"]
        self.alpha = state.get("alpha", self.alpha)


def build_context(query_emb_reduced, suggestion_emb_reduced=None, recalled_cluster_idx=None):
    """
    构建上下文特征向量

    特征组成:
    - 查询 embedding (64维)
    - 建议内容 embedding (64维, 如果有)
    - 召回簇 one-hot (n_clusters 维)

    总维度: 64 + 64 + n_clusters = 64 + 64 + 16 = 144
    """
    features = []

    # 1. 查询 embedding
    features.extend(query_emb_reduced.flatten())

    # 2. 建议内容 embedding (没有建议时用零向量)
    if suggestion_emb_reduced is not None:
        features.extend(suggestion_emb_reduced.flatten())
    else:
        features.extend(np.zeros(EMBEDDING_DIM))

    # 3. 召回簇 one-hot (没有时用零向量)
    cluster_onehot = np.zeros(n_clusters)
    if recalled_cluster_idx is not None:
        cluster_onehot[recalled_cluster_idx] = 1.0
    features.extend(cluster_onehot)

    return np.array(features)


# 初始化 LinUCB
CONTEXT_DIM = EMBEDDING_DIM * 2 + n_clusters  # 查询 + 建议 + 簇one-hot
linucb = LinUCB(n_arms=n_clusters, context_dim=CONTEXT_DIM, alpha=ALPHA)

print(f"✓ LinUCB 初始化: {n_clusters} 个臂, 特征维度 {CONTEXT_DIM}")

# ========== 双层语义匹配函数（保留作为备用） ==========

def match_intent_from_keywords(description, top_k=3):
    """关键词匹配意图"""
    keyword_intent_map = {
        # 诗歌/诗词
        "诗歌": ["poetry_QUERY"],
        "诗": ["poetry_QUERY"],
        "诗词": ["poetry_QUERY"],
        "古诗": ["poetry_QUERY"],
        "接龙": ["poetry_QUERY"],
        "诗句": ["poetry_QUERY"],
        # 猜谜
        "猜谜": ["riddle_QUERY"],
        "谜语": ["riddle_QUERY"],
        "谜": ["riddle_QUERY"],
        # 天气/时间
        "天气": ["weather_QUERY"],
        "时间": ["time_QUERY"],
        "几点": ["time_QUERY"],
        "日期": ["date_QUERY"],
        # 音乐/歌曲
        "音乐": ["music_PLAY", "music_QUERY"],
        "歌曲": ["music_PLAY", "music_QUERY"],
        "歌词": ["lyric_QUERY"],
        "播放": ["music_PLAY", "video_PLAY"],
        # 视频/电影
        "视频": ["video_PLAY", "video_QUERY"],
        "电影": ["video_QUERY", "cinemas_QUERY"],
        "电视": ["tvchannel_PLAY", "tvchannel_QUERY"],
        "剧场": ["cinemas_QUERY"],
        "影院": ["cinemas_QUERY"],
        "video": ["video_QUERY", "video_PLAY"],
        # APP相关
        "app": ["app_SELECT", "app_QUERY", "app_LAUNCH"],
        "应用": ["app_LAUNCH", "app_SELECT", "app_QUERY"],
        "打开": ["app_LAUNCH", "app_OPEN"],
        "启动": ["app_LAUNCH"],
        "运行": ["app_LAUNCH"],
        "选择": ["app_SELECT"],
        "下载": ["app_DOWNLOAD"],
        # 电台/频道
        "电台": ["radio_PLAY", "radio_QUERY"],
        "频道": ["tvchannel_PLAY", "tvchannel_QUERY"],
        # 其他
        "计算": ["calculate_QUERY"],
        "翻译": ["translation_QUERY"],
        "小说": ["novel_QUERY"],
        "故事": ["story_QUERY"],
        # 英文关键词
        "launch": ["app_LAUNCH"],
        "open": ["app_LAUNCH", "app_OPEN"],
        "select": ["app_SELECT"],
        "play": ["music_PLAY", "video_PLAY"],
        "query": ["_QUERY"],
    }

    desc_lower = description.lower()
    scores = defaultdict(float)

    for keyword, intents in keyword_intent_map.items():
        if keyword in desc_lower:
            for intent in intents:
                scores[intent] += 1.0

    top_intents = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
    return [(intent, score) for intent, score in top_intents if score > 0]


def get_suggestion_embedding(suggestion_text):
    """
    从建议文本生成 embedding

    使用训练集中相似样本的 embedding 平均
    """
    if not suggestion_text:
        return None

    # 找训练集中包含建议关键词的样本
    suggestion_lower = suggestion_text.lower()
    matched_indices = []

    for i, text in enumerate(train_texts):
        if any(kw in text.lower() for kw in suggestion_lower if len(kw) > 1):
            matched_indices.append(i)

    if matched_indices:
        # 取前 5 个匹配样本的 embedding 平均
        matched_indices = matched_indices[:5]
        emb = np.mean(train_emb_reduced[matched_indices], axis=0)
        return emb

    return None


# ========== 检索函数 ==========

def retrieve(query_emb, query_emb_reduced, top_k=5, use_linucb=True, suggestion_text=None):
    """
    簇召回 + 簇内检索

    支持 LinUCB 选择或传统语义相似度
    """
    if use_linucb:
        # 构建 LinUCB 上下文
        suggestion_emb = get_suggestion_embedding(suggestion_text) if suggestion_text else None
        context = build_context(query_emb_reduced, suggestion_emb)

        # LinUCB 选择簇
        selected_arm_idx, ucb_scores = linucb.select_arm(context)
        selected_cluster_id = cluster_ids[selected_arm_idx]

        # 按UCB分数排序，取前3个簇
        top_arm_indices = np.argsort(ucb_scores)[::-1][:3]
        top_cluster_ids = [cluster_ids[i] for i in top_arm_indices]
        top_ucb_scores = [ucb_scores[i] for i in top_arm_indices]
    else:
        # 传统语义相似度
        cluster_sims = []
        for c, center in cluster_centers.items():
            sim = np.dot(query_emb, center.reshape(1, -1).T)[0][0]
            w = cluster_weights.get(c, 1.0)
            score = sim * w
            cluster_sims.append((c, score, sim))

        top_clusters = sorted(cluster_sims, key=lambda x: -x[1])[:3]
        top_cluster_ids = [c for c, _, _ in top_clusters]
        top_ucb_scores = [s for _, s, _ in top_clusters]

    # 簇内检索
    candidates = []
    for c in top_cluster_ids:
        candidates.extend(cluster_to_indices[c])

    if not candidates:
        candidates = list(range(len(train_idx)))

    candidate_emb = train_norm[candidates]
    sims = np.dot(query_emb, candidate_emb.T)[0]

    # 主导意图加成
    dominant_intents = [cluster_to_dominant_intent.get(c) for c in top_cluster_ids[:1]]
    if dominant_intents:
        candidate_labels = [train_labels[idx] for idx in candidates]
        adjusted_scores = []
        for i, (idx, sim, label) in enumerate(zip(candidates, sims, candidate_labels)):
            intent_bonus = 0.3 if label in dominant_intents else 0.0
            adjusted_scores.append(sim + intent_bonus)
        top_local = np.argsort(adjusted_scores)[::-1][:top_k]
    else:
        top_local = np.argsort(sims)[::-1][:top_k]

    return (
        [candidates[i] for i in top_local],
        top_cluster_ids,
        top_ucb_scores,
        context if use_linucb else None,
        selected_arm_idx if use_linucb else None
    )


# ========== 持久化 ==========

PERSISTENCE_FILE = PROJECT_ROOT / "04_intent_data_mapping/results/feedback_v6_persistence.json"

def load_persistence():
    """加载持久化数据"""
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

        # 加载 LinUCB 状态
        if "linucb_state" in data:
            linucb.load_state(data["linucb_state"])
            print(f"✓ 加载 LinUCB 状态")

        # 加载映射
        if "query_correct_mapping" in data:
            query_correct_mapping.extend(data["query_correct_mapping"])

        # 加载历史
        if "feedback_history" in data:
            feedback_history.extend(data["feedback_history"])
            print(f"✓ 加载反馈历史: {len(feedback_history)} 条")

        return True

    except Exception as e:
        print(f"⚠ 加载失败: {e}")
        return False


def save_persistence():
    """保存持久化数据"""
    def convert_to_native(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(v) for v in obj]
        return obj

    def clean_unicode(obj):
        if isinstance(obj, str):
            return obj.encode('utf-8', errors='replace').decode('utf-8')
        elif isinstance(obj, dict):
            return {k: clean_unicode(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_unicode(v) for v in obj]
        return obj

    data = {
        "cluster_weights": {str(c): float(w) for c, w in cluster_weights.items()},
        "linucb_state": linucb.get_state(),
        "query_correct_mapping": clean_unicode(convert_to_native(query_correct_mapping)),
        "feedback_history": clean_unicode(convert_to_native(feedback_history)),
    }

    with open(PERSISTENCE_FILE, "w", encoding="utf-8", errors='replace') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 持久化保存")


# ========== 交互模式 ==========

def interactive_mode(initial_errors):
    """交互式验证"""
    print("\n" + "=" * 80)
    print("交互式反馈验证 v6 - LinUCB 集成版本")
    print("=" * 80)
    print("""
反馈方式:
─────────────────────────────
1. 先看结果，判断评分
2. 输入评分 (1/0)
3. 输入自然语言建议（可选）

LinUCB 特性:
  - 自动从反馈中学习建议→簇的映射
  - 探索-利用平衡
  - 新建议类型自动泛化

命令:
  - 输入数字: 选择测试样本
  - 'stats': 查看统计 + LinUCB 状态
  - 'clusters': 查看所有簇信息
  - 'cluster <数字>': 查看指定簇详情
  - 'intents': 查看意图-簇映射
  - 'intent <意图名>': 查看指定意图的簇分布
  - 'test': 批量测试
  - 'retest <数字>': 重新测试某样本
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

            elif user_input.lower().startswith('cluster '):
                parts = user_input.split()
                if len(parts) == 2 and parts[1].isdigit():
                    print_cluster_detail(int(parts[1]))

            elif user_input.lower() == 'intents':
                print_intents_info()

            elif user_input.lower().startswith('intent '):
                parts = user_input.split(maxsplit=1)
                if len(parts) == 2:
                    print_intent_clusters(parts[1])

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
    print("统计信息")
    print("="*70)

    # 反馈统计
    print(f"\n反馈统计:")
    print(f"  总反馈数: {len(feedback_history)}")
    pos = sum(1 for f in feedback_history if f['score'] == 1)
    neg = len(feedback_history) - pos
    if pos + neg > 0:
        print(f"  正反馈: {pos}, 负反馈: {neg} ({pos/(pos+neg)*100:.1f}%)")

    # LinUCB 状态
    print(f"\nLinUCB 状态:")
    print(f"  探索参数 α: {linucb.alpha}")
    print(f"  特征维度: {CONTEXT_DIM}")
    print(f"\n  各簇被选择次数和奖励:")
    print(f"  {'簇':>4} {'意图':>20} {'选择':>6} {'奖励':>6} {'均值':>6}")
    print("  " + "-" * 50)

    for arm in range(n_clusters):
        stats = linucb.get_arm_stats(arm)
        cluster_id = cluster_ids[arm]
        dominant = cluster_to_dominant_intent.get(cluster_id, "?")[:18]
        if stats["pulls"] > 0:
            print(f"  {cluster_id:>4} {dominant:>20} {stats['pulls']:>6} {stats['total_reward']:>6.0f} {stats['avg_reward']:>6.2f}")

    # 当前准确率
    correct, errors_fixed = test_current_accuracy(initial_errors)
    acc = correct / len(test_idx)
    print(f"\n当前 Top-1 准确率: {acc:.1%}")
    print(f"🎯 错误改善: {errors_fixed}/{len(initial_errors)} ({errors_fixed/len(initial_errors)*100:.1f}%)")


def print_clusters_info():
    """打印所有簇信息"""
    print(f"\n{'='*70}")
    print("所有簇信息")
    print("="*70)

    print(f"\n{'簇':>4} {'样本':>6} {'主导意图':>20} {'Top-2 意图分布'}")
    print("-" * 70)

    for c in sorted(cluster_to_indices.keys()):
        counter = Counter(cluster_to_labels[c])
        dominant = counter.most_common(1)[0]
        top2 = counter.most_common(2)
        top2_str = ", ".join([f"{i}:{n}" for i, n in top2])

        print(f"{c:>4} {len(cluster_to_indices[c]):>6} {dominant[0]:>20} {top2_str}")

    print(f"\n总计: {len(cluster_to_indices)} 个簇")


def print_cluster_detail(cluster_id):
    """打印指定簇详情"""
    if cluster_id not in cluster_to_indices:
        print(f"簇 #{cluster_id} 不存在")
        print(f"可用簇: {sorted(cluster_to_indices.keys())}")
        return

    print(f"\n{'='*70}")
    print(f"簇 #{cluster_id} 详情")
    print("="*70)

    # 基本信息
    counter = Counter(cluster_to_labels[cluster_id])
    dominant = counter.most_common(1)[0]
    print(f"\n样本数: {len(cluster_to_indices[cluster_id])}")
    print(f"主导意图: {dominant[0]} ({dominant[1]}个, {dominant[1]/len(cluster_to_indices[cluster_id]):.1%})")

    # 意图分布
    print(f"\n意图分布 (共 {len(counter)} 种意图):")
    for intent, count in counter.most_common(10):
        pct = count / len(cluster_to_indices[cluster_id]) * 100
        bar = "█" * int(pct / 5)
        print(f"  {intent:>25} {count:>4} ({pct:>5.1f}%) {bar}")

    # 代表样本
    summary = cluster_semantic_summary.get(cluster_id, {})
    if summary.get("representative_texts"):
        print(f"\n代表样本:")
        for i, text in enumerate(summary["representative_texts"][:3], 1):
            print(f"  {i}. \"{text[:50]}...\"")

    # LinUCB 状态
    if cluster_id in cluster_id_to_idx:
        arm_idx = cluster_id_to_idx[cluster_id]
        stats = linucb.get_arm_stats(arm_idx)
        print(f"\nLinUCB 状态:")
        print(f"  臂索引: {arm_idx}")
        print(f"  被选择: {stats['pulls']} 次")
        print(f"  总奖励: {stats['total_reward']:.0f}")
        print(f"  平均奖励: {stats['avg_reward']:.2f}")


def print_intents_info():
    """打印意图-簇映射概览"""
    print(f"\n{'='*70}")
    print("意图-簇映射概览")
    print("="*70)

    # 有主导簇的意图
    print(f"\n【有主导簇的意图】({len(intent_to_clusters)} 个):")
    intents_with_cluster = sorted(intent_to_clusters.keys())
    for i in range(0, len(intents_with_cluster), 4):
        row = intents_with_cluster[i:i+4]
        print("  " + ", ".join(f"{x:<20}" for x in row))

    # 无主导簇的意图
    all_intents_set = set(train_labels)
    intents_without = sorted(all_intents_set - set(intent_to_clusters.keys()))

    print(f"\n【无主导簇的意图】({len(intents_without)} 个):")
    for i in range(0, len(intents_without), 4):
        row = intents_without[i:i+4]
        print("  " + ", ".join(f"{x:<20}" for x in row))


def print_intent_clusters(intent_name):
    """打印指定意图的簇分布"""
    all_intents_set = set(train_labels)

    if intent_name not in all_intents_set:
        print(f"意图 '{intent_name}' 不存在")
        # 模糊匹配
        matches = [i for i in all_intents_set if intent_name.lower() in i.lower()]
        if matches:
            print(f"可能的意图: {matches[:10]}")
        return

    print(f"\n{'='*70}")
    print(f"意图 '{intent_name}' 的簇分布")
    print("="*70)

    # 主导簇
    dominant_clusters = intent_to_clusters.get(intent_name, [])
    if dominant_clusters:
        print(f"\n【主导簇】(该意图是簇的主要意图):")
        for c in dominant_clusters:
            counter = Counter(cluster_to_labels[c])
            total = len(cluster_to_labels[c])
            intent_count = counter.get(intent_name, 0)
            print(f"  簇 #{c}: {intent_count} 个样本, 占簇 {intent_count/total:.1%}")
    else:
        print(f"\n【主导簇】: 无")

    # 所在簇
    all_clusters = intent_to_all_clusters.get(intent_name, [])
    if all_clusters:
        print(f"\n【所有包含该意图的簇】:")
        print(f"  {'簇':>4} {'样本数':>8} {'占比':>8} {'主导意图':>20}")
        print("  " + "-" * 50)
        for c, count, ratio in all_clusters[:10]:
            counter = Counter(cluster_to_labels[c])
            dominant_intent = counter.most_common(1)[0][0]
            print(f"  {c:>4} {count:>8} {ratio:>7.1%} {dominant_intent:>20}")

    # 训练集中该意图的样本数
    total_samples = sum(1 for l in train_labels if l == intent_name)
    print(f"\n训练集中该意图样本数: {total_samples}")


def print_batch_test():
    """批量测试"""
    print("\n批量测试中...")
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        query_emb_red = test_emb_reduced[i:i+1]
        top_indices, _, _, _, _ = retrieve(query_emb, query_emb_red, top_k=1)
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
        query_emb_red = test_emb_reduced[i:i+1]
        top_indices, _, _, _, _ = retrieve(query_emb, query_emb_red, top_k=1)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
            if i in initial_errors:
                errors_fixed += 1
    return correct, errors_fixed


def retest_sample(idx):
    """重新测试样本"""
    query_text = test_texts[idx]
    query_label = test_labels[idx]
    query_emb = test_norm[idx:idx+1]
    query_emb_red = test_emb_reduced[idx:idx+1]

    print(f"\n{'='*60}")
    print(f"重新测试样本 #{idx+1}")
    print("="*60)
    print(f"查询: \"{query_text}\"")
    print(f"正确意图: {query_label}")

    top_indices, top_clusters, ucb_scores, context, arm_idx = retrieve(
        query_emb, query_emb_red, top_k=3
    )

    top1_intent = train_labels[top_indices[0]]
    intent_match = (top1_intent == query_label)

    print(f"\nLinUCB 选择簇: {top_clusters[0]} (UCB: {ucb_scores[0]:.3f})")
    print(f"\nTop-1: [{top1_intent}] {'✓' if intent_match else '✗'}")

    if intent_match:
        print(f"\n✅ 迭代成功!")
    else:
        print(f"\n❌ 仍需优化")


def process_sample(idx):
    """处理单个样本"""
    query_text = test_texts[idx]
    query_label = test_labels[idx]
    query_emb = test_norm[idx:idx+1]
    query_emb_red = test_emb_reduced[idx:idx+1]

    print(f"\n{'='*70}")
    print(f"查询 #{idx+1}")
    print("="*70)
    print(f"问题: \"{query_text}\"")
    print(f"正确意图: {query_label}")

    # 检索
    top_indices, top_clusters, ucb_scores, context, arm_idx = retrieve(
        query_emb, query_emb_red, top_k=3
    )

    print(f"\nLinUCB 选择簇: {top_clusters} (UCB分数: {[f'{s:.3f}' for s in ucb_scores]})")
    print(f"\nTop-3 结果:")

    top1_intent = train_labels[top_indices[0]]
    top1_semantic = np.dot(query_emb.flatten(), train_norm[top_indices[0]])
    intent_match = (top1_intent == query_label)

    for i, idx2 in enumerate(top_indices[:3], 1):
        intent = train_labels[idx2]
        match_mark = "✓" if intent == query_label else "✗"
        sim = np.dot(query_emb.flatten(), train_norm[idx2])
        print(f"\n  {i}. [{intent}] {match_mark} (语义 {sim:.2f})")
        print(f"     \"{train_texts[idx2][:40]}...\"")

    # 判断建议
    print(f"\n{'='*50}")
    print("判断")
    print("="*50)
    print(f"  Top-1 意图匹配: {'✓' if intent_match else '✗'}")
    suggested_score = 1 if intent_match else 0
    print(f"\n  → 建议评分: {suggested_score}")

    # 获取评分
    score_input = input("\n评分 (1/0): ").strip()

    if score_input not in ['1', '0']:
        print("输入无效，跳过")
        return

    score = int(score_input)

    # 获取建议
    print("\n请输入自然语言建议（可选，按Enter跳过）:")
    suggestion = input("建议: ").strip()

    # ===== 核心: 根据反馈更新 LinUCB =====
    if arm_idx is not None and context is not None:
        # 1. 更新当前选择的臂（正反馈奖励1，负反馈奖励0）
        linucb.update(arm_idx, context, score)
        print(f"\n✓ LinUCB 更新当前臂 {arm_idx} (奖励 {score})")

        # 2. 如果是负反馈且有建议，同时更新正确的臂
        if score == 0 and suggestion:
            intent_matches = match_intent_from_keywords(suggestion)
            if intent_matches:
                correct_intent = intent_matches[0][0]

                # 优先使用主导簇，如果没有则使用包含该意图的簇
                correct_cluster_ids = intent_to_clusters.get(correct_intent, [])

                if not correct_cluster_ids:
                    # 没有主导簇，找包含该意图样本的簇
                    cluster_info_list = intent_to_all_clusters.get(correct_intent, [])
                    if cluster_info_list:
                        # 选择样本数最多或占比最高的簇
                        best_cluster = cluster_info_list[0]  # 已按样本数排序
                        correct_cluster_ids = [best_cluster[0]]
                        print(f"  ℹ 意图 '{correct_intent}' 无主导簇，使用簇 #{best_cluster[0]} (样本 {best_cluster[1]}, 占比 {best_cluster[2]:.1%})")

                if correct_cluster_ids:
                    # 找到正确簇对应的臂索引
                    correct_arm_idx = None
                    correct_cluster_id = correct_cluster_ids[0]

                    if correct_cluster_id in cluster_id_to_idx:
                        correct_arm_idx = cluster_id_to_idx[correct_cluster_id]

                    if correct_arm_idx is not None and correct_arm_idx != arm_idx:
                        # 给正确臂正奖励
                        linucb.update(correct_arm_idx, context, 1.0)
                        print(f"✓ LinUCB 更新正确臂 {correct_arm_idx} (簇 #{correct_cluster_id}, 意图 {correct_intent}, 奖励 1.0)")

                        # 记录映射
                        mapping = {
                            "query_text": query_text,
                            "suggestion": suggestion,
                            "correct_intent": correct_intent,
                            "correct_cluster": correct_cluster_id,
                            "correct_arm": correct_arm_idx
                        }
                        query_correct_mapping.append(mapping)
                else:
                    print(f"  ⚠ 意图 '{correct_intent}' 没有对应的簇，无法奖励")

    # 记录反馈
    feedback_record = {
        "query_idx": idx,
        "query_text": query_text,
        "query_intent": query_label,
        "score": score,
        "suggestion": suggestion,
        "selected_arm": int(arm_idx) if arm_idx is not None else None,
        "selected_cluster": top_clusters[0] if top_clusters else None,
        "top1_intent": top1_intent,
        "is_correct": intent_match
    }
    feedback_history.append(feedback_record)

    save_persistence()
    print(f"✓ 反馈已记录")


# ========== 主程序 ==========

if __name__ == "__main__":
    # 加载历史
    print("\n加载持久化数据...")
    has_history = load_persistence()

    if has_history:
        correct, _ = test_current_accuracy([])
        acc = correct / len(test_idx)
        print(f"✓ 历史学习效果: Top-1 = {acc:.1%}")

    # 初始效果
    print("\n初始效果:")
    initial_errors = []
    correct = 0
    for i, query_label in enumerate(test_labels):
        query_emb = test_norm[i:i+1]
        query_emb_red = test_emb_reduced[i:i+1]
        top_indices, _, _, _, _ = retrieve(query_emb, query_emb_red, top_k=1)
        if train_labels[top_indices[0]] == query_label:
            correct += 1
        else:
            initial_errors.append(i)

    initial_acc = correct / len(test_idx)
    print(f"  初始 Top-1: {initial_acc:.1%}")
    print(f"  错误样本数: {len(initial_errors)}")

    # 启动交互
    interactive_mode(initial_errors)

    # 最终统计
    print("\n" + "=" * 80)
    print("最终统计")
    print("="*80)

    correct, errors_fixed = test_current_accuracy(initial_errors)
    final_acc = correct / len(test_idx)

    print(f"\n反馈数: {len(feedback_history)}")
    print(f"初始 Top-1: {initial_acc:.1%}")
    print(f"最终 Top-1: {final_acc:.1%}")
    print(f"变化: {(final_acc - initial_acc) * 100:+.1f}%")
    print(f"\n🎯 错误改善: {errors_fixed}/{len(initial_errors)} ({errors_fixed/len(initial_errors)*100:.1f}%)")

    save_persistence()