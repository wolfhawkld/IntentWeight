# Baseline 选取
# Baseline Selection

**创建时间 / Created**: 2026-04-20
**状态 / Status**: 讨论中

---

## 一、选取原则
## 1. Selection Principles

Baseline 选取需覆盖三个评估维度，每个维度对应不同的对比目标：

| 评估维度 | 对比目标 | 验证的问题 |
|---------|---------|-----------|
| **静态检索质量** | 经典检索方法 + 几何优化方法 | 第一次检索就够好吗？ |
| **自适应能力** | 自适应 RAG 方法 + Bandit RAG | 能否动态调整检索策略？ |
| **在线学习** | 上述所有 baseline（它们都是 flat 的） | 随反馈积累是否持续提升？ |

---

## 二、同类论文的 Baseline 做法
## 2. Baseline Practices in Related Papers

### MBA-RAG (COLING 2025) — Bandit 方法

| Baseline | 类型 | 说明 |
|----------|------|------|
| No-Retrieval | 无检索 | LLM 直接回答 |
| Adaptive-Retrieval | 自适应 | 动态决定是否检索 |
| Self-RAG | 自适应 | 自反思决定检索时机 |
| DRAGIN | 自适应 | Token 不确定性触发检索 |
| SeaKR | 自适应 | 自感知不确定性 |
| Adaptive-RAG | 自适应 | 按 query 复杂度选策略 |

### HypRAG (arXiv 2025) — 几何优化方法

| Baseline | 类型 | 说明 |
|----------|------|------|
| EucBERT | Dense 检索 | 标准欧氏 embedding |
| ModernBERT | Dense 检索 | 最新 Transformer embedding |
| GTE | Dense 检索 | 通用文本 embedding |
| Gemma | Dense 检索 | Google embedding |

### T2-RAGBench (2025) — 检索策略对比

| Baseline | 类型 | 说明 |
|----------|------|------|
| BM25 | 稀疏检索 | 关键词匹配 |
| Dense (BGE/GTE) | 密集检索 | 向量检索 |
| Hybrid (BM25+Dense, RRF) | 混合检索 | 生产级标准 |
| Contextual Retrieval | 增强索引 | LLM 预处理 chunk |
| CRAG | 自适应 | 质量评估 + 纠正 |
| Hybrid + Rerank | 重排序 | Cross-encoder 精排 |

---

## 三、Baseline 候选列表
## 3. Candidate Baseline List

### 第一档：静态检索 Baseline（必须）

验证聚类预筛选和基础检索质量。

| Baseline | 说明 | 优先级 | 实现难度 |
|----------|------|--------|---------|
| **BM25** | 稀疏检索，最低基线 | 必须 | 低 |
| **Dense Retrieval (BGE-large)** | 标准向量检索 | 必须 | 低 |
| **Hybrid (BM25+Dense, RRF)** | 生产级标准做法 | 必须 | 低 |

### 第二档：自适应 RAG Baseline（推荐）

验证动态策略调整能力。

| Baseline | 说明 | 优先级 | 实现难度 |
|----------|------|--------|---------|
| **Self-RAG** | 自反思检索，ICLR 2024 | 推荐 | 中（需要训练好的模型） |
| **CRAG** | 纠正式检索，评估+重检索 | 推荐 | 中 |
| **MBA-RAG** | Bandit 选检索方法，最直接竞争者 | 推荐 | 中（需复现） |

### 第三档：几何优化 Baseline（可选）

定位论文与几何方法的关系（互补而非竞争）。

| Baseline | 说明 | 优先级 | 实现难度 |
|----------|------|--------|---------|
| **HypRAG** | 双曲 embedding 检索 | 可选 | 高（需训练双曲模型） |

### 第四档：消融实验（必须）

验证各组件贡献。

| 配置 | 说明 | 优先级 |
|------|------|--------|
| **Full System** | 完整系统 | 必须 |
| **- 无聚类预筛选** | 去掉聚类，全库检索 | 必须 |
| **- 无在线学习** | 去掉 LinUCB，静态权重 | 必须 |
| **- 无反馈融合** | 仅用显式反馈，去掉隐式+上下文 | 必须 |
| **- 无信誉加权** | 去掉用户信誉防投毒 | 必须 |
| **- 无冷启动先验** | 随机初始化，无关键词先验 | 必须 |

---

## 四、与 MBA-RAG 的关键区别
## 4. Key Differences from MBA-RAG

MBA-RAG 是最直接的竞争者（同为 Bandit + RAG），审稿人一定会对比，需要清晰阐述区别：

| 维度 | MBA-RAG (COLING 2025) | 本方法 |
|------|----------------------|--------|
| **Bandit 的 arm** | 检索方法（none/single/multi-step） | 数据聚类（流形区域） |
| **优化目标** | 选最优检索策略 | 选最优检索区域 |
| **Context 设计** | DistilBERT query encoding | Query PCA + 聚类 reward + 使用比例 (94d) |
| **反馈信号** | Exact Match（单一信号） | 显式+隐式+上下文（多维融合 75/25） |
| **学习方式** | 离线训练 | **在线持续学习** |
| **用户信誉** | 无 | 3 方案协同防投毒 |
| **冷启动** | 需要训练数据 | 关键词先验 + LLM 热启动 |
| **适用场景** | 开放域 QA | 领域特定知识库 |

**互补关系**：MBA-RAG 选"怎么检索"（策略级），我们选"去哪检索"（区域级）。两者可以叠加。

---

## 五、评估协议与 Baseline 的映射
## 5. Evaluation Protocol × Baseline Mapping

### 协议一：静态检索质量（单次）

| Baseline | 协议 | 指标 |
|----------|------|------|
| BM25 | 单次检索，Top-K | Recall@K, MRR, nDCG, RAGAS (F/CR/AR) |
| Dense (BGE) | 同上 | 同上 |
| Hybrid (BM25+Dense) | 同上 | 同上 |
| **本系统 (Round 0)** | 冷启动，无反馈 | 同上 — 与上方 baseline 直接可比 |

### 协议二：自适应能力（按复杂度分组）

| Baseline | 协议 | 指标 |
|----------|------|------|
| Self-RAG | 按 query 类型分组评估 | EM, F1, Acc |
| CRAG | 同上 | 同上 |
| MBA-RAG | 同上 | 同上 + Step (检索次数) |
| **本系统** | 同上 | 同上 |

### 协议三：在线学习曲线（核心差异化）

| Baseline | Round 0 | Round 10 | Round 50 | Round 100 |
|----------|---------|----------|----------|-----------|
| BM25 | x% | x% | x% | x% (flat) |
| Dense | x% | x% | x% | x% (flat) |
| Self-RAG | x% | x% | x% | x% (flat) |
| MBA-RAG | x% | x% | x% | x% (flat 或微升) |
| **本系统** | x% | ↑ | ↑↑ | ↑↑↑ (上升曲线) |

**这是论文最有说服力的实验** — 所有 baseline 都是平线，只有我们的系统有上升曲线。

### 协议四：消融实验

在完整系统上逐一移除组件，观察性能下降：

| 配置 | 相对于 Full System 的下降 |
|------|------------------------|
| Full System | — (基线) |
| - 无聚类 | Δ₁ (聚类贡献) |
| - 无在线学习 | Δ₂ (LinUCB 贡献) |
| - 无反馈融合 | Δ₃ (多维反馈贡献) |
| - 无信誉加权 | Δ₄ (防投毒贡献) |
| - 无冷启动 | Δ₅ (冷启动贡献) |

---

## 六、待确认事项
## 6. Open Questions

1. Self-RAG / CRAG / MBA-RAG 三个自适应 baseline 是否全部需要？还是选其中 1-2 个？
2. HypRAG 是否作为正式 baseline？还是仅在 Related Work 中讨论（定位为互补）？
3. MBA-RAG 的复现是否可行？（代码已开源：github.com/FUTUREEEEEE/MBA）
4. 在线学习曲线的模拟轮次设计

---

*更新时间: 2026-04-20*
