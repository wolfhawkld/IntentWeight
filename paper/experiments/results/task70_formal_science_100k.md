# Task70 Frozen-Policy Unseen-Query Evaluation

Each held-out query is ranked once after training on the other four canonical folds. During test evaluation, no held-out label can update LinUCB parameters, local feedback memory, route statistics, or reward history.

## Out-of-Fold Retrieval

| Method | Hit@10 | Delta vs Dense | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| learned_full_frozen | 0.9004 | +0.78 pp | 0.7410 | 0.7369 | 0.6716 |
| learned_gated_frozen | 0.8367 | -5.59 pp | 0.6380 | 0.6925 | 0.5967 |
| static_nearest_full | 0.9060 | +1.34 pp | 0.7455 | 0.7376 | 0.6731 |
| static_nearest_gated | 0.8921 | -0.06 pp | 0.7236 | 0.7358 | 0.6617 |
| cold_no_feedback_full | 0.9044 | +1.17 pp | 0.7460 | 0.7375 | 0.6735 |
| cold_no_feedback_gated | 0.9044 | +1.17 pp | 0.7460 | 0.7375 | 0.6735 |
| dense | 0.8926 | +0.00 pp | 0.7328 | 0.7354 | 0.6683 |

## Paired Frozen-Query Comparisons

Each row is paired by the same unseen query population within one route seed. Bootstrap intervals apply to query-level deltas; McNemar tests apply to paired Hit@10 outcomes.

| Method | Baseline | Seeds | Mean Hit delta | Seed SD | Significant McNemar seeds |
|---|---|---|---:|---:|---:|
| learned_full_frozen | cold_no_feedback_full | 13|17|19 | -0.39 pp | 0.55 pp | 0/3 |
| learned_full_frozen | dense | 13|17|19 | +0.78 pp | 0.29 pp | 0/3 |
| learned_full_frozen | static_nearest_full | 13|17|19 | -0.56 pp | 0.32 pp | 0/3 |
| learned_gated_frozen | cold_no_feedback_gated | 13|17|19 | -6.77 pp | 2.06 pp | 3/3 |
| learned_gated_frozen | dense | 13|17|19 | -5.59 pp | 1.96 pp | 3/3 |
| learned_gated_frozen | static_nearest_gated | 13|17|19 | -5.54 pp | 1.98 pp | 3/3 |

| Method | Baseline | Seed | Hit delta 95% CI | Wins / Losses | McNemar p |
|---|---|---:|---:|---:|---:|
| learned_full_frozen | dense | 13 | [-1.01, +2.01] pp | 12 / 9 | 0.6636 |
| learned_full_frozen | dense | 17 | [-0.34, +2.85] pp | 15 / 8 | 0.21 |
| learned_full_frozen | dense | 19 | [-1.01, +2.35] pp | 14 / 10 | 0.5413 |
| learned_full_frozen | static_nearest_full | 13 | [-2.01, +0.00] pp | 2 / 8 | 0.1094 |
| learned_full_frozen | static_nearest_full | 17 | [-1.34, +0.67] pp | 4 / 6 | 0.7539 |
| learned_full_frozen | static_nearest_full | 19 | [-1.51, +0.84] pp | 5 / 7 | 0.7744 |
| learned_full_frozen | cold_no_feedback_full | 13 | [-2.35, +0.34] pp | 5 / 11 | 0.2101 |
| learned_full_frozen | cold_no_feedback_full | 17 | [-0.84, +1.51] pp | 8 / 6 | 0.7905 |
| learned_full_frozen | cold_no_feedback_full | 19 | [-2.01, +1.01] pp | 9 / 12 | 0.6636 |
| learned_gated_frozen | dense | 13 | [-7.55, -2.68] pp | 13 / 43 | 7.333e-05 |
| learned_gated_frozen | dense | 17 | [-5.87, -1.17] pp | 15 / 36 | 0.004601 |
| learned_gated_frozen | dense | 19 | [-10.91, -5.70] pp | 11 / 60 | 2.633e-09 |
| learned_gated_frozen | static_nearest_gated | 13 | [-7.05, -2.68] pp | 9 / 38 | 2.49e-05 |
| learned_gated_frozen | static_nearest_gated | 17 | [-5.70, -1.34] pp | 11 / 32 | 0.001914 |
| learned_gated_frozen | static_nearest_gated | 19 | [-10.74, -5.70] pp | 7 / 56 | 1.364e-10 |
| learned_gated_frozen | cold_no_feedback_gated | 13 | [-8.89, -4.19] pp | 8 / 47 | 8.068e-08 |
| learned_gated_frozen | cold_no_feedback_gated | 17 | [-6.71, -2.01] pp | 12 / 38 | 0.0003059 |
| learned_gated_frozen | cold_no_feedback_gated | 19 | [-12.08, -6.71] pp | 9 / 65 | 1.351e-11 |

## Interpretation Guardrail

This evaluates route-policy transfer to unseen queries. It is distinct from repeated-query prequential adaptation and does not by itself establish final-context token savings, human-feedback effectiveness, or universal non-inferiority. Paired statistics compare retrieval outcomes only and do not turn a non-significant result into proof of equivalence.
