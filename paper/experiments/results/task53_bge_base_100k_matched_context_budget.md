# Task38 Calibrated Context Budget

- Scale: `100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.88_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0242 | 20.91 | 0.7909 | 3 |
| token_budget_r0.85_m5 | False | -0.0242 | 20.90 | 0.7910 | 3 |
| token_budget_r0.85_m6 | False | -0.0242 | 20.83 | 0.7917 | 3 |
| token_budget_r0.85_m7 | False | -0.0242 | 19.98 | 0.8002 | 3 |
| token_budget_r0.88_m4 | False | -0.0205 | 17.96 | 0.8204 | 3 |
| token_budget_r0.88_m5 | False | -0.0205 | 17.96 | 0.8204 | 3 |
| token_budget_r0.88_m6 | False | -0.0205 | 17.92 | 0.8208 | 3 |
| token_budget_r0.85_m8 | False | -0.0223 | 17.62 | 0.8238 | 3 |
| token_budget_r0.88_m7 | False | -0.0205 | 17.60 | 0.8240 | 3 |
| token_budget_r0.90_m4 | False | -0.0205 | 16.76 | 0.8324 | 3 |
| token_budget_r0.90_m5 | False | -0.0205 | 16.76 | 0.8324 | 3 |
| token_budget_r0.90_m6 | False | -0.0205 | 16.72 | 0.8328 | 3 |
| token_budget_r0.90_m7 | False | -0.0205 | 16.48 | 0.8352 | 3 |
| token_budget_r0.88_m8 | False | -0.0205 | 16.19 | 0.8381 | 3 |
| token_budget_r0.90_m8 | False | -0.0205 | 15.50 | 0.8450 | 3 |
| token_budget_r0.92_m4 | False | -0.0205 | 15.18 | 0.8482 | 3 |
| token_budget_r0.92_m5 | False | -0.0205 | 15.18 | 0.8482 | 3 |
| token_budget_r0.92_m6 | False | -0.0205 | 15.14 | 0.8486 | 3 |
| token_budget_r0.92_m7 | False | -0.0205 | 15.12 | 0.8488 | 3 |
| token_budget_r0.92_m8 | False | -0.0205 | 14.59 | 0.8541 | 3 |
| token_budget_r0.95_m4 | False | -0.0205 | 12.95 | 0.8705 | 3 |
| token_budget_r0.95_m5 | False | -0.0205 | 12.95 | 0.8705 | 3 |
| token_budget_r0.95_m6 | False | -0.0205 | 12.95 | 0.8705 | 3 |
| token_budget_r0.95_m7 | False | -0.0205 | 12.95 | 0.8705 | 3 |
| token_budget_r0.95_m8 | False | -0.0205 | 12.88 | 0.8712 | 3 |
| token_budget_r0.98_m4 | False | -0.0205 | 10.68 | 0.8932 | 3 |
| token_budget_r0.98_m5 | False | -0.0205 | 10.68 | 0.8932 | 3 |
| token_budget_r0.98_m6 | False | -0.0205 | 10.68 | 0.8932 | 3 |
| token_budget_r0.98_m7 | False | -0.0205 | 10.68 | 0.8932 | 3 |
| token_budget_r0.98_m8 | False | -0.0205 | 10.68 | 0.8932 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8897 | -0.0096 | -0.0192 | -0.0024 | False | 0.8059 | 19.41 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8897 | -0.0096 | -0.0192 | -0.0024 | False | 0.8154 | 18.46 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8945 | -0.0048 | -0.0120 | 0.0000 | False | 0.8996 | 10.04 | 0.5 | 0.9952 |
| task38 | 13 | 0.8801 | -0.0192 | -0.0408 | 0.0024 | False | 0.8328 | 16.72 | 0.09625 | 0.8321 |
| task38 | 17 | 0.8705 | -0.0288 | -0.0504 | -0.0072 | False | 0.8333 | 16.67 | 0.0169 | 0.7770 |
| task38 | 19 | 0.8729 | -0.0264 | -0.0456 | -0.0072 | False | 0.8476 | 15.24 | 0.01273 | 0.7626 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
