# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.98_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0093 | 20.30 | 0.7970 | 3 |
| token_budget_r0.85_m5 | False | -0.0093 | 20.29 | 0.7971 | 3 |
| token_budget_r0.85_m6 | False | -0.0093 | 20.03 | 0.7997 | 3 |
| token_budget_r0.85_m7 | False | -0.0093 | 19.19 | 0.8081 | 3 |
| token_budget_r0.88_m4 | False | -0.0074 | 17.89 | 0.8211 | 3 |
| token_budget_r0.88_m5 | False | -0.0074 | 17.89 | 0.8211 | 3 |
| token_budget_r0.88_m6 | False | -0.0074 | 17.69 | 0.8231 | 3 |
| token_budget_r0.88_m7 | False | -0.0074 | 17.23 | 0.8277 | 3 |
| token_budget_r0.90_m4 | False | -0.0074 | 15.55 | 0.8445 | 3 |
| token_budget_r0.90_m5 | False | -0.0074 | 15.55 | 0.8445 | 3 |
| token_budget_r0.90_m6 | False | -0.0074 | 15.48 | 0.8452 | 3 |
| token_budget_r0.90_m7 | False | -0.0074 | 15.27 | 0.8473 | 3 |
| token_budget_r0.85_m8 | False | -0.0037 | 14.86 | 0.8514 | 3 |
| token_budget_r0.88_m8 | False | -0.0037 | 13.86 | 0.8614 | 3 |
| token_budget_r0.90_m8 | False | -0.0037 | 13.39 | 0.8661 | 3 |
| token_budget_r0.92_m4 | False | -0.0037 | 13.32 | 0.8668 | 3 |
| token_budget_r0.92_m5 | False | -0.0037 | 13.32 | 0.8668 | 3 |
| token_budget_r0.92_m6 | False | -0.0037 | 13.25 | 0.8675 | 3 |
| token_budget_r0.92_m7 | False | -0.0037 | 13.12 | 0.8688 | 3 |
| token_budget_r0.92_m8 | False | -0.0037 | 11.99 | 0.8801 | 3 |
| token_budget_r0.95_m4 | False | -0.0037 | 10.72 | 0.8928 | 3 |
| token_budget_r0.95_m5 | False | -0.0037 | 10.72 | 0.8928 | 3 |
| token_budget_r0.95_m6 | False | -0.0037 | 10.68 | 0.8932 | 3 |
| token_budget_r0.95_m7 | False | -0.0037 | 10.68 | 0.8932 | 3 |
| token_budget_r0.95_m8 | False | -0.0037 | 10.52 | 0.8948 | 3 |
| token_budget_r0.98_m4 | False | -0.0019 | 8.23 | 0.9177 | 3 |
| token_budget_r0.98_m5 | False | -0.0019 | 8.23 | 0.9177 | 3 |
| token_budget_r0.98_m6 | False | -0.0019 | 8.23 | 0.9177 | 3 |
| token_budget_r0.98_m7 | False | -0.0019 | 8.23 | 0.9177 | 3 |
| token_budget_r0.98_m8 | False | -0.0019 | 8.23 | 0.9177 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.8956 | 10.44 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8681 | 0.0096 | -0.0072 | 0.0288 | True | 0.9575 | 4.25 | 0.4545 | 0.6571 |
| task38 | 17 | 0.8633 | 0.0048 | -0.0144 | 0.0240 | False | 0.9571 | 4.29 | 0.8036 | 0.6523 |
| task38 | 19 | 0.8681 | 0.0096 | -0.0096 | 0.0288 | True | 0.9565 | 4.35 | 0.4545 | 0.6547 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
