# IntentWeight/IntentRoute 论文实验一致性与完整性 Review

**审阅人**: Nemesis  
**日期**: 2026-07-01  
**审阅范围**: paper/full_draft/, paper/draft/, paper/experiments/, pre_validation/, task51_experiment_manifest.json  
**目标**: 识别实验数据集、维度、抽样比例、命名、表述之间的不一致，为论文修订提供可操作的改进方案

---

## 一、问题总览

当前论文手稿存在 **6 类系统性问题**，核心症结是：实验设计在不同阶段（pre-validation → 主实验 → downstream）逐步扩展，但论文文本没有随之统一对齐，导致 abstract 创建了 6 数据集全面评估的预期，而实际量化证据几乎全部来自 LoTTE。同时 pre-validation 的大量工作与论文正文断裂，命名、query 数量、实验维度在不同文件间不一致。

**严重程度分级**: P0 = 必须修复（reviewer 会直接打回），P1 = 强烈建议修复，P2 = 建议修复

---

## 二、逐项问题分析

### P0-1. Abstract 与实验完整性的严重错位

**位置**: `paper/full_draft/01_abstract.md`

**现状**: Abstract 第 13-17 行写道：

> "We evaluate IntentRoute across six domain-specific settings. The primary scale study uses LoTTE technology/search from 100k to 638k chunks. A separate LoTTE science/search study tests cross-domain transfer at 20k and 100k corpus scales; PubMedQA and Banking77 examine feedback adaptation, while eManual and CUAD expose duplicate-text and sparse-ground-truth boundaries."

**问题**: 这段话创建了 6 个数据集都有实验支撑的预期。但翻阅 `paper/draft/experiments.md` 和 `task51_experiment_manifest.json`：

| 数据集 | Abstract 角色 | 实际量化结果 | 差距 |
|---|---|---|---|
| LoTTE technology/search | Primary scale study | 完整：4 scales × token-quality frontier + calibration/test + seed stability + geometry + downstream | ✅ 充分 |
| LoTTE science/search | Cross-domain transfer | 较完整：2 scales + cross-domain + feedback recovery | ✅ 较充分 |
| PubMedQA | Feedback adaptation | **无量化结果表**，experiments.md 仅标注 "feedback/manifold proof-of-concept" | ❌ 缺失 |
| Banking77 | Feedback adaptation | **无量化结果表**，experiments.md 仅标注 "intent/domain routing proxy" | ❌ 缺失 |
| eManual | Boundary case | **仅定性 failure 描述**，无量化指标 | ❌ 缺失 |
| CUAD | Boundary case | **仅 "sparse smoke/stress case"**，GT-anchored sampling，非完整评估 | ❌ 缺失 |

**影响**: Reviewer 会在 abstract 看到 6 个数据集，翻到 experiments 发现只有 LoTTE 有数字，直接判定 "overclaimed scope" 或 "incomplete evaluation"。

**建议修复方案**（二选一）：

**方案 A — 缩减 abstract 范围（推荐，工作量小）**:
将 abstract 改为明确分层：
- "Primary evidence is drawn from LoTTE technology/search (4 corpus scales, 100k–638k) and LoTTE science/search (2 scales). Boundary cases on eManual and CUAD expose known limitations of strict chunk-id matching and sparse ground truth. PubMedQA and Banking77 serve as preliminary feedback-adaptation checks whose quantitative results are deferred to supplementary material."

**方案 B — 补齐实验（工作量大）**:
为 PubMedQA、Banking77 补充量化结果表（至少 Hit@10 + token saving + feedback adaptation 对比），为 eManual/CUAD 补充 boundary case 的定量指标。如果 pre_validation 中已有 Banking77 的 intent clustering 结果，可整合进来。

---

### P0-2. Pre-validation 工作与论文正文的断裂

**位置**: `pre_validation/` 目录 vs `paper/` 目录

**现状**: `pre_validation/` 包含大量已完成的工作：
- Banking77: 10003 train / 3080 test, intent clustering + speech act classification
- CLINC150: 15250 train / 5500 test, intent clustering + speech act classification
- DailyDialog: speech act classification
- CMID: 中文医学意图，embedding 生成 + clustering
- SMP2019: 预处理脚本存在
- 完整的 cluster mapping、closure test、speech act 分类结果

**问题**:
1. 论文 experimental setup（`05_experimental_setup.md`）的 4.1 Datasets 节提到 Banking77 作为 "intent-routing proxy"，但**没有引用 pre_validation 的任何结果**
2. CLINC150、DailyDialog、CMID、SMP2019 **完全不出现在论文中**
3. Pre-validation 的 intent clustering framework（`cluster_with_framework.py`）与论文的 piecewise relevance-manifold hypothesis 之间**缺乏显式连接**
4. 论文的 manifold hypothesis 需要经验证据支撑——pre_validation 的 cluster mapping 和 closure test 结果恰好可以提供，但目前没有接入

**影响**: 
- 如果 reviewer 发现 pre_validation 目录存在但论文未引用，会质疑 "为什么做了实验不用"
- Manifold hypothesis 缺少 preliminary evidence，说服力不足
- Banking77 在 abstract 提了但论文里没有结果，进一步加剧 P0-1 的问题

**建议修复方案**（三选一）：

**方案 A — 整合为 Preliminary Evidence 节（推荐）**:
在 Experimental Setup 前或 Method 节内增加一个 "Preliminary Validation" 小节：
- 用 pre_validation 的 cluster mapping 结果（Banking77/CLINC150 等）证明垂类数据确实存在可用的 local geometry
- 用 closure test 结果证明 intent cluster 的覆盖性
- 用 speech act classification 结果证明 intent 维度的可分性
- 明确标注这些是 manifold hypothesis 的 preliminary evidence，不是 main retrieval results
- 对于 CLINC150/CMID/SMP2019：如果它们提供了跨语言/跨领域的额外 evidence，保留；否则明确排除并说明原因

**方案 B — 仅整合 Banking77**:
只把 Banking77 的 pre-validation 结果接入论文（因为 abstract 已提到），其余数据集明确排除。

**方案 C — 明确切割**:
在论文中声明 "preliminary validation experiments on Banking77, CLINC150, and CMID are documented in supplementary material and not included in the main retrieval evaluation"，然后从 abstract 中移除对这些数据集的提及。

---

### P1-3. Query 数量与抽样比例不统一

**位置**: 多处

**现状**: 不同文件和实验中 query 数量不一致，且缺乏统一说明：

| 数据集/实验 | 总 queries | 测试 queries | 抽样说明 | 来源文件 |
|---|---|---|---|---|
| LoTTE tech/search (全量) | 596 | - | - | manifest: expected_queries: 596 |
| LoTTE tech/search (test split) | - | 417 | 30% calibration / 70% test | 05_experimental_setup.md 4.7 |
| LoTTE sci/search 20k/q200 | 200 | 140 | q200 = 子采样到 200 | manifest: expected_queries: 200 |
| LoTTE sci/search 100k | 596 | 417 | 同 tech/search | manifest |
| Downstream answer eval | - | 300 | 从 417 中确定性抽取 | 05_experimental_setup.md 4.8 |
| LLM generation smoke (旧) | - | 60 | 从 100k 中采样 | experiments.md line 299 |
| Pre-validation Banking77 | 13083 | 3080 test | 原始数据集 split | pre_validation/processed/data_stats.json |
| Pre-validation CLINC150 | 23850 | 5500 test | 原始数据集 split | pre_validation/processed/data_stats.json |

**问题**:
1. 596 → 417 → 300 的三级抽样链条没有统一说明
2. q200 的含义（从多少中抽到 200）未解释
3. 60-query smoke 和 300-query evaluation 的关系未说明（是同一个实验的扩展？还是不同实验？）
4. Pre-validation 的 query 规模（3080/5500）与论文主实验（417/596）完全不在一个量级，读者会困惑

**建议修复方案**:

在 Experimental Setup 中增加一个 **Dataset Summary 表**，统一列出：

```markdown
| Dataset | Corpus Size | Total Queries | Eval Queries | Sampling Protocol | Experimental Role |
|---|---|---|---|---|---|
| LoTTE tech/search 100k | 101,311 chunks | 596 | 417 (test) | 30/70 cal/test split | Main scale point |
| LoTTE tech/search 200k | 201,010 | 596 | 417 | same | Main scale point |
| LoTTE tech/search 400k | 400,674 | 596 | 417 | same | Diagnostic scale |
| LoTTE tech/search 638k | 638,509 | 596 | 417 | same | Main scale point |
| LoTTE sci/search 20k | ~20k chunks | 200 (q200) | 140 (test) | q200 subsample + 30/70 | Cross-domain |
| LoTTE sci/search 100k | ~100k | 596 | 417 | same as tech | Cross-domain |
| Downstream (tech 100k) | 101,311 | 417 (test) | 300 | deterministic draw from 417 | Answer-level |
| Pre-val Banking77 | - | 13,083 | 3,080 | original dataset split | Preliminary |
| Pre-val CLINC150 | - | 23,850 | 5,500 | original dataset split | Preliminary |
```

并在 4.7 Calibration 中补充说明 596 → 417 的 split 逻辑，在 4.8 Downstream 中补充 417 → 300 的抽样说明。

---

### P1-4. 实验维度严重不均

**位置**: `paper/draft/experiments.md`

**现状**: LoTTE 数据集有非常丰富的实验维度，其他数据集几乎没有：

| 实验维度 | LoTTE tech | LoTTE sci | PubMedQA | Banking77 | eManual | CUAD |
|---|---|---|---|---|---|---|
| Token-quality frontier | ✅ 4 scales | ❌ | ❌ | ❌ | ❌ | ❌ |
| Calibration/test split | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Seed stability | ✅ 3-5 seeds | ✅ 3 seeds | ❌ | ❌ | ❌ | ❌ |
| Geometry diagnostics | ✅ PCA + cluster | ❌ | ❌ | ❌ | ❌ | ❌ |
| Arm-count sensitivity | ✅ K∈{8,...,128} | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-encoder reranker | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Sentence-MMR | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SelectiveContext-lite | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Embedding backbone (BGE/E5) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Downstream LLM (3 judges) | ✅ 300q | ❌ | ❌ | ❌ | ❌ | ❌ |
| Feedback adaptation | ✅ | ✅ | ❌ 提及无数据 | ❌ 提及无数据 | ❌ | ❌ |
| Feedback recovery | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Boundary/failure case | ❌ | ❌ | ❌ | ❌ | ✅ 定性 | ✅ 定性 |

**问题**: 
- PubMedQA 和 Banking77 在 abstract 声称 "examine feedback adaptation"，但没有量化结果
- eManual 和 CUAD 只有定性描述，没有 Hit@10 / token saving 等数字
- 实验维度的巨大差异让论文看起来像 "一个数据集的完整论文 + 几个数据集的脚注"

**建议修复方案**:

1. **对于有 pre-validation 结果的数据集（Banking77）**: 整合 intent clustering / feedback adaptation 的量化结果（即使指标不同，也应报告）
2. **对于 PubMedQA**: 如果有实验结果就补充；如果没有，从 abstract 和 experimental setup 中移除或降级为 "future work"
3. **对于 eManual/CUAD**: 补充基本的 retrieval 指标（Hit@10, token count），即使是 failure case 也应有数字支撑 failure 的结论
4. **在论文中明确实验层级**: 用一个表格或段落说明 "primary evidence (full experimental battery)" vs "supporting evidence (limited dimensions)" vs "boundary cases (diagnostic only)"

---

### P1-5. 命名不一致（IntentWeight vs IntentRoute）

**位置**: 多处

**现状**:
- `paper/full_draft/` 全部使用 "IntentRoute"
- `paper/draft/experiments.md` 全部使用 "IntentWeight"
- `paper/experiments/` 目录下的 task summary 文件混用
- `05_experimental_setup.md` 4.6 节有说明："Historical experiment directories and machine-readable method labels retain the legacy IntentWeight identifier... paper-facing terminology uses IntentRoute"
- 但 `experiments.md` 没有遵循这个约定

**问题**: 同一文档体系内方法名不一致，reviewer 会困惑 IntentWeight 和 IntentRoute 是否是两个不同的东西。

**建议修复方案**:
1. `paper/draft/experiments.md` 全篇替换 IntentWeight → IntentRoute（保留 4.6 的 legacy 说明）
2. `paper/experiments/` 下所有 paper-facing summary 文件统一为 IntentRoute
3. 代码目录和 manifest 保留 IntentWeight（作为 legacy identifier），但在论文文本中不出现
4. 建议在 paper 中首次出现时写明 "IntentRoute (implementation identifier: IntentWeight)"

---

### P2-6. Downstream Evaluation 的两个实验未交代关系

**位置**: `paper/draft/experiments.md` line 298-315 vs `paper/full_draft/05_experimental_setup.md` line 293-312

**现状**:
- experiments.md 描述了一个 "60 sampled LoTTE 100k queries" 的 LLM generation smoke check，使用 deepseek-v4-flash，对比 Dense top-10 vs Task29-C
- full_draft 描述了一个 "300 deterministic queries from 417-query frozen test split" 的 downstream evaluation，7 种方法，3 个 judge，2100 answers + 6265 judgments

**问题**: 
- 这是两个不同的实验（60 queries vs 300 queries），但论文没有说明它们的关系
- 60-query smoke 是否是 300-query evaluation 的前身？是否已被取代？
- 如果 60-query smoke 已被取代，应从论文中移除或明确标注为 superseded
- 如果两者都保留，需要说明为什么有两个不同规模的 downstream evaluation

**建议修复方案**:
1. 如果 300-query 已取代 60-query: 在 experiments.md 中标注 60-query smoke 为 "superseded by Task33.5+ downstream evaluation"，论文正文只用 300-query 结果
2. 如果两者都保留: 在 experimental setup 中说明 "an initial 60-query smoke check (Section X.X) validated the pipeline before scaling to the full 300-query, 3-judge evaluation (Section X.Y)"

---

### P2-7. experiments.md 的 superseded 标注不完整

**位置**: `paper/draft/experiments.md` 末尾

**现状**: experiments.md 末尾有标注：
> "Superseded draft / 已归档草稿: 当前论文主源为 paper/full_draft/，论文-facing 名称为 IntentRoute。本文件仅保留早期 IntentWeight 草稿记录。"

**问题**: 虽然有标注，但该文件仍在项目中被引用（task42 等文档引用了 experiments.md 的内容），且其中的数据（如 Task29-C 的 4.83% token saving）与 full_draft 的 6-18% 不一致（因为 full_draft 使用的是 Task38 calibrated 结果而非 Task29-C confidence-only 结果）。

**建议修复方案**:
1. 确认 experiments.md 中的所有数据是否已被 full_draft 取代
2. 如果是，在文件开头（不是末尾）加显眼的 superseded 标注
3. 确保论文正文只引用 full_draft 的数据，不混用 experiments.md 的旧数字

---

## 三、数据一致性核查清单

以下是需要统一核查的具体数字，确保论文全文（abstract → setup → results → discussion）一致：

| 指标 | experiments.md 中的值 | full_draft 中的值 | 是否一致 |
|---|---|---|---|
| Token saving 范围 | 4.83%–5.32% (Task29-C) | 6%–18% (Task38 calibrated) | ❌ 不同实验，需明确区分 |
| Downstream query 数 | 60 (smoke) | 300 (full) | ❌ 不同实验，需说明关系 |
| 方法名 | IntentWeight | IntentRoute | ❌ 需统一 |
| 数据集数量 | 6 (in experiments.md) | 6 (in abstract) | ✅ 但实际有量化结果的只有 2 |
| LoTTE tech queries | 596 total / 417 test | 596 / 417 | ✅ |
| LoTTE sci 20k queries | 200 | 200 (q200) | ✅ 但 q200 含义未解释 |
| Arm count | 32 (main) + sensitivity {8,...,128} | 32 + sensitivity | ✅ |
| Judges | 未提及 (smoke 只用 deepseek) | 3 (deepseek/glm-5.2/minimax-m3) | ❌ 不同实验 |
| Seed count | 3-5 seeds | 提及但未列具体数 | ⚠️ 需统一 |

---

## 四、建议的修复优先级

### Phase 1: P0 修复（必须在投稿前完成）

1. **重写 Abstract** — 明确区分 primary evidence (LoTTE) 和 supporting/boundary cases，不要让 6 个数据集看起来都有同等量化支撑
2. **决策 Pre-validation 的归属** — 要么整合进论文（推荐方案 A: 作为 Preliminary Evidence 节），要么从 abstract 中移除相关数据集

### Phase 2: P1 修复（强烈建议）

3. **制作 Dataset Summary 表** — 统一列出所有数据集的 corpus size、query count、sampling protocol、experimental role
4. **补齐或降级次要数据集** — PubMedQA/Banking77 要么补量化结果，要么降级；eManual/CUAD 补基本指标
5. **统一命名** — experiments.md 和所有 paper-facing 文件统一为 IntentRoute
6. **统一实验维度说明** — 用表格或段落说明哪些数据集有完整实验电池，哪些只有有限维度

### Phase 3: P2 修复（建议）

7. **说明 downstream evaluation 演进** — 60-query → 300-query 的关系
8. **清理 superseded 文件** — 确保 experiments.md 的旧数字不被误引
9. **统一所有数字** — 按 Section 三的核查清单逐项对齐

---

## 五、关键文件索引

供 Codex 分析时参考：

| 文件 | 用途 |
|---|---|
| `paper/full_draft/01_abstract.md` | 当前 abstract（主源） |
| `paper/full_draft/05_experimental_setup.md` | 当前实验设置（主源） |
| `paper/draft/experiments.md` | 早期实验草稿（已标注 superseded 但仍被引用） |
| `paper/experiments/task51_experiment_manifest.json` | 完整实验 manifest（1146 行，含所有实验的 dataset/query/artifact 配置） |
| `paper/experiments/task42_manuscript_review_alignment.md` | 上一次 review 对齐记录 |
| `paper/experiments/task36_9_full_draft_consistency_audit.md` | 自动化一致性审计（仅检查格式，未检查内容一致性） |
| `pre_validation/processed/data_stats.json` | Pre-validation 数据集统计 |
| `pre_validation/README.md` | Pre-validation 总览 |
| `pre_validation/results/` | Pre-validation 实验结果（cluster mapping, speech act, closure test） |
| `docs/publication-readiness-and-figure-plan.md` | 出版就绪与图表计划（提到 LoTTE 但未提其他数据集） |
| `paper/latex/main.tex` | LaTeX 主文件 |

---

## 六、补充观察

1. **task36_9 一致性审计的局限**: 该审计只检查格式问题（TODO 标记、manifold wording、LaTeX delimiter、BibTeX key），**没有检查内容一致性**（数据集范围、query 数量、实验维度对齐）。建议增加一个内容一致性检查脚本。

2. **Figure Plan 的范围**: `docs/publication-readiness-and-figure-plan.md` 中的图表计划全部围绕 LoTTE，没有为其他数据集规划图表。如果决定保留 6 数据集框架，需要补充图表。

3. **Review 包中的 manuscript**: `paper/review_packet/manuscript.md` 可能是提交给 reviewer 的版本——需要确认它是否与 full_draft 一致，特别是 abstract 的数据集范围表述。

4. **Manifest 的 expected_num_queries vs expected_queries**: manifest 中 `expected_num_queries` (417) 和 `expected_queries` (596) 同时出现但含义不同——前者是 test split，后者是全量。这个命名容易混淆，建议在 manifest 中加注释或重命名。

---

*本 review 基于 2026-07-01 的项目状态。如果后续实验有更新（特别是 PubMedQA/Banking77 补充了量化结果），请相应调整评估。*
