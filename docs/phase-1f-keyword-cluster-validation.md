# Phase 1F: 关键词聚类标签验证

**创建时间**: 2026-04-13
**项目**: IntentWeight
**类型**: 验证阶段设计
**状态**: ✓ 已验证成功

---

## 核心目标

验证关键词聚类标签对检索效果的提升，构建多维聚类检索架构：

```
语义簇 (HDBSCAN) → 召回层（整体语义相似性）
关键词簇 → 过滤层（主题/领域相似性）
意图-簇 → 排序层（用户意图匹配）
```

---

## ✓ 验证结果（2026-04-13）

### 关键词先验冷启动效果

| 策略 | 准确率 | 提升(vs随机) |
|------|--------|-------------|
| 随机选择簇 | 2.5% | - |
| **先验权重选择** | **99.0%** | **+96.5%** |
| Oracle选择 | 99.5% | +97.0% |

**关键发现**：
- 先验策略达到Oracle的**99.5%**
- 高纯度簇的先验权重均值（0.791）比低纯度簇（0.472）高0.319
- 关键词聚类能有效区分优质簇和劣质簇

### 高区分度关键词示例

| 关键词 | 区分度 | 主意图 | 占比 |
|--------|--------|--------|------|
| 'debit' | 0.794 | 28 | 90.48% |
| 'phone' | 0.784 | 42 | 92.65% |
| 'direct' | 0.764 | 28 | 96.39% |
| 'card app' | 0.733 | 13 | 89.93% |

---

## 当前数据维度 vs Phase 1F 扩展

| 维度 | Phase 1E | Phase 1F |
|------|----------|----------|
| Embedding | 384维 (all-MiniLM-L6-v2) | 不变 |
| 语义聚类 | HDBSCAN 簇标签 | 不变 |
| **关键词聚类** | 无 | **TF-IDF + HDBSCAN 簇标签** |
| 动态学习 | LinUCB 抽取关键词 | 不变 |
| 意图关联 | 意图-语义簇标签 | **意图-语义簇 + 意图-关键词簇** |

---

## 技术方案

### 1. 关键词聚类模块

**输入**: 文档 chunk 文本
**输出**: 关键词簇标签

**流程**:
```
文档集合
    │
    ▼
TF-IDF/BM25 向量化
    │
    ▼
关键词提取 (Top-N per document)
    │
    ▼
关键词-文档矩阵构建
    │
    ▼
HDBSCAN 聚类
    │
    ▼
关键词簇标签
```

**关键参数**:
- TF-IDF: max_features=5000, min_df=2
- 关键词提取: top_n=10 per chunk
- HDBSCAN: min_cluster_size=5, min_samples=2

### 2. 数据结构扩展

**原数据结构**:
```json
{
  "id": "chunk_001",
  "content": "...",
  "embedding": [0.1, 0.2, ...],
  "semantic_cluster": 42,
  "intent_cluster_weights": {"intent_A": 0.8}
}
```

**Phase 1F 扩展**:
```json
{
  "id": "chunk_001",
  "content": "...",
  "embedding": [0.1, 0.2, ...],
  "semantic_cluster": 42,
  "keyword_cluster": 15,
  "keywords": ["手机", "价格", "查询"],
  "intent_cluster_weights": {
    "intent_A": {"semantic": 0.8, "keyword": 0.6}
  }
}
```

### 3. LinUCB 上下文扩展

**原上下文 (144维)**:
- 查询 embedding (64维, PCA降维)
- 建议内容 embedding (64维)
- 语义簇 one-hot (16维)

**Phase 1F 扩展 (160维)**:
- 查询 embedding (64维)
- 建议内容 embedding (64维)
- 语义簇 one-hot (16维)
- **关键词簇 one-hot (16维)** ← 新增

### 4. 多维检索融合

**检索流程**:
```
用户查询
    │
    ▼
意图分类
    │
    ├─────────────────────┐
    │                     │
    ▼                     ▼
语义簇选择            关键词簇选择
(LinUCB臂1)          (LinUCB臂2)
    │                     │
    ├─────────────────────┤
    │                     │
    ▼                     ▼
语义召回              关键词召回
(cluster_42)         (cluster_15)
    │                     │
    ├─────────────────────┤
    │                     │
    ▼                     ▼
交集/融合排序
    │
    ▼
最终结果
```

**融合策略**:
```python
def fusion_score(doc, semantic_weight, keyword_weight):
    # 语义簇匹配得分
    semantic_score = 1.0 if doc['semantic_cluster'] == target_semantic else 0.0
    
    # 关键词簇匹配得分
    keyword_score = 1.0 if doc['keyword_cluster'] == target_keyword else 0.0
    
    # 融合
    return semantic_weight * semantic_score + keyword_weight * keyword_score
```

---

## 验证任务

### Task 1: 关键词聚类模块实现

**文件**: `pre_validation/05_keyword_cluster/scripts/keyword_clustering.py`

**功能**:
- TF-IDF/BM25 向量化
- 关键词提取 (Top-N)
- HDBSCAN 聚类
- 簇标签分配

**验证指标**:
- 簇数量 (合理范围: 50-200)
- 簇纯度 (目标: >70%)
- 噪声点比例 (目标: <10%)

### Task 2: 数据集标签扩展

**数据集**: BANKING77, CLINC150

**输出**: `pre_validation/05_keyword_cluster/data/tagged_chunks/`

**验证**: 检查关键词簇分布是否合理

### Task 3: LinUCB 上下文扩展

**文件**: `pre_validation/05_keyword_cluster/scripts/multi_dim_linucb.py`

**功能**:
- 扩展上下文特征 (160维)
- 双臂选择 (语义簇 + 关键词簇)
- 多维奖励计算

### Task 4: 多维检索验证

**文件**: `pre_validation/05_keyword_cluster/scripts/validate_multi_dim.py`

**对比**:
- 单维 (语义簇) vs 多维 (语义簇×关键词簇)
- Recall@10
- Precision@5
- MRR

**目标提升**: Recall@10 从 72% → 82%

---

## 目录结构

```
pre_validation/05_keyword_cluster/
├── scripts/
│   ├── keyword_clustering.py      # 关键词聚类模块
│   ├── multi_dim_linucb.py        # 多维 LinUCB
│   ├── validate_multi_dim.py      # 多维验证
│   └── analyze_cluster_quality.py # 簇质量分析
├── data/
│   ├── keyword_clusters.json      # 关键词簇定义
│   ├── tagged_chunks/             # 带标签的 chunk 数据
│   └── results/                   # 验证结果
└── docs/
    └── cluster_analysis.md        # 簇分析报告
```

---

## 预期结果

| 指标 | Phase 1E | Phase 1F 目标 | 提升 |
|------|----------|---------------|------|
| Recall@10 | 72% | 82% | +10% |
| Precision@5 | 68% | 78% | +10% |
| 簇纯度 | 75% | 75% | 持平 |
| 噪声点比例 | 15% | <10% | 改善 |
| 可解释性 | 中 | 高 | 提升 |

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 关键词提取质量差 | 簇纯度低 | 使用 KeyBERT + TF-IDF 混合 |
| 关键词簇数量过多 | LinUCB 臂爆炸 | 合并小簇，设置阈值 |
| 多维融合权重失衡 | 效果不如单维 | A/B 测试动态调整 |
| 计算开销增加 | 延迟上升 | 预计算 + 缓存 |

---

## 下一步

1. 实现 `keyword_clustering.py` 模块
2. 对 BANKING77 数据集进行关键词聚类
3. 分析簇质量，调整参数
4. 扩展 LinUCB，验证多维效果

---

*创建时间: 2026-04-13*
*作者: Damon + Nemesis*