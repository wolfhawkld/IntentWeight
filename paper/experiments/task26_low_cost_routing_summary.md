# Task26 Low-Cost Routing Summary

Task26 tests the follow-up hypothesis from Task25: once route-level credit
assignment shows that LinUCB cluster selection can improve, can the system
reduce dense/BM25 dependence and lower source-candidate cost?

The experiment keeps `reward_attribution=cluster_only` and
`confidence_mode=value`, then changes routing depths and confidence thresholds.
All formal rows use LoTTE technology/search 100k, held-out test queries,
`seeds=13,17,19`, `epochs=8`, and shared cached artifacts.

## Results

Reference points:

- Pure dense 100k baseline: `Hit@10=0.8674`, source candidate cost `100`.
- Full multi-route reference: source candidate cost `300`.
- Task25 cluster-credit route: `Hit@10=0.8764`, avg cost `181.47`.

| Config | Hit@10 | Evidence Recall@10 | Avg Cost | Last Epoch Cost | Dense Rate | Primary Rate | Fallback Rate | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Task25 `cluster_only/value` | 0.8764 | 0.6829 | 181.47 | 156.02 | 0.6708 | 0.3292 | 0.2757 | Stronger quality, still dense-heavy |
| Task26 A cost-first smoke | 0.8523 | 0.6468 | 84.38 | 75.37 | 0.4461 | 0.5539 | 0.0826 | Below dense cost, but visible quality loss |
| Task26 B cost-balanced | 0.8579 | 0.6506 | 121.00 | 104.30 | 0.5540 | 0.4460 | 0.1591 | Near dense cost, below dense quality |
| Task26 E quality-first | 0.8663 | 0.6588 | 166.33 | 140.04 | 0.6708 | 0.3292 | 0.2757 | Nearly dense-quality, cheaper than Task25 |

## Interpretation

Task26 confirms a tunable quality-cost frontier rather than a free-lunch
replacement for dense retrieval.

The cost-first setting A proves that the system can reduce source-candidate
cost below pure dense's top-100 candidate count, but this costs roughly 1.5
Hit@10 points against the dense 100k baseline.

The balanced setting B lowers average cost from Task25's `181.47` to `121.00`
and lowers last-epoch cost to `104.30`, close to dense's top-100 candidate
count. However, Hit@10 remains below dense (`0.8579` vs `0.8674`).

The quality-first setting E nearly matches dense (`0.8663` vs `0.8674`) while
reducing average cost relative to Task25 from `181.47` to `166.33` and
last-epoch cost from `156.02` to `140.04`. It remains above pure dense source
candidate cost, but it is a cleaner quality-preserving cost-reduction point.

## Paper Impact

Task26 should be used to frame IntentWeight as an adaptive quality-cost
controller, not as a universal dense replacement.

The current evidence supports these claims:

- Route-level LinUCB feedback can improve the selected cluster route itself
  after only eight prequential epochs.
- Once that route is stronger, reducing dense/BM25 candidate depths produces
  a controllable quality-cost trade-off.
- Dense remains valuable as a recall floor. Aggressive dense reduction can beat
  dense on source-candidate cost, but it currently gives up retrieval quality.
- The best paper-safe claim is that IntentWeight can move along a Pareto
  frontier between dense-heavy quality preservation and low-cost cluster-heavy
  retrieval.

## Post-Task28 Token-Cost Correction

Task26's `Avg Cost` column is source candidate count, not final LLM context
tokens. Task28 recomputed final top-10 context tokens for the formal Task26
runs:

- Task26-B: `avg_context_tokens@10=1517.60`, `1.0307x` dense.
- Task26-E: `avg_context_tokens@10=1530.35`, `1.0394x` dense.

Therefore Task26 does not prove token-cost savings. It proves retrieval-stage
candidate reduction. Under the fixed top-10 final context policy, token savings
are absent.

Recommended paper wording:

> After route-level credit assignment, the LinUCB cluster route becomes strong
> enough to support lower-cost routing policies. On LoTTE 100k, a quality-first
> low-cost setting nearly matches dense retrieval while reducing source
> candidate cost relative to the previous cluster-credit gated policy, whereas
> more aggressive settings can approach or undercut dense candidate cost at the
> expense of Hit@10. This supports a quality-cost trade-off claim rather than a
> claim of unconditional dense replacement.

Artifacts:

- Comparison CSV: `paper/experiments/task26_low_cost_routing_comparison.csv`
- Cost-first smoke: `paper/experiments/results/task26_100k_lowcost_A_smoke/`
- Balanced smoke/formal: `paper/experiments/results/task26_100k_lowcost_B_smoke/`,
  `paper/experiments/results/task26_100k_lowcost_B_formal/`
- Exploratory C/D smokes: `paper/experiments/results/task26_100k_lowcost_C_smoke/`,
  `paper/experiments/results/task26_100k_lowcost_D_smoke/`
- Quality-first smoke/formal: `paper/experiments/results/task26_100k_lowcost_E_smoke/`,
  `paper/experiments/results/task26_100k_lowcost_E_formal/`
