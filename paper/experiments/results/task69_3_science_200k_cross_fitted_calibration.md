# Task69 Cross-Fitted Calibration: lotte_science_search_200k

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 596 | 4/5 | -0.67 pp | 10.75% | 0/3 | 0.00% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `token_budget_r0.90_m8` | True | +0.83 pp | 11.94% | `dense_top10_fallback` |
| 1 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 2 | `token_budget_r0.85_m4` | True | -5.32 pp | 18.33% | `dense_top10_fallback` |
| 3 | `token_budget_r0.85_m8` | True | +0.28 pp | 11.72% | `dense_top10_fallback` |
| 4 | `token_budget_r0.90_m8` | True | +0.84 pp | 11.22% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
