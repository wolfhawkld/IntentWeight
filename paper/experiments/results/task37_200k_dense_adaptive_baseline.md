# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:fixed_top5 | fixed_top5 |  | 0.7299 | 0.5219 | 0.6188 | 0.5137 | 5.0000 | 742.2987 | 0.5140 | -0.0671 |
| dense:fixed_top6 | fixed_top6 |  | 0.7483 | 0.5459 | 0.6219 | 0.5280 | 6.0000 | 878.8255 | 0.6086 | -0.0487 |
| dense:fixed_top7 | fixed_top7 |  | 0.7617 | 0.5670 | 0.6238 | 0.5390 | 7.0000 | 1014.1426 | 0.7023 | -0.0352 |
| dense:fixed_top8 | fixed_top8 |  | 0.7768 | 0.5839 | 0.6257 | 0.5478 | 8.0000 | 1156.2987 | 0.8007 | -0.0201 |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.7852 | 0.6020 | 0.6266 | 0.5559 | 8.9077 | 1253.5537 | 0.8680 | -0.0117 |
| dense:fixed_top9 | fixed_top9 |  | 0.7903 | 0.6072 | 0.6272 | 0.5581 | 9.0000 | 1298.3087 | 0.8990 | -0.0067 |
| dense |  |  | 0.7970 | 0.6202 | 0.6279 | 0.5643 | 10.0000 | 1444.1242 | 1.0000 | 0.0000 |
| dense:fixed_top10 | fixed_top10 |  | 0.7970 | 0.6202 | 0.6279 | 0.5643 | 10.0000 | 1444.1242 | 1.0000 | 0.0000 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
