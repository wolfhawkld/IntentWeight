# Task40 Feedback Recovery

- Dataset: `lotte_science_search_400k`
- Budget policy: `r0.88_m4`
- Conservative retry ratio: `0.95`
- Calibration queries: `179`
- Test queries: `417`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 6 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 32.02% |
| same_query_retry | 13 | same_arm_boost |  | 6 |  | 0.8333 | 0.0000 | 0.0000 | 5 | 28.60% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 6 |  | 0.8333 | 0.0000 | 0.0000 | 5 | 19.98% |
| same_query_retry | 13 | same_full_context |  | 6 |  | 0.8333 | 0.0000 | 0.0000 | 5 | 12.13% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 596 |  | 0 | 0.8154 | -0.0084 | 0.0000 |  | 3.08% |
| same_query_retry_all_queries | 13 | same_arm_boost | 596 |  | 0 | 0.8238 | 0.0000 | 0.0084 |  | 3.05% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 596 |  | 0 | 0.8238 | 0.0000 | 0.0084 |  | 2.98% |
| same_query_retry_all_queries | 13 | same_full_context | 596 |  | 0 | 0.8238 | 0.0000 | 0.0084 |  | 2.91% |
| calibration_to_test | 13 | budgeted_before_feedback | 417 |  | 3 | 0.8297 | -0.0048 | 0.0000 |  | 3.24% |
| calibration_to_test | 13 | generalized_arm_boost | 417 |  | 3 | 0.8369 | 0.0024 | 0.0072 |  | 4.99% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 417 |  | 3 | 0.8393 | 0.0048 | 0.0096 |  | 3.93% |
| calibration_to_test | 13 | generalized_conservative_budget | 417 |  | 3 | 0.8369 | 0.0024 | 0.0072 |  | 4.02% |
| calibration_to_test | 13 | generalized_full_context | 417 |  | 3 | 0.8393 | 0.0048 | 0.0096 |  | 1.48% |
| same_query_retry | 17 | budgeted_before_feedback |  | 3 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 10.09% |
| same_query_retry | 17 | same_arm_boost |  | 3 |  | 0.6667 | 0.0000 | 0.0000 | 2 | 4.63% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 3 |  | 0.6667 | 0.0000 | 0.0000 | 2 | -4.84% |
| same_query_retry | 17 | same_full_context |  | 3 |  | 0.6667 | 0.0000 | 0.0000 | 2 | -37.49% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 596 |  | 0 | 0.8205 | -0.0034 | 0.0000 |  | 2.95% |
| same_query_retry_all_queries | 17 | same_arm_boost | 596 |  | 0 | 0.8238 | 0.0000 | 0.0034 |  | 2.94% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 596 |  | 0 | 0.8238 | 0.0000 | 0.0034 |  | 2.91% |
| same_query_retry_all_queries | 17 | same_full_context | 596 |  | 0 | 0.8238 | 0.0000 | 0.0034 |  | 2.82% |
| calibration_to_test | 17 | budgeted_before_feedback | 417 |  | 3 | 0.8369 | 0.0024 | 0.0000 |  | 2.79% |
| calibration_to_test | 17 | generalized_arm_boost | 417 |  | 3 | 0.8393 | 0.0048 | 0.0024 |  | 3.88% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 417 |  | 3 | 0.8417 | 0.0072 | 0.0048 |  | 3.18% |
| calibration_to_test | 17 | generalized_conservative_budget | 417 |  | 3 | 0.8393 | 0.0048 | 0.0024 |  | 3.62% |
| calibration_to_test | 17 | generalized_full_context | 417 |  | 3 | 0.8441 | 0.0096 | 0.0072 |  | 1.73% |
| same_query_retry | 19 | budgeted_before_feedback |  | 5 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 6.08% |
| same_query_retry | 19 | same_arm_boost |  | 5 |  | 0.8000 | 0.0000 | 0.0000 | 4 | 12.02% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 5 |  | 0.8000 | 0.0000 | 0.0000 | 4 | 3.07% |
| same_query_retry | 19 | same_full_context |  | 5 |  | 0.8000 | 0.0000 | 0.0000 | 4 | -4.45% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 596 |  | 0 | 0.8154 | -0.0084 | 0.0000 |  | 3.42% |
| same_query_retry_all_queries | 19 | same_arm_boost | 596 |  | 0 | 0.8221 | -0.0017 | 0.0067 |  | 3.46% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 596 |  | 0 | 0.8221 | -0.0017 | 0.0067 |  | 3.39% |
| same_query_retry_all_queries | 19 | same_full_context | 596 |  | 0 | 0.8221 | -0.0017 | 0.0067 |  | 3.34% |
| calibration_to_test | 19 | budgeted_before_feedback | 417 |  | 1 | 0.8249 | -0.0096 | 0.0000 |  | 3.76% |
| calibration_to_test | 19 | generalized_arm_boost | 417 |  | 1 | 0.8297 | -0.0048 | 0.0048 |  | 4.51% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 417 |  | 1 | 0.8297 | -0.0048 | 0.0048 |  | 4.16% |
| calibration_to_test | 19 | generalized_conservative_budget | 417 |  | 1 | 0.8297 | -0.0048 | 0.0048 |  | 4.25% |
| calibration_to_test | 19 | generalized_full_context | 417 |  | 1 | 0.8297 | -0.0048 | 0.0048 |  | 3.22% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
