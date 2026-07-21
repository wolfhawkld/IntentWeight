# IntentRoute Paper Core Narrative

Updated: 2026-07-01

本文档用于后续写作纠偏：当论文继续扩写、改标题、调图表或回应审稿意见时，优先对照这里的核心叙事，避免重新滑回“工程 task 汇报”或“泛化过度”的表达。

## Terminology And Fact Guardrail

- 当前论文、人类可读叙事和新代码统一使用 **IntentRoute**。
- **IntentWeight** 仅保留为历史项目名、legacy import path、历史实验目录或
  machine-readable artifact label。
- 当前论文主实验中的 route arms 由 **KMeans/MiniBatchKMeans fixed arms**
  构造；主设置为 `K=32`，并用 `K={8,16,32,64,128}` 做敏感性检查。
- 历史文档、早期原型和 `pre_validation/` 中出现的 HDBSCAN 方案不代表当前论文
  主方法。若引用这些材料，必须明确其历史/原型定位。

## One-Sentence Thesis

IntentRoute 是一个面向结构化垂类知识载体的反馈驱动证据选择控制器：它在 dense recall floor 之上结合 lexical anchor、局部几何路由和 LinUCB feedback adaptation，在保持答案可用证据召回的同时，动态控制最终送入 LLM 的 context token 成本，并为压缩导致的尾部失败提供反馈恢复路径。

## Core Problem

结构化垂类知识系统面临的核心问题不是“是否使用 RAG”，而是：

> 在有限 context、有限延迟和有限成本下，系统如何选择足够可靠、足够少且可用于回答问题的证据？

纯 dense retrieval 很强，但它是固定检索策略。它不能显式决定：

- 什么时候 lexical matching 更安全；
- 什么时候局部语义/结构几何可靠；
- 什么时候必须保留 dense fallback；
- 什么时候可以减少最终送入 LLM 的 evidence context；
- 当压缩导致失败时，如何利用反馈修复后续或重试行为。

## Core Hypothesis

垂类知识数据的 query-document relevance 通常不是均匀分布的，而是由以下因素形成 piecewise relevance structure：

- domain terminology；
- semantic neighborhoods；
- task workflows；
- entity and document organization；
- user intent and feedback behavior。

本文不主张证明严格数学意义上的流形定理。更稳妥的说法是：

> 垂类知识数据存在可被 dense、BM25、cluster-local routing 和 feedback signals 共同近似的局部相关性结构。

## Method Logic

IntentRoute 不替代 dense retrieval，而是在 dense recall floor 上做 adaptive control。

方法链路是：

1. Dense retrieval 提供全局语义召回和质量下限。
2. BM25 提供 lexical anchors，保护术语、实体、编号和精确匹配查询。
3. Fixed routing arms 用 KMeans/MiniBatchKMeans 构造稳定的局部路由空间。
4. LinUCB 根据 query/context/route features 学习哪些局部区域更可能有用。
5. Trust-weighted simulated feedback 更新 route-policy value field。
6. Independently calibrated context budgeting 在 routed ranking 上选择全局
   token ratio 与 minimum prefix，不把 route confidence 当作 per-query
   compression-safety predictor。
7. Feedback-triggered recovery 在压缩失败后触发更安全的预算或 fallback 策略。

## Evidence Chain

论文主证据应按以下顺序组织：

1. **Main calibrated token-quality frontier**:
   在 calibration/test 协议下，100k、200k、638k 的 calibration-eligible operating points 可节省 6-18% evidence-context tokens，并避免 dense-only adaptive truncation 的明显 Hit@10 损失。400k 原始 frozen split 的 calibration eligibility 未通过，必须继续保留该事实。统一 five-fold follow-up 在 400k 得到 14.50% mean saving 和约 0.00pp mean Hit delta，但五折选择五种策略且 strict NI 为 0/3，因此只能作为正向但仍有 partition sensitivity 的补强证据。
   独立 Dense calibration 在原 100k split 上选择 0% saving，而 IntentRoute
   选择 6.18% saving 且 mean Hit delta 为 0；但 strict NI 仍未建立。20-split
   sensitivity 强化 200k/638k，显示 100k 中等敏感、400k 混合；统一
   cross-fitted audit 进一步确认该结论，因此不能写成 split-invariant guarantee。

2. **Conservative confidence-only baseline**:
   在 100k-638k corpus chunks 上，保守 context policy 减少约 4.7-5.3% final retrieved context tokens，并保持 dense-level Hit@10。该结果作为稳定 baseline 和 seed-diagnostic 支撑，主结果应以前一项 calibrated policy 为核心。

3. **Cross-domain validation**  
   LoTTE science/search 支持 fixed top-10 ranking-side gain，但也说明 context compression strength 必须按 domain 和 scale 校准。

4. **Feedback-driven policy adaptation**  
   Feedback 的价值不一定总反映在最终 fused Hit@10，因为 dense/BM25 fallback 可能已经保护了最终质量。更清晰的证据是 selected-cluster hit、last true reward、dense rate 和 LinUCB route usage 的变化。

5. **Dynamic route mediation**
   冻结 selected arms 与 feedback trajectory 后，原始 confidence-tier assignment
   相比保持 tier 频率不变的 shuffled control，在相同预算前后均提高 4.80pp
   Hit@10；低置信 query 强制使用 cluster-primary 时明显失效。这支持
   `geometry/feedback -> confidence -> route shape/fallback -> evidence-pool quality`
   的操作化链路，但不支持 `confidence -> per-query compression safety`。

6. **Feedback-triggered recovery**
   对被 aggressive compression 伤害的 tail queries，arm-level simulated feedback 能恢复一部分失败样本。该证据支持 post-feedback recovery，不支持“首轮检索必然改善”的过度表述。

7. **Geometry diagnostics**
   NearestClusterHit@3、PCA spectrum 和 context retention 支持“局部结构有用”的解释，但不能写成数学证明。

8. **Boundary cases**
   eManual、CUAD、secondary datasets 用于限制主张边界，避免把结果写成所有 dataset、所有任务、所有指标上的全面胜利。

9. **Multi-judge downstream robustness**
   固定 2,100 个 generated answers 由 DeepSeek、GLM-5.2 和 MiniMax-M3
   独立评估。共同 2,072 条上 correctness agreement 较高，所有 matched
   correctness differences 均未达到显著，但 stricter judges 给出负向 BGE/E5
   point estimates，且 majority-vote BGE faithfulness 显著下降。因此正文可写
   bounded correctness robustness，不能写 uniform faithfulness preservation、
   strict non-inferiority 或 human-rated validation。

## Section-Level Intent

- **Introduction**：提出证据选择的 quality-cost-control 问题，强调本文不是替代 dense，而是在 dense 之上学习何时路由、何时压缩、何时恢复。
- **Related Work**：连接 RAG/dense/BM25/hybrid retrieval、contextual bandits、geometry-inspired retrieval、context compression 和 feedback/RLHF-inspired optimization。
- **Method**：描述 IntentRoute 的 controller 设计，而不是把各个组件写成工程流水线。
- **Experimental Setup**：明确数据集角色、metrics、prequential simulated feedback、cost layer separation。
- **Results**：先给 calibrated token-quality frontier，再给 cross-domain、component ablation、feedback adaptation/recovery、geometry 和 boundary/robustness checks。
- **Discussion**：解释为什么 multi-route 本身不等于省 token；route confidence
  用于 routing/fallback，主要成本收益来自独立校准的 final-context budget，
  feedback-triggered fallback 用于失败恢复。
- **Limitations**：主动限制 simulated feedback、single-resource-class encoder、Hit@10 只代表 usable evidence、geometry 只是 diagnostic support。
- **Conclusion**：回到 controller 贡献：quality、context token cost 和 recovery 的动态 trade-off。

## Claim Boundaries

Use:

- feedback-guided evidence selection controller；
- adaptive route-control problem；
- dense recall floor；
- piecewise relevance structure；
- final evidence-context token cost；
- quality-cost frontier；
- feedback-triggered recovery。

Avoid:

- IntentRoute universally beats dense；
- LinUCB alone explains all gains；
- KMeans is the best clustering method；
- geometry diagnostics prove a manifold theorem；
- simulated feedback equals real user feedback；
- candidate-count reduction equals LLM token saving；
- post-feedback retry equals first-pass IID improvement。

## Preferred Framing

最稳的论文定位是：

> 本文不是提出一个全面超过 dense retrieval 的检索器，而是提出一个 feedback-guided adaptive evidence selection controller。它把结构化垂类知识系统中的证据选择、context token 成本和失败恢复建模为一个可学习的控制问题，并在 LoTTE 大规模垂类检索实验中展示了可控的 quality-cost trade-off。
