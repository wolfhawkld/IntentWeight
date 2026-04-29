# Manifold-Local LinUCB Tables

## Evidence Retrieval Main Table

| dataset | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | gt_query_coverage | num_seeds | recall@1_mean | recall@10_mean | mrr@10_mean | avg_local_boost_norm_mean | cross_arm_update_weight_mean | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| emanual | heldout_test | test | full | 130 | 2 | 1.0 | 3 | 0.0000 | 0.0923 | 0.0193 | 0.0190 | 68.5486 |  |
| pubmedqa | full | train | full | 1000 | 0 | 1.0 | 3 | 0.4803 | 0.6607 | 0.5654 | 0.1182 | 547.7517 | GT is abstract context section-level, not strict answer-supporting sentence evidence. |

## Intent Retrieval Proxy

| dataset | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | gt_query_coverage | num_seeds | recall@1_mean | recall@10_mean | mrr@10_mean | avg_local_boost_norm_mean | cross_arm_update_weight_mean | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | heldout_test | test | full | 3080 | 0 | 1.0 | 3 | 0.7123 | 0.8247 | 0.7490 | 0.1930 | 2214.1367 | Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions. |

## Smoke / Sample Results

| dataset | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | gt_query_coverage | num_seeds | recall@1_mean | recall@10_mean | mrr@10_mean | avg_local_boost_norm_mean | cross_arm_update_weight_mean | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cuad | smoke_only | test | gt_anchored_10000 | 79 | 21 | 1.0 | 3 | 0.0084 | 0.0295 | 0.0120 | 0.0098 | 53.0610 | Sampled query/corpus scope; use only with matching comparison group. CUAD smoke/sample result; not a full-corpus held-out result. Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors. |

## Notes

- Protocol is prequential: each query is evaluated before its GT-derived feedback update.
- This is the Task 12 manifold-local variant: query-neighborhood feedback attention plus cross-arm distance-decay propagation.
- CUAD remains smoke/sample only; sampled CUAD corpora must pass GT-in-corpus coverage.
