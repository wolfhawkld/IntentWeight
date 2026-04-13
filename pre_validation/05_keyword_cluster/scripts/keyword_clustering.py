#!/usr/bin/env python3
"""
关键词聚类模块 - Phase 1F (冷启动优化版)

功能：
1. TF-IDF/KeyBERT 关键词提取
2. HDBSCAN 关键词聚类
3. 关键词-意图关联矩阵构建
4. LinUCB 冷启动先验计算

核心目标：为 LinUCB 提供初始化先验，加速冷启动收敛

作者: Damon + Nemesis
日期: 2026-04-13
"""

import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import hdbscan
from collections import defaultdict, Counter
import argparse
import warnings
warnings.filterwarnings('ignore')


class KeywordClusterer:
    """关键词聚类器 - Phase 1F 增强版"""

    def __init__(self,
                 max_features: int = 5000,
                 min_df: int = 2,
                 max_df: float = 0.8,
                 top_n_keywords: int = 10,
                 min_cluster_size: int = 5,
                 min_samples: int = 2,
                 n_components: int = 50,
                 use_keybert: bool = False):
        """
        初始化关键词聚类器

        Args:
            max_features: TF-IDF 最大特征数
            min_df: 最小文档频率
            max_df: 最大文档频率比例
            top_n_keywords: 每个 chunk 提取的关键词数量
            min_cluster_size: HDBSCAN 最小簇大小
            min_samples: HDBSCAN 最小样本数
            n_components: SVD 降维维度
            use_keybert: 是否使用 KeyBERT（需安装）
        """
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.top_n_keywords = top_n_keywords
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.n_components = n_components
        self.use_keybert = use_keybert

        self.vectorizer = None
        self.svd = None
        self.clusterer = None
        self.keyword_to_cluster = {}
        self.cluster_keywords_map = defaultdict(list)

        # Phase 1F 新增：关键词-意图关联
        self.keyword_intent_matrix = None
        self.keyword_prior_weights = {}

    def extract_keywords_tfidf(self, texts: list) -> tuple:
        """
        使用 TF-IDF 提取关键词

        Args:
            texts: 文本列表

        Returns:
            (keywords_dict, tfidf_matrix, feature_names)
        """
        print(f"[KeywordClusterer] 初始化 TF-IDF 向量化器...")
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words='english',
            ngram_range=(1, 2)  # 单词 + 双词组
        )

        print(f"[KeywordClusterer] 向量化 {len(texts)} 个文本...")
        tfidf_matrix = self.vectorizer.fit_transform(texts)

        print(f"[KeywordClusterer] TF-IDF 矩阵形状: {tfidf_matrix.shape}")

        # 获取特征词列表
        feature_names = self.vectorizer.get_feature_names_out()

        # 为每个文本提取 Top-N 关键词
        keywords_dict = {}
        for i in range(len(texts)):
            # 获取该文本的 TF-IDF 值
            tfidf_scores = tfidf_matrix[i].toarray().flatten()

            # 获取 Top-N 关键词索引
            top_indices = np.argsort(tfidf_scores)[-self.top_n_keywords:][::-1]

            # 提取关键词（过滤零值）
            keywords = []
            for idx in top_indices:
                if tfidf_scores[idx] > 0:
                    keywords.append((feature_names[idx], tfidf_scores[idx]))

            keywords_dict[f"chunk_{i:05d}"] = keywords

        return keywords_dict, tfidf_matrix, feature_names

    def fit_keyword_clusters(self, tfidf_matrix: np.ndarray) -> dict:
        """
        对关键词进行 HDBSCAN 聚类

        Args:
            tfidf_matrix: TF-IDF 矩阵

        Returns:
            dict: {keyword: cluster_label}
        """
        print(f"[KeywordClusterer] SVD 降维到 {self.n_components} 维...")
        self.svd = TruncatedSVD(n_components=self.n_components, random_state=42)
        reduced_matrix = self.svd.fit_transform(tfidf_matrix.T)  # 对特征词聚类

        print(f"[KeywordClusterer] 降维后矩阵形状: {reduced_matrix.shape}")

        print(f"[KeywordClusterer] HDBSCAN 聚类...")
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric='euclidean',
            cluster_selection_method='eom'
        )

        # 对特征词向量聚类
        cluster_labels = self.clusterer.fit_predict(reduced_matrix)

        # 构建关键词-簇映射
        feature_names = self.vectorizer.get_feature_names_out()
        for i, label in enumerate(cluster_labels):
            keyword = feature_names[i]
            self.keyword_to_cluster[keyword] = int(label)
            if label >= 0:  # 排除噪声点
                self.cluster_keywords_map[label].append(keyword)

        # 统计聚类结果
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = sum(1 for l in cluster_labels if l == -1)

        print(f"[KeywordClusterer] 聚类完成:")
        print(f"  - 簇数量: {n_clusters}")
        print(f"  - 噪声点: {n_noise} ({n_noise/len(cluster_labels)*100:.1f}%)")
        print(f"  - 关键词总数: {len(feature_names)}")

        return self.keyword_to_cluster

    def build_keyword_intent_matrix(self,
                                     keywords_dict: dict,
                                     chunks: list,
                                     semantic_clusters: dict = None) -> dict:
        """
        构建关键词-意图关联矩阵（Phase 1F 核心）

        目标：计算每个关键词在各意图/语义簇中的频率，
             作为 LinUCB 初始化先验

        Args:
            keywords_dict: {chunk_id: [(keyword, score), ...]}
            chunks: chunk 数据列表
            semantic_clusters: 语义聚类数据（可选）

        Returns:
            keyword_prior_weights: {keyword: {intent: weight}}
        """
        print(f"[KeywordClusterer] 构建关键词-意图关联矩阵...")

        # 统计关键词在各意图中的出现频率
        keyword_intent_counts = defaultdict(lambda: defaultdict(int))
        intent_total = defaultdict(int)

        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            intent = str(chunk.get('intent', 'unknown'))

            intent_total[intent] += 1

            keywords = keywords_dict.get(chunk_id, [])
            for kw, score in keywords:
                keyword_intent_counts[kw][intent] += score

        # 计算关键词-意图权重（归一化）
        keyword_prior_weights = {}

        for kw, intent_counts in keyword_intent_counts.items():
            total = sum(intent_counts.values())
            if total > 0:
                weights = {}
                for intent, count in intent_counts.items():
                    # 权重 = 关键词在该意图中的频率 / 关键词总频率
                    weights[intent] = count / total
                keyword_prior_weights[kw] = weights

        self.keyword_prior_weights = keyword_prior_weights

        # 统计
        print(f"[KeywordClusterer] 关键词-意图关联统计:")
        print(f"  - 关键词总数: {len(keyword_prior_weights)}")
        print(f"  - 意图总数: {len(intent_total)}")

        # 计算 Top 关键词（按意图区分度）
        keyword_discriminability = {}
        for kw, weights in keyword_prior_weights.items():
            # 区分度 = max_weight - mean_other_weights
            max_w = max(weights.values())
            mean_w = np.mean(list(weights.values()))
            discriminability = max_w - mean_w
            keyword_discriminability[kw] = discriminability

        # 打印高区分度关键词
        sorted_kw = sorted(keyword_discriminability.items(), key=lambda x: -x[1])[:10]
        print(f"\n  Top-10 高区分度关键词:")
        for kw, disc in sorted_kw:
            top_intent = max(keyword_prior_weights[kw].items(), key=lambda x: x[1])
            print(f"    '{kw}': 区分度 {disc:.3f}, 主意图 {top_intent[0]} ({top_intent[1]:.2%})")

        return keyword_prior_weights

    def assign_chunk_clusters(self, keywords_dict: dict) -> dict:
        """
        为每个 chunk 分配关键词簇标签

        Args:
            keywords_dict: {chunk_id: [(keyword, score), ...]}

        Returns:
            dict: {chunk_id: cluster_info}
        """
        chunk_clusters = {}

        for chunk_id, keywords in keywords_dict.items():
            # 找到该 chunk 关键词所属的簇
            cluster_scores = defaultdict(float)

            for kw, score in keywords:
                if kw in self.keyword_to_cluster:
                    cluster_label = self.keyword_to_cluster[kw]
                    if cluster_label >= 0:  # 排除噪声
                        cluster_scores[cluster_label] += score

            # 选择得分最高的簇作为主簇
            if cluster_scores:
                primary_cluster = max(cluster_scores, key=cluster_scores.get)
                chunk_clusters[chunk_id] = {
                    'primary_cluster': primary_cluster,
                    'cluster_scores': dict(cluster_scores),
                    'keywords': [kw for kw, _ in keywords]
                }
            else:
                chunk_clusters[chunk_id] = {
                    'primary_cluster': -1,  # 噪声
                    'cluster_scores': {},
                    'keywords': [kw for kw, _ in keywords]
                }

        return chunk_clusters

    def compute_linucb_prior(self,
                             cluster_data: dict,
                             keyword_prior_weights: dict,
                             n_clusters: int) -> dict:
        """
        计算 LinUCB 初始化先验

        将关键词权重映射到语义簇级别，
        作为 LinUCB 各臂的初始权重

        Args:
            cluster_data: 语义聚类数据（包含簇-意图映射）
            keyword_prior_weights: 关键词-意图权重
            n_clusters: LinUCB 臂数量

        Returns:
            linucb_prior: {cluster_id: initial_weight}
        """
        print(f"[KeywordClusterer] 计算 LinUCB 初始化先验...")

        # 构建簇-意图映射
        cluster_intent_map = {}
        for cluster in cluster_data.get('clusters', []):
            cluster_id = cluster['cluster_id']
            dominant_intent = str(cluster['dominant_intent'])
            intent_dist = cluster.get('intent_distribution', {})

            # 将 intent_distribution 的 key 转为 str
            intent_dist_str = {str(k): v for k, v in intent_dist.items()}

            cluster_intent_map[cluster_id] = {
                'dominant_intent': dominant_intent,
                'intent_distribution': intent_dist_str,
                'purity': cluster.get('purity', 0)
            }

        # 计算每个簇的初始权重
        linucb_prior = {}

        for cluster_id, cluster_info in cluster_intent_map.items():
            dominant_intent = cluster_info['dominant_intent']
            purity = cluster_info['purity']

            # 方法1: 基于簇纯度的初始权重
            # 纯度高的簇，初始权重更高
            base_weight = purity

            # 方法2: 基于关键词频率的调整
            # 计算该簇主导意图下的关键词平均权重
            intent_kw_weights = []
            for kw, weights in keyword_prior_weights.items():
                if dominant_intent in weights:
                    intent_kw_weights.append(weights[dominant_intent])

            if intent_kw_weights:
                kw_adjustment = np.mean(intent_kw_weights)
            else:
                kw_adjustment = 0.5

            # 融合
            initial_weight = base_weight * 0.7 + kw_adjustment * 0.3
            linucb_prior[cluster_id] = initial_weight

        self.linucb_prior = linucb_prior

        # 统计
        print(f"[KeywordClusterer] LinUCB 先验统计:")
        print(f"  - 簇数量: {len(linucb_prior)}")
        weights = list(linucb_prior.values())
        print(f"  - 权重范围: [{min(weights):.3f}, {max(weights):.3f}]")
        print(f"  - 权重均值: {np.mean(weights):.3f}")

        # 打印高权重簇
        sorted_prior = sorted(linucb_prior.items(), key=lambda x: -x[1])[:5]
        print(f"\n  Top-5 高权重簇:")
        for cluster_id, weight in sorted_prior:
            cluster_info = cluster_intent_map.get(cluster_id, {})
            intent = cluster_info.get('dominant_intent', '?')
            purity = cluster_info.get('purity', 0)
            print(f"    簇 {cluster_id}: 权重 {weight:.3f}, 意图 {intent}, 纯度 {purity:.2f}")

        return linucb_prior

    def process_dataset(self,
                        knowledge_base_path: str,
                        cluster_path: str,
                        output_path: str):
        """
        处理完整数据集

        Args:
            knowledge_base_path: 知识库 JSON 文件路径
            cluster_path: 语义聚类 JSON 文件路径
            output_path: 输出文件路径
        """
        print(f"[KeywordClusterer] 加载知识库: {knowledge_base_path}")

        with open(knowledge_base_path, 'r') as f:
            kb = json.load(f)

        chunks = kb['chunks']
        texts = [c['text'] for c in chunks]

        print(f"[KeywordClusterer] 加载聚类数据: {cluster_path}")

        with open(cluster_path, 'r') as f:
            cluster_data = json.load(f)

        print(f"[KeywordClusterer] 处理 {len(chunks)} 个 chunks...")

        # Step 1: 提取关键词
        keywords_dict, tfidf_matrix, feature_names = self.extract_keywords_tfidf(texts)

        # Step 2: 对关键词聚类
        kw_cluster_map = self.fit_keyword_clusters(tfidf_matrix)

        # Step 3: 构建关键词-意图关联矩阵
        keyword_prior_weights = self.build_keyword_intent_matrix(
            keywords_dict, chunks, cluster_data
        )

        # Step 4: 计算 LinUCB 初始化先验
        n_clusters = len(cluster_data.get('clusters', []))
        linucb_prior = self.compute_linucb_prior(
            cluster_data, keyword_prior_weights, n_clusters
        )

        # Step 5: 为 chunks 分配簇标签
        chunk_clusters = self.assign_chunk_clusters(keywords_dict)

        # Step 6: 扩展 chunks 数据
        tagged_chunks = []
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            cluster_info = chunk_clusters.get(chunk_id, {})

            # 计算该 chunk 的关键词先验权重
            kw_prior = {}
            for kw in cluster_info.get('keywords', []):
                if kw in keyword_prior_weights:
                    kw_prior[kw] = keyword_prior_weights[kw]

            tagged_chunk = {
                'chunk_id': chunk_id,
                'text': chunk['text'],
                'intent': chunk['intent'],
                'embedding_idx': chunk['embedding_idx'],
                'keywords': cluster_info.get('keywords', []),
                'keyword_cluster': cluster_info.get('primary_cluster', -1),
                'keyword_cluster_scores': cluster_info.get('cluster_scores', {}),
                'keyword_prior_weights': kw_prior
            }
            tagged_chunks.append(tagged_chunk)

        # 保存结果
        output_data = {
            'chunks': tagged_chunks,
            'keyword_clusters': {
                'n_clusters': len(self.cluster_keywords_map),
                'cluster_keywords': dict(self.cluster_keywords_map),
                'keyword_to_cluster': self.keyword_to_cluster
            },
            'keyword_intent_prior': keyword_prior_weights,
            'linucb_prior': linucb_prior,
            'stats': {
                'total_chunks': len(chunks),
                'n_keyword_clusters': len(self.cluster_keywords_map),
                'noise_ratio': sum(1 for c in tagged_chunks if c['keyword_cluster'] == -1) / len(tagged_chunks),
                'n_keywords': len(keyword_prior_weights),
                'n_intents': len(set(c['intent'] for c in chunks))
            }
        }

        # 转换numpy类型为原生Python类型
        def convert_to_native(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {str(k) if isinstance(k, np.integer) else k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(v) for v in obj]
            return obj

        output_data = convert_to_native(output_data)

        print(f"[KeywordClusterer] 保存结果到: {output_path}")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        # 打印统计
        self._print_stats(tagged_chunks, linucb_prior)

        return output_data

    def _print_stats(self, tagged_chunks: list, linucb_prior: dict):
        """打印统计信息"""
        # 簇分布
        cluster_counts = defaultdict(int)
        for chunk in tagged_chunks:
            cluster_counts[chunk['keyword_cluster']] += 1

        print("\n[KeywordClusterer] 簇分布统计:")
        print(f"  - 总簇数: {len(cluster_counts) - (1 if -1 in cluster_counts else 0)}")
        print(f"  - 噪声 chunk: {cluster_counts.get(-1, 0)}")

        # Top-10 大簇
        sorted_clusters = sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True)
        print(f"\n  Top-10 大簇:")
        for cluster, count in sorted_clusters[:10]:
            if cluster >= 0:
                keywords = self.cluster_keywords_map.get(cluster, [])[:5]
                print(f"    簇 {cluster}: {count} chunks, 关键词: {keywords}")

        # 簇纯度分析（基于 intent）
        cluster_intents = defaultdict(lambda: defaultdict(int))
        for chunk in tagged_chunks:
            if chunk['keyword_cluster'] >= 0:
                cluster_intents[chunk['keyword_cluster']][chunk['intent']] += 1

        purity_scores = []
        for cluster, intent_counts in cluster_intents.items():
            total = sum(intent_counts.values())
            max_intent = max(intent_counts.values())
            purity = max_intent / total if total > 0 else 0
            purity_scores.append(purity)

        avg_purity = np.mean(purity_scores) if purity_scores else 0
        print(f"\n  平均簇纯度（基于 intent）: {avg_purity:.2%}")

        # LinUCB 先验分布
        print(f"\n  LinUCB 先验权重分布:")
        weights = list(linucb_prior.values())
        print(f"    高权重簇 (>0.8): {sum(1 for w in weights if w > 0.8)}")
        print(f"    中权重簇 (0.5-0.8): {sum(1 for w in weights if 0.5 <= w <= 0.8)}")
        print(f"    低权重簇 (<0.5): {sum(1 for w in weights if w < 0.5)}")


def main():
    parser = argparse.ArgumentParser(description='关键词聚类模块 - Phase 1F')
    parser.add_argument('--input', type=str,
                        default='pre_validation/04_intent_data_mapping/results/knowledge_base_banking77.json',
                        help='输入知识库文件路径')
    parser.add_argument('--cluster', type=str,
                        default='pre_validation/04_intent_data_mapping/results/clusters_banking77.json',
                        help='语义聚类文件路径')
    parser.add_argument('--output', type=str,
                        default='pre_validation/05_keyword_cluster/data/tagged_chunks/banking77_keyword_tagged.json',
                        help='输出文件路径')
    parser.add_argument('--max_features', type=int, default=5000)
    parser.add_argument('--top_n', type=int, default=10)
    parser.add_argument('--min_cluster_size', type=int, default=5)

    args = parser.parse_args()

    # 初始化聚类器
    clusterer = KeywordClusterer(
        max_features=args.max_features,
        top_n_keywords=args.top_n,
        min_cluster_size=args.min_cluster_size
    )

    # 处理数据集
    clusterer.process_dataset(args.input, args.cluster, args.output)

    print("\n✓ Phase 1F 关键词聚类完成!")


if __name__ == '__main__':
    main()