# Task40 Feedback Recovery

- Dataset: `lotte_recreation_search_100k`
- Budget policy: cross-fitted selections from `paper/experiments/results/task73_recreation_100k_none_cross_fitted_budget.json`
- Conservative retry ratio: `0.98`
- Calibration queries: `277`
- Test queries: `647`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 17 |  | 0.0000 | 0.0000 | 0.0000 | 0 | -6.24% |
| same_query_retry | 13 | same_arm_boost |  | 17 |  | 0.1176 | 0.0000 | 0.0000 | 2 | -13.57% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 17 |  | 0.1176 | 0.0000 | 0.0000 | 2 | -16.35% |
| same_query_retry | 13 | same_full_context |  | 17 |  | 0.1176 | 0.0000 | 0.0000 | 2 | -29.76% |
| same_query_retry_compression_only | 13 | budgeted_before_feedback |  | 13 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 5.45% |
| same_query_retry_compression_only | 13 | same_arm_boost |  | 13 |  | 0.3077 | 0.0000 | 0.0000 | 4 | -1.77% |
| same_query_retry_compression_only | 13 | same_arm_boost_conservative |  | 13 |  | 0.3077 | 0.0000 | 0.0000 | 4 | -3.67% |
| same_query_retry_compression_only | 13 | same_full_context |  | 13 |  | 0.3846 | 0.0000 | 0.0000 | 5 | -6.03% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 924 |  | 0 | 0.8398 | -0.0097 | 0.0000 |  | 4.88% |
| same_query_retry_all_queries | 13 | same_arm_boost | 924 |  | 0 | 0.8420 | -0.0076 | 0.0022 |  | 4.78% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 924 |  | 0 | 0.8420 | -0.0076 | 0.0022 |  | 4.74% |
| same_query_retry_all_queries | 13 | same_full_context | 924 |  | 0 | 0.8420 | -0.0076 | 0.0022 |  | 4.54% |
| calibration_to_test | 13 | budgeted_before_feedback | 647 |  | 5 | 0.8377 | -0.0077 | 0.0000 |  | 5.26% |
| calibration_to_test | 13 | generalized_arm_boost | 647 |  | 5 | 0.8377 | -0.0077 | 0.0000 |  | 5.34% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 647 |  | 5 | 0.8377 | -0.0077 | 0.0000 |  | 4.69% |
| calibration_to_test | 13 | generalized_conservative_budget | 647 |  | 5 | 0.8377 | -0.0077 | 0.0000 |  | 4.59% |
| calibration_to_test | 13 | generalized_full_context | 647 |  | 5 | 0.8377 | -0.0077 | 0.0000 |  | 3.56% |
| same_query_retry | 17 | budgeted_before_feedback |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 6.12% |
| same_query_retry | 17 | same_arm_boost |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 3.96% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 2.24% |
| same_query_retry | 17 | same_full_context |  | 16 |  | 0.0000 | 0.0000 | 0.0000 | 0 | -16.45% |
| same_query_retry_compression_only | 17 | budgeted_before_feedback |  | 13 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 3.48% |
| same_query_retry_compression_only | 17 | same_arm_boost |  | 13 |  | 0.2308 | 0.0000 | 0.0000 | 3 | 1.37% |
| same_query_retry_compression_only | 17 | same_arm_boost_conservative |  | 13 |  | 0.2308 | 0.0000 | 0.0000 | 3 | 0.90% |
| same_query_retry_compression_only | 17 | same_full_context |  | 13 |  | 0.3846 | 0.0000 | 0.0000 | 5 | -7.68% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 924 |  | 0 | 0.8463 | -0.0032 | 0.0000 |  | 5.29% |
| same_query_retry_all_queries | 17 | same_arm_boost | 924 |  | 0 | 0.8463 | -0.0032 | 0.0000 |  | 5.26% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 924 |  | 0 | 0.8463 | -0.0032 | 0.0000 |  | 5.24% |
| same_query_retry_all_queries | 17 | same_full_context | 924 |  | 0 | 0.8463 | -0.0032 | 0.0000 |  | 5.00% |
| calibration_to_test | 17 | budgeted_before_feedback | 647 |  | 4 | 0.8423 | -0.0031 | 0.0000 |  | 6.33% |
| calibration_to_test | 17 | generalized_arm_boost | 647 |  | 4 | 0.8423 | -0.0031 | 0.0000 |  | 6.33% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 647 |  | 4 | 0.8423 | -0.0031 | 0.0000 |  | 6.06% |
| calibration_to_test | 17 | generalized_conservative_budget | 647 |  | 4 | 0.8423 | -0.0031 | 0.0000 |  | 6.05% |
| calibration_to_test | 17 | generalized_full_context | 647 |  | 4 | 0.8439 | -0.0015 | 0.0015 |  | 4.85% |
| same_query_retry | 19 | budgeted_before_feedback |  | 17 |  | 0.0000 | 0.0000 | 0.0000 | 0 | -1.35% |
| same_query_retry | 19 | same_arm_boost |  | 17 |  | 0.1176 | 0.0000 | 0.0000 | 2 | -6.44% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 17 |  | 0.1176 | 0.0000 | 0.0000 | 2 | -8.53% |
| same_query_retry | 19 | same_full_context |  | 17 |  | 0.1176 | 0.0000 | 0.0000 | 2 | -21.28% |
| same_query_retry_compression_only | 19 | budgeted_before_feedback |  | 14 |  | 0.0000 | 0.0000 | 0.0000 | 0 | -0.17% |
| same_query_retry_compression_only | 19 | same_arm_boost |  | 14 |  | 0.3571 | 0.0000 | 0.0000 | 5 | -0.26% |
| same_query_retry_compression_only | 19 | same_arm_boost_conservative |  | 14 |  | 0.3571 | 0.0000 | 0.0000 | 5 | -0.67% |
| same_query_retry_compression_only | 19 | same_full_context |  | 14 |  | 0.3571 | 0.0000 | 0.0000 | 5 | -4.74% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 924 |  | 0 | 0.8398 | -0.0097 | 0.0000 |  | 6.08% |
| same_query_retry_all_queries | 19 | same_arm_boost | 924 |  | 0 | 0.8420 | -0.0076 | 0.0022 |  | 6.01% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 924 |  | 0 | 0.8420 | -0.0076 | 0.0022 |  | 5.98% |
| same_query_retry_all_queries | 19 | same_full_context | 924 |  | 0 | 0.8420 | -0.0076 | 0.0022 |  | 5.81% |
| calibration_to_test | 19 | budgeted_before_feedback | 647 |  | 4 | 0.8362 | -0.0093 | 0.0000 |  | 6.41% |
| calibration_to_test | 19 | generalized_arm_boost | 647 |  | 4 | 0.8362 | -0.0093 | 0.0000 |  | 6.38% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 647 |  | 4 | 0.8362 | -0.0093 | 0.0000 |  | 6.25% |
| calibration_to_test | 19 | generalized_conservative_budget | 647 |  | 4 | 0.8362 | -0.0093 | 0.0000 |  | 6.30% |
| calibration_to_test | 19 | generalized_full_context | 647 |  | 4 | 0.8362 | -0.0093 | 0.0000 |  | 5.63% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
