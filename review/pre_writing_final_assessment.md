# IntentWeight 投稿前终审 Assessment

**日期**: 2026-05-27  
**审阅范围**: pre_validation 分支 全部 paper/draft/ + paper/experiments/ + 核心实验代码  
**对应提交**: 44c500e (task33.7 完成后)  
**审阅方法**: 文档逻辑审查 + 代码级验证 + 数值独立复现

---

## 一、整体判断

**Evidence chain 闭合，bounded claim 自洽，可以开始正式写作。**

所有发现均为写作层面需要 preempt 的问题，无阻塞性逻辑缺陷或数据错误。

---

## 二、第一轮审查发现（9 项）

### [高] 1. 400k Token Saving CI 异常宽

**事实**：三个 seed 的 token saving 分别是 ~3.15%, ~5.47%, ~7.34%。标准差 2.10%，95% CI = [0.11%, 10.53%]。

**对比**：
- 100k: std=0.78%, CI=[2.89%, 6.77%]
- 200k: std=0.32%, CI=[3.89%, 5.48%]
- 638k: std=0.25%, CI=[4.24%, 5.48%]
- **400k: std=2.10%, CI=[0.11%, 10.53%]** ← 异常

**根因**: KMeans 初始化在 400k 规模下对 context compaction 的影响比其他 scale 更大。同一 n_clusters=32 在 400k（~12.5k chunks/cluster）可能处于某种过渡区间。

**建议**：
- 论文中 acknowledge 400k 的更高方差
- 如时间允许，补 2 个 seed 把 400k 升到 5-seed
- 解释可能原因："at 400k scale, KMeans arm initialization produces more variable cluster quality across seeds"

---

### [高] 2. Task29-C "conservative" 标签缺乏系统性选择依据

**事实**：Task29-C 的 final context policy 是 `high_k=8, mid_k=10, fallback_k=10`。选择过程：
- Task29-A: high_k=5, mid_k=7 → 32% saving, -3.36pp Hit
- Task29-B: high_k=7, mid_k=9 → 14% saving, -1.85pp Hit
- Task29-C: high_k=8, mid_k=10 → 5% saving, -0.22pp Hit

三个配置只在 100k smoke run 上评估，然后 C 被选中跑了全部 4 个 scale 的 formal 实验。

**风险**：审稿人可能认为这是 cherry-picking（选了最接近 dense 的配置来声称 "near-dense"）。

**建议**：
- 用 Task29-A/B/C frontier 图表展示这是 Pareto 曲线上的一个 operating point
- 论文中明确："We select the conservative end of the frontier (Task29-C) as the main result because it prioritizes quality preservation over maximum token saving"
- 补充论述：aggressive 配置（A/B）展示了方法的上限，conservative 配置（C）展示了安全性

---

### [中高] 3. "Above-dense on 200k/400k/638k" 的 claim 需要 CI 限定

**事实**：
- 200k: +2.80pp, CI [+0.82, +4.77] — **不含零，safe**
- 400k: +1.01pp, CI [-0.10, +2.11] — **CI 几乎触及零**
- 638k: +1.85pp, CI [-0.36, +4.07] — **CI 包含零**

**建议**：
- 论文措辞改为 "mean Hit@10 is above dense on 200k, 400k, and 638k"（事实陈述）
- 不要使用 "significantly exceeds"
- 在 discussion 中："with three seeds, the improvement is directionally consistent but CI-level confirmation is only available at 200k"
- 当前文档已经在做这个，但 abstract/introduction 的 "exceeds dense" 措辞需要收紧

---

### [中] 4. Ablation table 中 "No feedback" 行 Hit@10 最高，可能困惑审稿人

**事实**：Task33.3 ablation 中：
- No feedback gated routing: Hit@10 = **0.8826**（最高）
- Trust-weighted feedback: Hit@10 = 0.8641
- Task29-C: Hit@10 = 0.8652

原因：No feedback → dense_rate=1.0 → 完全回退到 dense，其 Hit@10 实际上就是 full multi-route baseline。

**风险**：审稿人只看表格可能得出 "feedback 让质量变差了" 的结论。

**建议**：
- 表格 caption 加注："No-feedback routing defaults to full dense fallback (dense rate=1.0); its high Hit@10 reflects dense coverage, not learned route control"
- 强调 no-feedback 行的 token ratio=1.0603（比 dense 还高），说明无 feedback 时不节省任何 token
- 对比维度不只是 Hit@10，更重要的是 token ratio + route quality

---

### [中] 5. evidence_recall@10 在所有 IntentWeight 配置下低于 dense

**事实**：
| 配置 | evidence_recall@10 |
|------|-------------------|
| Dense | 0.7026 |
| Task29-C | 0.6737 |
| Trust mild | 0.6795 |
| Oracle | 0.6768 |

IntentWeight 的 context compaction 提高（或持平）Hit@10，但降低了多证据覆盖率。

**解释**：这是 expected tradeoff — Hit@10 只要求至少一个 GT chunk 在 top-k，而 evidence_recall 要求所有 GT chunk 都被召回。k=8 的压缩必然减少多证据覆盖。

**建议**：
- 明确论文 framing："The conservative policy optimizes for query-level hit (at least one relevant chunk) rather than evidence completeness"
- 在 limitations 中："For applications requiring complete evidence collection (legal, medical), a more conservative compaction policy or no compaction may be preferred"

---

### [中] 6. Task33.5 LLM smoke 使用 DeepSeek-V4-Flash 单一 judge

**事实**：`deepseek-v4-flash` with thinking enabled，60 queries，LLM-as-judge。

**风险**：
- 单一 judge 模型可能有系统性偏差
- DeepSeek 不是学术界最常用的 benchmark 模型

**缓解**：结果本身很好（tie=32, dense=14, treatment=14），且定位为 sanity check。

**建议**：
- Frame 为 "cost-efficient sanity check using a reasoning-capable model"
- Limitations 中 acknowledge single-model judge limitation
- 不需要重跑，但论文中不要过度依赖此结果

---

### [低中] 7. Multi-QA MiniLM (Task33.1a) token saving 只有 3.35%，低于主实验 4.83%

**事实**：
- all-MiniLM: 4.83% saving, Hit@10 = 0.8652 vs dense 0.8674
- multi-qa-MiniLM: 3.35% saving, Hit@10 = 0.8853 vs dense 0.8809

**解释**：更强的 encoder → 更强的 dense baseline → IntentWeight 的 margin 自然更小。

**建议**：
- Frame 为 "method remains functional under a stronger encoder"
- 不要回避这个下降，而是把它解释为 "stronger baselines leave less room for improvement, but the mechanism still works"

---

### [低] 8. 只在 LoTTE technology/search 一个 domain 有正面大规模结果

**事实**：LoTTE 有 5 个 domain（writing, recreation, science, lifestyle, technology），只用了 technology。eManual/CUAD 是 failure cases。

**建议**：
- Limitations 中 acknowledge
- Future work 中提及 cross-domain validation
- 如投稿前有时间，跑一个 LoTTE science/search 100k smoke 会显著加强

---

### [低] 9. "Piecewise relevance-manifold assumption" 术语对读者不友好

**建议**：在 abstract 首次出现时加一句直觉解释：
> "i.e., that query-document relevance in a vertical domain exhibits exploitable local cluster structure"

---

## 三、第二轮深度代码审查发现（5 项）

### [中高] 10. `final_context_mid_k=10` 是 no-op — "compact_context_rate" 指标具有误导性

**事实**：Task29-C 参数：
```
final_context_high_k: 8   ← 实际压缩（k 从 10 降到 8）
final_context_mid_k: 10   ← NO-OP（k 保持 10，和 baseline 相同）
```

系统报告的指标：
- `compact_context_rate: 0.7243` — 包含了 mid_confidence 的 39.5%
- `high_confidence_compact_rate: 0.3292` — 实际压缩的比例

这意味着 72.4% 的 "compaction" 中有 54.6% 什么都没做（mid_k=10 = baseline top-10）。

**验证**：
```
avg_final_context_k = 0.3292 × 8 + 0.6708 × 10 = 9.34 ✓（与报告一致）
```

**风险**：论文如果引用 "72% compact rate" 但只有 4.83% token saving，审稿人会困惑数字不匹配。

**建议**：
- 论文中只报告 **effective compaction rate = 33%**（high-confidence queries 占比）
- 或明确说明："mid-confidence queries retain full top-10 as a conservative safety margin"
- 把 mid_k=10 定位为 "two-tier design with a safety margin"，不要称其为 compaction

---

### [中] 11. Multi-epoch 语义需要更清晰的论文陈述

**事实**：实验跑 8 epochs，每 epoch 596 queries 随机 shuffle 后逐一处理。

关键动态：
| 指标 | Epoch 1 | Epoch 8 | 变化 |
|------|---------|---------|------|
| Hit@10 | ~0.8624 | 0.8652 | +0.28pp（微小）|
| Route true reward | ~0.39 | 0.83 | +0.44（巨大）|
| Confidence | ~0.40 | 0.70 | +0.30 |
| Lite route rate | ~14% | 86% | +72pp |

**含义**：到 epoch 8 时，每个 query 的 GT-derived feedback 已被用于更新策略 7 次。策略"知道"每个 query 的历史反馈模式。

**最终报告的 Hit@10 和 token metrics 都来自 epoch-8 的 rankings**（代码 `rankings[qid] = ranking` 每 epoch 覆写，最终调用 `evaluate_rankings` 评估最后一次存储的结果）。

**关键辩护点**：Hit@10 跨 epoch 几乎不变（+0.28pp），说明 multi-epoch 学到的是"如何更高效地路由"，不是"如何对 test queries 过拟合质量"。

**风险**：审稿人可能说 "8 passes over 596 test queries with GT feedback = test-set memorization"。

**建议**：
- Protocol section 中明确 8 epochs 的含义
- 强调 Hit@10 的 epoch 稳定性（+0.28pp across 8 epochs）
- 补一句："Multi-epoch adaptation improves route efficiency (lite route rate: 14%→86%) without meaningfully changing retrieval quality (Hit@10 gain < 0.3pp), indicating that the policy learns routing efficiency rather than memorizing query answers"
- 考虑报告 epoch-1 metrics 作为 "cold-start" reference point

---

### [低中] 12. `drift_threshold=1.0` 实际上禁用了 semantic drift fallback

**事实**：
- 平均 semantic drift = 0.65
- drift_threshold = 1.0（cosine-distance 最大值就是 1.0）
- fallback_high_drift_rate = 1.3%（几乎从不触发）

方法章节描述了 "confidence AND semantic drift" 双条件 gating，但实验中 routing 决策是 **纯 confidence-based**。

**建议**：
- 在论文中把 drift 定位为 "deployment safety guard"（defensive feature, rarely triggered on this benchmark）
- Discussion 中 acknowledge："On LoTTE, semantic drift rarely exceeds the fallback threshold; routing decisions are primarily confidence-driven. In more heterogeneous query distributions, drift-based fallback would become more active."
- 或者在 ablation 中加一行 drift_threshold=0.7 的结果

---

### [低中] 13. "Hybrid lite" 仍做 100-depth dense 检索

**事实**：
```
dense_lite_depth: 100   ← 与 full fallback 相同
dense_lite_floor_k: 5   ← 与 full fallback 相同
```

"Hybrid lite" 的 "lite" 仅体现在 fusion 权重翻转：
- Full: dense_weight=2.0, cluster_weight=0.8
- Hybrid lite: dense_lite_weight=0.8, cluster_primary_weight=2.0

实际 dense 计算量没有减少。只有 `linucb_primary`（dense_depth=0）真正跳过 dense retrieval。

**建议**：
- 论文中准确表述："hybrid_lite reduces dense influence in the final fusion ranking while retaining dense candidates as a safety net"
- 不要说 "hybrid_lite reduces dense computation"
- Dense computation saving 只在 linucb_primary 查询上实现

---

### [低] 14. `n_clusters=32` 跨所有 scale 使用，未解释

**事实**：
| Scale | Chunks per cluster |
|-------|-------------------|
| 100k | ~3,166 |
| 200k | ~6,281 |
| 400k | ~12,521 |
| 638k | ~19,953 |

**建议**：
- 解释为 "fixed arm count ensures comparable LinUCB state across scales and simplifies cross-scale comparison"
- 在 future work 中提及 scale-adaptive cluster count

---

## 四、逻辑一致性验证 — 无问题区域

| 维度 | 验证方法 | 状态 |
|------|---------|------|
| Hit@10 数字跨文件一致 | 交叉对比 draft/experiments/task31/task33.7 | ✅ |
| Token saving 计算 | 独立从 CSV 重算 CI | ✅ |
| 三层成本分离 | 代码 + 文档一致 | ✅ |
| Metric 定义一致 | retrieval_metrics.py 代码审查 | ✅ |
| Prequential 无 within-epoch leakage | 代码审查确认 ranking 在 feedback 前存储 | ✅ |
| LLM smoke 原始数据 | 独立从 JSONL 重算 winner counts 和 means | ✅ |
| Seed CI 数学 | 独立验证 t(2, 0.025)=4.303 | ✅ |
| Token metrics 与 Hit@10 来源一致 | 确认均来自 epoch-8 final rankings | ✅ |
| context_chunks@10 与 avg_final_context_k 关系 | epoch-8 ~9.0 vs all-epoch 9.34，一致 | ✅ |
| Claim boundary 统一 | 所有文档使用相同 bounded claim | ✅ |

---

## 五、完整问题汇总表

| # | 问题 | 严重程度 | 类型 | 建议处理 |
|---|------|---------|------|---------|
| 1 | 400k token saving CI 异常宽 | 高 | 统计 | Acknowledge + 可选补 seed |
| 2 | Task29-C 选择缺乏显式 rationale | 高 | 方法论 | Pareto frontier 图 + 文字说明 |
| 3 | "Above-dense" claim 需 CI 限定 | 中高 | 统计 | 收紧措辞为 "mean above dense" |
| 4 | No-feedback 行 Hit@10 最高 | 中 | 展示 | 表格 caption 解释 |
| 5 | evidence_recall 下降 | 中 | Tradeoff | 在 limitations 中定位为 expected |
| 6 | 单一 LLM judge | 中 | 方法论 | Frame 为 sanity check |
| 7 | Multi-QA token saving 下降 | 低中 | 鲁棒性 | 解释为 stronger baseline effect |
| 8 | 单一 domain | 低 | 外部效度 | Limitations + future work |
| 9 | Manifold 术语不友好 | 低 | 写作 | 加直觉解释 |
| 10 | mid_k=10 no-op + compact rate 误导 | 中高 | 方法/报告 | 只报告 effective compaction |
| 11 | Multi-epoch 含义未充分披露 | 中 | Protocol | 补充 epoch 动态说明 |
| 12 | drift_threshold 实际禁用 | 低中 | 方法/实验 | 定位为 deployment guard |
| 13 | Hybrid lite 仍做全量 dense | 低中 | 方法描述 | 准确表述 lite 含义 |
| 14 | n_clusters=32 未解释 | 低 | 方法论 | 补一句 justification |

---

## 六、投稿前行动优先级

### 必做（影响 claim 可信度）

1. **写作时 preempt 400k CI**（或补 2 seeds）
2. **Task29-C 选择显式 frame 为 Pareto + conservative decision**
3. **收紧 "above dense" 措辞**：mean above, CI confirmation only at 200k
4. **只报告 effective compaction rate（~33%）**，不用 misleading 的 72%
5. **Protocol section 补充 multi-epoch 含义** + epoch stability evidence

### 建议做（加强论文防御力）

6. Ablation table caption 解释 no-feedback 行
7. Limitations 中 address evidence_recall 下降
8. Abstract 中给 manifold 术语加直觉解释
9. Discussion 中 acknowledge drift 在 LoTTE 上不活跃
10. 准确描述 hybrid_lite 的 "lite" 含义

### 不阻塞投稿

11. LoTTE 第二个 domain（science/search）
12. Nomic/BGE encoder
13. KMeans k / epoch sensitivity
14. 400k 补 seed
15. drift_threshold 敏感性实验

---

## 七、最终结论

**投稿就绪度：完成上述 "必做" 5 项写作调整后即可投稿。**

核心 claim 安全：
> IntentWeight 是一个 feedback-driven adaptive retrieval controller。在 LoTTE technology/search 100k-638k 上，conservative 策略在保持 dense-level Hit@10 的同时，将 final retrieved context tokens 降低约 4.7-5.3%。Dense 仍是必要的 recall floor。

这个 bounded claim 经过代码级验证，无逻辑漏洞，无数据错误。所有发现都是写作层面可以 address 的 framing/disclosure 问题，不动摇实验结论本身。

---

*审阅完成日期: 2026-05-27*  
*审阅深度: 文档逻辑 + 代码审查 + 数值独立验证*
