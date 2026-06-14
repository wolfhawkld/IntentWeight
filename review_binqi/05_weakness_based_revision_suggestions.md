# Weakness-Based Revision Suggestions

> 整理自对更新稿薄弱部分的详细修改建议。  
> 核心目标：围绕最可能导致拒稿的问题集中改稿，而不是平均用力。

---

## 总体判断

基于上一轮审稿中最薄弱的部分，建议不要平均用力，而是围绕 **4 个会真正影响接收概率的硬伤** 来改：

1. **方法 novelty 仍像组合式系统；**
2. **缺少强 baseline，尤其 reranker / compression / stronger retriever；**
3. **LLM answer-level 证据不足，目前 60-query check 只能算 sanity check；**
4. **feedback 仍是 simulated / GT-derived，不能支撑太强的 feedback-guided claim。**

下面按“问题 → 为什么危险 → 怎么具体改 → 改到什么程度”展开。

---

# 1. 先重构论文主线：不要把 novelty 压在 “manifold + LinUCB” 上

## 当前问题

现在论文的 contribution 写法还是容易被审稿人解读成：

> dense + BM25 + KMeans cluster + LinUCB + confidence top-k + simulated feedback。

这些组件单看都不是新东西。新版确实加了 calibrated budget protocol，并证明 frozen budget policies 可以在 LoTTE technology/search 上省 6–18% final evidence-context tokens，同时优于 dense-only adaptive truncation 的 Hit@10 表现；但方法叙事里 “piecewise relevance-manifold” 和 “feedback-guided multi-route controller” 仍然太抢眼，容易让审稿人期待一个更强的新算法或理论。

## 建议改法

把论文核心从：

> Feedback-guided evidence selection under a piecewise relevance-manifold assumption

改成：

> Risk-calibrated final-context budget control for RAG evidence selection

也就是说，把主贡献明确改成：

**在 dense retrieval 作为 recall floor 的前提下，学习什么时候可以安全减少最终送入 LLM 的 evidence context。**

这样更贴合你现在最强的实验证据：你已经证明 final context token 才是 LLM input cost 的关键层，并且 calibrated budget 比 dense adaptive truncation 更能避免 Hit@10 损失。

## 建议替换的贡献表述

现在的 contribution 3 可以弱化，不要把“dense + BM25 + cluster + LinUCB”写成主要创新。

建议改成：

> We propose a risk-calibrated final-context budget controller that uses multi-route retrieval confidence, cluster-local route evidence, and simulated feedback signals to decide when a smaller retrieved context is safe.

然后把 contribution 排序改成：

1. **Problem formulation:** final-context budget control under dense-level retrieval quality constraint；
2. **Method:** risk-calibrated controller using route agreement, local cluster confidence, and dense fallback；
3. **Calibration protocol:** frozen calibration/test selection of token budgets；
4. **Empirical finding:** IntentWeight avoids the Hit@10 loss of dense-only adaptive truncation at meaningful token savings；
5. **Boundary:** compression requires domain calibration; feedback is useful mainly as recovery。

这样 novelty 不再依赖“我用了 LinUCB”，而是依赖 **risk-calibrated final-context control**。

## 标题建议

当前标题里的 “Piecewise Relevance-Manifold Assumption” 风险较大，因为你的 diagnostics 只是 PCA / NearestClusterHit / ContextRetention，不是理论证明。论文自己也承认 geometry 是 diagnostic 而不是 proof。

更稳的标题可以是：

> **IntentWeight: Risk-Calibrated Final-Context Budget Control for Retrieval-Augmented Evidence Selection**

或：

> **IntentWeight: Adaptive Evidence-Context Budgeting with Dense Fallback and Feedback-Triggered Recovery**

如果你想保留 piecewise local structure，可以放到副标题或方法动机里，而不是标题核心。

---

# 2. 补强 baseline：这是最直接影响审稿分数的部分

## 当前问题

你已经补了 dense-only adaptive truncation，这是非常重要的一步。它直接证明 IntentWeight 不是简单减少 dense top-k。

但顶会审稿人还会继续问：

> 为什么不直接用 reranker？  
> 为什么不直接用 prompt/context compression？  
> 如果换强 embedding，IntentWeight 还有效吗？  
> 这个 controller 是否只是弱 dense encoder 下的补丁？

论文自己也承认目前 MiniLM-family robustness 不能证明对 stronger domain-specific encoders、rerankers、late-interaction models 成立。

## 必须新增的 baseline

### 2.1 Cross-encoder reranker + budget baseline

这是 P0。

实验设计：

1. Dense top-50 或 BM25+dense RRF top-50 作为 candidate pool；
2. 用 cross-encoder reranker 排序；
3. 取 top-k 或 token budget；
4. 和 IntentWeight 使用相同 token budget 比较。

建议至少做三个版本：

| Baseline | 设置 | 目的 |
|---|---|---|
| Dense + reranker top-10 | full context | 检查 reranker 上限 |
| Dense + reranker same-budget | 与 IntentWeight token 数相同 | 公平比较 quality-cost |
| BM25+dense RRF + reranker same-budget | 强 hybrid reranker | 排除 route fusion 弱 baseline 问题 |

主指标不要只看 Hit@10，还要看：

- MRR@10；
- nDCG@10；
- EvidenceRecall@10；
- context tokens。

如果 IntentWeight 输给 reranker，但成本更低，也可以接受；你可以把 claim 改成：

> IntentWeight is a lightweight budget controller complementary to reranking.

如果 IntentWeight 在 same-budget 下接近 reranker，那说服力会明显提升。

### 2.2 Context compression baseline

这是 P0。

相关工作里已经讨论 Selective Context、LLMLingua、LLMLingua-2、DSLR 等 context compression / refinement 方法。如果实验没有对照，审稿人会认为你只是在避开最相关的 baseline。

建议至少选一个轻量可复现 baseline：

| Baseline | 比较方式 |
|---|---|
| Dense top-10 + sentence-level MMR | 最简单、自己实现 |
| Dense top-10 + Selective Context / LLMLingua 类压缩 | 通用 prompt compression |
| Dense top-10 + sentence reranking | 接近 DSLR 思路 |
| IntentWeight + sentence-level compression | 证明可组合性 |

如果工程时间有限，我建议先做：

**Dense top-10 → sentence split → query-sentence embedding similarity → MMR → same token budget。**

这不需要复杂模型，但能作为一个强 sanity baseline。它会直接回答：

> 你的 route-aware budget control 是否比简单 sentence-level compression 更好？

### 2.3 Strong retriever baseline

这是 P0 / P1，取决于算力。

至少增加一个更强 embedding model，例如 BGE / E5 / GTE 系列中的一个。

建议表格：

| Encoder | Dense Hit@10 | IntentWeight Hit@10 | Token saving | EvidenceRecall delta |
|---|---:|---:|---:|---:|
| all-MiniLM-L6-v2 | current | current | current | current |
| multi-qa-MiniLM-L6-cos-v1 | current | current | 3.35% | lower ER |
| BGE / E5 / GTE | new | new | new | new |

这里最重要的不是必须赢 stronger encoder，而是证明：

1. 如果 dense 变强，IntentWeight 是否仍能省 final context tokens；
2. 如果 Hit@10 不能提升，是否至少能做到 non-inferior + cheaper；
3. 如果 EvidenceRecall 掉，在哪些 query 类型上掉。

## 推荐新增主表

建议把原来的 Table 15 扩展成一个真正的 **same-budget baseline table**：

| Method | Hit@10 Δ | MRR@10 Δ | nDCG@10 Δ | EvidenceRecall@10 Δ | Token saving | Cost/correct | NI pass |
|---|---:|---:|---:|---:|---:|---:|---|
| Dense top-10 | 0 | 0 | 0 | 0 | 0 | baseline | - |
| Dense adaptive truncation | current | current | current | current | current | ? | often fail |
| Dense + score-threshold budget | new | new | new | new | new | ? | ? |
| Dense + sentence MMR | new | new | new | new | new | ? | ? |
| RRF + reranker same-budget | new | new | new | new | new | ? | ? |
| IntentWeight budget | current | current | current | current | current | ? | ? |

如果只能补一个 baseline，优先补 **Dense top-10 + sentence-level MMR same-budget**，因为它最直接挑战“为什么不直接压缩 context”。

---

# 3. 把 downstream generation 从 sanity check 变成正式实验

## 当前问题

现在 Table 14 只有 60 queries。这个结果只能说明没有明显灾难性下降，但不能支撑 “answer-level cost saving” 或 “LLM input cost reduction without quality loss” 的强 claim。

论文 limitation 里也承认 60-query answer-quality check 不是 full end-to-end human evaluation。

## 具体建议

### 3.1 扩大 query 数

最低建议：

- **300 queries**：可以作为主会最低可接受版本；
- **500 queries**：比较稳；
- **1000 queries**：如果可行，会显著增强说服力。

不要只抽 easy queries。建议分层抽样：

| Query bucket | 占比 |
|---|---:|
| Dense 和 IntentWeight 都命中 | 40% |
| IntentWeight 省 token 且命中 | 20% |
| Dense 命中但 IntentWeight budget miss | 15% |
| IntentWeight 命中但 dense miss | 10% |
| 多 GT / 多证据 query | 15% |

这样可以避免审稿人质疑你只评估安全样本。

### 3.2 换成 paired answer evaluation

每个 query 生成两个答案：

- Dense top-10 context answer；
- IntentWeight budgeted context answer。

然后让 judge 比较：

1. 哪个答案更正确；
2. 哪个答案更有证据支持；
3. 哪个引用更可靠；
4. 是否存在 hallucination；
5. 是否 answerable from provided context。

建议指标：

| 指标 | 含义 |
|---|---|
| Answer correctness | 最核心 |
| Faithfulness | 答案是否被 context 支撑 |
| Citation support | 引用证据是否支持答案 |
| Context sufficiency | context 是否足够回答 |
| Hallucination rate | 是否引入 context 外信息 |
| Pairwise win/tie/loss | 比平均分更直观 |
| Cost/query | 单问题输入成本 |
| Cost/correct answer | 最有说服力的成本归一化指标 |

### 3.3 加 cost per correct answer

之前提出“乘上 LLM token 单价”的方向是对的，但要防止审稿人说“省 token 但错更多”。

所以核心指标应是：

\[
CostPerCorrect =
\frac{\sum_q Cost(q)}
{\sum_q \mathbb{1}[\text{answer correct}]}
\]

同时报告：

\[
Cost(q)=
\frac{T_{in}(q)}{10^6}p_{in}
+
\frac{T_{out}(q)}{10^6}p_{out}
\]

如果 output tokens 差异不大，可以主文报告 input-only cost，附录报告 total cost。

### 3.4 推荐主表

| Method | Answer Acc | Faithfulness | Citation support | Hallucination ↓ | Input tokens ↓ | Input cost ↓ | Cost/correct ↓ | Pairwise W/T/L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense top-10 | baseline | baseline | baseline | baseline | 1.00x | 1.00x | 1.00x | - |
| Dense adaptive truncation | ? | ? | ? | ? | lower | lower | ? | ? |
| Dense + SentMMR | ? | ? | ? | ? | lower | lower | ? | ? |
| IntentWeight conservative | current | current | current | ? | 0.93x | lower | ? | current W/T/L |
| IntentWeight calibrated budget | new | new | new | new | 0.82–0.94x | lower | target best | new |

这样 “LLM input cost saving” 就不再只是 retrieval proxy，而是 end-to-end supported。

---

# 4. 修正 Table 15 的统计与 calibration eligibility 问题

## 当前问题

Table 15 是新版最关键结果，但有两个风险：

1. **400k 的 Calibration eligible = False**，但表中仍然报告 +2.32 pp / 6.57% saving；
2. 638k 虽然省 17.53%，但 Hit delta 是 -0.08 pp，严格 non-inferiority 是否成立要看 CI。

如果不解释，审稿人会认为你在挑选有利 operating point。

## 具体建议

### 4.1 把 Table 15 拆成两张表

**主文表只放 eligible=True 的政策：**

| Scale | Policy | Eligible | Hit Δ | Token saving | NI pass |
|---|---|---:|---:|---:|---:|
| 100k | r0.95_m4 | True | +0.00 | 6.18% | ? |
| 200k | r0.85_m4 | True | +1.20 | 16.00% | ? |
| 638k | r0.85_m4 | True | -0.08 | 17.53% | ? |

**附录表放所有 searched policies，包括 400k：**

| Scale | Policy | Eligible | Why selected/reported | Interpretation |
|---|---|---:|---|---|
| 400k | r0.98_m4 | False | diagnostic frontier point | not part of strict main claim |

这样可以避免 reviewer 抓住 400k 说主结果不干净。

### 4.2 明确 non-inferiority margin

必须设定一个预注册式 margin，例如：

- Hit@10 non-inferiority margin：δ = 1.0 pp；
- EvidenceRecall margin：δ = 2.0 pp；
- Faithfulness margin：δ = 0.1 / 5-point scale；
- Answer accuracy margin：δ = 1–2 pp。

然后写：

> A policy is eligible only if the lower bound of paired bootstrap CI for Hit@10 delta is above -δ on calibration.

或者更清楚：

\[
LCB_{\text{cal}}(\Delta Hit@10) \ge -\delta
\]

不要只说 “Calibration eligible=True/False”，要给公式和阈值。

### 4.3 增加 query-level paired statistics

现在的 seed-level result 不足以强支撑。建议对每个 scale 报告：

| Scale | Dense wins | IntentWeight wins | Ties | McNemar p | Paired bootstrap CI | Token-saving CI |
|---|---:|---:|---:|---:|---|---|
| 100k | ? | ? | ? | ? | ? | ? |
| 200k | ? | ? | ? | ? | ? | ? |
| 638k | ? | ? | ? | ? | ? | ? |

对于 Hit@10，最关键的是 discordant cases：

- Dense hit, IntentWeight miss；
- Dense miss, IntentWeight hit。

如果 638k 的 -0.08 pp 只是 1 个 query 的差异，那可以解释为 practically non-inferior；如果是多个 query 且集中在某些 types，就要做 failure bucket。

### 4.4 把 claim 改成更审稿友好的形式

不要写：

> IntentWeight preserves dense-level Hit@10 across all scales.

更稳的是：

> IntentWeight exposes eligible operating points that reduce final evidence-context tokens by 6–18% while avoiding the larger Hit@10 losses observed under dense-only adaptive truncation; strict non-inferiority is scale-dependent.

这个说法与你当前摘要和结果一致，也不容易被攻击。

---

# 5. Feedback 部分：降级为 recovery mechanism，同时补更真实的模拟

## 当前问题

论文现在说 simulated feedback 可以作为 controlled recovery mechanism，并且 Table 18/19 的确显示了一些 recovery 效果。但 calibration-to-test generalization 很小，甚至可能有负向情况。

因此，如果标题或摘要强调 “feedback-guided”，审稿人会期待更多真实反馈证据。现在最稳的处理方式是：

> Feedback is not first-pass improvement; it is a recovery and risk-control signal.

## 具体建议

### 5.1 主文中把 feedback claim 改窄

建议替换为：

> Simulated feedback is used to study whether the controller can identify risky local regions after compression failures. We treat feedback as a post-failure recovery trigger rather than evidence of first-pass generalization under real users.

### 5.2 增加 delayed / noisy / click-biased feedback 实验

不一定需要真实用户日志，但至少要比 GT-derived feedback 更接近现实。

建议设计四种 feedback setting：

| Feedback setting | 模拟方式 | 目的 |
|---|---|---|
| Oracle GT feedback | 当前上界 | 机制上限 |
| Noisy feedback | 10 / 20 / 30 / 40% label noise | 鲁棒性 |
| Delayed feedback | delay = 5 / 20 / 100 queries | 真实交互延迟 |
| Click-biased feedback | position bias + false click + no-click | 真实隐式反馈 |
| Adversarial feedback | 一小部分用户反向标注 | 安全性 |

主指标不要只看 Hit@10，要看：

- risky-arm precision；
- recovery rate；
- false fallback rate；
- token saving retained；
- feedback-induced regressions；
- delayed recovery latency。

### 5.3 不要只报告 recovered，也要报告 harmed

建议增加：

| Policy | Affected queries | Recovered | Still missed | New regressions | Net Hit Δ | Token saving |
|---|---:|---:|---:|---:|---:|---:|

尤其是 feedback-triggered fallback 可能会牺牲 token saving，甚至影响无关 query。需要展示安全边界。

### 5.4 用 risk predictor 替代 arm boost

现在的 arm boost 容易被质疑太 heuristic。建议改成：

\[
P(\text{compression failure} \mid q, a, C)
\]

输入：

- query features；
- selected arm；
- route confidence；
- dense / cluster disagreement；
- previous failures in same arm；
- token budget；
- evidence score gap。

输出：

- 是否 fallback；
- 是否使用 conservative budget；
- 是否禁用 aggressive compression。

这样 feedback 部分就从“boost arm”变成“learn failure risk”，更像论文贡献。

---

# 6. 方法部分要补可复现细节，否则系统论文会被扣分

## 当前问题

方法里写了 feature vector 包括 query embedding projections、route confidence signals、local geometry signals，但没有完整列出 feature 维度、归一化、阈值、融合方式和 policy 名称含义。

这会导致 reviewer 认为：

> 结果可能来自手工调参；方法难复现；calibrated policy 是黑箱。

## 具体建议

### 6.1 加一个 feature table

建议在方法或附录加入：

| Feature group | Feature | Dim | Normalization | Used by |
|---|---|---:|---|---|
| Query embedding | PCA projection / raw projection | p | z-score | LinUCB |
| Dense confidence | top1 score, top1-top2 gap, entropy | 3 | min-max | budget |
| BM25 confidence | top1 BM25, BM25 gap | 2 | z-score | budget |
| Route agreement | overlap dense/BM25/cluster | 3 | [0,1] | budget |
| Cluster geometry | nearest cluster rank, centroid sim | 2 | [0,1] | LinUCB |
| Drift | query-centroid distance / route disagreement | 1 | thresholded | fallback |
| Budget state | selected k/token budget | 1 | categorical | policy |

### 6.2 明确 policy 名称

Table 15 里的 `token_budget_r0.95_m4`、`r0.85_m4`、`r0.98_m4` 必须解释清楚。

例如：

- `r` 是否是 recall-retention threshold？
- `m4` 是否是 minimum 4 chunks？
- 预算是按 chunk 数还是 token 数？
- threshold 是 calibration set 学来的还是预设？
- 如果 `r0.98_m4` calibration eligible=False，为什么还报告？

建议新增一段：

> A budget policy token_budget_rX_mY keeps the smallest prefix whose cumulative calibrated confidence exceeds X, subject to at least Y evidence units. Eligibility requires calibration Hit@10 lower confidence bound ≥ dense Hit@10 − δ.

如果实际不是这个含义，就按真实定义写，但必须让读者无需看代码也能复现。

### 6.3 给完整伪代码

建议补一个更具体的 budget selection pseudocode：

```text
Input: fused ranking R, route scores S, dense fallback score d, policy π
for candidate budget b in B = {4, 6, 8, 10} or token budgets:
    C_b = truncate(R, b)
    risk_b = Risk(q, C_b, S)
select smallest b such that risk_b ≤ ε
if low confidence or high drift:
    return dense top-10
else:
    return C_b
```

### 6.4 补充超参表

| Hyperparameter | Value | Selected on | Sensitivity |
|---|---:|---|---|
| # arms | 32 | fixed | add appendix |
| LinUCB α | ? | calibration | needed |
| λ cost penalty | ? | calibration | needed |
| trust weights | ? | simulated setting | needed |
| BM25 k1/b | ? | fixed | needed |
| RRF k | ? | fixed | needed |
| dense top-N | ? | fixed | needed |
| cluster top arms | ? | fixed | needed |
| fallback drift threshold | ? | calibration | needed |

这类表对顶会审稿很重要，因为你是系统 / 实验型论文。

---

# 7. Evidence completeness 要从 limitation 变成正式分析

## 当前问题

主指标还是 Hit@10，但 Hit@10 只说明至少一个 relevant chunk 出现在 final context，不代表完整 evidence collection。context compaction 可能保留 Hit，但降低 EvidenceRecall@10。

这在 RAG QA 里可以接受，但如果 reviewer 关注多证据任务，会质疑：

> 你省 token 的代价是不是丢了完整证据？

## 具体建议

### 7.1 主表加入 EvidenceRecall delta

不要只在附录或 limitation 提 EvidenceRecall。主表应加：

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 | Tokens |
|---|---:|---:|---:|---:|---:|

特别是 calibrated budget policies 和 dense adaptive truncation 都要报告 EvidenceRecall。

### 7.2 分 multi-evidence query

把 query 分成：

- |GT| = 1；
- |GT| = 2–3；
- |GT| ≥ 4。

报告每组：

| GT count bucket | Hit Δ | EvidenceRecall Δ | Token saving |
|---|---:|---:|---:|

如果 IntentWeight 主要在 |GT|=1 上安全，在 |GT|≥4 上 risky，这不是坏事。你可以写成：

> IntentWeight is appropriate for usable-evidence RAG, but should disable compression for complete-evidence workflows.

### 7.3 加 citation support

如果做 downstream generation，citation support 是 EvidenceRecall 和 answer quality 之间的桥。建议让 judge 判断：

- answer claims 是否由 selected context 支持；
- cited chunk 是否包含 required evidence；
- compressed context 是否遗漏 necessary evidence。

这比单纯 answer score 更可信。

---

# 8. 外部有效性：LoTTE science 还不够，至少再补一个非 LoTTE 数据

## 当前问题

LoTTE science/search 是有价值的第二域验证，但仍是 LoTTE family。论文自己也说 science/search strengthen external validity but does not replace evaluation on additional vertical corpora。

## 具体建议

### 8.1 至少加一个非 LoTTE vertical corpus

选择标准：

- 有 query-qrels；
- passage-level evidence；
- domain terminology 明显；
- 不需要完整法律审查式 exhaustive evidence。

候选类型：

| 类型 | 价值 |
|---|---|
| Biomedical QA retrieval | 术语密集，适合 lexical + dense |
| Technical documentation QA | 接近 production RAG |
| Enterprise FAQ / product support | workflow/entity structure 明显 |
| Finance / compliance QA subset | 需要谨慎，但有 domain value |

如果时间不够，不必大规模。可以做：

- 1 个非 LoTTE corpus；
- 100k chunks 或可用全量；
- 300–500 queries；
- 只跑 dense、dense adaptive、IntentWeight budget、one compression baseline。

### 8.2 明确“domain calibration”的实验结论

Science/search 的结果说明 aggressive budget 在 100k science 上并不稳。不要硬包装成泛化成功。

建议写成：

> Ranking-side gains transfer, but budget strength does not. Domain calibration is required.

这反而会让论文更可信。

---

# 9. 统计显著性：把“工程稳定性”升级成“审稿可接受证据”

## 当前问题

论文 limitation 里承认 seed count 和 400k variance 问题，三 seed CI 只能算 engineering stability diagnostics，不应被过度解释为强统计显著性 proof。

## 具体建议

### 9.1 Paired bootstrap

对每个 query 采样，保留 Dense 和 IntentWeight 的 paired relation，重复 10k 次，报告：

- Hit@10 delta CI；
- EvidenceRecall delta CI；
- token saving CI；
- cost/correct answer CI。

### 9.2 McNemar test

对 Hit@10 这种二元 paired outcome，报告：

| | IntentWeight hit | IntentWeight miss |
|---|---:|---:|
| Dense hit | both hit | dense-only win |
| Dense miss | IW-only win | both miss |

然后 McNemar test 看 discordant pairs。

### 9.3 Non-inferiority + superiority 分开

不要混在一起：

- Quality：non-inferiority；
- Cost：superiority。

主 claim 应是：

> Quality non-inferior, cost superior.

这比“Hit@10 improves”更稳。

---

# 10. 论文表达上要减少“防御性堆叠”，增加“决策图”

## 当前问题

新版很谨慎，但有些地方 limitation / guardrails 写得较多，会让论文显得防御。建议把这些内容结构化，而不是散落在摘要、引言、讨论、附录。

## 具体建议

### 10.1 增加一张 decision map

画一个简单图：

```text
Query
  ↓
Dense/BM25/cluster retrieval
  ↓
Route agreement + confidence
  ↓
Is budget policy calibrated for this domain/scale?
  ├── no → dense top-10 fallback
  └── yes
       ↓
    Is risk low?
       ├── yes → compact context
       └── no → dense fallback / conservative budget
  ↓
Feedback after failure?
       ├── yes → mark risky region, safer retry
       └── no → normal flow
```

这张图会比大量文字更清楚地说明：

- dense 是 recall floor；
- compression 是 conditional；
- feedback 是 recovery；
- domain calibration 是 prerequisite。

### 10.2 加一张 “what is claimed / not claimed” 表

| Claim | Supported? | Evidence |
|---|---|---|
| Final context tokens can be reduced under calibrated policy | Yes | Table 15 |
| Dense adaptive truncation causes larger Hit loss | Yes | Table 15 |
| Fixed top-10 ranking gains transfer to science/search | Partially | Table 16 |
| Aggressive budget transfers without calibration | No | Table 17 |
| Real human feedback works | Not shown | simulated only |
| Generated answer quality is non-inferior | Not fully | 60-query sanity only |
| IntentWeight replaces dense retrieval | No | dense fallback retained |

这张表能显著降低 reviewer 误解，也能让论文显得成熟。

---

# 11. 最推荐的改稿优先级

| 优先级 | 修改 | 为什么最重要 | 最低可接受版本 |
|---:|---|---|---|
| P0 | 加 compression baseline | 直接回应“为什么不用现有 context compression” | Dense top-10 + sentence MMR same-budget |
| P0 | 加 reranker baseline | 回应强检索系统质疑 | Dense/RRF top-50 + cross-encoder reranker |
| P0 | 扩大 answer-level evaluation | 支撑 LLM input cost claim | 300–500 queries, paired judge |
| P0 | 修正 Table 15 calibration claim | 避免被质疑 cherry-picking | 主表只放 eligible=True，400k 放 diagnostic |
| P0 | Query-level paired stats | 把结果从趋势变成统计证据 | McNemar + paired bootstrap |
| P1 | 更真实 feedback simulation | 降低 simulated feedback 硬伤 | delayed/noisy/click-biased feedback |
| P1 | 补方法细节 | 提高可复现性 | feature table + hyperparam table + pseudocode |
| P1 | 多证据 / EvidenceRecall 分析 | 防止 Hit@10 掩盖 evidence loss | 按 |GT| 分桶 |
| P1 | 非 LoTTE corpus | 提高外部有效性 | 一个额外 vertical corpus |
| P2 | 改标题和 contribution wording | 降低 novelty 过度包装风险 | 从 manifold 改到 budget control |

---

# 12. 如果只能做 3 件事

## 第一件：加 Dense top-10 + sentence-level MMR same-budget baseline

这是性价比最高的 baseline。它直接挑战你的核心：

> 是否真的需要 IntentWeight，还是简单 sentence compression 就够了？

如果你赢了，论文说服力大幅提升。  
如果你输了，也可以改成 “IntentWeight is complementary to compression”，但主 claim 要收窄。

## 第二件：把 downstream evaluation 扩到 300–500 queries

这能把 “LLM input token cost saving” 从 proxy 变成真正 answer-level claim。现在 60-query check 不能支撑强结论。

## 第三件：把 Table 15 改成 strict calibration/test + paired NI

现在 Table 15 已经是论文最强结果，但 400k eligible=False 和 scale-dependent NI 是潜在攻击点。你需要把它处理干净：

- eligible=True 才进主表；
- 400k 作为 diagnostic；
- paired bootstrap；
- McNemar；
- non-inferiority margin 预设。

---

# 13. 建议的最终论文定位

建议最终把论文定位成：

> **IntentWeight is not a new retriever and not a universal dense replacement. It is a lightweight, risk-calibrated final-context budget controller for RAG systems. It uses route confidence and feedback-derived risk signals to decide when smaller evidence context is safe, and when dense fallback or recovery is required.**

中文就是：

> 它不是新检索器，而是一个用于 RAG 的最终上下文预算控制器。核心价值是：在 dense recall floor 存在的情况下，判断什么时候可以少给 LLM context、什么时候必须保守。

这个定位最符合当前证据，也最能避开 novelty 过度包装的风险。

如果这些修改完成，我对接收风险的判断会从：

> Borderline / Weak Reject

提升到：

> Borderline / Weak Accept

但前提是新增 baseline 和 answer-level evaluation 结果不能明显不利。如果 compression baseline 或 reranker baseline 明显优于 IntentWeight，那么论文仍可保留，但主 claim 必须改为：

> IntentWeight is a lightweight, reranker/compression-compatible controller rather than a replacement for stronger evidence refinement methods.
