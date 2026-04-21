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
- **具备 Ground Truth**：数据集必须有可靠的 GT 用于反馈模拟（详见第五节）

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

---

## 四、主流垂类 RAG 数据集全景分析
## 4. Comprehensive Analysis of Domain-Specific RAG Datasets

> 2026-04-21 更新：扩大调研范围，覆盖 FinQA、BioASQ、MIRAGE、RAGCare-QA、LegalQA、CRAG、RAGEval、DragonBench 等。

### 4.1 全部候选数据集一览

| 数据集 | 领域 | 规模 | 检索级 GT | 答案级 GT | 开源 | 来源论文/会议 |
|--------|------|------|----------|----------|------|-------------|
| **CUAD** | 法律合同 | 510 合同, 13K+ 标注, 41 类 | **有** — 段落级标注 | **有** | 已开源 (HuggingFace) | NeurIPS 2021 |
| **eManual** | 产品手册 | 中等 | **有** — RAGBench 提供 QA-chunk 映射 | **有** | 已开源 (RAGBench) | RAGBench 2024 |
| **PubMedQA** | 生物医学 | 1K 标注 + 61.2K 未标注 + 211.3K 生成 | **部分** — context 即摘要 | **有** — yes/no/maybe | 已开源 (HuggingFace) | EMNLP 2019 |
| **BioASQ** | 生物医学 | 4,721 问题, 语料库 40K+ 段落 | **有** — 相关文档+snippet 标注 | **有** — 精确答案+理想答案 | 已开源 | BioASQ Challenge (持续更新) |
| **MIRAGE** | 医学综合 | 7,663 问题 (含 PubMedQA + BioASQ) | 间接 — 通过子数据集 | **有** | 已开源 (MedRAG toolkit) | arXiv 2024 |
| **FinQA** | 金融 | 8K QA pairs, 2.8K 财报 | 无 — 数值推理为主 | **有** — 计算结果 | 已开源 (HuggingFace) | EMNLP 2021 |
| **LegalBench-RAG** | 法律综合 | 含 CUAD + MAUD + ContractNLI + PrivacyQA | **有** — 字符级精确标注 | **有** | 已开源 | NLLP 2025 |
| **CRAG** | 多领域(5) | 4,409 QA pairs + Mock APIs | 无 — 动态答案 | **有** — 人工验证 | 已开源 | NeurIPS 2024 / KDD Cup 2024 |
| **RAGEval** | 可定制(7 领域) | 生成式框架, 2,100+ 评估 queries | 按生成方式决定 | **有** | 已开源 | ACL 2025 |
| **RAGCare-QA** | 医学教育 | 419 问题, 5 类 | 有 — 页面级引用 | **有** — 多选题 | 已开源 (CC BY 4.0) | medRxiv 2025 |
| CovidQA | 生物医学 | **仅 124 pairs** | 无 | 有 | 已开源 | NLP-COVID 2020 |
| DragonBench/DRAGON | 新闻 | 动态更新 | 有 | 有 | 已开源 | EACL 2026 |

### 4.2 适合度分析（按我们的实验需求）

我们的实验需要数据集满足三个条件：
1. **领域特定闭域语料** — 适合聚类预筛选
2. **有 GT 用于反馈模拟** — 支持在线学习实验
3. **足够规模** — 支持 learning curve 展示

| 数据集 | 闭域语料 | GT 可靠度 | 规模 | 综合适合度 | 说明 |
|--------|---------|----------|------|-----------|------|
| **CUAD** | 优（510 合同） | 最高（段落级） | 中 | ⭐⭐⭐ | 文档结构化，聚类效果好 |
| **eManual** | 优（产品手册） | 高（chunk 映射） | 中 | ⭐⭐⭐ | 最接近企业知识库 |
| **PubMedQA** | 优（PubMed 文献） | 中高（摘要即 context） | 大（211K+） | ⭐⭐⭐ | 规模大，医学领域权威 |
| **BioASQ** | 优（PubMed 文献） | 高（文档+snippet 标注） | 中（4.7K 问题） | ⭐⭐⭐ | GT 最完整的医学数据集 |
| **BANKING77** | 优（银行意图） | 中（间接 GT） | 中（13K） | ⭐⭐ | 已有实验基础 |
| **CRAG** | 中（5 领域混合） | 中（人工验证答案，无检索 GT） | 中（4.4K） | ⭐⭐ | 知名度高，但偏开放域 |
| **FinQA** | 优（财报） | 低（数值推理，无检索 GT） | 中（8K） | ⭐ | 侧重数值推理，与聚类导航不匹配 |
| **LegalBench-RAG** | 优（法律文档） | 最高（字符级） | 中 | ⭐⭐ | 与 CUAD 重叠度高 |
| **RAGEval** | 可定制 | 取决于生成过程 | 可定制 | ⭐ | 框架而非固定数据集 |
| **RAGCare-QA** | 优 | 中（页面级） | 小（419） | ⭐ | 太小 |
| **MIRAGE** | 优 | 中 | 大（7.6K） | ⭐⭐ | 评估框架，含 PubMedQA/BioASQ |
| DragonBench | 差（新闻） | 有 | 动态 | ✗ | 俄语，非垂类 |

### 4.3 数据集选取方案

**核心数据集（3 个垂直领域，必须）：**

| 数据集 | 领域 | 选取理由 |
|--------|------|---------|
| **CUAD** | 法律 | 检索级 GT 最干净，段落级标注；文档结构化强，天然适合聚类 |
| **eManual** | 技术/产品 | 最接近企业知识库场景；HypRAG + RAGBench 双重覆盖，结果可对比 |
| **PubMedQA** | 生物医学 | 规模最大（211K+ 可用于在线学习曲线）；领域权威；MIRAGE 基准子集 |

**补充数据集（1-2 个，推荐）：**

| 数据集 | 领域 | 选取理由 |
|--------|------|---------|
| **BioASQ** | 生物医学 | GT 质量比 PubMedQA 更高（文档+snippet 双级标注）；可与 PubMedQA 形成医学领域的深度验证 |
| **BANKING77** | 金融/银行 | 已有完整实验数据（Phase 1B/1D）；展示与 pre-validation 研究的连续性 |

**不选的数据集及原因：**

| 数据集 | 不选原因 |
|--------|---------|
| FinQA | 侧重数值推理（表格计算），与我们的语义聚类+导航优化不匹配 |
| CRAG | 偏开放域（Sports/Music/Movies），无检索级 GT，不适合闭域聚类场景 |
| LegalBench-RAG | 与 CUAD 高度重叠（CUAD 是其子集），选一个即可 |
| RAGEval | 是生成框架，非固定数据集；审稿人可能质疑 GT 质量 |
| RAGCare-QA | 仅 419 问题，太小 |
| CovidQA | 仅 124 pairs，太小 |
| DragonBench | 俄语，非垂类 |
| MIRAGE | 评估框架而非独立数据集；其子集 PubMedQA/BioASQ 已单独选用 |

### 4.4 评估维度与数据集映射

| 评估维度 | 数据集 | 协议 |
|---------|--------|------|
| **静态检索质量** | CUAD, eManual, PubMedQA | 单次检索, RAGAS 指标 (F/CR/AR) |
| **在线学习曲线** | CUAD, eManual, PubMedQA | 多轮模拟, learning curve |
| **聚类有效性** | CUAD, eManual, PubMedQA (+ BANKING77) | 纯度, 搜索空间缩减比 |
| **消融实验** | CUAD (GT 最干净，消融结论最可信) | 逐一移除组件 |
| **跨领域泛化** | 3 个核心数据集对比 | 法律 vs 技术 vs 医学的效果差异 |

---

## 五、Ground Truth 分析与反馈模拟策略
## 5. Ground Truth Analysis & Feedback Simulation Strategy

### 5.1 核心问题

在线学习实验需要模拟用户反馈，反馈模拟的可靠性取决于 ground truth 的质量。
不是所有数据集都有检索级 GT（哪个 chunk 该被检索），有些只有答案级 GT（正确答案是什么）。

**GT 质量直接决定反馈模拟的可靠性，进而影响在线学习实验结论的可信度。**

### 5.2 选定数据集的 Ground Truth 情况

| 数据集 | 检索级 GT | 答案级 GT | GT 质量 | 反馈模拟可靠性 |
|--------|----------|----------|---------|--------------|
| **CUAD** | **有** — 每个条款类别标注了对应段落位置 | **有** — 标注的条款文本 | 最高 | 最高 — 直接判断检索对错 |
| **eManual (RAGBench)** | **有** — RAGBench 提供 QA + 源文档映射 | **有** — TRACe 标注 | 高 | 高 |
| **PubMedQA** | **部分** — context 是摘要（211K 规模可构建语料库） | **有** — yes/no/maybe + 结论段 | 中高 | 中高 — 规模大，统计上可靠 |
| **BioASQ** (补充) | **有** — 相关文档 + snippet 双级标注 | **有** — 精确答案 + 理想答案 | 高 | 高 — 医学领域 GT 最完整 |
| **BANKING77** (补充) | **间接** — 同 intent 的 train 样本 = 相关 chunk | **有** — intent 标签 | 中 | 中 — Phase 1D 已验证可行 |

### 5.3 三种反馈模拟策略

根据数据集提供的 GT 级别，采用不同策略：

**策略 A：检索级 GT（CUAD, eManual）— 最可靠**

```
检索到的 chunk ∈ GT 相关集合 → positive feedback
检索到的 chunk ∉ GT 相关集合 → negative feedback
```

- 无歧义，直接判定
- 反馈信号最干净
- **主实验优先使用这类数据集**

**策略 B：答案级 GT（PubMedQA, BANKING77）— 需要匹配逻辑**

```
检索到的 chunk 包含 GT answer（字符串匹配或语义匹配）→ positive
不包含 → negative
```

- 有噪声：chunk 可能包含答案关键词但实际不相关
- 需要设计匹配阈值
- 适合作为补充验证

**策略 C：无 GT（纯真实场景）— 用 LLM-as-judge**

```
LLM 判断检索到的 chunk 是否回答了 query → feedback score
```

- 成本最高（每次反馈需 LLM 调用）
- 引入 LLM 评判偏差
- 但最接近真实部署场景
- 适合企业场景的定性分析

### 5.4 各方法的反馈信号派生（统一信息源，各自转化）

所有方法的反馈从**同一个 ground truth** 派生，确保信息量公平。
静态 baseline 不接受反馈，在线 baseline 各自按自己的机制转化反馈信号。

| 方法 | 接受反馈 | 反馈信号格式 | 从 GT 如何派生 |
|------|---------|------------|--------------|
| BM25 / Dense / Hybrid | 否 | — | — |
| CRAG / MBA-RAG | 否 | — | 自适应但非在线学习 |
| DynamicRAG | 是 | LLM response quality (reward) | 检索结果是否覆盖 GT answer → reward score |
| Online-Opt RAG | 是 | binary (solved/unsolved) | answer 是否匹配 GT → 1/0 |
| FLAIR | 是 | feedback indicators | 同上，转化为 feedback signal |
| **本方法** | 是 | 显式+隐式+上下文（多维） | 匹配 GT → like+copy (0.8)；不匹配 → dislike (0.2)；部分匹配 → like+无copy (0.6) |

**公平性保证**：
- 所有方法从同一个 GT 获取等价信息量
- 静态方法不接受反馈 — 这是实验要验证的："在线学习是否有价值"
- 在线方法各自用各自的反馈格式 — 公平竞争学习效率

### 5.5 GT 质量与反馈模拟策略的匹配

| 数据集 | 适用策略 | 反馈模拟方式 |
|--------|---------|------------|
| **CUAD** | 策略 A（检索级） | chunk ∈ GT 段落集 → positive；否则 → negative |
| **eManual** | 策略 A（检索级） | chunk 在 RAGBench 映射中 → positive；否则 → negative |
| **PubMedQA** | 策略 B（答案级） | chunk 包含 GT 结论段的关键信息 → positive；211K 规模保证统计可靠性 |
| **BioASQ** | 策略 A（检索级） | chunk ∈ GT 相关 snippet 集 → positive |
| **BANKING77** | 策略 B（答案级） | chunk 属于同 intent 的 train 样本 → positive |

### 5.6 与 HypRAG 评估协议的差异

HypRAG 评估的是**单次检索质量（静态）**— 不同 embedding 模型在相同数据集上的检索效果。

本系统的核心优势是**多轮交互后的在线学习提升**，因此评估协议需要扩展：

1. **Round 0**：冷启动（关键词先验），与 HypRAG baseline 直接可比
2. **Round 1-N**：模拟用户反馈（按 5.4 中的策略），展示 learning curve
3. **收敛分析**：多少轮反馈后达到稳态

实验讲两层故事：
- **在线学习 vs 静态方法**：静态方法平线，在线方法上升 → "反馈学习有价值"
- **我们 vs 其他在线方法**：都上升，但我们更快/更高 → "我们的方式更有效"

---

## 六、待确认事项
## 6. Open Questions

1. ~~数据集选哪几个？~~ → 核心 3 个：CUAD + eManual + PubMedQA；补充：BioASQ + BANKING77
2. BioASQ 是否与 PubMedQA 同时使用？（同为医学领域，可能重叠；但 GT 质量互补）
3. BANKING77 是否保留？（已有实验基础，但 GT 是间接的）
4. 是否需要中文数据集？（SMP2019 或其他公开中文 RAG 数据集）
5. 在线学习的模拟轮次设计（50 轮？100 轮？需结合各数据集 query 规模）
6. CRAG 是否作为补充？（知名度高，NeurIPS/KDD Cup，但偏开放域）

---

*更新时间: 2026-04-21*
