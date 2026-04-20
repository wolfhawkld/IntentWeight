# IntentWeight 生产级模块
# IntentWeight Production Module

基于动态价值流形 (DVM) 理论的 RAG 检索优化模块。
RAG retrieval optimization module based on Dynamic Value Manifold (DVM) theory.

来源于 jq_kg_base 项目的工程验证实现，已去除企业隐私内容。
Derived from jq_kg_base project's engineering validation, with enterprise-private content removed.

---

## 三层架构
## Three-Layer Architecture

```
流形发现层 (Manifold Discovery)
├── clustering.py         # HDBSCAN + PCA：发现流形密度结构
└── keyword_prior.py      # TF-IDF 关键词：冷启动先验

流形导航层 (Manifold Navigation)
├── linucb.py             # LinUCB Contextual Bandit：在线学习导航策略
├── __init__.py           # IntentWeightManager：导航编排器
└── persistence.py        # JSON 状态持久化

流形标注层 (Manifold Annotation)
├── reward.py             # 奖励计算：显式+隐式融合 (75/25)
├── user_credibility.py   # 用户信誉：3方案协同防投毒
├── conversation_store.py # 对话存储：SQLite 持久化
├── insight_extractor.py  # Insight 提取：别名/查询扩展
└── models.py             # 数据模型
```

## 与 pre_validation/ 的关系

- `pre_validation/` = 研究实验代码（Phase 1A-1F 验证用）
- `intent_weight/` = 生产级实现（从 jq_kg_base 工程验证中提炼）

研究实验用 pre_validation/ 中的脚本，论文系统描述参考 intent_weight/ 中的实现。
