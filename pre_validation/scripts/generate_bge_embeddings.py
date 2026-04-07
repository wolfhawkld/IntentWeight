#!/usr/bin/env python3
"""
使用 BGE-large-zh-v1.5 生成中文 Embedding
"""

import json
import argparse
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "cmid"
OUTPUT_DIR = PROJECT_ROOT / "embeddings"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5", help="模型名称")
    parser.add_argument("--batch_size", type=int, default=32, help="批大小")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"使用 {args.model} 生成 CMID Embedding")
    print("=" * 60)
    
    # 加载数据
    with open(DATA_DIR / "cmid_processed.json", "r", encoding="utf-8") as f:
        samples = json.load(f)
    
    texts = [s["text"] for s in samples]
    print(f"✓ 加载样本: {len(texts)}")
    
    # 加载模型
    print(f"\n加载模型: {args.model}")
    model = SentenceTransformer(args.model)
    print(f"✓ 模型维度: {model.get_sentence_embedding_dimension()}")
    
    # 生成 embedding
    print(f"\n生成 embedding (batch_size={args.batch_size})...")
    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # BGE 推荐归一化
        convert_to_numpy=True
    )
    
    print(f"✓ Embedding shape: {embeddings.shape}")
    
    # 保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存为 cmid_bge_embeddings.npy
    output_path = OUTPUT_DIR / "cmid_bge_embeddings.npy"
    np.save(output_path, embeddings)
    print(f"✓ 保存到: {output_path}")
    
    # 保存元数据
    meta = {
        "model": args.model,
        "num_samples": len(texts),
        "embedding_dim": embeddings.shape[1],
        "normalized": True
    }
    with open(OUTPUT_DIR / "cmid_bge_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    
    # 统计
    print(f"\n统计:")
    print(f"  均值: {embeddings.mean():.4f}")
    print(f"  标准差: {embeddings.std():.4f}")
    print(f"  范围: [{embeddings.min():.4f}, {embeddings.max():.4f}]")
    
    print("\n✓ 完成!")


if __name__ == "__main__":
    main()