# 论文实验数据准备
# Paper Experiment Data Preparation

---

## 目录结构
## Directory Structure

```
paper/experiments/
├── scripts/
│   ├── download_parquet.py        # 通过 HuggingFace Parquet API 下载实验数据
│   ├── preprocess_ragbench.py     # eManual/CUAD (RAGBench) 预处理
│   ├── preprocess_pubmedqa.py     # PubMedQA 预处理
│   ├── preprocess_bioasq.py       # BioASQ 预处理
│   ├── preprocess_banking77.py    # BANKING77 预处理
│   ├── validate_processed.py      # 统一 processed 数据校验
│   ├── retrieval_metrics.py       # Recall/MRR/nDCG 评估
│   ├── bm25_baseline.py           # BM25 静态检索 baseline
│   ├── dense_baseline.py          # dense embedding 静态检索 baseline
│   └── hybrid_baseline.py         # BM25+dense RRF hybrid baseline
├── data/
│   ├── raw/                       # 下载的原始数据 (git ignored)
│   ├── processed/                 # 统一格式 (git ignored)
│   └── embeddings/                # 预计算 embedding (git ignored)
├── results/                       # baseline metrics/rankings/summary
└── README.md
```

---

## 运行步骤
## Steps

### Step 1: 下载数据集

```bash
# 在项目根目录下，激活 venv
source .venv/bin/activate

# 下载/校验 parquet 数据集
python paper/experiments/scripts/download_parquet.py
```

### Step 2: 预处理

逐个运行预处理脚本，将原始数据转换为统一格式：

```bash
python paper/experiments/scripts/preprocess_pubmedqa.py
python paper/experiments/scripts/preprocess_banking77.py
python paper/experiments/scripts/preprocess_ragbench.py --dataset emanual
python paper/experiments/scripts/preprocess_ragbench.py --dataset cuad

# BioASQ 如需纳入正式实验：
python paper/experiments/scripts/preprocess_bioasq.py

# PubMedQA 如需包含 211K artificial 子集（用于大规模在线学习模拟）：
python paper/experiments/scripts/preprocess_pubmedqa.py --include-artificial
```

### Step 3: 验证

```bash
python paper/experiments/scripts/validate_processed.py --dataset all
```

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

### Step 4: 静态检索 baseline

当前已实现三类静态检索 baseline：

```bash
python paper/experiments/scripts/bm25_baseline.py --dataset pubmedqa,banking77,emanual --top-k 10 --ks 1,5,10

python paper/experiments/scripts/dense_baseline.py \
  --dataset pubmedqa,banking77,emanual \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10

python paper/experiments/scripts/hybrid_baseline.py \
  --dataset pubmedqa,banking77,emanual \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --fusion-depth 100 --ks 1,5,10
```

CUAD full corpus 当前为 675400 sentence chunks，CPU exact dense 全量成本较高。当前 CUAD 结果应标为 smoke/sample，不应直接进入主表排名：

```bash
python paper/experiments/scripts/dense_baseline.py \
  --dataset cuad \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10 \
  --max-queries 100 --max-corpus 10000

python paper/experiments/scripts/hybrid_baseline.py \
  --dataset cuad \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --fusion-depth 100 --ks 1,5,10 \
  --max-queries 100 --max-corpus 10000
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

## 评估协议
## Evaluation Protocol

### Dataset task type

| 数据集 | Task type | 主表用途 | 说明 |
|--------|-----------|----------|------|
| PubMedQA | evidence retrieval | 可进入 evidence retrieval 主表 | 当前 GT 是 abstract context section-level，不能声称为严格 answer-supporting sentence recall |
| eManual | evidence retrieval | 可进入 evidence retrieval 主表 | RAGBench sentence-level chunks；必须显式记录 query split |
| CUAD | evidence retrieval | 当前仅 smoke/sample | full corpus 较大；BM25/dense/hybrid 必须统一 sample 后才可横向比较 |
| BANKING77 | intent retrieval proxy | 单独作为 intent/domain routing 子实验 | train utterances 是 corpus，test utterances 是 queries，同 intent train utterances 为 GT |

### Static retrieval metrics

当前静态检索指标为：

- `Recall@K`: top-K 中命中任意 ground-truth chunk 即为 1。
- `MRR@K`: top-K 内第一个 relevant chunk 的 reciprocal rank。
- `nDCG@K`: binary relevance，支持多个 ground-truth chunks。

默认跳过 `ground_truth_chunk_ids=[]` 的 query。RAGBench/CUAD 中这类 no-evidence query 应单独报告 `num_skipped_no_gt`。

### Split and comparability guardrails

Task 10 汇总表之前必须满足以下 guardrails：

1. RAGBench eManual/CUAD 需要显式记录 `query_split`。正式主表优先使用 held-out `test` query；train/validation 可用于调参、反馈流或 smoke。
2. 同一 dataset 的 BM25/dense/hybrid 横向比较必须使用相同 query subset 和 corpus subset。
3. CUAD 当前历史结果口径不完全一致，只能标为 `smoke_only` 或 `not_comparable`。
4. 表格需要包含 `scope`、`query_split`、`corpus_scope`、`task_type`、`comparable_group`、`is_comparable`、`notes`。
5. 当前 dense baseline 使用 `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine；除非另跑 BGE/GTE，否则论文中不得称为 BGE-large。

### Online learning protocol

Task 11-13 的在线学习实验必须先选定无泄漏协议：

- `prequential`: 每条 query 先评估，再使用其反馈更新模型。
- `train-feedback/test-eval`: train/validation query 只用于反馈流，held-out test query 只用于最终报告。

在线学习曲线应报告随机种子、mean/std、反馈预算、每轮 query 数和是否使用冷启动先验。

---

## 注意事项
## Notes

1. **BioASQ** 完整数据需要在 [bioasq.org](http://www.bioasq.org/) 注册下载。脚本会先尝试 HuggingFace 子集。
2. **PubMedQA artificial** 子集约 211K 条，下载和处理需要几分钟，默认不包含。
3. 所有 data/ 下的数据文件已在 `.gitignore` 中排除，不会提交到 git。
4. 预处理脚本会打印统计信息（chunks 数、queries 数、GT 覆盖率），请检查是否合理。
5. 当前 Task 7-9 结果工程上可复现，但 Task 10 之前需要先完成 Task 9.5 的 split/sample/comparability guardrails。

---

*创建时间: 2026-04-21*
*更新时间: 2026-04-27*
