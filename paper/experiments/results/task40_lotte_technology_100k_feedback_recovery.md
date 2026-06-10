# Task40 Feedback Recovery

- Dataset: `lotte_technology_search_100k`
- Budget policy: `r0.95_m4`
- Conservative retry ratio: `0.98`
- Calibration queries: `179`
- Test queries: `417`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 15 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 13.83% |
| same_query_retry | 13 | same_arm_boost |  | 15 |  | 0.1333 | 0.0000 | 0.0000 | 2 | 9.60% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 15 |  | 0.1333 | 0.0000 | 0.0000 | 2 | 6.71% |
| same_query_retry | 13 | same_full_context |  | 15 |  | 0.2667 | 0.0000 | 0.0000 | 4 | -4.03% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 596 |  | 0 | 0.8658 | -0.0017 | 0.0000 |  | 7.92% |
| same_query_retry_all_queries | 13 | same_arm_boost | 596 |  | 0 | 0.8691 | 0.0017 | 0.0034 |  | 7.84% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 596 |  | 0 | 0.8691 | 0.0017 | 0.0034 |  | 7.79% |
| same_query_retry_all_queries | 13 | same_full_context | 596 |  | 0 | 0.8725 | 0.0050 | 0.0067 |  | 7.61% |
| calibration_to_test | 13 | budgeted_before_feedback | 417 |  | 4 | 0.8681 | -0.0024 | 0.0000 |  | 6.43% |
| calibration_to_test | 13 | generalized_arm_boost | 417 |  | 4 | 0.8657 | -0.0048 | -0.0024 |  | 6.21% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 417 |  | 4 | 0.8681 | -0.0024 | 0.0000 |  | 5.72% |
| calibration_to_test | 13 | generalized_conservative_budget | 417 |  | 4 | 0.8657 | -0.0048 | -0.0024 |  | 6.03% |
| calibration_to_test | 13 | generalized_full_context | 417 |  | 4 | 0.8705 | 0.0000 | 0.0024 |  | 4.21% |
| same_query_retry | 17 | budgeted_before_feedback |  | 12 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 17.31% |
| same_query_retry | 17 | same_arm_boost |  | 12 |  | 0.2500 | 0.0000 | 0.0000 | 3 | 16.34% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 12 |  | 0.3333 | 0.0000 | 0.0000 | 4 | 14.69% |
| same_query_retry | 17 | same_full_context |  | 12 |  | 0.4167 | 0.0000 | 0.0000 | 5 | 2.75% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 596 |  | 0 | 0.8641 | -0.0034 | 0.0000 |  | 8.37% |
| same_query_retry_all_queries | 17 | same_arm_boost | 596 |  | 0 | 0.8691 | 0.0017 | 0.0050 |  | 8.36% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 596 |  | 0 | 0.8708 | 0.0034 | 0.0067 |  | 8.33% |
| same_query_retry_all_queries | 17 | same_full_context | 596 |  | 0 | 0.8725 | 0.0050 | 0.0084 |  | 8.13% |
| calibration_to_test | 17 | budgeted_before_feedback | 417 |  | 3 | 0.8657 | -0.0048 | 0.0000 |  | 7.14% |
| calibration_to_test | 17 | generalized_arm_boost | 417 |  | 3 | 0.8657 | -0.0048 | 0.0000 |  | 7.24% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 417 |  | 3 | 0.8681 | -0.0024 | 0.0024 |  | 6.37% |
| calibration_to_test | 17 | generalized_conservative_budget | 417 |  | 3 | 0.8657 | -0.0048 | 0.0000 |  | 6.71% |
| calibration_to_test | 17 | generalized_full_context | 417 |  | 3 | 0.8681 | -0.0024 | 0.0024 |  | 4.12% |
| same_query_retry | 19 | budgeted_before_feedback |  | 15 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 19.06% |
| same_query_retry | 19 | same_arm_boost |  | 15 |  | 0.2000 | 0.0000 | 0.0000 | 3 | 15.08% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 15 |  | 0.2000 | 0.0000 | 0.0000 | 3 | 13.87% |
| same_query_retry | 19 | same_full_context |  | 15 |  | 0.2000 | 0.0000 | 0.0000 | 3 | 4.17% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 596 |  | 0 | 0.8742 | 0.0067 | 0.0000 |  | 6.89% |
| same_query_retry_all_queries | 19 | same_arm_boost | 596 |  | 0 | 0.8792 | 0.0117 | 0.0050 |  | 6.81% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 596 |  | 0 | 0.8792 | 0.0117 | 0.0050 |  | 6.79% |
| same_query_retry_all_queries | 19 | same_full_context | 596 |  | 0 | 0.8792 | 0.0117 | 0.0050 |  | 6.59% |
| calibration_to_test | 19 | budgeted_before_feedback | 417 |  | 3 | 0.8777 | 0.0072 | 0.0000 |  | 4.98% |
| calibration_to_test | 19 | generalized_arm_boost | 417 |  | 3 | 0.8777 | 0.0072 | 0.0000 |  | 5.01% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 417 |  | 3 | 0.8777 | 0.0072 | 0.0000 |  | 4.91% |
| calibration_to_test | 19 | generalized_conservative_budget | 417 |  | 3 | 0.8753 | 0.0048 | -0.0024 |  | 4.90% |
| calibration_to_test | 19 | generalized_full_context | 417 |  | 3 | 0.8777 | 0.0072 | 0.0000 |  | 4.43% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
