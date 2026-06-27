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
| token_budget_r0.85_m4 | False | -0.0074 | 18.77 | 0.8123 | 3 |
| token_budget_r0.85_m5 | False | -0.0074 | 18.77 | 0.8123 | 3 |
| token_budget_r0.85_m6 | False | -0.0074 | 18.72 | 0.8128 | 3 |
| token_budget_r0.85_m7 | False | -0.0074 | 17.91 | 0.8209 | 3 |
| token_budget_r0.88_m4 | False | -0.0112 | 16.35 | 0.8365 | 3 |
| token_budget_r0.88_m5 | False | -0.0112 | 16.35 | 0.8365 | 3 |
| token_budget_r0.88_m6 | False | -0.0112 | 16.32 | 0.8368 | 3 |
| token_budget_r0.88_m7 | False | -0.0112 | 15.92 | 0.8408 | 3 |
| token_budget_r0.85_m8 | False | -0.0037 | 14.14 | 0.8586 | 3 |
| token_budget_r0.90_m4 | False | -0.0093 | 14.05 | 0.8595 | 3 |
| token_budget_r0.90_m5 | False | -0.0093 | 14.05 | 0.8595 | 3 |
| token_budget_r0.90_m6 | False | -0.0093 | 14.02 | 0.8598 | 3 |
| token_budget_r0.90_m7 | False | -0.0093 | 13.71 | 0.8629 | 3 |
| token_budget_r0.88_m8 | False | -0.0056 | 13.07 | 0.8693 | 3 |
| token_budget_r0.90_m8 | False | -0.0056 | 12.09 | 0.8791 | 3 |
| token_budget_r0.92_m4 | False | -0.0037 | 11.84 | 0.8816 | 3 |
| token_budget_r0.92_m5 | False | -0.0037 | 11.84 | 0.8816 | 3 |
| token_budget_r0.92_m6 | False | -0.0037 | 11.84 | 0.8816 | 3 |
| token_budget_r0.92_m7 | False | -0.0037 | 11.68 | 0.8832 | 3 |
| token_budget_r0.92_m8 | False | -0.0037 | 10.97 | 0.8903 | 3 |
| token_budget_r0.95_m4 | False | -0.0037 | 9.19 | 0.9081 | 3 |
| token_budget_r0.95_m5 | False | -0.0037 | 9.19 | 0.9081 | 3 |
| token_budget_r0.95_m6 | False | -0.0037 | 9.19 | 0.9081 | 3 |
| token_budget_r0.95_m7 | False | -0.0037 | 9.12 | 0.9088 | 3 |
| token_budget_r0.95_m8 | False | -0.0037 | 8.91 | 0.9109 | 3 |
| token_budget_r0.98_m4 | False | -0.0037 | 7.10 | 0.9290 | 3 |
| token_budget_r0.98_m5 | False | -0.0037 | 7.10 | 0.9290 | 3 |
| token_budget_r0.98_m6 | False | -0.0037 | 7.10 | 0.9290 | 3 |
| token_budget_r0.98_m7 | False | -0.0037 | 7.03 | 0.9297 | 3 |
| token_budget_r0.98_m8 | False | -0.0037 | 7.01 | 0.9299 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8393 | -0.0192 | -0.0336 | -0.0072 | False | 0.8402 | 15.98 | 0.007812 | 0.9808 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8729 | 0.0144 | -0.0048 | 0.0336 | True | 0.8996 | 10.04 | 0.2379 | 0.7266 |
| task38 | 17 | 0.8681 | 0.0096 | -0.0072 | 0.0288 | True | 0.8940 | 10.60 | 0.4545 | 0.7218 |
| task38 | 19 | 0.8705 | 0.0120 | -0.0072 | 0.0312 | True | 0.8994 | 10.06 | 0.3018 | 0.7290 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
