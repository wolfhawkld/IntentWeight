# Task38 Calibrated Context Budget

- Scale: `science_20k_q200`
- Calibration queries: `60`
- Frozen test queries: `140`
- Selected policy: `token_budget_r0.85_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.85_m4 | True | 0.0222 | 17.97 | 0.8203 | 3 |
| token_budget_r0.85_m5 | True | 0.0222 | 16.95 | 0.8305 | 3 |
| token_budget_r0.85_m6 | True | 0.0222 | 16.64 | 0.8336 | 3 |
| token_budget_r0.85_m7 | True | 0.0167 | 15.98 | 0.8402 | 3 |
| token_budget_r0.88_m4 | True | 0.0333 | 14.09 | 0.8591 | 3 |
| token_budget_r0.88_m5 | True | 0.0333 | 14.09 | 0.8591 | 3 |
| token_budget_r0.88_m6 | True | 0.0333 | 14.09 | 0.8591 | 3 |
| token_budget_r0.88_m7 | True | 0.0278 | 13.70 | 0.8630 | 3 |
| token_budget_r0.90_m4 | True | 0.0278 | 12.77 | 0.8723 | 3 |
| token_budget_r0.90_m5 | True | 0.0278 | 12.77 | 0.8723 | 3 |
| token_budget_r0.90_m6 | True | 0.0278 | 12.77 | 0.8723 | 3 |
| token_budget_r0.90_m7 | True | 0.0278 | 12.58 | 0.8742 | 3 |
| token_budget_r0.85_m8 | True | 0.0333 | 12.12 | 0.8788 | 3 |
| token_budget_r0.92_m4 | True | 0.0278 | 11.36 | 0.8864 | 3 |
| token_budget_r0.92_m5 | True | 0.0278 | 11.36 | 0.8864 | 3 |
| token_budget_r0.92_m6 | True | 0.0278 | 11.36 | 0.8864 | 3 |
| token_budget_r0.92_m7 | True | 0.0278 | 11.24 | 0.8876 | 3 |
| token_budget_r0.88_m8 | True | 0.0333 | 10.92 | 0.8908 | 3 |
| token_budget_r0.90_m8 | True | 0.0333 | 10.40 | 0.8960 | 3 |
| token_budget_r0.92_m8 | True | 0.0333 | 9.57 | 0.9043 | 3 |
| token_budget_r0.95_m4 | True | 0.0389 | 8.63 | 0.9137 | 3 |
| token_budget_r0.95_m5 | True | 0.0389 | 8.63 | 0.9137 | 3 |
| token_budget_r0.95_m6 | True | 0.0389 | 8.63 | 0.9137 | 3 |
| token_budget_r0.95_m7 | True | 0.0389 | 8.63 | 0.9137 | 3 |
| token_budget_r0.95_m8 | True | 0.0389 | 7.93 | 0.9207 | 3 |
| token_budget_r0.98_m4 | True | 0.0444 | 6.28 | 0.9372 | 3 |
| token_budget_r0.98_m5 | True | 0.0444 | 6.28 | 0.9372 | 3 |
| token_budget_r0.98_m6 | True | 0.0444 | 6.28 | 0.9372 | 3 |
| token_budget_r0.98_m7 | True | 0.0444 | 6.28 | 0.9372 | 3 |
| token_budget_r0.98_m8 | True | 0.0444 | 6.28 | 0.9372 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8857 | -0.0071 | -0.0214 | 0.0000 | False | 0.7731 | 22.69 | 1 | 0.9929 |
| dense_fixed |  | 0.8786 | -0.0143 | -0.0357 | 0.0000 | False | 0.7999 | 20.01 | 0.5 | 0.9857 |
| dense_fixed |  | 0.8786 | -0.0143 | -0.0357 | 0.0000 | False | 0.9048 | 9.52 | 0.5 | 0.9857 |
| task38 | 13 | 0.9214 | 0.0286 | 0.0071 | 0.0643 | True | 0.8682 | 13.18 | 0.125 | 0.7429 |
| task38 | 17 | 0.9071 | 0.0143 | -0.0145 | 0.0500 | False | 0.8569 | 14.31 | 0.6875 | 0.7571 |
| task38 | 19 | 0.9000 | 0.0071 | -0.0357 | 0.0500 | False | 0.8609 | 13.91 | 1 | 0.7143 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
