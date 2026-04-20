# -*- coding: utf-8 -*-
"""
文件级语义聚类
File-level Semantic Clustering

对文档（而非 chunk）进行 HDBSCAN 聚类，每个文档取其 chunk embedding 的均值作为代表向量。
Cluster documents (not chunks) using HDBSCAN. Each document is represented by the mean of its chunk embeddings.
"""
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from loguru import logger


def compute_document_embeddings(
    chunk_ids: List[str],
    embeddings: np.ndarray,
    chunk_metadata: List[Dict],
) -> Tuple[List[str], np.ndarray, Dict[str, List[str]]]:
    """
    从 chunk embeddings 计算文档级 embeddings（均值聚合）
    Compute document-level embeddings by averaging chunk embeddings

    Args:
        chunk_ids: chunk ID 列表
        embeddings: chunk embedding 矩阵 (n_chunks, dim)
        chunk_metadata: 每个 chunk 的元数据，需包含 source_file

    Returns:
        (doc_source_files, doc_embeddings, doc_to_chunk_ids)
    """
    # 按 source_file 分组
    doc_chunks: Dict[str, List[int]] = defaultdict(list)
    for i, meta in enumerate(chunk_metadata):
        source_file = meta.get("source_file", "unknown")
        doc_chunks[source_file].append(i)

    doc_source_files = []
    doc_embeddings_list = []
    doc_to_chunk_ids: Dict[str, List[str]] = {}

    for source_file, indices in doc_chunks.items():
        doc_source_files.append(source_file)
        # 均值聚合
        doc_emb = np.mean(embeddings[indices], axis=0)
        doc_embeddings_list.append(doc_emb)
        doc_to_chunk_ids[source_file] = [chunk_ids[i] for i in indices]

    doc_embeddings = np.array(doc_embeddings_list)
    logger.info(f"Computed {len(doc_source_files)} document embeddings from {len(chunk_ids)} chunks")
    return doc_source_files, doc_embeddings, doc_to_chunk_ids


def fit_pca(embeddings: np.ndarray, n_components: int = 64) -> Tuple[object, np.ndarray]:
    """
    拟合 PCA 并降维
    Fit PCA and transform embeddings

    Args:
        embeddings: 原始 embedding 矩阵 (n_samples, high_dim)
        n_components: 目标维度

    Returns:
        (pca_model, reduced_embeddings)
    """
    from sklearn.decomposition import PCA

    n_samples = embeddings.shape[0]
    actual_components = min(n_components, n_samples, embeddings.shape[1])
    if actual_components < n_components:
        logger.warning(
            f"PCA n_components adjusted from {n_components} to {actual_components} "
            f"(n_samples={n_samples}, n_features={embeddings.shape[1]})"
        )

    pca = PCA(n_components=actual_components, random_state=42)
    reduced = pca.fit_transform(embeddings)
    explained = sum(pca.explained_variance_ratio_) * 100
    logger.info(f"PCA: {embeddings.shape[1]}d -> {actual_components}d, explained variance: {explained:.1f}%")
    return pca, reduced


def cluster_documents(
    reduced_embeddings: np.ndarray,
    min_cluster_size: int = 3,
    min_samples: int = 2,
) -> np.ndarray:
    """
    HDBSCAN 聚类
    HDBSCAN clustering

    Args:
        reduced_embeddings: PCA 降维后的 embedding 矩阵
        min_cluster_size: 最小聚类大小
        min_samples: 最小样本数

    Returns:
        cluster_labels: 每个文档的聚类标签（-1 为噪声）
    """
    import hdbscan

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(reduced_embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    logger.info(f"HDBSCAN: {n_clusters} clusters, {n_noise} noise points out of {len(labels)} documents")

    # 将噪声点分配到最近的聚类
    if n_noise > 0 and n_clusters > 0:
        labels = _assign_noise_to_nearest(reduced_embeddings, labels)

    return labels


def _assign_noise_to_nearest(embeddings: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """将噪声点分配到最近的聚类中心 / Assign noise points to nearest cluster center"""
    from sklearn.metrics import pairwise_distances

    labels = labels.copy()
    unique_clusters = [c for c in set(labels) if c != -1]

    # 计算每个聚类的中心
    centers = {}
    for c in unique_clusters:
        mask = labels == c
        centers[c] = embeddings[mask].mean(axis=0)

    center_matrix = np.array([centers[c] for c in unique_clusters])
    noise_mask = labels == -1

    if noise_mask.sum() > 0:
        noise_embeddings = embeddings[noise_mask]
        distances = pairwise_distances(noise_embeddings, center_matrix)
        nearest = distances.argmin(axis=1)
        labels[noise_mask] = [unique_clusters[n] for n in nearest]
        logger.info(f"Assigned {noise_mask.sum()} noise points to nearest clusters")

    return labels


def build_cluster_data(
    doc_source_files: List[str],
    labels: np.ndarray,
    reduced_embeddings: np.ndarray,
    doc_to_chunk_ids: Dict[str, List[str]],
) -> Dict[int, Dict]:
    """
    构建聚类数据结构
    Build cluster data structure

    Args:
        doc_source_files: 文档路径列表
        labels: 聚类标签
        reduced_embeddings: PCA 降维后的文档 embedding
        doc_to_chunk_ids: 文档 -> chunk IDs 映射

    Returns:
        {cluster_id: {"source_files": [...], "chunk_ids": [...], "center": [...]}}
    """
    clusters: Dict[int, Dict] = {}
    for i, (source_file, label) in enumerate(zip(doc_source_files, labels)):
        label = int(label)
        if label not in clusters:
            clusters[label] = {
                "source_files": [],
                "chunk_ids": [],
                "embeddings_pca": [],
            }
        clusters[label]["source_files"].append(source_file)
        clusters[label]["chunk_ids"].extend(doc_to_chunk_ids.get(source_file, []))
        clusters[label]["embeddings_pca"].append(reduced_embeddings[i])

    # 计算聚类中心
    for cid, cdata in clusters.items():
        embs = np.array(cdata.pop("embeddings_pca"))
        cdata["center"] = embs.mean(axis=0).tolist()
        cdata["doc_count"] = len(cdata["source_files"])
        cdata["chunk_count"] = len(cdata["chunk_ids"])

    logger.info(f"Built {len(clusters)} clusters: " +
                ", ".join(f"C{cid}({d['doc_count']}docs)" for cid, d in sorted(clusters.items())))
    return clusters


def save_pca_model(pca_model: object, path: Path):
    """保存 PCA 模型 / Save PCA model"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(pca_model, f)
    logger.info(f"PCA model saved to {path}")


def load_pca_model(path: Path) -> Optional[object]:
    """加载 PCA 模型 / Load PCA model"""
    if not path.exists():
        return None
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info(f"PCA model loaded from {path}")
    return model
