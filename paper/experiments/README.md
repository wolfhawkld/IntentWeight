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
│   ├── preprocess_lotte.py        # LoTTE domain-search 预处理
│   ├── validate_processed.py      # 统一 processed 数据校验
│   ├── retrieval_metrics.py       # Recall/MRR/nDCG 评估
│   ├── embedding_cache.py         # reusable dense embedding cache
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

# LoTTE 小样本 / large-scale 垂类检索验证：
.venv/bin/python paper/experiments/scripts/preprocess_lotte.py \
  --domain technology --mode search --split test \
  --max-queries 20 --max-corpus 5000
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
100k distractors plus GT anchors) also passed the processed-data guardrail:

| Dataset | Corpus | Queries | GT refs | BM25 R@10 | Dense R@10 | LinUCB full R@10 | LinUCB gated R@10 | Gated cost reduction |
|---------|--------|---------|---------|-----------|------------|------------------|-------------------|----------------------|
| LoTTE technology/search 100k | 101311 | 596 | 2045 | 0.7232 | 0.8674 | 0.8725 | 0.8356 | 25.28% |

The 100k dense baseline took `1640.076s` on CPU exact cosine. The cost-aware
LinUCB smoke took `1772.420s` for full route and `1905.491s` for gated route
before embedding cache was added, because the old scripts repeated embedding
work across runs. Task 17 should now reuse the embedding cache before scaling to
more seeds, epochs, or full 638k corpus; a shared large-scale runner remains a
separate next step for avoiding repeated BM25 index and clustering work.

Current status as of 2026-05-06:

- LoTTE 100k corpus/query embedding cache has been generated locally under
  `paper/experiments/data/embeddings/` and is ignored by git.
- Cached shapes: corpus `[101311, 384]`, queries `[596, 384]`.
- Cache sizes: corpus `149M`, queries `896K`.
- First cache generation took `1598.231s`; second cache-hit validation took
  `0.204s` with `corpus_hit=true` and `query_hit=true`.
- LoTTE 100k BM25 and dense baselines are available, plus a cost-aware LinUCB
  smoke. The 100k hybrid baseline is not yet run, so the 100k
  BM25/dense/hybrid comparison group is still marked not comparable.
- Large-scale LoTTE manifold geometry diagnostics have not yet been run. The
  next Task 17 step is to reuse the embedding cache for large-scale manifold
  diagnostics before expanding seeds, epochs, or the full 638k corpus.

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
| LoTTE | evidence retrieval | Task 17 large-scale 主候选 | 垂类 domain-search，适合验证大规模质量-成本 trade-off |

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
*更新时间: 2026-05-06*
