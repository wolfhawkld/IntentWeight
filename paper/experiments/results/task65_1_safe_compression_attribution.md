# Task65.1 Safe-Compression Attribution

The upstream fixed-top-10 ranking is held constant. Selector thresholds
and token-budget actions are selected on calibration queries and frozen
before held-out test evaluation.

## Frozen Test Selection (calibration margin: 0 pp)

| Selector | Eligible | Ratio | Min keep | Target coverage | Test hit delta | Test token saving | Actual coverage | Selective risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| learned_confidence | True | 0.80 | 4 | 0.60 | -0.88 pp | 11.05% | 0.601 | 0.032 |
| geometry_similarity | True | 0.80 | 4 | 0.60 | -1.04 pp | 8.86% | 0.584 | 0.038 |
| shuffled_confidence | True | 0.80 | 4 | 0.60 | -0.64 pp | 9.20% | 0.601 | 0.029 |
| random_selector | True | 0.75 | 4 | 0.60 | -0.72 pp | 11.86% | 0.605 | 0.030 |
| budget_only | True | 0.95 | 4 | 1.00 | -0.00 pp | 6.18% | 1.000 | 0.010 |

## Frozen Test Selection (calibration margin: 1 pp)

| Selector | Eligible | Ratio | Min keep | Target coverage | Test hit delta | Test token saving | Actual coverage | Selective risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| learned_confidence | True | 0.80 | 4 | 0.80 | -1.36 pp | 16.69% | 0.815 | 0.031 |
| geometry_similarity | True | 0.80 | 4 | 0.90 | -1.28 pp | 17.64% | 0.893 | 0.028 |
| shuffled_confidence | True | 0.75 | 4 | 0.80 | -1.12 pp | 18.73% | 0.815 | 0.028 |
| random_selector | True | 0.75 | 4 | 0.80 | -1.36 pp | 19.00% | 0.809 | 0.031 |
| budget_only | True | 0.85 | 4 | 1.00 | -1.20 pp | 16.00% | 1.000 | 0.024 |

## Safe-Action Discrimination

The fixed action is `token_budget_r0.85_m4`. Labels are defined only on
queries whose uncompressed source ranking contains relevant evidence.

| Selector | AUROC | Average precision | Raw Brier | Isotonic Brier |
|---|---:|---:|---:|---:|
| learned_confidence | 0.432 | 0.975 | 0.134 | 0.023 |
| geometry_similarity | 0.298 | 0.962 | 0.412 | 0.024 |
| shuffled_confidence | 0.531 | 0.977 | 0.137 | 0.023 |
| random_selector | 0.524 | 0.982 | 0.345 | 0.025 |
| budget_only | 0.500 | 0.976 | 0.024 | 0.023 |

## Guardrails

- Full-top-10 quality, final budgeted quality, and route metrics are separate layers.
- A selector is useful only if it improves the held-out quality-cost frontier over shuffled/random and budget-only controls.
- The 1 pp margin is a sensitivity analysis; the zero-drop calibration gate is the primary result.
