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

LoTTE 100k three-seed formal run: seeds 13, 17, 19.

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

## Task29.1 LoTTE 200k Scale-Up

The same conservative Task29-C policy was then run on LoTTE 200k with the same
three seeds.

| Run | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---:|---:|---:|---:|
| Dense top-10 | 0.7970 | 1444.12 | 1.0000 | 0.0000 |
| Task29-C seed 13 | 0.8339 | 1376.87 | 0.9534 | +0.0369 |
| Task29-C seed 17 | 0.8188 | 1371.66 | 0.9498 | +0.0218 |
| Task29-C seed 19 | 0.8221 | 1380.85 | 0.9562 | +0.0252 |
| Task29-C mean | 0.8249 | 1376.46 | 0.9531 | +0.0280 |

The 200k result strengthens the efficiency claim:

> On a larger LoTTE corpus, confidence-based final context compaction reduces
> final context tokens by about 4.7% while improving `Hit@10` over dense-only by
> about 2.8 percentage points.

This suggests that the policy can become more useful as corpus scale increases,
where pure dense top-10 becomes less dominant and feedback-guided route control
can preserve better evidence coverage with fewer final context tokens.

## Task29.1 LoTTE 400k Scale-Up

The same Task29-C policy was also run on LoTTE 400k using the canonical scale
store corpus embeddings.

| Run | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---:|---:|---:|---:|
| Dense top-10 | 0.7718 | 1482.30 | 1.0000 | 0.0000 |
| Task29-C seed 13 | 0.7802 | 1401.14 | 0.9453 | +0.0084 |
| Task29-C seed 17 | 0.7869 | 1373.53 | 0.9266 | +0.0151 |
| Task29-C seed 19 | 0.7785 | 1435.61 | 0.9685 | +0.0067 |
| Task29-C mean | 0.7819 | 1403.43 | 0.9468 | +0.0101 |

The 400k result remains positive:

> On LoTTE 400k, Task29-C reduces final context tokens by about 5.3% while
> improving `Hit@10` over dense-only by about 1.0 percentage point.

Together, the 100k/200k/400k runs show a consistent final-context-token saving
pattern. The retrieval-quality delta varies with scale, but the conservative
confidence compaction policy never shows the strong quality collapse seen in
the aggressive A/B smoke settings.

## Task29.1 LoTTE 638k Scale-Up

The same Task29-C policy was finally run on the full LoTTE technology/search
test corpus slice (`638509` chunks) using the canonical scale store and shared
retrieval artifacts.

| Run | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---:|---:|---:|---:|
| Dense top-10 | 0.7282 | 1525.62 | 1.0000 | 0.0000 |
| Task29-C seed 13 | 0.7567 | 1455.79 | 0.9542 | +0.0285 |
| Task29-C seed 17 | 0.7399 | 1448.44 | 0.9494 | +0.0117 |
| Task29-C seed 19 | 0.7433 | 1450.23 | 0.9506 | +0.0151 |
| Task29-C mean | 0.7466 | 1451.49 | 0.9514 | +0.0185 |

The 638k result completes the scale-up chain:

> On LoTTE 638k, Task29-C reduces final context tokens by about 4.9% while
> improving `Hit@10` over dense-only by about 1.85 percentage points.

This is the strongest large-scale token-quality result so far because it uses
the full available LoTTE technology/search corpus size while preserving the same
conservative final-context policy.

## Task29.2 Frontier Consolidation

Task29.2 consolidates the scale and strategy results into a paper-facing
token-quality frontier.

| Scale | Method | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Hit Delta vs Dense |
|---|---|---:|---:|---:|---:|
| 100k | Task29-C mean | 0.8652 | 1401.24 | 0.9517 | -0.0022 |
| 200k | Task29-C mean | 0.8249 | 1376.46 | 0.9531 | +0.0280 |
| 400k | Task29-C mean | 0.7819 | 1403.43 | 0.9468 | +0.0101 |
| 638k | Task29-C mean | 0.7466 | 1451.49 | 0.9514 | +0.0185 |

The consolidated frontier supports using Task29-C as the main paper result and
Task29-A/B as ablations. Detailed frontier tables are stored in
`paper/experiments/task29_2_token_quality_frontier.md` and
`paper/experiments/results/task29_token_quality_frontier.csv`.

## Interpretation

Task29 changes the cost claim from the earlier source-candidate proxy to a real
final-context-token measurement. The result does not prove a large token saving
yet, but it does prove the mechanism is viable:

- Fixed top-10 multi-route retrieval does not save LLM context tokens.
- Confidence-gated final context compaction can reduce final tokens directly.
- Conservative compaction preserves near-dense quality.
- Aggressive compaction offers larger token savings at a clear quality cost.
- The 200k scale-up shows the same conservative policy can outperform dense
  quality while still reducing final context tokens.
- The 400k scale-up keeps the same direction: lower final tokens and above-dense
  `Hit@10`.
- The 638k full-corpus scale-up completes the pattern with lower final tokens
  and above-dense `Hit@10` on the largest LoTTE setting.

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
- 200k formal result dir: `paper/experiments/results/task29_200k_confidence_topk_C_formal/`
- 200k formal token table:
  `paper/experiments/results/task29_200k_confidence_topk_C_formal/context_tokens.md`
- 400k formal result dir: `paper/experiments/results/task29_400k_confidence_topk_C_formal/`
- 400k formal token table:
  `paper/experiments/results/task29_400k_confidence_topk_C_formal/context_tokens.md`
- 638k formal result dir: `paper/experiments/results/task29_638k_confidence_topk_C_formal/`
- 638k formal token table:
  `paper/experiments/results/task29_638k_confidence_topk_C_formal/context_tokens.md`
