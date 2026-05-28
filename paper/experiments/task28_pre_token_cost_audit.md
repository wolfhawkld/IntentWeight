# Pre-Task28 Token-Cost Scope Audit

> **Paper-use status: historical/superseded guardrail.**
> This audit predicted the token-cost overclaim risk before final context token
> measurements were completed. For current paper-facing corrections, use
> `task28_context_token_cost_summary.md` and
> `task28_1_context_token_backfill_summary.md`.

This audit marks prior tasks that used `cost`, `cost reduction`, or
`quality-cost frontier` language before final LLM context tokens were measured.
The current `avg_source_candidate_cost` metric is an unweighted retrieval-stage
candidate-count proxy:

```text
source_candidate_cost =
  dense_candidates + bm25_candidates + cluster_candidates
```

It is not actual LLM input token cost, not dollar cost, and not latency. Dense
`100` means dense top-100 retrieved candidates, not normalized token usage.
Full multi-route `300` means dense top-100 + BM25 top-100 + cluster top-100.

Task28 should recompute final top-k context tokens from saved rankings before
any claim about token savings is made.

## Affected Tasks

| Task | Status | Existing comparison logic | Required correction before paper |
|---|---|---|---|
| Task16 | Affected | Reports cost-aware gating on PubMedQA, Banking77, eManual, and CUAD with percentage cost reduction versus full route. | Keep as `source candidate count reduction`; do not describe as token reduction. Token-cost claims require final-context-token recomputation. |
| Task18 | Affected | LoTTE 100k full/gated comparison reports gated average cost and cost reduction. | Reword as retrieval candidate proxy. Recompute final top-k context tokens if used in cost section. |
| Task19 | Affected | Pareto frontier uses average source cost and dense query rate. | Reframe as candidate-count Pareto frontier, not token Pareto frontier. Token frontier must be recomputed. |
| Task20 | Affected | Conditional dense fallback compares average cost, dense saved rate, and quality. | Dense query rate remains valid as route behavior; average cost is candidate proxy only. Need token recomputation for LLM context claims. |
| Task21 | Affected summary | Paper-ready summary consolidates Task16/18/19/20 as quality-cost evidence. | Add guardrail that all reported costs are source candidate proxies unless Task28 token columns are present. |
| Task22 | Affected | LoTTE scale-up reports full/gated source costs at 200k/400k/638k. | Keep as large-scale retrieval candidate-cost evidence; do not imply lower LLM token cost. |
| Task23 | Affected but partially guarded | Scale-up summary already states cost is relative to full multi-route and not dense-only in absolute source candidates. | Add second guardrail: source candidate cost is not final context token cost. |
| Task24 | Affected guardrail | Audit fixed metric naming and dense-only comparison risk, but not the token-cost distinction. | Extend audit guardrails: cost claims are candidate-count claims until Task28 token metrics exist. |
| Task25 | Lightly affected | Credit-assignment result mentions source candidate cost drop from `193.92` to `181.47`. | Keep cost as secondary candidate proxy; main route-level learning conclusion remains valid. |
| Task26 | Strongly affected | Low-cost routing compares Task26 configs against pure dense `100` and discusses sub-dense cost. | Must be reinterpreted as sub-dense candidate-count proxy only. Needs final-context-token recomputation before any token-cost claim. |
| Task27 | Strongly affected | Dense-LinUCB two-route trade-off explicitly tests cost below pure dense top-100. | Valid only as candidate-count boundary experiment. It does not prove token-cost superiority. Needs Task28 token recomputation. |

## Lower-Risk Or Unaffected Tasks

| Task | Reason |
|---|---|
| Task11-13 | Mainly baseline/LinUCB retrieval effectiveness and early feedback experiments; no final-token-cost claim should be attached. |
| Task14/14.5 | Manifold diagnostics and eManual limitation analysis; geometry conclusions are separate from cost. |
| Task15 | Feedback self-evolution evidence; route reward / last true reward conclusions remain valid. |
| Task17/17.5 | Embedding cache and shared artifact infrastructure; engineering runtime/caching work, not token-cost evidence. |

## Paper-Safe Wording Before Task28

Use:

> We report source candidate count as a retrieval-stage cost proxy.

Avoid:

> The method reduces LLM token cost.

Use:

> Gated routing reduces dense-heavy retrieval candidates and dense invocation
> rate relative to full multi-route retrieval.

Avoid:

> Gated routing uses fewer tokens than dense-only.

## Task28 Implication

Task28 should compute, for each saved ranking:

- `avg_final_context_tokens@k`
- `median_final_context_tokens@k`
- `p95_final_context_tokens@k`
- `hit@k`, `evidence_recall@k`, `mrr@k`, `ndcg@k`
- token ratio versus dense-only

Only after those metrics exist can Task26/27 be restated as token-cost
experiments. If all methods use fixed top-10 and chunk lengths are similar,
token reduction may be small or absent even when source candidate cost falls.

## Task28 Result Link

Task28 has now been run for the LoTTE 100k key configurations. The result
confirms the risk identified here: candidate-count reductions do not currently
translate into final top-10 context token savings. See
`paper/experiments/task28_context_token_cost_summary.md`.
