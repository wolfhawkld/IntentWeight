# Task69 Cross-Fitted Calibration: lotte_writing_search_100k

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 1071 | 0/5 | +0.00 pp | 0.00% | 3/3 | 0.00% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 1 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 2 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 3 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |
| 4 | `dense_top10_fallback` | False | +0.00 pp | 0.00% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
