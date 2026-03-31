#!/usr/bin/env python3
"""
CMID Embedding 生成脚本
"""

import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer

INPUT_FILE = os.path.dirname(os.path.abspath(__file__)) + "/data/cmid/cmid_processed.json"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/embeddings"

def main():
    print("=" * 60)
    print("CMID Embedding 生成")
    print("=" * 60)
    
    # 加载数据
    print(f"\n加载数据: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✓ 加载 {len(data)} 条")
    
    # 加载模型
    model_name = "all-MiniLM-L6-v2"
    print(f"\n加载模型: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"✓ 模型加载完成")
    print(f"  Embedding 维度: {model.get_sentence_embedding_dimension()}")
    
    # 提取文本
    texts = [item["text"] for item in data]
    
    # 生成 Embedding
    print(f"\n生成 Embedding...")
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    print(f"✓ Embedding 生成完成: shape={embeddings.shape}")
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    np_path = f"{OUTPUT_DIR}/cmid_embeddings.npy"
    np.save(np_path, embeddings)
    print(f"✓ Embedding 保存到: {np_path}")
    
    # 保存元数据
    labels = [item.get("label_4", "") for item in data]
    meta = {
        "name": "CMID",
        "num_samples": len(embeddings),
        "embedding_dim": model.get_sentence_embedding_dimension(),
        "labels": labels
    }
    meta_path = f"{OUTPUT_DIR}/cmid_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"✓ 元数据保存到: {meta_path}")
    
    print("\n" + "=" * 60)
    print("✓ 完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()