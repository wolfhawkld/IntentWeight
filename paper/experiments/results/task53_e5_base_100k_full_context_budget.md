# Task38 Calibrated Context Budget

- Scale: `100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.88_m7`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0037 | 16.85 | 0.8315 | 3 |
| token_budget_r0.85_m5 | False | -0.0037 | 16.64 | 0.8336 | 3 |
| token_budget_r0.85_m6 | False | -0.0037 | 16.32 | 0.8368 | 3 |
| token_budget_r0.85_m7 | False | -0.0019 | 15.46 | 0.8454 | 3 |
| token_budget_r0.88_m4 | False | -0.0019 | 13.67 | 0.8633 | 3 |
| token_budget_r0.88_m5 | False | -0.0019 | 13.67 | 0.8633 | 3 |
| token_budget_r0.88_m6 | False | -0.0019 | 13.50 | 0.8650 | 3 |
| token_budget_r0.88_m7 | True | 0.0000 | 13.24 | 0.8676 | 3 |
| token_budget_r0.85_m8 | True | 0.0056 | 12.36 | 0.8764 | 3 |
| token_budget_r0.90_m4 | True | 0.0056 | 11.97 | 0.8803 | 3 |
| token_budget_r0.90_m5 | True | 0.0056 | 11.97 | 0.8803 | 3 |
| token_budget_r0.90_m6 | True | 0.0056 | 11.95 | 0.8805 | 3 |
| token_budget_r0.90_m7 | True | 0.0074 | 11.76 | 0.8824 | 3 |
| token_budget_r0.88_m8 | True | 0.0074 | 11.01 | 0.8899 | 3 |
| token_budget_r0.92_m4 | True | 0.0093 | 10.59 | 0.8941 | 3 |
| token_budget_r0.92_m5 | True | 0.0093 | 10.59 | 0.8941 | 3 |
| token_budget_r0.92_m6 | True | 0.0093 | 10.59 | 0.8941 | 3 |
| token_budget_r0.92_m7 | True | 0.0112 | 10.48 | 0.8952 | 3 |
| token_budget_r0.90_m8 | True | 0.0093 | 10.29 | 0.8971 | 3 |
| token_budget_r0.92_m8 | True | 0.0112 | 9.38 | 0.9062 | 3 |
| token_budget_r0.95_m4 | True | 0.0168 | 8.40 | 0.9160 | 3 |
| token_budget_r0.95_m5 | True | 0.0168 | 8.40 | 0.9160 | 3 |
| token_budget_r0.95_m6 | True | 0.0168 | 8.40 | 0.9160 | 3 |
| token_budget_r0.95_m7 | True | 0.0168 | 8.40 | 0.9160 | 3 |
| token_budget_r0.95_m8 | True | 0.0168 | 7.79 | 0.9221 | 3 |
| token_budget_r0.98_m4 | True | 0.0168 | 5.79 | 0.9421 | 3 |
| token_budget_r0.98_m5 | True | 0.0168 | 5.79 | 0.9421 | 3 |
| token_budget_r0.98_m6 | True | 0.0168 | 5.79 | 0.9421 | 3 |
| token_budget_r0.98_m7 | True | 0.0168 | 5.79 | 0.9421 | 3 |
| token_budget_r0.98_m8 | True | 0.0168 | 5.79 | 0.9421 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8609 | -0.0144 | -0.0264 | -0.0048 | False | 0.8232 | 17.68 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8633 | -0.0120 | -0.0240 | -0.0024 | False | 0.8221 | 17.79 | 0.0625 | 0.9880 |
| dense_fixed |  | 0.8657 | -0.0096 | -0.0192 | -0.0024 | False | 0.9064 | 9.36 | 0.125 | 0.9904 |
| task38 | 13 | 0.8681 | -0.0072 | -0.0240 | 0.0048 | False | 0.8723 | 12.77 | 0.5078 | 0.7818 |
| task38 | 17 | 0.8681 | -0.0072 | -0.0216 | 0.0048 | False | 0.8775 | 12.25 | 0.5078 | 0.7842 |
| task38 | 19 | 0.8705 | -0.0048 | -0.0216 | 0.0096 | False | 0.8842 | 11.58 | 0.7744 | 0.7650 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
