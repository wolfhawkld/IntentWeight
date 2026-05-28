# 论文初稿审阅意见

**日期**: 2026-05-25  
**审阅范围**: `paper/draft/` 全部文件 + `paper/experiments/task33_pre_writing_validation_backlog.md`  
**对应提交**: pre_validation 分支 5600391..61b24ba

---

## 1. 总体评价

论文初稿质量不错，方向和风格符合第二轮审计的建议。Codex 在 claim 边界控制、成本分层、流形术语审慎使用等方面执行到位。

| 维度 | 评价 |
|------|------|
| 论文结构和选题 | 好，符合 CIKM/SIGIR system paper 风格 |
| Claim 边界 | 优秀，审稿人很难攻击 over-claim |
| 实验设计 | 好，Task33 backlog 覆盖了主要风险 |
| 写作质量 | 中等偏上，需要润色但骨架清晰 |
| 投稿就绪度 | **完成 Task33.1-33.4 后可投** |

---

## 2. 做得好的地方

### 2.1 Claim 边界控制优秀

全文反复明确：
- "不是替代 dense，是 controller"
- "4.7-5.3% token saving under conservative policy"
- "bounded claim"
- "dense remains a recall floor"

这是第一轮审计最重要的建议，执行得很到位。

### 2.2 三层成本分离清晰

Source candidates / dense invocation rate / final context tokens 三层被正确区分。这是 Task28 自我纠错后的核心教训，在 method 和 experiments 中都被正确表述。

### 2.3 流形术语处理得当

使用 "piecewise relevance-manifold **assumption**"，明确说是 diagnostic 而非 proof。正是之前建议的 Route C 策略（manifold 作为 motivation/framework，不作为 proven theorem）。

### 2.4 Limitations 章节全面诚实

每个已知弱点都被列出且正确定位为 "boundary, not invalidation"：
- 模拟反馈（非真人）
- 仅检索层（无端到端 LLM 生成评估）
- 单一 encoder
- 3 seeds
- KMeans 是实验选择而非最优声明

### 2.5 Task33 Backlog 规划合理

- BGE 多模型验证（分阶段降低风险）
- Feedback sensitivity
- Clean ablation table
- Protocol defense

这些正是审计中标注的投稿前必做项。

---

## 3. 问题和建议

### 3.1 Abstract 缺少 "so what" 实用价值陈述

**问题**: 当前 abstract 结尾是 "adaptive quality-cost controller for large-scale vertical-domain RAG"，缺少量化的工程意义。

**建议**: 补一句：
> "For enterprise RAG systems processing tens of thousands of daily queries, even conservative 5% token reduction translates to significant inference cost savings that grow with interaction volume."

这让审稿人理解 5% 不是微不足道的数字。

### 3.2 Introduction 第一段措辞可更具体

**问题**: "persistent control problem" 措辞模糊。

**建议**: 改为更具体的问题陈述——如何在不损失质量的前提下减少送入 LLM 的 context token 数量。

### 3.3 Method 中 LinUCB 探索项缺少解释

**问题**: `alpha * sqrt(x_t^T A_a^{-1} x_t)` 是探索项，非 bandit 背景的读者可能不理解。

**建议**: 加一句 "where alpha controls the exploration-exploitation balance; higher alpha encourages exploring under-sampled arms."

### 3.4 Experiments 中 638k 结果需确认证据来源

**问题**: 表格有 638k 行（Hit@10=0.7466, token saving=4.86%），但需确认是否已有完整的 3-seed CI 支撑，还是单次运行结果。

**建议**: 若为单 seed，需标注；若有 3 seeds，补充 CI 到 seed stability 表。

### 3.5 Task33.1 BGE 策略有隐含依赖未提及

**问题**: BGE-base-en 是 768d embedding，但当前 LinUCB 的 `context_dim` 是按 384d MiniLM 设计的（PCA 到 64d）。换模型后：
- PCA 基需要重新计算
- KMeans cluster 需要重新训练
- context_dim 可能需要调整

**建议**: 在 Task33.1 plan 中明确标注这些依赖，避免直接跑然后报错。

### 3.6 Task33.5 LLM Generation Smoke 缺少具体配置

**问题**: Plan 说 "50-100 queries sanity check"，但没指定：
- 用哪个 LLM（API GPT-4? 本地 Llama-3-8B?）
- 推理配置（temperature, max_tokens）
- 评估方式（人工? LLM-as-judge?）

**建议**: 补上具体配置，或至少给出两个可选方案。

### 3.7 400k Seed CI 异常宽需准备解释

**问题**: 400k token saving CI 为 `[0.11%, 10.53%]`，意味着某个 seed 几乎没有 saving。

**建议**: 
- 检查该 seed 的 confidence 分布是否异常
- 准备 rebuttal 解释（如："one seed converged to a more conservative policy with lower confidence, resulting in less compaction"）
- 如果 Task33.6 能补更多 seeds，优先补 400k

---

## 4. 各章节具体评价

| 章节 | 评价 | 关键问题 |
|------|------|---------|
| outline.md | 结构清晰，claim boundary 明确 | Working title 推荐第一个，最简洁 |
| abstract.md | Claim checklist 是好实践 | 缺 "so what" 句（见 3.1） |
| introduction.md | 逻辑链完整，贡献列表准确 | 第一段可更聚焦（见 3.2） |
| method.md | 形式化清楚，algorithm sketch 好 | alpha 解释缺失（见 3.3） |
| experiments.md | 表格齐全，解释审慎 | 638k CI 需确认（见 3.4） |
| limitations.md | 全面诚实，每点都 fair | 无重大问题 |
| task33_backlog.md | 规划合理，优先级正确 | BGE 依赖和 LLM smoke 配置（见 3.5, 3.6） |

---

## 5. 最大风险

**单一 embedding model (Task33.1)** 仍是投稿前最大风险。

如果 BGE 下 IntentWeight 失效（即 token saving 消失或质量大幅下降），论文的泛化性主张会被严重削弱。建议：
1. 优先跑通 BGE 20k smoke（Task33.1a）
2. 若 BGE dense 本身很强（Hit@10 > MiniLM），IntentWeight 仍能保持 near-dense + token saving → 论文 claim 成立
3. 若 BGE 下 IntentWeight 质量明显低于 BGE dense → 需要在 limitation 中明确标注 encoder 依赖

---

## 6. 下一步建议

按优先级排序：

1. **Task33.1a**: 跑 BGE-base-en 20k smoke（注意重算 PCA/clusters）
2. **Task33.3**: 整理 clean ablation table（可与 33.1 并行）
3. **Task33.4**: 写 protocol defense subsection（纯写作，无计算依赖）
4. **Task33.2**: Feedback sensitivity（可与 33.1 并行）
5. **Task33.5**: LLM generation smoke（确定 LLM 选择后再做）
6. **论文润色**: 补充 3.1-3.7 中的修改建议

完成 Task33.1-33.4 后即可进入正式投稿准备阶段。

---

*审阅日期: 2026-05-25*
