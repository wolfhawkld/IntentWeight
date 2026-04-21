# 数据集选取
# Dataset Selection

**创建时间 / Created**: 2026-04-20
**更新时间 / Updated**: 2026-04-21
**状态 / Status**: 讨论中

---

## 一、选取原则
## 1. Selection Principles

### 论文核心 Claim

> 在固定的语义流形上，通过 LinUCB 在线导航 + 多维反馈闭环，持续优化 RAG 检索。
> 无需重训 embedding，无需 GPU，从用户交互中持续自进化。

### 数据集需求

论文实验需要回答三个问题，数据集选取围绕这三个问题展开：

1. **聚类预筛选是否有效？** — 搜索空间缩减 95%，精度不降或提升
2. **LinUCB 在线学习是否优于静态方法？** — 随交互次数增加，精度持续上升
3. **各组件的贡献如何？** — 消融实验

### 选取标准

- **领域特定**：本系统面向闭域 RAG（企业知识库），数据集应为领域特定语料而非开放域 QA
- **对齐同类论文**：参考 HypRAG (arXiv:2602.07739) 的数据集选取，该论文同为领域特定 RAG 检索优化
- **可模拟在线学习**：数据集需支持将 test set 按序处理，模拟多轮用户交互和反馈
- **跨领域验证**：覆盖多个垂直领域，证明方法的通用性

---

## 二、参考论文的数据集选取
## 2. Dataset Selection in Reference Papers

### HypRAG (arXiv:2602.07739, 2025) — 主要参考

HypRAG 使用 RAGAS 基准中的 5 个领域特定数据集，评估闭域 RAG 检索质量：

| 数据集 | 领域 | 特点 | 规模 | 评估指标 |
|--------|------|------|------|---------|
| **CovidQA** | 生物医学 | 基于 CORD-19 语料的医学文档 QA | **仅 124 QA pairs** | F / CR / AR |
| **CUAD** | 法律合同 | 合同条款理解与检索 | 中等 | F / CR / AR |
| **eManual** | 产品手册 | 技术文档检索 | 中等 | F / CR / AR |
| **DelucionQA** | 误导信息检测 | 带噪声的 QA | 中等 | F / CR / AR |
| **ExpertQA** | 专家知识 | 跨领域专业 QA | 中等 | F / CR / AR |

> **⚠️ CovidQA 规模问题**：CovidQA (Tang et al., 2020) 仅 124 个 QA pairs，
> 扩展版 COVID-QA (Möller et al., 2020) 也仅 2,019 对。
> 对于展示在线学习曲线，样本量可能不足。建议替换为 PubMedQA 或 RAGBench 医学子集。

RAGAS 三维度指标：
- **Faithfulness (F)**：答案是否基于检索到的内容
- **Context Relevance (CR)**：检索的上下文是否相关
- **Answer Relevance (AR)**：答案是否回答了问题

HypRAG 的 baselines：EucBERT, ModernBERT, GTE, Gemma 等 embedding 模型。

**适合参考的原因**：
1. 领域特定 RAG，非开放域 QA — 与我们的系统定位一致
2. 在有限语料库上评估检索质量 — 匹配我们的聚类+导航场景
3. RAGAS 指标是 RAG 评估的标准框架 — 审稿人认可度高

### RAGBench (arXiv:2407.11005, 2024) — 补充参考

RAGBench 是 100K 规模的跨领域 RAG 基准，覆盖 5 个行业垂直领域，配合 TRACe 评估框架：

| 子集 | 领域 | 特点 |
|------|------|------|
| **eManual** | 产品手册 | 同 HypRAG 使用的数据集 |
| **TechQA** | 技术支持 | IBM 技术文档 QA |
| **CUAD** | 法律合同 | 同 HypRAG 使用的数据集 |
| **PubMedQA / CovidQA** | 生物医学 | 医学文献，规模大于独立 CovidQA |
| **FinQA / TAT-QA** | 金融 | 数值推理型 QA |

**相比 HypRAG 数据集的优势**：
1. 规模更大（100K），足以支撑在线学习曲线展示
2. 与 HypRAG 有交集（eManual, CUAD），结果可间接对比
3. 标准化评估框架 TRACe（Utility, Relevance, Adherence, Completeness）

### MBA-RAG (COLING 2025) — Bandit 方法参考

MBA-RAG 使用 Adaptive-RAG 的标准 QA 数据集：

| 类型 | 数据集 | 特点 |
|------|--------|------|
| Single-hop | PopQA, TriviaQA, Natural Questions | 开放域，Wikipedia 语料 |
| Multi-hop | HotpotQA, MuSiQue, 2WikiMultiHopQA | 多跳推理 |

**不直接采用的原因**：
- 开放域 QA 以 Wikipedia 为语料，无法体现聚类预筛选的价值
- 单次 query-answer 场景，无法展示在线学习优势
- 但 MBA-RAG 的评估指标（EM, F1, Acc, Step）值得参考

### 其他参考

| 论文 | 会议 | 数据集 | 备注 |
|------|------|--------|------|
| Self-RAG | ICLR 2024 | PopQA, PubHealth, ARC, TriviaQA | 开放域 |
| CRAG | 2024 | 4,409 QA pairs + Mock APIs | 自有基准 |
| AutoRAG-HP | EMNLP 2024 | ALCE-ASQA, NQ | 开放域 |
| HyperbolicRAG | arXiv 2025 | NQ, PopQA, MuSiQue, 2Wiki, HotpotQA | 开放域 |
| RAGBench | 2024 | 100K examples, 5 industry domains | 大规模跨域 |

---

## 三、已有数据集资产
## 3. Existing Dataset Assets

### IntentWeight pre_validation 数据集

| 数据集 | 样本数 | 语言 | 领域 | 用于论文 | 备注 |
|--------|--------|------|------|---------|------|
| **BANKING77** | 13,083 | 英文 | 银行 | 待定 | 77 intent, 聚类纯度 95%, Top-1 +5.8% |
| **CLINC150** | 23,850 | 英文 | 多领域 | 待定 | 151 intent, Top-1 +5.6% |
| DailyDialog | 11,499 | 英文 | 日常对话 | 不用 | 非 RAG 场景 |
| CMID | 12,254 | 中文 | 医疗 | 不用 | 分类体系有问题(已验证) |
| **SMP2019** | 2,579 | 中文 | 多领域 | 待定 | 48 intent, BGE 聚类纯度 88.4% |
| **JQ 企业数据** | 2,623 chunks | 中文 | 企业运营 | E2E 案例 | 真实场景，110 docs |

### jq_kg_base 工程验证数据

- 110 docs → 2,623 chunks
- Azure 3072d + 腾讯 4096d 双平台
- 15 clusters (Azure) / 16 clusters (腾讯)
- PCA 方差保留 99.1%
- 105 次反馈记录

---

## 四、数据集选取方案（待讨论）
## 4. Dataset Selection Plan (To Be Discussed)

### 方案：HypRAG 对齐 + 已有数据集补充

**策略：HypRAG 对齐 + RAGBench 补充 + 已有数据集**

从 HypRAG 和 RAGBench 中选取领域特定数据集：

| 数据集 | 来源 | 是否选用 | 理由 |
|--------|------|---------|------|
| **eManual** | HypRAG + RAGBench | 推荐 | 产品手册，最接近企业知识库场景 |
| **CUAD** | HypRAG + RAGBench | 推荐 | 法律合同，文档结构化强，适合聚类 |
| **PubMedQA** | RAGBench | 推荐 | 替代 CovidQA（规模更大），医学领域 |
| **TechQA** | RAGBench | 可选 | IBM 技术支持，补充技术领域覆盖 |
| CovidQA | HypRAG | 不推荐 | 仅 124 pairs，太小，不足以展示在线学习曲线 |
| DelucionQA | HypRAG | 不推荐 | 侧重误导检测，与系统定位偏离 |
| ExpertQA | HypRAG | 可选 | 跨领域专家知识 |

**已有数据集（展示完整故事）：**

| 数据集 | 用途 | 理由 |
|--------|------|------|
| **BANKING77** | 聚类质量 + 检索优化 | 已有完整实验数据，聚类效果最好 |
| **JQ 企业数据** | E2E 系统验证 | 真实场景，system paper 必备 |

### 评估维度与数据集映射

| 评估维度 | 数据集 | 协议 |
|---------|--------|------|
| **静态检索质量** | eManual, CUAD, PubMedQA (+ BANKING77) | 单次检索, RAGAS 指标 (F/CR/AR) |
| **自适应能力** | 同上 | 按 query 复杂度分组 |
| **在线学习曲线** | 同上 | 多轮模拟, learning curve |
| **聚类有效性** | BANKING77, CLINC150 | 纯度, 搜索空间缩减比 |
| **端到端系统** | JQ 企业数据 | 全链路验证 |

---

## 五、与 HypRAG 数据集对齐的注意事项
## 5. Notes on Aligning with HypRAG Datasets

### 协议差异

HypRAG 评估的是**单次检索质量（静态）**— 不同 embedding 模型在相同数据集上的检索效果。

本系统的核心优势是**多轮交互后的在线学习提升**，因此评估协议需要扩展：

1. **Round 0**：冷启动（关键词先验），与 HypRAG baseline 直接可比
2. **Round 1-N**：模拟用户反馈，展示 LinUCB learning curve
3. **收敛分析**：多少轮反馈后达到稳态

### 反馈模拟策略

在标准数据集上模拟用户反馈的方式：
- 检索到的 chunk 包含 ground truth 答案 → reward = 0.8 (like + copy)
- 检索到的 chunk 不包含答案 → reward = 0.2 (dislike)
- 随机添加隐式信号噪声模拟真实场景

---

## 六、待确认事项
## 6. Open Questions

1. ~~HypRAG 的 5 个数据集中具体选哪几个？~~ → 建议 eManual + CUAD + PubMedQA（替代 CovidQA）
2. BANKING77/CLINC150 是否同时保留？还是只保留 BANKING77？
3. 是否需要中文数据集？（SMP2019 vs 只用 JQ 企业数据）
4. 在线学习的模拟轮次设计（50 轮？100 轮？）
5. RAGBench vs HypRAG 原始数据集？（RAGBench 规模更大，但 HypRAG 结果可直接对比）
6. 是否加入 TechQA（IBM 技术支持）作为第四个标准数据集？

---

*更新时间: 2026-04-21*
