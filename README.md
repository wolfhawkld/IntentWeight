# IntentRoute

**Geometry-guided and feedback-adaptive evidence routing for RAG**

## 核心理念

> 使用局部几何构建可复现的检索路由，以 LinUCB 和可信反馈更新路由置信度，
> 并在保留 dense recall floor 的前提下控制最终证据上下文。

## 研究方向

IntentRoute 在 dense、BM25 和 cluster-local 多路召回表面上进行自适应控制。
局部几何提供路由结构，可信用户反馈更新 LinUCB 路由状态，校准策略控制最终
送入生成模型的 evidence context。当前论文实验聚焦检索质量与 context-token
trade-off，并保留 dense 作为质量基线和 fallback。

## 核心创新点

| 创新点 | 描述 |
|-------|------|
| **几何引导路由** | 使用聚类局部结构构建可复现的 route arms |
| **反馈自适应** | 可信反馈更新 LinUCB 路由置信度和恢复状态 |
| **多路召回保护** | dense recall floor + BM25 lexical rescue |
| **上下文控制** | 将 route confidence 映射为校准后的 evidence context |

## 项目结构

```
<repository>/
├── README.md                   # 项目说明
├── requirements.txt            # 依赖
├── intent_route/               # canonical Python API
├── intent_weight/              # legacy-compatible implementation
├── pre_validation/             # 早期研究验证
├── paper/experiments/          # 正式实验、结果与任务记录
├── paper/full_draft/           # 论文 Markdown 主源
└── paper/latex/                # 生成的 LaTeX 与 PDF
```

## 快速开始

```bash
# 当前本地/Git 仓库目录仍保留历史名称 IntentWeight
cd ~/.openclaw/workspace/IntentWeight

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 下载 spaCy 模型
python -m spacy download en_core_web_sm
```

## Python API

```python
from intent_route import IntentRouteManager, IntentRouteStats

manager = IntentRouteManager(state_dir="data/intent_route")
```

旧接口 `from intent_weight import IntentWeightManager` 继续兼容。历史实验目录、
结果标签和 `data/intent_weight/` 状态目录不会被重命名。

## 参考

- [clawteam-projects/intent-clustering-analysis](../clawteam-projects/intent-clustering-analysis/) - 研究调研报告
- [clawteam-projects/kb-hop-reasoning](../clawteam-projects/kb-hop-reasoning/) - 多跳推理研究方向

---

*创建于 2026-03-27*
