# Task28.1 Historical Context Token Backfill

Task28 corrected the cost interpretation on a focused LoTTE 100k set. Task28.1
extends the same correction to saved historical Task16-25 artifacts without
rerunning retrieval. It reads existing final rankings, counts retrieved chunk
text with `cl100k_base`, and reports final top-k context tokens alongside the
older source-candidate proxy cost.

## Scope

- Script: `paper/experiments/scripts/task28_1_backfill_context_tokens.py`
- Outputs:
  - `paper/experiments/results/task28_1_context_token_backfill.csv`
  - `paper/experiments/results/task28_1_context_token_backfill.json`
  - `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv`
  - `paper/experiments/results/task28_1_context_token_backfill.md`
- Covered saved ranking artifacts: Banking77, CUAD, eManual, LoTTE sample,
  LoTTE 100k, 200k, 400k, and 638k.
- Total rows: 106 per-run rows and 48 aggregated rows.

This task does not reuse old metric summaries as final evidence. It only reuses
deterministic artifacts that define the already completed retrieval outputs:
corpus, queries, dense baselines, and saved ranking files.

## Key Findings

Historical `avg_source_candidate_cost` reductions do not generally imply lower
final LLM context token usage under a fixed top-10 generation surface.

Representative examples:

| Dataset/Scale | Run | Hit@10 | Avg context tokens@10 | Ratio vs dense | Source candidate cost |
|---|---|---:|---:|---:|---:|
| Banking77 | gated cost-aware | 0.9813 | 120.82 | 0.9978x | 142.51 |
| eManual | gated cost-aware | 0.0116 | 17.92 | 0.9829x | 214.07 |
| LoTTE 100k | Task19-D | 0.8770 | 1518.44 | 1.0313x | 229.97 |
| LoTTE 100k | Task20-S | 0.8747 | 1516.24 | 1.0298x | 227.29 |
| LoTTE 100k | Task25 cluster-credit | 0.8764 | 1550.65 | 1.0532x | 181.47 |
| LoTTE 200k | Task22 formal gated | 0.8154 | 1549.39 | 1.0729x | 232.01 |
| LoTTE 400k | Task22 formal gated | 0.7836 | 1547.66 | 1.0441x | 233.22 |
| LoTTE 638k | Task22 formal gated | 0.7343 | 1599.95 | 1.0487x | 236.22 |

The most important correction is therefore:

- Task16-27 candidate-cost claims should be interpreted as retrieval-stage
  source-candidate or dense-invocation reductions.
- They should not be used as evidence that final prompt/context token cost is
  lower than dense-only retrieval.
- Task29 is the first experiment family that directly changes final context
  size through `final_context_policy=confidence_topk`.

## Paper Implication

The paper should separate three cost layers:

1. Source candidate cost: how many candidates each retrieval route considers.
2. Dense invocation / dense query rate: how often the expensive dense path is
   invoked.
3. Final context token cost: how many retrieved chunk tokens are sent to the
   generator.

Task16-27 support the first two layers. Task28.1 prevents those claims from
being overstated. Task29 supplies the final-context-token evidence.

## Caveats

- Token metrics count retrieved chunk text only. They do not include prompt
  scaffolding, generated output, reranker internals, or embedding compute.
- Fixed top-10 rankings can select longer or shorter chunks depending on the
  retrieval policy, so source candidate reductions are not expected to map
  monotonically to final context token savings.
- CUAD and eManual remain limitation/stress cases for separate reasons already
  documented in earlier tasks.
