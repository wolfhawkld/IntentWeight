# IntentWeight v2 Full Assessment

**日期**: 2026-06-11
**审阅范围**: pre_validation 分支 03791af，对比 v1.1 (3c6f2e5) 至今全部新增内容
**新增实验**: Task37 (context-budget optimization) / Task38 (calibrated context-budget) / Task39 (cross-domain) / Task40 (feedback recovery)
**新增文档**: review_binqi/ 外部审阅 / docs/intentweight-paper-core-narrative.md / docs/IntentWeight_Optimization_Guide_20260608.md

---

## 一、总体判断

**v2 是质的飞跃。论文从一个防御性的 "4.8% token saving with bounded claim" 工作，变成了拥有多层证据链、跨域验证、反事实基线、统计检验和失败恢复机制的完整故事。投稿就绪度从 "可以投" 提升到 "有竞争力"。**

---

## 二、v1.1 → v2 关键变化评估

| 维度 | v1.1 | v2 | 评价 |
|------|------|-----|------|
| Token saving 主效应 | 4.7-5.3% (Task29-C fixed k=8/10) | 6-18% (calibrated token-budget, frozen policy) | 效应量翻倍以上 |
| 统计检验 | 3-seed CI only | query-level paired bootstrap + McNemar + Wilcoxon + NI test | 直接回应外部审阅 |
| 跨域验证 | 无（仅 technology/search） | + LoTTE science/search 20k + 100k | 消除最大外部效度风险 |
| 反事实基线 | 无 | Dense adaptive truncation（同 budget 规则应用于 dense ranking） | 排除 "只是 dense top-k 截断" 的替代解释 |
| 失败恢复 | 无 | Task40 feedback recovery（30% pooled conservative recovery） | 全新贡献维度 |
| Test-set selection bias | 无防御 | Task38 calibration/test split（179 cal / 417 test） | 方法论严谨性显著提升 |
| 成本定位 | "retrieved chunk tokens" | "final LLM evidence-context input tokens" | 与 LLM inference 成本直接挂钩 |
| Context-budget 机制 | 固定 k=8/10（mid_k=10 实为 no-op） | Per-query token budget（保前 5 chunks，尾部按 95% budget 裁剪） | 机制更合理，效果更强 |
| Core narrative | RAG-specific retrieval controller | Feedback-guided evidence selection over manifold-structured domain data | 理论定位通用化 |

### 各新增实验逐项评价

**Task37（Context-Budget Optimization）— 优秀**

最关键的改进。Token-budget policy 比固定 k=8 更聪明：保留前 5 chunks，仅当尾部超出 query-specific 95% budget 时才裁剪。直接解决了之前 review 中 "mid_k=10 no-op" 问题。Token saving 从 ~5% 提升到 ~7-9%，Hit@10 仍在 dense 水平或之上。Dense adaptive baseline 排除了最明显的 alternative explanation。四个 scale 全部验证。

**Task38（Calibrated Context-Budget）— 很好**

179 calibration / 417 test 的 split 有效防御了 test-set selection bias。200k 和 638k 的 frozen-test saving 达到 16-17.5%。400k 的 calibration 没找到 eligible policy 但 fallback 仍表现好，这种诚实报告是正确做法。

**Task39（Cross-Domain）— 重要且诚实**

Science/search 的加入直接回应了之前 review 中 "单一 domain" 的问题。20k/q200 结果很强（+3.17pp Hit, 13-14% saving），100k 结果更保守但仍 positive。论文诚实地报告了 "compression strength must be domain-calibrated"，比 overclaim universal transfer 更可信。

**Task40（Feedback Recovery）— 新颖**

完全新的贡献维度。30% pooled recovery rate 给了论文一个 v1 没有的故事线：feedback 不只是改善 routing，还能修复 compression 导致的失败。Calibration-to-test generalization 结果弱但诚实，定位为 "controlled fallback trigger" 而非 "universal improvement" 是正确的。

---

## 三、v1 review 14 项问题的解决状态

| # | 原问题 | 是否解决 | 如何解决 |
|---|--------|---------|---------|
| 1 | 400k token saving CI 异常宽 | ✅ 缓解 | Task37 scale extension 提供了新的 400k 数据点（9.44% saving），且有 paired significance |
| 2 | Task29-C 选择缺乏 rationale | ✅ 解决 | Task29-C 降级为 conservative baseline，Task37/38 token-budget 成为主 result |
| 3 | "Above-dense" claim 需 CI 限定 | ✅ 保持 | 措辞统一为 "mean above dense"，paired NI test 提供更强统计支撑 |
| 4 | No-feedback ablation 行困惑 | ⚠️ 部分 | 正文有解释但 table caption 仍不够自解释 |
| 5 | evidence_recall 下降 | ✅ 解决 | Discussion §6.5 + Limitations §7.4 明确定位为 expected tradeoff |
| 6 | 单一 LLM judge | ✅ 保持 | 定位为 sanity check，移到 appendix |
| 7 | Multi-QA token saving 低 | ✅ 保持 | 解释为 stronger baseline effect |
| 8 | 单一 domain | ✅ 解决 | Task39 science/search 跨域验证 |
| 9 | Manifold 术语不友好 | ⚠️ 部分 | Core narrative 文档有改善但 abstract 仍未加直觉解释 |
| 10 | mid_k=10 no-op / compact rate 误导 | ✅ 解决 | Task37 token-budget 替代了固定 k 机制 |
| 11 | Multi-epoch 披露 | ✅ 解决 | Method §3.8 + Setup §4.4 明确说明 |
| 12 | drift_threshold 实际禁用 | ⚠️ 未提及 | 论文中仍未 acknowledge drift 在 LoTTE 上不活跃 |
| 13 | Hybrid lite 仍做全量 dense | ✅ 解决 | Task37 architecture clarification 明确了 LinUCB 角色 |
| 14 | n_clusters=32 未解释 | ⚠️ 部分 | Method §3.4 说了 "fixed arm count for comparability" 但未给出为什么是 32 |

---

## 四、关键修改建议

### [高优先级] 1. 明确 LLM inference 成本放大效应

**问题**: 论文的 cost metric 已从 "retrieved chunk tokens" 转向 "final LLM evidence-context input tokens"，但这个 framing shift 的经济学意义没有被显式量化。审稿人可能仍然质疑 "5-18% saving 有什么用"。

**建议**: 在 Introduction（contribution list 之前）和 Discussion §6.6 中各加一句：

Introduction:
> "Because these retrieved chunks enter the LLM generator as input tokens, every percentage point of evidence-context reduction translates directly into a proportional reduction in per-query inference cost — a recurring saving that scales linearly with query volume in deployed systems."

Discussion §6.6:
> "The measured 6-18% evidence-context token reduction applies to the most expensive component of the RAG pipeline: LLM input tokens. At enterprise query volumes (10k+ queries/day), even the conservative 6% frozen-policy saving corresponds to meaningful cumulative inference cost reduction. More aggressive calibrated policies on some scales save 16-18%, amplifying this effect further."

这一点是论文 practical significance 的核心论证，不能只隐含在 "final LLM evidence-context input tokens" 的措辞中。

### [高优先级] 2. Abstract 瘦身至 ~200 words

**当前**: ~280 words，塞入了 conservative + calibration/test + cross-domain + recovery + geometry + smoke test。

**建议删减**:
- 删除 generation smoke test 句（"A 60-query downstream generation smoke test..."）→ 移到 Introduction
- 压缩 cross-domain 为半句（"and generalizes to a second LoTTE domain with domain-calibrated compression"）
- Recovery 压缩为一句（"Feedback-driven recovery can repair a meaningful fraction of compression-induced tail failures"）

**目标结构**（~190 words）:
1. Problem（2 句）
2. Method（2 句）
3. Scope limitation（1 句）
4. Main quantitative result：conservative + calibrated（2 句）
5. Cross-domain + recovery（1 句）
6. Positioning（1 句）

### [高优先级] 3. 理清 Task29-C vs Task37/38 的主次关系

**问题**: Results §5.1 报 Task29-C conservative (4.7-5.3%)，§5.3 报 Task38 calibrated (6-18%)。读者可能困惑哪个才是 main result。

**建议**:
- §5.1 改为 **"Main Token-Quality Frontier"**，直接以 Task37/38 calibrated budget 为主表
- Task29-C 降级为 §5.1 的一行 "conservative confidence-only baseline" 对比
- 或者把 §5.1 改为 "Conservative Baseline"，§5.3 改为 "Main Calibrated Result"，但这样读者要等到第 3 节才看到最强结果，不理想

最佳方案：**§5.1 直接展示 calibrated budget 作为 main result**，附带 conservative baseline 对比行和 dense adaptive truncation baseline 对比行。一张表讲完核心故事。

### [高优先级] 4. Results 重组：main body vs appendix

**当前**: §5.1-5.11 共 11 个 subsection，信息密度过高。

**建议 main body**（6 sections）:
- §5.1 Main calibrated token-quality frontier（Task38 + dense adaptive baseline）
- §5.2 Cross-domain validation（Task39 science/search）
- §5.3 Component ablation（Task33.3 ablation table）
- §5.4 Feedback-driven adaptation + recovery（合并 §5.6 和 §5.7）
- §5.5 Geometry diagnostics
- §5.6 Limitation cases（eManual/CUAD + domain calibration boundary）

**建议 appendix**:
- Seed stability tables + 5-seed extension
- Conservative baseline (Task29-C) detail
- Encoder robustness
- Downstream generation smoke
- Fixed-k compression frontier

### [中优先级] 5. 内部 task 编号全文清理

**当前仍存在的内部编号**:
- Method §3.9: "Task28 showed that..."
- Discussion §6.2: "Task29-C is intentionally conservative"
- Conclusion: "Under the conservative Task29-C policy"
- Results 多处: "Task33.6", "Task33.1a", "Task30"

**建议**: 建立命名映射表并全文替换：

| 内部编号 | 论文名称 |
|---------|---------|
| Task29-C | conservative confidence policy |
| Task37/38 | calibrated token-budget policy |
| Task33.3 | component ablation |
| Task33.6 | five-seed robustness check |
| Task33.1a | encoder robustness check |
| Task30 | geometry scale diagnostic |
| Task40 | feedback recovery experiment |

### [中优先级] 6. Ablation table "No feedback" 行的自解释性

**建议**: 在 Table 5 的 "No feedback gated" 行的 Role 列改为 "Dense-only fallback (no learning)" 或在 table caption 加注：

> "The no-feedback gated row shows the system with feedback disabled; its high Hit@10 reflects full dense fallback (dense rate = 1.0), not learned route efficiency."

### [低优先级] 7. Abstract 中 manifold 术语加直觉解释

**当前**: "piecewise relevance-manifold assumption"（opaque）

**建议**: 在首次出现后加半句：
> "motivated by a piecewise relevance-manifold assumption — i.e., that query-document relevance in vertical domains exhibits exploitable local cluster structure"

### [低优先级] 8. Discussion 中 acknowledge drift threshold 不活跃

**建议加一句**: "On LoTTE, semantic drift rarely exceeds the configured threshold, so routing decisions are primarily confidence-driven. In more heterogeneous query distributions, drift-based fallback would become more active."

### [低优先级] 9. n_clusters=32 给出简要 justification

**建议在 Method §3.4 补一句**: "We use 32 arms as a practical balance between routing granularity and per-arm sample size; sensitivity to arm count is left to future work."

---

## 五、论文叙事评价

### Core Narrative 文档（docs/intentweight-paper-core-narrative.md）

这份文档是整个项目最清晰的定位表述。One-sentence thesis 精准：

> IntentWeight 是一个面向结构化垂类知识载体的反馈驱动证据选择控制器：它在 dense recall floor 之上结合 lexical anchor、局部几何路由和 LinUCB feedback adaptation，在保持答案可用证据召回的同时，动态控制最终送入 LLM 的 context token 成本，并为压缩导致的尾部失败提供反馈恢复路径。

建议后续写作严格对照此文档。

### LLM Inference Cost Amplification（未充分利用的论证线）

v2 的最重要但最被低估的 framing 改进是 **cost metric 从 "retrieved tokens" 到 "LLM evidence-context input tokens" 的转变**。这不只是命名变化 — 它改变了 contribution 的经济学意义：

- Retrieved chunk token 本身几乎无成本（本地向量搜索的边际成本极低）
- 但这些 chunk 一旦进入 LLM context window，就按 input token 定价
- 垂类系统的 daily query volume 一旦上规模，每个百分点的 LLM input saving 都是可观的 recurring cost reduction
- 这是 per-query multiplicative saving，不是一次性优化

论文中 Task37/38 已经在用 "final LLM evidence-context input tokens" 措辞，但 Introduction 和 Discussion 还没有显式量化这个放大效应。这是当前最被低估的 practical significance 论证点。

---

## 六、外部审阅 (review_binqi) 回应状态

| review_binqi 建议 | 是否执行 | 备注 |
|------------------|---------|------|
| Query-level paired test | ✅ Task37-C | McNemar + Wilcoxon + bootstrap NI |
| Non-inferiority framing | ✅ | 1pp NI check on all scales |
| 扩大 query 数 | ⚠️ 部分 | 仍是 596 queries，但加了 cross-domain |
| Calibrated adaptive-k | ✅ Task37 | Token-budget 替代固定 k |
| Dense adaptive baseline | ✅ Task37-D | 同 budget 规则应用于 dense |
| Stratified evaluation | ❌ 未做 | Future work 级别 |
| More LoTTE domains | ✅ Task39 | science/search |

review_binqi 的核心建议（paired test + NI framing + calibrated k + dense baseline）已全部执行。Stratified evaluation 是 nice-to-have，不阻塞投稿。

---

## 七、最终结论

**投稿就绪。** 当前 blocking items 全部是写作层面的：

1. LLM inference cost amplification 需要在 Introduction + Discussion 中显式量化
2. Abstract 瘦身到 ~200 words
3. Task29-C vs Task37/38 主次关系理清
4. Results 11 个 subsection 重组为 6 main + appendix
5. 内部 task 编号全文清理

核心 claim 现在比 v1 更强且防御更扎实：

> IntentWeight 在 LoTTE technology/search 100k-638k 上，通过 calibrated token-budget policy 可节省 6-18% final LLM evidence-context input tokens（calibration/test frozen policy），同时保持 dense-level Hit@10 且优于 dense-only adaptive truncation。LoTTE science/search 验证了 ranking-side generalization，feedback-driven recovery 可修复约 30% 的 compression-induced tail failures。Dense 仍是 recall floor，compression strength 需按 domain 校准。

---

*审阅完成日期: 2026-06-11*
*审阅深度: 全部新增实验 summary + 论文 full_draft 更新 + 外部审阅对照 + core narrative 评估*
