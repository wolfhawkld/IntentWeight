# Task72 Recurrent Feedback-Stream Evaluation Plan

Updated: 2026-07-13

## Research Question

Task70 found no stable learned-feedback advantage for a frozen first-pass ranking of unseen queries. Task72 therefore evaluates the narrower mechanism that remains scientifically justified: whether controlled feedback can adapt cluster-local route selection when a query stream contains recurring local intents and changes its local-intent distribution over time.

This is not a real-user RLHF study, a general unseen-query result, or an end-to-end systems benchmark.

## Fixed Protocol

- Domains: LoTTE technology/search 100k and science/search 100k.
- Backbone and routing artifacts: existing all-MiniLM-L6-v2 exact-score, BM25, and KMeans artifacts; no corpus or query embedding is recomputed.
- Controller seeds: 13, 17, and 19.
- Retrieval surface: full Dense + BM25 + cluster-local fusion and fixed top-10 final context with identical route depths/weights for every controller.
- Controls: Dense-only, static-nearest full fusion, cold LinUCB full fusion with no feedback updates, and trust-weighted learned LinUCB full fusion.
- No answer cache, final-context cache, or response reuse is allowed. Every event executes arm selection, route fusion, final-context construction, and evaluation afresh. Immutable exact ranking artifacts are reused only as the declared retrieval backend for fair, reproducible event execution.

## Stream Construction

The stream is derived before controller execution from a fixed seed-13 KMeans query assignment. It selects the two largest eligible local-intent regions and uses disjoint query IDs in eight ordered phases:

1. region-A repeated anchors, warmup occurrence 1;
2. the same region-A anchors, warmup occurrence 2;
3. previously unseen queries nearby within region A;
4. region-B repeated anchors after the A-to-B distribution shift, occurrence 1;
5. the same region-B anchors, occurrence 2;
6. previously unseen queries nearby within region B;
7. a return to the recurring region-A anchors after the B-to-A shift; and
8. queries not previously observed in the stream.

The experiment tests a local-intent **distribution** shift. LoTTE offers one ground-truth evidence relation per query, so it would be misleading to fabricate a separate user-preference or relevance label solely to create a shift. Simulated feedback remains GT-derived and is applied only after the current event has been ranked and scored.

## Outcomes and Interpretation

For repeated, nearby, and unseen event groups, report query-event Hit@10, EvidenceRecall@10, MRR@10, nDCG@10, selected-cluster hit, route reward, final-context tokens, and Dense invocation rate. The primary adaptation diagnostic is the learned-versus-cold/static change in cluster-route quality from the first to later occurrence of recurring region-B events after the A-to-B shift.

For each controller seed, paired uncertainty uses a block bootstrap over unique query IDs, retaining all repeated events for a sampled ID. These intervals describe the declared trajectory and are not pooled as IID evidence across domains, phases, controller seeds, or repeated events. Recovery is conditional: an affected repeated query is counted as recovered only when an earlier cluster-route miss is followed by a later cluster-route hit under the same learned trajectory.

## Completion Criteria

1. A reproducible event-stream manifest records phases, query IDs, and source geometry assignment before controller execution.
2. Learned, cold, static, and Dense controls execute the same stream without answer/context caching.
3. Results separate repeated, nearby, and unseen conditions and expose both positive and negative adaptation effects.
4. The summary explicitly preserves the Task70 boundary: a positive recurrent result does not imply a frozen first-pass improvement for unseen queries.
