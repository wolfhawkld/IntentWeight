# Task59 Feedback-Control Ablation Summary

Task59 isolates what feedback-updated LinUCB contributes beyond static
geometry and no-feedback fallback controls on LoTTE technology/search 100k.
All final-context token results use the same Task38-style calibration/test
protocol under the `task59_100k` split with fixed seeds `13,17,19`.

## Route-Control Result

| Setting | Full Hit@10 | EvidenceRecall@10 | Route Reward | Cluster Hit | Confidence | Dense Rate | Primary Rate | Source Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| learned_full_multi_route | 0.8775 | 0.7169 | 0.6790 | 0.5766 | 0.5123 | 1.0000 | 0.0000 | 300.00 |
| learned_gated_cost_aware | 0.8384 | 0.6179 | 0.6790 | 0.5766 | 0.5123 | 0.7377 | 0.2623 | 178.09 |
| static_nearest_gated | 0.8674 | 0.6908 | 0.8563 | 0.8870 | 0.4169 | 0.9586 | 0.0414 | 191.79 |
| no_feedback_gated | 0.8809 | 0.7205 | 0.1504 | 0.1570 | 0.0000 | 1.0000 | 0.0000 | 300.00 |
| static_nearest_ensemble | 0.8764 | 0.7115 | 0.8563 | 0.8870 | 0.0000 | 1.0000 | 0.0000 | 300.00 |
| uniform_random_ensemble | 0.8842 | 0.7213 | 0.1499 | 0.1577 | 0.0000 | 1.0000 | 0.0000 | 300.00 |

## Frozen Budget Result

| Setting | Policy | Eligible | Test Hit Delta | Token Saving | NI Seeds |
| --- | --- | ---: | ---: | ---: | ---: |
| learned_full_multi_route | `token_budget_r0.85_m4` | True | -1.68 pp | 17.86% | 0/3 |
| learned_gated_cost_aware | `token_budget_r0.92_m4` | False | -5.20 pp | 11.83% | 0/3 |
| static_nearest_gated | `token_budget_r0.85_m8` | True | -2.40 pp | 12.01% | 0/3 |
| no_feedback_gated | `token_budget_r0.85_m4` | True | -1.60 pp | 16.56% | 0/3 |
| static_nearest_ensemble | `token_budget_r0.85_m4` | True | -1.68 pp | 18.14% | 0/3 |
| uniform_random_ensemble | `token_budget_r0.85_m4` | True | -1.44 pp | 18.39% | 0/3 |

## Interpretation

The no-feedback gated control has high final Hit@10 only because it falls
back to the full dense/BM25 surface: dense rate is `1.0000`, LinUCB primary
rate is `0.0000`, and route reward remains low. This prevents the paper
from attributing fallback quality to feedback learning.

Static-nearest geometry has strong route-control quality, but the gated
version still relies heavily on dense fallback. Learned gated routing saves
more retrieval-stage dense calls, but its final Hit@10 drops under the
current thresholds; it should be treated as a cost-aggressive boundary
rather than the main quality-preserving operating point.

The learned full multi-route row is the cleaner component-attribution row:
feedback-updated route selection is used inside the full rescue surface, and
external calibrated budget control produces token saving on this split, but
Task59 alone does not establish paired non-inferiority.

Paper-facing claim: LinUCB is a feedback-adaptive confidence/control
mechanism, not the sole explanation for final fused Hit@10 gains.
