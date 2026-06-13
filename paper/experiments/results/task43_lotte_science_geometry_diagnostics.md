# LoTTE science/search Geometry Validation

This diagnostic checks whether the LoTTE results are consistent with a
retrieval-geometry interpretation. It reuses the canonical scale-store
embeddings, shared PCA/KMeans context artifacts, and IntentWeight fixed top-10
metrics. No retrieval or LinUCB experiment is rerun.

## Multi-Scale Table

| Scale | Corpus | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Dense Hit@10 | IntentWeight fixed top-10 Hit@10 | Hit Delta | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20k_q200 | 20490 | 180 | 0.6377 | 0.9083 | 0.8939 | 0.8950 | 0.9267 | 3.17 pp | 13.80% |
| 100k | 101187 | 177 | 0.6459 | 0.8574 | 0.8628 | 0.8926 | 0.9077 | 1.51 pp | 19.09% |

## Correlation Diagnostics

- Pearson(`nearest_cluster_hit@3`, `IntentWeight fixed top-10 Hit Delta`) = `1.0000`.
- Pearson(`context_recall_retention@10`, `IntentWeight fixed top-10 Hit Delta`) = `1.0000`.
- Pearson(`nearest_cluster_hit@3`, `Token Saving`) = `-1.0000`.

These correlations use only 2 scale/domain points, so they are descriptive
diagnostics, not statistical proof.

## Interpretation

- The LoTTE corpus keeps high nearest-cluster GT routing signal across scale,
  with `nearest_cluster_hit@3` staying around the high-0.8 range.
- PCA/context retrieval alone retains a large fraction of dense Hit@10, but
  it does not fully replace dense retrieval. This supports the paper's
  bounded claim: geometry is useful as a routing/control signal, not as a
  stand-alone dense replacement.
- Dense Hit@10 and IntentWeight fixed top-10 Hit@10 should be read together with
  token saving to identify where compression remains safe.
- This supports the piecewise relevance-manifold framing as an explanatory
  assumption backed by diagnostics. It should not be written as a theorem
  that geometry alone guarantees better retrieval.

## Artifacts

- CSV: `paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv`
- Script: `paper/experiments/scripts/task30_lotte_geometry_scale_validation.py`
