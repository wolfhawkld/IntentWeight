#!/usr/bin/env python3
"""
数据预处理脚本
- 加载数据集
- 数据清洗
- 数据分析统计
- 保存处理后的数据
"""

import os
import json
import pandas as pd
from collections import Counter
from datasets import load_from_disk

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/data"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/processed"

def load_datasets():
    """加载已下载的数据集"""
    print("=" * 60)
    print("加载数据集...")
    print("=" * 60)
    
    # BANKING77
    banking77 = load_from_disk(f"{DATA_DIR}/banking77")
    print(f"✓ BANKING77 加载完成: 训练 {len(banking77['train'])} / 测试 {len(banking77['test'])}")
    
    # CLINC150
    clinc150 = load_from_disk(f"{DATA_DIR}/clinc150")
    print(f"✓ CLINC150 加载完成: 训练 {len(clinc150['train'])} / 验证 {len(clinc150['validation'])} / 测试 {len(clinc150['test'])}")
    
    return banking77, clinc150

def clean_text(text):
    """清洗文本"""
    if not text:
        return ""
    
    # 去除首尾空白
    text = text.strip()
    
    # 统一空格
    text = " ".join(text.split())
    
    return text

def analyze_dataset(name, dataset, text_col, label_col):
    """分析数据集"""
    print(f"\n{'='*60}")
    print(f"数据集分析: {name}")
    print(f"{'='*60}")
    
    all_data = []
    stats = {
        "name": name,
        "splits": {},
        "text_stats": {},
        "label_stats": {}
    }
    
    # 合并所有分割
    for split in dataset.keys():
        split_data = []
        for item in dataset[split]:
            text = clean_text(item[text_col])
            label = item[label_col]
            split_data.append({
                "text": text,
                "label": label,
                "split": split
            })
            all_data.append({
                "text": text,
                "label": label,
                "split": split
            })
        
        stats["splits"][split] = len(split_data)
        print(f"  {split}: {len(split_data)} 条")
    
    # 文本统计
    text_lengths = [len(d["text"]) for d in all_data]
    word_counts = [len(d["text"].split()) for d in all_data]
    
    stats["text_stats"] = {
        "total": len(all_data),
        "char_length": {
            "min": min(text_lengths),
            "max": max(text_lengths),
            "mean": sum(text_lengths) / len(text_lengths)
        },
        "word_count": {
            "min": min(word_counts),
            "max": max(word_counts),
            "mean": sum(word_counts) / len(word_counts)
        }
    }
    
    print(f"\n文本统计:")
    print(f"  总样本数: {len(all_data)}")
    print(f"  字符长度: min={min(text_lengths)}, max={max(text_lengths)}, avg={sum(text_lengths)/len(text_lengths):.1f}")
    print(f"  词数: min={min(word_counts)}, max={max(word_counts)}, avg={sum(word_counts)/len(word_counts):.1f}")
    
    # 标签统计
    label_counter = Counter([d["label"] for d in all_data])
    num_labels = len(label_counter)
    
    stats["label_stats"] = {
        "num_labels": num_labels,
        "min_samples_per_label": min(label_counter.values()),
        "max_samples_per_label": max(label_counter.values()),
        "avg_samples_per_label": sum(label_counter.values()) / num_labels
    }
    
    print(f"\n标签统计:")
    print(f"  意图类别数: {num_labels}")
    print(f"  每类样本数: min={min(label_counter.values())}, max={max(label_counter.values())}, avg={sum(label_counter.values())/num_labels:.1f}")
    
    # 标签分布
    print(f"\n样本数前5的意图:")
    for label, count in label_counter.most_common(5):
        print(f"  意图 {label}: {count} 条")
    
    print(f"\n样本数后5的意图:")
    for label, count in label_counter.most_common()[:-6:-1]:
        print(f"  意图 {label}: {count} 条")
    
    return all_data, stats

def save_processed_data(data, name, output_dir):
    """保存处理后的数据"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存为 JSON
    json_path = f"{output_dir}/{name.lower()}_processed.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 保存到: {json_path}")
    
    # 保存为 CSV (方便查看)
    df = pd.DataFrame(data)
    csv_path = f"{output_dir}/{name.lower()}_processed.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"✓ 保存到: {csv_path}")
    
    return json_path, csv_path

def save_stats(all_stats, output_dir):
    """保存统计信息"""
    os.makedirs(output_dir, exist_ok=True)
    
    stats_path = f"{output_dir}/data_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 统计信息保存到: {stats_path}")

def main():
    print("IntentRoute - 数据预处理")
    print(f"数据目录: {DATA_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 加载数据
    banking77, clinc150 = load_datasets()
    
    # 分析数据集
    banking77_data, banking77_stats = analyze_dataset(
        "BANKING77", 
        banking77, 
        text_col="text", 
        label_col="label"
    )
    
    clinc150_data, clinc150_stats = analyze_dataset(
        "CLINC150", 
        clinc150, 
        text_col="text", 
        label_col="intent"
    )
    
    # 保存处理后的数据
    print("\n" + "=" * 60)
    print("保存处理后的数据...")
    print("=" * 60)
    
    save_processed_data(banking77_data, "BANKING77", OUTPUT_DIR)
    save_processed_data(clinc150_data, "CLINC150", OUTPUT_DIR)
    
    # 保存统计信息
    all_stats = {
        "banking77": banking77_stats,
        "clinc150": clinc150_stats
    }
    save_stats(all_stats, OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("✓ 数据预处理完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
