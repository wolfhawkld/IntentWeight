# Task29.3 Seed Variance and Confidence Intervals

Task29.3 reports cross-seed stability for the conservative Task29-C
`confidence_topk` policy across LoTTE 100k/200k/400k/638k.

All intervals are two-sided 95% t intervals over three random seeds
(`13,17,19`). With only three seeds, these intervals should be read as
engineering stability diagnostics rather than strong inferential proof.

## Hit@10 Stability

| Scale | Dense Hit@10 | Task29-C mean | Std | 95% CI | Hit delta mean |
|---|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8652 | 0.0035 | [0.8565, 0.8739] | -0.0022 |
| 200k | 0.7970 | 0.8249 | 0.0079 | [0.8052, 0.8446] | 0.0280 |
| 400k | 0.7718 | 0.7819 | 0.0044 | [0.7709, 0.7929] | 0.0101 |
| 638k | 0.7282 | 0.7466 | 0.0089 | [0.7246, 0.7687] | 0.0185 |

## Final Context Token Stability

| Scale | Dense tokens@10 | Task29-C mean tokens@10 | Std | 95% CI | Saving mean | Saving 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 1472.39 | 1401.24 | 11.49 | [1372.70, 1429.79] | 4.83% | [2.89%, 6.77%] |
| 200k | 1444.12 | 1376.46 | 4.61 | [1365.01, 1387.91] | 4.69% | [3.89%, 5.48%] |
| 400k | 1482.30 | 1403.43 | 31.10 | [1326.16, 1480.69] | 5.32% | [0.11%, 10.53%] |
| 638k | 1525.62 | 1451.49 | 3.83 | [1441.97, 1461.00] | 4.86% | [4.24%, 5.48%] |

## Interpretation

- Token saving is stable across all four scales: the mean saving stays in the
  narrow `4.69%` to `5.32%` band.
- Hit@10 is near dense at 100k and above dense at 200k, 400k, and 638k.
- The 638k full-corpus result has above-dense Hit@10 with lower final
  context tokens, strengthening the large-scale efficiency claim.
- Because each scale has only three seeds, the CI bands are intentionally
  reported as stability diagnostics; the paper should avoid overclaiming
  statistical significance from this table alone.

## Artifacts

- CSV: `paper/experiments/results/task29_3_seed_variance_ci.csv`
- Source token tables:
  `paper/experiments/results/task29_{scale}_confidence_topk_C_formal/context_tokens.csv`
