# Task38 Calibrated Context Budget

- Scale: `task59_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | True | 0.0149 | 16.97 | 0.8303 | 3 |
| token_budget_r0.85_m5 | True | 0.0149 | 16.97 | 0.8303 | 3 |
| token_budget_r0.85_m6 | True | 0.0149 | 16.67 | 0.8333 | 3 |
| token_budget_r0.85_m7 | True | 0.0149 | 14.51 | 0.8549 | 3 |
| token_budget_r0.88_m4 | True | 0.0168 | 14.16 | 0.8584 | 3 |
| token_budget_r0.88_m5 | True | 0.0168 | 14.16 | 0.8584 | 3 |
| token_budget_r0.88_m6 | True | 0.0168 | 14.02 | 0.8598 | 3 |
| token_budget_r0.90_m4 | True | 0.0205 | 12.46 | 0.8754 | 3 |
| token_budget_r0.90_m5 | True | 0.0205 | 12.46 | 0.8754 | 3 |
| token_budget_r0.88_m7 | True | 0.0168 | 12.39 | 0.8761 | 3 |
| token_budget_r0.90_m6 | True | 0.0205 | 12.35 | 0.8765 | 3 |
| token_budget_r0.85_m8 | True | 0.0205 | 11.18 | 0.8882 | 3 |
| token_budget_r0.90_m7 | True | 0.0205 | 10.92 | 0.8908 | 3 |
| token_budget_r0.92_m4 | True | 0.0186 | 10.66 | 0.8934 | 3 |
| token_budget_r0.92_m5 | True | 0.0186 | 10.66 | 0.8934 | 3 |
| token_budget_r0.92_m6 | True | 0.0186 | 10.58 | 0.8942 | 3 |
| token_budget_r0.88_m8 | True | 0.0186 | 10.27 | 0.8973 | 3 |
| token_budget_r0.90_m8 | True | 0.0223 | 9.48 | 0.9052 | 3 |
| token_budget_r0.92_m7 | True | 0.0186 | 9.37 | 0.9063 | 3 |
| token_budget_r0.92_m8 | True | 0.0205 | 8.53 | 0.9147 | 3 |
| token_budget_r0.95_m4 | True | 0.0223 | 7.68 | 0.9232 | 3 |
| token_budget_r0.95_m5 | True | 0.0223 | 7.68 | 0.9232 | 3 |
| token_budget_r0.95_m6 | True | 0.0223 | 7.68 | 0.9232 | 3 |
| token_budget_r0.95_m7 | True | 0.0223 | 6.60 | 0.9340 | 3 |
| token_budget_r0.95_m8 | True | 0.0223 | 6.41 | 0.9359 | 3 |
| token_budget_r0.98_m4 | True | 0.0279 | 4.56 | 0.9544 | 3 |
| token_budget_r0.98_m5 | True | 0.0279 | 4.56 | 0.9544 | 3 |
| token_budget_r0.98_m6 | True | 0.0279 | 4.56 | 0.9544 | 3 |
| token_budget_r0.98_m7 | True | 0.0279 | 4.49 | 0.9551 | 3 |
| token_budget_r0.98_m8 | True | 0.0279 | 4.46 | 0.9554 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8705 | -0.0144 | -0.0264 | -0.0048 | False | 0.7667 | 23.33 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8657 | -0.0192 | -0.0336 | -0.0072 | False | 0.8108 | 18.92 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8753 | -0.0096 | -0.0192 | -0.0024 | False | 0.9022 | 9.78 | 0.125 | 0.9904 |
| task38 | 13 | 0.8657 | -0.0192 | -0.0384 | 0.0000 | False | 0.8360 | 16.40 | 0.07681 | 0.7866 |
| task38 | 17 | 0.8729 | -0.0120 | -0.0312 | 0.0072 | False | 0.8360 | 16.40 | 0.3323 | 0.7674 |
| task38 | 19 | 0.8681 | -0.0168 | -0.0360 | 0.0024 | False | 0.8312 | 16.88 | 0.1435 | 0.7962 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
