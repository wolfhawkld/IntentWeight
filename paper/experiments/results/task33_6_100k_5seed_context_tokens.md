# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 1472.3876 | 1312.0000 | 2908.2500 | 1.0000 | 0.0000 |
| task29_C_original:gated_cost_aware:seed13 | 13 | 0.8624 | 0.6708 | 0.7002 | 0.6180 | 1391.5940 | 1212.5000 | 2617.5000 | 0.9451 | -0.0050 |
| task29_C_original:gated_cost_aware:seed17 | 17 | 0.8641 | 0.6744 | 0.7110 | 0.6286 | 1398.1795 | 1234.5000 | 2804.5000 | 0.9496 | -0.0034 |
| task29_C_original:gated_cost_aware:seed19 | 19 | 0.8691 | 0.6759 | 0.7153 | 0.6288 | 1413.9547 | 1246.0000 | 2913.7500 | 0.9603 | 0.0017 |
| task33_6_extra:gated_cost_aware:seed23 | 23 | 0.8859 | 0.6945 | 0.7055 | 0.6362 | 1409.7869 | 1243.0000 | 2715.2500 | 0.9575 | 0.0185 |
| task33_6_extra:gated_cost_aware:seed29 | 29 | 0.8725 | 0.6792 | 0.7090 | 0.6281 | 1385.6309 | 1209.5000 | 2742.7500 | 0.9411 | 0.0050 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
