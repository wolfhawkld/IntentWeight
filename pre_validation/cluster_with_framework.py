#!/usr/bin/env python3
"""
聚类 + Speech Act 框架映射分析

Phase 1B 核心任务：
1. 对 embeddings 进行 HDBSCAN 聚类
2. 分析聚类结果与 Speech Act 的映射关系
3. 评估"分类锚点 + 聚类边界"融合效果

用法:
    python cluster_with_framework.py --dataset banking77
    python cluster_with_framework.py --dataset clinc150 --min_cluster_size 15
"""

import json
import argparse
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')


@dataclass
class ClusterAnalysis:
    """聚类分析结果"""
    cluster_id: int
    size: int
    speech_act_distribution: Dict[str, float]
    dominant_speech_act: str
    purity: float  # 主类型占比
    samples: List[str]  # 示例样本


class ClusterFrameworkMapper:
    """聚类 + Speech Act 框架映射分析器"""
    
    def __init__(self, embeddings_path: str, processed_path: str, speech_act_path: str):
        """
        Args:
            embeddings_path: embeddings.npy 文件路径
            processed_path: processed.json 文件路径（包含文本和原始意图）
            speech_act_path: speech act 分类结果路径
        """
        self.embeddings_path = embeddings_path
        self.processed_path = processed_path
        self.embeddings = np.load(embeddings_path)
        with open(processed_path, 'r', encoding='utf-8') as f:
            self.samples = json.load(f)  # 样本列表，每个包含 text, label, split
        with open(speech_act_path, 'r', encoding='utf-8') as f:
            self.speech_act_data = json.load(f)
        
        # 构建索引
        self.speech_act_map = {}
        for r in self.speech_act_data.get('results', []):
            self.speech_act_map[r['text']] = {
                'speech_act': r['speech_act'],
                'confidence': r['confidence'],
                'original_intent': r.get('original_intent')
            }
        
        print(f"加载 embeddings: {self.embeddings.shape}")
        print(f"加载 samples: {len(self.samples)} 条")
        print(f"加载 speech act: {len(self.speech_act_map)} 条")
    
    def run_hdbscan(self, min_cluster_size: int = 10, min_samples: int = 5) -> np.ndarray:
        """
        运行 HDBSCAN 聚类
        
        Args:
            min_cluster_size: 最小簇大小
            min_samples: 核心点最小样本数
        
        Returns:
            labels: 聚类标签数组
        """
        import hdbscan
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        print(f"\n运行 HDBSCAN 聚类...")
        print(f"  min_cluster_size: {min_cluster_size}")
        print(f"  min_samples: {min_samples}")
        
        labels = clusterer.fit_predict(self.embeddings)
        
        # 统计聚类结果
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"\n聚类结果:")
        print(f"  簇数量: {n_clusters}")
        print(f"  噪声点: {n_noise} ({n_noise/len(labels)*100:.1f}%)")
        
        # 计算聚类质量指标
        if n_clusters > 1:
            # 只对非噪声点计算轮廓系数
            mask = labels != -1
            if mask.sum() > 0:
                from sklearn.metrics import silhouette_score
                sil_score = silhouette_score(self.embeddings[mask], labels[mask])
                print(f"  轮廓系数: {sil_score:.3f}")
        
        self.clusterer = clusterer
        self.labels = labels
        
        return labels
    
    def analyze_cluster_mapping(self) -> List[ClusterAnalysis]:
        """
        分析聚类与 Speech Act 的映射关系
        
        Returns:
            分析结果列表
        """
        analyses = []
        
        # 按簇分组
        cluster_indices = defaultdict(list)
        for i, label in enumerate(self.labels):
            cluster_indices[label].append(i)
        
        print(f"\n分析聚类-意图映射...")
        
        for cluster_id, indices in sorted(cluster_indices.items()):
            if cluster_id == -1:
                continue  # 跳过噪声
            
            # 统计 Speech Act 分布
            speech_act_counts = defaultdict(int)
            samples = []
            
            for idx in indices:
                text = self.samples[idx].get('text', '')
                samples.append(text)
                
                if text in self.speech_act_map:
                    sa = self.speech_act_map[text]['speech_act']
                    speech_act_counts[sa] += 1
            
            # 计算分布
            total = len(indices)
            speech_act_dist = {
                sa: count / total 
                for sa, count in speech_act_counts.items()
            }
            
            # 找主类型
            if speech_act_dist:
                dominant = max(speech_act_dist.items(), key=lambda x: x[1])
                dominant_sa = dominant[0]
                purity = dominant[1]
            else:
                dominant_sa = "UNKNOWN"
                purity = 0.0
            
            # 取前3个样本作为示例
            sample_texts = samples[:3]
            
            analysis = ClusterAnalysis(
                cluster_id=cluster_id,
                size=total,
                speech_act_distribution=speech_act_dist,
                dominant_speech_act=dominant_sa,
                purity=purity,
                samples=sample_texts
            )
            analyses.append(analysis)
        
        # 按大小排序
        analyses.sort(key=lambda x: -x.size)
        
        return analyses
    
    def evaluate_fusion(self, analyses: List[ClusterAnalysis]) -> Dict:
        """
        评估融合效果
        
        Returns:
            融合效果指标
        """
        # 统计簇纯度分布
        purities = [a.purity for a in analyses]
        
        # 单一类型簇（纯度 > 0.9）
        pure_clusters = [a for a in analyses if a.purity > 0.9]
        
        # 混合类型簇（纯度 < 0.7）
        mixed_clusters = [a for a in analyses if a.purity < 0.7]
        
        # Speech Act 类型覆盖
        covered_speech_acts = set()
        for a in analyses:
            covered_speech_acts.add(a.dominant_speech_act)
        
        # 分析混合簇的 Speech Act 组合
        mixed_combinations = []
        for a in mixed_clusters:
            combo = sorted(a.speech_act_distribution.keys())
            mixed_combinations.append(tuple(combo))
        
        unique_combinations = set(mixed_combinations)
        
        # 计算筛选效率（平均簇大小 / 总样本数）
        total_samples = sum(a.size for a in analyses)
        avg_cluster_size = total_samples / len(analyses) if analyses else 0
        filter_efficiency = avg_cluster_size / len(self.samples) * 100
        
        metrics = {
            "n_clusters": len(analyses),
            "avg_purity": np.mean(purities) if purities else 0,
            "avg_cluster_size": avg_cluster_size,
            "pure_clusters_count": len(pure_clusters),
            "pure_clusters_pct": len(pure_clusters) / len(analyses) * 100 if analyses else 0,
            "mixed_clusters_count": len(mixed_clusters),
            "mixed_clusters_pct": len(mixed_clusters) / len(analyses) * 100 if analyses else 0,
            "covered_speech_acts": list(covered_speech_acts),
            "unique_combinations": len(unique_combinations),
            "filter_efficiency_pct": filter_efficiency,
            "combination_examples": [
                {"cluster_id": a.cluster_id, "distribution": a.speech_act_distribution}
                for a in mixed_clusters[:10]
            ]
        }
        
        return metrics
    
    def generate_report(self, analyses: List[ClusterAnalysis], metrics: Dict) -> str:
        """
        生成分析报告
        """
        report = []
        report.append("="*60)
        report.append("聚类 + Speech Act 框架映射分析报告")
        report.append("="*60)
        
        report.append("\n## 融合效果指标")
        report.append(f"  簇数量: {metrics['n_clusters']}")
        report.append(f"  平均纯度: {metrics['avg_purity']:.2%}")
        report.append(f"  单类型簇: {metrics['pure_clusters_count']} ({metrics['pure_clusters_pct']:.1f}%)")
        report.append(f"  混合类型簇: {metrics['mixed_clusters_count']} ({metrics['mixed_clusters_pct']:.1f}%)")
        report.append(f"  Speech Act 覆盖: {metrics['covered_speech_acts']}")
        report.append(f"  筛选效率: {metrics['filter_efficiency_pct']:.2f}% (每簇平均占比)")
        
        report.append("\n## 簇详情 (前20个)")
        report.append("-"*60)
        
        for a in analyses[:20]:
            report.append(f"\n簇 {a.cluster_id} ({a.size} 样本, 纯度 {a.purity:.2%})")
            report.append(f"  主类型: {a.dominant_speech_act}")
            
            # Speech Act 分布
            dist_str = ", ".join([
                f"{sa}: {pct:.1%}" 
                for sa, pct in sorted(a.speech_act_distribution.items(), key=lambda x: -x[1])
            ])
            report.append(f"  分布: {dist_str}")
            
            # 示例
            for i, sample in enumerate(a.samples[:2]):
                report.append(f"  示例{i+1}: {sample[:50]}...")
        
        report.append("\n" + "="*60)
        report.append("结论:")
        
        if metrics['avg_purity'] > 0.8:
            report.append("  ✅ 高纯度: 聚类结果与 Speech Act 映射良好")
            report.append("  建议: 簇可作为意图细粒度扩展")
        elif metrics['avg_purity'] > 0.6:
            report.append("  ⚠️ 中等纯度: 部分簇跨越多个 Speech Act")
            report.append("  建议: 分析混合簇，可能需要调整聚类参数")
        else:
            report.append("  ❌ 低纯度: 聚类与 Speech Act 映射不明显")
            report.append("  建议: 重新设计融合策略或调整参数")
        
        return "\n".join(report)
    
    def save_results(self, analyses: List[ClusterAnalysis], metrics: Dict, output_path: str):
        """
        保存分析结果
        """
        def convert_numpy(obj):
            """转换 numpy 类型为 Python 原生类型"""
            if isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(v) for v in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            else:
                return obj
        
        output_data = {
            "metadata": {
                "embeddings_file": str(Path(self.embeddings_path).name),
                "min_cluster_size": int(self.clusterer.min_cluster_size) if hasattr(self, 'clusterer') else None,
                "min_samples": int(self.clusterer.min_samples) if hasattr(self, 'clusterer') else None,
                "total_samples": len(self.samples)
            },
            "metrics": convert_numpy(metrics),
            "clusters": convert_numpy([
                {
                    "cluster_id": int(a.cluster_id),
                    "size": int(a.size),
                    "dominant_speech_act": a.dominant_speech_act,
                    "purity": float(a.purity),
                    "speech_act_distribution": a.speech_act_distribution,
                    "samples": a.samples
                }
                for a in analyses
            ])
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="聚类 + Speech Act 框架映射分析")
    parser.add_argument("--dataset", required=True, choices=["banking77", "clinc150", "dailydialog", "cmid"],
                       help="数据集名称")
    parser.add_argument("--min_cluster_size", type=int, default=10,
                       help="HDBSCAN 最小簇大小")
    parser.add_argument("--min_samples", type=int, default=5,
                       help="HDBSCAN 核心点最小样本数")
    parser.add_argument("--output", default=None,
                       help="输出文件路径（默认自动生成）")
    args = parser.parse_args()
    
    # 确定文件路径
    base_dir = Path(__file__).parent
    embeddings_path = base_dir / "embeddings" / f"{args.dataset}_embeddings.npy"
    
    # 不同数据集的 processed 文件位置不同
    if args.dataset == "dailydialog":
        processed_path = base_dir / "data" / "dailydialog" / "processed_dailydialog.json"
    elif args.dataset == "cmid":
        processed_path = base_dir / "data" / "cmid" / "cmid_processed.json"
    else:
        processed_path = base_dir / "processed" / f"{args.dataset}_processed.json"
    
    speech_act_path = base_dir / "results" / f"speech_act_{args.dataset}.json"
    
    # 检查文件存在
    for path in [embeddings_path, processed_path, speech_act_path]:
        if not path.exists():
            print(f"错误: 文件不存在 {path}")
            return
    
    # 输出路径
    if args.output:
        output_path = args.output
    else:
        output_path = base_dir / "results" / f"cluster_mapping_{args.dataset}.json"
    
    print(f"\n数据集: {args.dataset}")
    print(f"min_cluster_size: {args.min_cluster_size}")
    print(f"min_samples: {args.min_samples}")
    
    # 初始化分析器
    mapper = ClusterFrameworkMapper(
        str(embeddings_path),
        str(processed_path),
        str(speech_act_path)
    )
    
    # 运行聚类
    labels = mapper.run_hdbscan(
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples
    )
    
    # 分析映射
    analyses = mapper.analyze_cluster_mapping()
    
    # 评估融合效果
    metrics = mapper.evaluate_fusion(analyses)
    
    # 转换 numpy 类型为 Python原生类型
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        else:
            return obj
    
    metrics = convert_types(metrics)
    
    # 生成报告
    report = mapper.generate_report(analyses, metrics)
    print("\n" + report)
    
    # 保存结果
    mapper.save_results(analyses, metrics, str(output_path))


if __name__ == "__main__":
    main()