# Task29 Confidence-Based Final Context Policy

Task29 tests the correction raised by Task28: reducing retrieval-stage candidate
count is not enough to prove lower LLM input cost. The final generation context
must also be controlled directly.

## Method Change

`linucb_cost_aware_routing.py` now supports `final_context_policy`.

- `fixed_topk`: previous behavior; always return the final top-k chunks.
- `confidence_topk`: compact final context only when the selected route is
  `linucb_primary` or `hybrid_lite`, semantic drift passes the same gate, and
  LinUCB confidence crosses the configured threshold.

For Task29-C, the policy is conservative:

- high-confidence route: final `k=8`
- mid-confidence route: final `k=10`
- fallback route: final `k=10`

This means dense fallback is not compressed; only confident LinUCB-controlled
routes are allowed to reduce final LLM context.

## LoTTE 100k Smoke Frontier

All rows use seed 13, `cluster_only` credit, `confidence_mode=value`,
8 epochs, and `cl100k_base` final context token counting.

| Config | Final Context Policy | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---|---:|---:|---:|---:|
| Dense top-10 | fixed top-10 | 0.8674 | 1472.39 | 1.0000 | 0.0000 |
| Task29-A | high `k=5`, mid `k=7` | 0.8339 | 999.38 | 0.6787 | -0.0336 |
| Task29-B | high `k=7`, mid `k=9` | 0.8490 | 1261.91 | 0.8570 | -0.0185 |
| Task29-C | high `k=8`, mid `k=10` | 0.8624 | 1391.59 | 0.9451 | -0.0050 |

The frontier behaves as expected: more aggressive context compaction saves more
tokens but loses more retrieval coverage.

## Task29-C Formal Result

Three-seed formal run: seeds 13, 17, 19.

| Run | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---:|---:|---:|---:|
| Dense top-10 | 0.8674 | 1472.39 | 1.0000 | 0.0000 |
| Task29-C seed 13 | 0.8624 | 1391.59 | 0.9451 | -0.0050 |
| Task29-C seed 17 | 0.8641 | 1398.18 | 0.9496 | -0.0034 |
| Task29-C seed 19 | 0.8691 | 1413.95 | 0.9603 | +0.0017 |
| Task29-C mean | 0.8652 | 1401.24 | 0.9517 | -0.0022 |

Task29-C therefore shows a conservative, paper-safe token-cost result:

> Confidence-based final context compaction reduces LoTTE 100k final context
> tokens by about 4.8% on average while preserving near-dense retrieval quality
> (`Hit@10` within about 0.22 percentage points of dense-only).

## Interpretation

Task29 changes the cost claim from the earlier source-candidate proxy to a real
final-context-token measurement. The result does not prove a large token saving
yet, but it does prove the mechanism is viable:

- Fixed top-10 multi-route retrieval does not save LLM context tokens.
- Confidence-gated final context compaction can reduce final tokens directly.
- Conservative compaction preserves near-dense quality.
- Aggressive compaction offers larger token savings at a clear quality cost.

This is the correct direction for the paper's efficiency claim: IntentWeight
should be described as a feedback-improved retrieval controller that can trade
off answer evidence coverage and final context token budget, rather than a
method that automatically saves tokens from multi-route retrieval alone.

## Artifacts

- Script: `paper/experiments/scripts/linucb_cost_aware_routing.py`
- Token evaluator: `paper/experiments/scripts/context_token_cost.py`
- Smoke token table: `paper/experiments/results/task29_lotte100k_context_tokens_smoke.md`
- Formal result dir: `paper/experiments/results/task29_100k_confidence_topk_C_formal/`
- Formal token table:
  `paper/experiments/results/task29_100k_confidence_topk_C_formal/context_tokens.md`
