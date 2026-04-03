# Phase 1: 意图聚类验证

验证意图聚类方法的有效性，确定技术方案。

---

## 验证目标

| 目标 | 阈值 | 结果 |
|------|------|------|
| 轮廓系数 | > 0.5 | ✅ 达标 |
| NMI | > 0.7 | ✅ 达标 |
| ARI | > 0.6 | ✅ 达标 |

---

## 技术方案

- **嵌入**: SBERT (sentence-transformers)
- **聚类**: HDBSCAN（密度聚类，自动确定簇数）
- **增强**: 实体识别 + 特征融合

---

## 文件结构

```
01_intent_clustering/
├── scripts/
│   └── closure_test.py      # 闭环测试脚本
├── results/
│   └── closure_test_results.json
└── README.md
```

---

## 关键结论

1. **HDBSCAN 优于 K-Means**: 自动确定簇数，噪声点处理更好
2. **实体增强有效**: 金融领域实体（金额、利率等）显著提升聚类质量
3. **嵌入质量关键**: SBERT > BERT-base

---

*创建于 2026-03-27*