# Task69 Cross-Fitted Calibration: lotte_science_search_100k

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 596 | 5/5 | -0.11 pp | 16.88% | 0/3 | 2.41% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `token_budget_r0.88_m4` | True | +0.28 pp | 17.55% | `dense_top10_fallback` |
| 1 | `token_budget_r0.85_m4` | True | -0.56 pp | 20.87% | `token_budget_r0.98_m4` |
| 2 | `token_budget_r0.88_m4` | True | +0.28 pp | 15.47% | `dense_top10_fallback` |
| 3 | `token_budget_r0.88_m4` | True | +0.84 pp | 13.79% | `dense_top10_fallback` |
| 4 | `token_budget_r0.85_m4` | True | -1.40 pp | 16.64% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
