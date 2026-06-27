# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0112 | 19.52 | 0.8048 | 3 |
| token_budget_r0.85_m5 | False | -0.0112 | 19.49 | 0.8051 | 3 |
| token_budget_r0.85_m6 | False | -0.0112 | 19.33 | 0.8067 | 3 |
| token_budget_r0.85_m7 | False | -0.0112 | 17.96 | 0.8204 | 3 |
| token_budget_r0.88_m4 | False | -0.0130 | 16.77 | 0.8323 | 3 |
| token_budget_r0.88_m5 | False | -0.0130 | 16.74 | 0.8326 | 3 |
| token_budget_r0.88_m6 | False | -0.0130 | 16.66 | 0.8334 | 3 |
| token_budget_r0.88_m7 | False | -0.0130 | 16.13 | 0.8387 | 3 |
| token_budget_r0.90_m4 | False | -0.0112 | 15.17 | 0.8483 | 3 |
| token_budget_r0.90_m5 | False | -0.0112 | 15.14 | 0.8486 | 3 |
| token_budget_r0.90_m6 | False | -0.0112 | 15.07 | 0.8493 | 3 |
| token_budget_r0.90_m7 | False | -0.0112 | 14.87 | 0.8513 | 3 |
| token_budget_r0.85_m8 | False | -0.0112 | 14.08 | 0.8592 | 3 |
| token_budget_r0.92_m4 | False | -0.0112 | 13.70 | 0.8630 | 3 |
| token_budget_r0.92_m5 | False | -0.0112 | 13.67 | 0.8633 | 3 |
| token_budget_r0.92_m6 | False | -0.0112 | 13.59 | 0.8641 | 3 |
| token_budget_r0.92_m7 | False | -0.0112 | 13.54 | 0.8646 | 3 |
| token_budget_r0.88_m8 | False | -0.0112 | 13.23 | 0.8677 | 3 |
| token_budget_r0.90_m8 | False | -0.0112 | 12.64 | 0.8736 | 3 |
| token_budget_r0.92_m8 | False | -0.0112 | 11.91 | 0.8809 | 3 |
| token_budget_r0.95_m4 | False | -0.0112 | 10.63 | 0.8937 | 3 |
| token_budget_r0.95_m5 | False | -0.0112 | 10.63 | 0.8937 | 3 |
| token_budget_r0.95_m6 | False | -0.0112 | 10.63 | 0.8937 | 3 |
| token_budget_r0.95_m7 | False | -0.0112 | 10.62 | 0.8938 | 3 |
| token_budget_r0.95_m8 | False | -0.0112 | 10.21 | 0.8979 | 3 |
| token_budget_r0.98_m4 | False | -0.0112 | 8.25 | 0.9175 | 3 |
| token_budget_r0.98_m5 | False | -0.0112 | 8.25 | 0.9175 | 3 |
| token_budget_r0.98_m6 | False | -0.0112 | 8.25 | 0.9175 | 3 |
| token_budget_r0.98_m7 | False | -0.0112 | 8.25 | 0.9175 | 3 |
| token_budget_r0.98_m8 | False | -0.0112 | 8.24 | 0.9176 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8369 | -0.0216 | -0.0360 | -0.0096 | False | 0.7733 | 22.67 | 0.003906 | 0.9784 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8393 | -0.0192 | -0.0432 | 0.0048 | False | 0.8198 | 18.02 | 0.1686 | 0.7962 |
| task38 | 17 | 0.8465 | -0.0120 | -0.0360 | 0.0096 | False | 0.8313 | 16.87 | 0.4244 | 0.7938 |
| task38 | 19 | 0.8345 | -0.0240 | -0.0528 | 0.0024 | False | 0.8418 | 15.82 | 0.1102 | 0.7770 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
