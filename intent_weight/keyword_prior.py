# -*- coding: utf-8 -*-
"""
关键词冷启动先验
Keyword-based Cold-start Prior for LinUCB

参考 / Reference:
- IntentWeight 项目 keyword_clustering.py (Phase 1F)
- 通过 TF-IDF 关键词分析，为 LinUCB arms 计算初始权重
"""
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
from loguru import logger

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False


def extract_document_keywords(
    doc_texts: Dict[str, str],
    max_features: int = 3000,
    top_n: int = 15,
    min_df: int = 2,
    max_df: float = 0.8,
) -> Tuple[Dict[str, List[Tuple[str, float]]], object]:
    """
    提取文档级关键词
    Extract document-level keywords using TF-IDF

    Args:
        doc_texts: {source_file: concatenated_text}
        max_features: TF-IDF 最大特征数
        top_n: 每个文档提取的关键词数量
        min_df: 最小文档频率
        max_df: 最大文档频率比例

    Returns:
        (keywords_dict, vectorizer)
        keywords_dict: {source_file: [(keyword, score), ...]}
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    source_files = list(doc_texts.keys())
    texts = list(doc_texts.values())

    # 中文分词预处理
    if HAS_JIEBA:
        texts = [" ".join(jieba.cut(t)) for t in texts]

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
        ngram_range=(1, 2),
    )

    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    keywords_dict = {}
    for i, source_file in enumerate(source_files):
        scores = tfidf_matrix[i].toarray().flatten()
        top_indices = np.argsort(scores)[-top_n:][::-1]
        keywords = [
            (feature_names[idx], float(scores[idx]))
            for idx in top_indices
            if scores[idx] > 0
        ]
        keywords_dict[source_file] = keywords

    logger.info(f"Extracted keywords for {len(keywords_dict)} documents, "
                f"vocabulary size: {len(feature_names)}")
    return keywords_dict, vectorizer


def compute_cluster_priors(
    clusters: Dict[int, Dict],
    doc_keywords: Dict[str, List[Tuple[str, float]]],
) -> Dict[int, float]:
    """
    计算聚类冷启动先验权重
    Compute cluster cold-start prior weights for LinUCB

    聚类先验 = 关键词区分度加权平均
    Cluster prior = weighted average of keyword discriminability

    Args:
        clusters: {cluster_id: {"source_files": [...], "doc_count": int}}
        doc_keywords: {source_file: [(keyword, score), ...]}

    Returns:
        {cluster_id: prior_weight (0~1)}
    """
    # 收集每个聚类的关键词及其在该聚类中的出现频次
    cluster_keyword_freq: Dict[int, Counter] = {}
    global_keyword_freq: Counter = Counter()

    for cid, cdata in clusters.items():
        cluster_keyword_freq[cid] = Counter()
        for sf in cdata["source_files"]:
            for kw, score in doc_keywords.get(sf, []):
                cluster_keyword_freq[cid][kw] += score
                global_keyword_freq[kw] += score

    # 计算每个聚类的关键词区分度（discriminability）
    # discriminability = cluster_weight / global_weight
    # 高区分度意味着这个关键词主要出现在该聚类中
    priors = {}
    for cid, kw_freq in cluster_keyword_freq.items():
        if not kw_freq:
            priors[cid] = 0.5  # 无关键词的聚类给中性先验
            continue

        discriminabilities = []
        for kw, freq in kw_freq.most_common(10):  # 取 top-10 关键词
            global_freq = global_keyword_freq.get(kw, 1.0)
            disc = freq / global_freq  # 该聚类占全局的比重
            discriminabilities.append(disc)

        # 先验权重 = 平均区分度，映射到 [0.3, 0.9] 区间
        avg_disc = np.mean(discriminabilities) if discriminabilities else 0.5
        prior = 0.3 + 0.6 * min(1.0, avg_disc)
        priors[cid] = round(prior, 3)

    logger.info(f"Computed priors for {len(priors)} clusters: " +
                ", ".join(f"C{cid}={w:.3f}" for cid, w in sorted(priors.items())))
    return priors
