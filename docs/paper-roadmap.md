# 论文发表规划（更新版）
# Paper Publication Roadmap (Updated)

**创建时间 / Created**: 2026-03-29
**更新时间 / Updated**: 2026-04-20
**项目 / Project**: IntentWeight
**状态 / Status**: 合并为一篇论文，理论框架已确立

---

## 策略变更：两篇 → 一篇
## Strategy Change: Two Papers → One Paper

### 变更原因

原规划两篇论文（意图检索 + 自进化 Agent）重叠度高 — 聚类、意图识别、检索评估在两篇中都是核心角色。拆分后各自贡献不够集中，且静态流形验证缺乏独立新意。

**合并为一篇完整的 system paper**：理论基础（流形假说）和工程实现（在线学习）是不可拆分的完整故事。

### 核心叙事线

```
流形假说（理论基础，简要交代）
    ↓ 因为垂类知识数据存在流形结构，所以
语义聚类有效（发现流形上的密度结构）
    ↓ 但静态聚类不够，因为
不同 query 在流形上的最优检索路径不同
    ↓ 所以需要
LinUCB 在线学习导航策略（核心贡献）
    ↓ 导航策略的优化依赖于
多维反馈信号融合（显式 + 隐式 + 上下文）
    ↓ 反馈质量由
用户信誉评分保障（防投毒 + 可信度加权）
    ↓ 反馈中的领域知识通过
Insight 提取沉淀（别名 / 纠正 / 知识缺口）
    ↓ 最终实现
持续自进化的 RAG Agent（工程落地 + 实验验证）
```

---

## 论文概要
## Paper Overview

### 标题方向

**"Self-Evolving RAG Agent: Continuous Retrieval Optimization via Contextual Bandits on Semantic Manifolds"**

**"基于语义流形在线导航的自进化 RAG Agent"**

### 核心理论概念：动态价值流形 (Dynamic Value Manifold)

> 在固定的几何流形 M 上叠加一个随用户交互持续演化的价值分布场 V(x, t)，
> 形成增强流形 M* = (M, V)。检索优化的本质是学习 V 的参数。

```
M  = 固定几何流形（embedding 空间）
V(x, t) = 价值场（流形上每个点的检索价值密度，随反馈动态演化）
M* = (M, V) = 动态价值流形
LinUCB 学习的就是 V 的参数化表示：V(x, t) ≈ θ(t)ᵀ φ(x)
```

与学术前沿的差异化定位：
- 前沿（HypRAG/GSS/GNN-RAG）：优化 M（改变几何空间）→ 静态模型
- **本文**：优化 V（在固定流形上学习价值场）→ 动态在线学习

### 核心贡献

1. **理论贡献**：提出动态价值流形 (DVM) 概念 — 首次将流形假说与 RAG 在线优化建立显式连接
2. **方法贡献**：增强流形导航框架 — LinUCB Contextual Bandit + 多维反馈融合 + 用户信誉防投毒 + Insight 知识沉淀
3. **系统贡献**：完整的自进化 RAG Agent 实现 — ReAct 决策 + 聚类预筛选 + 查询扩展 + 冷启动机制
4. **实验贡献**：多数据集验证 + 企业真实场景端到端部署

---

## 论文结构
## Paper Structure

| 章节 | 内容 | 篇幅 |
|------|------|------|
| 1. Introduction | 企业知识库挑战 + 流形假说动机 + DVM 概念 + 本文贡献 | 1 页 |
| 2. Related Work | RAG 优化、Contextual Bandits in IR、流形几何方法(HypRAG/GSS)对比 | 1 页 |
| 3. Preliminaries | 流形假说 + LinUCB 算法 + 问题定义 | 1 页 |
| 4. Method | **核心**：DVM 形式化 + 聚类发现 + Bandit 导航 + 反馈融合 + 信誉评分 + Insight 沉淀 | 3 页 |
| 5. System | ReAct Agent 架构 + 工程实现 + 部署 | 1 页 |
| 6. Experiments | 多数据集验证 + 消融实验 + 企业场景端到端 | 2 页 |
| 7. Conclusion | 总结 + 局限性 + 未来工作 | 0.5 页 |

---

## 实验设计
## Experiment Design

### 6.1 聚类质量验证（Phase 1B 数据）

| 数据集 | 语言 | 样本数 | 指标 |
|--------|------|--------|------|
| BANKING77 | 英文 | 13,083 | 聚类纯度、单类型聚类比 |
| CLINC150 | 英文 | 23,850 | 同上 |
| DailyDialog | 英文 | 11,499 | 同上 |
| CMID (医疗) | 中文 | 12,254 | 同上 |
| **JQ 企业数据** | 中文 | 2,623 chunks | PCA 方差保留率、聚类纯度 |

### 6.2 LinUCB 检索优化（Phase 1C/1D 数据 + 新增）

| 实验 | 对比 | 指标 |
|------|------|------|
| LinUCB vs 基线 RAG | 无聚类预筛选 vs 有 | Top-1/5 准确率、搜索空间缩减 |
| LinUCB vs Thompson Sampling | 探索策略对比 | 准确率、平均 reward |
| LinUCB vs ε-greedy | 同上 | 同上 |
| 冷启动先验 vs 随机初始化 | 有/无关键词先验 | 冷启动准确率 |
| LLM 热启动 vs 无热启动 | 有/无伪反馈注入 | 初始 effective_α、收敛速度 |

### 6.3 反馈融合消融实验（新增）

| 实验 | 配置 | 指标 |
|------|------|------|
| 仅显式反馈 | like/dislike only | reward 质量、LinUCB 收敛 |
| 显式 + 隐式融合 | 75%/25% 融合 | 同上 |
| + 上下文奖励 | 追问关键词分析 | 同上 |
| + 用户信誉加权 | 三方案协同 | 防投毒效果、异常用户检测率 |
| 完整系统 | 全部组件 | 端到端准确率和满意度 |

### 6.4 探索衰减实验（新增）

| 实验 | α 策略 | 指标 |
|------|--------|------|
| 固定 α=1.0 | 无衰减 | 收敛速度、稳态准确率 |
| 衰减 α (decay=0.01, min=0.3) | 本文方案 | 同上 |
| 固定 α=0.3 | 纯利用 | 同上 |

### 6.5 企业场景端到端验证（新增）

基于 jq_kg_base 真实部署：

| 指标 | 结果 |
|------|------|
| 文档数 | 110 docs, 2623 chunks |
| 聚类数 | 15 (Azure) / 16 (腾讯) |
| PCA 方差保留 | 99.1% |
| 知识查询耗时 | ~14s (优化前 60s) |
| 闲聊耗时 | ~2.7s |
| 反馈闭环 | 验证通过（105 次反馈，权重变化可观测） |
| 别名提取 | 验证通过（LC RD → 液晶研发部门） |

---

## 目标会议/期刊
## Target Venues

| 目标 | 适合原因 | 优先级 |
|------|---------|--------|
| **AAAI** | 系统+方法+RL，综合性强 | ⭐⭐⭐ |
| **SIGIR** | 信息检索顶会，RAG 优化直接相关 | ⭐⭐⭐ |
| **ACL (System Demo)** | 完整系统实现，有 demo | ⭐⭐ |
| **CIKM** | 知识管理，企业应用场景匹配 | ⭐⭐ |

---

## 已有验证基础（来自 IntentWeight + jq_kg_base）
## Existing Validation Base

### IntentWeight 研究验证（Phase 1A-1F）

| Phase | 验证内容 | 状态 | 可用于论文 |
|-------|---------|------|----------|
| 1A | Speech Act 5 类分类 (94% 准确率) | ✅ | Related Work 参考 |
| 1B | 4 数据集聚类质量 (72-92% 纯度) | ✅ | **实验 6.1** |
| 1C | LinUCB vs Thompson vs ε-greedy | ✅ | **实验 6.2** |
| 1D | 意图-聚类关联 (BANKING77 +5.8%) | ✅ | **实验 6.2** |
| 1E | 交互反馈闭环 | ✅ | 方法验证 |
| 1F | 关键词冷启动先验 (99% vs 2.5%) | ✅ | **实验 6.2** |

### jq_kg_base 工程验证

| 验证内容 | 状态 | 可用于论文 |
|---------|------|----------|
| ReAct Agent 3-tool 决策 | ✅ E2E 5/5 通过 | **系统章节** |
| LinUCB 聚类预筛选 | ✅ 15 clusters | **实验 6.5** |
| 反馈融合 (显式+隐式+上下文) | ✅ reward 加权验证 | **实验 6.3** |
| 用户信誉 3 方案 | ✅ 信誉分变化可观测 | **实验 6.3** |
| 探索衰减 | ✅ α 1.0→0.526 | **实验 6.4** |
| 别名提取 + 查询扩展 | ✅ LC RD 验证 | **系统章节** |
| BM25 预热优化 | ✅ 60s→14s | **系统章节** |
| 双平台部署 (Azure/腾讯) | ✅ 均验证通过 | 可移植性证明 |

---

## 关键依赖更新
## Updated Dependencies

| 依赖项 | 原状态 | 当前状态 |
|-------|--------|---------|
| Speech Act 分类器 | ✅ | ✅ (作为 Related Work 参考) |
| 语义聚类 (HDBSCAN) | ✅ | ✅ (4 数据集 + 企业数据) |
| LinUCB 算法 | ✅ | ✅ (含探索衰减 + 丰富 State) |
| 反馈信号融合 | ✅ | ✅ (显式+隐式融合，v2) |
| ReAct Agent | ⏳ | ✅ (jq_kg_base 已实现) |
| 用户信誉防投毒 | ⏳ | ✅ (3 方案协同) |
| Insight 提取 | ⏳ | ✅ (规则+LLM 批量) |
| 冷启动 + 热启动 | ✅ | ✅ (关键词先验 + LLM 伪查询) |
| DVM 理论框架 | 无 | ✅ (新增核心理论贡献) |
| 企业场景端到端验证 | 无 | ✅ (jq_kg_base 部署) |

---

## 发表时间线
## Timeline

| 时间 | 目标 |
|------|------|
| 2026 Q2 | 补充实验：消融实验 + 探索衰减实验 + 多用户信誉验证 |
| 2026 Q3 | 论文初稿完成 |
| 2026 Q3-Q4 | 投稿 AAAI / SIGIR |

---

## 参考文档
## Reference Documents

### IntentWeight 项目
- `./system-architecture.md` — 系统架构
- `./phase-1f-architecture-summary.md` — Phase 1F 最终架构
- `./analysis-linucb-convergence.md` — LinUCB 收敛性分析
- `../VERIFIED_FACTS.md` — 验证后事实结论

### jq_kg_base 工程验证（新增）
- `./theory-manifold-hypothesis-rag.md` — **DVM 理论框架**
- `./analysis-manifold-rag-comparison.md` — 前沿研究对比
- `./system-linucb-specification-v0.9.2.md` — 系统完整规格
- `./analysis-rl-feedback-strategy.md` — 反馈策略详细设计
- `./vision-self-evolving-agent.md` — 项目愿景

### 外部调研
- `~/clawteam-projects/manifold-rag-research/` — 流形+RAG SOTA 调研
- `~/clawteam-projects/rl-optimization-analysis/` — RL 优化分析

---

*更新时间: 2026-04-20*
*作者: Damon Long*
