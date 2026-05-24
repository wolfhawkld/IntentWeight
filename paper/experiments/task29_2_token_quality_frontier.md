# Task29.2 Token-Quality Frontier

Task29.2 consolidates the confidence-based final context policy results into a
paper-facing Pareto frontier. The key distinction is that this frontier measures
final retrieved context tokens, not retrieval-stage candidate counts.

All token metrics use `cl100k_base` and count retrieved chunk text only. They do
not include system prompts, generation output, reranker internals, or future
LLM summarization/compression prompts.

## Conservative Scale Frontier

Task29-C uses the conservative final context policy:

- high-confidence LinUCB route: final `k=8`
- mid-confidence LinUCB route: final `k=10`
- dense fallback: final `k=10`

| Scale | Method | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Token Saving | Hit Delta vs Dense | Hit / 1k Tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | Dense top-10 | 0.8674 | 1472.39 | 1.0000 | 0.00% | 0.00 pp | 0.5891 |
| 100k | Task29-C mean | 0.8652 | 1401.24 | 0.9517 | 4.83% | -0.22 pp | 0.6175 |
| 200k | Dense top-10 | 0.7970 | 1444.12 | 1.0000 | 0.00% | 0.00 pp | 0.5519 |
| 200k | Task29-C mean | 0.8249 | 1376.46 | 0.9531 | 4.69% | +2.80 pp | 0.5993 |
| 400k | Dense top-10 | 0.7718 | 1482.30 | 1.0000 | 0.00% | 0.00 pp | 0.5207 |
| 400k | Task29-C mean | 0.7819 | 1403.43 | 0.9468 | 5.32% | +1.01 pp | 0.5571 |
| 638k | Dense top-10 | 0.7282 | 1525.62 | 1.0000 | 0.00% | 0.00 pp | 0.4773 |
| 638k | Task29-C mean | 0.7466 | 1451.49 | 0.9514 | 4.86% | +1.85 pp | 0.5144 |

## 100k Strategy Frontier

The 100k smoke frontier shows how final context compaction strength changes the
quality-cost trade-off. These are seed-13 smoke runs and should be used as
frontier exploration, not as the main formal result.

| Config | Final Context Policy | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Token Saving | Hit Delta vs Dense | Hit / 1k Tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| Dense top-10 | fixed top-10 | 0.8674 | 1472.39 | 1.0000 | 0.00% | 0.00 pp | 0.5891 |
| Task29-A | high `k=5`, mid `k=7` | 0.8339 | 999.38 | 0.6787 | 32.13% | -3.36 pp | 0.8344 |
| Task29-B | high `k=7`, mid `k=9` | 0.8490 | 1261.91 | 0.8570 | 14.30% | -1.85 pp | 0.6728 |
| Task29-C | high `k=8`, mid `k=10` | 0.8624 | 1391.59 | 0.9451 | 5.49% | -0.50 pp | 0.6197 |

## Interpretation

The frontier supports three claims:

1. Fixed top-10 multi-route retrieval does not itself reduce final context
   tokens. Task28 already showed that source-candidate reductions do not
   automatically translate to LLM input savings.
2. Confidence-based final context control does reduce final context tokens
   directly. The conservative Task29-C policy reduces final context tokens by
   about 4.7-5.3% across 100k, 200k, 400k, and 638k.
3. The quality-cost trade-off is controllable. Aggressive compaction saves many
   more tokens but has visible recall loss; conservative compaction gives a
   smaller but paper-safe saving and preserves near-/above-dense quality.

The most paper-safe summary is:

> IntentWeight does not automatically save LLM context tokens by using multiple
> retrieval routes. However, once LinUCB confidence is used to control the final
> context budget, the system can reduce retrieved context tokens while
> preserving near-dense quality, and on larger LoTTE scales it can outperform
> dense-only retrieval with fewer final context tokens.

Task29.3 adds seed-level stability diagnostics for this frontier. Across
100k/200k/400k/638k, Task29-C token saving remains positive in the three-seed
means, with mean savings in the narrow `4.69%` to `5.32%` band. Because each
scale only has three seeds, the confidence intervals are reported as stability
diagnostics, not as strong statistical significance claims.

## Paper Usage

Use Task29-C as the main result because it is conservative and has three-seed
formal runs at 100k/200k/400k/638k.

Use Task29-A/B only as a Pareto frontier or ablation showing the expected
trade-off between token saving and evidence coverage.

Avoid claiming end-to-end LLM cost savings unless a later experiment measures
full prompt and output tokens. The supported claim is final retrieved context
token reduction.

## Artifacts

- Frontier CSV: `paper/experiments/results/task29_token_quality_frontier.csv`
- 100k formal token table:
  `paper/experiments/results/task29_100k_confidence_topk_C_formal/context_tokens.md`
- 200k formal token table:
  `paper/experiments/results/task29_200k_confidence_topk_C_formal/context_tokens.md`
- 400k formal token table:
  `paper/experiments/results/task29_400k_confidence_topk_C_formal/context_tokens.md`
- 638k formal token table:
  `paper/experiments/results/task29_638k_confidence_topk_C_formal/context_tokens.md`
- Seed variance / CI table:
  `paper/experiments/results/task29_3_seed_variance_ci.md`
