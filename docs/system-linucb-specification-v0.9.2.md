# LinUCB 系统技术规格说明
# LinUCB System Technical Specification

**版本 / Version**: v0.9.2-dev
**分支 / Branch**: LinUCB
**最后更新 / Last Updated**: 2026-04-17

---

## 一、系统架构总览
## 1. System Architecture Overview

```
                              ┌─────────────────┐
                              │   用户浏览器     │
                              │ (登录 → 聊天)   │
                              └────────┬────────┘
                                       │ HTTPS
                              ┌────────▼────────┐
                              │  Next.js 前端    │
                              │  (Port 3000)     │
                              │  - 登录页        │
                              │  - 聊天 UI       │
                              │  - 反馈按钮      │
                              │  - 隐式行为采集  │
                              └────────┬────────┘
                                       │ REST/SSE
                              ┌────────▼────────┐
                              │  RAG Service     │
                              │  (Port 8004)     │
                              └────────┬────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
        ┌────────▼──────┐   ┌─────────▼────────┐   ┌───────▼────────┐
        │  ReAct Agent  │   │  IntentWeight    │   │  Hybrid Search │
        │  (决策引擎)    │   │  (LinUCB 优化)   │   │  (BM25+向量)   │
        └───────────────┘   └──────────────────┘   └────────────────┘
                 │                     │                     │
        ┌────────▼──────┐   ┌─────────▼────────┐   ┌───────▼────────┐
        │  LLM Client   │   │  用户信誉评分    │   │  ChromaDB      │
        │  (Azure/腾讯) │   │  (3方案协同)     │   │  (向量库)      │
        └───────────────┘   └──────────────────┘   └────────────────┘
                                       │
                              ┌────────▼────────┐
                              │  对话存储 +      │
                              │  Insight 提取    │
                              │  (SQLite)        │
                              └─────────────────┘
```

---

## 二、完整问答流程
## 2. Complete Q&A Flow

### 2.1 数据构建阶段（离线）

```
原始文档 (PDF/PPTX/DOCX/XLSX...)
    │
    ▼ Data Parser (Port 8003, Azure Mistral OCR / Qwen VL)
    │
Markdown 文件 (poc_output/)
    │
    ▼ index_documents.py (文档分块 + embedding + 入库)
    │
ChromaDB 向量库 (documents_azure / documents_tencent)
    │
    ▼ build_clusters.py (文件级聚类 + PCA + 冷启动先验)
    │
IntentWeight 数据 (data/intent_weight/{platform}/)
    │
    ▼ warmstart_linucb.py (可选：LLM 合成伪查询注入)
    │
LinUCB 就绪
```

### 2.2 在线问答阶段

```
用户登录 (user_id + password)
    │
    ▼ 用户输入查询
    │
Step 0: 上下文奖励推断
    │  分析当前 query 中的关键词
    │  深入关键词 → +0.5 (对上一轮正面评价)
    │  转向关键词 → -0.5 (对上一轮负面评价)
    │  如有上一轮 message_id → 自动更新 LinUCB
    │
Step 1: ReAct Agent 决策 (LLM 调用, ~2-3s)
    │  ├─ search_knowledge_base(query) → 需要文档支持的问题
    │  ├─ direct_answer(answer) → 打招呼/闲聊/感谢
    │  └─ refine_search(query) → 用户纠正上一轮回答 → 同时提取别名
    │
Step 2: 查询扩展
    │  aliases.json 中查找同义词
    │  例: "LC RD" → "LC RD 液晶研发部门"
    │
Step 3: LinUCB 聚类预筛选
    │  query embedding → PCA 降维 → 丰富特征构建 → UCB 分数计算
    │  选 top-3 聚类 → 获取聚类内文档列表 → ChromaDB where 过滤
    │
Step 4: 混合检索
    │  ├─ 向量检索 (ChromaDB, cosine similarity)
    │  ├─ BM25 检索 (关键词匹配, jieba 中文分词)
    │  └─ RRF 融合 (Reciprocal Rank Fusion, k=60)
    │  → top-5 检索结果
    │
Step 5: LLM 流式生成
    │  检索结果 + 对话历史 → LLM 生成回答 (SSE 流式)
    │
Step 6: 用户反馈收集
    │  ├─ 显式: 👍/👎 按钮点击
    │  ├─ 隐式: dwell_time / copy_action (自动采集)
    │  └─ 上下文: 下一条消息的关键词分析
    │
Step 7: LinUCB 权重更新
    │  raw_reward → 用户信誉加权 → LinUCB update(arm, context, reward)
    │
Step 8: 持久化
       ├─ 对话 → SQLite (conversations.db)
       ├─ LinUCB 状态 → linucb_state.json
       ├─ 用户信誉 → user_credibility.db
       └─ 别名 → aliases.json
```

---

## 三、LinUCB 参数规格
## 3. LinUCB Parameter Specification

### 3.1 核心算法

```
UCB_score = θᵀx + α(t) × √(xᵀA⁻¹x)

θ = A⁻¹b                          # 权重向量估计
A ← A + xxᵀ                       # 协方差矩阵更新
b ← b + r × x                     # 奖励累积向量更新
α(t) = max(α_min, α₀ / (1 + decay × total_feedback))  # 探索衰减
```

### 3.2 参数设置

| 参数 | 值 | 说明 |
|------|-----|------|
| `n_arms` | 15~16 | 文件级聚类数量（HDBSCAN 自动确定） |
| `context_dim` | 94 | 64 (PCA) + 15 (arm_rewards) + 15 (arm_ratios) |
| `alpha` | 1.0 | 初始探索参数 |
| `alpha_decay` | 0.01 | 探索衰减率 |
| `alpha_min` | 0.3 | 最小探索参数（防止停止探索） |
| `top_k_clusters` | 3 | 每次选择的目标聚类数量 |

### 3.3 PCA 降维

| 参数 | 值 | 说明 |
|------|-----|------|
| `n_components` | 64 | 降维目标维度 |
| Azure 输入维度 | 3072 | text-embedding-3-large |
| 腾讯输入维度 | 4096 | 腾讯云 embedding |
| 解释方差比 | 99.1% | 几乎无信息损失 |

### 3.4 HDBSCAN 聚类

| 参数 | 值 | 说明 |
|------|-----|------|
| `min_cluster_size` | 3 | 最小聚类文档数 |
| `min_samples` | 2 | 核心点最小邻居数 |
| `metric` | euclidean | 距离度量 |
| `cluster_selection_method` | eom | Excess of Mass |
| 噪声点处理 | 分配到最近聚类 | 不丢弃任何文档 |

### 3.5 丰富 State 特征

```
context = [query_embedding_pca, arm_rewards, arm_ratios]

query_embedding_pca:  64 维  # query 的 PCA 降维表征
arm_rewards:          15 维  # 各聚类的历史平均 reward
arm_ratios:           15 维  # 各聚类的被选择频率
─────────────────────────────
合计:                 94 维
```

---

## 四、奖励计算规格
## 4. Reward Calculation Specification

### 4.1 显式反馈基础分

| 反馈类型 | 基础分 | 触发方式 |
|---------|--------|---------|
| `like` | 1.0 | 用户点击 👍 |
| `dislike` | 0.0 | 用户点击 👎 |
| `correct` | 0.7 | 用户提交修正 |

### 4.2 隐式信号分数

| 信号 | 条件 | 权重 |
|------|------|------|
| copy_action | 用户复制了回答内容 | +0.15 |
| dwell_time | 10s < 停留 < 60s | +0.05 |
| scroll_depth | 滚动超过 70% | +0.05 |

隐式分数最大值：0.25

### 4.3 显式+隐式融合公式

```
融合权重：EXPLICIT_WEIGHT = 0.75, IMPLICIT_WEIGHT = 0.25

场景 1: 有显式 + 有隐式 → 加权融合
  reward = explicit_score × 0.75 + (0.5 + implicit_adjust) × 0.25

场景 2: 有显式 + 无隐式 → 直接使用显式分数
  reward = explicit_score

场景 3: 无显式 + 有隐式 → 隐式推断
  reward = 0.5 + implicit_adjust

场景 4: 无反馈 → 中性
  reward = 0.5
```

### 4.4 融合效果示例

| 显式 | 隐式行为 | 融合 reward | 说明 |
|------|---------|------------|------|
| like (1.0) | 复制+长停留+深滚动 | **0.94** | 最强正信号 |
| like (1.0) | 复制+长停留 | **0.92** | 强正信号 |
| like (1.0) | 无隐式 | **1.00** | 纯显式 |
| like (1.0) | 3s 跳过 | **0.88** | 显式正面但参与度低 |
| dislike (0.0) | 有复制行为 | **0.16** | 矛盾信号，隐式拉高 |
| dislike (0.0) | 无隐式 | **0.00** | 最强负信号 |
| correct (0.7) | 复制+长停留 | **0.70** | 修正+深度参与 |
| 无 | 复制+长停留 | **0.70** | 纯隐式正面 |
| 无 | 3s 跳过 | **0.50** | 中性 |

### 4.5 各反馈维度的完整流向

| 反馈维度 | LinUCB reward | 用户信誉 | 作用方式 |
|---------|:---:|:---:|------|
| 显式 (like/dislike) | 融合主导 (75%) | 方案 2 偏差检测 | 决定 reward 基础方向 |
| 隐式 (dwell/copy/scroll) | 融合微调 (25%) | 方案 3 矛盾检测 | 调整 reward 精度 + 验证显式真实性 |
| 上下文关键词 | 独立注入 (reward_override) | 不参与 | 追问/纠正 → 对上一轮的评价 |
| 信誉加权 | 缩放最终 reward | 自身更新 | 低信誉用户影响被抑制 |

### 4.6 上下文追问奖励

分析当前 query 中的关键词，推断对**上一轮**回答的满意度：

| 关键词类型 | 示例 | context_score | 映射 reward |
|-----------|------|--------------|------------|
| 深入关键词 | "详细"、"展开"、"还有"、"补充" | +0.5 | 1.0 |
| 转向关键词 | "不对"、"不是"、"错了"、"换个" | -0.5 | 0.0 |
| 澄清关键词 | "什么意思"、"没明白"、"不懂" | -0.2 | 0.3 |
| 无匹配 | | 0.0 | 不触发更新 |

映射公式：`reward = 0.5 + context_score`

---

## 五、用户信誉评分规格
## 5. User Credibility Scoring Specification

### 5.1 评分模型

```python
score_new = score_old + α × (target - score_old)

α = 1.0 / (feedback_count + 10)              # 衰减学习率
target = feedback_aligned × 0.7 + engagement_depth × 0.3  # 目标值
score ∈ [0.1, 1.0]                            # 输出范围
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 初始分数 | 0.5 | 新用户中性 |
| 下限 | 0.1 | 不完全忽略任何用户 |
| 上限 | 1.0 | 最高可信度 |
| 学习率基数 | 10 | `count + 10` 做分母，早期快速调整 |

### 5.2 feedback_aligned 三方案判定

**方案 1: 多用户共识（基础累积）**
- 默认 `feedback_aligned = True`
- 通过 `consistency_rate = positive / total` 累积一致性
- 后续可扩展为跨用户对同一内容的反馈比对

**方案 2: LinUCB 预期偏差检测**
```
expected_reward = LinUCB 对该 query 最优 arm 的历史平均 reward
actual_reward = 用户反馈计算的 reward

if |actual - expected| > 0.4:
    feedback_aligned = False  # 用户反馈与系统预期不一致
```

**方案 3: 隐式信号交叉验证**

| 矛盾场景 | 判定 | engagement_depth |
|---------|------|-----------------|
| 点赞但 dwell_time < 3s（没看就点） | aligned=False | 0.2 |
| 点踩但有 copy_action（觉得有用但点踩） | aligned=False | 0.3 |
| 有显式反馈 | aligned 由方案 2 决定 | 0.8 |
| 仅隐式信号 | aligned=True | 0.3 |

### 5.3 信誉加权应用

```python
effective_reward = 0.5 + (raw_reward - 0.5) × credibility

# 示例：
# credibility=1.0: like(1.0) → effective_reward=1.0（全权重）
# credibility=0.5: like(1.0) → effective_reward=0.75（减半影响）
# credibility=0.1: like(1.0) → effective_reward=0.55（几乎中性）
```

---

## 六、ReAct Agent 规格
## 6. ReAct Agent Specification

### 6.1 Tool 定义

| Tool | 用途 | 触发条件 |
|------|------|---------|
| `search_knowledge_base(query)` | 搜索知识库文档 | 需要文档支持的问题 |
| `direct_answer(answer)` | 直接回答 | 打招呼/闲聊/感谢 |
| `refine_search(query)` | 纠正后重新检索 | 用户指出上轮回答有误 |

### 6.2 Agent LLM 调用参数

| 参数 | 值 | 说明 |
|------|-----|------|
| max_tokens | 256 | 决策输出短，不需要长文本 |
| temperature | 0.3 | 低温度，稳定决策 |
| chat_history | 最近 6 条 | 3 轮对话上下文 |
| max_steps | 3 | 最大推理步数 |

### 6.3 SSE 事件格式

```
data: {"type": "message_id", "data": "uuid"}           # 反馈关联用
data: {"type": "agent_action", "data": {"action": "...", "input": "..."}}  # Agent 决策
data: {"type": "sources", "data": [{file_name, section, similarity}]}      # 检索来源
data: {"type": "content", "data": "回答文本片段"}        # 流式内容（多条）
data: [DONE]                                             # 结束标记
```

---

## 七、数据存储规格
## 7. Data Storage Specification

### 7.1 按 platform 隔离

```
data/intent_weight/
├── aliases.json              # 共享 — 别名字典
├── azure/                    # Azure 专用 (embedding 3072d)
│   ├── pca_model.pkl         # PCA 模型
│   ├── clusters.json         # 聚类数据
│   ├── linucb_state.json     # LinUCB A/b 矩阵 + 统计
│   └── cold_start_priors.json # 冷启动先验权重
└── tencent/                  # 腾讯专用 (embedding 4096d)
    ├── pca_model.pkl
    ├── clusters.json
    ├── linucb_state.json
    └── cold_start_priors.json

data/conversations.db          # 共享 — 对话历史 (SQLite)
data/user_credibility.db       # 共享 — 用户信誉 (SQLite)
data/vector_db/                # ChromaDB 向量库
    ├── documents_azure        # Azure collection (3072d)
    └── documents_tencent      # 腾讯 collection (4096d)
```

### 7.2 conversations 表结构

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_id TEXT,
    role TEXT NOT NULL,          -- 'user' | 'assistant'
    content TEXT NOT NULL,
    feedback TEXT,               -- 'like' | 'dislike' | NULL
    sources TEXT,                -- JSON array
    agent_action TEXT,           -- 'search_knowledge_base' | 'direct_answer' | 'refine_search'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7.3 user_scores 表结构

```sql
CREATE TABLE user_scores (
    user_id TEXT PRIMARY KEY,
    score REAL DEFAULT 0.5,
    feedback_count INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    consistency_rate REAL DEFAULT 0.5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 八、Insight 提取规格
## 8. Insight Extraction Specification

### 8.1 实时规则提取（零 LLM 成本）

**别名提取模式：**
```
"A就是B"  "A和B是同一个"  "A也叫B"  "A即B"
"A指的是B"  "A is also known as B"  "A = B"
```

过滤条件：实体长度 2~20 字符，不含标点。

触发时机：Agent 选择 `refine_search` 时，对用户消息执行提取。

### 8.2 每日 LLM 批量提取

```bash
python -m rag_service.extract_insights --days 7
```

提取类型：

| 类型 | 存储 | 反哺方式 |
|------|------|---------|
| aliases | aliases.json | 查询扩展（检索前） |
| corrections | corrections.md | 入向量库（可被语义召回） |
| gaps | gaps.json | 管理员报告（人工补充） |

---

## 九、混合检索参数
## 9. Hybrid Search Parameters

| 参数 | 值 | 说明 |
|------|-----|------|
| `enable_hybrid_search` | True | BM25 + 向量融合 |
| `bm25_top_k` | 10 | BM25 候选数量 |
| `rrf_k` | 60 | RRF 融合参数 |
| `top_k` | 5 | 最终返回结果数 |
| `similarity_threshold` | 0.5 | 向量相似度阈值 |
| `chunk_size` | 4096 | 文档分块大小（tokens） |
| `chunk_overlap` | 400 | 分块重叠（tokens） |
| `min_chunk_size` | 50 | 最小分块大小 |

---

## 十、LLM 调用参数
## 10. LLM Call Parameters

### 10.1 回答生成

| 参数 | 值 | 说明 |
|------|-----|------|
| max_tokens | 2048 | 最大输出长度 |
| temperature | 0.7 | 生成多样性 |
| timeout | 60s | API 超时 |
| chat_history | 最近 10 条 | 5 轮对话上下文 |
| 多轮增强 | history_context_max_chars=500, turns=6 | 检索 query 增强 |

### 10.2 平台配置

| 平台 | Embedding | LLM | 维度 |
|------|-----------|-----|------|
| Azure | text-embedding-3-large | gpt-51 | 3072 |
| 腾讯 | ms-x7g95cvc | ms-79rkgwxt | 4096 |

---

## 十一、性能基准
## 11. Performance Baseline

| 场景 | 耗时 | 备注 |
|------|------|------|
| 闲聊 (direct_answer) | ~2.7s | Agent 决策 + 直接回答 |
| 知识查询 (search) | ~14s (Azure) / ~6s (腾讯) | Agent + 检索 + LLM 生成 |
| 服务启动预热 | ~31s | BM25 索引构建 (2623 chunks) |
| 聚类构建 | ~62s | 全量 PCA + HDBSCAN |
| LLM 热启动 | ~270s | 15 clusters × 5 queries |
| 向量索引构建 | ~520s (腾讯) | 110 docs → 2623 chunks |

---

## 十二、测试账号
## 12. Test Accounts

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | admin |
| damon | damon123 | user |
| test1 | test123 | user |
| test2 | test123 | user |
| guest | guest | guest |

---

## 十三、运维命令速查
## 13. Operation Commands Quick Reference

```bash
# 服务管理
sudo systemctl start/stop/restart jq-rag jq-parser jq-frontend
sudo systemctl status jq-rag

# 向量索引重建
python -m rag_service.index_documents --source poc_output --limit 999

# 聚类重建（按当前 platform）
python -m rag_service.build_clusters

# LLM 热启动（聚类重建后可选执行一次）
python -m rag_service.warmstart_linucb --queries-per-cluster 5

# Insight 提取
python -m rag_service.extract_insights --days 7

# 系统状态
curl http://localhost:8004/health
curl http://localhost:8004/api/v1/intent-weight/stats

# E2E 测试
python -m rag_service.test_react_agent
```

---

*本文档描述 LinUCB 分支 v0.9.2-dev 的完整系统规格*
*负责人 / Owner: Damon Long <damon.long@merckgroup.com>*
