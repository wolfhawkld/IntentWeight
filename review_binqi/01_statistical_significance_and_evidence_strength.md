# 统计显著性与说服力优化建议

要大幅提升统计显著性和说服力，**最优先不是简单多跑几个 seed，而是扩大“有效样本量”、使用配对统计检验、增加强 baseline，并把 claim 从 mean improvement 改成可检验的 non-inferiority / cost-saving 结论**。当前论文主实验只有 LoTTE technology/search 的 596 个 test queries，且三 seed 只能作为工程稳定性诊断，100k 五 seed 的 Hit delta CI 仍跨 0；这说明问题主要不是“seed 太少”这么简单，而是效应量、样本设计和对照设计都还不够强。

## 1. 第一优先级：把统计检验从“seed 均值”改成“query-level paired test”

现在的结果主要写成不同 scale 下的平均 Hit@10 和 token saving，例如 100k 为 -0.22 pp，200k 为 +2.80 pp，400k 为 +1.01 pp，638k 为 +1.85 pp，同时 token saving 约 4.7–5.3%。这些 delta 都不大，尤其 400k 和 638k 的 Hit gain 很容易被审稿人认为是 query composition 或 seed variance。

建议改成以下统计协议：

| 指标 | 当前问题 | 推荐检验 |
|---|---|---|
| Hit@10 | 二元指标，不能只看 mean delta | **McNemar test** 或 paired permutation test |
| EvidenceRecall@10 / nDCG / MRR | 每个 query 都有一对结果 | paired bootstrap / paired randomization test |
| Tokens@10 | 连续变量，且每个 query 有 dense 与 IntentWeight 配对 | paired bootstrap CI / Wilcoxon signed-rank |
| Quality-cost frontier | 同时涉及质量和成本 | bootstrap over queries，报告 Pareto dominance probability |
| 多 scale / 多 baseline | 多重比较风险 | Holm-Bonferroni 或 Benjamini-Hochberg correction |

最关键的是：**每个 query 上 Dense 和 IntentWeight 是天然配对的**。不要只报告 seed-level mean ± CI。应该报告：

- Dense win / IntentWeight win / tie 的 query 数；
- 在多少 query 上 token 下降且 Hit 不变；
- 在多少 query 上 token 下降但 Hit 变差；
- 在多少 query 上 Hit 提升但 token 增加；
- paired confidence interval；
- one-sided non-inferiority test。

对这篇论文，最合适的主 claim 不是“Hit@10 statistically higher than dense”，而是：

> IntentWeight 在 Hit@10 不劣于 dense-only 的条件下，显著降低 final context tokens。

也就是把主假设改成：

- **H0-quality:** IntentWeight 的 Hit@10 比 dense 低超过 δ，例如 δ = 0.5 pp 或 1.0 pp；
- **H1-quality:** IntentWeight 在 Hit@10 上不劣于 dense；
- **H0-cost:** IntentWeight 的 token saving ≤ 0；
- **H1-cost:** IntentWeight 显著降低 final context tokens。

这比强行证明 Hit@10 超过 dense 更容易成立，也更符合论文当前定位。

## 2. 第二优先级：扩大 query 数，而不是只扩大 corpus scale

当前 LoTTE 主实验虽然有 100k 到 638k corpus chunks，但 test queries 仍是 596 个。对于 Hit@10 这种二元指标，596 queries 下 1 个百分点的差异大约只对应 6 个 query 的成败变化；如果 paired discordant cases 不够集中，统计显著性很难强。

优先做法：

1. **增加 query 数到至少 2k–5k。**  
   如果 LoTTE technology/search 本身 query 不够，应加入更多 LoTTE domains，而不是只继续增加 corpus chunks。

2. **做 stratified evaluation。**  
   按 query 类型分桶，例如：
   - lexical-anchor heavy；
   - entity-heavy；
   - long-tail technical term；
   - semantic paraphrase；
   - multi-hop / multi-evidence；
   - high dense-confidence；
   - low dense-confidence；
   - high cluster-confidence；
   - low cluster-confidence。

3. **报告每个 bucket 的效果。**  
   如果 IntentWeight 只在某些 query 类型上有效，这不是坏事，但必须说清楚。这样反而能增强论文说服力：方法不是平均意义上的微弱漂移，而是在特定条件下有稳定收益。

4. **避免只用 corpus scale 制造“规模感”。**  
   100k、200k、400k、638k chunks 看起来很大，但统计显著性主要由 query 数和 paired differences 决定，不由 corpus chunks 数直接决定。

## 3. 第三优先级：提高效应量，否则再多统计也只能证明“小收益显著”

目前 conservative policy 的 final context token saving 只有约 4.7–5.3%，而且高置信情况下只是从 top-10 压到 k=8。这个收益太保守，容易被审稿人质疑实际价值。

### 3.1 把固定 k=8 改成 calibrated adaptive-k

不要只设三档：low confidence top-10、mid top-10、high top-8。可以改成：

| 置信区间 | top-k | 策略 |
|---|---:|---|
| very high confidence | k=4 或 k=5 | aggressive compression |
| high confidence | k=6 或 k=8 | moderate compression |
| medium confidence | k=10 | safe default |
| low confidence | dense fallback top-10 或 top-12 | rescue |
| drift high | no compression | safety |

然后用 validation set 学习 threshold，而不是手工设定。目标函数可以是：

> minimize tokens subject to Hit@10 drop ≤ δ

例如 δ = 0.5 pp 或 1.0 pp。

这样主结果可能从 5% token saving 提升到 10–20%，同时仍保持 non-inferiority。只有当 savings 明显增大，统计显著性才更有说服力。

### 3.2 用 risk-controlled selective compression

把 context compaction 视为 selective prediction 问题。只有当模型确信“压缩不会降低 retrieval success”时才压缩。可以报告：

- coverage：多少 query 被压缩；
- risk：压缩 query 中 Hit@10 下降率；
- saving：压缩 query 的 token saving；
- global saving：整体 token saving；
- calibration curve：预测置信度 vs 实际 failure rate。

这比单一平均 token ratio 更强。

### 3.3 分别优化“质量提升”和“token saving”

现在 IntentWeight 同时声称 Hit@10 near-dense / above-dense 和 token saving，但两个目标可能冲突。建议拆成两个实验设置：

1. **Quality-preserving mode:** Hit@10 不劣，最大化 token saving。  
2. **Quality-improving mode:** token budget 相同，最大化 Hit@10 / EvidenceRecall / nDCG。

这样能避免审稿人觉得结果混在一起、不知道方法到底优化什么。

## 4. 第四优先级：加入真正强的 same-budget baseline

当前 baseline 包括 BM25-only、dense-only、dense+BM25 hybrid、full multi-route、gated variants、nearest-cluster、random/epsilon-greedy 等，但这还不够。最危险的问题是：**IntentWeight 的 5% token saving 是否只是 dense top-k 从 10 改到 8 的效果？** 当前 baseline 不能完全排除这个质疑。

必须增加以下 baseline：

| Baseline | 为什么关键 |
|---|---|
| Dense top-8 | 直接检验 IntentWeight 是否只是减少 k |
| Dense adaptive top-k by score threshold | 检验是否需要 LinUCB |
| Dense score gap / entropy confidence policy | 检验 confidence compaction 是否可由 dense 自身完成 |
| BM25+dense RRF same-token-budget | 检验多路 fusion 是否比静态 hybrid 真有优势 |
| Cross-encoder reranker + top-k compression | 顶会审稿人很可能期待这个 |
| Prompt/context compression baseline | 如 Selective Context / LLMLingua 类方法 |
| Stronger embedding model | 排除 MiniLM baseline 偏弱问题 |
| Late-interaction retriever | 如果算力允许，加入 ColBERT 类对照会显著增强说服力 |

审稿人最关心的对照应该是：

> 在相同 token budget 下，IntentWeight 是否显著优于 dense adaptive top-k？

如果不能赢这个 baseline，论文贡献会明显缩水。

## 5. 第五优先级：把 simulated feedback 做得更真实

当前反馈是 ground-truth-derived simulated feedback，不能证明真实 human feedback 下仍有效。

为了增强说服力，建议至少做三层反馈实验：

### Level 1：controlled simulation

保留现有 oracle / equal noisy / trust-weighted noise，但系统化扫参数：

- noise rate: 0%, 10%, 20%, 30%, 40%；
- trust calibration error；
- delayed feedback: delay = 1, 5, 20, 100 queries；
- missing feedback rate；
- adversarial feedback rate；
- non-stationary intent shift。

### Level 2：click-model simulation

不要只用 ground truth 生成反馈。可以模拟真实检索点击偏差：

- position bias；
- trust bias；
- user expertise bias；
- false positive clicks；
- no-click ambiguity；
- repeated user/session behavior。

这样比“GT-derived feedback”更接近生产场景。

### Level 3：小规模人工反馈

不需要很大，哪怕 100–300 query 的人工标注也会明显增强可信度。可以让 annotator 判断：

- retrieved context 是否足够回答；
- compressed context 是否丢失关键信息；
- dense 与 IntentWeight 哪个 context 更好；
- citation support 是否充分。

即使人工实验规模小，也比完全 simulated feedback 更有说服力。

## 6. 第六优先级：把 downstream generation 从 smoke test 扩展成正式实验

当前 downstream generation 只有 60 queries，应该改成正式 end-to-end evaluation：

| 项目 | 建议 |
|---|---|
| Query 数 | 至少 300–500，最好 1k |
| 生成模型 | 至少 2 个模型：一个强模型，一个成本敏感模型 |
| 评价方式 | LLM judge + 人工抽检 |
| 指标 | answer correctness、faithfulness、citation support、context sufficiency、hallucination rate |
| 统计 | paired win-rate、bootstrap CI、sign test |
| 成本 | prompt tokens、completion tokens、latency、$/query |

最终要证明的不是“retrieval Hit@10 没掉”，而是：

> 压缩后的 context 没有显著降低答案质量，同时真实降低了生成成本。

这会比单独报告 Hit@10 和 Tokens@10 更有说服力。

## 7. 第七优先级：增加跨域验证，形成“稳定有效”而非“单域有效”

当前主证据主要来自 LoTTE technology/search，其他数据集被定义为 supporting evidence 或 limitation cases。建议至少做：

| 类型 | 数据集角色 |
|---|---|
| LoTTE technology/search | 保留为主实验 |
| 另 2–3 个 LoTTE domains | 检验跨域稳定性 |
| 一个术语密集型技术/科学语料 | 检验 lexical + dense + cluster 是否有价值 |
| 一个多证据任务 | 检验 EvidenceRecall trade-off |
| 一个失败域 | 主动展示边界条件 |

不要害怕失败域。顶会论文可以接受“方法不是处处有效”，但需要清楚解释：

- 哪些 corpus geometry 有利于 IntentWeight；
- 哪些 query 类型适合压缩；
- 哪些任务必须保留 dense top-10 或 top-12；
- 哪些场景不应使用该方法。

## 8. 推荐的重写版主实验设计

### Experiment 1：Same-budget retrieval comparison

问题：在相同 token budget 下，IntentWeight 是否优于强 baseline？

比较：

- dense top-10；
- dense top-8；
- dense adaptive top-k；
- BM25+dense RRF same-budget；
- reranker same-budget；
- IntentWeight adaptive-k。

主指标：

- Hit@10；
- EvidenceRecall@10；
- MRR；
- nDCG；
- Tokens/query；
- paired significance。

### Experiment 2：Non-inferiority cost reduction

问题：在 retrieval quality 不劣于 dense 的约束下，能省多少 token？

报告：

- 最大 token saving；
- Hit@10 lower confidence bound；
- EvidenceRecall lower confidence bound；
- fallback rate；
- compression coverage；
- failure case rate。

### Experiment 3：Feedback robustness

问题：LinUCB + trust weighting 是否真的带来 route learning？

比较：

- no feedback；
- equal noisy；
- trust-weighted；
- delayed feedback；
- biased feedback；
- adversarial feedback；
- oracle upper bound。

主指标：

- selected-cluster hit；
- last true reward；
- final Hit@10；
- token saving；
- regret curve；
- convergence curve。

### Experiment 4：End-to-end generation

问题：压缩 context 是否真的不损害答案质量？

比较：

- dense top-10 context；
- dense top-8 context；
- IntentWeight compressed context；
- reranker compressed context；
- prompt compression baseline。

指标：

- answer correctness；
- faithfulness；
- citation support；
- hallucination；
- latency；
- cost。

### Experiment 5：Cross-domain generalization

问题：该方法在哪些域成立？

报告每个 domain 的：

- dense baseline；
- IntentWeight delta；
- token saving；
- geometry diagnostics；
- query bucket analysis。

## 9. 最关键的修改优先级表

| 优化点 | 解决的问题 | 具体做法 | 优先级 |
|---|---|---|---|
| Query-level paired significance | 目前 seed-level CI 说服力弱 | McNemar、paired bootstrap、paired permutation、win/loss/tie 表 | P0 |
| Non-inferiority framing | Hit gain 太小，不适合强 claim | 设定 Hit@10 drop ≤ 0.5/1.0 pp，同时证明 token saving > 0 | P0 |
| Dense adaptive top-k baseline | 排除“只是 top-k 变小”质疑 | dense top-8、score threshold、score gap confidence policy | P0 |
| 扩大 query 数 | 596 queries 难支撑小 delta | 增加到 2k–5k query，或加入更多 LoTTE domains | P0 |
| adaptive-k 替代固定 k=8 | 5% token saving 太小 | very-high confidence 压到 k=4/5/6，validation 学 threshold | P0 |
| same-budget 强 baseline | 排除弱 baseline 问题 | 加 reranker、compression、stronger encoder、static hybrid same-budget | P0 |
| 反馈鲁棒性实验 | simulated feedback 外部有效性弱 | delayed/noisy/biased/adversarial feedback + 小规模人工反馈 | P1 |
| 正式 generation evaluation | 60-query smoke 不足 | 300–1000 query，paired judge/human eval，faithfulness/citation/cost | P1 |
| 跨域验证 | 单一主域外推不足 | 多 LoTTE domains + 至少一个真实 vertical corpus | P1 |
| 分桶分析 | 平均结果解释不足 | 按 query 类型、置信度、lexical anchor、cluster hit 分析 | P1 |

## 结论性建议

最有效的提升路径是：

**先把主 claim 改成“Hit@10 non-inferior + token saving significant”，然后用 query-level paired test 证明；再加入 dense adaptive top-k 和 same-budget reranker/compression baseline；最后扩大 query/domain 和 generation evaluation。**

单纯把 seed 从 3 增到 10 会有帮助，但不会根本改变审稿判断。真正能改变接收概率的是证明三件事：

1. **不是随机波动：** paired significance 成立；  
2. **不是简单 top-k trick：** 强 adaptive baseline 打不过或不如 IntentWeight 稳定；  
3. **不是 retrieval-only 幻觉：** end-to-end answer quality 和 citation faithfulness 没有显著下降。
