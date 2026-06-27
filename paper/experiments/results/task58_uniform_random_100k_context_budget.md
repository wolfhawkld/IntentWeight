# Task38 Calibrated Context Budget

- Scale: `task58_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.88_m8`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0186 | 17.77 | 0.8223 | 3 |
| token_budget_r0.85_m5 | False | -0.0186 | 17.77 | 0.8223 | 3 |
| token_budget_r0.85_m6 | False | -0.0186 | 17.52 | 0.8248 | 3 |
| token_budget_r0.85_m7 | False | -0.0186 | 16.67 | 0.8333 | 3 |
| token_budget_r0.88_m4 | False | -0.0168 | 15.18 | 0.8482 | 3 |
| token_budget_r0.88_m5 | False | -0.0168 | 15.18 | 0.8482 | 3 |
| token_budget_r0.88_m6 | False | -0.0168 | 15.11 | 0.8489 | 3 |
| token_budget_r0.88_m7 | False | -0.0168 | 14.67 | 0.8533 | 3 |
| token_budget_r0.85_m8 | False | -0.0093 | 12.83 | 0.8717 | 3 |
| token_budget_r0.90_m4 | False | -0.0130 | 12.32 | 0.8768 | 3 |
| token_budget_r0.90_m5 | False | -0.0130 | 12.32 | 0.8768 | 3 |
| token_budget_r0.90_m6 | False | -0.0130 | 12.25 | 0.8775 | 3 |
| token_budget_r0.90_m7 | False | -0.0130 | 11.95 | 0.8805 | 3 |
| token_budget_r0.88_m8 | False | -0.0074 | 11.63 | 0.8837 | 3 |
| token_budget_r0.90_m8 | False | -0.0074 | 10.65 | 0.8935 | 3 |
| token_budget_r0.92_m4 | False | -0.0074 | 10.13 | 0.8987 | 3 |
| token_budget_r0.92_m5 | False | -0.0074 | 10.13 | 0.8987 | 3 |
| token_budget_r0.92_m6 | False | -0.0074 | 10.08 | 0.8992 | 3 |
| token_budget_r0.92_m7 | False | -0.0074 | 9.96 | 0.9004 | 3 |
| token_budget_r0.92_m8 | False | -0.0074 | 9.16 | 0.9084 | 3 |
| token_budget_r0.95_m4 | False | -0.0093 | 7.24 | 0.9276 | 3 |
| token_budget_r0.95_m5 | False | -0.0093 | 7.24 | 0.9276 | 3 |
| token_budget_r0.95_m6 | False | -0.0093 | 7.24 | 0.9276 | 3 |
| token_budget_r0.95_m7 | False | -0.0093 | 7.22 | 0.9278 | 3 |
| token_budget_r0.95_m8 | False | -0.0093 | 6.96 | 0.9304 | 3 |
| token_budget_r0.98_m4 | False | -0.0074 | 5.56 | 0.9444 | 3 |
| token_budget_r0.98_m5 | False | -0.0074 | 5.56 | 0.9444 | 3 |
| token_budget_r0.98_m6 | False | -0.0074 | 5.56 | 0.9444 | 3 |
| token_budget_r0.98_m7 | False | -0.0074 | 5.56 | 0.9444 | 3 |
| token_budget_r0.98_m8 | False | -0.0074 | 5.56 | 0.9444 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8609 | -0.0096 | -0.0192 | -0.0024 | False | 0.8478 | 15.22 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8561 | -0.0144 | -0.0264 | -0.0048 | False | 0.8126 | 18.74 | 0.03125 | 0.9856 |
| dense_fixed |  | 0.8633 | -0.0072 | -0.0168 | 0.0000 | False | 0.9019 | 9.81 | 0.25 | 0.9928 |
| task38 | 13 | 0.8825 | 0.0120 | -0.0072 | 0.0312 | True | 0.8838 | 11.62 | 0.3018 | 0.7602 |
| task38 | 17 | 0.8873 | 0.0168 | -0.0024 | 0.0360 | True | 0.8825 | 11.75 | 0.1435 | 0.7506 |
| task38 | 19 | 0.8729 | 0.0024 | -0.0144 | 0.0192 | False | 0.8760 | 12.40 | 1 | 0.7458 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
