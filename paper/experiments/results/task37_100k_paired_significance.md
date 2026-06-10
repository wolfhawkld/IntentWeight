# Task37 Paired Significance

| scale | method_label | seed | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | token_saving_ci_low | token_saving_ci_high | method_only_hits | baseline_only_hits | mcnemar_p_two_sided | token_down_nonworse_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100k | task29_C | 13 | 0.8624 | -0.005034 | -0.02517 | 0.01342 | False | 0.9451 | 5.487 | 38.3 | 127 | 15 | 18 | 0.7283 | 0.547 |
| 100k | task29_C | 17 | 0.8641 | -0.003356 | -0.01846 | 0.01174 | False | 0.9496 | 5.04 | 29.41 | 119.7 | 11 | 13 | 0.8388 | 0.5436 |
| 100k | task29_C | 19 | 0.8691 | 0.001678 | -0.01846 | 0.02181 | False | 0.9603 | 3.969 | 17.12 | 100.7 | 17 | 16 | 1 | 0.5252 |
| 100k | task37 | 13 | 0.8658 | -0.001678 | -0.01846 | 0.0151 | False | 0.9208 | 7.917 | 76.21 | 158.2 | 14 | 15 | 1 | 0.6812 |
| 100k | task37 | 17 | 0.8641 | -0.003356 | -0.01846 | 0.01174 | False | 0.9163 | 8.371 | 79.53 | 166.5 | 10 | 12 | 0.8318 | 0.6711 |
| 100k | task37 | 19 | 0.8742 | 0.006711 | -0.01342 | 0.02517 | False | 0.9311 | 6.888 | 61.65 | 143.4 | 19 | 15 | 0.6076 | 0.6426 |

## Notes

- Hit tests are paired by query against dense top-10.
- `noninferior_by_ci` uses the bootstrap CI lower bound and the configured Hit@10 margin.
- Token saving is final evidence-context token saving, not corpus indexing or dense retrieval compute.
