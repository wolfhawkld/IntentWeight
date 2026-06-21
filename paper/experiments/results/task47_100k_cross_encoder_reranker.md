# Task47 Cross-Encoder Reranker Same-Budget Baseline

- Scale: `100k`
- Evaluation split: `test`
- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Candidate depth: `50`
- Reranked pairs: `20850`
- Predict elapsed seconds: `414.802`

## Summary

| method_label | seed | budget_target_run_id | hit@10 | hit_delta_vs_dense@10 | evidence_recall@10 | avg_context_tokens@10 | avg_budget_tokens@10 | budget_fill_ratio@10 | context_token_saving_percent_vs_dense@10 | avg_context_chunks@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense_top10 |  |  | 0.8705 | 0 | 0.7081 | 1470 | 1470 | 1 | 0 | 10 |
| intentweight_target | 13 |  | 0.8681 | -0.002398 | 0.6824 | 1376 | 1376 | 1 | 6.426 | 8.909 |
| intentweight_target | 17 |  | 0.8657 | -0.004796 | 0.6766 | 1365 | 1365 | 1 | 7.137 | 8.89 |
| intentweight_target | 19 |  | 0.8777 | 0.007194 | 0.6871 | 1397 | 1397 | 1 | 4.98 | 8.902 |
| reranker_same_budget | 13 | task38:task37_source:gated_cost_aware:seed13:token_budget_r0.95_m4 | 0.8633 | -0.007194 | 0.7031 | 1370 | 1376 | 0.9955 | 6.843 | 8.743 |
| reranker_same_budget | 17 | task38:task37_source:gated_cost_aware:seed17:token_budget_r0.95_m4 | 0.8633 | -0.007194 | 0.6975 | 1360 | 1365 | 0.9962 | 7.494 | 8.652 |
| reranker_same_budget | 19 | task38:task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4 | 0.8729 | 0.002398 | 0.7044 | 1390 | 1397 | 0.9953 | 5.427 | 8.679 |
| reranker_top10 |  |  | 0.8777 | 0.007194 | 0.7332 | 1792 | 1792 | 1 | -21.91 | 10 |

## Paired Dense Comparison

| method_label | seed | budget_target_run_id | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reranker_top10 |  |  | 0.8777 | 0.007194 | -0.01918 | 0.03357 | False | 1.219 | -21.91 | 0.7359 |
| intentweight_target | 13 |  | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.9357 | 6.426 | 1 |
| intentweight_target | 17 |  | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.9286 | 7.137 | 0.8036 |
| intentweight_target | 19 |  | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.9502 | 4.98 | 0.69 |
| reranker_same_budget | 13 | task38:task37_source:gated_cost_aware:seed13:token_budget_r0.95_m4 | 0.8633 | -0.007194 | -0.03837 | 0.02158 | False | 0.9316 | 6.843 | 0.7493 |
| reranker_same_budget | 17 | task38:task37_source:gated_cost_aware:seed17:token_budget_r0.95_m4 | 0.8633 | -0.007194 | -0.03597 | 0.02158 | False | 0.9251 | 7.494 | 0.7493 |
| reranker_same_budget | 19 | task38:task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4 | 0.8729 | 0.002398 | -0.02644 | 0.02878 | False | 0.9457 | 5.427 | 1 |

## Notes

- The cross-encoder reranks dense candidates; it does not retrieve over the full corpus.
- Same-budget rows greedily keep reranked chunks under each target IntentWeight per-query token budget, with a one-chunk safety prefix.
- Token metrics count selected chunk text only; they do not include reranker compute or model prompt tokens.
