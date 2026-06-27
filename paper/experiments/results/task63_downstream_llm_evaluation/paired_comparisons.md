# Task63 Paired Comparisons

| comparison | paired_queries | baseline_correct_rate | challenger_correct_rate | correct_delta_pp | correct_delta_ci_low_pp | correct_delta_ci_high_pp | mcnemar_exact_p | context_token_saving_percent | context_token_saving_ci_low_percent | context_token_saving_ci_high_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bge_intentweight_vs_dense | 300 | 0.9167 | 0.9167 | 0 | -2.667 | 2.667 | 1 | 6 | 4.013 | 7.972 |
| e5_intentweight_vs_dense | 300 | 0.9167 | 0.92 | 0.3333 | -3 | 3.667 | 1 | 12.04 | 9.931 | 14.16 |
| sent_mmr_intentweight_vs_dense | 300 | 0.89 | 0.9133 | 2.333 | -1.667 | 6.333 | 0.324 | 6.648 | 4.285 | 8.972 |
