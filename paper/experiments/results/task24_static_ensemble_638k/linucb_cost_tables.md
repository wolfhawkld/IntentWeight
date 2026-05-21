# Cost-Aware LinUCB Routing Tables

| dataset | routing_mode | scope | query_split | num_queries | hit@10_mean | recall@10_mean | evidence_recall@10_mean | quality_cost_ratio@10_mean | last_epoch_true_reward_mean | avg_source_candidate_cost_mean | dense_query_rate_mean | dense_saved_rate_mean | static_nearest_ensemble_rate_mean | linucb_primary_rate_mean | hybrid_lite_rate_mean | full_dense_fallback_rate_mean | fallback_low_confidence_rate_mean | fallback_high_drift_rate_mean | fallback_reward_drop_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lotte_technology_search_638k | static_nearest_ensemble | heldout_test | test | 596 | 0.7612 | 0.7612 | 0.5154 | 0.0025 | 0.7030 | 300.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Notes

- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.
- `static_nearest_ensemble` uses the same dense/BM25/cluster fusion surface but selects cluster arms by nearest centroid and applies no feedback policy update.
- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.
- `hit@k` is the query-level success metric historically reported as `recall@k`; `evidence_recall@k` reports the fraction of all ground-truth chunks retrieved.
- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.
