# LinUCB Credit Assignment 与 Cost Gating 机制分析

**日期**: 2026-05-22  
**背景**: Task24 消融实验揭示 LinUCB 的 arm 选择质量(0.5136)远低于 static nearest centroid(0.9016)，但 gated LinUCB 仍然实现了 cost saving。本文分析 cost saving 的真正来源及修复路径。

---

## 1. 核心发现：Cost Saving 来自 Confidence 膨胀，非真正学到路由策略

### 因果链

```
LinUCB 选了 arm（质量不高，cluster_hit=0.5136）
    ↓
dense_floor_k=5 保护了最终 top-10 的质量
    ↓
reward 基于最终 ranking 计算（包含 dense floor 贡献）→ reward 较高
    ↓
高 reward 更新 LinUCB 的 A/b → θ^T x 价值估计膨胀
    ↓
maturity = min(1.0, mean_pulls / 8.0) 随交互次数饱和到 1.0
    ↓
confidence = maturity × (0.85 × bounded_value + 0.15 × margin) → 持续增长
    ↓
confidence >= threshold → 门控打开 → 跳过 dense → cost 下降
```

**本质**：LinUCB 把 dense floor 兜底的功劳归功于自己的 arm 选择，基于虚高信心去关闭 dense。这是一个 attribution error 的自我强化循环。

### 对比证据

| 方法 | Cluster Hit | Dense Query Rate | Hit@10 |
|------|------------|-----------------|--------|
| Static nearest (无学习) | 0.9016 | 0.9972 (几乎不敢关dense) | 0.7500 |
| LinUCB gated (有学习) | 0.4965 | 0.9146 (8.5%关闭dense) | 0.7343 |

Static nearest 虽然 arm 选得更准，但它用余弦相似度做 confidence，值通常只有 0.3-0.5（64维PCA空间），低于 high_threshold=0.65，所以几乎不敢关 dense — **这是诚实的门控**。

LinUCB 虽然 arm 选得更差，但 confidence 因 maturity 饱和 + value 膨胀而突破门槛 — **这是膨胀的门控**。

---

## 2. "RLHF 强信号能解决" — 部分正确，但需要修改

### 论点评估

| 主张 | 评估 | 原因 |
|------|------|------|
| "仅是收敛不够快" | 部分错误 | 还有 credit assignment 和线性模型表达力问题 |
| "RLHF 强信号能大幅降低副作用" | 部分对 | 但需要 route-specific reward，不是简单的最终结果 RLHF |
| "最终能节省token且不降分" | 理论上对 | 前提是修复 reward 归因 |
| "多路召回保持不关 dense" | 正确且关键 | 安全底线 |

### Credit Assignment 问题的本质

```
用户看到最终回答 → 给 "good/bad" 反馈
    ↓
但这个回答由 dense + BM25 + cluster 三路融合 + dense_floor 产出
    ↓
reward 无法区分："cluster arm 选对了" vs "dense floor 救了你"
```

即使使用真实 RLHF，用户评价的是最终输出质量，不是单条检索路径的贡献。除非 instrument route-specific feedback（让用户标注每个 chunk 来自哪条路径——实际不可行），否则归因误差持续存在。

### LinUCB 的线性局限

`θ^T x` 是线性值函数。如果"何时可以安全跳过 dense"的真正决策边界是非线性的（很可能如此——某些 query 类型+某些 cluster 组合才安全），LinUCB 永远不会收敛到最优策略。

---

## 3. 修复方案

### 方案A：Route-Specific Reward（推荐）

```python
# 当前（归因错误）：
reward = 最终融合 ranking 是否命中 GT → 全部归功于 LinUCB

# 修复后（正确归因）：
cluster_route_reward = cluster 路径单独检索 top-k 是否命中 GT
# LinUCB 只基于 cluster_route_reward 更新，不受 dense floor 影响
```

这样：
- 选错 arm → cluster 独立结果差 → reward 低 → 修正方向正确
- 选对 arm → cluster 独立结果好 → reward 高 → 强化正确选择
- Dense floor 仍然保护最终输出，但不污染学习信号

### 方案B：Confidence 基于实际 Arm 质量

```python
# 当前（结构性膨胀）：
confidence = maturity(交互次数) × value(被dense保护的估值)

# 修复后：
confidence = cluster_only_hit_rate(最近N次该arm独立检索的命中率)
```

Confidence 不再依赖交互量和估值，而是直接衡量"cluster route 独立可靠性"。

### 方案C：Dual-Reward 架构

```
final_reward → 用于评估最终系统质量（不更新 LinUCB）
route_reward → 用于更新 LinUCB 的 arm 策略
cost_reward  → 用于 cost gating 决策
```

分离学习信号，让每个组件只对自己负责的部分学习。

---

## 4. 实验验证计划

### 验证目标

证明修复 reward attribution 后，LinUCB 能否：
1. Cluster hit 从当前 0.5136 提升到接近 static nearest 的 0.9016
2. 在 cluster hit 提升后，cost gating 基于真实能力开门 → 降本不降质
3. 收敛速度在 route-specific reward 下显著加快

### 建议实验

| 实验 | 设置 | 预期结果 |
|------|------|---------|
| E1: Route-specific reward | LinUCB 更新只用 cluster 路径独立 recall | Cluster hit 应大幅提升 |
| E2: Route-specific + gating | E1 基础上开启 cost gating | 降本同时 Hit@10 不降 |
| E3: Confidence 修复 | 用 cluster 独立命中率做 confidence | 门控更保守但更准确 |
| E4: 与 static nearest gated 对比 | E2/E3 vs static nearest gated | 证明学习后优于静态 |

### 成功标准

```
修复后 LinUCB gated:
  - Cluster hit >= 0.75 (当前 0.5136，static nearest 0.9016)
  - Hit@10 >= 0.7500 (>= static nearest gated)
  - Source cost <= 250 (低于 full multi-route 300)
  - Dense query rate <= 0.92 (有意义的 cost saving)
```

---

## 5. 对论文定位的影响

### 如果修复成功

论文可以声称：
> "Route-specific credit assignment enables LinUCB to learn genuine routing quality, achieving cost reduction based on true arm reliability rather than confidence inflation."

这本身就是一个方法贡献——multi-route retrieval 中的 credit assignment。

### 如果修复后仍不优于 static nearest

说明对于静态基准测试，几何路由已经足够好。LinUCB 的价值必须重新定位为：
- 非平稳环境（query 分布变化时静态路由失效）
- 用户个性化（不同用户偏好不同检索路径）
- 长期持续优化（静态路由不会改进，学习路由可以）

这些都需要新的实验设计来验证。

---

## 6. 总结

当前 LinUCB cost gating 的 "cost saving" 是 confidence 膨胀的副产品，不是真正学到了路由策略。修复路径清晰：route-specific reward attribution。这个修复既是论文的方法贡献，也是让 LinUCB 真正有效的前提条件。

如果实验验证修复有效，论文的 claim 变得更强且更可信：
- 不再是"LinUCB 以某种方式降低了 cost"（机制不清）
- 而是"正确的 credit assignment 让 LinUCB 学到真正的路由质量，从而实现有理有据的 cost reduction"

---

*分析日期: 2026-05-22*
