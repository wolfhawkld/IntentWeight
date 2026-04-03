#!/usr/bin/env python3
"""
RAG + Bandit 对比验证

设计有挑战性的场景：
- RAG Top-1 召回可能错误
- 正确答案在 Top-K 中
- Bandit 通过反馈学习纠正

对比：
- 纯 RAG（只用向量相似度）
- RAG + Bandit（向量召回 + 用户反馈优化）
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

sys.path.append(str(Path(__file__).parent))
from validate_rag_bandit import RAGBanditSystem


def create_ambiguous_queries() -> List[Dict]:
    """
    创建歧义查询
    
    这些查询的特点：
    1. RAG Top-1 可能召回到相似的但错误的文档
    2. 正确答案在 Top-3 中
    3. 用户反馈可以帮助纠正
    """
    
    queries = [
        # 歧义查询 1: "申请流程" 太泛
        {
            "query": "申请流程是什么？",
            "ground_truth": "chunk_001",  # 用户实际想问原料申请
            "rag_might_return": "chunk_005",  # RAG 可能返回药品注册
            "user_clarification": "我指的是试验用药原料申请",
            "scenario": "ambiguity"
        },
        
        # 歧义查询 2: "审批" 有多个相关文档
        {
            "query": "审批需要多长时间？",
            "ground_truth": "chunk_001",  # 用户想问原料审批
            "rag_might_return": "chunk_005",  # RAG 可能返回注册审批
            "user_clarification": "我说的是原料审批",
            "scenario": "ambiguity"
        },
        
        # 歧义查询 3: "临床试验" 相关
        {
            "query": "临床试验怎么做？",
            "ground_truth": "chunk_004",  # 用户想问方案设计
            "rag_might_return": "chunk_002",  # RAG 可能返回 CRO 外包
            "user_clarification": "我想问方案设计的要点",
            "scenario": "ambiguity"
        },
        
        # 相似文档混淆
        {
            "query": "外包流程有哪些步骤？",
            "ground_truth": "chunk_002",
            "rag_might_return": "chunk_004",  # 都涉及临床试验
            "user_clarification": "我指的是找 CRO 外包",
            "scenario": "confusion"
        },
        
        # 新意图：用户提出文档没覆盖的问题
        {
            "query": "制备原料的温度控制标准是什么？",
            "ground_truth": "chunk_003",
            "rag_might_return": "chunk_001",  # 都涉及原料
            "user_clarification": "我说的是制备过程的温度",
            "scenario": "refinement"
        }
    ]
    
    return queries


def run_comparison_validation():
    """
    对比验证：展示 Bandit 如何纠正 RAG 错误
    """
    
    print("=" * 70)
    print("RAG vs RAG+Bandit 对比验证")
    print("=" * 70)
    
    # 初始化两个系统进行对比
    print("\n[Step 1] 初始化系统...")
    
    # 系统 A: 纯 RAG（不学习）
    rag_only = RAGBanditSystem(embedding_dim=384, rag_top_k=3)
    
    # 系统 B: RAG + Bandit（会学习）
    rag_bandit = RAGBanditSystem(embedding_dim=384, rag_top_k=3)
    
    # 添加相同的知识库
    from validate_rag_bandit import create_knowledge_base
    kb = create_knowledge_base()
    
    for doc in kb:
        rag_only.add_document(doc["chunk_id"], doc["content"], doc["intent"])
        rag_bandit.add_document(doc["chunk_id"], doc["content"], doc["intent"])
    
    print(f"  知识库: {len(kb)} 个文档")
    
    # 测试查询
    queries = create_ambiguous_queries()
    
    print("\n[Step 2] 第一轮测试（Bandit 未学习）...")
    
    first_round = []
    
    for i, q in enumerate(queries):
        print(f"\n--- 查询 {i+1}: {q['query']} ---")
        print(f"  正确答案: {q['ground_truth']}")
        
        # 纯 RAG
        rag_result = rag_only.query(q["query"], q["ground_truth"])
        
        # RAG + Bandit（第一轮，还没学习）
        bandit_result = rag_bandit.query(q["query"], q["ground_truth"])
        
        print(f"  RAG Top-1: {rag_result['rag_top1']} {'✅' if rag_result['rag_correct'] else '❌'}")
        print(f"  Bandit: {bandit_result['bandit_selected']} {'✅' if bandit_result['bandit_correct'] else '❌'}")
        
        # 显示候选
        if bandit_result["candidates"]:
            print(f"  候选列表:")
            for chunk_id, score in bandit_result["candidates"][:3]:
                marker = "✅" if chunk_id == q["ground_truth"] else "  "
                print(f"    {marker} {chunk_id}: {score:.3f}")
        
        first_round.append({
            "query": q["query"],
            "ground_truth": q["ground_truth"],
            "rag_correct": rag_result["rag_correct"],
            "bandit_correct": bandit_result["bandit_correct"]
        })
    
    # 第一轮统计
    rag_correct_r1 = sum(1 for r in first_round if r["rag_correct"])
    bandit_correct_r1 = sum(1 for r in first_round if r["bandit_correct"])
    
    print(f"\n第一轮统计:")
    print(f"  RAG 准确率: {rag_correct_r1}/{len(queries)}")
    print(f"  Bandit 准确率: {bandit_correct_r1}/{len(queries)}")
    
    # 模拟用户反馈，让 Bandit 学习
    print("\n[Step 3] 用户反馈学习阶段...")
    
    for i, q in enumerate(queries):
        # 模拟用户澄清后的反馈
        # 如果 Bandit 选错了，给负反馈
        # 如果 Bandit 选对了，给正反馈
        
        result = rag_bandit.query(q["query"], q["ground_truth"])
        
        if result["bandit_correct"]:
            reward = 0.85
            print(f"  查询 {i+1}: 选对了，奖励={reward}")
        else:
            reward = 0.25
            print(f"  查询 {i+1}: 选错了，奖励={reward}")
            
            # 额外：给正确答案正向信号
            rag_bandit.update_from_feedback(
                q["ground_truth"],
                q["query"],
                0.90  # 正确答案的奖励
            )
        
        # 更新 Bandit
        if result["bandit_selected"]:
            rag_bandit.update_from_feedback(
                result["bandit_selected"],
                q["query"],
                reward
            )
    
    # 第二轮测试（Bandit 已学习）
    print("\n[Step 4] 第二轮测试（Bandit 已学习）...")
    
    second_round = []
    
    for i, q in enumerate(queries):
        print(f"\n--- 查询 {i+1}: {q['query']} ---")
        
        # 纯 RAG（不变）
        rag_result = rag_only.query(q["query"], q["ground_truth"])
        
        # RAG + Bandit（已学习）
        bandit_result = rag_bandit.query(q["query"], q["ground_truth"])
        
        print(f"  RAG Top-1: {rag_result['rag_top1']} {'✅' if rag_result['rag_correct'] else '❌'}")
        print(f"  Bandit: {bandit_result['bandit_selected']} {'✅' if bandit_result['bandit_correct'] else '❌'}")
        
        # 显示改进
        improved = False
        if not first_round[i]["bandit_correct"] and bandit_result["bandit_correct"]:
            improved = True
            print(f"  🎯 Bandit 纠正了错误！")
        
        second_round.append({
            "query": q["query"],
            "ground_truth": q["ground_truth"],
            "rag_correct": rag_result["rag_correct"],
            "bandit_correct": bandit_result["bandit_correct"],
            "improved": improved
        })
    
    # 最终统计
    print("\n" + "=" * 70)
    print("最终统计")
    print("=" * 70)
    
    rag_correct_r2 = sum(1 for r in second_round if r["rag_correct"])
    bandit_correct_r2 = sum(1 for r in second_round if r["bandit_correct"])
    improved_count = sum(1 for r in second_round if r.get("improved"))
    
    print(f"\n第一轮:")
    print(f"  RAG 准确率: {rag_correct_r1}/{len(queries)} ({rag_correct_r1/len(queries):.1%})")
    print(f"  Bandit 准确率: {bandit_correct_r1}/{len(queries)} ({bandit_correct_r1/len(queries):.1%})")
    
    print(f"\n第二轮:")
    print(f"  RAG 准确率: {rag_correct_r2}/{len(queries)} ({rag_correct_r2/len(queries):.1%})")
    print(f"  Bandit 准确率: {bandit_correct_r2}/{len(queries)} ({bandit_correct_r2/len(queries):.1%})")
    
    print(f"\nBandit 改进:")
    print(f"  纠正错误数: {improved_count}")
    print(f"  准确率提升: {(bandit_correct_r2 - bandit_correct_r1)/len(queries):.1%}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "rag_accuracy_r1": rag_correct_r1 / len(queries),
            "bandit_accuracy_r1": bandit_correct_r1 / len(queries),
            "rag_accuracy_r2": rag_correct_r2 / len(queries),
            "bandit_accuracy_r2": bandit_correct_r2 / len(queries),
            "improved_count": improved_count
        },
        "first_round": first_round,
        "second_round": second_round
    }
    
    report_path = Path("results/rag_bandit_comparison.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    run_comparison_validation()