# -*- coding: utf-8 -*-
"""
论文实验数据集下载脚本
Paper Experiment Dataset Download Script

下载 5 个数据集到 data/raw/ 目录：
- CUAD (法律合同)
- eManual (产品手册, RAGBench)
- PubMedQA (生物医学)
- BioASQ (生物医学, HuggingFace 子集)
- BANKING77 (银行意图)

用法 / Usage:
    python paper/experiments/scripts/download_datasets.py
    python paper/experiments/scripts/download_datasets.py --dataset cuad
    python paper/experiments/scripts/download_datasets.py --dataset emanual pubmedqa
"""

import os
import argparse
from datasets import load_dataset


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")

ALL_DATASETS = ["cuad", "emanual", "pubmedqa", "bioasq", "banking77"]


def download_cuad():
    """下载 CUAD 数据集 (Contract Understanding Atticus Dataset)

    510 合同, 13K+ 标注, 41 类条款
    来源: theatticusproject/cuad (HuggingFace)
    """
    print("=" * 60)
    print("下载 CUAD (法律合同) ...")
    print("=" * 60)

    dataset = load_dataset("theatticusproject/cuad")
    save_path = os.path.join(RAW_DIR, "cuad")
    dataset.save_to_disk(save_path)

    for split_name, split_data in dataset.items():
        print(f"  {split_name}: {len(split_data)} 条")
    print(f"  已保存到: {save_path}")

    return dataset


def download_emanual():
    """下载 eManual 数据集 (RAGBench 子集)

    165 文档, ~1K QA pairs, 产品手册领域
    来源: galileo-ai/ragbench, emanual 配置
    """
    print("=" * 60)
    print("下载 eManual (产品手册, RAGBench) ...")
    print("=" * 60)

    dataset = load_dataset("galileo-ai/ragbench", "emanual")
    save_path = os.path.join(RAW_DIR, "emanual")
    dataset.save_to_disk(save_path)

    for split_name, split_data in dataset.items():
        print(f"  {split_name}: {len(split_data)} 条")
    print(f"  已保存到: {save_path}")

    return dataset


def download_pubmedqa():
    """下载 PubMedQA 数据集

    pqa_labeled: 1K 专家标注
    pqa_artificial: 211.3K 自动生成
    来源: qiaojin/PubMedQA (HuggingFace)
    """
    print("=" * 60)
    print("下载 PubMedQA (生物医学) ...")
    print("=" * 60)

    # 下载标注子集
    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")
    save_path_labeled = os.path.join(RAW_DIR, "pubmedqa_labeled")
    labeled.save_to_disk(save_path_labeled)
    print(f"  pqa_labeled: {len(labeled['train'])} 条")
    print(f"  已保存到: {save_path_labeled}")

    # 下载自动生成子集（规模大，用于在线学习模拟）
    print("  下载 pqa_artificial (211K, 可能需要几分钟) ...")
    artificial = load_dataset("qiaojin/PubMedQA", "pqa_artificial")
    save_path_artificial = os.path.join(RAW_DIR, "pubmedqa_artificial")
    artificial.save_to_disk(save_path_artificial)
    print(f"  pqa_artificial: {len(artificial['train'])} 条")
    print(f"  已保存到: {save_path_artificial}")

    return labeled, artificial


def download_bioasq():
    """下载 BioASQ 数据集 (HuggingFace 子集)

    生物医学 QA, 含文档+snippet 级标注
    来源: bigbio/pubmed_qa 或 BioASQ 官方

    注意: BioASQ 完整数据需注册 (bioasq.org),
    这里先下载 HuggingFace 上的公开子集
    """
    print("=" * 60)
    print("下载 BioASQ (生物医学, HuggingFace 子集) ...")
    print("=" * 60)

    try:
        dataset = load_dataset("bigbio/bioasq_task_b", "bioasq_task_b_source")
        save_path = os.path.join(RAW_DIR, "bioasq")
        dataset.save_to_disk(save_path)
        for split_name, split_data in dataset.items():
            print(f"  {split_name}: {len(split_data)} 条")
        print(f"  已保存到: {save_path}")
        return dataset
    except Exception as e:
        print(f"  BioASQ 自动下载失败: {e}")
        print("  BioASQ 完整数据需要注册: http://www.bioasq.org/")
        print("  请手动下载后放到: data/raw/bioasq/")
        print("  继续处理其他数据集...")
        return None


def download_banking77():
    """下载 BANKING77 数据集

    13,083 样本, 77 intent
    来源: PolyAI/banking77 (HuggingFace)

    注意: pre_validation/data/banking77/ 中可能已有下载
    """
    print("=" * 60)
    print("下载 BANKING77 (银行意图) ...")
    print("=" * 60)

    # 检查 pre_validation 中是否已有
    pre_val_path = os.path.join(
        SCRIPT_DIR, "..", "..", "..", "pre_validation", "data", "banking77"
    )
    if os.path.exists(pre_val_path):
        print(f"  已存在于 pre_validation: {pre_val_path}")
        print("  创建符号链接到 data/raw/ ...")
        link_path = os.path.join(RAW_DIR, "banking77")
        if not os.path.exists(link_path):
            try:
                os.symlink(os.path.abspath(pre_val_path), link_path)
                print(f"  已创建链接: {link_path} -> {pre_val_path}")
            except OSError:
                # Windows/WSL 可能不支持 symlink，直接重新下载
                print("  符号链接创建失败，重新下载...")
                dataset = load_dataset("PolyAI/banking77")
                dataset.save_to_disk(link_path)
        return None

    dataset = load_dataset("PolyAI/banking77")
    save_path = os.path.join(RAW_DIR, "banking77")
    dataset.save_to_disk(save_path)

    for split_name, split_data in dataset.items():
        print(f"  {split_name}: {len(split_data)} 条")
    print(f"  已保存到: {save_path}")

    return dataset


DOWNLOAD_FUNCS = {
    "cuad": download_cuad,
    "emanual": download_emanual,
    "pubmedqa": download_pubmedqa,
    "bioasq": download_bioasq,
    "banking77": download_banking77,
}


def main():
    parser = argparse.ArgumentParser(description="下载论文实验数据集")
    parser.add_argument(
        "--dataset",
        nargs="*",
        choices=ALL_DATASETS,
        default=None,
        help="指定要下载的数据集 (默认全部下载)",
    )
    args = parser.parse_args()

    datasets_to_download = args.dataset or ALL_DATASETS

    os.makedirs(RAW_DIR, exist_ok=True)

    print("IntentWeight 论文实验 - 数据集下载")
    print(f"数据保存目录: {os.path.abspath(RAW_DIR)}")
    print(f"待下载: {', '.join(datasets_to_download)}\n")

    results = {}
    for name in datasets_to_download:
        try:
            results[name] = DOWNLOAD_FUNCS[name]()
            print(f"  [OK] {name}\n")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}\n")
            results[name] = None

    print("\n" + "=" * 60)
    print("下载结果汇总:")
    print("=" * 60)
    for name, result in results.items():
        status = "成功" if result is not None else "失败/跳过"
        print(f"  {name}: {status}")
    print("=" * 60)
    print("\n下一步: 运行预处理脚本")
    print("  python paper/experiments/scripts/preprocess_cuad.py")
    print("  python paper/experiments/scripts/preprocess_emanual.py")
    print("  ...")


if __name__ == "__main__":
    main()
