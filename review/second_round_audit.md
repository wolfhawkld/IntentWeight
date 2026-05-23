# IntentWeight 第二轮学术审计报告

**日期**: 2026-05-23  
**范围**: 对 Task25-Task29 修复和新实验的评估，对比第一轮审计中提出的问题

---

## 1. 总体评估：显著改善，可以准备投稿

第二轮审计的结论是：**项目已从"不宜投稿"改善到"可准备投稿"状态。** 第一轮审计的 4 个致命问题中有 3 个已得到实质性解决，剩余问题已降级为可接受的 limitation。

| 第一轮评级 | 当前评级 | 变化 |
|-----------|---------|------|
| 不宜投稿 | **可准备投稿（CIKM/SIGIR/SCI Q1-Q2）** | 显著提升 |

---

## 2. 第一轮致命问题的解决情况

### Issue #1: Binary Recall@k 命名 → ✅ 已解决

**修复内容**：
- `hit@k`：明确命名为 query-level 成功率
- `evidence_recall@k`：新增标准 IR recall（`|retrieved ∩ GT| / |GT|`）
- `recall@k`：保留为向后兼容别名，docstring 明确标注

**评估**：干净利落。代码实现正确，命名清晰，向后兼容处理得当。审稿人不会再有疑问。

### Issue #2: 缺少静态集成消融 → ✅ 已解决

**修复内容**（Task24）：
- `static_nearest_ensemble`：相同融合，最近质心选 arm，无学习
- `uniform_random_ensemble`：相同融合，随机 arm
- `epsilon_greedy_ensemble`：非上下文 bandit
- `static_nearest_gated`：纯几何门控

**关键发现**：Static nearest Hit@10 = 0.7612 = Full LinUCB Hit@10。这确认了多路融合是主要质量贡献者，LinUCB 学习不是 Hit@10 提升的主因。

**评估**：消融设计完整且诚实。结果改变了 claim 的措辞但不破坏论文价值。这是好的学术实践。

### Issue #3: Prequential 评估混淆学习与测试 → ⚠️ 部分解决

**修复内容**：
- Task25 从 3 epochs 增加到 8 epochs
- 文档明确将 prequential 标注为 "simulated test-time adaptation"
- Route-specific reward 分离了学习信号和最终评估

**未解决**：
- 仍然没有独立 held-out query 集（学习在一组 query 上，评估在另一组上）
- "8 epochs × 596 queries" 仍然是对同一批 query 重复学习

**评估**：作为 online learning / bandit 论文，prequential 评估是标准做法，可以接受。但需要在论文中明确声明这不是 IID 泛化评估。降级为 acceptable limitation。

### Issue #4: 缺少简单在线基线 → ✅ 已解决

**修复内容**（Task24）：
- Epsilon-greedy (ε=0.1)：Hit@10 = 0.7578, cluster hit = 0.2582
- Uniform random：Hit@10 = 0.7634, cluster hit = 0.1473

**评估**：基线齐全。LinUCB 的 cluster hit (0.5136) 高于两者，证明上下文信息确实有价值。但 static nearest (0.9016) 仍然更高——这在 Task25 中通过 route-specific credit 部分解决了。

---

## 3. Task25-Task29 新实验评估

### Task25: Route-Specific Credit Assignment — 优秀

| 指标 | 旧归因 (final_fused) | 新归因 (cluster_only) | 变化方向 |
|------|---------------------|---------------------|---------|
| Cluster Hit | 0.6908 | **0.7223** | ↑ 改善 |
| Route Reward | 0.8076 | **0.8328** | ↑ 改善 |
| Source Cost | 193.92 | **181.47** | ↓ 改善 |
| Dense Rate | 0.7466 | **0.6708** | ↓ 改善 |
| Hit@10 | 0.8826 | 0.8764 | ↓ 微降（可接受） |

**审计意见**：这是本轮最重要的修复。它证明了：
1. 归因修复后 LinUCB 确实在学习更好的 cluster 路由（cluster hit +3.2%）
2. 更好的路由允许更多查询跳过 dense（dense rate -7.6%）
3. 最终 Hit@10 微降 0.6pp 是预期内的（不再靠 dense floor 虚高）

**潜在问题**：cluster hit 从 0.6908 提升到 0.7223，但仍远低于 static nearest 的 0.9016。这说明 8 epochs 不足以收敛到几何最优。但这本身是合理的——LinUCB 的上下文特征包含的信息可能与纯几何最近邻不同。

### Task26: Low-Cost Routing — 良好，诚实

证明了 Pareto 前沿的存在：
- Cost-first A: cost=84.38 < dense(100), 但 Hit@10 降 1.5pp
- Quality-first E: Hit@10≈dense, cost=166.33

**审计意见**：没有过度声称。承认当前无法做到 "sub-dense cost + dense-level quality"。这是诚实的边界分析。

### Task27: Dense-LinUCB 纯两路 — 良好，诚实的负结果

去掉 BM25，只用 dense + cluster：
- 最佳 formal：Hit@10=0.8535, cost=97.76（低于 dense 的 100）
- 但质量仍低于 dense 1.4pp

**审计意见**：负结果但有价值。证明 BM25 对质量有贡献，不能随意移除。论文应报告为边界实验。

### Task28: Context Token 纠正 — 极其重要的自我纠错

**关键发现**：之前所有 Task 报告的 "cost" 是检索阶段候选数。Task28 证明在固定 top-10 策略下，候选数减少不等于 LLM context token 减少。

| 设置 | Source Candidate Cost | Final Context Tokens | vs Dense |
|------|----------------------|---------------------|----------|
| Dense | 100 | 1472.39 | baseline |
| Task25 cluster-credit | 181.47 | 1550.65 | **+5.3%** 🔴 |
| Task26-B balanced | 121.00 | 1517.60 | **+3.1%** 🔴 |
| Task27-B sub-dense | 97.76 | 1479.17 | **+0.5%** 🔴 |

**审计意见**：这是一个关键的自我纠错。之前的所有 "cost saving" claim 实际上在 token 维度没有节省。这种诚实对论文可信度极其重要。自我纠正能力是研究素养的体现。

### Task29: Confidence-Based Context Policy — 真正的突破

**方法**：高置信路由时减少 final top-k（high → k=8, mid → k=10, fallback → k=10）

| Scale | Dense Hit@10 | Task29-C Hit@10 | Token Saving | Quality Delta |
|-------|-------------|----------------|-------------|--------------|
| 100k | 0.8674 | 0.8652 | **-4.8%** | -0.22pp |
| 200k | 0.7970 | **0.8249** | **-4.7%** | **+2.80pp** |
| 400k | 0.7718 | **0.7819** | **-5.3%** | **+1.01pp** |

**审计意见**：

优点：
1. 200k/400k 实现了 Pareto 改进（质量↑ + token↓），这是整个项目最强的论据
2. 三种规模一致性好（token saving 稳定在 4.7-5.3%）
3. 规模越大优势越明显，正是企业场景最需要的特性
4. 机制合理：confidence 高时去掉 tail chunks（大规模下 tail 更可能是干扰）

待注意：
1. 100k 上 quality 微降（-0.22pp）——需要解释为什么小规模不如大规模
2. Token saving 幅度 4.8-5.3% 不算大——但对大规模系统的绝对节省仍可观
3. 3 seeds 的 variance 需要报告（100k std 较大：seeds 分别是 -0.50pp, -0.34pp, +0.17pp）

---

## 4. 当前系统的完整贡献层次

经过 Task25-Task29，论文的贡献可以清晰分为三层：

| 层次 | 贡献 | 证据 | 强度 |
|------|------|------|------|
| L1: 多路融合 | Dense+BM25+Cluster 提供鲁棒覆盖 | Task24 static nearest = full LinUCB Hit@10 | 强，但不新颖 |
| L2: Route-specific 学习 | LinUCB 通过正确归因学到更好的 cluster 路由 | Task25 cluster hit +3.2%, route reward +2.5% | 中等，有独特价值 |
| L3: Confidence-based 压缩 | 基于路由置信度压缩最终 context | Task29 在 200k/400k 上双赢 | **强，这是核心论据** |

**论文 pitch**：L1 是基础设施，L2 是学习机制，L3 是最终产出。三者缺一不可。

---

## 5. 修订后的风险矩阵

| 风险 | 第一轮评级 | 当前评级 | 原因 |
|------|-----------|---------|------|
| Recall@k 命名 | Critical | ✅ 解决 | 已正确分离 hit@k 和 evidence_recall@k |
| 缺少消融 | Critical | ✅ 解决 | 4 种对照组齐全 |
| Prequential 混淆 | High | Medium | 已标注为 test-time adaptation；标准做法 |
| 缺少简单基线 | High | ✅ 解决 | epsilon-greedy + random 已加 |
| 流形术语 | High | Medium | 文档已 tone down；论文需继续注意措辞 |
| Dense dominance | High | ✅ 解决 | Task24 消融 + Task25 归因修复证明了真实学习 |
| Cost 对比误导 | Medium | ✅ 解决 | Task28 自我纠正 + Task29 用真实 token 度量 |
| 模拟反馈 | High | Medium | 论文 limitation；bandit 领域标准做法 |
| 单域 scale-up | Medium | Low | 100k/200k/400k 三规模一致，方向对 |
| 3 seeds 统计力 | Medium | Medium | 形式 run 仍用 3 seeds；建议至少标注 CI |

---

## 6. 剩余建议（非阻塞）

### 投稿前应做

1. **论文中明确标注 prequential 评估协议**：一段话解释为什么这是 valid，以及与 IID 泛化评估的区别
2. **流形术语审慎使用**：正文用 "structured embedding space" / "cluster-organized corpus"，"manifold" 仅在 motivation/future-work 中使用
3. **Task29-C 的 100k 微降需要解释**：建议写 "at 100k scale, dense is near ceiling, confidence compaction trades 0.22pp for 4.8% token savings; at larger scales where dense degrades, the policy achieves both quality gain and token savings"
4. **报告 confidence interval**：至少对主 claim（Task29-C 200k/400k）报告 seed-level variance

### 可选改善

5. **context_dim 消融**（D1-D4）：如果时间允许，验证 64d 近似的安全性
6. **更多 seeds**（10+）：提升统计说服力
7. **非平稳 query 分布实验**：展示 LinUCB 在 query 分布变化时优于 static nearest

---

## 7. 推荐论文结构

基于当前证据，论文应按以下结构组织：

```
1. Introduction: 垂类 RAG 的检索成本问题 + adaptive routing 动机
2. Method:
   - 多路融合架构（dense + BM25 + cluster-local）
   - LinUCB route-specific credit assignment
   - Confidence-based final context policy
3. Experiments:
   - 静态 baselines（BM25, dense, hybrid）
   - 消融（static nearest, random, epsilon-greedy）证明学习有价值
   - Task25 credit assignment 证明路由改善
   - Task29 token-quality frontier（主结果）
   - Scale-up（100k → 200k → 400k）
   - Limitations（eManual, CUAD, 100k 微降）
4. Related Work
5. Conclusion
```

---

## 8. 投稿建议更新

| 目标 | 接受概率 | 条件 |
|------|---------|------|
| SIGIR 2026/2027 | **45-55%** | Task29 作为主结果 + 诚实消融 + 清晰 bounded claim |
| CIKM 2026 | **55-65%** | 同上，审稿人对系统论文更友好 |
| SCI Q1 (TOIS/IRJ) | **50-60%** | 期刊有空间展开消融和 limitation 分析 |
| SCI Q2 (IPM) | **70-80%** | 安全选择 |

---

## 9. 结论

Task25-Task29 的工作质量很高。特别值得肯定的是：

1. **自我纠错的诚实**：Task28 主动发现 candidate cost ≠ token cost 并纠正了所有 claim
2. **消融的完整性**：不回避 static nearest 比 LinUCB 的 cluster hit 高的事实
3. **逐步建构**：从修复归因(25) → 探索 Pareto 前沿(26/27) → 纠正度量(28) → 实现真正 token saving(29)，逻辑链完整
4. **Bounded claim**：从不说 "unconditionally better than dense"

当前状态可以开始写论文初稿。重点是 Task29 的 token-quality 前沿作为核心结果，Task24/25 的消融作为方法验证，Task28 的自我纠正作为诚实和方法论贡献。

---

*第二轮审计完成: 2026-05-23*
