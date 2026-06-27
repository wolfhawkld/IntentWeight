# Task58 Geometry Random Ablation Summary

Task58 compares static nearest-centroid geometry against uniform random
cluster-arm selection on LoTTE technology/search 100k. Both settings keep
the same dense/BM25/cluster multi-route fusion surface and are evaluated
with the same Task38 calibration/test context-budget protocol.

## Route-Level Result

| Setting | Full Top-10 Hit@10 | EvidenceRecall@10 | Route Reward | Selected Cluster Hit | Dense Rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| static_nearest | 0.8764 | 0.7115 | 0.8563 | 0.8870 | 1.0000 |
| uniform_random | 0.8842 | 0.7213 | 0.1499 | 0.1577 | 1.0000 |

## Budgeted Frozen-Test Result

| Setting | Selected Policy | Calibration Eligible | Test Hit Delta | Token Saving | NI Seeds |
| --- | --- | ---: | ---: | ---: | ---: |
| static_nearest | `token_budget_r0.98_m4` | False | +1.44 pp | 5.03% | 3/3 |
| uniform_random | `token_budget_r0.88_m8` | False | +1.04 pp | 11.92% | 2/3 |

## Interpretation

The full fused ranking is protected by dense/BM25 rescue paths: uniform
random cluster-arm selection does not collapse final Hit@10 under the
full multi-route surface. This means final Hit@10 alone is not a clean
test of whether geometry matters.

The route-control metrics tell the important story. Static nearest-centroid
geometry has a much higher route reward and selected-cluster hit than the
uniform random control. Therefore geometry should be written as a useful
route-control and confidence signal, not as a standalone replacement for
dense retrieval.

The random control can still obtain strong budgeted Hit@10 because the
dense/BM25 rescue surface is active. This is boundary evidence that the
paper should not claim geometry alone explains final fused-ranking gains.
