# Task38 Calibrated Context Budget

- Scale: `science_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | True | 0.0130 | 16.83 | 0.8317 | 3 |
| token_budget_r0.85_m5 | True | 0.0130 | 16.83 | 0.8317 | 3 |
| token_budget_r0.85_m6 | True | 0.0130 | 16.45 | 0.8355 | 3 |
| token_budget_r0.85_m7 | True | 0.0093 | 15.54 | 0.8446 | 3 |
| token_budget_r0.88_m4 | True | 0.0130 | 14.31 | 0.8569 | 3 |
| token_budget_r0.88_m5 | True | 0.0130 | 14.31 | 0.8569 | 3 |
| token_budget_r0.88_m6 | True | 0.0130 | 13.98 | 0.8602 | 3 |
| token_budget_r0.88_m7 | True | 0.0130 | 13.55 | 0.8645 | 3 |
| token_budget_r0.90_m4 | True | 0.0168 | 12.32 | 0.8768 | 3 |
| token_budget_r0.90_m5 | True | 0.0168 | 12.32 | 0.8768 | 3 |
| token_budget_r0.90_m6 | True | 0.0168 | 12.11 | 0.8789 | 3 |
| token_budget_r0.90_m7 | True | 0.0168 | 11.82 | 0.8818 | 3 |
| token_budget_r0.85_m8 | True | 0.0168 | 11.78 | 0.8822 | 3 |
| token_budget_r0.88_m8 | True | 0.0168 | 10.99 | 0.8901 | 3 |
| token_budget_r0.92_m4 | True | 0.0168 | 10.39 | 0.8961 | 3 |
| token_budget_r0.92_m5 | True | 0.0168 | 10.39 | 0.8961 | 3 |
| token_budget_r0.92_m6 | True | 0.0168 | 10.39 | 0.8961 | 3 |
| token_budget_r0.92_m7 | True | 0.0168 | 10.20 | 0.8980 | 3 |
| token_budget_r0.90_m8 | True | 0.0168 | 10.05 | 0.8995 | 3 |
| token_budget_r0.92_m8 | True | 0.0168 | 9.14 | 0.9086 | 3 |
| token_budget_r0.95_m4 | True | 0.0168 | 8.01 | 0.9199 | 3 |
| token_budget_r0.95_m5 | True | 0.0168 | 8.01 | 0.9199 | 3 |
| token_budget_r0.95_m6 | True | 0.0168 | 8.01 | 0.9199 | 3 |
| token_budget_r0.95_m7 | True | 0.0168 | 7.91 | 0.9209 | 3 |
| token_budget_r0.95_m8 | True | 0.0168 | 7.57 | 0.9243 | 3 |
| token_budget_r0.98_m4 | True | 0.0168 | 5.27 | 0.9473 | 3 |
| token_budget_r0.98_m5 | True | 0.0168 | 5.27 | 0.9473 | 3 |
| token_budget_r0.98_m6 | True | 0.0168 | 5.27 | 0.9473 | 3 |
| token_budget_r0.98_m7 | True | 0.0168 | 5.27 | 0.9473 | 3 |
| token_budget_r0.98_m8 | True | 0.0168 | 5.25 | 0.9475 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8849 | -0.0144 | -0.0264 | -0.0048 | False | 0.7740 | 22.60 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8897 | -0.0096 | -0.0192 | -0.0024 | False | 0.7963 | 20.37 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8969 | -0.0024 | -0.0072 | 0.0000 | True | 0.8980 | 10.20 | 1 | 0.9976 |
| task38 | 13 | 0.8873 | -0.0120 | -0.0336 | 0.0096 | False | 0.8079 | 19.21 | 0.3833 | 0.8201 |
| task38 | 17 | 0.8993 | 0.0000 | -0.0168 | 0.0168 | False | 0.8247 | 17.53 | 1 | 0.7914 |
| task38 | 19 | 0.8897 | -0.0096 | -0.0288 | 0.0096 | False | 0.7947 | 20.53 | 0.4545 | 0.8058 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
