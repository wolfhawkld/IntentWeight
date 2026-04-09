# LinUCB 在 RAG 场景的收敛性分析

**创建时间**: 2026-04-10
**项目**: IntentWeight
**类型**: 理论分析
**状态**: 架构约束验证

---

## 核心问题

随着用户使用和反馈的增加，LinUCB 模型是否会无限增长？

**结论：不会。RAG 系统的可回答范围决定了模型的规模上限。**

---

## 关键洞察

```
知识库大小固定
    ↓
可回答问题范围有上限
    ↓
用户查询词汇空间收敛
    ↓
关键词空间有上限
    ↓
LinUCB 参数量有界
```

---

## 与传统推荐系统的关键区别

| 维度 | 传统推荐系统 | IntentWeight (RAG) |
|------|-------------|-------------------|
| **用户空间** | 无限增长（新用户持续加入） | 有限（单一用户或小群体） |
| **物品空间** | 无限增长（新商品/内容） | **有限**（知识库固定） |
| **Arm 空间** | 用户数 × 物品数 → 无限 | 关键词组合 → **有上限** |
| **模型增长** | 线性/指数增长 | **收敛到稳态** |

---

## 关键词空间的上限分析

### 各层词汇来源及规模

**L1 核心关键词**：

```
来源 = 用户查询中的词汇
上限 = 知识库覆盖的词汇量

假设: 10万篇文档，平均1000词/篇
去重后词汇量 ≈ 5-10万词
实际高频关键词 ≈ 1-2万词
```

**L2 上位扩展**：

```
来源 = HowNet/WordNet 概念层级
上限 = 本体概念数量

HowNet 概念量 ≈ 10万+
实际使用的高层概念 ≈ 5000-10000
```

**L3 下位扩展**：

```
来源 = KG实例 + 领域术语
上限 = 领域实体数量

具体领域实体 ≈ 1-10万
实际高频实体 ≈ 5000-20000
```

### 总规模估算

```
总关键词空间 = L1 ∪ L2 ∪ L3
            ≈ 1-2万 (L1) + 0.5-1万 (L2) + 0.5-2万 (L3)
            ≈ 2-5万 词

LinUCB 参数量 = d (特征维度) × K (关键词数)
             ≈ 1000 × 50000 = 50M 参数 ≈ 200MB

结论：完全可控！
```

---

## 收敛过程

### 三阶段演化

```
阶段1: 冷启动期
├── 关键词快速增加
├── 权重波动大
└── 参数量增长

阶段2: 学习期
├── 常见关键词覆盖完成
├── 权重逐渐稳定
└── 参数量增速下降

阶段3: 稳态期
├── 新关键词边际效益递减
├── 权重收敛
└── 参数量稳定（仅微调）
```

### 收敛条件

当满足以下条件时，模型进入稳态：

| 条件 | 阈值 | 说明 |
|------|------|------|
| **词汇覆盖** | 90%+ | 查询可被已有关键词覆盖 |
| **权重稳定** | 方差 < 0.01 | 各关键词权重变化小 |
| **反馈饱和** | 改变量 < 0.001 | 新反馈对权重的边际效应低 |

### 收敛示意图

```
          │
    参数量 │     ┌───────────── 稳态上限
          │    ╱
          │   ╱
          │  ╱  学习期
          │ ╱
          │╱ 冷启动
          └───────────────────────→
               时间/用户反馈量
```

---

## 实际约束验证

### 知识库 → 词汇空间的映射

```
知识库规模          预估词汇空间        模型参数量
─────────────────────────────────────────────────
1万篇文档      →    5000-10000词    →   ~50MB
10万篇文档     →    1-2万词         →   ~100MB
100万篇文档    →    2-5万词         →   ~200MB
1000万篇文档   →    5-10万词        →   ~500MB
```

**关键发现**：
- 文档数量增长 10 倍 → 词汇量增长约 2 倍（对数关系）
- 原因：词汇有边际递减效应，高频词在早期就覆盖了

---

## 稳态维护策略

### 增量更新

```python
def incremental_update(new_query, feedback):
    """稳态后的增量更新"""
    
    # 1. 检查是否为新关键词
    if is_new_keyword(new_query):
        # 新增 arm，但频率很低
        add_keyword_arm(new_query)
    
    # 2. 更新权重（仅涉及相关 arm）
    update_weights(new_query, feedback)
    
    # 3. 周期性剪枝（移除低效 arm）
    if periodic_prune():
        remove_low_utility_arms(threshold=0.001)
```

### 剪枝策略

```python
def prune_arms(model, threshold=0.01, min_samples=10):
    """移除低效用关键词 Arm"""
    
    # 统计各 arm 的使用频率和收益
    arm_stats = analyze_arm_performance(model)
    
    # 移除条件：
    # 1. 使用频率低（样本数 < min_samples）
    # 2. 平均收益低（低于 threshold）
    low_utility_arms = [
        arm for arm, stats in arm_stats.items()
        if stats['count'] < min_samples or 
           stats['avg_reward'] < threshold
    ]
    
    # 保留 L1 核心关键词（不剪枝）
    for arm in low_utility_arms:
        if arm not in model.l1_keywords:
            model.remove_arm(arm)
```

---

## 降维优化（可选）

即使关键词空间达到上限，也可以通过降维进一步压缩：

### 方法1：关键词 Embedding 聚类

```python
# 原方案：每个关键词一个 arm
n_arms = len(all_keywords)  # 可能达到数万

# 优化方案：关键词 embedding 聚类
keyword_embs = encode(keywords)
cluster_centers = kmeans(keyword_embs, k=1000)  # 聚类到1000个中心

# 每个 cluster 一个 arm
n_arms = 1000  # 大幅压缩

# 预测时：新关键词 → 最近 cluster → 对应 arm
def predict(new_keyword):
    emb = encode(new_keyword)
    cluster = nearest_cluster(emb, cluster_centers)
    return linucb.predict(cluster)
```

### 方法2：Neural Linear Bandit

```python
class NeuralLinearBandit:
    """用神经网络学习固定维度特征表示"""
    
    def __init__(self, input_dim, hidden_dim, output_dim):
        self.encoder = MLP(input_dim, hidden_dim, output_dim)
        self.linucb = LinUCB(output_dim, n_arms)
    
    def forward(self, context, keywords):
        # 将变长关键词编码为固定维度特征
        features = self.encoder(context, keywords)
        return self.linucb.predict(features)
    
    def update(self, context, keywords, arm, reward):
        features = self.encoder(context, keywords)
        self.linucb.update(features, arm, reward)
```

**优势**：
- 输入维度固定，不受关键词数量影响
- 神经网络可学习语义相似性
- 新关键词无需新增 arm

---

## 业务增长匹配

```
业务规模增长 → 知识库扩展 → 词汇空间增长 → 模型扩容
                      ↑
                 同步增长，可控
```

| 业务阶段 | 知识库规模 | 词汇空间 | 模型大小 | 更新频率 |
|----------|-----------|----------|----------|----------|
| 初创期 | 1万篇 | 5000词 | ~50MB | 每日增量 |
| 成长期 | 10万篇 | 1-2万词 | ~100MB | 每周增量 |
| 成熟期 | 50万篇 | 2-3万词 | ~150MB | 每月增量 |
| 稳定期 | 100万篇+ | 3-5万词 | ~200MB | 季度微调 |

---

## 总结

| 问题 | 答案 |
|------|------|
| **模型会无限增长吗？** | 不会，知识库有界 → 模型有界 |
| **参数量上限是多少？** | 约 2-5 万关键词 → 200MB 级别 |
| **会收敛吗？** | 会，反馈足够后权重稳定 |
| **维护成本？** | 稳态后仅需增量更新 + 周期剪枝 |
| **如何进一步压缩？** | Embedding 聚类 / Neural Linear Bandit |

---

## 核心洞察

> RAG 系统的可回答范围决定了 LinUCB 模型的规模上限。
> 
> 这是一个**自约束系统**，不会像传统推荐系统那样无限膨胀。

**关键原因**：
1. 知识库固定 → 可回答问题有限
2. 用户查询会收敛到知识库覆盖范围
3. 关键词空间随知识库规模对数增长
4. 反馈信号在稳态后边际效益递减

---

## 参考

- 分层关键词设计: `insight-hierarchical-keyword-expansion.md`
- 策略对比: `analysis-clustering-vs-hierarchical-keywords.md`
- LinUCB 实现: `../src/core/linucb.py`

---

*文档创建: 2026-04-10*
*版本: v1.0*
*作者: Damon + Nemo*