# Task69 Cross-Fitted Calibration: emanual_deduplicated

Five balanced folds reuse frozen Dense and IntentRoute rankings. Four folds select each policy, and every query is evaluated out of fold once.

## Result

| Queries | Eligible folds | Hit delta | Context saving | Strict NI seeds | Dense saving |
|---:|---:|---:|---:|---:|---:|
| 132 | 5/5 | -0.26 pp | 16.20% | 0/3 | 0.00% |

## Fold Selections

| Fold | IntentRoute policy | Eligible | Test Hit delta | Saving | Dense policy |
|---:|---|---:|---:|---:|---|
| 0 | `token_budget_r0.85_m4` | True | -6.17 pp | 14.69% | `dense_top10_fallback` |
| 1 | `token_budget_r0.85_m8` | True | +3.70 pp | 13.23% | `dense_top10_fallback` |
| 2 | `token_budget_r0.85_m7` | True | +1.28 pp | 18.19% | `dense_top10_fallback` |
| 3 | `token_budget_r0.85_m4` | True | -1.33 pp | 16.48% | `dense_top10_fallback` |
| 4 | `token_budget_r0.85_m7` | True | +1.33 pp | 18.30% | `dense_top10_fallback` |

## Guardrail

This reuses frozen rankings and recomputes fold selection and paired statistics. It is not a new retrieval run, and strict non-inferiority is reported separately from mean quality preservation.
