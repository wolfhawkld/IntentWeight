# Task40 Feedback Recovery

- Dataset: `covidqa`
- Budget policy: `r0.95_m4`
- Conservative retry ratio: `0.98`
- Calibration queries: `530`
- Test queries: `1235`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 56 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 12.20% |
| same_query_retry | 13 | same_arm_boost |  | 56 |  | 0.0714 | 0.0000 | 0.0000 | 4 | 11.65% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 56 |  | 0.0893 | 0.0000 | 0.0000 | 5 | 11.28% |
| same_query_retry | 13 | same_full_context |  | 56 |  | 0.3393 | 0.0000 | 0.0000 | 19 | -0.41% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 1765 |  | 0 | 0.5921 | -0.0040 | 0.0000 |  | 8.36% |
| same_query_retry_all_queries | 13 | same_arm_boost | 1765 |  | 0 | 0.5943 | -0.0017 | 0.0023 |  | 8.34% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 1765 |  | 0 | 0.5949 | -0.0011 | 0.0028 |  | 8.33% |
| same_query_retry_all_queries | 13 | same_full_context | 1765 |  | 0 | 0.6028 | 0.0068 | 0.0108 |  | 7.94% |
| calibration_to_test | 13 | budgeted_before_feedback | 1235 |  | 9 | 0.6000 | -0.0073 | 0.0000 |  | 8.33% |
| calibration_to_test | 13 | generalized_arm_boost | 1235 |  | 9 | 0.5984 | -0.0089 | -0.0016 |  | 8.85% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 1235 |  | 9 | 0.5976 | -0.0097 | -0.0024 |  | 8.66% |
| calibration_to_test | 13 | generalized_conservative_budget | 1235 |  | 9 | 0.6008 | -0.0065 | 0.0008 |  | 8.70% |
| calibration_to_test | 13 | generalized_full_context | 1235 |  | 9 | 0.6089 | 0.0016 | 0.0089 |  | 5.38% |
| same_query_retry | 17 | budgeted_before_feedback |  | 59 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 15.03% |
| same_query_retry | 17 | same_arm_boost |  | 59 |  | 0.1695 | 0.0000 | 0.0000 | 10 | 15.05% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 59 |  | 0.1864 | 0.0000 | 0.0000 | 11 | 14.40% |
| same_query_retry | 17 | same_full_context |  | 59 |  | 0.3390 | 0.0000 | 0.0000 | 20 | 2.98% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 1765 |  | 0 | 0.5932 | -0.0028 | 0.0000 |  | 8.57% |
| same_query_retry_all_queries | 17 | same_arm_boost | 1765 |  | 0 | 0.5989 | 0.0028 | 0.0057 |  | 8.57% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 1765 |  | 0 | 0.5994 | 0.0034 | 0.0062 |  | 8.55% |
| same_query_retry_all_queries | 17 | same_full_context | 1765 |  | 0 | 0.6045 | 0.0085 | 0.0113 |  | 8.14% |
| calibration_to_test | 17 | budgeted_before_feedback | 1235 |  | 8 | 0.6008 | -0.0065 | 0.0000 |  | 8.30% |
| calibration_to_test | 17 | generalized_arm_boost | 1235 |  | 8 | 0.6000 | -0.0073 | -0.0008 |  | 8.68% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 1235 |  | 8 | 0.6008 | -0.0065 | 0.0000 |  | 8.50% |
| calibration_to_test | 17 | generalized_conservative_budget | 1235 |  | 8 | 0.6032 | -0.0040 | 0.0024 |  | 8.55% |
| calibration_to_test | 17 | generalized_full_context | 1235 |  | 8 | 0.6097 | 0.0024 | 0.0089 |  | 4.82% |
| same_query_retry | 19 | budgeted_before_feedback |  | 61 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 16.22% |
| same_query_retry | 19 | same_arm_boost |  | 61 |  | 0.1148 | 0.0000 | 0.0000 | 7 | 14.91% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 61 |  | 0.1311 | 0.0000 | 0.0000 | 8 | 13.80% |
| same_query_retry | 19 | same_full_context |  | 61 |  | 0.2951 | 0.0000 | 0.0000 | 18 | 2.97% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 1765 |  | 0 | 0.5966 | 0.0006 | 0.0000 |  | 8.04% |
| same_query_retry_all_queries | 19 | same_arm_boost | 1765 |  | 0 | 0.6006 | 0.0045 | 0.0040 |  | 7.99% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 1765 |  | 0 | 0.6011 | 0.0051 | 0.0045 |  | 7.95% |
| same_query_retry_all_queries | 19 | same_full_context | 1765 |  | 0 | 0.6068 | 0.0108 | 0.0102 |  | 7.56% |
| calibration_to_test | 19 | budgeted_before_feedback | 1235 |  | 10 | 0.6016 | -0.0057 | 0.0000 |  | 8.07% |
| calibration_to_test | 19 | generalized_arm_boost | 1235 |  | 10 | 0.5976 | -0.0097 | -0.0040 |  | 8.74% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 1235 |  | 10 | 0.5992 | -0.0081 | -0.0024 |  | 8.55% |
| calibration_to_test | 19 | generalized_conservative_budget | 1235 |  | 10 | 0.6016 | -0.0057 | 0.0000 |  | 8.55% |
| calibration_to_test | 19 | generalized_full_context | 1235 |  | 10 | 0.6105 | 0.0032 | 0.0089 |  | 5.00% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
