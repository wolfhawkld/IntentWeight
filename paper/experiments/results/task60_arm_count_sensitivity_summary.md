# Task60 Arm-Count Sensitivity Summary

Task60 tests whether the fixed `n_clusters=32` arm design is a brittle
assumption. The experiment runs LoTTE technology/search 100k with MiniLM,
fixed seeds `13,17,19`, and arm counts `K in {8,16,32,64,128}`.

## Route-Level Sensitivity

| K | Mode | Full Hit@10 | EvidenceRecall@10 | Route Reward | Cluster Hit | Dense Rate | Primary Rate | Source Cost |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | static_nearest_ensemble | 0.8803 | 0.7205 | 0.9128 | 0.9480 | 1.0000 | 0.0000 | 300.00 |
| 8 | full_multi_route | 0.8837 | 0.7219 | 0.9088 | 0.9038 | 1.0000 | 0.0000 | 300.00 |
| 8 | gated_cost_aware | 0.8680 | 0.6816 | 0.9088 | 0.9038 | 0.4083 | 0.5917 | 137.83 |
| 16 | static_nearest_ensemble | 0.8798 | 0.7163 | 0.8826 | 0.9122 | 1.0000 | 0.0000 | 300.00 |
| 16 | full_multi_route | 0.8809 | 0.7234 | 0.8384 | 0.7515 | 1.0000 | 0.0000 | 300.00 |
| 16 | gated_cost_aware | 0.8624 | 0.6647 | 0.8384 | 0.7515 | 0.6089 | 0.3911 | 156.07 |
| 32 | static_nearest_ensemble | 0.8764 | 0.7115 | 0.8563 | 0.8870 | 1.0000 | 0.0000 | 300.00 |
| 32 | full_multi_route | 0.8775 | 0.7169 | 0.6790 | 0.5766 | 1.0000 | 0.0000 | 300.00 |
| 32 | gated_cost_aware | 0.8384 | 0.6179 | 0.6790 | 0.5766 | 0.7377 | 0.2623 | 178.09 |
| 64 | static_nearest_ensemble | 0.8786 | 0.7153 | 0.8272 | 0.8496 | 1.0000 | 0.0000 | 300.00 |
| 64 | full_multi_route | 0.8792 | 0.7212 | 0.4855 | 0.3255 | 1.0000 | 0.0000 | 300.00 |
| 64 | gated_cost_aware | 0.8367 | 0.6245 | 0.4855 | 0.3255 | 0.8986 | 0.1014 | 218.24 |
| 128 | static_nearest_ensemble | 0.8826 | 0.7199 | 0.8479 | 0.8691 | 1.0000 | 0.0000 | 300.00 |
| 128 | full_multi_route | 0.8837 | 0.7271 | 0.1633 | 0.1299 | 1.0000 | 0.0000 | 300.00 |
| 128 | gated_cost_aware | 0.8428 | 0.6473 | 0.1633 | 0.1299 | 0.9502 | 0.0498 | 245.85 |

## Frozen Budget Result

| K | Mode | Policy | Eligible | Test Hit Delta | Token Saving | NI Seeds |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 8 | static_nearest_ensemble | `token_budget_r0.98_m4` | True | +1.12 pp | 3.87% | 3/3 |
| 8 | full_multi_route | `token_budget_r0.95_m4` | False | +1.44 pp | 6.23% | 3/3 |
| 8 | gated_cost_aware | `token_budget_r0.85_m4` | False | -1.84 pp | 16.90% | 0/3 |
| 16 | static_nearest_ensemble | `token_budget_r0.85_m8` | True | +0.80 pp | 11.50% | 1/3 |
| 16 | full_multi_route | `token_budget_r0.85_m8` | True | +0.80 pp | 10.49% | 1/3 |
| 16 | gated_cost_aware | `token_budget_r0.85_m8` | False | -1.68 pp | 11.95% | 0/3 |
| 32 | static_nearest_ensemble | `token_budget_r0.98_m4` | False | +0.80 pp | 4.30% | 2/3 |
| 32 | full_multi_route | `token_budget_r0.98_m4` | False | +0.56 pp | 4.68% | 1/3 |
| 32 | gated_cost_aware | `token_budget_r0.85_m4` | False | -4.48 pp | 18.00% | 0/3 |
| 64 | static_nearest_ensemble | `token_budget_r0.88_m4` | True | -0.48 pp | 13.80% | 0/3 |
| 64 | full_multi_route | `token_budget_r0.85_m8` | False | +0.40 pp | 11.19% | 1/3 |
| 64 | gated_cost_aware | `token_budget_r0.92_m4` | False | -3.76 pp | 12.47% | 0/3 |
| 128 | static_nearest_ensemble | `token_budget_r0.85_m8` | True | +0.80 pp | 10.51% | 2/3 |
| 128 | full_multi_route | `token_budget_r0.85_m8` | False | +1.20 pp | 10.23% | 3/3 |
| 128 | gated_cost_aware | `token_budget_r0.88_m4` | False | -3.12 pp | 15.64% | 0/3 |

## Interpretation

Static-nearest geometry is not brittle across this arm-count grid. Its route
reward stays in `0.8272-0.9128`,
which supports using KMeans arms as an engineering route-control surface
rather than a theoretically unique manifold partition.

Full multi-route retrieval is also stable at the fused-ranking level:
full-route Hit@10 stays in `0.8775-0.8837`.
This stability is partly protected by dense/BM25 rescue paths, so it should
not be interpreted as proof that arm count is irrelevant to route learning.

Learned gated routing is sensitive to arm count. Smaller K values allow more
dense saving (`dense_rate` as low as `0.4083`),
while finer arms dilute feedback and push the controller back toward dense
fallback. The frozen-test Hit deltas range from `-4.48`
pp to `-1.68` pp, so this setting remains a
cost-aggressive boundary rather than the main quality-preserving claim.

Paper-facing claim: `n_clusters=32` is a reproducible engineering default,
not a theoretical optimum. The method is robust on the full multi-route
surface, while retrieval-stage gating should be tuned separately if dense
call reduction is the deployment target.
