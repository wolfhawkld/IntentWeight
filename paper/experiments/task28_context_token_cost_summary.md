# Task28 Final Context Token-Cost Summary

> **Paper-use status: supporting guardrail.**
> Use this file to explain why historical source-candidate reductions are not
> enough for token-cost claims. It is not the positive final token-saving
> result; use the confidence-based final context policy results for that.

Task28 corrects the cost interpretation used in earlier routing tasks. Previous
tasks reported `avg_source_candidate_cost`, an unweighted retrieval-stage
candidate-count proxy. That proxy does not measure final LLM context tokens.

Task28 recomputes final top-10 context tokens from saved rankings and corpus
chunk text using `tiktoken` `cl100k_base`. Token metrics count retrieved chunk
text only. They do not include system prompts, instructions, generated output,
or reranker internals.

## LoTTE 100k Key Results

Baseline:

- Dense-only: `Hit@10=0.8674`, `avg_context_tokens@10=1472.39`.

| Config | Runs | Hit@10 | Avg Context Tokens@10 | Token Ratio vs Dense | Token Delta vs Dense | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| dense | 1 | 0.8674 | 1472.39 | 1.0000 | 0.00 | Token baseline |
| Task19-D | 3 | 0.8770 | 1518.44 | 1.0313 | +46.05 | Better retrieval quality, slightly more context tokens |
| Task19-E | 3 | 0.8865 | 1549.83 | 1.0526 | +77.45 | Highest quality, more context tokens |
| Task20-S | 3 | 0.8747 | 1516.24 | 1.0298 | +43.86 | Better quality, no token saving |
| Task25 cluster-credit | 3 | 0.8764 | 1550.65 | 1.0532 | +78.26 | Route learning improves, but final context tokens increase |
| Task26-B | 3 | 0.8579 | 1517.60 | 1.0307 | +45.21 | Source candidates drop, context tokens do not |
| Task26-E | 3 | 0.8663 | 1530.35 | 1.0394 | +57.96 | Near dense quality, more context tokens |
| Task27-B | 3 | 0.8535 | 1479.17 | 1.0046 | +6.79 | Source candidates below dense, context tokens roughly equal/slightly higher |
| Task27-C | 3 | 0.8535 | 1494.21 | 1.0148 | +21.83 | No token-cost win |
| Task27-F smoke | 1 | 0.8624 | 1521.45 | 1.0333 | +49.07 | More quality than B, more tokens |

## Interpretation

The strongest intended claim is not supported by the current final-context-token
evidence:

> LinUCB after feedback does not currently reduce final top-10 context tokens
> below dense-only while preserving dense-level retrieval quality on LoTTE 100k.

The earlier candidate-cost findings still remain useful, but they must be
reframed:

- Task19/20/25 improve retrieval quality or route learning, but final context
  tokens are slightly higher than dense.
- Task26 reduces retrieval source candidates, but final top-10 context tokens
  remain higher than dense.
- Task27-B reduces retrieval source candidate count below dense, but final
  context token count is essentially the same as dense and retrieval quality is
  lower.

This happens because final generation still uses a fixed top-10 context. Even
when retrieval-stage candidates are reduced, the final answer context still
contains ten chunks with similar or slightly larger average token lengths.

## Corrected Paper Claim

Use:

> IntentWeight reduces retrieval-stage candidate volume and dense invocation
> rate under some routing policies, while preserving or improving retrieval
> quality in quality-first settings.

Do not use:

> IntentWeight has been shown to reduce LLM context token cost.

Use:

> Final-context-token savings remain unproven under fixed top-10 generation.

Do not use:

> Candidate-count cost below dense implies token-cost below dense.

## What Would Be Needed To Prove Token Savings

A future task must change the final-context policy, not only the retrieval
candidate policy. Plausible designs:

- variable top-k: allow confident LinUCB routes to send fewer final chunks;
- token-budgeted context packing: stop adding chunks after a fixed token budget;
- confidence-based evidence compression: summarize or trim low-marginal chunks;
- answerability-aware stopping: stop retrieval/context expansion when evidence
  confidence is high.

Only these designs can directly test whether LinUCB feedback can reduce final
LLM input tokens while preserving answer evidence.

Artifacts:

- Script: `paper/experiments/scripts/context_token_cost.py`
- Per-run table: `paper/experiments/results/task28_lotte100k_context_tokens.csv`
- Aggregated table: `paper/experiments/results/task28_lotte100k_context_tokens_aggregated.csv`
- Markdown table: `paper/experiments/results/task28_lotte100k_context_tokens.md`
