#!/usr/bin/env python3
"""
模拟数据生成脚本

生成包含用户反馈信号的对话数据，用于验证反馈信号模块有效性。
"""

import json
import random
import argparse
from datetime import datetime
from pathlib import Path

# 领域：金融问答
INTENT_CLUSTERS = {
    "pe_calculation": "市盈率计算",
    "pe_interpretation": "市盈率解读",
    "pb_calculation": "市净率计算",
    "roe_explanation": "ROE解释",
    "dividend_policy": "分红政策",
    "risk_assessment": "风险评估",
    "trading_rules": "交易规则",
    "account_operation": "账户操作",
}

# 模拟问答模板
QA_TEMPLATES = {
    "pe_calculation": {
        "queries": [
            "怎么计算市盈率？",
            "PE公式是什么？",
            "市盈率怎么算？",
        ],
        "answers": [
            "市盈率(PE) = 股价 / 每股收益(EPS)。例如，股价50元，EPS5元，则PE=10倍。",
            "PE计算公式：当前股价 ÷ 最近12个月每股净利润。反映投资回收年限。",
        ],
    },
    "pe_interpretation": {
        "queries": [
            "PE太高说明什么？",
            "市盈率高好还是低好？",
            "PE多少算合理？",
        ],
        "answers": [
            "PE高可能意味着：1) 市场预期高增长；2) 股价被高估；需结合行业对比判断。",
            "PE低可能说明：1) 价值低估；2) 增长预期低；传统行业PE通常较低。",
        ],
    },
    "pb_calculation": {
        "queries": [
            "市净率怎么算？",
            "PB和PE有什么区别？",
        ],
        "answers": [
            "市净率(PB) = 股价 / 每股净资产。PB<1可能意味着股价低于净资产价值。",
        ],
    },
    "roe_explanation": {
        "queries": [
            "ROE是什么意思？",
            "净资产收益率怎么看？",
        ],
        "answers": [
            "ROE(净资产收益率) = 净利润 / 净资产，衡量公司运用股东资金的能力，一般>15%较好。",
        ],
    },
}

# 用户行为模板（按满意度类型）
BEHAVIOR_PROFILES = {
    "satisfied": {
        "explicit": ["like", None],  # 50%会点赞
        "implicit": {
            "dwell_time": [20, 60],   # 停留较长
            "copy_action": True,      # 常会拷贝
            "scroll_depth": [0.7, 1.0],
            "bounce": False,
        },
        "follow_up": "deepen",  # 继续深入追问
    },
    "unsatisfied": {
        "explicit": ["dislike", None, "correct"],  # 可能点踩或修正
        "implicit": {
            "dwell_time": [3, 10],    # 快速离开或反复看不懂
            "copy_action": False,
            "scroll_depth": [0.2, 0.5],
            "bounce": True,           # 可能跳出
        },
        "follow_up": "redirect",  # 转问其他问题
    },
    "neutral": {
        "explicit": None,
        "implicit": {
            "dwell_time": [10, 20],
            "copy_action": False,
            "scroll_depth": [0.5, 0.7],
            "bounce": False,
        },
        "follow_up": None,  # 可能结束或继续
    },
    "confused": {
        "explicit": None,
        "implicit": {
            "dwell_time": [30, 90],   # 停留很久但没拷贝（困惑）
            "copy_action": False,
            "scroll_depth": [0.3, 0.6],
            "bounce": False,
        },
        "follow_up": "clarify",  # 请求澄清
    },
}


def generate_turn(intent: str, satisfaction_type: str, turn_id: int) -> dict:
    """生成单轮对话"""
    qa = QA_TEMPLATES.get(intent, QA_TEMPLATES["pe_calculation"])
    behavior = BEHAVIOR_PROFILES[satisfaction_type]
    
    query = random.choice(qa["queries"])
    answer = random.choice(qa["answers"])
    
    # 显式反馈
    explicit_options = behavior["explicit"]
    if isinstance(explicit_options, list):
        explicit = random.choice(explicit_options)
    else:
        explicit = explicit_options
    
    # 隐式反馈
    implicit = {}
    if "dwell_time" in behavior["implicit"]:
        implicit["dwell_time"] = random.randint(*behavior["implicit"]["dwell_time"])
    if "copy_action" in behavior["implicit"]:
        implicit["copy_action"] = behavior["implicit"]["copy_action"]
    if "scroll_depth" in behavior["implicit"]:
        implicit["scroll_depth"] = random.uniform(*behavior["implicit"]["scroll_depth"])
    if "bounce" in behavior["implicit"]:
        implicit["bounce"] = behavior["implicit"]["bounce"]
    
    return {
        "turn_id": turn_id,
        "query": query,
        "answer": answer,
        "intent_cluster": intent,
        "user_actions": {
            "explicit": explicit,
            "implicit": implicit,
        },
    }


def generate_session(session_id: str, scenario: str) -> dict:
    """生成完整对话session"""
    
    # 场景配置
    scenario_configs = {
        "positive_explicit": {  # 明确正反馈
            "satisfaction": 0.9,
            "turns": [("pe_calculation", "satisfied"), ("pe_interpretation", "satisfied")],
        },
        "positive_implicit": {  # 隐式正反馈（无点赞但行为积极）
            "satisfaction": 0.8,
            "turns": [("pe_calculation", "satisfied")],
        },
        "negative_explicit": {  # 明确负反馈
            "satisfaction": 0.2,
            "turns": [("pe_calculation", "unsatisfied")],
        },
        "negative_implicit": {  # 隐式负反馈（跳出）
            "satisfaction": 0.3,
            "turns": [("pe_calculation", "unsatisfied")],
        },
        "sparse_feedback": {    # 稀疏反馈（无明确信号）
            "satisfaction": 0.5,
            "turns": [("pe_calculation", "neutral")],
        },
        "confused_user": {      # 困惑用户（停留长但无拷贝）
            "satisfaction": 0.4,
            "turns": [("pe_calculation", "confused")],
        },
        "follow_up_deepen": {   # 追问深入（正信号）
            "satisfaction": 0.7,
            "turns": [("pe_calculation", "satisfied"), ("pe_interpretation", "satisfied")],
        },
        "follow_up_redirect": { # 追问转向（负信号）
            "satisfaction": 0.4,
            "turns": [("pe_calculation", "unsatisfied"), ("pb_calculation", "neutral")],
        },
        "intent_correct": {     # 意图识别正确
            "satisfaction": 0.8,
            "turns": [("pe_calculation", "satisfied")],
            "intent_accuracy": [True],
        },
        "intent_wrong": {       # 意图识别错误
            "satisfaction": 0.3,
            "turns": [("pe_calculation", "unsatisfied")],
            "intent_accuracy": [False],
        },
    }
    
    config = scenario_configs[scenario]
    turns = []
    
    for i, (intent, sat_type) in enumerate(config["turns"], 1):
        turn = generate_turn(intent, sat_type, i)
        turns.append(turn)
    
    # 添加追问场景的追问内容
    if scenario == "follow_up_deepen" and len(turns) > 1:
        turns[1]["query"] = "那PE和PB有什么区别？能详细说说吗？"  # 深入追问
    elif scenario == "follow_up_redirect" and len(turns) > 1:
        turns[1]["query"] = "算了，我想问下怎么开户？"  # 转向追问
    
    # 意图正确性标注
    intent_accuracy = config.get("intent_accuracy", [True] * len(turns))
    
    return {
        "session_id": session_id,
        "scenario": scenario,
        "turns": turns,
        "ground_truth": {
            "satisfaction": config["satisfaction"],
            "intent_accuracy": intent_accuracy,
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "user_type": "professional",  # 专业用户
        },
    }


def generate_dataset(num_sessions: int = 50) -> list:
    """生成完整数据集"""
    
    # 场景分布（模拟真实反馈分布）
    scenario_distribution = {
        "positive_explicit": 0.10,    # 只有10%会明确点赞
        "positive_implicit": 0.15,    # 15%隐式正反馈
        "negative_explicit": 0.05,    # 5%明确点踩
        "negative_implicit": 0.10,    # 10%隐式负反馈
        "sparse_feedback": 0.35,      # 35%无明显反馈（沉默的大多数）
        "confused_user": 0.10,        # 10%困惑
        "follow_up_deepen": 0.08,     # 8%追问深入
        "follow_up_redirect": 0.05,   # 5%追问转向
        "intent_correct": 0.02,       # 补充意图正确案例
        "intent_wrong": 0.02,         # 补充意图错误案例
    }
    
    sessions = []
    session_idx = 1
    
    for scenario, proportion in scenario_distribution.items():
        count = int(num_sessions * proportion)
        for _ in range(count):
            session = generate_session(f"s{session_idx:03d}", scenario)
            sessions.append(session)
            session_idx += 1
    
    # 补足剩余
    while len(sessions) < num_sessions:
        scenario = random.choice(list(scenario_distribution.keys()))
        session = generate_session(f"s{session_idx:03d}", scenario)
        sessions.append(session)
        session_idx += 1
    
    return sessions


def main():
    parser = argparse.ArgumentParser(description="生成模拟对话数据")
    parser.add_argument("--num_sessions", type=int, default=50, help="生成session数量")
    parser.add_argument("--output", type=str, default="data/mock_sessions.json", help="输出文件")
    args = parser.parse_args()
    
    print(f"生成 {args.num_sessions} 个模拟对话session...")
    
    sessions = generate_dataset(args.num_sessions)
    
    # 统计
    scenario_counts = {}
    for s in sessions:
        scenario = s["scenario"]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    
    print("\n场景分布:")
    for scenario, count in sorted(scenario_counts.items()):
        print(f"  {scenario}: {count}")
    
    # 输出
    output_path = Path(__file__).parent.parent / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_path}")
    print(f"总sessions: {len(sessions)}")


if __name__ == "__main__":
    main()