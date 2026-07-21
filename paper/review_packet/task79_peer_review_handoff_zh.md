# IntentRoute 截至 Task79 的同行审阅交接说明

> **Historical Task79 review checkpoint:** 当前状态与剩余任务请以
> `../experiments/task80_authoritative_submission_state.md` 和
> `../experiments/task80_remaining_work_checklist.md` 为准。

状态：Task79 已完成，Task80 尚未开始全局状态对账
审阅基线：`pre_validation` 分支，Task79 complete-recovery revision
日期：2026-07-21

## 1. 文档目的

本文档供未参与日常实验开发的同事独立审阅当前研究。它不是论文正文，
而是截至 Task79 的科学主张、方法、证据、负向结果、复现状态和待审问题的
统一入口。内部 Task 编号仅用于追溯；论文正文使用概念化名称。

建议先阅读本文档，再阅读：

- 完整论文 PDF：[`../latex/main.pdf`](../latex/main.pdf)
- Markdown 正文：[`../full_draft/`](../full_draft/)
- 实验使用状态：[`../experiments/task_paper_use_status.md`](../experiments/task_paper_use_status.md)
- Task79 总结：[`../experiments/task79_llmlingua2_matched_compressor_summary.md`](../experiments/task79_llmlingua2_matched_compressor_summary.md)
- 人工校验标准：[`../../docs/human_validation_criteria.md`](../../docs/human_validation_criteria.md)

## 2. 一句话定位

IntentRoute 是一个由局部几何结构启发、由反馈修正的自适应证据路由与
最终上下文预算控制器。它在保留 Dense/BM25 安全召回路径的同时，利用
cluster-local route 和 LinUCB route confidence，在特定语料、域和校准条件下
寻找回答质量与最终 LLM evidence-context token 之间的可用折中点。

研究逻辑链为：

> local geometric structure -> adaptive route selection -> feedback correction
> -> quality-efficiency trade-off

其中：

- 几何/流形是方法设计假设和诊断性证据，不是已证明的流形定理；
- LinUCB 是现有 contextual bandit 在 route-confidence 学习中的应用，不是新算法；
- feedback 是受控模拟下的适应与恢复证据，不是真实生产 RLHF；
- Dense 是安全召回和 fallback，不是应被无条件关闭的冗余路径；
- 成本指标是送入生成模型的最终 evidence-context tokens，不是端到端系统成本。

## 3. 研究问题

当前论文实际回答四个相互关联的问题：

1. 垂直领域语料的局部结构是否足以构造有信息量的 cluster-local routes？
2. contextual bandit 和反馈能否学习或修正这些 route 的使用方式？
3. 独立校准的上下文预算能否在部分域和规模上减少最终 LLM 输入证据，
   同时保持接近 Dense 的 query-level retrieval quality？
4. 当同样的后检索压缩器用于 Dense 和 IntentRoute 时，较短上下文关系是否仍然存在？

论文不试图证明：

- 任意语料都可以无损压缩；
- 几何指标可以直接预测每个 query 的安全压缩率；
- 首次遇到未见 query 时，反馈学习必然优于静态或无反馈策略；
- `Hit@10` 等同于完整证据覆盖或最终答案正确；
- final-context token saving 等同于端到端部署成本按同比例下降。

## 4. 方法结构

### 4.1 离线结构与共享索引

- 使用固定数量的 KMeans/MiniBatchKMeans clusters 构造 LinUCB arms。
- Dense embedding 描述局部语义邻域；BM25 提供 lexical anchor 和全局补救。
- 聚类数固定是为了 arm 空间可复现和 bandit 状态可管理，不表示 KMeans 是最佳聚类算法。
- embedding、BM25 ranking 和其他公共中间 artifact 可由不同 baseline 复用；最终实验结果不互相复用。

### 4.2 在线证据路由

- Dense、BM25 和 cluster-local route 分别产生候选证据。
- LinUCB 基于 query/context feature 和历史 reward 学习 cluster arm 的 route confidence。
- confidence gate 决定 cluster-local route 与全局 rescue route 的组合方式。
- Dense floor 在低置信度或高风险情况下保护召回覆盖。

### 4.3 Feedback 与 reward

- 实验 feedback 来自 ground truth 派生信号，并加入受控噪声和 trust weighting。
- feedback 用于验证 route credit assignment、重复交互适应和受损 query 的恢复潜力。
- reward 是可观测相关性/效用的工程近似，不等同于真实潜在流形本身。

### 4.4 最终上下文预算

- route confidence 与 final-context budget 是两个不同决策层。
- 预算动作只在 calibration split 上选择，随后冻结到 test split。
- token cost 按实际送入生成模型的 evidence context 统计。
- 当前证据不支持用 route confidence 直接预测单 query 的 compression headroom。

## 5. 实验覆盖

实验覆盖九种 dataset/domain setting、八类领域，但各设置承担不同证据职责，
不能视为九次同质 full-stack replication，也不应汇总成单一 pooled effect。

| 数据设置 | 规模/协议 | 主要职责 |
|---|---|---|
| LoTTE technology/search | 100k、200k、400k、638k | 核心多规模、完整 route/budget/feedback 证据 |
| LoTTE science/search | 20k、100k、200k、400k | 跨域与规模边界 |
| LoTTE recreation/search | 100k，预先规定协议 | 外部有效性负向/边界案例 |
| LoTTE writing/search | 100k，预先规定协议 | 外部有效性正向 frontier |
| PubMedQA | native full | Dense ceiling transfer |
| CovidQA-RAG | native full | 非 ceiling 生物医学 transfer |
| eManual | deduplicated native full | 重复证据修正后的边界 |
| Banking77 | native full | intent-routing mechanism，不含同口径 context endpoint |
| CUAD | GT-anchored 10k sample | sparse-ground-truth boundary |

使用的主要 encoder 包括 MiniLM、BGE-base 和 E5-base；强基线还包括
BM25、hybrid、Dense adaptive truncation、Sentence-MMR、cross-encoder reranker
以及官方 LLMLingua-2。

## 6. 核心结果

### 6.1 多规模 token-quality frontier

LoTTE technology/search 原始冻结 split 的主要 operating points：

| Corpus scale | Test Hit delta vs Dense | Final-context token saving | 解释 |
|---:|---:|---:|---|
| 100k | +0.00 pp | 6.18% | calibration eligible；严格 NI 为 0/3 seeds |
| 200k | +1.20 pp | 16.00% | calibration eligible |
| 400k | +2.32 pp | 6.57% | 原 calibration gate 未通过，仅作 diagnostic |
| 638k | -0.08 pp | 17.53% | calibration eligible；严格 NI 为 0/3 seeds |

统一五折 follow-up 的 Hit delta/token saving 分别为：

- 100k：`-1.06pp / 4.16%`；
- 200k：`+1.40pp / 16.07%`；
- 400k：`+0.00pp / 14.50%`；
- 638k：`+0.28pp / 15.23%`。

400k 五折均可选出非零压缩动作，但每折选择不同 policy，且严格
non-inferiority 仍为 `0/3` seeds。因此它支持平均 trade-off，不支持稳定、
split-independent 的无损压缩声明。

Dense-only adaptive truncation 通常节省更多 token，但在四个原始 scale 上均出现
`Hit@10` 降低。IntentRoute 的目标是更保守的 bounded frontier，而非最大压缩率。

### 6.2 跨域结果显示明显异质性

| Setting | Hit delta | Token saving | 结论角色 |
|---|---:|---:|---|
| science/search 100k | -0.11 pp | 16.88% | 有用但无严格 NI |
| science/search 200k | -0.67 pp | 10.75% | 规模扩展边界 |
| science/search 400k | -0.67 pp | 3.15% | 仅 1/5 folds 压缩，明确负向边界 |
| recreation/search 100k | -0.76 pp | 5.42% | 0/3 strict NI，边界案例 |
| writing/search 100k | +0.12 pp | 10.09% | 2/3 strict NI，有用 frontier |
| CovidQA-RAG native full | -0.21 pp | 9.00% | 生物医学 transfer |
| eManual deduplicated | -0.26 pp | 16.20% | 修正后的边界结果 |

PubMedQA 位于 Dense ceiling，未产生额外压缩；Banking77 和 CUAD 不具备与
上述 full-stack 行相同的 final-context endpoint。结果支持域/规模特定校准，
不支持统一压缩比例。

### 6.3 Encoder robustness

LoTTE technology/search 100k 的 matched-backbone 结果：

| Backbone/policy | Hit delta vs matched Dense | Token saving |
|---|---:|---:|
| MiniLM calibrated | +0.00 pp | 6.18% |
| BGE full multi-route | -0.08 pp | 11.99% |
| E5 full multi-route | -0.64 pp | 12.20% |
| BGE quality-first | +0.88 pp | 7.23% |

BGE 存在 above-dense quality-first point；E5 没有观察到相同现象，因此不能把
该结果泛化为任意 encoder 都能同时提高 Hit 和节省 token。

### 6.4 Geometry、feedback 与 rescue 的职责分离

- Static-nearest geometry 的 route reward/cluster hit 为 `0.8563/0.8870`，
  uniform-random arms 为 `0.1499/0.1577`，说明局部结构对 route construction 有信息量。
- Dense/BM25 rescue 会显著缩小 geometry 与 random 在最终 fused `Hit@10` 上的差距，
  因此最终质量不能归因于 geometry alone。
- learned route 的 route reward/cluster hit 为 `0.6790/0.5766`，no-feedback control
  为 `0.1504/0.1570`；feedback 能改变 route quality，但 tested learned gate 相比
  Dense 在冻结测试上下降 `5.20pp`。
- 保持 route trajectory 不变时，真实 confidence-tier assignment 比 shuffled-tier
  高 `4.80pp Hit@10`，比 always-cluster-primary 高 `10.79pp`，支持 confidence 用于
  route/fallback assignment。
- confidence 与 per-query compression headroom 没有稳定关系，不能将其描述为
  safe-compression oracle。
- same-query conservative retry 在 technology/search 与 science/search 100k 共恢复
  `23/76` 个 budget-induced misses。完整 recurrent-stream 实验没有显示 feedback 对
  最终 fused retrieval 的稳定普遍增益。

因此，当前反馈主张是“受控重复交互下的 route adaptation 与条件恢复”，而不是
“首次未见 query 上普遍提高最终质量”。

### 6.5 强后检索基线

- Dense+Sentence-MMR 在保持 Dense chunk-support `Hit@10=0.8705` 时节省
  `11.4-13.1%` sentence tokens。
- 相同 Sentence-MMR 用于两种 upstream pool 后，IntentRoute 的总节省为
  `10.1-21.2%`，说明 routing 与 downstream compression 可以组合。
- cross-encoder reranker 将 Dense full-top-10 Hit 从 `0.8705` 提高至 `0.8777`，
  但 context tokens 增加 `21.9%`；matched-budget 下未统一支配 IntentRoute。

这些结果要求论文把 IntentRoute 描述为可与 compressor/reranker 组合的 route-and-budget
controller，而不是声称它独占 context compression 能力。

## 7. 下游答案级证据

### 7.1 Sentence-MMR 与 matched-backbone evaluation

主下游实验固定 300 queries、7 methods，共生成 2,100 answers；DeepSeek、GLM-5.2
和 MiniMax-M3 提供 6,272 条有效判断。三 Judge 共有 2,072 个完整 query-method keys；
同协议恢复重试后仍有 28 条 MiniMax provider-filtered judgments 不插补。

匹配比较中的 context-saving 置信区间均为正，但 correctness 的 individual-judge
和 majority intervals 全部跨零。BGE majority faithfulness 下降 `4.15pp`
（95% CI `[-6.92,-1.73]`，`p=0.0018`），Sentence-MMR composition 上升
`3.67pp`（95% CI `[+0.33,+7.00]`，`p=0.0522`）。这说明 correctness robustness
不能替代 faithfulness 分析。

### 7.2 Task79：官方 LLMLingua-2 matched-compressor test

Task79 使用相同的 300 个 frozen queries、相同 upstream evidence pools、相同 answer
prompt/generator，以及预先冻结的 target rule。Dense 和 IntentRoute 均调用官方
`microsoft/llmlingua-2-xlm-roberta-large-meetingbank`，没有重新调 retrieval 或 routing。

| Endpoint | Mean context tokens |
|---|---:|
| Dense + LLMLingua-2 | 1,259.22 |
| IntentRoute + LLMLingua-2 | 1,175.02 |

IntentRoute 的 paired context saving 为 `6.69%`，95% bootstrap CI
`[4.32%,9.03%]`；prompt-token saving 为 `6.77%`。

| Judge | Correctness delta | 95% CI | Faithfulness delta |
|---|---:|---:|---:|
| DeepSeek | +3.00 pp | [-1.00,+7.00] | +3.67 pp |
| GLM-5.2 | +0.67 pp | [-3.33,+4.67] | +0.33 pp |
| MiniMax-M3 | +0.00 pp | [-3.67,+4.00] | -1.33 pp |
| Three-judge majority | +0.67 pp | [-3.00,+4.33] | +0.00 pp |

majority exact McNemar `p=0.8642`。因此 Task79 支持：在该固定设置中，
IntentRoute 较短上下文关系在官方 learned compressor 下仍然存在，且没有检测到
correctness degradation。它不支持严格 non-inferiority、显著答案提升、
geometry-to-compression causality 或 universal compressor generalization。

三 Judge 对四个 endpoint 均为 `1,200/1,200` 完整覆盖。此前缺失的 7 条
Sentence-MMR MiniMax 判断已由完全相同的 Judge 协议恢复，失败尝试继续保留为 provenance。

## 8. 统计与协议保护

- calibration 与 frozen test 分离，正式 test labels 不参与 action selection；
- 主要质量比较使用 query-level pairing、paired bootstrap confidence intervals 和
  exact McNemar tests；
- seed 13/17/19 是工程稳定性重复，不能替代 query-level inference；
- strict non-inferiority 与“point estimate 接近 Dense”分开报告；
- 不跨异构 domain、dataset role 或 metric 计算 pooled effect；
- 失败、provider filtering 和 missing judgments 均记录且不插补；
- 复用的 embedding/BM25/ranking 是共享中间 artifact，不是复用最终统计结果；
- `Hit@10` 只表示 top-10 中至少存在一个可用证据，不表示 complete evidence collection。

## 9. 当前最重要的负向和边界结果

审阅时请确认这些内容没有在摘要、正文或图表中被弱化：

1. science/search 400k 只有 `3.15%` saving、`-0.67pp` Hit，且仅 `1/5` folds 压缩。
2. recreation/search 为 `5.42%/-0.76pp`，strict NI 为 `0/3`。
3. geometry 与 feedback 的 route-level 优势会被 Dense/BM25 rescue 掩盖，不能直接解释最终 Hit。
4. learned gated routing 在冻结未见 query 上显著弱于 Dense；feedback 不具备普遍 first-pass 优势。
5. confidence 不能稳定识别 per-query safe compression。
6. BGE downstream majority faithfulness 显著下降，尽管 context 更短且 correctness 未显著变化。
7. 多数正向点没有建立严格 non-inferiority；“未检测到差异”不等于“证明等价”。
8. final-context saving 尚未证明完整端到端成本下降，尤其未覆盖索引构建、所有检索计算和输出 token。

## 10. 可复现性和当前产物状态

- Task78 在 AMD Radeon RX 9070 XT 上完成 MiniLM/BGE/E5 及关键 domain 的 GPU
  数值复核；固定 artifact 可在 CPU 上重建论文统计和 PDF。
- 对浮点 tie 使用 byte-exact、ranking-exact 和 scientific-equivalence 分级，不把
  数值等价误写成字节一致。
- Task79 固定模型 revision、官方代码 commit、权重 SHA256、tokenizer、ROCm 环境，
  并通过 `14/14` local gates。
- 当前统一实验审计为 `921/921`，表格/图数据审计为 `128/128`。
- ACL 完整证据 PDF 为 34 页；CAS 匿名主稿 26 页、supplement 13 页、title page 1 页。
- 两种 PDF pipeline 均通过构建、引用、交叉引用、关键版面和字体审计；CAS Type 3
  字体 fallback 已通过显式 `T1 + lmodern` 配置消除。
- Task79 API 凭证未进入 tracked artifact；失败请求保留为技术 retry provenance。
- exact historical fresh-route replay 仍缺少部分早期未跟踪 cache；固定最终 artifact
  复现和关键 GPU 数值复核已经通过。详见 Task78 summary。

## 11. 当前允许与不允许的论文主张

### 可以主张

- 局部几何结构能构造有信息量的 cluster-local route。
- feedback 和 confidence 能影响 route quality、fallback assignment，并在部分重复交互
  或受损 query 上提供条件恢复。
- 独立校准的 route-and-budget controller 在多个、但非全部 domain/scale 上形成
  near-Dense quality 与较少 final-context tokens 的有用折中。
- 该 token/quality 关系在 MiniLM/BGE/E5、Sentence-MMR 和一个官方 LLMLingua-2
  固定测试中具有一定鲁棒性。
- Dense fallback 与 downstream compressor 是方案的互补组件，而不是需要排除的对手。

### 不可以主张

- 方法普遍超过或替代 Dense；
- 几何验证了真实 query-document relevance manifold；
- geometry/confidence 可以直接确定安全压缩比例；
- simulated feedback 等同于真实用户 RLHF，或普遍提升首次未见 query；
- quality-preserving、lossless 或 non-inferior 在所有设置上成立；
- context-token saving 已经等价为完整系统成本节省；
- automated multi-judge evaluation 等同于 human evaluation。

## 12. 希望同行重点审阅的问题

请按“阻断发表 / 重要但可修 / 表达优化”三级给出反馈，优先回答：

1. **主张闭环**：局部结构、route control、feedback correction 与最终 budget
   trade-off 是否形成连贯论证，还是仍存在跳步？
2. **归因边界**：论文是否清楚区分 route quality、rescue quality 和 final-context
   budgeting，是否仍容易让读者误以为 LinUCB 直接决定 token ratio？
3. **统计解释**：对 confidence interval、McNemar、strict NI、seed 和 split sensitivity
   的解释是否充分且没有把“不显著”写成“等价”？
4. **Baseline fairness**：Dense、BM25、hybrid、same-budget truncation、Sentence-MMR、
   reranker、BGE/E5 和 LLMLingua-2 是否构成足够公平的 baseline surface？
5. **跨域有效性**：九种 setting 的角色划分是否清楚，是否仍给人“只在一个 LoTTE
   domain 上完成全部实验，却暗示普遍泛化”的印象？
6. **Feedback 价值**：当前受控 feedback 证据是否足以支持“adaptive correction
   potential”，其边界是否表达得足够直接？
7. **答案级证据**：三 Judge、单 generator、无人工评分以及 BGE faithfulness 下降，
   是否要求进一步降低某些表述或增加 human audit？
8. **投稿呈现**：五张主表、三张主图和 23 张补充表是否信息密度合理；哪些证据应在
   主文与 supplement 之间重新分配？
9. **复现与匿名性**：固定 artifact、模型/API provenance、许可和 blind artifact
   策略是否足以满足目标期刊审查？
10. **最高价值补充项**：在不无限扩展实验的前提下，哪一个补充最可能改变论文结论
    或审稿风险？

## 13. 关键 artifact 索引

- 主结果：[`../full_draft/06_results.md`](../full_draft/06_results.md)
- Discussion：[`../full_draft/07_discussion.md`](../full_draft/07_discussion.md)
- Limitations：[`../full_draft/08_limitations.md`](../full_draft/08_limitations.md)
- 完整 appendix：[`../full_draft/12_appendix.md`](../full_draft/12_appendix.md)
- 统一 evidence audit：[`../experiments/results/task67_paper_evidence_audit.json`](../experiments/results/task67_paper_evidence_audit.json)
- Task79 paired 结果：[`../experiments/results/task79_llmlingua2_multi_judge_analysis.paired.csv`](../experiments/results/task79_llmlingua2_multi_judge_analysis.paired.csv)
- Task79 execution manifest：[`../experiments/results/task79_llmlingua2_downstream_evaluation/llm_execution_manifest.md`](../experiments/results/task79_llmlingua2_downstream_evaluation/llm_execution_manifest.md)
- Task79 local gate：[`../experiments/results/task79_local_validation.md`](../experiments/results/task79_local_validation.md)
- Task78 跨设备复现：[`../experiments/task78_cross_machine_reproduction_and_gpu_revalidation_summary.md`](../experiments/task78_cross_machine_reproduction_and_gpu_revalidation_summary.md)
- CAS 匿名稿：[`../journal_submission/latex/anonymous_manuscript.pdf`](../journal_submission/latex/anonymous_manuscript.pdf)
- CAS supplement：[`../journal_submission/latex/supplementary_material.pdf`](../journal_submission/latex/supplementary_material.pdf)

## 14. Task79 后的剩余工作边界

下一阶段 Task80 只做最终 evidence integration 和 submission-state reconciliation：
刷新所有状态数字、对账 task/review/readiness 文件、执行全量审计，并生成唯一权威
remaining-work checklist。它不应改变 Task79 数据，也不应借整理过程扩大中央主张。

Task81-83 分别处理作者自有矢量图和元数据、公开复现/许可包、独立终审与最终冻结。
这些是投稿准备工作，不是当前科学结果的一部分。
