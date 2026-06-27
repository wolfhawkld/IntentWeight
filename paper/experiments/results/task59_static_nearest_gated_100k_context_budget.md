# Task38 Calibrated Context Budget

- Scale: `task59_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m8`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0056 | 21.00 | 0.7900 | 3 |
| token_budget_r0.85_m5 | False | -0.0056 | 20.99 | 0.7901 | 3 |
| token_budget_r0.85_m6 | False | -0.0056 | 20.50 | 0.7950 | 3 |
| token_budget_r0.85_m7 | False | -0.0056 | 19.25 | 0.8075 | 3 |
| token_budget_r0.88_m4 | False | -0.0056 | 17.88 | 0.8212 | 3 |
| token_budget_r0.88_m5 | False | -0.0056 | 17.87 | 0.8213 | 3 |
| token_budget_r0.88_m6 | False | -0.0056 | 17.71 | 0.8229 | 3 |
| token_budget_r0.88_m7 | False | -0.0056 | 17.20 | 0.8280 | 3 |
| token_budget_r0.90_m4 | False | -0.0056 | 16.59 | 0.8341 | 3 |
| token_budget_r0.90_m5 | False | -0.0056 | 16.58 | 0.8342 | 3 |
| token_budget_r0.90_m6 | False | -0.0056 | 16.46 | 0.8354 | 3 |
| token_budget_r0.90_m7 | False | -0.0056 | 16.22 | 0.8378 | 3 |
| token_budget_r0.85_m8 | True | 0.0019 | 15.04 | 0.8496 | 3 |
| token_budget_r0.92_m4 | False | -0.0000 | 14.98 | 0.8502 | 3 |
| token_budget_r0.92_m5 | False | -0.0000 | 14.98 | 0.8502 | 3 |
| token_budget_r0.92_m6 | False | -0.0000 | 14.87 | 0.8513 | 3 |
| token_budget_r0.92_m7 | False | -0.0000 | 14.73 | 0.8527 | 3 |
| token_budget_r0.88_m8 | True | 0.0019 | 14.18 | 0.8582 | 3 |
| token_budget_r0.90_m8 | True | 0.0019 | 13.68 | 0.8632 | 3 |
| token_budget_r0.92_m8 | True | 0.0019 | 12.73 | 0.8727 | 3 |
| token_budget_r0.95_m4 | True | 0.0056 | 11.74 | 0.8826 | 3 |
| token_budget_r0.95_m5 | True | 0.0056 | 11.74 | 0.8826 | 3 |
| token_budget_r0.95_m6 | True | 0.0056 | 11.68 | 0.8832 | 3 |
| token_budget_r0.95_m7 | True | 0.0056 | 11.66 | 0.8834 | 3 |
| token_budget_r0.95_m8 | True | 0.0074 | 11.35 | 0.8865 | 3 |
| token_budget_r0.98_m4 | True | 0.0130 | 8.79 | 0.9121 | 3 |
| token_budget_r0.98_m5 | True | 0.0130 | 8.79 | 0.9121 | 3 |
| token_budget_r0.98_m6 | True | 0.0130 | 8.79 | 0.9121 | 3 |
| token_budget_r0.98_m7 | True | 0.0130 | 8.79 | 0.9121 | 3 |
| token_budget_r0.98_m8 | True | 0.0130 | 8.77 | 0.9123 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8729 | -0.0120 | -0.0240 | -0.0024 | False | 0.8372 | 16.28 | 0.0625 | 0.9880 |
| dense_fixed |  | 0.8657 | -0.0192 | -0.0336 | -0.0072 | False | 0.8108 | 18.92 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8753 | -0.0096 | -0.0192 | -0.0024 | False | 0.9022 | 9.78 | 0.125 | 0.9904 |
| task38 | 13 | 0.8633 | -0.0216 | -0.0408 | -0.0024 | False | 0.8787 | 12.13 | 0.04904 | 0.7986 |
| task38 | 17 | 0.8609 | -0.0240 | -0.0480 | -0.0024 | False | 0.8794 | 12.06 | 0.06391 | 0.7866 |
| task38 | 19 | 0.8585 | -0.0264 | -0.0480 | -0.0095 | False | 0.8816 | 11.84 | 0.01273 | 0.7938 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
