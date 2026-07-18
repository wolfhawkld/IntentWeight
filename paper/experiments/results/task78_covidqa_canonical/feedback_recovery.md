# Task40 Feedback Recovery

- Dataset: `covidqa`
- Budget policy: cross-fitted selections from `paper/experiments/results/task78_covidqa_canonical/cross_fitted_calibration.json`
- Conservative retry ratio: `0.98`
- Calibration queries: `530`
- Test queries: `1235`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 55 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 15.43% |
| same_query_retry | 13 | same_arm_boost |  | 55 |  | 0.1455 | 0.0000 | 0.0000 | 8 | 15.13% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 55 |  | 0.1636 | 0.0000 | 0.0000 | 9 | 12.58% |
| same_query_retry | 13 | same_full_context |  | 55 |  | 0.3273 | 0.0000 | 0.0000 | 18 | 2.50% |
| same_query_retry_compression_only | 13 | budgeted_before_feedback |  | 44 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 11.30% |
| same_query_retry_compression_only | 13 | same_arm_boost |  | 44 |  | 0.3636 | 0.0000 | 0.0000 | 16 | 10.97% |
| same_query_retry_compression_only | 13 | same_arm_boost_conservative |  | 44 |  | 0.4091 | 0.0000 | 0.0000 | 18 | 9.61% |
| same_query_retry_compression_only | 13 | same_full_context |  | 44 |  | 0.7273 | 0.0000 | 0.0000 | 32 | 0.99% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 1765 |  | 0 | 0.5955 | -0.0023 | 0.0000 |  | 9.01% |
| same_query_retry_all_queries | 13 | same_arm_boost | 1765 |  | 0 | 0.6000 | 0.0023 | 0.0045 |  | 9.00% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 1765 |  | 0 | 0.6006 | 0.0028 | 0.0051 |  | 8.91% |
| same_query_retry_all_queries | 13 | same_full_context | 1765 |  | 0 | 0.6057 | 0.0079 | 0.0102 |  | 8.57% |
| calibration_to_test | 13 | budgeted_before_feedback | 1235 |  | 9 | 0.5960 | -0.0113 | 0.0000 |  | 8.87% |
| calibration_to_test | 13 | generalized_arm_boost | 1235 |  | 9 | 0.5927 | -0.0146 | -0.0032 |  | 8.84% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 1235 |  | 9 | 0.5927 | -0.0146 | -0.0032 |  | 8.36% |
| calibration_to_test | 13 | generalized_conservative_budget | 1235 |  | 9 | 0.5960 | -0.0113 | 0.0000 |  | 8.41% |
| calibration_to_test | 13 | generalized_full_context | 1235 |  | 9 | 0.6032 | -0.0040 | 0.0073 |  | 5.79% |
| same_query_retry | 17 | budgeted_before_feedback |  | 58 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 19.07% |
| same_query_retry | 17 | same_arm_boost |  | 58 |  | 0.0690 | 0.0000 | 0.0000 | 4 | 18.92% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 58 |  | 0.0690 | 0.0000 | 0.0000 | 4 | 17.30% |
| same_query_retry | 17 | same_full_context |  | 58 |  | 0.2414 | 0.0000 | 0.0000 | 14 | 7.60% |
| same_query_retry_compression_only | 17 | budgeted_before_feedback |  | 41 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 9.87% |
| same_query_retry_compression_only | 17 | same_arm_boost |  | 41 |  | 0.2683 | 0.0000 | 0.0000 | 11 | 9.46% |
| same_query_retry_compression_only | 17 | same_arm_boost_conservative |  | 41 |  | 0.2927 | 0.0000 | 0.0000 | 12 | 8.04% |
| same_query_retry_compression_only | 17 | same_full_context |  | 41 |  | 0.6098 | 0.0000 | 0.0000 | 25 | 1.35% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 1765 |  | 0 | 0.5966 | -0.0011 | 0.0000 |  | 9.23% |
| same_query_retry_all_queries | 17 | same_arm_boost | 1765 |  | 0 | 0.5989 | 0.0011 | 0.0023 |  | 9.22% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 1765 |  | 0 | 0.5989 | 0.0011 | 0.0023 |  | 9.16% |
| same_query_retry_all_queries | 17 | same_full_context | 1765 |  | 0 | 0.6045 | 0.0068 | 0.0079 |  | 8.80% |
| calibration_to_test | 17 | budgeted_before_feedback | 1235 |  | 7 | 0.6008 | -0.0065 | 0.0000 |  | 9.03% |
| calibration_to_test | 17 | generalized_arm_boost | 1235 |  | 7 | 0.5960 | -0.0113 | -0.0049 |  | 9.11% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 1235 |  | 7 | 0.5976 | -0.0097 | -0.0032 |  | 8.66% |
| calibration_to_test | 17 | generalized_conservative_budget | 1235 |  | 7 | 0.6008 | -0.0065 | 0.0000 |  | 8.71% |
| calibration_to_test | 17 | generalized_full_context | 1235 |  | 7 | 0.6040 | -0.0032 | 0.0032 |  | 6.39% |
| same_query_retry | 19 | budgeted_before_feedback |  | 59 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 15.14% |
| same_query_retry | 19 | same_arm_boost |  | 59 |  | 0.0847 | 0.0000 | 0.0000 | 5 | 15.23% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 59 |  | 0.1017 | 0.0000 | 0.0000 | 6 | 13.23% |
| same_query_retry | 19 | same_full_context |  | 59 |  | 0.2712 | 0.0000 | 0.0000 | 16 | 3.16% |
| same_query_retry_compression_only | 19 | budgeted_before_feedback |  | 44 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 8.48% |
| same_query_retry_compression_only | 19 | same_arm_boost |  | 44 |  | 0.3636 | 0.0000 | 0.0000 | 16 | 8.21% |
| same_query_retry_compression_only | 19 | same_arm_boost_conservative |  | 44 |  | 0.3864 | 0.0000 | 0.0000 | 17 | 7.27% |
| same_query_retry_compression_only | 19 | same_full_context |  | 44 |  | 0.6364 | 0.0000 | 0.0000 | 28 | -0.57% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 1765 |  | 0 | 0.5949 | -0.0028 | 0.0000 |  | 8.79% |
| same_query_retry_all_queries | 19 | same_arm_boost | 1765 |  | 0 | 0.5977 | 0.0000 | 0.0028 |  | 8.79% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 1765 |  | 0 | 0.5983 | 0.0006 | 0.0034 |  | 8.72% |
| same_query_retry_all_queries | 19 | same_full_context | 1765 |  | 0 | 0.6040 | 0.0062 | 0.0091 |  | 8.36% |
| calibration_to_test | 19 | budgeted_before_feedback | 1235 |  | 12 | 0.6032 | -0.0040 | 0.0000 |  | 8.77% |
| calibration_to_test | 19 | generalized_arm_boost | 1235 |  | 12 | 0.6024 | -0.0049 | -0.0008 |  | 8.82% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 1235 |  | 12 | 0.6032 | -0.0040 | 0.0000 |  | 8.17% |
| calibration_to_test | 19 | generalized_conservative_budget | 1235 |  | 12 | 0.6032 | -0.0040 | 0.0000 |  | 8.11% |
| calibration_to_test | 19 | generalized_full_context | 1235 |  | 12 | 0.6081 | 0.0008 | 0.0049 |  | 4.62% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
