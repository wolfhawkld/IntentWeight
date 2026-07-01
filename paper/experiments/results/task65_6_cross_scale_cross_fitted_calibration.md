# Task65.6 Cross-Scale Cross-Fitted Calibration

Five balanced, disjoint folds use the same locked grid and selection rule at every scale.

## Out-of-Fold Results

| Scale | Eligible folds | IntentRoute Hit delta | IntentRoute saving | NI seeds | Dense Hit delta | Dense saving |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 2/5 | -1.06pp | 4.16% | 0/3 | +0.00pp | 0.00% |
| 200k | 5/5 | +1.40pp | 16.07% | 2/3 | +0.00pp | 0.00% |
| 400k | 5/5 | -0.00pp | 14.50% | 0/3 | +0.00pp | 0.00% |
| 638k | 5/5 | +0.28pp | 15.23% | 0/3 | +0.00pp | 0.00% |

## Fold Selections

| Scale | Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy | Dense saving |
|---|---:|---|---:|---:|---:|---|---:|
| 100k | 0 | `dense_top10_fallback` | False | +0.00pp | 0.00% | `dense_top10_fallback` | 0.00% |
| 100k | 1 | `dense_top10_fallback` | False | +0.00pp | 0.00% | `dense_top10_fallback` | 0.00% |
| 100k | 2 | `dense_top10_fallback` | False | +0.00pp | 0.00% | `dense_top10_fallback` | 0.00% |
| 100k | 3 | `token_budget_r0.92_m4` | True | -2.52pp | 12.05% | `dense_top10_fallback` | 0.00% |
| 100k | 4 | `token_budget_r0.92_m4` | True | -2.80pp | 8.92% | `dense_top10_fallback` | 0.00% |
| 200k | 0 | `token_budget_r0.85_m4` | True | +1.67pp | 19.11% | `dense_top10_fallback` | 0.00% |
| 200k | 1 | `token_budget_r0.85_m4` | True | +0.84pp | 13.03% | `dense_top10_fallback` | 0.00% |
| 200k | 2 | `token_budget_r0.85_m4` | True | +2.24pp | 15.63% | `dense_top10_fallback` | 0.00% |
| 200k | 3 | `token_budget_r0.85_m4` | True | -0.84pp | 17.00% | `dense_top10_fallback` | 0.00% |
| 200k | 4 | `token_budget_r0.85_m4` | True | +3.08pp | 15.26% | `dense_top10_fallback` | 0.00% |
| 400k | 0 | `token_budget_r0.95_m7` | True | +4.44pp | 10.53% | `dense_top10_fallback` | 0.00% |
| 400k | 1 | `token_budget_r0.85_m7` | True | -1.12pp | 16.32% | `dense_top10_fallback` | 0.00% |
| 400k | 2 | `token_budget_r0.85_m4` | True | -3.64pp | 20.18% | `dense_top10_fallback` | 0.00% |
| 400k | 3 | `token_budget_r0.85_m5` | True | -2.80pp | 16.52% | `dense_top10_fallback` | 0.00% |
| 400k | 4 | `token_budget_r0.92_m8` | True | +3.08pp | 8.83% | `dense_top10_fallback` | 0.00% |
| 638k | 0 | `token_budget_r0.85_m8` | True | +2.50pp | 17.29% | `dense_top10_fallback` | 0.00% |
| 638k | 1 | `token_budget_r0.85_m4` | True | -1.12pp | 14.60% | `dense_top10_fallback` | 0.00% |
| 638k | 2 | `token_budget_r0.85_m4` | True | -0.56pp | 17.74% | `dense_top10_fallback` | 0.00% |
| 638k | 3 | `token_budget_r0.85_m4` | True | -3.08pp | 14.99% | `dense_top10_fallback` | 0.00% |
| 638k | 4 | `token_budget_r0.90_m4` | True | +3.64pp | 10.91% | `dense_top10_fallback` | 0.00% |

## Guardrail

This post-hoc cross-fitted audit uses a normalized protocol across all scales. It does not erase the original 400k calibration failure or establish universal non-inferiority.
