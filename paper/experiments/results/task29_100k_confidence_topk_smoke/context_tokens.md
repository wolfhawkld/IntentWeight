# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 1472.3876 | 1312.0000 | 2908.2500 | 1.0000 | 0.0000 |
| task29_smoke:gated_cost_aware:seed13 | 13 | 0.8339 | 0.6167 | 0.6965 | 0.5893 | 999.3775 | 873.5000 | 2110.2500 | 0.6787 | -0.0336 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
