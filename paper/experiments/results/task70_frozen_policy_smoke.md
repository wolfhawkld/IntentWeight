# Task70 Frozen-Policy Unseen-Query Evaluation

Each held-out query is ranked once after training on the other four canonical folds. During test evaluation, no held-out label can update LinUCB parameters, local feedback memory, route statistics, or reward history.

## Out-of-Fold Retrieval

| Method | Hit@10 | Delta vs Dense | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| learned_full_frozen | 0.8826 | +1.51 pp | 0.7165 | 0.7105 | 0.6527 |
| learned_gated_frozen | 0.8221 | -4.53 pp | 0.6063 | 0.6767 | 0.5751 |
| static_nearest_full | 0.8742 | +0.67 pp | 0.7101 | 0.7096 | 0.6520 |
| static_nearest_gated | 0.8658 | -0.17 pp | 0.6924 | 0.7104 | 0.6429 |
| cold_no_feedback_full | 0.8792 | +1.17 pp | 0.7180 | 0.7099 | 0.6534 |
| cold_no_feedback_gated | 0.8792 | +1.17 pp | 0.7180 | 0.7099 | 0.6534 |
| dense | 0.8674 | +0.00 pp | 0.7026 | 0.7081 | 0.6487 |

## Interpretation Guardrail

This evaluates route-policy transfer to unseen queries. It is distinct from repeated-query prequential adaptation and does not by itself establish final-context token savings, human-feedback effectiveness, or universal non-inferiority.
