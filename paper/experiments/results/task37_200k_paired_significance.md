# Task37 Paired Significance

| scale | method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | token_saving_ci_low | token_saving_ci_high | method_only_hits | baseline_only_hits | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 200k | task29_C | 13 | 0.8339 | 0.03691 | 0.01678 | 0.05705 | True | 0.9534 | 4.657 | 31.36 | 102.6 | 30 | 8 | 0.000472 | 0.5688 |
| 200k | task29_C | 17 | 0.8188 | 0.02181 | 0.001678 | 0.04362 | True | 0.9498 | 5.018 | 38.46 | 107.5 | 27 | 14 | 0.05958 | 0.5285 |
| 200k | task29_C | 19 | 0.8221 | 0.02517 | 0.005034 | 0.04698 | True | 0.9562 | 4.382 | 27.47 | 99.11 | 27 | 12 | 0.0237 | 0.5503 |
| 200k | task37 | 13 | 0.8289 | 0.03188 | 0.01174 | 0.05201 | True | 0.939 | 6.098 | 46.08 | 124.3 | 28 | 9 | 0.002563 | 0.6577 |
| 200k | task37 | 17 | 0.8104 | 0.01342 | -0.006711 | 0.03356 | True | 0.9197 | 8.033 | 85.38 | 150.1 | 23 | 15 | 0.2559 | 0.6644 |
| 200k | task37 | 19 | 0.8188 | 0.02181 | 0.001636 | 0.04195 | True | 0.9301 | 6.993 | 66.14 | 135.4 | 26 | 13 | 0.05325 | 0.6594 |

## Notes

- Hit tests are paired by query against dense top-10.
- `noninferior_by_ci` uses the bootstrap CI lower bound and the configured Hit@10 margin.
- Token saving is final evidence-context token saving, not corpus indexing or dense retrieval compute.
