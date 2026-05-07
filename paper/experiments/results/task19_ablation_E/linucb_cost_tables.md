# Cost-Aware LinUCB Routing Tables

| dataset | routing_mode | scope | query_split | num_queries | recall@10_mean | last_epoch_true_reward_mean | avg_source_candidate_cost_mean | dense_query_rate_mean | linucb_primary_rate_mean | hybrid_lite_rate_mean | full_dense_fallback_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lotte_technology_search_100k | gated_cost_aware | heldout_test | test | 596 | 0.8865 | 0.6370 | 258.8386 | 0.9489 | 0.0511 | 0.2459 | 0.7030 |

## Notes

- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.
- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.
- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.
