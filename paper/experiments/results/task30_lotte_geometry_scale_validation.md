# Task30 LoTTE Multi-Scale Geometry Validation

Task30 checks whether the LoTTE scale-up results are consistent with a
retrieval-geometry interpretation. It reuses the canonical scale-store
embeddings, shared PCA/KMeans context artifacts, and Task29-C token-quality
frontier. No retrieval or LinUCB experiment is rerun.

## Multi-Scale Table

| Scale | Corpus | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Dense Hit@10 | Task29-C Hit@10 | Hit Delta | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100k | 101311 | 182 | 0.6437 | 0.8870 | 0.9033 | 0.8674 | 0.8652 | -0.22 pp | 4.83% |
| 200k | 201010 | 186 | 0.6292 | 0.8697 | 0.8947 | 0.7970 | 0.8249 | 2.80 pp | 4.69% |
| 400k | 400674 | 190 | 0.6110 | 0.9016 | 0.8826 | 0.7718 | 0.7819 | 1.01 pp | 5.32% |
| 638k | 638509 | 196 | 0.5867 | 0.9016 | 0.8571 | 0.7282 | 0.7466 | 1.85 pp | 4.86% |

## Correlation Diagnostics

- Pearson(`nearest_cluster_hit@3`, `Task29 Hit Delta`) = `-0.3933`.
- Pearson(`context_recall_retention@10`, `Task29 Hit Delta`) = `-0.3597`.
- Pearson(`nearest_cluster_hit@3`, `Token Saving`) = `0.7134`.

These correlations use only four scale points, so they are descriptive
diagnostics, not statistical proof.

## Interpretation

- The LoTTE corpus keeps high nearest-cluster GT routing signal across scale,
  with `nearest_cluster_hit@3` staying around the high-0.8 range.
- PCA/context retrieval alone retains a large fraction of dense Hit@10, but
  it does not fully replace dense retrieval. This supports the paper's
  bounded claim: geometry is useful as a routing/control signal, not as a
  stand-alone dense replacement.
- Dense Hit@10 declines as corpus scale grows, while Task29-C remains
  above dense at 200k/400k/638k with lower final context tokens.
- This supports the piecewise relevance-manifold framing as an explanatory
  assumption backed by diagnostics. It should not be written as a theorem
  that geometry alone guarantees better retrieval.

## Artifacts

- CSV: `paper/experiments/results/task30_lotte_geometry_scale_validation.csv`
- Script: `paper/experiments/scripts/task30_lotte_geometry_scale_validation.py`
