# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:fixed_top5 | fixed_top5 |  | 0.6258 | 0.3850 | 0.4964 | 0.3752 | 5.0000 | 733.9547 | 0.4811 | -0.1023 |
| dense:fixed_top6 | fixed_top6 |  | 0.6560 | 0.4173 | 0.5015 | 0.3921 | 6.0000 | 874.1913 | 0.5730 | -0.0721 |
| dense:fixed_top7 | fixed_top7 |  | 0.6728 | 0.4368 | 0.5039 | 0.4016 | 7.0000 | 1033.5503 | 0.6775 | -0.0554 |
| dense:fixed_top8 | fixed_top8 |  | 0.6963 | 0.4603 | 0.5068 | 0.4120 | 8.0000 | 1190.0235 | 0.7800 | -0.0319 |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.7148 | 0.4821 | 0.5089 | 0.4211 | 8.9413 | 1314.0738 | 0.8613 | -0.0134 |
| dense:fixed_top9 | fixed_top9 |  | 0.7164 | 0.4841 | 0.5091 | 0.4217 | 9.0000 | 1357.2651 | 0.8896 | -0.0117 |
| dense |  |  | 0.7282 | 0.5041 | 0.5102 | 0.4303 | 10.0000 | 1525.6191 | 1.0000 | 0.0000 |
| dense:fixed_top10 | fixed_top10 |  | 0.7282 | 0.5041 | 0.5102 | 0.4303 | 10.0000 | 1525.6191 | 1.0000 | 0.0000 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
