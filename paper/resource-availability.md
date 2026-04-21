# 资源可用性汇总：数据集与 Baseline 开源 / GPU 需求
# Resource Availability: Datasets & Baselines Open-Source / GPU Requirements

**创建时间 / Created**: 2026-04-21
**状态 / Status**: 已确认

---

## 一、数据集开源情况
## 1. Dataset Availability

### 核心数据集

| 数据集 | 规模 | 开源 | 来源 | 许可证 | 备注 |
|--------|------|------|------|--------|------|
| **CUAD** | 510 合同, 13K+ 标注, 41 类 | 已开源 | [HuggingFace: theatticusproject/cuad](https://huggingface.co/datasets/theatticusproject/cuad) | CC BY 4.0 | 法律合同，检索级 GT（段落级标注） |
| **eManual** | 中等 | 已开源 | [RAGBench (HuggingFace)](https://huggingface.co/datasets) | CC BY 4.0 | 产品手册，检索级 GT（QA-chunk 映射） |
| **PubMedQA** | 1K 标注 + 61.2K 未标注 + 211.3K 自动生成 | 已开源 | [HuggingFace: qiaojin/PubMedQA](https://huggingface.co/datasets/qiaojin/PubMedQA) | MIT | 生物医学，规模大，MIRAGE 基准子集 |

### 补充数据集

| 数据集 | 规模 | 开源 | 来源 | 许可证 | 备注 |
|--------|------|------|------|--------|------|
| **BioASQ** | 4,721 问题, 40K+ 段落 | 已开源 | [BioASQ](http://www.bioasq.org/) | 注册获取 | 医学领域 GT 最完整（文档+snippet 双级标注） |
| **BANKING77** | 13,083 样本, 77 intent | 已开源 | [HuggingFace: PolyAI/banking77](https://huggingface.co/datasets/PolyAI/banking77) | Apache 2.0 | 已有 Phase 1B/1D 实验数据 |

### 已有数据集

| 数据集 | 规模 | 开源 | 来源 | 备注 |
|--------|------|------|------|------|
| **BANKING77** | 13,083 样本, 77 intent | 已开源 | [HuggingFace: PolyAI/banking77](https://huggingface.co/datasets/PolyAI/banking77) | 已有完整实验数据（Phase 1B/1D） |
| CLINC150 | 23,850 样本, 151 intent | 已开源 | [HuggingFace](https://huggingface.co/datasets) | 已有实验数据，待定是否用于论文 |
| SMP2019 (可选) | 2,579 样本, 48 intent | 公开 | SMP 竞赛 | 中文数据集，BGE 聚类纯度 88.4% |

### 数据集总结

所有候选数据集均已开源，可直接获取，无授权障碍。

---

## 二、Baseline 开源与 GPU 需求
## 2. Baseline Open-Source & GPU Requirements

### 第一档：静态检索（无 GPU 需求）

| Baseline | 开源 | 代码/库 | GPU 需求 | 估计工作量 |
|----------|------|---------|---------|-----------|
| **BM25** | 已开源 | [pyserini](https://github.com/castorini/pyserini) 或 rank_bm25 | 无 | 半天，几行代码 |
| **Dense (BGE-large)** | 已开源 | [sentence-transformers](https://github.com/UKPLab/sentence-transformers) | 推理可 CPU，生成 embedding 建议 GPU | 半天 |
| **Hybrid (BM25+Dense, RRF)** | 自己实现 | BM25 + Dense 分数融合 | 同 Dense | 半天，逻辑简单 |

### 第二档：自适应 RAG（需要 LLM API 或 GPU）

| Baseline | 开源 | 代码地址 | GPU 需求 | 估计工作量 |
|----------|------|---------|---------|-----------|
| **CRAG** | 已开源 | [HuskyInSalt/CRAG](https://github.com/HuskyInSalt/CRAG) | LLM API 即可（文档评估+重写） | 1-2 天，适配数据集 |
| **MBA-RAG** | 已开源 | [FUTUREEEEEE/MBA](https://github.com/FUTUREEEEEE/MBA) | DistilBERT (CPU 可) + LLM API | 1-2 天，适配数据集 |

### 第三档：在线学习 / 反馈驱动 RAG（需要 GPU）

| Baseline | 开源 | 代码地址 | GPU 需求 | 模型规模 | 估计工作量 |
|----------|------|---------|---------|---------|-----------|
| **DynamicRAG** | **已开源** | [GasolSun36/DynamicRAG](https://github.com/GasolSun36/DynamicRAG) | **需要 GPU** — Llama3-8B SFT + DPO 两阶段训练 | 8B 参数 | **3-5 天 A100** |
| **Online-Opt RAG** | **未确认** | arXiv:2509.20415 (ICLR 2026 投稿) | **需要 GPU** — 在线梯度更新 embedding | 取决于 embedding 模型 | 2-3 天（如需复现） |
| **FLAIR** | **已开源** | arXiv:2508.13390 (CIKM 2025) | **需要 GPU** — LLM 生成 hypothetical queries | LLM inference | 1-2 天 |

### 第四档：几何优化（可选，高 GPU 需求）

| Baseline | 开源 | 代码地址 | GPU 需求 | 估计工作量 |
|----------|------|---------|---------|-----------|
| HypRAG | 已开源 | [Graph-and-Geometric-Learning/HypRAG](https://github.com/Graph-and-Geometric-Learning/HypRAG) | **需要 GPU** — 训练双曲 embedding 模型 | 5+ 天 |

### 第五档：消融实验（无 GPU 需求）

| 配置 | 代码 | GPU 需求 | 估计工作量 |
|------|------|---------|-----------|
| Full System | `intent_weight/` | 无（LinUCB 全 CPU） | - |
| - 无聚类预筛选 | 关闭聚类模块 | 无 | 半天 |
| - 无在线学习 | 关闭 LinUCB，静态权重 | 无 | 半天 |
| - 无反馈融合 | 仅显式反馈 | 无 | 半天 |
| - 无信誉加权 | 关闭信誉模块 | 无 | 半天 |
| - 无冷启动先验 | 随机初始化 | 无 | 半天 |

---

## 三、GPU 资源规划
## 3. GPU Resource Planning

### 统一实验环境：A100 80GB

所有实验统一在 **NVIDIA A100 80GB** 上执行，确保结果可比性和可复现性。

A100 80GB 可完全覆盖所有实验需求：

| 任务 | 显存需求 | 在 A100 80GB 上 | 估计时间 |
|------|---------|----------------|---------|
| 数据集 embedding 生成 (BGE-large) | ~2-4 GB | 非常充裕 | 半天 |
| DynamicRAG (Llama3-8B SFT) | ~40-50 GB (full) / ~20 GB (QLoRA) | 充裕 | 2-3 天 |
| DynamicRAG (Llama3-8B DPO) | ~40-50 GB (full) / ~20 GB (QLoRA) | 充裕 | 1-2 天 |
| Online-Opt RAG 复现 | ~10-20 GB | 充裕 | 2-3 天 |
| FLAIR (HyQE 生成) | ~10-20 GB | 充裕 | 1-2 天 |
| CRAG / MBA-RAG | LLM API 即可 | 无需 GPU | 1-2 天 |
| RAGAS 评估 (LLM-as-judge) | LLM API 即可 | 无需 GPU | 1-2 天 |
| **合计** | | | **约 1.5-2 周** |

### 可在本地 GTX 1650 完成的工作

- BM25 / Hybrid baseline
- MBA-RAG（DistilBERT 部分）
- 我们的系统全部实验 + 消融实验
- 小规模 embedding 生成（小 batch size）

### 必须租用云 GPU (A100 80GB) 的工作

- DynamicRAG 训练（Llama3-8B SFT + DPO）
- Online-Opt RAG 复现
- FLAIR（如不使用 API）
- 大规模 embedding 生成

---

## 四、GPU 对实验结果的影响与控制
## 4. GPU Impact on Results & Controls

### 影响层面

| 层面 | 影响程度 | 说明 |
|------|---------|------|
| **训练** | 较大 | 显存 → batch size → 训练动态 → 最终 checkpoint 不完全一致 |
| | | 精度 (BF16/FP16/FP32) → 数值差异 |
| **推理** | 极小 | 同一 checkpoint 在不同 GPU 上推理结果基本一致 |

### 控制措施（论文中需报告）

| 措施 | 做法 | 论文中的表述 |
|------|------|-------------|
| GPU 一致性 | 所有 baseline + 我们的系统统一在 A100 80GB 上跑 | "All experiments are conducted on a single NVIDIA A100 80GB GPU" |
| 精度一致 | 统一 BF16（A100 原生支持） | "All models use BF16 precision" |
| 随机种子 | 固定 seed，报告 mean ± std（跑 3-5 次） | "Results averaged over 3 runs with seeds {42, 123, 456}" |
| 软件环境 | 统一 PyTorch 版本、CUDA 版本 | "PyTorch 2.x, CUDA 12.x" |

### 计算效率对比（论文实验的加分项）

这是我们方法的工程卖点之一 — 可在 Experiments 中增加一张 computational cost 对比表：

| 方法 | 训练阶段 | 推理硬件 | 推理延迟 | 显存占用 |
|------|---------|---------|---------|---------|
| DynamicRAG | A100 × 3-5 天 (Llama3-8B SFT+DPO) | GPU | 待测 | ~40 GB |
| Online-Opt RAG | A100 × 2-3 天 (梯度更新) | GPU | 待测 | ~10-20 GB |
| FLAIR | A100 × 1-2 天 (HyQE 生成) | GPU / API | 待测 | ~10-20 GB |
| MBA-RAG | DistilBERT 训练 | CPU + API | 待测 | ~1 GB |
| CRAG | 无训练 | CPU + API | 待测 | ~1 GB |
| **本方法** | **无训练** | **CPU** | 待测 | **< 1 GB** |

> **论文中可强调**："Our method requires no GPU for either training or inference,
> while achieving competitive or superior retrieval quality compared to methods
> that require multi-day GPU training on 8B-parameter models."

---

## 五、风险项
## 5. Risk Items

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| **Online-Opt RAG 代码未开源** | 无法复现，需自己实现 | 降级到 Related Work 讨论，或根据论文描述复现核心算法 |
| DynamicRAG 训练不稳定 | 耗时超预期 | 使用作者提供的 checkpoint 做 inference |
| RAGAS 评估 API 费用 | 大规模评估成本高 | 使用开源 LLM (Llama3) 替代 GPT-4 做 judge |
| 数据集预处理差异 | 与 HypRAG 结果不可比 | 尽量对齐 HypRAG 的 chunk 策略和 embedding 配置 |

---

*更新时间: 2026-04-21*
