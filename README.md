# IntentWeight

**意图驱动的动态权重学习系统**

## 核心理念

> 让系统从每一次用户交互中学习，将反馈沉淀为可复用的"意图-数据"权重关联

## 研究方向

在多类型RAG数据（向量、KV、KG）构成的动态多路召回系统中，通过用户反馈（显式+隐式）驱动的RL推理，动态更新"意图-数据元素"的语义关联权重，实现系统问答效果的持续提升。

## 核心创新点

| 创新点 | 描述 |
|-------|------|
| **意图聚类** | 无监督发现用户问题意图类别 |
| **实体增强** | 融合知识图谱实体信息提升聚类质量 |
| **反馈驱动权重** | 用户反馈 → 数据元素级权重更新 |
| **动态闭环** | 持续学习、持续优化的自适应系统 |

## 项目结构

```
IntentWeight/
├── README.md                   # 项目说明
├── requirements.txt            # 依赖
├── venv/                       # 虚拟环境
├── pre_validation/             # Phase 1A: 意图聚类方法验证
├── data/                       # 数据集（待创建）
├── models/                     # 模型（待创建）
├── experiments/                # 实验记录（待创建）
└── docs/                       # 文档（待创建）
```

## 快速开始

```bash
# 进入项目目录
cd ~/.openclaw/workspace/IntentWeight

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 下载 spaCy 模型
python -m spacy download en_core_web_sm
```

## 研究阶段

| 阶段 | 目标 | 状态 |
|-----|------|------|
| **Phase 1A** | 意图聚类方法验证 | 🔄 进行中 |
| **Phase 1B** | 构建RAG验证数据集 | ⏳ 待开始 |
| **Phase 1C** | 意图-数据关联验证 | ⏳ 待开始 |
| **Phase 2** | 检索策略实现 | ⏳ 待开始 |
| **Phase 3** | 用户反馈闭环 | ⏳ 待开始 |
| **Phase 4** | 论文产出 | ⏳ 待开始 |

## 参考

- [clawteam-projects/intent-clustering-analysis](../clawteam-projects/intent-clustering-analysis/) - 研究调研报告
- [clawteam-projects/kb-hop-reasoning](../clawteam-projects/kb-hop-reasoning/) - 多跳推理研究方向

---

*创建于 2026-03-27*