# Task65.5 Calibration-Split Sensitivity

20 deterministic 30/70 calibration/test splits reuse frozen Task37 rankings.
Splits overlap and are stability diagnostics, not independent experimental seeds.

| Scale | Eligible | Policies | Mode rate | Test hit range | Mean test hit | Test saving range | Mean saving | Hit >= 0 | Hit >= -1pp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100k | 12/20 | 6 | 50% | [-2.00, +0.72] pp | -0.45 pp | [6.18, 17.73]% | 10.64% | 45% | 70% |
| 200k | 19/20 | 3 | 90% | [+0.56, +3.52] pp | +1.53 pp | [5.33, 17.29]% | 15.25% | 100% | 100% |
| 400k | 16/20 | 8 | 30% | [-2.08, +2.80] pp | +0.45 pp | [6.57, 18.27]% | 12.47% | 60% | 85% |
| 638k | 19/20 | 6 | 70% | [-0.88, +2.24] pp | +0.44 pp | [7.85, 17.91]% | 14.96% | 80% | 100% |

## Original Split

- 100k: `token_budget_r0.95_m4`, eligible=True, test Hit delta -0.00 pp, saving 6.18%.
- 200k: `token_budget_r0.85_m4`, eligible=True, test Hit delta +1.20 pp, saving 16.00%.
- 400k: `token_budget_r0.98_m4`, eligible=False, test Hit delta +2.32 pp, saving 6.57%.
- 638k: `token_budget_r0.85_m4`, eligible=True, test Hit delta -0.08 pp, saving 17.53%.

## Guardrail

This audit measures sensitivity to query partitioning. It does not turn overlapping splits into independent evidence or establish universal non-inferiority.
