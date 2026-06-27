# Task65.2 Fixed-Pool Factorial Safe-Compression Attribution

All five treatments use the same dense top-10 candidate pool, split,
token-budget grid, and seeds. Route signals only select which queries
receive compression.

## Same Quality Constraint

| Selector | Calibration margin | Test hit delta | Test token saving |
|---|---:|---:|---:|
| geometry_feedback | 0 pp | -0.40 pp | 5.32% |
| geometry_no_feedback | 0 pp | -1.76 pp | 5.66% |
| random_feedback | 0 pp | -0.64 pp | 8.32% |
| random_no_feedback | 0 pp | -1.04 pp | 9.48% |
| dense_budget_only | 0 pp | -1.92 pp | 22.89% |
| geometry_feedback | 1 pp | -1.92 pp | 21.41% |
| geometry_no_feedback | 1 pp | -1.92 pp | 20.35% |
| random_feedback | 1 pp | -1.68 pp | 21.55% |
| random_no_feedback | 1 pp | -1.84 pp | 19.77% |
| dense_budget_only | 1 pp | -1.92 pp | 22.89% |

## Same Token-Saving Target

| Selector | Target | Test hit delta | Test token saving |
|---|---:|---:|---:|
| geometry_feedback | 5% | -0.24 pp | 4.00% |
| geometry_no_feedback | 5% | -0.96 pp | 5.00% |
| random_feedback | 5% | -0.32 pp | 5.15% |
| random_no_feedback | 5% | -0.32 pp | 3.61% |
| dense_budget_only | 5% | -0.96 pp | 10.05% |
| geometry_feedback | 10% | -0.96 pp | 9.51% |
| geometry_no_feedback | 10% | -2.48 pp | 10.14% |
| random_feedback | 10% | -1.04 pp | 10.59% |
| random_no_feedback | 10% | -1.04 pp | 8.98% |
| dense_budget_only | 10% | -0.96 pp | 10.05% |
| geometry_feedback | 15% | -1.92 pp | 13.80% |
| geometry_no_feedback | 15% | -2.32 pp | 13.72% |
| random_feedback | 15% | -1.44 pp | 14.24% |
| random_no_feedback | 15% | -1.52 pp | 13.02% |
| dense_budget_only | 15% | -1.20 pp | 12.33% |
| geometry_feedback | 20% | -1.68 pp | 18.33% |
| geometry_no_feedback | 20% | -1.44 pp | 17.54% |
| random_feedback | 20% | -1.68 pp | 17.94% |
| random_no_feedback | 20% | -1.60 pp | 16.61% |
| dense_budget_only | 20% | -1.92 pp | 17.89% |

## Fixed-Action Failure Prediction

The fixed action is `token_budget_r0.85_m4`; higher scores predict safe
compression. Metrics are held-out means across seeds.

| Selector | AUROC | AUPRC | Isotonic Brier | Isotonic ECE |
|---|---:|---:|---:|---:|
| geometry_feedback | 0.434 | 0.975 | 0.022 | 0.013 |
| geometry_no_feedback | 0.201 | 0.956 | 0.023 | 0.013 |
| random_feedback | 0.573 | 0.983 | 0.022 | 0.012 |
| random_no_feedback | 0.381 | 0.968 | 0.022 | 0.012 |
| dense_budget_only | 0.500 | 0.978 | 0.022 | 0.009 |

## Pairwise Effects At Matched Saving Targets

Positive hit delta favors the method named before `vs`; values are
means across seeds. Per-seed bootstrap intervals are in the CSV artifact.

| Contrast | Target | Hit delta | Method saving | Reference saving |
|---|---:|---:|---:|---:|
| geometry_feedback vs geometry_no_feedback | 5% | +0.72 pp | 4.00% | 5.00% |
| geometry_feedback vs geometry_no_feedback | 10% | +1.52 pp | 9.51% | 10.14% |
| geometry_feedback vs geometry_no_feedback | 15% | +0.40 pp | 13.80% | 13.72% |
| geometry_feedback vs geometry_no_feedback | 20% | -0.24 pp | 18.33% | 17.54% |
| geometry_feedback vs random_feedback | 5% | +0.08 pp | 4.00% | 5.15% |
| geometry_feedback vs random_feedback | 10% | +0.08 pp | 9.51% | 10.59% |
| geometry_feedback vs random_feedback | 15% | -0.48 pp | 13.80% | 14.24% |
| geometry_feedback vs random_feedback | 20% | +0.00 pp | 18.33% | 17.94% |
| geometry_no_feedback vs random_no_feedback | 5% | -0.64 pp | 5.00% | 3.61% |
| geometry_no_feedback vs random_no_feedback | 10% | -1.44 pp | 10.14% | 8.98% |
| geometry_no_feedback vs random_no_feedback | 15% | -0.80 pp | 13.72% | 13.02% |
| geometry_no_feedback vs random_no_feedback | 20% | +0.16 pp | 17.54% | 16.61% |
| random_feedback vs random_no_feedback | 5% | +0.00 pp | 5.15% | 3.61% |
| random_feedback vs random_no_feedback | 10% | +0.00 pp | 10.59% | 8.98% |
| random_feedback vs random_no_feedback | 15% | +0.08 pp | 14.24% | 13.02% |
| random_feedback vs random_no_feedback | 20% | -0.08 pp | 17.94% | 16.61% |
| geometry_feedback vs dense_budget_only | 5% | +0.72 pp | 4.00% | 10.05% |
| geometry_feedback vs dense_budget_only | 10% | +0.00 pp | 9.51% | 10.05% |
| geometry_feedback vs dense_budget_only | 15% | -0.72 pp | 13.80% | 12.33% |
| geometry_feedback vs dense_budget_only | 20% | +0.24 pp | 18.33% | 17.89% |

## Interpretation Guardrail

This experiment tests safe-compression identification only. It does not
replace Task58/59 route-quality evidence because the candidate ranking is
deliberately fixed to dense top-10.
