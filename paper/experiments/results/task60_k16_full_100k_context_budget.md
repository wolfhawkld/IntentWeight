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
| token_budget_r0.85_m4 | False | -0.0056 | 19.27 | 0.8073 | 3 |
| token_budget_r0.85_m5 | False | -0.0056 | 19.27 | 0.8073 | 3 |
| token_budget_r0.85_m6 | False | -0.0056 | 19.21 | 0.8079 | 3 |
| token_budget_r0.85_m7 | False | -0.0056 | 17.92 | 0.8208 | 3 |
| token_budget_r0.88_m4 | False | -0.0056 | 16.52 | 0.8348 | 3 |
| token_budget_r0.88_m5 | False | -0.0056 | 16.52 | 0.8348 | 3 |
| token_budget_r0.88_m6 | False | -0.0056 | 16.48 | 0.8352 | 3 |
| token_budget_r0.88_m7 | False | -0.0056 | 15.75 | 0.8425 | 3 |
| token_budget_r0.90_m4 | False | -0.0037 | 14.29 | 0.8571 | 3 |
| token_budget_r0.90_m5 | False | -0.0037 | 14.29 | 0.8571 | 3 |
| token_budget_r0.90_m6 | False | -0.0037 | 14.26 | 0.8574 | 3 |
| token_budget_r0.90_m7 | False | -0.0037 | 13.83 | 0.8617 | 3 |
| token_budget_r0.85_m8 | True | 0.0000 | 13.67 | 0.8633 | 3 |
| token_budget_r0.88_m8 | False | -0.0019 | 12.71 | 0.8729 | 3 |
| token_budget_r0.92_m4 | False | -0.0019 | 12.20 | 0.8780 | 3 |
| token_budget_r0.92_m5 | False | -0.0019 | 12.20 | 0.8780 | 3 |
| token_budget_r0.92_m6 | False | -0.0019 | 12.17 | 0.8783 | 3 |
| token_budget_r0.90_m8 | False | -0.0019 | 12.12 | 0.8788 | 3 |
| token_budget_r0.92_m7 | False | -0.0019 | 11.88 | 0.8812 | 3 |
| token_budget_r0.92_m8 | False | -0.0019 | 10.91 | 0.8909 | 3 |
| token_budget_r0.95_m4 | False | -0.0019 | 9.76 | 0.9024 | 3 |
| token_budget_r0.95_m5 | False | -0.0019 | 9.76 | 0.9024 | 3 |
| token_budget_r0.95_m6 | False | -0.0019 | 9.73 | 0.9027 | 3 |
| token_budget_r0.95_m7 | False | -0.0019 | 9.73 | 0.9027 | 3 |
| token_budget_r0.95_m8 | False | -0.0019 | 9.55 | 0.9045 | 3 |
| token_budget_r0.98_m4 | False | -0.0019 | 7.22 | 0.9278 | 3 |
| token_budget_r0.98_m5 | False | -0.0019 | 7.22 | 0.9278 | 3 |
| token_budget_r0.98_m6 | False | -0.0019 | 7.22 | 0.9278 | 3 |
| token_budget_r0.98_m7 | False | -0.0019 | 7.22 | 0.9278 | 3 |
| token_budget_r0.98_m8 | False | -0.0019 | 7.20 | 0.9280 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8402 | 15.98 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8729 | 0.0144 | -0.0024 | 0.0312 | True | 0.8967 | 10.33 | 0.1796 | 0.7650 |
| task38 | 17 | 0.8657 | 0.0072 | -0.0120 | 0.0264 | False | 0.8809 | 11.91 | 0.6291 | 0.7794 |
| task38 | 19 | 0.8609 | 0.0024 | -0.0168 | 0.0216 | False | 0.9076 | 9.24 | 1 | 0.7482 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
