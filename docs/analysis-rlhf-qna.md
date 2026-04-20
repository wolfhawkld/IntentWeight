# RLHF 方案技术答疑
# RLHF Technical Q&A

**日期 / Date**: 2026-04-20
**分支 / Branch**: RLHF
**背景 / Background**: 梳理 RLHF 分支三个优化方向的技术细节和常见疑问

---

## Q1: 两个 BERT 模型分别替代什么？

**Reward Model** 替代的是 `calculate_reward()` 中的手工权重公式（显式 75% + 隐式 25% 的硬编码融合），用训练出的模型直接预测用户满意度 [0, 1]。

**意图分类器** 替代的是 ReAct Agent 中的 **LLM 决策调用**（判断 search_knowledge_base / direct_answer / refine_search），而**不是**替代 HDBSCAN 聚类或 LinUCB 聚类选择。

```
当前：Query → LLM 调用 (~3s) → 3 分类决策 → LinUCB 选聚类 → 检索
目标：Query → BERT 分类 (~50ms) → 3 分类决策 → LinUCB 选聚类 → 检索
                                                    ↑ 保留不变
```

HDBSCAN 聚类和 LinUCB 的在线学习机制保持不动，BERT 只加速前面的意图判断环节。

---

## Q2: 离线 RL 是不是用来替代 LinUCB 的？

**不是替代，是定期补课。**

- **LinUCB（在线）**：每次反馈立即更新，实时响应
- **离线 RL（批量）**：从全部历史数据一次性重新估算 LinUCB 的 A/b 参数

两者互补：离线 RL 定期生成更优的基线参数，LinUCB 从这个更好的起点继续在线学习。

```
每周：离线 RL 从全部历史数据训练 → 输出更优的 A, b 参数
实时：LinUCB 加载新参数 → 继续在线学习
```

类比：离线 RL 是"复习全部考试经验总结规律"，LinUCB 是"课堂上随时根据新题调整策略"。

---

## Q3: 离线 RL 训练的是什么模型？

**没有模型。** 离线 RL（CQL）不训练新模型，它是一个优化算法，输出的就是 LinUCB 自己的参数（A 矩阵和 b 向量）。

```python
# 离线 RL 实际做的事
def offline_rl_update():
    history = load_all_interactions()        # 从 SQLite 读全部历史
    for arm in range(n_arms):
        arm_data = filter(history, arm)
        A[arm] = I + Σ(x @ x.T)             # 批量重算协方差
        b[arm] = Σ(r * x)                   # 批量重算奖励累积
        if len(arm_data) < threshold:
            A[arm] += regularization * I     # 保守正则化
    save(A, b)                               # LinUCB 加载这组新参数
```

---

## Q4: CQL 具体是什么算法？

CQL (Conservative Q-Learning) 是 Q-Learning 的离线变体（Kumar et al., 2020）。

**Q-Learning 基础：**
- 学一个 Q 函数：Q(state, action) → 预期累积奖励
- 更新公式：Q(s,a) ← r + γ × max Q(s', a')
- 含义："在这个状态下选这个动作，长期能拿多少奖励"

**离线 Q-Learning 的问题：**
- 历史数据中没见过的 (state, action) 组合 → Q 值过度乐观
- 系统可能选了一个"看起来好但没人试过"的 action → 效果很差

**CQL 的核心创新 — 保守惩罚：**
```
CQL Loss = 标准 Q-Learning Loss
         + α × (对数据中没出现过的 action 的 Q 值施加惩罚)

直觉：宁可低估没试过的选项，也不冒险选未知的
```

**但对我们的系统，完整 CQL 是杀鸡用牛刀：**

| 完整 CQL | 我们的系统 |
|---------|----------|
| 神经网络拟合 Q 函数 | Q 函数就是 LinUCB 的 θᵀx，线性的 |
| 复杂连续状态空间 | 只有 15 个 arm |
| 需要大量数据 | 数据量有限 |
| 需要 GPU | CPU 几秒搞定 |

实际用到的是 CQL 的**思想**（保守正则化），而非完整算法。更准确的描述是：**带保守正则化的批量参数重估**。

---

## Q5: 这里的优化一定要用真正的 RL 算法吗？

**不需要。** "离线 RL" 是借用了 RL 的思想框架（state/action/reward + 保守策略），但实际实现就是从历史数据批量重算 LinUCB 参数加上正则化，一个 Python 脚本就能完成，不涉及模型训练。

---

## 总结：RLHF 分支三个方向的本质

| 方向 | 本质 | 需要 GPU | 需要训练 |
|------|------|:---:|:---:|
| BERT Reward Model | 监督学习（回归） | L20 | 需要，200+ 条带反馈对话 |
| BERT 意图分类器 | 监督学习（3 分类） | L20 | 需要，几百条标注 query |
| 离线参数重估 | 批量计算 + 正则化 | CPU | 不需要，是算法不是模型 |

三者是**叠加关系**，不互斥：
- Reward Model → 提升 reward 信号质量 → LinUCB 学得更准
- 意图分类器 → 替代 LLM 决策调用 → 省延迟省成本
- 离线参数重估 → 定期校准 LinUCB 基线 → 消除在线学习的路径依赖

---

*本文档基于 2026-04-19 ~ 2026-04-20 的技术讨论整理*
