# Task38 Calibrated Context Budget

- Scale: `200k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | True | 0.0186 | 16.26 | 0.8374 | 3 |
| token_budget_r0.85_m5 | True | 0.0186 | 16.26 | 0.8374 | 3 |
| token_budget_r0.85_m6 | True | 0.0186 | 16.02 | 0.8398 | 3 |
| token_budget_r0.85_m7 | True | 0.0205 | 15.03 | 0.8497 | 3 |
| token_budget_r0.88_m4 | True | 0.0205 | 13.82 | 0.8618 | 3 |
| token_budget_r0.88_m5 | True | 0.0205 | 13.82 | 0.8618 | 3 |
| token_budget_r0.88_m6 | True | 0.0205 | 13.61 | 0.8639 | 3 |
| token_budget_r0.88_m7 | True | 0.0223 | 13.12 | 0.8688 | 3 |
| token_budget_r0.90_m4 | True | 0.0242 | 12.20 | 0.8780 | 3 |
| token_budget_r0.90_m5 | True | 0.0242 | 12.20 | 0.8780 | 3 |
| token_budget_r0.90_m6 | True | 0.0242 | 12.00 | 0.8800 | 3 |
| token_budget_r0.85_m8 | True | 0.0261 | 11.81 | 0.8819 | 3 |
| token_budget_r0.90_m7 | True | 0.0261 | 11.66 | 0.8834 | 3 |
| token_budget_r0.88_m8 | True | 0.0261 | 10.79 | 0.8921 | 3 |
| token_budget_r0.92_m4 | True | 0.0279 | 10.29 | 0.8971 | 3 |
| token_budget_r0.92_m5 | True | 0.0279 | 10.29 | 0.8971 | 3 |
| token_budget_r0.92_m6 | True | 0.0279 | 10.19 | 0.8981 | 3 |
| token_budget_r0.92_m7 | True | 0.0279 | 10.14 | 0.8986 | 3 |
| token_budget_r0.90_m8 | True | 0.0279 | 9.82 | 0.9018 | 3 |
| token_budget_r0.92_m8 | True | 0.0298 | 9.02 | 0.9098 | 3 |
| token_budget_r0.95_m4 | True | 0.0317 | 7.57 | 0.9243 | 3 |
| token_budget_r0.95_m5 | True | 0.0317 | 7.57 | 0.9243 | 3 |
| token_budget_r0.95_m6 | True | 0.0317 | 7.57 | 0.9243 | 3 |
| token_budget_r0.95_m7 | True | 0.0317 | 7.56 | 0.9244 | 3 |
| token_budget_r0.95_m8 | True | 0.0317 | 7.38 | 0.9262 | 3 |
| token_budget_r0.98_m4 | True | 0.0335 | 5.20 | 0.9480 | 3 |
| token_budget_r0.98_m5 | True | 0.0335 | 5.20 | 0.9480 | 3 |
| token_budget_r0.98_m6 | True | 0.0335 | 5.20 | 0.9480 | 3 |
| token_budget_r0.98_m7 | True | 0.0335 | 5.20 | 0.9480 | 3 |
| token_budget_r0.98_m8 | True | 0.0335 | 5.20 | 0.9480 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.7722 | -0.0240 | -0.0408 | -0.0096 | False | 0.7805 | 21.95 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.7794 | -0.0168 | -0.0288 | -0.0048 | False | 0.8027 | 19.73 | 0.01562 | 0.9832 |
| dense_fixed |  | 0.7890 | -0.0072 | -0.0168 | 0.0000 | False | 0.9040 | 9.60 | 0.25 | 0.9928 |
| task38 | 13 | 0.8201 | 0.0240 | 0.0024 | 0.0456 | True | 0.8516 | 14.84 | 0.06391 | 0.7722 |
| task38 | 17 | 0.8034 | 0.0072 | -0.0144 | 0.0288 | False | 0.8305 | 16.95 | 0.6636 | 0.7794 |
| task38 | 19 | 0.8010 | 0.0048 | -0.0192 | 0.0312 | False | 0.8381 | 16.19 | 0.8506 | 0.7698 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
