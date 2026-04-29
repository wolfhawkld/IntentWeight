# Soft-Routed Manifold LinUCB Tables

## Evidence Retrieval Main Table

| dataset | scope | query_split | corpus_scope | num_queries | gt_query_coverage | num_seeds | recall@10_mean | mrr@10_mean | selected_cluster_hit_rate_mean | soft_rescue_on_cluster_miss_rate_mean | dense_fallback_hit_rate_mean | bm25_fallback_hit_rate_mean | dense_floor_k | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| emanual | heldout_test | test | full | 130 | 1.0 | 3 | 0.1436 | 0.0337 | 0.2641 | 0.1173 | 0.1692 | 0.1154 | 5 |  |
| pubmedqa | full | train | full | 1000 | 1.0 | 3 | 0.9920 | 0.8466 | 0.6817 | 0.9800 | 0.9930 | 0.9770 | 5 | GT is abstract context section-level, not strict answer-supporting sentence evidence. |

## Intent Retrieval Proxy

| dataset | scope | query_split | corpus_scope | num_queries | gt_query_coverage | num_seeds | recall@10_mean | mrr@10_mean | selected_cluster_hit_rate_mean | soft_rescue_on_cluster_miss_rate_mean | dense_fallback_hit_rate_mean | bm25_fallback_hit_rate_mean | dense_floor_k | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | heldout_test | test | full | 3080 | 1.0 | 3 | 0.9831 | 0.9420 | 0.8829 | 0.9699 | 0.9805 | 0.9698 | 5 | Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions. |

## Smoke / Sample Results

| dataset | scope | query_split | corpus_scope | num_queries | gt_query_coverage | num_seeds | recall@10_mean | mrr@10_mean | selected_cluster_hit_rate_mean | soft_rescue_on_cluster_miss_rate_mean | dense_fallback_hit_rate_mean | bm25_fallback_hit_rate_mean | dense_floor_k | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cuad | smoke_only | test | gt_anchored_10000 | 79 | 1.0 | 3 | 0.0844 | 0.0344 | 0.3713 | 0.0865 | 0.0759 | 0.0506 | 5 | Sampled query/corpus scope; use only with matching comparison group. CUAD smoke/sample result; not a full-corpus held-out result. Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors. |

## Notes

- Protocol is prequential: each query is evaluated before its GT-derived feedback update.
- This is the Task 13.5 variant: manifold-local LinUCB arm selection plus global dense/BM25 bypass and weighted RRF fusion.
- selected_cluster_hit_rate diagnoses hard-pruning coverage; soft_rescue_on_cluster_miss_rate diagnoses fallback recovery after a selected-cluster miss.
- CUAD remains smoke/sample only; sampled CUAD corpora must pass GT-in-corpus coverage.
