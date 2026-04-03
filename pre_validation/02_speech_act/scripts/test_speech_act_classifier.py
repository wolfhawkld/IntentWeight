#!/usr/bin/env python3
"""
Speech Act Classification Test Script

测试 Speech Act 分类器在不同清晰度问题上的表现

用法:
    python test_speech_act_classifier.py --data data/test_speech_act_100.json --backend rule|llm

输出:
    - 总体准确率
    - 各 Speech Act 类别准确率
    - 不同清晰度问题的准确率
    - 置信度分布分析
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Speech Act 分类规则 (简化版，用于快速测试)
SPEECH_ACT_RULES = {
    "L_ASSERTIVE": {
        "keywords": ["是多少", "是什么", "是谁", "在哪里", "什么时候", "有多少", "哪个", "哪些", "怎样", "如何", "为什么"],
        "patterns": ["？$", "吗[？?]?$", "是什么呢", "是谁呢"]
    },
    "L_DIRECTIVE": {
        "keywords": ["请帮我", "帮我", "请给我", "给我", "请帮我", "帮我", "能不能", "可以吗", "请"],
        "patterns": ["^请", "^帮我", "^帮我", "^能不能", "^可以"]
    },
    "L_COMMISSIVE": {
        "keywords": ["我会", "我保证", "我承诺", "我答应", "我一定"],
        "patterns": ["^我会", "^我保证", "^我承诺", "^我答应"]
    },
    "L_EXPRESSIVE": {
        "keywords": ["谢谢", "感谢", "对不起", "抱歉", "祝贺", "恭喜", "太好了", "太棒了", "很失望", "很欣赏"],
        "patterns": ["^谢谢", "^感谢", "^对不起", "^抱歉", "^祝贺", "^恭喜"]
    },
    "L_DECLARATIVE": {
        "keywords": ["我宣布", "我任命", "我辞职", "即日起", "正式"],
        "patterns": ["^我宣布", "^我任命", "^我辞职", "正式.*结束", "即.*生效"]
    }
}


def rule_based_classify(question: str) -> Tuple[str, float]:
    """
    基于规则的 Speech Act 分类
    
    返回: (speech_act_id, confidence)
    """
    scores = defaultdict(float)
    
    for speech_act, rules in SPEECH_ACT_RULES.items():
        # 关键词匹配
        for keyword in rules["keywords"]:
            if keyword in question:
                scores[speech_act] += 0.3
        
        # 模式匹配
        import re
        for pattern in rules["patterns"]:
            if re.search(pattern, question):
                scores[speech_act] += 0.4
    
    if not scores:
        # 默认归类为 Assertive
        return ("L_ASSERTIVE", 0.5)
    
    # 选择得分最高的
    best_act = max(scores, key=scores.get)
    confidence = min(scores[best_act], 1.0)
    
    return (best_act, confidence)


def load_test_data(data_path: str) -> Dict:
    """加载测试数据"""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_classifier(
    samples: List[Dict],
    classify_func,
    verbose: bool = False
) -> Dict:
    """
    评估分类器
    
    返回评估结果字典
    """
    results = {
        "total": len(samples),
        "correct": 0,
        "by_speech_act": defaultdict(lambda: {"correct": 0, "total": 0}),
        "by_clarity": defaultdict(lambda: {"correct": 0, "total": 0}),
        "confidence_analysis": {
            "high_conf_correct": 0,
            "high_conf_total": 0,
            "low_conf_correct": 0,
            "low_conf_total": 0,
        },
        "errors": []
    }
    
    for sample in samples:
        question = sample["question"]
        expected_act = sample["speech_act"]
        expected_conf = sample.get("expected_confidence", 0.8)
        clarity = sample["clarity"]
        
        # 分类
        predicted_act, confidence = classify_func(question)
        
        # 统计
        is_correct = (predicted_act == expected_act)
        if is_correct:
            results["correct"] += 1
        
        # 按 Speech Act 统计
        results["by_speech_act"][expected_act]["total"] += 1
        if is_correct:
            results["by_speech_act"][expected_act]["correct"] += 1
        
        # 按清晰度统计
        results["by_clarity"][clarity]["total"] += 1
        if is_correct:
            results["by_clarity"][clarity]["correct"] += 1
        
        # 置信度分析
        if expected_conf >= 0.8:
            results["confidence_analysis"]["high_conf_total"] += 1
            if is_correct:
                results["confidence_analysis"]["high_conf_correct"] += 1
        else:
            results["confidence_analysis"]["low_conf_total"] += 1
            if is_correct:
                results["confidence_analysis"]["low_conf_correct"] += 1
        
        # 记录错误
        if not is_correct and verbose:
            results["errors"].append({
                "question": question,
                "expected": expected_act,
                "predicted": predicted_act,
                "clarity": clarity
            })
    
    return results


def print_results(results: Dict):
    """打印评估结果"""
    print("\n" + "="*60)
    print("Speech Act 分类测试结果")
    print("="*60)
    
    # 总体准确率
    accuracy = results["correct"] / results["total"] * 100
    print(f"\n📊 总体准确率: {accuracy:.1f}% ({results['correct']}/{results['total']})")
    
    # 按 Speech Act 分类
    print("\n📋 各类别准确率:")
    print("-"*40)
    for act, stats in sorted(results["by_speech_act"].items()):
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
            bar = "█" * int(acc / 5) + "░" * (20 - int(acc / 5))
            print(f"  {act:15} │{bar}│ {acc:5.1f}% ({stats['correct']:2}/{stats['total']:2})")
    
    # 按清晰度分类
    print("\n🔍 不同清晰度准确率:")
    print("-"*40)
    clarity_names = {
        "clear": "清晰问题",
        "moderate": "略带模糊",
        "vague_entity": "实体歧义",
        "vague_intent": "意图模糊"
    }
    for clarity, stats in sorted(results["by_clarity"].items()):
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
            name = clarity_names.get(clarity, clarity)
            print(f"  {name:10} │ {acc:5.1f}% ({stats['correct']:2}/{stats['total']:2})")
    
    # 置信度分析
    print("\n📈 预期置信度分析:")
    print("-"*40)
    high = results["confidence_analysis"]
    if high["high_conf_total"] > 0:
        high_acc = high["high_conf_correct"] / high["high_conf_total"] * 100
        print(f"  高预期置信度 (≥0.8): {high_acc:.1f}% ({high['high_conf_correct']}/{high['high_conf_total']})")
    if high["low_conf_total"] > 0:
        low_acc = high["low_conf_correct"] / high["low_conf_total"] * 100
        print(f"  低预期置信度 (<0.8): {low_acc:.1f}% ({high['low_conf_correct']}/{high['low_conf_total']})")
    
    # 错误样本
    if results["errors"]:
        print(f"\n❌ 错误样本 ({len(results['errors'])}个):")
        print("-"*40)
        for err in results["errors"][:10]:  # 只显示前10个
            print(f"  Q: {err['question'][:30]}...")
            print(f"     期望: {err['expected']} → 预测: {err['predicted']}")
            print()


def main():
    parser = argparse.ArgumentParser(description="测试 Speech Act 分类器")
    parser.add_argument("--data", default="data/test_speech_act_100.json", help="测试数据路径")
    parser.add_argument("--backend", choices=["rule", "llm"], default="rule", help="分类后端")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    args = parser.parse_args()
    
    # 加载数据
    print(f"📂 加载测试数据: {args.data}")
    data = load_test_data(args.data)
    samples = data["samples"]
    print(f"   总样本数: {len(samples)}")
    
    # 选择分类器
    if args.backend == "rule":
        classify_func = rule_based_classify
        print("🔧 使用规则分类器")
    else:
        # TODO: 实现 LLM 分类器
        print("⚠️ LLM 分类器未实现，使用规则分类器")
        classify_func = rule_based_classify
    
    # 评估
    print("\n🧪 开始评估...")
    results = evaluate_classifier(samples, classify_func, verbose=args.verbose)
    
    # 打印结果
    print_results(results)
    
    return results


if __name__ == "__main__":
    main()