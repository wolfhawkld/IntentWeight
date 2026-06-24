# Task38 Calibrated Context Budget

- Scale: `100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.95_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0372 | 15.69 | 0.8431 | 3 |
| token_budget_r0.85_m5 | False | -0.0372 | 15.55 | 0.8445 | 3 |
| token_budget_r0.85_m6 | False | -0.0372 | 15.48 | 0.8452 | 3 |
| token_budget_r0.85_m7 | False | -0.0372 | 14.17 | 0.8583 | 3 |
| token_budget_r0.88_m4 | False | -0.0372 | 12.91 | 0.8709 | 3 |
| token_budget_r0.88_m5 | False | -0.0372 | 12.90 | 0.8710 | 3 |
| token_budget_r0.88_m6 | False | -0.0372 | 12.87 | 0.8713 | 3 |
| token_budget_r0.88_m7 | False | -0.0372 | 12.34 | 0.8766 | 3 |
| token_budget_r0.85_m8 | False | -0.0372 | 11.64 | 0.8836 | 3 |
| token_budget_r0.90_m4 | False | -0.0335 | 11.11 | 0.8889 | 3 |
| token_budget_r0.90_m5 | False | -0.0335 | 11.11 | 0.8889 | 3 |
| token_budget_r0.90_m6 | False | -0.0335 | 11.10 | 0.8890 | 3 |
| token_budget_r0.90_m7 | False | -0.0335 | 10.82 | 0.8918 | 3 |
| token_budget_r0.88_m8 | False | -0.0372 | 10.76 | 0.8924 | 3 |
| token_budget_r0.90_m8 | False | -0.0354 | 9.74 | 0.9026 | 3 |
| token_budget_r0.92_m4 | False | -0.0354 | 9.33 | 0.9067 | 3 |
| token_budget_r0.92_m5 | False | -0.0354 | 9.33 | 0.9067 | 3 |
| token_budget_r0.92_m6 | False | -0.0354 | 9.33 | 0.9067 | 3 |
| token_budget_r0.92_m7 | False | -0.0354 | 9.16 | 0.9084 | 3 |
| token_budget_r0.92_m8 | False | -0.0354 | 8.60 | 0.9140 | 3 |
| token_budget_r0.95_m4 | False | -0.0317 | 7.40 | 0.9260 | 3 |
| token_budget_r0.95_m5 | False | -0.0317 | 7.40 | 0.9260 | 3 |
| token_budget_r0.95_m6 | False | -0.0317 | 7.40 | 0.9260 | 3 |
| token_budget_r0.95_m7 | False | -0.0317 | 7.35 | 0.9265 | 3 |
| token_budget_r0.95_m8 | False | -0.0317 | 7.20 | 0.9280 | 3 |
| token_budget_r0.98_m4 | False | -0.0317 | 4.93 | 0.9507 | 3 |
| token_budget_r0.98_m5 | False | -0.0317 | 4.93 | 0.9507 | 3 |
| token_budget_r0.98_m6 | False | -0.0317 | 4.93 | 0.9507 | 3 |
| token_budget_r0.98_m7 | False | -0.0317 | 4.93 | 0.9507 | 3 |
| token_budget_r0.98_m8 | False | -0.0317 | 4.93 | 0.9507 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8657 | -0.0096 | -0.0192 | -0.0024 | False | 0.8695 | 13.05 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8633 | -0.0120 | -0.0240 | -0.0024 | False | 0.8221 | 17.79 | 0.0625 | 0.9880 |
| dense_fixed |  | 0.8657 | -0.0096 | -0.0192 | -0.0024 | False | 0.9064 | 9.36 | 0.125 | 0.9904 |
| task38 | 13 | 0.8369 | -0.0384 | -0.0647 | -0.0144 | False | 0.9473 | 5.27 | 0.005223 | 0.6091 |
| task38 | 17 | 0.8345 | -0.0408 | -0.0647 | -0.0192 | False | 0.9189 | 8.11 | 0.0009105 | 0.6139 |
| task38 | 19 | 0.8513 | -0.0240 | -0.0456 | -0.0024 | False | 0.9288 | 7.12 | 0.04139 | 0.6523 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
