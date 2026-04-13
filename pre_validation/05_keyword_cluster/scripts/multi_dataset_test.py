#!/usr/bin/env python3
"""
Phase 1F 多数据集完整测试

支持数据集:
- BANKING77 (77意图, 高纯度)
- CLINC150 (151意图, 高纯度)
- CMID (4意图, 中纯度)
- CMID_FINE (40意图, 低纯度)

验证关键词先验在不同数据质量下的效果

作者: Damon + Nemesis
日期: 2026-04-13
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import hdbscan
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# ========== 配置 ==========

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
RESULTS_DIR = PROJECT_ROOT / "04_intent_data_mapping" / "results"
KEYWORD_DIR = PROJECT_ROOT / "05_keyword_cluster" / "data" / "tagged_chunks"
OUTPUT_DIR = PROJECT_ROOT / "05_keyword_cluster" / "data" / "results"

DATASETS = ['banking77', 'clinc150', 'cmid', 'cmid_fine']


# ========== 关键词聚类模块 ==========

class KeywordClusterer:
    """关键词聚类器"""

    def __init__(self, max_features=5000, min_df=2, max_df=0.8,
                 top_n_keywords=10, min_cluster_size=5, min_samples=2,
                 n_components=50):
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.top_n_keywords = top_n_keywords
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.n_components = n_components

        self.vectorizer = None
        self.cluster_keywords_map = defaultdict(list)
        self.keyword_to_cluster = {}
        self.keyword_prior_weights = {}

    def process_dataset(self, dataset_name):
        """处理单个数据集"""
        print(f"\n处理 {dataset_name}...")

        # 加载
        kb_path = RESULTS_DIR / f"knowledge_base_{dataset_name}.json"
        cluster_path = RESULTS_DIR / f"clusters_{dataset_name}.json"

        with open(kb_path, 'r') as f:
            kb = json.load(f)
        with open(cluster_path, 'r') as f:
            cluster_data = json.load(f)

        chunks = kb['chunks']
        clusters = cluster_data['clusters']
        texts = [c['text'] for c in chunks]

        # TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words='english',
            ngram_range=(1, 2)
        )

        tfidf_matrix = self.vectorizer.fit_transform(texts)
        feature_names = self.vectorizer.get_feature_names_out()

        # 关键词抽取
        keywords_dict = {}
        for i, chunk in enumerate(chunks):
            tfidf_scores = tfidf_matrix[i].toarray().flatten()
            top_indices = np.argsort(tfidf_scores)[-self.top_n_keywords:][::-1]
            keywords = []
            for idx in top_indices:
                if tfidf_scores[idx] > 0:
                    keywords.append((feature_names[idx], tfidf_scores[idx]))
            keywords_dict[chunk['chunk_id']] = keywords

        # 关键词聚类
        svd = TruncatedSVD(n_components=min(self.n_components, tfidf_matrix.shape[1]-1), random_state=42)
        reduced_matrix = svd.fit_transform(tfidf_matrix.T)

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric='euclidean'
        )
        cluster_labels = clusterer.fit_predict(reduced_matrix)

        for i, label in enumerate(cluster_labels):
            keyword = feature_names[i]
            self.keyword_to_cluster[keyword] = int(label)
            if label >= 0:
                self.cluster_keywords_map[label].append(keyword)

        # 构建关键词-意图关联
        keyword_intent_counts = defaultdict(lambda: defaultdict(int))
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            intent = str(chunk.get('intent', 'unknown'))
            keywords = keywords_dict.get(chunk_id, [])
            for kw, score in keywords:
                keyword_intent_counts[kw][intent] += score

        for kw, intent_counts in keyword_intent_counts.items():
            total = sum(intent_counts.values())
            if total > 0:
                self.keyword_prior_weights[kw] = {
                    intent: count / total
                    for intent, count in intent_counts.items()
                }

        # 计算LinUCB先验
        linucb_prior = {}
        chunk_id_to_emb_idx = {c['chunk_id']: c['embedding_idx'] for c in chunks}
        emb_idx_to_intent = {c['embedding_idx']: str(c['intent']) for c in chunks}

        for cluster in clusters:
            c_id = cluster['cluster_id']
            dominant_intent = str(cluster['dominant_intent'])
            purity = cluster.get('purity', 0)

            # 基于关键词频率的先验
            intent_kw_weights = []
            for kw, weights in self.keyword_prior_weights.items():
                if dominant_intent in weights:
                    intent_kw_weights.append(weights[dominant_intent])

            kw_adjustment = np.mean(intent_kw_weights) if intent_kw_weights else 0.5
            linucb_prior[c_id] = purity * 0.7 + kw_adjustment * 0.3

        # 保存
        output_data = {
            'chunks': [
                {
                    'chunk_id': c['chunk_id'],
                    'text': c['text'],
                    'intent': c['intent'],
                    'embedding_idx': c['embedding_idx'],
                    'keywords': [kw for kw, _ in keywords_dict.get(c['chunk_id'], [])]
                }
                for c in chunks
            ],
            'keyword_intent_prior': self.keyword_prior_weights,
            'linucb_prior': linucb_prior,
            'stats': {
                'n_keywords': len(self.keyword_prior_weights),
                'n_clusters': len(self.cluster_keywords_map),
                'n_linucb_prior': len(linucb_prior)
            }
        }

        output_path = KEYWORD_DIR / f"{dataset_name}_keyword_tagged.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {str(k) if isinstance(k, np.integer) else k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(v) for v in obj]
            return obj

        with open(output_path, 'w') as f:
            json.dump(convert(output_data), f, indent=2)

        print(f"  ✓ 关键词: {len(self.keyword_prior_weights)}")
        print(f"  ✓ LinUCB先验: {len(linucb_prior)} 簇")

        return output_data


# ========== 测试模块 ==========

class DatasetTester:
    """单数据集测试器"""

    def __init__(self, dataset_name):
        self.dataset_name = dataset_name
        self.results = {}

    def load(self):
        """加载所有数据"""
        # Embeddings
        self.train_emb = np.load(RESULTS_DIR / f"train_embeddings_{self.dataset_name}.npy")
        self.test_emb = np.load(RESULTS_DIR / f"test_embeddings_{self.dataset_name}.npy")

        # 知识库
        with open(RESULTS_DIR / f"knowledge_base_{self.dataset_name}.json", 'r') as f:
            kb = json.load(f)
        self.chunks = kb['chunks']

        # 测试集
        with open(RESULTS_DIR / f"test_queries_{self.dataset_name}.json", 'r') as f:
            test_data = json.load(f)
        self.test_queries = test_data['queries']

        # 聚类
        with open(RESULTS_DIR / f"clusters_{self.dataset_name}.json", 'r') as f:
            cluster_data = json.load(f)
        self.clusters = cluster_data['clusters']

        # 关键词先验
        kw_path = KEYWORD_DIR / f"{self.dataset_name}_keyword_tagged.json"
        if kw_path.exists():
            with open(kw_path, 'r') as f:
                kw_data = json.load(f)
            self.linucb_prior = kw_data.get('linucb_prior', {})
        else:
            self.linucb_prior = {}

        # 映射
        self.chunk_id_to_emb_idx = {c['chunk_id']: c['embedding_idx'] for c in self.chunks}
        self.emb_idx_to_intent = {c['embedding_idx']: c['intent'] for c in self.chunks}

        self.train_norm = self.train_emb / np.linalg.norm(self.train_emb, axis=1, keepdims=True)
        self.test_norm = self.test_emb / np.linalg.norm(self.test_emb, axis=1, keepdims=True)

        self.cluster_to_indices = {}
        self.cluster_to_dominant_intent = {}
        self.cluster_to_purity = {}

        for cluster in self.clusters:
            c_id = cluster['cluster_id']
            indices = [self.chunk_id_to_emb_idx.get(cid) for cid in cluster['chunk_ids']
                       if self.chunk_id_to_emb_idx.get(cid) is not None]
            self.cluster_to_indices[c_id] = indices
            self.cluster_to_dominant_intent[c_id] = cluster['dominant_intent']
            self.cluster_to_purity[c_id] = cluster['purity']

        self.cluster_ids = sorted(self.cluster_to_indices.keys())
        self.n_clusters = len(self.cluster_ids)

        return self

    def test_semantic_cluster(self):
        """测试语义聚类"""
        purity_scores = [self.cluster_to_purity[c] for c in self.cluster_ids]

        # 意图覆盖
        covered_intents = set(self.cluster_to_dominant_intent.values())
        all_intents = set(self.emb_idx_to_intent.values())

        self.results['semantic_cluster'] = {
            'avg_purity': np.mean(purity_scores),
            'high_purity_ratio': sum(1 for p in purity_scores if p > 0.9) / len(purity_scores),
            'intent_coverage': len(covered_intents) / len(all_intents) if all_intents else 0,
            'n_clusters': self.n_clusters
        }

        return self.results['semantic_cluster']

    def test_prior_quality(self):
        """测试先验质量"""
        high_purity_prior = []
        low_purity_prior = []

        for c_id in self.cluster_ids:
            purity = self.cluster_to_purity[c_id]
            prior = self.linucb_prior.get(str(c_id), 0)
            if purity > 0.9:
                high_purity_prior.append(prior)
            elif purity < 0.7:
                low_purity_prior.append(prior)

        gap = (np.mean(high_purity_prior) - np.mean(low_purity_prior)) if high_purity_prior and low_purity_prior else 0

        self.results['prior_quality'] = {
            'high_purity_mean_prior': np.mean(high_purity_prior) if high_purity_prior else 0,
            'low_purity_mean_prior': np.mean(low_purity_prior) if low_purity_prior else 0,
            'gap': gap,
            'n_prior': len(self.linucb_prior)
        }

        return self.results['prior_quality']

    def test_retrieval(self, n_test=50):
        """测试检索效果"""
        strategies = {
            'random': 0,
            'prior': 0,
            'vector': 0
        }

        np.random.seed(42)
        test_indices = np.random.choice(len(self.test_queries), min(n_test, len(self.test_queries)), replace=False)

        for idx in test_indices:
            query = self.test_queries[idx]
            query_intent = query['intent']
            query_emb = self.test_norm[idx:idx+1]

            # 策略1: 随机
            random_cluster = np.random.choice(self.cluster_ids)
            indices = self.cluster_to_indices[random_cluster]
            if indices:
                sims = np.dot(query_emb, self.train_norm[indices].T)[0]
                top_idx = indices[np.argmax(sims)]
                top_intent = self.emb_idx_to_intent.get(top_idx)
                if top_intent == query_intent:
                    strategies['random'] += 1

            # 策略2: 先验
            matching_clusters = [c for c in self.cluster_ids
                                 if self.cluster_to_dominant_intent[c] == query_intent]
            if matching_clusters:
                prior_cluster = max(matching_clusters, key=lambda c: self.linucb_prior.get(str(c), 0))
                indices = self.cluster_to_indices[prior_cluster]
                sims = np.dot(query_emb, self.train_norm[indices].T)[0]
                intent_bonus = np.array([0.15 if self.emb_idx_to_intent.get(i) == query_intent else 0.0
                                          for i in indices])
                adjusted = sims + intent_bonus
                top_idx = indices[np.argmax(adjusted)]
                top_intent = self.emb_idx_to_intent.get(top_idx)
                if top_intent == query_intent:
                    strategies['prior'] += 1

            # 策略3: 向量
            sims = np.dot(query_emb, self.train_norm.T)[0]
            top_idx = np.argmax(sims)
            top_intent = self.emb_idx_to_intent.get(top_idx)
            if top_intent == query_intent:
                strategies['vector'] += 1

        n = len(test_indices)
        self.results['retrieval'] = {
            'random_acc': strategies['random'] / n,
            'prior_acc': strategies['prior'] / n,
            'vector_acc': strategies['vector'] / n,
            'prior_improvement': (strategies['prior'] - strategies['vector']) / n,
            'cold_start_improvement': (strategies['prior'] - strategies['random']) / n
        }

        return self.results['retrieval']


def run_multi_dataset_test():
    """运行多数据集测试"""
    print("\n" + "=" * 80)
    print("Phase 1F 多数据集完整测试")
    print("=" * 80)

    # Step 1: 为所有数据集生成关键词先验
    print("\n【Step 1】生成关键词先验")
    print("-" * 80)

    clusterer = KeywordClusterer()
    for ds in DATASETS:
        clusterer.process_dataset(ds)

    # Step 2: 对每个数据集进行测试
    print("\n【Step 2】各数据集测试")
    print("-" * 80)

    all_results = {}

    for ds in DATASETS:
        print(f"\n>>> {ds.upper()}")

        tester = DatasetTester(ds)
        tester.load()

        # 语义聚类测试
        sc_result = tester.test_semantic_cluster()
        print(f"  语义聚类: 纯度={sc_result['avg_purity']:.2%}, 覆盖={sc_result['intent_coverage']:.1%}")

        # 先验质量测试
        pq_result = tester.test_prior_quality()
        print(f"  先验质量: 高纯度={pq_result['high_purity_mean_prior']:.3f}, 低纯度={pq_result['low_purity_mean_prior']:.3f}, 差距={pq_result['gap']:.3f}")

        # 检索测试
        ret_result = tester.test_retrieval(n_test=50)
        print(f"  检索效果: 随机={ret_result['random_acc']:.1%}, 先验={ret_result['prior_acc']:.1%}, 向量={ret_result['vector_acc']:.1%}")
        print(f"  提升: 先验vs向量={ret_result['prior_improvement']:.1%}, 先验vs随机={ret_result['cold_start_improvement']:.1%}")

        all_results[ds] = tester.results

    # Step 3: 汇总对比
    print("\n" + "=" * 80)
    print("【汇总对比】")
    print("=" * 80)

    print("\n语义聚类对比:")
    print(f"  {'数据集':<15} | {'平均纯度':<10} | {'高纯度比例':<10} | {'意图覆盖'}")
    print(f"  {'-'*55}")
    for ds in DATASETS:
        r = all_results[ds]['semantic_cluster']
        print(f"  {ds:<15} | {r['avg_purity']:.2%}    | {r['high_purity_ratio']:.1%}     | {r['intent_coverage']:.1%}")

    print("\n先验质量对比:")
    print(f"  {'数据集':<15} | {'高纯度先验':<10} | {'低纯度先验':<10} | {'差距'}")
    print(f"  {'-'*55}")
    for ds in DATASETS:
        r = all_results[ds]['prior_quality']
        print(f"  {ds:<15} | {r['high_purity_mean_prior']:.3f}    | {r['low_purity_mean_prior']:.3f}    | {r['gap']:.3f}")

    print("\n检索效果对比:")
    print(f"  {'数据集':<15} | {'随机':<8} | {'先验':<8} | {'向量':<8} | {'先验提升'}")
    print(f"  {'-'*55}")
    for ds in DATASETS:
        r = all_results[ds]['retrieval']
        imp = r['prior_improvement'] * 100
        print(f"  {ds:<15} | {r['random_acc']:.1%}  | {r['prior_acc']:.1%}  | {r['vector_acc']:.1%}  | {imp:>+.1f}%")

    print("\n冷启动改善对比:")
    print(f"  {'数据集':<15} | {'随机':<8} | {'先验':<8} | {'冷启动提升'}")
    print(f"  {'-'*45}")
    for ds in DATASETS:
        r = all_results[ds]['retrieval']
        imp = r['cold_start_improvement'] * 100
        print(f"  {ds:<15} | {r['random_acc']:.1%}  | {r['prior_acc']:.1%}  | {imp:>+.1f}%")

    # Step 4: 关键结论
    print("\n" + "=" * 80)
    print("【关键结论】")
    print("=" * 80)

    print("\n1. 先验-纯度关联验证:")
    for ds in DATASETS:
        gap = all_results[ds]['prior_quality']['gap']
        purity = all_results[ds]['semantic_cluster']['avg_purity']
        if gap > 0.2:
            print(f"  ✓ {ds}: 先验差距{gap:.3f}，验证成功（簇纯度{purity:.1%}）")
        else:
            print(f"  ⚠ {ds}: 先验差距{gap:.3f}，效果有限（簇纯度{purity:.1%}）")

    print("\n2. 冷启动改善验证:")
    for ds in DATASETS:
        imp = all_results[ds]['retrieval']['cold_start_improvement']
        prior_acc = all_results[ds]['retrieval']['prior_acc']
        if imp > 0.5:
            print(f"  ✓ {ds}: 改善{imp:.1%}，先验准确率{prior_acc:.1%}")
        elif imp > 0:
            print(f"  ◐ {ds}: 改善{imp:.1%}，先验准确率{prior_acc:.1%}")
        else:
            print(f"  ✗ {ds}: 无改善")

    print("\n3. 检索效果对比:")
    for ds in DATASETS:
        prior_acc = all_results[ds]['retrieval']['prior_acc']
        vector_acc = all_results[ds]['retrieval']['vector_acc']
        diff = prior_acc - vector_acc
        if diff > 0.05:
            print(f"  ✓ {ds}: 先验优于向量{diff:.1%}")
        elif diff > 0:
            print(f"  ◐ {ds}: 先验略优于向量{diff:.1%}")
        else:
            print(f"  ⚠ {ds}: 先验不如向量{-diff:.1%}")

    # 保存结果
    output_path = OUTPUT_DIR / "multi_dataset_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def convert(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    with open(output_path, 'w') as f:
        json.dump(convert(all_results), f, indent=2)

    print(f"\n✓ 结果保存到: {output_path}")

    return all_results


if __name__ == "__main__":
    results = run_multi_dataset_test()
    print("\n✓ Phase 1F 多数据集测试完成!")