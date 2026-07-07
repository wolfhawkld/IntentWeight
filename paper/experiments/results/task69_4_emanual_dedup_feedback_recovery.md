# Task40 Feedback Recovery

- Dataset: `emanual_deduplicated`
- Budget policy: `r0.85_m4`
- Conservative retry ratio: `0.95`
- Calibration queries: `40`
- Test queries: `92`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 15 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 91.68% |
| same_query_retry | 13 | same_arm_boost |  | 15 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 91.72% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 15 |  | 0.1333 | 0.0000 | 0.0000 | 2 | 90.86% |
| same_query_retry | 13 | same_full_context |  | 15 |  | 0.1333 | 0.0000 | 0.0000 | 2 | 89.46% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 132 |  | 0 | 0.8485 | -0.1136 | 0.0000 |  | 91.33% |
| same_query_retry_all_queries | 13 | same_arm_boost | 132 |  | 0 | 0.8485 | -0.1136 | 0.0000 |  | 91.34% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 132 |  | 0 | 0.8636 | -0.0985 | 0.0152 |  | 91.23% |
| same_query_retry_all_queries | 13 | same_full_context | 132 |  | 0 | 0.8636 | -0.0985 | 0.0152 |  | 91.06% |
| calibration_to_test | 13 | budgeted_before_feedback | 92 |  | 4 | 0.8478 | -0.1196 | 0.0000 |  | 91.27% |
| calibration_to_test | 13 | generalized_arm_boost | 92 |  | 4 | 0.8478 | -0.1196 | 0.0000 |  | 91.27% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 92 |  | 4 | 0.8478 | -0.1196 | 0.0000 |  | 91.13% |
| calibration_to_test | 13 | generalized_conservative_budget | 92 |  | 4 | 0.8478 | -0.1196 | 0.0000 |  | 91.13% |
| calibration_to_test | 13 | generalized_full_context | 92 |  | 4 | 0.8478 | -0.1196 | 0.0000 |  | 90.96% |
| same_query_retry | 17 | budgeted_before_feedback |  | 15 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 92.38% |
| same_query_retry | 17 | same_arm_boost |  | 15 |  | 0.1333 | 0.0000 | 0.0000 | 2 | 92.04% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 15 |  | 0.2000 | 0.0000 | 0.0000 | 3 | 91.17% |
| same_query_retry | 17 | same_full_context |  | 15 |  | 0.2667 | 0.0000 | 0.0000 | 4 | 90.22% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 132 |  | 0 | 0.8485 | -0.1136 | 0.0000 |  | 91.76% |
| same_query_retry_all_queries | 17 | same_arm_boost | 132 |  | 0 | 0.8636 | -0.0985 | 0.0152 |  | 91.72% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 132 |  | 0 | 0.8712 | -0.0909 | 0.0227 |  | 91.62% |
| same_query_retry_all_queries | 17 | same_full_context | 132 |  | 0 | 0.8788 | -0.0833 | 0.0303 |  | 91.50% |
| calibration_to_test | 17 | budgeted_before_feedback | 92 |  | 5 | 0.8587 | -0.1087 | 0.0000 |  | 91.70% |
| calibration_to_test | 17 | generalized_arm_boost | 92 |  | 5 | 0.8696 | -0.0978 | 0.0109 |  | 91.67% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 92 |  | 5 | 0.8696 | -0.0978 | 0.0109 |  | 91.59% |
| calibration_to_test | 17 | generalized_conservative_budget | 92 |  | 5 | 0.8696 | -0.0978 | 0.0109 |  | 91.61% |
| calibration_to_test | 17 | generalized_full_context | 92 |  | 5 | 0.8804 | -0.0870 | 0.0217 |  | 91.43% |
| same_query_retry | 19 | budgeted_before_feedback |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 92.47% |
| same_query_retry | 19 | same_arm_boost |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 92.48% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 16 |  | 0.1250 | 0.0000 | 0.0000 | 2 | 91.95% |
| same_query_retry | 19 | same_full_context |  | 16 |  | 0.2500 | 0.0000 | 0.0000 | 4 | 90.76% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 132 |  | 0 | 0.8409 | -0.1212 | 0.0000 |  | 91.77% |
| same_query_retry_all_queries | 19 | same_arm_boost | 132 |  | 0 | 0.8409 | -0.1212 | 0.0000 |  | 91.77% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 132 |  | 0 | 0.8561 | -0.1061 | 0.0152 |  | 91.70% |
| same_query_retry_all_queries | 19 | same_full_context | 132 |  | 0 | 0.8712 | -0.0909 | 0.0303 |  | 91.55% |
| calibration_to_test | 19 | budgeted_before_feedback | 92 |  | 5 | 0.8587 | -0.1087 | 0.0000 |  | 91.68% |
| calibration_to_test | 19 | generalized_arm_boost | 92 |  | 5 | 0.8587 | -0.1087 | 0.0000 |  | 91.68% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 92 |  | 5 | 0.8696 | -0.0978 | 0.0109 |  | 91.53% |
| calibration_to_test | 19 | generalized_conservative_budget | 92 |  | 5 | 0.8696 | -0.0978 | 0.0109 |  | 91.52% |
| calibration_to_test | 19 | generalized_full_context | 92 |  | 5 | 0.8804 | -0.0870 | 0.0217 |  | 91.13% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
