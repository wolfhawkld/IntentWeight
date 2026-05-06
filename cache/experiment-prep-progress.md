# IntentWeight 本机实验准备进度

创建时间: 2026-04-27
维护者: Damon + Nemesis

## 背景

根据最新提交 `c5fdb56 docs: 新增流形局部反馈机制与 FAISS/HNSW 引擎设计`，当前研究方向从“全局 LinUCB 反馈更新”扩展到“流形局部反馈”：

- 历史反馈按 query/cluster 在流形上的距离加权
- 单个 cluster 的反馈可按距离衰减传播到邻近 cluster
- 多轮对话内，用 query embedding 距离做反馈 attention
- 用户信誉从全局信誉扩展到局部/领域信誉
- FAISS/HNSW 作为 CPU-only 的实时流形近似引擎

但当前代码仍主要是全局 LinUCB：`intent_weight/linucb.py` 中 `update()` 只更新当前 arm 的 A/b，最新提交尚未落成代码。

## 当前本机状态摘要

仓库路径:

```bash
/home/damon/.openclaw/workspace/IntentWeight
```

当前分支:

```bash
pre_validation
```

虚拟环境:

```bash
.venv 存在
venv 不存在
```

所以实际激活命令应为：

```bash
source .venv/bin/activate
```

本机硬件：

- CPU: 16 cores
- Memory: 6.2 GiB
- Disk: 约 915 GiB free
- GPU: `nvidia-smi` 不可用

适合本机做：

- 数据下载/预处理
- BM25 baseline
- 小规模 dense embedding
- Hybrid 检索
- LinUCB 在线学习模拟
- FAISS/HNSW CPU 版流形局部反馈实验
- 小规模 RAGAS / LLM-as-Judge 抽样评估

不适合本机做：

- DynamicRAG 的 Llama3-8B SFT/DPO
- FLAIR 大模型本地 HyQE 推理
- 大规模 BGE-large 全量 embedding 高速生成
- 全量 RAGAS 大规模 LLM judge

## 当前依赖状态

`.venv` 中已有：

- datasets
- pandas
- pyarrow
- sentence_transformers
- sklearn
- hdbscan
- numpy

缺失：

- loguru
- rank_bm25
- faiss-cpu / faiss
- hnswlib
- ragas

当前 `import intent_weight.linucb` 会因为缺 `loguru` 失败。

## 当前数据状态

`paper/experiments/data/raw/` 中已有：

- `banking77_train.parquet`
- `banking77_test.parquet`
- `cuad.parquet`
- `emanual_train.parquet`
- `emanual_test.parquet`
- `emanual_validation.parquet`
- `pubmedqa_labeled.parquet`
- `pubmedqa_artificial.parquet`（损坏，不完整）
- `pubmedqa_labeled/` datasets save_to_disk 格式
- `emanual/` datasets save_to_disk 格式
- `banking77 -> pre_validation/data/banking77` symlink

已验证：

- PubMedQA labeled 可读，可预处理
- Banking77 可预处理
- eManual 当前预处理脚本输出无效：`Corpus chunks: 0`, `Queries: 1318 (with GT: 0)`
- CUAD 当前 `preprocess_cuad.py` 失败，因为它期待 `raw/cuad/` datasets 目录，但当前只有 `cuad.parquet`
- `pubmedqa_artificial.parquet` 当前约 5 MB，但 HF 实际文件约 233 MB，读取时报 Parquet footer 错误，必须续传/重下

## 分阶段任务

### Task 1: 修复 `download_parquet.py`

目标：让 HuggingFace Parquet 下载脚本可断点续传、可校验、不会把损坏文件误判为“已存在”。

文件：

- 修改：`paper/experiments/scripts/download_parquet.py`
- 新增测试：`cache/test_download_parquet.py`

必须完成：

- `curl` 命令加入 `-C -` 断点续传
- `curl` 命令加入 `-f`，HTTP 错误时失败
- 已存在文件必须先 `verify_parquet()`；校验失败时不能跳过，必须重新下载/续传
- 下载后再次校验，校验失败记为失败
- 保持原有 CLI 用法不变：`python paper/experiments/scripts/download_parquet.py`

验证：

```bash
cd ~/.openclaw/workspace/IntentWeight
source .venv/bin/activate
python cache/test_download_parquet.py
python paper/experiments/scripts/download_parquet.py
```

### Task 2: 新增/修复 RAGBench 预处理

目标：统一处理 eManual 和 RAGBench CUAD parquet/save_to_disk 数据。

建议新增：

- `paper/experiments/scripts/preprocess_ragbench.py`

支持：

```bash
python paper/experiments/scripts/preprocess_ragbench.py --dataset emanual
python paper/experiments/scripts/preprocess_ragbench.py --dataset cuad
```

核心逻辑：

- 读取 `documents_sentences`
- 每个 sentence 作为一个 chunk
- `all_relevant_sentence_keys` 映射为 `ground_truth_chunk_ids`
- 输出统一格式 corpus/queries JSON

### Task 3: 新增 processed 数据验证脚本

建议新增：

- `paper/experiments/scripts/validate_processed.py`

检查：

- corpus/query 文件存在
- chunks > 0
- queries > 0
- GT 覆盖率合理
- 所有 `ground_truth_chunk_ids` 都存在于 corpus
- 输出 summary

### Task 4: 更新依赖

修改：

- `requirements.txt`

增加：

```text
loguru>=0.7.0
rank-bm25>=0.2.2
faiss-cpu>=1.8.0
hnswlib>=0.8.0
ragas>=0.2.0
```

并验证：

```bash
python - <<'PY'
import loguru, faiss, rank_bm25
import intent_weight.linucb
print('env ok')
PY
```

### Task 5: 跑数据生成验证

目标：得到至少以下可用 processed 数据：

- PubMedQA labeled
- Banking77
- eManual
- CUAD RAGBench

然后再进入 retrieval baseline / LinUCB 实验。

## 当前执行进度

- [x] 已完成初步分析
- [x] Task 1: 修复 `download_parquet.py`
- [x] Task 2: 新增/修复 RAGBench 预处理
- [x] Task 3: 新增 processed 数据验证脚本
- [x] Task 4: 更新依赖
- [x] Task 5: 跑数据生成验证
- [x] Task 6: 实现 retrieval metrics
- [x] Task 7: 实现 BM25 retrieval baseline
- [x] Task 8: 实现 dense embedding retrieval baseline
- [x] Task 9: 实现 hybrid BM25 + dense retrieval baseline
- [x] Task 9.5: 修正实验协议与评估口径 guardrails
- [x] Task 10: 汇总 BM25 / dense / hybrid baseline 对比表
- [x] Task 11: 设计并运行 LinUCB baseline / ablation 实验
- [x] Task 12: 实现流形局部反馈机制（CPU exact 邻域检索 + 距离加权反馈）
- [x] Task 13: 对比全局 LinUCB 与流形局部反馈效果
- [x] Task 14: 流形假设诊断与 eManual 失败定位
- [x] Task 15: Trust-weighted feedback LinUCB
- [x] Task 16: Cost-aware soft routing
- [x] Task 17: LoTTE large-scale pre-validation / 100k stage-1 smoke
- [x] Task 17.1: LoTTE 100k hybrid baseline with embedding cache
- [x] Task 17.2: LoTTE 100k manifold geometry diagnostics
- [x] Task 17.3: LoTTE 100k cached cost-aware LinUCB rerun
- [x] Task 17.4: Shared large-scale retrieval artifacts
- [x] Task 17.5: Shared artifact cache 接入 dense_baseline / hybrid_baseline / manifold_diagnostics

## 后续任务规划

### Task 9: Hybrid BM25 + Dense retrieval baseline

状态：已完成。

目标：融合 Task 7 的 BM25 lexical signal 和 Task 8 的 dense semantic signal，形成第三个 retrieval baseline。

建议优先方案：Reciprocal Rank Fusion (RRF)。

原因：

- 不需要校准 BM25 分数和 dense cosine 分数尺度；
- 实现简单、稳定、可复现；
- 适合作为 hybrid baseline 的第一版。

预计新增：

- `cache/test_hybrid_baseline.py`
- `paper/experiments/scripts/hybrid_baseline.py`
- `paper/experiments/results/hybrid_baseline_summary.csv`
- `paper/experiments/results/hybrid_{dataset}_metrics.json`
- `paper/experiments/results/hybrid_{dataset}_rankings.json`

预计运行：

- PubMedQA full
- Banking77 full
- eManual full
- CUAD sample/smoke（沿用 BM25/dense 的抽样约束，避免 CPU 全量超时）

### Task 9.5: 实验协议与评估口径修正

状态：已完成。

目标：在 Task 10 汇总表之前，先修正静态检索实验的论文口径，避免把不可比较结果放进同一主表，也为 Task 11-13 的在线学习实验预先规定无泄漏协议。

必须完成：

1. RAGBench split 口径：
   - eManual/CUAD 当前 processed queries 混合 train/validation/test。
   - baseline 评估和 summary 必须显式记录 `query_split`。
   - 正式主表优先使用 held-out `test` query；train/validation 可用于调参、反馈流或 smoke。
2. CUAD sample/corpus 口径：
   - BM25/dense/hybrid 在同一 comparison group 中必须使用相同 query subset 和 corpus subset。
   - 当前 CUAD 结果只能标为 smoke/sample，不得默默放进主表排名。
3. Dataset task type：
   - PubMedQA/eManual/CUAD 归为 evidence retrieval。
   - Banking77 归为 intent retrieval proxy/domain routing。
   - Task 10 表格必须带 `task_type`，论文结论不得把 Banking77 当作普通 evidence retrieval。
4. Dense baseline 命名：
   - 当前已跑结果使用 `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine。
   - 文档和表格不得称为 BGE-large；如需 BGE/GTE，后续另跑正式结果。
5. Comparison guardrails：
   - Task 10 汇总器必须写出 `scope`、`query_split`、`corpus_scope`、`comparable_group`、`is_comparable`、`notes`。
   - 同 dataset/method group 下 query/corpus/sample/model 口径不一致时，自动标为 `not_comparable` 或 `smoke_only`。
6. PubMedQA GT caveat：
   - 当前 PubMedQA GT 是 abstract context section-level，Recall 表示命中该问题对应论文摘要任一 context section。
   - 不得表述为严格 answer-supporting sentence/evidence recall。
7. 在线学习协议：
   - Task 11-13 必须先选择并记录 prequential 或 train-feedback/test-eval 协议。
   - 若用 prequential：每条 query 必须先评估再用反馈更新。
   - 若用 train-feedback/test-eval：反馈流只来自 train/validation，最终报告只用 held-out test。
   - 多随机种子时报告 mean/std。
8. Scientific tests：
   - 新增测试覆盖 split filtering、sample consistency、comparison guardrails、scope/notes 标注。
   - 保留现有 ranking/metrics 工程测试，但不能把它们等同于实验有效性验证。

建议实现顺序：

1. 更新实验 README 和本进度文档，固定协议。
2. 给 baseline 脚本或汇总脚本增加 split/sample metadata guardrails。已完成。
3. 重新生成或重新标注 retrieval baseline comparison 数据。已完成。
4. 再进入 Task 10 主表汇总。

### Task 10: Baseline 对比汇总表

状态：已完成。

目标：把 BM25、dense、hybrid 的结果统一成论文可用的表格。

已输出：

- `paper/experiments/results/retrieval_baseline_comparison.csv`
- `paper/experiments/results/retrieval_baseline_main_table.csv`
- `paper/experiments/results/retrieval_baseline_intent_proxy_table.csv`
- `paper/experiments/results/retrieval_baseline_smoke_table.csv`
- `paper/experiments/results/retrieval_baseline_tables.md`

实现：

- 新增 `paper/experiments/scripts/summarize_retrieval_baselines.py`。
- 从 guarded `retrieval_baseline_comparison.csv` 生成论文表格。
- Evidence retrieval 主表只纳入 `task_type=evidence_retrieval`、`is_comparable=true`、`scope in {full, heldout_test}`、`corpus_scope=full` 的结果。
- Banking77 单独进入 intent/domain routing proxy 表。
- CUAD 单独进入 smoke/sample 表，不进入 evidence full-corpus 主表。

表格应至少包含：

- dataset
- method
- task_type
- scope/full-or-sample
- query_split
- corpus_scope
- comparable_group
- is_comparable
- num_corpus_chunks
- evaluated_queries
- skipped_no_gt
- Recall@1/5/10
- MRR@10
- nDCG@10
- elapsed_sec
- notes，例如 CUAD sample 限制。

当前 Task 10 表格摘要：

- Evidence retrieval main table: 6 rows
  - PubMedQA full/train/full corpus: BM25, dense, hybrid
  - eManual heldout_test/test/full corpus: BM25, dense, hybrid
- Intent proxy table: 3 rows
  - Banking77 heldout_test/test/full corpus: BM25, dense, hybrid
- Smoke/sample table: 3 rows
  - CUAD smoke_only/test/first_10000: BM25, dense, hybrid
- 已运行验证：
  - `.venv/bin/python -m unittest cache/test_summarize_retrieval_baselines.py cache/test_experiment_guardrails.py cache/test_bm25_baseline.py cache/test_dense_baseline.py cache/test_hybrid_baseline.py cache/test_retrieval_metrics.py`，26 tests 通过。
  - `.venv/bin/python -m py_compile paper/experiments/scripts/summarize_retrieval_baselines.py paper/experiments/scripts/experiment_guardrails.py paper/experiments/scripts/bm25_baseline.py paper/experiments/scripts/dense_baseline.py paper/experiments/scripts/hybrid_baseline.py cache/test_summarize_retrieval_baselines.py cache/test_experiment_guardrails.py cache/test_bm25_baseline.py`，通过。

### Task 11: LinUCB baseline / ablation 实验

状态：已启动。

目标：在已有 retrieval baseline 基础上，验证当前代码中的全局 LinUCB 反馈策略。

注意：当前 `intent_weight/linucb.py` 仍是全局 arm 更新，尚未实现最新设计文档中的流形局部反馈。

当前 Task 11 边界：

- 使用 `prequential` 无泄漏协议：每条 query 先评估，再用 GT 派生反馈更新。
- 只验证全局 LinUCB baseline：cluster arms 的全局 A/b 更新。
- 不在 Task 11 中训练 Reward Model；Reward Model 和第四信誉方案作为中期扩展记录。
- 不在 Task 11 中实现流形局部反馈、跨 arm 距离衰减传播或局部信誉；这些属于 Task 12。

已实现：

- 新增 `paper/experiments/scripts/linucb_online_baseline.py`
  - corpus embedding 聚类得到 arms；
  - PCA context features；
  - 全局 LinUCB 使用探索衰减 `alpha / (1 + alpha_decay * total_feedback)`；
  - 每个 seed 使用随机 query stream，报告 mean/std；
  - 输出 `linucb_{dataset}_prequential_metrics.json`、`linucb_{dataset}_prequential_rankings.json`、`linucb_online_summary.csv`。
- 新增 `cache/test_linucb_online_baseline.py`，覆盖 selected-arm retrieval、prequential update、seed aggregation、output files。

已完成 smoke：

```bash
.venv/bin/python paper/experiments/scripts/linucb_online_baseline.py \
  --dataset pubmedqa \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --local-files-only --device cpu --batch-size 64 \
  --top-k 10 --ks 1,5,10 \
  --max-queries 50 --max-corpus 500 \
  --seeds 13,17 --n-clusters 8 --context-dim 16 --candidate-arms 3
```

Smoke result:

- PubMedQA sample: evaluated_queries=50, skipped_no_gt=0
- recall@10_mean=0.8200, recall@10_std=0.0600
- mrr@10_mean=0.7096, mrr@10_std=0.0729
- final_effective_alpha_mean=0.4000

已完成正式 Task 11 baseline matrix：

- PubMedQA full/train/full corpus:
  - evaluated_queries=1000, skipped_no_gt=0, seeds=3
  - recall@10_mean=0.5480, recall@10_std=0.0159
  - mrr@10_mean=0.4637, mrr@10_std=0.0186
- eManual heldout_test/test/full corpus:
  - evaluated_queries=130, skipped_no_gt=2, seeds=3
  - recall@10_mean=0.1154, recall@10_std=0.0326
  - mrr@10_mean=0.0182, mrr@10_std=0.0042
- Banking77 intent proxy heldout_test/test/full corpus:
  - evaluated_queries=3080, skipped_no_gt=0, seeds=3
  - recall@10_mean=0.7215, recall@10_std=0.0087
  - mrr@10_mean=0.6094, mrr@10_std=0.0093
- CUAD smoke_only/test/first_10000:
  - evaluated_queries=79, skipped_no_gt=21, seeds=3
  - recall@10_mean=0.0000, mrr@10_mean=0.0000

已生成 Task 11 表格：

- `paper/experiments/results/linucb_online_main_table.csv`
- `paper/experiments/results/linucb_online_intent_proxy_table.csv`
- `paper/experiments/results/linucb_online_smoke_table.csv`
- `paper/experiments/results/linucb_online_tables.md`

已完成初步 ablation（PubMedQA sample: max_queries=200, max_corpus=1000, seeds=13/17/19, n_clusters=16, context_dim=32）：

| Variant | Recall@10 mean | MRR@10 mean | 观察 |
|---------|----------------|-------------|------|
| default: alpha_decay=0.01, candidate_arms=3 | 0.5450 | 0.4690 | 参考配置 |
| alpha_decay=0.0, candidate_arms=3 | 0.6550 | 0.5615 | 好于默认，当前衰减可能过早 exploitation |
| alpha_decay=0.01, candidate_arms=1 | 0.2433 | 0.2060 | 过窄，容易错过正确 cluster |
| alpha_decay=0.01, candidate_arms=5 | 0.8150 | 0.6984 | sample 中最好，candidate breadth 是关键超参 |

已生成 ablation 表格：

- `paper/experiments/results/linucb_ablations/linucb_ablation_summary.csv`
- `paper/experiments/results/linucb_ablations/linucb_ablation_summary.md`

当前观察：

- 全局 LinUCB 在 PubMedQA full 上低于 Task 10 的 dense/hybrid 静态检索结果。
- eManual held-out 上全局 LinUCB Recall@10 与 BM25 持平，但低于 dense。
- 这说明简单全局 cluster-arm 更新不足以稳定改进 evidence retrieval，是 Task 12 流形局部反馈的关键对照。

已验证：

- `.venv/bin/python -m unittest cache/test_linucb_online_baseline.py cache/test_summarize_retrieval_baselines.py cache/test_experiment_guardrails.py cache/test_retrieval_metrics.py`，13 tests 通过。
- `.venv/bin/python -m py_compile paper/experiments/scripts/linucb_online_baseline.py cache/test_linucb_online_baseline.py`，通过。

下一步：

- 如需正式论文级 ablation，扩展当前 sample ablation 到 eManual held-out 和 PubMedQA full。
- 补充 random/no-learning cluster selection 与 context_dim ablation。
- 决定 Task 12 的局部流形反馈是否沿用同一 prequential 协议和数据口径。

### Task 12: 流形局部反馈实现

目标：根据 `paper/feedback-simulation.md` 实现局部反馈机制。

核心方向：

- 使用 CPU exact numpy 邻域检索作为 FAISS/HNSW-compatible 实验内核；
- 历史反馈按 query embedding/PCA context 距离加权；
- 单 cluster 反馈向邻近 cluster 衰减传播；
- 多轮/序列内按 query embedding 距离做 feedback attention；
- 用户信誉从全局扩展到局部/领域信誉（保留为后续 Task 13/14 或真实用户反馈扩展，不进入当前 GT 模拟闭环）。

已完成：

- 新增 `paper/experiments/scripts/linucb_manifold_local.py`：
  - 复用 Task 11 的 prequential 协议、SentenceTransformer embedding、PCA context、MiniBatchKMeans cluster arms、dense intra-arm retrieval、GT-derived reward。
  - 新增 query-local feedback attention：当前 query 在历史 feedback contexts 中找近邻，按 `exp(-distance / feedback_tau)` 加权，把近邻历史 reward 作为 arm score boost。
  - 新增 cross-arm feedback propagation：selected arm 收到反馈后，按 cluster centroid 距离对邻近 arms 做 `propagation_strength * exp(-distance / arm_decay_sigma)` 权重更新。
  - 输出 `linucb_manifold_{dataset}_prequential_metrics.json`、`linucb_manifold_{dataset}_prequential_rankings.json`、`linucb_manifold_summary.csv`。
  - metadata 包含 `online_learning_scope=manifold_local_feedback_propagation`、`manifold_neighbor_engine=cpu_exact_numpy`、`arm_neighbor_k`、`arm_decay_sigma`、`propagation_strength`、`feedback_k`、`feedback_tau`、`feedback_weight`、`cross_arm_update_weight_mean`、`avg_local_boost_norm_mean`。
- 新增 `paper/experiments/scripts/summarize_linucb_manifold.py`：
  - 生成 `linucb_manifold_main_table.csv`、`linucb_manifold_intent_proxy_table.csv`、`linucb_manifold_smoke_table.csv`、`linucb_manifold_tables.md`。
- 新增测试：
  - `cache/test_linucb_manifold_local.py`
  - `cache/test_summarize_linucb_manifold.py`
- 已运行正式 Task 12 矩阵：
  - PubMedQA full/train/full: recall@10_mean=0.6607, mrr@10_mean=0.5654
  - eManual heldout_test/test/full: recall@10_mean=0.0923, mrr@10_mean=0.0193
  - Banking77 heldout_test/test/full: recall@10_mean=0.8247, mrr@10_mean=0.7490
  - CUAD smoke_only/test/gt_anchored_10000: recall@10_mean=0.0295, mrr@10_mean=0.0120
- 初步对比 Task 11：
  - PubMedQA 和 Banking77 明显提升；
  - eManual 与 CUAD 没有提升，说明当前局部传播参数/假设不是无条件有效，Task 13 需要重点解释并做消融。

### Task 13: 全局 LinUCB vs 流形局部反馈对比

目标：比较旧的全局 LinUCB 和新的局部流形反馈机制。

重点关注：

- 冷启动表现；
- 小样本反馈后的提升速度；
- 不同数据集上的稳定性；
- 对 eManual / CUAD 这种困难数据集的改善幅度。

### Task 14: 论文实验整理

目标：把可用结果整理成论文实验部分素材。

包括：

- baseline 表格；
- 消融实验；
- 方法优势；
- 失败案例；
- CUAD full/sample 限制说明；
- 后续工作。

## 进度记录

### 2026-04-27

- 创建本 cache 进度文件
- Task 1 已完成：
  - 新增 `cache/test_download_parquet.py`，覆盖断点续传参数和损坏文件重下载逻辑
  - `download_file()` 的 curl 命令已加入 `-C -` 断点续传和 `-f` fail-fast
  - `main()` 现在会先校验已存在 parquet；校验失败时继续下载/续传，不再误判为“已存在”
  - 已运行 `python cache/test_download_parquet.py`，2 个测试通过
  - 已运行 `.venv/bin/python paper/experiments/scripts/download_parquet.py`，下载/验证通过
  - `pubmedqa_artificial.parquet` 已从损坏的约 4.79 MB 续传到 222.60 MB，验证为 211269 行、5 列
  - RAGBench CUAD parquet 已下载：train 1530 行、test 510 行、validation 510 行
- Task 2 已完成：
  - 新增 `cache/test_preprocess_ragbench.py`，覆盖 RAGBench sentence-level chunk 生成、relevant sentence key 到 `ground_truth_chunk_ids` 映射、query/corpus 元数据输出
  - 新增 `paper/experiments/scripts/preprocess_ragbench.py`，支持：
    - `.venv/bin/python paper/experiments/scripts/preprocess_ragbench.py --dataset emanual`
    - `.venv/bin/python paper/experiments/scripts/preprocess_ragbench.py --dataset cuad`
  - 已运行 `.venv/bin/python cache/test_preprocess_ragbench.py`，1 个测试通过
  - 已运行实际预处理：
    - eManual: corpus chunks 18812, queries 1318, queries with GT 1298
    - CUAD: corpus chunks 675400, queries 2550, queries with GT 2056
  - 已验证 processed 输出：
    - eManual: `missing_gt_chunk_refs=0`
    - CUAD: `missing_gt_chunk_refs=0`
  - 已回归运行 `.venv/bin/python cache/test_download_parquet.py` 和 `.venv/bin/python cache/test_preprocess_ragbench.py`，全部通过
- Task 3 已完成：
  - 新增 `cache/test_validate_processed.py`，覆盖有效数据与缺失 GT chunk 引用两种情况
  - 新增 `paper/experiments/scripts/validate_processed.py`，支持：
    - `.venv/bin/python paper/experiments/scripts/validate_processed.py --dataset all`
    - `.venv/bin/python paper/experiments/scripts/validate_processed.py --dataset emanual`
    - `.venv/bin/python paper/experiments/scripts/validate_processed.py --dataset pubmedqa,banking77,emanual,cuad`
  - 验证项包括：文件存在、JSON list 格式、corpus/query 非空、chunk_id 唯一、chunk/query 文本非空、所有 `ground_truth_chunk_ids` 均存在于 corpus、GT 覆盖率统计
  - 已运行 `.venv/bin/python cache/test_validate_processed.py`，2 个测试通过
  - 已运行真实 processed 数据验证：
    - banking77: corpus 10003, queries 3080, queries_with_gt 3080, GT coverage 100.00%, missing refs 0
    - cuad: corpus 675400, queries 2550, queries_with_gt 2056, GT coverage 80.63%, missing refs 0
    - emanual: corpus 18812, queries 1318, queries_with_gt 1298, GT coverage 98.48%, missing refs 0
    - pubmedqa: corpus 4348, queries 1000, queries_with_gt 1000, GT coverage 100.00%, missing refs 0
  - 已回归运行 Task 1/2/3 测试：`cache/test_download_parquet.py`、`cache/test_preprocess_ragbench.py`、`cache/test_validate_processed.py`，全部通过
- Task 4 已完成：
  - 新增 `cache/test_requirements.py`，覆盖 `requirements.txt` 必需依赖声明
  - 更新 `requirements.txt`，新增：
    - `loguru>=0.7.0`
    - `rank-bm25>=0.2.2`
    - `faiss-cpu>=1.8.0`
    - `hnswlib>=0.8.0`
    - `ragas>=0.2.0`
  - 已运行 `.venv/bin/python -m pip install -r requirements.txt`，安装成功
  - 已验证导入：`loguru`、`rank_bm25`、`faiss`、`hnswlib`、`ragas`、`intent_weight.linucb`、`intent_weight.reward` 均 OK
  - 已回归运行 Task 1/2/3/4 测试：`cache/test_download_parquet.py`、`cache/test_preprocess_ragbench.py`、`cache/test_validate_processed.py`、`cache/test_requirements.py`，全部通过
- Task 5 已完成：
  - 未重新下载 raw 数据；此前已确认核心 raw parquet 均存在且可读
  - 已重跑四个 processed 生成脚本：
    - `.venv/bin/python paper/experiments/scripts/preprocess_pubmedqa.py`
    - `.venv/bin/python paper/experiments/scripts/preprocess_banking77.py`
    - `.venv/bin/python paper/experiments/scripts/preprocess_ragbench.py --dataset emanual`
    - `.venv/bin/python paper/experiments/scripts/preprocess_ragbench.py --dataset cuad`
  - 生成结果：
    - PubMedQA labeled: corpus chunks 4348, queries 1000, queries with GT 1000
    - Banking77: corpus chunks 10003, queries 3080
    - eManual RAGBench: corpus chunks 18812, queries 1318, queries with GT 1298
    - CUAD RAGBench: corpus chunks 675400, queries 2550, queries with GT 2056
  - 已运行 `.venv/bin/python paper/experiments/scripts/validate_processed.py --dataset all`，结果 `ALL VALID`
  - 验证明细：
    - banking77: corpus 10003, queries 3080, queries_with_gt 3080, GT coverage 100.00%, missing refs 0, duplicate chunks 0
    - cuad: corpus 675400, queries 2550, queries_with_gt 2056, GT coverage 80.63%, missing refs 0, duplicate chunks 0
    - emanual: corpus 18812, queries 1318, queries_with_gt 1298, GT coverage 98.48%, missing refs 0, duplicate chunks 0
    - pubmedqa: corpus 4348, queries 1000, queries_with_gt 1000, GT coverage 100.00%, missing refs 0, duplicate chunks 0
  - 已回归运行 Task 1/2/3/4 测试：`cache/test_download_parquet.py`、`cache/test_preprocess_ragbench.py`、`cache/test_validate_processed.py`、`cache/test_requirements.py`，全部通过
  - 至此，本机实验准备阶段 Task 1-5 全部完成，可进入 retrieval baseline / LinUCB / 流形局部反馈实验阶段
- Task 6 已完成：retrieval metrics
  - 新增 `cache/test_retrieval_metrics.py`，按 TDD 先验证 RED：`paper/experiments/scripts/retrieval_metrics.py` 不存在时测试失败
  - 新增 `paper/experiments/scripts/retrieval_metrics.py`
  - 支持指标：
    - binary `Recall@k`: top-k 中任意 ground-truth chunk 命中即为 1
    - `MRR@k`: top-k 内第一个相关 chunk 的 reciprocal rank
    - `nDCG@k`: binary relevance，支持多个 ground-truth chunks
  - `evaluate_rankings()` 默认跳过无 ground-truth 的 query；这适配 CUAD/RAGBench 中存在的 no-evidence query，避免把无法检索到正例的问题算入检索 recall
  - 支持 CLI：
    - `.venv/bin/python paper/experiments/scripts/retrieval_metrics.py --queries <queries.json> --rankings <rankings.json> --ks 1,5,10`
  - 已运行 `.venv/bin/python cache/test_retrieval_metrics.py`，3 个测试通过
  - 已运行回归测试：`cache/test_download_parquet.py`、`cache/test_preprocess_ragbench.py`、`cache/test_validate_processed.py`、`cache/test_requirements.py`，全部通过
  - 已运行 `python -m py_compile paper/experiments/scripts/retrieval_metrics.py cache/test_retrieval_metrics.py`，语法检查通过
- Task 7 已完成：BM25 retrieval baseline
  - 新增 `cache/test_bm25_baseline.py`，覆盖 tokenizer、top-k 排序、稀疏 BM25 只访问匹配 postings、toy ranking/metrics、`max_queries` 抽样、CLI 输出文件。
  - 新增 `paper/experiments/scripts/bm25_baseline.py`：
    - 读取 `paper/experiments/data/processed/{dataset}_corpus.json` 和 `{dataset}_queries.json`
    - 使用确定性英文/数字 tokenizer
    - 实现 sparse inverted-index BM25，避免 `rank_bm25.get_scores()` 对 CUAD 675400 chunks 每个 query 全量扫描
    - 输出 `paper/experiments/results/bm25_{dataset}_rankings.json`、`bm25_{dataset}_metrics.json` 和 `bm25_baseline_summary.csv`
    - 支持 `--dataset`、`--top-k`、`--ks`、`--max-queries`
  - BM25 结果统计表（CUAD 为 sample/smoke，非全量）：

    | Dataset | Scope | Corpus chunks | Evaluated queries | Skipped no-GT | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Elapsed |
    | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
    | PubMedQA | full | 4348 | 1000 | 0 | 0.6910 | 0.9730 | 0.9770 | 0.8273 | 0.6648 | 3.321s |
    | Banking77 | full | 10003 | 3080 | 0 | 0.8019 | 0.9370 | 0.9698 | 0.8604 | 0.6762 | 23.559s |
    | eManual | full | 18812 | 1298 | 20 | 0.0362 | 0.1579 | 0.2820 | 0.0911 | 0.0643 | 12.131s |
    | CUAD | sample: `--max-queries 100` | 675400 | 74 | 26 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 148.687s |

  - CUAD 全量 BM25 说明：
    - CUAD corpus=675400 chunks, total queries=2550, queries_with_gt=2056
    - 纯 Python 全量 BM25 即使改为稀疏倒排，交互命令仍在 600s 超时；保留为后续后台长跑/进一步优化项。
    - 已完成可复现 smoke/sample：`.venv/bin/python paper/experiments/scripts/bm25_baseline.py --dataset cuad --top-k 10 --ks 1,5,10 --max-queries 100`
  - 已运行回归测试：`cache/test_bm25_baseline.py`、`cache/test_retrieval_metrics.py`、`cache/test_download_parquet.py`、`cache/test_preprocess_ragbench.py`、`cache/test_validate_processed.py`、`cache/test_requirements.py`，全部通过。
  - 已运行 `python -m py_compile paper/experiments/scripts/bm25_baseline.py cache/test_bm25_baseline.py`，语法检查通过。
- Task 8 已完成：dense embedding retrieval baseline
  - 新增 `cache/test_dense_baseline.py`，覆盖 embedding normalization、top-k tie 稳定排序、toy dense ranking/metrics、`max_queries`/`max_corpus` 抽样、结果文件与 summary 输出。
  - 新增 `paper/experiments/scripts/dense_baseline.py`：
    - 读取 `paper/experiments/data/processed/{dataset}_corpus.json` 和 `{dataset}_queries.json`
    - 使用 SentenceTransformer 生成 dense embeddings，并统一 L2 normalize
    - 用 exact cosine similarity (`query_embeddings @ corpus_embeddings.T`) 做 top-k retrieval
    - 输出 `paper/experiments/results/dense_{dataset}_rankings.json`、`dense_{dataset}_metrics.json` 和 `dense_baseline_summary.csv`
    - 支持 `--dataset`、`--model`、`--local-files-only`、`--device`、`--batch-size`、`--top-k`、`--ks`、`--max-queries`、`--max-corpus`
  - 使用本地缓存模型：`sentence-transformers/all-MiniLM-L6-v2`，`--local-files-only --device cpu`。
  - 全量已完成数据集 dense 结果：
    - PubMedQA: chunks=4348, queries=1000, skipped_no_gt=0, elapsed=53.697s, recall@1=0.7090, recall@5=0.9870, recall@10=0.9930, mrr@10=0.8468, ndcg@10=0.7396
    - Banking77: chunks=10003, queries=3080, skipped_no_gt=0, elapsed=31.568s, recall@1=0.9205, recall@5=0.9701, recall@10=0.9805, mrr@10=0.9416, ndcg@10=0.8797
    - eManual: chunks=18812, total_queries=1318, evaluated_queries=1298, skipped_no_gt=20, elapsed=46.231s, recall@1=0.0378, recall@5=0.1988, recall@10=0.2997, mrr@10=0.1029, ndcg@10=0.0666
  - CUAD dense 说明：
    - CUAD full corpus=675400 chunks，CPU exact dense 全量 embedding/scoring 成本较高；Task 8 先保留 smoke/sample。
    - 已完成可复现 sample：`.venv/bin/python paper/experiments/scripts/dense_baseline.py --dataset cuad --model sentence-transformers/all-MiniLM-L6-v2 --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10 --max-queries 100 --max-corpus 10000`
    - CUAD sample: max_queries=100, max_corpus=10000, evaluated_queries=74, skipped_no_gt=26, elapsed=78.099s, recall@1=0.0135, recall@5=0.0135, recall@10=0.0135, mrr@10=0.0135, ndcg@10=0.0063
  - 已运行回归测试：`cache/test_dense_baseline.py`、`cache/test_bm25_baseline.py`、`cache/test_retrieval_metrics.py`、`cache/test_download_parquet.py`、`cache/test_preprocess_ragbench.py`、`cache/test_validate_processed.py`、`cache/test_requirements.py`，全部通过。
  - 已运行 `python -m py_compile paper/experiments/scripts/dense_baseline.py cache/test_dense_baseline.py`，语法检查通过。
- Task 9 已完成：hybrid BM25 + dense retrieval baseline
  - 新增 `cache/test_hybrid_baseline.py`，覆盖 RRF 融合排序、toy hybrid ranking/metrics、`max_queries`/`max_corpus` 抽样、结果文件与 summary 输出。
  - 新增 `paper/experiments/scripts/hybrid_baseline.py`：
    - 复用 `bm25_baseline.py` 的 sparse BM25 排序和 `dense_baseline.py` 的 exact cosine dense 排序。
    - 使用 Reciprocal Rank Fusion (RRF) 融合 BM25/dense 排名，默认 `rrf_k=60`，`fusion_depth=100`，避免校准 BM25 分数和 dense cosine 分数。
    - 输出 `paper/experiments/results/hybrid_{dataset}_rankings.json`、`hybrid_{dataset}_metrics.json` 和 `hybrid_baseline_summary.csv`。
    - 支持 `--dataset`、`--model`、`--local-files-only`、`--device`、`--batch-size`、`--top-k`、`--fusion-depth`、`--rrf-k`、`--ks`、`--max-queries`、`--max-corpus`。
  - 使用本地缓存模型：`sentence-transformers/all-MiniLM-L6-v2`，`--local-files-only --device cpu`。
  - 全量已完成数据集 hybrid RRF 结果：
    - PubMedQA: chunks=4348, queries=1000, skipped_no_gt=0, elapsed=63.261s, recall@1=0.7070, recall@5=0.9830, recall@10=0.9890, mrr@10=0.8443, ndcg@10=0.7230
    - Banking77: chunks=10003, queries=3080, skipped_no_gt=0, elapsed=55.848s, recall@1=0.9136, recall@5=0.9721, recall@10=0.9851, mrr@10=0.9394, ndcg@10=0.8504
    - eManual: chunks=18812, total_queries=1318, evaluated_queries=1298, skipped_no_gt=20, elapsed=58.741s, recall@1=0.0501, recall@5=0.2203, recall@10=0.3552, mrr@10=0.1213, ndcg@10=0.0850
  - CUAD hybrid 说明：
    - CUAD full corpus=675400 chunks，CPU exact dense 全量 embedding/scoring 成本较高；Task 9 沿用 smoke/sample。
    - 已完成可复现 sample：`.venv/bin/python paper/experiments/scripts/hybrid_baseline.py --dataset cuad --model sentence-transformers/all-MiniLM-L6-v2 --local-files-only --device cpu --batch-size 64 --top-k 10 --fusion-depth 100 --ks 1,5,10 --max-queries 100 --max-corpus 10000`
    - CUAD sample: max_queries=100, max_corpus=10000, evaluated_queries=74, skipped_no_gt=26, elapsed=80.288s, recall@1=0.0000, recall@5=0.0270, recall@10=0.0405, mrr@10=0.0096, ndcg@10=0.0060
  - 已运行回归测试：`cache/test_hybrid_baseline.py`、`cache/test_dense_baseline.py`、`cache/test_bm25_baseline.py`、`cache/test_retrieval_metrics.py`，全部通过。
  - 已运行 `python -m py_compile paper/experiments/scripts/hybrid_baseline.py cache/test_hybrid_baseline.py`，语法检查通过。
- Task 9.5 已完成：实验协议与评估口径修正
  - 背景：Task 7-9 结果工程上可复现，但论文口径需要先收紧，否则 Task 10 汇总表会把不可比较结果放进同一主表。
  - 已确认 8 个必须修正点：
    - RAGBench eManual/CUAD 必须显式区分 train/validation/test query split。
    - CUAD 的 BM25/dense/hybrid sample/corpus 口径必须一致；当前结果先标为 smoke/sample。
    - PubMedQA/eManual/CUAD 属于 evidence retrieval；Banking77 属于 intent retrieval proxy/domain routing。
    - 当前 dense baseline 是 `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine，不是 BGE-large。
    - Task 10 汇总器需要 `scope`、`query_split`、`corpus_scope`、`comparable_group`、`is_comparable`、`notes` guardrails。
    - PubMedQA GT 是 abstract context section-level，不是严格 answer-supporting sentence-level evidence。
    - Task 11-13 在线学习必须使用 prequential 或 train-feedback/test-eval 防泄漏协议。
    - 需要新增 scientific tests 覆盖 split filtering、sample consistency、comparison guardrails、scope/notes 标注。
  - 已更新本进度文档的 Task 9.5 规划。
  - 已更新 `paper/experiments/README.md`：
    - 同步当前脚本目录和 baseline 运行方式。
    - 新增 Dataset task type、静态检索指标、split/comparability guardrails、在线学习防泄漏协议。
    - 明确当前 CUAD 结果为 smoke/sample，当前 dense baseline 为 `all-MiniLM-L6-v2` CPU exact cosine。
  - 新增 `paper/experiments/scripts/experiment_guardrails.py`：
    - 统一实现 `query_split` 过滤、query/corpus sample scope 标注、dataset `task_type`、PubMedQA/Banking77/dense model notes。
    - 可从历史 `*_metrics.json` 生成 `paper/experiments/results/retrieval_baseline_comparison.csv`。
    - comparison group 由 dataset、query scope、corpus scope、top_k、ks 组成；缺少 BM25/dense/hybrid 三方同口径结果时自动 `is_comparable=false`。
  - 已更新 `bm25_baseline.py`、`dense_baseline.py`、`hybrid_baseline.py`：
    - 新增 `--query-split`，支持 RAGBench held-out `test` query 评估。
    - BM25 新增 `--max-corpus`，便于和 dense/hybrid 使用同一 CUAD sample corpus。
    - metrics/summary 输出新增 `task_type`、`scope`、`query_split`、`query_splits`、`query_scope`、`corpus_scope`、`comparable_group`、`is_comparable`、`metric_ks`、`notes`。
  - 已生成 `paper/experiments/results/retrieval_baseline_comparison.csv`：
    - 12 rows，覆盖 BM25/dense/hybrid × PubMedQA/Banking77/eManual/CUAD。
    - eManual 历史结果标为 `historical_mixed_split`，三方法口径一致但不能作为 held-out 主表。
    - CUAD 历史结果标为 `smoke_only`；BM25 full corpus 与 dense/hybrid first-10000 corpus 不同组，均 `is_comparable=false`。
    - Banking77 标为 `intent_retrieval_proxy`，和 evidence retrieval 分开解释。
  - 新增 `cache/test_experiment_guardrails.py`，覆盖 split filtering、sample/smoke scope、comparison guardrails、legacy metrics enrichment。
  - 已运行回归测试：`python -m unittest cache/test_experiment_guardrails.py cache/test_bm25_baseline.py cache/test_dense_baseline.py cache/test_hybrid_baseline.py cache/test_retrieval_metrics.py`，24 tests 通过。
  - 已运行语法检查：`python -m py_compile paper/experiments/scripts/experiment_guardrails.py paper/experiments/scripts/bm25_baseline.py paper/experiments/scripts/dense_baseline.py paper/experiments/scripts/hybrid_baseline.py cache/test_experiment_guardrails.py cache/test_bm25_baseline.py`，通过。
  - 已基于新 guardrails 重跑相关 baseline：
    - eManual held-out `test` split + full corpus：
      - BM25: evaluated_queries=130, skipped_no_gt=2, recall@10=0.1154, mrr@10=0.0244
      - dense all-MiniLM-L6-v2: evaluated_queries=130, skipped_no_gt=2, recall@10=0.3231, mrr@10=0.0551
      - hybrid RRF: evaluated_queries=130, skipped_no_gt=2, recall@10=0.1692, mrr@10=0.0366
    - CUAD unified smoke/sample `test + max_queries=100 + max_corpus=10000`：
      - BM25: evaluated_queries=79, skipped_no_gt=21, recall@10=0.0000, mrr@10=0.0000
      - dense all-MiniLM-L6-v2: evaluated_queries=79, skipped_no_gt=21, recall@10=0.0000, mrr@10=0.0000
      - hybrid RRF: evaluated_queries=79, skipped_no_gt=21, recall@10=0.0000, mrr@10=0.0000
    - 已重新生成 `paper/experiments/results/retrieval_baseline_comparison.csv`：
      - eManual 三方法均为 `heldout_test/test/full/is_comparable=true`。
      - CUAD 三方法均为 `smoke_only/test/first_10000/is_comparable=true`，但仍不得作为 full-corpus 主表结果。
  - 重跑后已再次验证：`.venv/bin/python -m unittest cache/test_experiment_guardrails.py cache/test_bm25_baseline.py cache/test_dense_baseline.py cache/test_hybrid_baseline.py cache/test_retrieval_metrics.py`，24 tests 通过；`.venv/bin/python -m py_compile ...` 通过。
  - Task 10 已完成：基于 `retrieval_baseline_comparison.csv` 生成论文主表；CUAD 只进入 smoke/sample 附表或注释，不进入 full-corpus 主表。

- 2026-04-28 CUAD GT guardrail follow-up：
  - 问题定位：旧 CUAD `test + first_100 queries + first_10000 corpus` 中，79 个有 GT 的评估 query 有 0 个 query 的 GT chunk 落在 selected corpus，因此 BM25/dense/hybrid/LinUCB 全 0 属于 sample protocol failure，不是算法结论。
  - 已新增 GT-in-corpus guardrail：
    - `gt_corpus_coverage()` / `assert_gt_corpus_coverage()` 统计并强制检查 `num_queries_with_gt_in_corpus`、`gt_query_coverage`、`gt_ref_coverage`、`gt_corpus_guardrail`。
    - sampled corpus 若让任一有 GT 的评估 query 完全没有 GT chunk，会直接报错。
  - 已新增 CUAD `gt_anchored` corpus sampling：
    - 默认 `--corpus-sampling auto` 下，CUAD 只要设置 `--max-corpus` 就使用 `gt_anchored`。
    - sample 由 selected query 的 GT chunks + 随机 distractors 组成，metadata 写为 `corpus_scope=gt_anchored_10000`。
  - 已重跑 CUAD smoke：
    - Static BM25: `gt_query_coverage=1.0000`, recall@10=0.0506, mrr@10=0.0232
    - Static dense all-MiniLM-L6-v2: `gt_query_coverage=1.0000`, recall@10=0.0759, mrr@10=0.0334
    - Static hybrid RRF: `gt_query_coverage=1.0000`, recall@10=0.0633, mrr@10=0.0254
    - Global LinUCB: `gt_query_coverage=1.0000`, recall@10_mean=0.0464, mrr@10_mean=0.0275
  - 已重新生成：
    - `paper/experiments/results/retrieval_baseline_comparison.csv`
    - `paper/experiments/results/retrieval_baseline_*_table.csv`
    - `paper/experiments/results/retrieval_baseline_tables.md`
    - `paper/experiments/results/linucb_online_*_table.csv`
    - `paper/experiments/results/linucb_online_tables.md`
  - 已修正 `summarize_retrieval_baselines.py`，静态 retrieval table 只收 BM25/dense/hybrid，避免把 LinUCB metrics 混入静态 baseline 表。
  - 已运行完整回归：`.venv/bin/python -m unittest discover cache`，40 tests 通过。

- 2026-04-28 Task 13 global vs manifold-local comparison：
  - 新增 `paper/experiments/scripts/compare_linucb_variants.py`：
    - 读取 `linucb_online_summary.csv` 与 `linucb_manifold_summary.csv`。
    - 按 `dataset/task_type/scope/query_split/corpus_scope/top_k/metric_ks` 对齐同口径结果。
    - 输出 `delta_recall@10_mean`、`relative_recall@10_pct`、`delta_mrr@10_mean`、winner 与解释文本。
  - 新增 `cache/test_compare_linucb_variants.py`，覆盖 delta/winner、非同口径跳过、CSV/Markdown 输出。
  - 已生成：
    - `paper/experiments/results/linucb_variant_comparison.csv`
    - `paper/experiments/results/linucb_variant_comparison.md`
  - 对比结论：
    - PubMedQA: global recall@10=0.5480, manifold recall@10=0.6607, delta=+0.1127；MRR@10 delta=+0.1016。
    - eManual: global recall@10=0.1154, manifold recall@10=0.0923, delta=-0.0231；但 MRR@10 delta=+0.0012。
    - Banking77: global recall@10=0.7215, manifold recall@10=0.8247, delta=+0.1031；MRR@10 delta=+0.1395。
    - CUAD smoke: global recall@10=0.0464, manifold recall@10=0.0295, delta=-0.0169；MRR@10 delta=-0.0155。
  - 论文解释要点：
    - 流形局部反馈在 PubMedQA 与 Banking77 这类结构较清晰/标签较密的数据上有效。
    - eManual/CUAD 当前未提升，说明局部传播对 sparse evidence、噪声 GT、长文档局部证据可能过度传播或参数不匹配。
    - Task 13 结果支持“可验证条件下的流形局部反馈”，但不支持“无条件优于全局 LinUCB”的强结论。

- 2026-04-29 Task 13.5 soft-routed manifold LinUCB：
  - 新增 `paper/experiments/scripts/linucb_soft_routing.py`：
    - 保留 Task 12 的 manifold-local LinUCB arm selection、query-neighborhood feedback attention、cross-arm propagation。
    - 最终检索不再 hard gate 到 selected clusters，而是融合三路候选：global dense、global BM25、selected-cluster dense。
    - 使用 weighted RRF，并新增 `--dense-floor-k` 保护前若干 global dense 候选，降低 soft fusion 将 dense 证据挤出 top-k 的风险。
    - 新增 hard-pruning 诊断：`selected_cluster_hit_rate`、`selected_cluster_miss_rate`、`soft_rescue_on_cluster_miss_rate`、`dense_fallback_hit_rate`、`bm25_fallback_hit_rate`、`cluster_local_hit_rate`。
    - dense source ranking 在 Task 13.5 内使用 stable score-desc/index-asc 排序，避免 `argpartition` 在大量 tie/near-tie 时因 `depth=10` vs `depth=100` 产生不稳定前缀。
  - 新增 `paper/experiments/scripts/summarize_linucb_soft.py`：
    - 输出 `linucb_soft_main_table.csv`、`linucb_soft_intent_proxy_table.csv`、`linucb_soft_smoke_table.csv`、`linucb_soft_tables.md`。
  - 新增测试：
    - `cache/test_linucb_soft_routing.py`
    - `cache/test_summarize_linucb_soft.py`
  - 已运行正式矩阵：
    - PubMedQA full/train/full: recall@10_mean=0.9920, mrr@10_mean=0.8466, selected_cluster_hit_rate=0.6817, soft_rescue_on_cluster_miss_rate=0.9800。
    - eManual heldout_test/test/full: recall@10_mean=0.1436, mrr@10_mean=0.0337, selected_cluster_hit_rate=0.2641, soft_rescue_on_cluster_miss_rate=0.1173；仍低于 dense baseline，说明 source recall/cluster routing 仍是瓶颈。
    - Banking77 heldout_test/test/full: recall@10_mean=0.9831, mrr@10_mean=0.9420, selected_cluster_hit_rate=0.8829, soft_rescue_on_cluster_miss_rate=0.9699。
    - CUAD smoke_only/test/gt_anchored_10000: recall@10_mean=0.0844, mrr@10_mean=0.0344, selected_cluster_hit_rate=0.3713, soft_rescue_on_cluster_miss_rate=0.0865；仅作为 smoke/sample。
  - 已生成：
    - `paper/experiments/results/linucb_soft_summary.csv`
    - `paper/experiments/results/linucb_soft_*_table.csv`
    - `paper/experiments/results/linucb_soft_tables.md`
  - 当前解释：
    - Task 13.5 明显修复了 Task 11/12 的 hard-pruning 损失，在 PubMedQA、Banking77、CUAD smoke 上恢复到接近或略高于 dense 的 Recall@10。
    - eManual 仍是负例，说明“流形 + feedback + BM25/dense fusion”不是无条件优于 dense；论文应将其作为适用边界和后续 reranker/领域 embedding/arm 设计改进方向。

- 2026-04-29 阶段性经验总结 / 当前暂停点：
  - 当前方法定位已从“LinUCB 替代 dense/BM25”修正为“LinUCB-guided adaptive multi-route retrieval”：
    - dense/BM25 提供稳定召回底座和 bypass，避免 hard pruning 的不可恢复漏召回。
    - cluster-local dense + LinUCB 提供可学习的局部流形导航信号。
    - weighted RRF + dense floor 负责把 lexical、semantic、cluster-local 三类信号融合成最终候选。
  - 当前结果支持“双重优势”但需限定边界：
    - 稳定性：Task 13.5 在 PubMedQA、Banking77、CUAD smoke 上显著减少 Task 11/12 的硬裁剪损失。
    - 自我进化：LinUCB arm 选择可随 GT/用户反馈更新；若引入用户信誉分，可对高可信反馈赋予更大更新权重，降低用户反馈噪声和方差。
    - 边界条件：eManual 仍低于 dense baseline，说明部分 sparse evidence/长文档局部证据场景仍需继续诊断，不能声称无条件优于 dense。
  - 成本优化逻辑需要作为下一阶段，而不是 Task 13.5 已完成的结论：
    - Task 13.5 是 robustness phase：三路召回全开，主要解决召回稳定性。
    - 后续应进入 efficiency phase：把成本、延迟、上下文 token、rerank 候选数写入 reward。
    - 随着 LinUCB arm 策略收敛，可逐步降低 global dense/BM25 depth 或权重，让系统更多依赖高置信 selected arms，从而减少 embedding/index 查询、rerank 候选和 LLM context token。
  - Task 13.5 后补充确认：
    - 当前实验仍是 retrieval-only evaluation，尚未调用 LLM；评估目标是检索出的 context/chunk 是否命中 GT，而不是生成答案质量。
    - 这一设计在当前阶段是合理的：目标 context 正确是 LLM 回答正确的必要前提，后续端到端 answer relevance、faithfulness、citation correctness、RAGAS/LLM-as-judge 可作为扩展实验。
    - 即使暂时忽略 LLM，用户 feedback 仍可作用于 retrieval bandit：反馈可绑定到最终 context、引用 chunk、点击/采纳证据、检索 route 或 cluster arm，再转化为 LinUCB reward 更新。
    - 真实系统中应把用户信誉分纳入更新权重，例如用 `trust_user * reward` 更新对应 arm，以降低低质量反馈带来的方差。
    - 综合 reward 不是流形特征本身，而是流形上动态价值场的观测；embedding/PCA/cluster/dense/BM25 描述相对稳定的几何结构，reward 描述不同 query/context/arm 在该结构上的价值分布。
  - 建议后续任务：
    - Task 14：manifold diagnostics，先验证各数据集是否存在可利用的局部流形结构，并解释 eManual 失败原因。
    - Task 15：trust-weighted feedback LinUCB，模拟高/低信誉用户反馈，比较等权反馈 vs 信誉加权反馈的收敛和鲁棒性。
    - Task 16：cost-aware soft routing，比较固定三路全开 vs confidence-gated routing，在 Recall@k/MRR 与 latency/candidate/context token 成本之间画 trade-off。

- 2026-04-29 Task 14 manifold diagnostics：
  - 新增 `paper/experiments/scripts/manifold_diagnostics.py`：
    - 计算 PCA spectrum、`pca_dim_for_90pct`、participation ratio、spectral entropy 等低维集中度指标。
    - 基于现有 PCA context + MiniBatchKMeans cluster arms，计算 cluster size entropy、silhouette sample、metadata label purity/NMI/ARI。
    - 计算 local label purity，衡量 embedding/PCA 邻域是否与可用 metadata label 对齐。
    - 计算 `nearest_cluster_hit@1/3/5`：不用 LinUCB，只按 query context 到 cluster centroid 的距离，看最近 cluster 是否包含 GT chunk。
    - 计算 `context_gt_recall@k` 与 `context_recall_retention@k`，验证 PCA context 是否保留 dense evidence retrieval 能力。
  - 新增 `paper/experiments/scripts/summarize_manifold_diagnostics.py`：
    - 将 `manifold_diagnostics_summary.csv` 与 dense baseline、Task13.5 soft summary 对齐。
    - 输出 `manifold_diagnostics_comparison.csv` 与 `manifold_diagnostics_tables.md`。
  - 新增测试：
    - `cache/test_manifold_diagnostics.py`
    - `cache/test_summarize_manifold_diagnostics.py`
  - 已运行正式矩阵：
    - PubMedQA full/train/full: `pca_dim_for_90pct=177`, `local_label_purity=0.2439`, `nearest_cluster_hit@3=0.9680`, `context_gt_recall@10=0.9860`, Task13.5-dense delta=-0.0010。
    - eManual heldout_test/test/full: `pca_dim_for_90pct=111`, `local_label_purity=0.0169`, `nearest_cluster_hit@3=0.8923`, `context_gt_recall@10=0.3615`, Task13.5-dense delta=-0.1795。
    - Banking77 heldout_test/test/full: `pca_dim_for_90pct=105`, `local_label_purity=0.8539`, `nearest_cluster_hit@3=0.9968`, `context_gt_recall@10=0.9782`, Task13.5-dense delta=+0.0026。
    - CUAD smoke_only/test/gt_anchored_10000: `pca_dim_for_90pct=182`, `local_label_purity=0.0716`, `nearest_cluster_hit@3=0.6076`, `context_gt_recall@10=0.0759`, Task13.5-dense delta=+0.0084。
  - 当前解释：
    - Banking77 的流形结构最清晰：label/local purity 与 nearest-cluster hit 都高，支持 intent proxy 上的 soft routing 表现。
    - PubMedQA 的 metadata label purity 不高，但 nearest-cluster hit 与 context recall 很高，说明 evidence routing 几何有效，Task13.5 主要是在保留 dense 强基线。
    - CUAD smoke 局部结构弱，Task13.5 的小幅提升主要来自多路召回鲁棒性，不足以作为 full-corpus 结论。
    - eManual 并不是“完全没有几何信号”：nearest_cluster_hit@3=0.8923 且 context_gt_recall@10 高于 dense baseline；失败更可能在 LinUCB arm 选择、credit assignment、fusion/ranking 或 reward 对 selected cluster 的利用不足。
  - 后续任务顺序调整：
    - Task 14.5：eManual failure analysis，比较 strict chunk-id、text-equivalent、deduplicated corpus、nearest-centroid routing、LinUCB selected cluster。
    - Task 15：trust-weighted feedback LinUCB。
    - Task 16：cost-aware soft routing。

- 2026-04-29 Task 14.5 eManual failure analysis：
  - 新增 `paper/experiments/scripts/emanual_failure_analysis.py`：
    - 复用现有 eManual rankings，分别计算 strict chunk-id 与 text-equivalent retrieval 指标。
    - 统计 eManual full corpus 的 exact duplicate normalized text 分布和 GT duplicate exposure。
    - 构造 text-deduplicated eManual corpus，重跑 BM25/dense/hybrid baseline。
    - 重跑 nearest-centroid local routing 与 GT-cluster oracle，用来区分“几何信号是否存在”和“LinUCB/fusion 是否吃到几何红利”。
  - 新增 `cache/test_emanual_failure_analysis.py`，覆盖 text-equivalent 评估、GT 去重映射、seed-nested rankings 加载、duplicate stats。
  - 已运行正式分析：
    - eManual full corpus: 18812 chunks，但只有 1729 个 unique normalized texts。
    - duplicate text groups=1571，chunks_in_duplicate_text_groups=18654，最大重复组大小=326。
    - test GT refs=861，其中 861/861 都有 duplicate text；每个 GT text 平均重复 22.2636 次。
    - dense strict recall@10=0.3231，但 text-equivalent recall@10=0.5615。
    - Task13.5 soft strict recall@10=0.1436，但 text-equivalent recall@10=0.5795。
    - deduplicated dense recall@10=0.8615，deduplicated hybrid recall@10=0.8615。
    - nearest-centroid 3-cluster strict recall@10=0.3308，text-equivalent recall@10=0.5462。
    - GT-cluster oracle strict recall@10=0.3308，text-equivalent recall@10=0.6615。
    - LinUCB selected_cluster_hit_rate_mean=0.2641，cluster_local_hit_rate_mean=0.0487。
  - 当前解释：
    - eManual 不能作为“无流形结构”的证据；其 `record_id` 是实例级标签，不是主题/功能级语义标签。
    - eManual strict chunk-id 指标明显受跨 record 重复文本影响，会把“同一句证据但来自另一条 record”的结果判为 miss。
    - eManual 当前负例更准确地描述为：存在可利用几何和文本证据信号，但当前 LinUCB arm selection、fusion/ranking、credit assignment 没有把该信号稳定转化为 strict chunk-id 命中。
    - 论文主表仍应保留 strict chunk-id 作为 guarded metric；text-equivalent 与 deduplicated results 作为 failure analysis / diagnostic appendix，不替代主结论。
  - 论文实验设计补充：
    - 本论文的消融实验不是附属内容，而是证明机制有效性的关键证据。
    - 当前方法由 BM25、dense、cluster、LinUCB、feedback、fusion、guardrails 组成；只报告最终分数无法说明提升或失败来自哪个环节。
    - 必须通过组件消融回答：dense/BM25 是召回底座还是遮蔽 LinUCB？cluster 是帮助局部导航还是造成漏召回？dense floor 是否让方法退化成 dense？feedback 是否真的改善 arm policy？
    - 必须通过 eManual 修正型消融回答：strict chunk-id、text-equivalent、deduplicated corpus、nearest-centroid warm start、text-equivalent reward、fusion calibration 分别如何影响结果。
    - 必须通过成本消融回答：full multi-route、confidence-gated routing、reduced dense/BM25 depth 在 recall、candidate count、context token、latency 之间的 trade-off。
    - 因此后续 Task 15/16 不应只追求单个更高分数，而应围绕 ablation matrix 解释机制边界、适用条件和工程收益。

- 2026-04-30 研究定位更新与 Task 15 前置结论：
  - 当前论文价值应从“静态无条件超过 dense”转向“feedback-driven self-evolving retrieval policy”。
  - dense 是强基线，不应被描述成必须替代的对象；更合理定位是稳定召回底座、强对照组和可降级安全兜底通道。
  - 本方法最大研究价值在于：把 RAG 检索从固定排序问题改造成可通过用户反馈持续修正的策略学习问题。
  - 在小/中规模公开数据集上，dense 可能已经足够强；本方法的工程优势更可能出现在大规模、垂类、异构、持续交互、成本敏感的 RAG 系统中。
  - 后续 scale-up 实验需要验证 corpus size 增长时，本方法能否在接近 dense 质量的同时降低 candidate count、context token、latency 或 dense/BM25 查询深度。
  - 后续 cost-aware routing 中，dense 不应永久关闭，而应降级为 conditional fallback：
    - 高置信：cluster/BM25/lightweight route 优先；
    - 中置信：保留 small dense floor；
    - 低置信、OOD、负反馈增加或语义相关性不足：触发 full dense fallback。
  - Task 15 的核心目标不是刷新静态 recall，而是验证 feedback 是否能让 LinUCB arm policy 随使用逐步改善，并证明 trust-weighted feedback 比等权 noisy feedback 更稳。
  - Task 16/17 应继续验证 confidence-gated dense fallback 与 large-scale RAG scaling。

- 2026-04-30 Task 15 trust-weighted feedback LinUCB：
  - 新增 `paper/experiments/scripts/linucb_trust_feedback.py`：
    - 保留 Task13.5 的 soft multi-route retrieval：global dense、global BM25、LinUCB-selected cluster-local dense、weighted RRF、dense floor。
    - 新增 repeated prequential feedback protocol：每个 query 先评估，再用模拟 feedback 更新 selected cluster arms，支持多 epoch 观察自进化趋势。
    - 对比 `none`、`oracle`、`equal_noisy`、`trust_weighted` 四种模式。
    - `trust_weighted` 用模拟用户信誉分缩放 LinUCB update weight 与 local feedback memory，近似工程系统中“高信誉用户反馈更可信、低信誉用户反馈降权”的机制。
  - 新增测试 `cache/test_linucb_trust_feedback.py`，覆盖 feedback mode 解析、用户反馈模拟、window gain、prequential seed evolution、结果写盘。
  - 已运行 Task15 矩阵：
    - PubMedQA full/train/full：`trust_weighted recall@10=0.9940`，`last_epoch_true_reward=0.8727`，`epoch_true_reward_gain=+0.4030`，`selected_cluster_hit_gain=+0.3950`。
    - eManual heldout_test/test/full：`trust_weighted recall@10=0.1487`，`last_epoch_true_reward=0.0556`，`epoch_true_reward_gain=+0.0152`，`selected_cluster_hit_gain=+0.0429`。
    - Banking77 heldout_test/test/full：`trust_weighted recall@10=0.9844`，低于 no-feedback `0.9855` 约 `-0.0011`；但 `last_epoch_true_reward=0.9805`、`epoch_true_reward_gain=+0.1317`、`selected_cluster_hit_gain=+0.0627`，说明 full 版主要验证 policy self-evolution，而不是 final recall 提升。
    - Banking77 sample/test/full：`trust_weighted recall@10=0.9863`，`last_epoch_true_reward=0.9583`，`epoch_true_reward_gain=+0.2863`，`selected_cluster_hit_gain=+0.1957`；sample 版显示 final recall 小幅提升，但论文主叙述应以 full 版为准。
    - CUAD smoke_only/test/gt_anchored_10000：`trust_weighted recall@10=0.0886`，`last_epoch_true_reward=0.0233`，`epoch_true_reward_gain=+0.0167`，`selected_cluster_hit_gain=+0.0400`。
  - 当前解释：
    - Task15 最终论文口径：`last_epoch_true_reward` 是 LinUCB 自进化最核心证据；`epoch_true_reward_gain` 与 `selected_cluster_hit_gain` 是学习过程和 arm selection 改善的辅助证据；`Recall@k` 是多路融合后的下游检索结果，不应单独用来判断 LinUCB 是否自进化。
    - Task15 验证的不是“静态检索分数大幅超过 dense”，而是 feedback 能让 LinUCB 的 arm policy / value field 随交互变好。
    - final recall 的变化可能较小，因为 dense/BM25 bypass 与 dense floor 已经把最终召回稳定住；因此应同时报告 `last_epoch_true_reward`、`epoch_true_reward_gain`、`selected_cluster_hit_rate`、`selected_cluster_hit_gain`。
    - PubMedQA、Banking77 full/sample 都显示 trust-weighted feedback 能显著改善策略层指标；但 Banking77 full 的 final recall 未提升，说明 final R@k 会被 dense/BM25 floor、近天花板基线和 fusion 排序共同影响。
    - CUAD smoke 在稀疏 GT 下只有小幅正向趋势；eManual 仍受 strict chunk-id、duplicate text 与 policy/fusion 问题限制。
    - dense 不应永久关闭，而应在后续 Task16 cost-aware routing 中作为 conditional fallback：高置信时降低 dense/BM25 depth 或权重，低置信、OOD、负反馈增加或语义相关不足时恢复 full dense fallback。

- 2026-04-30 Task 16 cost-aware soft routing：
  - 新增 `paper/experiments/scripts/linucb_cost_aware_routing.py`：
    - 复用 Task13.5/15 的 global dense、BM25、LinUCB-selected cluster-local dense、weighted RRF、trust-weighted feedback。
    - 新增 `full_multi_route` 与 `gated_cost_aware` 两个 routing mode。
    - `full_multi_route` 保持 dense/BM25/cluster 三路全开，作为质量优先对照。
    - `gated_cost_aware` 根据 LinUCB policy confidence 与 selected-cluster semantic drift 切换路由；当前正式矩阵采用保守阈值，只启用 `hybrid_lite + full_dense_fallback`，不直接完全关闭 dense。
    - 成本指标使用 source candidate count：`dense_candidates + bm25_candidates + cluster_candidates`，同时记录 `dense_query_rate`、`hybrid_lite_rate`、`full_dense_fallback_rate`。
  - 新增 `cache/test_linucb_cost_aware_routing.py`，覆盖 route mode 解析、gating 决策、policy confidence maturity、结果写盘。
  - 已运行正式矩阵：
    - PubMedQA full/train/full：full `recall@10=0.9940`、cost `299.94`；gated `recall@10=0.9893`、cost `152.36`，R@10 `-0.0047`，成本下降 `49.20%`。
    - Banking77 heldout_test/test/full：full `recall@10=0.9844`、cost `300.00`；gated `recall@10=0.9813`、cost `142.51`，R@10 `-0.0031`，成本下降 `52.50%`。
    - Banking77 sample/test/full：full `recall@10=0.9863`、cost `300.00`；gated `recall@10=0.9817`、cost `146.28`，R@10 `-0.0047`，成本下降 `51.24%`；作为 full 结果的补充观察。
    - eManual heldout_test/test/full：full `recall@10=0.1487`、cost `300.00`；gated `recall@10=0.1154`、cost `214.07`，R@10 `-0.0333`，成本下降 `28.64%`。
    - CUAD smoke_only/test/gt_anchored_10000：full `recall@10=0.0886`、cost `300.00`；gated `recall@10=0.0633`、cost `203.47`，R@10 `-0.0253`，成本下降 `32.18%`。
  - 当前解释：
    - Task16 验证了成本优化存在可行 trade-off，但不是无损提升。
    - PubMedQA 与 Banking77 full 能以低于 0.5 个百分点 R@10 损失换约 49%-52% source candidate cost 降低，支持“feedback 后可逐步降低 dense/BM25 深度和候选规模”的工程价值。
    - eManual 与 CUAD 不适合使用同一 gating 强度；这两个数据集应保持更强 full dense fallback，或等待 text-equivalent reward、dedup/reranker、领域 embedding 等修正后再做成本压缩。
    - 当前正式结果支持“先 dense-lite / BM25-lite，再 full dense fallback”的保守路线；直接把 dense 完全关闭为兜底通道仍需要更强的 policy confidence、语义漂移检测和 OOD guardrail。

- 2026-05-05 Task 17 前置讨论与 LoTTE 小样本验证：
  - 当前 large-scale 数据集定位：
    - PubMedQA full 已完成：`1000` queries / `4348` corpus chunks，是 full 小规模 evidence anchor，不再作为 large-scale。
    - Banking77 full 已完成：`3080` queries / `10003` corpus chunks，是 full 中规模 intent/domain routing proxy，不再作为 large-scale。
    - CUAD corpus 大，但 GT 稀疏且结构弱，更适合作为 large-scale stress / limitation case，而不是主正向证明。
    - LoTTE 更适合 Task17：垂类 domain-search，technology/search test corpus 约 `638509` passages，test queries 约 `596`，有 qrels，可同时验证垂类适配和大规模质量-成本 trade-off。
  - 新增 `paper/experiments/scripts/preprocess_lotte.py`：
    - 支持 `mteb/LoTTE` 的 `{domain}_{mode}-corpus`、`queries`、`qrels` 映射到统一 processed schema。
    - 默认非 streaming 加载，避免 HF streaming 在当前环境退出时出现 Python finalization 错误；保留 `--streaming` 选项。
    - 小样本为 GT-anchored：抽中 query 的所有正样本 corpus chunk 必须进入 corpus，再补 distractors。
  - 新增/更新测试：
    - `cache/test_preprocess_lotte.py`
    - `cache/test_experiment_guardrails.py` 中新增 `lotte_* -> evidence_retrieval` 分类测试。
  - 已生成 LoTTE technology/search 小样本：
    - 命令：`.venv/bin/python paper/experiments/scripts/preprocess_lotte.py --domain technology --mode search --split test --max-queries 20 --max-corpus 5000`
    - 输出：`lotte_technology_search_corpus.json` / `lotte_technology_search_queries.json`
    - corpus chunks=`5018`，queries=`20`，GT refs=`56`
    - validate：queries_with_gt=`20`，GT coverage=`100.00%`，missing refs=`0`
  - LoTTE 小样本 baseline：
    - BM25：Recall@10=`0.9000`，MRR@10=`0.8100`
    - dense all-MiniLM-L6-v2：Recall@10=`0.9000`，MRR@10=`0.9000`
    - hybrid RRF：Recall@10=`1.0000`，MRR@10=`0.9300`
  - LoTTE 小样本 cost-aware LinUCB smoke：
    - 配置：1 seed / 1 epoch / 16 clusters / 32 context dim / depth 50
    - full_multi_route：Recall@10=`1.0000`，last_reward=`0.5000`，avg_cost=`150.00`，dense_rate=`1.0000`
    - gated_cost_aware：Recall@10=`0.9500`，last_reward=`0.4500`，avg_cost=`129.50`，dense_rate=`0.9500`，primary_rate=`0.0500`
  - 当前结论：
    - LoTTE 小样本已经通过数据、GT、baseline 与 LinUCB 路由的 pipeline 验证。
    - Task17 可以以 LoTTE 为主做 large-scale，重点不是证明无条件超过 dense，而是验证大规模垂类场景下的 self-evolving policy 与 quality-cost trade-off。
    - 正式 Task17 应逐步扩大 query/corpus scope，并报告 Recall/MRR/nDCG、candidate cost、dense query rate、fallback rate、policy reward evolution、selected-cluster hit evolution。

- 2026-05-05 Task 17 stage-1 LoTTE 100k large-scale smoke：
  - 生成独立 large-scale processed dataset，避免覆盖小样本：
    - 命令：`.venv/bin/python paper/experiments/scripts/preprocess_lotte.py --domain technology --mode search --split test --max-queries 596 --max-corpus 100000 --output-name lotte_technology_search_100k`
    - 输出：`lotte_technology_search_100k_corpus.json` / `lotte_technology_search_100k_queries.json`
    - corpus chunks=`101311`，queries=`596`，GT refs=`2045`
    - validate：queries_with_gt=`596`，GT coverage=`100.00%`，missing refs=`0`
  - 100k baseline：
    - BM25：Recall@10=`0.7232`，MRR@10=`0.5545`，nDCG@10=`0.4768`，elapsed=`108.834s`
    - dense all-MiniLM-L6-v2 CPU exact cosine：Recall@10=`0.8674`，MRR@10=`0.7081`，nDCG@10=`0.6487`，elapsed=`1640.076s`
  - 100k cost-aware LinUCB smoke：
    - 配置：1 seed / 1 epoch / 32 clusters / 64 context dim / depths 100
    - full_multi_route：Recall@10=`0.8725`，MRR@10=`0.7089`，last_reward=`0.3104`，avg_cost=`300.00`，dense_rate=`1.0000`，elapsed=`1772.420s`
    - gated_cost_aware：Recall@10=`0.8356`，MRR@10=`0.6888`，last_reward=`0.3356`，avg_cost=`224.16`，dense_rate=`0.9530`，primary_rate=`0.0470`，elapsed=`1905.491s`
    - cost reduction=`25.28%`，Recall@10 delta vs full route=`-0.0369`
  - 当前解释：
    - 这是 Task17 的第一条 large-scale 正向信号：full multi-route LinUCB 在 100k corpus 上略高于 dense baseline（`0.8725` vs `0.8674`）。
    - gated mode 已显示成本压缩潜力，但当前阈值/1-epoch 策略导致 R@10 损失约 `3.69` 个百分点，正式结论不能声称无损。
    - dense baseline 单次 CPU exact cosine 已耗时约 27 分钟，LinUCB 也重复了 embedding 计算；正式 Task17 在扩展 seeds/epochs/full 638k 前，应先实现 embedding cache 或共享 large-scale runner。

- 2026-05-05 Task 17 embedding cache：
  - 新增 `paper/experiments/scripts/embedding_cache.py`：
    - cache key 包含 dataset、model、record kind、record id 与 text fingerprint。
    - 输出 `.npy` embedding 与 `.json` metadata，默认位置 `paper/experiments/data/embeddings/`。
    - 数据或模型变化会自动生成新 cache，不会复用旧向量。
  - 已接入：
    - `dense_baseline.py`
    - `hybrid_baseline.py`
    - `linucb_cost_aware_routing.py`
  - CLI 默认启用 cache，新增参数：
    - `--embedding-cache-dir`
    - `--no-embedding-cache`
    - `--force-embedding-cache`
  - 新增/更新测试：
    - `cache/test_embedding_cache.py`
    - `cache/test_dense_baseline.py`
  - 已做 CLI smoke：
    - LoTTE 小样本 5 query / 100 corpus，第一次 elapsed=`1.484s`，第二次 cache hit elapsed=`0.001s`。
    - 第二次 metrics 标记：`embedding_cache_enabled=True`，`corpus_embedding_cache_hit=True`，`query_embedding_cache_hit=True`。
  - 当前解释：
    - embedding cache 已解决 dense/hybrid/Task16 cost-aware LinUCB 重复编码问题。
    - shared large-scale runner 仍是下一步：它需要进一步复用 BM25 index、dense rankings、cluster labels 等非 embedding 中间产物。

- 2026-05-06 Task 17 LoTTE 100k embedding cache 生成：
  - 已为 `lotte_technology_search_100k` 生成本地 embedding cache：
    - corpus shape=`[101311, 384]`
    - queries shape=`[596, 384]`
    - corpus cache file=`paper/experiments/data/embeddings/lotte_technology_search_100k__sentence-transformers-all-MiniLM-L6-v2__corpus__n101311__60ef5529c079a71e.npy`
    - query cache file=`paper/experiments/data/embeddings/lotte_technology_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n596__6c7ae007c1bcc394.npy`
    - size: corpus=`149M`，queries=`896K`
  - 生成与验证：
    - 首次生成 elapsed=`1598.231s`
    - 二次 cache-hit 校验 elapsed=`0.204s`
    - 校验结果：`corpus_hit=True`，`query_hit=True`
  - 当前状态：
    - cache 文件位于 `paper/experiments/data/embeddings/`，被 `.gitignore` 忽略，不进入 git。
    - LoTTE 100k BM25/dense baseline 与 cost-aware LinUCB smoke 已有结果。
    - LoTTE 100k hybrid baseline 尚未运行，因此 `retrieval_baseline_comparison.csv` 中 100k BM25/dense 仍因缺 hybrid 标为 not comparable。
    - large-scale LoTTE manifold geometry diagnostics 尚未运行；下一步应复用该 embedding cache 运行 Task17 manifold diagnostics。

- 2026-05-06 Task 17.1 / 17.2 LoTTE 100k hybrid 与 manifold diagnostics：
  - LoTTE 100k hybrid baseline 已运行，复用 embedding cache：
    - command: `.venv/bin/python paper/experiments/scripts/hybrid_baseline.py --dataset lotte_technology_search_100k --query-split test --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10`
    - Recall@10=`0.8624`，MRR@10=`0.6973`，nDCG@10=`0.6216`，elapsed=`102.776s`
    - metrics 标记：`embedding_cache_enabled=True`，`corpus_embedding_cache_hit=True`，`query_embedding_cache_hit=True`
    - `retrieval_baseline_comparison.csv` 已更新为 18 rows；LoTTE 100k BM25/dense/hybrid 三方法 now comparable。
  - `manifold_diagnostics.py` 已接入 embedding cache：
    - 新增 `--embedding-cache-dir`、`--no-embedding-cache`、`--force-embedding-cache`
    - 新增测试：LoTTE 不再把 constant `metadata.source=lotte` 当作 label。
  - LoTTE 100k large-scale manifold diagnostics 已运行：
    - command: `.venv/bin/python paper/experiments/scripts/manifold_diagnostics.py --dataset lotte_technology_search_100k --query-split test --local-files-only --device cpu --batch-size 64 --n-clusters 32 --context-dim 64 --seed 13 --sample-size 1000 --neighbor-k 10 --cluster-hit-ks 1,3,5 --recall-ks 1,5,10`
    - elapsed=`6.746s`，cache hit for corpus/query embeddings
    - `pca_dim_for_90pct=182`，`pca_var@64=0.6432`
    - `nearest_cluster_hit@1=0.6997`，`nearest_cluster_hit@3=0.8809`，`nearest_cluster_hit@5=0.9413`
    - dense Recall@10=`0.8674`，context Recall@10=`0.7836`，context retention@10=`0.9033`
    - `gt_cluster_span_mean=1.7282`，`gt_cluster_concentration_mean=0.8120`
    - `label_coverage=0.0`，`cluster_label_purity=0.0`，`local_label_purity=0.0`；LoTTE processed qrels 没有真实 corpus topic/intent label，因此 label metrics 不用于解释。
  - 当前解释：
    - LoTTE 100k large-scale 不只验证了效果与成本，也验证了可利用检索几何：正确证据有较高概率落在 query 近邻 cluster 内。
    - context/PCA 空间保留了约 `90.33%` 的 dense R@10 信号，说明流形压缩可用；但 context-only R@10 仍低于 dense，不能关闭 dense，只能作为 gated / LinUCB routing 的依据。
    - full multi-route LinUCB R@10=`0.8725` 仍是当前 100k 最优结果，高于 dense `0.8674`、hybrid `0.8624`、BM25 `0.7232`。

- 2026-05-06 Task 17.3 LoTTE 100k cached cost-aware LinUCB rerun：
  - 复用已生成的 LoTTE 100k corpus/query embedding cache 重跑 cost-aware LinUCB：
    - command: `.venv/bin/python paper/experiments/scripts/linucb_cost_aware_routing.py --dataset lotte_technology_search_100k --query-split test --local-files-only --device cpu --batch-size 64 --top-k 10 --ks 1,5,10 --seeds 13 --epochs 1 --n-clusters 32 --context-dim 64 --candidate-arms 3 --dense-depth 100 --bm25-depth 100 --cluster-depth 100 --dense-lite-depth 20 --bm25-lite-depth 20 --feedback-k 16 --window-size 50`
    - metrics 标记：`embedding_cache_enabled=True`，`corpus_embedding_cache_hit=True`，`query_embedding_cache_hit=True`
  - 结果：
    - full_multi_route：Recall@10=`0.8725`，MRR@10=`0.7089`，nDCG@10=`0.6525`，last_reward=`0.3104`，avg_cost=`300.00`，dense_rate=`1.0000`，elapsed=`134.640s`
    - gated_cost_aware：Recall@10=`0.8356`，MRR@10=`0.6888`，nDCG@10=`0.6031`，last_reward=`0.3356`，avg_cost=`224.16`，dense_rate=`0.9530`，primary_rate=`0.0470`，elapsed=`266.344s`
  - 当前解释：
    - 与 pre-cache run 相比，retrieval metrics 保持一致，说明 cache 没改变实验语义。
    - full route elapsed 从 `1772.420s` 降到 `134.640s`，gated route elapsed 从 `1905.491s` 降到 `266.344s`，证明 embedding 重算是此前主要工程瓶颈之一。
    - cached rerun 后仍有百秒级成本，下一步如果扩展 seeds/epochs/full corpus，应优先复用 BM25 index、dense rankings、cluster labels 等非 embedding 中间产物。

- 2026-05-06 Task 17.4 shared large-scale runner / retrieval artifacts：
  - 新增 `paper/experiments/scripts/large_scale_artifacts.py`：
    - 统一缓存 dense top-depth rankings、BM25 top-depth rankings、PCA context + cluster labels/centroids。
    - artifact fingerprint 覆盖 dataset、model、corpus/query id+text fingerprint、depth、context_dim、n_clusters、seed 与 artifact 版本。
    - artifact 默认写入 `paper/experiments/data/retrieval_artifacts/`，该目录位于 git ignored data 下。
  - `linucb_cost_aware_routing.py` 已接入：
    - 新增 CLI：`--artifact-cache-dir`、`--no-artifact-cache`、`--force-artifact-cache`。
    - CLI 默认启用 artifact cache；直接调用 `run_dataset` 默认关闭，避免小单测或外部调用意外写大缓存。
    - metrics 新增：`artifact_cache_enabled`、`dense_ranking_cache_hit`、`bm25_ranking_cache_hit`、`context_cluster_cache_hits` 与 artifact path 字段。
  - LoTTE 小样本真实 CLI smoke：
    - 第一次生成 artifact：dense/BM25/context cache hit 均为 false。
    - 第二次同参数 rerun：`dense_ranking_cache_hit=True`，`bm25_ranking_cache_hit=True`，`context_cluster_cache_hits=[True]`，embedding cache 也命中。
  - LoTTE 100k shared artifact rerun：
    - 第一次 artifact-generating rerun：metrics 不变；full_multi_route elapsed=`110.931s`，gated_cost_aware elapsed=`117.796s`。
    - 第二次 artifact-cache-hit rerun：metrics 不变；full_multi_route elapsed=`7.392s`，gated_cost_aware elapsed=`14.080s`。
    - 当前 metrics 标记：`embedding_cache_enabled=True`，`corpus_embedding_cache_hit=True`，`query_embedding_cache_hit=True`，`artifact_cache_enabled=True`，`dense_ranking_cache_hit=True`，`bm25_ranking_cache_hit=True`，`context_cluster_cache_hits=[True]`。
  - 当前解释：
    - shared large-scale runner 不改变检索语义，只消除重复 dense ranking、BM25 ranking、PCA/context 与 KMeans cluster 构造。
    - Task17 后续可以更现实地扩展到 multiple seeds / epochs；full 638k corpus 仍需要谨慎，因为 artifact 体积和 BM25/index 构造成本会进一步上升。

- 2026-05-06 Task 17.5 shared artifact integration into baseline & diagnostics scripts：
  - 已接入 `dense_baseline.py`：
    - 新增 `large_scale_artifacts` 模块导入。
    - `run_dataset()` 新增 `artifact_cache_dir`、`use_artifact_cache`、`force_artifact_cache` 参数。
    - 当 `use_embedding_cache=True` 且 `use_artifact_cache=True` 时，通过 `load_or_compute_dense_rankings(depth=max(top_k, 100))` 获取缓存的 dense rankings，截断到 `top_k` 后评估。
    - metrics 输出新增 `artifact_cache_enabled`、`dense_ranking_cache_hit`、`dense_ranking_artifact_path`。
    - CLI 新增 `--artifact-cache-dir`、`--no-artifact-cache`、`--force-artifact-cache`。
  - 已接入 `hybrid_baseline.py`：
    - 新增 `large_scale_artifacts` 模块导入。
    - `run_dataset()` 新增三个 artifact 参数。
    - 当 artifact cache 启用时，同时加载 dense rankings 和 BM25 rankings，截断到 `fusion_depth` 后做 RRF 融合。
    - metrics 输出新增 `artifact_cache_enabled`、`dense_ranking_cache_hit`、`bm25_ranking_cache_hit`、`dense_ranking_artifact_path`、`bm25_ranking_artifact_path`。
    - CLI 新增三个 artifact 参数。
  - 已接入 `manifold_diagnostics.py`：
    - 新增 `large_scale_artifacts` 模块导入。
    - `run_dataset()` 新增三个 artifact 参数。
    - 当 artifact cache 启用时，通过 `load_or_compute_context_clusters()` 获取缓存的 PCA context、cluster labels、centroids。
    - `run_diagnostics()` 新增 `shared_context_artifacts` 可选参数，有值时跳过本地 PCA + KMeans 计算。
    - metrics 输出新增 `artifact_cache_enabled`、`context_cluster_cache_hit`、`context_cluster_artifact_path`。
    - CLI 新增三个 artifact 参数。
  - 新增测试 `cache/test_artifact_integration.py`：
    - 覆盖 dense_baseline、hybrid_baseline、manifold_diagnostics 三个脚本的 artifact cache 首次 miss + 二次 hit 场景。
    - 使用 toy data + tempdir，不依赖真实大规模数据。
    - 验证 cache hit 前后检索指标一致。
  - 已验证：
    - `py_compile` 语法检查通过：`dense_baseline.py`、`hybrid_baseline.py`、`manifold_diagnostics.py`、`test_artifact_integration.py`。
    - AST parse 通过。
    - CLI 参数命名与 `linucb_cost_aware_routing.py` 一致。
  - 本地复测与修正：
    - 初次运行发现 `dense_baseline -> large_scale_artifacts -> linucb_online_baseline -> dense_baseline` 循环导入；已将 `large_scale_artifacts.py` 改为自包含 PCA / MiniBatchKMeans / centroid 逻辑，避免反向依赖 LinUCB 脚本。
    - 修正 `cache/test_artifact_integration.py` 的 fake encoder，使其兼容 `SentenceTransformer.encode()` 的 `convert_to_numpy` 等 keyword 参数。
    - `.venv/bin/python -m unittest cache/test_artifact_integration.py cache/test_dense_baseline.py cache/test_hybrid_baseline.py cache/test_manifold_diagnostics.py cache/test_large_scale_artifacts.py` 通过：23 tests OK。
    - `py_compile` 与 `git diff --check` 通过。
  - LoTTE 100k 真实 smoke（输出写入 `/tmp/intentweight_task175_smoke/results`，不污染正式 results）：
    - dense artifact-hit rerun：Recall@10=`0.8674`，MRR@10=`0.7081`，nDCG@10=`0.6487`，elapsed=`0.433s`，`dense_ranking_cache_hit=True`。
    - hybrid artifact-hit rerun：Recall@10=`0.8624`，MRR@10=`0.6973`，nDCG@10=`0.6216`，elapsed=`0.541s`，`dense_ranking_cache_hit=True`，`bm25_ranking_cache_hit=True`。
    - manifold artifact-hit rerun：`nearest_cluster_hit@3=0.8809`，`context_gt_recall@10=0.7836`，elapsed=`6.668s`，`context_cluster_cache_hit=True`。

- 2026-05-06 后续任务规划记录：
  - 当前总判断：
    - 现有数据支持“方法成立但不是无条件替代 dense”的结论。
    - dense 仍应作为 recall floor / fallback；LinUCB 随反馈成熟后可逐步提高权重、降低 dense 深度或调用频率。
    - 后续重点不是证明单点全面超过 dense，而是系统性刻画 quality-cost trade-off、feedback self-evolution 与 conditional dense fallback。
  - Task 17.5：把 shared artifacts 接到更多分项实验。
    - 当前 shared artifacts 主路径已接入 `linucb_cost_aware_routing.py`。
    - 后续可接入 `dense_baseline.py`、`hybrid_baseline.py`、`manifold_diagnostics.py`，让 BM25/dense/hybrid/manifold/LinUCB 尽量共享同一套 ranking/context artifacts。
  - Task 18：LoTTE 100k 多 seed / 多 epoch 正式实验。
    - 目标配置优先考虑 `seeds=13,17,19`、`epochs=3`。
    - 重点验证 full multi-route 是否稳定高于 dense，gated cost-aware 是否能在可接受召回损失下显著降成本，以及 feedback reward 是否持续提升。
  - Task 19：dense / LinUCB 权重与阈值 ablation。
    - 重点调参：`dense_weight`、`cluster_primary_weight`、`dense_floor_k`、`dense_lite_depth`、`high_confidence_threshold`、`mid_confidence_threshold`、`drift_threshold`。
    - 目标是找 quality-cost Pareto frontier，而不是只追一个最高 Recall@10 单点。
  - Task 20：conditional dense fallback 实验。
    - 将 dense 从常驻主路逐步降级为条件兜底。
    - 触发条件可包括 LinUCB confidence 低、semantic drift 高、selected cluster 距 query 远、最近窗口 reward 下降、负反馈或 OOD query。
    - 这是最贴近“随着反馈增长降低 dense 比重、靠 LinUCB 主召回降成本”的实验。
  - Task 21：论文实验表格与论证整理。
    - 汇总 static baselines、manifold diagnostics、feedback self-evolution、cost-aware routing、LoTTE large-scale、failure/limitation cases。
    - 论文表述应强调成立条件、弱收益/失败条件、dense 不能简单替代的原因，以及 feedback-driven routing 的研究价值。
  - Task 22（可选）：LoTTE full corpus 扩展。
    - 只有当 100k 多 seed/ablation 结果足够稳，且论文需要更强 large-scale claim 时再做。
    - full `638509` corpus 的 artifact 体积、BM25/index 构造和结果文件规模都需要单独评估。
