# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m8`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0074 | 19.27 | 0.8073 | 3 |
| token_budget_r0.85_m5 | False | -0.0074 | 19.26 | 0.8074 | 3 |
| token_budget_r0.85_m6 | False | -0.0074 | 18.81 | 0.8119 | 3 |
| token_budget_r0.85_m7 | False | -0.0074 | 17.89 | 0.8211 | 3 |
| token_budget_r0.88_m4 | False | -0.0000 | 16.92 | 0.8308 | 3 |
| token_budget_r0.88_m5 | False | -0.0000 | 16.92 | 0.8308 | 3 |
| token_budget_r0.88_m6 | False | -0.0000 | 16.62 | 0.8338 | 3 |
| token_budget_r0.88_m7 | False | -0.0000 | 16.04 | 0.8396 | 3 |
| token_budget_r0.90_m4 | False | -0.0000 | 14.58 | 0.8542 | 3 |
| token_budget_r0.90_m5 | False | -0.0000 | 14.58 | 0.8542 | 3 |
| token_budget_r0.90_m6 | False | -0.0000 | 14.54 | 0.8546 | 3 |
| token_budget_r0.90_m7 | False | -0.0000 | 14.19 | 0.8581 | 3 |
| token_budget_r0.85_m8 | True | 0.0037 | 13.59 | 0.8641 | 3 |
| token_budget_r0.88_m8 | True | 0.0037 | 12.67 | 0.8733 | 3 |
| token_budget_r0.90_m8 | True | 0.0037 | 12.17 | 0.8783 | 3 |
| token_budget_r0.92_m4 | True | 0.0037 | 12.16 | 0.8784 | 3 |
| token_budget_r0.92_m5 | True | 0.0037 | 12.16 | 0.8784 | 3 |
| token_budget_r0.92_m6 | True | 0.0037 | 12.16 | 0.8784 | 3 |
| token_budget_r0.92_m7 | True | 0.0037 | 11.94 | 0.8806 | 3 |
| token_budget_r0.92_m8 | True | 0.0037 | 10.83 | 0.8917 | 3 |
| token_budget_r0.95_m4 | True | 0.0037 | 9.37 | 0.9063 | 3 |
| token_budget_r0.95_m5 | True | 0.0037 | 9.37 | 0.9063 | 3 |
| token_budget_r0.95_m6 | True | 0.0037 | 9.37 | 0.9063 | 3 |
| token_budget_r0.95_m7 | True | 0.0037 | 9.37 | 0.9063 | 3 |
| token_budget_r0.95_m8 | True | 0.0037 | 9.16 | 0.9084 | 3 |
| token_budget_r0.98_m4 | True | 0.0037 | 7.28 | 0.9272 | 3 |
| token_budget_r0.98_m5 | True | 0.0037 | 7.28 | 0.9272 | 3 |
| token_budget_r0.98_m6 | True | 0.0037 | 7.28 | 0.9272 | 3 |
| token_budget_r0.98_m7 | True | 0.0037 | 7.28 | 0.9272 | 3 |
| token_budget_r0.98_m8 | True | 0.0037 | 7.28 | 0.9272 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8402 | 15.98 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8729 | 0.0144 | -0.0024 | 0.0312 | True | 0.8906 | 10.94 | 0.1796 | 0.7794 |
| task38 | 17 | 0.8681 | 0.0096 | -0.0096 | 0.0288 | True | 0.9045 | 9.55 | 0.4545 | 0.7386 |
| task38 | 19 | 0.8585 | 0.0000 | -0.0216 | 0.0168 | False | 0.8894 | 11.06 | 1 | 0.7530 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
