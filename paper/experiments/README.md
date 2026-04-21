# 论文实验数据准备
# Paper Experiment Data Preparation

---

## 目录结构
## Directory Structure

```
paper/experiments/
├── scripts/
│   ├── download_datasets.py       # 一键下载所有数据集
│   ├── preprocess_cuad.py         # CUAD 预处理
│   ├── preprocess_emanual.py      # eManual (RAGBench) 预处理
│   ├── preprocess_pubmedqa.py     # PubMedQA 预处理
│   ├── preprocess_bioasq.py       # BioASQ 预处理
│   └── preprocess_banking77.py    # BANKING77 预处理
├── data/
│   ├── raw/                       # 下载的原始数据 (git ignored)
│   ├── processed/                 # 统一格式 (git ignored)
│   └── embeddings/                # 预计算 embedding (git ignored)
└── README.md
```

---

## 运行步骤
## Steps

### Step 1: 下载数据集

```bash
# 在项目根目录下，激活 venv
source .venv/bin/activate

# 下载全部 5 个数据集
python paper/experiments/scripts/download_datasets.py

# 或只下载指定数据集
python paper/experiments/scripts/download_datasets.py --dataset cuad emanual
```

### Step 2: 预处理

逐个运行预处理脚本，将原始数据转换为统一格式：

```bash
python paper/experiments/scripts/preprocess_cuad.py
python paper/experiments/scripts/preprocess_emanual.py
python paper/experiments/scripts/preprocess_pubmedqa.py
python paper/experiments/scripts/preprocess_bioasq.py
python paper/experiments/scripts/preprocess_banking77.py

# PubMedQA 如需包含 211K artificial 子集（用于大规模在线学习模拟）：
python paper/experiments/scripts/preprocess_pubmedqa.py --include-artificial
```

### Step 3: 验证

预处理完成后，`data/processed/` 下应有以下文件：

```
data/processed/
├── cuad_corpus.json           # CUAD 语料库
├── cuad_queries.json          # CUAD 查询 + GT
├── emanual_corpus.json        # eManual 语料库
├── emanual_queries.json       # eManual 查询 + GT
├── pubmedqa_corpus.json       # PubMedQA 语料库 (labeled only)
├── pubmedqa_queries.json      # PubMedQA 查询 + GT
├── bioasq_corpus.json         # BioASQ 语料库
├── bioasq_queries.json        # BioASQ 查询 + GT
├── banking77_corpus.json      # BANKING77 语料库
└── banking77_queries.json     # BANKING77 查询 + GT
```

---

## 统一数据格式
## Unified Data Format

### Corpus (语料库)

```json
[
  {
    "chunk_id": "cuad_c00001",
    "text": "This Agreement shall commence on...",
    "doc_id": "contract_001",
    "metadata": {"source": "cuad", "split": "train"}
  }
]
```

### Queries (查询 + GT 映射)

```json
[
  {
    "query_id": "cuad_q00001",
    "text": "What is the effective date?",
    "ground_truth_chunk_ids": ["cuad_c00001", "cuad_c00003"],
    "answer": "January 1, 2020",
    "split": "test",
    "metadata": {"source": "cuad", "answerable": true}
  }
]
```

---

## 数据集概览
## Dataset Overview

| 数据集 | 领域 | 来源 | 预计 Corpus | 预计 Queries |
|--------|------|------|------------|-------------|
| CUAD | 法律合同 | theatticusproject/cuad | ~5K-10K chunks | ~13K |
| eManual | 产品手册 | galileo-ai/ragbench (emanual) | ~165 docs | ~1K |
| PubMedQA | 生物医学 | qiaojin/PubMedQA | ~1K-211K | ~1K-211K |
| BioASQ | 生物医学 | bigbio/bioasq_task_b | ~40K snippets | ~4.7K |
| BANKING77 | 银行意图 | PolyAI/banking77 | ~10K (train) | ~3K (test) |

---

## 注意事项
## Notes

1. **BioASQ** 完整数据需要在 [bioasq.org](http://www.bioasq.org/) 注册下载。脚本会先尝试 HuggingFace 子集。
2. **PubMedQA artificial** 子集约 211K 条，下载和处理需要几分钟，默认不包含。
3. 所有 data/ 下的数据文件已在 `.gitignore` 中排除，不会提交到 git。
4. 预处理脚本会打印统计信息（chunks 数、queries 数、GT 覆盖率），请检查是否合理。

---

*创建时间: 2026-04-21*
