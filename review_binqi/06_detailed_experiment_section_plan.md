# Detailed Experiment Section Plan

> 整理自针对更新稿实验部分的详细建议。  
> 核心原则：实验部分应按 **“先证明核心 claim，再排除替代解释，最后证明系统价值”** 来重构。

---

## 实验部分的核心目标

实验不应该只证明：

> IntentWeight 能省一些 context tokens。

而应该证明：

> 在保证 retrieval / answer quality 不显著下降的前提下，IntentWeight 比简单 dense truncation、普通 hybrid、reranker、context compression 等方案更稳地降低最终 LLM evidence-context input cost。

当前论文已经明确区分了三层成本：

1. source candidate cost；
2. dense invocation rate；
3. final context tokens。

并且主 claim 使用的是最终送给 generator 的 retrieved context tokens，这是对的。

所以实验设计要围绕三件事：

1. **Quality 是否保持？**  
   Hit@10、MRR、nDCG、EvidenceRecall、answer correctness、faithfulness。

2. **Cost 是否真的下降？**  
   final evidence-context tokens、input cost/query、cost/correct answer。

3. **是否优于简单替代方法？**  
   dense adaptive top-k、sentence compression、reranker same-budget、stronger retriever。

---

# 1. 主实验一：Calibrated Token-Quality Frontier

## 目的

这是目前论文最强的实验，应该放在实验部分第一位。

它要回答：

> IntentWeight 是否能在 frozen calibration/test protocol 下，用更少 final context tokens 保持 dense-level retrieval quality？

当前论文已经有这个结构：final-context policy 先在 calibration queries 上选择，然后 frozen 到 held-out test queries 上评估。这个设计非常重要，因为它可以避免 test-set threshold tuning 的嫌疑。

## 当前结果怎么用

现在 Table 15 的结果很有价值：

| Scale | IntentWeight token saving | IntentWeight Hit Δ | Dense adaptive token saving | Dense adaptive Hit Δ |
|---|---:|---:|---:|---:|
| 100k | 6.18% | +0.00 pp | 13.83% | -1.44 pp |
| 200k | 16.00% | +1.20 pp | 21.95% | -2.40 pp |
| 400k | 6.57% | +2.32 pp | 11.44% | -0.24 pp |
| 638k | 17.53% | -0.08 pp | 21.90% 左右 | -3.84 pp |

这个表说明一件关键事情：

**dense-only adaptive truncation 可以省更多 tokens，但会更明显损害 Hit@10；IntentWeight 的价值是更稳地控制 quality-cost trade-off。**

## 需要修改的问题

400k 的 `Calibration eligible = False` 是一个潜在攻击点。它虽然有 +2.32 pp Hit gain 和 6.57% saving，但如果这个点没有通过 calibration eligibility，就不应该作为主 claim 的核心证据。

## 建议做法

把 Table 15 拆成两张表。

### 主文表：只放 calibration eligible=True 的结果

| Scale | Selected policy | Calibration eligible | Hit Δ vs dense | Token saving | Dense adaptive Hit Δ | Dense adaptive saving | NI pass |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | r0.95_m4 | True | +0.00 pp | 6.18% | -1.44 pp | 13.83% | Yes / No |
| 200k | r0.85_m4 | True | +1.20 pp | 16.00% | -2.40 pp | 21.95% | Yes / No |
| 638k | r0.85_m4 | True | -0.08 pp | 17.53% | -3.84 pp | 21.90% | Yes / No |

### 附录表：放所有 frontier points

| Scale | Selected policy | Calibration eligible | Interpretation |
|---|---|---:|---|
| 400k | r0.98_m4 | False | Diagnostic frontier point, not part of strict main claim |

这样会显著降低 reviewer 对 cherry-picking 的攻击。

## 必须补充的统计

只报告平均 Hit Δ 不够。建议加：

| 统计项 | 作用 |
|---|---|
| Paired bootstrap CI | 给 Hit Δ、EvidenceRecall Δ、token saving 加置信区间 |
| McNemar test | 对 Hit@10 这种二元 paired outcome 做显著性检验 |
| Dense win / IntentWeight win / tie | 告诉审稿人差异来自多少 query |
| Non-inferiority margin | 明确质量不劣的判断标准 |

建议设：

\[
\delta_{\text{Hit@10}} = 1.0\text{ pp}
\]

即：

> 如果 IntentWeight 的 Hit@10 下置信界不低于 dense − 1.0 pp，则认为 quality non-inferior。

主 claim 可以写成：

> IntentWeight achieves cost superiority under a retrieval-quality non-inferiority constraint.

也就是：

- quality：non-inferiority；
- cost：superiority。

这个 framing 比“Hit@10 更高”更稳。

---

# 2. 主实验二：Same-Budget Strong Baseline Comparison

## 目的

这个实验要回答审稿人最可能问的问题：

> IntentWeight 的效果是不是简单 dense top-k、reranker、sentence compression 就能做到？

当前论文已有 BM25-only、dense-only、BM25+dense hybrid、full multi-route、gated cost-aware、confidence-based IntentWeight、nearest-cluster、random / epsilon-greedy 等 baseline。但这些还不够，因为它们没有覆盖最强的 **same-budget evidence refinement** baselines。

## 必须新增的 baseline

### Baseline A：Dense adaptive top-k / token budget

你已经有 dense-only adaptive truncation，这个必须保留，而且应该作为第一强对照。它直接证明 IntentWeight 不是简单减少 dense top-k。当前结果显示 dense adaptive 每个 scale 都出现 Hit@10 loss，因此这个 baseline 对你有利。

建议补充 dense adaptive 的多个版本：

| Baseline | 说明 |
|---|---|
| Dense top-8 | 最简单 top-k 减少 |
| Dense top-6 | 更激进压缩 |
| Dense token budget 1024 | 固定 token budget |
| Dense score-threshold adaptive | 根据 dense score confidence 截断 |
| Dense score-gap adaptive | 根据 top1-top2 gap 截断 |
| Dense entropy adaptive | 根据分数分布不确定性截断 |

这样可以排除：

> IntentWeight 只是 dense confidence truncation 的复杂版本。

### Baseline B：Dense top-10 + sentence-level MMR

这是最建议马上补的 baseline，性价比最高。

做法：

1. dense top-10 检索完整 chunks；
2. 把 chunks 拆成 sentences；
3. 用 query-sentence embedding similarity 排序；
4. 用 MMR 去冗余；
5. 按与 IntentWeight 相同的 token budget 选句子；
6. 送入相同 generator 或用于同样 retrieval/evidence support evaluation。

这个 baseline 的意义是：

> 如果简单 sentence compression 已经能做到同样效果，那么 IntentWeight 的必要性会下降；如果 IntentWeight 更稳，则说明 route-aware confidence 有价值。

建议命名：

- `Dense+SentMMR@same-budget`
- `Dense+SentenceCompression`
- `Dense+MMR-Compress`

### Baseline C：BM25+dense RRF + sentence-level MMR

因为你的方法使用 BM25+dense+cluster routes，所以还要给一个强 hybrid baseline：

1. BM25 top-N；
2. dense top-N；
3. RRF fusion；
4. sentence-level MMR；
5. same token budget。

这能回答：

> 是否普通 static hybrid + compression 就够了？

### Baseline D：Cross-encoder reranker same-budget

这是顶会 reviewer 很可能期待的强 baseline。

做法：

1. dense top-50 或 RRF top-50；
2. cross-encoder reranker rerank；
3. 取 top-k 或按 token budget 截断；
4. 与 IntentWeight 在同等 token budget 下比较。

建议至少做两个版本：

| Baseline | Candidate pool | Final selection |
|---|---|---|
| Dense + reranker | dense top-50 | same token budget |
| RRF + reranker | BM25 top-50 + dense top-50 | same token budget |

如果算力有限，可以只在 100k 和 200k scale 上做。

### Baseline E：Prompt/context compression baseline

相关工作里已经讨论了 Selective Context、LLMLingua、LLMLingua-2、DSLR 等 context compression / evidence refinement 方法。如果实验中完全不比，会被 reviewer 质疑。

最低可接受版本：

| Baseline | 工程成本 | 价值 |
|---|---:|---|
| Dense top-10 + sentence similarity compression | 低 | 必须做 |
| Dense top-10 + MMR compression | 低 | 推荐做 |
| Dense top-10 + LLMLingua / Selective Context | 中 | 强烈建议 |
| RRF top-10 + compression | 中 | 更公平 |

## 推荐主表

建议做一张 “same-budget quality-cost comparison”：

| Method | Hit@10 | ΔHit | MRR@10 | nDCG@10 | EvidenceRecall@10 | Avg context tokens | Token saving | NI pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense top-10 | baseline | 0 | baseline | baseline | baseline | baseline | 0 | - |
| Dense adaptive truncation |  |  |  |  |  |  |  |  |
| Dense score-gap adaptive |  |  |  |  |  |  |  |  |
| Dense+SentMMR same-budget |  |  |  |  |  |  |  |  |
| RRF+SentMMR same-budget |  |  |  |  |  |  |  |  |
| Reranker same-budget |  |  |  |  |  |  |  |  |
| IntentWeight budget |  |  |  |  |  |  |  |  |

这张表是最能提升审稿说服力的。

---

# 3. 主实验三：Answer-Level Cost-Quality Evaluation

## 目的

如果论文要强调 **LLM input token cost saving**，只做 retrieval Hit@10 还不够。必须证明：

> 更短的 context 没有显著降低答案质量。

当前论文的 60-query downstream answer-quality check 只能作为 sanity check。它可以说“没有明显退化”，但不能支撑强 end-to-end claim。

## 建议扩展规模

最低：

- 300 queries。

较稳：

- 500 queries。

更强：

- 1000 queries。

抽样不要随机一把抓，建议 stratified sampling：

| Bucket | 建议占比 | 目的 |
|---|---:|---|
| Dense 与 IntentWeight 都 hit | 35–40% | 检查压缩是否影响答案 |
| IntentWeight hit，dense miss | 10% | 展示 routing gain |
| Dense hit，IntentWeight miss | 15% | 分析失败风险 |
| IntentWeight 高压缩 query | 15% | 检查省 token 是否安全 |
| 多证据 query | 15% | 检查 EvidenceRecall 风险 |
| 低置信 fallback query | 10% | 证明 fallback 有必要 |

## 生成设置

每个 query 至少生成两组答案：

1. Dense top-10 context；
2. IntentWeight calibrated budget context。

建议再加两组：

3. Dense adaptive truncation context；
4. Dense+SentMMR same-budget context。

这样可以直接比较：

> IntentWeight 省 token 后的答案质量是否比简单压缩更稳？

## 评价指标

不要只给 LLM judge 平均分。建议使用：

| 指标 | 含义 | 重要性 |
|---|---|---:|
| Answer correctness | 答案是否正确 | P0 |
| Faithfulness | 答案是否被 context 支撑 | P0 |
| Citation support | 引用 evidence 是否支持答案 | P0 |
| Context sufficiency | context 是否足够回答 | P0 |
| Hallucination rate | 是否引入 context 外信息 | P0 |
| Pairwise win/tie/loss | IntentWeight vs Dense 直接比较 | P0 |
| Input tokens/query | 输入 token 成本 | P0 |
| Cost/query | 按 LLM input price 计算成本 | P1 |
| Cost/correct answer | 成本归一化质量 | P0 |

最重要的是 **Cost per correct answer**：

\[
CostPerCorrect =
\frac{\sum_q Cost(q)}
{\sum_q \mathbb{1}[\text{answer correct}]}
\]

它能防止 reviewer 说：

> 你只是省 token，但答案错更多。

## 推荐 answer-level 主表

| Method | Answer Acc | Faithfulness | Citation support | Hallucination ↓ | Input tokens | Input cost | Cost/correct ↓ | Pairwise W/T/L vs dense |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense top-10 | baseline | baseline | baseline | baseline | 1.00x | 1.00x | 1.00x | - |
| Dense adaptive |  |  |  |  |  |  |  |  |
| Dense+SentMMR |  |  |  |  |  |  |  |  |
| Reranker same-budget |  |  |  |  |  |  |  |  |
| IntentWeight budget |  |  |  |  |  |  |  |  |

## LLM judge 设计

为了降低 judge bias，建议：

1. **blind pairwise judging**：不要告诉 judge 哪个是 Dense，哪个是 IntentWeight；
2. **答案顺序随机化**；
3. **引用 evidence 一起给 judge**；
4. **用两个 judge 模型或一个 judge + 人工抽检**；
5. **人工复核 50–100 个 disagreement cases**。

judge prompt 要拆成多个维度，而不是一个总分：

```text
Given the question, reference answer or ground-truth evidence, and two model answers,
judge:
1. Which answer is more factually correct?
2. Which answer is better supported by the provided context?
3. Does either answer contain unsupported claims?
4. Are the cited passages sufficient?
Return: A wins / B wins / Tie, with short rationale.
```

---

# 4. 主实验四：Evidence Completeness / Multi-Evidence Analysis

## 目的

主指标是 Hit@10，但 Hit@10 只要求至少一个 ground-truth chunk 出现。论文已经明确承认：final context compaction 可以保持“至少一个 relevant chunk 被检索到”，同时降低所有 ground-truth chunks 的覆盖。

对于法律、医学、合规等 complete-evidence tasks，这会是风险。

所以需要单独做 evidence completeness 分析。

## 建议分桶

按每个 query 的 ground-truth chunk 数量分桶：

| Bucket | 含义 |
|---|---|
| \|GT\| = 1 | 单证据问题 |
| \|GT\| = 2–3 | 中等多证据问题 |
| \|GT\| ≥ 4 | 多证据 / complete evidence 风险问题 |

每个 bucket 报：

| Bucket | Method | Hit@10 | EvidenceRecall@10 | nDCG@10 | Token saving | Failure mode |
|---|---|---:|---:|---:|---:|---|
| \|GT\|=1 | Dense |  |  |  |  |  |
| \|GT\|=1 | IntentWeight |  |  |  |  |  |
| \|GT\|=2–3 | Dense |  |  |  |  |  |
| \|GT\|=2–3 | IntentWeight |  |  |  |  |  |
| \|GT\|≥4 | Dense |  |  |  |  |  |
| \|GT\|≥4 | IntentWeight |  |  |  |  |  |

## 推荐 claim

如果结果显示多证据问题上 EvidenceRecall 会下降，不要回避。可以写：

> IntentWeight is best suited for usable-evidence QA where one or a few supporting chunks are sufficient. For complete-evidence workflows, the controller should either disable compaction or use a stricter EvidenceRecall-preserving budget.

这会让论文显得更可信。

---

# 5. 反馈实验：从 “feedback improves” 改成 “feedback-triggered recovery”

## 当前问题

论文现在已经比较谨慎：hard-case recovery 关注的是 dense top-10 能检索到 GT，但 budgeted IntentWeight context miss 的 affected queries；same-query retry 是 post-feedback repair，不是 first-pass generalization。

这是正确方向。不要把 feedback 写成“泛化提升”，而要写成：

> feedback can repair tail failures after compression.

## 建议新增实验

### 5.1 Feedback settings

| Setting | 描述 | 目的 |
|---|---|---|
| Oracle feedback | 当前 GT-derived upper bound | 上限 |
| Noisy feedback 10 / 20 / 30 / 40% | 随机翻转一部分反馈 | 鲁棒性 |
| Delayed feedback | delay = 5 / 20 / 100 queries | 模拟真实系统延迟 |
| Click-biased feedback | position bias + false click + no-click | 模拟隐式反馈 |
| Adversarial feedback | 部分用户恶意反向反馈 | 安全性 |
| Missing feedback | 只有一部分 query 有反馈 | 稀疏反馈 |

### 5.2 Recovery metrics

不要只报 recovered 数量，还要报 harmed 数量：

| Metric | 说明 |
|---|---|
| Affected queries | dense hit but budgeted miss |
| Recovered | retry 后命中 |
| Still missed | retry 后仍 miss |
| New regressions | 原来命中，feedback 后 miss |
| Net Hit Δ | 总体收益 |
| Token saving retained | recovery 后还保留多少 token saving |
| Fallback rate | 有多少 query 触发 full dense fallback |

推荐表格：

| Feedback mode | Affected | Recovered | New regressions | Net Hit Δ | Token saving retained | Fallback rate |
|---|---:|---:|---:|---:|---:|---:|
| Oracle |  |  |  |  |  |  |
| Noisy 10% |  |  |  |  |  |  |
| Noisy 30% |  |  |  |  |  |  |
| Delayed 20 |  |  |  |  |  |  |
| Click-biased |  |  |  |  |  |  |

## 建议定位

Feedback 部分不要作为主贡献第一证据，而是作为第三主实验或机制分析：

> The feedback module is useful as a safety and recovery layer, not as evidence that simulated feedback improves all future retrieval.

这和论文当前 limitation 一致：真实反馈仍需 trust scoring、delay handling 和 adversarial safeguards。

---

# 6. 跨域实验：LoTTE science 之外最好再加一个非 LoTTE

## 当前情况

LoTTE science/search 是有价值的第二域。当前结果显示 fixed top-10 ranking-side effect 能迁移：science/search 20k/q200 的 dense Hit@10 是 0.8950，IntentWeight fixed top-10 是 0.9267，提升 +3.17 pp；science/search 100k 是 0.8926 到 0.9077，提升 +1.51 pp。

context-budget 结果更复杂：20k/q200 能保存约 13–14% tokens，100k aggressive budget 虽能省 17–21%，但会出现小 Hit@10 drops。

这个结果应该被写成：

> ranking-side generalization transfers, but compression strength requires domain calibration.

不要写成：

> 方法跨域稳定成功。

## 建议补一个非 LoTTE corpus

如果投稿顶会，LoTTE technology + LoTTE science 仍容易被说成同 family。论文自己也承认 LoTTE science/search 增强 external validity，但不能替代更多 vertical corpora。

建议至少加一个：

| Corpus 类型 | 为什么适合 |
|---|---|
| technical documentation QA | 与实际 RAG deployment 接近 |
| biomedical QA retrieval | 术语密集，适合 BM25+dense+local geometry |
| product support / FAQ | workflow/entity structure 明显 |
| finance / compliance QA subset | vertical-domain 性质强 |

最低要求：

- 300–500 queries；
- 50k–100k chunks；
- 跑 Dense、Dense adaptive、Dense+SentMMR、IntentWeight；
- 报 Hit@10、EvidenceRecall、tokens、NI pass。

如果时间不够，可以把它作为 “external stress test” 而不是完整主 benchmark。

---

# 7. Encoder / Retriever Robustness

## 当前情况

论文已有一个 QA-tuned MiniLM-family encoder robustness check：dense baseline 提高到 Hit@10 = 0.8809，IntentWeight 达到 0.8853，同时 final context tokens 减少 3.35%；但 ranking metrics 和 evidence recall 低于 dense，所以这是 bounded robustness，不是 universal improvement。

论文 limitation 也承认不能泛化到 stronger domain-specific encoders、rerankers、late-interaction models。

## 建议新增

至少加一个 stronger embedding model：

| Encoder | 目的 |
|---|---|
| all-MiniLM-L6-v2 | 当前主 baseline |
| multi-qa-MiniLM-L6-cos-v1 | 当前 robustness |
| BGE / E5 / GTE | 更强 dense retriever |
| ColBERT / late-interaction | 如果算力允许，最强对照 |

主问题不是一定要超过强 retriever，而是：

> 当 dense baseline 变强时，IntentWeight 是否仍能提供 final context budget benefit？

推荐表格：

| Encoder | Method | Hit@10 | MRR@10 | nDCG@10 | EvidenceRecall@10 | Token saving | NI pass |
|---|---|---:|---:|---:|---:|---:|---:|
| MiniLM | Dense |  |  |  |  | 0 | - |
| MiniLM | IntentWeight |  |  |  |  |  |  |
| Multi-QA MiniLM | Dense | 0.8809 | 0.7220 | 0.6616 | 0.7163 | 0 | - |
| Multi-QA MiniLM | IntentWeight | 0.8853 | 0.7118 | 0.6291 | 0.6789 | 3.35% | bounded |
| BGE / E5 / GTE | Dense |  |  |  |  | 0 | - |
| BGE / E5 / GTE | IntentWeight |  |  |  |  |  |  |

---

# 8. Ablation Study：证明每个组件有必要

## 当前需要回答的问题

方法组件较多：

- dense；
- BM25；
- cluster-local；
- LinUCB；
- trust weighting；
- confidence budget；
- fallback；
- feedback recovery。

审稿人会问：

> 哪个组件真的有用？是否只是 dense + budget policy 起作用？

## 建议 ablation matrix

### 8.1 Route ablation

| Variant | Dense | BM25 | Cluster | LinUCB | Budget |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | ✓ | ✗ | ✗ | ✗ | ✗ |
| BM25 only | ✗ | ✓ | ✗ | ✗ | ✗ |
| Dense+BM25 RRF | ✓ | ✓ | ✗ | ✗ | ✗ |
| Dense+cluster static | ✓ | ✗ | ✓ | ✗ | ✗ |
| Dense+BM25+cluster static | ✓ | ✓ | ✓ | ✗ | ✗ |
| IntentWeight no budget | ✓ | ✓ | ✓ | ✓ | ✗ |
| IntentWeight budget | ✓ | ✓ | ✓ | ✓ | ✓ |

这样可以分离：

- ranking gain 来自哪里；
- token saving 来自哪里；
- LinUCB 是否真的优于 static cluster。

### 8.2 Budget ablation

| Variant | 说明 |
|---|---|
| Fixed k=8 for all | 检查简单截断 |
| Fixed k=6 for all | 检查激进截断 |
| Dense confidence budget | 无 route signals |
| Route confidence budget | 当前核心 |
| Route confidence + drift fallback | 检查 fallback 价值 |
| Route confidence + feedback risk | 检查 recovery 价值 |

### 8.3 Feedback ablation

| Variant | 说明 |
|---|---|
| No feedback | 静态 policy |
| Oracle feedback | 上限 |
| Equal noisy feedback | 不区分 trust |
| Trust-weighted feedback | 当前方法 |
| Trust-weighted + delayed | 更真实 |
| Trust-weighted + adversarial | 安全性 |

### 8.4 Geometry ablation

| Variant | 说明 |
|---|---|
| Random clusters | 排除 KMeans 偶然性 |
| Nearest cluster only | static geometry control |
| LinUCB cluster selection | 当前 |
| Different #arms: 16 / 32 / 64 | arm sensitivity |
| PCA/context-space only | 测 local geometry 是否足够 |

论文当前已经有 geometry diagnostics，但 diagnostics 不是 theorem-level manifold proof。所以 ablation 要把“geometry 是有用信号，但不是完整检索器”证明清楚。

---

# 9. 统计检验与报告规范

## 为什么必须做

论文 limitation 已经承认三 seed CI 是 engineering stability diagnostics，不应过度解释为强统计显著性 proof；LoTTE 400k token-saving interval 也更宽，说明 route confidence 和 budget control 存在 seed variance。

## 推荐统计协议

### 9.1 Query-level paired bootstrap

对 query 采样，保留每个 query 上 dense 和 IntentWeight 的 paired relation。

报告：

- ΔHit@10 95% CI；
- ΔEvidenceRecall@10 95% CI；
- ΔMRR@10 95% CI；
- ΔnDCG@10 95% CI；
- token saving 95% CI；
- cost/correct answer 95% CI。

### 9.2 McNemar test for Hit@10

构造：

|  | IntentWeight hit | IntentWeight miss |
|---|---:|---:|
| Dense hit | both hit | dense-only win |
| Dense miss | IW-only win | both miss |

报告：

- dense-only win；
- IW-only win；
- p-value；
- effect size。

### 9.3 Non-inferiority + cost superiority

写法建议：

> We test quality non-inferiority and cost superiority separately.

具体：

\[
H_0^{quality}: \Delta Hit@10 < -\delta
\]

\[
H_1^{quality}: \Delta Hit@10 \geq -\delta
\]

\[
H_0^{cost}: \Delta Tokens \geq 0
\]

\[
H_1^{cost}: \Delta Tokens < 0
\]

其中 \(\delta\) 可以设为 1.0 pp。

---

# 10. 最终实验章节结构建议

## 4 Experimental Setup

### 4.1 Datasets and evidentiary roles

保留当前角色划分：

- LoTTE technology/search：main benchmark；
- LoTTE science/search：cross-domain validation；
- PubMedQA / Banking77：feedback mechanism checks；
- eManual / CUAD：boundary cases。

### 4.2 Baselines

分成五类：

1. retrieval baselines；
2. adaptive truncation baselines；
3. compression baselines；
4. reranker baselines；
5. feedback / ablation controls。

### 4.3 Metrics

分三组：

1. retrieval quality：Hit@10、MRR、nDCG、EvidenceRecall；
2. context cost：final context tokens、input cost/query、cost/correct；
3. answer quality：correctness、faithfulness、citation support、hallucination。

### 4.4 Calibration/test protocol

明确：

- calibration split；
- test split；
- budget policy search space；
- eligibility rule；
- non-inferiority margin；
- no test-set tuning。

### 4.5 Statistical testing

写清：

- paired bootstrap；
- McNemar；
- CI；
- seed protocol；
- multiple comparison correction。

---

## 5 Results

### 5.1 Calibrated token-quality frontier

主结果：IntentWeight vs dense adaptive。

### 5.2 Same-budget baseline comparison

新增：SentMMR、RRF+compression、reranker。

### 5.3 Answer-level cost-quality evaluation

新增：300–500 query generation evaluation。

### 5.4 Evidence completeness and multi-evidence risk

新增：按 GT count 分桶。

### 5.5 Cross-domain validation

LoTTE science + 至少一个非 LoTTE。

### 5.6 Feedback-triggered recovery

把 feedback 定位为 recovery。

### 5.7 Ablations

组件必要性。

### 5.8 Failure analysis

明确哪些 query 会失败。

---

# 11. 最应该优先补的实验

| 优先级 | 实验 | 为什么重要 | 最低可接受版本 |
|---:|---|---|---|
| P0 | Dense+SentMMR same-budget baseline | 直接挑战 context compression 必要性 | 100k + 200k |
| P0 | Reranker same-budget baseline | 顶会强 baseline | 100k 或 200k 子集 |
| P0 | 300–500 query answer-level eval | 支撑 LLM cost claim | paired LLM judge + 人工抽检 |
| P0 | Table 15 paired NI statistics | 让主结果统计上站得住 | McNemar + paired bootstrap |
| P0 | 修正 400k eligible=False 呈现 | 避免 cherry-picking 攻击 | 主表剔除或降级 |
| P1 | EvidenceRecall / multi-evidence bucket | 防止 Hit@10 掩盖证据损失 | 按 \|GT\| 分桶 |
| P1 | Noisy / delayed / click-biased feedback | 降低 simulated feedback 硬伤 | 3–4 个 feedback settings |
| P1 | Stronger encoder | 防止 MiniLM-only | BGE / E5 / GTE 任选一个 |
| P1 | 非 LoTTE corpus | 提升外部有效性 | 300–500 queries |
| P2 | arm count sensitivity | 增强完整性 | 16 / 32 / 64 arms |

---

# 12. 最关键的实验 claim 应该这样写

不要写：

> IntentWeight generally improves retrieval and reduces cost.

建议写：

> Under a frozen calibration/test protocol, IntentWeight identifies bounded operating points that reduce final LLM evidence-context input tokens while avoiding the larger Hit@10 losses caused by dense-only adaptive truncation. This effect is strongest on LoTTE technology/search and requires domain calibration for transfer.

如果补完 answer-level evaluation，可以进一步写：

> In downstream QA evaluation, IntentWeight reduces input cost per query and cost per correct answer without statistically significant degradation in answer correctness, faithfulness, or citation support.

这就是一个更完整、更顶会友好的实验闭环。
