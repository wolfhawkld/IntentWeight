# RL 反馈策略与用户信誉评分深度分析
# RL Feedback Strategy & User Credibility Scoring Analysis

**日期 / Date**: 2026-04-16
**背景 / Background**: 基于当前 LinUCB 实现，讨论算法选择、多维反馈融合、用户信誉防投毒、少量数据下的 RL 策略

---

## 1. 算法选择：PPO / Q-Learning / DPO vs LinUCB
## 1. Algorithm Selection

**结论：当前数据规模下 LinUCB 就是最优解，不需要换算法。**
**Conclusion: LinUCB is optimal for current data scale. No need to switch algorithms.**

| 算法 | 数据需求 | 适用场景 | 对本系统评估 |
|------|---------|---------|------------|
| **LinUCB** | 极少（第一次交互即可学习） | 单步决策 + 小离散动作空间 | **正好匹配**（15 clusters, 单步选择） |
| Q-Learning | 中等（几百 episode） | 多步决策 + 离线学习 | 未来可用于会话级策略优化 |
| PPO | 大量（持续在线数据） | 连续动作空间 + 策略优化 | **不适合** — 数据需求远超系统产出 |
| DPO | 中等（需偏好对） | 偏好学习 | 需改 UI 展示对比结果，远期考虑 |

**核心观点：真正该优化的不是算法本身，而是输入算法的信号质量（State 表征 + Reward 信号）。**

如果未来需要多步 RL：
- **Conservative Q-Learning (CQL)** 适合离线学习（从 SQLite 历史数据）
- **不推荐 PPO** — 对数据量要求太高

参考：
- LinUCB: Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article Recommendation"
- CQL: Kumar et al. (2020) "Conservative Q-Learning for Offline Reinforcement Learning"
- DPO: Rafailov et al. (2023) "Direct Preference Optimization"

---

## 2. 多维反馈信号融合
## 2. Multi-dimensional Feedback Signal Fusion

### 反馈金字塔
### Feedback Pyramid

```
         显式按钮 (最强信号，最稀疏)
           👍 / 👎
            ╱  ╲
      对话语义反馈 (丰富但需解析)
     "不对" / "很好" / "缺少XX"
          ╱      ╲
     隐式行为信号 (持续采集，需推断)
    停留时长 / 复制 / 滚动 / 二次查询
```

### 当前实现状态
### Current Implementation Status

| 信号层 | 采集 | 融入 Reward | 状态 |
|--------|------|------------|------|
| 显式按钮 | ✅ 前端已有 | ✅ like=1.0, dislike=0.0 | 完成 |
| 对话语义 | ✅ SQLite 存储 | ⚠️ 仅关键词匹配 (infer_context_reward) | 可优化 → Reward Model |
| 隐式行为 | ⚠️ 字段已预留 | ⚠️ 代码框架有但未完整接入 | 需前端埋点 |
| 结果信号 | ❌ 未采集 | ❌ | 用户是否二次查询同一主题 |

### 融合公式（扩展 IntentWeight 研究方案）
### Fusion Formula

```
R_total = w1 × S_explicit            # 按钮反馈：确定性最高
        + w2 × S_conversational       # 对话语义：追问/纠正/补充的语义分析
        + w3 × S_implicit             # 隐式行为：停留/复制/滚动
        + w4 × S_outcome              # 结果信号：是否二次查询同一主题

推荐权重：w1=0.4, w2=0.3, w3=0.2, w4=0.1
```

### 各信号详细设计
### Signal Design Details

**S_explicit（显式按钮）:**
```
like    → +1.0
dislike → 0.0
correct → 0.7  （用户手动修正，部分肯定）
无反馈  → 不参与计算（非 0.5 中性）
```

**S_conversational（对话语义）:**
- 当前：关键词匹配（"不对" → -0.5, "详细" → +0.5）
- 未来：BERT Reward Model，输入 (query, answer, followup) 输出满意度
- 这是**提升空间最大的信号层** — 包含最丰富的信息

**S_implicit（隐式行为）:**
```
停留时长：<5s → -0.3 (跳出)
         10-30s → +0.2 (认真阅读)
         30-60s → +0.4 (深度阅读)
         >60s → +0.2 (可能困惑，降分)
复制行为：+0.5 (强正信号)
滚动深度：>70% → +0.2
二次查询同主题：-0.3 (上次没解决)
```

**S_outcome（结果信号）:**
```
会话后不再追问同一主题 → +0.3 (问题已解决)
短时间内重复查询相似内容 → -0.3 (未解决)
```

---

## 3. 用户信誉评分（Anti-poisoning）
## 3. User Credibility Scoring (Anti-poisoning)

### 核心机制
### Core Mechanism

为 LinUCB 的 reward 加可信度权重：

```python
effective_reward = raw_reward × user_credibility(user_id)
```

高信誉用户的反馈权重大，低信誉用户的反馈影响被抑制。

### 信誉评分模型
### Credibility Scoring Model

```python
class UserCredibility:
    def __init__(self):
        self.score = 0.5          # 新用户默认中性
        self.feedback_count = 0
        self.consistency_rate = 0  # 反馈与多数用户一致的比率
        self.engagement_depth = 0  # 参与深度

    def update(self, feedback_aligned_with_consensus: bool):
        """
        反馈与其他用户对同一内容的评价一致 → 信誉上升
        总是与多数人相反 → 信誉下降
        """
        self.feedback_count += 1
        α = 1 / (self.feedback_count + 10)  # 衰减学习率
        target = 1.0 if feedback_aligned_with_consensus else 0.0
        self.score += α * (target - self.score)
        # 限制在 [0.1, 1.0]，不完全忽略任何用户
        self.score = max(0.1, min(1.0, self.score))
```

### 信誉评分维度
### Credibility Dimensions

| 维度 | 正面 | 负面 | 权重 |
|------|------|------|------|
| 反馈一致性 | 与多数用户评价方向一致 | 总是与多数人相反 | 40% |
| 参与深度 | 多轮深入对话、给具体建议 | 随意点踩、无实质交互 | 25% |
| 反馈结果 | 采纳后系统效果改善 | 采纳后效果变差 | 25% |
| 使用频率 | 持续使用 | 偶尔一次 | 10% |

### 实现前提
### Implementation Prerequisites

- **需要用户身份识别**：当前系统只有 session_id，没有 user_id
- 接入 Azure AD SSO 后（CLAUDE.md Phase 3 计划）自然有 user_id
- 实现：SQLite 新增 `user_scores` 表，`record_feedback` 时乘以信誉系数

### 防投毒场景
### Anti-poisoning Scenarios

| 场景 | 行为模式 | 系统响应 |
|------|---------|---------|
| 恶意用户 | 持续给好答案点踩 | 信誉下降，反馈权重被抑制 |
| 随机用户 | 无规律点赞点踩 | 一致性低，信誉趋向中性 |
| 认真用户 | 反馈与多数一致，有纠正建议 | 信誉上升，反馈权重增大 |
| 领域专家 | 反馈独到但正确（少数派对） | 短期信誉可能下降，需人工标记专家角色 |

**注意：领域专家可能是"正确的少数派"**，纯粹的一致性评分会压低他们。
解决方案：支持管理员手动设置某些用户为"可信专家"（credibility=1.0 固定）。

---

## 4. 少量数据下的 RL 策略
## 4. RL Strategy with Limited Data

### 为什么 LinUCB 已是最优选择
### Why LinUCB is Already Optimal

| 特性 | 为什么适合少量数据 |
|------|-----------------|
| 冷启动先验 | 零反馈就有合理权重（关键词聚类纯度提供初始值） |
| 线性模型 | 参数少 (A: 64×64, b: 64)，不容易过拟合 |
| UCB 探索 | 主动探索不确定的 arm，最大化信息收集效率 |
| 在线学习 | 每条反馈立即生效，不需要积累批量数据 |
| 数学保证 | 后悔值 (regret) 以 O(√T) 增长，理论最优 |

### 少量数据下可额外做的提升
### Additional Improvements for Small Data

**1. 探索衰减（几行代码）:**
```python
α(t) = α_0 / (1 + decay_rate × total_feedback)
# 早期 α=1.0 多探索，快速收集信息
# 后期 α→0.3 收敛到最优策略
```

**2. 先验注入更多来源:**
- 当前：关键词聚类纯度
- 可增加：文档标题语义、目录结构层级、文档类型（SOP/通知/表格）
- 这些元信息不需要用户反馈就能提供有意义的先验

**3. 用户信誉加权（第 3 点）:**
- 高质量反馈 × 高信誉 → 大权重更新
- 低质量反馈 × 低信誉 → 小权重更新
- 等效于用更少数据达到更好效果

**4. LLM 合成数据热启动（最独特的方案）:**

```
对每个聚类:
  1. 读取聚类内文档摘要
  2. 用 LLM 生成 50-100 个可能的用户查询
  3. 标注：该查询 → 该聚类应被选中
  4. 作为伪反馈注入 LinUCB (reward=0.8)
```

效果：系统上线前就有相当于几百条真实反馈的学习量。
成本：一次性 LLM 调用（extract_insights.py 类似流程）。
**这是"用 LLM 的知识热启动 RL"的典型范式。**

### 不同数据量下的策略路线
### Strategy Roadmap by Data Volume

```
0 条反馈：     冷启动先验 + LLM 合成热启动
1-50 条：      LinUCB 在线学习 + 探索衰减
50-200 条：    + 用户信誉评分 + 隐式信号接入
200-500 条：   + BERT Reward Model (L20)
500-1000 条：  + 离线 RL (CQL) 利用历史数据
1000+ 条：     + 多步 RL / DPO 偏好学习
```

---

## 总结：优先实施清单
## Summary: Priority Implementation List

| 优先级 | 项目 | 数据需求 | 改动量 |
|--------|------|---------|--------|
| ⭐⭐⭐ | 探索衰减 (α 递减) | 0 | 几行代码 |
| ⭐⭐⭐ | LLM 合成数据热启动 | 0（LLM 生成） | 新脚本 |
| ⭐⭐⭐ | 丰富 State 特征 (64d→146d) | 0 | 小改动 |
| ⭐⭐ | 隐式行为信号前端埋点 | 需上线 | 前端改动 |
| ⭐⭐ | 用户信誉评分 | 需 user_id (SSO) | 新模块 |
| ⭐ | BERT Reward Model | 200+ 条对话 | L20 训练 |
| ⭐ | 离线 RL (CQL) | 500+ 条对话 | 新算法 |

---

*本文档基于 2026-04-16 的技术讨论整理*
*核心观点：优化信号质量优先于更换算法，少量数据下 LinUCB + 先验注入是最优策略*
