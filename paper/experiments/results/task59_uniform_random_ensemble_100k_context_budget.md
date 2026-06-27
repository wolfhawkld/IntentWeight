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
| token_budget_r0.85_m4 | True | 0.0261 | 17.47 | 0.8253 | 3 |
| token_budget_r0.85_m5 | True | 0.0261 | 17.46 | 0.8254 | 3 |
| token_budget_r0.85_m6 | True | 0.0261 | 17.09 | 0.8291 | 3 |
| token_budget_r0.85_m7 | True | 0.0261 | 15.65 | 0.8435 | 3 |
| token_budget_r0.88_m4 | True | 0.0279 | 14.70 | 0.8530 | 3 |
| token_budget_r0.88_m5 | True | 0.0279 | 14.70 | 0.8530 | 3 |
| token_budget_r0.88_m6 | True | 0.0279 | 14.49 | 0.8551 | 3 |
| token_budget_r0.88_m7 | True | 0.0279 | 13.63 | 0.8637 | 3 |
| token_budget_r0.90_m4 | True | 0.0261 | 12.88 | 0.8712 | 3 |
| token_budget_r0.90_m5 | True | 0.0261 | 12.88 | 0.8712 | 3 |
| token_budget_r0.90_m6 | True | 0.0261 | 12.72 | 0.8728 | 3 |
| token_budget_r0.85_m8 | True | 0.0335 | 12.23 | 0.8777 | 3 |
| token_budget_r0.90_m7 | True | 0.0261 | 12.10 | 0.8790 | 3 |
| token_budget_r0.88_m8 | True | 0.0298 | 11.45 | 0.8855 | 3 |
| token_budget_r0.90_m8 | True | 0.0298 | 10.60 | 0.8940 | 3 |
| token_budget_r0.92_m4 | True | 0.0298 | 10.56 | 0.8944 | 3 |
| token_budget_r0.92_m5 | True | 0.0298 | 10.56 | 0.8944 | 3 |
| token_budget_r0.92_m6 | True | 0.0298 | 10.50 | 0.8950 | 3 |
| token_budget_r0.92_m7 | True | 0.0298 | 10.23 | 0.8977 | 3 |
| token_budget_r0.92_m8 | True | 0.0298 | 9.25 | 0.9075 | 3 |
| token_budget_r0.95_m4 | True | 0.0317 | 7.71 | 0.9229 | 3 |
| token_budget_r0.95_m5 | True | 0.0317 | 7.71 | 0.9229 | 3 |
| token_budget_r0.95_m6 | True | 0.0317 | 7.71 | 0.9229 | 3 |
| token_budget_r0.95_m7 | True | 0.0317 | 7.62 | 0.9238 | 3 |
| token_budget_r0.95_m8 | True | 0.0317 | 7.36 | 0.9264 | 3 |
| token_budget_r0.98_m4 | True | 0.0372 | 5.44 | 0.9456 | 3 |
| token_budget_r0.98_m5 | True | 0.0372 | 5.44 | 0.9456 | 3 |
| token_budget_r0.98_m6 | True | 0.0372 | 5.44 | 0.9456 | 3 |
| token_budget_r0.98_m7 | True | 0.0372 | 5.37 | 0.9463 | 3 |
| token_budget_r0.98_m8 | True | 0.0372 | 5.37 | 0.9463 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8705 | -0.0144 | -0.0264 | -0.0048 | False | 0.7667 | 23.33 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8657 | -0.0192 | -0.0336 | -0.0072 | False | 0.8108 | 18.92 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8753 | -0.0096 | -0.0192 | -0.0024 | False | 0.9022 | 9.78 | 0.125 | 0.9904 |
| task38 | 13 | 0.8753 | -0.0096 | -0.0288 | 0.0096 | False | 0.8191 | 18.09 | 0.4545 | 0.8106 |
| task38 | 17 | 0.8705 | -0.0144 | -0.0336 | 0.0048 | False | 0.8193 | 18.07 | 0.2379 | 0.7986 |
| task38 | 19 | 0.8657 | -0.0192 | -0.0384 | 0.0000 | False | 0.8100 | 19.00 | 0.07681 | 0.7986 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
