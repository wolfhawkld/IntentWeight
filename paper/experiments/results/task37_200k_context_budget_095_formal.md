# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.7852 | 0.6020 | 0.6266 | 0.5559 | 8.9077 | 1253.5537 | 0.8680 | -0.0117 |
| dense |  |  | 0.7970 | 0.6202 | 0.6279 | 0.5643 | 10.0000 | 1444.1242 | 1.0000 | 0.0000 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.8289 | 0.6142 | 0.6359 | 0.5516 | 8.9010 | 1356.0587 | 0.9390 | 0.0319 |
| gated_fixed:gated_cost_aware:seed13 |  | 13 | 0.8440 | 0.6315 | 0.6375 | 0.5591 | 10.0000 | 1564.4983 | 1.0834 | 0.0470 |
| gated_fixed:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.8104 | 0.6019 | 0.6345 | 0.5472 | 8.9211 | 1328.1141 | 0.9197 | 0.0134 |
| gated_fixed:gated_cost_aware:seed17 |  | 17 | 0.8255 | 0.6196 | 0.6361 | 0.5546 | 10.0000 | 1535.8339 | 1.0635 | 0.0285 |
| gated_fixed:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.8188 | 0.6136 | 0.6396 | 0.5591 | 8.9010 | 1343.1376 | 0.9301 | 0.0218 |
| gated_fixed:gated_cost_aware:seed19 |  | 19 | 0.8339 | 0.6366 | 0.6412 | 0.5686 | 10.0000 | 1542.0805 | 1.0678 | 0.0369 |
| task29_C:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.8121 | 0.5940 | 0.6339 | 0.5407 | 7.8440 | 1187.2919 | 0.8222 | 0.0151 |
| task29_C:gated_cost_aware:seed13 |  | 13 | 0.8339 | 0.6129 | 0.6365 | 0.5498 | 8.9027 | 1376.8708 | 0.9534 | 0.0369 |
| task29_C:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.8003 | 0.5848 | 0.6332 | 0.5384 | 7.9178 | 1175.0973 | 0.8137 | 0.0034 |
| task29_C:gated_cost_aware:seed17 |  | 17 | 0.8188 | 0.6041 | 0.6353 | 0.5471 | 8.9732 | 1371.6577 | 0.9498 | 0.0218 |
| task29_C:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.8020 | 0.5896 | 0.6375 | 0.5464 | 7.8138 | 1189.3020 | 0.8235 | 0.0050 |
| task29_C:gated_cost_aware:seed19 |  | 19 | 0.8221 | 0.6156 | 0.6399 | 0.5582 | 8.8826 | 1380.8473 | 0.9562 | 0.0252 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
