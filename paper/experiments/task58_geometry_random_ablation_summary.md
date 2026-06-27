# Task58 Geometry Random Ablation Summary

Updated: 2026-06-25

## Objective

Test whether the LoTTE local-geometry signal matters under the same
final-context-budget evaluation frame used by Task38. This task compares
static nearest-centroid cluster-arm selection against uniform random cluster-arm
selection on LoTTE technology/search 100k, using fixed seeds `13,17,19`.

This task does not attempt to prove that geometry alone explains final fused
ranking gains. Dense and BM25 rescue paths remain active by design, because the
paper's method uses dense retrieval as a recall floor. The purpose is to
separate route-control signal from final fused-ranking protection.

## Artifacts

- Route run:
  `paper/experiments/results/task58_geometry_random_100k_routes/`
- Static nearest budget evaluation:
  `paper/experiments/results/task58_static_nearest_100k_context_budget.*`
- Uniform random budget evaluation:
  `paper/experiments/results/task58_uniform_random_100k_context_budget.*`
- Summary script:
  `paper/experiments/scripts/task58_geometry_random_ablation_summary.py`
- Aggregate summary:
  `paper/experiments/results/task58_geometry_random_ablation_summary.md`

## Main Result

| Setting | Full Top-10 Hit@10 | Route Reward | Selected Cluster Hit | Selected Policy | Test Hit Delta | Token Saving | NI Seeds |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Static nearest geometry | 0.8764 | 0.8563 | 0.8870 | `token_budget_r0.98_m4` | +1.44 pp | 5.03% | 3/3 |
| Uniform random control | 0.8842 | 0.1499 | 0.1577 | `token_budget_r0.88_m8` | +1.04 pp | 11.92% | 2/3 |

Both settings are evaluated on the same Task38-style calibration/test split
(`179` calibration queries and `417` frozen-test queries).

## Interpretation

The result is intentionally nuanced.

Final fused Hit@10 is protected by dense/BM25 rescue paths. Uniform random
cluster-arm selection does not collapse final Hit@10 because the full
multi-route surface still contains global dense retrieval, BM25, weighted RRF,
and dense floor behavior. This means final Hit@10 alone is not a clean proof
that geometry matters.

The route-control metrics do distinguish the settings. Static nearest geometry
has high route reward (`0.8563`) and selected-cluster hit (`0.8870`), while the
uniform random control has low route reward (`0.1499`) and selected-cluster hit
(`0.1577`). This supports the paper's bounded geometry claim:
local geometry is a useful route-control and confidence signal, not a
standalone replacement for dense retrieval.

The uniform random control's stronger token saving is not a positive geometry
claim. It is boundary evidence that aggressive or accidental evidence-pool
differences can still appear acceptable when dense/BM25 rescue paths mask route
quality. Task59 should therefore isolate learned LinUCB confidence versus
static/no-feedback controls under the same budget frame.

## Paper-Use Guidance

Use Task58 defensively:

> Under full multi-route rescue, random cluster-arm selection can still preserve
> final fused Hit@10, so final Hit@10 should not be used as the sole evidence
> for geometry. However, static nearest-centroid geometry produces much stronger
> route-control metrics than the random control, supporting geometry as a
> confidence signal within the controller.

Do not write:

> Geometry alone explains the final retrieval gains.
