# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0410 | 19.57 | 0.8043 | 3 |
| token_budget_r0.85_m5 | False | -0.0410 | 19.56 | 0.8044 | 3 |
| token_budget_r0.85_m6 | False | -0.0410 | 19.45 | 0.8055 | 3 |
| token_budget_r0.85_m7 | False | -0.0410 | 18.00 | 0.8200 | 3 |
| token_budget_r0.88_m4 | False | -0.0447 | 16.81 | 0.8319 | 3 |
| token_budget_r0.88_m5 | False | -0.0447 | 16.81 | 0.8319 | 3 |
| token_budget_r0.88_m6 | False | -0.0447 | 16.81 | 0.8319 | 3 |
| token_budget_r0.88_m7 | False | -0.0447 | 16.39 | 0.8361 | 3 |
| token_budget_r0.90_m4 | False | -0.0447 | 14.95 | 0.8505 | 3 |
| token_budget_r0.90_m5 | False | -0.0447 | 14.95 | 0.8505 | 3 |
| token_budget_r0.90_m6 | False | -0.0447 | 14.95 | 0.8505 | 3 |
| token_budget_r0.90_m7 | False | -0.0447 | 14.80 | 0.8520 | 3 |
| token_budget_r0.85_m8 | False | -0.0410 | 14.13 | 0.8587 | 3 |
| token_budget_r0.88_m8 | False | -0.0428 | 13.37 | 0.8663 | 3 |
| token_budget_r0.92_m4 | False | -0.0410 | 13.25 | 0.8675 | 3 |
| token_budget_r0.92_m5 | False | -0.0410 | 13.25 | 0.8675 | 3 |
| token_budget_r0.92_m6 | False | -0.0410 | 13.25 | 0.8675 | 3 |
| token_budget_r0.92_m7 | False | -0.0410 | 13.20 | 0.8680 | 3 |
| token_budget_r0.90_m8 | False | -0.0428 | 12.52 | 0.8748 | 3 |
| token_budget_r0.92_m8 | False | -0.0410 | 11.82 | 0.8818 | 3 |
| token_budget_r0.95_m4 | False | -0.0410 | 10.36 | 0.8964 | 3 |
| token_budget_r0.95_m5 | False | -0.0410 | 10.36 | 0.8964 | 3 |
| token_budget_r0.95_m6 | False | -0.0410 | 10.36 | 0.8964 | 3 |
| token_budget_r0.95_m7 | False | -0.0410 | 10.36 | 0.8964 | 3 |
| token_budget_r0.95_m8 | False | -0.0410 | 9.85 | 0.9015 | 3 |
| token_budget_r0.98_m4 | False | -0.0428 | 8.03 | 0.9197 | 3 |
| token_budget_r0.98_m5 | False | -0.0428 | 8.03 | 0.9197 | 3 |
| token_budget_r0.98_m6 | False | -0.0428 | 8.03 | 0.9197 | 3 |
| token_budget_r0.98_m7 | False | -0.0428 | 8.03 | 0.9197 | 3 |
| token_budget_r0.98_m8 | False | -0.0428 | 8.03 | 0.9197 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8369 | -0.0216 | -0.0360 | -0.0096 | False | 0.7733 | 22.67 | 0.003906 | 0.9784 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8106 | -0.0480 | -0.0743 | -0.0216 | False | 0.8305 | 16.95 | 0.0008214 | 0.7362 |
| task38 | 17 | 0.8321 | -0.0264 | -0.0504 | -0.0024 | False | 0.8182 | 18.18 | 0.05224 | 0.7650 |
| task38 | 19 | 0.7986 | -0.0600 | -0.0911 | -0.0312 | False | 0.8112 | 18.88 | 0.0001702 | 0.7290 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
