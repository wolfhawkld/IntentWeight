# Task65.3 Dynamic-Route Mediation and Evidence Survival

The experiment freezes the Task37 selected arms and confidence trajectory,
then replays alternative route shapes before applying the same `r0.95/m4`
final-context budget.

## Common Frozen Budget

| Variant | Hit@10 | Hit delta vs dense | Token saving vs dense |
|---|---:|---:|---:|
| dynamic_gated | 0.8705 | -0.00 pp | 6.18% |
| fixed_full | 0.8745 | +0.40 pp | 5.27% |
| fixed_cluster_primary | 0.7626 | -10.79 pp | 6.93% |
| shuffled_tiers | 0.8225 | -4.80 pp | 6.54% |
| dense | 0.8561 | -1.44 pp | 13.83% |

## Dynamic-Gating Mediation

Positive hit delta favors dynamic gating.

| Reference | Stage | Hit delta | CI excludes zero |
|---|---|---:|---:|
| fixed_full | source | -0.48 pp | 0/3 |
| fixed_full | budget_r0.95_m4 | -0.40 pp | 0/3 |
| shuffled_tiers | source | +4.80 pp | 3/3 |
| shuffled_tiers | budget_r0.95_m4 | +4.80 pp | 3/3 |
| fixed_cluster_primary | source | +10.95 pp | 3/3 |
| fixed_cluster_primary | budget_r0.95_m4 | +10.79 pp | 3/3 |

## Original Confidence-Tier Outcomes

Rows are grouped by the tier assigned by the original dynamic policy.

| Tier | Stage | Dynamic | Shuffled | Fixed full | Always cluster-primary |
|---|---|---:|---:|---:|---:|
| linucb_primary | source | 0.924 | 0.927 | 0.927 | 0.924 |
| linucb_primary | budget_r0.95_m4 | 0.913 | 0.916 | 0.916 | 0.913 |
| hybrid_lite | source | 0.850 | 0.803 | 0.858 | 0.748 |
| hybrid_lite | budget_r0.95_m4 | 0.843 | 0.795 | 0.850 | 0.744 |
| full_dense_fallback | source | 0.800 | 0.553 | 0.800 | 0.240 |
| full_dense_fallback | budget_r0.95_m4 | 0.794 | 0.553 | 0.794 | 0.240 |

## Evidence Survival

| Variant | Relevant chunks | First rank | Max safe saving | Safe at r0.85 |
|---|---:|---:|---:|---:|
| dynamic_gated | 2.121 | 1.845 | 53.05% | 0.976 |
| fixed_full | 2.315 | 1.935 | 55.39% | 0.977 |
| fixed_cluster_primary | 1.787 | 1.897 | 52.12% | 0.974 |
| shuffled_tiers | 2.056 | 1.894 | 53.50% | 0.976 |
| dense | 2.266 | 1.876 | 52.76% | 0.978 |

## Confidence Diagnostic

Route confidence versus oracle maximum safe saving is diagnostic only.
Mean Spearman rho across seeds: `-0.056`.

## Guardrail

A dynamic-route advantage would support confidence-mediated candidate-pool
construction. It would not establish route confidence as a direct predictor
of per-query compression safety.
