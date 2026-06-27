# Task38 Calibrated Context Budget

- Scale: `task58_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.98_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0354 | 19.77 | 0.8023 | 3 |
| token_budget_r0.85_m5 | False | -0.0354 | 19.77 | 0.8023 | 3 |
| token_budget_r0.85_m6 | False | -0.0354 | 19.53 | 0.8047 | 3 |
| token_budget_r0.85_m7 | False | -0.0354 | 18.53 | 0.8147 | 3 |
| token_budget_r0.88_m4 | False | -0.0335 | 17.23 | 0.8277 | 3 |
| token_budget_r0.88_m5 | False | -0.0335 | 17.23 | 0.8277 | 3 |
| token_budget_r0.88_m6 | False | -0.0335 | 17.19 | 0.8281 | 3 |
| token_budget_r0.88_m7 | False | -0.0335 | 16.53 | 0.8347 | 3 |
| token_budget_r0.90_m4 | False | -0.0279 | 14.02 | 0.8598 | 3 |
| token_budget_r0.90_m5 | False | -0.0279 | 14.02 | 0.8598 | 3 |
| token_budget_r0.90_m6 | False | -0.0279 | 14.00 | 0.8600 | 3 |
| token_budget_r0.85_m8 | False | -0.0223 | 13.95 | 0.8605 | 3 |
| token_budget_r0.90_m7 | False | -0.0279 | 13.68 | 0.8632 | 3 |
| token_budget_r0.88_m8 | False | -0.0223 | 12.89 | 0.8711 | 3 |
| token_budget_r0.90_m8 | False | -0.0223 | 12.20 | 0.8780 | 3 |
| token_budget_r0.92_m4 | False | -0.0223 | 11.95 | 0.8805 | 3 |
| token_budget_r0.92_m5 | False | -0.0223 | 11.95 | 0.8805 | 3 |
| token_budget_r0.92_m6 | False | -0.0223 | 11.95 | 0.8805 | 3 |
| token_budget_r0.92_m7 | False | -0.0223 | 11.79 | 0.8821 | 3 |
| token_budget_r0.92_m8 | False | -0.0223 | 11.02 | 0.8898 | 3 |
| token_budget_r0.95_m4 | False | -0.0205 | 9.31 | 0.9069 | 3 |
| token_budget_r0.95_m5 | False | -0.0205 | 9.31 | 0.9069 | 3 |
| token_budget_r0.95_m6 | False | -0.0205 | 9.31 | 0.9069 | 3 |
| token_budget_r0.95_m7 | False | -0.0205 | 9.29 | 0.9071 | 3 |
| token_budget_r0.95_m8 | False | -0.0205 | 8.90 | 0.9110 | 3 |
| token_budget_r0.98_m4 | False | -0.0168 | 6.59 | 0.9341 | 3 |
| token_budget_r0.98_m5 | False | -0.0168 | 6.59 | 0.9341 | 3 |
| token_budget_r0.98_m6 | False | -0.0168 | 6.59 | 0.9341 | 3 |
| token_budget_r0.98_m7 | False | -0.0168 | 6.59 | 0.9341 | 3 |
| token_budget_r0.98_m8 | False | -0.0168 | 6.59 | 0.9341 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8633 | -0.0072 | -0.0168 | 0.0000 | False | 0.8928 | 10.72 | 0.25 | 0.9928 |
| dense_fixed |  | 0.8561 | -0.0144 | -0.0264 | -0.0048 | False | 0.8126 | 18.74 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8633 | -0.0072 | -0.0168 | 0.0000 | False | 0.9019 | 9.81 | 0.25 | 0.9928 |
| task38 | 13 | 0.8873 | 0.0168 | 0.0000 | 0.0336 | True | 0.9440 | 5.60 | 0.09229 | 0.6643 |
| task38 | 17 | 0.8825 | 0.0120 | -0.0048 | 0.0312 | True | 0.9569 | 4.31 | 0.3018 | 0.6619 |
| task38 | 19 | 0.8849 | 0.0144 | -0.0024 | 0.0312 | True | 0.9482 | 5.18 | 0.1796 | 0.6691 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
