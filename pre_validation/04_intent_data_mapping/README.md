# Phase 1D: 意图-数据聚类关联验证

**目标**: 验证用户问题的意图能否正确映射到相关数据簇

---

## 与 Phase 1 的关系

本模块是 Phase 1 的第四个子阶段：

| 模块 | 内容 | 状态 |
|------|------|------|
| 01_intent_clustering | 意图聚类验证 | ✅ 完成 |
| 02_speech_act | Speech Act 分类 | ✅ 完成 |
| 03_feedback_signal | 反馈信号 + Bandit | ✅ 完成 |
| **04_intent_data_mapping** | **意图-数据关联** | 📋 进行中 |

---

## 实验设计

### 数据来源

使用 Phase 1 已验证的数据集：

| 数据集 | Train (知识库) | Test (问题) | 意图类别 |
|--------|----------------|-------------|----------|
| BANKING77 | 9,003 | 3,080 | 77 |
| CLINC150 | 22,500 | 1,350 | 150 |

### 实验流程

```
┌─────────────────────────────────────────────────────┐
│ Step 1: 构建知识库                                   │
│   Train 样本 → Embedding → 聚类 → 数据簇             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: 问题意图识别                                 │
│   Test 问题 → Speech Act 分类 + 簇识别               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: 召回与评估                                   │
│   问题 → 预测簇 → 语义检索 → Top-K 结果              │
│   对比 ground truth 计算准确率                       │
└─────────────────────────────────────────────────────┘
```

---

## 对比实验

| 方案 | 召回范围 | 描述 |
|------|----------|------|
| **基线: 纯语义检索** | 100% | 无筛选，直接语义检索 |
| **方案A: 纯簇筛选** | ~5% | 先识别簇，簇内检索 |
| **方案B: 融合方案** | ~5% | 簇筛选 + Bandit 精排 |

---

## 评估指标

| 指标 | 公式 | 说明 |
|------|------|------|
| **簇召回率** | 正确簇被召回的比例 | 意图-簇关联准确性 |
| **Top-K 准确率** | Top-K 中包含正确答案 | 最终召回质量 |
| **筛选效率** | 召回数据量 / 总数据量 | 召回效率 |
| **MRR** | 正确答案排名倒数均值 | 排序质量 |

---

## 运行方式

```bash
# 激活环境
cd ~/.openclaw/workspace/IntentWeight
source .venv/bin/activate

# Step 1: 构建知识库
python phase2_intent_data_mapping/scripts/build_knowledge_base.py --dataset banking77

# Step 2: 聚类
python phase2_intent_data_mapping/scripts/cluster_chunks.py --dataset banking77

# Step 3: 评估
python phase2_intent_data_mapping/scripts/evaluate_mapping.py --dataset banking77

# Step 4: 对比实验
python phase2_intent_data_mapping/scripts/compare_methods.py --dataset banking77
```

---

## 预期结果

| 方案 | Top-1 准确率 | Top-5 准确率 | 召回范围 |
|------|-------------|-------------|----------|
| 纯语义检索 | ~85% | ~95% | 100% |
| 纯簇筛选 | ~75% | ~90% | ~5% |
| **融合方案** | ~90% | ~97% | ~5% |

---

## 文件结构

```
phase2_intent_data_mapping/
├── README.md
├── scripts/
│   ├── build_knowledge_base.py    # 构建知识库
│   ├── cluster_chunks.py          # Chunk 聚类
│   ├── evaluate_mapping.py        # 评估意图-簇关联
│   └── compare_methods.py         # 对比实验
├── configs/
│   └── experiment_config.yaml     # 实验配置
└── results/                       # 实验结果
```

---

*创建时间: 2026-04-06*