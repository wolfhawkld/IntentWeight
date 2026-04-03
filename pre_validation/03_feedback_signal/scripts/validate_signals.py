#!/usr/bin/env python3
"""
信号有效性验证脚本

验证反馈信号是否能准确反映用户真实满意度。
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
import math


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """计算Pearson相关系数"""
    n = len(x)
    if n == 0 or n != len(y):
        return 0.0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)
    
    if std_x == 0 or std_y == 0:
        return 0.0
    
    return cov / (std_x * std_y)


def analyze_signal_components(rewards: List[Dict]) -> Dict:
    """分析各信号成分的有效性"""
    
    # 收集数据
    R_explicit_list = []
    R_implicit_list = []
    R_context_list = []
    R_total_list = []
    satisfaction_list = []
    
    for r in rewards:
        turns = r.get("turn_rewards", [])
        for turn in turns:
            components = turn.get("reward_components", {})
            
            # 各信号贡献
            R_explicit_list.append(components["explicit"]["score"] * components["explicit"]["weight"])
            R_implicit_list.append(components["implicit"]["score"] * components["implicit"]["weight"])
            R_context_list.append(components["context"]["score"] * components["context"]["weight"])
            R_total_list.append(turn["R_total"])
        
        satisfaction = r.get("ground_truth", {}).get("satisfaction", 0)
        # 将session满意度扩展到每轮（简化）
        satisfaction_list.extend([satisfaction] * len(turns))
    
    # 计算各信号与满意度的相关性
    corr_explicit = pearson_correlation(R_explicit_list, satisfaction_list)
    corr_implicit = pearson_correlation(R_implicit_list, satisfaction_list)
    corr_context = pearson_correlation(R_context_list, satisfaction_list)
    corr_total = pearson_correlation(R_total_list, satisfaction_list)
    
    return {
        "explicit": {
            "correlation": corr_explicit,
            "avg_contribution": sum(R_explicit_list) / len(R_explicit_list) if R_explicit_list else 0,
        },
        "implicit": {
            "correlation": corr_implicit,
            "avg_contribution": sum(R_implicit_list) / len(R_implicit_list) if R_implicit_list else 0,
        },
        "context": {
            "correlation": corr_context,
            "avg_contribution": sum(R_context_list) / len(R_context_list) if R_context_list else 0,
        },
        "total": {
            "correlation": corr_total,
            "avg_reward": sum(R_total_list) / len(R_total_list) if R_total_list else 0,
        },
    }


def analyze_scenario_accuracy(rewards: List[Dict]) -> Dict:
    """按场景分析奖励准确性"""
    
    scenario_stats = {}
    
    for r in rewards:
        scenario = r.get("scenario", "unknown")
        R_avg = r.get("R_session_avg", 0)
        satisfaction = r.get("ground_truth", {}).get("satisfaction", 0)
        gap = abs(R_avg - satisfaction)
        
        if scenario not in scenario_stats:
            scenario_stats[scenario] = {
                "count": 0,
                "avg_reward": 0,
                "avg_satisfaction": 0,
                "avg_gap": 0,
            }
        
        stats = scenario_stats[scenario]
        stats["count"] += 1
        stats["avg_reward"] += R_avg
        stats["avg_satisfaction"] += satisfaction
        stats["avg_gap"] += gap
    
    # 计算平均值
    for scenario, stats in scenario_stats.items():
        n = stats["count"]
        stats["avg_reward"] /= n
        stats["avg_satisfaction"] /= n
        stats["avg_gap"] /= n
    
    return scenario_stats


def check_thresholds(feedback_analysis: Dict, signal_analysis: Dict) -> Dict:
    """检查是否达到验证阈值"""
    
    thresholds = {
        "feedback_rate": 0.05,       # 有效反馈率 > 5%
        "signal_correlation": 0.6,   # 奖励-满意度相关性 > 0.6
        "implicit_correlation": 0.5, # 隐式信号相关性 > 0.5
    }
    
    results = {
        "feedback_rate": {
            "value": feedback_analysis.get("effective_feedback_rate", 0),
            "threshold": thresholds["feedback_rate"],
            "pass": feedback_analysis.get("effective_feedback_rate", 0) >= thresholds["feedback_rate"],
        },
        "signal_correlation": {
            "value": signal_analysis["total"]["correlation"],
            "threshold": thresholds["signal_correlation"],
            "pass": signal_analysis["total"]["correlation"] >= thresholds["signal_correlation"],
        },
        "implicit_correlation": {
            "value": signal_analysis["implicit"]["correlation"],
            "threshold": thresholds["implicit_correlation"],
            "pass": signal_analysis["implicit"]["correlation"] >= thresholds["implicit_correlation"],
        },
    }
    
    all_pass = all(r["pass"] for r in results.values())
    
    return {
        "thresholds": results,
        "all_pass": all_pass,
        "conclusion": "反馈信号模块验证通过" if all_pass else "反馈信号模块需要优化",
    }


def generate_report(data: Dict) -> str:
    """生成验证报告"""
    
    feedback = data.get("feedback_analysis", {})
    signal = data.get("signal_analysis", {})
    scenario = data.get("scenario_analysis", {})
    threshold_check = data.get("threshold_check", {})
    
    report = """# 反馈信号模块验证报告

## 一、反馈率统计

| 指标 | 数值 | 说明 |
|------|------|------|
| 总对话轮数 | {total_turns} | |
| 显式反馈率 | {explicit_rate:.2%} | 点赞/点踩/修正 |
| 有效隐式率 | {implicit_rate:.2%} | 停留>5s/拷贝/滚动>50% |
| 无反馈率 | {no_feedback_rate:.2%} | 沉默用户 |
| **有效反馈率** | **{effective_rate:.2%}** | 显式+有效隐式 |

## 二、信号有效性分析

### 各信号与满意度的相关性

| 信号类型 | 相关系数 | 平均贡献 | 评估 |
|----------|----------|----------|------|
| 显式反馈 | {corr_explicit:.3f} | {contrib_explicit:.3f} | {eval_explicit} |
| 隐式信号 | {corr_implicit:.3f} | {contrib_implicit:.3f} | {eval_implicit} |
| 上下文追问 | {corr_context:.3f} | {contrib_context:.3f} | {eval_context} |
| **总奖励** | **{corr_total:.3f}** | {avg_reward:.3f} | {eval_total} |

### 相关性解读

- **r > 0.7**: 强正相关，信号可靠
- **r > 0.5**: 中等正相关，信号有效
- **r < 0.3**: 弱相关，信号不可靠

## 三、场景准确性分析

| 场景 | 样本数 | 平均奖励 | 真实满意度 | 偏差 | 评估 |
|------|--------|----------|------------|------|------|
""".format(
        total_turns=feedback.get("total_turns", 0),
        explicit_rate=feedback.get("explicit_feedback_rate", 0),
        implicit_rate=feedback.get("implicit_rich_rate", 0),
        no_feedback_rate=feedback.get("no_feedback_rate", 0),
        effective_rate=feedback.get("effective_feedback_rate", 0),
        corr_explicit=signal.get("explicit", {}).get("correlation", 0),
        corr_implicit=signal.get("implicit", {}).get("correlation", 0),
        corr_context=signal.get("context", {}).get("correlation", 0),
        corr_total=signal.get("total", {}).get("correlation", 0),
        contrib_explicit=signal.get("explicit", {}).get("avg_contribution", 0),
        contrib_implicit=signal.get("implicit", {}).get("avg_contribution", 0),
        contrib_context=signal.get("context", {}).get("avg_contribution", 0),
        avg_reward=signal.get("total", {}).get("avg_reward", 0),
        eval_explicit="✅ 可靠" if signal.get("explicit", {}).get("correlation", 0) > 0.5 else "⚠️ 需优化",
        eval_implicit="✅ 有效" if signal.get("implicit", {}).get("correlation", 0) > 0.5 else "⚠️ 需优化",
        eval_context="⚠️ 辅助" if signal.get("context", {}).get("correlation", 0) > 0.3 else "❌ 无效",
        eval_total="✅ 可用" if signal.get("total", {}).get("correlation", 0) > 0.6 else "⚠️ 需调参",
    )
    
    # 添加场景分析表格
    for scn, stats in sorted(scenario.items()):
        gap_eval = "✅" if stats["avg_gap"] < 0.2 else "⚠️" if stats["avg_gap"] < 0.4 else "❌"
        report += f"| {scn} | {stats['count']} | {stats['avg_reward']:.2f} | {stats['avg_satisfaction']:.2f} | {stats['avg_gap']:.2f} | {gap_eval} |\n"
    
    # 添加阈值检查
    report += """
## 四、阈值验证

"""
    
    for name, check in threshold_check.get("thresholds", {}).items():
        status = "✅ 通过" if check["pass"] else "❌ 未达标"
        report += f"| {name} | {check['value']:.3f} | ≥ {check['threshold']} | {status} |\n"
    
    report += f"""
## 五、结论

**{threshold_check.get('conclusion', '待分析')}**

### 发现的问题

"""
    
    problems = []
    if not threshold_check.get("thresholds", {}).get("feedback_rate", {}).get("pass", True):
        problems.append("- 反馈率过低，需要优化反馈收集机制")
    if not threshold_check.get("thresholds", {}).get("signal_correlation", {}).get("pass", True):
        problems.append("- 奖励计算与真实满意度相关性不足，需要调整权重")
    if not threshold_check.get("thresholds", {}).get("implicit_correlation", {}).get("pass", True):
        problems.append("- 隐式信号有效性不足，需要优化阈值或权重")
    
    if problems:
        report += "\n".join(problems)
    else:
        report += "- 无明显问题，验证通过\n"
    
    report += """
### 建议

1. 如果隐式信号相关性低 → 调整 dwell_time 阈值，增加困惑检测
2. 如果上下文信号相关性低 → 优化追问语义解析逻辑
3. 如果反馈率低 → 设计主动询问机制（"答案是否解决了您的问题？"）

---

*生成时间: 2026-04-03*
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="验证反馈信号有效性")
    parser.add_argument("--input", type=str, default="results/rewards.json", help="输入数据文件")
    parser.add_argument("--report", type=str, default="results/validation_report.md", help="报告输出文件")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent.parent
    
    # 加载奖励数据
    input_path = base_path / args.input
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    rewards = data.get("session_rewards", [])
    feedback_analysis = data.get("feedback_analysis", {})
    
    print("分析信号有效性...")
    
    # 各信号成分分析
    signal_analysis = analyze_signal_components(rewards)
    
    # 场景准确性分析
    scenario_analysis = analyze_scenario_accuracy(rewards)
    
    # 阈值检查
    threshold_check = check_thresholds(feedback_analysis, signal_analysis)
    
    # 合并数据
    full_data = {
        "feedback_analysis": feedback_analysis,
        "signal_analysis": signal_analysis,
        "scenario_analysis": scenario_analysis,
        "threshold_check": threshold_check,
    }
    
    # 生成报告
    report = generate_report(full_data)
    
    print("\n验证结果:")
    print(f"  有效反馈率: {feedback_analysis.get('effective_feedback_rate', 0):.2%}")
    print(f"  奖励-满意度相关性: {signal_analysis['total']['correlation']:.3f}")
    print(f"  验证结论: {threshold_check['conclusion']}")
    
    # 输出报告
    report_path = base_path / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n报告已保存到: {report_path}")
    
    # 同时保存完整数据
    full_data_path = base_path / "results/full_validation_data.json"
    with open(full_data_path, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    
    print(f"完整数据已保存到: {full_data_path}")


if __name__ == "__main__":
    main()