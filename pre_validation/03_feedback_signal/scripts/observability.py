#!/usr/bin/env python3
"""
可观测性验证工具

让用户能够：
1. 可视化数据分布
2. 检查数据合理性
3. 追踪每个样本的奖励计算过程
4. 敏感性分析（参数变化的影响）
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
import math


def visualize_data_distribution(sessions: List[Dict]) -> str:
    """可视化数据分布，检查是否有bias"""
    
    # 场景分布
    scenario_counts = {}
    for s in sessions:
        scenario = s.get("scenario", "unknown")
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    
    # 满意度分布
    satisfactions = [s.get("ground_truth", {}).get("satisfaction", 0) for s in sessions]
    
    # 显式反馈分布
    explicit_counts = {"like": 0, "dislike": 0, "correct": 0, "null": 0}
    for s in sessions:
        for turn in s.get("turns", []):
            exp = turn.get("user_actions", {}).get("explicit")
            if exp:
                explicit_counts[exp] = explicit_counts.get(exp, 0) + 1
            else:
                explicit_counts["null"] += 1
    
    # 隐式信号分布
    dwell_times = []
    copy_actions = 0
    bounces = 0
    for s in sessions:
        for turn in s.get("turns", []):
            implicit = turn.get("user_actions", {}).get("implicit", {})
            dwell_times.append(implicit.get("dwell_time", 0))
            if implicit.get("copy_action"):
                copy_actions += 1
            if implicit.get("bounce"):
                bounces += 1
    
    # 生成报告
    report = """# 数据分布可观测性报告

## 一、场景分布

检查：是否存在某些场景过度采样？

| 场景 | 数量 | 占比 | 条形图 |
|------|------|------|--------|
"""
    total = len(sessions)
    for scenario, count in sorted(scenario_counts.items()):
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        report += f"| {scenario} | {count} | {pct:.1f}% | {bar} |\n"
    
    report += f"""
**分析**:
- 总样本数: {total}
- 场景覆盖: {len(scenario_counts)} 种
- 分布均衡性: {'均衡' if max(scenario_counts.values()) / total < 0.4 else '⚠️ 可能存在偏差'}

---

## 二、满意度分布（Ground Truth）

检查：人工标注的满意度是否合理分布？

| 统计量 | 值 |
|--------|-----|
| 平均值 | {sum(satisfactions)/len(satisfactions):.2f} |
| 最小值 | {min(satisfactions):.2f} |
| 最大值 | {max(satisfactions):.2f} |
| 标准差 | {math.sqrt(sum((x-sum(satisfactions)/len(satisfactions))**2 for x in satisfactions)/len(satisfactions)):.2f} |

**满意度分布直方图**:
```
"""
    # 简单直方图
    bins = [0] * 10
    for s in satisfactions:
        idx = min(int(s * 10), 9)
        bins[idx] += 1
    max_bin = max(bins) if bins else 1
    for i, count in enumerate(bins):
        bar = "█" * int(count / max_bin * 20)
        report += f"{i/10:.1f}-{(i+1)/10:.1f}: {bar} ({count})\n"
    
    report += f"""```

**分析**:
- 分布形态: {'近似正态' if max(bins) in bins[3:7] else '⚠️ 可能存在偏差'}
- ⚠️ 注意: Ground Truth 是人工设定的，需要审视合理性

---

## 三、显式反馈分布

| 类型 | 数量 | 占比 |
|------|------|------|
| like | {explicit_counts['like']} | {explicit_counts['like']/sum(explicit_counts.values())*100:.1f}% |
| dislike | {explicit_counts['dislike']} | {explicit_counts['dislike']/sum(explicit_counts.values())*100:.1f}% |
| correct | {explicit_counts['correct']} | {explicit_counts['correct']/sum(explicit_counts.values())*100:.1f}% |
| null（无反馈） | {explicit_counts['null']} | {explicit_counts['null']/sum(explicit_counts.values())*100:.1f}% |

**分析**:
- 显式反馈率: {(explicit_counts['like'] + explicit_counts['dislike'] + explicit_counts['correct'])/sum(explicit_counts.values())*100:.1f}%
- {'⚠️ 显式反馈率过低，真实场景可能更稀疏' if explicit_counts['null']/sum(explicit_counts.values()) > 0.5 else '反馈率合理'}

---

## 四、隐式信号分布

### 停留时间

| 统计量 | 值 |
|--------|-----|
| 平均 | {sum(dwell_times)/len(dwell_times):.1f}秒 |
| 最小 | {min(dwell_times)}秒 |
| 最大 | {max(dwell_times)}秒 |

**停留时间分布**:
```
"""
    # 停留时间分段
    dwell_bins = {"<5s": 0, "5-15s": 0, "15-30s": 0, "30-60s": 0, ">60s": 0}
    for t in dwell_times:
        if t < 5:
            dwell_bins["<5s"] += 1
        elif t < 15:
            dwell_bins["5-15s"] += 1
        elif t < 30:
            dwell_bins["15-30s"] += 1
        elif t < 60:
            dwell_bins["30-60s"] += 1
        else:
            dwell_bins[">60s"] += 1
    
    for label, count in dwell_bins.items():
        bar = "█" * int(count / max(dwell_bins.values()) * 15) if max(dwell_bins.values()) > 0 else ""
        report += f"{label:8s}: {bar} ({count})\n"
    
    report += f"""```

### 其他隐式行为

| 行为 | 数量 | 占比 |
|------|------|------|
| 拷贝 | {copy_actions} | {copy_actions/len(dwell_times)*100:.1f}% |
| 跳出 | {bounces} | {bounces/len(dwell_times)*100:.1f}% |

---

## 五、数据合理性自检清单

请手动确认以下问题：

- [ ] 场景分布是否覆盖了你关心的场景？
- [ ] 满意度标注是否符合你的直觉？
- [ ] 隐式信号分布是否符合真实用户行为？
- [ ] 是否有某些场景被过度/不足采样？
- [ ] 模拟数据是否包含你没考虑到的边界情况？

---

*生成时间: 2026-04-03*
"""
    return report


def trace_single_session(session: Dict, weights: Dict) -> str:
    """追踪单个session的奖励计算过程"""
    
    from calculate_rewards import (
        calculate_implicit_score, 
        infer_context_score,
        EXPLICIT_SCORES,
        IMPLICIT_WEIGHTS
    )
    
    report = f"""# 单样本追踪: {session['session_id']}

## 基本信息

| 字段 | 值 |
|------|-----|
| 场景 | {session.get('scenario')} |
| 满意度(Ground Truth) | {session.get('ground_truth', {}).get('satisfaction')} |
| 对话轮数 | {len(session.get('turns', []))} |

---

## 逐轮奖励计算

"""
    turns = session.get("turns", [])
    total_R = 0
    
    for i, turn in enumerate(turns, 1):
        user_actions = turn.get("user_actions", {})
        
        # 显式反馈
        explicit = user_actions.get("explicit")
        s_explicit = EXPLICIT_SCORES.get(explicit, 0.0)
        
        # 隐式信号
        implicit = user_actions.get("implicit", {})
        s_implicit = calculate_implicit_score(implicit)
        
        # 上下文
        s_context = infer_context_score(turn, turns)
        
        # 总奖励
        R = (
            weights["explicit"] * s_explicit +
            weights["implicit"] * s_implicit +
            weights["context"] * s_context
        )
        total_R += R
        
        report += f"""### 第 {i} 轮

**用户查询**: {turn.get('query')}

**意图簇**: {turn.get('intent_cluster')}

#### 显式反馈

| 信号 | 原始值 | 得分 | 权重 | 贡献 |
|------|--------|------|------|------|
| explicit | {explicit} | {s_explicit} | {weights['explicit']} | {s_explicit * weights['explicit']:.3f} |

#### 隐式信号

| 信号 | 原始值 | 计算过程 | 贡献 |
|------|--------|----------|------|
| dwell_time | {implicit.get('dwell_time', 0)}秒 | 阈值分段得分 | {IMPLICIT_WEIGHTS['dwell_time'] * s_implicit:.3f} |
| copy_action | {implicit.get('copy_action', False)} | True→1.0 | {IMPLICIT_WEIGHTS['copy_action'] * (1 if implicit.get('copy_action') else 0):.3f} |
| scroll_depth | {implicit.get('scroll_depth', 0):.2f} | 直接使用 | {IMPLICIT_WEIGHTS['scroll_depth'] * implicit.get('scroll_depth', 0):.3f} |
| bounce | {implicit.get('bounce', False)} | True→-0.5 | {IMPLICIT_WEIGHTS['bounce'] * (-0.5 if implicit.get('bounce') else 0):.3f} |
| **隐式总分** | - | - | **{s_implicit:.3f}** |

#### 上下文推断

| 信号 | 得分 | 权重 | 贡献 |
|------|------|------|------|
| context | {s_context:.3f} | {weights['context']} | {s_context * weights['context']:.3f} |

#### 本轮总奖励

$$R_{i} = {weights['explicit']} \\times {s_explicit} + {weights['implicit']} \\times {s_implicit:.3f} + {weights['context']} \\times {s_context:.3f} = {R:.3f}$$

---

"""
    
    avg_R = total_R / len(turns) if turns else 0
    true_satisfaction = session.get("ground_truth", {}).get("satisfaction", 0)
    gap = abs(avg_R - true_satisfaction)
    
    report += f"""## 汇总

| 指标 | 值 |
|------|-----|
| 平均奖励 | {avg_R:.3f} |
| 真实满意度 | {true_satisfaction} |
| 偏差 | {gap:.3f} |

**评估**: {'✅ 奖励与满意度接近' if gap < 0.2 else '⚠️ 偏差较大，需检查'}

---

*追踪完成*
"""
    return report


def sensitivity_analysis(sessions: List[Dict]) -> str:
    """敏感性分析：参数变化对结果的影响"""
    
    from calculate_rewards import calculate_session_rewards
    
    # 不同权重配置
    configs = [
        {"name": "默认配置", "weights": {"explicit": 0.5, "implicit": 0.3, "context": 0.2}},
        {"name": "重显式", "weights": {"explicit": 0.7, "implicit": 0.2, "context": 0.1}},
        {"name": "重隐式", "weights": {"explicit": 0.2, "implicit": 0.6, "context": 0.2}},
        {"name": "重上下文", "weights": {"explicit": 0.2, "implicit": 0.2, "context": 0.6}},
        {"name": "均等权重", "weights": {"explicit": 0.33, "implicit": 0.34, "context": 0.33}},
    ]
    
    results = []
    for config in configs:
        gaps = []
        for session in sessions:
            # 使用指定权重计算
            # (这里简化，实际需要修改 calculate_session_rewards 接受权重参数)
            pass
        results.append({"name": config["name"], "weights": config["weights"]})
    
    report = """# 敏感性分析

## 目的

验证结论是否对参数选择敏感。如果不同权重配置都得到相似结论，说明方法稳健。

## 测试配置

| 配置名 | 显式权重 | 隐式权重 | 上下文权重 |
|--------|----------|----------|------------|
| 默认配置 | 0.5 | 0.3 | 0.2 |
| 重显式 | 0.7 | 0.2 | 0.1 |
| 重隐式 | 0.2 | 0.6 | 0.2 |
| 重上下文 | 0.2 | 0.2 | 0.6 |
| 均等权重 | 0.33 | 0.34 | 0.33 |

## ⚠️ 待实现

敏感性分析需要修改奖励计算函数以接受自定义权重参数。

当前结论仅基于默认权重 (0.5/0.3/0.2)。

---

## 手动验证建议

你可以通过修改 `calculate_rewards.py` 中的 `WEIGHTS` 变量，重新运行验证：

```python
WEIGHTS = {
    "explicit": 0.5,  # 尝试 0.3, 0.7
    "implicit": 0.3,  # 尝试 0.2, 0.6
    "context": 0.2,   # 尝试 0.1, 0.4
}
```

观察相关性是否显著变化。

---

*生成时间: 2026-04-03*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="可观测性验证工具")
    parser.add_argument("--input", type=str, default="data/mock_sessions.json")
    parser.add_argument("--trace", type=str, help="追踪指定session_id，如 s001")
    parser.add_argument("--output", type=str, default="results/observability_report.md")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent.parent
    
    # 加载数据
    with open(base_path / args.input, "r", encoding="utf-8") as f:
        sessions = json.load(f)
    
    print(f"加载 {len(sessions)} 个session...")
    
    # 生成报告
    report = visualize_data_distribution(sessions)
    
    # 追踪单个session
    if args.trace:
        session = next((s for s in sessions if s["session_id"] == args.trace), None)
        if session:
            report += "\n\n---\n\n" + trace_single_session(
                session, 
                {"explicit": 0.5, "implicit": 0.3, "context": 0.2}
            )
        else:
            print(f"未找到 session: {args.trace}")
    
    # 敏感性分析
    report += "\n\n---\n\n" + sensitivity_analysis(sessions)
    
    # 输出
    output_path = base_path / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"可观测性报告已生成: {output_path}")
    print("\n建议操作:")
    print("1. 阅读报告，检查数据分布是否合理")
    print("2. 运行: python scripts/observability.py --trace s001")
    print("   追踪单个session的奖励计算过程")
    print("3. 手动修改权重参数，验证敏感性")


if __name__ == "__main__":
    main()