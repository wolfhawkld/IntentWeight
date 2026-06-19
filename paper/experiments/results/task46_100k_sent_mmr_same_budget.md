# Task46 Dense+Sentence-MMR Same-Budget Baseline

- Scale: `100k`
- Evaluation split: `test`
- Dense candidate depth: `10`
- MMR lambda: `0.70`
- Sentence unit cap: `128` tokens
- Budget source: `task38=paper/experiments/results/task38_100k_calibrated_context_budget.rankings.json`

## Summary

| method_label | budget_target_run_id | hit@10 | hit_delta_vs_dense@10 | evidence_recall@10 | avg_context_tokens@10 | avg_budget_tokens@10 | budget_fill_ratio@10 | context_token_ratio_vs_dense@10 | context_token_saving_percent_vs_dense@10 | avg_selected_sentences@10 | avg_supported_chunks@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| budget_target | task38:task37_source:gated_cost_aware:seed13:token_budget_r0.95_m4 | 0.8681 | -0.002398 | 0.6824 | 1376 | 1376 | 1 | 0.9357 | 6.426 | 0 | 8.909 |
| budget_target | task38:task37_source:gated_cost_aware:seed17:token_budget_r0.95_m4 | 0.8657 | -0.004796 | 0.6766 | 1365 | 1365 | 1 | 0.9286 | 7.137 | 0 | 8.89 |
| budget_target | task38:task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4 | 0.8777 | 0.007194 | 0.6871 | 1397 | 1397 | 1 | 0.9502 | 4.98 | 0 | 8.902 |
| dense_sent_mmr | task38:task37_source:gated_cost_aware:seed13:token_budget_r0.95_m4 | 0.8705 | 0 | 0.7081 | 1288 | 1376 | 0.9361 | 0.876 | 12.4 | 52 | 9.995 |
| dense_sent_mmr | task38:task37_source:gated_cost_aware:seed17:token_budget_r0.95_m4 | 0.8705 | 0 | 0.7075 | 1278 | 1365 | 0.9362 | 0.8693 | 13.07 | 51.68 | 9.981 |
| dense_sent_mmr | task38:task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4 | 0.8705 | 0 | 0.7081 | 1302 | 1397 | 0.9321 | 0.8857 | 11.43 | 52.7 | 9.993 |
| dense_top10 |  | 0.8705 | 0 | 0.7081 | 1470 | 1470 | 1 | 1 | 0 | 0 | 10 |

## Paired Dense Comparison

| method_label | budget_target_run_id | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | token_down_nonworse_rate | mcnemar_p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense_sent_mmr | task38:task37_source:gated_cost_aware:seed13:token_budget_r0.95_m4 | 0.8705 | 0 | 0 | 0 | True | 0.876 | 12.4 | 0.7938 | 1 |
| dense_sent_mmr | task38:task37_source:gated_cost_aware:seed17:token_budget_r0.95_m4 | 0.8705 | 0 | 0 | 0 | True | 0.8693 | 13.07 | 0.7914 | 1 |
| dense_sent_mmr | task38:task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4 | 0.8705 | 0 | 0 | 0 | True | 0.8857 | 11.43 | 0.7578 | 1 |

## Notes

- Dense+SentMMR starts from dense top-k chunks and only compresses the final evidence context.
- Same-budget means the per-query sentence budget is capped by the selected target policy's final chunk-token budget.
- Hit and evidence-recall metrics use unique source chunks represented by selected sentences.
- Token metrics for SentMMR count selected sentence text, while dense and target rows count selected chunk text.
