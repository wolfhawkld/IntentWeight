# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.8809 | 0.7163 | 0.7220 | 0.6616 | 1514.5067 | 1342.5000 | 2927.2500 | 1.0000 | 0.0000 |
| task29c:gated_cost_aware:seed13 | 13 | 0.8792 | 0.6784 | 0.7069 | 0.6266 | 1508.6745 | 1322.5000 | 3085.7500 | 0.9961 | -0.0017 |
| task29c:gated_cost_aware:seed17 | 17 | 0.8943 | 0.6826 | 0.7159 | 0.6334 | 1430.7785 | 1256.5000 | 2855.2500 | 0.9447 | 0.0134 |
| task29c:gated_cost_aware:seed19 | 19 | 0.8826 | 0.6756 | 0.7126 | 0.6274 | 1451.6745 | 1258.5000 | 2891.2500 | 0.9585 | 0.0017 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
