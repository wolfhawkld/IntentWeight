# Task23 LoTTE Scale-Up Evidence Summary

Updated: 2026-05-21

This document consolidates the LoTTE technology/search scale-up evidence from 100k to the full 638k corpus. It is intended as the paper-facing bridge from individual task logs to the final experimental argument.

## Scope

- Dataset family: LoTTE technology/search.
- Query split: held-out `test`, `596` queries at every scale.
- Ground-truth refs: `2045`, with full GT corpus coverage in the reported scale-up runs.
- Dense encoder: `sentence-transformers/all-MiniLM-L6-v2`, CPU exact cosine ranking.
- LinUCB setup: `seeds=13,17,19`, `epochs=3`, `n_clusters=32`, `context_dim=64`, KMeans/MiniBatchKMeans fixed arm space.
- Artifact reuse means deterministic intermediate artifacts only: corpus/query embeddings, dense top-depth rankings, BM25 top-depth rankings, and context cluster artifacts. Final evaluation statistics are recomputed per run.

## Main Scale-Up Table

| Scale | Corpus | BM25 R@10 | Dense R@10 | Hybrid R@10 | Full R@10 | Gated R@10 | Full ΔDense | Gated ΔDense | Gated Cost | Cost ↓ vs Full | Dense Query Rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100k | 101311 | 0.7232 | 0.8674 | 0.8624 | 0.8826 | 0.8440 | 0.0151 | -0.0235 | 191.68 | 36.11% | 0.8220 |
| 200k | 201010 | 0.6292 | 0.7970 | 0.8003 | 0.8300 | 0.8154 | 0.0330 | 0.0185 | 232.01 | 22.66% | 0.9027 |
| 400k | 400674 | 0.5721 | 0.7718 | 0.7617 | 0.8003 | 0.7836 | 0.0285 | 0.0117 | 233.22 | 22.26% | 0.9141 |
| 638k | 638509 | 0.5084 | 0.7282 | 0.7181 | 0.7612 | 0.7343 | 0.0330 | 0.0062 | 236.22 | 21.26% | 0.9146 |

## Detailed Metrics

| Scale | BM25 MRR@10 | BM25 nDCG@10 | Dense MRR@10 | Dense nDCG@10 | Full MRR@10 | Full nDCG@10 | Full Reward | Full Reward Gain | Gated MRR@10 | Gated nDCG@10 | Gated Reward | Gated Reward Gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100k | 0.5545 | 0.4768 | 0.7081 | 0.6487 | 0.7105 | 0.6573 | 0.5671 | 0.2880 | 0.6950 | 0.5889 | 0.5923 | 0.2931 |
| 200k | 0.4572 | 0.3832 | 0.6279 | 0.5643 | 0.6326 | 0.5720 | 0.5078 | 0.2875 | 0.6305 | 0.5472 | 0.5677 | 0.3395 |
| 400k | 0.3714 | 0.3167 | 0.5876 | 0.5174 | 0.5920 | 0.5251 | 0.5537 | 0.2864 | 0.5860 | 0.5084 | 0.4983 | 0.2366 |
| 638k | 0.2910 | 0.2451 | 0.5102 | 0.4303 | 0.5153 | 0.4358 | 0.5034 | 0.2220 | 0.5089 | 0.4233 | 0.4636 | 0.1946 |

## 100k Optimized Conditional Fallback Reference

| Setting | R@10 | Avg Source Cost | Dense Query Rate | Interpretation |
| --- | --- | --- | --- | --- |
| Task18 gated 100k | 0.8440 | 191.68 | 0.8220 | Original multi-seed gated setting; saves cost but is below dense. |
| Task20-S 100k | 0.8747 | 227.29 | 0.8945 | Optimized conditional dense fallback point; above dense with lower cost than Task19-D. |

## Interpretation

1. Dense remains a strong baseline, but its Recall@10 declines as the nested corpus grows: `0.8674` at 100k, `0.7970` at 200k, `0.7718` at 400k, and `0.7282` at 638k.
2. BM25-only is substantially below dense at every scale. This supports the interpretation that lexical coverage is useful as one route, but it is not the main source of the final quality gain.
3. Simple static hybrid RRF does not reliably beat dense. It is slightly above dense at 200k but below dense at 100k, 400k, and 638k. This supports the claim that fixed fusion is not enough; adaptive routing is the key contribution.
4. Full multi-route LinUCB is above dense at every scale. The gains over dense are `+0.0151`, `+0.0330`, `+0.0285`, and `+0.0330` R@10 from 100k to 638k.
5. Gated cost-aware LinUCB is above dense at 200k, 400k, and 638k while reducing source candidate cost relative to full multi-route by `22.66%`, `22.26%`, and `21.26%` respectively. At 100k, the original Task18 gated setting is below dense, but the later Task20-S fallback optimization is above dense.
6. The cost claim should be written carefully: current gated routing is cheaper than full multi-route and reduces dense query rate, but it is not cheaper than dense-only in absolute source-candidate count because dense-only uses a single 100-candidate source.

## Paper-Ready Claim

A bounded, evidence-supported claim is: IntentWeight does not replace dense retrieval unconditionally. Instead, in large-scale vertical-domain RAG, it uses dense as a recall floor/fallback while LinUCB learns how to combine dense, BM25, and cluster-local retrieval. Across LoTTE scale-up experiments, full multi-route LinUCB consistently exceeds dense-only Recall@10, and gated cost-aware routing preserves part of this gain while reducing the candidate cost of dense-heavy multi-route retrieval.

## Task24 Post-Audit Note

Task24 adds static and naive online ablations for the 638k setting. These results show that final query-level `Hit@10` can be heavily protected by global dense/BM25 and dense floor: static nearest, uniform random, and epsilon-greedy cluster-arm selectors all remain near full multi-route Hit@10 when the full retrieval surface is active. The paper should therefore treat the historical `Recall@10` field as query-level `Hit@10`, report `evidence_recall@10` where available, and separate final retrieval quality from arm-policy quality.

The corrected 638k interpretation is:

- full multi-route and static nearest ensemble both reach `Hit@10=0.7612`;
- static nearest has much stronger selected-cluster hit (`0.9016`) than random (`0.1473`) or epsilon-greedy (`0.2582`), supporting the usefulness of geometry;
- static nearest gated reaches `Hit@10=0.7500` with source cost `223.49`, which is stronger than the current gated LinUCB setting on this static 638k benchmark;
- gated LinUCB remains the cost-aware deployment point: `Hit@10=0.7343`, above dense-only `0.7282`, while reducing source candidate cost versus full multi-route from `300.00` to `236.22`;
- do not claim LinUCB alone explains the full-route quality gain or that it is necessary for one-shot static geometry gating. Claim that LinUCB supplies feedback-adaptive, confidence-gated control over a strong multi-route retrieval surface, while static geometry gating is a strong non-learning baseline.

## Recommended Paper Tables

- Main scale-up table: use the `Main Scale-Up Table` above.
- Detailed quality table: use Recall@10, MRR@10, nDCG@10, reward, and reward gain from `Detailed Metrics`.
- Cost table: report gated average source cost, cost reduction vs full multi-route, dense query rate, and dense saved rate.
- Boundary table: contrast BM25-only, dense-only, static hybrid, full multi-route, and gated routing to show that adaptive routing, not a single retrieval channel or fixed RRF, explains the gain.

## Source Files

- CSV: `paper/experiments/results/task23_lotte_scaleup_summary.csv`
- 400k/638k BM25 completion: `paper/experiments/results/task23_bm25_scale_completion/`
- 100k LinUCB formal: `paper/experiments/results/linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential_metrics.json`
- 200k LinUCB formal: `paper/experiments/results/task22_200k_formal/linucb_cost_lotte-technology-search-200k_heldout-test_test_corpus-full_q596_prequential_metrics.json`
- 400k LinUCB formal: `paper/experiments/results/task22_5_lotte_400k_linucb_formal/linucb_cost_lotte-technology-search-400k_heldout-test_test_corpus-full_q596_prequential_metrics.json`
- 638k LinUCB formal: `paper/experiments/results/task22_9_lotte_638k_linucb_formal/linucb_cost_lotte-technology-search-638k_heldout-test_test_corpus-full_q596_prequential_metrics.json`
