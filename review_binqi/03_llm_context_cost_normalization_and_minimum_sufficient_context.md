# LLM 上下文成本归一化与最小充分上下文设计

这个设计方向是对的，而且比继续纠结“5% token saving”更有论文价值。你应该把叙事从：

> 我用反馈和路由减少了一点 retrieved context tokens

改成：

> 我优化最终送入 LLM 的最小充分上下文，在保证答案质量不下降的前提下，显著降低 answer-level input cost。

这会更贴近真实 RAG 成本，也更容易说服审稿人。论文现在已经把成本分成 source candidates、dense invocation、final context tokens 三层，并明确说真正和 LLM context cost 对应的是最终送给 generator 的 retrieved context tokens，而不是候选数量。这个基础是有的，可以直接强化为主线。

## 关键概念要稍微改一下

不要说“省 embedding token”。更准确的说法应该是：

> embedding-driven final context optimization

也就是：

> 用 embedding / route / feedback / confidence 信号来决定哪些 evidence snippets 最值得进入最终 LLM context，从而减少 generator input tokens。

embedding 本身只是选择信号，真正省钱的是 **LLM input context tokens**。论文当前已经定义 final context token cost 为最终 context 中各 chunk token 数之和，这个定义可以保留，但需要从 chunk-level 扩展到 sentence/span-level。

---

## 我建议的新核心思路

可以把方法重构成：

## Risk-Controlled Minimum Sufficient Context Selection

中文可以叫：

> 风险可控的最小充分上下文选择

核心目标不是“少拿两个 chunk”，而是：

\[
\min_{C_q} \text{Tokens}(C_q)
\]

subject to:

\[
P(\text{AnswerCorrect} \mid q, C_q) \geq 1 - \epsilon
\]

也就是：  
**对每个问题，选择最少的 context，但保证它仍然足够支持正确回答。**

这比现在的 top-10 → top-8 强很多。当前 conservative policy 只是高置信时把 top-10 压到 k=8，所以最终只能省 4.7–5.3%，这是设计上限导致的，不是实验没跑够。

---

## 推荐的新 pipeline

### 1. 高召回候选池

先保留原来的 dense、BM25、cluster-local route，不要在第一步就过度压缩。

例如：

- dense top-30；
- BM25 top-20；
- cluster-local top-20；
- RRF / weighted fusion 得到候选池。

这一层的目标是 recall，不是省 token。

### 2. 将 chunk 拆成更细粒度 evidence units

不要直接把完整 chunk 放进 context。把候选 chunk 拆成：

- sentence；
- sliding window；
- proposition；
- heading-aware snippet；
- relevant sentence ±1 sentence。

这样 final context 不再是 10 个完整 chunk，而是若干个 query-relevant snippets。

这是收益提升的关键。  
如果一个 chunk 有 200 tokens，但真正相关的是 30–50 tokens 的一句话，保留整块 chunk 天然浪费。

### 3. 用 embedding 优化 evidence packing

对每个 evidence unit 计算：

- query-evidence semantic similarity；
- BM25 lexical anchor score；
- dense/BM25/cluster route agreement；
- LinUCB route confidence；
- redundancy with already selected evidence；
- token length；
- source reliability；
- position / section signal。

然后按 value-per-token 选择：

\[
score(e_i) =
\alpha \cdot rel(q,e_i)
+
\beta \cdot agreement(e_i)
+
\gamma \cdot novelty(e_i)
-
\lambda \cdot tokens(e_i)
\]

其中 novelty 用来避免重复证据，tokens 惩罚用来偏好短而有效的 evidence。

这一步的贡献点可以叫：

> embedding-guided evidence packing

而不是普通 top-k retrieval。

### 4. 加一个 sufficiency predictor

这是最关键的模块。

它不再只问：

> 这个 chunk 是否相关？

而是问：

> 当前已经选出的 context 是否足够回答这个问题？

输入可以是：

- query；
- selected snippets；
- top candidate score distribution；
- dense score gap；
- route agreement；
- selected token budget；
- query difficulty；
- LinUCB confidence；
- semantic drift。

输出：

\[
P(\text{sufficient} \mid q, C_q)
\]

选择过程变成：

1. 加入最高 value-per-token evidence；
2. 预测当前 context 是否 sufficient；
3. sufficient 则停止；
4. 不 sufficient 则继续加入 evidence；
5. 如果一直不 sufficient，触发 dense top-10 / reranker fallback。

这样可以做到：

- easy query：只用 300–600 tokens；
- medium query：用 800–1200 tokens；
- hard query：保留完整 top-10；
- multi-evidence query：禁止过度压缩。

这比固定 k=8 更合理。

---

## 成本归一化怎么写

你这个想法非常适合做 cost-normalized evaluation。

不要只报告 token saving，而是报告：

### 1. 每个 query 的 LLM input cost

\[
Cost_{in}(q)
=
\frac{
T_{system}
+
T_{question}
+
T_{context}(q)
}{10^6}
\cdot p_{in}
\]

其中：

- \(T_{system}\)：固定系统 prompt tokens；
- \(T_{question}\)：问题 tokens；
- \(T_{context}(q)\)：最终送给 LLM 的 evidence context tokens；
- \(p_{in}\)：该 LLM 每百万 input tokens 的价格。

如果 system prompt 和 question 对所有方法相同，也可以重点报告：

\[
ContextCost(q)
=
\frac{T_{context}(q)}{10^6}
\cdot p_{in}
\]

### 2. 如果生成长度也变化，要计入 output cost

\[
Cost(q)
=
\frac{T_{in}(q)}{10^6}
\cdot p_{in}
+
\frac{T_{out}(q)}{10^6}
\cdot p_{out}
\]

不过你的方法主要影响 input context，所以主表可以报告 input cost，附表报告 total cost。

### 3. 最有说服力的指标不是 cost/query，而是 cost/correct answer

建议加：

\[
CostPerCorrect
=
\frac{\sum_q Cost(q)}
{\sum_q \mathbb{1}[\text{answer correct}]}
\]

这个指标非常适合审稿叙事。它能防止一种情况：

> 方法省了 token，但答案错了更多。

如果你的方法能做到：

- answer accuracy 与 dense top-10 不显著下降；
- cost per correct answer 明显降低；

那说服力会比“省 5% context tokens”强很多。

---

## 主实验应该改成什么样

我建议你把主实验从 retrieval-only 改成 answer-level cost-quality frontier。

### Baseline

至少比较：

| 方法 | 作用 |
|---|---|
| Dense top-10 full context | 当前强基线 |
| Dense top-5 / top-8 | 排除“只是少放几个 chunk” |
| Dense adaptive top-k | 排除简单 confidence policy |
| BM25+dense RRF same-budget | 排除普通 hybrid baseline |
| Reranker top-k | 排除强 reranker 方案 |
| LLMLingua / Selective Context 类压缩 | 排除通用 prompt compression baseline |
| IntentWeight 原始 conservative policy | 证明新版比旧版强 |
| 新方法：IntentWeight-MinContext | 主方法 |

论文相关工作里已经提到 Selective Context、LLMLingua、LLMLingua-2、DSLR 等 context compression / sentence-level refinement 方法，因此新版必须和这些方向区分清楚：你的方法不是通用 prompt compression，而是 **retrieval-aware、embedding-guided、risk-controlled evidence selection before generation**。

### 指标

主表建议这样设计：

| 指标 | 目的 |
|---|---|
| Answer Accuracy | 是否真的能答对 |
| Faithfulness | 是否由 context 支撑 |
| Citation Support | 引用证据是否支持答案 |
| Context Tokens | 输入成本 |
| Input Cost / Query | 单问题成本 |
| Cost / Correct Answer | 成本归一化质量 |
| Compression Coverage | 有多少 query 被压缩 |
| Fallback Rate | 有多少 query 仍需完整 context |
| Failure Rate among Compressed Queries | 压缩是否安全 |

尤其要把 **Cost / Correct Answer** 作为核心指标之一。

---

## 论文 claim 可以改成这样

原来的 claim 是：

> conservative context policy reduces final retrieved context tokens by 4.7–5.3% while preserving dense-level Hit@10.

新版可以改成：

> IntentWeight-MinContext uses embedding-guided evidence packing and risk-calibrated sufficiency prediction to select a minimum sufficient context for generation. Under a non-inferiority constraint on answer accuracy and citation faithfulness, it reduces LLM input cost and improves cost per correct answer compared with dense top-10 and adaptive top-k baselines.

中文意思是：

> 在答案正确率和引用忠实性不下降的约束下，显著降低 LLM 输入成本，并改善每个正确答案的成本。

这比单纯说 token saving 更像一篇完整论文。

---

## 这个方向的优点

### 1. 直接对应真实商业成本

审稿人会更容易接受：

> 最终 context 变短 → input tokens 变少 → 按 LLM token 单价计算，成本下降。

论文当前已经意识到 candidate-count reduction 不等于 LLM cost saving，因此你现在把重点放到 final context cost，是顺着论文原本最合理的方向强化。

### 2. 贡献更清晰

原方法容易被质疑：

> dense + BM25 + cluster + LinUCB 是不是已有组件组合？

新版更容易成立为一个独立贡献：

> 如何为每个问题选择最小充分上下文？

这是一个更清楚、更直接、更有必要的问题。

### 3. 收益上限更高

top-10 → top-8 的收益上限太低。  
但 chunk → snippet / sentence / evidence unit 的收益上限明显更高。

你不需要承诺一定能省多少，但实验上有机会从 5% 提升到更有意义的区间，例如 15–30% 甚至更高。前提是 answer quality 不掉。

### 4. 更容易做 cost-quality frontier

你可以画：

- x-axis: LLM input cost；
- y-axis: answer accuracy / faithfulness；
- 每个点是一种方法或 budget；
- dense top-10 是右上角高成本基线；
- 你的方法如果在同等 accuracy 下更靠左，就非常直观。

这种图比现在的 Hit@10-token frontier 更有说服力。

---

## 需要注意的审稿风险

### 风险 1：不能只算 token 价格，不评估答案质量

如果只写：

> context tokens 少了，所以成本低了

审稿人会质疑：

> 答案是不是变差了？证据是不是不完整了？citation 是否还可靠？

所以必须把 answer correctness、faithfulness、citation support 放进主实验。当前论文只有 60-query downstream generation smoke test，这不能替代完整 end-to-end evaluation。新版如果走 cost-normalized answer route，这部分必须扩充。

### 风险 2：Hit@10 不够了

Hit@10 只能说明至少一个 ground-truth chunk 出现了。  
但如果你压缩到 snippets，就更应该评估：

- selected snippet 是否真的包含 answer support；
- answer 是否能被 selected context 支撑；
- 是否丢失多证据信息。

论文当前也承认，context compaction 可能降低 EvidenceRecall@10，完整证据任务需要更保守策略或禁用压缩。这个边界需要继续保留。

### 风险 3：不能用测试集调 compression threshold

如果 sufficiency threshold、budget tier、confidence cutoff 是在 test set 上调出来的，会被审稿人认为数据泄漏。

要严格分成：

- train / calibration set：学习 sufficiency predictor 和阈值；
- validation set：选择 token-quality operating point；
- test set：只评估一次。

### 风险 4：必须和通用 prompt compression 区分

LLMLingua 类方法已经是 context compression。你的差异应该是：

> 我们不是对已经选好的 prompt 做通用压缩，而是在 retrieval stage 利用 embedding、route agreement、domain-local geometry 和 feedback 信号，选择最小充分 evidence set。

否则审稿人会问：为什么不用现有 compression 方法？

---

## 我建议的方法命名

可以把新版叫：

- **IntentWeight-MinContext**
- **IntentWeight-SufficientContext**
- **IntentWeight-Budget**
- **IntentWeight-MSE**，Minimum Sufficient Evidence
- **IntentWeight-CPQ**，Cost-Preserved Quality

我更推荐：

> IntentWeight-MinContext

名字直观，和主 claim 对齐。

---

## 新版 contribution 可以写成 4 点

1. **Minimum sufficient context formulation**  
   将 RAG evidence selection 定义为在答案质量风险约束下最小化 LLM input context tokens 的问题。

2. **Embedding-guided evidence packing**  
   将 retrieved chunks 拆成 sentence/span evidence units，并用 query embedding similarity、route agreement、local geometry、feedback confidence 和 token cost 进行 value-per-token selection。

3. **Risk-calibrated sufficiency controller**  
   学习一个 sufficiency predictor，动态决定每个问题需要多少 context，并在低置信时回退到 dense full context。

4. **Cost-normalized answer evaluation**  
   不仅报告 retrieval Hit@10 和 tokens，还报告 answer accuracy、faithfulness、citation support、input cost/query、cost/correct answer 和 quality-cost frontier。

---

## 最小可行实验版本

如果你不想大改太多，可以先做一个中等规模版本：

### Method

在当前 IntentWeight 输出 top-10 chunks 后：

1. sentence split；
2. 对每个 sentence 计算 query similarity；
3. 用 MMR 去冗余；
4. 选择 top sentences until budget ∈ {512, 768, 1024, 1536}；
5. 用 validation set 找到不显著降低 answer accuracy 的最小 budget；
6. 低置信 query 保留完整 dense top-10 context。

### Evaluation

用至少 300–500 个 queries 做 generation evaluation：

| 方法 | Answer Acc | Faithfulness | Context Tokens | Input Cost | Cost/Correct |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | baseline | baseline | high | high | high |
| Dense top-8 | ? | ? | lower | lower | ? |
| LLMLingua / compression | ? | ? | lower | lower | ? |
| IntentWeight conservative | near baseline | near baseline | -5% | -5% | slight gain |
| IntentWeight-MinContext | target near baseline | target near baseline | much lower | much lower | best |

这就能把论文从“保守省 5%”推进到“answer-level cost optimization”。

---

## 最终建议

这个思路值得采用，而且应该成为论文主线。  
但表述上要非常清楚：

**不是优化 embedding token，而是利用 embedding 信号优化最终 LLM context。**  
**不是证明召回所有 context，而是证明 selected context sufficient for correct answer。**  
**不是只算 token 单价，而是在答案质量不下降的前提下算 cost per correct answer。**

最强的论文主张可以是：

> 在 dense retrieval 作为 recall floor 的基础上，IntentWeight-MinContext 学习为每个 query 构造最小充分 evidence context；在 answer correctness 和 citation faithfulness non-inferior 的条件下，显著降低 LLM input cost 和 cost per correct answer。

这比现在的 4.7–5.3% token saving 更有冲击力，也更符合真实 RAG 系统优化的价值。
