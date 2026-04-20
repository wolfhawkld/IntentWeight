# 系统扩展性分析
# System Scalability Analysis

**日期 / Date**: 2026-04-20
**当前规模 / Current Scale**: 110 文档, 2623 chunks, ~20 条对话
**分析目标 / Target**: 评估数据量增长 10x~100x 时各组件的承受能力

---

## 一、各组件扩展性评估
## 1. Component Scalability Assessment

| 组件 | 当前规模 | 10x | 100x | 瓶颈 |
|------|---------|-----|------|------|
| ChromaDB 向量库 | 2623 chunks | ~26K ✅ | ~260K ✅ | HNSW O(log n)，百万级无压力 |
| BM25 索引 | 2623 docs, 30s 启动 | ~26K ⚠️ | ~260K ❌ | 启动重建时间线性增长 |
| HDBSCAN 聚类 | 110 docs, 15 clusters | ~1.1K ⚠️ | ~11K ❌ | 聚类数膨胀，O(n²) 距离计算 |
| LinUCB | 15 arms, 94d | ~50 arms ⚠️ | ~200 arms ❌ | arms 增多导致收敛慢 |
| PCA | 110 samples | ~1.1K ✅ | ~11K ✅ | 秒级完成 |
| SQLite 对话 | ~20 条 | 万级 ✅ | 百万级 ✅ | 有索引即可 |
| 别名字典 | 1 条 | 数百条 ✅ | 数千条 ✅ | JSON 加载毫秒级 |
| 服务器内存 (8GB) | ~2GB 使用 | ~6GB ⚠️ | 超限 ❌ | embedding + BM25 逼近上限 |

---

## 二、文档增删改支持现状
## 2. Document CRUD Support Status

### 已自动化

| 操作 | 机制 | 说明 |
|------|------|------|
| 新增文档 → 向量库 | `sync_document()` | 增量添加，file_hash 去重 |
| 修改文档 → 向量库 | `sync_document()` | hash 变更检测，删旧加新 |
| 删除文档 → 向量库 | `delete_by_source()` | 按 source_file 清除 |

### 需要人工介入

| 操作 | 当前状态 | 影响 |
|------|---------|------|
| 新增/删改文档 → BM25 索引 | 需重启服务 | 新文档不参与 BM25 关键词检索 |
| 新增/删改文档 → 聚类 | 需手动跑 `build_clusters.py` | 新文档未被分配到聚类，LinUCB 过滤可能遗漏 |
| 聚类重建 → LinUCB | 聚类重建后参数被重置 | 需重跑 `warmstart_linucb.py` 或靠在线学习恢复 |

### 自动化改进方向

```
文档变更检测 (file watcher / API hook)
    ↓
向量库增量同步 (已有)
    ↓
BM25 索引增量更新 (待实现：添加新 doc 到现有索引，无需全量重建)
    ↓
聚类增量分配 (待实现：新文档分配到最近聚类，无需全量重聚类)
    ↓
LinUCB 参数保持 (待实现：新 arm 用先验初始化，旧 arm 参数不丢失)
```

---

## 三、具体瓶颈分析与解决方案
## 3. Specific Bottleneck Analysis & Solutions

### 3.1 BM25 启动瓶颈

**问题**：BM25 索引在每次服务启动时全量重建（从 ChromaDB 读取所有文档 → 分词 → 构建索引）。

```
当前:   2,623 chunks → ~30s
10x:   26,000 chunks → ~5 分钟
100x: 260,000 chunks → ~30 分钟（服务不可用）
```

**解决方案**：BM25 索引持久化到磁盘
```python
# 构建后保存
bm25_index.save("data/bm25_index.pkl")

# 启动时加载（秒级）
bm25_index = BM25Index.load("data/bm25_index.pkl")

# 文档变更时增量更新
bm25_index.add_documents(new_docs)
bm25_index.save("data/bm25_index.pkl")
```

**实施优先级**：高（10x 数据时就需要）

### 3.2 聚类数量膨胀

**问题**：文档增多 → HDBSCAN 产生更多聚类 → LinUCB arms 增多 → context_dim 增大 → 收敛变慢。

```
当前:   110 docs → 15 clusters → 94d context → 几十条反馈收敛
10x:  1,100 docs → ~50 clusters → 164d context → 几百条反馈才收敛
100x: 11,000 docs → ~200 clusters → 464d context → 几千条反馈才收敛
```

**解决方案**：限制聚类上限 + 层次聚类

```python
# 方案 A: HDBSCAN 后合并小聚类，控制总数 ≤ 30
if n_clusters > 30:
    merge_smallest_clusters(target=30)

# 方案 B: 两级聚类
# L1: 大领域聚类（固定 10-20 个）→ LinUCB 在这层选择
# L2: 子主题聚类（每个大聚类内部细分）→ 向量检索在这层过滤
```

**实施优先级**：中（10x 数据时建议实施）

### 3.3 聚类自动重建

**问题**：文档增删改后，向量库自动同步了，但聚类和 BM25 没有同步更新。

**解决方案**：变更检测 + 增量更新

```python
# 新文档 → 分配到最近的现有聚类（无需全量重聚类）
def assign_to_nearest_cluster(new_doc_embedding, existing_clusters):
    distances = [cosine(new_doc_embedding, c.center) for c in existing_clusters]
    return clusters[argmin(distances)]

# 定期全量重聚类（如每周或文档变更超过 20% 时）
def should_rebuild_clusters():
    new_docs_ratio = new_docs_since_last_build / total_docs
    return new_docs_ratio > 0.2
```

**实施优先级**：中

### 3.4 内存天花板

**问题**：4C8G 服务器在数据量增长后内存不足。

```
主要内存消耗：
- ChromaDB: ~chunk_count × embedding_dim × 4 bytes
  当前: 2623 × 3072 × 4 = ~30MB
  10x:  26K × 3072 × 4 = ~300MB
  100x: 260K × 3072 × 4 = ~3GB

- BM25 索引: ~chunk_count × avg_vocabulary
  当前: ~200MB
  10x:  ~2GB
  100x: ~20GB（远超内存）

- 系统 + Python + 其他: ~1-2GB
```

**解决方案（按数据量递进）**：

| 数据量 | 方案 |
|--------|------|
| 10x | 升配到 16GB 内存 |
| 50x+ | BM25 改用磁盘索引（如 Whoosh / Elasticsearch） |
| 100x+ | 向量库迁移到独立服务（Milvus / Qdrant），ChromaDB 不适合大规模 |

**实施优先级**：低（当前规模远未触及）

### 3.5 LinUCB 参数膨胀

**问题**：arms 增多时，每个 arm 的 A 矩阵（d×d）占用更多内存和计算。

```
当前:  15 arms × 94 × 94 × 8 bytes = ~1MB
10x:   50 arms × 164 × 164 × 8 bytes = ~10MB
100x: 200 arms × 464 × 464 × 8 bytes = ~340MB
```

**解决方案**：
- 限制聚类数量（3.2 节方案）间接限制了 arms 数量
- 如果必须更多 arms：用稀疏矩阵或对角近似代替全矩阵

**实施优先级**：低（跟随 3.2 一起解决）

---

## 四、扩展性路线图
## 4. Scalability Roadmap

```
当前 (110 docs)          → 所有组件在舒适区，无需优化
    ↓
500 docs (5x)            → 建议实施 BM25 持久化
    ↓
1,000 docs (10x)         → 实施聚类上限 + 增量分配 + 内存升配
    ↓
5,000 docs (50x)         → BM25 迁移到磁盘索引引擎
    ↓
10,000+ docs (100x)      → 向量库迁移独立服务 + 分布式架构
```

---

## 五、业务维度拆分策略
## 5. Business-level Partitioning Strategy

除了技术层面的优化，更务实的扩展方案是**从业务维度拆分成多个独立实例**，让每个实例保持在舒适区内。

### 核心思路

与其让一个系统硬扛所有数据，不如按业务领域拆分：

```
                    统一入口 / 路由层
               (按查询意图或用户部门路由)
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   工厂运营知识库     质量合规知识库    客户管理知识库
   (独立向量库)      (独立向量库)     (独立向量库)
   (独立聚类)        (独立聚类)       (独立聚类)
   (独立LinUCB)      (独立LinUCB)     (独立LinUCB)
   ~100 docs         ~200 docs        ~150 docs
```

### 拆分优势

| 优势 | 说明 |
|------|------|
| **每个实例保持小规模** | 百级文档，所有组件在舒适区，无需复杂优化 |
| **聚类更精准** | 同领域文档语义集中，聚类纯度更高 |
| **LinUCB 收敛更快** | arms 少 + 查询语义集中 → 少量反馈就能学好 |
| **故障隔离** | 一个实例出问题不影响其他领域 |
| **独立演进** | 不同领域可以有不同的优化策略和更新节奏 |
| **框架完全复用** | 代码一套，数据和权重各自独立 |

### 共享 vs 独立

| 组件 | 策略 | 原因 |
|------|------|------|
| 框架代码 | 共享 | 一套代码部署多个实例 |
| LLM / Embedding API | 共享 | 通用能力，不区分领域 |
| 用户认证 | 共享 | 统一账号体系 |
| 向量库 | **独立** | 不同领域文档分开存储和检索 |
| 聚类 + LinUCB | **独立** | 每个领域独立学习检索偏好 |
| 别名字典 | **独立** | 不同领域的术语可能含义不同 |
| 用户信誉 | 共享 | 用户可信度跨领域通用 |
| 对话历史 | 可共享 | 统一存储便于分析 |

### 路由层设计

```python
# 简单路由：按用户部门或查询关键词
def route_query(query, user_department):
    if user_department in ["生产", "运营", "EHS"]:
        return "factory_ops_instance"
    elif user_department in ["质量", "合规", "QA"]:
        return "quality_compliance_instance"
    else:
        return "general_instance"  # 兜底
```

未来可以用 BERT 分类器自动路由，或者 ReAct Agent 决定查哪个领域的知识库。

### 与技术优化的关系

业务拆分和技术优化不互斥，而是互补：

```
数据量小 (当前)：    单实例，无需拆分
数据量中 (10x)：     业务拆分 → 每个实例仍在舒适区
数据量大 (100x)：    业务拆分 + 技术优化（BM25 持久化等）
```

**业务拆分是最低成本的扩展手段** — 不需要改代码，不需要换技术栈，只需要按领域部署多个实例。这正好呼应项目的设计哲学：**框架通用，数据独立**。

---

## 六、结论
## 6. Conclusion

**闭环不会失败，但会变慢。**

扩展策略分两条线：

1. **技术优化线**：BM25 持久化 → 聚类上限 → 磁盘索引 → 独立向量库服务
2. **业务拆分线**：按领域拆分独立实例，让每个实例保持小规模

两条线互补，优先用业务拆分保持简单，技术优化按需引入。

核心闭环逻辑（LinUCB + 反馈 + Insight）在任何规模下都不需要改变。系统有优雅降级能力 — 即使 LinUCB 预筛选不准确，也只是 fallback 到全量检索，不会比没有 LinUCB 时更差。

---

*本文档基于 2026-04-20 的技术讨论整理*
