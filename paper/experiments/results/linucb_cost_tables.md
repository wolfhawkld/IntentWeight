# Cost-Aware LinUCB Routing Tables

| dataset | routing_mode | scope | query_split | num_queries | recall@10_mean | last_epoch_true_reward_mean | avg_source_candidate_cost_mean | dense_query_rate_mean | linucb_primary_rate_mean | hybrid_lite_rate_mean | full_dense_fallback_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | full_multi_route | heldout_test | test | 3080 | 0.9844 | 0.9805 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| banking77 | gated_cost_aware | heldout_test | test | 3080 | 0.9813 | 0.9784 | 142.5108 | 1.0000 | 0.0000 | 0.9843 | 0.0157 |
| banking77 | full_multi_route | sample | test | 1000 | 0.9863 | 0.9583 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| banking77 | full_multi_route | sample | test | 200 | 0.9900 | 0.6150 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| banking77 | gated_cost_aware | sample | test | 1000 | 0.9817 | 0.9407 | 146.2756 | 1.0000 | 0.0000 | 0.9608 | 0.0392 |
| banking77 | gated_cost_aware | sample | test | 200 | 0.9900 | 0.7900 | 150.8000 | 1.0000 | 0.0000 | 0.9325 | 0.0675 |
| cuad | full_multi_route | smoke_only | test | 79 | 0.0886 | 0.0233 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| cuad | gated_cost_aware | smoke_only | test | 79 | 0.0633 | 0.0200 | 203.4667 | 1.0000 | 0.0000 | 0.6033 | 0.3967 |
| emanual | full_multi_route | heldout_test | test | 130 | 0.1487 | 0.0556 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| emanual | gated_cost_aware | heldout_test | test | 130 | 0.1154 | 0.0808 | 214.0741 | 1.0000 | 0.0000 | 0.5370 | 0.4630 |
| lotte_technology_search | full_multi_route | heldout_test | test | 20 | 1.0000 | 0.5000 | 150.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| lotte_technology_search | gated_cost_aware | heldout_test | test | 20 | 0.9500 | 0.4500 | 129.5000 | 0.9500 | 0.0500 | 0.2000 | 0.7500 |
| lotte_technology_search_100k | full_multi_route | heldout_test | test | 596 | 0.8826 | 0.5671 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| lotte_technology_search_100k | gated_cost_aware | heldout_test | test | 596 | 0.8440 | 0.5923 | 191.6816 | 0.8220 | 0.1780 | 0.4767 | 0.3453 |
| pubmedqa | full_multi_route | full | train | 1000 | 0.9940 | 0.8727 | 299.9400 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| pubmedqa | gated_cost_aware | full | train | 1000 | 0.9893 | 0.8667 | 152.3558 | 1.0000 | 0.0000 | 0.9227 | 0.0773 |
| pubmedqa | full_multi_route | sample | train | 100 | 0.9800 | 0.3300 | 300.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| pubmedqa | gated_cost_aware | sample | train | 100 | 0.9800 | 0.3300 | 239.2000 | 1.0000 | 0.0000 | 0.3800 | 0.6200 |

## Notes

- `full_multi_route` keeps global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor enabled.
- `gated_cost_aware` shifts to LinUCB-primary or hybrid-lite routes when confidence is high and semantic drift is low; otherwise it uses full dense fallback.
- Cost is reported as source candidate count before fusion; dense query rate captures how often global dense retrieval is still executed.
