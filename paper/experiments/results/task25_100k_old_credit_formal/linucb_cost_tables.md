# Cost-Aware LinUCB Routing Tables

| dataset | routing_mode | reward_attribution | confidence_mode | scope | query_split | num_queries | hit@10_mean | recall@10_mean | evidence_recall@10_mean | quality_cost_ratio@10_mean | last_epoch_true_reward_mean | last_epoch_final_true_reward_mean | last_epoch_route_true_reward_mean | avg_source_candidate_cost_mean | dense_query_rate_mean | dense_saved_rate_mean | static_nearest_ensemble_rate_mean | uniform_random_ensemble_rate_mean | epsilon_greedy_ensemble_rate_mean | linucb_primary_rate_mean | hybrid_lite_rate_mean | full_dense_fallback_rate_mean | fallback_low_confidence_rate_mean | fallback_high_drift_rate_mean | fallback_reward_drop_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lotte_technology_search_100k | gated_cost_aware | final_fused | value | heldout_test | test | 596 | 0.8826 | 0.8826 | 0.6871 | 0.0046 | 0.7584 | 0.7584 | 0.8076 | 193.9178 | 0.7466 | 0.2534 | 0.0000 | 0.0000 | 0.0000 | 0.2534 | 0.4031 | 0.3435 | 0.3207 | 0.0228 | 0.0000 |

## Notes

- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.
- `static_nearest_ensemble` uses the same dense/BM25/cluster fusion surface but selects cluster arms by nearest centroid and applies no feedback policy update.
- `static_nearest_gated` uses nearest-centroid arm selection plus the same cost-aware route shapes, with centroid similarity as a non-learned confidence proxy.
- `uniform_random_ensemble` and `epsilon_greedy_ensemble` are non-contextual arm-selection baselines over the same multi-route retrieval surface.
- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.
- `reward_attribution=cluster_only` updates LinUCB from the selected cluster route alone, separating policy credit from dense/BM25 rescue hits.
- `confidence_mode=route_quality` gates from historical cluster-route reward instead of the LinUCB value estimate.
- `hit@k` is the query-level success metric historically reported as `recall@k`; `evidence_recall@k` reports the fraction of all ground-truth chunks retrieved.
- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.
