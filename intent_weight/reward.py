# -*- coding: utf-8 -*-
"""
奖励计算模块（v2 含上下文奖励）
Reward Calculation Module (v2 with Context Reward)

参考 / Reference:
- IntentRoute 项目 calculate_rewards.py / infer_context_score()
- 显式反馈 + 隐式信号 + 上下文追问分析
"""
from typing import Dict, List, Optional


# 显式反馈分数映射
EXPLICIT_SCORES = {
    "like": 1.0,
    "dislike": 0.0,
    "correct": 0.7,
}


# 隐式信号权重配置
IMPLICIT_WEIGHTS = {
    "copy_action": 0.15,    # 复制行为：强正信号
    "dwell_time": 0.05,     # 适中停留时间：轻度正信号
    "scroll_depth": 0.05,   # 深度滚动：轻度正信号
}

# 显式/隐式融合权重
EXPLICIT_WEIGHT = 0.75      # 显式反馈主导
IMPLICIT_WEIGHT = 0.25      # 隐式信号微调


def _calculate_implicit_score(implicit: Dict) -> float:
    """
    计算隐式信号得分
    Calculate implicit signal score

    Returns:
        score: [0.0, 0.25] 范围的隐式调整值
    """
    score = 0.0

    if implicit.get("copy_action", False):
        score += IMPLICIT_WEIGHTS["copy_action"]

    dwell = implicit.get("dwell_time", 0)
    if 10 < dwell < 60:
        score += IMPLICIT_WEIGHTS["dwell_time"]

    if implicit.get("scroll_depth", 0) > 0.7:
        score += IMPLICIT_WEIGHTS["scroll_depth"]

    return score


def calculate_reward(
    explicit: Optional[str] = None,
    implicit: Optional[Dict] = None,
) -> float:
    """
    计算反馈奖励值（显式+隐式融合）
    Calculate feedback reward value (explicit + implicit fusion)

    v2 策略：
    - 有显式 + 有隐式：加权融合（显式 75% + 隐式 25%）
    - 有显式无隐式：直接使用显式分数
    - 无显式有隐式：从隐式信号推断
    - 完全无反馈：0.5 中性

    融合公式：
    reward = explicit_score × 0.75 + (0.5 + implicit_adjust) × 0.25

    效果示例：
    - like + 复制 + 长停留: 1.0×0.75 + 0.75×0.25 = 0.9375
    - like + 3s跳过:        1.0×0.75 + 0.50×0.25 = 0.875
    - dislike + 复制:       0.0×0.75 + 0.65×0.25 = 0.1625

    Args:
        explicit: 显式反馈类型 ("like", "dislike", "correct", None)
        implicit: 隐式信号 {"dwell_time", "copy_action", "scroll_depth"}

    Returns:
        reward: [0.0, 1.0] 范围的奖励值
    """
    implicit_adjust = _calculate_implicit_score(implicit) if implicit else 0.0

    if explicit in EXPLICIT_SCORES:
        explicit_score = EXPLICIT_SCORES[explicit]
        if implicit:
            # 显式 + 隐式融合
            reward = explicit_score * EXPLICIT_WEIGHT + (0.5 + implicit_adjust) * IMPLICIT_WEIGHT
        else:
            # 仅显式
            reward = explicit_score
        return min(1.0, max(0.0, reward))

    # 无显式反馈 → 用隐式信号推断
    if implicit is None:
        return 0.5  # 中性默认值

    return min(1.0, max(0.0, 0.5 + implicit_adjust))


# ==================== 上下文追问奖励 ====================
# Context Follow-up Reward

# 深入关键词（正信号）→ 用户对上一轮回答满意，想了解更多
DEEPEN_KEYWORDS = [
    "详细", "展开", "再说", "还有", "补充", "继续", "更多", "具体",
    "tell me more", "more detail", "elaborate", "continue", "go on",
]

# 转向关键词（负信号）→ 用户对上一轮回答不满意
REDIRECT_KEYWORDS = [
    "不对", "不是", "错了", "换个", "重新", "应该", "我问的是", "不是这个",
    "算了", "别的", "wrong", "incorrect", "not what I asked", "try again",
]

# 澄清关键词（轻度负信号）→ 用户没看懂
CLARIFY_KEYWORDS = [
    "什么意思", "没明白", "不懂", "能解释", "看不懂", "不理解",
    "what do you mean", "don't understand", "confused", "clarify",
]


def infer_context_reward(query: str) -> float:
    """
    从用户追问内容推断对上一轮回答的满意度
    Infer satisfaction with previous answer from follow-up query

    Args:
        query: 当前用户输入

    Returns:
        context_score: [-0.5, 0.5]，0 表示中性
    """
    q = query.lower()

    for kw in REDIRECT_KEYWORDS:
        if kw in q:
            return -0.5

    for kw in CLARIFY_KEYWORDS:
        if kw in q:
            return -0.2

    for kw in DEEPEN_KEYWORDS:
        if kw in q:
            return 0.5

    return 0.0
