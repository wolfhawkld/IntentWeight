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
- [ ] Task 9.5: 修正实验协议与评估口径 guardrails
- [ ] Task 10: 汇总 BM25 / dense / hybrid baseline 对比表
- [ ] Task 11: 设计并运行 LinUCB baseline / ablation 实验
- [ ] Task 12: 实现流形局部反馈机制（FAISS/HNSW 邻域检索 + 距离加权反馈）
- [ ] Task 13: 对比全局 LinUCB 与流形局部反馈效果
- [ ] Task 14: 整理论文实验表格、结论和局限性

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

状态：文档协议已确认，代码 guardrails 尚未实现。

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
2. 给 baseline 脚本或汇总脚本增加 split/sample metadata guardrails。
3. 重新生成或重新标注 retrieval baseline comparison 数据。
4. 再进入 Task 10 主表汇总。

### Task 10: Baseline 对比汇总表

目标：把 BM25、dense、hybrid 的结果统一成论文可用的表格。

预计输出：

- `paper/experiments/results/retrieval_baseline_comparison.csv`
- 可选 Markdown 表格，写入本文档或实验说明文档。

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

### Task 11: LinUCB baseline / ablation 实验

目标：在已有 retrieval baseline 基础上，验证当前代码中的全局 LinUCB 反馈策略。

注意：当前 `intent_weight/linucb.py` 仍是全局 arm 更新，尚未实现最新设计文档中的流形局部反馈。

### Task 12: 流形局部反馈实现

目标：根据 `paper/feedback-simulation.md` 实现局部反馈机制。

核心方向：

- 使用 FAISS/HNSW 做 query/chunk/cluster 邻域检索；
- 历史反馈按 embedding 距离加权；
- 单 cluster 反馈向邻近 cluster 衰减传播；
- 多轮对话内按 query embedding 距离做 feedback attention；
- 用户信誉从全局扩展到局部/领域信誉。

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
- Task 9.5 已启动：实验协议与评估口径修正
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
  - 下一步：根据剩余 quota/时间决定是否继续进入代码实现和测试。
