# IntentWeight 同行评审报告

> 2026-06-24 · Metis (Hermes Agent) · 基于 full_draft + 实验代码 + 多轮审稿历史的综合评审

---

## 一、项目全览

```
项目:     IntentWeight — Feedback-Adaptive Evidence Selection
目标期刊: IP&M (Information Processing & Management), SCI Q2
备选:     ESWA (Expert Systems with Applications)
代码:     intent_weight/ 库 + paper/experiments/scripts/ 50+ 实验脚本
论文:     full_draft/ 10 节完整草稿 + LaTeX 版 (ACL 格式，待转 Elsevier)
实验:     Task 21-56，LoTTE technology/science，100k-638k 规模
提交历史: 22 commits since Jun 1，最新 Task56 claim-evidence alignment
```

---

## 二、论文核心主张

> IntentWeight 是一个**反馈引导的自适应证据选择控制器**，在 dense 检索的召回地板上，用 LinUCB 学习 cluster-local 路由的价值，通过置信度驱动的最终上下文压缩，在 LoTTE 100k-638k 上实现 **6-18% 最终上下文 token 节省**，同时避免 dense-only 自适应截断的 Hit@10 损失。**不是 dense 检索的替代品，而是路由-预算控制器。**

---

## 三、优点

### 1. 问题定义精准（最大亮点）

论文明确区分了三层成本——(a) 候选检索量、(b) dense 调用率、(c) 最终送入 LLM 的上下文 token 数。Task28 发现"减少候选量不等于减少最终 token"这个反直觉结论，直接 motivates 了最终上下文压缩机制。这个三层分离在 RAG 文献中很少见，是有价值的问题重构。

### 2. Claim 极其克制和诚实

经过多轮审稿修订，论文从最初的"manifold theorem"退到了"manifold-inspired diagnostic assumption"，从"beat dense"退到了"complementary controller with dense as recall floor"。10 条 explicit limitations 写得比很多审稿人能挑出来的还全面。这种学术诚实度在工程化论文中难得。

### 3. 实验设计严谨

- Calibration/test split (30/70) 避免 model selection bias
- Query-level paired bootstrap CI + McNemar test + 非劣效性 margin
- Prequential protocol 无数据泄漏
- 多 backbone 验证 (MiniLM / BGE-base / E5-base)
- Dense adaptive truncation 作为"更激进但丢质量"的对照

### 4. Strong baselines 覆盖充分

经过 Task46-53 的补课，已覆盖：SentMMR 压缩、cross-encoder reranker、strong embedding (BGE/E5)、compressor-normalized 对比。特别是 Task24 的 static ensemble ablation 揭示了一个关键发现：**多路由融合是质量主要贡献者，而非 LinUCB 学习**——这种"拆穿自己"的实验体现了学术诚信。

### 5. 工程质量高

- 代码双语注释完整
- experiment_guardrails 做 GT coverage 断言
- 原子持久化、防反馈投毒设计
- 可复现参数全部列出

---

## 四、弱点

### A. 新颖性（最大风险 — Major）

三个竞争性 novelty center，单独看都不够：

| Novelty 角度 | 问题 |
|---|---|
| Manifold theory | 仅诊断性（PCA + cluster hit），无拓扑/曲率/测地线；"不可调和悖论"：如果流形曲率高，PCA+KMeans 无法利用；如果低，流形概念多余 |
| LinUCB 算法 | 标准 LinUCB + 工程适配（alpha decay, trust weighting），无新 regret bound |
| Budget control | 本质是 adaptive top-k / confidence thresholding |

**审稿人视角**：这是一个"已有组件的工程组合"（dense + BM25 + KMeans + LinUCB + trust weighting + budget control），而非新算法。论文目前的 composite novelty 定位（"manifold-guided, trust-weighted cluster-LinUCB controller for budgeted evidence selection"）是合理的，但需要更强的 ablation 来证明**每个组件都是必要的**。

**缺失的关键实验**：
- ❌ Random-cluster / shuffled-cluster 对照（证明 cluster 结构真的重要，而非随机分桶就行）
- ❌ No-geometry / no-LinUCB ablation（证明 LinUCB 比 random routing 好）
- ❌ Geometry-to-gain 相关性分析（manifold diagnostic 能否预测 token saving gain）

### B. 统计显著性（Major）

- 3 seeds (2 degrees of freedom) — 方差估计不可靠
- 400k CI [0.11%, 10.53%] — 几乎触零，calibration eligible=False
- 638k Hit delta CI [-0.36, +4.07] — 包含零
- 596 queries，1pp 差异 = ~6 queries，统计功效弱

虽然加了 query-level paired tests 缓解，但审稿人会指出：**"6-18% token saving" 的下界 6% 在 100k 规模上 Hit@10 delta = +0.00pp，CI 必然跨越零**。这意味着 100k 的 claim 实质上是"不劣于 dense 且省 token"，而非"更好"。

### C. 反馈闭环的循环性（Major）

- GT 定义目标 → GT 推导 reward → GT 评估结果
- 无真实用户反馈、无 position bias、无 delayed feedback
- "Self-evolving" claim 实质上只在已见过的 query 上改进

审稿人会问：**"如果去掉 LinUCB（用 static 融合权重），Hit@10 和 token saving 会差多少？"** Task24 的答案是：static ensemble Hit@10 = 0.7612 = full LinUCB 的 0.7612——**完全一样**。这意味着 LinUCB 学习对最终 Hit@10 的贡献为零，质量完全来自多路由融合。

### D. 下游评估不足（Major for IP&M）

- 仅 60 query LLM smoke test
- 无 faithfulness / citation support / hallucination rate / cost-per-correct-answer
- 单一 LLM judge (DeepSeek-V4-Flash)
- 论文 claim 涉及"evidence selection for RAG"，但 RAG 的 R（生成质量）几乎没评

### E. 数据集多样性（Minor-Major）

- 仅 LoTTE family (technology + science)，都是 LoTTE
- eManual 失败案例 (-54% vs dense) 说明方法对语料属性敏感
- 无非 LoTTE 的垂直领域语料

### F. 缺失的 baseline 比较（Minor）

- LLMLingua / Selective Context / DSLR — related work 讨论了但没跑实验
- SentMMR 是 strong baseline，只比 IntentWeight 差 2-3pp token saving 但完全不丢 Hit@10

---

## 五、质量评估矩阵

| 维度 | 评分 | 说明 |
|---|---|---|
| 问题定义 | ★★★★☆ | 三层成本分离精准，动机清晰 |
| 理论深度 | ★★☆☆☆ | manifold 仅诊断性，无新理论贡献 |
| 方法新颖性 | ★★★☆☆ | 组合创新，单组件均已有先例 |
| 实验严谨性 | ★★★★☆ | calibration/test + paired stats + 多 backbone |
| 统计显著性 | ★★★☆☆ | 3 seeds 不够，CI 多处触零 |
| Baseline 公平性 | ★★★★☆ | 经多轮补课后充分，缺 LLMLingua |
| 下游评估 | ★★☆☆☆ | 60 query smoke test 不足以支撑 claim |
| 可复现性 | ★★★★☆ | 参数完整，代码有，缺 formal tests |
| 写作质量 | ★★★☆☆ | 结构完整但 11 个 results 子节信息过载 |
| Claim 诚实度 | ★★★★★ | 10 条 limitations，bounded claims |
| **IP&M 录取概率估计** | **60-70%** | |

---

## 六、具体建议

### P0 — 投稿前必须做（否则大概率被拒）

1. **Random-cluster 对照实验**：用随机分配的 cluster（打乱 cluster label）跑一遍 IntentWeight。如果 token saving 和 Hit@10 不变，说明 cluster 结构无关紧要，整个 manifold motivation 就是空话。这是审稿人一定会问的。

2. **No-LinUCB ablation**：用 static fusion weights（dense 2.0 / BM25 0.8 / cluster 0.8）+ 同样的 confidence-based budget policy 跑一遍。如果 token saving 不变但 Hit@10 也不变，说明 LinUCB 学习是多余的，budget policy 才是真正贡献者。这个实验能精确回答"LinUCB 带来了什么"。

3. **Elsevier 格式转换 + 匿名化**：当前还是 ACL LaTeX 格式，IP&M 要求 elsarticle + double-anonymized。

### P1 — 审稿人大概率要求 major revision 时补

4. **扩大下游评估**：至少 300 queries，用 ≥2 个 LLM judge，评 faithfulness + answer correctness + citation support。否则 "evidence selection for RAG" 的 RAG 部分站不住。

5. **LLMLingua-2 实验**：至少跑一个 prompt compression baseline 的实验比较，不用全套，在 100k 上跑一组即可。

6. **增加 seeds 到 ≥5**（至少在 100k 和 638k 上），让 CI 收窄。

### P2 — 强化论文但不阻塞投稿

7. **Geometry-to-gain 回归分析**：用 PCAvar@64 / NearestClusterHit@3 / ContextRetention@10 作为自变量，token saving 作为因变量，跑一个简单线性回归。如果 R² > 0.3，manifold diagnostic 就有预测力，理论故事就成立。

8. **Arm count sensitivity**（K ∈ {8,16,32,64,128}）：n_clusters=32 目前无任何解释。

9. **精简 Results 节**：11 个子节合并为 4-5 个（主结果 → strong baselines → ablation → cross-domain → feedback recovery）。

---

## 七、关键洞察：真正的贡献

读完全部材料后，我认为这篇论文**真正的贡献**不是 LinUCB，不是 manifold，而是：

> **"confidence-based final context budget control" 是将多路由检索的隐性收益转化为显性 token 节省的必要机制。**

Task28 证明了"多路由不省 token"，Task37 证明了"budget policy 才省 token"，Task37-D 证明了"dense-only 截断省更多但丢质量"。论文的核心价值链是：

```
多路由融合 → 质量保障（Hit@10 不降）
     ↓
confidence assessment → 识别"哪些 query 可以安全压缩"
     ↓
budget policy → 在安全 query 上压缩 top-10 → top-8
     ↓
6-18% token saving（dense-only 截断做不到，因为它不知道哪些 query 安全）
```

**如果论文把这个故事讲成主线**（而非现在的"manifold + LinUCB + budget 三足鼎立"），新颖性更聚焦，审稿人更容易买账。LinUCB 和 manifold 是"怎么计算 confidence"的手段，budget control 才是"为什么能省 token"的原因。

---

## 八、最终判断

**当前状态**：科学内容基本完成（claim ledger 已对齐），格式包装待做。两个 P0 实验（random-cluster + no-LinUCB ablation）不做的话，审稿人有 70% 概率要求 major revision 时补做。

**投稿建议**：
- 如果赶时间 → 现在转 Elsevier 格式 + 匿名化，直接投 IP&M，赌审稿人不要求 random-cluster（有 30% 概率）
- 如果不赶时间 → 先做 P0 两个实验（预计 1-2 天），再投稿，major revision 概率降到 40%

**综合评价**：这是一篇**工程质量高于理论深度**的应用型论文。它的价值在于"把 RAG 检索的 cost 控制问题重新定义为三层结构，并用 confidence-based budget policy 解决第三层"，而非"发明了新算法"。作为 IP&M 投稿，定位合理；如果想冲 SIGIR/CIKM，理论贡献不够。

---

## 附：评审依据

本报告基于以下材料的完整阅读：
- `docs/intentweight-paper-core-narrative.md` — 核心叙事
- `paper/research-hypothesis-and-theory.md` — 研究假设
- `paper/paper-positioning.md` — 定位
- `paper/full_draft/00-09` — 完整草稿 10 节
- `intent_weight/` — 全部 10 个 Python 模块
- `paper/experiments/scripts/` — 6 个关键实验脚本
- `review/` — 8 篇审稿文档
- `review_binqi/` — 8 篇外部审稿文档 (01-08)
- `paper/experiments/task45-56` — 最新实验摘要
- `paper/journal_submission/` — 期刊投稿准备文件
