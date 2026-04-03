# Phase 2: 言语行为分类验证

验证言语行为（Speech Act）分类的有效性，辅助意图识别。

---

## 验证目标

| 目标 | 说明 |
|------|------|
| 区分言语行为类型 | Statement/Question/Request/Complaint 等 |
| 与意图关联 | 言语行为 → 意图类型推断辅助 |

---

## 文件结构

```
02_speech_act/
├── scripts/
│   ├── speech_act_classify.py        # 分类脚本
│   └── test_speech_act_classifier.py # 测试脚本
├── data/
│   └── speech_act_test.json          # 测试数据
├── results/
│   ├── speech_act_banking77.json
│   ├── speech_act_clinc150.json
│   └── speech_act_dailydialog.json
│   └── speech_act_test.json
└── README.md
```

---

## 言语行为分类

| 类型 | 说明 | 意图关联 |
|------|------|----------|
| **Statement** | 陈述事实 | 信息型意图 |
| **Question** | 提问 | 查询型意图 |
| **Request** | 请求/指令 | 操作型意图 |
| **Complaint** | 投诉/抱怨 | 问题反馈意图 |
| **Greeting** | 问候 | 社交型意图 |

---

## 关键结论

1. **分类准确率**: Question/Statement 区分准确率 > 90%
2. **意图辅助**: 言语行为可作为意图识别的前置过滤器
3. **领域适配**: 金融领域 Request 类型识别需要领域关键词

---

*创建于 2026-03-28*