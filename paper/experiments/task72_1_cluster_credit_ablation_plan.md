# Task72.1 Cluster-Credit Feedback Ablation Plan

Updated: 2026-07-13

## Purpose

Task72 showed that feedback-induced route changes do not reliably improve the
final fused Dense+BM25+cluster ranking. Its final-fused reward is a confounded
credit signal: Dense/BM25 rescue can reward a selected cluster arm even when
that arm did not retrieve the evidence. Task72.1 therefore isolates the
narrower mechanism claim: whether controlled simulated feedback can improve
**cluster-route retrieval** when the reward, policy update, and evaluation all
refer to the same cluster-only retrieval surface.

This is a component ablation. It is not a replacement for Dense, a claim that
the complete multi-route system improves from feedback, real-user RLHF, or an
end-to-end generation study.

## Fixed, Outcome-Independent Protocol

- Reuse the already materialized Task72 event manifests unchanged: the same
  two LoTTE 100k domains, 212-event A-to-B-to-A recurrent streams, and query
  IDs. No post-result subset selection is allowed.
- Reuse the existing MiniLM embeddings, exact query-corpus score cache, BM25
  artifacts, KMeans context artifacts, stream cluster seed 13, and controller
  seeds 13/17/19.
- Use only selected cluster-arm ranking: `dense_depth=0`, `bm25_depth=0`,
  `dense_floor_k=0`, cluster depth 100, cluster-only RRF weight 1, and fixed
  final top-10. No answer, response, or final-context cache is permitted.
- Update reward uses `reward_attribution=cluster_only`; it is measured from
  the ranked cluster-route candidates before any global rescue route exists.

## Controls

1. static-nearest cluster route, no policy feedback update;
2. cold LinUCB cluster route, no feedback update;
3. LinUCB with equal-noisy simulated feedback;
4. LinUCB with trust-weighted simulated feedback; and
5. LinUCB with oracle feedback as a simulation upper bound.

The trust-weighted versus equal-noisy comparison isolates the configured
trust-weighting rule. Oracle is not a deployment baseline; it tests whether
the declared stream and LinUCB capacity could respond under perfect simulated
observations.

## Outcomes and Inference

Primary outcomes are selected-cluster hit, cluster-only Hit@10,
EvidenceRecall@10, MRR@10, nDCG@10, and the first-to-second region-B shift
change. Secondary outcomes are conditional cluster-route recovery and final
context token count, reported without an end-to-end cost claim.

All comparisons are per domain and controller seed. Query-ID block bootstrap
retains all repeated occurrences of a query within a block. There is no pooled
IID p-value across domains, seeds, phases, or repeated events.

## Decision Rule

Task72.1 supports only the mechanism claim when trust-weighted feedback shows
a stable route-level and cluster-only retrieval improvement over the cold and
equal-noisy controls, with no conflicting seed/domain pattern. A route-only
gain that fails to improve cluster-only retrieval is insufficient. A positive
Task72.1 result does not erase Task72's full-fusion boundary; both results must
be retained in any paper-facing account.
