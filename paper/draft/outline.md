# Paper Outline

Updated: 2026-06-11

## Working Titles

1. IntentWeight: Feedback-Driven Adaptive Retrieval Control for Vertical-Domain RAG
2. IntentWeight: Contextual Bandit Routing for Efficient Vertical-Domain RAG
3. Adaptive Multi-Route Retrieval under a Piecewise Relevance-Manifold Assumption

Recommended title for the first complete draft:

**IntentWeight: Feedback-Driven Adaptive Retrieval Control for Vertical-Domain RAG**

## Core Thesis

Vertical-domain RAG systems must trade off retrieval coverage, precision,
latency, and final context budget. Dense retrieval is a strong recall floor, but
a single fixed route has limited control over heterogeneous query types and
cost-sensitive deployment. IntentWeight treats retrieval as a feedback-driven
route-control problem: it combines dense, BM25, and cluster-local routes, learns
route value with trust-weighted LinUCB, and applies confidence-based final
context compaction.

The current evidence supports a bounded claim:

- IntentWeight preserves near-dense quality on LoTTE 100k and has mean Hit@10
  above dense on LoTTE 200k, 400k, and 638k.
- It reduces final retrieved context tokens by about 4.7-5.3% across these
  LoTTE scales under the conservative Task29-C policy.
- Calibration/test validation shows 6-18% final evidence-context token savings
  under frozen budget selection, with scale-dependent strict non-inferiority.
- LoTTE science/search supports cross-domain ranking gains but shows that
  context-budget strength must be domain calibrated.
- Feedback-driven hard-case recovery can repair a meaningful fraction of
  budget-induced tail failures in post-feedback retry.
- It exposes a quality-cost frontier rather than universally dominating dense
  retrieval on every dataset and metric.

## Research Questions

1. Can a contextual bandit controller learn useful retrieval-route preferences
   from simulated feedback in vertical-domain RAG?
2. Can multi-route retrieval, with dense as a recall floor and cluster geometry
   as a routing signal, improve large-scale retrieval quality relative to
   dense-only retrieval?
3. Can confidence-based route control reduce final retrieved context tokens
   while preserving dense-level Hit@10?
4. Do geometry diagnostics support the piecewise relevance-manifold framing,
   and where does that framing break down?
5. Can feedback-triggered fallback recover tail queries harmed by aggressive
   final-context compression?

## Contributions

1. **Adaptive retrieval controller.** We formulate RAG retrieval-route selection
   as a contextual bandit problem over dense, lexical, and cluster-local
   retrieval surfaces.
2. **Feedback-aware route learning.** We introduce trust-weighted simulated
   feedback and route-level credit assignment for LinUCB so that route value can
   improve over repeated interactions.
3. **Geometry-aware retrieval surface.** We use fixed KMeans/MiniBatchKMeans
   cluster arms to approximate local regions of a vertical-domain relevance
   manifold while retaining dense and BM25 recall safeguards.
4. **Final context-token control.** We separate retrieval candidate cost from
   final context tokens and show that confidence-based context compaction can
   reduce retrieved context tokens while preserving retrieval quality.
5. **Calibration and cross-domain validation.** We validate budget selection
   under calibration/test splits and replicate ranking-side gains on LoTTE
   science/search.
6. **Feedback-driven recovery.** We show that simulated feedback can trigger
   safer fallback behavior and recover part of the tail failures caused by
   aggressive context compression.
7. **Large-scale evidence and limitations.** We evaluate LoTTE
   technology/search from 100k to 638k chunks and include ablations and failure
   cases showing where dense remains necessary.

## Section Plan

### 1. Introduction

- RAG retrieval has an inherent coverage-efficiency-quality trade-off.
- Dense retrieval is strong but static.
- Vertical-domain corpora often contain local semantic, lexical, and behavioral
  structure.
- IntentWeight learns to route over this structure instead of using one fixed
  retrieval path.
- State bounded result: 4.7-5.3% final context-token reduction on LoTTE
  100k-638k, with mean Hit@10 above dense on 200k/400k/638k.
- State strengthened evidence: calibration/test context budgets, science/search
  cross-domain ranking support, and feedback recovery for budget-induced tail
  failures.

### 2. Related Work

Suggested buckets:

- Retrieval-augmented generation and evidence retrieval.
- Dense retrieval, sparse retrieval, hybrid retrieval, and reranking.
- Contextual bandits and online recommendation.
- Adaptive retrieval, routing, and agentic RAG.
- Manifold or geometry-inspired retrieval diagnostics.

### 3. Method

- Problem formulation.
- Multi-route retrieval surface: dense, BM25, cluster-local dense, and hybrid
  rescue.
- KMeans cluster arms and piecewise relevance-manifold assumption.
- LinUCB route policy and context features.
- Trust-weighted feedback and route-level credit.
- Confidence-based final context compaction.

### 4. Experimental Setup

- Dataset roles and guardrails.
- Retrieval metrics: Hit@K, evidence_recall@K, MRR@K, nDCG@K.
- Cost metrics: source candidate count, dense invocation rate, final context
  tokens.
- Prequential simulated feedback protocol.
- Dense baseline: `sentence-transformers/all-MiniLM-L6-v2`, CPU exact cosine.

### 5. Results

- Static baselines and multi-route scale-up.
- Task29 final context-token frontier.
- Calibration/test validation from Task38.
- Cross-domain LoTTE science/search validation from Task39.
- Seed stability from Task29.3 and Task33.6.
- Feedback self-evolution evidence from Task15/25/33.2.
- Feedback-driven hard-case recovery from Task40.
- Encoder robustness and LLM generation smoke from Task33.1a and Task33.5.
- Geometry diagnostics from Task30.
- Failure and limitation cases: eManual and CUAD.

### 6. Discussion

- Why dense remains an important recall floor.
- Why geometry helps routing but does not replace dense.
- Why feedback value is clearer in policy metrics than in already-saturated
  final Hit@10 on some datasets.
- Why feedback recovery should be treated as a controlled fallback trigger,
  not a universal reranking rule.
- Deployment interpretation: dense can be reduced under confidence, but should
  remain as a fallback.

### 7. Limitations and Future Work

- Simulated feedback, no real human feedback yet.
- Only a small LLM generation smoke, not full human/end-to-end validation.
- Main experiments use one dense encoder, with one MiniLM-family robustness
  check.
- Three seed stability diagnostics across all scales, plus five seeds on
  LoTTE 100k; not strong significance proof.
- Geometry diagnostics support an assumption, not a theorem.
- Post-feedback recovery is not the same as first-pass IID improvement.
- Context-budget parameters require domain and scale calibration.

## Figure Plan

1. **System overview.** Query enters IntentWeight, routes to dense/BM25/cluster
   local retrieval, LinUCB updates from feedback, final context policy compacts
   evidence.
2. **Quality-token frontier.** LoTTE 100k/200k/400k/638k comparing dense and
   Task29-C in Hit@10 vs average context tokens.
3. **Feedback self-evolution.** Last true reward and selected-cluster hit over
   epochs for trust-weighted vs no-feedback or equal-noisy modes.
4. **Calibration and cross-domain context budgets.** Frozen budget policies on
   LoTTE technology/search and science/search.
5. **Feedback recovery.** Affected tail queries and recovered queries under
   conservative retry.
6. **Geometry diagnostics.** Nearest-cluster hit@3 and context retention across
   LoTTE scales.
7. **Cost-layer separation.** Candidate cost, dense invocation rate, and final
   context tokens as separate layers.

## Table Plan

1. Dataset roles and guardrails.
2. Static BM25/dense/hybrid baselines.
3. Main LoTTE Task29-C token-quality table.
4. Task29.3 seed CI table.
5. Task38 calibration/test context-budget table.
6. Task39 cross-domain LoTTE table.
7. Task40 hard-case recovery table.
8. Task30 geometry table.
9. Feedback and credit-assignment ablation table.
10. Robustness/sanity table for Task33.1a, Task33.5, and Task33.6.
11. Limitation case table for eManual and CUAD.

## Claim Boundaries

Use:

- "feedback-driven adaptive retrieval controller"
- "quality-cost frontier"
- "final retrieved context tokens"
- "piecewise relevance-manifold assumption"
- "dense remains a recall floor"

Avoid:

- "universally outperforms dense retrieval"
- "proves the manifold hypothesis"
- "candidate cost reduction equals LLM token saving"
- "end-to-end answer quality is improved"
- "LinUCB alone explains all gains"
