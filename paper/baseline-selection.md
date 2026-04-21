# Baseline 选取
# Baseline Selection

**创建时间 / Created**: 2026-04-20
**更新时间 / Updated**: 2026-04-21
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
| **CRAG** | 纠正式检索，评估+重检索 | 推荐 | 中 |
| **MBA-RAG** | Bandit 选检索方法，COLING 2025 | 推荐 | 中（代码已开源） |
| Self-RAG | 自反思检索，ICLR 2024 | 可选 | 中（与 CRAG 功能重叠） |

### 第三档：在线学习 / 反馈驱动 RAG Baseline（必须）

> **2026-04-21 新增**：经 double check 发现三个直接涉及在线学习/反馈驱动 RAG 优化的方法，
> 昨天的分析中遗漏了这一层。这是与我们最直接可比的竞争者。

| Baseline | 说明 | 优先级 | 实现难度 |
|----------|------|--------|---------|
| **DynamicRAG** | RL 优化 reranker，动态选择和排序文档 (Sun et al., 2025) | 必须 | 中 |
| **Online-Optimized RAG** | 在线梯度更新 retrieval embedding (ICLR 2026 投稿) | 必须 | 高（需复现） |
| **FLAIR** | 用户/合成反馈驱动的双轨 re-ranking (Zhang et al., 2025) | 推荐 | 中 |

**为什么这一层至关重要**：
- 昨天我们认为"在线学习 RAG 几乎空白"，实际上已有 3 个相关工作
- 审稿人很可能知道这些工作，不比较会被质疑 novelty
- 但我们的差异化依然成立（见下方第五节对比表）

### 第四档：几何优化 Baseline（可选）

定位论文与几何方法的关系（互补而非竞争）。

| Baseline | 说明 | 优先级 | 实现难度 |
|----------|------|--------|---------|
| **HypRAG** | 双曲 embedding 检索 | 可选 | 高（需训练双曲模型） |

### 第五档：消融实验（必须）

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

## 四、与关键竞争者的差异化分析
## 4. Differentiation from Key Competitors

### 4.1 与 MBA-RAG 的区别（Bandit 方法层面）

MBA-RAG 是 Bandit + RAG 的直接竞争者，审稿人一定会对比：

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

### 4.2 与在线学习 RAG 方法的全面对比（2026-04-21 新增）

> 这是论文 Related Work 和实验部分的核心对比表，审稿人最关注。

| 维度 | Online-Opt RAG | DynamicRAG | FLAIR | **本方法** |
|------|----------------|------------|-------|-----------|
| **优化对象** | Retrieval embedding | Reranker 排序 | Re-ranking scores | **聚类导航策略** |
| **是否改变流形** | 是（修改 embedding） | 否 | 否 | **否（固定流形 + 价值场）** |
| **学习算法** | Online gradient descent | RL (PPO) | Scoring function | **LinUCB Contextual Bandit** |
| **反馈信号** | Binary (solved/unsolved) | RL reward | Feedback indicators | **多维融合（显式+隐式+上下文）** |
| **反馈质量控制** | 无 | 无 | 无 | **用户信誉 3 方案协同** |
| **冷启动** | 需预训练 embedding | 需训练数据 | 需数据 | **关键词先验 + LLM 热启动** |
| **知识沉淀** | 无 | 无 | 无 | **Insight 提取（别名/纠正/知识缺口）** |
| **搜索空间缩减** | 无 | 无（全库排序） | 无 | **聚类预筛选，缩减 95%** |
| **理论框架** | 无 | 无 | 无 | **DVM 动态价值流形** |
| **部署要求** | GPU（梯度更新） | GPU（RL 训练） | 中等 | **CPU 即可** |

**核心差异化总结**：
1. **优化维度不同**：它们优化"检索什么/排什么序"，我们优化"去哪个区域检索"
2. **流形不变性**：Online-Opt RAG 修改 embedding（改变流形），我们保持流形固定，仅学习价值分布
3. **反馈丰富度**：其他方法用单一信号，我们融合显式+隐式+上下文三层信号
4. **防护机制**：我们是唯一有用户信誉防投毒的方法
5. **理论贡献**：DVM 概念为所有组件提供统一解释框架

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

| Baseline | Round 0 | Round 10 | Round 50 | Round 100 | 曲线形态 |
|----------|---------|----------|----------|-----------|---------|
| BM25 | x% | x% | x% | x% | flat |
| Dense | x% | x% | x% | x% | flat |
| CRAG | x% | x% | x% | x% | flat |
| MBA-RAG | x% | x% | x% | x% | flat（离线训练，不随反馈变） |
| DynamicRAG | x% | ↑? | ↑? | ↑? | 可能微升（RL 有在线成分） |
| Online-Opt RAG | x% | ↑ | ↑ | ↑ | 上升（在线梯度更新） |
| FLAIR | x% | ↑? | ↑? | ↑? | 可能微升（有反馈成分） |
| **本系统** | x% | ↑ | ↑↑ | ↑↑↑ | **上升最快（LinUCB + 冷启动先验）** |

**这是论文最有说服力的实验**：
- 静态方法（BM25/Dense/CRAG/MBA-RAG）都是平线
- Online-Opt RAG 和 FLAIR 可能有上升，但我们预期上升更快（冷启动先验 + 丰富反馈信号）
- 即使其他在线方法也上升，我们的差异化在于：起点更高（冷启动）、上升更快（多维反馈）、更鲁棒（信誉防投毒）

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

## 七、论文定位的修正
## 7. Corrected Paper Positioning

### 修正前（2026-04-20）

> "在线学习 RAG 领域几乎空白，本项目填补了这个缺口。"

### 修正后（2026-04-21）

> "已有少量工作探索在线学习/反馈驱动的 RAG 优化（DynamicRAG, Online-Opt RAG, FLAIR），
> 但这些方法要么修改 embedding（破坏流形稳定性），要么仅优化排序（不缩减搜索空间），
> 且均缺乏反馈质量控制和冷启动机制。
>
> 本方法首次提出在固定流形上通过 Contextual Bandit 学习导航策略，
> 结合多维反馈融合、用户信誉防投毒和零数据冷启动，
> 实现搜索空间 95% 缩减的同时持续提升检索精度。"

---

## 八、待确认事项
## 8. Open Questions

1. ~~Self-RAG / CRAG / MBA-RAG 三个是否全部需要？~~ → CRAG + MBA-RAG（Self-RAG 降为可选）
2. HypRAG 是否作为正式 baseline？还是仅在 Related Work 中讨论？
3. MBA-RAG 复现：代码已开源 (github.com/FUTUREEEEEE/MBA)
4. **DynamicRAG 和 Online-Optimized RAG 的复现可行性需评估**
5. FLAIR 是否作为正式 baseline？还是仅在 Related Work 中讨论？
6. 在线学习曲线的模拟轮次设计（需要足够轮次让各方法的差异显现）

---

*更新时间: 2026-04-21*
