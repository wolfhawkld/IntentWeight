# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.92_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0503 | 20.88 | 0.7912 | 3 |
| token_budget_r0.85_m5 | False | -0.0484 | 20.82 | 0.7918 | 3 |
| token_budget_r0.85_m6 | False | -0.0484 | 20.06 | 0.7994 | 3 |
| token_budget_r0.85_m7 | False | -0.0484 | 18.38 | 0.8162 | 3 |
| token_budget_r0.88_m4 | False | -0.0503 | 17.10 | 0.8290 | 3 |
| token_budget_r0.88_m5 | False | -0.0484 | 17.05 | 0.8295 | 3 |
| token_budget_r0.88_m6 | False | -0.0484 | 16.99 | 0.8301 | 3 |
| token_budget_r0.88_m7 | False | -0.0484 | 16.27 | 0.8373 | 3 |
| token_budget_r0.90_m4 | False | -0.0466 | 15.48 | 0.8452 | 3 |
| token_budget_r0.90_m5 | False | -0.0466 | 15.48 | 0.8452 | 3 |
| token_budget_r0.90_m6 | False | -0.0466 | 15.43 | 0.8457 | 3 |
| token_budget_r0.90_m7 | False | -0.0466 | 14.98 | 0.8502 | 3 |
| token_budget_r0.85_m8 | False | -0.0447 | 14.80 | 0.8520 | 3 |
| token_budget_r0.88_m8 | False | -0.0466 | 13.79 | 0.8621 | 3 |
| token_budget_r0.92_m4 | False | -0.0428 | 13.52 | 0.8648 | 3 |
| token_budget_r0.92_m5 | False | -0.0428 | 13.51 | 0.8649 | 3 |
| token_budget_r0.92_m6 | False | -0.0428 | 13.46 | 0.8654 | 3 |
| token_budget_r0.92_m7 | False | -0.0428 | 13.36 | 0.8664 | 3 |
| token_budget_r0.90_m8 | False | -0.0447 | 13.08 | 0.8692 | 3 |
| token_budget_r0.92_m8 | False | -0.0428 | 12.21 | 0.8779 | 3 |
| token_budget_r0.95_m4 | False | -0.0428 | 10.99 | 0.8901 | 3 |
| token_budget_r0.95_m5 | False | -0.0428 | 10.99 | 0.8901 | 3 |
| token_budget_r0.95_m6 | False | -0.0428 | 10.96 | 0.8904 | 3 |
| token_budget_r0.95_m7 | False | -0.0428 | 10.96 | 0.8904 | 3 |
| token_budget_r0.95_m8 | False | -0.0428 | 10.44 | 0.8956 | 3 |
| token_budget_r0.98_m4 | False | -0.0428 | 8.56 | 0.9144 | 3 |
| token_budget_r0.98_m5 | False | -0.0428 | 8.56 | 0.9144 | 3 |
| token_budget_r0.98_m6 | False | -0.0428 | 8.56 | 0.9144 | 3 |
| token_budget_r0.98_m7 | False | -0.0428 | 8.56 | 0.9144 | 3 |
| token_budget_r0.98_m8 | False | -0.0428 | 8.54 | 0.9146 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8356 | 16.44 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8249 | -0.0336 | -0.0600 | -0.0096 | False | 0.8649 | 13.51 | 0.01254 | 0.6859 |
| task38 | 17 | 0.8177 | -0.0408 | -0.0695 | -0.0144 | False | 0.8485 | 15.15 | 0.005988 | 0.6882 |
| task38 | 19 | 0.8201 | -0.0384 | -0.0671 | -0.0120 | False | 0.9125 | 8.75 | 0.009041 | 0.6379 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
