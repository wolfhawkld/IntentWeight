# Task40 Feedback Recovery

- Dataset: `lotte_writing_search_100k`
- Budget policy: cross-fitted selections from `paper/experiments/results/task73_writing_100k_none_cross_fitted_budget.json`
- Conservative retry ratio: `0.95`
- Calibration queries: `321`
- Test queries: `750`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 18 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 2.87% |
| same_query_retry | 13 | same_arm_boost |  | 18 |  | 0.1667 | 0.0000 | 0.0000 | 3 | 2.36% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 18 |  | 0.2222 | 0.0000 | 0.0000 | 4 | -4.44% |
| same_query_retry | 13 | same_full_context |  | 18 |  | 0.2222 | 0.0000 | 0.0000 | 4 | -16.61% |
| same_query_retry_compression_only | 13 | budgeted_before_feedback |  | 9 |  | 0.0000 | 0.0000 | 0.0000 | 0 | -10.86% |
| same_query_retry_compression_only | 13 | same_arm_boost |  | 9 |  | 0.8889 | 0.0000 | 0.0000 | 8 | -58.09% |
| same_query_retry_compression_only | 13 | same_arm_boost_conservative |  | 9 |  | 1.0000 | 0.0000 | 0.0000 | 9 | -74.48% |
| same_query_retry_compression_only | 13 | same_full_context |  | 9 |  | 1.0000 | 0.0000 | 0.0000 | 9 | -85.66% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 1071 |  | 0 | 0.8768 | 0.0028 | 0.0000 |  | 10.53% |
| same_query_retry_all_queries | 13 | same_arm_boost | 1071 |  | 0 | 0.8796 | 0.0056 | 0.0028 |  | 10.52% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 1071 |  | 0 | 0.8805 | 0.0065 | 0.0037 |  | 10.42% |
| same_query_retry_all_queries | 13 | same_full_context | 1071 |  | 0 | 0.8805 | 0.0065 | 0.0037 |  | 10.25% |
| calibration_to_test | 13 | budgeted_before_feedback | 750 |  | 2 | 0.8787 | 0.0000 | 0.0000 |  | 11.40% |
| calibration_to_test | 13 | generalized_arm_boost | 750 |  | 2 | 0.8787 | 0.0000 | 0.0000 |  | 11.36% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 750 |  | 2 | 0.8787 | 0.0000 | 0.0000 |  | 11.31% |
| calibration_to_test | 13 | generalized_conservative_budget | 750 |  | 2 | 0.8787 | 0.0000 | 0.0000 |  | 11.31% |
| calibration_to_test | 13 | generalized_full_context | 750 |  | 2 | 0.8787 | 0.0000 | 0.0000 |  | 10.88% |
| same_query_retry | 17 | budgeted_before_feedback |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 13.39% |
| same_query_retry | 17 | same_arm_boost |  | 16 |  | 0.2500 | 0.0000 | 0.0000 | 4 | 6.69% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 16 |  | 0.2500 | 0.0000 | 0.0000 | 4 | 2.32% |
| same_query_retry | 17 | same_full_context |  | 16 |  | 0.2500 | 0.0000 | 0.0000 | 4 | -9.70% |
| same_query_retry_compression_only | 17 | budgeted_before_feedback |  | 11 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 18.72% |
| same_query_retry_compression_only | 17 | same_arm_boost |  | 11 |  | 1.0000 | 0.0000 | 0.0000 | 11 | 19.36% |
| same_query_retry_compression_only | 17 | same_arm_boost_conservative |  | 11 |  | 1.0000 | 0.0000 | 0.0000 | 11 | 11.05% |
| same_query_retry_compression_only | 17 | same_full_context |  | 11 |  | 1.0000 | 0.0000 | 0.0000 | 11 | -1.92% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 1071 |  | 0 | 0.8777 | 0.0037 | 0.0000 |  | 10.11% |
| same_query_retry_all_queries | 17 | same_arm_boost | 1071 |  | 0 | 0.8814 | 0.0075 | 0.0037 |  | 10.02% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 1071 |  | 0 | 0.8814 | 0.0075 | 0.0037 |  | 9.96% |
| same_query_retry_all_queries | 17 | same_full_context | 1071 |  | 0 | 0.8814 | 0.0075 | 0.0037 |  | 9.80% |
| calibration_to_test | 17 | budgeted_before_feedback | 750 |  | 3 | 0.8787 | 0.0000 | 0.0000 |  | 10.32% |
| calibration_to_test | 17 | generalized_arm_boost | 750 |  | 3 | 0.8773 | -0.0013 | -0.0013 |  | 10.28% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 750 |  | 3 | 0.8773 | -0.0013 | -0.0013 |  | 10.08% |
| calibration_to_test | 17 | generalized_conservative_budget | 750 |  | 3 | 0.8787 | 0.0000 | 0.0000 |  | 10.12% |
| calibration_to_test | 17 | generalized_full_context | 750 |  | 3 | 0.8800 | 0.0013 | 0.0013 |  | 8.99% |
| same_query_retry | 19 | budgeted_before_feedback |  | 20 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 6.10% |
| same_query_retry | 19 | same_arm_boost |  | 20 |  | 0.3000 | 0.0000 | 0.0000 | 6 | 11.34% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 20 |  | 0.3000 | 0.0000 | 0.0000 | 6 | 8.18% |
| same_query_retry | 19 | same_full_context |  | 20 |  | 0.3000 | 0.0000 | 0.0000 | 6 | -13.65% |
| same_query_retry_compression_only | 19 | budgeted_before_feedback |  | 9 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 10.79% |
| same_query_retry_compression_only | 19 | same_arm_boost |  | 9 |  | 1.0000 | 0.0000 | 0.0000 | 9 | 0.85% |
| same_query_retry_compression_only | 19 | same_arm_boost_conservative |  | 9 |  | 1.0000 | 0.0000 | 0.0000 | 9 | -1.61% |
| same_query_retry_compression_only | 19 | same_full_context |  | 9 |  | 1.0000 | 0.0000 | 0.0000 | 9 | -13.01% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 1071 |  | 0 | 0.8711 | -0.0028 | 0.0000 |  | 9.64% |
| same_query_retry_all_queries | 19 | same_arm_boost | 1071 |  | 0 | 0.8768 | 0.0028 | 0.0056 |  | 9.74% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 1071 |  | 0 | 0.8768 | 0.0028 | 0.0056 |  | 9.68% |
| same_query_retry_all_queries | 19 | same_full_context | 1071 |  | 0 | 0.8768 | 0.0028 | 0.0056 |  | 9.30% |
| calibration_to_test | 19 | budgeted_before_feedback | 750 |  | 5 | 0.8773 | -0.0013 | 0.0000 |  | 9.80% |
| calibration_to_test | 19 | generalized_arm_boost | 750 |  | 5 | 0.8747 | -0.0040 | -0.0027 |  | 9.58% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 750 |  | 5 | 0.8747 | -0.0040 | -0.0027 |  | 8.62% |
| calibration_to_test | 19 | generalized_conservative_budget | 750 |  | 5 | 0.8773 | -0.0013 | 0.0000 |  | 8.81% |
| calibration_to_test | 19 | generalized_full_context | 750 |  | 5 | 0.8773 | -0.0013 | 0.0000 |  | 5.13% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
