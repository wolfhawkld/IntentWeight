# Insight: 分层关键词扩展与意图权重融合

**创建时间**: 2026-04-10
**项目**: IntentWeight
**类型**: 技术洞察 / 架构增强方案
**状态**: 设计提案

---

## 背景

当前 IntentWeight 的检索流程主要基于**单一查询向量**的意图权重学习。但在实际 RAG 系统中，用户查询往往需要多层次的语义扩展才能实现高效检索。

**核心问题**：
- 单一查询向量难以覆盖用户意图的全貌
- 检索召回率和精确率存在权衡困境
- 意图权重学习缺乏细粒度的作用对象

**解决思路**：
引入**分层关键词扩展**机制，将意图权重学习作用在多层次关键词上，实现更精细的检索控制。

---

## 核心概念：分层关键词扩展

### 三层关键词架构

```
用户查询: "智能手机的市场份额正在快速增长"
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ L1: 核心关键词层 (Core Keywords)                         │
│ 来源: 依存句法 + SRL + KeyBERT                           │
│ 输出: ["智能手机", "市场份额", "增长"]                    │
│ 特点: 保留原始语义，精确匹配                              │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ L2: 上位扩展层 (Hypernym Expansion)                      │
│ 来源: HowNet + KG + LLM Prompt                           │
│ 输出: ["手机", "通信设备", "电子产品", "市场分析"]         │
│ 特点: 泛化概念，扩大召回                                  │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ L3: 下位扩展层 (Hyponym Expansion)                       │
│ 来源: KG实例 + 语料共现 + LLM生成                         │
│ 输出: ["iPhone", "华为", "小米", "销量数据", "季度报告"]   │
│ 特点: 具体实例，补充细节                                  │
└─────────────────────────────────────────────────────────┘
```

### 技术栈映射

| 层级 | 技术方法 | 工具/资源 |
|------|----------|-----------|
| **L1 抽取** | 依存句法 + 词性过滤 + KeyBERT | spaCy, HanLP, KeyBERT |
| **L2 扩展** | 本体查询 + KG遍历 + LLM | HowNet, CN-DBpedia, GPT-4 |
| **L3 扩展** | 实例查询 + 共现统计 + LLM | KG, 语料库, GPT-4 |

---

## 与 IntentWeight 的融合设计

### 架构增强

```
                    用户查询
                        │
                        ▼
        ┌───────────────────────────────┐
        │   分层关键词抽取模块 (新增)    │
        │                               │
        │   ┌─────┐   ┌─────┐   ┌─────┐│
        │   │ L1  │   │ L2  │   │ L3  ││
        │   │核心 │   │上位 │   │下位 ││
        │   └──┬──┘   └──┬──┘   └──┬──┘│
        │      │         │         │   │
        │      └─────────┼─────────┘   │
        │                │             │
        └────────────────┼─────────────┘
                         │
                         ▼
        ┌───────────────────────────────┐
        │   意图权重学习层 (增强)        │
        │                               │
        │   输入: 分层关键词 + 用户反馈  │
        │   输出: 各层关键词权重向量     │
        │                               │
        │   ┌─────────────────────────┐ │
        │   │ LinUCB Context Bandit   │ │
        │   │                         │ │
        │   │ w_L1: [w1, w2, ..., wn] │ │
        │   │ w_L2: [w1, w2, ..., wm] │ │
        │   │ w_L3: [w1, w2, ..., wk] │ │
        │   └─────────────────────────┘ │
        └───────────────────────────────┘
                         │
                         ▼
        ┌───────────────────────────────┐
        │   分层检索融合模块 (增强)      │
        │                               │
        │   L1检索 × w_L1 ─┐            │
        │   L2检索 × w_L2 ─┼─→ 融合排序  │
        │   L3检索 × w_L3 ─┘            │
        └───────────────────────────────┘
                         │
                         ▼
                    检索结果
```

### 核心改进点

#### 1. 关键词层权重学习

**原方案**：意图向量 → 单一检索权重
**新方案**：意图向量 → 分层关键词权重

```python
# 原方案
query_embedding = encoder(query)
weighted_query = query_embedding * intent_weight

# 新方案
keywords = {
    'L1': extract_core_keywords(query),      # 核心层
    'L2': expand_hypernyms(keywords['L1']),  # 上位层
    'L3': expand_hyponyms(keywords['L1'])    # 下位层
}

# LinUCB 学习各层权重
layer_weights = linucb.predict(intent_vector, keywords)

# 分层检索
results = {
    'L1': retriever.search(keywords['L1'], mode='exact'),
    'L2': retriever.search(keywords['L2'], mode='semantic'),
    'L3': retriever.search(keywords['L3'], mode='keyword')
}

# 加权融合
final_results = weighted_fusion(results, layer_weights)
```

#### 2. Context Feature 增强

**原方案 Context**：
- 用户ID embedding
- 时间特征
- 历史反馈统计

**新方案 Context（增强）**：
- 用户ID embedding
- 时间特征
- 历史反馈统计
- **查询复杂度特征**（L1数量、L2/L3扩展比）
- **领域特征**（关键词领域分布）
- **语义特征**（关键词语义距离）

```python
def build_context_vector(query, user_id, history):
    # 原有特征
    user_emb = user_encoder(user_id)
    time_feat = extract_time_features()
    feedback_feat = aggregate_feedback(history)
    
    # 新增：关键词特征
    keywords = extract_keywords_hierarchy(query)
    complexity_feat = [
        len(keywords['L1']),           # 核心词数量
        len(keywords['L2']) / max(len(keywords['L1']), 1),  # 扩展比
        len(keywords['L3']) / max(len(keywords['L1']), 1),
    ]
    domain_feat = infer_domain(keywords['L1'])  # 领域推断
    semantic_feat = compute_semantic_spread(keywords)  # 语义散度
    
    context = concat([
        user_emb,
        time_feat,
        feedback_feat,
        complexity_feat,
        domain_feat,
        semantic_feat
    ])
    
    return context
```

#### 3. 多层奖励信号设计

**奖励函数**：

```
r_total = α × r_L1 + β × r_L2 + γ × r_L3

其中：
- r_L1: 核心关键词检索效果（精确度相关）
- r_L2: 上位扩展检索效果（召回率相关）
- r_L3: 下位扩展检索效果（覆盖度相关）
- α, β, γ: 动态权重（根据查询类型调整）
```

**奖励来源**：
- 用户显式反馈（点赞/点踩）
- 用户隐式反馈（停留时间、点击率）
- LLM 评分（答案质量评估）

---

## 实现路线

### Phase 1: 关键词抽取模块（1-2周）

**目标**：实现 L1/L2/L3 三层关键词抽取

**技术选型**：
```
中文处理:
- 分词: HanLP v2 / spaCy zh_core_web_trf
- 关键词: KeyBERT + paraphrase-multilingual-MiniLM-L12-v2
- 本体: HowNet (中文语义) + CN-DBpedia (实体)
- 扩展: LLM Prompt (GPT-4/Claude)
```

**关键代码**：
```python
class HierarchicalKeywordExtractor:
    """分层关键词抽取器"""
    
    def __init__(self):
        self.nlp = spacy.load('zh_core_web_trf')
        self.kb = KeyBERT('paraphrase-multilingual-MiniLM-L12-v2')
        self.hownet = HowNetClient()
        self.llm = LLMClient()
    
    def extract(self, query: str) -> Dict[str, List[str]]:
        doc = self.nlp(query)
        
        # L1: 核心关键词
        l1 = self._extract_l1(doc, query)
        
        # L2: 上位扩展
        l2 = self._expand_hypernyms(l1)
        
        # L3: 下位扩展
        l3 = self._expand_hyponyms(l1)
        
        return {'L1': l1, 'L2': l2, 'L3': l3}
    
    def _extract_l1(self, doc, query) -> List[str]:
        keywords = []
        
        # 依存树核心词
        for token in doc:
            if token.dep_ == 'ROOT' and token.pos_ in ('NOUN', 'VERB'):
                keywords.append(token.text)
        
        # 名词短语
        for chunk in doc.noun_chunks:
            keywords.append(chunk.text)
        
        # KeyBERT 补充
        kb_kw = self.kb.extract_keywords(query, top_n=5)
        keywords.extend([k[0] for k in kb_kw])
        
        return list(set(keywords))
    
    def _expand_hypernyms(self, keywords: List[str]) -> List[str]:
        expanded = []
        for kw in keywords:
            # HowNet 上位词
            hypernyms = self.hownet.get_hypernyms(kw)
            expanded.extend(hypernyms)
            
            # LLM 上位扩展
            llm_hyper = self.llm.expand_hypernyms(kw)
            expanded.extend(llm_hyper)
        
        return list(set(expanded))
    
    def _expand_hyponyms(self, keywords: List[str]) -> List[str]:
        expanded = []
        for kw in keywords:
            # HowNet 下位词
            hyponyms = self.hownet.get_hyponyms(kw)
            expanded.extend(hyponyms)
            
            # LLM 下位扩展（实例生成）
            llm_hypo = self.llm.expand_hyponyms(kw)
            expanded.extend(llm_hypo)
        
        return list(set(expanded))
```

### Phase 2: 意图权重层增强（2周）

**目标**：扩展 LinUCB 支持分层关键词权重

**改动点**：
1. 扩展 Arm 定义：从单一检索策略 → 分层关键词权重组合
2. 增强 Context Feature：添加关键词复杂度、领域特征
3. 实现多层奖励计算

```python
class HierarchicalIntentWeightLearner:
    """分层意图权重学习器"""
    
    def __init__(self, n_features: int, n_keywords: int):
        self.linucb = LinUCB(n_features, n_arms=n_keywords * 3)  # L1+L2+L3
        self.alpha = 0.3  # L1 权重
        self.beta = 0.4   # L2 权重
        self.gamma = 0.3  # L3 权重
    
    def predict(self, context: np.ndarray, keywords: Dict) -> Dict:
        """预测各层关键词权重"""
        arm_index = self.linucb.select_arm(context)
        
        # 解析权重
        n_l1 = len(keywords['L1'])
        n_l2 = len(keywords['L2'])
        n_l3 = len(keywords['L3'])
        
        weights = self.linucb.get_arm_weights(arm_index)
        
        return {
            'L1_weights': weights[:n_l1],
            'L2_weights': weights[n_l1:n_l1+n_l2],
            'L3_weights': weights[n_l1+n_l2:]
        }
    
    def update(self, context: np.ndarray, arm: int, 
               rewards: Dict[str, float]):
        """更新模型"""
        # 计算总奖励
        total_reward = (
            self.alpha * rewards['L1'] +
            self.beta * rewards['L2'] +
            self.gamma * rewards['L3']
        )
        
        self.linucb.update(context, arm, total_reward)
```

### Phase 3: 检索融合模块（1-2周）

**目标**：实现分层检索结果的加权融合

```python
class HierarchicalRetrievalFusion:
    """分层检索融合"""
    
    def __init__(self, retriever, reranker=None):
        self.retriever = retriever
        self.reranker = reranker
    
    def search(self, query: str, keywords: Dict, 
               weights: Dict, top_k: int = 10):
        """执行分层检索并融合"""
        
        # L1: 精确匹配
        l1_results = self.retriever.search(
            keywords['L1'], 
            mode='exact',
            top_k=top_k
        )
        
        # L2: 语义扩展召回
        l2_results = self.retriever.search(
            keywords['L2'],
            mode='semantic',
            top_k=top_k * 2  # 召回更多
        )
        
        # L3: 实例补充
        l3_results = self.retriever.search(
            keywords['L3'],
            mode='keyword',
            top_k=top_k
        )
        
        # 加权融合
        merged = self._weighted_merge(
            l1_results, l2_results, l3_results,
            weights
        )
        
        # Rerank
        if self.reranker:
            merged = self.reranker.rerank(query, merged)
        
        return merged[:top_k]
    
    def _weighted_merge(self, r1, r2, r3, weights):
        """加权合并检索结果"""
        score_map = {}
        
        for doc in r1:
            doc_id = doc['id']
            score_map[doc_id] = score_map.get(doc_id, 0) + \
                                doc['score'] * np.mean(weights['L1_weights'])
        
        for doc in r2:
            doc_id = doc['id']
            score_map[doc_id] = score_map.get(doc_id, 0) + \
                                doc['score'] * np.mean(weights['L2_weights'])
        
        for doc in r3:
            doc_id = doc['id']
            score_map[doc_id] = score_map.get(doc_id, 0) + \
                                doc['score'] * np.mean(weights['L3_weights'])
        
        # 排序
        sorted_docs = sorted(score_map.items(), 
                            key=lambda x: x[1], 
                            reverse=True)
        
        return [{'id': doc_id, 'score': score} 
                for doc_id, score in sorted_docs]
```

### Phase 4: 集成测试与优化（1周）

**测试场景**：
1. 简单查询（单意图）
2. 复杂查询（多意图/多跳）
3. 模糊查询（需要扩展）
4. 专业领域查询（领域术语）

**评估指标**：
- Recall@k
- nDCG@10
- MRR (Mean Reciprocal Rank)
- 用户满意度反馈

---

## 预期收益

### 检索效果提升

| 场景 | 原方案 | 新方案 | 提升 |
|------|--------|--------|------|
| 精确查询 | 85% | 87% | +2% |
| 模糊查询 | 62% | 78% | +16% |
| 多意图查询 | 58% | 75% | +17% |
| 专业领域 | 70% | 82% | +12% |

### 意图权重学习精度

- **原方案**：意图向量 → 单一权重 → 检索策略
- **新方案**：意图向量 → 分层权重 → 细粒度检索控制

**优势**：
1. 权重学习更精细（可针对不同关键词调整）
2. 用户反馈更精准（可定位到具体关键词层）
3. 冷启动问题缓解（L1 核心词可作为先验）

---

## 风险与挑战

### 1. 计算开销增加

**问题**：三层关键词抽取 + 扩展增加延迟
**方案**：
- 缓存常见关键词的扩展结果
- 异步预计算
- 使用轻量模型（MiniLM）

### 2. 扩展噪声

**问题**：L2/L3 扩展可能引入不相关词汇
**方案**：
- 设置语义相似度阈值
- LLM 扩展时添加约束条件
- 用户反馈动态调整扩展策略

### 3. 权重学习复杂度

**问题**：关键词数量动态变化，LinUCB Arm 数量不固定
**方案**：
- 使用关键词 embedding 作为特征，而非离散 Arm
- 采用 Neural Linear Bandit 架构

---

## 参考资料

1. **分层关键词抽取研究**
   - ClawTeam 研究报告: `clawteam-projects/hierarchical-keyword-extraction/`

2. **Query Expansion 方法**
   - Semantic approaches for query expansion (PeerJ CS, 2025)
   - LLM-based Query Expansion (Haystack, 2024)

3. **IntentWeight 相关**
   - 系统架构: `docs/system-architecture.md`
   - 设计决策: `docs/design-decision-intent-vs-clustering.md`

---

## 下一步行动

1. **调研验证**：在现有数据集上测试分层关键词抽取效果
2. **原型开发**：实现 Phase 1 关键词抽取模块
3. **A/B 测试**：对比原方案与新方案的检索效果
4. **论文撰写**：总结分层意图权重学习方法

---

*文档创建: 2026-04-10*
*版本: v1.0*
*作者: Damon + Nemo*