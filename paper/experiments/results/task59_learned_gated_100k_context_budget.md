# Task38 Calibrated Context Budget

- Scale: `task59_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.92_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0205 | 19.00 | 0.8100 | 3 |
| token_budget_r0.85_m5 | False | -0.0205 | 18.96 | 0.8104 | 3 |
| token_budget_r0.85_m6 | False | -0.0205 | 18.72 | 0.8128 | 3 |
| token_budget_r0.85_m7 | False | -0.0205 | 17.56 | 0.8244 | 3 |
| token_budget_r0.88_m4 | False | -0.0168 | 16.38 | 0.8362 | 3 |
| token_budget_r0.88_m5 | False | -0.0168 | 16.38 | 0.8362 | 3 |
| token_budget_r0.88_m6 | False | -0.0168 | 16.35 | 0.8365 | 3 |
| token_budget_r0.88_m7 | False | -0.0168 | 15.92 | 0.8408 | 3 |
| token_budget_r0.90_m4 | False | -0.0168 | 14.89 | 0.8511 | 3 |
| token_budget_r0.90_m5 | False | -0.0168 | 14.88 | 0.8512 | 3 |
| token_budget_r0.90_m6 | False | -0.0168 | 14.86 | 0.8514 | 3 |
| token_budget_r0.90_m7 | False | -0.0168 | 14.64 | 0.8536 | 3 |
| token_budget_r0.85_m8 | False | -0.0186 | 13.58 | 0.8642 | 3 |
| token_budget_r0.92_m4 | False | -0.0149 | 13.26 | 0.8674 | 3 |
| token_budget_r0.92_m5 | False | -0.0149 | 13.26 | 0.8674 | 3 |
| token_budget_r0.92_m6 | False | -0.0149 | 13.24 | 0.8676 | 3 |
| token_budget_r0.92_m7 | False | -0.0149 | 13.11 | 0.8689 | 3 |
| token_budget_r0.88_m8 | False | -0.0168 | 12.84 | 0.8716 | 3 |
| token_budget_r0.90_m8 | False | -0.0168 | 12.23 | 0.8777 | 3 |
| token_budget_r0.92_m8 | False | -0.0149 | 11.22 | 0.8878 | 3 |
| token_budget_r0.95_m4 | False | -0.0149 | 9.94 | 0.9006 | 3 |
| token_budget_r0.95_m5 | False | -0.0149 | 9.94 | 0.9006 | 3 |
| token_budget_r0.95_m6 | False | -0.0149 | 9.94 | 0.9006 | 3 |
| token_budget_r0.95_m7 | False | -0.0149 | 9.94 | 0.9006 | 3 |
| token_budget_r0.95_m8 | False | -0.0149 | 9.44 | 0.9056 | 3 |
| token_budget_r0.98_m4 | False | -0.0168 | 7.39 | 0.9261 | 3 |
| token_budget_r0.98_m5 | False | -0.0168 | 7.39 | 0.9261 | 3 |
| token_budget_r0.98_m6 | False | -0.0168 | 7.39 | 0.9261 | 3 |
| token_budget_r0.98_m7 | False | -0.0168 | 7.39 | 0.9261 | 3 |
| token_budget_r0.98_m8 | False | -0.0168 | 7.36 | 0.9264 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8729 | -0.0120 | -0.0240 | -0.0024 | False | 0.8322 | 16.78 | 0.0625 | 0.9880 |
| dense_fixed |  | 0.8657 | -0.0192 | -0.0336 | -0.0072 | False | 0.8108 | 18.92 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8753 | -0.0096 | -0.0192 | -0.0024 | False | 0.9022 | 9.78 | 0.125 | 0.9904 |
| task38 | 13 | 0.8345 | -0.0504 | -0.0767 | -0.0240 | False | 0.8923 | 10.77 | 0.0001037 | 0.6930 |
| task38 | 17 | 0.8297 | -0.0552 | -0.0840 | -0.0288 | False | 0.8758 | 12.42 | 0.0001168 | 0.6547 |
| task38 | 19 | 0.8345 | -0.0504 | -0.0791 | -0.0216 | False | 0.8769 | 12.31 | 0.0007529 | 0.6307 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
