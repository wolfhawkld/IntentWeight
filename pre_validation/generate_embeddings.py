#!/usr/bin/env python3
"""
Embedding 生成脚本
使用 all-MiniLM-L6-v2 模型生成问题向量
"""

import os
import json
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

INPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/processed"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/embeddings"

def load_processed_data(name):
    """加载处理后的数据"""
    json_path = f"{INPUT_DIR}/{name.lower()}_processed.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✓ 加载 {name}: {len(data)} 条")
    return data

def generate_embeddings(data, model_name="all-MiniLM-L6-v2", batch_size=32):
    """生成 Embedding"""
    print(f"\n加载模型: {model_name}")
    
    # 加载模型
    model = SentenceTransformer(model_name)
    print(f"✓ 模型加载完成")
    print(f"  Embedding 维度: {model.get_sentence_embedding_dimension()}")
    
    # 提取文本
    texts = [item["text"] for item in data]
    
    # 生成 Embedding
    print(f"\n生成 Embedding (batch_size={batch_size})...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    print(f"✓ Embedding 生成完成: shape={embeddings.shape}")
    
    return embeddings, model.get_sentence_embedding_dimension()

def save_embeddings(embeddings, labels, splits, name, output_dir, embed_dim):
    """保存 Embedding"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存 numpy 数组
    np_path = f"{output_dir}/{name.lower()}_embeddings.npy"
    np.save(np_path, embeddings)
    print(f"✓ Embedding 保存到: {np_path}")
    
    # 保存标签和分割信息
    meta = {
        "name": name,
        "num_samples": len(embeddings),
        "embedding_dim": embed_dim,
        "labels": labels,
        "splits": splits
    }
    meta_path = f"{output_dir}/{name.lower()}_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"✓ 元数据保存到: {meta_path}")
    
    return np_path, meta_path

def main():
    print("=" * 60)
    print("IntentRoute - Embedding 生成")
    print("=" * 60)
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 模型配置
    model_name = "all-MiniLM-L6-v2"
    batch_size = 64  # GTX 1650 可以用较大的 batch
    
    # 处理 BANKING77
    print("\n" + "=" * 60)
    print("处理 BANKING77")
    print("=" * 60)
    
    banking77_data = load_processed_data("BANKING77")
    banking77_embeddings, embed_dim = generate_embeddings(
        banking77_data, 
        model_name=model_name,
        batch_size=batch_size
    )
    
    banking77_labels = [item["label"] for item in banking77_data]
    banking77_splits = [item["split"] for item in banking77_data]
    save_embeddings(
        banking77_embeddings, 
        banking77_labels, 
        banking77_splits,
        "BANKING77", 
        OUTPUT_DIR, 
        embed_dim
    )
    
    # 处理 CLINC150
    print("\n" + "=" * 60)
    print("处理 CLINC150")
    print("=" * 60)
    
    clinc150_data = load_processed_data("CLINC150")
    clinc150_embeddings, embed_dim = generate_embeddings(
        clinc150_data, 
        model_name=model_name,
        batch_size=batch_size
    )
    
    clinc150_labels = [item["label"] for item in clinc150_data]
    clinc150_splits = [item["split"] for item in clinc150_data]
    save_embeddings(
        clinc150_embeddings, 
        clinc150_labels, 
        clinc150_splits,
        "CLINC150", 
        OUTPUT_DIR, 
        embed_dim
    )
    
    # 总结
    print("\n" + "=" * 60)
    print("✓ Embedding 生成完成!")
    print("=" * 60)
    print(f"模型: {model_name}")
    print(f"Embedding 维度: {embed_dim}")
    print(f"BANKING77: {banking77_embeddings.shape}")
    print(f"CLINC150: {clinc150_embeddings.shape}")

if __name__ == "__main__":
    main()
