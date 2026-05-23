# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.7970 | 0.6202 | 0.6279 | 0.5643 | 1444.1242 | 1266.0000 | 2827.7500 | 1.0000 | 0.0000 |
| task29_C_200k:gated_cost_aware:seed13 | 13 | 0.8339 | 0.6129 | 0.6365 | 0.5498 | 1376.8708 | 1239.5000 | 2696.7500 | 0.9534 | 0.0369 |
| task29_C_200k:gated_cost_aware:seed17 | 17 | 0.8188 | 0.6041 | 0.6353 | 0.5471 | 1371.6577 | 1204.0000 | 2810.7500 | 0.9498 | 0.0218 |
| task29_C_200k:gated_cost_aware:seed19 | 19 | 0.8221 | 0.6156 | 0.6399 | 0.5582 | 1380.8473 | 1216.5000 | 2820.7500 | 0.9562 | 0.0252 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
