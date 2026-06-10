# Task37 Context-Budget Optimization

## Goal

Task37 starts from the reviewer-driven concern that the previous Task29-C
operating point is too conservative: it saves final retrieved context tokens, but
only by about 4.8-5.3%. The goal is to strengthen the quality-cost frontier
without lowering the paper's claim boundary.

The optimization target is:

> Preserve dense-level query-level Hit@10 while increasing final retrieved
> context-token saving beyond the previous Task29-C conservative policy.

All runs in this note use LoTTE technology/search 100k, the same held-out test
queries, the same `sentence-transformers/all-MiniLM-L6-v2` encoder, and the same
prequential LinUCB route-learning configuration unless noted otherwise.

## Important Architecture Clarification

The experiment also clarifies the actual role of LinUCB in the current
multi-route implementation.

LinUCB is not a parent router that decides whether the system runs dense, BM25,
or cluster-local retrieval. The implementation is better described as a
parallel multi-route surface:

```text
Query
  -> global dense route
  -> global BM25 route
  -> LinUCB-selected cluster-local route
  -> fusion / confidence signal
  -> final context-budget policy
```

LinUCB controls the cluster-local route and provides confidence signals for
final context compaction. Dense remains a recall floor / fallback route. This
means the paper figure and wording should avoid implying that LinUCB is the
single upstream router for dense and BM25.

## A. Fixed-k Compression Frontier

First, we tested whether simply making the existing Task29-C `confidence_topk`
policy more aggressive can improve token saving.

Compared with dense top-10:

| Policy | Seed | Hit@10 | Token ratio | Token saving | Hit delta |
|---|---:|---:|---:|---:|---:|
| Task29-C high=8, mid=10 | 13 | 0.8624 | 0.9451 | 5.49% | -0.50 pp |
| high=7, mid=9 | 13 | 0.8490 | 0.8570 | 14.30% | -1.85 pp |
| high=6, mid=8 | 13 | 0.8389 | 0.7683 | 23.17% | -2.85 pp |
| high=5, mid=7 | 13 | 0.8339 | 0.6787 | 32.13% | -3.36 pp |

This result is useful but not paper-safe as a main policy. It shows that
aggressive fixed-k compaction can save many tokens, but quality degrades too
quickly. The stronger direction is therefore not a smaller fixed `k`, but a
content-budget policy that prunes long tail context more selectively.

Artifacts:

- `paper/experiments/results/task37_100k_topk_frontier_context_tokens.md`
- `paper/experiments/results/task37_100k_aggressive_topk_smoke/`
- `paper/experiments/results/task37_100k_topk_7_9_smoke/`
- `paper/experiments/results/task37_100k_topk_6_8_smoke/`

## B. Token-Budget Final Context Policy

Task37 then adds `task37_context_budget_search.py`, a deterministic post-ranking
final-context policy search. The policy does not use ground-truth labels. For
each query it:

1. keeps a safe prefix of the ranked context;
2. computes the token count of the original top-10 context;
3. keeps additional tail chunks only while the context remains under a
   per-query token budget.

The strongest tested point uses:

```text
token_budget_r0.95_m5
```

That means: keep at least the first 5 chunks, then keep additional ranked chunks
only while the resulting context stays within 95% of that query's original
top-10 context tokens.

## C. Three-seed Formal Result

We first generate a complete gated top-10 ranking using the same LinUCB route
policy but `final_context_policy=fixed_topk`. This ranking has higher quality
than dense but no token saving:

| Method | Seeds | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 | Token ratio |
|---|---:|---:|---:|---:|---:|---:|
| Dense top-10 | - | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 1.0000 |
| Gated fixed top-10 | 3 | 0.8775 | 0.6906 | 0.7101 | 0.6334 | 1.0543 |

Applying `token_budget_r0.95_m5` to the gated fixed top-10 ranking gives:

| Method | Seeds | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 | Token ratio | Token saving | Hit delta vs dense |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Task29-C original | 3 | 0.8652 | 0.6737 | 0.7088 | 0.6251 | 0.9517 | 4.83% | -0.22 pp |
| Gated fixed + token budget 0.95 | 3 | 0.8680 | 0.6756 | 0.7092 | 0.6266 | 0.9227 | 7.73% | +0.06 pp |

This is the best Task37 result so far. It improves the main 100k quality-cost
frontier relative to Task29-C:

- token saving improves from about 4.83% to about 7.73%;
- mean Hit@10 moves from slightly below dense to slightly above dense;
- MRR@10 is slightly above dense, while nDCG@10 and EvidenceRecall@10 remain
  below dense because complete-evidence coverage is not the primary objective.

## D. Scale Extension: 100k to 638k

Task37-B extends the same `gated_fixed + token_budget_r0.95_m5` policy from
LoTTE 100k to 200k, 400k, and the full 638k corpus scale. The policy is kept
fixed across scales:

1. run the same gated cost-aware LinUCB route surface with `fixed_topk` to obtain
   a complete top-10 evidence ranking;
2. keep at least the first five chunks;
3. prune only tail chunks that would push the final context above 95% of that
   query's original top-10 context tokens.

This policy does not reduce corpus indexing, embedding generation, or dense
retrieval compute in the current implementation. It reduces the downstream LLM
generator evidence-context tokens.

| Scale | Dense Hit@10 | Task29-C Hit@10 | Task29-C token ratio | Task37 Hit@10 | Task37 token ratio | Task37 saving | Task37 Hit delta vs dense |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8652 | 0.9517 | 0.8680 | 0.9227 | 7.73% | +0.06 pp |
| 200k | 0.7970 | 0.8249 | 0.9531 | 0.8194 | 0.9296 | 7.04% | +2.24 pp |
| 400k | 0.7718 | 0.7819 | 0.9468 | 0.7791 | 0.9056 | 9.44% | +0.73 pp |
| 638k | 0.7282 | 0.7466 | 0.9514 | 0.7433 | 0.9176 | 8.24% | +1.51 pp |

The average Task37 token ratio across the four LoTTE scales is about `0.9189x`
dense, corresponding to about `8.1%` final evidence-context token saving. This
is stronger than the previous Task29-C conservative policy, whose scale-level
token ratios stay around `0.9468-0.9531x`.

The trade-off is also clear: Task37's token-budget policy usually has slightly
lower Hit@10 than the uncompressed gated fixed top-10 ranking and is sometimes
slightly lower than Task29-C, but it remains above dense-only Hit@10 at every
tested scale while using fewer final context tokens than both dense and Task29-C.

Artifacts:

- `paper/experiments/scripts/task37_context_budget_search.py`
- `paper/experiments/scripts/task37_paired_significance.py`
- `paper/experiments/results/task37_100k_gated_fixed_top10_formal/`
- `paper/experiments/results/task37_100k_context_budget_095_formal.md`
- `paper/experiments/results/task37_100k_context_budget_095_formal.csv`
- `paper/experiments/results/task37_100k_context_budget_095_rankings.json`
- `paper/experiments/results/task37_200k_gated_fixed_top10_formal/`
- `paper/experiments/results/task37_200k_context_budget_095_formal.md`
- `paper/experiments/results/task37_400k_gated_fixed_top10_formal/`
- `paper/experiments/results/task37_400k_context_budget_095_formal.md`
- `paper/experiments/results/task37_638k_gated_fixed_top10_formal/`
- `paper/experiments/results/task37_638k_context_budget_095_formal.md`

## E. Query-level Paired Significance

Task37-C adds query-level paired tests against dense top-10. For each query, the
script compares dense and method rankings on Hit@10, final evidence-context
tokens, EvidenceRecall@10, MRR@10, and nDCG@10. It reports:

- bootstrap confidence intervals for Hit@10 delta and token saving;
- McNemar exact tests over paired Hit@10 wins/losses;
- one-sided Wilcoxon tests for positive token saving;
- a strict `1pp` Hit@10 non-inferiority check based on the bootstrap CI lower
  bound.

The strict non-inferiority test is intentionally conservative. Because each
LoTTE scale currently uses the same 596 held-out queries, some seed-level
confidence intervals remain wider than the observed positive mean deltas.

### Aggregate paired result

The table below aggregates the three seeds for each scale and method. `NI seeds`
counts how many seeds pass the strict 1pp non-inferiority criterion. Token saving
is final evidence-context token saving relative to dense top-10.

| Scale | Method | Mean Hit delta vs dense | NI seeds | Mean token saving | Token-saving p<0.05 seeds | Mean token-down non-worse rate |
|---|---|---:|---:|---:|---:|---:|
| 100k | Task29-C | -0.22 pp | 0/3 | 4.83% | 3/3 | 0.539 |
| 100k | Task37 | +0.06 pp | 0/3 | 7.73% | 3/3 | 0.665 |
| 200k | Task29-C | +2.80 pp | 3/3 | 4.69% | 3/3 | 0.549 |
| 200k | Task37 | +2.24 pp | 3/3 | 7.04% | 3/3 | 0.661 |
| 400k | Task29-C | +1.01 pp | 1/3 | 5.32% | 3/3 | 0.549 |
| 400k | Task37 | +0.73 pp | 1/3 | 9.44% | 3/3 | 0.673 |
| 638k | Task29-C | +1.85 pp | 2/3 | 4.86% | 3/3 | 0.523 |
| 638k | Task37 | +1.51 pp | 2/3 | 8.24% | 3/3 | 0.666 |

### Interpretation

Task37-C supports three paper-facing conclusions:

1. Final context-token saving is statistically robust. Every seed at every
   scale has a one-sided Wilcoxon `p<0.05` for positive token saving.
2. Task37 improves the token frontier relative to Task29-C. It roughly doubles
   the average final evidence-context token saving from about `4.8-5.3%` to
   about `7.0-9.4%`.
3. Hit@10 is dense-level or above-dense on average at all four scales, but strict
   1pp non-inferiority is not uniformly proven for every seed. The safest claim
   is therefore not "statistically non-inferior in every setting"; it is:

> Task37 provides significant final evidence-context token reduction while
> preserving dense-level query-level Hit@10 on average, with strict
> non-inferiority supported in most larger-scale seed/scale settings but not
> uniformly across all seeds.

This is still a stronger main result than Task29-C because the method saves
more LLM input context while keeping the query-level sufficient-evidence metric
near or above dense. It also makes the remaining risk explicit: the paper should
include seed-level paired statistics rather than only the aggregate means.

Artifacts:

- `paper/experiments/results/task37_100k_paired_significance.md`
- `paper/experiments/results/task37_200k_paired_significance.md`
- `paper/experiments/results/task37_400k_paired_significance.md`
- `paper/experiments/results/task37_638k_paired_significance.md`

## F. Dense Adaptive Top-k / Same-budget Baselines

Task37-D tests the main alternative explanation: perhaps the observed saving is
only caused by sending fewer dense chunks to the generator. To check this, we
apply the same final-context controls directly to dense top-10 rankings:

- fixed dense prefix baselines: dense top-5, top-6, top-7, top-8, top-9, top-10;
- dense `token_budget_r0.95_m5`, using the same per-query token-budget rule as
  Task37.

These baselines use the same dense ranking and the same context-token counter.
They do not use ground-truth labels when selecting chunks.

| Scale | Dense top-10 Hit@10 | Dense top-9 Hit@10 | Dense top-9 token ratio | Dense budget Hit@10 | Dense budget token ratio | Task37 Hit@10 | Task37 token ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8574 | 0.9050 | 0.8540 | 0.8591 | 0.8680 | 0.9227 |
| 200k | 0.7970 | 0.7903 | 0.8990 | 0.7852 | 0.8680 | 0.8194 | 0.9296 |
| 400k | 0.7718 | 0.7668 | 0.8935 | 0.7634 | 0.8572 | 0.7791 | 0.9056 |
| 638k | 0.7282 | 0.7164 | 0.8896 | 0.7148 | 0.8613 | 0.7433 | 0.9176 |

This comparison is important:

- naive dense top-k reduction saves more tokens, but loses query-level Hit@10;
- applying the same token-budget rule to dense also loses Hit@10 at every scale;
- Task37 keeps a slightly larger context than dense top-9 / dense budget, but it
  preserves or improves dense-level Hit@10 while still saving about `7-9%` final
  evidence-context tokens.

Therefore Task37's result is not explained by simple dense top-k truncation. The
useful mechanism is the combination of:

1. a feedback-trained gated route surface that produces a stronger ranking than
   dense-only in large-scale settings;
2. a dense fallback route that prevents early pruning failures;
3. a conservative token-budget tail-pruning policy that removes low-marginal
   context after ranking quality has already been improved.

Artifacts:

- `paper/experiments/results/task37_100k_dense_adaptive_baseline.md`
- `paper/experiments/results/task37_200k_dense_adaptive_baseline.md`
- `paper/experiments/results/task37_400k_dense_adaptive_baseline.md`
- `paper/experiments/results/task37_638k_dense_adaptive_baseline.md`

## Interpretation

The useful conclusion is not that every compression policy improves accuracy.
The fixed-k frontier shows the opposite: naive aggressive compaction hurts
Hit@10.

The stronger conclusion is:

> A feedback-trained gated route surface can produce a higher-quality top-10
> ranking, and a conservative token-budget tail-pruning policy can convert that
> ranking into stronger final context-token savings while preserving dense-level
> sufficient-evidence retrieval.

This supports the paper's intended framing better than Task29-C alone. The
mechanism is no longer only "when confidence is high, use top-8"; it is:

1. use LinUCB feedback to improve the cluster-local route and fused ranking;
2. preserve dense fallback in the retrieval surface;
3. apply token-aware final context control to prune low-marginal-value tail
   context.

## Current Limitations

- Task37-C validates query-level paired significance on LoTTE
  100k/200k/400k/638k, but strict 1pp non-inferiority is not uniformly proven
  for every seed. The final paper should report seed-level paired statistics
  and avoid claiming universal statistical non-inferiority.
- The policy reduces final context tokens, not necessarily dense embedding
  compute, because dense still remains part of the route surface.
- EvidenceRecall@10 and nDCG@10 remain below dense, so the claim should stay
  focused on sufficient evidence under query-level Hit@10, not complete evidence
  collection.
- The method figure should be corrected to show LinUCB as the controller for the
  cluster-local route and final context confidence, not as the upstream selector
  of dense/BM25/cluster routes.

## Next Step

Task37 has now completed the core reviewer-driven checks: scale extension,
query-level paired statistics, and dense adaptive baselines. The remaining
paper-writing steps are:

- update the main paper table to use Task37 as the stronger context-cost result
  while keeping Task29-C as the conservative baseline;
- show dense adaptive top-k / same-budget results as an ablation against a
  simple truncation explanation;
- keep the claim boundary focused on final LLM evidence-context input tokens
  and query-level sufficient-evidence Hit@10.

The next optional experiment would be a larger generation-quality check, but the
retrieval/context-cost evidence chain is now strong enough to support paper
draft revision.
