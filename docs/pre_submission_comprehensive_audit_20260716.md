# IntentRoute 发稿前综合审计

审计日期：2026-07-16
目标期刊：Information Processing & Management（IP&M）
审计范围：当前主稿、Task70-Task74 证据边界、外部审阅闭环、CAS 投稿包、图表、人工交付项与 IP&M 当前投稿要求。

## 1. 总体判断

项目已经从“继续堆实验”进入“最后一轮人工定稿与投稿冻结”阶段。

科学证据、负面结果、边界条件、统计协议和可复现性基本闭环，当前版本已经适合提交给领域专家做正式投稿前审阅。它还不能直接进入投稿系统，主要剩余项是最终 Figure 1、关键措辞校正、2026 年最新相关工作、公开工件、作者声明和人工语言润色。

核心主线不需要重做，也不需要删除 geometry、LinUCB 或 feedback。后续工作的目标是准确控制主张强度、提高阅读效率并完成投稿资产，而不是继续无边界增加实验。

## 2. 当前可支持的核心主张

当前证据支持以下有边界的机制链：

```text
局部几何组织候选路由
  -> feedback 在受控信用归因下更新局部路由状态
  -> Dense/BM25 提供最终质量底线
  -> 独立校准最终证据上下文预算
  -> 得到有边界的质量/上下文 token 前沿
```

已经处理得较好的防御性边界包括：

- manifold 是局部路由设计的启发和诊断，不是数学定理；
- route confidence 不直接预测安全压缩比例；
- 模拟 feedback 不是生产环境中的真实用户 RLHF；
- “未检测到显著差异”不等于严格等价或非劣；
- 400k、recreation/search、answer faithfulness 和 frozen unseen-query 等不利结果均被保留；
- Dense、BM25、reranking、Sentence-MMR、prompt compression 和 final-context budgeting 的职责已经分离；
- 最终 token saving 不能被扩大解释为未测量的端到端延迟、能耗、内存或总服务成本下降。

## 3. 投稿前仍需收紧的主张

### 3.1 Feedback 的标题权重

`Feedback-Adaptive` 作为机制描述可以保留，但不能暗示 feedback 是最终 token saving 或 fused quality 的稳定来源。当前证据支持的是受控 route-state adaptation、cluster-credit capacity 和条件性失败恢复，不支持普遍的 frozen unseen-query 或 full-fusion superiority。

建议将类似 `Feedback Improves the Policy Field` 的小节标题改为更精确的 `Feedback Updates Route State under Controlled Credit`，并继续保留正文中的现有限制。

### 3.2 `preregistered` 用词

Task73 的协议确实在下载和查看结果前冻结，但计划没有提交到公开注册平台，也没有在结果生成前形成公开不可变时间戳。严格意义上不宜称为正式 preregistration。

除非补充可验证的正式注册证据，主稿、补充材料和任务记录应统一使用：

- `predeclared`；或
- `prospectively specified`。

这只是术语校正，不改变 Task73 的科学设计或结果有效性。

### 3.3 成本表述

证据上下文减少能够直接映射到 LLM 输入 token 数量及其条件性输入价格分量，但不能直接推出同比的总推理成本下降。以下表达应收紧：

- `proportional per-query inference-cost reduction`；
- `the most expensive recurring component`。

推荐统一写成 `generation-stage evidence-input token reduction` 或 `conditional LLM input-cost reduction`，并明确排除检索、路由、缓存构建、延迟、内存和能耗。

### 3.4 防御性重复

当前摘要、引言、结果、讨论、结论和 Limitations 多次重复 `bounded`、`not universal` 和非劣性限制。这些边界不能删除，但应集中表达，避免主稿呈现为审稿回复。

目标是在每个主要章节先清楚给出正面贡献，再用一个集中段落说明边界，而不是在每个结果句后重复全部限制。

## 4. 论文的科学上限与下限

### 4.1 科学上限

当前版本的合理上限是一篇证据充分、可复现性很强的工程型 IR/RAG 论文。主要贡献是：

- 受控系统组合；
- route、fused retrieval 和 final-context cost 的归因分离；
- calibration/test 与 cross-fitted 评估协议；
- 多 backbone、scale 和 domain 下的 bounded frontier；
- 对负面结果和失效边界的完整报告。

它不是基础算法或理论论文。以当前方法和证据，IP&M 的 methods/critical application 类型是合理目标，ESWA 是稳健后备目标。若希望进一步冲击更高理论或 IR 方法上限，需要新的算法原理、真实反馈、稳定的 unseen-query feedback 增益或更完整的端到端系统证据，而不是再增加普通数据集数量。

### 4.2 科学下限

方法的保守下限是回退 Dense：保持既有质量，但不产生 token saving。实验不支持以下普遍性结论：

- 每个 domain、scale、split 和 seed 都存在可用压缩点；
- universal strict non-inferiority；
- feedback 普遍优于 static geometry；
- geometry 直接产生 token saving；
- route confidence 直接预测安全压缩；
- evidence completeness 保持不变；
- 端到端系统成本必然下降。

即使审稿人不接受较强的 geometry/feedback 解释，校准多路 evidence selection、Dense fallback、budget frontier 和完整负面归因仍构成有效的工程研究结果。

### 4.3 投稿结果边界

最可能的负面审稿理由不是结果错误，而是组件新颖性中等、feedback 的中心性弱于标题、稿件过重或系统成本措辞过强。当前更现实的预期是“具备投稿条件，但可能经历 major revision”，而不是轻松接收。

如果 IP&M 因新颖性或定位拒稿，现有证据仍足以重定位到应用型 AI/IR 期刊，不会退化成无法发表的工作。

## 5. 结构、规格与稿件质量

当前 CAS 包状态：

- anonymous main manuscript：28 页，含参考文献；
- supplementary material：15 页、30 张表；
- title page：1 页；
- abstract：244 词；
- keywords：7 个；
- main displays：5 张可编辑表、3 张矢量图；
- 主稿正文约 1.58 万词。

IP&M 当前 Guide for Authors 没有列出主稿总页数上限。现有摘要长度、关键词数量、双匿名主稿、独立 title page 和可编辑表格均符合公开要求。

当前主要结构问题不是违规，而是阅读负担：

- Abstract 已接近 250 词上限且信息过密；
- Method 和 Experimental Setup 小节较碎；
- 624 词 Conclusion 偏长，并与 Discussion 重复；
- Table 1 的原始 policy code、下划线和 `True/False` 不够期刊化；
- Table 5 部分方法标签换行不够整洁；
- supplement 首页空白过多；
- 末页 Table S30 排在 S13 标题之前，虽不影响引用但应在终稿中调整。

建议执行约 10% 的人工语言压缩，重点合并重复解释，不删除实验、关键数据、负面结果或主线论述。

## 6. 图表判断

### 6.1 Figure 1

当前 Figure 1 只是结构占位图，技术尺寸检查通过，但视觉质量尚未达到正式投稿要求。最终图必须由作者人工制作，并遵守：

- 190 mm 全宽矢量 PDF；
- 7 pt 或更大的成品文字；
- 嵌入字体、无 Type 3、无裁切；
- 明确区分 offline/control、online evidence flow 和 later-query feedback；
- 不画出 `route confidence -> compression ratio` 的直接箭头；
- 不暗示 LinUCB 替代 Dense/BM25；
- 保留独立 calibration budget 和 Dense fallback。

IP&M 当前期刊专属指南明确不允许生成式 AI 制作投稿插图。即使 Elsevier 的通用政策可能允许部分 explanatory images，也应遵守更严格的期刊专属要求。

### 6.2 Figure 2 和 Figure 3

两图均满足物理尺寸、矢量格式、字体和可读性要求，已达到可投稿的技术下限，但视觉叙事属于“合格”而不是“突出”。

- Figure 2 可以继续采用 quality/token frontier，但适合改为更直接的 Pareto arrow 或 stability strip；
- Figure 3 只有少量 scale 点，不应作为 manifold 或确定性相关性的视觉证明；
- 现有三面板 geometry-to-control 方案比当前小样本散点图更能展示 route-level、rescue 和 arm-granularity 证据；
- 3D embedding 图仅适合作为有明确方差声明的补充投影，不应进入主稿承担 manifold 证据职责。

Figure 2/3 优化是高价值展示提升，但不是当前科学有效性的硬阻塞项。

## 7. 最新文献定位风险

当前参考文献约 30 篇，Task71.3 主要刷新到 2025 年。2026 年 7 月已经出现数篇直接相邻工作，投稿前至少需要补充并明确区别：

- R³AG：retriever capability 与 generation utility 的 query-specific routing；
- QuDAR：基于 confidence 的 query-wise sparse/dense adaptive fusion；
- Budget-Aware Routing for Long Clinical Text：严格 token budget 下的 evidence subset selection；
- RouteRAG：RL 驱动的 text/graph adaptive retrieval，可作为较远但相关的端到端 routing 对比。

这些工作不推翻 IntentRoute，但会增加新颖性定位压力。应明确本文的区别是 geometry-defined local arms、controlled repeated feedback、Dense/BM25 rescue、independent budget calibration，以及 route/fusion/final-context attribution，而不是宣称首先提出 adaptive RAG 或 retriever routing。

该项只要求文献和叙事更新，不要求重跑实验。

## 8. 作者必须完成的事项

正式投稿前仍需人工完成：

1. 最终 Figure 1 和可编辑作者源文件；
2. 作者顺序、单位、ORCID 和通讯作者完整信息；
3. CRediT contributor roles；
4. funding、competing interest 和 acknowledgements；
5. 精确的 generative-AI disclosure，包括实际工具、用途、人工复核和责任声明；
6. 公共代码与研究数据归档链接；
7. 数据集、模型、生成答案和所含文本的许可证审计；
8. 领域专家的独立投稿前审阅；
9. 英文母语级语言和版面校对；
10. 最终投稿系统字段与文件属性匿名性检查。

当前 tracked 文件未发现 API Key 模式，但公开 release 仍必须排除 `.env`、本地缓存、虚拟环境、模型缓存、原始受限数据和机器路径。

## 9. 数据、代码与 preprint 决策

IP&M 对研究数据采用 Option C：应把验证研究结论所需的数据、代码、模型、协议或其他材料存入合适仓库并在文章中引用和链接；无法共享时必须解释原因。

推荐最终公开包采用：

- 干净的 GitHub release；
- Zenodo DOI 或等价不可变归档；
- 环境锁定文件和模型 revision；
- 数据下载脚本、source revision 和 checksums，而不是未经许可证确认的原始数据副本；
- 论文表格和图数据的来源 manifest；
- 不包含本地 `.venv-rocm` 或 AMD 专用机器状态。

IP&M 虽承认 preprint 不属于重复发表，但因采用 double-anonymized review，当前指南明确建议最终决定前不要发布 preprint。原先的 arXiv 计划应改为：

- 优先在期刊最终决定后发布；或
- 明确认知匿名性风险后，再决定是否提前发布。

## 10. 可提高上限但非硬阻塞的工作

按边际价值排序：

1. 对分层抽样答案做少量人工 correctness/faithfulness/citation rating；
2. 在匹配硬件和 cache 条件下报告 Dense/Hybrid/IntentRoute 的端到端延迟、内存和成本分解；
3. 增加正式 LLMLingua-2 或同等级 learned compressor 基线；
4. 优化 Figure 2/3 的信息表达；
5. 在真实或延迟反馈环境中验证 feedback adaptation。

这些工作能提高论文上限，但不应阻止当前 bounded evidence-selection 论文进入投稿流程。继续增加普通数据集、更多 seed 或更多 embedding backbone 的边际价值已经较低。

## 11. 投稿前优先级

### P0：提交前必须完成

- 将 `preregistered` 校正为 `predeclared/prospectively specified`；
- 收紧 input-token saving 与总推理成本之间的表述；
- 校正 feedback 小节标题和少量结论措辞；
- 刷新 2026 年直接相邻文献；
- 完成最终 Figure 1；
- 完成作者、CRediT、funding、conflict、AI disclosure；
- 准备公开数据/代码归档或无法共享说明；
- 完成一次真实人工科学审阅和语言校对；
- 提交并冻结 Task73/Task74 与最终稿件，建立 release tag；
- 重建并通过全部 experiment、evidence、LaTeX、PDF、anonymity 和 artwork 检查。

### P1：强烈建议优化

- 将主稿压缩约 10%，重点去除防御性重复；
- 优化 Table 1、Table 5 和 supplement 浮动布局；
- 采用更强的 Figure 2/3 视觉方案；
- 完成许可证清单和公开工件使用说明。

### P2：仅在提高上限或审稿人要求时执行

- 人工 answer-level rating；
- 端到端 systems profile；
- LLMLingua-2；
- 真实用户或非平稳 feedback；
- 更多 domain、seed 或 encoder。

## 12. 最终结论

IntentRoute 已经离正式投稿不远。科学主线无需重做，geometry 和 LinUCB 也不应被删除或降没。当前最重要的工作是完成一次严格的终稿工程：校正少量术语和成本表述、刷新 2026 文献、制作 Figure 1、准备公开工件、填写作者声明、执行人工润色并冻结投稿版本。

完成 P0 后，稿件可以合理进入 IP&M 投稿流程。当前状态更准确地描述为：

> ready for final independent pre-submission review, but not yet ready to click submit.

## 13. 官方依据

- IP&M Guide for Authors：<https://www.sciencedirect.com/journal/information-processing-and-management/publish/guide-for-authors>
- Elsevier generative-AI policy：<https://www.elsevier.com/en-au/about/policies-and-standards/generative-ai-policies-for-journals>
- Elsevier double-anonymized review guidance：<https://www.elsevier.com/reviewer/what-is-peer-review/guidelines>
- R³AG：<https://aclanthology.org/2026.acl-long.939/>
- QuDAR：<https://aclanthology.org/2026.acl-long.1791/>
- Budget-Aware Routing：<https://aclanthology.org/2026.findings-acl.2114/>
- RouteRAG：<https://aclanthology.org/2026.findings-acl.1502/>
