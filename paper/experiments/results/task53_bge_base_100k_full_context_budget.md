# Task38 Calibrated Context Budget

- Scale: `100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.92_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | False | -0.0037 | 21.01 | 0.7899 | 3 |
| token_budget_r0.85_m5 | False | -0.0037 | 21.01 | 0.7899 | 3 |
| token_budget_r0.85_m6 | False | -0.0037 | 20.87 | 0.7913 | 3 |
| token_budget_r0.85_m7 | False | -0.0037 | 19.97 | 0.8003 | 3 |
| token_budget_r0.88_m4 | False | -0.0056 | 18.61 | 0.8139 | 3 |
| token_budget_r0.88_m5 | False | -0.0056 | 18.61 | 0.8139 | 3 |
| token_budget_r0.88_m6 | False | -0.0056 | 18.59 | 0.8141 | 3 |
| token_budget_r0.88_m7 | False | -0.0056 | 18.14 | 0.8186 | 3 |
| token_budget_r0.85_m8 | False | -0.0037 | 17.66 | 0.8234 | 3 |
| token_budget_r0.90_m4 | False | -0.0056 | 16.96 | 0.8304 | 3 |
| token_budget_r0.90_m5 | False | -0.0056 | 16.96 | 0.8304 | 3 |
| token_budget_r0.90_m6 | False | -0.0056 | 16.94 | 0.8306 | 3 |
| token_budget_r0.90_m7 | False | -0.0056 | 16.77 | 0.8323 | 3 |
| token_budget_r0.88_m8 | False | -0.0037 | 16.53 | 0.8347 | 3 |
| token_budget_r0.90_m8 | False | -0.0037 | 15.79 | 0.8421 | 3 |
| token_budget_r0.92_m4 | True | 0.0037 | 15.38 | 0.8462 | 3 |
| token_budget_r0.92_m5 | True | 0.0037 | 15.38 | 0.8462 | 3 |
| token_budget_r0.92_m6 | True | 0.0037 | 15.38 | 0.8462 | 3 |
| token_budget_r0.92_m7 | True | 0.0037 | 15.33 | 0.8467 | 3 |
| token_budget_r0.92_m8 | True | 0.0037 | 14.78 | 0.8522 | 3 |
| token_budget_r0.95_m4 | True | 0.0019 | 13.48 | 0.8652 | 3 |
| token_budget_r0.95_m5 | True | 0.0019 | 13.48 | 0.8652 | 3 |
| token_budget_r0.95_m6 | True | 0.0019 | 13.48 | 0.8652 | 3 |
| token_budget_r0.95_m7 | True | 0.0019 | 13.48 | 0.8652 | 3 |
| token_budget_r0.95_m8 | True | 0.0019 | 13.41 | 0.8659 | 3 |
| token_budget_r0.98_m4 | True | 0.0019 | 11.75 | 0.8825 | 3 |
| token_budget_r0.98_m5 | True | 0.0019 | 11.75 | 0.8825 | 3 |
| token_budget_r0.98_m6 | True | 0.0019 | 11.75 | 0.8825 | 3 |
| token_budget_r0.98_m7 | True | 0.0019 | 11.75 | 0.8825 | 3 |
| token_budget_r0.98_m8 | True | 0.0019 | 11.75 | 0.8825 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8897 | -0.0096 | -0.0216 | -0.0024 | False | 0.8483 | 15.17 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8897 | -0.0096 | -0.0192 | -0.0024 | False | 0.8154 | 18.46 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8945 | -0.0048 | -0.0120 | 0.0000 | False | 0.8996 | 10.04 | 0.5 | 0.9952 |
| task38 | 13 | 0.8993 | 0.0000 | -0.0144 | 0.0144 | False | 0.8757 | 12.43 | 1 | 0.8010 |
| task38 | 17 | 0.8945 | -0.0048 | -0.0216 | 0.0120 | False | 0.8797 | 12.03 | 0.7905 | 0.7602 |
| task38 | 19 | 0.9017 | 0.0024 | -0.0120 | 0.0168 | False | 0.8850 | 11.50 | 1 | 0.7938 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
