# Task27 Dense-LinUCB Trade-off Summary

> **Paper-use status: boundary/negative evidence.**
> This file tests a stricter two-route dense-vs-LinUCB cost hypothesis. It is
> not positive evidence for token-cost savings or dense replacement: the
> sub-dense source-candidate setting loses retrieval quality, and final context
> token savings are not demonstrated.

Task27 tests a sharper version of the cost hypothesis: remove BM25 from the
main route and trade off only between global dense and the learned LinUCB
cluster route. The target is stricter than Task26:

> Can IntentWeight reach cost below pure dense's top-100 candidate budget while
> keeping Hit@10 close to, or above, pure dense?

Implementation change: `linucb_cost_aware_routing.py` now accepts
`bm25_depth=0` and `bm25_lite_depth=0`. When BM25 depth is zero, the runner does
not build or load a BM25 ranking artifact, and BM25 contributes zero candidates
to cost.

Reference points:

- Pure dense 100k baseline: `Hit@10=0.8674`, source candidate cost `100`.
- Task26 B with BM25: `Hit@10=0.8579`, avg cost `121.00`.
- Task26 E with BM25: `Hit@10=0.8663`, avg cost `166.33`.

## Results

All formal rows use LoTTE technology/search 100k, held-out test queries,
`reward_attribution=cluster_only`, `confidence_mode=value`, and
`epochs=8`.

| Config | Seeds | BM25 | Hit@10 | Evidence Recall@10 | Avg Cost | Last Epoch Cost | Dense Rate | Primary Rate | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A cost-first smoke | 13 | off | 0.8456 | 0.6413 | 92.00 | 86.29 | 0.4427 | 0.5573 | Below dense cost, too much quality loss |
| B sub-dense cost | 13,17,19 | off | 0.8535 | 0.6447 | 97.76 | 89.25 | 0.4894 | 0.5106 | Meets cost target, still below dense quality |
| C near-boundary | 13,17,19 | off | 0.8535 | 0.6352 | 107.18 | 99.35 | 0.4785 | 0.5215 | Slightly above dense cost, no quality gain |
| D aggressive gate smoke | 13 | off | 0.8490 | 0.6501 | 91.12 | 86.01 | 0.3840 | 0.6160 | Lower dense rate hurts quality |
| E cluster85 smoke | 13 | off | 0.8574 | 0.6573 | 98.79 | 92.51 | 0.4427 | 0.5573 | Best sub-100 smoke, not formal |
| F quality smoke | 13 | off | 0.8624 | 0.6598 | 132.59 | 120.50 | 0.6422 | 0.3578 | Better quality requires higher cost |

## Interpretation

Task27 gives a negative-but-useful answer to the strict hypothesis. With BM25
removed and cost held below the dense top-100 candidate budget, the best formal
two-route setting reaches `Hit@10=0.8535` at average cost `97.76`. This proves
that the dense-LinUCB two-route controller can reduce candidate count below
pure dense, but not yet without visible quality loss.

The quality-first smoke setting reaches `Hit@10=0.8624`, closer to pure dense,
but its cost rises to `132.59`. This mirrors Task26's conclusion: dense remains
an important recall floor, and reducing dense too aggressively moves the system
down the quality-cost frontier.

BM25 is not merely free noise in the current LoTTE setup. Comparing Task26 and
Task27, removing BM25 lowers cost, but it also makes it harder to recover
quality near dense. The safer interpretation is:

- Dense is still the dominant quality anchor on LoTTE 100k.
- LinUCB cluster routing supplies a learnable low-cost route and can reduce
  dense usage.
- BM25 can be omitted for a cleaner dense-vs-LinUCB study, but the resulting
  two-route system has not yet achieved sub-dense cost with dense-level quality.

## Paper Impact

Task27 should be reported as a boundary experiment. It strengthens the paper by
showing that the authors tested the most direct cost hypothesis and did not
overclaim it.

## Post-Task28 Token-Cost Correction

Task27's cost target was source candidate count, not final LLM context tokens.
Task28 recomputed final top-10 context tokens:

- Task27-B formal: `avg_context_tokens@10=1479.17`, `1.0046x` dense.
- Task27-C formal: `avg_context_tokens@10=1494.21`, `1.0148x` dense.
- Task27-F smoke: `avg_context_tokens@10=1521.45`, `1.0333x` dense.

Thus even the sub-dense source-candidate setting does not produce meaningful
final context token savings under fixed top-10 generation. Task27 remains valid
as a retrieval-candidate boundary experiment, but not as evidence of LLM token
cost superiority.

Recommended wording:

> We further tested a two-route variant that removes BM25 and trades off only
> between global dense retrieval and the learned LinUCB cluster route. This
> variant can reduce source candidate cost below dense-only, but on LoTTE 100k
> it does not yet match dense Hit@10 under that stricter cost budget. The result
> indicates that IntentWeight currently provides a tunable quality-cost frontier
> rather than a guaranteed sub-dense-cost replacement for dense retrieval.

Artifacts:

- Comparison CSV: `paper/experiments/task27_dense_linucb_tradeoff_comparison.csv`
- BM25-disabled runner/test changes:
  `paper/experiments/scripts/linucb_cost_aware_routing.py`,
  `cache/test_linucb_cost_aware_routing.py`
- Main formal result:
  `paper/experiments/results/task27_100k_dense_linucb_B_formal/`
- Boundary formal result:
  `paper/experiments/results/task27_100k_dense_linucb_C_formal/`
