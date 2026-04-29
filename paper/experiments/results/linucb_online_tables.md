# Global LinUCB Online Baseline Tables

## Evidence Retrieval Main Table

| dataset | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | num_queries_with_gt_in_corpus | gt_query_coverage | num_seeds | recall@1_mean | recall@10_mean | mrr@10_mean | ndcg@10_mean | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| emanual | heldout_test | test | full | 130 | 2 |  |  | 3 | 0.0000 | 0.1154 | 0.0182 | 0.0138 |  |
| pubmedqa | full | train | full | 1000 | 0 |  |  | 3 | 0.3927 | 0.5480 | 0.4637 | 0.3440 | GT is abstract context section-level, not strict answer-supporting sentence evidence. |

## Intent Retrieval Proxy

| dataset | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | num_queries_with_gt_in_corpus | gt_query_coverage | num_seeds | recall@1_mean | recall@10_mean | mrr@10_mean | ndcg@10_mean | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | heldout_test | test | full | 3080 | 0 |  |  | 3 | 0.5570 | 0.7215 | 0.6094 | 0.4602 | Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions. |

## Smoke / Sample Results

| dataset | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | num_queries_with_gt_in_corpus | gt_query_coverage | num_seeds | recall@1_mean | recall@10_mean | mrr@10_mean | ndcg@10_mean | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cuad | smoke_only | test | gt_anchored_10000 | 79 | 21 | 79 | 1.0 | 3 | 0.0211 | 0.0464 | 0.0275 | 0.0155 | Sampled query/corpus scope; use only with matching comparison group. CUAD smoke/sample result; not a full-corpus held-out result. Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors. |

## Notes

- Protocol is prequential: each query is evaluated before its GT-derived feedback update.
- This is the global LinUCB baseline. Manifold-local feedback propagation is reserved for Task 12.
- CUAD remains smoke/sample only; sampled CUAD corpora must pass GT-in-corpus coverage.
