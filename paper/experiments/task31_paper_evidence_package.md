# Task31 Paper Evidence Package

Updated: 2026-05-27

Task31 is the paper-writing handoff document. It consolidates the current
experimental evidence into claims, tables, limitations, and section-level
writing guidance. It does not introduce new experiments.

## Final Thesis

IntentWeight is a feedback-driven adaptive retrieval controller for
vertical-domain RAG. It combines dense retrieval, BM25 lexical recall,
cluster-local retrieval, and LinUCB route selection under a piecewise
query-document relevance-manifold assumption. The strongest current evidence is
not that the method universally beats dense retrieval, but that it can use
feedback and route confidence to control final context budget while preserving
dense-level retrieval quality on large-scale vertical-domain retrieval.

The paper should emphasize:

- adaptive route control over a multi-route retrieval surface;
- trust-weighted simulated feedback as a policy self-evolution mechanism;
- geometry-aware routing as a diagnostic and control signal;
- final context-token reduction through confidence-based context compaction;
- bounded claims against strong dense baselines.

## Claim Ledger

| Claim | Status | Evidence | Paper Wording |
|---|---|---|---|
| IntentWeight can reduce final retrieved context tokens while preserving retrieval quality | Strong | Task29-C 100k/200k/400k/638k, Task29.3 CI | Main efficiency claim |
| IntentWeight has mean above-dense Hit@10 on larger LoTTE scales while using fewer final context tokens | Strong as mean result on LoTTE 200k/400k/638k; CI-level confirmation strongest at 200k | Task29.1/29.2/29.3 | Main large-scale result |
| Trust-weighted feedback improves the learned route policy | Strong as simulated online evidence | Task15, Task25 route-level credit | Feedback self-evolution claim |
| Geometry is useful for route control | Supported diagnostically | Task14, Task24 static nearest, Task30 | Theoretical support, not theorem |
| LinUCB alone explains all quality gains | Not supported | Task24 static/naive ablations | Avoid |
| Candidate cost reduction implies LLM token saving | Rejected | Task28/28.1 | Explicitly correct |
| Method universally dominates dense | Not supported | eManual, CUAD, Task27 | Avoid |
| Full end-to-end LLM answer quality is proven | Not supported | Task33.5 is a small smoke only | Avoid; use only as sanity check |
| Task29-C does not obviously degrade downstream generation quality | Weak smoke support | Task33.5 60-query generation smoke | Optional appendix / sanity check |
| Result is tied to one exact encoder | Reduced risk | Task33.1a multi-qa MiniLM robustness | Robustness, not universal encoder claim |

## Main Result Table

Use Task29-C as the main result because it directly measures final context
tokens. Earlier source-candidate cost results should not be used as the headline
token-efficiency result.

| Scale | Corpus | Dense Hit@10 | Task29-C Hit@10 | Hit Delta | Dense Tokens@10 | Task29-C Tokens@10 | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE 100k | 101311 | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| LoTTE 200k | 201010 | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| LoTTE 400k | 400674 | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| LoTTE 638k | 638509 | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

Seed-level stability from Task29.3:

| Scale | Task29-C Hit@10 mean | Hit@10 95% CI | Token saving mean | Token saving 95% CI |
|---|---:|---:|---:|---:|
| 100k | 0.8652 | [0.8565, 0.8739] | 4.83% | [2.89%, 6.77%] |
| 200k | 0.8249 | [0.8052, 0.8446] | 4.69% | [3.89%, 5.48%] |
| 400k | 0.7819 | [0.7709, 0.7929] | 5.32% | [0.11%, 10.53%] |
| 638k | 0.7466 | [0.7246, 0.7687] | 4.86% | [4.24%, 5.48%] |

Use the confidence intervals as engineering stability diagnostics. With only
three seeds, do not frame them as strong statistical significance proof.
The 400k token-saving CI is notably wider than the other scales and should be
acknowledged as seed-level variance in route confidence and context-budget
control.

Task33.6 extends the LoTTE 100k Task29-C setting from three to five seeds. The
five-seed mean is Hit@10 `0.8708` versus dense `0.8674`, with final context
token ratio `0.9507x`. The Hit delta CI overlaps zero, so this strengthens
stability but does not justify a statistical-superiority claim at 100k.

## Mechanism Evidence

| Mechanism | Supporting Tasks | Evidence | Interpretation |
|---|---|---|---|
| Multi-route retrieval surface | Task13.5, Task18, Task22/23 | Full multi-route improves coverage in large LoTTE settings when dense remains available | Dense/BM25/cluster fusion improves coverage but does not replace dense |
| Trust-weighted feedback | Task15, Task25, Task33.2 | Last true reward and selected-cluster hit improve under trust weighting | Simulated feedback can optimize the policy value field |
| Route-level credit assignment | Task25 | `cluster_only/value` raises selected-cluster hit from 0.6908 to 0.7223 on LoTTE 100k | LinUCB can improve the selected cluster route itself |
| Static geometry baseline | Task24 | Static nearest has selected-cluster hit 0.9016 on 638k | Geometry is strong and must be treated as a baseline, not hidden inside LinUCB |
| Final context compaction | Task29 | Task29-C lowers final context tokens at all LoTTE scales | The true token-saving mechanism is final context-budget control |
| Geometry validation | Task30 | Nearest-cluster hit@3 stays around 0.87-0.90 across LoTTE scales | Manifold framing is diagnostically supported |
| Embedding robustness | Task33.1a | Multi-qa MiniLM preserves the bounded claim on LoTTE 100k | Not tied to one exact MiniLM encoder |
| Downstream generation smoke | Task33.5 | Dense and Task29-C have equal non-tie wins on 60 LoTTE queries | No obvious degradation; not full answer-quality proof |

## Geometry Evidence

Task30 shows that LoTTE retains usable geometric routing signal as scale grows:

| Scale | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Task29 Hit Delta |
|---|---:|---:|---:|---:|---:|
| 100k | 182 | 0.6437 | 0.8870 | 0.9033 | -0.22 pp |
| 200k | 186 | 0.6292 | 0.8697 | 0.8947 | +2.80 pp |
| 400k | 190 | 0.6110 | 0.9016 | 0.8826 | +1.01 pp |
| 638k | 196 | 0.5867 | 0.9016 | 0.8571 | +1.85 pp |

Recommended wording:

> The diagnostics support a piecewise relevance-manifold assumption: local
> cluster geometry is informative for routing, but not sufficient to replace
> dense retrieval. IntentWeight uses geometry as one signal in a feedback-driven
> controller rather than treating it as a complete retrieval model.

Avoid wording:

> The manifold hypothesis is proven, and geometry alone explains the gain.

## Cost Layer Separation

Task28 and Task28.1 corrected the cost story. The paper must keep three cost
layers separate:

| Layer | Meaning | Supported By | Paper Use |
|---|---|---|---|
| Source candidate cost | Number of candidates considered before fusion | Task16-27 | Retrieval-stage efficiency / ablation |
| Dense invocation rate | Fraction of queries using global dense path | Task16-27, Task29 | Dense-compute proxy |
| Final context tokens | Retrieved chunk tokens sent to generator | Task28/28.1/29 | Main token-efficiency metric |

Strong statement:

> Confidence-based final context compaction reduces retrieved context tokens by
> about 4.7-5.3% across LoTTE 100k-638k while preserving dense-level Hit@10;
> mean Hit@10 is above dense on 200k, 400k, and 638k.

Do not write:

> Earlier candidate-cost reductions prove lower LLM token cost.

## Dataset Roles

| Dataset | Role | Use In Paper | Caveat |
|---|---|---|---|
| LoTTE technology/search | Main vertical evidence retrieval benchmark | Main scale-up, token-quality frontier, geometry validation | No true corpus topic labels in processed qrels |
| PubMedQA | Feedback/manifold proof-of-concept | Shows manifold-local and trust feedback can improve policy | GT is abstract-level context, not strict answer sentence |
| Banking77 | Intent/domain routing proxy | Shows strong feedback self-evolution and intent structure | Do not mix with evidence retrieval main table |
| eManual | Failure/limitation case | Shows duplicate text and strict chunk-id issues | Low strict recall is not proof geometry is absent |
| CUAD | Sparse smoke/stress case | Shows sparse legal-domain limitation | GT-anchored sample only, not full-corpus main evidence |

## Recommended Paper Structure

### Abstract

Include:

- vertical-domain RAG faces a coverage-efficiency-quality trade-off;
- IntentWeight treats retrieval route selection as a contextual bandit problem;
- method combines dense, BM25, cluster-local retrieval, trust-weighted feedback,
  and confidence-based final context control;
- on LoTTE up to 638k chunks, conservative context control reduces final
  retrieved context tokens by about 4.7-5.3% and has mean above-dense Hit@10 on
  200k/400k/638k.

Avoid:

- claiming real human feedback was used;
- claiming full end-to-end LLM answer-quality superiority;
- claiming universal superiority over dense retrieval.

### Introduction

Main argument:

1. RAG retrieval must trade off coverage, precision, latency, and context cost.
2. Dense retrieval is strong, but single-route retrieval has limited adaptive
   control under heterogeneous vertical-domain workloads.
3. Vertical-domain corpora often exhibit local semantic/lexical/behavioral
   structure that can be treated as a piecewise relevance manifold.
4. IntentWeight learns a feedback-updated retrieval policy over this surface.

### Method

Describe:

- corpus chunks embedded by `sentence-transformers/all-MiniLM-L6-v2`;
- KMeans/MiniBatchKMeans fixed arms for LinUCB compatibility;
- routes: dense, BM25, cluster-local dense, hybrid-lite/full fallback;
- LinUCB context features and trust-weighted simulated reward;
- `cluster_only` credit assignment for route-level learning;
- `confidence_topk` final context policy.

Be explicit that KMeans is chosen for fixed arm count and reproducibility, not
because it is claimed to be the globally best clustering algorithm.

### Experiments

Suggested table order:

1. Dataset/split/guardrail table.
2. Static baselines: BM25, dense, hybrid.
3. Feedback self-evolution: none/equal/trust/oracle or route reward metrics.
4. LoTTE source-candidate scale-up and ablations.
5. Task29 final context-token frontier.
6. Robustness and sanity checks from Task33.
7. Geometry diagnostics and failure cases.

### Discussion

Emphasize:

- dense remains a strong recall floor;
- geometry helps route control but is not enough alone;
- final token savings require explicit final context compaction;
- Task29-C is the conservative operating point on a quality-token frontier, not
  the maximum-saving policy;
- query-level Hit@10 is the headline; evidence completeness can drop under
  compaction and should be discussed for complete-evidence applications;
- online user feedback in production should be trust-weighted and guarded;
- future work should test real human feedback, stronger dense encoders, larger
  generation studies, and end-to-end human evaluation.

## Reviewer Risk Checklist

| Risk | Mitigation |
|---|---|
| "Dense is stronger on some datasets" | State the method is not universal; LoTTE large-scale is the main positive domain |
| "Cost metric is confused" | Use Task29 final context tokens as main cost metric; label candidate cost separately |
| "Prequential uses test feedback" | Describe as simulated test-time adaptation, not offline IID held-out generalization |
| "Feedback is simulated" | State explicitly; treat as controlled policy-learning validation |
| "Static geometry baseline is strong" | Include Task24; position LinUCB as adaptive controller, not sole source of one-shot gain |
| "Manifold claim is vague" | Use Task14/30 diagnostics and bounded language |
| "Only retrieval, no LLM generation" | Task33.5 adds a small LLM smoke; still limit main claim to retrieval/context tokens |
| "Only one encoder" | Task33.1a adds a multi-qa MiniLM-family robustness check; still avoid universal encoder claims |
| "Only three seeds" | Task33.6 adds five-seed LoTTE 100k stability; larger scales remain three-seed diagnostics |
| "400k CI is wide" | Acknowledge higher seed variance in route confidence/context compaction; avoid significance claims |
| "No-feedback row is strong" | Explain that no-feedback falls back to full dense/multi-route retrieval and does not learn efficient routing |
| "evidence_recall drops" | State that compaction optimizes query-level usable evidence, not exhaustive evidence collection |

## Final Paper Claim

Recommended English wording:

> We propose IntentWeight, a feedback-driven adaptive retrieval controller for
> vertical-domain RAG. Under a piecewise relevance-manifold assumption, it
> combines dense, BM25, and cluster-local retrieval with trust-weighted LinUCB
> route learning and confidence-based final context compaction. Experiments on
> LoTTE technology/search up to 638k corpus chunks show that the conservative
> policy reduces final retrieved context tokens by approximately 4.7-5.3% and
> has mean above-dense Hit@10 on 200k, 400k, and 638k scales. Diagnostics and
> ablations indicate that geometry provides useful routing signal, while dense
> remains an important recall floor.

Recommended Chinese wording:

> IntentWeight 是一种面向垂类 RAG 的反馈驱动自适应检索控制器。它在分片相关性流形假设下，将 dense、BM25、聚类局部召回、可信反馈加权 LinUCB 路由学习，以及基于置信度的最终 context 压缩结合起来。LoTTE technology/search 在最高 638k 语料规模上的实验显示，保守策略可将最终检索 context token 降低约 4.7-5.3%，并在 200k、400k、638k 规模上取得均值高于 dense-only 的 Hit@10。诊断和消融表明，几何结构能够提供有效路由信号，但 dense 仍是重要召回兜底。

## Source Artifacts

- Main token frontier: `paper/experiments/task29_2_token_quality_frontier.md`
- Task29 detailed summary: `paper/experiments/task29_confidence_context_policy_summary.md`
- Seed CI: `paper/experiments/results/task29_3_seed_variance_ci.md`
- Geometry validation: `paper/experiments/task30_lotte_geometry_scale_validation.md`
- Historical token correction: `paper/experiments/task28_1_context_token_backfill_summary.md`
- Academic audit fixes: `paper/experiments/task24_audit_fixes_summary.md`
- Credit assignment: `paper/experiments/task25_credit_assignment_summary.md`
- LoTTE source-candidate scale-up: `paper/experiments/task23_lotte_scaleup_summary.md`
- Multi-embedding robustness: `paper/experiments/task33_1a_multiqa_minilm_robustness_summary.md`
- Feedback sensitivity: `paper/experiments/task33_2_feedback_sensitivity_summary.md`
- Clean ablation table: `paper/experiments/task33_3_clean_ablation_table.md`
- LLM generation smoke: `paper/experiments/task33_5_llm_generation_smoke_summary.md`
- Additional seed stability: `paper/experiments/task33_6_additional_seeds_summary.md`
- Pre-writing consistency audit: `paper/experiments/task33_7_pre_writing_consistency_audit.md`
