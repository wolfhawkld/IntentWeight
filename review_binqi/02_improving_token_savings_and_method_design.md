# 收益率提升与方法思路建议

我的直接判断：**收益率低的根因不是 seed、统计检验或小调参，而是当前压缩动作本身太保守、粒度太粗、目标函数没有直接优化“最小充分证据集”。** 现在的策略本质上只是在高置信 query 上把 top-10 压到 k=8，中置信仍保留 k=10，低置信继续 dense fallback；因此即使策略完全正确，理论收益上限也不高。论文当前主策略是 conservative confidence_topk，最终 token saving 只有约 4.7–5.3%。

## 一句话建议

**建议把论文核心从“多路检索 + LinUCB 路由”重构为“risk-controlled minimum sufficient evidence selection”，也就是在可控质量风险下，学习每个 query 最少需要多少证据、哪些证据真正必要。**

这会比继续在 route selection 上调参更有潜力。

---

## 1. 为什么现在收益率天然偏低

### 1.1 top-10 到 top-8 的压缩动作太弱

当前策略的主要压缩动作是：

> 高置信时 top-10 → k=8；  
> 中置信仍 k=10；  
> 低置信 dense fallback + k=10。

这意味着即使所有 chunk 等长、所有 query 都进入高置信压缩，理论最大 token saving 也只有约 20%。但实际只有一部分 query 会进入高置信压缩，所以最终只能落在 5% 左右。这个结果不是偶然，而是策略设计决定的。

换句话说，当前方法不是“不够会学”，而是**它被设计成只能省一点**。

### 1.2 你现在优化的是 route confidence，不是 evidence sufficiency

IntentWeight 学的是“哪个 cluster/local route 更可信”，但最终真正影响 token 成本的是：

> 这个 query 到底需要几个 evidence units 才足够回答？

这和 route selection 不是同一个问题。一个 route 选得对，不代表 top-8 就是最小充分证据；一个 route 置信度高，也不代表 top-3 或 top-5 足够。当前方法缺少一个直接判断 **context sufficiency** 的模块。

### 1.3 chunk 级压缩太粗

现在是按 chunk 数压缩，比如 top-10 → top-8。问题是 chunk 内部通常有大量无关句子。即使只保留 8 个 chunk，真正有用的可能只是 2–5 个句子。

所以收益低还有一个结构性原因：

> 你在删 chunk，而不是删无关 token。

如果目标是 final context token saving，仅做 top-k 缩减是不够的。更高收益通常来自 sentence/span-level selection、query-focused extraction、去重和动态预算，而不是固定减少两个 chunk。

### 1.4 dense fallback 保护了质量，也限制了收益

论文目前强调 dense remains recall floor，这是合理的，也降低了质量风险。但副作用是：系统不敢真正跳过大 context，不敢真正 aggressive compaction。

所以现在处在一个保守 operating point：

> 质量安全，但收益不够大；  
> 收益扩大，又容易掉 Hit@10。

这说明需要换优化目标，而不是单纯把阈值调得更激进。

---

## 2. 最值得改的核心思路：从“路由器”改成“最小充分证据控制器”

我建议把论文主问题改成：

> Given a query, select the minimum sufficient evidence set that preserves answer support under a calibrated risk bound.

中文就是：

> 对每个 query，选择最小但足够支撑答案的证据集合，并且用校准风险控制质量损失。

这比“选择哪个 retrieval route”更直接，也更有论文价值。

当前 IntentWeight 可以保留，但它应该从主角变成其中一个信号源：

- dense score；
- BM25 score；
- cluster confidence；
- LinUCB route confidence；
- evidence redundancy；
- chunk length；
- query difficulty；
- answerability / sufficiency score。

最终决策不再是“走哪个 route”，而是：

> 我是否已经收集到足够证据？  
> 还需要继续加入下一个 chunk / sentence / span 吗？  
> 当前 context 再增加 200 tokens 的边际收益是否值得？

这会自然带来更高 token saving。

---

## 3. 具体可行的提升方向

### 方向 A：把 fixed top-k 改成 calibrated adaptive budget

不要再用固定的 top-8 / top-10。建议改成 **动态 token budget**，例如：

| Query 状态 | 当前策略 | 建议策略 |
|---|---|---|
| 极高置信 | top-8 | top-3 / top-5 / 512 tokens |
| 高置信 | top-8 | top-5 / top-6 / 768 tokens |
| 中置信 | top-10 | top-8 / 1024 tokens |
| 低置信 | top-10 fallback | top-10 / top-12 fallback |
| 高 drift / 多证据需求 | top-10 | 禁止压缩或扩展 context |

关键是不要直接预测 k，而是预测 **risk**：

> 压缩到某个 budget 后，Hit@10 / EvidenceRecall / answer faithfulness 下降的概率是多少？

然后在 calibration set 上选择阈值，例如：

> 在验证集上保证 Hit@10 drop ≤ 0.5 pp 的前提下，最大化 token saving。

这样主 claim 可以变成：

> 在 retrieval quality non-inferior 的条件下，显著降低 final context tokens。

这比现在“约 5% token saving”强很多，也更容易被审稿人接受。

### 方向 B：从 chunk-level selection 改成 sentence/span-level evidence selection

这是最可能实质性提高收益的方向。

当前 top-k chunk selection 的问题是：一个 chunk 可能 150–300 tokens，但真正相关的只有一句话。建议 pipeline 改成：

1. 先用 dense/BM25/cluster route 召回 top-N chunks；
2. 对这些 chunks 做 sentence splitting；
3. 对每个 sentence/span 计算 query relevance；
4. 用 MMR 或 value-per-token 选择句子；
5. 必要时保留 parent chunk 的局部窗口，例如 relevant sentence ±1 sentence；
6. 最终送给 generator 的不是完整 chunk，而是 compact evidence snippets。

目标可以从：

> top-10 chunks ≈ 1500 tokens

变成：

> 5–12 evidence snippets ≈ 400–900 tokens

这样 token saving 才有可能从 5% 提到 20%、30% 甚至更高。当然这需要严肃验证 answer faithfulness，不能只看 Hit@10。

一个更强的论文卖点可以是：

> route-level retrieval finds where evidence may be; snippet-level selection decides what evidence is sufficient.

这比单纯多路检索更有新意。

### 方向 C：引入“边际收益 / token”的排序目标

现在的 ranking 主要还是 relevance-first。要省 token，需要显式优化：

> evidence utility per token

可以把最终选择改成类似 knapsack / submodular selection：

\[
\max_{S} \sum_{e_i \in S} u(q, e_i) - \lambda \cdot \text{tokens}(e_i) - \mu \cdot \text{redundancy}(e_i, S)
\]

其中：

- \(u(q,e_i)\)：query-evidence relevance；
- \(\text{tokens}(e_i)\)：证据长度；
- \(\text{redundancy}\)：和已选证据的重复度；
- \(\lambda\)：token cost penalty；
- \(\mu\)：冗余惩罚。

这样系统会偏好：

- 短但高价值的 evidence；
- 与已有证据互补的 evidence；
- 避免多个 chunk 讲同一件事；
- 避免 BM25 拉进来很长但边际价值低的段落。

这比“高置信 top-8”更直接面向收益。

### 方向 D：把 LinUCB 的 action 从“cluster arm”改成“budget action”

现在 LinUCB 主要选 cluster-local route。可以考虑更 radical 的改法：

> arm 不只是 cluster，而是 retrieval-budget policy。

例如每个 action 是：

| Action | 含义 |
|---|---|
| A1 | dense top-10 full fallback |
| A2 | dense top-5 + BM25 top-3 |
| A3 | cluster top-5 only |
| A4 | BM25 top-5 for lexical query |
| A5 | dense top-3 + snippet extraction |
| A6 | reranker top-5 |
| A7 | high-confidence 512-token evidence budget |
| A8 | multi-evidence 1536-token budget |

这样 bandit 学到的是：

> 对这种 query，哪种 budgeted evidence strategy 最划算？

而不是只学：

> 哪个 cluster 比较可能包含答案？

这会让方法目标和收益目标更一致。也更容易讲成一个真正的 **budgeted contextual bandit for RAG evidence selection**。

### 方向 E：加入 sufficiency predictor，而不是只用 retrieval confidence

现在的 confidence 主要来自 route confidence、LinUCB confidence、semantic drift 等。它们只能间接说明 retrieval 是否可靠。

更关键的是直接预测：

> 当前已选 context 是否足够回答问题？

可以训练一个轻量 sufficiency model：

输入：

- query；
- selected evidence；
- top candidate scores；
- dense/BM25/cluster agreement；
- top1-top2 score gap；
- evidence diversity；
- selected token count；
- query complexity features。

输出：

\[
P(\text{sufficient} \mid q, C)
\]

然后 sequentially add evidence：

1. 从最强 evidence 开始；
2. 每加入一个 snippet/chunk，预测 sufficiency；
3. 如果 sufficiency 超过阈值，就停止；
4. 如果不够，再加入下一个 evidence；
5. 如果低置信或冲突，触发 dense fallback / reranker。

这个思路比固定 k 更合理，因为不同 query 的证据需求差异很大。

---

## 4. 我最推荐的新版系统设计

可以把方法重构成四层：

### Layer 1：High-recall candidate pool

保留 dense、BM25、cluster-local route。这里目标不是省 token，而是保证候选覆盖。

输出 top-30 或 top-50 candidates。

### Layer 2：Evidence unit decomposition

把 chunk 拆成更小 evidence units：

- sentence；
- proposition；
- passage window；
- table row；
- heading-aware section；
- entity-centered snippet。

这样 final context 可以更细粒度控制。

### Layer 3：Risk-controlled evidence selector

对每个 evidence unit 估计：

- relevance；
- novelty；
- supportiveness；
- token cost；
- route agreement；
- uncertainty。

然后按 value/token 选择，直到 sufficiency 达标。

### Layer 4：Fallback and calibration

用验证集校准：

- 哪些 query 可以压到 512 tokens；
- 哪些 query 需要 1024 tokens；
- 哪些 query 不能压缩；
- 哪些 query 需要 dense top-10 / top-12 fallback。

最终报告完整 frontier：

| Mode | Token saving | Hit@10 drop | EvidenceRecall drop | Answer quality |
|---|---:|---:|---:|---:|
| Conservative | 5% | ≈0 | 小 | 稳 |
| Moderate | 15% | ≤0.5 pp | 中 | 稳 |
| Aggressive | 30% | ≤1–2 pp | 较大 | 需看任务 |
| Extreme | 50%+ | 明显下降 | 大 | 不推荐 |

这样读者会觉得你不是在硬凑 5%，而是在系统性研究 quality-cost frontier。

---

## 5. 可以直接写进论文的新贡献点

### 新贡献 1：Minimum Sufficient Evidence Selection

提出一个新的 evidence selection objective：

> 在保证答案支持风险不超过阈值的情况下，最小化 final context tokens。

这比“adaptive route control”更强。

### 新贡献 2：Risk-calibrated adaptive budget policy

不是手工 top-8，而是通过 calibration set 学习不同 query 的预算。

核心 claim：

> IntentWeight-Budget learns when 512/768/1024/1536-token context is sufficient.

### 新贡献 3：Route agreement as sufficiency signal

dense、BM25、cluster-local 三者不是单纯 fusion，而是提供 agreement / disagreement signal：

- 三路都指向同一 evidence → 可以压缩；
- dense 与 BM25 冲突 → 保守；
- cluster route 命中高但 dense 分散 → 局部压缩；
- BM25 强 exact anchor → 少量 lexical evidence 可能足够。

这个比“多路检索”更有解释性。

### 新贡献 4：Value-per-token evidence packing

最终 context 构造不是 top-k，而是 evidence packing：

\[
\text{score}(e) =
\alpha \cdot \text{relevance}
+
\beta \cdot \text{route agreement}
+
\gamma \cdot \text{novelty}
-
\lambda \cdot \text{tokens}
\]

这直接服务收益率。

---

## 6. 实验上应该怎么证明收益变高是可信的

不要只报告平均 token saving。建议主表改成：

| 指标 | 为什么重要 |
|---|---|
| Token saving | 直接收益 |
| Hit@10 | 基础 retrieval quality |
| EvidenceRecall@10 | 防止多证据损失被隐藏 |
| Answer correctness | 证明不是 retrieval-only |
| Faithfulness / citation support | 证明压缩后没有幻觉 |
| Compression coverage | 有多少 query 被压缩 |
| Failure rate among compressed queries | 压缩是否安全 |
| Dense fallback rate | 是否仍然依赖 dense |
| Average selected evidence units | 证明不是单纯 top-k trick |
| Latency / cost per query | 证明系统收益真实 |

特别要报告这几个分桶：

| Query 类型 | 预期策略 |
|---|---|
| entity / exact term query | BM25 + small snippet，强压缩 |
| high dense confidence query | dense top-3/top-5，强压缩 |
| route agreement high query | 低预算 |
| multi-evidence query | 禁止 aggressive compression |
| low confidence / high drift query | dense fallback |
| long query / ambiguous query | 保守预算 |

如果结果显示 easy query 可以省 30–50%，hard query 保持 full context，整体省 15–25%，那会比现在 5% 强很多。

---

## 7. 不建议继续投入的方向

### 不建议只调 LinUCB 参数

调 \(\alpha\)、trust weight、cluster 数、noise 参数可能能带来小提升，但很难从 5% 变成 20%。因为瓶颈不是 bandit 没学好，而是最终压缩动作太弱。

### 不建议继续强调 manifold

“piecewise relevance-manifold”目前更像动机，不是收益来源。继续强化这个概念，可能反而让审稿人质疑 novelty。真正该强调的是：

> local structure helps estimate evidence sufficiency and safe budget reduction.

### 不建议把 aggressive top-k 当主结果

直接把 top-10 压到 top-5，token saving 会好看，但 Hit@10 / EvidenceRecall / answer faithfulness 很可能掉。

更好的做法是 **risk-controlled aggressive compression**：

> 只对可证明安全的 query aggressive；  
> 对不安全 query 保守。

### 不建议只宣传 production 可能更好

生产中 repeated query patterns、user feedback、richer confidence tiers 可能增加可压缩 query 比例，但这仍然只是 hypothesis，不是当前实验已经证明的结论。如果要这么写，必须配生产模拟或 session-level repeated query 实验。

---

## 8. 我建议的最强改稿路线

### 路线一：小改，目标从 5% 提到 10–15%

适合时间有限。

做法：

1. 加 dense adaptive top-k baseline；
2. 把 fixed k=8 改成 k ∈ {5, 6, 8, 10, 12}；
3. 用 validation set 校准阈值；
4. 加 length-aware reranking；
5. 加 dedup / MMR；
6. 主 claim 改成 non-inferior Hit@10 + higher token saving。

这条路线比较稳，但 novelty 仍然有限。

### 路线二：中改，目标 15–30%

我最推荐。

做法：

1. 保留多路 retrieval 作为 candidate generator；
2. 增加 sentence/span-level evidence selection；
3. 加 sufficiency predictor；
4. 用 risk-controlled stopping 决定 context budget；
5. 报告 full quality-cost frontier；
6. 做 end-to-end answer faithfulness 评估。

这条路线能把论文从“RAG 路由组合”提升为“最小充分证据选择框架”。

### 路线三：大改，目标系统级收益

适合做系统论文。

做法：

1. 不只优化 final tokens，还优化 dense invocation；
2. 对高置信 query 跳过 global dense；
3. 使用 BM25-first / cluster-first / ANN-local-first cascade；
4. 只在不确定时调用 dense full search 或 reranker；
5. 报告 latency、throughput、GPU/CPU cost、LLM cost。

这条路线的优势是实际系统价值强，但实验工程量最大。

---

## 9. 最推荐的主线表述

我建议把论文主线改成这样：

> Dense retrieval is a strong recall floor, but fixed top-k wastes context because many queries require far less than ten chunks. IntentWeight-Budget treats evidence selection as a risk-controlled minimum-sufficient-context problem. It uses route agreement, local geometry, feedback confidence, and evidence-level value-per-token scoring to adaptively stop evidence accumulation once answer support is likely sufficient.

中文核心就是：

> 不是“我有一个更聪明的检索路由器”，而是“我能判断一个 query 最少需要多少证据，并且在风险可控的前提下停止加入 context”。

这会显著改善论文的贡献感。

---

## 10. 最后给一个明确建议

我会优先做这三个改动：

| 优先级 | 改动 | 原因 |
|---:|---|---|
| P0 | fixed top-k → calibrated adaptive token budget | 直接突破 5% 收益上限 |
| P0 | chunk-level → sentence/span-level evidence selection | 最大概率实质提高 token saving |
| P0 | route confidence → sufficiency prediction | 让方法直接优化“够不够回答”，而不是间接优化 route |

当前 5% saving 作为 conservative operating point 可以保留，但不应该作为论文最强结果。更好的结构是：

> conservative mode 证明安全性；  
> adaptive budget mode 展示主要收益；  
> aggressive mode 展示 frontier 上限；  
> failure buckets 说明边界。

这样论文会从“收益太低的 RAG controller”变成“有可控风险、有实际收益、有清晰 frontier 的 evidence budget framework”。
