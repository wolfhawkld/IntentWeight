#!/usr/bin/env python3
"""
Phase 2: 对比实验

对比三种方案的完整效果：
1. 纯语义检索
2. 纯簇筛选
3. 簇筛选 + Bandit 精排

输入:
  - results/evaluation_{dataset}.json
  - Phase 1C 的 Bandit 模型

输出:
  - results/comparison_{dataset}.json
"""

import os
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# 项目根目录 (scripts -> 04 -> pre_validation -> IntentWeight)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = Path(__file__).parent.parent / "results"
PHASE1C_DIR = PROJECT_ROOT / "pre_validation" / "03_feedback_signal"


def load_evaluation_results(dataset: str) -> Dict:
    """加载评估结果"""
    path = RESULTS_DIR / f"evaluation_{dataset}.json"
    with open(path, "r") as f:
        return json.load(f)


def compare_methods(evaluation_results: Dict) -> Dict:
    """
    对比三种方法
    
    Returns:
        对比结果
    """
    semantic = evaluation_results["semantic_retrieval"]["metrics"]
    fusion = evaluation_results["cluster_semantic_fusion"]["metrics"]
    cluster_mapping = evaluation_results["cluster_mapping"]["metrics"]
    
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "methods": [
            {
                "name": "pure_semantic",
                "description": "纯语义检索（无筛选）",
                "metrics": {
                    "top_1_accuracy": semantic["top_1_accuracy"],
                    "top_3_accuracy": semantic["top_3_accuracy"],
                    "top_5_accuracy": semantic["top_5_accuracy"],
                    "top_10_accuracy": semantic["top_10_accuracy"],
                    "mrr": semantic["mrr"],
                    "recall_range": "100%"
                }
            },
            {
                "name": "cluster_semantic_fusion",
                "description": "簇筛选 + 语义检索",
                "metrics": {
                    "top_1_accuracy": fusion["top_1_accuracy"],
                    "top_3_accuracy": fusion["top_3_accuracy"],
                    "top_5_accuracy": fusion["top_5_accuracy"],
                    "top_10_accuracy": fusion["top_10_accuracy"],
                    "mrr": fusion["mrr"],
                    "recall_range": "~5%",
                    "cluster_recall": cluster_mapping["cluster_recall"]
                }
            }
        ],
        "comparison": {}
    }
    
    # 计算提升
    for metric in ["top_1_accuracy", "top_5_accuracy", "mrr"]:
        improvement = fusion[metric] - semantic[metric]
        comparison["comparison"][metric] = {
            "semantic": semantic[metric],
            "fusion": fusion[metric],
            "improvement": improvement,
            "improvement_pct": improvement / semantic[metric] if semantic[metric] > 0 else 0
        }
    
    return comparison


def print_comparison(comparison: Dict):
    """打印对比结果"""
    print("\n" + "=" * 70)
    print("Phase 2 对比实验结果")
    print("=" * 70)
    
    print(f"\n{'方法':<30} {'Top-1':>10} {'Top-5':>10} {'MRR':>10} {'召回范围':>12}")
    print("-" * 70)
    
    for method in comparison["methods"]:
        m = method["metrics"]
        print(f"{method['description']:<30} "
              f"{m['top_1_accuracy']:>10.1%} "
              f"{m['top_5_accuracy']:>10.1%} "
              f"{m['mrr']:>10.3f} "
              f"{m['recall_range']:>12}")
    
    print("\n" + "-" * 70)
    print("提升分析:")
    print("-" * 70)
    
    for metric, data in comparison["comparison"].items():
        print(f"  {metric}:")
        print(f"    纯语义: {data['semantic']:.3f}")
        print(f"    融合:   {data['fusion']:.3f}")
        print(f"    提升:   {data['improvement']:+.3f} ({data['improvement_pct']:+.1%})")


def save_comparison(comparison: Dict, dataset: str):
    """保存对比结果"""
    output_path = RESULTS_DIR / f"comparison_{dataset}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 对比结果保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="对比实验")
    parser.add_argument("--dataset", type=str, required=True,
                        choices=["banking77", "clinc150", "cmid"],
                        help="数据集名称")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Phase 2 Step 4: 对比实验 - {args.dataset}")
    print("=" * 60)
    
    # 加载评估结果
    evaluation_results = load_evaluation_results(args.dataset)
    
    # 对比
    comparison = compare_methods(evaluation_results)
    
    # 打印
    print_comparison(comparison)
    
    # 保存
    save_comparison(comparison, args.dataset)
    
    print("\n✓ 对比实验完成!")


if __name__ == "__main__":
    main()