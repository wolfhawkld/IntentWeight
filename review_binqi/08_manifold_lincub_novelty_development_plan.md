# Manifold + LinUCB Novelty Development Plan

> 整理自关于“如果 novelty 仍然希望尽量往 manifold + LinUCB 方向走，还需要做什么”的详细建议。  
> 核心结论：可以往 **manifold + LinUCB** 方向走，但要把它从“概念包装”升级成“可检验的结构假设 + 明确的 bandit 变体 + 因果消融证据”。

---

## 总体建议

可以往 **manifold + LinUCB** 方向走，但要把它从“概念包装”升级成：

1. **可检验的结构假设；**
2. **明确的 bandit 变体；**
3. **因果消融证据。**

否则审稿人会认为：

> 你只是用了 KMeans cluster 做 arms，再套了标准 LinUCB，最后用 budget policy 省 token。

我建议最终定位不要写成：

> 我们提出新的流形理论。

也不要写成：

> 我们提出新的 LinUCB 算法。

而是写成：

> **IntentWeight is a manifold-guided, trust-weighted cluster-LinUCB controller for budgeted evidence selection.**

也就是：

- **manifold** 是结构先验；
- **LinUCB** 是自适应学习机制；
- **final-context budget** 是应用目标和收益体现。

这样既能保留你们想强调的 novelty，又不会被审稿人用“没有理论证明 / 没有新 regret bound”直接打掉。

---

# 1. 当前版本在 manifold + LinUCB 方向已经有什么基础？

当前稿子其实已经具备一些基础，不是完全从零开始。

## 1.1 Piecewise relevance-manifold assumption 已经有 bounded framing

论文已经把 piecewise relevance-manifold assumption 定义为一个 **bounded assumption**：

> vertical-domain evidence retrieval 中，query-document relevance 往往呈现由术语、语义邻域、文档组织和用户意图诱导的 piecewise local structure。

同时也明确说：

- geometry 不是充分条件；
- dense 仍是 recall floor；
- BM25 提供 lexical anchors；
- cluster-local retrieval 提供 local evidence patches。

这个定位是稳的。

---

## 1.2 KMeans clusters 作为 fixed LinUCB arms 已经有方法基础

当前方法确实把 KMeans / MiniBatchKMeans clusters 用作 fixed LinUCB arms，并解释了为什么使用固定 32 arms：

- LinUCB 需要固定 arm space；
- fixed arms 有利于跨 scale 可复现和比较；
- cluster route 在 selected arms 内做 dense retrieval；
- dense / BM25 作为 rescue paths。

这为 “cluster-LinUCB” 提供了方法基础。

---

## 1.3 LinUCB 部分已经不只是公式

当前 LinUCB 部分已经加入了：

- route confidence；
- semantic drift；
- trust-weighted feedback；
- cluster-only credit assignment；
- prequential no-leakage protocol。

尤其是：

- route confidence 来自 selected-arm value estimate、top-versus-rest arm margin 和 arm maturity；
- semantic drift 定义为 one minus nearest selected-centroid similarity；
- low confidence 或 high drift 会保留 dense fallback。

所以不是完全裸用 LinUCB。

---

## 1.4 论文已经承认 manifold evidence 是 diagnostic，不是 proof

当前稿子承认：

> geometry diagnostics support useful motivation and diagnostic analysis, not a theorem-level proof.

这是对的。

Geometry diagnostics 包括：

- NearestClusterHit@3；
- PCA spectrum；
- ContextRetention；
- route / retention diagnostics。

这些说明 local geometry 对 LoTTE routing 有信息量，且 dense retrieval 仍然必要。

所以现在的问题不是“没有 manifold + LinUCB 基础”，而是：

> **目前证据还停留在 diagnostic + engineering adaptation 层面，尚不足以把 novelty 强压在 manifold theory 或 LinUCB algorithm 上。**

---

# 2. 如果 novelty 要往 manifold + LinUCB 走，最稳的主张是什么？

不建议写：

> We propose a new relevance-manifold theory.

也不建议写：

> We propose a new LinUCB algorithm.

这两个都太容易被攻击。

更稳的主张是：

> We propose a **manifold-guided cluster-LinUCB evidence controller**: local relevance structure defines fixed cluster-local evidence arms; trust-weighted LinUCB learns which local arms are reliable under query context and feedback; route confidence and drift then determine whether compact evidence can be trusted or dense fallback is needed.

中文就是：

> 本文不是单独提出“流形理论”或“新 LinUCB 算法”，而是提出一种 **由局部相关结构驱动的 cluster-LinUCB evidence controller**。流形假设决定 arm 构造，LinUCB 学习 arm 可信度，budget control 只是最终把这种可信度转化为成本收益的下游决策。

这样 novelty 的逻辑链是完整的。

| 层次 | 作用 | 当前是否已有 | 还需要补什么 |
|---|---|---:|---|
| Manifold / local relevance prior | 解释为什么 cluster-local arms 有意义 | 有初步定义和 diagnostics | 需要更正式定义、负例、相关性分析 |
| Cluster-LinUCB | 学习哪个 local region 对当前 query 可信 | 有公式、trust weighting、cluster-only credit | 需要更强 bandit ablation 和 regret / proxy regret 曲线 |
| Confidence / drift | 判断 local routing 是否安全 | 已有 route confidence 和 drift | 需要 calibration / risk prediction 分析 |
| Final context budget | 把可信度变成 cost-quality trade-off | 已有 6–18% saving | 作为 payoff，而不是唯一 novelty |

---

# 3. Manifold 方向要补什么？

如果希望“piecewise relevance-manifold”不只是动机，至少要补 **定义、验证、反事实、预测能力** 四件事。

---

## 3.1 给出一个更正式的 manifold / local relevance 定义

当前定义偏自然语言，适合 introduction，但如果要作为 novelty，需要在方法部分加入一个形式化定义。

可以定义一个 **Local Relevance Concentration** 指标。

设语料 chunks 被划分为 clusters \(C_1,\dots,C_K\)，query \(q\) 的 ground-truth evidence set 为 \(G(q)\)，query 最近的 top-m clusters 为 \(N_m(q)\)。定义：

\[
LRC_m(q)=
\frac{
|G(q)\cap \bigcup_{c\in N_m(q)} C_c|
}{
|G(q)|
}
\]

如果 \(LRC_m(q)\) 高，说明 relevant evidence 集中在 query 附近的少数 local patches 内。

然后定义全局平均：

\[
LRC_m =
\mathbb{E}_{q\in Q_{GT}}[LRC_m(q)]
\]

这比单纯 NearestClusterHit@K 更强，因为 NearestClusterHit 只看“有没有一个 GT chunk 落在最近 clusters”，而 LRC 可以看 **GT evidence 的集中程度**。

建议新增 3 个指标：

| 指标 | 说明 | 为什么重要 |
|---|---|---|
| Local Relevance Concentration \(LRC_m\) | GT evidence 有多少比例落在 query 最近 m 个 clusters | 直接检验“piecewise local relevance” |
| Cluster Entropy of Evidence | GT evidence 分布在多少 clusters，上熵多大 | 判断 evidence 是否局部集中 |
| Safe Locality Rate | 只用 nearest clusters 是否能保持 dense-level Hit@10 | 连接 manifold 到 retrieval outcome |

这样 manifold 就不只是 PCA 图，而是和 retrieval task 直接绑定。

---

## 3.2 证明 manifold diagnostics 能预测方法收益

当前稿子中，geometry diagnostics 已经显示 NearestClusterHit@3 在 LoTTE domains 上较高，但 ContextRetention 会随 scale 下降；论文也说 geometry 与 quality-cost frontier 的关系 informative but not deterministic。

这句话很稳，但还不够强。如果希望 manifold 成为 novelty，需要证明：

> local geometry diagnostics 不只是“看起来合理”，而是能预测什么时候 IntentWeight 有效、什么时候会失败。

建议做一个 query-level 或 bucket-level regression：

\[
P(\text{safe compression}_q)
=
\sigma(
\beta_1 \cdot \text{NearestClusterHitScore}_q
+
\beta_2 \cdot \text{RouteAgreement}_q
+
\beta_3 \cdot \text{ContextRetentionProxy}_q
-
\beta_4 \cdot \text{SemanticDrift}_q
)
\]

其中 safe compression 可以定义为：

\[
\text{safe}_q =
\mathbb{1}[
Hit_{IntentWeight}(q)=Hit_{Dense}(q)
\land
Tokens_{IntentWeight}(q)<Tokens_{Dense}(q)
]
\]

然后报告：

| Predictor | Target | 期望结果 |
|---|---|---|
| Nearest cluster similarity | safe compression | 正相关 |
| Route agreement | safe compression | 正相关 |
| Semantic drift | compression failure | 正相关 |
| Arm maturity | safe compression | 正相关 |
| ContextRetention proxy | Hit preservation | 正相关 |

如果这个分析成立，就可以写：

> The manifold diagnostics are predictive of safe budgeted evidence selection, not merely descriptive.

这比“我们画了 PCA / cluster diagnostic”强很多。

---

## 3.3 做 random cluster / shuffled cluster 的反事实实验

这是最关键的 manifold 实验之一。

如果 local geometry 真有用，那么 random cluster 或 shuffled cluster label 应该明显变差。

建议加以下 ablation：

| Variant | 目的 | 预期 |
|---|---|---|
| KMeans clusters | 主方法 | 最好或较好 |
| Random equal-size clusters | 破坏几何结构 | NearestClusterHit、selected-cluster hit、budget safety 下降 |
| Shuffled cluster labels | 保留 cluster size，破坏语义 | route learning 下降 |
| Nearest centroid static routing | 不用 LinUCB，只用最近 cluster | 检验 geometry-alone 上限 |
| No-geometry features | LinUCB 去掉 centroid / drift / PCA features | 检验 geometry features 的贡献 |
| Dense/BM25 only + same budget | 检验没有 cluster-local arms 是否足够 | 应劣于完整模型或更不稳 |

这个实验非常重要，因为它可以直接支撑：

> local geometry is not decorative; it changes route learning and safe compaction behavior.

如果 random clusters 结果接近 KMeans，那 manifold claim 基本就站不住；如果明显变差，manifold novelty 会强很多。

---

## 3.4 做 arm count sensitivity

当前稿子说使用 32 arms 是 practical balance，arm count sensitivity 留给 future work。

如果要强调 manifold + LinUCB，这个不能只留 future work，至少要做小规模实验。

建议在 LoTTE 100k 或 200k 上跑：

\[
K \in \{8,16,32,64,128\}
\]

看 local granularity 和 feedback sample size 的 trade-off。

主指标：

- NearestClusterHit@3；
- LRC@3；
- selected-cluster hit；
- last true reward；
- Hit@10；
- token saving；
- feedback convergence speed。

如果出现一个 reasonable sweet spot，例如 32 或 64 最好，就可以说：

> The local relevance prior requires a balance between geometric resolution and bandit feedback density.

这会让 manifold + LinUCB 的耦合更可信。

---

## 3.5 做 cross-clustering robustness

如果只用 KMeans，审稿人会问：

> 你证明的是 manifold，还是 KMeans artifact？

建议至少补一个替代 clustering：

| Clustering | 说明 |
|---|---|
| KMeans / MiniBatchKMeans | 当前主方法 |
| Spherical KMeans | 更适合 cosine embedding |
| HDBSCAN | density-based local regions |
| Graph community / kNN graph clusters | 更接近 manifold neighborhood |

如果时间有限，至少做 **spherical KMeans** 或 **KMeans with different seeds**。

如果替代 clustering 结果方向一致，就能加强“local structure prior”而不是“KMeans trick”。

---

# 4. LinUCB 方向要补什么？

如果要把 novelty 往 LinUCB 方向推，需要证明它不是“标准 LinUCB 随便套一下”，而是一个 retrieval-specific adaptation。

当前稿子已经有：

- trust-weighted update；
- cluster-only credit assignment；
- prequential no-leakage protocol；
- route confidence；
- semantic drift；
- confidence-to-budget coupling。

但还需要更多对照和指标。

---

## 4.1 给方法命名：Trust-Weighted Cluster LinUCB

建议不要说“new LinUCB algorithm”，而说：

> **Trust-Weighted Cluster LinUCB**, a retrieval-specific LinUCB adaptation over fixed local evidence arms.

这比“new algorithm”更稳。

它的特殊性可以写成 5 点：

1. **cluster-local arms**：arms 不是 retrieval method，而是 domain corpus 的 local evidence patches；
2. **cluster-only credit assignment**：只根据 cluster route 自身质量更新 arm，避免 dense / BM25 rescue 污染 reward；
3. **trust-weighted updates**：反馈不被视为 perfect oracle，而是按 reliability 缩放；
4. **route confidence extraction**：LinUCB 不只是选 arm，还产生 confidence signal；
5. **risk-aware fallback / budget coupling**：confidence 和 semantic drift 决定是否压缩 context 或回退 dense。

这已经构成一个 **application-specific LinUCB variant**。

---

## 4.2 加 bandit baseline 对照

当前已有 random / epsilon-greedy / nearest-cluster 等 baseline，但如果要强调 LinUCB，需要把 bandit 对照放成主表。

建议表格：

| Policy | Context features | Feedback | Trust weight | Cluster-only credit | Selected-cluster hit | Last true reward | Final Hit@10 | Token ratio |
|---|---|---|---|---|---:|---:|---:|---:|
| Random cluster | ✗ | ✗ | ✗ | ✗ |  |  |  |  |
| Nearest cluster | geometry only | ✗ | ✗ | ✗ |  |  |  |  |
| Epsilon-greedy | weak | ✓ | ✗ | ✓ |  |  |  |  |
| UCB no context | ✗ | ✓ | optional | ✓ |  |  |  |  |
| Vanilla LinUCB | ✓ | ✓ | ✗ | fused reward |  |  |  |  |
| Cluster-only LinUCB | ✓ | ✓ | ✗ | ✓ |  |  |  |  |
| Trust-weighted Cluster LinUCB | ✓ | ✓ | ✓ | ✓ |  |  |  |  |
| Trust-weighted + budget recovery | ✓ | ✓ | ✓ | ✓ |  |  |  |  |

需要证明：

> LinUCB adaptation improves the policy field, not only the final fused ranking.

---

## 4.3 报告 regret / proxy regret 曲线

如果想让 LinUCB 更像算法贡献，就不能只报最后 Hit@10。建议报告 prequential learning curve。

定义 oracle arm：

\[
a_t^* = \arg\max_a r_t(a)
\]

其中 \(r_t(a)\) 是该 query 上每个 cluster-local arm 的 hindsight cluster-only reward。

定义 instantaneous proxy regret：

\[
\text{regret}_t =
r_t(a_t^*) - r_t(a_t)
\]

报告 cumulative regret：

\[
R_T = \sum_{t=1}^{T} \text{regret}_t
\]

不一定要证明理论 regret bound，但可以画：

- random；
- epsilon-greedy；
- vanilla LinUCB；
- trust-weighted Cluster LinUCB；
- oracle upper bound。

如果 trust-weighted Cluster LinUCB 的 cumulative proxy regret 下降更快，就能显著增强 LinUCB novelty。

注意表述要谨慎：

> We report empirical proxy regret under hindsight cluster-only rewards, not a formal regret guarantee.

---

## 4.4 做 feedback noise / delay / trust calibration 实验

当前稿子承认真实反馈是 delayed、biased、sparse、user-dependent，当前实验是 controlled simulated feedback，不证明真实 human feedback 已经解决。

如果要强调 feedback + LinUCB，这个必须加强。

建议做 4 种 feedback setting：

| Setting | 目的 |
|---|---|
| Oracle feedback | 上界 |
| Equal noisy feedback | 无 trust baseline |
| Trust-weighted noisy feedback | 当前主方法 |
| Miscalibrated trust | 检验 trust 错误时是否崩 |
| Delayed feedback | 模拟真实用户延迟 |
| Click-biased feedback | 模拟 implicit feedback |
| Missing feedback | 反馈稀疏性 |
| Adversarial feedback | 安全边界 |

主指标：

- selected-cluster hit；
- last true reward；
- proxy regret；
- final Hit@10；
- token ratio；
- false compression rate；
- recovery rate；
- new regressions。

这样 LinUCB 的 novelty 不只是“我用它”，而是：

> trust-weighted LinUCB remains useful under controlled noisy feedback and reveals the failure boundary under delay / bias / trust miscalibration.

---

## 4.5 把 action space 扩展成 budgeted arm，如果想更强

当前 LinUCB 主要选 cluster-local arms，budget policy 是后续模块。若想让 LinUCB 成为更核心创新，可以把 action 定义为：

\[
a = (c, b, f)
\]

其中：

- \(c\)：cluster arm；
- \(b\)：budget level，例如 top-4 / top-6 / top-8 / top-10 / token ratio；
- \(f\)：fallback mode，例如 dense fallback on / off。

reward：

\[
r_t(a)=
\mathbb{1}[\text{Hit@10}]
-\lambda \cdot \text{TokenRatio}
-\mu \cdot \mathbb{1}[\text{Fallback}]
\]

约束：

\[
P(\text{miss}\mid q_t,a_t)\le \epsilon
\]

这可以命名为：

> **Risk-Aware Budgeted Cluster LinUCB**

这才更像“新算法”。但代价是实验复杂度显著上升，需要对比：

- Cluster-only LinUCB；
- Budget-only policy；
- Budgeted Cluster LinUCB；
- oracle budget；
- dense adaptive budget。

如果时间有限，不建议现在大改成这个；但如果后续想投更强 venue，这是最值得发展的方向。

---

# 5. 现在最应该补的实验组合

如果目标是让 **manifold + LinUCB novelty** 更站得住，建议按优先级做以下实验。

---

## P0：必须做，性价比最高

### 实验 1：Random / shuffled cluster 反事实

目的：证明 local geometry 不是装饰。

| Variant | 指标 |
|---|---|
| KMeans clusters | 主方法 |
| Random equal-size clusters | 破坏 geometry |
| Shuffled cluster labels | 保留 size，破坏语义 |
| Nearest-cluster static | geometry-only baseline |

报告：

- NearestClusterHit@3；
- LRC@3；
- selected-cluster hit；
- final Hit@10；
- token saving；
- false compression rate。

如果 KMeans 明显优于 random / shuffled，manifold claim 会强很多。

---

### 实验 2：No-geometry / no-LinUCB ablation

目的：证明 manifold features 和 LinUCB 都有必要。

| Variant | 去掉什么 |
|---|---|
| Full IntentWeight | - |
| No local geometry features | 去掉 centroid similarity、PCA projection、drift |
| No LinUCB | 静态 cluster routing |
| No trust weighting | 等权 noisy feedback |
| No cluster-only credit | 用 fused reward |
| No feedback | 只用初始 policy |

报告：

- selected-cluster hit；
- last true reward；
- Hit@10；
- token ratio；
- recovery rate。

这个表可以直接支撑：

> local geometry structures the arm space; LinUCB learns reliability; trust-weighted credit improves adaptive routing.

---

### 实验 3：Geometry-to-gain 相关性分析

目的：证明 manifold diagnostics 能预测收益。

把 query 或 bucket 分成：

- high route agreement；
- low route agreement；
- low semantic drift；
- high semantic drift；
- high nearest-centroid similarity；
- low nearest-centroid similarity；
- high LRC；
- low LRC。

报告：

| Bucket | Hit Δ | Token saving | Compression failure rate |
|---|---:|---:|---:|

如果 high-locality bucket 明显更适合压缩，manifold claim 就从“动机”变成“predictive prior”。

---

### 实验 4：Bandit baseline + proxy regret

目的：证明 LinUCB adaptation 有效。

比较：

- random；
- epsilon-greedy；
- UCB no context；
- vanilla LinUCB；
- trust-weighted Cluster LinUCB。

报告：

- learning curve；
- selected-cluster hit；
- proxy regret；
- last true reward；
- final Hit@10；
- dense fallback rate；
- token ratio。

这个实验会直接加强 LinUCB novelty。

---

## P1：强烈建议

### 实验 5：Arm count sensitivity

在 100k 或 200k 跑：

\[
K \in \{8,16,32,64,128\}
\]

看 local granularity 和 feedback sample size 的 trade-off。

如果 32 是 reasonable sweet spot，当前设计就更有依据。

---

### 实验 6：Alternative clustering robustness

至少做一个：

- spherical KMeans；
- HDBSCAN；
- kNN graph communities。

如果不同 clustering 下 local relevance signal 仍成立，manifold claim 更稳。

---

### 实验 7：Noisy / delayed feedback

至少做：

- 10%、20%、30% noise；
- delayed feedback = 5 / 20 queries；
- missing feedback rate。

如果 trust-weighted LinUCB 对 moderate noise 稳定，对 high noise 失效，也没关系；这能展示边界。

---

# 6. 论文写法应该怎么改？

如果要强调 manifold + LinUCB，建议贡献重写为下面这种结构。

## 推荐贡献版本

1. **Piecewise local relevance prior.**  
   We formulate a bounded piecewise local relevance assumption for vertical-domain evidence retrieval and operationalize it through cluster-local evidence patches.

2. **Manifold diagnostics and falsification.**  
   We introduce local-structure diagnostics, including NearestClusterHit, ContextRetention, and Local Relevance Concentration, and test them with random-cluster and no-geometry controls.

3. **Trust-weighted Cluster LinUCB.**  
   We adapt LinUCB to fixed cluster-local evidence arms with cluster-only credit assignment, trust-weighted feedback, and route-confidence extraction.

4. **Risk-aware evidence control.**  
   Route confidence and semantic drift decide when local evidence can be trusted and when dense / BM25 fallback should remain active.

5. **Quality-cost frontier.**  
   Under frozen calibration/test policies, the controller reduces final evidence-context tokens while avoiding the larger Hit losses of dense-only adaptive truncation.

这样写，budget control 不再是唯一创新，而是前面 manifold + LinUCB 的结果体现。

---

# 7. 标题建议

如果希望 novelty 明确往 manifold + LinUCB 靠，可以考虑：

## 最推荐

**IntentWeight: Manifold-Guided Cluster LinUCB for Budgeted Evidence Selection**

这个标题非常直接：

- Manifold-Guided：保留 local relevance novelty；
- Cluster LinUCB：突出 bandit adaptation；
- Budgeted Evidence Selection：保留实际任务目标。

## 更稳一点

**IntentWeight: Trust-Weighted Cluster LinUCB under a Piecewise Local Relevance Assumption**

这个标题更学术，但 budget / cost 的价值弱一点。

## 更系统一点

**IntentWeight: Feedback-Adaptive Local Evidence Routing for Budgeted RAG Context Selection**

这个最稳，但弱化了 manifold。

如果内部更想突出 manifold + LinUCB，我会选第一个。

---

# 8. 摘要可以怎么改？

可以写成：

> We propose IntentWeight, a manifold-guided Cluster LinUCB controller for budgeted evidence selection in retrieval-augmented QA. The key hypothesis is that vertical-domain relevance is not uniformly distributed in embedding space, but concentrates in piecewise local evidence regions induced by terminology, workflow structure, and user intent. IntentWeight operationalizes this hypothesis by constructing fixed cluster-local evidence arms, learning their query-conditioned reliability with trust-weighted LinUCB, and extracting route confidence for risk-aware dense fallback and final-context compaction. We evaluate the local-structure prior with geometry diagnostics and random-cluster controls, and evaluate the controller under a no-leakage prequential feedback protocol. On LoTTE technology/search, frozen calibration/test budget policies reduce final evidence-context input tokens while avoiding the larger Hit@10 losses of dense-only adaptive truncation. The results support IntentWeight as a manifold-guided adaptive evidence controller, not as a universal dense replacement or a proof that geometry alone solves retrieval.

这段的好处是：

- 把 manifold 放在 hypothesis；
- 把 LinUCB 放在 controller；
- 把 budget 放在 payoff；
- 明确不是 dense replacement；
- 避免“新理论 / 新算法”过度承诺。

---

# 9. 什么说法要避免？

## 避免 1：不要说“证明了 relevance manifold”

当前最多能说：

> supports a piecewise local relevance prior.

不要说：

> proves a relevance manifold exists.

因为当前 diagnostics 不是 theorem。

---

## 避免 2：不要说“提出新的 LinUCB 算法”

除非真的加了新的 action space、reward、理论分析或 regret bound。

更稳的是：

> retrieval-specific adaptation of LinUCB.

---

## 避免 3：不要让 budget control 看起来只是附属技巧

budget control 仍然重要，因为它是最终收益。但它应被表述为：

> the downstream decision layer that converts route confidence into cost-quality control.

而不是：

> 本文唯一创新是 final-context budget control.

---

# 10. 最小改稿方案

如果时间有限，我建议做 **4 个最小补强**：

| 优先级 | 内容 | 为什么 |
|---:|---|---|
| P0 | Random cluster / shuffled cluster control | 支撑 manifold，不做这个很难说 local structure 是核心 |
| P0 | No-geometry / no-LinUCB ablation | 支撑 manifold features 和 LinUCB 的必要性 |
| P0 | Bandit baseline：epsilon-greedy / vanilla LinUCB / trust-weighted LinUCB | 支撑 LinUCB adaptation |
| P0 | Geometry-to-safe-compression bucket analysis | 证明 manifold diagnostic 能预测收益 |

这 4 个做完，就可以比较有底气地把 novelty 写成：

> manifold-guided trust-weighted Cluster LinUCB for budgeted evidence selection.

如果只做预算和 token saving，而不做这 4 个实验，那仍然不建议把 novelty 强压在 manifold + LinUCB 上。

---

# 11. 更强版本：如果后续想继续发展成更硬的论文

可以规划成下一版或扩展版。

## 11.1 理论层

提出一个 local relevance concentration assumption：

\[
\mathbb{E}[LRC_m(q)] \ge \rho
\]

并证明在该假设下，cluster-local candidate search 的 miss risk 可由 \(1-\rho\) 控制；如果再加 dense fallback，系统风险上界进一步降低。

不需要很强的 theorem，但可以有一个 proposition：

> If relevant evidence is \(\rho\)-concentrated in top-m local patches and fallback is triggered when confidence is below threshold, then safe local routing preserves Hit@K up to a bounded miss probability.

这会让 manifold 不是空泛概念。

---

## 11.2 算法层

提出 **Risk-Aware Budgeted Cluster LinUCB**：

\[
a_t=(c_t,b_t,f_t)
\]

reward：

\[
r_t=
\mathbb{1}[\text{hit}]
-\lambda \cdot \text{tokens}
-\mu \cdot \mathbb{1}[\text{fallback}]
\]

risk constraint：

\[
\Pr(\text{miss}\mid q_t,a_t)\le \epsilon
\]

这会把 LinUCB 与 budget 直接耦合，而不是先 LinUCB route、再另一个 policy 做 budget。

---

## 11.3 实验层

加入：

- synthetic manifold benchmark；
- random manifold corruption；
- cross-domain non-LoTTE；
- delayed / noisy feedback；
- reranker / compression compatibility。

这就是比较完整的“manifold + LinUCB”路线。

---

# 12. 最终建议

可以继续把 novelty 往 **manifold + LinUCB** 方向推，但建议这样定：

> **不是“流形理论论文”，也不是“新 LinUCB 理论论文”，而是“manifold-guided trust-weighted Cluster LinUCB evidence controller”。**

后续最关键的是补证据链：

1. **Manifold 是否存在？**  
   用 LRC、NearestClusterHit、ContextRetention、cluster entropy 证明 local relevance concentration。

2. **Manifold 是否有用？**  
   用 random cluster / shuffled cluster / no-geometry ablation 证明 local structure 不是装饰。

3. **LinUCB 是否必要？**  
   用 random、nearest-cluster、epsilon-greedy、vanilla LinUCB、trust-weighted Cluster LinUCB 对比。

4. **LinUCB 是否真的学了？**  
   用 selected-cluster hit、last true reward、proxy regret、learning curve，而不是只看 final Hit@10。

5. **二者是否共同带来收益？**  
   用 geometry-to-safe-compression 分桶证明：locality 高、route confidence 高、drift 低的 query 更适合压缩；locality 低或 drift 高时 dense fallback 必要。

如果做到这一步，novelty 就不再是“budget control 不够新”，而是：

> **在 piecewise local relevance prior 下，把 corpus local regions 变成 cluster arms，并用 trust-weighted LinUCB 学习 route reliability，最终实现 risk-aware evidence selection。**

这条线是可以成立的，而且比单独讲 budget control 更有学术味。
