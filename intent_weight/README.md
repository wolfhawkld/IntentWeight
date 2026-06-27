# IntentRoute Legacy Compatibility Package

`intent_weight` is the legacy import path for the IntentRoute production
module. New integrations should import from `intent_route`:

```python
from intent_route import IntentRouteManager
```

Existing imports remain valid:

```python
from intent_weight import IntentWeightManager
```

Both names resolve to the same implementation. Existing state directories,
including `data/intent_weight/`, remain compatible and are not migrated.

IntentRoute is a geometry-guided and feedback-adaptive evidence-routing
controller for RAG. It uses cluster-local routing and LinUCB feedback state
while retaining dense retrieval as a fallback.

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
├── __init__.py           # IntentRouteManager + legacy alias
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
- `intent_route/` = canonical public API
- `intent_weight/` = legacy-compatible implementation package

研究实验使用 `pre_validation/` 和 `paper/experiments/` 中的脚本；新代码和
论文展示统一使用 IntentRoute 名称。
