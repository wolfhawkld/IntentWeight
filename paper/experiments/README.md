# 论文实验数据准备
# Paper Experiment Data Preparation

---

## Paper-Use Status

Before using any task summary in the paper draft, check
`paper/experiments/task_paper_use_status.md`. It marks which task documents are
main evidence, supporting evidence, boundary/negative evidence, historical or
superseded, and internal handoff/backlog only.

Current repository-controlled counts and remaining submission work are
authoritative in `paper/experiments/task80_authoritative_submission_state.md`
and `paper/experiments/task80_remaining_work_checklist.md`. The numbered
history below is retained for provenance and should not be used as a live
submission dashboard.

In particular, historical candidate-cost summaries before the final context
token correction must not be cited as evidence of lower LLM context-token cost.

## Naming Policy

- New paper text, task summaries, figures, and human-readable method labels use
  `IntentRoute`.
- New Python integrations import `IntentRouteManager` from `intent_route`.
- Historical lowercase IDs such as `intentweight_target`, existing CLI aliases,
  result paths, and JSON selectors remain unchanged for reproducibility.
- Do not rewrite prior result artifacts merely to rename the method; translate
  legacy IDs to `IntentRoute` only in presentation layers.

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
│   ├── preprocess_lotte.py        # LoTTE domain-search 预处理
│   ├── validate_processed.py      # 统一 processed 数据校验
│   ├── retrieval_metrics.py       # Recall/MRR/nDCG 评估
│   ├── embedding_cache.py         # reusable dense embedding cache
│   ├── large_scale_artifacts.py   # reusable dense/BM25/context artifacts
│   ├── lotte_scale_store.py       # LoTTE nested-scale canonical embedding manifests
│   ├── bm25_baseline.py           # BM25 静态检索 baseline
│   ├── dense_baseline.py          # dense embedding 静态检索 baseline
│   ├── hybrid_baseline.py         # BM25+dense RRF hybrid baseline
│   ├── experiment_guardrails.py   # split/sample/comparability guardrails + comparison CSV
│   ├── summarize_retrieval_baselines.py # paper-ready baseline tables
│   ├── linucb_online_baseline.py  # global LinUCB prequential online baseline
│   ├── summarize_linucb_online.py # paper-ready LinUCB online tables
│   ├── linucb_manifold_local.py   # manifold-local LinUCB feedback propagation
│   ├── summarize_linucb_manifold.py # paper-ready manifold-local LinUCB tables
│   ├── linucb_trust_feedback.py   # trust-weighted repeated-feedback LinUCB
│   └── linucb_cost_aware_routing.py # confidence-gated cost-aware routing
├── data/
│   ├── raw/                       # 下载的原始数据 (git ignored)
│   ├── processed/                 # 统一格式 (git ignored)
│   ├── embeddings/                # 预计算 embedding (git ignored)
│   ├── scale_store/               # canonical scale manifests/embedding rows (git ignored)
│   └── retrieval_artifacts/        # dense/BM25/context artifact cache (git ignored)
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

# LoTTE 小样本 / large-scale 垂类检索验证：
.venv/bin/python paper/experiments/scripts/preprocess_lotte.py \
  --domain technology --mode search --split test \
  --max-queries 20 --max-corpus 5000
```

### Step 3: 验证

```bash
python paper/experiments/scripts/validate_processed.py --dataset all
```

### Step 3.5: 统一实验 artifact 审计

Task51 提供一个不重跑实验的统一审计入口，用于后续新增实验前后的
dimension/statistics/display readiness 检查：

```bash
.venv/bin/python paper/experiments/scripts/task51_experiment_validation.py
```

默认 manifest 是 `paper/experiments/task51_experiment_manifest.json`，输出为：

```text
paper/experiments/results/task51_experiment_validation_audit.csv
paper/experiments/results/task51_experiment_validation_audit.json
paper/experiments/results/task51_experiment_validation_audit.md
```

常用变体：

```bash
.venv/bin/python paper/experiments/scripts/task51_experiment_validation.py --list-experiments

.venv/bin/python paper/experiments/scripts/task51_experiment_validation.py \
  --experiments task47_cross_encoder_reranker,task48_compressor_normalized_comparison
```

该审计检查已经生成的 artifacts：processed query/corpus shape、ranking
variant/query/chunk 引用、paired CSV 统计一致性、CI/p-value/range 合法性、
token-ratio 算术、以及 paper-facing Markdown 摘要是否具备基本展示结构。它不
替代真实实验，也不生成新的实验结论。

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
├── banking77_queries.json     # BANKING77 查询 + GT
├── lotte_technology_search_corpus.json  # LoTTE technology/search 语料库
└── lotte_technology_search_queries.json # LoTTE technology/search 查询 + GT
```

### Step 4: 静态检索 baseline

当前已实现三类静态检索 baseline：

```bash
python paper/experiments/scripts/bm25_baseline.py --dataset pubmedqa,banking77,emanual --top-k 10 --ks 1,5,10

# RAGBench held-out query split example:
python paper/experiments/scripts/bm25_baseline.py --dataset emanual --query-split test --top-k 10 --ks 1,5,10

python paper/experiments/scripts/dense_baseline.py \
  --dataset pubmedqa,banking77,emanual \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10

python paper/experiments/scripts/hybrid_baseline.py \
  --dataset pubmedqa,banking77,emanual \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --fusion-depth 100 --ks 1,5,10
```

Dense, hybrid, and cost-aware LinUCB scripts now enable reusable embedding cache
by default. Cache files are written under `paper/experiments/data/embeddings/`
and are ignored by git. The cache key includes dataset, model, record kind,
record ids, and record text, so changing the model or processed data naturally
creates a new cache.

Useful cache flags:

```bash
--embedding-cache-dir paper/experiments/data/embeddings
--no-embedding-cache
--force-embedding-cache
```

For LoTTE scale-up experiments, build a canonical scale store after generating
the nested processed slices and their corpus embedding caches:

```bash
.venv/bin/python paper/experiments/scripts/lotte_scale_store.py \
  --datasets lotte_technology_search_100k,lotte_technology_search_200k \
  --canonical-name lotte_technology_search \
  --model sentence-transformers/all-MiniLM-L6-v2
```

The store keys corpus rows by LoTTE `original_corpus_id`, not by scale-specific
processed `chunk_id`, so the same original corpus item is shared across 100k,
200k, and future 400k/full slices. Generated store files live under
`paper/experiments/data/scale_store/` and are ignored by git.

To append a larger nested slice without recomputing existing canonical rows:

```bash
.venv/bin/python paper/experiments/scripts/lotte_scale_store.py \
  --datasets lotte_technology_search_400k \
  --canonical-name lotte_technology_search \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --append-existing-store --compute-missing \
  --local-files-only --device cpu --batch-size 64
```

For the full LoTTE technology/search test corpus, use the mmap-backed append
path to keep memory bounded:

```bash
.venv/bin/python paper/experiments/scripts/preprocess_lotte.py \
  --domain technology --mode search --split test \
  --max-queries 596 --max-corpus 638509 \
  --output-name lotte_technology_search_638k \
  --local-arrow-cache

.venv/bin/python paper/experiments/scripts/lotte_scale_store.py \
  --datasets lotte_technology_search_638k \
  --canonical-name lotte_technology_search \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --append-existing-store --compute-missing --streaming-append \
  --local-files-only --device cpu --batch-size 64 --encode-chunk-size 10000
```

Dense and hybrid baselines can consume the canonical store directly:

```bash
.venv/bin/python paper/experiments/scripts/dense_baseline.py \
  --dataset lotte_technology_search_638k \
  --query-split test \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 16 \
  --top-k 10 --ks 1,5,10 \
  --use-scale-store \
  --output-dir paper/experiments/results/task22_7_lotte_638k_dense

.venv/bin/python paper/experiments/scripts/hybrid_baseline.py \
  --dataset lotte_technology_search_638k \
  --query-split test \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 16 \
  --top-k 10 --ks 1,5,10 --fusion-depth 100 \
  --use-scale-store \
  --output-dir paper/experiments/results/task22_8_lotte_638k_hybrid
```

For 638k LoTTE hybrid, BM25 ranking artifacts use a query-term bounded BM25
engine. It computes exact BM25 rankings for the selected queries without
holding a full-corpus inverted index in memory, which avoids WSL swap pressure
on the local 6.2 GiB RAM environment.

The cost-aware LinUCB runner also supports the same scale store:

```bash
.venv/bin/python paper/experiments/scripts/linucb_cost_aware_routing.py \
  --dataset lotte_technology_search_400k \
  --query-split test \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 16 \
  --top-k 10 --ks 1,5,10 \
  --seeds 13 --epochs 1 \
  --n-clusters 32 --context-dim 64 --candidate-arms 3 \
  --dense-depth 100 --bm25-depth 100 --cluster-depth 100 \
  --dense-lite-depth 30 --bm25-lite-depth 20 --dense-lite-floor-k 3 \
  --mid-confidence-threshold 0.44 --high-confidence-threshold 0.74 \
  --routing-modes full_multi_route,gated_cost_aware \
  --use-scale-store
```

For the 400k formal LinUCB run, use multi-seed / multi-epoch:

```bash
.venv/bin/python paper/experiments/scripts/linucb_cost_aware_routing.py \
  --dataset lotte_technology_search_400k \
  --query-split test \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 16 \
  --top-k 10 --ks 1,5,10 \
  --seeds 13,17,19 --epochs 3 \
  --n-clusters 32 --context-dim 64 --candidate-arms 3 \
  --dense-depth 100 --bm25-depth 100 --cluster-depth 100 \
  --dense-lite-depth 30 --bm25-lite-depth 20 --dense-lite-floor-k 3 \
  --mid-confidence-threshold 0.44 --high-confidence-threshold 0.74 \
  --routing-modes full_multi_route,gated_cost_aware \
  --use-scale-store
```

CUAD full corpus 当前为 675400 sentence chunks，CPU exact dense 全量成本较高。CUAD smoke/sample 必须使用 GT-anchored corpus sampling：先固定评估 query，把这些 query 的 GT chunks 放入候选 corpus，再补采样 distractors。当前 CUAD 结果应标为 smoke/sample，不应直接进入主表排名：

```bash
.venv/bin/python paper/experiments/scripts/bm25_baseline.py \
  --dataset cuad \
  --query-split test \
  --top-k 10 --ks 1,5,10 \
  --max-queries 100 --max-corpus 10000

.venv/bin/python paper/experiments/scripts/dense_baseline.py \
  --dataset cuad \
  --query-split test \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10 \
  --max-queries 100 --max-corpus 10000

.venv/bin/python paper/experiments/scripts/hybrid_baseline.py \
  --dataset cuad \
  --query-split test \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 --top-k 10 --fusion-depth 100 --ks 1,5,10 \
  --max-queries 100 --max-corpus 10000
```

生成带 guardrails 的静态检索对比表：

```bash
.venv/bin/python paper/experiments/scripts/experiment_guardrails.py \
  --results-dir paper/experiments/results \
  --data-dir paper/experiments/data/processed \
  --output paper/experiments/results/retrieval_baseline_comparison.csv
```

生成论文用 baseline 主表、proxy 表、smoke/sample 表：

```bash
.venv/bin/python paper/experiments/scripts/summarize_retrieval_baselines.py \
  --comparison paper/experiments/results/retrieval_baseline_comparison.csv \
  --output-dir paper/experiments/results
```

输出：

- `paper/experiments/results/retrieval_baseline_main_table.csv`
- `paper/experiments/results/retrieval_baseline_intent_proxy_table.csv`
- `paper/experiments/results/retrieval_baseline_smoke_table.csv`
- `paper/experiments/results/retrieval_baseline_tables.md`

### Step 5: Global LinUCB online baseline

Task 11 starts with a global LinUCB baseline under a no-leakage `prequential` protocol:
each query is evaluated first, then GT-derived feedback updates the selected cluster arms.
This is the online-learning baseline for Task 12/13; manifold-local propagation is not included here.

Smoke example:

```bash
.venv/bin/python paper/experiments/scripts/linucb_online_baseline.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --top-k 10 --ks 1,5,10 \
  --max-queries 50 --max-corpus 500 \
  --seeds 13,17 --n-clusters 8 --context-dim 16 --candidate-arms 3
```

Current smoke output:

- `paper/experiments/results/linucb_pubmedqa_prequential_metrics.json`
- `paper/experiments/results/linucb_pubmedqa_prequential_rankings.json`
- `paper/experiments/results/linucb_online_summary.csv`

Generate paper-ready LinUCB tables:

```bash
.venv/bin/python paper/experiments/scripts/summarize_linucb_online.py \
  --summary paper/experiments/results/linucb_online_summary.csv \
  --output-dir paper/experiments/results
```

Formal global LinUCB baseline matrix:

| Dataset | Scope | Queries | Seeds | Recall@10 mean | MRR@10 mean | Notes |
|---------|-------|---------|-------|----------------|-------------|-------|
| PubMedQA | full/train/full | 1000 | 3 | 0.5480 | 0.4637 | Section-level GT caveat |
| eManual | heldout_test/test/full | 130 | 3 | 0.1154 | 0.0182 | Evidence retrieval held-out |
| Banking77 | heldout_test/test/full | 3080 | 3 | 0.7215 | 0.6094 | Intent/domain routing proxy |
| CUAD | smoke_only/test/gt_anchored_10000 | 79 | 3 | 0.0464 | 0.0275 | GT-anchored smoke/sample only |

Outputs:

- `paper/experiments/results/linucb_online_main_table.csv`
- `paper/experiments/results/linucb_online_intent_proxy_table.csv`
- `paper/experiments/results/linucb_online_smoke_table.csv`
- `paper/experiments/results/linucb_online_tables.md`

Initial PubMedQA sample ablation (`max_queries=200`, `max_corpus=1000`, `seeds=13,17,19`):

| Variant | Recall@10 | MRR@10 | Observation |
|---------|-----------|--------|-------------|
| default: alpha_decay=0.01, candidate_arms=3 | 0.5450 | 0.4690 | Reference sample |
| alpha_decay=0.0, candidate_arms=3 | 0.6550 | 0.5615 | Better than default; decay may exploit too early |
| alpha_decay=0.01, candidate_arms=1 | 0.2433 | 0.2060 | Too narrow |
| alpha_decay=0.01, candidate_arms=5 | 0.8150 | 0.6984 | Best in sample; candidate breadth is critical |

Outputs:

- `paper/experiments/results/linucb_ablations/linucb_ablation_summary.csv`
- `paper/experiments/results/linucb_ablations/linucb_ablation_summary.md`

### Step 6: Manifold-local LinUCB feedback

Task 12 extends the global LinUCB baseline with manifold-local feedback propagation under the same `prequential` protocol:

- query-local feedback attention: nearby historical query feedback boosts relevant arms;
- cross-arm propagation: selected-arm feedback updates neighboring cluster arms with `exp(-distance / sigma)` decay;
- fixed semantic geometry: embeddings/PCA/clusters define the manifold, while feedback updates the value field.

Smoke example:

```bash
.venv/bin/python paper/experiments/scripts/linucb_manifold_local.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --top-k 10 --ks 1,5,10 \
  --max-queries 50 --max-corpus 500 \
  --seeds 13,17 --n-clusters 8 --context-dim 16 --candidate-arms 3
```

Generate paper-ready manifold-local LinUCB tables:

```bash
.venv/bin/python paper/experiments/scripts/summarize_linucb_manifold.py \
  --summary paper/experiments/results/linucb_manifold_summary.csv \
  --output-dir paper/experiments/results
```

Formal manifold-local LinUCB matrix:

| Dataset | Scope | Queries | Seeds | Recall@10 mean | MRR@10 mean | Task 11 Recall@10 | Notes |
|---------|-------|---------|-------|----------------|-------------|-------------------|-------|
| PubMedQA | full/train/full | 1000 | 3 | 0.6607 | 0.5654 | 0.5480 | Improves over global LinUCB |
| eManual | heldout_test/test/full | 130 | 3 | 0.0923 | 0.0193 | 0.1154 | Worse Recall@10; local propagation not universally beneficial |
| Banking77 | heldout_test/test/full | 3080 | 3 | 0.8247 | 0.7490 | 0.7215 | Intent proxy improves strongly |
| CUAD | smoke_only/test/gt_anchored_10000 | 79 | 3 | 0.0295 | 0.0120 | 0.0464 | Smoke/sample only; worse than global on this sample |

Outputs:

- `paper/experiments/results/linucb_manifold_main_table.csv`
- `paper/experiments/results/linucb_manifold_intent_proxy_table.csv`
- `paper/experiments/results/linucb_manifold_smoke_table.csv`
- `paper/experiments/results/linucb_manifold_tables.md`

### Step 7: Global vs manifold-local LinUCB comparison

Task 13 compares Task 11 and Task 12 under matching dataset/split/corpus/protocol scopes:

```bash
.venv/bin/python paper/experiments/scripts/compare_linucb_variants.py \
  --global-summary paper/experiments/results/linucb_online_summary.csv \
  --manifold-summary paper/experiments/results/linucb_manifold_summary.csv \
  --output-csv paper/experiments/results/linucb_variant_comparison.csv \
  --output-markdown paper/experiments/results/linucb_variant_comparison.md
```

Current comparison:

| Dataset | Scope | Global Recall@10 | Manifold Recall@10 | Delta | Global MRR@10 | Manifold MRR@10 | Interpretation |
|---------|-------|------------------|--------------------|-------|---------------|-----------------|----------------|
| PubMedQA | full/train/full | 0.5480 | 0.6607 | +0.1127 | 0.4637 | 0.5654 | Manifold-local improves both recall and MRR |
| eManual | heldout_test/test/full | 0.1154 | 0.0923 | -0.0231 | 0.0182 | 0.0193 | Global has better recall; local has slight rank-quality gain |
| Banking77 | heldout_test/test/full | 0.7215 | 0.8247 | +0.1031 | 0.6094 | 0.7490 | Manifold-local improves both recall and MRR |
| CUAD | smoke_only/test/gt_anchored_10000 | 0.0464 | 0.0295 | -0.0169 | 0.0275 | 0.0120 | Global remains stronger on CUAD smoke sample |

Outputs:

- `paper/experiments/results/linucb_variant_comparison.csv`
- `paper/experiments/results/linucb_variant_comparison.md`

### Step 8: Soft-routed manifold LinUCB

Task 13.5 keeps manifold-local LinUCB as the adaptive policy, but removes the
hard cluster gate from final retrieval. Each query fuses three candidate
streams with weighted RRF:

- global dense retrieval over the selected corpus;
- global BM25 lexical retrieval over the selected corpus;
- dense retrieval inside LinUCB-selected cluster arms.

It also reports hard-pruning diagnostics: selected GT-cluster hit rate and
rescue rate after a selected-cluster miss.

Example:

```bash
.venv/bin/python paper/experiments/scripts/linucb_soft_routing.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --top-k 10 --ks 1,5,10 \
  --seeds 13,17,19 --n-clusters 32 --context-dim 64 --candidate-arms 3 \
  --dense-depth 100 --bm25-depth 100 --cluster-depth 100 --dense-floor-k 5
```

Generate paper-ready soft-routing tables:

```bash
.venv/bin/python paper/experiments/scripts/summarize_linucb_soft.py \
  --summary paper/experiments/results/linucb_soft_summary.csv \
  --output-dir paper/experiments/results
```

Current Task 13.5 results:

| Dataset | Scope | Recall@10 mean | MRR@10 mean | Selected cluster hit | Rescue on cluster miss | Dense baseline Recall@10 | Notes |
|---------|-------|----------------|-------------|----------------------|------------------------|--------------------------|-------|
| PubMedQA | full/train/full | 0.9920 | 0.8466 | 0.6817 | 0.9800 | 0.9930 | Soft routing removes most hard-pruning loss |
| eManual | heldout_test/test/full | 0.1436 | 0.0337 | 0.2641 | 0.1173 | 0.3231 | Still below dense; source recall and cluster routing remain weak |
| Banking77 | heldout_test/test/full | 0.9831 | 0.9420 | 0.8829 | 0.9699 | 0.9805 | Intent proxy matches/exceeds dense under this run |
| CUAD | smoke_only/test/gt_anchored_10000 | 0.0844 | 0.0344 | 0.3713 | 0.0865 | 0.0759 | Smoke/sample only; slightly above dense on this sample |

Outputs:

- `paper/experiments/results/linucb_soft_summary.csv`
- `paper/experiments/results/linucb_soft_main_table.csv`
- `paper/experiments/results/linucb_soft_intent_proxy_table.csv`
- `paper/experiments/results/linucb_soft_smoke_table.csv`
- `paper/experiments/results/linucb_soft_tables.md`

### Step 9: Manifold diagnostics

Task 14 directly tests whether the datasets expose usable local geometry for
the manifold-routing assumption. It stays at the retrieval layer and reports:

- PCA spectrum and intrinsic-dimensionality proxies;
- cluster balance, silhouette sample, and metadata label alignment;
- local neighborhood label purity;
- nearest-cluster GT hit rates without LinUCB feedback;
- context-space GT recall and retention versus dense retrieval;
- Task13.5 soft-routing gain relative to dense.

Example:

```bash
.venv/bin/python paper/experiments/scripts/manifold_diagnostics.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --n-clusters 32 --context-dim 64 --sample-size 1000 \
  --neighbor-k 10 --cluster-hit-ks 1,3,5 --recall-ks 1,5,10
```

Join diagnostics with dense and Task13.5 soft-routing results:

```bash
.venv/bin/python paper/experiments/scripts/summarize_manifold_diagnostics.py \
  --diagnostics paper/experiments/results/manifold_diagnostics_summary.csv \
  --dense-summary paper/experiments/results/dense_baseline_summary.csv \
  --soft-summary paper/experiments/results/linucb_soft_summary.csv \
  --output-csv paper/experiments/results/manifold_diagnostics_comparison.csv \
  --output-markdown paper/experiments/results/manifold_diagnostics_tables.md
```

Current Task 14 diagnostics:

| Dataset | Scope | PCA dim 90% | Local purity | Nearest cluster hit@3 | Context recall@10 | Soft - Dense R@10 | Interpretation |
|---------|-------|-------------|--------------|------------------------|-------------------|-------------------|----------------|
| PubMedQA | full/train/full | 177 | 0.2439 | 0.9680 | 0.9860 | -0.0010 | Strong GT-cluster routing signal; soft routing mainly preserves dense baseline |
| eManual | heldout_test/test/full | 111 | 0.0169 | 0.8923 | 0.3615 | -0.1795 | Geometry can route to GT clusters, but learned arm/fusion underuses the signal |
| Banking77 | heldout_test/test/full | 105 | 0.8539 | 0.9968 | 0.9782 | +0.0026 | Strong local routing signal aligns with intent-proxy soft routing |
| CUAD | smoke_only/test/gt_anchored_10000 | 182 | 0.0716 | 0.6076 | 0.0759 | +0.0084 | Smoke/sample only; soft routing helps despite imperfect cluster routing |

Outputs:

- `paper/experiments/results/manifold_diagnostics_summary.csv`
- `paper/experiments/results/manifold_diagnostics_comparison.csv`
- `paper/experiments/results/manifold_diagnostics_tables.md`
- `paper/experiments/results/manifold_diagnostics_{dataset}.json`

### Step 10: eManual failure analysis

Task 14.5 isolates why eManual underperforms under strict chunk-id recall. It
does not replace the guarded main metric. It adds diagnostics for duplicate
manual sentences, text-equivalent evidence matching, deduplicated-corpus
baselines, and centroid-routing upper bounds.

Run:

```bash
.venv/bin/python paper/experiments/scripts/emanual_failure_analysis.py
```

Current Task 14.5 findings:

| Diagnostic | Result | Interpretation |
|------------|--------|----------------|
| Corpus chunks vs unique texts | 18812 chunks / 1729 unique normalized texts | eManual full corpus has heavy repeated sentences |
| GT duplicate exposure | 861/861 test GT refs have duplicate text | strict chunk-id recall can mark identical evidence text as wrong |
| Dense strict vs text-equivalent R@10 | 0.3231 -> 0.5615 | dense retrieves more semantic evidence than strict chunk IDs show |
| Task13.5 strict vs text-equivalent R@10 | 0.1436 -> 0.5795 | soft routing is hurt strongly by duplicate-id evaluation |
| Deduplicated dense/hybrid R@10 | 0.8615 / 0.8615 | after collapsing duplicate texts, evidence retrieval is much easier |
| Nearest-centroid 3-cluster R@10 | strict 0.3308 / text 0.5462 | geometry is usable; LinUCB selected-cluster policy underuses it |
| LinUCB selected cluster hit | 0.2641 | learned arm selection is far below nearest-centroid routing |

Conclusion: eManual is not evidence that the manifold assumption is absent.
Its low strict Task13.5 score is mainly a combination of weak instance-level
labels, heavy duplicate text across records, and a LinUCB/fusion policy that
does not yet exploit the available centroid-routing geometry.

Outputs:

- `paper/experiments/results/emanual_failure_analysis.json`
- `paper/experiments/results/emanual_failure_analysis_tables.csv`
- `paper/experiments/results/emanual_failure_analysis_tables.md`
- `paper/experiments/results/emanual_deduplicated_rankings.json`

### Step 11: Trust-weighted feedback LinUCB

Task 15 keeps the Task13.5 soft multi-route retrieval surface and changes the
online signal: the LinUCB cluster-arm policy is updated by repeated simulated
feedback. It compares four feedback modes:

- `none`: no feedback control;
- `oracle`: clean GT-derived feedback;
- `equal_noisy`: simulated user feedback with equal update weight;
- `trust_weighted`: simulated user feedback whose update weight and local
  feedback memory are scaled by user trust.

Example:

```bash
.venv/bin/python paper/experiments/scripts/linucb_trust_feedback.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --top-k 10 --ks 1,5,10 --seeds 13,17,19 \
  --epochs 3 --n-clusters 32 --context-dim 64 --candidate-arms 3
```

Current Task 15 results:

| Dataset | Scope | Mode | R@10 | Last true reward | Reward gain | Last selected-cluster hit | Selected-cluster gain | Interpretation |
|---------|-------|------|------|------------------|-------------|---------------------------|-----------------------|----------------|
| PubMedQA | full/train/full | none | 0.9933 | 0.1383 | -0.0063 | 0.1623 | -0.0060 | Dense floor keeps recall high, but arm policy does not improve without feedback |
| PubMedQA | full/train/full | trust_weighted | 0.9940 | 0.8727 | +0.4030 | 0.8860 | +0.3950 | Trust feedback clearly improves the policy value field |
| eManual | heldout_test/test/full | none | 0.1436 | 0.0152 | -0.0227 | 0.2121 | -0.0581 | Strict chunk-id/duplicate-text issues still dominate |
| eManual | heldout_test/test/full | trust_weighted | 0.1487 | 0.0556 | +0.0152 | 0.2652 | +0.0429 | Feedback helps policy metrics, but not enough to fix strict evidence recall |
| Banking77 | heldout_test/test/full | none | 0.9855 | 0.1660 | -0.0005 | 0.4390 | +0.0043 | Full intent-proxy run; final recall is already near ceiling |
| Banking77 | heldout_test/test/full | trust_weighted | 0.9844 | 0.9805 | +0.1317 | 0.9983 | +0.0627 | Strong policy improvement, but no final R@10 gain on full |
| Banking77 | sample/test/full | none | 0.9840 | 0.1773 | -0.0123 | 0.4387 | -0.0077 | Sampled 1000-query intent proxy run |
| Banking77 | sample/test/full | trust_weighted | 0.9863 | 0.9583 | +0.2863 | 0.9843 | +0.1957 | Sample shows small final R@10 gain and strong policy improvement |
| CUAD | smoke_only/test/gt_anchored_10000 | none | 0.0675 | 0.0133 | +0.0067 | 0.2433 | +0.0167 | Sparse smoke sample remains weak |
| CUAD | smoke_only/test/gt_anchored_10000 | trust_weighted | 0.0886 | 0.0233 | +0.0167 | 0.2900 | +0.0400 | Small positive movement under sparse GT |

The main Task 15 signal is policy self-evolution, not a large final R@10 jump.
Because dense/BM25 bypass and dense floor already protect final recall, feedback
improvement is most visible in `last_epoch_true_reward` and
`last_epoch_selected_cluster_hit_rate`. For paper reporting,
`last_epoch_true_reward` is the primary LinUCB self-evolution metric, while
Recall@k is the downstream multi-route retrieval outcome.

Outputs:

- `paper/experiments/results/linucb_trust_summary.csv`
- `paper/experiments/results/linucb_trust_tables.md`
- `paper/experiments/results/linucb_trust_{dataset}_{scope}_{split}_{corpus}_{query_count}_prequential_metrics.json`
- `paper/experiments/results/linucb_trust_{dataset}_{scope}_{split}_{corpus}_{query_count}_prequential_rankings.json`

### Step 12: Cost-aware LinUCB routing

Task 16 tests whether the feedback-improved LinUCB policy can reduce retrieval
cost by shifting from full dense-heavy multi-route retrieval to confidence-gated
lite routing. The formal run below uses a conservative gate: it does not fully
disable dense; it lowers dense/BM25 candidate depth under sufficient confidence
and falls back to the full route otherwise.

Example:

```bash
.venv/bin/python paper/experiments/scripts/linucb_cost_aware_routing.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --top-k 10 --ks 1,5,10 --seeds 13,17,19 --epochs 3 \
  --n-clusters 32 --context-dim 64 --candidate-arms 3 \
  --high-confidence-threshold 1.1 --mid-confidence-threshold 0.25 \
  --confidence-feedback-floor 6 --drift-threshold 1.1
```

Current Task 16 results:

| Dataset | Scope | Full R@10 | Gated R@10 | Delta | Full cost | Gated cost | Cost reduction | Interpretation |
|---------|-------|-----------|------------|-------|-----------|------------|----------------|----------------|
| PubMedQA | full/train/full | 0.9940 | 0.9893 | -0.0047 | 299.94 | 152.36 | 49.20% | Good quality-cost trade-off |
| Banking77 | heldout_test/test/full | 0.9844 | 0.9813 | -0.0031 | 300.00 | 142.51 | 52.50% | Good intent-proxy trade-off on full test |
| eManual | heldout_test/test/full | 0.1487 | 0.1154 | -0.0333 | 300.00 | 214.07 | 28.64% | Cost gating hurts weak strict evidence recall |
| CUAD | smoke_only/test/gt_anchored_10000 | 0.0886 | 0.0633 | -0.0253 | 300.00 | 203.47 | 32.18% | Sparse smoke result; not safe for aggressive gating |

Task 16 supports a cost-aware claim, not a free-lunch claim. On PubMedQA and
Banking77, conservative gating cuts source candidate cost by roughly half with
less than 0.5 percentage-point Recall@10 loss. Banking77 also has a 1000-query
sample run with a similar trade-off, but the full held-out run above should
anchor the main result. On eManual and CUAD, the same gate hurts recall too
much, so dense/BM25 fallback should remain stronger.

Outputs:

- `paper/experiments/results/linucb_cost_summary.csv`
- `paper/experiments/results/linucb_cost_tables.md`
- `paper/experiments/results/linucb_cost_{dataset}_{scope}_{split}_{corpus}_{query_count}_prequential_metrics.json`
- `paper/experiments/results/linucb_cost_{dataset}_{scope}_{split}_{corpus}_{query_count}_prequential_rankings.json`

### Step 13: LoTTE large-scale pre-validation

Task 17 should use LoTTE as the primary large-scale vertical-domain evidence
retrieval candidate. PubMedQA and Banking77 have already been fully evaluated
in the current processed form, so they should remain full small/medium-scale
anchors rather than large-scale evidence. CUAD remains useful as a sparse
large-scale stress/limitation case, not as the main positive proof.

LoTTE small validation (`technology/search`, `test`, 20 queries, 5000
distractors plus GT anchors) passed the processed-data guardrail:

| Dataset | Corpus | Queries | GT refs | BM25 R@10 | Dense R@10 | Hybrid R@10 | LinUCB full R@10 | LinUCB gated R@10 |
|---------|--------|---------|---------|-----------|------------|-------------|------------------|-------------------|
| LoTTE technology/search sample | 5018 | 20 | 56 | 0.9000 | 0.9000 | 1.0000 | 1.0000 | 0.9500 |

The cost-aware LinUCB smoke used one seed and one epoch. It verifies pipeline
compatibility, not final Task 17 significance. The full Task 17 run should scale
LoTTE by increasing query count and corpus scope while reporting quality-cost
trade-offs, dense query rate, fallback rate, and policy self-evolution metrics.

Task 17 stage-1 large-scale smoke (`technology/search`, full 596 test queries,
100k distractors plus GT anchors) also passed the processed-data guardrail.
The static BM25/dense/hybrid comparison group is now complete and comparable:

| Dataset | Corpus | Queries | GT refs | BM25 R@10 | Dense R@10 | Hybrid R@10 | LinUCB full R@10 | LinUCB gated R@10 | Gated cost reduction |
|---------|--------|---------|---------|-----------|------------|-------------|------------------|-------------------|----------------------|
| LoTTE technology/search 100k | 101311 | 596 | 2045 | 0.7232 | 0.8674 | 0.8624 | 0.8725 | 0.8356 | 25.28% |

Task 18 reran the same LoTTE 100k setting with `seeds=13,17,19` and
`epochs=3`, using shared dense/BM25/context artifacts:

| Setting | LinUCB full R@10 | Full R@10 std | LinUCB gated R@10 | Gated R@10 std | Full last reward | Gated last reward | Gated avg cost | Gated cost reduction | Gated dense query rate |
|---------|------------------|---------------|-------------------|----------------|------------------|-------------------|----------------|----------------------|------------------------|
| LoTTE 100k Task18 | 0.8826 | 0.0036 | 0.8440 | 0.0107 | 0.5671 | 0.5923 | 191.68 | 36.11% | 0.8220 |

The multi-seed result strengthens the positive signal: full multi-route LinUCB
is above dense-only by about `+1.51` Recall@10 points (`0.8826` vs `0.8674`).
The gated route still trades away recall, but it reduces average source
candidate cost from `300.00` to `191.68` while preserving a positive feedback
learning signal.

Task 19 mapped the gated cost-aware quality-cost frontier with five
dense/LinUCB gating configurations. All runs used LoTTE 100k, `seeds=13,17,19`,
`epochs=3`, `n_clusters=32`, and shared artifact cache hits.

| Setting | Dense-lite depth | Dense-lite floor | Mid/high confidence | R@10 | MRR@10 | nDCG@10 | Last reward | Reward gain | Avg cost | Dense query rate | Fallback rate | LinUCB primary rate |
|---------|------------------|------------------|---------------------|------|--------|---------|-------------|-------------|----------|------------------|---------------|---------------------|
| Task18 gated | 20 | 2 | 0.35 / 0.65 | 0.8440 | 0.6950 | 0.5889 | 0.5923 | +0.2931 | 191.68 | 0.8220 | 0.3453 | 0.1780 |
| Task19-A | 30 | 2 | 0.35 / 0.65 | 0.8378 | 0.6911 | 0.5872 | 0.5632 | +0.2724 | 199.56 | 0.8249 | 0.3654 | 0.1751 |
| Task19-B | 50 | 2 | 0.35 / 0.65 | 0.8479 | 0.6935 | 0.5923 | 0.5962 | +0.3043 | 205.96 | 0.8138 | 0.3482 | 0.1862 |
| Task19-C | 30 | 3 | 0.35 / 0.65 | 0.8496 | 0.6941 | 0.6042 | 0.5783 | +0.2875 | 198.77 | 0.8276 | 0.3596 | 0.1724 |
| Task19-D | 30 | 3 | 0.45 / 0.75 | 0.8770 | 0.7065 | 0.6321 | 0.6074 | +0.3160 | 229.97 | 0.9029 | 0.5526 | 0.0971 |
| Task19-E | 50 | 5 | 0.55 / 0.85 | 0.8865 | 0.7116 | 0.6508 | 0.6370 | +0.3507 | 258.84 | 0.9489 | 0.7030 | 0.0511 |

The Task 19 ablation confirms that the method exposes a tunable Pareto
frontier. A/B/C are medium-cost points and remain below dense-only R@10
`0.8674`. D/E are quality-first points and exceed dense-only, with E reaching
`0.8865`, but they do so by triggering more full dense fallback. This means the
current evidence should be framed as adaptive route weighting under a cost
budget, not as a universal low-cost replacement for dense retrieval.

Task 20 then tested conditional dense fallback. The routing script now records
why full dense fallback fires: low confidence, high semantic drift, or recent
reward drop. It also reports dense saved rate and a simple quality-cost ratio.

| Setting | Dense-lite depth | Dense-lite floor | Mid/high confidence | Reward-drop threshold | R@10 | MRR@10 | nDCG@10 | Last reward | Reward gain | Avg cost | Dense query rate | Dense saved rate | Fallback reason summary |
|---------|------------------|------------------|---------------------|-----------------------|------|--------|---------|-------------|-------------|----------|------------------|------------------|-------------------------|
| Task20-L | 10 | 1 | 0.20 / 0.45 | 0.20 | 0.7383 | 0.6221 | 0.5007 | 0.6292 | +0.3322 | 143.22 | 0.5405 | 0.4595 | low_conf=0.0462, drift=0.0515, reward_drop=0.0071 |
| Task20-M | 30 | 3 | 0.35 / 0.65 | 0.05 | 0.8624 | 0.7009 | 0.6198 | 0.5889 | +0.3048 | 225.49 | 0.8689 | 0.1311 | low_conf=0.2261, drift=0.0431, reward_drop=0.2603 |
| Task20-H | 30 | 3 | 0.40 / 0.70 | 0.05 | 0.8669 | 0.7048 | 0.6271 | 0.5587 | +0.2752 | 237.54 | 0.9053 | 0.0947 | low_conf=0.3098, drift=0.0429, reward_drop=0.2498 |
| Task20-S | 30 | 3 | 0.44 / 0.74 | 0.00 | 0.8747 | 0.7071 | 0.6308 | 0.6074 | +0.3160 | 227.29 | 0.8945 | 0.1055 | low_conf=0.4862, drift=0.0501, reward_drop=0.0000 |

Task20-S is the best current conditional-fallback point: it exceeds dense-only
R@10 `0.8674`, stays below Task19-D cost (`227.29` vs `229.97`), and reduces
dense query rate below Task19-D (`0.8945` vs `0.9029`). The reward-drop trigger
is useful diagnostically, but in these runs it increased fallback cost without
beating the cleaner confidence/drift-only S configuration.

Task 21 consolidates the paper-facing evidence chain in
`paper/experiments/task21_paper_ready_summary.md`. The summary frames Task19 as
the hypothesis/Pareto validation stage and Task20 as the conditional dense
fallback optimization stage. The bounded paper claim is that IntentRoute can
learn useful route value from trust-weighted feedback and expose a controllable
quality-cost frontier; it should not be claimed as a universal low-cost
replacement for dense retrieval.

Task 28.1 later backfills these historical Task16-25 cost claims with final
context-token measurements. The candidate-cost values in Task16-25 should be
read as source-candidate or dense-invocation proxies, not as final LLM context
token savings.

Task 22 extends LoTTE incrementally beyond the 100k reference. Task22.2 generated
and evaluated a 200k corpus (`201010` chunks, `596` test queries, `2045` GT
refs, 100% GT coverage):

| Setting | R@10 | MRR@10 | nDCG@10 | Last reward | Reward gain | Avg cost | Dense query rate | Notes |
|---------|------|--------|---------|-------------|-------------|----------|------------------|-------|
| BM25 200k | 0.6292 | 0.4572 | 0.3832 | - | - | - | - | Static lexical baseline |
| Dense 200k | 0.7970 | 0.6279 | 0.5643 | - | - | 100.00 | 1.0000 | all-MiniLM-L6-v2 CPU exact cosine |
| Hybrid 200k | 0.8003 | 0.6045 | 0.5323 | - | - | 200.00 | 1.0000 | RRF, fusion depth 100 |
| Task22.2 full multi-route | 0.8300 | 0.6326 | 0.5720 | 0.5078 | +0.2875 | 300.00 | 1.0000 | seeds=13,17,19; epochs=3 |
| Task22.2 gated | 0.8154 | 0.6305 | 0.5472 | 0.5677 | +0.3395 | 232.01 | 0.9027 | Task20-S-style thresholds |

The 200k result preserves the large-scale signal: full multi-route remains
above dense by about `+3.30` Recall@10 points, and gated routing remains above
dense while reducing source candidate cost relative to the full route. Static
baselines drop from 100k to 200k, confirming that the incremental scale-up makes
retrieval harder rather than merely duplicating the 100k setting.

The 100k dense baseline took `1640.076s` on CPU exact cosine before reusable
embedding cache was added. The original cost-aware LinUCB smoke took
`1772.420s` for full route and `1905.491s` for gated route because it repeated
embedding work. After embedding-cache integration, the same one-seed/one-epoch
LoTTE 100k LinUCB run hit both corpus and query embedding cache: full route
elapsed `134.640s`, gated route elapsed `266.344s`, with unchanged retrieval
metrics. Task 17 now also has a shared large-scale artifact cache for dense
top-depth rankings, BM25 top-depth rankings, and PCA/context cluster artifacts.
The first artifact-generating rerun elapsed `110.931s` / `117.796s` for
full/gated route; the second artifact-cache-hit rerun elapsed `7.392s` /
`14.080s`, again with unchanged retrieval metrics. This makes more seeds and
epochs practical before attempting the full 638k corpus.

Current status as of 2026-05-07:

- LoTTE 100k corpus/query embedding cache has been generated locally under
  `paper/experiments/data/embeddings/` and is ignored by git.
- Cached shapes: corpus `[101311, 384]`, queries `[596, 384]`.
- Cache sizes: corpus `149M`, queries `896K`.
- First cache generation took `1598.231s`; second cache-hit validation took
  `0.204s` with `corpus_hit=true` and `query_hit=true`.
- LoTTE 100k BM25, dense, and hybrid baselines are available and marked
  comparable by the guardrail table.
- LoTTE 100k large-scale manifold geometry diagnostics have been run with
  embedding-cache hits.
- LoTTE 100k cost-aware LinUCB has been rerun with embedding-cache hits:
  full route `R@10=0.8725`, elapsed `134.640s`; gated route `R@10=0.8356`,
  elapsed `266.344s`, average source candidate cost `224.16`.
- Shared large-scale artifacts have been generated for LoTTE 100k under
  `paper/experiments/data/retrieval_artifacts/` and are ignored by git. With
  dense/BM25/context artifact hits, the same LoTTE 100k cost-aware rerun now
  reports full route elapsed `7.392s` and gated route elapsed `14.080s`.
- Task18 LoTTE 100k multi-seed/multi-epoch run is complete with all shared
  artifact hits: full route `R@10=0.8826`, gated route `R@10=0.8440`, gated
  average source candidate cost `191.68`.
- Task19 LoTTE 100k dense/LinUCB gating ablation is complete: medium-cost C
  reaches `R@10=0.8496` at cost `198.77`, while quality-first D/E exceed dense
  baseline with `R@10=0.8770` / `0.8865` at costs `229.97` / `258.84`.
- Task20 LoTTE 100k conditional dense fallback is complete: S reaches
  `R@10=0.8747` at cost `227.29`, with dense query rate `0.8945` and dense
  saved rate `0.1055`.
- Task21 paper-ready summary is complete:
  `paper/experiments/task21_paper_ready_summary.md`.
- Task22.2 LoTTE 200k scale-up is complete: static dense `R@10=0.7970`,
  full multi-route `R@10=0.8300`, gated `R@10=0.8154`, gated average source
  cost `232.01`.
- Task22.3-22.5 LoTTE 400k scale-up is complete: static dense
  `R@10=0.7718`, hybrid RRF `R@10=0.7617`, full multi-route
  `R@10=0.8003`, and gated cost-aware `R@10=0.7836` with average source
  cost `233.22`.
- Task22.6-22.9 LoTTE 638k full-corpus setup, static baselines, and LinUCB
  validation are complete:
  canonical scale store now contains `638509` rows, and 638k dense baseline
  reaches `R@10=0.7282`, `MRR@10=0.5102`, `nDCG@10=0.4303` in `51.726s`.
  The bounded-BM25 hybrid RRF baseline reaches `R@10=0.7181`,
  `MRR@10=0.4675`, `nDCG@10=0.3954` in `157.984s`.
  The 638k formal LinUCB run reaches full multi-route `R@10=0.7612` and
  gated cost-aware `R@10=0.7343`; gated remains above dense while reducing
  average source candidate cost from `300.00` to `236.22`.
- Task23 paper-facing LoTTE scale-up summary is complete:
  `paper/experiments/task23_lotte_scaleup_summary.md` and
  `paper/experiments/results/task23_lotte_scaleup_summary.csv`. The summary
  explicitly separates deterministic artifact reuse from final metric reuse and
  states the cost claim as cost reduction versus full multi-route, not versus
  dense-only.
- Task23 BM25 scale completion is complete: standalone BM25-only metrics are
  now materialized for LoTTE 400k (`R@10=0.5721`) and 638k (`R@10=0.5084`) from
  shared BM25 ranking artifacts, completing the LoTTE scale × baseline matrix.

Current LoTTE 100k manifold diagnostics:

| Dataset | pca_dim90 | pca_var@64 | nearest_cluster_hit@1 | nearest_cluster_hit@3 | nearest_cluster_hit@5 | dense R@10 | context R@10 | context retention@10 |
|---------|-----------|------------|-----------------------|-----------------------|-----------------------|------------|-------------|----------------------|
| LoTTE technology/search 100k | 182 | 0.6432 | 0.6997 | 0.8809 | 0.9413 | 0.8674 | 0.7836 | 0.9033 |

LoTTE does not provide a true corpus topic/intent label in the processed qrels
schema, so label-purity metrics are intentionally disabled for `lotte_*`
datasets instead of using the constant `source=lotte` metadata field as a
surrogate label. The diagnostics therefore support a retrieval-geometry claim:
the corpus has usable cluster routing signal (`nearest_cluster_hit@3=0.8809`)
and PCA-context retrieval retains about `90.33%` of dense Recall@10, but the
geometry is not sufficient to replace dense retrieval by itself.

Next roadmap:

| Task | Goal | Main evidence |
|------|------|---------------|
| 17.5 | Connect shared artifacts to more experiment scripts | BM25/dense/hybrid/manifold/LinUCB use more consistent cached ranking/context assets |
| 18 | Run LoTTE 100k multi-seed / multi-epoch experiments | Stability of full multi-route, gated cost-aware trade-off, reward evolution |
| 19 | Run dense/LinUCB weight and threshold ablations | Complete: quality-cost Pareto frontier, with D/E exceeding dense at higher cost |
| 20 | Test conditional dense fallback | Complete: S exceeds dense while reducing dense query rate below Task19-D |
| 21 | Assemble paper-ready result tables and argument | Complete: bounded evidence summary and recommended paper claim |
| 22.1 | LoTTE 100k scale reference | Complete: Task18/19/20 quality-cost frontier |
| 22.2 | LoTTE 200k incremental scale-up | Complete: full/gated remain above dense under larger corpus |
| 22.3 | LoTTE 400k baseline/artifact integration | Complete: dense/hybrid use canonical scale store |
| 22.4 | LoTTE 400k LinUCB smoke | Complete: full/gated above dense smoke |
| 22.5 | LoTTE 400k LinUCB formal | Complete: full/gated above dense, gated reduces candidate cost |
| 22.6 | LoTTE 638k full-corpus expansion | Complete: streaming append avoids full embedding recompute |
| 22.7 | LoTTE 638k dense baseline | Complete: full-corpus dense baseline and ranking artifact generated |
| 22.8 | LoTTE 638k BM25/hybrid artifacts | Complete: query-term bounded BM25 artifact plus full-corpus hybrid baseline |
| 22.9 | LoTTE 638k LinUCB smoke/formal | Complete: full/gated above dense; gated lowers source candidate cost |
| 23 | Consolidate LoTTE scale-up evidence | Complete: paper-facing 100k/200k/400k/638k quality-cost tables |
| 24 | Add audit guardrails and static controls | Complete: metric naming fixed; static/naive controls added for 638k |
| 25 | Separate final fused reward from route-level credit | Complete: cluster-only credit improves selected route quality on LoTTE 100k |
| 26 | Test low-cost dense fallback after route-level learning | Complete: quality-cost frontier; near-dense quality at lower cost than Task25, sub-dense cost with quality loss |
| 27 | Test dense-LinUCB two-route trade-off with BM25 disabled | Complete: sub-dense candidate cost is possible, but dense-level quality is not yet preserved |
| 28 | Recompute final context token cost | Complete: candidate-count savings do not translate into top-10 token savings |
| 28.1 | Backfill historical Task16-25 final context tokens | Complete: old candidate-cost claims are now separated from final context token metrics |
| 29 | Confidence-based final context policy | Complete: 100k/200k/400k/638k final-context-token frontier |
| 29.3 | Seed variance / CI for Task29-C | Complete: token saving is stable across 100k/200k/400k/638k |
| 30 | LoTTE multi-scale geometry validation | Complete: geometry remains usable at scale but is diagnostic, not sufficient alone |
| 31 | Paper evidence package | Complete: final claim ledger, main tables, limitations, and paper structure guidance |
| 32 | Paper draft skeleton | Complete: outline, abstract, introduction, method, experiments, and limitations drafts under `paper/draft/` |
| 33 | Pre-writing validation backlog | Planned: multi-embedding robustness, feedback sensitivity, clean ablation, protocol defense, LLM smoke, optional more seeds |

Example smoke commands:

```bash
.venv/bin/python paper/experiments/scripts/validate_processed.py --dataset lotte_technology_search
.venv/bin/python paper/experiments/scripts/bm25_baseline.py --dataset lotte_technology_search --query-split test --top-k 10 --ks 1,5,10
.venv/bin/python paper/experiments/scripts/dense_baseline.py --dataset lotte_technology_search --query-split test --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10
.venv/bin/python paper/experiments/scripts/hybrid_baseline.py --dataset lotte_technology_search --query-split test --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10
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
| LoTTE technology/search | 技术问答检索 | mteb/LoTTE | ~638K test corpus | ~596 test queries |

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
| LoTTE | evidence retrieval | Task 22/23 large-scale 主表 | 垂类 domain-search，已完成 100k/200k/400k/638k scale-up 验证 |

### Static retrieval metrics

当前静态检索指标为：

- `Hit@K`: top-K 中命中任意 ground-truth chunk 即为 1。
- `Recall@K`: 历史结果文件中的 legacy 字段，当前等价于 query-level `Hit@K`，保留用于向后兼容。
- `evidence_recall@K`: top-K 中命中的 ground-truth chunk 数 / 该 query 的全部 ground-truth chunk 数。
- `MRR@K`: top-K 内第一个 relevant chunk 的 reciprocal rank。
- `nDCG@K`: binary relevance，支持多个 ground-truth chunks。

默认跳过 `ground_truth_chunk_ids=[]` 的 query。RAGBench/CUAD 中这类 no-evidence query 应单独报告 `num_skipped_no_gt`。

### Split and comparability guardrails

Task 10 汇总表之前必须满足以下 guardrails：

1. RAGBench eManual/CUAD 需要显式记录 `query_split`。正式主表优先使用 held-out `test` query；train/validation 可用于调参、反馈流或 smoke。
2. 同一 dataset 的 BM25/dense/hybrid 横向比较必须使用相同 query subset 和 corpus subset。
3. sampled corpus 必须通过 GT-in-corpus guardrail：所有有 GT 的评估 query 至少有一个 GT chunk 出现在 selected corpus。
4. CUAD 当前历史结果口径不完全一致，只能标为 `smoke_only` 或 `not_comparable`。
5. 表格需要包含 `scope`、`query_split`、`corpus_scope`、`corpus_sampling`、`task_type`、`comparable_group`、`is_comparable`、`gt_query_coverage`、`notes`。
6. 当前 dense baseline 使用 `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine；除非另跑 BGE/GTE，否则论文中不得称为 BGE-large。

当前 guardrails 已在 `experiment_guardrails.py` 中实现。baseline metrics/summary 会写出 split/sample metadata；`retrieval_baseline_comparison.csv` 会自动标注：

- eManual 已重跑为 held-out `test` split，三方法均为 `is_comparable=true`。
- CUAD 已重跑为统一 `test + max_queries=100 + gt_anchored_10000 corpus` smoke/sample 口径，三方法均为 `is_comparable=true`，但仍不得作为 full-corpus 主表结果。
- Banking77 为 `intent_retrieval_proxy`，应和 evidence retrieval 结论分开表述。

当前 guarded rerun 结果：

| Dataset | Scope | Query split | Corpus scope | Method | Queries | Skipped no GT | GT query coverage | Recall@10 | MRR@10 |
|---------|-------|-------------|--------------|--------|---------|---------------|-------------------|-----------|--------|
| eManual | heldout_test | test | full | BM25 | 130 | 2 | 1.0000 | 0.1154 | 0.0244 |
| eManual | heldout_test | test | full | dense all-MiniLM-L6-v2 | 130 | 2 | 1.0000 | 0.3231 | 0.0551 |
| eManual | heldout_test | test | full | hybrid RRF | 130 | 2 | 1.0000 | 0.1692 | 0.0366 |
| CUAD | smoke_only | test | gt_anchored_10000 | BM25 | 79 | 21 | 1.0000 | 0.0506 | 0.0232 |
| CUAD | smoke_only | test | gt_anchored_10000 | dense all-MiniLM-L6-v2 | 79 | 21 | 1.0000 | 0.0759 | 0.0334 |
| CUAD | smoke_only | test | gt_anchored_10000 | hybrid RRF | 79 | 21 | 1.0000 | 0.0633 | 0.0254 |

### Online learning protocol

Task 11-13 的在线学习实验必须先选定无泄漏协议：

- `prequential`: 每条 query 先评估，再使用其反馈更新模型。
- `train-feedback/test-eval`: train/validation query 只用于反馈流，held-out test query 只用于最终报告。

在线学习曲线应报告随机种子、mean/std、反馈预算、每轮 query 数和是否使用冷启动先验。

### Task24 audit guardrails

Task24 增加了审稿前修复项：

- 不再把 legacy `Recall@K` 当成严格多证据 recall；论文正文优先写 `Hit@K`，并在可用时补 `evidence_recall@K`。
- `prequential` 结果解释为模拟 test-time adaptation：每条 query 先评估，再用其模拟反馈更新策略；不能写成离线训练后独立 IID test。
- 成本下降口径限定为相对 full multi-route source candidate cost，不是相对 dense-only 更低。
- LoTTE 638k 新增 `static_nearest_ensemble`、`static_nearest_gated`、`uniform_random_ensemble`、`epsilon_greedy_ensemble`，用于区分多路召回表面、静态几何 arm 选择、静态几何成本门控和 LinUCB 反馈控制。
- `static_nearest_gated` 在 638k 上是强 baseline；论文主张应写成：dense/BM25/cluster 多路召回提供 coverage，静态几何已经能支持强 cost gate，LinUCB 的增量价值是 feedback-adaptive / trust-weighted / non-stationary route control。不能说 LinUCB 单独解释所有 full-route quality gain，也不能说当前实验已证明 LinUCB 对单次静态 cost gate 必不可少。

### Task25 credit assignment guardrail

Task25 修复并验证了 LinUCB reward 归因口径：

- 历史默认 `reward_attribution=final_fused` 仍保留，用于复现旧实验；但该口径会把 dense/BM25 rescue 命中也归因给所选 cluster arm。
- 新增 `reward_attribution=cluster_only`，用所选 cluster route 自身的 ranking reward 更新 LinUCB，从而避免 fused-ranking credit inflation。
- 新增 `confidence_mode=route_quality` 作为诊断 gate。100k smoke 显示它目前过于保守，几乎全量 fallback，因此当前主配置仍建议使用 `cluster_only/value`。
- LoTTE 100k 多 seed、8 epoch 对比显示：`cluster_only/value` 的 last route reward 从旧口径 `0.8076` 提升到 `0.8328`，selected cluster hit 从 `0.6908` 提升到 `0.7223`，平均 source candidate cost 从 `193.92` 降到 `181.47`；最终 Hit@10 从 `0.8826` 小幅降至 `0.8764`。这说明 LinUCB route 自身确实变好，但 dense/BM25 recall floor 对最终质量仍然重要。

Task25 结果记录在 `paper/experiments/task25_credit_assignment_summary.md` 和
`paper/experiments/task25_credit_assignment_comparison.csv`。

### Task26 low-cost routing

Task26 在 Task25 的 `cluster_only/value` 基础上降低 dense/BM25/cluster 深度，
验证 LinUCB route 变强后是否能进一步降成本：

- Task25 cluster-credit reference: `Hit@10=0.8764`, avg source cost `181.47`。
- Task26 B cost-balanced: `Hit@10=0.8579`, avg source cost `121.00`, last-epoch cost `104.30`，接近 pure dense top-100 成本但质量低于 dense。
- Task26 E quality-first: `Hit@10=0.8663`, avg source cost `166.33`, last-epoch cost `140.04`，几乎贴近 dense 100k baseline `0.8674`，但成本仍高于 pure dense。
- Task26 A cost-first smoke: avg source cost `84.38`，已经低于 dense top-100 成本，但 `Hit@10=0.8523`，质量损失明显。

结论：目前证据支持 quality-cost frontier，而不是无条件替代 dense。
IntentRoute 可以在 dense-heavy 高质量和 cluster-heavy 低成本之间调节；
越激进降低 dense，成本越低，但 Hit@10 会下降。详细记录见
`paper/experiments/task26_low_cost_routing_summary.md` 和
`paper/experiments/task26_low_cost_routing_comparison.csv`。

### Task27 dense-LinUCB two-route trade-off

Task27 关闭 BM25，只在 global dense 与 LinUCB cluster route 之间做 trade-off。
代码已允许 `bm25_depth=0` / `bm25_lite_depth=0`，此时不会生成或读取 BM25
artifact，BM25 候选成本为 0。

主要结果：

- Pure dense 100k baseline: `Hit@10=0.8674`, source candidate cost `100`。
- Task27 B formal: `Hit@10=0.8535`, avg source cost `97.76`, last-epoch cost `89.25`。成本低于 dense，但质量明显低于 dense。
- Task27 C formal: `Hit@10=0.8535`, avg source cost `107.18`, last-epoch cost `99.35`。稍高于 dense 成本，也没有补回质量。
- Task27 F quality smoke: `Hit@10=0.8624`, avg source cost `132.59`。更接近 dense，但成本不再低于 dense。

结论：二路 dense-LinUCB 可以把 candidate cost 压到 pure dense 以下，但当前
LoTTE 100k 上还不能在该成本预算下保持 dense-level quality。该结果应作为
边界实验写入论文：IntentRoute 当前支持可调 quality-cost frontier，而不是
保证低于 dense 成本且无损替代 dense。详细记录见
`paper/experiments/task27_dense_linucb_tradeoff_summary.md` 和
`paper/experiments/task27_dense_linucb_tradeoff_comparison.csv`。

### Task28 final context token-cost correction

Task28 复算了 saved rankings 的 final top-10 context tokens。此前所有
`avg_source_candidate_cost` 都是 retrieval-stage candidate-count proxy，不是
LLM context token cost。

LoTTE 100k `cl100k_base` 复算结果：

- Dense-only: `Hit@10=0.8674`, `avg_context_tokens@10=1472.39`。
- Task19-D: `Hit@10=0.8770`, `avg_context_tokens@10=1518.44`, `1.0313x` dense。
- Task19-E: `Hit@10=0.8865`, `avg_context_tokens@10=1549.83`, `1.0526x` dense。
- Task20-S: `Hit@10=0.8747`, `avg_context_tokens@10=1516.24`, `1.0298x` dense。
- Task25 cluster-credit: `Hit@10=0.8764`, `avg_context_tokens@10=1550.65`, `1.0532x` dense。
- Task26-B: `Hit@10=0.8579`, `avg_context_tokens@10=1517.60`, `1.0307x` dense。
- Task26-E: `Hit@10=0.8663`, `avg_context_tokens@10=1530.35`, `1.0394x` dense。
- Task27-B: `Hit@10=0.8535`, `avg_context_tokens@10=1479.17`, `1.0046x` dense。

结论：当前固定 top-10 generation 下，候选数下降没有转化为 final context
token 下降。论文中不能声称 IntentRoute 已证明 LLM token cost 低于 dense。
目前成立的是 retrieval candidate reduction / dense invocation reduction。
若要证明 token cost 优势，需要后续设计 variable top-k、token-budgeted context
packing 或 confidence-based evidence compression。

Task28.1 将这个修正回填到历史 Task16-25 saved rankings，覆盖 Banking77、
CUAD、eManual、LoTTE sample、LoTTE 100k/200k/400k/638k，共 `106` 条
per-run 记录和 `48` 条聚合记录。结果记录在
`paper/experiments/task28_1_context_token_backfill_summary.md` 和
`paper/experiments/results/task28_1_context_token_backfill.md`。

代表性结论：

- Banking77 gated cost-aware: `Hit@10=0.9813`，context token 为 dense 的
  `0.9978x`，source candidate cost 为 `142.51`。
- LoTTE 100k Task20-S: `Hit@10=0.8747`，context token 为 dense 的 `1.0298x`，
  source candidate cost 为 `227.29`。
- LoTTE 100k Task25 cluster-credit: `Hit@10=0.8764`，context token 为 dense
  的 `1.0532x`，source candidate cost 为 `181.47`。
- LoTTE 638k Task22 formal gated: `Hit@10=0.7343`，context token 为 dense 的
  `1.0487x`，source candidate cost 为 `236.22`。

因此，Task16-27 的成本结论应写为 source-candidate / dense-query reduction。
最终 prompt/context token cost 的正面证据从 Task29 的
`final_context_policy=confidence_topk` 开始。

### Task29 confidence-based final context policy

Task29 正式把 Task28 的修正落到实验策略上：不再只减少 retrieval-stage
candidate，而是让 LinUCB 在高置信 route 下直接减少最终送入 LLM 的 context
chunk 数。

新增 `final_context_policy=confidence_topk`：

- `fixed_topk`：保持此前固定 top-k。
- `confidence_topk`：只有当 route 为 `linucb_primary` 或 `hybrid_lite`，且
  confidence/semantic drift 通过 gate 时，才压缩最终 context。
- dense fallback 不压缩，继续作为低置信兜底。

LoTTE 100k smoke frontier：

- A：high `k=5`，mid `k=7`：`Hit@10=0.8339`，
  `avg_context_tokens@10=999.38`，为 dense 的 `0.6787x`。
- B：high `k=7`，mid `k=9`：`Hit@10=0.8490`，
  `avg_context_tokens@10=1261.91`，为 dense 的 `0.8570x`。
- C：high `k=8`，mid `k=10`：`Hit@10=0.8624`，
  `avg_context_tokens@10=1391.59`，为 dense 的 `0.9451x`。

Task29-C 三 seed formal：

- Dense top-10 baseline：`Hit@10=0.8674`，
  `avg_context_tokens@10=1472.39`。
- Task29-C mean：`Hit@10=0.8652`，
  `avg_context_tokens@10=1401.24`，为 dense 的 `0.9517x`。

结论：保守的 confidence-based final context compaction 可以在 LoTTE 100k 上
把最终 context tokens 降低约 `4.8%`，同时保持 near-dense quality
（`Hit@10` 平均仅低约 `0.22` 个百分点）。这证明了真实 token-cost
优化机制可行，但也说明更激进的 token saving 会带来明确召回损失。
详细记录见 `paper/experiments/task29_confidence_context_policy_summary.md`。

Task29.1 LoTTE 200k scale-up 使用同一套 Task29-C 策略：

- Dense top-10 baseline：`Hit@10=0.7970`，
  `avg_context_tokens@10=1444.12`。
- Task29-C mean：`Hit@10=0.8249`，
  `avg_context_tokens@10=1376.46`，为 dense 的 `0.9531x`。

200k 结果更强：final context tokens 下降约 `4.7%`，同时 mean `Hit@10`
高于 dense-only 约 `2.8` 个百分点。这支持一个更具体的论文判断：当 corpus
规模增大、pure dense top-10 优势下降时，feedback-guided LinUCB route
control 更可能同时带来 dense-level quality 与真实 final-context-token 节省。

Task29.1 LoTTE 400k scale-up 继续使用同一套 Task29-C 策略，并复用 canonical
scale-store corpus embeddings：

- Dense top-10 baseline：`Hit@10=0.7718`，
  `avg_context_tokens@10=1482.30`。
- Task29-C mean：`Hit@10=0.7819`，
  `avg_context_tokens@10=1403.43`，为 dense 的 `0.9468x`。

400k 结果继续支持该方向：final context tokens 下降约 `5.3%`，同时 mean
`Hit@10` 高于 dense-only 约 `1.0` 个百分点。100k/200k/400k 三组共同说明：
保守的 confidence-based final context compaction 可以稳定降低最终 context
token，且在更大 corpus 上有机会保持 dense-level 召回质量。

Task29.1 LoTTE 638k full-corpus scale-up 使用同一套 Task29-C 策略，并复用
canonical scale store 与 shared retrieval artifacts：

- Dense top-10 baseline：`Hit@10=0.7282`，
  `avg_context_tokens@10=1525.62`。
- Task29-C mean：`Hit@10=0.7466`，
  `avg_context_tokens@10=1451.49`，为 dense 的 `0.9514x`。

638k 结果完成了 LoTTE 全量规模链路：final context tokens 下降约 `4.9%`，
同时 mean `Hit@10` 高于 dense-only 约 `1.85` 个百分点。100k/200k/400k/638k
共同说明：保守的 confidence-based final context compaction 可以稳定降低最终
context token，并且在更大 corpus 上保持 dense-level quality。

Task29.2 将上述结果整理为 token-quality frontier：

| Scale | Method | Hit@10 | Avg Context Tokens@10 | Token Ratio | Hit Delta |
|---|---|---:|---:|---:|---:|
| 100k | Task29-C mean | 0.8652 | 1401.24 | 0.9517x | -0.22 pp |
| 200k | Task29-C mean | 0.8249 | 1376.46 | 0.9531x | +2.80 pp |
| 400k | Task29-C mean | 0.7819 | 1403.43 | 0.9468x | +1.01 pp |
| 638k | Task29-C mean | 0.7466 | 1451.49 | 0.9514x | +1.85 pp |

同时，100k A/B/C smoke frontier 说明 compaction 越激进，token saving 越大，
但召回损失也越明显。论文主结果应使用保守的 Task29-C；A/B 可作为
quality-cost frontier 消融。整理文件：
`paper/experiments/task29_2_token_quality_frontier.md`，
CSV 为 `paper/experiments/results/task29_token_quality_frontier.csv`。

Task29.3 补充了 Task29-C 的 seed-level variance / 95% CI。所有区间均基于
`13,17,19` 三个 seed 的 two-sided t interval，因此应作为工程稳定性诊断，
不能单独当作强统计显著性证明：

| Scale | Task29-C Hit@10 mean | Hit@10 95% CI | Token saving mean | Token saving 95% CI |
|---|---:|---:|---:|---:|
| 100k | 0.8652 | [0.8565, 0.8739] | 4.83% | [2.89%, 6.77%] |
| 200k | 0.8249 | [0.8052, 0.8446] | 4.69% | [3.89%, 5.48%] |
| 400k | 0.7819 | [0.7709, 0.7929] | 5.32% | [0.11%, 10.53%] |
| 638k | 0.7466 | [0.7246, 0.7687] | 4.86% | [4.24%, 5.48%] |

Task29.3 支持的论文口径是：Task29-C 的 token saving 不是单个 seed 的偶然
结果；四个规模上的均值均保持正向，且 638k 的 token saving 区间较窄。
详细记录见 `paper/experiments/results/task29_3_seed_variance_ci.md`。

### Task30 LoTTE multi-scale geometry validation

Task30 补充了正式写论文前的流形几何验证尝试。它不重跑 retrieval 或 LinUCB，
而是复用 canonical scale-store embeddings、shared PCA/KMeans context
artifacts，以及 Task29-C token-quality frontier，检查 LoTTE 100k/200k/400k/638k
上的几何信号是否能支持 piecewise relevance-manifold 解释。

| Scale | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Dense Hit@10 | Task29-C Hit@10 | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100k | 182 | 0.6437 | 0.8870 | 0.9033 | 0.8674 | 0.8652 | 4.83% |
| 200k | 186 | 0.6292 | 0.8697 | 0.8947 | 0.7970 | 0.8249 | 4.69% |
| 400k | 190 | 0.6110 | 0.9016 | 0.8826 | 0.7718 | 0.7819 | 5.32% |
| 638k | 196 | 0.5867 | 0.9016 | 0.8571 | 0.7282 | 0.7466 | 4.86% |

解释：

- LoTTE 随规模增大表现出更复杂的几何结构：sample `PCA dim90` 从 `182`
  增至 `196`，`PCA var@64` 从 `0.6437` 降至 `0.5867`。
- 但 nearest-cluster GT routing signal 没有消失，`nearest_cluster_hit@3`
  稳定在高 `0.8` 到 `0.9` 区间。
- PCA/context geometry alone 的 retention 从 `0.9033` 降到 `0.8571`，说明
  geometry 适合作为 route-control signal，但不能单独替代 dense retrieval。
- Task30 支持“分片相关性流形”作为解释性假设和诊断框架；不能写成几何指标
  单独保证召回提升的定理。

详细记录见 `paper/experiments/task30_lotte_geometry_scale_validation.md` 和
`paper/experiments/results/task30_lotte_geometry_scale_validation.md`。

### Task31 paper evidence package

Task31 是正式写论文前的总控证据包，不新增实验。它把 Task1-30 的结果整理成：

- final thesis；
- claim ledger；
- main Task29 token-quality result table；
- feedback / geometry / cost 分层证据；
- dataset roles；
- paper section outline；
- reviewer risk checklist；
- final English / Chinese paper claim wording。

正式写论文时优先使用 `paper/experiments/task31_paper_evidence_package.md` 作为
入口，再回溯引用各 task 的详细结果。Task31 的核心结论是：论文主张应放在
“feedback-driven adaptive retrieval controller + confidence-based final context
compaction”，而不是“无条件替代 dense”或“candidate cost 等于 token cost”。

### Task32 paper draft skeleton

Task32 开始正式论文写作阶段，在 `paper/draft/` 下建立可迭代的初稿骨架：

- `paper/draft/README.md`：写作入口、证据来源和当前主张边界。
- `paper/draft/outline.md`：标题候选、核心 thesis、贡献、章节结构和图表计划。
- `paper/draft/abstract.md`：摘要初稿和短版摘要。
- `paper/draft/introduction.md`：Introduction 初稿，明确 RAG trade-off、垂类分片相关性流形假设、IntentRoute 控制器定位和贡献。
- `paper/draft/method.md`：Method 初稿，覆盖 multi-route surface、KMeans fixed arms、LinUCB、trust-weighted feedback、route-level credit、final context compaction。
- `paper/draft/experiments.md`：Experiments 初稿，记录 dataset roles、protocol、Task29 主表、Task29.3 CI、Task30 geometry 和 limitation cases。
- `paper/draft/limitations.md`：Limitations 初稿，明确 simulated feedback、retrieval-only、dense baseline、geometry framing、KMeans 选择和 token cost 口径。

Task32 不新增实验，也不修改结果文件。它把 Task31 证据包转成论文草稿结构，
后续正式写作应继续以 `paper/experiments/task31_paper_evidence_package.md` 为
证据总入口。

### Task33 pre-writing validation backlog

Task33 最初记录正式扩写论文前建议补齐的风险缓解项；当前该 section 已更新为
完成状态和写作口径索引。
计划文件为 `paper/experiments/task33_pre_writing_validation_backlog.md`。

优先级如下：

1. multi-embedding robustness：模型选择矩阵见
   `paper/experiments/task33_1_embedding_model_selection.md`。优先使用
   `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` 做 LoTTE 100k
   CPU-friendly robustness；`nomic-ai/nomic-embed-text-v1.5` 作为开源强模型
   smoke；BGE 降级为 GPU/overnight optional。
   Task33.1a 已完成：multi-qa dense `Hit@10=0.8809`，Task29-C mean
   `Hit@10=0.8853`，final context token saving `3.35%`，
   `nearest_cluster_hit@3=0.8826`。详见
   `paper/experiments/task33_1a_multiqa_minilm_robustness_summary.md`。
2. feedback simulation sensitivity：覆盖 no/mild/strong noise、equal noisy、
   trust-weighted 等设置。Task33.2 已完成，使用主证据模型
   `sentence-transformers/all-MiniLM-L6-v2` 在 LoTTE 100k 上验证：
   no-feedback 主要依赖 dense/full fallback，不代表自进化；oracle 是上界；
   trust_default 相比 equal_default 将 last true reward 从 `0.7517` 提升到
   `0.8328`，selected-cluster hit 从 `0.5979` 提升到 `0.7223`，dense rate
   从 `0.7480` 降到 `0.6708`；trust_mild 达到 `Hit@10=0.8775`、final
   context token ratio `0.9255x`；strong noise 会破坏策略，应作为 limitation。
   详见 `paper/experiments/task33_2_feedback_sensitivity_summary.md`。
3. clean ablation table：Task33.3 已完成，详见
   `paper/experiments/task33_3_clean_ablation_table.md`。表格整理了
   dense-only、BM25-only、dense+BM25 hybrid、static KMeans geometry、
   no-feedback、equal-feedback、trust-feedback、trust-mild、Task29-C 和
   oracle feedback。核心归因是：dense 是质量地板；BM25/static hybrid
   提供路线多样性但不能直接省 token；KMeans geometry 提供 route signal；
   LinUCB 需要可靠 feedback 才能体现自进化；trust-weighting 改善 credit
   assignment；final context compaction 才是最终 token saving 机制。
4. protocol defense write-up：Task33.4 已完成，详见
   `paper/experiments/task33_4_protocol_defense.md`，并已写入
   `paper/draft/experiments.md` 和 `paper/draft/method.md`。核心口径是：
   每条 query 先冻结当前 policy、完成 ranking 和 evaluation，然后才把该
   query 的 GT 转成 simulated feedback 更新 LinUCB；当前 query 的 feedback
   不能反向改善当前 ranking，future query feedback 也不可见。因此该协议是
   no-leakage prequential simulated test-time adaptation，不是 offline IID test。
5. small end-to-end LLM generation smoke：Task33.5 已完成，详见
   `paper/experiments/task33_5_llm_generation_smoke_summary.md`。使用
   `deepseek-v4-flash` thinking mode 对 LoTTE 100k 的 60 条 query 进行了
   dense top-10 vs Task29-C compressed context 生成质量 smoke。judge 全部有效
   `60/60`，winner counts 为 `tie=32`、`dense=14`、`Task29-C=14`；
   faithfulness 基本持平，Task29-C sampled prompt context token proxy 为
   `0.9321x` dense。该结果支持“没有明显生成质量退化”的 sanity-check 结论，
   但不替代 retrieval/token 主实验。
6. optional additional seeds：Task33.6 已完成，详见
   `paper/experiments/task33_6_additional_seeds_summary.md`。LoTTE 100k
   Task29-C 从 3 seeds 扩展到 5 seeds 后，mean `Hit@10=0.8708`，dense
   `Hit@10=0.8674`，final context token ratio `0.9507x`，约节省 `4.93%`
   final retrieved context tokens。Hit delta 的 95% CI 跨过 0，因此该项只用于
   稳定性补强，不用于声称统计显著优于 dense。
7. pre-writing consistency audit：Task33.7 已完成，详见
   `paper/experiments/task33_7_pre_writing_consistency_audit.md`。该项不新增
   实验，而是统一正式写作前的 claim boundary、metric vocabulary、
   claim-to-evidence map 和 reviewer-risk guardrails。
8. review defense revision：Task34 已完成，详见
   `paper/experiments/task34_review_defense_revision_plan.md`。该项吸收 Opus
   review 中最关键的写作防御点：400k CI 方差、Task29-C conservative
   rationale、mean-above-dense 措辞、effective compaction rate、multi-epoch
   disclosure，以及 evidence_recall trade-off。
9. context-budget optimization：Task37 已开始，详见
   `paper/experiments/task37_context_budget_optimization.md`。该项先验证了
   aggressive fixed-k compaction 会显著增加 token saving 但损伤 Hit@10；
   更有效的方向是基于完整 gated top-10 ranking 做 token-budget tail
   pruning。Task37-B 已扩展到 LoTTE 100k/200k/400k/638k。固定
   `gated_fixed + token_budget_r0.95_m5` 在四个 scale 上均保持 above-dense
   `Hit@10`，final context token ratio 分别为 `0.9227x`、`0.9296x`、
   `0.9056x`、`0.9176x`，平均约 `0.9189x`，即约 `8.1%` LLM
   evidence-context input token saving。相比 Task29-C 约 `4.7-5.3%` 的
   saving，Task37 是更强的主结果候选。Task37-C 已完成 query-level paired
   significance test：所有 scale/seed 的 final context token saving 均为
   Wilcoxon `p<0.05`，Task37 在四个规模上的三 seed 平均 Hit delta 均不低于
   dense；但严格 `1pp` non-inferiority 不是所有 seed 都通过。因此论文主张应
   写成“显著降低 LLM evidence-context input tokens，同时在均值上保持
   dense-level 或 above-dense Hit@10”，而不是“所有 seed/scale 均统计显著
   non-inferior”。Task37-D 已补 dense adaptive top-k / same-budget baseline：
   dense top-9 和 dense `token_budget_r0.95_m5` 虽然能节省更多 token，但在
   100k/200k/400k/638k 上均损伤 Hit@10；Task37 保持更高 Hit@10，同时仍节省
   约 `7-9%` final evidence-context tokens。因此 Task37 的收益不能简化解释为
   “dense 少取几个 chunk”，而应归因于更强的 gated ranking + conservative
   tail pruning。
10. calibrated context-budget validation：Task38 已完成，详见
    `paper/experiments/task38_calibrated_context_budget_validation.md`。该项回应
    Task37 可能存在的 test-set model-selection bias：将 LoTTE 596 个 held-out
    queries 确定性划分为 179 calibration / 417 frozen test queries，只在
    calibration 上选择 token-budget policy，然后冻结到 test 上评估。结果显示：
    Task38 在 100k/200k/400k/638k 的 frozen test 上分别取得约 `6.18%`、
    `16.00%`、`6.57%`、`17.53%` final LLM evidence-context input token
    saving；平均 Hit@10 在 100k 基本等于 dense，在 200k/400k 高于 dense，在
    638k 仅低约 `0.08pp`。dense adaptive truncation 虽然更省 token，但所有
    scale 都损伤 Hit@10。Task38 因此强化了“不是简单 dense top-k 裁剪”的结论，
    但仍应透明报告严格 seed-level non-inferiority 并非所有 scale/seed 都通过。
11. LoTTE cross-domain validation：Task39 的 science/search 20k/q200 和
    100k checkpoint 均已完成，详见
    `paper/experiments/task39_lotte_cross_domain_validation.md`。当前已完成
    `LoTTE science/search` 的数据缓存、`20k/q200` 与 `100k` processed
    slices、science scale-store 增量扩展、dense baseline、gated cost-aware
    LinUCB formal run，以及 Task38-style calibrated context-budget protocol。
    `lotte_science_search_20k_q200` dense baseline 为 `Hit@10=0.8950`、
    `EvidenceRecall@10=0.7384`；gated cost-aware LinUCB 为
    `Hit@10=0.9267`、`EvidenceRecall@10=0.7406`。在 60 calibration / 140
    frozen test split 上，选出的 `token_budget_r0.85_m4` 使三个 LinUCB seed
    的 frozen-test Hit@10 均高于 dense top-10，并节省约 `13.18%`、
    `14.31%`、`13.91%` final LLM evidence-context input tokens；dense
    adaptive truncation 虽然节省约 `22.69%` tokens，但 Hit@10 低于 dense。
    `lotte_science_search_100k` dense baseline 为 `Hit@10=0.8926`、
    `EvidenceRecall@10=0.7328`；gated cost-aware LinUCB 为
    `Hit@10=0.9077`、`EvidenceRecall@10=0.7277`。100k 的 calibrated
    `token_budget_r0.85_m4` 可节省约 `17.53%` 到 `20.53%` final context
    tokens，但 frozen-test Hit@10 相对 dense top-10 为小幅下降到持平；该结果
    支持 ranking-side cross-domain generalization，同时提示 context compression
    强度需要按 domain/scale 校准，不能无条件迁移。
12. feedback-driven hard-case recovery：Task40 已完成，详见
    `paper/experiments/task40_feedback_recovery_summary.md`。该项针对 aggressive
    context-budget 造成的尾部 affected queries，验证 simulated feedback 是否能
    恢复证据召回。Same-query retry 在 `science 100k` 上使用 arm boost +
    conservative budget 恢复 `14/34` affected queries，平均仍保留约 `5.76%`
    token saving；在 `technology 100k` 上恢复 `9/42` affected queries，平均
    保留约 `11.75%` token saving。更强的 full-context fallback 可恢复更多
    query，但 token saving 明显下降。Calibration-to-test 泛化结果较保守：
    learned risky-arm fallback 在 science 上平均提升约 `+0.16pp` 到 `+0.48pp`
    Hit@10，在 technology 上约为 `-0.16pp` 到 `+0.16pp`。结论是 feedback
    可作为 tail-query recovery / fallback trigger，但不能写成无条件全局提升。
    从统计解释上，same-query post-feedback recovery 是最强证据：
    conservative retry 合并两个 100k domains 后恢复 `23/76` affected queries，
    约 `30.3%`，近似 Wilson 区间约为 `21%` 到 `41%`；而 calibration-to-test
    泛化只能作为方向性和边界证据，不应写成显著 held-out improvement。
13. Dense+Sentence-MMR same-budget baseline：Task46 已完成，详见
    `paper/experiments/task46_sentence_mmr_same_budget_summary.md`。该项直接回应
    “为什么不直接压缩 dense top-10 context”的审稿问题：在 LoTTE
    technology/search 100k 的 Task38 frozen test split 上，Dense+Sentence-MMR
    以 dense top-10 为候选句子池，并使用 Task38 frozen policy 的 per-query
    final-context token budget 作为上限。结果显示该 baseline 在 chunk-support
    `Hit@10` 上与 dense top-10 持平，同时节省约 `11.4-13.1%` selected
    sentence tokens。该结果应作为强 compression baseline / boundary evidence
    使用，提示论文不能声称 IntentRoute 支配句子级 compression；更稳妥的表述是
    IntentRoute 是与 sentence compression / reranking 互补的 route-and-budget
    controller。
14. compressor-normalized comparison：Task48 已完成，详见
    `paper/experiments/task48_compressor_normalized_summary.md`。该项将同一个
    SentMMR final-context compressor 同时接到 dense top-10 和 Task38 frozen
    IntentRoute evidence pools 后面，检验“统一 compression layer”下的公平对比。
    在 LoTTE technology/search 100k frozen test split 上，Dense+SentMMR 在
    `0.95/0.90/0.85` ratios 下均保持 dense chunk-support `Hit@10=0.8705`，
    并节省约 `5.3/10.2/15.2%` tokens。IntentRoute+SentMMR 继承各自
    IntentRoute seed 的 `Hit@10=0.8657-0.8777`，在相同 compressor ratios
    下相对 dense 共节省约 `10.1-21.2%` tokens，相对自身未压缩 source 额外节省
    约 `5.4/10.3/15.2%`。该结果支持把 SentMMR 写成共享 final-context
    compressor，把 IntentRoute 写成上游 route-and-budget controller；不要写成
    IntentRoute 支配 compression。
15. cross-encoder reranker same-budget baseline：Task47 已完成，详见
    `paper/experiments/task47_cross_encoder_reranker_summary.md`。该项以 dense
    top-50 为候选池，用 `cross-encoder/ms-marco-MiniLM-L-6-v2` 对 query-chunk
    对重排，并在 LoTTE technology/search 100k 的 Task38 frozen test split 上
    比较 full reranked top-10 与同预算重排结果。Full reranked top-10 将
    `Hit@10` 从 dense 的 `0.8705` 提升到 `0.8777`，`EvidenceRecall@10` 从
    `0.7081` 提升到 `0.7332`，但平均 context tokens 从 `1470` 增加到
    `1792`。在 Task38 per-query token budget 下，reranker same-budget 的
    `Hit@10=0.8633-0.8729`，未稳定超过 IntentRoute target 的
    `0.8657-0.8777`。该结果支持把 cross-encoder 写成强 ranking baseline，
    同时保留 IntentRoute 作为轻量 route-and-budget controller 的定位。
16. strong-baseline-aware manuscript reframing：Task49 已完成，详见
    `paper/experiments/task49_strong_baseline_reframing_summary.md`。该项将
    Task46/47/48 的强 baseline 证据整合进 abstract、introduction、related
    work、experimental setup、results、conclusion 和 appendix，并重新生成
    LaTeX。当前论文主张已统一为：dense 是 recall floor，SentMMR 是共享
    final-context compressor，cross-encoder 是 late ranking layer，IntentRoute
    是可与二者叠加的 route-and-budget controller。
17. experiment validation framework：Task51 已完成，详见
    `paper/experiments/task51_experiment_validation_framework.md`。该项新增
    `task51_experiment_manifest.json` 和
    `scripts/task51_experiment_validation.py`，把后续新增实验统一纳入
    dimension/statistics/display readiness 审计。默认审计覆盖 Task38 主
    token-quality frontier、Task39 science/search cross-domain validation、
    Task46 Sentence-MMR、Task47 cross-encoder reranker、Task48
    compressor-normalized comparison、Task52 BGE-base dense baseline、Task53
    matched-backbone embedding generalization，以及 Task54 positive-hit
    trade-off tuning、Task55 backbone stability summary、Task58 geometry
    random ablation、Task59 feedback-control ablation、Task60 arm-count
    sensitivity、Task61 geometry-to-control analysis 和 Task62
    prompt-compression baseline。当前审计结果为
    `763 PASS / 0 WARN / 0 ERROR`。
    Task39 science/search processed dataset、Task53 artifacts、Task54
    positive-hit artifacts、Task55 stability artifacts、Task58 geometry
    ablation artifacts、Task59 feedback-control artifacts、Task60 arm-count
    sensitivity artifacts、Task61 diagnostic artifacts 和 Task62
    prompt-compression artifacts 已在本地 manifest 中配置，并开启 query、GT、
    top-k ranking chunk 引用、paired 统计与展示结构校验。
18. strong embedding dense baseline：Task52 已完成，详见
    `paper/experiments/task52_strong_embedding_baseline_summary.md`。该项用
    `.venv-rocm` 和 AMD Radeon RX 9070 XT 跑
    `BAAI/bge-base-en-v1.5`，在 LoTTE technology/search 100k 上生成
    top-50 dense rankings，并用 Task38 frozen test split 做强 embedding
    baseline 对比。BGE-base dense 将 held-out `Hit@10` 从 MiniLM dense 的
    `0.8705` 提升到 `0.8993`，paired delta 为 `+2.88pp`，95% bootstrap CI
    为 `+0.48pp` 到 `+5.28pp`，McNemar `p=0.0357`；同时平均 top-10 context
    tokens 从 `1470` 增加到 `1708`，相对 MiniLM dense 增加约 `16.18%`。
    当前 MiniLM-branch IntentRoute target policies 相对 BGE 仍节省约
    `18.22-20.07%` tokens，但 `Hit@10` 低 `2.16-3.36pp`。该结果应写成
    claim-tightening strong baseline：强 dense 会抬高质量 floor，后续需要
    将 IntentRoute 的 dense branch 也替换为 BGE 后再比较统一 route-and-budget
    frontier。
19. embedding backbone generalization：Task53 已完成，详见
    `paper/experiments/task53_embedding_backbone_generalization_summary.md`。
    该项把 IntentRoute 与 dense baseline 统一为 matched-backbone 对比：
    MiniLM、BGE-base 和 E5-base 均使用同一 LoTTE technology/search 100k
    corpus、Task38 frozen split、context-token accounting 和 Task51 审计。
    BGE-base full multi-route 在 held-out 上相对 BGE dense 的平均
    `Hit@10` delta 为 `-0.08pp`，同时节省约 `11.99%` final context
    tokens；E5-base full multi-route 平均 delta 为 `-0.64pp`，节省约
    `12.20%` tokens。BGE/E5 gated-cost variants 则分别降低约 `2.48pp`
    和 `3.44pp` Hit@10，可作为更激进 retrieval-cost boundary，而不是主
    quality-preserving 结论。该结果支持把论文主张写成 matched-backbone
    route-and-budget trade off，而不是 MiniLM-specific dominance claim。
20. positive-hit trade-off tuning：Task54 已完成，详见
    `paper/experiments/task54_positive_hit_tradeoff_summary.md`。该项在 BGE
    full multi-route rankings 上改用更保守的 `token_budget_r0.97_m4`
    operating point，使 frozen test 三个 seed 的 `Hit@10` 均高于 BGE dense：
    delta 为 `+0.72pp` 到 `+0.96pp`，同时仍节省 `6.50-8.11%` final
    context tokens。E5-base 在当前 frozen split 下没有找到同时高于 dense
    且省 token 的点，因此 Task54 应写成 BGE quality-first tunability
    evidence，而不是所有 backbone 的通用正向结论。
21. backbone stability summary：Task55 已完成，详见
    `paper/experiments/task55_backbone_stability_summary.md`。该项不重跑
    retrieval，而是复用 Task38、Task53、Task54 既有 artifacts，对固定
    seeds `13,17,19` 做 seed-level stability 汇总。其目的不是寻找最佳
    seed，而是验证 matched-backbone route-and-budget 主张在随机聚类、
    query 顺序和模拟反馈变化下是否稳定且可统计检验。结果显示 BGE full
    的 mean Hit@10 delta 为 `-0.08pp`、seed SD 为 `0.37pp`，同时节省
    `11.99%` final context tokens；BGE positive 的 mean delta 为
    `+0.88pp`、seed SD 为 `0.14pp`，同时节省 `7.23%` tokens；BGE/E5
    gated variants 均表现为稳定负向 Hit@10 delta，应作为 cost-aggressive
    boundary，而不是主推 setting。
22. claim-evidence alignment：Task56 已完成，详见
    `paper/experiments/task56_claim_evidence_alignment.md`。该项不新增实验，
    而是把 manifold-inspired motivation、LoTTE 几何诊断、Task38/39
    calibration evidence、Task46/47/48 strong baselines、Task53 matched
    backbone、Task54 BGE positive-hit tuning 和 Task55 seed stability 统一成
    claim-evidence map。当前建议的核心写法是：IntentRoute 是由流形假设启发、
    经几何诊断支持的 route-and-budget controller；它不证明流形定理，也不
    universal dominate dense，但在 calibrated/frozen 与 matched-backbone
    设置下可以形成可统计检验的 dense-level / near-dense quality-cost
    trade-off，并在 BGE quality-first operating point 上取得高于 BGE dense
    的 Hit@10 且节省 final context tokens。
23. review response action map：Task57 已完成，详见
    `paper/experiments/task57_review_response_action_map.md`。该项保存
    Hermes/GLM review 后的后续任务路线，并明确不把论文降级为普通
    compression baseline：几何/流形启发定义结构化 route，feedback-updated
    LinUCB 估计 route confidence 并控制 route shape/fallback，独立校准的
    final-context budget 负责形成 token-quality operating points。后续任务固定使用
    seeds `13,17,19`，不再扩 seed；统计支撑改由 query-level paired tests、
    cross-backbone、cross-domain、cross-ablation 和 calibration/test discipline
    共同完成。Task58-67 将依次处理 random/shuffled geometry ablation、
    static/no-LinUCB feedback-control ablation、arm-count sensitivity、
    geometry-to-control analysis、prompt-compression baseline、expanded
    downstream LLM evaluation、manuscript claim reframe、table/figure refresh、
    Elsevier/IP&M conversion 和 final validation packet。
24. geometry random ablation：Task58 已完成，详见
    `paper/experiments/task58_geometry_random_ablation_summary.md`。该项在
    LoTTE technology/search 100k 上比较 static nearest-centroid geometry 与
    uniform random cluster-arm selection，固定 seeds `13,17,19`，并使用同一
    Task38 calibration/test final-context budget protocol。结果显示 full
    multi-route surface 下 final `Hit@10` 会被 dense/BM25 rescue 保护：
    random control 仍可取得 mean test Hit delta `+1.04pp` 和 `11.92%`
    token saving；但 route-control 指标明显区分 geometry 与 random，static
    nearest 的 route reward 为 `0.8563`、selected cluster hit 为 `0.8870`，
    random control 分别只有 `0.1499` 和 `0.1577`。因此论文应写成：
    geometry 是有效 route-confidence/control signal，但不是 standalone
    dense replacement，也不能用 final fused Hit@10 alone 证明 geometry
    解释全部收益。
25. feedback-control ablation：Task59 已完成，详见
    `paper/experiments/task59_feedback_control_ablation_summary.md`。该项在
    LoTTE technology/search 100k 上比较 learned full multi-route、learned
    gated cost-aware、static-nearest gated、no-feedback gated、static-nearest
    ensemble 和 uniform-random ensemble，并使用同一 `task59_100k`
    calibration/test final-context budget split。结果显示 no-feedback gated
    的高 final Hit@10 来自 full dense/BM25 fallback：dense rate 为 `1.0000`、
    LinUCB primary rate 为 `0.0000`、route reward 仅 `0.1504`。反馈学习
    相比 no-feedback/random 有明显 route-quality 信号（learned route reward
    `0.6790` vs. random/no-feedback 约 `0.15`），但 static-nearest geometry
    仍是更强 route prior（route reward `0.8563`、selected cluster hit
    `0.8870`）。当前 learned gated setting 能降低 dense 调用（dense rate
    `0.7377`、primary rate `0.2623`），但 frozen-test Hit@10 下降较大
    （`-5.20pp`），应作为 cost-aggressive boundary，而不是主
    quality-preserving 结论。
26. arm-count sensitivity：Task60 已完成，详见
    `paper/experiments/task60_arm_count_sensitivity_summary.md`。该项在
    LoTTE technology/search 100k 上测试 `K in {8,16,32,64,128}`，固定
    seeds `13,17,19`，并比较 static-nearest geometry、full multi-route
    和 gated cost-aware 三种模式。结果显示 static-nearest geometry 的 route
    reward 在 `0.8272-0.9128` 范围内，selected-cluster hit 保持在
    `0.8496-0.9480`，说明几何 arm surface 对合理 K 变化不脆弱。full
    multi-route 的 fused Hit@10 保持在 `0.8775-0.8837`，budgeted frozen-test
    rows 均为正 mean Hit@10 delta 且节省 final context tokens。retrieval-stage
    gated 对 K 敏感：K=8 可把 dense rate 降到 `0.4083`，但 gated rows 均有
    负向 frozen-test Hit@10 delta，因此仍应作为 dense-call saving 的
    cost-aggressive boundary，而不是主质量保持结论。Task60 支持将
    `n_clusters=32` 写成可复现工程默认值，而不是理论最优值。
27. geometry-to-control analysis：Task61 已完成，详见
    `paper/experiments/task61_geometry_to_control_analysis.md`。该项复用
    Task30、Task43、Task58、Task60 和 Figure 4 的既有结果，不重跑检索，
    用相关性诊断连接 geometry metrics、route-control outcomes 和
    budgeted final-context results。结果显示跨规模 Figure 4 诊断是 small-N
    且混合的：nearest-cluster hit 与 final Hit delta 为正相关，但与 token
    saving 为负相关，说明不能写成 geometry alone 决定最终收益。控制层信号
    更清楚：Task60 中 `arm_count` 与 learned route reward 的 Pearson
    `r=-0.9913`，learned route reward 与 gated dense rate 的 Pearson
    `r=-0.9141`；Task58 中 static geometry 相比 uniform random 的 route
    reward 高 `+70.64pp`、selected-cluster hit 高 `+72.93pp`。因此论文应写成：
    geometry 是 route-control/confidence 的解释性和设计性信号，最终
    quality-cost trade off 来自 geometry-defined arms、feedback-updated
    LinUCB、dense/BM25 rescue 与 calibrated budget control 的组合。
28. prompt-compression baseline：Task62 已完成，详见
    `paper/experiments/task62_prompt_compression_baseline_summary.md`。该项在
    LoTTE technology/search 100k frozen test split 上新增
    Selective Context-style prompt-pruning baseline，并使用与 Task38/46/48
    一致的 `tiktoken/cl100k_base` token accounting。Dense+
    SelectiveContext-lite 在 ratios `0.95/0.90/0.85/0.75` 下均保持
    `Hit@10=0.8705`，token saving 分别为 `5.66%/10.42%/15.31%/25.19%`。
    同一压缩器接到 IntentRoute evidence pools 后保持各自
    `Hit@10=0.8657-0.8777`，并将 total token saving 提高到最高约
    `30.57%`。该结果支持把 prompt compression 写成强 downstream baseline，
    不是 IntentRoute 要替代的对象；正确主张是 IntentRoute 作为上游
    route-and-budget controller 可与 prompt compression 叠加。
29. downstream answer-level evaluation：Task63 已完成，详见
    `paper/experiments/task63_downstream_llm_evaluation_summary.md`。冻结 300
    个 queries，覆盖 7 种方法、2,100 个 answers 和 2,100 个有效 judgments。
    三组 matched comparisons 的 token-saving intervals 均为正，correctness
    delta intervals 均包含 0，因此支持“更低 context 下未检测到正确率变化”，
    不支持显著 answer-quality improvement。
30. manuscript claim reframe：Task64 已完成，详见
    `paper/experiments/task64_manuscript_claim_reframe_summary.md`。论文主线已
    调整为 confidence-gated route control 与 independent budget calibration，
    同时保留 geometry/manifold 的启发与诊断作用，以及 LinUCB/feedback 的
    自适应置信度和恢复作用。
31. table and figure refresh：Task65 已完成，详见
    `paper/experiments/task65_table_figure_refresh_summary.md`。正文结果展示已
    收敛为 5 张主表和 3 幅主图，完整 cross-domain、recovery、compressor、
    reranker 和 control 明细保留于附录；ACL-style 工作 PDF 从 30 页降至
    28 页且 PDF audit 通过。Task65.3-65.5 新增防御证据后，当前工作 PDF
    为 30 页且 critical warnings 仍为 0。
32. safe-compression attribution：Task65.1 已完成，详见
    `paper/experiments/task65_1_safe_compression_attribution_summary.md`。该项
    精确复现 Task37 100k 配置并导出逐 query trace，在固定上游排序下比较
    learned confidence、geometry similarity、shuffled/random selector 与
    budget-only。结果未证明 confidence 或 geometry 能优于随机信号预测逐
    query 安全压缩；当前较强 `6-18%` frontier 应归因于 confidence-gated
    evidence pool 与独立校准长度预算的组合。该结果收紧机制归因，但不否定
    geometry/LinUCB 在 route-control 和 dense fallback 决策中的作用。
33. factorial safe-compression attribution：Task65.2 已完成，详见
    `paper/experiments/task65_2_factorial_safe_compression_summary.md`。该项在
    完全固定的 dense top-10 candidate pool、Task38 split、budget grid 和
    seeds 下，完成 geometry/random-partition × feedback/no-feedback 2×2
    对照并加入 dense budget-only。结果显示 geometry 对 route reward 的作用
    明显，但 geometry+feedback 相比 random-partition+feedback 在约 `10%`
    saving 下仅有 `+0.08pp` Hit 差，三个 seed 的 paired bootstrap CI 均跨
    0；固定动作 AUROC 也未显示 geometry/feedback 的稳定安全压缩识别优势。
34. dynamic-route mediation：Task65.3 已完成，详见
    `paper/experiments/task65_3_dynamic_route_mediation_summary.md`。该项冻结
    Task37 的 selected arms、feedback state 与 confidence trajectory，并在相同
    candidate components 和 `r0.95/m4` budget 下回放 dynamic gating、fixed
    full fusion、always cluster-primary、shuffled tiers 和 dense。原始
    query-to-tier assignment 相比保持 tier 频率不变的 shuffled control，在预算
    前后均高 `+4.80pp` Hit@10，三个 seed 的 paired bootstrap CI 均不跨 0；
    相比 always cluster-primary，预算后高 `+10.79pp`。但 fixed full fusion
    仍高 `+0.40pp`，且 route confidence 与 oracle safe-token headroom 的平均
    Spearman 仅 `-0.056`。因此结果支持 confidence 用于 query-specific route
    shape 和 fallback，不支持把它解释为逐 query 压缩安全分数。
35. independently calibrated matched frontier：Task65.4 已完成，详见
    `paper/experiments/task65_4_matched_frontier_summary.md`。该项在原 100k
    calibration/test split 上给 Dense 与 IntentRoute 相同的 fine budget grid，
    但允许各自独立选动作。零 observed-drop gate 下，IntentRoute 选择
    `r0.95/m4`，frozen-test mean Hit delta `0.00pp` 且 saving `6.18%`；Dense
    只能选择 `r1.00/m4`、saving `0%`。但 IntentRoute strict NI 仍为 `0/3`。
    held-out same-saving interpolation 在 5%-20% saving 上仅显示
    `+0.47pp` 到 `-0.01pp` 的小差异，因此支持 conservative operating point，
    不支持 universal Pareto dominance。
36. calibration-split sensitivity：Task65.5 已完成，详见
    `paper/experiments/task65_5_calibration_split_sensitivity_summary.md`。该项
    复用四个规模的 frozen rankings，在每个规模上运行 20 个 deterministic
    30/70 partitions。200k/638k 的 selected-policy test Hit 在 20/20 splits
    均保持 dense `-1pp` 以内；100k 为 14/20，400k 为 17/20。该结果强化
    200k/638k，要求 100k 标注 split sensitivity，并继续把 400k 保留为
    diagnostic。overlapping splits 不作为新增 training seeds 或独立重复。
37. cross-scale cross-fitted calibration：Task65.6 已完成，详见
    `paper/experiments/task65_6_cross_scale_cross_fitted_calibration_summary.md`。
    四档规模使用相同 canonical query folds、Task38 budget grid、zero-drop gate、
    seeds 和 Dense fallback。400k 在 5/5 folds 均选择合格压缩策略，OOF mean
    Hit delta 约 `0.00pp`、saving `14.50%`；但五折选择五种策略且 strict NI
    仍为 `0/3`。该结果完成 400k follow-up，但不覆盖原始 split failure，也不
    支持 split-invariant guarantee。
38. multi-judge downstream robustness：Task65.7 已完成，详见
    `paper/experiments/task65_7_multi_judge_analysis_summary.md`。该项复用
    Task63 固定的 2,100 个 answers，不重新生成答案；DeepSeek/GLM-5.2
    各完成 2,100 条判断，MiniMax-M3 完成 2,072 条；原缺失项经同协议重试后
    仍有 28 条因 provider-side content filtering 缺失且不插补。三 judge 共同
    2,072 条上的 correctness raw agreement 为 89.86%-92.18%，Cohen's kappa
    为 0.504-0.656。所有
    individual-judge 和 majority correctness comparisons 均不显著，但
    majority-vote faithfulness 对 BGE 为显著负向；SentMMR composition 的
    正向点估计未达到 `p<0.05`。因此只支持 bounded correctness robustness，不支持 uniform
    faithfulness preservation 或 strict answer-level non-inferiority。
39. Elsevier/IP&M submission conversion：Task66 已完成，详见
    `paper/journal_submission/task66_elsevier_ipm_conversion_summary.md`。当前
    IP&M 官方指南指向 Elsevier CAS single-column 模板，因此旧 `elsarticle`
    计划已替换为 `cas-sc` double-blind 投稿包。匿名稿与独立标题页均可编译，
    摘要现为 218 词，33 张表和 3 张图全部具有正文交叉引用；作者、机构、CRediT、
    funding、competing interest 和公开数据/代码链接仍需人类作者提交前填写。
40. final submission validation：Task67 已完成，详见
    `paper/journal_submission/task67_submission_readiness_report.md`。主稿与
    supplementary material 已拆分，921 项 artifact checks、139 项
    source/display checks、5 张主表、2 份绘图数据以及补充材料 446 个数值均通过
    provenance 校验；Figure 1 和本地字体环境仍是 artwork 阶段事项。
41. multi-dataset narrative alignment：Task68 已完成，详见
    `paper/experiments/task68_multi_dataset_narrative_alignment_summary.md`。
    Abstract、Introduction、Experimental Setup、Results、Discussion、
    Limitations 和 Conclusion 现在显式覆盖六个垂类评估场景，并区分 LoTTE
    full-stack/cross-domain、PubMedQA/Banking77 mechanism-transfer 与
    eManual/CUAD boundary evidence，避免把不同任务的指标合并为一个结果。
42. cross-dataset experimental consistency：Task69.1-69.2 已完成，详见
    `paper/experiments/task69_cross_dataset_consistency_plan.md`。该任务冻结了
    evidence-retrieval 最小公共协议，并生成 dataset/protocol inventory、
    evidence coverage matrix、current-result snapshot 与 missing-batch 清单。
    当前 LoTTE technology/search 是可直接复用、无需重跑的完整 full-stack
    anchor；science/search 100k/200k、PubMedQA 与去重 eManual 已有完整统一
    协议行。science/search 400k 已补齐 matched retrieval、feedback control 与
    五折 OOF budget，但仅 `1/5` fold 通过预算资格门槛，因此作为明确的规模
    boundary，而非强 token-saving 证据。Banking77 与 CUAD 分别保持
    mechanism-only 和 boundary-only，不参与跨数据集 pooled conclusion。
43. LoTTE science/search common-protocol checkpoints：Task69.3 的 100k、200k
    与 400k core endpoint 均已完成，详见
    `paper/experiments/task69_3_science_100k_checkpoint_summary.md`、
    `paper/experiments/task69_3_science_200k_checkpoint_summary.md` 和
    `paper/experiments/task69_3_science_400k_checkpoint_summary.md`。400k OOF
    Hit@10 delta 为 `-0.67pp`、final-context saving 为 `3.15%`、strict NI 为
    `0/3`，仅支持一个保守的规模边界结论；在该 checkpoint 时尚未启动的
    新增 LoTTE domains 已由后续第 44 项完成。
44. LoTTE domain expansion and submission integration：Tasks73-78 已完成。
    recreation/search 与 writing/search 增加了预先指定的 100k 跨域证据；随后
    完成论文整合、文本压缩、Occam display revision、跨设备复现与 GPU
    revalidation。它们保留异质 frontier 和负向边界，不形成 pooled effect。
45. learned-compressor evaluation and final reconciliation：Tasks79-80 已完成。
    official LLMLingua-2 matched-compressor 实验在 300 个 frozen queries 上完成
    1,200 个 endpoint-answer records 与 3,600/3,600 judgments；Task80 对当前
    evidence surface、生成稿、ACL/CAS PDF、匿名性和历史状态文件完成统一对账，
    最终控制审计 20/20 通过。剩余工作仅见
    `task80_remaining_work_checklist.md`。
46. Figure 2 paired trade-off redesign：Task80.1 已完成，详见
    `paper/experiments/task80_1_figure2_pareto_redesign_summary.md`。原有六行
    实验数据未变；图形改为 Dense adaptive truncation 到 IntentRoute 的配对箭头，
    在同一坐标系展示 final evidence-context token saving 与 Hit@10 delta，并保留
    technology/search 400k 空心诊断点及非普遍 Pareto dominance 边界。
47. citation and Figure 3 layout revision：Task80.2 已完成，详见
    `paper/experiments/task80_2_citation_and_figure3_layout_summary.md`。CAS 正文和
    supplementary 的首次多作者引用改为紧凑 `et al.` 形式；Figure 3 的 Panel A/B
    图例移出数据区，Panel C 使用末端直标。原始 CSV、实验数值、表格加粗、公式对齐
    和 caption 位置均未改变。
48. citation provenance audit：Task80.3 已完成，详见
    `paper/experiments/task80_3_citation_provenance_audit_summary.md`。Introduction、
    Method 与 Experimental Setup 已在外部数据集、算法、encoder、baseline 和统计
    方法首次出现处补充原始或规范来源；BibTeX 从 32 项扩展到 50 项，当前引用键与
    条目为 `50/50`，无未引用条目或未解析引用。Results、Discussion 与 Conclusion
    仍以本研究 artifact 为依据，没有为追求章节分布而机械增加引用。

最低完成集 1-4 已完成；第 5 项强加分项、第 6 项稳定性补强项、第 7 项写作前
一致性审计、第 8 项 review 防御修订、第 9 项 Task37 优化、第 10 项 Task38
calibration/test 防御、第 11 项 Task39 science/search 跨域复现 20k/q200
和 100k checkpoints、第 12 项 Task40 feedback-driven hard-case recovery、
第 13 项 Task46 Dense+Sentence-MMR same-budget baseline，以及第 14 项 Task48
compressor-normalized comparison、第 15 项 Task47 cross-encoder reranker
same-budget baseline、第 16 项 Task49 strong-baseline-aware manuscript
reframing、第 17 项 Task51 experiment validation framework、第 18 项 Task52
strong embedding dense baseline、第 19 项 Task53 embedding backbone
generalization、第 20 项 Task54 positive-hit trade-off tuning、第 21 项
Task55 backbone stability summary、第 22 项 Task56 claim-evidence alignment
和第 23 项 Task57 review response action map、第 24 项 Task58 geometry
random ablation、第 25 项 Task59 feedback-control ablation、第 26 项
Task60 arm-count sensitivity、第 27 项 Task61 geometry-to-control analysis
和第 28 项 Task62 prompt-compression baseline、第 29 项 Task63 downstream
answer-level evaluation、第 30 项 Task64 manuscript claim reframe 及第 31 项
Task65 table and figure refresh、第 32 项 Task65.1 safe-compression
attribution、第 33 项 Task65.2 factorial safe-compression attribution 均已完成。
第 34 项 Task65.3 dynamic-route mediation 也已完成。
第 35 项 Task65.4 independently calibrated matched frontier 和第 36 项
Task65.5 calibration-split sensitivity、第 37 项 Task65.6 cross-scale
cross-fitted calibration、第 38 项 Task65.7 multi-judge downstream
robustness 也已完成。
第 39 项 Task66 Elsevier/IP&M submission conversion 也已完成。
第 40 项 Task67 final submission validation 与第 41 项 Task68 multi-dataset
narrative alignment 也已完成。第 42 项 Task69 已完成 69.1-69.6：science/search
100k/200k/400k、非 LoTTE common-protocol rows、机制/边界表和论文整合均已
闭环。science/search 400k 是明确的弱规模边界，新增 LoTTE domains 和 native
science full 属于 post-Task69 的假设驱动扩展，不是当前任务缺失项。

---

## 注意事项
## Notes

1. **BioASQ** 完整数据需要在 [bioasq.org](http://www.bioasq.org/) 注册下载。脚本会先尝试 HuggingFace 子集。
2. **PubMedQA artificial** 子集约 211K 条，下载和处理需要几分钟，默认不包含。
3. 所有 data/ 下的数据文件已在 `.gitignore` 中排除，不会提交到 git。
4. 预处理脚本会打印统计信息（chunks 数、queries 数、GT 覆盖率），请检查是否合理。
5. Task 10 表格已基于 guarded results 生成；CUAD 仅进入 smoke/sample 表，不进入 full-corpus evidence 主表。

---

*创建时间: 2026-04-21*
*更新时间: 2026-07-21*
