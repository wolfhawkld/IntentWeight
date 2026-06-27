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
| token_budget_r0.85_m4 | False | -0.0112 | 19.30 | 0.8070 | 3 |
| token_budget_r0.85_m5 | False | -0.0112 | 19.29 | 0.8071 | 3 |
| token_budget_r0.85_m6 | False | -0.0112 | 19.04 | 0.8096 | 3 |
| token_budget_r0.85_m7 | False | -0.0112 | 18.14 | 0.8186 | 3 |
| token_budget_r0.88_m4 | False | -0.0112 | 16.39 | 0.8361 | 3 |
| token_budget_r0.88_m5 | False | -0.0112 | 16.39 | 0.8361 | 3 |
| token_budget_r0.88_m6 | False | -0.0112 | 16.26 | 0.8374 | 3 |
| token_budget_r0.88_m7 | False | -0.0112 | 15.80 | 0.8420 | 3 |
| token_budget_r0.90_m4 | False | -0.0093 | 14.03 | 0.8597 | 3 |
| token_budget_r0.90_m5 | False | -0.0093 | 14.03 | 0.8597 | 3 |
| token_budget_r0.90_m6 | False | -0.0093 | 14.01 | 0.8599 | 3 |
| token_budget_r0.90_m7 | False | -0.0093 | 13.72 | 0.8628 | 3 |
| token_budget_r0.85_m8 | False | -0.0074 | 13.68 | 0.8632 | 3 |
| token_budget_r0.88_m8 | False | -0.0074 | 12.51 | 0.8749 | 3 |
| token_budget_r0.92_m4 | False | -0.0074 | 12.00 | 0.8800 | 3 |
| token_budget_r0.92_m5 | False | -0.0074 | 12.00 | 0.8800 | 3 |
| token_budget_r0.92_m6 | False | -0.0074 | 12.00 | 0.8800 | 3 |
| token_budget_r0.90_m8 | False | -0.0074 | 11.85 | 0.8815 | 3 |
| token_budget_r0.92_m7 | False | -0.0074 | 11.81 | 0.8819 | 3 |
| token_budget_r0.92_m8 | False | -0.0074 | 10.53 | 0.8947 | 3 |
| token_budget_r0.95_m4 | False | -0.0074 | 9.08 | 0.9092 | 3 |
| token_budget_r0.95_m5 | False | -0.0074 | 9.08 | 0.9092 | 3 |
| token_budget_r0.95_m6 | False | -0.0074 | 9.08 | 0.9092 | 3 |
| token_budget_r0.95_m7 | False | -0.0074 | 9.08 | 0.9092 | 3 |
| token_budget_r0.95_m8 | False | -0.0074 | 8.97 | 0.9103 | 3 |
| token_budget_r0.98_m4 | False | -0.0056 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m5 | False | -0.0056 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m6 | False | -0.0056 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m7 | False | -0.0056 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m8 | False | -0.0056 | 6.94 | 0.9306 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.8956 | 10.44 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8561 | -0.0024 | -0.0216 | 0.0168 | False | 0.9618 | 3.82 | 1 | 0.6163 |
| task38 | 17 | 0.8633 | 0.0048 | -0.0168 | 0.0264 | False | 0.9589 | 4.11 | 0.8318 | 0.6043 |
| task38 | 19 | 0.8729 | 0.0144 | -0.0048 | 0.0336 | True | 0.9390 | 6.10 | 0.2101 | 0.5971 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
