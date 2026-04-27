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
- [ ] Task 5: 跑数据生成验证

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
