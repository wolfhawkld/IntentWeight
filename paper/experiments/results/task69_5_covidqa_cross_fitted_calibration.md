# Task69 Cross-Fitted Calibration: covidqa

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 1765 | 4/5 | -0.21 pp | 8.34% | 0/3 | 0.00% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 1 | `token_budget_r0.95_m4` | True | -0.29 pp | 10.02% | `dense_top10_fallback` |
| 2 | `token_budget_r0.98_m4` | True | +0.38 pp | 9.41% | `dense_top10_fallback` |
| 3 | `token_budget_r0.92_m4` | True | -0.77 pp | 11.87% | `dense_top10_fallback` |
| 4 | `token_budget_r0.95_m4` | True | -0.39 pp | 10.23% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
