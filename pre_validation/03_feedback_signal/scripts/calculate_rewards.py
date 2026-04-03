#!/usr/bin/env python3
"""
奖励计算脚本

根据用户反馈信号计算每轮对话的奖励值 R。
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# 权重配置（来自形式化文档）
WEIGHTS = {
    "explicit": 0.5,
    "implicit": 0.3,
    "context": 0.2,
}

# 隐式信号权重
IMPLICIT_WEIGHTS = {
    "dwell_time": 0.4,
    "copy_action": 0.3,
    "scroll_depth": 0.2,
    "bounce": 0.1,
}

# 隐式信号阈值配置
DWELL_TIME_THRESHOLDS = {
    "very_short": 5,     # <5秒: 可能不满意或答案太简洁
    "short": 10,
    "medium": 20,
    "long": 30,          # >30秒: 可能满意或困惑
}

# 显式反馈映射
EXPLICIT_SCORES = {
    "like": 1.0,
    "dislike": -1.0,
    "correct": 0.5,      # 用户修正答案，部分正信号
    None: 0.0,
}


def calculate_implicit_score(implicit: Dict) -> float:
    """计算隐式信号得分"""
    
    score = 0.0
    
    # 停留时间得分（非线性）
    dwell_time = implicit.get("dwell_time", 0)
    if dwell_time < DWELL_TIME_THRESHOLDS["very_short"]:
        dwell_score = -0.3  # 太短：可能是跳出或答案没用
    elif dwell_time < DWELL_TIME_THRESHOLDS["short"]:
        dwell_score = 0.0   # 较短：中性
    elif dwell_time < DWELL_TIME_THRESHOLDS["medium"]:
        dwell_score = 0.2   # 中等：轻度关注
    elif dwell_time < DWELL_TIME_THRESHOLDS["long"]:
        dwell_score = 0.4   # 较长：明显关注
    elif dwell_time < 60:
        dwell_score = 0.6   # 很长：深度阅读（可能是满意）
    else:
        dwell_score = 0.3   # 极长：可能困惑，降分
    
    score += IMPLICIT_WEIGHTS["dwell_time"] * dwell_score
    
    # 拷贝行为
    copy_action = implicit.get("copy_action", False)
    copy_score = 1.0 if copy_action else 0.0
    score += IMPLICIT_WEIGHTS["copy_action"] * copy_score
    
    # 滚动深度
    scroll_depth = implicit.get("scroll_depth", 0.0)
    scroll_score = scroll_depth  # 直接用比例
    score += IMPLICIT_WEIGHTS["scroll_depth"] * scroll_score
    
    # 跳出行为
    bounce = implicit.get("bounce", False)
    bounce_score = -0.5 if bounce else 0.0
    score += IMPLICIT_WEIGHTS["bounce"] * bounce_score
    
    # 归一化到 [-1, 1]
    score = max(-1.0, min(1.0, score))
    
    return score


def infer_context_score(turn: Dict, turns: List[Dict]) -> float:
    """从上下文追问推断信号"""
    
    turn_id = turn["turn_id"]
    
    # 如果是最后一轮，没有后续追问
    if turn_id >= len(turns):
        return 0.0
    
    next_turn = turns[turn_id]  # 下一轮（索引=turn_id-1+1=turn_id）
    
    # 分析追问类型
    next_query = next_turn.get("query", "").lower()
    
    # 追问深入关键词（正信号）
    deepen_keywords = ["详细", "展开", "再说", "区别", "对比", "还有", "补充"]
    for kw in deepen_keywords:
        if kw in next_query:
            return 0.5
    
    # 追问转向关键词（负信号）
    redirect_keywords = ["算了", "不是", "不对", "换个", "我问的是"]
    for kw in redirect_keywords:
        if kw in next_query:
            return -0.5
    
    # 澄清请求（中性偏负）
    clarify_keywords = ["什么意思", "没明白", "不懂", "能解释"]
    for kw in clarify_keywords:
        if kw in next_query:
            return -0.2
    
    # 继续问相关问题（轻度正信号）
    if next_turn.get("intent_cluster") == turn.get("intent_cluster"):
        return 0.3
    
    # 默认中性
    return 0.0


def calculate_turn_reward(turn: Dict, turns: List[Dict]) -> Dict:
    """计算单轮对话奖励"""
    
    user_actions = turn.get("user_actions", {})
    
    # 1. 显式反馈得分
    explicit = user_actions.get("explicit")
    s_explicit = EXPLICIT_SCORES.get(explicit, 0.0)
    
    # 2. 隐式信号得分
    implicit = user_actions.get("implicit", {})
    s_implicit = calculate_implicit_score(implicit)
    
    # 3. 上下文追问得分
    s_context = infer_context_score(turn, turns)
    
    # 4. 总奖励（加权融合）
    R_total = (
        WEIGHTS["explicit"] * s_explicit +
        WEIGHTS["implicit"] * s_implicit +
        WEIGHTS["context"] * s_context
    )
    
    return {
        "turn_id": turn["turn_id"],
        "reward_components": {
            "explicit": {
                "signal": explicit,
                "score": s_explicit,
                "weight": WEIGHTS["explicit"],
            },
            "implicit": {
                "details": implicit,
                "score": s_implicit,
                "weight": WEIGHTS["implicit"],
            },
            "context": {
                "score": s_context,
                "weight": WEIGHTS["context"],
            },
        },
        "R_total": R_total,
    }


def calculate_session_rewards(session: Dict) -> Dict:
    """计算整个session的奖励"""
    
    turns = session.get("turns", [])
    turn_rewards = []
    
    for turn in turns:
        reward = calculate_turn_reward(turn, turns)
        reward["intent_cluster"] = turn.get("intent_cluster")
        reward["query"] = turn.get("query")
        turn_rewards.append(reward)
    
    # session级别聚合
    R_session = sum(r["R_total"] for r in turn_rewards) / len(turn_rewards) if turn_rewards else 0.0
    
    # 与真实满意度对比
    ground_truth = session.get("ground_truth", {})
    true_satisfaction = ground_truth.get("satisfaction", 0.0)
    
    return {
        "session_id": session["session_id"],
        "scenario": session.get("scenario"),
        "turn_rewards": turn_rewards,
        "R_session_avg": R_session,
        "ground_truth": {
            "satisfaction": true_satisfaction,
            "intent_accuracy": ground_truth.get("intent_accuracy", []),
        },
        "reward_satisfaction_gap": abs(R_session - true_satisfaction),
    }


def analyze_feedback_rate(sessions: List[Dict]) -> Dict:
    """分析反馈率"""
    
    total_turns = 0
    explicit_feedback_count = 0
    implicit_rich_count = 0  # 有有效隐式信号
    no_feedback_count = 0
    
    for session in sessions:
        for turn in session.get("turns", []):
            total_turns += 1
            actions = turn.get("user_actions", {})
            
            explicit = actions.get("explicit")
            if explicit is not None:
                explicit_feedback_count += 1
            
            implicit = actions.get("implicit", {})
            # 有效隐式信号定义：停留>5秒 或 有拷贝 或 滚动>50%
            has_rich_implicit = (
                implicit.get("dwell_time", 0) > 5 or
                implicit.get("copy_action", False) or
                implicit.get("scroll_depth", 0) > 0.5
            )
            if has_rich_implicit:
                implicit_rich_count += 1
            
            # 完全无反馈
            if explicit is None and not has_rich_implicit:
                no_feedback_count += 1
    
    return {
        "total_turns": total_turns,
        "explicit_feedback_count": explicit_feedback_count,
        "explicit_feedback_rate": explicit_feedback_count / total_turns if total_turns > 0 else 0,
        "implicit_rich_count": implicit_rich_count,
        "implicit_rich_rate": implicit_rich_count / total_turns if total_turns > 0 else 0,
        "no_feedback_count": no_feedback_count,
        "no_feedback_rate": no_feedback_count / total_turns if total_turns > 0 else 0,
        "effective_feedback_rate": (explicit_feedback_count + implicit_rich_count) / total_turns if total_turns > 0 else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="计算奖励信号")
    parser.add_argument("--input", type=str, default="data/mock_sessions.json", help="输入数据文件")
    parser.add_argument("--output", type=str, default="results/rewards.json", help="输出文件")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent.parent
    
    # 加载数据
    input_path = base_path / args.input
    with open(input_path, "r", encoding="utf-8") as f:
        sessions = json.load(f)
    
    print(f"加载 {len(sessions)} 个session...")
    
    # 计算奖励
    rewards = []
    for session in sessions:
        reward = calculate_session_rewards(session)
        rewards.append(reward)
    
    # 反馈率分析
    feedback_analysis = analyze_feedback_rate(sessions)
    
    print("\n反馈率分析:")
    print(f"  显式反馈率: {feedback_analysis['explicit_feedback_rate']:.2%}")
    print(f"  有效隐式率: {feedback_analysis['implicit_rich_rate']:.2%}")
    print(f"  无反馈率: {feedback_analysis['no_feedback_rate']:.2%}")
    print(f"  有效反馈率: {feedback_analysis['effective_feedback_rate']:.2%}")
    
    # 奖励-满意度相关性（简单统计）
    gaps = [r["reward_satisfaction_gap"] for r in rewards]
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    print(f"\n奖励-满意度平均偏差: {avg_gap:.3f}")
    
    # 输出
    output = {
        "feedback_analysis": feedback_analysis,
        "session_rewards": rewards,
        "summary": {
            "avg_gap": avg_gap,
            "num_sessions": len(sessions),
        },
    }
    
    output_path = base_path / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    main()