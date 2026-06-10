# Task38 Calibrated Context Budget

- Scale: `638k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | True | 0.0149 | 14.67 | 0.8533 | 3 |
| token_budget_r0.85_m5 | True | 0.0149 | 14.67 | 0.8533 | 3 |
| token_budget_r0.85_m6 | True | 0.0149 | 14.41 | 0.8559 | 3 |
| token_budget_r0.85_m7 | True | 0.0149 | 13.81 | 0.8619 | 3 |
| token_budget_r0.88_m4 | True | 0.0205 | 11.83 | 0.8817 | 3 |
| token_budget_r0.88_m5 | True | 0.0205 | 11.83 | 0.8817 | 3 |
| token_budget_r0.88_m6 | True | 0.0205 | 11.59 | 0.8841 | 3 |
| token_budget_r0.88_m7 | True | 0.0205 | 11.21 | 0.8879 | 3 |
| token_budget_r0.85_m8 | True | 0.0149 | 10.96 | 0.8904 | 3 |
| token_budget_r0.90_m4 | True | 0.0223 | 10.30 | 0.8970 | 3 |
| token_budget_r0.90_m5 | True | 0.0223 | 10.30 | 0.8970 | 3 |
| token_budget_r0.90_m6 | True | 0.0223 | 10.20 | 0.8980 | 3 |
| token_budget_r0.90_m7 | True | 0.0223 | 10.08 | 0.8992 | 3 |
| token_budget_r0.88_m8 | True | 0.0223 | 9.48 | 0.9052 | 3 |
| token_budget_r0.92_m4 | True | 0.0223 | 8.82 | 0.9118 | 3 |
| token_budget_r0.92_m5 | True | 0.0223 | 8.82 | 0.9118 | 3 |
| token_budget_r0.92_m6 | True | 0.0223 | 8.72 | 0.9128 | 3 |
| token_budget_r0.90_m8 | True | 0.0223 | 8.69 | 0.9131 | 3 |
| token_budget_r0.92_m7 | True | 0.0223 | 8.61 | 0.9139 | 3 |
| token_budget_r0.92_m8 | True | 0.0223 | 7.74 | 0.9226 | 3 |
| token_budget_r0.95_m4 | True | 0.0223 | 6.28 | 0.9372 | 3 |
| token_budget_r0.95_m5 | True | 0.0223 | 6.28 | 0.9372 | 3 |
| token_budget_r0.95_m6 | True | 0.0223 | 6.28 | 0.9372 | 3 |
| token_budget_r0.95_m7 | True | 0.0223 | 6.27 | 0.9373 | 3 |
| token_budget_r0.95_m8 | True | 0.0223 | 6.08 | 0.9392 | 3 |
| token_budget_r0.98_m4 | True | 0.0223 | 4.12 | 0.9588 | 3 |
| token_budget_r0.98_m5 | True | 0.0223 | 4.12 | 0.9588 | 3 |
| token_budget_r0.98_m6 | True | 0.0223 | 4.12 | 0.9588 | 3 |
| token_budget_r0.98_m7 | True | 0.0223 | 4.12 | 0.9588 | 3 |
| token_budget_r0.98_m8 | True | 0.0223 | 4.11 | 0.9589 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.6835 | -0.0384 | -0.0576 | -0.0216 | False | 0.7810 | 21.90 | 3.052e-05 | 0.9616 |
| dense_fixed |  | 0.6882 | -0.0336 | -0.0528 | -0.0168 | False | 0.7796 | 22.04 | 0.0001221 | 0.9664 |
| dense_fixed |  | 0.7074 | -0.0144 | -0.0264 | -0.0048 | False | 0.8897 | 11.03 | 0.03125 | 0.9856 |
| task38 | 13 | 0.7338 | 0.0120 | -0.0168 | 0.0408 | False | 0.8222 | 17.78 | 0.5224 | 0.7962 |
| task38 | 17 | 0.7098 | -0.0120 | -0.0432 | 0.0192 | False | 0.8255 | 17.45 | 0.5424 | 0.7530 |
| task38 | 19 | 0.7194 | -0.0024 | -0.0288 | 0.0264 | False | 0.8263 | 17.37 | 1 | 0.7554 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
