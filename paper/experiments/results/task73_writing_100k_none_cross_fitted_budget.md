# Task69 Cross-Fitted Calibration: lotte_writing_search_100k

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 1071 | 5/5 | +0.12 pp | 10.09% | 2/3 | 0.00% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `token_budget_r0.88_m8` | True | +0.62 pp | 7.61% | `dense_top10_fallback` |
| 1 | `token_budget_r0.88_m8` | True | +0.62 pp | 9.49% | `dense_top10_fallback` |
| 2 | `token_budget_r0.85_m8` | True | -0.62 pp | 9.09% | `dense_top10_fallback` |
| 3 | `token_budget_r0.88_m8` | True | +0.78 pp | 12.20% | `dense_top10_fallback` |
| 4 | `token_budget_r0.85_m8` | True | -0.78 pp | 12.09% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
