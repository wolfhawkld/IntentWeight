# LinUCB Variant Comparison

## Evidence Retrieval Main

| dataset | scope | corpus_scope | global_recall@10_mean | manifold_recall@10_mean | delta_recall@10_mean | global_mrr@10_mean | manifold_mrr@10_mean | delta_mrr@10_mean | winner_recall@10 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| emanual | heldout_test | full | 0.1154 | 0.0923 | -0.0231 | 0.0182 | 0.0193 | 0.0012 | global | global has better recall; manifold has offsetting rank-quality signal |
| pubmedqa | full | full | 0.5480 | 0.6607 | 0.1127 | 0.4637 | 0.5654 | 0.1016 | manifold_local | manifold-local improves both recall and MRR |

## Intent Retrieval Proxy

| dataset | scope | corpus_scope | global_recall@10_mean | manifold_recall@10_mean | delta_recall@10_mean | global_mrr@10_mean | manifold_mrr@10_mean | delta_mrr@10_mean | winner_recall@10 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | heldout_test | full | 0.7215 | 0.8247 | 0.1031 | 0.6094 | 0.7490 | 0.1395 | manifold_local | manifold-local improves both recall and MRR |

## Smoke / Sample Results

| dataset | scope | corpus_scope | global_recall@10_mean | manifold_recall@10_mean | delta_recall@10_mean | global_mrr@10_mean | manifold_mrr@10_mean | delta_mrr@10_mean | winner_recall@10 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cuad | smoke_only | gt_anchored_10000 | 0.0464 | 0.0295 | -0.0169 | 0.0275 | 0.0120 | -0.0155 | global | global remains stronger on CUAD smoke sample |

## Notes

- Global LinUCB is the Task 11 baseline.
- Manifold-local LinUCB is the Task 12 variant with query-neighborhood feedback attention and cross-arm distance-decay propagation.
- Positive delta means manifold-local is better than global under the same query/corpus/protocol scope.
- CUAD remains smoke/sample only and should not be treated as full-corpus held-out evidence.
