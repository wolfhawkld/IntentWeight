# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8876 | 1264.9765 | 0.8591 | -0.0134 |
| dense |  |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 10.0000 | 1472.3876 | 1.0000 | 0.0000 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13 |  | 13 | 0.8775 | 0.6892 | 0.7017 | 0.6265 | 10.0000 | 1548.3742 | 1.0516 | 0.0101 |
| gated_fixed:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.8641 | 0.6737 | 0.7110 | 0.6294 | 8.9010 | 1349.1309 | 0.9163 | -0.0034 |
| gated_fixed:gated_cost_aware:seed17 |  | 17 | 0.8758 | 0.6887 | 0.7122 | 0.6362 | 10.0000 | 1537.9178 | 1.0445 | 0.0084 |
| gated_fixed:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.8742 | 0.6822 | 0.7159 | 0.6317 | 8.9010 | 1370.9748 | 0.9311 | 0.0067 |
| gated_fixed:gated_cost_aware:seed19 |  | 19 | 0.8792 | 0.6939 | 0.7164 | 0.6376 | 10.0000 | 1570.8591 | 1.0669 | 0.0117 |
| task29_C:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.8473 | 0.6492 | 0.6983 | 0.6076 | 7.9060 | 1213.4195 | 0.8241 | -0.0201 |
| task29_C:gated_cost_aware:seed13 |  | 13 | 0.8624 | 0.6708 | 0.7002 | 0.6180 | 8.9765 | 1391.5940 | 0.9451 | -0.0050 |
| task29_C:gated_cost_aware:seed17:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 17 | 0.8574 | 0.6562 | 0.7102 | 0.6194 | 7.9916 | 1215.5604 | 0.8256 | -0.0101 |
| task29_C:gated_cost_aware:seed17 |  | 17 | 0.8641 | 0.6744 | 0.7110 | 0.6286 | 9.0638 | 1398.1795 | 0.9496 | -0.0034 |
| task29_C:gated_cost_aware:seed19:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 19 | 0.8574 | 0.6601 | 0.7139 | 0.6204 | 7.9396 | 1222.1091 | 0.8300 | -0.0101 |
| task29_C:gated_cost_aware:seed19 |  | 19 | 0.8691 | 0.6759 | 0.7153 | 0.6288 | 9.0034 | 1413.9547 | 0.9603 | 0.0017 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
