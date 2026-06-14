# Updated Paper Review

> 整理自对更新稿 `main(1).pdf` 的正式审稿意见。  
> 评审口径：顶级 AI / 机器学习 / NLP 学术会议审稿标准。

---

## 一句话总体评价

这篇更新稿已经从“收益偏低的 RAG 路由组合”提升为一个较完整的 **bounded quality-cost controller** 论文，但顶会层面仍受限于方法 novelty 偏组合式、真实 end-to-end 生成验证不足、反馈仍为模拟、强 baseline 仍不充分，因此目前更接近 **Borderline，偏 Weak Reject**。

---

## 主要优点

### 1. 主 claim 比上一版明显更合理

新版不再只强调 4.7–5.3% 的 conservative saving，而是加入了 **calibration/test context-budget protocol**：在 calibration queries 上选择预算策略，并冻结后在 test queries 上评估。这个设计比直接调 test set threshold 更严谨，也更容易支撑“质量-成本前沿”这一叙事。

主结果显示 IntentWeight 在 LoTTE technology/search 上可节省约 6–18% final evidence-context tokens，并相较 dense-only adaptive truncation 保留更多 Hit@10。

### 2. 新增 dense-only adaptive truncation baseline 是重要改进

上一版最大的质疑是：IntentWeight 是否只是 dense top-k 减少。新版用 dense-only adaptive truncation 作为直接对照，显示 dense adaptive 往往能省更多 token，但在所有 LoTTE technology/search scale 上都有 Hit@10 loss。

例如：

- 200k 下 IntentWeight：+1.20 pp / 16.00% saving；
- dense adaptive：-2.40 pp / 21.95% saving。

这个对照显著增强了论文的说服力。

### 3. 跨域验证比上一版更可信

新增 LoTTE science/search 作为第二域验证是有价值的。science/search fixed top-10 ranking 在 20k/q200 和 100k 上分别有 +3.17 pp 和 +1.51 pp Hit@10 提升，说明 ranking-side effect 不是完全局限于 technology/search。

论文也承认 context-budget strength 不能直接跨域迁移，需要 domain calibration，这种克制表述是优点。

### 4. Feedback recovery 的定位比单纯“反馈提升”更可信

新版把 feedback 作用从“泛化提升”收窄为 **post-feedback repair / recovery mechanism**。这比声称 simulated feedback 能直接提升 first-pass generalization 更严谨。

Table 18 显示 arm boost + conservative budget 在 science 100k 上恢复 14/34 affected queries，在 technology 100k 上恢复 9/42 affected queries；pooled conservative retry recovery 约 30%。这个结果虽然不是强泛化证明，但作为 tail failure recovery 证据是有意义的。

### 5. 论文自我约束明显增强

新版明确区分：

1. source candidate cost；
2. dense invocation rate；
3. final context tokens。

并强调主效率 claim 只基于最终进入 generator 的 evidence-context input tokens。它还明确说明 simulated feedback、60-query generation check、geometry diagnostics、KMeans arms、encoder/domain coverage 都是限制。这种边界意识比上一版更成熟。

---

## 主要问题

### 1. 核心创新仍偏组合式，方法 novelty 不够强

IntentWeight 仍然是以下组件的组合：

- dense retrieval；
- BM25；
- KMeans cluster routing；
- LinUCB；
- trust weighting；
- confidence-based budget control。

新版虽然增强了实验，但方法本身没有形成一个真正新的建模范式。例如 calibrated token-budget policy 很有用，但它更像系统策略和实验协议，而不是新的算法贡献。

论文贡献列表中“multi-route controller + trust-weighted LinUCB + confidence compaction”仍容易被审稿人认为是已有模块的工程组合。

这会影响接收概率，因为顶会审稿人通常会问：

> 为什么这不是 adaptive retrieval + contextual bandit + top-k budget policy 的直接组合？

### 2. 主实验仍主要依赖 LoTTE，外部有效性有限

虽然新增 science/search，但它仍属于 LoTTE family。technology/search 是主正向证据，science/search 是第二域验证，PubMedQA / Banking77 / eManual / CUAD 仍主要是 supporting 或 boundary cases。

因此，“structured vertical-domain evidence selection”这个 broader claim 仍然偏大。更准确的表述应是：

> 在 LoTTE-style retrieval-backed QA 上，IntentWeight 展示了一个可行的 bounded quality-cost frontier。

而不是泛化到广义 vertical-domain knowledge agents。

### 3. Calibrated budget 结果有说服力，但仍不够稳

Table 15 是新版最关键结果，但也暴露了问题：

- 100k：+0.00 pp / 6.18% saving；
- 200k：最强；
- 400k：+2.32 pp / 6.57% saving，但 **Calibration eligible = False**；
- 638k：-0.08 pp / 17.53% saving。

也就是说，严格 non-inferiority 并非全 scale 成立。400k 的 calibration eligibility 问题尤其需要解释，否则主表中最强 Hit gain 之一会被认为不干净。

### 4. 下游生成评估仍然太弱

新版仍只有 60-query downstream answer-quality check。这个结果只能说明“没有明显灾难性下降”，不能证明 answer-level quality non-inferior。

如果论文要强调 LLM input cost reduction，就必须更正式地评估：

- answer correctness；
- faithfulness；
- citation support；
- cost per correct answer。

现在的 retrieval-token saving 与真实 QA 成本收益之间仍差一步。

### 5. Strong baseline 仍不够充分

新版新增 dense adaptive truncation 是关键进步，但还缺少至少三类强 baseline：

1. **Reranker-based compression**  
   dense/BM25 candidate + cross-encoder reranker + top-k budget。

2. **Context compression baseline**  
   LLMLingua、Selective Context、DSLR 类方法。

3. **Stronger retrievers**  
   domain-specific encoder、E5 / BGE / GTE 类强 embedding、ColBERT / late-interaction。

论文相关工作已经讨论这些方向，但实验中没有把它们作为主要对照，这会被审稿人质疑。

### 6. Simulated feedback 仍是硬伤

论文已经把 simulated feedback 的 claim 收得比较稳，但这仍然是一个主要弱点。

当前反馈来自 ground-truth-derived simulation，post-feedback recovery 也是 same-query retry / calibration-to-test 机制。held-out recovery generalization 很小且 domain-dependent。

因此 feedback 部分更适合作为 mechanism analysis，而不是主贡献。若论文把 “feedback-guided” 放在标题和方法核心位置，审稿人会期待更强的真实或至少更真实的 delayed / noisy / click-biased feedback 实验。

### 7. Hit@10 仍然是偏宽松的主指标

Hit@10 只说明至少一个 relevant chunk 出现，不能保证 complete evidence。对于 RAG 生成，尤其多证据问题，EvidenceRecall@10、nDCG、citation support 更关键。

如果目标是“answer quality under smaller context”，则 Hit@10 只是必要不充分条件。

### 8. 方法细节仍不够可复现

方法部分仍然对以下细节交代不足：

- context feature vector 的完整定义；
- route confidence 的具体计算；
- semantic drift 的定义和阈值；
- calibrated token-budget policy 的搜索空间；
- r0.85 / r0.95 / m4 等策略名的含义；
- calibration eligible 的判定标准；
- fusion 权重或 RRF 参数；
- chunk tokenization 和 chunk length distribution；
- LinUCB α、λ、τ 的选择方式。

这些细节会影响结果，尤其 calibrated budget policy 是新版核心结果。如果不补全，审稿人会认为方法难以复现。

---

## 具体修改建议

### 摘要

摘要现在比上一版强，但仍建议再收敛一点。当前摘要说：

> saves 6–18% final evidence-context tokens while outperforming dense-only adaptive truncation in Hit@10, with scale-dependent non-inferiority.

这句话基本准确，但建议明确补一句：

> These results are retrieval-level and final-context-token results; end-to-end answer-quality validation remains preliminary.

原因是目前 60-query generation check 不足以支撑 answer-level cost claim。

### 引言

引言应更突出新版最强贡献：**不是多路检索本身，而是 frozen calibration/test budget control**。

建议把主问题重写为：

> When can a RAG system safely reduce the final evidence context, and how can route confidence help avoid the quality loss of naive dense truncation?

这样比“piecewise relevance-manifold assumption”更直接，也更能对应主实验。

同时，“vertical-domain data”要谨慎。建议改为：

> LoTTE-style vertical retrieval settings

或：

> structured domain evidence settings represented by LoTTE technology/search and science/search

避免让审稿人认为外推过度。

### 方法

方法部分需要补足关键实现细节，尤其是：

#### 1. Budget policy 定义

必须解释：

- `token_budget_r0.95_m4`；
- `token_budget_r0.85_m4`；
- `r`；
- `m`；
- eligible 的具体含义。

Table 15 里 400k “Calibration eligible = False” 会引起强烈质疑，必须在正文解释为什么仍报告该点，以及是否应从主 claim 中降级。

#### 2. Feature vector 定义

不能只说包括 query embedding projections、route confidence、local geometry signals。需要列出 feature 表，包括维度、归一化、是否训练/冻结、是否使用 calibration labels。

#### 3. Confidence 和 semantic drift

需要给公式或伪代码。现在读者知道“低置信 fallback，高置信压缩”，但不知道置信度如何得到。

#### 4. Recovery mechanism

需要明确：

- same-query retry；
- post-feedback retry；
- calibration-to-test recovery；

三者的差别。否则容易被误读为 test leakage 或 same-query label insertion。

### 实验

必须增加或强化：

1. **Reranker baseline**  
   Cross-encoder reranker + same token budget 是非常重要的对照。

2. **Prompt/context compression baseline**  
   既然论文讨论 LLMLingua / Selective Context / DSLR，就应至少选一个作为 baseline。

3. **更强 embedding baseline**  
   目前 QA-tuned MiniLM-family encoder robustness 只能说明同资源级 MiniLM family 内稳健，不能推广到 stronger encoders、rerankers 或 late-interaction models。

4. **正式 answer-level evaluation**  
   60-query smoke test 应扩展到至少 300–500 queries，并报告 answer accuracy、faithfulness、citation support、cost/query、cost/correct answer。

5. **更多 query-level paired statistics**  
   对 Hit@10 用 McNemar / paired bootstrap，对 tokens 用 paired bootstrap，对 cost-quality frontier 报告 Pareto dominance probability。

6. **分桶分析**  
   按 query 类型、lexical-anchor、dense confidence、route agreement、cluster-local hit、multi-evidence query 分析。

### 相关工作

相关工作覆盖面比上一版好，但还需要更锋利地区分本文和已有方法：

- 与 Adaptive-RAG / CRAG / Self-RAG 的差异：本文不是 generation-time retrieval decision，而是 retrieval-stage final-context budget control。
- 与 LLMLingua / Selective Context / DSLR 的差异：本文不是通用 prompt compression，而是 retrieval-aware budget selection。
- 与 MBA-RAG 的差异：本文不是 retrieval-method arms，而是 cluster-local arms + final context budget + recovery。
- 与 reranker 的差异：本文是否能替代 reranker，还是可组合？目前实验没有回答。

建议相关工作最后加一个 comparison table，列出每类方法是否支持 feedback、route control、final context budget、dense fallback、post-feedback recovery。

### 图表

Figure 2 是新版最重要图，建议保留并增强。它应该明确标出：

- IntentWeight vs dense adaptive truncation；
- technology/search vs science/search；
- non-inferiority 是否成立；
- calibration eligible 是否为 True；
- 每个点的 seed 数和 CI。

Table 15 中 400k Calibration eligible = False 不应藏在附录或表格里，应在主文讨论。否则审稿人会怀疑主图里用了未通过 calibration 筛选的点。

Table 14 建议不要放成强结果，只能作为 sanity check。表格标题可改为：

> Small downstream sanity check

而不是：

> answer-quality check

避免过度 claim。

### 结论

结论应进一步收敛为：

> IntentWeight demonstrates a bounded retrieval-level quality-cost frontier on LoTTE-style RAG evidence selection.

不要说得像已经解决了 general knowledge-augmented agent evidence selection。当前结论已经说不是 universal dense replacement，这点应保留。

---

## 风险判断

### 当前更接近：Borderline，偏 Weak Reject

相比上一版，我会把判断从 **Weak Reject** 上调到 **Borderline / Weak Reject 边界**。原因是新版确实补上了几个关键短板：

- 有 calibrated token-budget protocol；
- 有 dense-only adaptive truncation 对照；
- 有第二 LoTTE domain；
- 有 post-feedback recovery；
- claim 更克制；
- final context token cost 的叙事更清楚。

但按顶级会议主会标准，仍有四个主要拒稿风险：

1. **方法 novelty 仍偏工程组合**，不是明显新的算法或理论。
2. **真实 answer-level cost-quality 证据不足**，60-query smoke test 不够。
3. **feedback 核心仍是 simulated / GT-derived**，与标题中的 feedback-guided 重要性不完全匹配。
4. **强 baseline 不够完整**，尤其缺 reranker、prompt compression、stronger retriever / late-interaction 对照。

如果是 ACL / EMNLP / NAACL Findings、workshop、industry track 或 applied systems track，这篇稿子已经比较有竞争力；如果目标是 ACL / EMNLP / NeurIPS / ICLR 主会，仍需要更强实验或更明确的新方法贡献。

---

## 最强部分与最薄弱部分

### 最强部分

新版最强的是 **calibrated token-quality frontier**。它直接回应了“不要只省 candidate，要省最终 LLM context tokens”的问题，并且用 dense adaptive truncation 对照证明“简单减少 dense top-k 会伤 Hit@10”。这是论文目前最有价值、最能被审稿人认可的部分。

### 最薄弱部分

最薄弱的是 **方法贡献和 end-to-end 证据之间仍不匹配**。论文标题和方法强调 feedback-guided evidence selection，但 feedback 仍然是模拟；论文强调 LLM input cost，但 answer-level evaluation 只有 60 queries；论文强调 context control，但还没和主流 compression / reranker baseline 充分比较。

---

## 修改优先级

| 问题 | 严重程度 | 修改建议 | 优先级 |
|---|---:|---|---:|
| 缺少 reranker / compression 强 baseline | 严重 | 加 cross-encoder reranker、LLMLingua / Selective Context / DSLR 类对照，使用 same token budget 比较 | P0 |
| 下游生成评估过小 | 严重 | 将 60-query smoke test 扩展到 300–500+ queries，报告 answer accuracy、faithfulness、citation support、cost/correct answer | P0 |
| Simulated feedback 仍支撑标题核心 | 严重 | 加 delayed / noisy / click-biased / adversarial feedback simulation；最好加入小规模人工反馈或真实日志模拟 | P0 |
| Calibrated budget 结果 scale-dependent | 严重 | 对 Table 15 增加 paired significance、non-inferiority CI、query-level win/loss/tie；解释 400k Calibration eligible=False | P0 |
| 方法 novelty 偏组合 | 严重 | 将贡献重心从“多路检索 + LinUCB”改成“risk-calibrated final context budget controller”；弱化 manifold 和 bandit novelty | P0 |
| 方法细节不足 | 中高 | 补全 feature vector、confidence score、semantic drift、budget policy、fusion formula、LinUCB 超参、calibration protocol | P1 |
| 外部有效性仍有限 | 中高 | 增加至少一个非 LoTTE vertical corpus，或明确把 claim 限定为 LoTTE-style retrieval-backed QA | P1 |
| EvidenceRecall / complete evidence 风险 | 中高 | 把 EvidenceRecall、nDCG、citation support 和 multi-evidence query 分桶作为主表或副主表 | P1 |
| Science/search budget 需要校准 | 中等 | 把 science 100k 的 Hit drop 作为 boundary condition 分析，而不是只作为 positive replication | P1 |
| 标题中的 “piecewise relevance-manifold” 可能偏包装 | 中等 | 改成 “piecewise local relevance structure” 或在正文强调只是 diagnostic hypothesis | P1 |
| 表格和主文信息密度偏高 | 轻微 | 精简贡献列表，减少防御性语句，把关键信息集中到主实验和 limitation | P2 |

---

## 最终评分

| 维度 | 评分 |
|---|---:|
| Novelty | 5.0 / 10 |
| Technical Quality | 6.5 / 10 |
| Experimental Support | 6.0 / 10 |
| Clarity | 7.0 / 10 |
| Overall Recommendation | Borderline / Weak Reject |

---

## 审稿结论

这版已经明显比上一版强，尤其是 **6–18% calibrated final-context token saving + dense adaptive truncation 对照** 让论文从“收益太低”变成了“有一个可讨论的 quality-cost frontier”。

但如果按顶会主会标准，当前还不够稳：

- 方法仍像组合式系统；
- feedback 证据仍是模拟；
- answer-level cost saving 还没有被充分证明；
- 强 baseline 还缺位。

最建议下一步优先补三件事：

1. **加 reranker / compression / stronger retriever baseline；**
2. **把 downstream answer-quality evaluation 做成正式实验；**
3. **对 calibrated budget 做 query-level paired non-inferiority 统计，并解释 400k calibration eligibility 问题。**

补完这三点后，这篇论文有机会从 Borderline 偏 Weak Reject 提升到 **Borderline 偏 Weak Accept**。
