# IntentWeight 论文优化指导文档

> 目的：把当前初稿从“有潜力的系统研究论文”推进到“更有说服力的投稿版本”。
>
> 核心原则：不要把论文改成另一个方向。应当保留 **Hit@10 sufficient evidence 目标** 和 **piecewise relevance-manifold 研究来源**，同时补强 reviewer 最可能质疑的三个环节：**算法必要性、统计可信度、反馈真实性**。

---

## 0. 一句话定位

当前论文的价值不在于提出一个“碾压 dense retrieval 的新 retriever”，而在于提出了一个面向垂类 RAG 的 **质量—成本—反馈控制框架**：

> 垂类知识数据可能存在 piecewise relevance-manifold structure；dense retrieval 是强 recall floor，但固定 dense route 不能显式处理 lexical anchors、cluster-level routing、user-specific relevance 和 final context budget。因此，IntentWeight 将 evidence selection 建模为一个 adaptive route-control problem，在 dense/BM25/cluster-local 多路检索之上，用 LinUCB + trust-weighted feedback 学习 route preference，并用 confidence-based policy 控制 final context budget。

推荐将论文主叙事收敛为：

> **A feedback-ready adaptive evidence-selection controller for sufficient grounding evidence under a reduced final context budget.**

---

## 1. 当前论文的真实状态判断

### 1.1 可以守住的价值

当前稿子已经具备以下优点：

1. **问题是真实的**：垂类 RAG 中，检索质量、route 选择、dense fallback、final context budget 不是同一个问题，当前很多工作会把它们混在一起。
2. **系统闭环是完整的**：dense/BM25/cluster-local retrieval → LinUCB route policy → trust-weighted feedback → confidence-based context compaction → retrieval/token evaluation。
3. **claim 边界较克制**：稿子明确强调 IntentWeight 不是 dense replacement，而是 controller；dense remains recall floor。
4. **成本定义较专业**：区分 source candidate cost、dense invocation rate、final context tokens，并把主效率 claim 放在 final context tokens 上。
5. **manifold 不是空泛修辞**：它是研究假设来源，后续通过 PCA、NearestClusterHit、ContextRetention 等 diagnostics 做了 operational validation。

### 1.2 目前最弱的地方

目前主要不足不是“方向不成立”，而是证据厚度还不够：

1. **强工程组合多于强算法创新**：组件组合合理，但 reviewer 会问为什么 LinUCB controller 必要，而不是简单 heuristic gate 或 adaptive top-k。
2. **统计显著性不足**：多 seed 数量少，部分 confidence interval overlap zero，不能过度声称 superiority。
3. **5% token saving 偏小**：作为 conservative safe point 是合理的，但需要成本模型或更清晰的 frontier 解释。
4. **feedback 仍是 simulated**：如果标题和方法强调 feedback-guided，就必须说明 controlled feedback simulation 的边界，或增强 bias/noise/delay 模拟。
5. **主正向证据集中在 LoTTE technology/search**：external validity 仍有限。

### 1.3 目标投稿判断

- **Workshop / Industry track**：当前版本经过写作清理和少量补实验，有机会达到 Weak Accept / Accept。
- **ACL/EMNLP main**：当前更像 Borderline，需要补 baseline、统计测试和 feedback simulation 才更稳。

---

## 2. 必须守住的两个核心立场

## 2.1 Hit@10 可以继续作为 headline，但任务边界要写硬

当前论文不是 exhaustive evidence retrieval，而是：

> 在较小 final context budget 下，尽量保留至少一个可用回答证据。

因此 Hit@10 是合理主指标。不要轻易让步成完整证据收集任务，否则论文目标会变散。

### 推荐任务命名

可在 Introduction / Metrics 中明确提出：

- **usable-evidence preservation under reduced context budget**
- **sufficient-evidence selection for RAG grounding**
- **sufficient grounding evidence rather than exhaustive evidence collection**

### 推荐正文表述

> We use query-level Hit@10 as the primary retrieval headline because the evaluated setting targets sufficient grounding evidence for RAG-style QA: at least one relevant chunk is often enough to support a grounded answer. This objective differs from exhaustive evidence collection. Therefore, EvidenceRecall@10 is reported as a secondary trade-off metric rather than optimized as the main objective.

### 注意

EvidenceRecall@10 仍建议报告，但它应该被定义为 **trade-off metric**，而不是主优化目标。

对于 legal review、medical synthesis、compliance audit 这类 complete-evidence tasks，需要明确说明应使用更保守 policy 或关闭 compaction。

---

## 2.2 Manifold 不能完全弱化，但要明确 epistemic status

manifold 是本文研究来源，不应该完全改成普通 local cluster structure。否则论文会失去理论动机，变成普通 hybrid retrieval controller。

但要避免让 reviewer 以为你在证明严格数学流形。

### 推荐定位

将 manifold 定义为：

> **manifold-inspired inductive bias**

或者：

> **piecewise relevance-manifold assumption as an operational routing hypothesis**

### 推荐正文表述

> The piecewise relevance-manifold assumption is not used as a theorem-level claim. Instead, it serves as an operational inductive bias: vertical-domain relevance may concentrate in local semantic, lexical, workflow, and intent-induced regions. IntentWeight tests whether this local structure provides useful routing signal while keeping dense retrieval as a recall floor.

### 需要强调的四层逻辑

1. **观察来源**：垂类数据中的术语、实体、workflow、用户 intent 使 relevance 不均匀分布。
2. **方法假设**：如果 relevance 具有 piecewise local geometry，那么 cluster-local route 有意义。
3. **安全机制**：geometry alone 不安全，所以保留 dense fallback 和 BM25 lexical anchor。
4. **诊断验证**：NearestClusterHit、PCAvar、PCAdim90、ContextRetention 支持 local routing signal，但不证明数学流形存在。

---

## 3. 优化后的主线叙事

建议将论文主线改写为下面这个闭环：

```text
Vertical-domain knowledge data may exhibit piecewise relevance-manifold structure.
        ↓
Dense retrieval is a strong recall floor, but fixed dense-only routing cannot express lexical anchors, local route confidence, or user-specific relevance.
        ↓
Geometry alone is useful but unsafe; early cluster pruning may lose evidence.
        ↓
Therefore, evidence selection should be treated as adaptive route control rather than fixed retriever selection.
        ↓
IntentWeight combines dense, BM25, and cluster-local routes, learns route preference with trust-weighted LinUCB, and applies confidence-based final context compaction.
        ↓
The conservative policy preserves sufficient grounding evidence while reducing final retrieved context tokens.
```

一句话版本：

> IntentWeight studies whether manifold-inspired local relevance structure, feedback-based route learning, and conservative confidence control can reduce final RAG context budget while preserving sufficient grounding evidence.

---

## 4. 最优先补强：证明 controller 是必要的

这是主会 reviewer 最可能攻击的点：

> 为什么不是简单 top-k 压缩？为什么不是 heuristic confidence gate？为什么需要 LinUCB？

### 4.1 必补 baseline

建议至少补以下 baseline：

| Baseline | 目的 | Reviewer 质疑点 |
|---|---|---|
| Dense@8 | 检查简单少取 2 个 chunk 是否也能省 token | 如果 Dense@8 接近 IntentWeight，controller 价值下降 |
| Dense adaptive 8/10 | 用 dense score margin 决定 k=8 或 k=10 | 检查 confidence top-k 是否不需要多路 route |
| BM25+dense RRF adaptive top-k | 检查静态 hybrid + top-k policy 是否足够 | 如果接近，LinUCB 必要性不足 |
| Score-margin heuristic gate | 用 top1-top2 / top1-topK score gap 做 gate | 检查是否简单 heuristic 就够 |
| Static nearest-cluster routing + fallback | 检查 bandit learning 是否真的贡献 | 如果接近，feedback learning 贡献不足 |
| Non-bandit learned gate / logistic gate | 检查 LinUCB 是否必要 | 如果简单 supervised gate 接近，需解释 online adaptation 优势 |
| Random cluster / shuffled cluster control | 检查 geometry signal 是否真实 | 支持 manifold-inspired assumption |

### 4.2 希望得到的结果模式

理想结果不是所有指标都碾压，而是展示：

1. Dense@8 省 token 但 Hit@10 明显下降；
2. Dense adaptive top-k 比 Dense@8 稳，但不如 IntentWeight；
3. Static cluster 有 routing signal，但不稳定；
4. LinUCB + trust feedback 在 selected-cluster hit、last true reward、fallback decision 上更优；
5. IntentWeight 是 quality-cost frontier 上更安全的 operating point。

### 4.3 推荐写法

> The key comparison is not whether IntentWeight beats dense-only retrieval as a retriever, but whether it provides a safer quality-cost operating point than naive context reduction and static confidence heuristics.

---

## 5. 统计显著性优化

当前 seed 数偏少，最好不要把 mean improvement 写成强 dominance。

### 5.1 建议补充的统计测试

| 测试 | 用途 |
|---|---|
| Paired bootstrap over queries | 给 Hit@10 delta、MRR delta、token saving CI |
| McNemar test | 比较 dense vs IntentWeight 在 Hit@10 上的 paired difference |
| Paired randomization test | 更稳健地比较 query-level metric |
| Per-query delta histogram | 展示哪些 query 改善/受损 |
| Query difficulty buckets | 看短 query、长 query、lexical-heavy query、semantic query 的差异 |

### 5.2 推荐报告方式

不要写：

> IntentWeight significantly outperforms dense retrieval.

更稳的写法：

> IntentWeight preserves dense-level Hit@10 under a conservative context policy, with mean above-dense results at larger LoTTE scales. Statistical evidence for superiority is limited, so we frame the result as quality-preserving context control rather than universal retrieval improvement.

### 5.3 主表建议

主表建议从：

- Dense Hit@10
- IntentWeight Hit@10
- Token saving

扩展为：

- Hit@10
- EvidenceRecall@10
- MRR@10
- nDCG@10
- Tokens@10
- Token ratio
- Paired CI / p-value

这样不会显得选择性展示。

---

## 6. 5% saving 的处理方式

5% 不是不能用，但不能把它包装成巨大节省。它应该被定位为：

> conservative safe point on the token-quality frontier

### 6.1 推荐解释

1. 当前 policy 故意保守，只在 high-confidence case 压缩到 k=8；
2. mid-confidence case 保留 k=10；
3. low-confidence case 保留 dense fallback；
4. 更激进策略可以省更多，但会产生 visible Hit@10 loss；
5. 本文选择质量优先的 conservative operating point。

### 6.2 建议补充成本模型

至少给一个简单公式：

```text
Total Cost = Retrieval Compute Cost + Reranking Cost + LLM Input Token Cost + LLM Output Token Cost
```

然后说明本文主 claim 是：

```text
LLM Input Token Cost reduction through final retrieved context compaction
```

不是：

```text
global dense retrieval compute reduction
```

除非实验真的跳过 global dense route。

### 6.3 建议补充指标

- high-confidence compression rate；
- fallback rate；
- dense invocation rate；
- median token saving；
- p90/p95 token saving；
- retrieval latency；
- end-to-end generation latency。

---

## 7. Feedback simulation 优化

当前 feedback 是 controlled simulated feedback，这是合理第一步，但需要增强真实性。

### 7.1 必须守住的表述

不要写：

> IntentWeight learns from user feedback.

更稳：

> IntentWeight is evaluated under controlled simulated feedback derived from ground-truth labels. This validates the route-learning mechanism under feedback-like signals, but does not claim production human-feedback deployment.

### 7.2 建议新增 feedback 模拟

| 模拟类型 | 目的 |
|---|---|
| Position bias | 模拟用户更容易点击/认可排名靠前结果 |
| Click noise | 模拟误点、误赞、误反馈 |
| Trust drift | 用户可靠性随时间变化 |
| Delayed feedback | feedback 在若干 query 后才到达 |
| Sparse feedback | 只有部分 query 有 feedback |
| Adversarial feedback | 低可信用户故意给错反馈 |
| User group heterogeneity | 不同用户群偏好不同 route |
| Non-stationary intent | query distribution 随时间变化 |

### 7.3 建议主实验结构

可以设计三层 feedback 实验：

1. **Clean oracle feedback**：上界；
2. **Noisy trust-weighted feedback**：主机制验证；
3. **Biased/delayed/sparse feedback**：真实部署压力测试。

### 7.4 推荐结论写法

> Trust weighting improves route-policy metrics under controlled noisy feedback, especially selected-cluster hit and last true reward. Under more realistic biased and sparse feedback, the benefit should be evaluated as robustness of policy adaptation rather than final Hit@10 superiority, because dense/BM25 fallback can saturate final retrieval quality.

---

## 8. Manifold 相关实验补强

为了让 manifold-inspired assumption 更有说服力，建议补一些 geometry control。

### 8.1 建议补充实验

| 实验 | 目的 |
|---|---|
| Random cluster control | 证明不是任意分组都有效 |
| Shuffled embedding control | 证明 embedding geometry 有贡献 |
| K sensitivity | 检查 KMeans cluster 数变化是否稳定 |
| Cluster purity proxy | 看 GT chunk 是否集中于少数 clusters |
| NearestClusterHit@1/3/5 | 看 local routing 的可用范围 |
| ContextRetention vs scale | 展示 geometry alone 随规模下降，因此需要 dense fallback |
| Query-to-cluster entropy | 看 query 的 route uncertainty |

### 8.2 推荐写法

> These diagnostics do not prove a mathematical manifold theorem. They test whether the manifold-inspired assumption provides operational routing signal. The result supports using local geometry as one controller signal, not as a replacement for dense retrieval.

### 8.3 不建议做的事

不要把标题和摘要写得像在证明：

> vertical-domain data lies on a relevance manifold

更稳的表达是：

> under a piecewise relevance-manifold assumption

或者：

> motivated by piecewise relevance-manifold structure

---

## 9. Downstream generation smoke test 优化

当前 60-query smoke test 可以保留，但不能作为强 claim。

### 9.1 建议扩展

最低增强版：

- 200-300 queries；
- 一个 generator，一个独立 judge；
- answer relevance；
- citation support；
- hallucination / unsupported claim rate；
- 人工抽样 30-50 条。

### 9.2 推荐写法

> The generation experiment is a sanity check for answer-quality preservation under conservative context compaction, not a claim that IntentWeight improves generated answer quality.

### 9.3 理想结论

如果结果显示 answer quality 基本不降，那么可以支撑 Hit@10 sufficient evidence 的任务设定：

> preserving at least one usable evidence chunk is often sufficient for RAG-style QA grounding under the evaluated setting.

---

## 10. 写作结构建议

## 10.1 Introduction 建议结构

1. RAG evidence selection 的核心矛盾：quality vs latency/noise/context cost。
2. 垂类数据的特殊性：terminology、workflow、local semantic neighborhoods、user intent。
3. Piecewise relevance-manifold assumption：relevance is locally structured but not globally uniform。
4. Dense retrieval 是强 baseline，但 fixed dense route 不能处理所有 route-control decision。
5. Geometry alone 不安全，需要 dense fallback。
6. IntentWeight：feedback-ready adaptive route controller。
7. Main claim：conservative final context compaction preserves sufficient grounding evidence while reducing final context tokens。
8. 明确边界：not dense replacement, not theorem-level manifold proof, not real feedback deployment。

## 10.2 Method 建议强调

- route-control problem，而不是 retriever replacement；
- LinUCB 负责学习 route preference；
- trust weighting 负责 feedback reliability；
- cluster-only reward 负责避免 dense/BM25 rescue 过度归功；
- confidence-based final policy 才是 token saving 来源。

## 10.3 Results 建议结构

1. Main token-quality frontier；
2. Naive top-k / heuristic baseline comparison；
3. Component ablation；
4. Statistical stability；
5. Feedback simulation robustness；
6. Geometry diagnostics；
7. Generation smoke。

## 10.4 Discussion 建议结构

1. Supported claim；
2. Why controller rather than fixed retriever；
3. Why Hit@10 is the right headline for sufficient evidence；
4. Why manifold is useful but not sufficient；
5. Why feedback result is mechanism validation, not production proof；
6. Production interpretation。

---

## 11. 推荐修改标题和摘要方向

### 11.1 当前标题风险

当前标题里的：

> Feedback-Guided Evidence Selection under a Piecewise Relevance-Manifold Assumption

优点是有辨识度；风险是 reviewer 会对 feedback 和 manifold 期待很高。

### 11.2 可选标题

偏保守：

> IntentWeight: Feedback-Simulated Evidence Selection under a Piecewise Relevance-Manifold Assumption

偏系统：

> IntentWeight: Adaptive Evidence Route Control for Retrieval-Augmented QA

偏理论动机 + 系统：

> IntentWeight: Manifold-Inspired Adaptive Evidence Selection for Retrieval-Augmented QA

偏投稿稳健：

> IntentWeight: Conservative Context Control with Feedback-Ready Evidence Routing for Retrieval-Augmented QA

### 11.3 推荐摘要核心句

> IntentWeight is not a replacement for dense retrieval. It is a feedback-ready route-control framework that uses dense retrieval as a recall floor, exploits manifold-inspired local relevance structure as a routing signal, and applies conservative confidence-based context compaction to reduce final retrieved context tokens while preserving sufficient grounding evidence.

---

## 12. 优先级路线图

## P0：投稿前必须做

1. 增加 Dense@8、Dense adaptive top-k、score-margin gate、static cluster gate baseline。
2. 主表增加 EvidenceRecall/MRR/nDCG，不只 Hit@10 + tokens。
3. 做 paired bootstrap 或 McNemar test。
4. 清理正文中“像内部备注”的句子。
5. 把 Hit@10 sufficient evidence 的任务边界提前到 Metrics / Main Results。
6. 把 manifold 的 epistemic status 提前到 Introduction / Method。

## P1：强烈建议做

1. feedback 增加 bias、sparse、delayed、adversarial simulation。
2. 增加 random cluster / shuffled embedding / K sensitivity。
3. 补成本模型或 latency 分析。
4. 扩大 generation smoke test。

## P2：有时间再做

1. 更多 LoTTE domains；
2. stronger encoder / reranker / late-interaction retrieval；
3. real user feedback pilot；
4. graph/HDBSCAN dynamic clustering；
5. production-like online A/B simulation。

---

## 13. Reviewer 可能问题与推荐回答

### Q1：为什么主指标是 Hit@10，而不是 EvidenceRecall@10？

推荐回答：

> The evaluated task targets sufficient grounding evidence for RAG-style QA, where retrieving at least one relevant chunk is often enough to support a grounded answer. We therefore use Hit@10 as the primary headline and report EvidenceRecall@10 separately as a trade-off metric. For complete-evidence tasks such as legal or medical review, compaction should be disabled or made more conservative.

### Q2：5% token saving 是否太小？

推荐回答：

> The conservative policy is intentionally quality-first. It compresses only high-confidence cases and keeps dense fallback under uncertainty. More aggressive policies save more tokens but introduce visible Hit@10 loss. We present this as a safe operating point on the token-quality frontier, not as the maximum achievable saving.

### Q3：这是不是简单工程组合？

推荐回答：

> The contribution is not any single component. It is the route-control formulation and the interaction among cluster-only credit assignment, trust-weighted adaptation, dense fallback, and final context compaction. Additional naive top-k and heuristic-gating baselines are used to test whether the controller provides a safer quality-cost frontier than simple context reduction.

### Q4：feedback 是 simulated，为什么叫 feedback-guided？

推荐回答：

> The current experiments validate the mechanism under controlled feedback-like signals. We do not claim production human-feedback deployment. The paper frames this as feedback-ready or simulated-feedback route adaptation, with real delayed and biased feedback left for future production evaluation.

### Q5：manifold 是否被证明？

推荐回答：

> No theorem-level manifold proof is claimed. The piecewise relevance-manifold assumption is an operational inductive bias motivated by vertical-domain local relevance structure. Geometry diagnostics test whether this assumption provides usable routing signal; dense fallback remains necessary because geometry alone is insufficient.

---

## 14. 最终建议

不要因为“不是强算法突破”而否定这篇论文。它真正的价值是：

> 把垂类 RAG 的 evidence selection 从固定检索器选择，推进为一个包含 local geometry、feedback reliability、dense fallback 和 final context budget 的 adaptive control problem。

接下来优化的重点不是推翻原框架，而是补齐证据链：

```text
simple baseline 打不赢 → controller 必要
paired statistics 更稳 → 结果可信
feedback bias simulation 更真实 → feedback claim 更可信
geometry control 更强 → manifold-inspired assumption 更可信
Hit@10 边界写清 → reviewer 不会按 complete retrieval 错误审稿
```

如果这些补上，这篇论文的定位会从：

> promising engineering system idea

提升到：

> convincing system research paper with a clear theoretical motivation and a bounded empirical claim
