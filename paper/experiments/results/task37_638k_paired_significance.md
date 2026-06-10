# Task37 Paired Significance

| scale | method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | token_saving_ci_low | token_saving_ci_high | method_only_hits | baseline_only_hits | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 638k | task29_C | 13 | 0.7567 | 0.02852 | 0.005034 | 0.05201 | True | 0.9542 | 4.577 | 35.51 | 103.1 | 34 | 17 | 0.02409 | 0.5285 |
| 638k | task29_C | 17 | 0.7399 | 0.01174 | -0.01174 | 0.03859 | False | 0.9494 | 5.059 | 39.35 | 118.4 | 32 | 25 | 0.427 | 0.505 |
| 638k | task29_C | 19 | 0.7433 | 0.0151 | -0.008389 | 0.03859 | True | 0.9506 | 4.941 | 39.04 | 115.1 | 30 | 21 | 0.2624 | 0.5369 |
| 638k | task37 | 13 | 0.7534 | 0.02517 | 0.003356 | 0.04698 | True | 0.9204 | 7.957 | 89.51 | 153.7 | 30 | 15 | 0.0357 | 0.6762 |
| 638k | task37 | 17 | 0.7332 | 0.005034 | -0.02013 | 0.03188 | False | 0.9188 | 8.12 | 88.81 | 161.2 | 30 | 27 | 0.7914 | 0.6527 |
| 638k | task37 | 19 | 0.7433 | 0.0151 | -0.006711 | 0.03691 | True | 0.9135 | 8.651 | 96.77 | 167.3 | 28 | 19 | 0.243 | 0.6678 |

## Notes

- Hit tests are paired by query against dense top-10.
- `noninferior_by_ci` uses the bootstrap CI lower bound and the configured Hit@10 margin.
- Token saving is final evidence-context token saving, not corpus indexing or dense retrieval compute.
