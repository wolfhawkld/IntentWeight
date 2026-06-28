# Task65.3 Dynamic-Route Mediation and Evidence Survival Plan

## Objective

Explain which post-fusion ranking properties determine whether prefix-based
token budgeting preserves `Hit@10`. The task must not assume that RRF creates
more relevant-chunk redundancy or that route confidence predicts compression
safety. Both are hypotheses to test.

The current `gated_cost_aware` implementation already uses confidence
causally at the routing layer: high confidence selects a cluster-primary route,
mid confidence selects a hybrid-lite route, and low confidence selects the full
dense fallback. Task65.3 therefore also tests whether this tiered route-shape
switching improves the evidence pool on which the separate budget acts.

## Research Questions

1. Which ranking properties distinguish safe from unsafe compression?
2. Do routed evidence pools differ from dense top-10 in those properties?
3. Does confidence-gated route-shape switching improve post-budget survival
   relative to fixed fusion under the same arms and budget protocol?
4. Does route confidence add held-out explanatory value after rank and token
   placement are known?

## Fixed Protocol

- LoTTE technology/search 100k.
- Existing 179-query calibration / 417-query frozen-test split.
- Seeds `13,17,19`.
- Existing dense, Task37 routed, static-geometry, and randomized-partition
  rankings where available.
- Actual `tiktoken/cl100k_base` accounting.
- Prefix actions over the existing ratio/minimum-prefix grid.

No embedding, retrieval, or LLM generation should be rerun unless route-source
provenance is unavailable and proves necessary.

## Route-Mediation Controls

Use the same selected arms, feedback state, candidate depths, split, and budget
grid wherever possible. Compare:

- current confidence-gated route shapes and weights;
- fixed full multi-route fusion;
- fixed cluster-primary fusion as a quality-risk boundary;
- shuffled confidence-tier assignments that preserve per-seed tier frequency;
- dense budget-only.

The primary mediation contrast is current dynamic gating versus fixed full
fusion. Shuffled tiers test whether the observed confidence-to-route assignment,
rather than merely the proportion of route shapes, matters.

## Per-Query Diagnostics

- number of unique relevant chunks in uncompressed top-10;
- first relevant-chunk rank;
- cumulative tokens through the first retained relevant chunk;
- minimum token ratio required to preserve at least one relevant chunk;
- total top-10 tokens and relevant-chunk token length;
- relevant evidence supported by dense, BM25, and cluster routes, if source
  provenance can be exported without changing retrieval behavior;
- route confidence, geometry similarity, and feedback condition.

## Analyses

- paired dense-versus-routed comparisons with query bootstrap intervals;
- failure rate stratified by relevant-chunk count and first relevant rank;
- continuous association with the oracle minimum-safe-token ratio;
- fixed-action AUROC/AUPRC and risk-coverage for rank/token features;
- incremental model comparison: rank/token features alone versus the same
  features plus route confidence;
- paired dynamic-gating versus fixed-fusion comparisons before and after the
  same frozen budget action;
- mediation decomposition into route-tier assignment, candidate-pool change,
  and post-budget evidence survival;
- cluster bootstrap by query when multiple budget actions are pooled.

## Guardrails

- Ground-truth-derived survival margin is a diagnostic, not a deployable
  confidence estimator.
- Failure to detect an association is not proof of independence.
- Do not attribute safety to RRF redundancy unless routed pools show greater
  measured redundancy and that difference explains held-out survival.
- Do not infer causal mediation from correlation or feature importance.
- A positive dynamic-gating effect supports
  `confidence -> route composition -> evidence pool`; it does not by itself
  support `confidence -> per-query compression-safety prediction`.

## Preliminary Check

On the frozen test split, dense top-10 contains `2.60` relevant chunks on
average and has `60.9%` of hit queries with at least two relevant chunks. The
Task37 routed pools contain about `2.40-2.43` relevant chunks and have
`57.7-59.8%` with at least two. For `r0.85/m4`, all eight dense failures occur
among queries with exactly one relevant chunk, so redundancy is associated
with safety, but the routed pools do not currently show more unique relevant
chunks than dense. Rank and cumulative-token placement therefore remain the
more plausible untested explanations.

## Paper Use

Use Task65.3 only to explain observed compression survival boundaries. The
paper-facing result should remain route control plus separately calibrated
budgeting unless this task establishes a narrower supported mechanism.
