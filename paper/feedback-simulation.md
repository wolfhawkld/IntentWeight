# 反馈模拟策略设计
# Feedback Simulation Strategy Design

**创建时间 / Created**: 2026-04-21
**状态 / Status**: 已确认

---

## 一、核心原则：学习信号与评估指标解耦
## 1. Core Principle: Decouple Learning Signal from Evaluation Metric

反馈在实验中有两个不同用途，必须严格分开：

| 用途 | 说明 | 来源 | 不能混用的原因 |
|------|------|------|--------------|
| **学习信号** | 喂给 LinUCB 做参数更新 | GT 派生 + 概率采样 | 如果用 LLM 评分做学习信号，又用 LLM 做评估 → 循环论证 |
| **评估指标** | 评判最终检索/生成质量 | LLM-as-Judge (RAGAS) | 独立于学习过程，确保评估客观性 |

```
实验流程:

  [数据集 GT] ──→ [反馈模拟器] ──→ [学习信号] ──→ LinUCB 在线学习
                                                        ↓
                                                   检索结果
                                                        ↓
                                              [LLM-as-Judge (RAGAS)]
                                                        ↓
                                                   评估指标
                                                   (F / CR / AR)

  ↑ 学习信号来源                              ↑ 评估指标来源
  两条线独立，互不干扰
```

---

## 二、学习信号：GT 派生 + 概率采样模拟
## 2. Learning Signal: GT-derived + Probabilistic Sampling

### 2.1 设计思路

从 GT 相关性出发，按**概率分布采样**隐式信号，而非确定性赋值。

概率采样的优势：
- 天然带噪声，更接近真实用户行为
- 每次运行结果略有不同，可计算 mean ± std
- 支撑消融实验中多维反馈 vs 单一反馈的对比

### 2.2 各信号的模拟规则

**显式反馈（确定性，从 GT 直接派生）：**

| 检索结果 | 显式反馈 | reward 基础值 |
|---------|---------|-------------|
| chunk ∈ GT 相关集合 | like | 1.0 |
| chunk ∉ GT 相关集合 | dislike | 0.0 |
| chunk 部分匹配 GT | correct (修正) | 0.7 |

**隐式反馈（概率性，从分布采样）：**

| 隐式信号 | 检索命中 GT | 未命中 GT | 信号含义 |
|---------|-----------|----------|---------|
| **停留时间** | 采样 ~N(30s, 10s) | 采样 ~N(5s, 3s) | 命中时用户阅读时间长 |
| **复制行为** | P(copy) = 0.7 | P(copy) = 0.05 | 命中时用户倾向复制有用内容 |
| **滚动深度** | 采样 ~U(0.7, 1.0) | 采样 ~U(0.1, 0.4) | 命中时用户滚动更深 |

**上下文追问（概率性）：**

| 检索结果 | P(深入追问) | P(转向追问) | P(无追问) |
|---------|-----------|-----------|----------|
| 命中 GT | 0.3 | 0.0 | 0.7 |
| 部分匹配 | 0.1 | 0.2 | 0.7 |
| 未命中 | 0.0 | 0.5 | 0.5 |

### 2.3 模拟反馈示例

```json
// 检索命中 GT 的反馈示例
{
  "explicit": "like",
  "implicit": {
    "dwell_time": 27.3,
    "copy_action": true,
    "scroll_depth": 0.82
  },
  "context": null
}

// 检索未命中 GT 的反馈示例
{
  "explicit": "dislike",
  "implicit": {
    "dwell_time": 4.1,
    "copy_action": false,
    "scroll_depth": 0.23
  },
  "context": "redirecting"
}
```

### 2.4 最终 reward 计算

使用 `intent_weight/reward.py` 中的融合公式：

```
reward = explicit_weight(0.75) × explicit_score
       + implicit_weight(0.25) × implicit_score

其中：
  explicit_score = like(1.0) / dislike(0.0) / correct(0.7)
  implicit_score = copy(0.15) + dwell_in_range(0.05) + scroll_deep(0.05)
```

---

## 三、评估指标：LLM-as-Judge (RAGAS)
## 3. Evaluation Metric: LLM-as-Judge (RAGAS)

### 3.1 使用方式

RAGAS 框架评估最终检索和生成质量，独立于学习过程：

| 指标 | 评估内容 | 计算方式 |
|------|---------|---------|
| **Faithfulness (F)** | 答案是否基于检索到的内容 | LLM 检查答案中的每个 claim 是否有 context 支撑 |
| **Context Relevance (CR)** | 检索的上下文是否相关 | LLM 评估 context 中相关句子的比例 |
| **Answer Relevance (AR)** | 答案是否回答了问题 | LLM 生成反向问题，计算与原问题的相似度 |

### 3.2 可复现性要求

| 要求 | 做法 |
|------|------|
| 模型固定 | 使用固定版本（如 GPT-4-turbo-2024-04-09），论文中明确标注 |
| Prompt 固定 | 使用 RAGAS 默认 prompt，不做定制修改 |
| 温度固定 | temperature = 0，确保确定性输出 |
| 交叉验证 | 可选：用第二个 LLM（如 Claude）做 judge，验证评估一致性 |

---

## 四、各 Baseline 的反馈信号对齐
## 4. Feedback Signal Alignment Across Baselines

所有方法从同一个 GT 派生反馈，但各自按自己的机制转化：

| 方法 | 接受反馈 | 反馈格式 | 从 GT 如何派生 |
|------|---------|---------|--------------|
| BM25 / Dense / Hybrid | 否 | — | 不接受反馈（静态方法） |
| CRAG / MBA-RAG | 否 | — | 自适应但非在线学习 |
| DynamicRAG | 是 | RL reward (LLM 输出质量) | 检索结果覆盖 GT → reward score |
| Online-Opt RAG | 是 | binary (solved/unsolved) | answer 匹配 GT → 1/0 |
| FLAIR | 是 | feedback indicators | 匹配 GT → positive indicator |
| **本方法** | 是 | 显式+隐式+上下文（多维） | 按第二节的概率采样模拟 |

**公平性保证**：
- 所有方法从同一个 GT 获取等价信息量
- 各自用各自的反馈格式 — 不强行统一
- 静态方法不接受反馈 — 验证"在线学习是否有价值"

---

## 五、噪声与鲁棒性实验
## 5. Noise & Robustness Experiments

### 5.1 实验设计

在主实验的基础上，额外进行三组鲁棒性实验：

| 实验 | 反馈设置 | 目的 |
|------|---------|------|
| **主实验** | GT 派生 + 概率采样（干净） | 方法在理想条件下的上限 |
| **噪声实验** | + 10%/20%/30% 随机翻转显式反馈 | 模拟真实用户的不完美反馈 |
| **对抗实验** | + 20% 恶意反馈（like↔dislike 全部反转） | 验证信誉机制的防投毒能力 |

### 5.2 噪声注入方式

```python
# 噪声实验：随机翻转 noise_ratio 比例的显式反馈
if random.random() < noise_ratio:
    feedback["explicit"] = "dislike" if feedback["explicit"] == "like" else "like"
    # 隐式信号保持不变（用户行为不会完全反转）

# 对抗实验：特定"恶意用户"的反馈全部反转
if user_id in malicious_users:  # 20% 的用户被标记为恶意
    feedback["explicit"] = "dislike" if feedback["explicit"] == "like" else "like"
    feedback["implicit"]["copy_action"] = not feedback["implicit"]["copy_action"]
```

### 5.3 预期结论

| 实验 | 无信誉加权 | 有信誉加权 | 论文叙事 |
|------|-----------|-----------|---------|
| 10% 噪声 | 性能轻微下降 | 几乎不受影响 | 信誉机制提供基础鲁棒性 |
| 20% 噪声 | 性能明显下降 | 轻微下降 | 信誉机制在中等噪声下仍有效 |
| 30% 噪声 | 性能严重下降 | 中等下降 | 信誉机制有上限，但仍优于无保护 |
| 20% 恶意 | 性能可能崩溃 | 检测并降权恶意用户 | **信誉机制的核心价值** |

---

## 六、消融实验中的反馈维度对比
## 6. Feedback Dimension Ablation

通过逐层添加反馈维度，展示多维反馈的增量价值：

| 消融配置 | 反馈内容 | 信息量 | 预期效果 |
|---------|---------|--------|---------|
| 仅显式 | like/dislike (binary) | 最低 | 基线学习能力 |
| 显式 + 隐式 | + dwell/copy/scroll | 中 | 收敛更快，学到更细粒度的偏好 |
| **完整**（显式+隐式+上下文） | + 追问类型 | 最高 | 学习效率最高，尤其在部分匹配场景 |

这组消融直接回答审稿人的问题："多维反馈到底比单一反馈好多少？"

---

## 七、论文中的透明度声明
## 7. Transparency Statement for Paper

Experiments 章节需要明确写清楚以下内容：

```
Feedback Simulation:
  学习信号来自 GT 派生 + 概率采样模拟（详见 Section X）。
  显式反馈确定性派生：命中 GT → like，未命中 → dislike。
  隐式信号概率采样：停留时间 ~N(30,10)s / ~N(5,3)s，
  复制行为 P=0.7/0.05，滚动深度 ~U(0.7,1.0) / ~U(0.1,0.4)。
  上下文追问按条件概率采样。

Evaluation:
  使用 RAGAS 框架（GPT-4-turbo 作为 judge, temperature=0），
  评估 Faithfulness / Context Relevance / Answer Relevance。
  学习信号和评估指标完全解耦。

Robustness:
  额外进行 10%/20%/30% 噪声注入和 20% 恶意用户对抗实验。

Limitation:
  模拟反馈与真实用户反馈存在差距。概率采样和噪声实验
  部分弥补了这一 gap，但完整的用户研究留作未来工作。
```

---

## 八、流形局部反馈机制（2026-04-23 新增）
## 8. Manifold-Local Feedback Mechanism (Added 2026-04-23)

### 8.1 核心思想

当前反馈更新是"全局"的 — 所有历史反馈等权更新 LinUCB 的 A/b 矩阵。
但在对话上下文中，不同话题的历史反馈对当前 query 的参考价值是不同的。

**新思路：用流形距离加权反馈的相关性**，让同一流形区域的历史反馈影响更大，
远处区域的反馈影响衰减。本质是给反馈信号增加"局部几何性"。

```
传统:  Q_new → LinUCB 用全局 A/b 选 arm
                    ↑
         所有历史反馈等权更新 A/b

新思路:  Q_new → 在流形上定位 → FAISS/HNSW 找到邻域内的历史反馈
                                        ↓
                              按流形距离加权（近邻反馈权重大，远处衰减）
                                        ↓
                              LinUCB arm 选择更精准
```

### 8.2 实现路径

#### （1）跨 arm 的反馈传播

当 cluster i 收到反馈时，不只更新 A_i/b_i，还按流形距离衰减地更新邻近 cluster j：

```
A_j += decay(d(i,j)) × x·xᵀ
b_j += decay(d(i,j)) × r·x

其中 decay(d) = exp(-d/σ)，σ 控制传播范围
```

这让相邻聚类之间可以共享反馈信息，加速冷启动区域的学习。

#### （2）对话内的反馈注意力

多轮对话中，用 query embedding 的流形距离做注意力权重：

```
对话历史: Q1(feedback1), Q2(feedback2), ..., Q_t(feedback_t)
当前 query: Q_new

attention_i = softmax(-d_manifold(Q_new, Q_i) / τ)
weighted_feedback = Σ attention_i × feedback_i
```

话题相关的历史反馈信号增强，无关的衰减。

#### （3）局部信誉

用户信誉也可按流形区域局部化 — 某用户在医学领域的反馈可信度高，
但在法律领域可能不可靠。信誉 = f(全局信誉, 区域历史准确率)。

### 8.3 FAISS/HNSW 作为流形近似计算引擎

实时场景下，流形距离计算需要高效的 ANN（近似最近邻）支撑。
FAISS/HNSW 在 CPU 上即可提供亚毫秒级查询，完美匹配论文的"CPU-only"定位。

| 流形概念 | FAISS/HNSW 对应 | 说明 |
|---------|----------------|------|
| 测地线距离 | HNSW 搜索路径 | 沿数据分布的图结构跳转，非欧氏直线 |
| 流形最近邻 | ANN 查询结果 | 近似流形邻域 |
| 局部密度 | 节点 degree / hub 频率 | 可用于估计局部流形特征 |
| 流形导航 | 图上的贪心搜索 | HNSW 搜索 ≈ 近似测地线遍历 |

CPU 性能参考：

| 规模 | HNSW 查询延迟（CPU） | 对应场景 |
|------|---------------------|---------|
| 1K 向量 | < 0.1ms | 对话历史反馈 |
| 100K 向量 | ~1ms | 中等知识库 |
| 1M 向量 | ~5ms | 大规模知识库 |

### 8.4 与 DVM 理论的衔接

这个机制为 DVM（Dynamic Value Manifold）框架增加了新维度：

- **之前**：流形定义搜索空间（聚类 = 流形区域），反馈更新全局价值
- **现在**：流形同时定义了反馈的有效范围 — 反馈的影响力随流形距离衰减

这意味着 DVM 中的"价值场"不是全局均匀更新的，而是从反馈发生点向外
沿流形传播、逐渐衰减，类似物理中的场传播。

### 8.5 实验设计（消融）

| 配置 | 说明 | 预期效果 |
|------|------|---------|
| 全局反馈（当前） | 所有历史反馈等权 | 基线 |
| 流形局部反馈 | 按距离加权 | 收敛更快，尤其在多主题混合场景 |
| 跨 arm 传播 | 邻近聚类共享反馈 | 冷启动聚类学习加速 |
| 局部信誉 | 信誉按区域分化 | 对抗实验中鲁棒性更强 |

---

## 九、待确认事项
## 9. Open Questions

1. 隐式信号的分布参数（如停留时间 N(30,10)）需要参考真实数据校准，目前为估计值
2. LLM-as-Judge 用 GPT-4 还是开源模型（Llama3）？成本 vs 可复现性
3. 是否需要小规模人工标注实验（50-100 条）验证模拟反馈与真实反馈的相关性
4. 噪声实验的噪声比例设置（10/20/30% 是否合理）
5. 流形局部反馈的衰减函数选择：指数衰减 exp(-d/σ) vs 高斯核 vs 其他
6. 跨 arm 传播的范围控制：σ 参数如何设定（固定 vs 自适应）
7. FAISS 索引类型选择：HNSW vs IVF-Flat，对比实验中是否需要测试

---

*更新时间: 2026-04-23*
