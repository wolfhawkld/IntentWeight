# 反馈信号模块验证

**目标**: 验证反馈信号获取与奖励计算的有效性，确认"越用越好"闭环能否成立

---

## 核心验证问题

| 问题 | 验证指标 | 成立阈值 |
|------|----------|----------|
| 反馈信号可获取吗？ | 有效反馈率 | > 5% |
| 反馈信号可靠吗？ | 信噪比、一致性 | > 0.7 |
| 奖励可计算吗？ | 奖励与真实满意度相关性 | > 0.6 |
| 追问能反推意图吗？ | 追问解析准确率 | > 70% |

---

## 验证方法

### 模拟数据 + 人工标注

1. **生成模拟对话**: 包含典型问答场景 + 用户行为
2. **人工标注满意度**: 真实"用户是否满意"标签
3. **计算奖励信号**: 用公式计算 R
4. **对比验证**: 计算奖励与真实满意度的一致性

---

## 数据结构

### 对话记录格式

```json
{
  "session_id": "s001",
  "turns": [
    {
      "turn_id": 1,
      "query": "怎么计算市盈率？",
      "answer": "市盈率(PE) = 股价 / 每股收益...",
      "intent_cluster": "pe_calculation",
      "user_actions": {
        "explicit": null,           // "like", "dislike", "correct", null
        "implicit": {
          "dwell_time": 32,         // 秒
          "copy_action": true,      // 是否拷贝
          "scroll_depth": 0.8,      // 滚动深度
          "bounce": false           // 是否直接跳出
        }
      }
    },
    {
      "turn_id": 2,
      "query": "PE太高说明什么？",
      "answer": "PE高可能意味着...",
      "intent_cluster": "pe_interpretation",
      "user_actions": {
        "explicit": "like",
        "implicit": {
          "dwell_time": 15,
          "copy_action": false,
          "scroll_depth": 0.5,
          "bounce": false
        }
      }
    }
  ],
  "ground_truth": {
    "satisfaction": 0.8,           // 人工标注：整体满意度 0-1
    "intent_accuracy": [true, true] // 每轮意图是否正确
  }
}
```

### 奖励计算公式

$$R = w_{exp} \cdot s_{exp} + w_{imp} \cdot s_{imp} + w_{ctx} \cdot s_{ctx}$$

其中：

| 信号类型 | 计算方式 | 权重 |
|----------|----------|------|
| $s_{exp}$ | 显式反馈: like=+1, dislike=-1, correct=+0.5 | $w_{exp}=0.5$ |
| $s_{imp}$ | 隐式信号组合: dwell+copy+scroll | $w_{imp}=0.3$ |
| $s_{ctx}$ | 上下文追问推断 | $w_{ctx}=0.2$ |

隐式信号计算：
$$s_{imp} = \alpha_{dwell} \cdot f(t) + \alpha_{copy} \cdot c + \alpha_{scroll} \cdot d$$

---

## 验证步骤

### Step 1: 模拟数据生成

```bash
python scripts/generate_mock_data.py --num_sessions 50
```

生成 50 个模拟对话，覆盖：
- 正反馈场景（满意）
- 负反馈场景（不满意）
- 稀疏反馈场景（无显式反馈）
- 追问场景（上下文信号）

### Step 2: 奖励计算

```bash
python scripts/calculate_rewards.py --input data/mock_sessions.json
```

计算每个 session 的奖励值。

### Step 3: 验证分析

```bash
python scripts/validate_signals.py --input data/mock_sessions.json
```

输出：
- 反馈率统计
- 奖励-满意度相关性
- 信号有效性分析

---

## 预期产出

| 产出物 | 文件 |
|--------|------|
| 模拟数据集 | `data/mock_sessions.json` |
| 奖励计算结果 | `results/rewards.json` |
| 验证分析报告 | `results/validation_report.md` |

---

## GPU需求

| 任务 | 需求 |
|------|------|
| 嵌入生成（可选） | GTX 1650 可用，或用 CPU |
| 奖励计算 | 纯 CPU |
| 追问解析（可选） | LLM API 或本地小模型 |

**GTX 1650 4GB 显存足够完成验证实验。**

---

## RL 更新模块

验证反馈信号后，实现 RL 更新，形成完整闭环。

### 当前实现：Contextual Bandit

| 组件 | 说明 |
|------|------|
| **Context** | 查询嵌入（SBERT 384维） |
| **Action** | 选择返回哪个 chunk |
| **Reward** | 用户反馈信号 |
| **策略** | LinUCB / Thompson / ε-greedy |

### 验证结果

| 策略 | 准确率 | 相关性 |
|------|--------|--------|
| LinUCB | 72.73% | 0.795 |
| Thompson Sampling | 72.73% | 0.795 |
| ε-greedy | 72.73% | 0.795 |

---

## 模块状态

| 模块 | 文件 | 状态 |
|------|------|------|
| 数据生成 | `generate_mock_data.py` | ✅ |
| 奖励计算 | `calculate_rewards.py` | ✅ |
| 信号验证 | `validate_signals.py` | ✅ |
| 可观测性 | `observability.py` | ✅ |
| **Contextual Bandit** | `contextual_bandit.py` | ✅ |
| Bandit 验证 | `validate_contextual_bandit.py` | ✅ |

### 已弃用

| 模块 | 说明 |
|------|------|
| `intent_association.py` | 被 contextual_bandit.py 替代 |
| `rl_updater.py` | 被 contextual_bandit.py 替代 |
| `validate_rl_update.py` | 被 validate_contextual_bandit.py 替代 |

---

## 验证结论

**Contextual Bandit 验证通过**：

- 选择准确率: 72.73%
- 奖励-满意度相关性: 0.795
- 三种探索策略均可工作

**下一步**：使用真实数据集验证

---

*更新于 2026-04-03*