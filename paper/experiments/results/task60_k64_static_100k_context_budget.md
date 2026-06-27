# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.88_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0074 | 19.42 | 0.8058 | 3 |
| token_budget_r0.85_m5 | False | -0.0074 | 19.42 | 0.8058 | 3 |
| token_budget_r0.85_m6 | False | -0.0074 | 19.24 | 0.8076 | 3 |
| token_budget_r0.85_m7 | False | -0.0074 | 18.16 | 0.8184 | 3 |
| token_budget_r0.88_m4 | True | 0.0000 | 16.86 | 0.8314 | 3 |
| token_budget_r0.88_m5 | True | 0.0000 | 16.86 | 0.8314 | 3 |
| token_budget_r0.88_m6 | True | 0.0000 | 16.73 | 0.8327 | 3 |
| token_budget_r0.88_m7 | True | 0.0000 | 16.09 | 0.8391 | 3 |
| token_budget_r0.90_m4 | True | 0.0000 | 14.28 | 0.8572 | 3 |
| token_budget_r0.90_m5 | True | 0.0000 | 14.28 | 0.8572 | 3 |
| token_budget_r0.90_m6 | True | 0.0000 | 14.24 | 0.8576 | 3 |
| token_budget_r0.90_m7 | True | 0.0000 | 13.77 | 0.8623 | 3 |
| token_budget_r0.85_m8 | True | 0.0037 | 13.65 | 0.8635 | 3 |
| token_budget_r0.88_m8 | True | 0.0037 | 12.57 | 0.8743 | 3 |
| token_budget_r0.92_m4 | True | 0.0037 | 11.99 | 0.8801 | 3 |
| token_budget_r0.92_m5 | True | 0.0037 | 11.99 | 0.8801 | 3 |
| token_budget_r0.92_m6 | True | 0.0037 | 11.96 | 0.8804 | 3 |
| token_budget_r0.90_m8 | True | 0.0037 | 11.85 | 0.8815 | 3 |
| token_budget_r0.92_m7 | True | 0.0037 | 11.58 | 0.8842 | 3 |
| token_budget_r0.92_m8 | True | 0.0037 | 10.65 | 0.8935 | 3 |
| token_budget_r0.95_m4 | True | 0.0037 | 9.56 | 0.9044 | 3 |
| token_budget_r0.95_m5 | True | 0.0037 | 9.56 | 0.9044 | 3 |
| token_budget_r0.95_m6 | True | 0.0037 | 9.53 | 0.9047 | 3 |
| token_budget_r0.95_m7 | True | 0.0037 | 9.46 | 0.9054 | 3 |
| token_budget_r0.95_m8 | True | 0.0037 | 9.00 | 0.9100 | 3 |
| token_budget_r0.98_m4 | True | 0.0037 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m5 | True | 0.0037 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m6 | True | 0.0037 | 6.94 | 0.9306 | 3 |
| token_budget_r0.98_m7 | True | 0.0037 | 6.87 | 0.9313 | 3 |
| token_budget_r0.98_m8 | True | 0.0037 | 6.87 | 0.9313 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8369 | -0.0216 | -0.0360 | -0.0096 | False | 0.8067 | 19.33 | 0.003906 | 0.9784 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8561 | -0.0024 | -0.0240 | 0.0192 | False | 0.8590 | 14.10 | 1 | 0.7866 |
| task38 | 17 | 0.8513 | -0.0072 | -0.0288 | 0.0144 | False | 0.8631 | 13.69 | 0.6636 | 0.7746 |
| task38 | 19 | 0.8537 | -0.0048 | -0.0264 | 0.0144 | False | 0.8640 | 13.60 | 0.8238 | 0.7674 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
