#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文实验数据集下载脚本 - Parquet 直接下载方式
Paper Experiment Dataset Download Script - Direct Parquet Download

直接从 HuggingFace Parquet API 下载文件，避免 datasets 库的 loading script 问题。

用法:
    python paper/experiments/scripts/download_parquet.py
"""

import os
import subprocess
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")

# Parquet 文件下载链接
PARQUET_URLS = {
    "pubmedqa_labeled": {
        "url": "https://huggingface.co/api/datasets/qiaojin/PubMedQA/parquet/pqa_labeled/train/0.parquet",
        "filename": "pubmedqa_labeled.parquet",
    },
    "pubmedqa_artificial": {
        "url": "https://huggingface.co/api/datasets/qiaojin/PubMedQA/parquet/pqa_artificial/train/0.parquet",
        "filename": "pubmedqa_artificial.parquet",
    },
    "cuad": {
        "url": "https://huggingface.co/api/datasets/theatticusproject/cuad/parquet/default/train/0.parquet",
        "filename": "cuad.parquet",
    },
    "cuad_ragbench_train": {
        "url": "https://huggingface.co/api/datasets/galileo-ai/ragbench/parquet/cuad/train/0.parquet",
        "filename": "cuad_ragbench_train.parquet",
    },
    "cuad_ragbench_test": {
        "url": "https://huggingface.co/api/datasets/galileo-ai/ragbench/parquet/cuad/test/0.parquet",
        "filename": "cuad_ragbench_test.parquet",
    },
    "cuad_ragbench_val": {
        "url": "https://huggingface.co/api/datasets/galileo-ai/ragbench/parquet/cuad/validation/0.parquet",
        "filename": "cuad_ragbench_validation.parquet",
    },
    "emanual_train": {
        "url": "https://huggingface.co/api/datasets/galileo-ai/ragbench/parquet/emanual/train/0.parquet",
        "filename": "emanual_train.parquet",
    },
    "emanual_test": {
        "url": "https://huggingface.co/api/datasets/galileo-ai/ragbench/parquet/emanual/test/0.parquet",
        "filename": "emanual_test.parquet",
    },
    "emanual_val": {
        "url": "https://huggingface.co/api/datasets/galileo-ai/ragbench/parquet/emanual/validation/0.parquet",
        "filename": "emanual_validation.parquet",
    },
}

# 代理设置（从环境变量读取，或使用默认）
PROXY = os.environ.get("HTTPS_PROXY", os.environ.get("HTTP_PROXY", "http://127.0.0.1:7897"))


def download_file(url: str, output_path: str, proxy: str = None) -> bool:
    """使用 curl 下载文件，支持断点续传并在 HTTP 错误时失败。

    - ``-C -``: 断点续传，适合 HuggingFace 大 parquet 文件中断后继续下载
    - ``-f``: HTTP 4xx/5xx 时返回非零状态，避免把错误页保存成 parquet
    """
    cmd = [
        "curl",
        "-L",
        "-C", "-",
        "-f",
        "-o", output_path,
        "-s",
        "--connect-timeout", "30",
    ]
    if proxy:
        cmd.extend(["-x", proxy])
    cmd.append(url)
    
    print(f"  下载: {url}")
    print(f"  保存: {output_path}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  错误: {result.stderr}")
        return False
    
    # 检查文件大小
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"  完成: {size / 1024 / 1024:.2f} MB")
        return True
    return False


def verify_parquet(filepath: str) -> bool:
    """验证 parquet 文件是否有效"""
    try:
        import pandas as pd
        df = pd.read_parquet(filepath)
        print(f"  验证: {len(df)} 行, {len(df.columns)} 列")
        return True
    except Exception as e:
        print(f"  验证失败: {e}")
        return False


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    
    print("=" * 60)
    print("IntentWeight 论文实验 - Parquet 数据集下载")
    print("=" * 60)
    print(f"数据保存目录: {os.path.abspath(RAW_DIR)}")
    print(f"代理: {PROXY}")
    print()
    
    results = {}
    for name, info in PARQUET_URLS.items():
        print(f"\n[{name}]")
        output_path = os.path.join(RAW_DIR, info["filename"])
        
        # 检查是否已下载；必须先验证 parquet，有损坏文件时继续下载/续传
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 1000:  # 至少 1KB
                print(f"  已存在: {size / 1024 / 1024:.2f} MB，开始校验...")
                if verify_parquet(output_path):
                    results[name] = "已存在"
                    continue
                print("  已存在文件校验失败，将尝试断点续传/重新下载")
        
        success = download_file(info["url"], output_path, PROXY)
        if success and verify_parquet(output_path):
            results[name] = "成功"
        elif success:
            results[name] = "下载成功但校验失败"
        else:
            results[name] = "失败"
    
    print("\n" + "=" * 60)
    print("下载结果汇总:")
    print("=" * 60)
    for name, status in results.items():
        print(f"  {name}: {status}")
    
    # 列出目录内容
    print("\n" + "=" * 60)
    print("数据目录内容:")
    print("=" * 60)
    for f in os.listdir(RAW_DIR):
        path = os.path.join(RAW_DIR, f)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            print(f"  {f}: {size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()