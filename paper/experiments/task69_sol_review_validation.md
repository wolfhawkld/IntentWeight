# Task69 Sol Review Validation

Updated: 2026-07-12

## Scope

This audit validates Task69 against
`docs/scientific-review-gpt56-20260712.md`, rather than using dataset count as
the completion criterion. It separates Task69 cross-dataset protocol work from
the review's separate method, unseen-query, systems-cost, and figure work.

## Review Mapping

| Sol finding | Current status | Task69 disposition |
|---|---|---|
| Formal science/search 400k common protocol | Complete as a weak boundary row | Dense/BM25/hybrid, trust/no-feedback routes, OOF budget, paired tests, tokens, and recovery are traceable. |
| Additional LoTTE domains | Not required for Task69 | Deferred: Sol recommends at most one or two hypothesis-driven additions, not all three domains for count. |
| Protocol-version audit table | Complete | Task69.6 added Supplementary Table S29, which records dataset/query scope, protocol, endpoints, and non-pooling boundaries. |
| OOF evidence in primary narrative | Complete | Task69.6 states the science 100k/200k/400k OOF results and the 400k boundary without pooling them into the technology/search headline. |
| LinUCB feature/reward/budget description | Open P0 | Method-to-code alignment is outside Task69 and must be corrected before submission. |
| Frozen unseen-query policy test | Formal experiment complete; paper integration pending | Task70 now evaluates two 100k LoTTE domains with five folds, seeds 13/17/19, eight history epochs, frozen held-out ranking, bootstrap CIs, and McNemar tests. It does not show a learned-feedback advantage over matched static/cold full routing. |
| End-to-end latency, memory, and amortized cost | Open P0 | Not a Task69 retrieval-quality endpoint; measure before submission. |

## Science/Search 400k Closure

The frozen five-fold budget result has one eligible fold of five, mean
`Hit@10` delta `-0.67pp`, `3.15%` final-context token saving, and strict 1pp
non-inferiority in `0/3` seeds. It is therefore a scale boundary, not support
for robust lossless compression.

The recovery endpoint uses the same frozen OOF rankings and `r0.88_m4` action.
There are only 6, 3, and 5 affected queries for seeds 13, 17, and 19. A
same-query arm boost recovers 5, 2, and 4 of those queries. The
calibration-to-test replay learns only 3, 3, and 1 arms. These results close
the endpoint but are small-sample recovery evidence, not a new first-pass
generalization claim.

During this audit, Task40 was corrected to measure both Hit and token cost at
the evaluated `top_k`. This prevents a top-100 Dense artifact cache from
inflating the Dense baseline or affected-query set. The regression test is
`cache/test_task40_feedback_recovery.py`. Historical science/search 100k
recovery uses an actual top-10 Dense input and is unaffected.

## Task69 Completion Gate

Tasks 69.1-69.6 are complete. The compact dataset/protocol inventory and the
OOF boundary text are integrated into the paper, and the evidence, review, and
journal-submission packages have been regenerated and validated. The Task69
audit reports zero missing mandatory batches. The deferred LoTTE domain rows,
native science full scale, and new vertical datasets are post-Task69 expansion
work, not incomplete Task69 evidence.

This closure does not resolve the review's separate pre-submission P0 items:
method-to-code alignment, integration of the formal Task70 boundary into the
paper, and end-to-end latency/memory/amortized-cost measurement.
