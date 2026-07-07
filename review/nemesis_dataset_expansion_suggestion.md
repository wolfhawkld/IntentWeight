# IntentWeight 数据集扩展建议

**作者**: Nemesis  
**日期**: 2026-07-01  
**目标**: 评估当前实验数据集的适配性，搜索并推荐更合适的开源数据集，提升论文的横向可比性与纵向深度

---

## 一、当前数据集格局评估

| 数据集 | 角色 | 来源 | 当前 Hit@10 | 问题 |
|---|---|---|---|---|
| LoTTE technology/search | 主 benchmark (4 scales) | LoTTE | 0.73–0.87 | ✅ 核心证据，无问题 |
| LoTTE science/search | 跨域验证 (2 scales) | LoTTE | 0.89–0.91 | ✅ 但只有 2 个 LoTTE 域，跨域说服力有限 |
| PubMedQA | feedback 适配 | RAGBench | 0.9930 | ❌ 近天花板，区分度极低，难以展示 feedback 增益 |
| Banking77 | intent routing proxy | pre-validation | 0.98 | ⚠️ 非 evidence retrieval，不能进同一性能表 |
| eManual | boundary case | RAGBench | 0.32→0.86 (dedup) | ⚠️ duplicate text 有诊断价值，但 corpus 小 (132 test queries) |
| CUAD | boundary case | RAGBench | 0.0759 | ❌ GT-anchored smoke，dense 基线极低，基本无区分度 |

**核心问题**：
1. LoTTE 只有 2 个域，cross-domain claim 偏弱
2. PubMedQA 天花板效应——0.9930 的 dense baseline 让 feedback 改善几乎不可测
3. CUAD 的 0.0759 太低，reviewer 会质疑"这个数据集到底证明了什么"
4. 缺少技术支持和金融垂类的覆盖

---

## 二、推荐扩展方案

按优先级排序，前 3 项为强烈建议。

### 优先级 1：加 LoTTE lifestyle/search + recreation/search

**数据集**：
- `lotte/lifestyle/dev/search` + `lotte/lifestyle/test/search`
- `lotte/recreation/dev/search` + `lotte/recreation/test/search`

**来源**: LoTTE (Stanford ColBERT) — https://github.com/stanford-futuredata/ColBERT/blob/main/LoTTE.md  
**HuggingFace**: https://huggingface.co/datasets/mteb/LoTTE  
**ir_datasets**: https://ir-datasets.com/lotte.html

**理由**：
- LoTTE 总共 5 个域（technology、science、lifestyle、recreation、writing），当前只用了 2 个
- 格式、corpus 结构、query 类型与现有 tech/search、sci/search **完全一致**
- 预处理 pipeline、embedding 生成、retrieval 评估代码**零修改复用**
- 跨域验证从 2 域扩展到 4 域，cross-domain transfer claim 强度直接翻倍

**建议协议**：
- 各跑 100k corpus scale（与 tech/search 100k 对齐）
- 最小公共协议：Dense/BM25/Hybrid/IntentRoute + top-k=10 + calibration/test + 3 seeds
- 如有计算资源，lifestyle/search 可扩展到 200k/400k

**工作量**: 极低。数据下载 + 现有 pipeline 运行，无新代码。

---

### 优先级 2：用 LegalBench-RAG 替代 CUAD

**数据集**: LegalBench-RAG  
**来源**: https://zeroentropy.dev/articles/legalbench-rag-the-first-open-source-retrieval-benchmark-for-the-legal-domain  
**规模**: 6,858 query-answer pairs，corpus 79M 字符，覆盖 NDA、M&A、商业合同、隐私政策  
**标注**: 人工标注 ground-truth retrieval span

**替代理由**：
- CUAD 当前问题：GT-anchored sampling → dense Hit@10=0.0759 → 基本无区分度
- CUAD 在论文中的角色是"sparse-GT boundary case"，但 0.0759 的 baseline 太低，reviewer 会质疑数据集本身是否有 retrieval 价值
- LegalBench-RAG 是**专门为 RAG retrieval 组件设计**的法律 benchmark（不同于 LegalBench 的 generation focus）
- 有完整 corpus + 人工标注 span → 可以做真正的 evidence retrieval 评估
- 规模远大于 CUAD 的 GT-anchored 100-query smoke

**建议协议**：
- Dense/BM25/Hybrid/IntentRoute + top-k=10 + calibration/test
- 标注为法律域 evidence-retrieval 证据，而非 boundary case
- 如 corpus 过大，可按 RAGBench 预处理方式分片

**工作量**: 中。需写预处理脚本（参考 `preprocess_cuad.py`），但数据集格式标准。

---

### 优先级 3：加 TechQA (RAGBench)

**数据集**: TechQA  
**来源**: RAGBench — https://huggingface.co/datasets/rungalileo/ragbench  
**原始来源**: IBM Research — https://research.ibm.com/publications/the-techqa-dataset  
**规模**: 801,998 Technotes (corpus), ~1.2k train / 302 dev / 310 test (RAGBench 版本)  
**域**: 技术支持（IT 论坛真实问题 + IBM Technote 文档）  
**doc length**: avg 1,800 tokens

**理由**：
- 技术支持是**典型垂类场景**——真实用户在论坛提的技术问题，不是合成 QA
- corpus 规模大（801K Technotes），能测试 routing 在大 corpus 下的行为
- 直接对齐论文的"vertical domain retrieval"主张
- RAGBench 格式，已有 `preprocess_pubmedqa.py` / `preprocess_emanual.py` / `preprocess_cuad.py` 可参考
- 可替代 CUAD 作为 boundary/supporting case，或作为独立的技术域 evidence

**建议协议**：
- 最小公共协议：Dense/BM25/Hybrid/IntentRoute + top-k=10 + calibration/test + 3 seeds
- 与 LoTTE technology/search 形成"技术检索 vs 技术支持 QA"的互补

**工作量**: 低。RAGBench 格式，预处理脚本已有参考。

---

### 优先级 4：用 CovidQA-RAG 替代或补充 PubMedQA

**数据集**: CovidQA-RAG  
**来源**: RAGBench — https://huggingface.co/datasets/rungalileo/ragbench  
**规模**: ~2.5k train / 534 dev / 492 test  
**域**: 生物医学（COVID-19 研究论文）  
**doc length**: avg 122 tokens  
**特点**: 多跳推理，多篇研究论文作为 context

**替代理由**：
- PubMedQA 的 dense Hit@10=0.9930 天花板效应严重——0.9930 → 0.9940 的改善几乎不可测
- CovidQA-RAG 的多跳推理 + 研究论文 corpus 提供更高的区分度
- 同属 RAGBench 生物医学域，可直接替换

**建议**：
- 可直接替代 PubMedQA，或两者并列（PubMedQA 作为 ceiling reference，CovidQA 作为 discriminative test）
- 如替代，最小公共协议同上

**工作量**: 低。RAGBench 格式。

---

### 优先级 5（可选）：加金融域 — FinQA 或 FiQA

**选项 A: FinQA (RAGBench)**
- 来源: RAGBench，财报文档，avg 310 tokens/doc
- 规模: ~12k train / 1.7k dev / 2.2k test
- 特点: 数值推理，混合表格+文本

**选项 B: FiQA (BEIR)**
- 来源: BEIR benchmark
- 规模: 57K docs corpus
- 特点: 金融 QA，独立于 RAGBench

**理由**：
- 增加金融垂类覆盖，让论文的"vertical domain"主张覆盖技术/科学/法律/医学/金融 5 个域
- 非必需，但如果有余力可以增强论文的领域广度

**建议**：二选一即可。FinQA 更方便（RAGBench 格式），FiQA corpus 更大。

**工作量**: 低（FinQA）/ 中（FiQA，需 BEIR 预处理）。

---

## 三、扩展后的数据集格局

完成优先级 1-4 后的数据集矩阵：

| 数据集 | 域 | 角色 | Corpus 规模 | 预期区分度 |
|---|---|---|---|---|
| LoTTE technology/search | 技术 | 主 benchmark (4 scales) | 100k–638k | ✅ 高 |
| LoTTE science/search | 科学 | 跨域验证 | 20k, 100k | ✅ 高 |
| LoTTE lifestyle/search | 生活 | 跨域验证 | 100k | ✅ 待测 |
| LoTTE recreation/search | 娱乐 | 跨域验证 | 100k | ✅ 待测 |
| TechQA | 技术支持 | 垂类 evidence | 801K technotes | ✅ 待测 |
| LegalBench-RAG | 法律 | 垂类 evidence (替代 CUAD) | 79M chars | ✅ 高（人工标注 span） |
| CovidQA-RAG | 生物医学 | feedback 适配 (替代 PubMedQA) | 研究论文 | ✅ 中高（多跳） |
| eManual | 客服 | boundary case (dedup) | 18K chunks | ⚠️ 低（但 dedup 诊断有价值） |
| Banking77 | 银行 | intent routing (独立表) | 13K intents | ⚠️ 非 evidence retrieval |

**对比当前格局的改善**：
- 跨域验证：2 域 → 4 域
- 法律域：从 0.0759 无区分度的 smoke → 有完整 corpus + 人工标注的 retrieval benchmark
- 医学域：从 0.9930 天花板 → 多跳推理有区分度
- 技术支持域：新增 801K corpus 的垂类 evidence
- 横向可比性：4 个 LoTTE 域 + 3 个 RAGBench/独立垂类，可以用最小公共协议形成统一性能表

---

## 四、不推荐的数据集

| 数据集 | 原因 |
|---|---|
| HotpotQA (RAGBench/BEIR) | 通用知识域（Wikipedia），非垂类 |
| MS Marco (RAGBench/BEIR) | 通用 web 搜索，非垂类 |
| HAGRID (RAGBench) | 通用知识域，非垂类 |
| ExpertQA (RAGBench) | 通用搜索，非垂类 |
| DelucionQA (RAGBench) | 客服域，和 eManual 太像，重复 |
| SciFact (BEIR) | 科学域但 corpus 太小 (5.2K)，已有 LoTTE science |
| MIRAGE | 偏向 generator 评测，不是纯 retrieval benchmark |
| NFCorpus (BEIR) | 医学域但太小 (3.6K docs)，PubMedQA/CovidQA 已覆盖 |

---

## 五、执行建议

### 阶段一：零成本扩展（优先级 1）
1. 下载 LoTTE lifestyle/search 和 recreation/search 数据
2. 用现有 pipeline 跑 100k 最小公共协议
3. 加入跨域性能表

### 阶段二：RAGBench 内扩展（优先级 3、4）
1. 下载 TechQA 和 CovidQA-RAG（RAGBench 格式）
2. 参考 `preprocess_emanual.py` 写预处理脚本
3. 跑最小公共协议

### 阶段三：CUAD 替换（优先级 2）
1. 下载 LegalBench-RAG
2. 写预处理脚本（参考 `preprocess_cuad.py`）
3. 跑最小公共协议
4. 论文中用 LegalBench-RAG 结果替换 CUAD

### 阶段四（可选）：金融域（优先级 5）
1. 下载 FinQA（RAGBench 格式）
2. 预处理 + 最小公共协议

---

## 六、数据集来源索引

| 数据集 | 链接 |
|---|---|
| LoTTE (全部 5 域) | https://github.com/stanford-futuredata/ColBERT/blob/main/LoTTE.md |
| LoTTE (HuggingFace) | https://huggingface.co/datasets/mteb/LoTTE |
| LoTTE (ir_datasets) | https://ir-datasets.com/lotte.html |
| RAGBench (12 子集) | https://huggingface.co/datasets/rungalileo/ragbench |
| RAGBench 论文 | https://arxiv.org/abs/2407.11005 |
| LegalBench-RAG | https://zeroentropy.dev/articles/legalbench-rag-the-first-open-source-retrieval-benchmark-for-the-legal-domain |
| TechQA (原始) | https://research.ibm.com/publications/the-techqa-dataset |
| TechQA (ACL 2020) | https://aclanthology.org/2020.acl-main.117.pdf |
| FiQA (BEIR) | https://github.com/beir-cellar/beir |
| BEIR 论文 | https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/65b9eea6e1cc6bb9f0cd2a47751a186f-Paper-round2.pdf |

---

*本建议基于 2026-07-01 的项目状态和公开数据集信息。执行前建议 Codex 先确认各数据集的 license 兼容性和具体下载方式。*
