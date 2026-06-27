#!/usr/bin/env python3
"""
下载数据集脚本
数据集: BANKING77, CLINC150
"""

import os
from datasets import load_dataset

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/data"

def download_banking77():
    """下载 BANKING77 数据集"""
    print("=" * 50)
    print("下载 BANKING77 数据集...")
    print("=" * 50)
    
    dataset = load_dataset("banking77")
    
    # 保存到本地
    save_path = f"{DATA_DIR}/banking77"
    dataset.save_to_disk(save_path)
    
    print(f"✓ BANKING77 已保存到: {save_path}")
    print(f"  训练集: {len(dataset['train'])} 条")
    print(f"  测试集: {len(dataset['test'])} 条")
    print(f"  意图数: {dataset['train'].features['label'].num_classes}")
    
    return dataset

def download_clinc150():
    """下载 CLINC150 数据集"""
    print("\n" + "=" * 50)
    print("下载 CLINC150 数据集...")
    print("=" * 50)
    
    # CLINC150 在 HuggingFace 上叫 clinc_oos
    # "plus" 配置包含 150 个意图（不含 OOS）
    dataset = load_dataset("clinc_oos", "plus")
    
    # 保存到本地
    save_path = f"{DATA_DIR}/clinc150"
    dataset.save_to_disk(save_path)
    
    print(f"✓ CLINC150 已保存到: {save_path}")
    print(f"  训练集: {len(dataset['train'])} 条")
    print(f"  验证集: {len(dataset['validation'])} 条")
    print(f"  测试集: {len(dataset['test'])} 条")
    print(f"  意图数: {dataset['train'].features['intent'].num_classes}")
    
    return dataset

def main():
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("IntentRoute - 数据集下载")
    print(f"数据保存目录: {DATA_DIR}\n")
    
    # 下载数据集
    banking77 = download_banking77()
    clinc150 = download_clinc150()
    
    print("\n" + "=" * 50)
    print("✓ 所有数据集下载完成!")
    print("=" * 50)
    
    # 打印数据示例
    print("\nBANKING77 示例:")
    example = banking77['train'][0]
    print(f"  问题: {example['text']}")
    print(f"  意图ID: {example['label']}")
    
    print("\nCLINC150 示例:")
    example = clinc150['train'][0]
    print(f"  问题: {example['text']}")
    print(f"  意图ID: {example['intent']}")

if __name__ == "__main__":
    main()
