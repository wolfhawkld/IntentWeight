# Task56 Claim-Evidence Alignment

Updated: 2026-06-24

## Objective

Align the current paper claims with the completed evidence after Task53,
Task54, and Task55. This task does not add new experiments. It defines which
claims are now well supported, which claims require careful boundaries, and
which claims should remain out of the paper.

The central purpose is to preserve claim height while making the support
structure cleaner: manifold-inspired motivation, measured geometry diagnostics,
matched-backbone route-and-budget experiments, strong baseline comparisons,
and stability checks should reinforce one coherent argument rather than appear
as separate task fragments.

## Core Narrative

The defensible narrative is:

1. The manifold hypothesis motivates the expectation that semantic retrieval
   corpora may contain local relevance structure.
2. LoTTE geometry diagnostics confirm that the evaluated corpora have usable
   local structure, including high nearest-cluster GT routing signal and
   non-random context retention.
3. IntentWeight operationalizes this structure as a route-and-budget
   controller, not as a pure geometry retriever.
4. Dense retrieval remains a recall floor. BM25, cluster-local retrieval,
   LinUCB route learning, and final context-budget control are combined rather
   than treated as replacements for dense retrieval.
5. Matched-backbone experiments with MiniLM, BGE, and E5 test whether the
   quality-cost pattern is tied to one embedding model.
6. The completed evidence supports a statistically checkable quality-cost
   trade-off: dense-level or near-dense answer support can be preserved while
   reducing final evidence-context tokens, and a BGE quality-first operating
   point can exceed its dense baseline while still saving tokens.

The claim should not be written as theorem-level manifold proof or universal
dominance over dense retrieval.

## Claim Ledger

| Claim | Current status | Primary evidence | Paper-facing wording |
| --- | --- | --- | --- |
| IntentWeight is a manifold-inspired route-and-budget controller for evidence selection. | Supported as method framing | Task30, Task43, Task36.1, method design | Use "manifold-inspired" and "piecewise relevance-manifold assumption"; avoid "manifold-proven". |
| The evaluated LoTTE corpora have usable local geometry for routing. | Supported diagnostically | Task30 technology/search, Task43 science/search | Geometry provides routing signal but cannot replace dense retrieval alone. |
| IntentWeight can reduce final evidence-context tokens while preserving dense-level or near-dense Hit@10. | Strong main claim | Task38, Task39, Task53, Task55 | Use calibrated/frozen and matched-backbone evidence; state strict non-inferiority remains setting-dependent. |
| The result is not MiniLM-specific. | Strengthened by Task53/55 | MiniLM, BGE-base, E5-base matched-backbone runs | Claim backbone-level robustness of the trade-off pattern, not universal encoder dominance. |
| A quality-first BGE operating point can exceed BGE dense while saving tokens. | Supported but scope-limited | Task54, Task55 | Present as BGE/LoTTE 100k tunability evidence, not as all-backbone behavior. |
| SentMMR and cross-encoder baselines invalidate the method. | Rejected by decomposition | Task46, Task47, Task48, Task49 | SentMMR is a shared compressor; cross-encoder is a late reranker; IntentWeight controls route and budget upstream. |
| Aggressive gated-cost routing always preserves quality. | Not supported | Task53, Task55 | Treat BGE/E5 gated variants as boundary evidence showing over-compression cost. |
| IntentWeight universally dominates dense retrieval. | Not supported | Task27, eManual/CUAD limitations, Task52/53 | Avoid. Dense remains a recall floor and strong baseline. |
| Geometry alone explains retrieval gains. | Not supported | Task30, Task43, ablations | Avoid. Geometry is one signal inside a multi-route controller. |
| Full end-to-end answer quality superiority is proven. | Not supported | Task33.5 only a smoke check | Limit main claim to retrieval-backed evidence support and final context tokens. |

## Evidence Map

| Evidence group | Main artifacts | What it supports | Best placement |
| --- | --- | --- | --- |
| Geometry diagnostics | Task30, Task43, Task36.1 | Manifold-inspired motivation and usable routing signal | Method motivation, results geometry table/figure, limitations |
| Calibrated context-budget validation | Task38 | Frozen policy selection, final context token savings, dense adaptive truncation defense | Main results |
| Cross-domain LoTTE validation | Task39 | Science/search transfer and calibration boundary | Main or appendix depending space |
| Strong compressor/reranker baselines | Task46, Task47, Task48, Task49 | IntentWeight is complementary to SentMMR and cross-encoder reranking | Related work/results discussion |
| Strong embedding baseline | Task52 | BGE raises dense floor and motivates matched-backbone testing | Baseline setup or appendix |
| Matched-backbone generalization | Task53 | MiniLM/BGE/E5 quality-cost trade-off under same backbone comparison | Main robustness table |
| Positive-hit tunability | Task54 | BGE quality-first point above dense with token saving | Main table if space allows; otherwise highlighted appendix result |
| Seed stability | Task55 | Fixed-seed stability; not seed search | Statistical robustness appendix or brief main-text sentence |
| Validation guardrail | Task51 | Dimension, statistics, ranking artifacts, display readiness | Reproducibility appendix |

## Recommended Main Claims

Use these as the highest-strength defensible claims:

1. IntentWeight is a geometry-inspired, feedback-adaptive route-and-budget
   controller for retrieval-backed evidence selection.
2. On LoTTE, measured local geometry supports the design assumption that
   cluster-local evidence can be useful for routing, while dense retrieval must
   remain available as a recall floor.
3. Under calibrated/frozen evaluation, IntentWeight can reduce final
   evidence-context tokens while preserving dense-level or near-dense
   sufficient-evidence Hit@10.
4. Under matched-backbone comparison, the quality-cost trade-off persists
   across MiniLM, BGE-base, and E5-base; BGE and E5 full multi-route settings
   save about 12% final context tokens with small average Hit@10 deltas.
5. A BGE quality-first operating point exceeds BGE dense Hit@10 by `+0.88pp`
   on average across fixed seeds while still saving `7.23%` final context
   tokens.
6. Strong post-retrieval components do not replace the route-and-budget
   question: SentMMR compresses final contexts, cross-encoders rerank selected
   candidates, and IntentWeight controls which evidence pool and budget enter
   those later stages.

## Wording To Use

Recommended English wording:

> Inspired by the manifold hypothesis, we first diagnose whether the retrieval
> corpus exhibits exploitable local geometry in embedding space. The observed
> cluster-level signal motivates IntentWeight as a feedback-adaptive
> route-and-budget controller rather than as a stand-alone geometric retriever.
> Across calibrated and matched-backbone experiments, IntentWeight preserves
> dense-level or near-dense answer support while reducing final evidence-context
> tokens, and a BGE quality-first operating point exceeds the BGE dense
> baseline with lower context cost.

Recommended Chinese wording:

> 本文不是用流形假设直接证明方法有效，而是先用几何诊断确认目标检索语料
> 存在可利用的局部结构，再将这种结构转化为反馈自适应的 route-and-budget
> controller。实验显示，在校准/冻结和 matched-backbone 对比下，IntentWeight
> 可以在保持 dense-level 或 near-dense answer support 的同时减少最终
> evidence-context tokens；其中 BGE 的 quality-first operating point 还能在
> 低于 dense context cost 的情况下取得略高于 BGE dense 的 Hit@10。

## Wording To Avoid

Avoid these claims:

- "The manifold hypothesis is proven."
- "Geometry alone explains the gains."
- "IntentWeight universally dominates dense retrieval."
- "All embedding backbones show positive-Hit improvement."
- "Seed variation was used to find the best seed."
- "Chunk-support Hit@10 proves final answer quality."
- "Candidate retrieval cost is equivalent to LLM context-token cost."

## Table And Figure Placement

Recommended main-paper display:

| Slot | Content | Rationale |
| --- | --- | --- |
| Main Table 1 | Dataset and metric roles | Prevents overclaiming across heterogeneous datasets. |
| Main Table 2 | Calibrated/frozen context-budget frontier | Main efficiency claim. |
| Main Table 3 | Matched-backbone MiniLM/BGE/E5 comparison | Supports backbone robustness. |
| Main Figure 1 | System/controller diagram | Shows route-and-budget decomposition. |
| Main Figure 2 | Token-quality frontier | Makes trade-off visible. |
| Main Figure 3 | Geometry diagnostic trend | Connects manifold-inspired motivation to measured structure. |

Recommended appendix or supplement:

| Appendix item | Content |
| --- | --- |
| Strong baselines | SentMMR, compressor-normalized comparison, cross-encoder reranker |
| Stability | Task55 fixed-seed table and per-seed rows |
| Positive-Hit detail | Task54 BGE policy scan and paired statistics |
| Guardrails | Task51 audit, cost-layer separation, historical corrections |
| Limitations | E5 no positive-Hit point, gated-cost quality loss, eManual/CUAD boundary cases |

If page budget is tight, keep the matched-backbone table in the main paper and
move the full strong-baseline details to the appendix while summarizing their
conclusion in the results discussion.

## Statistical Framing

Use query-level paired statistics as the primary inferential evidence:

- paired bootstrap confidence intervals;
- McNemar tests for query-level Hit@10 changes;
- frozen calibration/test selection where available.

Use seed-level summaries as stability diagnostics:

- fixed seeds `13,17,19` are replicate conditions;
- the purpose is not seed search;
- three-seed intervals are engineering stability checks, not large-sample
  random-effects proof.

This framing lets the paper keep a strong claim while remaining defensible:
the main result is statistically checkable at the query level and stable under
fixed-seed replicate conditions.

## Revision Guidance

When the manuscript is next updated:

1. Update the abstract and conclusion to mention matched-backbone robustness,
   not only MiniLM-scale experiments.
2. Add a compact BGE/E5 matched-backbone table to the results or appendix.
3. Keep the BGE positive-Hit point as tunability evidence, with the E5 caveat.
4. Keep dense retrieval as the recall floor throughout the paper.
5. Rephrase manifold language as motivation plus diagnostic support, not proof.
6. Keep the answer-quality boundary: the current main metric is
   retrieval-backed answer support, not full human answer evaluation.

