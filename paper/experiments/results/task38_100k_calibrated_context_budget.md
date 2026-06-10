# Task38 Calibrated Context Budget

- Scale: `100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.95_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0074 | 20.09 | 0.7991 | 3 |
| token_budget_r0.85_m5 | False | -0.0074 | 20.08 | 0.7992 | 3 |
| token_budget_r0.85_m6 | False | -0.0074 | 19.86 | 0.8014 | 3 |
| token_budget_r0.85_m7 | False | -0.0074 | 18.90 | 0.8110 | 3 |
| token_budget_r0.88_m4 | False | -0.0093 | 17.47 | 0.8253 | 3 |
| token_budget_r0.88_m5 | False | -0.0093 | 17.46 | 0.8254 | 3 |
| token_budget_r0.88_m6 | False | -0.0093 | 17.43 | 0.8257 | 3 |
| token_budget_r0.88_m7 | False | -0.0093 | 17.16 | 0.8284 | 3 |
| token_budget_r0.90_m4 | False | -0.0056 | 15.66 | 0.8434 | 3 |
| token_budget_r0.90_m5 | False | -0.0056 | 15.65 | 0.8435 | 3 |
| token_budget_r0.90_m6 | False | -0.0056 | 15.63 | 0.8437 | 3 |
| token_budget_r0.90_m7 | False | -0.0056 | 15.55 | 0.8445 | 3 |
| token_budget_r0.85_m8 | False | -0.0093 | 15.37 | 0.8463 | 3 |
| token_budget_r0.88_m8 | False | -0.0093 | 14.56 | 0.8544 | 3 |
| token_budget_r0.92_m4 | False | -0.0056 | 13.99 | 0.8601 | 3 |
| token_budget_r0.92_m5 | False | -0.0056 | 13.99 | 0.8601 | 3 |
| token_budget_r0.92_m6 | False | -0.0056 | 13.98 | 0.8602 | 3 |
| token_budget_r0.92_m7 | False | -0.0056 | 13.97 | 0.8603 | 3 |
| token_budget_r0.90_m8 | False | -0.0074 | 13.62 | 0.8638 | 3 |
| token_budget_r0.92_m8 | False | -0.0056 | 12.71 | 0.8729 | 3 |
| token_budget_r0.95_m4 | True | 0.0019 | 11.31 | 0.8869 | 3 |
| token_budget_r0.95_m5 | True | 0.0019 | 11.31 | 0.8869 | 3 |
| token_budget_r0.95_m6 | True | 0.0019 | 11.31 | 0.8869 | 3 |
| token_budget_r0.95_m7 | True | 0.0019 | 11.31 | 0.8869 | 3 |
| token_budget_r0.95_m8 | True | 0.0019 | 10.97 | 0.8903 | 3 |
| token_budget_r0.98_m4 | True | 0.0019 | 9.36 | 0.9064 | 3 |
| token_budget_r0.98_m5 | True | 0.0019 | 9.36 | 0.9064 | 3 |
| token_budget_r0.98_m6 | True | 0.0019 | 9.36 | 0.9064 | 3 |
| token_budget_r0.98_m7 | True | 0.0019 | 9.36 | 0.9064 | 3 |
| token_budget_r0.98_m8 | True | 0.0019 | 9.33 | 0.9067 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8561 | -0.0144 | -0.0264 | -0.0048 | False | 0.8617 | 13.83 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8513 | -0.0192 | -0.0336 | -0.0072 | False | 0.8126 | 18.74 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8609 | -0.0096 | -0.0192 | -0.0024 | False | 0.9046 | 9.54 | 0.125 | 0.9904 |
| task38 | 13 | 0.8681 | -0.0024 | -0.0240 | 0.0192 | False | 0.9357 | 6.43 | 1 | 0.6691 |
| task38 | 17 | 0.8657 | -0.0048 | -0.0240 | 0.0120 | False | 0.9286 | 7.14 | 0.8036 | 0.6715 |
| task38 | 19 | 0.8777 | 0.0072 | -0.0144 | 0.0312 | False | 0.9502 | 4.98 | 0.69 | 0.6355 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
