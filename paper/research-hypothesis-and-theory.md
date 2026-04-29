# IntentWeight Research Hypothesis and Theory

**Created**: 2026-04-28
**Status**: Working paper-positioning summary

---

## Core Claim

IntentWeight is not primarily a study of a single algorithm such as LinUCB. Its core research question is:

> Do domain-specific RAG corpora exhibit exploitable semantic manifold structure, and can that structure support a self-evolving retrieval system through clustering, online bandit navigation, and feedback-driven value updates?

In Chinese:

> IntentWeight 研究垂类 RAG 语料是否存在可利用的语义流形结构，并进一步验证该结构能否作为系统自进化的基础：通过聚类识别局部语义区域，通过上下文 Bandit 学习检索导航策略，通过问答反馈持续更新流形上的价值场，最终实现 RAG 系统的自动优化与升级。

---

## Research Chain

The project follows this chain of hypotheses:

```text
垂类 RAG 数据是否存在可利用的语义流形结构？
        ↓
如果存在，能否通过聚类/降维识别其局部结构？
        ↓
如果局部结构可识别，能否把检索视为流形上的导航问题？
        ↓
如果检索是导航问题，用户/GT 反馈能否持续修正导航价值场？
        ↓
最终能否形成自动升级、自我进化的 RAG 系统？
```

This reframes retrieval optimization from "find the nearest chunk once" to "learn how to navigate a domain semantic manifold over time."

---

## Layer 1: Verifying the Manifold Hypothesis

The first layer of the research is to show that domain-specific knowledge data is not random scatter in a high-dimensional embedding space. It should have usable structure:

- embeddings concentrate around lower-dimensional effective structure;
- PCA or similar reductions preserve most useful variation;
- clustering reveals semantically coherent local regions;
- domains, intents, document types, or evidence types show spatial regularity;
- local neighborhoods correlate with retrieval relevance and feedback outcomes.

This layer answers:

> Why is it valid to model RAG retrieval as navigation over a semantic manifold?

---

## Layer 2: Self-Evolving Optimization on the Manifold

If the manifold hypothesis holds, RAG should not remain a static nearest-neighbor system. The system should learn:

- which semantic regions are valuable for different query types;
- which retrieval route works best for each query context;
- which user feedback is trustworthy;
- which local feedback should propagate to nearby regions;
- which aliases, corrections, and knowledge gaps should be persisted as system updates.

This layer corresponds to:

- clustering and local semantic-region discovery;
- BM25, dense, and hybrid retrieval inside or across regions;
- LinUCB online navigation;
- multi-dimensional reward from explicit, implicit, and contextual feedback;
- user credibility and anti-poisoning;
- insight extraction, alias expansion, correction memory, and knowledge-gap accumulation;
- future manifold-local feedback propagation.

---

## Dynamic Value Manifold

The central theoretical abstraction is the Dynamic Value Manifold (DVM):

```text
M       = fixed semantic geometry from embeddings
V(x, t) = time-varying value field shaped by feedback
M*      = (M, V), the dynamic value manifold
```

The embedding model defines the relatively stable geometric manifold `M`. User feedback, historical rewards, cluster behavior, domain signals, and credibility shape the value field `V(x, t)`.

LinUCB is one practical parameterization of that value field:

```text
V(x, t) ~= theta(t)^T phi(x)
```

where `phi(x)` contains query, cluster, retrieval, and feedback-context features, and `theta(t)` changes as feedback arrives.

Thus, LinUCB is a mechanism for learning the value field and navigation policy. It is not the research object by itself.

---

## Distinction From Existing RAG Optimization

| Direction | What It Optimizes |
|-----------|-------------------|
| Traditional RAG | Static nearest-neighbor retrieval in embedding space |
| Hybrid RAG | Lexical + semantic scoring |
| Graph / HypRAG / GNN-RAG | Geometry or graph structure `M` |
| IntentWeight | Dynamic value field `V(x, t)` over a fixed domain manifold |

The key distinction is:

> Existing manifold-aware approaches often change or enrich the geometry. IntentWeight keeps the geometry mostly fixed and learns where value lies on that geometry as interactions accumulate.

This makes the system lightweight, CPU-friendly, and suitable for low-data enterprise deployment.

---

## Role of Current and Future Tasks

The current experiment pipeline maps to the theory as follows:

| Task Area | Role in Theory |
|-----------|----------------|
| Static BM25/dense/hybrid baselines | Establish non-learning retrieval baselines |
| Guardrails and comparison tables | Prevent invalid claims across split/sample/task-type boundaries |
| Global LinUCB baseline | First implementation of online value-field learning |
| Manifold-local feedback | Make feedback propagation local in semantic geometry |
| Global vs local comparison | Test whether manifold-aware feedback improves convergence and stability |
| Soft-routed multi-route retrieval | Combine dense/BM25 bypass with LinUCB-selected local manifold retrieval to avoid hard-pruning loss |
| Paper synthesis | Turn the theory and experiments into a coherent system-paper argument |

For Task 11-13, the intended progression is:

1. **Task 11**: evaluate global LinUCB as the online-learning baseline;
2. **Task 12**: implement manifold-local feedback using neighborhood distance, cross-arm decay, and possibly local credibility;
3. **Task 13**: compare global value updates against manifold-local value propagation.
4. **Task 13.5**: replace hard cluster pruning with soft multi-route retrieval, using global dense/BM25 as a recall floor and LinUCB-selected clusters as the adaptive local-manifold route.

---

## Lessons From Task 13.5

Task 13.5 changes the practical interpretation of the method. LinUCB should not
be treated as a replacement for dense retrieval or BM25. Instead, it should be
treated as an adaptive policy over multiple retrieval routes.

Current retrieval routes:

- **global dense**: semantic recall and stable fallback;
- **global BM25**: lexical, entity, term, and exact-match coverage;
- **LinUCB-selected cluster-local dense**: adaptive local-manifold navigation;
- **weighted fusion and dense floor**: reduce the risk that fusion noise removes
  strong dense candidates.

The resulting system is better described as:

> LinUCB-guided adaptive multi-route retrieval over a domain relevance manifold.

This formulation is more defensible than claiming that LinUCB alone should beat
dense retrieval. It also explains the mixed experimental results:

- PubMedQA and Banking77 show that soft routing can recover most hard-pruning
  losses and approach or match dense retrieval.
- CUAD smoke/sample slightly improves over dense under the GT-anchored sample,
  but remains only a smoke result.
- eManual remains below dense, showing that sparse evidence, long-document
  structure, cluster quality, or source-retriever weakness can still dominate.

Therefore the current evidence supports a robustness and adaptivity claim, not a
universal accuracy dominance claim.

---

## Stability, Self-Evolution, and Cost

The current architecture has two near-term advantages and one future-facing
advantage.

**Stability** comes from the dense/BM25 bypass and dense floor. These channels
prevent the system from losing all relevant evidence when LinUCB selects the
wrong cluster arm.

**Self-evolution** comes from feedback-updated LinUCB arms. As interactions
accumulate, LinUCB can learn which local semantic regions and retrieval routes
produce higher reward for each query context. If user credibility scores are
used, feedback can be reliability-weighted so that high-trust users have more
impact on the online value-field update and noisy users have less impact.

**Cost reduction** is not the main property of Task 13.5 itself, because Task
13.5 runs multiple retrieval routes for robustness. The cost advantage should be
framed as a later cost-aware phase:

```text
reward = quality - lambda_cost * retrieval_cost
                 - lambda_token * context_tokens
                 - lambda_latency * latency
```

After LinUCB becomes confident in specific arms, the system can reduce global
dense/BM25 depth or weight, rely more on high-confidence cluster-local retrieval,
and shrink rerank candidates and final LLM context. This gives a plausible path
from robust retrieval to cost-aware adaptive pruning.

---

## One-Sentence Positioning

English:

> IntentWeight frames self-evolving RAG as online value-field learning on a domain-specific semantic manifold: dense/BM25 provide a stable recall floor, clustering exposes local semantic regions, and LinUCB with reliability-weighted feedback learns which retrieval routes are valuable and how that value should evolve over time.

Chinese:

> IntentWeight 将自进化 RAG 建模为垂类语义流形上的在线价值场学习：dense/BM25 提供稳定召回底座，聚类识别局部语义区域，LinUCB 结合可信反馈持续学习不同检索路径的价值分布和导航策略，从而推动 RAG 系统自动优化、升级，并在后续阶段具备成本自适应压缩的潜力。
