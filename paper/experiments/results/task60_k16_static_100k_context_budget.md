# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m8`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0056 | 19.37 | 0.8063 | 3 |
| token_budget_r0.85_m5 | False | -0.0056 | 19.37 | 0.8063 | 3 |
| token_budget_r0.85_m6 | False | -0.0056 | 19.28 | 0.8072 | 3 |
| token_budget_r0.85_m7 | False | -0.0056 | 18.20 | 0.8180 | 3 |
| token_budget_r0.88_m4 | False | -0.0019 | 16.79 | 0.8321 | 3 |
| token_budget_r0.88_m5 | False | -0.0019 | 16.79 | 0.8321 | 3 |
| token_budget_r0.88_m6 | False | -0.0019 | 16.74 | 0.8326 | 3 |
| token_budget_r0.88_m7 | False | -0.0019 | 16.15 | 0.8385 | 3 |
| token_budget_r0.90_m4 | False | -0.0019 | 14.79 | 0.8521 | 3 |
| token_budget_r0.90_m5 | False | -0.0019 | 14.79 | 0.8521 | 3 |
| token_budget_r0.90_m6 | False | -0.0019 | 14.78 | 0.8522 | 3 |
| token_budget_r0.90_m7 | False | -0.0019 | 14.40 | 0.8560 | 3 |
| token_budget_r0.85_m8 | True | 0.0019 | 13.28 | 0.8672 | 3 |
| token_budget_r0.92_m4 | True | 0.0019 | 12.45 | 0.8755 | 3 |
| token_budget_r0.92_m5 | True | 0.0019 | 12.45 | 0.8755 | 3 |
| token_budget_r0.92_m6 | True | 0.0019 | 12.43 | 0.8757 | 3 |
| token_budget_r0.88_m8 | True | 0.0019 | 12.20 | 0.8780 | 3 |
| token_budget_r0.92_m7 | True | 0.0019 | 12.15 | 0.8785 | 3 |
| token_budget_r0.90_m8 | True | 0.0019 | 11.73 | 0.8827 | 3 |
| token_budget_r0.92_m8 | True | 0.0019 | 10.74 | 0.8926 | 3 |
| token_budget_r0.95_m4 | True | 0.0019 | 9.66 | 0.9034 | 3 |
| token_budget_r0.95_m5 | True | 0.0019 | 9.66 | 0.9034 | 3 |
| token_budget_r0.95_m6 | True | 0.0019 | 9.66 | 0.9034 | 3 |
| token_budget_r0.95_m7 | True | 0.0019 | 9.59 | 0.9041 | 3 |
| token_budget_r0.95_m8 | True | 0.0019 | 9.39 | 0.9061 | 3 |
| token_budget_r0.98_m4 | True | 0.0019 | 6.83 | 0.9317 | 3 |
| token_budget_r0.98_m5 | True | 0.0019 | 6.83 | 0.9317 | 3 |
| token_budget_r0.98_m6 | True | 0.0019 | 6.83 | 0.9317 | 3 |
| token_budget_r0.98_m7 | True | 0.0019 | 6.83 | 0.9317 | 3 |
| token_budget_r0.98_m8 | True | 0.0019 | 6.83 | 0.9317 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8402 | 15.98 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8681 | 0.0096 | -0.0072 | 0.0264 | True | 0.8899 | 11.01 | 0.424 | 0.7890 |
| task38 | 17 | 0.8657 | 0.0072 | -0.0120 | 0.0264 | False | 0.8863 | 11.37 | 0.6291 | 0.8082 |
| task38 | 19 | 0.8657 | 0.0072 | -0.0120 | 0.0264 | False | 0.8790 | 12.10 | 0.6072 | 0.8034 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
