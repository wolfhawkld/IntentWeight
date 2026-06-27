# Task38 Calibrated Context Budget

- Scale: `task60_100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.88_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `False`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0372 | 20.82 | 0.7918 | 3 |
| token_budget_r0.85_m5 | False | -0.0372 | 20.79 | 0.7921 | 3 |
| token_budget_r0.85_m6 | False | -0.0372 | 20.71 | 0.7929 | 3 |
| token_budget_r0.85_m7 | False | -0.0372 | 19.84 | 0.8016 | 3 |
| token_budget_r0.88_m4 | False | -0.0354 | 18.24 | 0.8176 | 3 |
| token_budget_r0.88_m5 | False | -0.0354 | 18.21 | 0.8179 | 3 |
| token_budget_r0.88_m6 | False | -0.0354 | 18.17 | 0.8183 | 3 |
| token_budget_r0.88_m7 | False | -0.0354 | 17.72 | 0.8228 | 3 |
| token_budget_r0.90_m4 | False | -0.0354 | 16.53 | 0.8347 | 3 |
| token_budget_r0.90_m5 | False | -0.0354 | 16.53 | 0.8347 | 3 |
| token_budget_r0.90_m6 | False | -0.0354 | 16.50 | 0.8350 | 3 |
| token_budget_r0.90_m7 | False | -0.0354 | 16.20 | 0.8380 | 3 |
| token_budget_r0.85_m8 | False | -0.0372 | 15.78 | 0.8422 | 3 |
| token_budget_r0.88_m8 | False | -0.0354 | 14.76 | 0.8524 | 3 |
| token_budget_r0.92_m4 | False | -0.0354 | 14.38 | 0.8562 | 3 |
| token_budget_r0.92_m5 | False | -0.0354 | 14.38 | 0.8562 | 3 |
| token_budget_r0.92_m6 | False | -0.0354 | 14.38 | 0.8562 | 3 |
| token_budget_r0.92_m7 | False | -0.0354 | 14.24 | 0.8576 | 3 |
| token_budget_r0.90_m8 | False | -0.0354 | 13.92 | 0.8608 | 3 |
| token_budget_r0.92_m8 | False | -0.0354 | 12.94 | 0.8706 | 3 |
| token_budget_r0.95_m4 | False | -0.0354 | 11.86 | 0.8814 | 3 |
| token_budget_r0.95_m5 | False | -0.0354 | 11.86 | 0.8814 | 3 |
| token_budget_r0.95_m6 | False | -0.0354 | 11.86 | 0.8814 | 3 |
| token_budget_r0.95_m7 | False | -0.0354 | 11.79 | 0.8821 | 3 |
| token_budget_r0.95_m8 | False | -0.0354 | 11.37 | 0.8863 | 3 |
| token_budget_r0.98_m4 | False | -0.0354 | 9.40 | 0.9060 | 3 |
| token_budget_r0.98_m5 | False | -0.0354 | 9.40 | 0.9060 | 3 |
| token_budget_r0.98_m6 | False | -0.0354 | 9.40 | 0.9060 | 3 |
| token_budget_r0.98_m7 | False | -0.0354 | 9.33 | 0.9067 | 3 |
| token_budget_r0.98_m8 | False | -0.0354 | 9.32 | 0.9068 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8369 | -0.0216 | -0.0360 | -0.0096 | False | 0.8067 | 19.33 | 0.003906 | 0.9784 |
| dense_fixed |  | 0.8345 | -0.0240 | -0.0408 | -0.0096 | False | 0.8174 | 18.26 | 0.001953 | 0.9760 |
| dense_fixed |  | 0.8441 | -0.0144 | -0.0264 | -0.0048 | False | 0.9042 | 9.58 | 0.03125 | 0.9856 |
| task38 | 13 | 0.8249 | -0.0336 | -0.0600 | -0.0095 | False | 0.8322 | 16.78 | 0.01612 | 0.7122 |
| task38 | 17 | 0.8201 | -0.0384 | -0.0647 | -0.0144 | False | 0.8463 | 15.37 | 0.005223 | 0.6715 |
| task38 | 19 | 0.8369 | -0.0216 | -0.0504 | 0.0048 | False | 0.8522 | 14.78 | 0.1755 | 0.7026 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
