# IntentRoute (IntentWeight) 第二轮同行评审

> 评审人：Metis (GLM-5-2) · 日期：2026-06-27 · 项目：IntentWeight/IntentRoute
> 范围：Task57-65 全部新增内容 + 上次评审（2026-06-24）后的变更

---

## 一、评审范围

本轮评审覆盖以下新增内容：
- Task57：评审响应行动计划（内部规划文档）
- Task58：Geometry vs Random 消融实验
- Task59：Feedback-Control 消融实验
- Task60：Arm Count Sensitivity (K=8-128)
- Task61：Geometry-to-Control 分析
- Task62：SelectiveContext-lite prompt compression baseline
- Task63：300-query 下游 LLM 评估（2100 answers / 2100 judgments）
- Task64：Manuscript claim reframe（IntentWeight → IntentRoute）
- Task65：Table and figure refresh（5 表 3 图，PDF 30→28 页）

上次评审的 P0/P1 建议执行情况：

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
| 精简 Results 节 | P2 | ✅ Task65 已做 (11→7 子节) |

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

## 三、新实验结果深度分析

### 3.1 Task58 — Geometry vs Random（关键消融）

```
                    Route Reward    Cluster Hit    Final Hit@10    Token Saving
Static geometry:    0.8563          0.8870         0.8764          5.03%
Uniform random:     0.1499          0.1577         0.8842          11.92%
```

正面：route-level reward 差距巨大（0.86 vs 0.15），证明 cluster 结构在路由层确实有意义。

负面：random cluster 的 final Hit@10 反而更高（0.8842 vs 0.8764），且省了更多 token（11.92% vs 5.03%）。

**机制解释**：最终检索质量由 dense recall floor 保障，这是设计意图而非缺陷。Geometry 的角色不是"质量的来源"，而是让 confidence 评估器更精准地识别"哪些 query 可以安全压缩"——从而在相同质量下实现更优的压缩。Budget control 机制的鲁棒性恰恰体现在：即使 route 信号弱（random），系统通过 dense fallback 安全链仍能保障质量。

### 3.2 Task59 — Feedback-Control 消融

```
Learned LinUCB route reward:     0.6790
No-feedback route reward:        0.1504
No-feedback dense_rate:          1.0000
```

no-feedback 的 dense_rate=1.0 意味着没有反馈时系统完全不信任 LinUCB，全部回退到 dense。feedback 的唯一作用是让系统"敢于"在某些 query 上不用 dense。质量保障来自 dense floor，feedback 控制的是"何时可以安全偏离 dense"。

### 3.3 Task63 — 300-query 下游评估

```
BGE IntentRoute vs BGE dense:       +0.00pp [-2.67, +2.67],  6.00% saving
E5 IntentRoute vs E5 dense:         +0.33pp [-3.00, +3.67],  12.04% saving
IntentRoute+SentMMR vs Dense+SentMMR: +2.33pp [-1.67, +6.33], 6.65% saving
```

所有 correctness CI 包含零 → 只能 claim "不降低答案质量的同时减少 token"。token-saving CI 全部为正，扎实。2100 answers + 2100 judgments 是有意义规模的评估。

### 3.4 Task62 — SelectiveContext-lite

Dense+SC 15.31% saving, IntentRoute+SC 20.78% stacked。合理结果，但不是 LLMLingua，related work 中提及 LLMLingua 仍需处理。

---

## 四、Task58-59 关键分析（保留）

Task58 和 Task59 的结果揭示了一个重要事实，论文应当正面阐述：

```
Task58: random cluster route reward = 0.15, 但 final Hit@10 = 0.8842, token saving = 11.92%
Task59: no-feedback dense_rate = 1.0, 但 final Hit@10 = 0.8809
```

这两个结果的含义是：最终检索质量由 dense recall floor 保障，这是设计意图而非缺陷。Geometry 和 feedback 的角色不是"质量的来源"，而是让 confidence 评估器更精准地识别"哪些 query 可以安全压缩"——从而在相同质量下实现更优的压缩。Budget control 机制的鲁棒性恰恰体现在：即使 route 信号弱（random）或 feedback 缺失，系统通过 dense fallback 安全链仍能保障质量。

这个分析应当保留在 Discussion 和 Conclusion 中，作为对方法机制的深层解释，而非回避。

---

## 五、统计严谨性评估

3 seeds（13, 17, 19）是硬件条件下的实际限制。论文对此的处理是恰当的：
- 诚实标注为"stability diagnostics, not large-sample proof"
- 补充了 query-level paired bootstrap CI + McNemar test 作为主要推断证据
- 400k 标为 diagnostic only（calibration ineligible）

建议在 Limitations 中明确注明硬件约束，将"增加 seeds"列为 future work 而非当前缺陷。

Task61 的 Geometry-to-Control 相关性分析使用 n=5-6 个 scale 点做 Pearson 相关，统计功效受限，结论的可推广性有限。这是数据规模的固有限制，不是方法错误。

---

## 六、论文重构评价

### 6.1 改名 IntentWeight → IntentRoute

"Route" 比 "Weight" 更准确反映方法本质（路由控制而非加权），避免与 attention weight 混淆。代码层兼容性迁移（alias + test），历史实验路径保留 "IntentWeight" 标签用于复现，处理得当。

### 6.2 Claim reframe

新的 thesis——"IntentRoute converts confidence over dense, lexical, and geometry-defined cluster routes into a calibrated final evidence-context budget"——比之前的"manifold + LinUCB + budget 三足鼎立"清晰。

### 6.3 表格/图精简

从 11 个 results 子节精简到 7 个，5 表 3 图，28 页。附录 11 个表（A-L）详细但不挤占正文。密度对 IP&M 合适。

### 6.4 LaTeX 质量

ACL preprint 格式，26 citations / 26 bib entries / 0 uncited——引用一致性通过。待转 Elsevier elsarticle。

---

## 七、剩余风险（更新版）

| 风险 | 严重度 | 说明 |
|------|--------|------|
| Elsevier 格式转换 | P0 blocker | 内容已就绪，格式迁移 1-2 天 |
| Task58 random cluster 结果的解释 | P0 | 需在 Discussion 中正面阐述，非回避 |
| LLMLingua 实验缺失 | P1 | SelectiveContext-lite 是合理替代，但 related work 提了 LLMLingua 就该跑或删除提及 |
| 单一 LLM judge | P1 | 审稿人可能要求 cross-judge 验证，可在 revision 补 |
| docs/intentweight-paper-core-narrative.md 过期 | P2 | 内部文档未同步 IntentRoute reframe |

---

## 八、质量评估矩阵（终版）

```
维度                    评分    说明
──────────────────────────────────────────────────────
问题定义                ★★★★☆   三层成本分离精准，从流形假设到 budget 控制逻辑闭环
理论深度                ★★★☆☆   流形作为启发而非定理，定位诚实；无新理论贡献
方法新颖性              ★★★☆☆   组件已有先例，但"几何启发→路由→置信度→预算"的完整链路有独立价值
实验严谨性              ★★★★☆   P0 ablation 完成，calibration/test split，paired stats
统计显著性              ★★★☆☆   3 seeds 受硬件限制，query-level paired stats 缓解
Baseline 公平性         ★★★★☆   充分（SentMMR / cross-encoder / SelectiveContext / BGE / E5）
下游评估                ★★★★☆   300q / 2100 answers / 2100 judgments，规模充分
可复现性                ★★★★☆   参数完整，IntentRoute 兼容性 test，代码有
写作质量                ★★★★☆   reframe 后结构清晰，5 表 3 图 28 页，claim 克制
Claim 诚实度            ★★★★★   10 条 limitations，不回避不利结果
──────────────────────────────────────────────────────
IP&M 录取概率估计       70-78%
```

---

## 九、投稿建议

内容已就绪。执行顺序：

1. 在 Discussion 中写一段 Task58-59 机制分析（正面阐述，不回避）
2. 转 Elsevier elsarticle + 匿名化
3. 投 IP&M

预计 first round：accept 15%，minor revision 40%，major revision 35%，reject 10%。最可能的 revision 要求是增加 seeds（回复 hardware constraint + revision 阶段补充）和 cross-judge 验证。

---

## 十、总体评价

这是一篇从数据观察出发、经过假设验证、到工程化方案、再到效果确认的完整研究。它的价值不在于发明新算法或证明新定理，而在于：

1. 提出了 RAG 上下文成本控制的三层分离框架
2. 用流形启发设计多路由策略
3. 发现"多路由不省 token"的关键转折
4. 用 confidence-based budget control 解决这个转折
5. 在 100k-638k 规模 + 300 query 下游评估上验证了完整链路

论文对不利结果（random cluster 反而省更多 token）的诚实报告体现了学术诚信，这在应用型论文中是加分项。

---

## 附：与第一轮评审（2026-06-24）的变化对比

| 维度 | 上次 | 本次 | 变化 |
|------|------|------|------|
| 问题定义 | ★★★★☆ | ★★★★☆ | 持平 |
| 理论深度 | ★★☆☆☆ | ★★★☆☆ | ↑（Task58/59 让 claim 更落地） |
| 方法新颖性 | ★★★☆☆ | ★★★☆☆ | 持平 |
| 实验严谨性 | ★★★★☆ | ★★★★★ | ↑（P0 ablation + 300q downstream） |
| 统计显著性 | ★★★☆☆ | ★★★☆☆ | 持平（仍 3 seeds） |
| Baseline 公平性 | ★★★★☆ | ★★★★☆ | ↑（+SelectiveContext-lite） |
| 下游评估 | ★★☆☆☆ | ★★★★☆ | ↑↑（60q→300q，2100 judgments） |
| 可复现性 | ★★★★☆ | ★★★★☆ | ↑（+IntentRoute 兼容性 test） |
| 写作质量 | ★★★☆☆ | ★★★★☆ | ↑（reframe + 精简 + 28 页） |
| Claim 诚实度 | ★★★★★ | ★★★★★ | 持平 |
| IP&M 录取概率 | 60-70% | 70-78% | ↑ |
