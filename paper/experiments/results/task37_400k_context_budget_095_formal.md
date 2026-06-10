# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.7634 | 0.5618 | 0.5867 | 0.5098 | 8.9312 | 1270.5889 | 0.8572 | -0.0084 |
| dense |  |  | 0.7718 | 0.5777 | 0.5876 | 0.5174 | 10.0000 | 1482.2987 | 1.0000 | 0.0000 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.7768 | 0.5586 | 0.5644 | 0.4914 | 8.9060 | 1347.6913 | 0.9092 | 0.0050 |
| gated_fixed:gated_cost_aware:seed13 |  | 13 | 0.7936 | 0.5754 | 0.5662 | 0.4990 | 10.0000 | 1546.8221 | 1.0435 | 0.0218 |
| gated_fixed:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.7869 | 0.5769 | 0.5898 | 0.5130 | 8.9128 | 1324.5688 | 0.8936 | 0.0151 |
| gated_fixed:gated_cost_aware:seed17 |  | 17 | 0.8037 | 0.5940 | 0.5916 | 0.5203 | 10.0000 | 1520.4547 | 1.0257 | 0.0319 |
| gated_fixed:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.7735 | 0.5673 | 0.5844 | 0.5065 | 8.9279 | 1354.7534 | 0.9140 | 0.0017 |
| gated_fixed:gated_cost_aware:seed19 |  | 19 | 0.7903 | 0.5883 | 0.5862 | 0.5156 | 10.0000 | 1571.1023 | 1.0599 | 0.0185 |
| task29_C:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.7567 | 0.5379 | 0.5619 | 0.4810 | 7.9044 | 1208.4832 | 0.8153 | -0.0151 |
| task29_C:gated_cost_aware:seed13 |  | 13 | 0.7802 | 0.5577 | 0.5648 | 0.4903 | 8.9765 | 1401.1443 | 0.9453 | 0.0084 |
| task29_C:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.7668 | 0.5523 | 0.5873 | 0.5012 | 7.8926 | 1180.8507 | 0.7966 | -0.0050 |
| task29_C:gated_cost_aware:seed17 |  | 17 | 0.7869 | 0.5727 | 0.5898 | 0.5110 | 8.9597 | 1373.5268 | 0.9266 | 0.0151 |
| task29_C:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.7567 | 0.5436 | 0.5824 | 0.4953 | 8.0151 | 1227.6460 | 0.8282 | -0.0151 |
| task29_C:gated_cost_aware:seed19 |  | 19 | 0.7785 | 0.5682 | 0.5849 | 0.5061 | 9.0638 | 1435.6057 | 0.9685 | 0.0067 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
