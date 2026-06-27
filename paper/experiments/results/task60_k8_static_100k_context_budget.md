# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.98_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0149 | 19.67 | 0.8033 | 3 |
| token_budget_r0.85_m5 | False | -0.0149 | 19.67 | 0.8033 | 3 |
| token_budget_r0.85_m6 | False | -0.0149 | 19.59 | 0.8041 | 3 |
| token_budget_r0.85_m7 | False | -0.0149 | 18.50 | 0.8150 | 3 |
| token_budget_r0.88_m4 | False | -0.0074 | 17.21 | 0.8279 | 3 |
| token_budget_r0.88_m5 | False | -0.0074 | 17.21 | 0.8279 | 3 |
| token_budget_r0.88_m6 | False | -0.0074 | 17.19 | 0.8281 | 3 |
| token_budget_r0.88_m7 | False | -0.0074 | 16.52 | 0.8348 | 3 |
| token_budget_r0.90_m4 | False | -0.0074 | 14.95 | 0.8505 | 3 |
| token_budget_r0.90_m5 | False | -0.0074 | 14.95 | 0.8505 | 3 |
| token_budget_r0.90_m6 | False | -0.0074 | 14.93 | 0.8507 | 3 |
| token_budget_r0.90_m7 | False | -0.0074 | 14.51 | 0.8549 | 3 |
| token_budget_r0.85_m8 | False | -0.0037 | 14.15 | 0.8585 | 3 |
| token_budget_r0.88_m8 | False | -0.0019 | 13.17 | 0.8683 | 3 |
| token_budget_r0.92_m4 | False | -0.0019 | 12.53 | 0.8747 | 3 |
| token_budget_r0.92_m5 | False | -0.0019 | 12.53 | 0.8747 | 3 |
| token_budget_r0.92_m6 | False | -0.0019 | 12.53 | 0.8747 | 3 |
| token_budget_r0.90_m8 | False | -0.0019 | 12.50 | 0.8750 | 3 |
| token_budget_r0.92_m7 | False | -0.0019 | 12.26 | 0.8774 | 3 |
| token_budget_r0.92_m8 | False | -0.0019 | 11.04 | 0.8896 | 3 |
| token_budget_r0.95_m4 | False | -0.0000 | 10.03 | 0.8997 | 3 |
| token_budget_r0.95_m5 | False | -0.0000 | 10.03 | 0.8997 | 3 |
| token_budget_r0.95_m6 | False | -0.0000 | 10.03 | 0.8997 | 3 |
| token_budget_r0.95_m7 | False | -0.0000 | 9.87 | 0.9013 | 3 |
| token_budget_r0.95_m8 | False | -0.0000 | 9.56 | 0.9044 | 3 |
| token_budget_r0.98_m4 | True | 0.0019 | 6.76 | 0.9324 | 3 |
| token_budget_r0.98_m5 | True | 0.0019 | 6.76 | 0.9324 | 3 |
| token_budget_r0.98_m6 | True | 0.0019 | 6.76 | 0.9324 | 3 |
| token_budget_r0.98_m7 | True | 0.0019 | 6.69 | 0.9331 | 3 |
| token_budget_r0.98_m8 | True | 0.0019 | 6.69 | 0.9331 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.8956 | 10.44 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8657 | 0.0072 | -0.0096 | 0.0240 | True | 0.9579 | 4.21 | 0.6072 | 0.6307 |
| task38 | 17 | 0.8681 | 0.0096 | -0.0072 | 0.0264 | True | 0.9624 | 3.76 | 0.424 | 0.6379 |
| task38 | 19 | 0.8753 | 0.0168 | -0.0024 | 0.0360 | True | 0.9635 | 3.65 | 0.1185 | 0.6379 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
