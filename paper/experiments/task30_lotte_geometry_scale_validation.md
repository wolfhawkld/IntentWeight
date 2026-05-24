# Task30 LoTTE Multi-Scale Geometry Validation

Task30 addresses the remaining manifold-geometry validation concern before
paper writing: whether the LoTTE large-scale results are consistent with the
piecewise relevance-manifold interpretation.

The experiment is diagnostic only. It does not rerun retrieval or LinUCB. It
reuses:

- canonical LoTTE scale-store embeddings;
- shared PCA/KMeans context artifacts from the large-scale runs;
- Task29-C token-quality frontier results.

## Result

| Scale | Corpus | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Dense Hit@10 | Task29-C Hit@10 | Hit Delta | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100k | 101311 | 182 | 0.6437 | 0.8870 | 0.9033 | 0.8674 | 0.8652 | -0.22 pp | 4.83% |
| 200k | 201010 | 186 | 0.6292 | 0.8697 | 0.8947 | 0.7970 | 0.8249 | +2.80 pp | 4.69% |
| 400k | 400674 | 190 | 0.6110 | 0.9016 | 0.8826 | 0.7718 | 0.7819 | +1.01 pp | 5.32% |
| 638k | 638509 | 196 | 0.5867 | 0.9016 | 0.8571 | 0.7282 | 0.7466 | +1.85 pp | 4.86% |

## Interpretation

The geometry signal remains usable as corpus scale grows:

- `nearest_cluster_hit@3` stays high, around `0.87-0.90`, so the KMeans/PCA
  geometry can often route queries near the GT cluster region.
- `PCA dim90` rises from `182` to `196`, and `PCA var@64` drops from `0.6437`
  to `0.5867`, suggesting that the representation geometry becomes more
  complex at larger scale.
- `context_recall_retention@10` declines from `0.9033` to `0.8571`, showing
  that PCA/context geometry alone loses some retrieval coverage as scale
  increases.
- Dense-only Hit@10 declines more strongly as corpus size grows, while Task29-C
  remains above dense at 200k/400k/638k and uses fewer final context tokens.

This supports the paper's bounded theoretical framing:

> LoTTE exhibits usable local geometry consistent with a piecewise relevance
> manifold assumption. The geometry is strong enough to act as a route-control
> signal, but not sufficient to replace dense retrieval by itself. IntentWeight's
> value comes from combining geometry-aware routing, dense/BM25 rescue paths,
> feedback-updated LinUCB confidence, and final context-budget control.

## Limits

The four-scale correlations are descriptive only. With just four scale points,
they should not be presented as statistical proof that a single geometry metric
predicts retrieval gain. In fact, the relationship is not monotonic: 638k has
strong geometry and above-dense Task29-C quality, but the gain is not simply
determined by `nearest_cluster_hit@3`.

The paper should therefore use Task30 as diagnostic support for the manifold
assumption, not as a theorem-level proof.

## Artifacts

- Script: `paper/experiments/scripts/task30_lotte_geometry_scale_validation.py`
- CSV: `paper/experiments/results/task30_lotte_geometry_scale_validation.csv`
- Markdown table: `paper/experiments/results/task30_lotte_geometry_scale_validation.md`
