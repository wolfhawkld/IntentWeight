# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:fixed_top5 | fixed_top5 |  | 0.8104 | 0.6111 | 0.7004 | 0.5993 | 5.0000 | 770.5185 | 0.5233 | -0.0570 |
| dense:fixed_top6 | fixed_top6 |  | 0.8272 | 0.6353 | 0.7032 | 0.6132 | 6.0000 | 910.0185 | 0.6181 | -0.0403 |
| dense:fixed_top7 | fixed_top7 |  | 0.8406 | 0.6575 | 0.7051 | 0.6250 | 7.0000 | 1046.3289 | 0.7106 | -0.0268 |
| dense:fixed_top8 | fixed_top8 |  | 0.8490 | 0.6756 | 0.7062 | 0.6347 | 8.0000 | 1190.2030 | 0.8083 | -0.0185 |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8876 | 1264.9765 | 0.8591 | -0.0134 |
| dense:fixed_top9 | fixed_top9 |  | 0.8574 | 0.6904 | 0.7071 | 0.6426 | 9.0000 | 1332.4950 | 0.9050 | -0.0101 |
| dense |  |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 10.0000 | 1472.3876 | 1.0000 | 0.0000 |
| dense:fixed_top10 | fixed_top10 |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 10.0000 | 1472.3876 | 1.0000 | 0.0000 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
