# Task25 Credit Assignment Summary

Task25 addresses the audit concern that the gated LinUCB policy could receive
credit for dense/BM25 rescue hits. Earlier cost-aware routing updated LinUCB
with reward computed from the final fused ranking. When dense floor or BM25
hit the answer, the selected cluster arm could still receive positive feedback,
inflating confidence without proving that the cluster-local route itself was
responsible.

## Implementation

`linucb_cost_aware_routing.py` now separates three signals:

- `final_true_reward`: reward measured on the final fused dense/BM25/cluster ranking.
- `route_true_reward`: reward measured only on the selected cluster-route ranking.
- `true_reward`: the reward actually used for simulated feedback and policy update.

Two explicit knobs were added:

- `--reward-attribution final_fused|cluster_only`
- `--confidence-mode value|route_quality`

The default remains `final_fused/value`, preserving historical behavior. The
new diagnostic mode `cluster_only` updates LinUCB only from the selected
cluster route, which makes policy learning evidence stricter. The experimental
`route_quality` confidence gate uses historical cluster-route reward rather
than LinUCB value estimates.

## LoTTE 100k Results

All formal rows use LoTTE technology/search 100k, held-out test queries,
`seeds=13,17,19`, `epochs=8`, and shared cached retrieval artifacts.

| Config | Hit@10 | Evidence Recall@10 | Last Final Reward | Last Route Reward | Route Reward Gain | Avg Cost | Dense Rate | LinUCB Primary Rate | Selected Cluster Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| old `final_fused/value` | 0.8826 | 0.6871 | 0.7584 | 0.8076 | 0.4899 | 193.92 | 0.7466 | 0.2534 | 0.6908 |
| `cluster_only/value` | 0.8764 | 0.6829 | 0.7606 | 0.8328 | 0.4379 | 181.47 | 0.6708 | 0.3292 | 0.7223 |
| `cluster_only/route_quality` smoke, seed 13 | 0.8792 | 0.7259 | 0.7768 | 0.8540 | 0.3440 | 299.28 | 1.0000 | 0.0000 | 0.7594 |

## Interpretation

The stricter `cluster_only/value` run improves the learned route's own quality:
last-epoch route reward rises from `0.8076` to `0.8328`, and selected-cluster
hit rises from `0.6908` to `0.7223`. It also reduces average source candidate
cost from `193.92` to `181.47` by increasing LinUCB-primary routing.

The final Hit@10 drops slightly from `0.8826` to `0.8764`, which is expected:
the stricter reward no longer lets dense/BM25 rescue hits directly reinforce
cluster arms. This is a cleaner paper result because it separates final system
quality from the route-specific learning signal.

The `route_quality` confidence gate is currently too conservative. It produces
strong route quality on the seed-13 smoke run, but confidence remains low, so
nearly all queries fall back to the full dense route. This should be treated as
a diagnostic finding rather than the current main setting.

## Paper Impact

Task25 strengthens the feedback-learning claim. The paper can now say that
LinUCB's route-level feedback can improve the selected cluster route itself,
not merely benefit from final dense/BM25 rescue. The strongest current claim is
still bounded:

> IntentWeight builds a dense/BM25/cluster multi-route retrieval surface and
> uses trust-weighted contextual bandit feedback to improve route-specific
> cluster selection over time. Dense remains an important recall floor, but
> stricter route-level credit assignment shows that LinUCB can improve the
> quality of the cluster route itself while reducing source candidate cost
> relative to the old fused-credit gated policy.

Artifacts:

- Code: `paper/experiments/scripts/linucb_cost_aware_routing.py`
- Comparison CSV: `paper/experiments/task25_credit_assignment_comparison.csv`
- Old-credit formal run: `paper/experiments/results/task25_100k_old_credit_formal/`
- Cluster-credit formal run: `paper/experiments/results/task25_100k_cluster_credit_formal/`
- Route-quality smoke run: `paper/experiments/results/task25_100k_route_credit/`
