# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m8`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0317 | 21.69 | 0.7831 | 3 |
| token_budget_r0.85_m5 | False | -0.0317 | 21.63 | 0.7837 | 3 |
| token_budget_r0.85_m6 | False | -0.0317 | 21.27 | 0.7873 | 3 |
| token_budget_r0.85_m7 | False | -0.0317 | 19.17 | 0.8083 | 3 |
| token_budget_r0.88_m4 | False | -0.0317 | 18.25 | 0.8175 | 3 |
| token_budget_r0.88_m5 | False | -0.0317 | 18.20 | 0.8180 | 3 |
| token_budget_r0.88_m6 | False | -0.0317 | 18.02 | 0.8198 | 3 |
| token_budget_r0.88_m7 | False | -0.0317 | 17.16 | 0.8284 | 3 |
| token_budget_r0.90_m4 | False | -0.0317 | 16.43 | 0.8357 | 3 |
| token_budget_r0.90_m5 | False | -0.0317 | 16.43 | 0.8357 | 3 |
| token_budget_r0.90_m6 | False | -0.0317 | 16.42 | 0.8358 | 3 |
| token_budget_r0.90_m7 | False | -0.0317 | 16.02 | 0.8398 | 3 |
| token_budget_r0.85_m8 | False | -0.0298 | 15.23 | 0.8477 | 3 |
| token_budget_r0.92_m4 | False | -0.0298 | 14.58 | 0.8542 | 3 |
| token_budget_r0.92_m5 | False | -0.0298 | 14.58 | 0.8542 | 3 |
| token_budget_r0.92_m6 | False | -0.0298 | 14.57 | 0.8543 | 3 |
| token_budget_r0.92_m7 | False | -0.0298 | 14.44 | 0.8556 | 3 |
| token_budget_r0.88_m8 | False | -0.0298 | 14.43 | 0.8557 | 3 |
| token_budget_r0.90_m8 | False | -0.0298 | 13.88 | 0.8612 | 3 |
| token_budget_r0.92_m8 | False | -0.0298 | 13.08 | 0.8692 | 3 |
| token_budget_r0.95_m4 | False | -0.0298 | 11.96 | 0.8804 | 3 |
| token_budget_r0.95_m5 | False | -0.0298 | 11.96 | 0.8804 | 3 |
| token_budget_r0.95_m6 | False | -0.0298 | 11.96 | 0.8804 | 3 |
| token_budget_r0.95_m7 | False | -0.0298 | 11.96 | 0.8804 | 3 |
| token_budget_r0.95_m8 | False | -0.0298 | 11.56 | 0.8844 | 3 |
| token_budget_r0.98_m4 | False | -0.0298 | 10.27 | 0.8973 | 3 |
| token_budget_r0.98_m5 | False | -0.0298 | 10.27 | 0.8973 | 3 |
| token_budget_r0.98_m6 | False | -0.0298 | 10.27 | 0.8973 | 3 |
| token_budget_r0.98_m7 | False | -0.0298 | 10.27 | 0.8973 | 3 |
| token_budget_r0.98_m8 | False | -0.0298 | 10.08 | 0.8992 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8402 | 15.98 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8441 | -0.0144 | -0.0384 | 0.0096 | False | 0.8914 | 10.86 | 0.3616 | 0.7242 |
| task38 | 17 | 0.8489 | -0.0096 | -0.0336 | 0.0168 | False | 0.8641 | 13.59 | 0.5572 | 0.7458 |
| task38 | 19 | 0.8321 | -0.0264 | -0.0504 | 0.0000 | False | 0.8861 | 11.39 | 0.06143 | 0.7242 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
