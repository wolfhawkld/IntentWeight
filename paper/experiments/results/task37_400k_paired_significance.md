# Task37 Paired Significance

| scale | method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | token_saving_ci_low | token_saving_ci_high | method_only_hits | baseline_only_hits | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 400k | task29_C | 13 | 0.7802 | 0.008389 | -0.01342 | 0.0302 | False | 0.9453 | 5.475 | 46.74 | 113.7 | 25 | 20 | 0.5515 | 0.5587 |
| 400k | task29_C | 17 | 0.7869 | 0.0151 | -0.008389 | 0.04027 | True | 0.9266 | 7.338 | 72.36 | 145.2 | 32 | 23 | 0.2806 | 0.5805 |
| 400k | task29_C | 19 | 0.7785 | 0.006711 | -0.01678 | 0.0302 | False | 0.9685 | 3.15 | 9.6 | 84.46 | 26 | 22 | 0.6655 | 0.5067 |
| 400k | task37 | 13 | 0.7768 | 0.005034 | -0.01514 | 0.02685 | False | 0.9092 | 9.081 | 103.2 | 165.6 | 23 | 20 | 0.7608 | 0.6896 |
| 400k | task37 | 17 | 0.7869 | 0.0151 | -0.008431 | 0.04027 | True | 0.8936 | 10.64 | 126.1 | 190.6 | 30 | 21 | 0.2624 | 0.6812 |
| 400k | task37 | 19 | 0.7735 | 0.001678 | -0.02013 | 0.02349 | False | 0.914 | 8.605 | 95.51 | 161.2 | 23 | 22 | 1 | 0.6477 |

## Notes

- Hit tests are paired by query against dense top-10.
- `noninferior_by_ci` uses the bootstrap CI lower bound and the configured Hit@10 margin.
- Token saving is final evidence-context token saving, not corpus indexing or dense retrieval compute.
