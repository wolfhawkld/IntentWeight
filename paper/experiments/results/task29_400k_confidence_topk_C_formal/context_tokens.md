# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.7718 | 0.5777 | 0.5876 | 0.5174 | 1482.2987 | 1288.5000 | 3003.0000 | 1.0000 | 0.0000 |
| task29_C_400k:gated_cost_aware:seed13 | 13 | 0.7802 | 0.5577 | 0.5648 | 0.4903 | 1401.1443 | 1251.0000 | 2864.0000 | 0.9453 | 0.0084 |
| task29_C_400k:gated_cost_aware:seed17 | 17 | 0.7869 | 0.5727 | 0.5898 | 0.5110 | 1373.5268 | 1217.0000 | 2675.0000 | 0.9266 | 0.0151 |
| task29_C_400k:gated_cost_aware:seed19 | 19 | 0.7785 | 0.5682 | 0.5849 | 0.5061 | 1435.6057 | 1252.0000 | 3036.7500 | 0.9685 | 0.0067 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
