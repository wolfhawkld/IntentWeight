# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.7282 | 0.5041 | 0.5102 | 0.4303 | 1525.6191 | 1329.5000 | 2935.5000 | 1.0000 | 0.0000 |
| task29_C_638k:gated_cost_aware:seed13 | 13 | 0.7567 | 0.5016 | 0.5199 | 0.4292 | 1455.7869 | 1286.5000 | 2925.0000 | 0.9542 | 0.0285 |
| task29_C_638k:gated_cost_aware:seed17 | 17 | 0.7399 | 0.5009 | 0.5001 | 0.4233 | 1448.4379 | 1315.0000 | 2740.0000 | 0.9494 | 0.0117 |
| task29_C_638k:gated_cost_aware:seed19 | 19 | 0.7433 | 0.4979 | 0.4943 | 0.4192 | 1450.2349 | 1289.5000 | 2796.0000 | 0.9506 | 0.0151 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
