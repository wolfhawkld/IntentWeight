# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:fixed_top5 | fixed_top5 |  | 0.6896 | 0.4706 | 0.5762 | 0.4647 | 5.0000 | 731.6376 | 0.4936 | -0.0822 |
| dense:fixed_top6 | fixed_top6 |  | 0.7148 | 0.4994 | 0.5804 | 0.4805 | 6.0000 | 874.2114 | 0.5898 | -0.0570 |
| dense:fixed_top7 | fixed_top7 |  | 0.7349 | 0.5264 | 0.5833 | 0.4936 | 7.0000 | 1029.4413 | 0.6945 | -0.0369 |
| dense:fixed_top8 | fixed_top8 |  | 0.7517 | 0.5426 | 0.5854 | 0.5016 | 8.0000 | 1170.9832 | 0.7900 | -0.0201 |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.7634 | 0.5618 | 0.5867 | 0.5098 | 8.9312 | 1270.5889 | 0.8572 | -0.0084 |
| dense:fixed_top9 | fixed_top9 |  | 0.7668 | 0.5661 | 0.5870 | 0.5114 | 9.0000 | 1324.4463 | 0.8935 | -0.0050 |
| dense |  |  | 0.7718 | 0.5777 | 0.5876 | 0.5174 | 10.0000 | 1482.2987 | 1.0000 | 0.0000 |
| dense:fixed_top10 | fixed_top10 |  | 0.7718 | 0.5777 | 0.5876 | 0.5174 | 10.0000 | 1482.2987 | 1.0000 | 0.0000 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
