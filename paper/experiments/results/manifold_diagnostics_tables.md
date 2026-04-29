# Manifold Diagnostics

## Evidence Retrieval Main

| dataset | scope | corpus_scope | pca_dim_for_90pct | cluster_label_purity | local_label_purity | nearest_cluster_hit@3 | context_gt_recall@10 | dense_recall@10 | soft_recall@10 | soft_minus_dense_recall@10 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| emanual | heldout_test | full | 111 | 0.0275 | 0.0169 | 0.8923 | 0.3615 | 0.3231 | 0.1436 | -0.1795 | geometry can route to GT clusters, but learned arm/fusion underuses the signal |
| pubmedqa | full | full | 177 | 0.0366 | 0.2439 | 0.9680 | 0.9860 | 0.9930 | 0.9920 | -0.0010 | strong GT-cluster routing signal; soft routing mainly preserves dense baseline |

## Intent Retrieval Proxy

| dataset | scope | corpus_scope | pca_dim_for_90pct | cluster_label_purity | local_label_purity | nearest_cluster_hit@3 | context_gt_recall@10 | dense_recall@10 | soft_recall@10 | soft_minus_dense_recall@10 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | heldout_test | full | 105 | 0.6389 | 0.8539 | 0.9968 | 0.9782 | 0.9805 | 0.9831 | 0.0026 | strong GT-cluster routing signal; soft routing mainly preserves dense baseline |

## Smoke / Sample Results

| dataset | scope | corpus_scope | pca_dim_for_90pct | cluster_label_purity | local_label_purity | nearest_cluster_hit@3 | context_gt_recall@10 | dense_recall@10 | soft_recall@10 | soft_minus_dense_recall@10 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cuad | smoke_only | gt_anchored_10000 | 182 | 0.0524 | 0.0716 | 0.6076 | 0.0759 | 0.0759 | 0.0844 | 0.0084 | soft routing helps despite imperfect cluster routing |

## Notes

- PCA/context metrics test whether low-dimensional geometry preserves evidence retrieval.
- Cluster/local purity metrics test whether the corpus has coherent local neighborhoods under available metadata labels.
- nearest_cluster_hit@k tests whether query contexts route toward clusters containing GT chunks without using LinUCB feedback.
- soft_minus_dense_recall@10 relates these diagnostics to Task 13.5 soft-routing gains.
