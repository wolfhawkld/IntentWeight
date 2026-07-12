# Cost-Aware LinUCB Routing Tables

| dataset | routing_mode | reward_attribution | confidence_mode | final_context_policy | scope | query_split | num_queries | hit@10_mean | recall@10_mean | evidence_recall@10_mean | quality_cost_ratio@10_mean | last_epoch_true_reward_mean | last_epoch_final_true_reward_mean | last_epoch_route_true_reward_mean | avg_source_candidate_cost_mean | avg_final_context_k_mean | compact_context_rate_mean | high_confidence_compact_rate_mean | mid_confidence_compact_rate_mean | fallback_full_topk_context_rate_mean | dense_query_rate_mean | dense_saved_rate_mean | static_nearest_ensemble_rate_mean | uniform_random_ensemble_rate_mean | random_partition_feedback_ensemble_rate_mean | random_partition_static_ensemble_rate_mean | epsilon_greedy_ensemble_rate_mean | linucb_primary_rate_mean | hybrid_lite_rate_mean | full_dense_fallback_rate_mean | fallback_low_confidence_rate_mean | fallback_high_drift_rate_mean | fallback_reward_drop_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lotte_technology_search_100k | full_multi_route | final_fused | value | fixed_topk | heldout_test | test | 596 | 0.8865 | 0.8865 | 0.7293 | 0.0030 | 0.7534 | 0.7534 | 0.8082 | 300.0000 | 10.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| lotte_technology_search_100k | gated_cost_aware | final_fused | value | fixed_topk | heldout_test | test | 596 | 0.8775 | 0.8775 | 0.6819 | 0.0044 | 0.7539 | 0.7539 | 0.7992 | 201.1130 | 10.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.6393 | 0.3607 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3607 | 0.4244 | 0.2148 | 0.1923 | 0.0226 | 0.0000 |

## Notes

- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.
- `static_nearest_ensemble` uses the same dense/BM25/cluster fusion surface but selects cluster arms by nearest centroid and applies no feedback policy update.
- `static_nearest_gated` uses nearest-centroid arm selection plus the same cost-aware route shapes, with centroid similarity as a non-learned confidence proxy.
- `uniform_random_ensemble` and `epsilon_greedy_ensemble` are non-contextual arm-selection baselines over the same multi-route retrieval surface.
- `random_partition_feedback_ensemble` preserves the contextual LinUCB feedback estimator but shuffles geometry-derived cluster membership before learning.
- `random_partition_static_ensemble` applies nearest-centroid selection to the same shuffled partition without policy updates.
- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.
- `reward_attribution=cluster_only` updates LinUCB from the selected cluster route alone, separating policy credit from dense/BM25 rescue hits.
- `confidence_mode=route_quality` gates from historical cluster-route reward instead of the LinUCB value estimate.
- `final_context_policy=confidence_topk` reduces final context chunk count only when the selected LinUCB route is confident; it is measured separately from retrieval-stage source cost.
- `hit@k` is the query-level success metric historically reported as `recall@k`; `evidence_recall@k` reports the fraction of all ground-truth chunks retrieved.
- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.
