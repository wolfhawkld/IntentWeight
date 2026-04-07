#!/usr/bin/env python3
"""
使用 BGE-large-zh-v1.5 生成中文 Embedding (快速版 - 部分样本)
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "cmid"
OUTPUT_DIR = PROJECT_ROOT / "embeddings"

def main():
    print("=" * 60)
    print("BGE-large-zh-v1.5 生成 CMID Embedding (快速验证)")
    print("=" * 60)
    
    # 加载数据
    with open(DATA_DIR / "cmid_processed.json", "r", encoding="utf-8") as f:
        samples = json.load(f)
    
    # 使用前 2000 样本做快速验证
    N_SAMPLES = 2000
    texts = [s["text"] for s in samples[:N_SAMPLES]]
    labels = [s["label_4"] for s in samples[:N_SAMPLES]]
    
    print(f"✓ 加载样本: {len(texts)} (快速验证)")
    
    # 加载模型
    print(f"\n加载模型: BAAI/bge-large-zh-v1.5")
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    print(f"✓ 模型维度: {model.get_sentence_embedding_dimension()}")
    
    # 生成 embedding
    print(f"\n生成 embedding...")
    embeddings = model.encode(
        texts,
        batch_size=64,  # 增大批次
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    
    print(f"✓ Embedding shape: {embeddings.shape}")
    
    # 保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存样本
    subset_data = {
        "samples": samples[:N_SAMPLES],
        "embeddings_path": "cmid_bge_embeddings_2k.npy"
    }
    
    output_path = OUTPUT_DIR / "cmid_bge_embeddings_2k.npy"
    np.save(output_path, embeddings)
    print(f"✓ 保存到: {output_path}")
    
    # 保存样本信息
    with open(OUTPUT_DIR / "cmid_bge_samples_2k.json", "w", encoding="utf-8") as f:
        json.dump(subset_data, f, ensure_ascii=False, indent=2)
    
    # 快速聚类验证
    print("\n" + "=" * 60)
    print("快速聚类验证")
    print("=" * 60)
    
    import hdbscan
    from collections import Counter
    
    # 聚类
    clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=5, metric='euclidean')
    labels_pred = clusterer.fit_predict(embeddings)
    
    # 计算纯度
    n_clusters = len(set(labels_pred)) - (1 if -1 in labels_pred else 0)
    n_noise = list(labels_pred).count(-1)
    
    print(f"簇数量: {n_clusters}")
    print(f"噪声点: {n_noise} ({n_noise/len(labels_pred)*100:.1f}%)")
    
    # 每个簇的纯度
    cluster_labels = {}
    for i, (true_label, pred_label) in enumerate(zip(labels, labels_pred)):
        if pred_label == -1:
            continue
        if pred_label not in cluster_labels:
            cluster_labels[pred_label] = []
        cluster_labels[pred_label].append(true_label)
    
    purities = []
    for cluster_id, true_labels in cluster_labels.items():
        counter = Counter(true_labels)
        purity = counter.most_common(1)[0][1] / len(true_labels)
        purities.append(purity)
    
    avg_purity = np.mean(purities) if purities else 0
    print(f"平均纯度: {avg_purity:.2%}")
    
    # 对比原模型
    print(f"\n对比 all-MiniLM-L6-v2: 纯度 66%, 噪声 76%")
    print(f"BGE-large-zh 提升: 纯度 +{avg_purity-0.66:.1%}, 噪声 -{0.76-n_noise/len(labels_pred):.1%}")
    
    print("\n✓ 完成!")


if __name__ == "__main__":
    main()