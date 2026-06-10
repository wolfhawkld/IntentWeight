# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 1472.3876 | 1312.0000 | 2908.2500 | 1.0000 | 0.0000 |
| task29_C:gated_cost_aware:seed13 | 13 | 0.8624 | 0.6708 | 0.7002 | 0.6180 | 1391.5940 | 1212.5000 | 2617.5000 | 0.9451 | -0.0050 |
| task29_C:gated_cost_aware:seed17 | 17 | 0.8641 | 0.6744 | 0.7110 | 0.6286 | 1398.1795 | 1234.5000 | 2804.5000 | 0.9496 | -0.0034 |
| task29_C:gated_cost_aware:seed19 | 19 | 0.8691 | 0.6759 | 0.7153 | 0.6288 | 1413.9547 | 1246.0000 | 2913.7500 | 0.9603 | 0.0017 |
| task37_7_9:gated_cost_aware:seed13 | 13 | 0.8490 | 0.6517 | 0.6986 | 0.6090 | 1261.9077 | 1094.0000 | 2488.5000 | 0.8570 | -0.0185 |
| task37_6_8:gated_cost_aware:seed13 | 13 | 0.8389 | 0.6341 | 0.6973 | 0.5993 | 1131.1879 | 993.0000 | 2309.7500 | 0.7683 | -0.0285 |
| task37_5_7:gated_cost_aware:seed13 | 13 | 0.8339 | 0.6167 | 0.6965 | 0.5893 | 999.3775 | 873.5000 | 2110.2500 | 0.6787 | -0.0336 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
