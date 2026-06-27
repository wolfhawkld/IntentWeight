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
| token_budget_r0.85_m4 | True | 0.0093 | 18.77 | 0.8123 | 3 |
| token_budget_r0.85_m5 | True | 0.0093 | 18.63 | 0.8137 | 3 |
| token_budget_r0.85_m6 | True | 0.0093 | 18.42 | 0.8158 | 3 |
| token_budget_r0.85_m7 | True | 0.0093 | 17.46 | 0.8254 | 3 |
| token_budget_r0.88_m4 | True | 0.0130 | 15.97 | 0.8403 | 3 |
| token_budget_r0.88_m5 | True | 0.0130 | 15.97 | 0.8403 | 3 |
| token_budget_r0.88_m6 | True | 0.0130 | 15.83 | 0.8417 | 3 |
| token_budget_r0.88_m7 | True | 0.0130 | 15.44 | 0.8456 | 3 |
| token_budget_r0.90_m4 | True | 0.0130 | 14.34 | 0.8566 | 3 |
| token_budget_r0.90_m5 | True | 0.0130 | 14.33 | 0.8567 | 3 |
| token_budget_r0.90_m6 | True | 0.0130 | 14.22 | 0.8578 | 3 |
| token_budget_r0.90_m7 | True | 0.0130 | 13.95 | 0.8605 | 3 |
| token_budget_r0.85_m8 | True | 0.0223 | 12.73 | 0.8727 | 3 |
| token_budget_r0.88_m8 | True | 0.0223 | 11.76 | 0.8824 | 3 |
| token_budget_r0.92_m4 | True | 0.0242 | 11.74 | 0.8826 | 3 |
| token_budget_r0.92_m5 | True | 0.0242 | 11.74 | 0.8826 | 3 |
| token_budget_r0.92_m6 | True | 0.0242 | 11.65 | 0.8835 | 3 |
| token_budget_r0.92_m7 | True | 0.0242 | 11.52 | 0.8848 | 3 |
| token_budget_r0.90_m8 | True | 0.0223 | 11.06 | 0.8894 | 3 |
| token_budget_r0.92_m8 | True | 0.0223 | 10.08 | 0.8992 | 3 |
| token_budget_r0.95_m4 | True | 0.0223 | 8.74 | 0.9126 | 3 |
| token_budget_r0.95_m5 | True | 0.0223 | 8.74 | 0.9126 | 3 |
| token_budget_r0.95_m6 | True | 0.0223 | 8.70 | 0.9130 | 3 |
| token_budget_r0.95_m7 | True | 0.0223 | 8.68 | 0.9132 | 3 |
| token_budget_r0.95_m8 | True | 0.0223 | 8.34 | 0.9166 | 3 |
| token_budget_r0.98_m4 | True | 0.0242 | 5.97 | 0.9403 | 3 |
| token_budget_r0.98_m5 | True | 0.0242 | 5.97 | 0.9403 | 3 |
| token_budget_r0.98_m6 | True | 0.0242 | 5.97 | 0.9403 | 3 |
| token_budget_r0.98_m7 | True | 0.0242 | 5.97 | 0.9403 | 3 |
| token_budget_r0.98_m8 | True | 0.0242 | 5.94 | 0.9406 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8705 | -0.0144 | -0.0264 | -0.0048 | False | 0.7667 | 23.33 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8657 | -0.0192 | -0.0336 | -0.0072 | False | 0.8108 | 18.92 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8753 | -0.0096 | -0.0192 | -0.0024 | False | 0.9022 | 9.78 | 0.125 | 0.9904 |
| task38 | 13 | 0.8633 | -0.0216 | -0.0432 | -0.0024 | False | 0.8178 | 18.22 | 0.06357 | 0.8417 |
| task38 | 17 | 0.8705 | -0.0144 | -0.0360 | 0.0072 | False | 0.8190 | 18.10 | 0.2863 | 0.8345 |
| task38 | 19 | 0.8705 | -0.0144 | -0.0336 | 0.0024 | False | 0.8189 | 18.11 | 0.2101 | 0.8369 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
