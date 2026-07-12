# Task70 Frozen-Policy Unseen-Query Evaluation

Each held-out query is ranked once after training on the other four canonical folds. During test evaluation, no held-out label can update LinUCB parameters, local feedback memory, route statistics, or reward history.

## Out-of-Fold Retrieval

| Method | Hit@10 | Delta vs Dense | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| learned_full_frozen | 0.8792 | +1.17 pp | 0.7174 | 0.7101 | 0.6537 |
| learned_gated_frozen | 0.8266 | -4.08 pp | 0.6207 | 0.6797 | 0.5853 |
| static_nearest_full | 0.8764 | +0.89 pp | 0.7115 | 0.7098 | 0.6520 |
| static_nearest_gated | 0.8674 | +0.00 pp | 0.6908 | 0.7089 | 0.6408 |
| cold_no_feedback_full | 0.8803 | +1.29 pp | 0.7186 | 0.7102 | 0.6535 |
| cold_no_feedback_gated | 0.8803 | +1.29 pp | 0.7186 | 0.7102 | 0.6535 |
| dense | 0.8674 | +0.00 pp | 0.7026 | 0.7081 | 0.6487 |

## Paired Frozen-Query Comparisons

Each row is paired by the same unseen query population within one route seed. Bootstrap intervals apply to query-level deltas; McNemar tests apply to paired Hit@10 outcomes.

| Method | Baseline | Seeds | Mean Hit delta | Seed SD | Significant McNemar seeds |
|---|---|---|---:|---:|---:|
| learned_full_frozen | cold_no_feedback_full | 13|17|19 | -0.11 pp | 0.21 pp | 0/3 |
| learned_full_frozen | dense | 13|17|19 | +1.17 pp | 0.63 pp | 1/3 |
| learned_full_frozen | static_nearest_full | 13|17|19 | +0.28 pp | 0.62 pp | 0/3 |
| learned_gated_frozen | cold_no_feedback_gated | 13|17|19 | -5.37 pp | 0.90 pp | 3/3 |
| learned_gated_frozen | dense | 13|17|19 | -4.08 pp | 1.06 pp | 3/3 |
| learned_gated_frozen | static_nearest_gated | 13|17|19 | -4.08 pp | 1.11 pp | 3/3 |

| Method | Baseline | Seed | Hit delta 95% CI | Wins / Losses | McNemar p |
|---|---|---:|---:|---:|---:|
| learned_full_frozen | dense | 13 | [-0.67, +2.68] pp | 16 / 10 | 0.3269 |
| learned_full_frozen | dense | 17 | [-1.17, +2.18] pp | 15 / 12 | 0.7011 |
| learned_full_frozen | dense | 19 | [+0.34, +3.69] pp | 19 / 7 | 0.02896 |
| learned_full_frozen | static_nearest_full | 13 | [-0.67, +1.34] pp | 6 / 4 | 0.7539 |
| learned_full_frozen | static_nearest_full | 17 | [-1.68, +0.50] pp | 4 / 7 | 0.5488 |
| learned_full_frozen | static_nearest_full | 19 | [+0.00, +2.18] pp | 9 / 3 | 0.146 |
| learned_full_frozen | cold_no_feedback_full | 13 | [-1.34, +1.01] pp | 6 / 7 | 1 |
| learned_full_frozen | cold_no_feedback_full | 17 | [-1.51, +0.84] pp | 5 / 7 | 0.7744 |
| learned_full_frozen | cold_no_feedback_full | 19 | [-1.01, +1.34] pp | 7 / 6 | 1 |
| learned_gated_frozen | dense | 13 | [-5.37, -0.83] pp | 15 / 33 | 0.01328 |
| learned_gated_frozen | dense | 17 | [-8.05, -3.02] pp | 12 / 45 | 1.313e-05 |
| learned_gated_frozen | dense | 19 | [-6.21, -1.34] pp | 17 / 39 | 0.004562 |
| learned_gated_frozen | static_nearest_gated | 13 | [-4.87, -1.01] pp | 9 / 26 | 0.005988 |
| learned_gated_frozen | static_nearest_gated | 17 | [-7.89, -3.35] pp | 10 / 43 | 5.551e-06 |
| learned_gated_frozen | static_nearest_gated | 19 | [-6.21, -1.68] pp | 12 / 35 | 0.001089 |
| learned_gated_frozen | cold_no_feedback_gated | 13 | [-6.54, -1.85] pp | 14 / 39 | 0.0008023 |
| learned_gated_frozen | cold_no_feedback_gated | 17 | [-8.72, -4.03] pp | 9 / 47 | 2.572e-07 |
| learned_gated_frozen | cold_no_feedback_gated | 19 | [-7.89, -3.36] pp | 8 / 41 | 1.965e-06 |

## Interpretation Guardrail

This evaluates route-policy transfer to unseen queries. It is distinct from repeated-query prequential adaptation and does not by itself establish final-context token savings, human-feedback effectiveness, or universal non-inferiority. Paired statistics compare retrieval outcomes only and do not turn a non-significant result into proof of equivalence.
