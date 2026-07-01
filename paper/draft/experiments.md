# Experiments Draft

Updated: 2026-06-11

## Experimental Goals

The experiments test five claims:

1. Multi-route retrieval can improve coverage relative to a single dense route
   on large vertical-domain retrieval.
2. Trust-weighted feedback can improve LinUCB route-policy quality.
3. Geometry provides useful routing signal, but cannot replace dense retrieval.
4. Confidence-based final context compaction can reduce retrieved context tokens
   while preserving dense-level Hit@10.
5. Feedback-triggered fallback can recover a meaningful fraction of tail
   failures caused by aggressive context compaction.

## Dataset Roles

| Dataset | Role | Paper Use | Caveat |
|---|---|---|---|
| LoTTE technology/search | Main vertical-domain retrieval benchmark | Main scale-up, token-quality frontier, geometry validation | No true corpus topic labels in processed qrels |
| LoTTE science/search | Cross-domain vertical-domain validation | Tests whether ranking and context-budget findings transfer beyond technology/search | Compression strength is more domain-sensitive at 100k |
| PubMedQA | Feedback/manifold proof-of-concept | Shows trust feedback and local propagation can improve policy | GT is abstract-level context, not strict answer sentence |
| Banking77 | Intent/domain routing proxy | Shows strong feedback self-evolution and intent structure | Should not be mixed with evidence-retrieval main table |
| eManual | Failure/limitation case | Shows duplicate text and strict chunk-id issues | Low strict recall does not prove geometry is absent |
| CUAD | Sparse smoke/stress case | Shows sparse legal-domain limitation | GT-anchored sample only, not full-corpus main evidence |

## Baselines

The baseline family includes:

- BM25-only lexical retrieval.
- Dense-only retrieval with `sentence-transformers/all-MiniLM-L6-v2`.
- BM25 + dense hybrid retrieval using reciprocal-rank fusion.
- Full multi-route IntentWeight.
- Gated cost-aware IntentWeight.
- Confidence-based final context IntentWeight.
- Static geometry controls such as nearest-cluster routing.
- Naive controls such as random or epsilon-greedy arm selection.

Dense-only is the primary quality baseline. The paper should avoid weak
baseline framing; dense is strong and remains a required recall floor in the
method.

## Metrics

Retrieval quality:

- `Hit@K`: whether any ground-truth chunk appears in the top K.
- `evidence_recall@K`: fraction of all ground-truth chunks retrieved.
- `MRR@K`: reciprocal rank of the first relevant chunk.
- `nDCG@K`: binary relevance ranking quality.

Cost and efficiency:

- Source candidate cost: number of candidates considered before final fusion.
- Dense invocation rate: fraction of queries using the global dense path.
- Final context tokens: token count of retrieved chunks sent to the generator.

The main cost result uses final context tokens. Source candidate cost and dense
invocation rate are auxiliary retrieval-stage diagnostics.

## Protocol

### Prequential Simulated-Feedback Protocol

LinUCB experiments use a no-leakage prequential simulated-feedback protocol.
For each query `q_t`, the current policy state is frozen before retrieval. The
system ranks candidates, constructs the final context, and is evaluated against
the ground-truth evidence. Only after this evaluation is the ground-truth label
converted into simulated feedback and used to update the LinUCB state for later
queries.

This means the feedback for `q_t` cannot improve the ranking of `q_t` itself.
Earlier feedback can influence later queries, but future query feedback is not
available to the current policy. Saved rankings and final metrics are therefore
produced before the corresponding query update.

The protocol evaluates simulated test-time adaptation rather than offline IID
generalization. It should not be described as training a bandit on the test set
and then evaluating on the same examples. The correct interpretation is that a
retrieval controller is deployed over a query stream and adapts after each
interaction.

Some LinUCB experiments use multiple prequential epochs over the same query
stream to simulate repeated interactions. This setting should be disclosed
explicitly: it is useful for measuring route-policy self-evolution, but it is
not an IID held-out generalization protocol. In each epoch, the query is still
ranked before that query's feedback is applied.

### Feedback Source and Limitations

The feedback signal is controlled and ground-truth-derived. Oracle feedback is
used only as an upper bound. Equal noisy and trust-weighted modes simulate
imperfect user feedback with different reliability assumptions. Trust weighting
changes how strongly a feedback event updates the route policy, but it does not
give the current query access to its answer label before ranking.

This setup validates the route-learning mechanism under controlled feedback
quality. It does not claim that real user feedback has already been collected,
nor that delayed, biased, or adversarial human feedback would have the same
effect without additional deployment safeguards.

The protocol can be summarized as:

> Each query is evaluated before its simulated feedback updates the policy.
> The experiment tests controlled test-time adaptation and prevents
> future-label leakage into the current ranking.

## Main Result: LoTTE Token-Quality Frontier

Task29-C is the paper's main token-efficiency result because it directly
measures final retrieved context tokens. It is selected as the conservative end
of the Task29-A/B/C token-quality frontier: Task29-A and Task29-B show that more
aggressive context reduction is possible at a visible Hit@10 cost, while
Task29-C prioritizes quality preservation over maximum token saving.

| Scale | Corpus | Dense Hit@10 | Task29-C Hit@10 | Hit Delta | Dense Tokens@10 | Task29-C Tokens@10 | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE 100k | 101311 | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| LoTTE 200k | 201010 | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| LoTTE 400k | 400674 | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| LoTTE 638k | 638509 | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

Interpretation:

- The 100k result is near-dense, with a small Hit@10 drop.
- The 200k, 400k, and 638k results have mean Hit@10 above dense while using
  fewer final context tokens.
- The result should be framed as conservative final context compaction, not as
  aggressive dense replacement.

## Seed Stability

Task29.3 adds three-seed stability diagnostics for Task29-C. With only three
seeds, these intervals should be presented as engineering stability diagnostics,
not strong statistical significance proof.

| Scale | Task29-C Hit@10 mean | Hit@10 95% CI | Token saving mean | Token saving 95% CI |
|---|---:|---:|---:|---:|
| 100k | 0.8652 | [0.8565, 0.8739] | 4.83% | [2.89%, 6.77%] |
| 200k | 0.8249 | [0.8052, 0.8446] | 4.69% | [3.89%, 5.48%] |
| 400k | 0.7819 | [0.7709, 0.7929] | 5.32% | [0.11%, 10.53%] |
| 638k | 0.7466 | [0.7246, 0.7687] | 4.86% | [4.24%, 5.48%] |

The 400k token-saving interval is wider than the other scales. This should be
described as seed-level variance in routing confidence and context-budget
control, not as a contradiction of the overall direction. CI-level confirmation
of Hit@10 improvement is strongest at 200k; the 400k and 638k rows should be
reported as mean above-dense results with limited seed counts.

Task33.6 further extends the LoTTE 100k Task29-C setting from three to five
seeds. The five-seed mean is Hit@10 `0.8708` versus dense `0.8674`, with final
context token ratio `0.9507x`. The five-seed Hit delta confidence interval
overlaps zero (`[-0.82, +1.50]` percentage points), so this should be used only
as stability evidence: token saving remains directionally stable while quality
stays dense-level.

## Calibration/Test Context-Budget Validation

Task38 addresses a reviewer-facing risk: a context-budget policy selected after
inspecting the same test results can overstate the quality-cost trade-off. The
validation therefore splits held-out LoTTE technology/search queries into
calibration and frozen test subsets. The budget policy is selected only on
calibration queries and then evaluated unchanged on the frozen test split.

| Scale | Selected policy | Hit delta vs dense | Token saving vs dense | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

Interpretation:

- The calibrated policy saves final LLM evidence-context input tokens under a
  frozen policy-selection protocol.
- Dense-only adaptive truncation usually saves more tokens, but loses Hit@10 on
  every scale.
- IntentWeight therefore does more than simple dense top-k truncation: it uses
  route quality to decide where a shorter final context is safer.
- Strict seed-level non-inferiority remains scale-dependent and should not be
  overclaimed.

## Cross-Domain LoTTE Science/Search Validation

Task39 repeats the main validation pattern on LoTTE science/search. This is not
the primary scale-up benchmark, but it tests whether the result is limited to
technology/search.

| Domain/scale | Dense Hit@10 | IntentWeight fixed top-10 Hit@10 | Hit delta | Notes |
|---|---:|---:|---:|---|
| science/search 20k/q200 | 0.8950 | 0.9267 | +3.17 pp | Three seeds, eight prequential epochs |
| science/search 100k | 0.8926 | 0.9077 | +1.51 pp | Three seeds, eight prequential epochs |

The fixed top-10 ranking-side effect transfers to a second LoTTE domain.
Context compression is more nuanced:

| Domain/scale | Frozen budget policy | Budgeted Hit delta vs dense | Final context token saving |
|---|---|---:|---:|
| science/search 20k/q200 | `token_budget_r0.85_m4` | +0.71 to +2.86 pp | 13.18-14.31% |
| science/search 100k | `token_budget_r0.85_m4` | -1.20 to +0.00 pp | 17.53-20.53% |

The science/search result should be written as cross-domain support plus a
calibration boundary. IntentWeight improves fixed top-10 ranking quality on the
second domain, but an aggressive final-context budget that works well on a
smaller science slice can produce small Hit@10 drops at 100k. Compression
strength should therefore be calibrated per domain and scale rather than copied
unchanged.

## Geometry Diagnostics

Task30 validates whether LoTTE retains usable local geometry as scale grows.

| Scale | PCA dim90 sample | PCA var@64 sample | Nearest cluster hit@3 | Context retention@10 | Task29 Hit Delta |
|---|---:|---:|---:|---:|---:|
| 100k | 182 | 0.6437 | 0.8870 | 0.9033 | -0.22 pp |
| 200k | 186 | 0.6292 | 0.8697 | 0.8947 | +2.80 pp |
| 400k | 190 | 0.6110 | 0.9016 | 0.8826 | +1.01 pp |
| 638k | 196 | 0.5867 | 0.9016 | 0.8571 | +1.85 pp |

Interpretation:

- PCA dim90 increases and PCA var@64 decreases with scale, suggesting a more
  complex corpus geometry.
- Nearest-cluster hit@3 stays high, suggesting local geometry remains useful
  for routing.
- Context retention declines with scale, showing that geometry alone should not
  replace dense retrieval.

## Feedback-Driven Policy Adaptation

Task15 and Task25 provide the feedback-learning evidence.

Important interpretation:

- Dense and BM25 rescue routes can saturate final Hit@10, making feedback gains
  less visible in the final fused ranking.
- The strongest LinUCB self-evolution metrics are last true reward and
  selected-cluster hit rate.
- Task25's cluster-only reward attribution is important because it avoids
  crediting the selected cluster arm for dense/BM25 rescue hits.
- No-feedback gated routing can have high Hit@10 because it falls back to full
  dense/multi-route retrieval. That row is a safety/fallback control, not
  evidence that feedback is unnecessary.

Recommended paper wording:

> Trust-weighted simulated feedback improves the route-policy value field,
> while dense and BM25 fallback protect final retrieval quality.

Avoid:

> Feedback alone explains all retrieval gains.

## Feedback-Driven Hard-Case Recovery

Task40 tests a narrower but important question: when final-context compression
causes a tail query to lose evidence that dense top-10 would have retrieved,
can simulated feedback help recover that failure? This is a post-feedback
recovery experiment, not a first-pass IID ranking claim.

Same-query retry identifies affected queries where dense top-10 hits at least
one GT chunk but the budgeted IntentWeight context misses. Feedback then
updates arm-level routing state and triggers a safer retry policy.

| Domain | Conservative retry affected queries | Recovered | Recovery rate | Avg token saving vs dense |
|---|---:|---:|---:|---:|
| science/search 100k | 34 | 14 | 41.18% | 5.76% |
| technology/search 100k | 42 | 9 | 21.43% | 11.75% |
| pooled | 76 | 23 | 30.26% | - |

The pooled conservative retry recovery rate is approximately 30%, with an
approximate Wilson interval around 21-41%. This supports a practical recovery
claim: budget-induced failures are not always permanent, and feedback can
repair a meaningful fraction of them. It does not imply that every failed query
is recoverable, nor that feedback will always improve unrelated future queries.

A stricter calibration-to-test variant learns risky-arm fallback on calibration
failures and applies the frozen rule to held-out test queries. The effect is
small and domain-dependent: science/search improves by roughly +0.16 to
+0.48 pp, while technology/search ranges from -0.16 to +0.16 pp depending on
the fallback. This result supports controlled fallback behavior, not
unconditional global arm boosting.

## Context Compaction Trade-Off

Task29-C is optimized for query-level `Hit@10`, meaning at least one relevant
chunk appears in the final context. Because the policy sometimes sends fewer
chunks, `evidence_recall@10` can be lower than dense-only retrieval when a query
has multiple GT chunks. This is an expected trade-off: the conservative policy
targets usable evidence under a smaller context budget, not complete evidence
collection for every query.

## Downstream Answer-Quality Check

Task33.5 adds a small LLM generation sanity check. It compares dense top-10
context with Task29-C compressed context on 60 sampled LoTTE 100k queries using
`deepseek-v4-flash` with thinking enabled.

| Method | Answer score | Faithfulness | Answer relevance | Win count | Context token proxy ratio |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 4.4000 | 4.6500 | 4.6500 | 14 | 1.0000 |
| Task29-C | 4.2833 | 4.6333 | 4.4500 | 14 | 0.9321 |
| Tie | - | - | - | 32 | - |

Interpretation:

- The smoke does not show obvious answer-quality degradation from Task29-C
  context compaction.
- Dense has a small average-score and relevance edge, so this should not be
  overclaimed as Task29-C beating dense in generated answer quality.
- The result is a downstream sanity check, not a replacement for the retrieval
  and final-context-token experiments.

## Failure and Limitation Cases

### eManual

eManual contains heavy duplicate evidence text and strict chunk-id labels. Task
14.5 shows that strict chunk-id recall can mark text-equivalent retrieved
evidence as wrong. The dataset is useful as a limitation case: geometry may be
usable, but the current learned route and strict labels understate retrieval
success.

### CUAD

CUAD remains a sparse smoke/stress case. Current experiments use GT-anchored
sampling rather than full-corpus comparable evaluation. It should not be used as
main positive evidence.

## Paper Result Order

Recommended ordering in the results section:

1. Dataset and protocol guardrails.
2. Static baseline comparison.
3. Main LoTTE Task29-C token-quality frontier.
4. Seed stability diagnostics.
5. Calibration/test context-budget validation.
6. Cross-domain LoTTE science/search validation.
7. Feedback self-evolution and credit assignment.
8. Feedback-driven hard-case recovery.
9. Geometry diagnostics.
10. Failure cases and limitations.

## Artifact References

- Main evidence package: `paper/experiments/task31_paper_evidence_package.md`
- Task29 frontier: `paper/experiments/task29_2_token_quality_frontier.md`
- Seed CI: `paper/experiments/results/task29_3_seed_variance_ci.md`
- Geometry validation: `paper/experiments/task30_lotte_geometry_scale_validation.md`
- Historical token correction: `paper/experiments/task28_1_context_token_backfill_summary.md`
- Credit assignment: `paper/experiments/task25_credit_assignment_summary.md`
- LoTTE scale-up: `paper/experiments/task23_lotte_scaleup_summary.md`
- Protocol defense: `paper/experiments/task33_4_protocol_defense.md`
- LLM generation smoke: `paper/experiments/task33_5_llm_generation_smoke_summary.md`
- Additional seed stability:
  `paper/experiments/task33_6_additional_seeds_summary.md`
- Pre-writing consistency audit:
  `paper/experiments/task33_7_pre_writing_consistency_audit.md`
- Calibration/test context budget:
  `paper/experiments/task38_calibrated_context_budget_validation.md`
- Cross-domain LoTTE validation:
  `paper/experiments/task39_lotte_cross_domain_validation.md`
- Feedback-driven hard-case recovery:
  `paper/experiments/task40_feedback_recovery_summary.md`
> **Superseded draft / 已归档草稿**: 当前论文主源为 `paper/full_draft/`，
> 论文-facing 名称为 IntentRoute。本文件仅保留早期 IntentWeight 草稿记录。
