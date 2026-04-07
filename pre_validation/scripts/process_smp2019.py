#!/usr/bin/env python3
"""
处理 SMP2019 数据集并生成 BGE embedding
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from collections import Counter

PROJECT_ROOT = Path("/home/damon/.openclaw/workspace/IntentWeight/pre_validation")
DATA_DIR = PROJECT_ROOT / "data" / "smp2019" / "CAISandSMP-master" / "SMP" / "source"
OUTPUT_DIR = PROJECT_ROOT / "data" / "smp2019"
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"

def main():
    print("=" * 60)
    print("处理 SMP2019 数据集")
    print("=" * 60)
    
    # 加载数据
    with open(DATA_DIR / "2019train.json", "r", encoding="utf-8") as f:
        train_data = json.load(f)
    
    # 处理
    samples = []
    for item in train_data:
        intent = f"{item['domain']}_{item['intent']}"
        samples.append({
            "text": item["text"],
            "domain": item["domain"],
            "intent": intent,
            "slots": item.get("slots", {})
        })
    
    print(f"✓ 样本数: {len(samples)}")
    
    # 统计意图
    intents = [s["intent"] for s in samples]
    intent_counter = Counter(intents)
    print(f"✓ 意图数: {len(intent_counter)}")
    
    # 保存处理后的数据
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "smp2019_processed.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f"✓ 保存到: {OUTPUT_DIR / 'smp2019_processed.json'}")
    
    # 保存元数据
    meta = {
        "num_samples": len(samples),
        "num_intents": len(intent_counter),
        "num_domains": len(set(s["domain"] for s in samples)),
        "intents": list(intent_counter.keys())
    }
    with open(EMBEDDINGS_DIR / "smp2019_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # 生成 BGE embedding
    print("\n" + "=" * 60)
    print("生成 BGE embedding")
    print("=" * 60)
    
    texts = [s["text"] for s in samples]
    
    print("加载模型...")
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    print(f"✓ 模型维度: {model.get_sentence_embedding_dimension()}")
    
    print("生成 embedding...")
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    
    print(f"✓ Embedding shape: {embeddings.shape}")
    
    # 保存
    np.save(EMBEDDINGS_DIR / "smp2019_embeddings.npy", embeddings)
    print(f"✓ 保存到: {EMBEDDINGS_DIR / 'smp2019_embeddings.npy'}")
    
    print("\n✓ 完成!")


if __name__ == "__main__":
    main()