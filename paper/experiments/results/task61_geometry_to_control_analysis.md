# Task61 Geometry-To-Control Analysis

Task61 connects geometry diagnostics to route-control and budget-control
outcomes using already-generated artifacts. It does not rerun retrieval
or claim that the sample size proves a manifold theorem.

## Figure 4 Cross-Scale Diagnostics

| X metric | Y metric | n | Pearson r | Spearman r | Pattern |
| --- | --- | ---: | ---: | ---: | --- |
| nearest_cluster_hit_at_3 | policy_hit_delta_pp | 6 | 0.5551 | 0.6088 | strong_positive |
| nearest_cluster_hit_at_3 | policy_saving_pct | 6 | -0.4319 | -0.4058 | moderate_negative |
| context_retention_at_10 | policy_hit_delta_pp | 6 | 0.4601 | 0.3714 | moderate_positive |
| context_retention_at_10 | policy_saving_pct | 6 | -0.6381 | -0.7143 | strong_negative |
| pca_dim_for_90pct | context_retention_at_10 | 6 | -0.3495 | -0.2571 | moderate_negative |

These cross-scale correlations are mixed and small-N. This is useful
because it prevents an overclaim: geometry diagnostics explain why local
route structure is worth using, but final Hit@10 and token saving are
also shaped by fusion, dense/BM25 rescue, and the calibrated budget
policy.

## Task60 Route-Control Diagnostics

| X metric | Y metric | n | Pearson r | Spearman r | Pattern |
| --- | --- | ---: | ---: | ---: | --- |
| arm_count | learned_route_reward | 5 | -0.9913 | -1.0000 | very_strong_negative |
| arm_count | learned_cluster_hit | 5 | -0.9506 | -1.0000 | very_strong_negative |
| learned_route_reward | gated_dense_rate | 5 | -0.9141 | -1.0000 | very_strong_negative |
| learned_route_reward | gated_primary_rate | 5 | 0.9141 | 1.0000 | very_strong_positive |
| learned_route_reward | gated_hit_delta_pp | 5 | 0.4765 | 0.5000 | moderate_positive |
| static_route_reward | full_hit_delta_pp | 5 | 0.7089 | 0.7000 | strong_positive |
| arm_count | gated_dense_rate | 5 | 0.8595 | 1.0000 | very_strong_positive |

The control-layer signal is clearer than the final-gain signal. As K
increases, learned route reward and selected-cluster hit decline, and the
current gated controller falls back to dense retrieval more often. This
supports the interpretation that geometry is most defensible as a
route-control surface and confidence signal.

## Task58 Random-Control Anchor

| Contrast | Value |
| --- | ---: |
| Static minus random route reward | +70.64 pp |
| Static minus random selected-cluster hit | +72.93 pp |
| Static minus random final test Hit delta | +0.40 pp |
| Static minus random token saving | -6.89% |

Task58 is the clearest route-level control: static geometry strongly beats
uniform random selection on route reward and selected-cluster hit. The much
smaller final Hit gap is expected because dense/BM25 rescue protects the
fused result.

## Paper-Facing Conclusion

Use Task61 to write a bounded claim:

> Geometry diagnostics are explanatory and design-guiding signals for
> structured route control. They are not standalone proof that a smooth
> manifold governs retrieval, and they do not alone explain final Hit@10.

This preserves the core method: local geometry defines structured arms,
feedback-updated LinUCB estimates route reliability, and calibrated budget
control converts reliable decisions into final-context savings.
