# LinUCB 强化学习优化方向分析
# LinUCB Reinforcement Learning Optimization Analysis

**日期 / Date**: 2026-04-16
**背景 / Background**: 分析当前 LinUCB Contextual Bandit 方案从 RLHF/RL 范式角度的可优化方向

---

## 当前 RL 框架
## Current RL Framework

当前系统本质上是一个 **Contextual Bandit**（上下文赌博机），是 RL 的简化形态 — 单步决策，无状态转移。

```
State:   query embedding (64d PCA)        ← 偏简单
Action:  选择 top-k 聚类 (15 arms)        ← OK
Reward:  like=1.0 / dislike=0.0 / 关键词   ← 偏粗糙
Policy:  LinUCB (线性 UCB)                 ← 偏简单
Horizon: 单步（每次查询独立）               ← 没建模会话
```

核心公式：
```
UCB_score = θᵀx + α√(xᵀA⁻¹x)
更新: A ← A + xxᵀ, b ← b + rx
```

参考：Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article Recommendation"

---

## 优化方向（按性价比排序）
## Optimization Directions (by ROI)

### 1. 奖励模型 (Reward Model) — 最大收益点
### 1. Reward Model — Highest Impact

**当前问题：**
奖励信号是手工规则（like=1, dislike=0, 关键词匹配），粒度粗，无法理解细微反馈。

**RLHF 方案：**
训练一个 BERT Reward Model，输入 (query, answer, user_followup)，输出预测的用户满意度 [0, 1]。

**模型本质是监督学习（回归），不是 RL 训练。** 叫"Reward Model"是因为其输出被用作 LinUCB 的 reward 信号。
**This is supervised learning (regression), not RL training.** It's called "Reward Model" because the output is used as the reward signal for LinUCB.

**具体架构 / Architecture：**

```
输入: [CLS] query [SEP] answer [SEP] user_followup [SEP]
       ↓
  BERT-base-chinese (110M)
       ↓
  [CLS] token → Linear(768, 1) → Sigmoid → [0, 1]
```

- max_length=512（输入包含 answer 文本，需要更长上下文）
- 显存需求极低：L20 × 0.1 卡（4.8GB）即可训练

**对比（含隐式信号交叉验证场景）：**
**Comparison (including implicit signal cross-validation):**

| 场景 | 当前规则 | Reward Model |
|--|---------|-------------|
| "这个回答还行但不够全面" | 中性 (0.5) | ~0.35（偏负面） |
| "谢谢，正好需要这个" | 中性 (0.5) | ~0.95（强正面） |
| "不是这个部门的，是LC RD的" | 负面 (-0.5) | ~0.15（精确负面） |
| **点赞但只看了 2 秒** | **1.0（按按钮算）** | **~0.4（怀疑误点）** |

最后一行是关键进步：RM 能在模型层面交叉验证显式与隐式信号，而非依赖手工权重融合。
The last row is the key advance: RM can cross-validate explicit vs implicit signals at the model level, rather than relying on hand-crafted weight fusion.

**数据需求：** 200+ 条带反馈的真实对话
**算力需求：** L20 训练 BERT-base，几小时
**优先级：** ⭐⭐⭐ 中期（等数据积累）

---

### 2. 更丰富的 State 表征
### 2. Richer State Representation

**当前问题：**
Context 只有 query embedding (64d)，LinUCB 无法区分"同一查询在不同上下文中的不同意图"。

**优化方案：**
扩展 context 特征向量：

| 特征 | 维度 | 来源 | 作用 |
|------|------|------|------|
| query embedding (PCA) | 64d | 已有 | 语义信息 |
| 用户历史偏好 | 15d | 各聚类的历史 reward 均值 | 个性化 |
| 会话上下文 | 64d | 对话历史 embedding 均值 | 多轮理解 |
| 查询类型 | 3d | Agent action one-hot | 意图区分 |
| **合计** | **~146d** | | |

**改动量：** 小（修改 LinUCB context 构建逻辑）
**优先级：** ⭐⭐⭐ 短期可做

---

### 3. 探索策略优化
### 3. Exploration Strategy Optimization

**当前问题：**
α=1.0 固定不变，初期和后期使用同样的探索力度。

**优化方案：**

**衰减探索：**
```python
α(t) = α_0 / (1 + decay_rate * total_feedback)
# 初始 α=1.0，随反馈积累逐步降低
# 早期多探索，后期多利用
```

**自适应探索：**
```python
# 模糊查询（短、含"什么"、"怎么"等）→ 高 α（多探索）
# 精确查询（长、含具体实体）→ 低 α（多利用）
α_query = base_α * (1 + ambiguity_score)
```

**改动量：** 极小（几行代码）
**优先级：** ⭐⭐⭐ 短期可做

---

### 4. 从单步 Bandit 到多步 RL
### 4. From Single-step Bandit to Multi-step RL

**当前问题：**
每次查询独立决策，无法规划多步策略（如先澄清再搜索）。

**优化方案：**
建模为 MDP（马尔可夫决策过程）：

```
State_t     → Action_t        → Reward_t → State_{t+1}
(查询+历史)   (搜索/澄清/深入)   (反馈)     (追问+更新后的历史)
```

- 会话结束时的总满意度作为 delayed reward
- 用 Q-learning 或 PPO 优化策略
- Agent 可以学会"先问清楚再搜索"比"直接搜索"效果更好

**数据需求：** 上千条完整会话
**复杂度：** 高（需要重新设计 state/action 空间）
**优先级：** ⭐ 长期目标

---

### 5. DPO 偏好学习
### 5. DPO Preference Learning

**当前问题：**
标量 reward (0~1) 信息量有限，用户有时难以给出绝对评分。

**RLHF/DPO 方案：**
收集偏好对而非标量分数：
- 展示两个检索结果，用户选更好的
- 用 DPO (Direct Preference Optimization) 训练
- 比标量 reward 更稳定，用户决策负担更低

**参考：** Rafailov et al. (2023) "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"

**改动量：** 大（需要修改 UI 交互方式 + 训练流程）
**优先级：** ⭐ 长期目标

---

### 6. 离线 RL (Off-Policy Learning)
### 6. Offline RL (Off-Policy Learning)

**当前问题：**
LinUCB 只能从在线交互中学习，SQLite 中的历史数据没有被充分利用。

**优化方案：**
用历史对话数据做离线策略优化：
- Conservative Q-Learning (CQL) 或 Batch Constrained Q-learning (BCQ)
- 在不产生新交互的情况下，从已有数据中学习更好的策略
- 每天批量训练，白天在线部署

**数据需求：** 几百条带 reward 的交互记录
**优先级：** ⭐⭐ 中期

---

## 实施路线图
## Implementation Roadmap

```
短期（立即可做，代码改动小）:
├── 探索衰减策略 (α 随反馈积累递减)
└── 丰富 State 特征 (64d → ~146d)

中期（需积累几百条对话）:
├── BERT Reward Model (L20 训练)
└── 离线 RL (利用 SQLite 历史数据)

长期（需上千条数据 + UI 改造）:
├── 多步 RL (MDP 建模完整会话)
└── DPO 偏好学习 (偏好对收集 + 训练)
```

---

## 与 IntentWeight 研究项目的对应关系
## Mapping to IntentWeight Research

| 研究验证 | 当前系统实现 | RL 优化方向 |
|---------|------------|-----------|
| LinUCB 算法 (Phase 1C) | ✅ 文件级聚类 arms | → Reward Model + 丰富 State |
| 反馈信号验证 (Phase 1C) | ✅ 按钮 + 上下文奖励 | → BERT Reward Model |
| 冷启动先验 (Phase 1F) | ✅ 关键词聚类先验 | → 离线 RL 热启动 |
| 言语行为分类 (Phase 1A) | ✅ ReAct Agent 替代 | → BERT 分类器替代 LLM |
| 多轮对话 | ✅ chat_history 传递 | → 多步 RL (MDP) |

---

*本文档基于 2026-04-16 的技术讨论整理*
*参考：IntentWeight 研究项目 (LinUCB Contextual Bandit)*
