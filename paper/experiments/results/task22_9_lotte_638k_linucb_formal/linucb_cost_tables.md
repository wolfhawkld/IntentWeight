# Cost-Aware LinUCB Routing Tables

| dataset | routing_mode | scope | query_split | num_queries | recall@10_mean | quality_cost_ratio@10_mean | last_epoch_true_reward_mean | avg_source_candidate_cost_mean | dense_query_rate_mean | dense_saved_rate_mean | linucb_primary_rate_mean | hybrid_lite_rate_mean | full_dense_fallback_rate_mean | fallback_low_confidence_rate_mean | fallback_high_drift_rate_mean | fallback_reward_drop_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lotte_technology_search_638k | full_multi_route | heldout_test | test | 596 | 0.7612 | 0.0025 | 0.5034 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| lotte_technology_search_638k | gated_cost_aware | heldout_test | test | 596 | 0.7343 | 0.0031 | 0.4636 | 236.2248 | 0.9146 | 0.0854 | 0.0854 | 0.3227 | 0.5919 | 0.5291 | 0.0628 | 0.0000 |

## Notes

- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.
- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.
- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.
