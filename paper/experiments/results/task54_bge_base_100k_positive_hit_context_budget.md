# Task38 Calibrated Context Budget

- Scale: `100k`
- Calibration queries: `179`
- Frozen test queries: `417`
- Selected policy: `token_budget_r0.97_m4`
- Selection hit margin: `0.0000`
- Selection eligible: `True`

## Calibration Selection

| policy | eligible | mean_hit_delta | mean_token_saving_percent | mean_token_ratio | seed_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| token_budget_r0.97_m4 | True | 0.0019 | 12.15 | 0.8785 | 3 |

## Frozen Test Paired Results

| method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_adaptive |  | 0.8945 | -0.0048 | -0.0120 | 0.0000 | False | 0.8883 | 11.17 | 0.5 | 0.9952 |
| dense_fixed |  | 0.8897 | -0.0096 | -0.0192 | -0.0024 | False | 0.8154 | 18.46 | 0.125 | 0.9904 |
| dense_fixed |  | 0.8945 | -0.0048 | -0.0120 | 0.0000 | False | 0.8996 | 10.04 | 0.5 | 0.9952 |
| task38 | 13 | 0.9089 | 0.0096 | -0.0048 | 0.0240 | True | 0.9189 | 8.11 | 0.3438 | 0.7026 |
| task38 | 17 | 0.9065 | 0.0072 | -0.0072 | 0.0216 | True | 0.9293 | 7.07 | 0.5488 | 0.6882 |
| task38 | 19 | 0.9089 | 0.0096 | -0.0024 | 0.0240 | True | 0.9350 | 6.50 | 0.2891 | 0.7002 |

## Notes

- Policy selection uses only calibration queries.
- Frozen test evaluation is paired by query against dense top-10.
- Token saving is final LLM evidence-context input token saving.
