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
| token_budget_r0.85_m4 | True | 0.0112 | 17.80 | 0.8220 | 3 |
| token_budget_r0.85_m5 | True | 0.0112 | 17.79 | 0.8221 | 3 |
| token_budget_r0.85_m6 | True | 0.0112 | 17.48 | 0.8252 | 3 |
| token_budget_r0.85_m7 | True | 0.0112 | 16.09 | 0.8391 | 3 |
| token_budget_r0.88_m4 | True | 0.0186 | 14.49 | 0.8551 | 3 |
| token_budget_r0.88_m5 | True | 0.0186 | 14.49 | 0.8551 | 3 |
| token_budget_r0.88_m6 | True | 0.0186 | 14.43 | 0.8557 | 3 |
| token_budget_r0.88_m7 | True | 0.0186 | 13.91 | 0.8609 | 3 |
| token_budget_r0.90_m4 | True | 0.0186 | 12.81 | 0.8719 | 3 |
| token_budget_r0.90_m5 | True | 0.0186 | 12.80 | 0.8720 | 3 |
| token_budget_r0.90_m6 | True | 0.0186 | 12.77 | 0.8723 | 3 |
| token_budget_r0.90_m7 | True | 0.0186 | 12.38 | 0.8762 | 3 |
| token_budget_r0.85_m8 | True | 0.0242 | 12.16 | 0.8784 | 3 |
| token_budget_r0.88_m8 | True | 0.0261 | 11.21 | 0.8879 | 3 |
| token_budget_r0.92_m4 | True | 0.0261 | 10.46 | 0.8954 | 3 |
| token_budget_r0.92_m5 | True | 0.0261 | 10.46 | 0.8954 | 3 |
| token_budget_r0.92_m6 | True | 0.0261 | 10.45 | 0.8955 | 3 |
| token_budget_r0.90_m8 | True | 0.0261 | 10.29 | 0.8971 | 3 |
| token_budget_r0.92_m7 | True | 0.0261 | 10.19 | 0.8981 | 3 |
| token_budget_r0.92_m8 | True | 0.0261 | 9.07 | 0.9093 | 3 |
| token_budget_r0.95_m4 | True | 0.0261 | 7.31 | 0.9269 | 3 |
| token_budget_r0.95_m5 | True | 0.0261 | 7.31 | 0.9269 | 3 |
| token_budget_r0.95_m6 | True | 0.0261 | 7.31 | 0.9269 | 3 |
| token_budget_r0.95_m7 | True | 0.0261 | 7.31 | 0.9269 | 3 |
| token_budget_r0.95_m8 | True | 0.0261 | 7.15 | 0.9285 | 3 |
| token_budget_r0.98_m4 | True | 0.0317 | 5.34 | 0.9466 | 3 |
| token_budget_r0.98_m5 | True | 0.0317 | 5.34 | 0.9466 | 3 |
| token_budget_r0.98_m6 | True | 0.0317 | 5.34 | 0.9466 | 3 |
| token_budget_r0.98_m7 | True | 0.0317 | 5.34 | 0.9466 | 3 |
| token_budget_r0.98_m8 | True | 0.0317 | 5.31 | 0.9469 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8705 | -0.0144 | -0.0264 | -0.0048 | False | 0.7667 | 23.33 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8657 | -0.0192 | -0.0336 | -0.0072 | False | 0.8108 | 18.92 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8753 | -0.0096 | -0.0192 | -0.0024 | False | 0.9022 | 9.78 | 0.125 | 0.9904 |
| task38 | 13 | 0.8657 | -0.0192 | -0.0408 | 0.0024 | False | 0.8264 | 17.36 | 0.1153 | 0.8106 |
| task38 | 17 | 0.8609 | -0.0240 | -0.0456 | -0.0048 | False | 0.8239 | 17.61 | 0.04139 | 0.7914 |
| task38 | 19 | 0.8777 | -0.0072 | -0.0264 | 0.0120 | False | 0.8140 | 18.60 | 0.6291 | 0.7938 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
