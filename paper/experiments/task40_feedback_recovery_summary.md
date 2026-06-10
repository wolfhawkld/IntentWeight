# Task40 Feedback-driven Hard-case Recovery

## Goal

Task40 tests whether simulated feedback can repair tail queries harmed by
aggressive final-context budgets. This directly complements Task38 and Task39:
those tasks show that budgeted final contexts can reduce LLM evidence-context
input tokens, while Task40 asks whether the small set of budget-induced failures
can be recovered through feedback-driven routing changes.

The experiment uses two LoTTE 100k domains:

- `lotte_science_search_100k`
- `lotte_technology_search_100k`

Both use existing dense top-10 rankings, fixed top-10 gated LinUCB rankings,
budgeted LinUCB rankings, GT evidence, and cached KMeans arm assignments. No new
embedding or retrieval model is trained.

## Protocols

### Same-query Retry

Same-query retry is an engineering self-repair test. A query is affected when
dense top-10 hits at least one GT evidence chunk but the budgeted LinUCB final
context misses. After this simulated failure, feedback identifies the GT
evidence arm rather than directly inserting a GT chunk. The retry then reorders
the fixed LinUCB top-10 by the feedback-positive arm and reapplies a budget.

This is not an IID first-pass evaluation. It represents a post-feedback retry
after an observed failed answer.

### Calibration-to-test Generalization

Calibration-to-test generalization is stricter. Only calibration affected
queries are used to learn a risky query-arm to evidence-arm/fallback mapping.
The learned rule is frozen and evaluated on the held-out test split.

The tested generalization variants include direct arm boost, conservative
budget fallback, and full-context fallback on learned risky arms.

## Same-query Recovery Results

| Domain | Retry method | Affected queries | Recovered | Recovery rate | Avg token saving vs dense |
|---|---|---:|---:|---:|---:|
| science 100k | arm boost | 34 | 5 | 14.71% | 17.40% |
| science 100k | arm boost + conservative budget | 34 | 14 | 41.18% | 5.76% |
| science 100k | full-context fallback | 34 | 17 | 50.00% | -8.07% |
| technology 100k | arm boost | 42 | 8 | 19.05% | 13.68% |
| technology 100k | arm boost + conservative budget | 42 | 9 | 21.43% | 11.75% |
| technology 100k | full-context fallback | 42 | 12 | 28.57% | 0.96% |

The result supports the core feedback-recovery claim: budget-induced failures
are not necessarily permanent. Simulated feedback at the arm level can recover a
meaningful fraction of affected queries. The trade-off is explicit: stronger
fallback recovers more queries but reduces or removes token savings.

From a statistical interpretation standpoint, same-query retry is the strongest
Task40 evidence. The conservative retry setting recovers `14/34` affected
queries on science 100k and `9/42` on technology 100k, or `23/76` when pooled
across the two 100k domains. This is not a one-off recovery of one or two
examples; it is a meaningful post-feedback repair rate. Approximate Wilson
intervals put the pooled recovery rate around 21-41%. However, this evidence is
about post-feedback retry behavior, not first-pass IID test performance.

## Calibration-to-test Results

| Domain | Frozen test policy | Mean Hit@10 delta vs budgeted-before-feedback | Avg token saving vs dense |
|---|---|---:|---:|
| science 100k | conservative budget on learned risky arms | +0.16 pp | 16.13% |
| science 100k | full-context fallback on learned risky arms | +0.48 pp | 13.09% |
| technology 100k | conservative budget on learned risky arms | -0.16 pp | 5.88% |
| technology 100k | full-context fallback on learned risky arms | +0.16 pp | 4.25% |

The calibration-to-test result is more conservative than same-query retry. It
shows that learned fallback can slightly improve or preserve test Hit@10, but
the effect is small and domain-dependent. Naive arm boosting can cause negative
transfer, so the paper should prefer conservative fallback language rather than
claiming universal arm-boost generalization.

This split should not be presented as statistically significant held-out
improvement. Its role is narrower: it shows that learned risky-arm fallback can
be applied without catastrophic degradation and may preserve or slightly improve
Hit@10, while also exposing the limitation that feedback generalization depends
on domain structure and feedback quality.

## Interpretation

Task40 strengthens the paper in three ways.

First, it validates the self-evolution mechanism as a recovery path for tail
queries. When aggressive context compression loses evidence, simulated feedback
can update the arm-level preference and recover part of the affected set.

Second, it clarifies the operational design: feedback should not blindly
increase a learned arm everywhere. The safer deployment behavior is to use
feedback to trigger a less aggressive budget or full-context fallback for risky
local regions.

Third, it gives a precise boundary for the claim. Same-query retry demonstrates
post-feedback repair. Calibration-to-test provides limited but useful evidence
that learned risky-arm fallback can generalize. The result does not justify
claiming that feedback universally improves all future queries.

## Paper-facing Claim

A safe paper-facing statement is:

> Feedback-driven routing provides a recovery mechanism for tail queries harmed
> by aggressive context compression. In same-query retry experiments on two
> LoTTE 100k domains, arm-level simulated feedback recovers 21-41% of affected
> queries under conservative retry policies, while preserving part of the
> context-token savings. Calibration-to-test results indicate that learned
> risky-arm fallback can preserve or slightly improve held-out Hit@10, but the
> effect is domain-dependent; therefore feedback should be used as a controlled
> fallback trigger rather than an unconditional global reranking rule.

## Artifacts

- `paper/experiments/scripts/task40_feedback_recovery.py`
- `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv`
- `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.json`
- `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.md`
- `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv`
- `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.json`
- `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.md`
