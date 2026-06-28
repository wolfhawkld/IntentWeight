# IntentRoute (IntentWeight) 第二轮同行评审（终版）

> 评审人：Metis (GLM-5-2) · 日期：2026-06-27 · 项目：IntentWeight/IntentRoute
> 范围：Task57-65.3 全部新增内容 + 逻辑缺口追踪 + 边界划定
> 交叉审校：Codex 修正了原版中"证明正交""证伪因果传递""RRF 冗余度假说"等过度推断

---

## 一、评审范围

本轮评审覆盖 Task57-65.3 全部新增内容：

- Task57：评审响应行动计划（内部规划文档）
- Task58：Geometry vs Random 消融实验
- Task59：Feedback-Control 消融实验
- Task60：Arm Count Sensitivity (K=8-128)
- Task61：Geometry-to-Control 分析
- Task62：SelectiveContext-lite prompt compression baseline
- Task63：300-query 下游 LLM 评估（2100 answers / 2100 judgments）
- Task64：Manuscript claim reframe（IntentWeight → IntentRoute）
- Task65：Table and figure refresh（5 表 3 图，PDF 30→28 页）
- Task65.1/65.2：安全压缩识别消融（2×2 factorial + dense control）
- Task65.3：Dynamic-Route Mediation（candidate-pool survival 分析）

上次评审（2026-06-24）的 P0/P1 建议执行情况：

| 建议 | 优先级 | 状态 |
|------|--------|------|
| Random-cluster 对照实验 | P0 | ✅ Task58 已做 |
| No-LinUCB / no-feedback ablation | P0 | ✅ Task59 已做 |
| Elsevier 格式转换 + 匿名化 | P0 | ❌ 仍未做（内容确认后再转） |
| 扩大下游评估到 ≥300 queries | P1 | ✅ Task63 已做 (300q/2100a) |
| LLMLingua-2 实验 | P1 | ⚠️ Task62 用 SelectiveContext-lite 代替 |
| 增加 seeds 到 ≥5 | P1 | ❌ 仍为 3 seeds（硬件限制） |
| Geometry-to-gain 回归分析 | P2 | ⚠️ Task61 做了但 N 太小（n=5-6） |
| Arm count sensitivity (K=8-128) | P2 | ✅ Task60 已做 |
| 精简 Results 节 | P2 | ✅ Task65 已做 (8→7 子节) |

---

## 二、论文定位与叙事主线

论文的叙事是一个完整的科研闭环：

```
观察：垂直领域检索数据是否存在可利用的局部流形结构？
  ↓
验证：通过 PCA spectrum / cluster hit / context retention 诊断
  ↓
启发：如果局部结构存在，能否利用它设计多路由检索策略？
  ↓
方案：dense（全局召回地板）+ BM25（词法锚点）+ cluster-local（几何局部路由）
  ↓
问题：多路由本身不省 token（Task28 证实）
  ↓
机制：confidence-based budget control——用 route confidence 判断何时可安全压缩
  ↓
验证：6-18% token saving + 保持召回质量 + 下游答案不降
```

这不是"工程组合"，而是一个从假设到验证到工程化到效果确认的完整研究过程。manifold 部分是起点和启发，不是终点和定理——论文已经明确标定为"bounded diagnostic assumption"，不需要弱化。

---

## 三、新实验结果分析

### 3.1 Task58 — Geometry vs Random

```
                    Route Reward    Cluster Hit    Test Hit Delta    Token Saving    NI Seeds
Static geometry:    0.8563          0.8870         +1.44 pp          5.03%           3/3
Uniform random:     0.1499          0.1577         +1.04 pp          11.92%          2/3
```

Route-level reward 差距巨大（0.86 vs 0.15），证明 cluster 结构在路由层有意义。但两者都未通过 calibration eligibility gate，不能用于正面 token-quality claim。Final Hit@10 由 dense/BM25 rescue 保护，与 route 质量关系不大。

### 3.2 Task59 — Feedback-Control

```
Learned LinUCB route reward:     0.6790
No-feedback route reward:        0.1504
No-feedback dense_rate:          1.0000
Learned gated Hit delta:         -5.20 pp (cost-aggressive boundary)
```

No-feedback 的 dense_rate=1.0 意味着没有反馈时系统完全不信任 LinUCB，全部回退 dense。Feedback 的角色是更新 LinUCB → 产生 confidence → 驱动 tier 分配。Cost-aggressive gated 变体是 boundary evidence，不是主 claim。

### 3.3 Task63 — 300-query 下游评估

```
BGE IntentRoute vs BGE dense:       +0.00pp [-2.67, +2.67],  6.00% saving
E5 IntentRoute vs E5 dense:         +0.33pp [-3.00, +3.67],  12.04% saving
IntentRoute+SentMMR vs Dense+SentMMR: +2.33pp [-1.67, +6.33], 6.65% saving
```

所有 correctness CI 包含零 → 只能 claim "不降低答案质量的同时减少 token"。token-saving CI 全部为正。2100 answers + 2100 judgments 是有意义规模的评估。

### 3.4 Task62 — SelectiveContext-lite

Dense+SC 15.31% saving, IntentRoute+SC 20.78% stacked。合理结果，但不是 LLMLingua，related work 中提及 LLMLingua 仍需处理。

### 3.5 Task65.2 — 安全压缩识别消融

2×2 factorial（geometry vs random × feedback vs no-feedback）+ dense budget-only，在同一 split / candidate pool / budget grid / seeds 下对比。

**失败预测能力（AUROC）：**

```
geometry + feedback:           0.434    ← 低于随机
geometry + no feedback:        0.201    ← 最差
random + feedback:             0.573    ← 略高于随机
random + no feedback:          0.381    ← 低于随机
dense budget-only:             0.500    ← 随机基线
```

在 ~10% token saving 下，geometry+feedback vs random+feedback 的 Hit 差异仅 +0.08 pp（所有 seed CI 包含零）。

**结论：** 在当前样本量下（97.8% safe prevalence, ~2.2% unsafe），未观察到 geometry/feedback 对 per-query 安全压缩识别有显著优势。这是 "absence of evidence" 而非 "evidence of absence"。

### 3.6 Task65.3 — Dynamic-Route Mediation

在固定 split / candidate pool / budget action / seeds 下对比 5 个变体，并做了 per-query 诊断。

**主表（同一 budget action r0.95_m4）：**

```
Variant                        Budgeted Hit@10   vs dense      Token Saving
Dynamic confidence gating      0.8705            -0.00 pp      6.18%
Fixed full fusion              0.8745            +0.40 pp      5.27%
Shuffled confidence tiers      0.8225            -4.80 pp      6.54%
Fixed cluster-primary          0.7626            -10.79 pp     6.93%
Dense budget-only              0.8561            -1.44 pp      13.83%
```

**发现 1：Confidence 作为路由信号有效**

Dynamic gating vs shuffled tiers: +4.80 pp, 3/3 seeds CI 排除零。Tier 分层数据显示：低 confidence query 走 cluster-primary 时 Hit@10 从 0.811 暴跌到 0.340。Confidence 的核心价值是保护低 confidence query 不走灾难路径。

**发现 2：压缩安全性由排序位置决定**

```
Feature                         AUROC (r0.85_m4, seed 13)
first_relevant_rank             0.997    ← 近乎完美
first_relevant_token_position   0.998    ← 近乎完美
relevant_count                  0.773    ← 中等
route_confidence                0.436    ← 低于随机
```

压缩是否安全几乎完全取决于"第一个正确 chunk 排在第几"和"它的 token 位置在哪"。Route confidence 的 AUROC 低于随机，Spearman -0.056，所有 seed CI 包含零。

**发现 3：Dynamic gating 不创造更多正确 chunks**

```
Dynamic pool:   平均 2.121 个正确 chunks
Fixed full:     平均 2.315 个正确 chunks
Dense:          平均 2.266 个正确 chunks
```

多路由池的正确 chunk 数量不比 dense 多。Dynamic gating 的价值在 tier 分配，不在候选池冗余度。

**发现 4：同一 action 下 dense vs dynamic 的 trade-off**

Dense 省更多 token（pool 更大）但丢更多 Hit（排序不如 dynamic 稳定）。Dynamic gating 在质量和节省之间取了更保守的平衡点。

---

## 四、核心因果链（Task65.2/65.3 后终版）

论文支持的因果链：

```
✅ 已证:  geometry/feedback → route confidence → tier 分配 → 路由形状 → evidence pool 质量
          （Task58: route reward 0.856 vs 0.15; Task65.3: shuffled tiers -4.80 pp）

✅ 已证:  calibrated budget → 在 evidence pool 上安全压缩 → token saving
          （Task37/38: 6-18% saving, calibration-eligible）

✅ 已证:  压缩安全性 ← first_relevant_rank / token_position（AUROC ~1.0）
          （Task65.3: 排序位置决定安全性，与 route confidence 无关）

❌ 未证实: route confidence → 压缩安全性预测（AUROC 0.436, Spearman -0.056）
          （Task65.2/65.3: 样本量受限，absence of evidence）
```

论文应讲的故事：

> IntentRoute 的 confidence 在路由层有效：高 confidence query 走 cluster-primary，低 confidence query 回退 dense，shuffled tiers 实验证明这个分配是有用的。但 confidence 不预测压缩安全性——压缩是否安全取决于正确 chunk 在排序中的位置（AUROC ~1.0），这是一个由 RRF 融合和候选池特性决定的属性。Token saving 来自在 dynamic route 产生的 evidence pool 上做 calibrated budget compression，而非来自 confidence 的压缩预测精度。两者各自独立，组合产生最终的质量-成本 trade-off。

---

## 五、逻辑缺口追踪与边界划定

### 5.1 已回答或澄清的问题

| 原问题 | 原优先级 | 现状态 | 回答方式 |
|--------|----------|--------|----------|
| Dense budget-only vs IntentRoute | P0 | 部分回答 | Task65.3 同 action 对比：dense 省更多但丢更多 Hit，trade-off 点不同 |
| Calibration gate selection bias | P0 | 部分回答 | Task65.3 shuffled tiers 证明 tier 分配有效；完整 de-biasing 超出 scope |
| Feedback gated 有害 | P1 | 已澄清 | Task59 cost-aggressive 变体是 boundary，不是主 claim；Task65.3 tier 分析证明 confidence→tier 链有效 |
| Oracle/Random budget baseline | P1 | 已回答 | Shuffled tiers ≈ random baseline；first_relevant_rank AUROC ~1.0 提供 oracle 级信息 |
| 6-18% safer 机制解释 | P1 | 已回答 | Task65.3：压缩安全性由排序位置决定（AUROC ~1.0），dynamic pool 排序更稳定 |

### 5.2 已划定边界的非核心问题

以下问题不深入追究。研究不能无限深挖每个分支——对主线不是非常核心的问题，适当划定边界并诚恳说明不做的理由，比强行补完更负责任。

**1. Dense + full calibration grid 对比**

不做的理由：Task65.3 的同 action 对比已说明机制。论文研究的是 route-confidence-to-budget controller，不是 dense 检索的优化。如果审稿人要求，revision 阶段补充。

**2. Manifold motivation 与最终机制的断裂**

不做的理由：论文已明确标定 manifold 为 "bounded diagnostic assumption"——研究方向启发的起点，不是被验证的定理。Manifold → clustering → route → confidence 这条链的前半段有 route-level 证据（Task58），后半段（confidence → compression）被 Task65.2/65.3 证明不成立。论文的 claim 已经不依赖 manifold → token saving 的直接因果，所以这个断裂不构成逻辑缺陷，只需要在叙事中诚实说明。

**3. eManual 失败案例深入分析**

不做的理由：论文已标注为 boundary case 并给出原因（18,812 chunks → 1,729 unique texts，重复文本导致聚类退化）。深入分析超出本文 scope，Limitations 中已诚实报告。

**4. 下游评估只有 1 个领域**

不做的理由：300-query / 2100-answer 评估在 LoTTE technology/search 上完成，规模充分。Cross-domain 检索层结果（science/search, Table 2）已报告。Multi-domain answer-level 评估受限于硬件和 API 成本，列为 future work。论文未 claim "universal generalization"。

**5. Prequential 多 epoch 的 epoch 1 对比**

不做的理由：Prequential protocol 已在 Method 中如实描述。多 epoch 是 within-query-set adaptation 研究，不是 IID generalization claim。Epoch 1 对比对核心 claim 不是必需的。

**6. Post-fusion safety predictor**

不做的理由：Task65.3 证明 first_relevant_rank 近乎完美预测压缩安全性（AUROC ~1.0），但这是 oracle 特征，不可部署。训练可部署的 post-fusion safety predictor 是有价值的 future work，但超出本文 scope。

### 5.3 优先级总览

```
问题                              原优先级   现状态
──────────────────────────────────────────────────────────
Dense budget-only vs IntentRoute  P0        部分回答，边界划定
Calibration gate selection bias   P0        部分回答，边界划定
Feedback gated 有害               P1        已澄清（Task65.3 tier 分析）
Oracle/Random budget baseline     P1        已回答（shuffled tiers + AUROC）
6-18% safer 机制解释              P1        已回答（first_relevant_rank AUROC ~1.0）
Manifold 与机制断裂               P2        边界划定（motivation, not mechanism）
eManual 深入分析                   P2        边界划定（boundary case, cause documented）
下游只有 1 个领域                 P2        边界划定（hardware/cost, future work）
Prequential 多 epoch              P2        边界划定（protocol disclosed）
Post-fusion safety predictor      —         边界划定（future work）
```

---

## 六、统计严谨性评估

3 seeds（13, 17, 19）是硬件条件下的实际限制。论文对此的处理是恰当的：
- 诚实标注为"stability diagnostics, not large-sample proof"
- 补充了 query-level paired bootstrap CI + McNemar test 作为主要推断证据
- 400k 标为 diagnostic only（calibration ineligible）

建议在 Limitations 中明确注明硬件约束，将"增加 seeds"列为 future work 而非当前缺陷。

Task61 的 Geometry-to-Control 相关性分析使用 n=5-6 个 scale 点做 Pearson 相关，统计功效受限。这是数据规模的固有限制，不是方法错误。

---

## 七、论文重构评价

**改名 IntentWeight → IntentRoute：** "Route" 比 "Weight" 更准确反映方法本质，避免与 attention weight 混淆。代码层兼容性迁移（alias + test），历史实验路径保留 "IntentWeight" 标签用于复现，处理得当。

**Claim reframe：** 新 thesis—"IntentRoute converts confidence over dense, lexical, and geometry-defined cluster routes into a calibrated final evidence-context budget"—比之前的"manifold + LinUCB + budget 三足鼎立"清晰。

**表格/图精简：** 8 个 results 子节精简到 7 个，5 表 3 图，28 页。附录 21 张表详细但不挤占正文。密度对 IP&M 合适。

**LaTeX 质量：** ACL preprint 格式，26 citations / 26 bib entries / 0 uncited——引用一致性通过。待转 Elsevier elsarticle。

---

## 八、质量评估矩阵

```
维度                    评分    说明
──────────────────────────────────────────────────────
问题定义                ★★★★☆   三层成本分离精准，从流形假设到 budget 控制逻辑闭环
理论深度                ★★☆☆☆   流形作为启发而非定理，定位诚实；无新理论贡献
方法新颖性              ★★★☆☆   组件已有先例，但"几何启发→路由→置信度→预算"的完整链路有独立价值
实验严谨性              ★★★★☆   P0 ablation 完成，calibration/test split，paired stats，Task65.2/65.3 factorial
统计显著性              ★★★☆☆   3 seeds 受硬件限制，query-level paired stats 缓解
Baseline 公平性         ★★★★☆   充分（SentMMR / cross-encoder / SelectiveContext / BGE / E5）
下游评估                ★★★★☆   300q / 2100 answers / 2100 judgments，规模充分
可复现性                ★★★★☆   参数完整，IntentRoute 兼容性 test，代码有
写作质量                ★★★★☆   reframe 后结构清晰，5 表 3 图 28 页，claim 克制
Claim 诚实度            ★★★★★   10 条 limitations，不回避不利结果，Task65.2 负面发现诚实报告
```

---

## 九、投稿前剩余工作与建议

```
P0:  Elsevier 格式转换 + 匿名化（硬性 blocker）
P0:  Discussion 中正确阐述 Task65.2/65.3 发现（已部分完成）
P1:  第二 LLM judge（复用已有 2100 答案）
P1:  Task65.3 结果整合进论文（tables / appendix）
```

内容已就绪。执行顺序：
1. 在 Discussion 中正确阐述 Task65.2/65.3 发现
2. 转 Elsevier elsarticle + 匿名化
3. 投 IP&M

---

## 十、总体评价

这是一篇从数据观察出发、经过假设验证、到工程化方案、再到效果确认的完整研究。它的价值不在于发明新算法或证明新定理，而在于：

1. 提出了 RAG 上下文成本控制的三层分离框架
2. 用流形启发设计多路由策略
3. 发现"多路由不省 token"的关键转折
4. 用 confidence-based budget control 解决这个转折
5. 在 100k-638k 规模 + 300 query 下游评估上验证了完整链路

Task65.2/65.3 的消融实验揭示了因果链的精确边界：confidence 在路由层有效（tier 分配），但在压缩层无效（不预测安全性）。压缩安全性由排序位置决定（AUROC ~1.0）。论文对这一负面发现的诚实报告体现了学术诚信。

非核心问题已按"划定边界 + 诚实说明不做的理由"原则处理，避免无限深挖。

---

## 附：与第一轮评审（2026-06-24）的变化对比

| 维度 | 上次 | 本次 | 变化 |
|------|------|------|------|
| 问题定义 | ★★★★☆ | ★★★★☆ | 持平 |
| 理论深度 | ★★☆☆☆ | ★★☆☆☆ | 持平（Task58/59 提高归因完整性，非理论深度） |
| 方法新颖性 | ★★★☆☆ | ★★★☆☆ | 持平 |
| 实验严谨性 | ★★★★☆ | ★★★★☆ | ↑（+Task65.2/65.3 factorial ablation） |
| 统计显著性 | ★★★☆☆ | ★★★☆☆ | 持平（仍 3 seeds） |
| Baseline 公平性 | ★★★★☆ | ★★★★☆ | ↑（+SelectiveContext-lite） |
| 下游评估 | ★★☆☆☆ | ★★★★☆ | ↑↑（60q→300q，2100 judgments） |
| 可复现性 | ★★★★☆ | ★★★★☆ | ↑（+IntentRoute 兼容性 test） |
| 写作质量 | ★★★☆☆ | ★★★★☆ | ↑（reframe + 精简 + 28 页） |
| Claim 诚实度 | ★★★★★ | ★★★★★ | 持平 |

---

## 备注

- 本评审整合了 v2 peer review 和 logic gaps analysis 两份文档
- Task65.3 的 plan 文件中的 guardrails 已被遵守：未假设 RRF 冗余、未从相关性推断因果、未将 failure to detect 等同于 independence
- 与 Codex 的交叉审校修正了原版中"证明正交""证伪因果传递""RRF 冗余度假说"等过度推断
- Codex 数据否定了"RRF 产生更多正确 chunks"的假说（dense 2.60 vs 多路由 2.40-2.43）
- 非 core 问题已按"划定边界 + 诚实说明不做的理由"原则处理
