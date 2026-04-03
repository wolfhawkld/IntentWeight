#!/usr/bin/env python3
"""
Speech Act 闭包性验证实验

通过反例搜索验证 Speech Act 5类是否能够覆盖所有言语行为

实验设计:
1. 对大规模语料进行分类
2. 统计无法分类的样本比例
3. 人工审核"边界样本"
4. 验证闭包性假设

用法:
    python closure_test.py --data processed/*.json --output results/closure_test.json
"""

import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from collections import Counter
import random

# Speech Act 5类定义 (完整版)
SPEECH_ACT_DEFINITIONS = {
    "L_ASSERTIVE": {
        "name": "Assertive",
        "definition": "陈述事实，让听者相信某事为真",
        "direction": "Words → World",
        "illocutionary_point": "描述世界状态",
        "examples": [
            "The sky is blue.",
            "What time is it?",
            "I believe this is correct.",
            "The meeting starts at 3pm."
        ]
    },
    "L_DIRECTIVE": {
        "name": "Directive",
        "definition": "指令行为，希望听者执行某事",
        "direction": "World → Words",
        "illocutionary_point": "让听者行动",
        "examples": [
            "Please close the door.",
            "Can you help me?",
            "I need you to sign this.",
            "Let's go to the movies."
        ]
    },
    "L_COMMISSIVE": {
        "name": "Commissive",
        "definition": "承诺行为，说话者承诺未来行动",
        "direction": "World → Words",
        "illocutionary_point": "自己承诺行动",
        "examples": [
            "I will call you tomorrow.",
            "I promise to finish it.",
            "I'll be there.",
            "Consider it done."
        ]
    },
    "L_EXPRESSIVE": {
        "name": "Expressive",
        "definition": "表达行为，表达心理状态",
        "direction": "Null",
        "illocutionary_point": "表达心理状态",
        "examples": [
            "Thank you so much!",
            "I'm sorry for the delay.",
            "Congratulations!",
            "I really appreciate your help."
        ]
    },
    "L_DECLARATIVE": {
        "name": "Declarative",
        "definition": "宣告行为，通过言语改变世界状态",
        "direction": "World ↔ Words",
        "illocutionary_point": "直接改变状态",
        "examples": [
            "I hereby declare the meeting open.",
            "You're fired.",
            "I pronounce you husband and wife.",
            "The contract is now in effect."
        ]
    }
}


@dataclass
class ClassificationResult:
    """分类结果"""
    text: str
    speech_act: str
    confidence: float
    is_boundary: bool  # 是否为边界样本
    reason: str
    source: Optional[str] = None


class SpeechActClassifier:
    """增强版 Speech Act 分类器"""
    
    def __init__(self, confidence_threshold: float = 0.6):
        self.threshold = confidence_threshold
        
        # 扩展的模式定义
        self.patterns = {
            "L_DECLARATIVE": {
                "strong": ["i hereby", "i declare", "i pronounce", "i sentence",
                          "i appoint", "you are fired", "is now in effect",
                          "i certify", "i name", "i crown"],
                "medium": ["declared", "announced that", "effective immediately"]
            },
            "L_EXPRESSIVE": {
                "strong": ["thank you", "thanks", "sorry", "apologize", "appreciate",
                          "congratulations", "congrats", "i'm happy", "i'm grateful",
                          "i regret", "i'm disappointed", "wonderful", "terrible",
                          "i love it", "i hate it", "awesome", "amazing"],
                "medium": ["glad", "pleased", "unhappy", "satisfied", "grateful"]
            },
            "L_COMMISSIVE": {
                "strong": ["i will", "i promise", "i guarantee", "i commit",
                          "i assure", "i'll", "i would like to", "i plan to",
                          "i intend to", "count on me"],
                "medium": ["going to", "will be", "shall"]
            },
            "L_DIRECTIVE": {
                "strong": ["please", "can you", "could you", "would you",
                          "help me", "how do i", "how can i", "i need to",
                          "i want to", "tell me", "let me", "let's",
                          "you should", "you must", "make sure"],
                "medium": ["need", "want", "require", "request"]
            },
            "L_ASSERTIVE": {
                "strong": ["is", "are", "was", "were", "what", "where", "when",
                          "who", "which", "how many", "how much", "why", "how come",
                          "i think", "i believe", "in my opinion", "according to"],
                "medium": ["fact", "true", "false", "correct", "wrong"]
            }
        }
    
    def classify(self, text: str) -> ClassificationResult:
        """分类单个文本"""
        text_lower = text.lower()
        scores = {}
        matched_patterns = {}
        
        for speech_act, pattern_set in self.patterns.items():
            score = 0
            matches = []
            
            # 强模式匹配 (权重 3)
            for pattern in pattern_set.get("strong", []):
                if pattern in text_lower:
                    score += 3
                    matches.append(f"strong:{pattern}")
            
            # 中等模式匹配 (权重 1)
            for pattern in pattern_set.get("medium", []):
                if pattern in text_lower:
                    score += 1
                    matches.append(f"medium:{pattern}")
            
            scores[speech_act] = score
            matched_patterns[speech_act] = matches
        
        # 确定最佳分类
        max_score = max(scores.values())
        
        if max_score == 0:
            # 无法匹配任何模式 → 潜在反例
            return ClassificationResult(
                text=text,
                speech_act="UNCLASSIFIABLE",
                confidence=0.0,
                is_boundary=True,
                reason="No pattern matched - potential counterexample"
            )
        
        # 找到最佳匹配
        best_act = max(scores, key=scores.get)
        
        # 检查是否为边界样本 (多个类别分数接近)
        sorted_scores = sorted(scores.values(), reverse=True)
        is_boundary = len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) <= 1
        
        # 计算置信度
        total_score = sum(scores.values())
        confidence = scores[best_act] / total_score if total_score > 0 else 0
        
        # 置信度低于阈值 → 标记为边界样本
        if confidence < self.threshold:
            is_boundary = True
        
        return ClassificationResult(
            text=text,
            speech_act=best_act,
            confidence=round(confidence, 3),
            is_boundary=is_boundary,
            reason=f"Matched: {matched_patterns[best_act][:3]}"
        )


class ClosureTestExperiment:
    """闭包性验证实验"""
    
    def __init__(self, classifier: SpeechActClassifier):
        self.classifier = classifier
        self.results = []
        self.unclassifiable = []
        self.boundary_cases = []
    
    def run(self, data_sources: List[dict], sample_size: int = None) -> dict:
        """
        运行闭包性实验
        
        Args:
            data_sources: 数据源列表 [{"path": ..., "name": ...}]
            sample_size: 每个数据源采样数量 (None = 全部)
        """
        all_samples = []
        
        # 加载所有数据
        for source in data_sources:
            path = source["path"]
            name = source["name"]
            
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 处理不同数据格式
            if isinstance(data, list):
                samples = [item.get("text", str(item)) for item in data]
            elif isinstance(data, dict) and "results" in data:
                samples = [item.get("text", "") for item in data["results"]]
            else:
                samples = [data.get("text", str(data))]
            
            # 采样
            if sample_size and len(samples) > sample_size:
                samples = random.sample(samples, sample_size)
            
            for sample in samples:
                if sample and len(sample) > 5:  # 过滤空/过短
                    all_samples.append({"text": sample, "source": name})
        
        print(f"总样本数: {len(all_samples)}")
        
        # 分类所有样本
        for i, sample in enumerate(all_samples):
            result = self.classifier.classify(sample["text"])
            result.source = sample["source"]
            self.results.append(result)
            
            if (i + 1) % 1000 == 0:
                print(f"进度: {i+1}/{len(all_samples)}")
        
        # 分析结果
        return self.analyze()
    
    def analyze(self) -> dict:
        """分析实验结果"""
        total = len(self.results)
        
        # 统计分布
        distribution = Counter(r.speech_act for r in self.results)
        
        # 不可分类样本
        self.unclassifiable = [r for r in self.results if r.speech_act == "UNCLASSIFIABLE"]
        
        # 边界样本
        self.boundary_cases = [r for r in self.results if r.is_boundary and r.speech_act != "UNCLASSIFIABLE"]
        
        # 按数据源统计
        by_source = {}
        for r in self.results:
            source = r.source or "unknown"
            if source not in by_source:
                by_source[source] = {"total": 0, "unclassifiable": 0, "boundary": 0}
            by_source[source]["total"] += 1
            if r.speech_act == "UNCLASSIFIABLE":
                by_source[source]["unclassifiable"] += 1
            if r.is_boundary:
                by_source[source]["boundary"] += 1
        
        # 闭包率计算
        closure_rate = (total - len(self.unclassifiable)) / total if total > 0 else 0
        
        return {
            "summary": {
                "total_samples": total,
                "classified": total - len(self.unclassifiable),
                "unclassifiable": len(self.unclassifiable),
                "boundary_cases": len(self.boundary_cases),
                "closure_rate": round(closure_rate * 100, 2),
                "avg_confidence": round(sum(r.confidence for r in self.results) / total, 3) if total > 0 else 0
            },
            "distribution": dict(distribution),
            "distribution_percent": {k: round(v/total*100, 2) for k, v in distribution.items()},
            "by_source": by_source,
            "unclassifiable_samples": [
                {"text": r.text[:100], "source": r.source} 
                for r in self.unclassifiable[:50]  # 最多展示50个
            ],
            "boundary_samples": [
                {"text": r.text[:100], "speech_act": r.speech_act, "confidence": r.confidence, "source": r.source}
                for r in random.sample(self.boundary_cases, min(30, len(self.boundary_cases)))
            ]
        }


def main():
    parser = argparse.ArgumentParser(description="Speech Act 闭包性验证实验")
    parser.add_argument("--data", nargs="+", required=True, help="数据文件路径")
    parser.add_argument("--names", nargs="+", help="数据集名称 (与 --data 一一对应)")
    parser.add_argument("--sample", type=int, default=None, help="每个数据集采样数量")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--threshold", type=float, default=0.6, help="置信度阈值")
    args = parser.parse_args()
    
    # 准备数据源
    data_sources = []
    names = args.names or [f"dataset_{i}" for i in range(len(args.data))]
    
    for path, name in zip(args.data, names):
        data_sources.append({"path": path, "name": name})
    
    print("="*60)
    print("Speech Act 闭包性验证实验")
    print("="*60)
    print(f"数据源: {len(data_sources)} 个")
    for ds in data_sources:
        print(f"  - {ds['name']}: {ds['path']}")
    print(f"采样数量: {args.sample or '全部'}")
    print(f"置信度阈值: {args.threshold}")
    print()
    
    # 运行实验
    classifier = SpeechActClassifier(confidence_threshold=args.threshold)
    experiment = ClosureTestExperiment(classifier)
    results = experiment.run(data_sources, sample_size=args.sample)
    
    # 保存结果
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 打印报告
    print()
    print("="*60)
    print("实验结果")
    print("="*60)
    print(f"总样本数: {results['summary']['total_samples']}")
    print(f"成功分类: {results['summary']['classified']}")
    print(f"不可分类: {results['summary']['unclassifiable']}")
    print(f"边界样本: {results['summary']['boundary_cases']}")
    print(f"闭包率: {results['summary']['closure_rate']}%")
    print(f"平均置信度: {results['summary']['avg_confidence']}")
    print()
    
    print("分类分布:")
    for act, pct in sorted(results['distribution_percent'].items(), key=lambda x: -x[1]):
        count = results['distribution'].get(act, 0)
        print(f"  {act}: {pct}% ({count})")
    
    if results['unclassifiable_samples']:
        print()
        print(f"⚠️  不可分类样本 ({len(results['unclassifiable_samples'])} 个):")
        for i, sample in enumerate(results['unclassifiable_samples'][:10], 1):
            print(f"  {i}. [{sample['source']}] {sample['text'][:60]}...")
    
    print()
    print(f"详细结果已保存到: {output_path}")
    
    # 闭包性结论
    print()
    print("="*60)
    if results['summary']['closure_rate'] >= 99.9:
        print("✅ 闭包性验证通过: 所有样本均可分类")
    elif results['summary']['closure_rate'] >= 99:
        print("✅ 闭包性验证通过: 99%以上样本可分类")
        print("   不可分类样本需人工审核确认是否为真正反例")
    else:
        print("⚠️  闭包性存疑: 存在较多不可分类样本")
        print("   建议人工审核并考虑扩展分类体系")
    print("="*60)


if __name__ == "__main__":
    main()