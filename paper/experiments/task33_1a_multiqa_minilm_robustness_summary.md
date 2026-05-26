# Task33.1a Multi-QA MiniLM Robustness Summary

Updated: 2026-05-26

Task33.1a tests whether IntentWeight's main claim depends on the exact
`sentence-transformers/all-MiniLM-L6-v2` encoder. It replaces the main encoder
with `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA/search-tuned
MiniLM-family model with the same 384-dimensional embedding size and similar
CPU-friendly resource class.

This is a robustness check, not an embedding-model benchmark.

## Setup

| Item | Value |
|---|---|
| Dataset | LoTTE technology/search 100k |
| Corpus chunks | 101,311 |
| Queries | 596 test queries |
| GT refs | 2,045 |
| Encoder | `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` |
| Embedding dim | 384 |
| Model max sequence length | 512 |
| Device | CPU |
| Dense batch size | 64 |
| LinUCB seeds | 13, 17, 19 |
| LinUCB epochs | 8 |
| Reward attribution | `cluster_only` |
| Confidence mode | `value` |
| Final context policy | `confidence_topk`, high `k=8`, mid `k=10`, fallback `k=10` |

The first dense run generated reusable embedding cache files:

- corpus cache: `paper/experiments/data/embeddings/lotte_technology_search_100k__sentence-transformers-multi-qa-MiniLM-L6-cos-v1__corpus__n101311__60ef5529c079a71e.npy`
- query cache: `paper/experiments/data/embeddings/lotte_technology_search_100k__sentence-transformers-multi-qa-MiniLM-L6-cos-v1__queries__n596__6c7ae007c1bcc394.npy`

These cache files are ignored by git.

## Dense Baseline

| Model | Hit@10 | MRR@10 | nDCG@10 | evidence_recall@10 | Avg Context Tokens@10 | Elapsed |
|---|---:|---:|---:|---:|---:|---:|
| `all-MiniLM-L6-v2` main Task29 baseline | 0.8674 | - | - | - | 1472.39 | - |
| `multi-qa-MiniLM-L6-cos-v1` | 0.8809 | 0.7220 | 0.6616 | 0.7163 | 1514.51 | 2066.43s |

The QA-tuned MiniLM dense baseline is stronger than the original all-MiniLM
dense baseline on LoTTE 100k. This makes it a useful robustness check because
IntentWeight is evaluated against a stronger same-resource-class dense encoder.

## Task29-C Under Multi-QA MiniLM

| Method | Hit@10 | MRR@10 | nDCG@10 | evidence_recall@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dense-only | 0.8809 | 0.7220 | 0.6616 | 0.7163 | 1514.51 | 1.0000 | 0.0000 |
| Task29-C seed 13 | 0.8792 | 0.7069 | 0.6266 | 0.6784 | 1508.67 | 0.9961 | -0.0017 |
| Task29-C seed 17 | 0.8943 | 0.7159 | 0.6334 | 0.6826 | 1430.78 | 0.9447 | +0.0134 |
| Task29-C seed 19 | 0.8826 | 0.7126 | 0.6274 | 0.6756 | 1451.67 | 0.9585 | +0.0017 |
| Task29-C mean | 0.8853 | 0.7118 | 0.6291 | 0.6789 | 1463.71 | 0.9665 | +0.0045 |

Interpretation:

- Task29-C remains above the multi-qa dense baseline in mean Hit@10:
  `0.8853` vs `0.8809` (`+0.45` percentage points).
- Final context tokens are reduced from `1514.51` to `1463.71`, a `3.35%`
  saving.
- Average final context size drops to about `9.0` chunks, confirming that
  confidence-based context compaction is active.
- evidence_recall@10 and ranking metrics are lower than dense, so this should
  be framed as query-level Hit@10 plus context-token robustness, not as a
  universal improvement on every retrieval metric.

## Route-Control Metrics

From the cost-aware LinUCB summary:

| Metric | Value |
|---|---:|
| last_epoch_true_reward_mean | 0.8579 |
| last_epoch_final_true_reward_mean | 0.7975 |
| last_epoch_route_true_reward_mean | 0.8579 |
| avg_source_candidate_cost_mean | 185.79 |
| avg_final_context_k_mean | 9.3865 |
| compact_context_rate_mean | 0.7000 |
| dense_query_rate_mean | 0.6932 |
| dense_saved_rate_mean | 0.3068 |
| linucb_primary_rate_mean | 0.3068 |
| hybrid_lite_rate_mean | 0.3932 |
| full_dense_fallback_rate_mean | 0.3000 |

These values show that the controller is not simply returning dense top-10 for
all queries. It uses compacted LinUCB/hybrid-lite routes for about 70% of
queries and falls back to full dense for about 30%.

## Geometry Diagnostics

| Metric | Value |
|---|---:|
| PCA dim for 90% variance | 150 |
| PCA var@64 | 0.6738 |
| nearest_cluster_hit@1 | 0.6493 |
| nearest_cluster_hit@3 | 0.8826 |
| nearest_cluster_hit@5 | 0.9346 |
| context_gt_recall@10 | 0.8238 |
| context_recall_retention@10 | 0.9352 |
| cluster_silhouette_sample | 0.0471 |
| cluster_size_entropy_norm | 0.9928 |

The geometry signal remains usable under the QA-tuned MiniLM encoder.
`nearest_cluster_hit@3=0.8826` is close to the original all-MiniLM LoTTE 100k
geometry result, and context retention@10 is above 93% of dense Hit@10.

## Conclusion

Task33.1a reduces the single-embedding-model risk. Under a different
same-resource-class, QA/search-tuned MiniLM encoder:

- dense-only becomes stronger than the original all-MiniLM dense baseline;
- IntentWeight Task29-C still slightly exceeds dense-only Hit@10;
- final retrieved context tokens are still reduced;
- local geometry remains useful for route control.

The result supports the paper's bounded claim:

> IntentWeight is not tied to one exact embedding encoder. Under a QA-tuned
> MiniLM-family encoder, it remains a valid adaptive retrieval controller that
> can preserve or slightly improve query-level Hit@10 while reducing final
> context tokens.

It should not be overclaimed as an embedding-model comparison or as improvement
on every retrieval metric.

## Artifacts

- Dense metrics:
  `paper/experiments/results/task33_1a_multiqa_100k_dense/dense_lotte_technology_search_100k_metrics.json`
- Dense rankings:
  `paper/experiments/results/task33_1a_multiqa_100k_dense/dense_lotte_technology_search_100k_rankings.json`
- Task29-C metrics:
  `paper/experiments/results/task33_1a_multiqa_100k_task29c/linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential_metrics.json`
- Task29-C rankings:
  `paper/experiments/results/task33_1a_multiqa_100k_task29c/linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential_rankings.json`
- Context token table:
  `paper/experiments/results/task33_1a_multiqa_100k_context_tokens.md`
- Geometry diagnostics:
  `paper/experiments/results/task33_1a_multiqa_100k_geometry/manifold_diagnostics_lotte_technology_search_100k.json`
