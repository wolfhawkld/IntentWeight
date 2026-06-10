# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.7148 | 0.4821 | 0.5089 | 0.4211 | 8.9413 | 1314.0738 | 0.8613 | -0.0134 |
| dense |  |  | 0.7282 | 0.5041 | 0.5102 | 0.4303 | 10.0000 | 1525.6191 | 1.0000 | 0.0000 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.7534 | 0.4990 | 0.5196 | 0.4291 | 8.9245 | 1404.2299 | 0.9204 | 0.0252 |
| gated_fixed:gated_cost_aware:seed13 |  | 13 | 0.7701 | 0.5161 | 0.5213 | 0.4363 | 10.0000 | 1622.3473 | 1.0634 | 0.0419 |
| gated_fixed:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.7332 | 0.4958 | 0.4995 | 0.4216 | 8.9463 | 1401.7332 | 0.9188 | 0.0050 |
| gated_fixed:gated_cost_aware:seed17 |  | 17 | 0.7534 | 0.5180 | 0.5016 | 0.4306 | 10.0000 | 1628.7013 | 1.0676 | 0.0252 |
| gated_fixed:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.7433 | 0.4953 | 0.4944 | 0.4188 | 8.9312 | 1393.6342 | 0.9135 | 0.0151 |
| gated_fixed:gated_cost_aware:seed19 |  | 19 | 0.7617 | 0.5141 | 0.4963 | 0.4267 | 10.0000 | 1608.7366 | 1.0545 | 0.0336 |
| task29_C:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.7332 | 0.4813 | 0.5172 | 0.4202 | 7.9379 | 1249.3926 | 0.8189 | 0.0050 |
| task29_C:gated_cost_aware:seed13 |  | 13 | 0.7567 | 0.5016 | 0.5199 | 0.4292 | 8.9899 | 1455.7869 | 0.9542 | 0.0285 |
| task29_C:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.7148 | 0.4742 | 0.4972 | 0.4115 | 7.9966 | 1242.6711 | 0.8145 | -0.0134 |
| task29_C:gated_cost_aware:seed17 |  | 17 | 0.7399 | 0.5009 | 0.5001 | 0.4233 | 9.0403 | 1448.4379 | 0.9494 | 0.0117 |
| task29_C:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.7181 | 0.4724 | 0.4914 | 0.4085 | 7.9648 | 1242.2399 | 0.8143 | -0.0101 |
| task29_C:gated_cost_aware:seed19 |  | 19 | 0.7433 | 0.4979 | 0.4943 | 0.4192 | 9.0168 | 1450.2349 | 0.9506 | 0.0151 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
