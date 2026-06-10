# Task40 Feedback Recovery

- Dataset: `lotte_science_search_100k`
- Budget policy: `r0.85_m4`
- Conservative retry ratio: `0.95`
- Calibration queries: `179`
- Test queries: `417`

## Results

| protocol | seed | method | queries | affected | learned arms | hit | delta vs dense | delta vs before | recovered | token saving |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| same_query_retry | 13 | budgeted_before_feedback |  | 14 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 16.55% |
| same_query_retry | 13 | same_arm_boost |  | 14 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 16.45% |
| same_query_retry | 13 | same_arm_boost_conservative |  | 14 |  | 0.3571 | 0.0000 | 0.0000 | 5 | 3.45% |
| same_query_retry | 13 | same_full_context |  | 14 |  | 0.4286 | 0.0000 | 0.0000 | 6 | -7.35% |
| same_query_retry_all_queries | 13 | budgeted_before_feedback | 596 |  | 0 | 0.8859 | -0.0067 | 0.0000 |  | 18.72% |
| same_query_retry_all_queries | 13 | same_arm_boost | 596 |  | 0 | 0.8859 | -0.0067 | 0.0000 |  | 18.72% |
| same_query_retry_all_queries | 13 | same_arm_boost_conservative | 596 |  | 0 | 0.8943 | 0.0017 | 0.0084 |  | 18.41% |
| same_query_retry_all_queries | 13 | same_full_context | 596 |  | 0 | 0.8960 | 0.0034 | 0.0101 |  | 18.16% |
| calibration_to_test | 13 | budgeted_before_feedback | 417 |  | 3 | 0.8873 | -0.0072 | 0.0000 |  | 18.76% |
| calibration_to_test | 13 | generalized_arm_boost | 417 |  | 3 | 0.8825 | -0.0120 | -0.0048 |  | 18.65% |
| calibration_to_test | 13 | generalized_arm_boost_conservative | 417 |  | 3 | 0.8873 | -0.0072 | 0.0000 |  | 15.90% |
| calibration_to_test | 13 | generalized_conservative_budget | 417 |  | 3 | 0.8873 | -0.0072 | 0.0000 |  | 15.65% |
| calibration_to_test | 13 | generalized_full_context | 417 |  | 3 | 0.8897 | -0.0048 | 0.0024 |  | 12.62% |
| same_query_retry | 17 | budgeted_before_feedback |  | 8 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 13.19% |
| same_query_retry | 17 | same_arm_boost |  | 8 |  | 0.2500 | 0.0000 | 0.0000 | 2 | 14.27% |
| same_query_retry | 17 | same_arm_boost_conservative |  | 8 |  | 0.5000 | 0.0000 | 0.0000 | 4 | -0.38% |
| same_query_retry | 17 | same_full_context |  | 8 |  | 0.6250 | 0.0000 | 0.0000 | 5 | -10.72% |
| same_query_retry_all_queries | 17 | budgeted_before_feedback | 596 |  | 0 | 0.8977 | 0.0050 | 0.0000 |  | 16.97% |
| same_query_retry_all_queries | 17 | same_arm_boost | 596 |  | 0 | 0.9010 | 0.0084 | 0.0034 |  | 16.98% |
| same_query_retry_all_queries | 17 | same_arm_boost_conservative | 596 |  | 0 | 0.9044 | 0.0117 | 0.0067 |  | 16.80% |
| same_query_retry_all_queries | 17 | same_full_context | 596 |  | 0 | 0.9060 | 0.0134 | 0.0084 |  | 16.66% |
| calibration_to_test | 17 | budgeted_before_feedback | 417 |  | 1 | 0.8969 | 0.0024 | 0.0000 |  | 17.41% |
| calibration_to_test | 17 | generalized_arm_boost | 417 |  | 1 | 0.8873 | -0.0072 | -0.0096 |  | 18.24% |
| calibration_to_test | 17 | generalized_arm_boost_conservative | 417 |  | 1 | 0.8993 | 0.0048 | 0.0024 |  | 15.83% |
| calibration_to_test | 17 | generalized_conservative_budget | 417 |  | 1 | 0.8993 | 0.0048 | 0.0024 |  | 15.13% |
| calibration_to_test | 17 | generalized_full_context | 417 |  | 1 | 0.9065 | 0.0120 | 0.0096 |  | 11.31% |
| same_query_retry | 19 | budgeted_before_feedback |  | 12 |  | 0.0000 | 0.0000 | 0.0000 | 0 | 14.20% |
| same_query_retry | 19 | same_arm_boost |  | 12 |  | 0.2500 | 0.0000 | 0.0000 | 3 | 21.49% |
| same_query_retry | 19 | same_arm_boost_conservative |  | 12 |  | 0.4167 | 0.0000 | 0.0000 | 5 | 14.19% |
| same_query_retry | 19 | same_full_context |  | 12 |  | 0.5000 | 0.0000 | 0.0000 | 6 | -6.15% |
| same_query_retry_all_queries | 19 | budgeted_before_feedback | 596 |  | 0 | 0.8909 | -0.0017 | 0.0000 |  | 19.57% |
| same_query_retry_all_queries | 19 | same_arm_boost | 596 |  | 0 | 0.8960 | 0.0034 | 0.0050 |  | 19.69% |
| same_query_retry_all_queries | 19 | same_arm_boost_conservative | 596 |  | 0 | 0.8993 | 0.0067 | 0.0084 |  | 19.57% |
| same_query_retry_all_queries | 19 | same_full_context | 596 |  | 0 | 0.9010 | 0.0084 | 0.0101 |  | 19.25% |
| calibration_to_test | 19 | budgeted_before_feedback | 417 |  | 3 | 0.8921 | -0.0024 | 0.0000 |  | 19.37% |
| calibration_to_test | 19 | generalized_arm_boost | 417 |  | 3 | 0.8849 | -0.0096 | -0.0072 |  | 19.51% |
| calibration_to_test | 19 | generalized_arm_boost_conservative | 417 |  | 3 | 0.8897 | -0.0048 | -0.0024 |  | 17.84% |
| calibration_to_test | 19 | generalized_conservative_budget | 417 |  | 3 | 0.8945 | 0.0000 | 0.0024 |  | 17.59% |
| calibration_to_test | 19 | generalized_full_context | 417 |  | 3 | 0.8945 | 0.0000 | 0.0024 |  | 15.33% |

## Interpretation

- Same-query retry uses simulated corrective feedback after an observed failure; it is engineering recovery evidence, not IID first-pass evaluation.
- Generalization learns only from calibration affected queries and freezes the arm-boost map before evaluating test queries.
- Positive feedback is represented at the KMeans evidence-arm level, not by directly inserting a known GT chunk.
