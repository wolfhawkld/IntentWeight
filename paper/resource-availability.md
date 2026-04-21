# 资源可用性汇总：数据集与 Baseline 开源 / GPU 需求
# Resource Availability: Datasets & Baselines Open-Source / GPU Requirements

**创建时间 / Created**: 2026-04-21
**状态 / Status**: 已确认

---

## 一、数据集开源情况
## 1. Dataset Availability

### 标准基准数据集（领域特定）

| 数据集 | 规模 | 开源 | 来源 | 许可证 | 备注 |
|--------|------|------|------|--------|------|
| **eManual** | 中等 | 已开源 | [RAGBench (HuggingFace)](https://huggingface.co/datasets) | CC BY 4.0 | 产品手册，最接近企业知识库场景。同时被 HypRAG 和 RAGBench 使用 |
| **CUAD** | 510 合同, 13K+ 标注 | 已开源 | [HuggingFace: theatticusproject/cuad](https://huggingface.co/datasets/theatticusproject/cuad) | CC BY 4.0 | 法律合同，41 类条款标注。同时被 HypRAG 和 RAGBench 使用 |
| **PubMedQA** | 1K 标注 + 61.2K 未标注 + 211.3K 自动生成 | 已开源 | [HuggingFace: qiaojin/PubMedQA](https://huggingface.co/datasets/qiaojin/PubMedQA) | MIT | 生物医学 QA，替代 CovidQA（仅 124 pairs） |
| TechQA (可选) | 中等 | 已开源 | RAGBench 子集 | - | IBM 技术支持 QA |

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

### 硬件需求总结

| 任务 | GPU 类型 | 估计时间 | 备注 |
|------|---------|---------|------|
| 数据集 embedding 生成 (BGE-large) | A100 40GB 或 A800 | 半天 | eManual/CUAD/PubMedQA |
| DynamicRAG (SFT + DPO) | A100 40GB | 3-5 天 | **最耗时**，Llama3-8B 训练 |
| Online-Opt RAG 复现 | A100 40GB | 2-3 天 | 代码可能未开源，需评估 |
| FLAIR | A100 40GB 或 API | 1-2 天 | HyQE 生成 + 反馈循环 |
| CRAG / MBA-RAG | LLM API 即可 | 1-2 天 | 无需 GPU 训练 |
| RAGAS 评估 (LLM-as-judge) | LLM API | 1-2 天 | 需要 API 费用 |
| **合计** | **A100 40GB** | **约 1.5-2 周** | |

### 可在本地 GTX 1650 完成的工作

- BM25 / Hybrid baseline
- MBA-RAG（DistilBERT 部分）
- 我们的系统全部实验 + 消融实验
- 小规模 embedding 生成（小 batch size）

### 必须租用云 GPU 的工作

- DynamicRAG 训练（Llama3-8B SFT + DPO）
- Online-Opt RAG 复现
- FLAIR（如不使用 API）
- 大规模 embedding 生成

---

## 四、风险项
## 4. Risk Items

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| **Online-Opt RAG 代码未开源** | 无法复现，需自己实现 | 降级到 Related Work 讨论，或根据论文描述复现核心算法 |
| DynamicRAG 训练不稳定 | 耗时超预期 | 使用作者提供的 checkpoint 做 inference |
| RAGAS 评估 API 费用 | 大规模评估成本高 | 使用开源 LLM (Llama3) 替代 GPT-4 做 judge |
| 数据集预处理差异 | 与 HypRAG 结果不可比 | 尽量对齐 HypRAG 的 chunk 策略和 embedding 配置 |

---

*更新时间: 2026-04-21*
