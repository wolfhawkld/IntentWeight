# Updated Paper Review, Rerank Discussion, and Novelty Guidance

> 整理自针对最新版论文 `main(2).pdf` 的审核意见，以及关于是否需要做 rerank、novelty 是否应放在 final-context budget control / manifold / LinUCB 上的详细建议。  
> 评审标准：适当降低标准，不按顶刊 / 顶会强理论论文要求，而按应用型 NLP / RAG 系统论文 / ACL Findings / EMNLP Findings / industry track / workshop / 中等偏上会议标准判断。

---

## 1. 总体审核结论

根据 **2026-06-18 上传的新稿 main(2).pdf** 来看，这一版已经比上一版更成熟，尤其是把 claim 明确收束到 retrieval-backed QA、final evidence-context input tokens、calibration/test budget policy 和 dense fallback 上。

它现在不应再被按“顶刊 / 顶会强理论论文”来要求，而更适合按：

- 应用型 NLP 论文；
- RAG 系统论文；
- ACL Findings；
- EMNLP Findings；
- industry track；
- workshop；
- 中等偏上会议。

整体上，我会给出：

> **弱接收到边界接收之间，取决于是否补一个轻量 rerank / compression baseline，以及是否把 novelty 表述得更稳。**

---

## 一句话评价

这版论文已经具备一个相对完整的应用型贡献：

> **在 dense retrieval 作为 recall floor 的前提下，用 local geometry + LinUCB route confidence + feedback recovery 来控制最终送入 LLM 的 evidence context budget。**

但如果继续把 novelty 主要压在“流形理论”或“LinUCB 新算法”上，目前证据还不够，会增加被审稿人质疑“包装过度”的风险。

---

## 当前推荐判断

如果目标是顶刊 / NeurIPS / ICLR / ACL main 高标准：

> **Borderline / Weak Reject**

如果目标是 ACL Findings、EMNLP Findings、NAACL Findings、RAG workshop、industry track、applied NLP track、中等偏上的应用型会议：

> **Borderline / Weak Accept**

如果进一步补上一个轻量 rerank 或 sentence-level compression baseline，并把 novelty 重新包装为“manifold-guided budgeted evidence controller”，我认为可以到：

> **Weak Accept**

---

# 2. 这版相比上一版的主要提升

## 2.1 Claim 更收敛，可信度更高

新稿已经明确说明：虽然动机来自 broader knowledge-augmented agents，但实证验证只落在 retrieval-augmented QA 上。

它还区分了三层成本：

1. source candidates；
2. dense invocation rate；
3. final retrieved context tokens。

并把主效率 claim 放在最终进入 generator 的 evidence-context input tokens 上。

这一点很重要，因为它避免了之前容易被攻击的说法：

> candidate 少了，所以 LLM 成本一定低。

现在论文明确说：

> 只有 final context tokens 减少，才对应 LLM input cost 减少。

这是一个强改进。

---

## 2.2 Calibrated token-quality frontier 已经成为论文最强证据

新稿强调 frozen calibration/test budget policy：

1. 在 calibration queries 上选 budget policy；
2. 然后冻结到 test evaluation。

这个设计比直接调 test threshold 更可信。

论文现在声称 calibration-eligible operating points 在 100k、200k、638k 上节省 **6–18% final evidence-context tokens**，400k 是 positive diagnostic point 但未通过 calibration eligibility gate。

这比最早的 4.7–5.3% conservative saving 更有说服力。保守策略仍可作为安全 baseline，但主结果应放在 calibrated budget frontier 上。

---

## 2.3 Dense-only adaptive truncation 对照很有价值

现在论文已经比较清楚地说明：

> 简单 dense adaptive truncation 虽然也能省 token，但会带来更大的 Hit@10 loss；IntentWeight 的价值不是“省得最多”，而是 **在更小 quality loss 下省 context**。

这对审稿很关键，因为它直接回答：

> 你是不是只是把 top-10 改成 top-8 / top-k？

目前这个质疑已经被部分解决。

---

## 2.4 方法细节比之前更完整

新稿增加了：

- feature groups；
- route confidence；
- semantic drift；
- trust-weighted feedback；
- prequential protocol；
- feedback-triggered recovery；
- algorithm sketch；
- reproducibility parameters。

尤其是 route confidence 由 selected-arm value estimate、top-versus-rest arm margin、arm maturity 构成；semantic drift 定义为 one minus nearest selected-centroid similarity。

这比之前更可复现。

---

## 2.5 反馈部分定位更合理

新稿已经把 feedback 明确限制为：

- simulated；
- ground-truth-derived；
- controlled mechanism validation。

并且把 hard-case recovery 解释为 post-feedback repair，而不是 first-pass IID generalization。

这个收缩是对的。论文也明确说 same-query retry 是反馈后的修复机制，不是提前知道答案。

---

# 3. 当前仍然存在的主要问题

## 3.1 Novelty 仍然有“叙事重心不稳”的问题

论文现在有三个可能的 novelty 重心：

1. piecewise relevance-manifold assumption；
2. trust-weighted LinUCB route controller；
3. final-context budget control。

这三个都能讲，但不能同时都讲成“核心创新”。否则审稿人会觉得论文在找包装点。

目前最扎实的实验证据其实是：

> local geometry 有用，但不是充分条件；LinUCB 学到 route confidence，但最终收益体现在 context budget control；dense fallback 仍然必要。

新稿自己也承认 geometry diagnostics 支持的是 useful motivation and diagnostic，不是 theorem；context retention 会随 scale 下降，geometry alone 不能替代 dense retrieval。

所以如果强行把 novelty 放在“流形理论”，会被问：

> 你的 manifold 是定理、假设、诊断指标，还是实际算法依赖？

如果强行放在“LinUCB 新算法”，会被问：

> 你改了 LinUCB 的 regret bound 吗？有新的 bandit formulation 吗？和普通 contextual bandit 的本质区别是什么？

这两个方向不是不能做，但需要补足对应证据。

---

## 3.2 Rerank / compression baseline 仍是最容易被问到的实验缺口

新稿 related work 已经提到：

- Selective Context；
- LLMLingua；
- LLMLingua-2；
- DSLR；
- REPLUG。

并说明 IntentWeight operates earlier in the pipeline and is compatible with prompt compression, reranking, and black-box generation。

这段写得不错，但也带来一个问题：既然你承认这些方法相关且兼容，审稿人自然会问：

> 那为什么不和一个 reranker 或 compression baseline 比？

按非顶刊标准，这不是绝对必须，但它是最划算的补强实验之一。

---

## 3.3 下游 answer-quality 仍然只能作为 sanity check

新稿仍只有 60-query downstream answer-quality check。

论文自己也说它不显示 obvious degradation，但仍是 small sanity check，不是 full human evaluation。

如果论文主 claim 是 retrieval-level quality-cost frontier，这可以接受；但如果你要强调 LLM input cost saving 的生产价值，最好不要把 60-query check 写得太强。

---

## 3.4 Simulated feedback 还是不能支撑很强的 feedback-guided claim

新稿中 trust-weighted feedback improves policy metrics，例如：

- selected-cluster hit；
- last true reward；
- dense rate；
- LinUCB usage。

这些可以作为机制分析。

但 real feedback delayed、biased、sparse、user-dependent，论文也承认现在是 controlled simulated feedback，不是 collected production feedback。

所以“feedback-guided”可以保留，但最好不要把它写成真实用户反馈已经验证。

---

# 4. 关于 rerank：到底要不要做？

我的建议是：

> **要做，但不要把 rerank 并入主方法；把它作为 reviewer-facing diagnostic baseline。**

也就是说：

> rerank 不是为了改变论文方法，而是为了让审稿人相信：IntentWeight 的价值不是一个强 reranker baseline 就能完全解释掉。

---

## 4.1 为什么建议做 rerank baseline？

因为当前论文的主对照已经包括：

- dense-only；
- BM25；
- hybrid；
- dense adaptive truncation。

但还缺一个强 evidence refinement baseline。

RAG 论文里，审稿人看到 retrieval quality 和 final context budget，通常会自然想到：

> dense top-N + cross-encoder reranker + top-k / token budget

如果完全不做 rerank，可能会被认为 baseline 不够强。尤其论文 related work 已经提到 DSLR 这类 sentence-level reranking / reconstruction 方法，以及 context compression 方法。

---

## 4.2 但 rerank 不应该成为主方法

不要把 IntentWeight 改成：

> dense + BM25 + cluster + LinUCB + reranker + budget

这样会让方法更像堆系统模块，反而削弱论文主线。

更好的定位是：

> Reranking is a strong evidence-refinement baseline. IntentWeight is a lightweight route-and-budget controller. They solve adjacent but different parts of the pipeline.

也就是说：

- rerank 是排序质量增强器；
- IntentWeight 是预算与风险控制器。

---

## 4.3 最小可接受 rerank 实验怎么做？

如果资源有限，我建议只做一个轻量版本，不必全 scale 跑。

### 设置 A：Dense + Cross-Encoder Reranker

在 LoTTE technology/search 100k 或 200k 上做：

1. dense top-50；
2. cross-encoder rerank；
3. 取 top-10；
4. 再取 same-token-budget top-k；
5. 和 IntentWeight calibrated budget 比较。

推荐表格：

| Method | Hit@10 | MRR@10 | nDCG@10 | EvidenceRecall@10 | Context tokens | Token saving |
|---|---:|---:|---:|---:|---:|---:|
| Dense top-10 | baseline | baseline | baseline | baseline | baseline | 0 |
| Dense adaptive truncation |  |  |  |  |  |  |
| Dense + reranker top-10 |  |  |  |  |  |  |
| Dense + reranker same-budget |  |  |  |  |  |  |
| IntentWeight budget |  |  |  |  |  |  |

---

## 4.4 三种可能结果该怎么解释？

### 情况 1：IntentWeight 接近 reranker，且成本更低

这是最理想的。可以写：

> IntentWeight provides a lightweight alternative to reranking for budget-aware evidence selection.

### 情况 2：reranker 质量更高，但 token 或 latency 成本更高

也可以接受。可以写：

> Reranking improves ranking quality, while IntentWeight provides cheaper route-budget control; the two are complementary.

### 情况 3：reranker same-budget 全面优于 IntentWeight

这会削弱主 claim，但不一定毁掉论文。可以改成：

> IntentWeight is not a replacement for reranking; it is a routing and budget controller that can be combined with rerankers.

并增加一个组合实验：

> IntentWeight + reranker budget

如果组合效果最好，论文仍然能成立。

---

## 4.5 如果不想做 cross-encoder rerank，最低替代方案是什么？

做 **sentence-level MMR compression baseline**。

这个比 cross-encoder 轻，且更直接挑战 final-context budget control。

流程：

1. dense top-10；
2. split chunks into sentences；
3. query-sentence embedding similarity；
4. MMR 去冗余；
5. 选到和 IntentWeight 相同 token budget；
6. 比 Hit、EvidenceRecall、answer-quality sanity。

它可以叫：

> Dense+SentMMR@same-budget

这是非常划算的 baseline。即使不做 heavy reranker，我也建议至少做这个。

---

## 4.6 Rerank 实验是否“必须”？

按顶刊标准：

> 几乎必须。

按中等偏上应用型论文标准：

> **不是绝对必须，但强烈建议至少做一个轻量 rerank 或 compression baseline。**

如果时间非常紧，最低要求是：

1. 保留 dense adaptive truncation；
2. 增加 Dense+SentMMR@same-budget；
3. 在 limitation 里说明 cross-encoder reranker 是 future work。

但如果你们想显著降低被拒风险，我建议至少在 100k 上做一个 reranker baseline。

---

# 5. 关于 novelty：应该放在 final-context budget、流形理论，还是 LinUCB？

这是内部最关键的分歧。

我的直接结论：

> **不要把 novelty 单独放在 final-context budget control；也不要单独放在“流形理论”或“LinUCB 新算法”。最稳的做法是把 novelty 定义为：manifold-guided, feedback-adaptive, budgeted evidence selection controller。**

也就是说，创新不是某一个点，而是三者之间的耦合：

1. **piecewise local relevance structure** 提供结构性假设；
2. **LinUCB over cluster-local arms** 提供可学习的 route policy；
3. **final-context budget control** 提供实际 cost-quality objective；
4. **dense fallback / feedback recovery** 提供安全边界。

这样既满足希望强调“流形 / LinUCB”的诉求，又避免被审稿人质疑“你只是 budget control”。

---

# 6. 为什么不建议单独强调 final-context budget control？

“只是 budget control 不足以体现创新”这个判断有一部分是对的。

如果论文只说：

> 我们做 final-context budget control。

那确实容易被认为是：

- adaptive top-k；
- confidence thresholding；
- context truncation；
- prompt compression；
- engineering policy。

这不足以构成很强的算法 novelty。

所以 final-context budget control **适合作为 objective 和 measurable payoff**，但不适合作为唯一 novelty。

更好的说法是：

> We study budgeted evidence selection under a local relevance-structure prior.

也就是：

> budget 是目标，manifold / local structure 是假设，LinUCB 是学习机制。

---

# 7. 为什么不建议把 novelty 强行放在“流形理论”？

因为目前论文中的 manifold 证据是 diagnostic，不是 theoretical。

新稿中 geometry diagnostics 包括：

- NearestClusterHit@3；
- ContextRetention@10；
- PCAvar@64；
- PCAdim90。

论文明确说这些支持 piecewise relevance-manifold framing as useful motivation and diagnostic, not as a theorem。

这句话是对的，也应该保留。

如果你把论文包装成“流形理论论文”，审稿人会期待：

1. 明确定义 relevance manifold；
2. 证明或至少严格推导 local relevance structure；
3. 说明为什么 KMeans arms 近似 manifold patches；
4. 给出条件：什么数据分布下 local routing 优于 global dense；
5. 给出理论界或统计分析；
6. 证明 geometry diagnostics 与 retrieval gains 有稳定相关性。

目前论文还没有这些。因此如果标题或贡献过度强调“manifold theory”，会被审稿人反打：

> 这不是 manifold theory，只是 PCA + clustering diagnostics。

---

## 更好的处理方式

把“manifold”从理论主张改成 **structural prior**：

> We use a piecewise local relevance prior to motivate cluster-local arms and diagnostic calibration.

而不是：

> We propose a new relevance-manifold theory.

可以改名为：

- piecewise local relevance structure；
- local relevance patches；
- manifold-inspired route prior；
- local structure prior for budgeted evidence selection。

如果坚持保留“manifold”，建议写成：

> piecewise relevance-manifold assumption

但在摘要和贡献中加限定：

> bounded, diagnostic, operationalized through cluster-local routing and context-retention metrics.

---

# 8. 如果想把“流形理论”方向做强，后续应该怎么完善？

可以，但要补三类内容。

## 8.1 给出更正式的定义

现在的假设是自然语言描述：

> relevance follows local structure induced by terminology, neighborhoods, organization, intent.

建议形式化为：

设 embedding space 中存在若干 local patches \(M_1, \dots, M_K\)，对于 query \(q\)，其 relevant evidence \(G(q)\) 更可能集中在少数 patches 内：

\[
P(d \in G(q) \mid d \in M_{z(q)}) >
P(d \in G(q) \mid d \notin M_{z(q)})
\]

或者定义 local concentration ratio：

\[
LCR@K(q) =
\frac{
|G(q) \cap \bigcup_{c \in N_K(q)} C_c|
}{
|G(q)|
}
\]

其中 \(N_K(q)\) 是 query 最近的 K 个 clusters。

然后用它预测：

- Hit@10 gain；
- token saving；
- compression failure；
- dense fallback need。

---

## 8.2 证明 geometry diagnostic 和收益有关

当前你有 Figure 3 / Figure 4，已经说明 ContextRetention 和 quality-cost frontier 有关系，但关系不是 deterministic。

建议进一步加一个 correlation / regression analysis：

| Predictor | Target |
|---|---|
| NearestClusterHit@3 | IntentWeight Hit Δ |
| ContextRetention@10 | compression success |
| PCAvar@64 | local route reliability |
| semantic drift | fallback probability |
| route agreement | token saving without Hit loss |

例如：

\[
\Pr(\text{safe compression}) =
\sigma(
\beta_1 \cdot \text{ContextRetention}
+
\beta_2 \cdot \text{RouteAgreement}
-
\beta_3 \cdot \text{Drift}
)
\]

这会让 manifold 不只是“画图诊断”，而是进入决策模型。

---

## 8.3 增加反事实 / 负例实验

为了证明 local structure 真的有用，要加入：

| 实验 | 目的 |
|---|---|
| random clusters | 证明不是任意分组都行 |
| shuffled cluster labels | 证明 cluster identity 有信息 |
| HDBSCAN / spectral clusters | 证明不依赖 KMeans 特定实现 |
| no-geometry features | 证明 geometry features 有贡献 |
| high-drift-only bucket | 证明 drift 能预测失败 |
| low-retention domain | 证明 manifold assumption 不成立时收益下降 |

这样你可以写：

> The manifold prior is falsifiable: when local retention is low or clusters are randomized, routing gains and safe compression degrade.

这会显著增强“流形假设”的学术可信度。

---

# 9. 为什么不建议把 novelty 强行放在“LinUCB 新算法”？

目前你们用的是 LinUCB 标准形式：

\[
\hat{\theta}_a = A_a^{-1} b_a
\]

\[
s_t(a) = \hat{\theta}_a^\top x_t + \alpha \sqrt{x_t^\top A_a^{-1}x_t}
\]

这个是经典 LinUCB。

新稿真正的变化是：

- fixed cluster-local arms；
- trust-weighted feedback；
- cluster-only credit assignment；
- route confidence feeding budget policy；
- feedback-triggered recovery；
- dense / BM25 rescue paths。

这些是 **system adaptation of LinUCB**，不是严格意义上的新 bandit algorithm。

如果你把它包装成“LinUCB 新算法”，审稿人会问：

1. 新 regret bound 在哪里？
2. trust-weighted update 是否有理论性质？
3. partial feedback 和 noisy trust feedback 的假设是什么？
4. cluster-only reward 是否导致 biased estimator？
5. 与 contextual bandit baselines 比如 Thompson Sampling、epsilon-greedy、EXP4、NeuralUCB 的对比在哪里？

目前这些都还不够。

---

## 更好的处理方式

不要说：

> We propose a new LinUCB algorithm.

而说：

> We adapt LinUCB to fixed cluster-local evidence arms with trust-weighted route-level credit assignment and budget-aware recovery.

这句话更准。

---

# 10. 如果想把 LinUCB 方向做强，后续应该怎么完善？

可以走两个层次。

## 10.1 轻量增强：把它写成 LinUCB variant

命名：

> Trust-Weighted Cluster LinUCB

核心不是新 regret theory，而是一个 retrieval-specific adaptation：

1. arms = fixed cluster-local evidence regions；
2. reward = cluster-only retrieval success minus cost penalty；
3. update weight = feedback trust；
4. confidence = arm value + maturity + route margin；
5. risk = confidence + semantic drift；
6. recovery = negative feedback triggers safer budget / fallback。

你需要加一个 ablation table：

| Variant | Selected-cluster hit | Last true reward | Hit@10 | Token ratio |
|---|---:|---:|---:|---:|
| Random arms |  |  |  |  |
| Epsilon-greedy |  |  |  |  |
| Vanilla LinUCB |  |  |  |  |
| LinUCB + cluster-only reward |  |  |  |  |
| LinUCB + trust weighting |  |  |  |  |
| LinUCB + trust + budget recovery |  |  |  |  |

这样可以证明 LinUCB adaptation 不是可有可无。

---

## 10.2 强增强：提出 Budgeted Risk-Aware LinUCB

如果你们真的想讲“新算法”，可以把 action 从 cluster arm 扩展为：

\[
a = (\text{cluster route}, \text{budget level}, \text{fallback mode})
\]

其中：

- cluster route；
- budget level；
- fallback mode。

奖励定义为：

\[
r_t =
\mathbb{1}[\text{hit}]
-
\lambda \cdot \text{token\_cost}
-
\mu \cdot \mathbb{1}[\text{fallback}]
\]

风险约束：

\[
P(\text{miss} \mid q, a) \le \epsilon
\]

然后方法不再只是 LinUCB 选 cluster，而是：

> LinUCB selects budgeted evidence actions under dense-fallback safety constraints.

这才更像新算法。但这需要更多实验，否则会显得复杂化。

---

# 11. 我建议的最终 novelty 定位

建议采用一个“中间路线”，既不只说 budget control，也不把理论夸大。

## 推荐标题方向

### 方案 A：最稳

**IntentWeight: Manifold-Guided Budgeted Evidence Selection with Feedback-Adaptive Routing**

优点：保留 manifold，强调 budgeted evidence selection，避免说 new LinUCB algorithm。

### 方案 B：偏系统

**IntentWeight: Feedback-Adaptive Local Evidence Routing for Budgeted RAG Context Selection**

优点：更像应用型系统论文，风险低。

### 方案 C：偏理论动机

**IntentWeight: Piecewise Local Relevance Priors for Feedback-Adaptive Evidence Budgeting**

优点：把 manifold 改成 local relevance prior，更稳。

我最推荐 **方案 A**。

---

## 推荐 contribution 重写

建议贡献写成 5 点：

1. **Piecewise local relevance prior.**  
   We formulate a bounded local-structure hypothesis for vertical-domain evidence retrieval and operationalize it through cluster-local routing diagnostics.

2. **Trust-weighted cluster LinUCB controller.**  
   We adapt LinUCB to fixed cluster-local evidence arms with route-level credit assignment and trust-weighted simulated feedback.

3. **Risk-aware final-context budget policy.**  
   We use route confidence, semantic drift, and dense fallback to decide when final evidence context can be compacted.

4. **Calibration/test quality-cost frontier.**  
   We evaluate frozen budget policies and show 6–18% final evidence-context token savings under bounded operating points, while avoiding larger losses from dense-only adaptive truncation.

5. **Recovery and boundary analysis.**  
   We show feedback-triggered recovery for compression-induced tail failures and document cases where geometry or compaction should not be trusted.

这样同事关心的“流形”和“LinUCB”都有位置，但不会把它们过度包装成“理论创新”或“新 bandit 算法”。

---

# 12. 关于是否要继续强化 final-context budget control

要强化，但不要孤立强化。

final-context budget control 的价值在于：

1. 它是实际成本收益来源；
2. 它区分了 candidate reduction 和 LLM input cost；
3. 它有 dense adaptive truncation baseline 支撑；
4. 它能和 reranker / compression 区分；
5. 它是论文最容易被应用型 reviewer 接受的贡献。

所以它不能被删，也不应该降级为附属实验。

但是建议表述为：

> final-context budget control is the objective, not the sole novelty.

也就是说：

- novelty hypothesis：piecewise local relevance；
- learning mechanism：trust-weighted cluster LinUCB；
- deployment objective：final-context budget control；
- safety mechanism：dense fallback + feedback recovery。

这个结构最稳。

---

# 13. 修改建议：按优先级

| 优先级 | 建议 | 目的 |
|---:|---|---|
| P0 | 至少补一个 Dense+SentMMR@same-budget 或 reranker baseline | 回应“为什么不用 rerank / compression” |
| P0 | 把 novelty 改成 “manifold-guided budgeted evidence selection” | 平衡同事想法和审稿风险 |
| P0 | 不要声称“new LinUCB algorithm” | 避免被理论审稿人攻击 |
| P0 | 保留 final-context budget control 作为 objective 和主实验证据 | 这是当前最扎实的贡献 |
| P1 | 加 random cluster / no-geometry / no-LinUCB ablation | 支撑 manifold 和 LinUCB 的必要性 |
| P1 | 增加 geometry-to-gain correlation / regression | 让 manifold 不只是动机 |
| P1 | 扩大 downstream QA 至 200–300 queries | 支撑 LLM input cost claim |
| P1 | 加 noisy / delayed feedback setting | 降低 simulated feedback 风险 |
| P2 | 尝试 HDBSCAN / arm count sensitivity | 增强 local structure 分析 |
| P2 | 把 400k diagnostic point 从主 claim 降级 | 避免 calibration eligibility 被抓住 |

---

# 14. 我会怎么改摘要

建议改成类似：

> We propose IntentWeight, a manifold-guided, feedback-adaptive controller for budgeted evidence selection in retrieval-augmented QA. The key hypothesis is that vertical-domain relevance often concentrates in local evidence regions induced by terminology, workflow structure, and user intent. IntentWeight operationalizes this hypothesis by constructing fixed cluster-local retrieval arms, learning route confidence with trust-weighted LinUCB, and using dense/BM25 fallback to guard against unsafe local pruning. A risk-aware final-context policy converts route confidence into reduced evidence context sent to the generator. On LoTTE technology/search, frozen calibration/test budget policies save 6–18% final evidence-context input tokens at calibration-eligible operating points while avoiding the larger Hit@10 losses of dense-only adaptive truncation. Geometry diagnostics and cross-domain LoTTE science/search validation support the local-structure prior, while feedback-triggered recovery repairs a meaningful fraction of compression-induced tail failures. The results position IntentWeight not as a new retriever or a universal dense replacement, but as a manifold-guided route-and-budget controller for structured domain evidence selection.

这个版本同时保留：

- manifold；
- LinUCB；
- budget；
- dense fallback；
- bounded claim。

---

# 15. 最终建议

## 对 rerank 的建议

**建议做一个轻量 rerank / compression baseline，但不要把 rerank 加进主方法。**

最小版本：

- Dense top-10 + sentence-level MMR same-budget；
- 或 Dense top-50 + cross-encoder reranker same-budget；
- 只跑 LoTTE technology/search 100k / 200k 即可。

这样足以降低 reviewer 对 baseline 的质疑。

## 对 novelty 的建议

不要在三者中二选一。最佳结构是：

> **Manifold-guided local route learning + trust-weighted LinUCB adaptation + risk-aware final-context budget control。**

其中：

- **manifold / local structure** 是理论动机和可诊断假设；
- **LinUCB** 是反馈自适应机制；
- **final-context budget** 是实际优化目标和成本收益来源。

如果只强调 budget，创新感偏弱。  
如果只强调 manifold，理论证据不够。  
如果只强调 LinUCB，新算法性不够。  
三者结合，才是这篇论文最稳的 novelty。

## 对当前版本的综合判断

按降低后的标准，我认为这篇论文已经可以作为一篇 **有应用价值的 RAG evidence-selection 系统论文**。

目前最需要补的不是大规模重写，而是：

1. 补一个 rerank 或 compression baseline；
2. 把 novelty 重写成 manifold-guided budgeted controller；
3. 增加 no-geometry / random-cluster / no-LinUCB ablation；
4. 不要过度声称 manifold theory 或 new LinUCB algorithm；
5. 把 60-query generation check 保持为 sanity check，不要作为主 claim。

这样改完后，它的定位会更稳，也更容易说服非顶刊标准下的审稿人。
