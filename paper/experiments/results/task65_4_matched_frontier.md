# Task65.4 Independently Calibrated Matched Frontier

Dense and IntentRoute independently select actions on the same calibration split and budget grid.

## Quality-Constrained Selection

| Margin | IntentRoute policy | IR test hit | IR saving | Dense policy | Dense test hit | Dense saving | IR-Dense hit |
|---:|---|---:|---:|---|---:|---:|---:|
| 0.0 pp | `token_budget_r0.95_m4` | -0.00 pp | 6.18% | `token_budget_r1.00_m4` | +0.00 pp | 0.00% | -0.00 pp |
| 0.5 pp | `token_budget_r0.93_m4` | -0.32 pp | 7.97% | `token_budget_r1.00_m4` | +0.00 pp | 0.00% | -0.32 pp |
| 1.0 pp | `token_budget_r0.84_m4` | -1.28 pp | 17.13% | `token_budget_r1.00_m4` | +0.00 pp | 0.00% | -1.28 pp |
| 2.0 pp | `token_budget_r0.80_m4` | -1.60 pp | 20.90% | `token_budget_r0.82_m4` | -2.40 pp | 25.22% | +0.80 pp |

## Calibration-Targeted Actions

| Target | IR test saving | IR test hit | Dense test saving | Dense test hit | Saving gap | IR-Dense hit |
|---:|---:|---:|---:|---:|---:|---:|
| 5% | 2.98% | -0.16 pp | 9.62% | -0.96 pp | 6.64 pp | +0.80 pp |
| 10% | 5.20% | -0.16 pp | 9.62% | -0.96 pp | 4.42 pp | +0.80 pp |
| 15% | 9.99% | -0.88 pp | 12.61% | -1.20 pp | 2.62 pp | +0.32 pp |
| 20% | 15.80% | -1.20 pp | 17.28% | -1.44 pp | 1.48 pp | +0.24 pp |

The test saving gaps above are distribution-shift diagnostics; they are not same-saving comparisons.

## Same-Saving Held-Out Frontier (Post-Hoc Diagnostic)

| Test saving | IntentRoute interpolated hit | Dense interpolated hit | IR-Dense hit |
|---:|---:|---:|---:|
| 5% | +0.08 pp | -0.39 pp | +0.47 pp |
| 10% | -0.75 pp | -0.79 pp | +0.04 pp |
| 15% | -0.99 pp | -1.21 pp | +0.22 pp |
| 20% | -1.55 pp | -1.54 pp | -0.01 pp |

## Paired Check

- Margin 0.0 pp: mean IntentRoute-minus-Dense Hit +0.00 pp; strict NI 0/3 seeds.
- Margin 0.5 pp: mean IntentRoute-minus-Dense Hit -0.32 pp; strict NI 0/3 seeds.
- Margin 1.0 pp: mean IntentRoute-minus-Dense Hit -1.28 pp; strict NI 0/3 seeds.
- Margin 2.0 pp: mean IntentRoute-minus-Dense Hit +0.80 pp; strict NI 1/3 seeds.
