# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m8`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0093 | 18.19 | 0.8181 | 3 |
| token_budget_r0.85_m5 | False | -0.0093 | 18.19 | 0.8181 | 3 |
| token_budget_r0.85_m6 | False | -0.0093 | 18.12 | 0.8188 | 3 |
| token_budget_r0.85_m7 | False | -0.0093 | 17.11 | 0.8289 | 3 |
| token_budget_r0.88_m4 | False | -0.0112 | 15.69 | 0.8431 | 3 |
| token_budget_r0.88_m5 | False | -0.0112 | 15.69 | 0.8431 | 3 |
| token_budget_r0.88_m6 | False | -0.0112 | 15.66 | 0.8434 | 3 |
| token_budget_r0.88_m7 | False | -0.0112 | 15.13 | 0.8487 | 3 |
| token_budget_r0.90_m4 | False | -0.0074 | 13.91 | 0.8609 | 3 |
| token_budget_r0.90_m5 | False | -0.0074 | 13.91 | 0.8609 | 3 |
| token_budget_r0.90_m6 | False | -0.0074 | 13.88 | 0.8612 | 3 |
| token_budget_r0.90_m7 | False | -0.0074 | 13.50 | 0.8650 | 3 |
| token_budget_r0.85_m8 | False | -0.0000 | 13.21 | 0.8679 | 3 |
| token_budget_r0.88_m8 | False | -0.0019 | 12.31 | 0.8769 | 3 |
| token_budget_r0.92_m4 | False | -0.0019 | 11.66 | 0.8834 | 3 |
| token_budget_r0.92_m5 | False | -0.0019 | 11.66 | 0.8834 | 3 |
| token_budget_r0.92_m6 | False | -0.0019 | 11.64 | 0.8836 | 3 |
| token_budget_r0.90_m8 | False | -0.0019 | 11.56 | 0.8844 | 3 |
| token_budget_r0.92_m7 | False | -0.0019 | 11.37 | 0.8863 | 3 |
| token_budget_r0.92_m8 | False | -0.0019 | 10.21 | 0.8979 | 3 |
| token_budget_r0.95_m4 | False | -0.0019 | 9.03 | 0.9097 | 3 |
| token_budget_r0.95_m5 | False | -0.0019 | 9.03 | 0.9097 | 3 |
| token_budget_r0.95_m6 | False | -0.0019 | 9.00 | 0.9100 | 3 |
| token_budget_r0.95_m7 | False | -0.0019 | 8.93 | 0.9107 | 3 |
| token_budget_r0.95_m8 | False | -0.0019 | 8.29 | 0.9171 | 3 |
| token_budget_r0.98_m4 | False | -0.0019 | 5.93 | 0.9407 | 3 |
| token_budget_r0.98_m5 | False | -0.0019 | 5.93 | 0.9407 | 3 |
| token_budget_r0.98_m6 | False | -0.0019 | 5.93 | 0.9407 | 3 |
| token_budget_r0.98_m7 | False | -0.0019 | 5.86 | 0.9414 | 3 |
| token_budget_r0.98_m8 | False | -0.0019 | 5.67 | 0.9433 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8402 | 15.98 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8585 | 0.0000 | -0.0192 | 0.0192 | False | 0.8886 | 11.14 | 1 | 0.7386 |
| task38 | 17 | 0.8561 | -0.0024 | -0.0192 | 0.0144 | False | 0.8780 | 12.20 | 1 | 0.7554 |
| task38 | 19 | 0.8729 | 0.0144 | -0.0048 | 0.0336 | True | 0.8976 | 10.24 | 0.2101 | 0.7362 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
