# Task38 Calibrated Context Budget

- Scale: `400k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.98_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0223 | 18.95 | 0.8105 | 3 |
| token_budget_r0.85_m5 | False | -0.0205 | 18.78 | 0.8122 | 3 |
| token_budget_r0.85_m6 | False | -0.0205 | 18.59 | 0.8141 | 3 |
| token_budget_r0.85_m7 | False | -0.0205 | 17.65 | 0.8235 | 3 |
| token_budget_r0.88_m4 | False | -0.0149 | 16.20 | 0.8380 | 3 |
| token_budget_r0.88_m5 | False | -0.0149 | 16.20 | 0.8380 | 3 |
| token_budget_r0.88_m6 | False | -0.0149 | 16.09 | 0.8391 | 3 |
| token_budget_r0.88_m7 | False | -0.0149 | 15.49 | 0.8451 | 3 |
| token_budget_r0.85_m8 | False | -0.0168 | 14.83 | 0.8517 | 3 |
| token_budget_r0.90_m4 | False | -0.0149 | 14.32 | 0.8568 | 3 |
| token_budget_r0.90_m5 | False | -0.0149 | 14.32 | 0.8568 | 3 |
| token_budget_r0.90_m6 | False | -0.0149 | 14.32 | 0.8568 | 3 |
| token_budget_r0.90_m7 | False | -0.0149 | 14.19 | 0.8581 | 3 |
| token_budget_r0.88_m8 | False | -0.0112 | 13.54 | 0.8646 | 3 |
| token_budget_r0.92_m4 | False | -0.0130 | 12.80 | 0.8720 | 3 |
| token_budget_r0.92_m5 | False | -0.0130 | 12.80 | 0.8720 | 3 |
| token_budget_r0.92_m6 | False | -0.0130 | 12.80 | 0.8720 | 3 |
| token_budget_r0.92_m7 | False | -0.0130 | 12.80 | 0.8720 | 3 |
| token_budget_r0.90_m8 | False | -0.0130 | 12.78 | 0.8722 | 3 |
| token_budget_r0.92_m8 | False | -0.0112 | 11.84 | 0.8816 | 3 |
| token_budget_r0.95_m4 | False | -0.0093 | 10.51 | 0.8949 | 3 |
| token_budget_r0.95_m5 | False | -0.0093 | 10.51 | 0.8949 | 3 |
| token_budget_r0.95_m6 | False | -0.0093 | 10.51 | 0.8949 | 3 |
| token_budget_r0.95_m7 | False | -0.0093 | 10.51 | 0.8949 | 3 |
| token_budget_r0.95_m8 | False | -0.0093 | 10.26 | 0.8974 | 3 |
| token_budget_r0.98_m4 | False | -0.0074 | 8.43 | 0.9157 | 3 |
| token_budget_r0.98_m5 | False | -0.0074 | 8.43 | 0.9157 | 3 |
| token_budget_r0.98_m6 | False | -0.0074 | 8.43 | 0.9157 | 3 |
| token_budget_r0.98_m7 | False | -0.0074 | 8.43 | 0.9157 | 3 |
| token_budget_r0.98_m8 | False | -0.0074 | 8.43 | 0.9157 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.7554 | -0.0024 | -0.0072 | 0.0000 | True | 0.8856 | 11.44 | 1 | 0.9976 |
| dense_fixed |  | 0.7386 | -0.0192 | -0.0336 | -0.0072 | False | 0.7886 | 21.14 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.7554 | -0.0024 | -0.0072 | 0.0000 | True | 0.8933 | 10.67 | 1 | 0.9976 |
| task38 | 13 | 0.7794 | 0.0216 | -0.0024 | 0.0480 | True | 0.9337 | 6.63 | 0.136 | 0.6451 |
| task38 | 17 | 0.7890 | 0.0312 | 0.0024 | 0.0600 | True | 0.9165 | 8.35 | 0.04703 | 0.6547 |
| task38 | 19 | 0.7746 | 0.0168 | -0.0096 | 0.0432 | True | 0.9528 | 4.72 | 0.281 | 0.6283 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
