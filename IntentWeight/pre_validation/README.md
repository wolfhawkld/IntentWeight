# Pre-Validation: IntentWeight 模块验证

验证 IntentWeight 系统各核心模块的有效性，确定技术方案可行性。

---

## 目录结构

```
pre_validation/
├── datasets/                    # 共享数据集
│   ├── banking77/              # 银行领域意图数据
│   ├── clinc150/               # 多领域意图数据
│   ├── dailydialog/            # 对话数据
│   ├── embeddings/             # 预计算嵌入向量
│   └── processed/              # 处理后数据
├── 01_intent_clustering/        # Phase 1: 意图聚类验证
├── 02_speech_act/               # Phase 2: 言语行为分类验证
├── 03_feedback_signal/          # Phase 3: 反馈信号有效性验证
└── utils/                       # 共享工具脚本
```

---

## 验证阶段

| Phase | 模块 | 状态 | 结论 |
|-------|------|------|------|
| **01_intent_clustering** | 意图聚类 | ✅ 完成 | HDBSCAN + 实体增强可行 |
| **02_speech_act** | 言语行为分类 | ✅ 完成 | 可辅助意图识别 |
| **03_feedback_signal** | 反馈信号有效性 | ✅ 完成 | 隐式信号高度可靠 (r=0.928) |

---

## 共享数据集

| 数据集 | 规模 | 意图数 | 领域 |
|-------|------|-------|------|
| BANKING77 | 13K | 77 | 银行 |
| CLINC150 | 23K | 150 | 多领域 |
| DailyDialog | 11K | - | 日常对话 |

---

## 工具脚本

| 脚本 | 用途 |
|------|------|
| `download_data.py` | 数据集下载 |
| `generate_embeddings.py` | 嵌入向量生成 |
| `preprocess.py` | 数据预处理 |

---

## 核心发现

1. **意图聚类有效**: HDBSCAN + 实体增强，轮廓系数 > 0.5
2. **言语行为可分类**: 可区分陈述/提问/请求等，辅助意图识别
3. **反馈信号可靠**: 隐式信号（停留时间、拷贝）与满意度相关性 r=0.928

---

*更新于 2026-04-03*