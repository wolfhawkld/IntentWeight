# Task21 Paper-Ready Evidence Summary

Updated: 2026-05-07

Note: Task23 extends the LoTTE scale-up evidence through 400k and full 638k.
For the latest large-scale quality-cost tables and paper-facing scale-up claim,
use `paper/experiments/task23_lotte_scaleup_summary.md`.

This document consolidates the experimental evidence from Task1-Task20 into a
paper-facing argument. It should be read as a bounded claim: IntentWeight is not
a universal replacement for dense retrieval. The supported claim is that
feedback-driven adaptive multi-route retrieval can learn a useful routing value
field and expose a controllable quality-cost frontier in vertical-domain RAG.

## Core Claim

IntentWeight models vertical-domain RAG retrieval as adaptive route selection
over a piecewise query-document relevance manifold. Dense and BM25 provide
global recall floors, clustering exposes local semantic regions, and LinUCB
with reliability-weighted feedback learns when each route is valuable. In
large-scale LoTTE, this produces a tunable quality-cost frontier and a
conditional dense fallback point that exceeds the dense baseline while reducing
dense usage.

## Claim Boundaries

Supported:

- Multi-route retrieval can exceed dense-only on large-scale vertical-domain
  evidence retrieval when dense remains available as a recall floor/fallback.
- Trust-weighted feedback improves the learned policy value field, measured by
  last-epoch true reward and selected-cluster hit evolution.
- Manifold geometry diagnostics can explain when the method is likely to work
  and when it is likely to fail or underperform.
- Cost-aware gating creates a controllable Pareto frontier between quality and
  dense/candidate cost.

Not supported:

- The method is not an unconditional low-cost replacement for dense retrieval.
- The method does not dominate dense-only on every dataset.
- CUAD smoke/sample results should not be used as full-corpus evidence.
- eManual underperformance should not be treated as proof that the manifold
  assumption is absent; duplicate/weak-label and strict chunk-id effects are
  major confounders.

## Dataset Roles

| Dataset | Role | Scope used | Main use in paper | Caveat |
| --- | --- | --- | --- | --- |
| PubMedQA | Evidence retrieval | full/train/full | Feedback and manifold-local proof-of-concept | GT is abstract context section-level, not strict answer sentence evidence |
| Banking77 | Intent/domain routing proxy | heldout_test/test/full | Strong feedback self-evolution and intent manifold proxy | Do not mix with evidence retrieval main claims |
| eManual | Failure/limitation case | heldout_test/test/full | Diagnoses weak strict-evidence performance | Heavy duplicate text and strict chunk-id mismatch |
| CUAD | Sparse smoke/sample | test/gt_anchored_10000 | Sparse legal-domain limitation and guardrail case | Not full-corpus held-out evidence |
| LoTTE technology/search 100k | Large-scale vertical evidence retrieval | heldout_test/test/full | Main large-scale quality-cost and fallback evidence | No true corpus topic labels in processed qrels schema |

## Static Retrieval Baselines

Dense uses `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine.

| Dataset | BM25 R@10 | Dense R@10 | Hybrid R@10 | Interpretation |
| --- | ---: | ---: | ---: | --- |
| PubMedQA | 0.9770 | 0.9930 | 0.9890 | Dense is near ceiling |
| eManual | 0.1154 | 0.3231 | 0.1692 | Dense is strongest but strict evidence recall remains low |
| Banking77 | 0.9698 | 0.9805 | 0.9851 | Intent proxy is near ceiling |
| CUAD smoke | 0.0506 | 0.0759 | 0.0633 | Sparse smoke only, weak recall |
| LoTTE 100k | 0.7232 | 0.8674 | 0.8624 | Dense is a strong large-scale baseline |

## LinUCB Evolution Across Tasks

| Task | Mechanism | Strong positive evidence | Limitation |
| --- | --- | --- | --- |
| Task11 | Global LinUCB over fixed KMeans arms | Establishes no-leakage prequential baseline | Hard cluster routing is weak for evidence retrieval |
| Task12/13 | Manifold-local feedback propagation | PubMedQA improves R@10 from 0.5480 to 0.6607; Banking77 from 0.7215 to 0.8247 | eManual and CUAD do not improve |
| Task13.5 | Soft multi-route retrieval with dense/BM25/cluster/LinUCB | PubMedQA 0.9920, Banking77 0.9831, CUAD smoke 0.0844 | eManual remains far below dense |
| Task15 | Trust-weighted feedback | PubMedQA last true reward 0.8727 with +0.4030 gain; Banking77 full last true reward 0.9805 with +0.1317 gain | Final R@10 may already be near ceiling and not move much |
| Task16 | Cost-aware gating | PubMedQA and Banking77 cut source candidate cost by about half with small R@10 loss | eManual/CUAD lose recall under aggressive gating |

## Manifold Diagnostics

| Dataset | PCA dim 90% | Local purity | Nearest cluster hit@3 | Context R@10 | Dense R@10 | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| PubMedQA | 177 | 0.2439 | 0.9680 | 0.9860 | 0.9930 | Strong GT-cluster routing signal |
| eManual | 111 | 0.0169 | 0.8923 | 0.3615 | 0.3231 | Geometry can route to GT clusters, but learned arm/fusion underuses it |
| Banking77 | 105 | 0.8539 | 0.9968 | 0.9782 | 0.9805 | Strong intent-proxy manifold signal |
| CUAD smoke | 182 | 0.0716 | 0.6076 | 0.0759 | 0.0759 | Sparse and weak local signal |
| LoTTE 100k | 182 | n/a | 0.8809 | 0.7836 | 0.8674 | Usable retrieval geometry but dense still needed |

## LoTTE 100k Main Evidence

LoTTE 100k is the main large-scale vertical evidence retrieval setting:
`101311` corpus chunks, `596` held-out test queries, `2045` GT refs.

| Setting | R@10 | MRR@10 | nDCG@10 | Last reward | Reward gain | Avg source cost | Dense query rate | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BM25 baseline | 0.7232 | - | - | - | - | - | - | Lexical baseline |
| Dense baseline | 0.8674 | 0.7081 | 0.6487 | - | - | 100.00 | 1.0000 | Strong semantic baseline |
| Hybrid baseline | 0.8624 | 0.6973 | 0.6216 | - | - | 200.00 | 1.0000 | RRF hybrid slightly below dense |
| Task18 full multi-route | 0.8826 | 0.7105 | 0.6573 | 0.5671 | +0.2880 | 300.00 | 1.0000 | Stable multi-seed gain over dense |
| Task18 gated | 0.8440 | 0.6950 | 0.5889 | 0.5923 | +0.2931 | 191.68 | 0.8220 | Cost saving but recall below dense |
| Task19-D | 0.8770 | 0.7065 | 0.6321 | 0.6074 | +0.3160 | 229.97 | 0.9029 | Quality-first Pareto point above dense |
| Task19-E | 0.8865 | 0.7116 | 0.6508 | 0.6370 | +0.3507 | 258.84 | 0.9489 | Highest quality but dense-heavy |
| Task20-S | 0.8747 | 0.7071 | 0.6308 | 0.6074 | +0.3160 | 227.29 | 0.8945 | Best conditional fallback point |

## LoTTE Incremental Scale-Up

Task22 begins the move from the 100k reference to larger LoTTE corpora. Task22.2
uses `201010` corpus chunks, `596` held-out test queries, and `2045` GT refs
with 100% GT coverage.

| Setting | R@10 | MRR@10 | nDCG@10 | Last reward | Reward gain | Avg source cost | Dense query rate | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BM25 200k | 0.6292 | 0.4572 | 0.3832 | - | - | - | - | Lexical baseline drops with more distractors |
| Dense 200k | 0.7970 | 0.6279 | 0.5643 | - | - | 100.00 | 1.0000 | Strong baseline but lower than 100k dense |
| Hybrid 200k | 0.8003 | 0.6045 | 0.5323 | - | - | 200.00 | 1.0000 | Slightly above dense in recall |
| Task22.2 full multi-route | 0.8300 | 0.6326 | 0.5720 | 0.5078 | +0.2875 | 300.00 | 1.0000 | Still above dense at 200k |
| Task22.2 gated | 0.8154 | 0.6305 | 0.5472 | 0.5677 | +0.3395 | 232.01 | 0.9027 | Above dense with lower source cost than full |

This strengthens the scale argument. As corpus size increases from 100k to
200k, static baselines degrade, but adaptive full/gated multi-route retrieval
still remains above dense-only. The next scale checkpoint should be 400k before
attempting the full `638509`-passage corpus.

## Task19 vs Task20 Interpretation

Task19 is the hypothesis/Pareto validation stage. It shows that gated
multi-route retrieval has a real quality-cost control surface: medium-cost
settings remain below dense, while conservative quality-first settings D/E
exceed dense by increasing fallback.

Task20 is the optimization stage based on Task19. It asks whether dense can be
reduced from a permanent main route into a conditional fallback. Task20-S shows
that confidence/drift-only fallback can exceed dense baseline while keeping
dense query rate below `0.90`, and slightly improves the cost side relative to
Task19-D. Reward-drop fallback is useful diagnostically, but the current M/H
runs show it can increase fallback cost without reliably improving quality.

## Failure And Limitation Cases

| Case | Observed behavior | Interpretation |
| --- | --- | --- |
| eManual | Dense R@10 0.3231, soft routing 0.1436, trust feedback 0.1487 | Strict chunk-id recall, duplicate sentence text, and weak labels dominate |
| CUAD smoke | Results are low even after GT-anchored sampling | Sparse GT and sampling constraints make this a limitation/smoke case |
| Aggressive cost routing | Task20-L cost 143.22, dense rate 0.5405, but R@10 0.7383 | Large dense savings are possible, but quality loss is unacceptable |
| Reward-drop fallback | Task20-M/H increase fallback/cost but do not dominate Task20-S | Reward-window fallback should be optional safety logic, not the default best configuration |

## Paper-Ready Research Questions

| Research question | Evidence | Answer |
| --- | --- | --- |
| Does vertical-domain RAG expose usable geometry? | PubMedQA, Banking77, LoTTE manifold diagnostics | Yes, but strength varies by dataset |
| Does feedback improve the learned routing value field? | Task15 last true reward and selected-cluster hit gains | Yes, especially PubMedQA and Banking77 |
| Can multi-route LinUCB exceed dense on large-scale evidence retrieval? | Task18 full, Task19-D/E, Task20-S on LoTTE 100k | Yes, when dense remains a recall floor/fallback |
| Can the system reduce dense usage while staying competitive? | Task16, Task19, Task20 | Yes, but only within a quality-cost trade-off |
| Is the method universally better than dense? | eManual, CUAD, Task20-L | No |

## Recommended Paper Claim

English:

> IntentWeight is a feedback-driven adaptive retrieval policy for vertical-domain
> RAG. It combines dense, BM25, cluster-local retrieval, and LinUCB routing under
> a piecewise relevance-manifold assumption. Experiments show that the method
> can learn useful routing value from trust-weighted feedback, expose a
> controllable quality-cost frontier, and exceed a strong dense baseline on
> LoTTE 100k when dense is retained as a conditional fallback.

Chinese:

> IntentWeight 是一种面向垂类 RAG 的反馈驱动自适应检索策略。它在分片相关性流形假设下结合 dense、BM25、聚类局部召回与 LinUCB 路由，通过可信反馈学习不同检索路径的价值。实验表明，该方法能够形成可调节的质量-成本边界，并在 LoTTE 100k 大规模垂类检索中，在保留 dense 作为条件兜底通道的前提下超过强 dense baseline。

## Suggested Main Tables For The Paper

1. Static retrieval baselines: BM25, dense, hybrid across PubMedQA, eManual,
   Banking77, CUAD smoke, LoTTE 100k.
2. Manifold diagnostics: local geometry and GT cluster routing indicators.
3. Feedback self-evolution: none vs trust-weighted vs oracle/equal-noisy.
4. LoTTE 100k quality-cost frontier: dense, Task18 full/gated, Task19-D/E,
   Task20-S.
5. Limitation cases: eManual, CUAD, aggressive low-cost routing.
