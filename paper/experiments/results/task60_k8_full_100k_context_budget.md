# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.95_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0130 | 19.08 | 0.8092 | 3 |
| token_budget_r0.85_m5 | False | -0.0130 | 19.08 | 0.8092 | 3 |
| token_budget_r0.85_m6 | False | -0.0130 | 18.98 | 0.8102 | 3 |
| token_budget_r0.85_m7 | False | -0.0130 | 17.75 | 0.8225 | 3 |
| token_budget_r0.88_m4 | False | -0.0074 | 16.24 | 0.8376 | 3 |
| token_budget_r0.88_m5 | False | -0.0074 | 16.24 | 0.8376 | 3 |
| token_budget_r0.88_m6 | False | -0.0074 | 16.20 | 0.8380 | 3 |
| token_budget_r0.88_m7 | False | -0.0074 | 15.61 | 0.8439 | 3 |
| token_budget_r0.90_m4 | False | -0.0074 | 14.43 | 0.8557 | 3 |
| token_budget_r0.90_m5 | False | -0.0074 | 14.43 | 0.8557 | 3 |
| token_budget_r0.90_m6 | False | -0.0074 | 14.39 | 0.8561 | 3 |
| token_budget_r0.85_m8 | False | -0.0019 | 14.07 | 0.8593 | 3 |
| token_budget_r0.90_m7 | False | -0.0074 | 14.00 | 0.8600 | 3 |
| token_budget_r0.88_m8 | False | -0.0019 | 13.09 | 0.8691 | 3 |
| token_budget_r0.92_m4 | False | -0.0019 | 12.49 | 0.8751 | 3 |
| token_budget_r0.92_m5 | False | -0.0019 | 12.49 | 0.8751 | 3 |
| token_budget_r0.92_m6 | False | -0.0019 | 12.49 | 0.8751 | 3 |
| token_budget_r0.90_m8 | False | -0.0019 | 12.48 | 0.8752 | 3 |
| token_budget_r0.92_m7 | False | -0.0019 | 12.24 | 0.8776 | 3 |
| token_budget_r0.92_m8 | False | -0.0019 | 11.31 | 0.8869 | 3 |
| token_budget_r0.95_m4 | False | -0.0000 | 9.81 | 0.9019 | 3 |
| token_budget_r0.95_m5 | False | -0.0000 | 9.81 | 0.9019 | 3 |
| token_budget_r0.95_m6 | False | -0.0000 | 9.81 | 0.9019 | 3 |
| token_budget_r0.95_m7 | False | -0.0000 | 9.68 | 0.9032 | 3 |
| token_budget_r0.95_m8 | False | -0.0000 | 9.44 | 0.9056 | 3 |
| token_budget_r0.98_m4 | False | -0.0000 | 6.79 | 0.9321 | 3 |
| token_budget_r0.98_m5 | False | -0.0000 | 6.79 | 0.9321 | 3 |
| token_budget_r0.98_m6 | False | -0.0000 | 6.79 | 0.9321 | 3 |
| token_budget_r0.98_m7 | False | -0.0000 | 6.79 | 0.9321 | 3 |
| token_budget_r0.98_m8 | False | -0.0000 | 6.78 | 0.9322 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8565 | 14.35 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8705 | 0.0120 | -0.0048 | 0.0288 | True | 0.9363 | 6.37 | 0.2668 | 0.6763 |
| task38 | 17 | 0.8753 | 0.0168 | 0.0000 | 0.0336 | True | 0.9364 | 6.36 | 0.09229 | 0.6930 |
| task38 | 19 | 0.8729 | 0.0144 | -0.0024 | 0.0336 | True | 0.9404 | 5.96 | 0.1796 | 0.6835 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
