# Task33.6 Additional Seed Stability Summary

Updated: 2026-05-27

## Purpose

Task33.6 extends the key LoTTE 100k Task29-C configuration from three seeds
(`13,17,19`) to five seeds by adding seeds `23` and `29`.

This is a stability check for KMeans arm initialization, LinUCB stochastic
order effects, and route-policy variance. It is not a new main experiment and
should not be framed as a statistical superiority test.

## Configuration

- Dataset: `lotte_technology_search_100k`
- Query split: `test`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Routing mode: `gated_cost_aware`
- Reward attribution: `cluster_only`
- Confidence mode: `value`
- Final context policy: `confidence_topk`
- Epochs: `8`
- KMeans arms: `32`
- Original seeds: `13,17,19`
- Additional seeds: `23,29`

## Result

| Seed group | Seeds | Hit@10 | Avg context tokens@10 | Token ratio vs dense | Token saving |
|---|---:|---:|---:|---:|---:|
| Task29-C original | 3 | 0.8652 | 1401.24 | 0.9517x | 4.83% |
| Task33.6 additional | 2 | 0.8792 | 1397.71 | 0.9493x | 5.07% |
| Combined | 5 | 0.8708 | 1399.83 | 0.9507x | 4.93% |

Dense baseline on the same LoTTE 100k setting:

- Hit@10: `0.8674`
- Avg context tokens@10: `1472.39`
- Token ratio: `1.0000x`

The five-seed Task29-C mean is therefore `+0.34` percentage points over dense
Hit@10 while using `4.93%` fewer final retrieved context tokens.

## Five-Seed Confidence Intervals

The intervals below use the five seed-level observations and a two-sided
t interval with `df=4`. They should be treated as engineering stability
diagnostics rather than strong statistical significance evidence.

| Metric | Mean | 95% CI |
|---|---:|---:|
| Hit@10 | 0.8708 | [0.8592, 0.8824] |
| Avg context tokens@10 | 1399.83 | [1385.00, 1414.66] |
| Token ratio vs dense | 0.9507x | [0.9406x, 0.9608x] |
| Hit delta vs dense | +0.0034 | [-0.0082, +0.0150] |

Interpretation:

- The token-saving result remains stable across five seeds.
- Hit@10 remains near dense and slightly above dense on average.
- The Hit@10 delta interval overlaps zero, so the paper should not claim
  statistically significant retrieval-quality improvement at LoTTE 100k.
- The stronger claim is stability: Task29-C preserves dense-level retrieval
  quality while reducing final retrieved context tokens.

## Route Diagnostics

Combined five-seed route-policy diagnostics:

| Metric | Mean |
|---|---:|
| Dense query rate | 0.6494 |
| LinUCB primary rate | 0.3506 |
| Selected-cluster hit rate | 0.7378 |
| Last true reward | 0.8419 |
| Source candidate cost | 205.85 |
| Final context k | 9.30 |

These diagnostics support the intended interpretation: Task29-C is not
eliminating dense retrieval. It uses LinUCB confidence and route quality to
reduce dense dependence and compact the final context while retaining a dense
fallback for quality protection.

## Paper Use

Use Task33.6 in the seed-stability subsection or appendix. The safe wording is:

> Extending the LoTTE 100k Task29-C policy from three to five seeds preserves
> the original conclusion: final retrieved context tokens are reduced by about
> 5% while Hit@10 remains dense-level. The quality delta is not statistically
> significant at this seed count, but the token-reduction direction is stable.

Do not use Task33.6 to claim that IntentWeight significantly beats dense on
LoTTE 100k.

## Artifacts

- Extra seed LinUCB results:
  `paper/experiments/results/task33_6_100k_extra_seeds/`
- Five-seed context-token table:
  `paper/experiments/results/task33_6_100k_5seed_context_tokens.md`
- Five-seed context-token CSV:
  `paper/experiments/results/task33_6_100k_5seed_context_tokens.csv`
