#!/usr/bin/env python3
"""
Contextual Bandit 完整验证

对比：
1. 增量更新（之前的实现）
2. Contextual Bandit（LinUCB）
3. Thompson Sampling

验证指标：
- 奖励-满意度相关性
- 选择准确率
- 探索效率
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from contextual_bandit import (
    ContextualBanditRLUpdater,
    DialogueSession
)


def generate_test_sessions(num_sessions: int = 20) -> List[Dict]:
    """
    生成测试会话
    
    包含多种场景，验证 Bandit 的学习和探索能力
    """
    
    # 定义 chunk-intent 真实对应关系（ground truth）
    ground_truth = {
        "chunk_001": ["医疗试验用药原材料申请审批", "原料申请"],
        "chunk_002": ["药物研发CRO流程", "CRO外包"],
        "chunk_003": ["原料制备流程", "制备工艺"],
    }
    
    # 模拟查询模板
    query_templates = {
        "chunk_001": [
            "试验用药原材料申请怎么走？",
            "原材料审批流程是什么？",
            "如何申请试验用药的原料？",
            "原料申请需要哪些材料？",
        ],
        "chunk_002": [
            "CRO流程是什么？",
            "药物研发外包怎么做？",
            "CRO公司选择标准？",
            "研发外包流程？",
        ],
        "chunk_003": [
            "原料制备要注意什么？",
            "制备工艺流程？",
            "原料生产工艺？",
            "制备过程质量控制？",
        ]
    }
    
    # 生成会话
    sessions = []
    
    for i in range(num_sessions):
        # 随机选择一个"正确"的 chunk
        true_chunk = np.random.choice(list(ground_truth.keys()))
        query = np.random.choice(query_templates[true_chunk])
        
        # 模拟不同的反馈场景
        scenario = np.random.choice(
            ["positive", "negative", "neutral", "clarify"],
            p=[0.5, 0.15, 0.25, 0.1]
        )
        
        if scenario == "positive":
            # 正反馈：匹配正确
            matched_chunk = true_chunk
            reward = np.random.uniform(0.7, 0.95)
            satisfaction = np.random.uniform(0.8, 1.0)
        
        elif scenario == "negative":
            # 负反馈：匹配错误
            other_chunks = [c for c in ground_truth.keys() if c != true_chunk]
            matched_chunk = np.random.choice(other_chunks)
            reward = np.random.uniform(0.1, 0.35)
            satisfaction = np.random.uniform(0.1, 0.4)
        
        elif scenario == "neutral":
            # 中性：匹配正确但反馈一般
            matched_chunk = true_chunk
            reward = np.random.uniform(0.4, 0.6)
            satisfaction = np.random.uniform(0.5, 0.7)
        
        else:  # clarify
            # 澄清：先匹配错误，澄清后正确
            # 这个场景在多轮对话中处理
            other_chunks = [c for c in ground_truth.keys() if c != true_chunk]
            wrong_chunk = np.random.choice(other_chunks)
            
            sessions.append({
                "session_id": f"s{i:03d}",
                "turns": [
                    {
                        "query": query,
                        "matched_chunk": wrong_chunk,
                        "matched_intent": ground_truth[wrong_chunk][0],
                        "reward": 0.2
                    },
                    {
                        "query": f"我是问{ground_truth[true_chunk][0]}",
                        "matched_chunk": true_chunk,
                        "matched_intent": ground_truth[true_chunk][0],
                        "reward": 0.8
                    }
                ],
                "ground_truth_chunk": true_chunk,
                "satisfaction": 0.75
            })
            continue
        
        sessions.append({
            "session_id": f"s{i:03d}",
            "turns": [{
                "query": query,
                "matched_chunk": matched_chunk,
                "matched_intent": ground_truth[matched_chunk][0],
                "reward": reward
            }],
            "ground_truth_chunk": true_chunk,
            "satisfaction": satisfaction
        })
    
    return sessions


def evaluate_bandit(
    bandit_updater: ContextualBanditRLUpdater,
    test_sessions: List[Dict]
) -> Dict:
    """
    评估 Bandit 模型
    
    让 Bandit 实际做选择，而不是用预设的 matched_chunk
    
    指标：
    1. 选择准确率：选对 chunk 的比例
    2. 累积奖励
    3. 探索次数
    """
    
    correct_selections = 0
    total_selections = 0
    explore_count = 0
    
    rewards = []
    
    for session in test_sessions:
        for turn in session["turns"]:
            query = turn["query"]
            ground_truth = session.get("ground_truth_chunk")
            
            # 获取所有候选 chunks
            all_chunks = list(bandit_updater.bandit.arms.keys())
            
            # 记录选择前的置信度
            pre_conf = bandit_updater.get_chunk_confidence(ground_truth) if ground_truth else 0
            
            # Bandit 选择
            selected_chunk, score, top_k = bandit_updater.select_chunks(
                query, 
                candidate_chunks=all_chunks,
                top_k=3
            )
            
            # 计算这个选择的"真实奖励"
            if selected_chunk == ground_truth:
                # 选对了
                reward = 0.85
                correct_selections += 1
            else:
                # 选错了
                reward = 0.25
            
            rewards.append(reward)
            
            # 更新 Bandit（在线学习）
            context = bandit_updater.get_context(query)
            bandit_updater.bandit.update(selected_chunk, context, reward)
            
            total_selections += 1
    
    return {
        "accuracy": correct_selections / total_selections if total_selections > 0 else 0,
        "avg_reward": np.mean(rewards),
        "total_selections": total_selections,
        "correct_selections": correct_selections
    }


def run_comparison():
    """
    对比不同方法
    """
    
    print("=" * 70)
    print("Contextual Bandit 验证")
    print("=" * 70)
    
    # 初始化数据
    clustering_result = {
        "clusters": [
            {
                "cluster_id": "c001",
                "intent_label": "医疗试验用药原材料申请审批",
                "chunks": ["chunk_001"],
                "confidence": 0.65  # 初始置信度偏低
            },
            {
                "cluster_id": "c002",
                "intent_label": "药物研发CRO流程",
                "chunks": ["chunk_002"],
                "confidence": 0.65
            },
            {
                "cluster_id": "c003",
                "intent_label": "原料制备流程",
                "chunks": ["chunk_003"],
                "confidence": 0.65
            }
        ]
    }
    
    # 测试不同的探索策略
    strategies = [
        ("linucb", "LinUCB (α=1.0)"),
        ("thompson", "Thompson Sampling"),
        ("epsilon_greedy", "ε-greedy (ε=0.1)")
    ]
    
    # 生成测试数据
    print("\n[Step 1] 生成测试数据...")
    test_sessions = generate_test_sessions(num_sessions=30)
    print(f"  生成 {len(test_sessions)} 个测试会话")
    
    results = {}
    
    for strategy_key, strategy_name in strategies:
        print(f"\n{'='*70}")
        print(f"策略: {strategy_name}")
        print("=" * 70)
        
        # 初始化 Bandit
        bandit = ContextualBanditRLUpdater(
            context_dim=384,
            exploration=strategy_key,
            batch_size=5,
            storage_path=f"data/bandit_{strategy_key}.json"
        )
        bandit.init_from_clustering(clustering_result)
        
        print(f"\n[Step 2] 训练阶段 - 处理反馈...")
        
        # 训练阶段：处理会话反馈
        train_sessions = test_sessions[:20]
        
        for session_data in train_sessions:
            session = DialogueSession(session_data["session_id"])
            session.turns = session_data["turns"]
            session.is_complete = True
            
            bandit.add_session(session)
        
        print(f"  处理了 {len(train_sessions)} 个训练会话")
        
        # 测试阶段：评估选择
        print(f"\n[Step 3] 测试阶段 - 评估选择...")
        
        test_subset = test_sessions[20:]
        eval_result = evaluate_bandit(bandit, test_subset)
        
        print(f"  选择准确率: {eval_result['accuracy']:.2%}")
        print(f"  平均奖励: {eval_result['avg_reward']:.3f}")
        print(f"  正确选择: {eval_result['correct_selections']}/{eval_result['total_selections']}")
        
        # 查看学习到的置信度
        print(f"\n[Step 4] 学习到的 chunk 置信度:")
        for chunk_id in ["chunk_001", "chunk_002", "chunk_003"]:
            conf = bandit.get_chunk_confidence(chunk_id)
            intents = bandit.get_top_intents(chunk_id)
            print(f"  {chunk_id}: {conf:.3f} ({intents[0] if intents else 'N/A'})")
        
        results[strategy_key] = {
            "name": strategy_name,
            "stats": bandit.get_stats(),
            "evaluation": eval_result
        }
    
    # 汇总对比
    print("\n" + "=" * 70)
    print("汇总对比")
    print("=" * 70)
    
    print(f"\n{'策略':<25} {'准确率':>10} {'平均奖励':>10} {'正确选择':>10}")
    print("-" * 60)
    
    for strategy_key, result in results.items():
        eval_r = result["evaluation"]
        print(f"{result['name']:<25} {eval_r['accuracy']:>10.2%} {eval_r['avg_reward']:>10.3f} {eval_r['correct_selections']:>10}")
    
    # 保存结果
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_sessions": len(test_sessions),
        "strategies": results
    }
    
    report_path = Path("results/contextual_bandit_validation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n报告已保存: {report_path}")
    
    return results


if __name__ == "__main__":
    run_comparison()