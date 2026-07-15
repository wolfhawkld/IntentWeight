# Task69 Cross-Fitted Calibration: lotte_recreation_search_100k

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 924 | 4/5 | -0.76 pp | 5.42% | 0/3 | 0.00% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 1 | `token_budget_r0.95_m4` | True | -0.72 pp | 7.10% | `dense_top10_fallback` |
| 2 | `token_budget_r0.95_m4` | True | -0.90 pp | 7.25% | `dense_top10_fallback` |
| 3 | `token_budget_r0.95_m4` | True | -0.90 pp | 6.70% | `dense_top10_fallback` |
| 4 | `token_budget_r0.95_m4` | True | -1.27 pp | 5.99% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
