# Experiments Draft

Updated: 2026-05-25

## Experimental Goals

The experiments test four claims:

1. Multi-route retrieval can improve coverage relative to a single dense route
   on large vertical-domain retrieval.
2. Trust-weighted feedback can improve LinUCB route-policy quality.
3. Geometry provides useful routing signal, but cannot replace dense retrieval.
4. Confidence-based final context compaction can reduce retrieved context tokens
   while preserving near- or above-dense Hit@10.

## Dataset Roles

| Dataset | Role | Paper Use | Caveat |
|---|---|---|---|
| LoTTE technology/search | Main vertical-domain retrieval benchmark | Main scale-up, token-quality frontier, geometry validation | No true corpus topic labels in processed qrels |
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
measures final retrieved context tokens.

| Scale | Corpus | Dense Hit@10 | Task29-C Hit@10 | Hit Delta | Dense Tokens@10 | Task29-C Tokens@10 | Token Saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE 100k | 101311 | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| LoTTE 200k | 201010 | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| LoTTE 400k | 400674 | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| LoTTE 638k | 638509 | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

Interpretation:

- The 100k result is near-dense, with a small Hit@10 drop.
- The 200k, 400k, and 638k results are above dense while using fewer final
  context tokens.
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

## Feedback Self-Evolution

Task15 and Task25 provide the feedback-learning evidence.

Important interpretation:

- Dense and BM25 rescue routes can saturate final Hit@10, making feedback gains
  less visible in the final fused ranking.
- The strongest LinUCB self-evolution metrics are last true reward and
  selected-cluster hit rate.
- Task25's cluster-only reward attribution is important because it avoids
  crediting the selected cluster arm for dense/BM25 rescue hits.

Recommended paper wording:

> Trust-weighted simulated feedback improves the route-policy value field,
> while dense and BM25 fallback protect final retrieval quality.

Avoid:

> Feedback alone explains all retrieval gains.

## Downstream Generation Smoke

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
5. Feedback self-evolution and credit assignment.
6. Geometry diagnostics.
7. Failure cases and limitations.

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
