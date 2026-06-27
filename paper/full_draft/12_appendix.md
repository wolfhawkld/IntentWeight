# Appendix

## A. Conservative Baseline and Seed Stability Diagnostics

The conservative confidence-only context policy is the stable baseline for
context compaction. The main text reports calibrated token-budget policies as
the primary cost result; this appendix keeps the earlier confidence-only scale
table and seed diagnostics. These intervals are engineering stability
diagnostics, not strong inferential proof: each scale has only three
observations.

**Appendix Table A1. Multi-seed retrieval-quality stability.**

| Scale | Dense $\mathrm{Hit@10}$ | Policy $\mathrm{Hit@10}$ mean | Std | 95% CI | Mean hit delta |
|---|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8652 | 0.0035 | [0.8565, 0.8739] | -0.0022 |
| 200k | 0.7970 | 0.8249 | 0.0079 | [0.8052, 0.8446] | +0.0280 |
| 400k | 0.7718 | 0.7819 | 0.0044 | [0.7709, 0.7929] | +0.0101 |
| 638k | 0.7282 | 0.7466 | 0.0089 | [0.7246, 0.7687] | +0.0185 |

**Appendix Table A2. Multi-seed final context-token stability.**

| Scale | Dense $\mathrm{Tokens@10}$ | Policy $\mathrm{Tokens@10}$ mean | Std | 95% CI | Mean token saving | Saving 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 1472.39 | 1401.24 | 11.49 | [1372.70, 1429.79] | 4.83% | [2.89%, 6.77%] |
| 200k | 1444.12 | 1376.46 | 4.61 | [1365.01, 1387.91] | 4.69% | [3.89%, 5.48%] |
| 400k | 1482.30 | 1403.43 | 31.10 | [1326.16, 1480.69] | 5.32% | [0.11%, 10.53%] |
| 638k | 1525.62 | 1451.49 | 3.83 | [1441.97, 1461.00] | 4.86% | [4.24%, 5.48%] |

The token-saving direction is consistent across scales. The wider 400k token
interval should be interpreted as route-confidence and context-budget variance,
not hidden as a uniform result.

## B. Static Retrieval Baselines

Dense retrieval is the primary quality baseline. BM25 supplies lexical
coverage, but it is weaker as a standalone retriever on LoTTE. Static
dense-plus-BM25 reciprocal-rank fusion is competitive at some scales but does
not consistently dominate dense.

**Appendix Table B1. Static LoTTE retrieval baselines across corpus scale.**

| Scale | Corpus chunks | BM25 $\mathrm{Hit@10}$ | Dense $\mathrm{Hit@10}$ | Static hybrid $\mathrm{Hit@10}$ |
|---|---:|---:|---:|---:|
| 100k | 101311 | 0.7232 | 0.8674 | 0.8624 |
| 200k | 201010 | 0.6292 | 0.7970 | 0.8003 |
| 400k | 400674 | 0.5721 | 0.7718 | 0.7617 |
| 638k | 638509 | 0.5084 | 0.7282 | 0.7181 |

The declining dense score as corpus scale grows motivates adaptive context
control, but it does not make dense retrieval obsolete. Dense remains an
important recall floor and fallback route in IntentRoute.

## C. Cost Metric Separation

The experiments separate three efficiency layers:

1. source candidate cost: candidates considered before final fusion;
2. dense invocation rate: fraction of queries using global dense retrieval;
3. final context tokens: retrieved chunk tokens sent to the generator.

The main paper claim uses the third layer. Historical routing experiments
showed that reducing candidate counts does not automatically reduce final
context tokens when the final context remains fixed at top-10.

**Appendix Table C1. Representative fixed-top-10 correction audit.**

| Dataset / scale | Routing setting | $\mathrm{Hit@10}$ | Avg $\mathrm{Tokens@10}$ | Ratio vs dense | Source candidate cost |
|---|---|---:|---:|---:|---:|
| Banking77 | Gated cost-aware routing | 0.9813 | 120.82 | 0.9978x | 142.51 |
| eManual | Gated cost-aware routing | 0.0116 | 17.92 | 0.9829x | 214.07 |
| LoTTE 100k | Quality-first routing | 0.8770 | 1518.44 | 1.0313x | 229.97 |
| LoTTE 100k | Conditional fallback routing | 0.8747 | 1516.24 | 1.0298x | 227.29 |
| LoTTE 100k | Cluster-credit routing | 0.8764 | 1550.65 | 1.0532x | 181.47 |
| LoTTE 200k | Initial gated routing | 0.8154 | 1549.39 | 1.0729x | 232.01 |
| LoTTE 400k | Initial gated routing | 0.7836 | 1547.66 | 1.0441x | 233.22 |
| LoTTE 638k | Initial gated routing | 0.7343 | 1599.95 | 1.0487x | 236.22 |

This audit motivated the explicit confidence-based final context policy. Its
token savings come from reducing selected final context size in
high-confidence cases, not from treating candidate-count savings as prompt
token savings.

## D. Secondary Datasets and Boundary Cases

The secondary datasets have different roles and should not be pooled into the
main LoTTE evidence claim.

- **PubMedQA** is an evidence-retrieval proof-of-concept near a dense ceiling.
  Dense reaches $\mathrm{Hit@10}=0.9930$; trust-weighted feedback reaches
  $\mathrm{Hit@10}=0.9940$, last reward $0.8727$, and selected-cluster hit
  $0.8860$. The ground truth is abstract-level context, not a strict answer
  sentence.
- **Banking77** is an intent-routing proxy rather than an evidence-retrieval
  benchmark. Dense/reference $\mathrm{Hit@10}$ is $0.9805$; trust-weighted
  feedback reaches $\mathrm{Hit@10}=0.9844$, last reward $0.9805$, and
  selected-cluster hit $0.9983$. It supports the feedback mechanism, not the
  main evidence-retrieval headline.
- **eManual** is a duplicate-text limitation case. Strict dense
  $\mathrm{Hit@10}$ is $0.3231$, text-equivalent dense $\mathrm{Hit@10}$ is
  $0.5615$, and deduplicated dense $\mathrm{Hit@10}$ rises to $0.8615$. Strict
  chunk IDs can therefore understate useful retrieval.
- **CUAD** is a sparse legal smoke/stress case. Dense/reference
  $\mathrm{Hit@10}$ is $0.0759$ and the trust-weighted smoke reaches
  $\mathrm{Hit@10}=0.0886$. It is a GT-anchored sample, not positive
  full-corpus evidence.

### D.1 eManual Duplicate-Text Diagnostic

eManual contains 18,812 corpus chunks but only 1,729 unique text strings.
Strict chunk-id evaluation can therefore mark semantically equivalent
retrievals as incorrect.

**Appendix Table D1. eManual strict, text-equivalent, and deduplicated
evaluation.**

| Method | Evaluation mode | $\mathrm{Hit@10}$ | $\mathrm{MRR@10}$ | $\mathrm{nDCG@10}$ |
|---|---|---:|---:|---:|
| BM25 | Strict chunk ID | 0.1154 | 0.0244 | 0.0256 |
| BM25 | Text-equivalent | 0.3846 | 0.3059 | 0.1620 |
| Dense | Strict chunk ID | 0.3231 | 0.0551 | 0.0526 |
| Dense | Text-equivalent | 0.5615 | 0.4716 | 0.2030 |
| Static hybrid | Strict chunk ID | 0.1692 | 0.0366 | 0.0287 |
| Static hybrid | Text-equivalent | 0.5846 | 0.4895 | 0.2263 |
| Dense | Deduplicated corpus | 0.8615 | 0.5736 | 0.3807 |

The text-equivalent and deduplicated metrics are diagnostics, not replacements
for the strict evaluation. They show that eManual's low strict score cannot be
interpreted as proof that useful local structure is absent.

## E. Encoder Robustness

The main scale-up uses `sentence-transformers/all-MiniLM-L6-v2`. A LoTTE 100k
robustness check replaces it with
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA-tuned MiniLM-family
encoder with the same 384-dimensional embedding size and a similar
CPU-friendly resource class.

**Appendix Table E1. QA-tuned MiniLM-family encoder robustness.**

| Method | $\mathrm{Hit@10}$ | $\mathrm{MRR@10}$ | $\mathrm{nDCG@10}$ | $\mathrm{EvidenceRecall@10}$ | Avg $\mathrm{Tokens@10}$ | Token ratio vs dense |
|---|---:|---:|---:|---:|---:|---:|
| Dense-only | 0.8809 | 0.7220 | 0.6616 | 0.7163 | 1514.51 | 1.0000x |
| Conservative policy | 0.8853 | 0.7118 | 0.6291 | 0.6789 | 1463.71 | 0.9665x |

Under the QA-tuned encoder, the dense baseline becomes stronger and the
conservative policy still preserves dense-level query hit while reducing final
context tokens by 3.35%. Ranking metrics and evidence recall are lower than
dense, so this is a bounded robustness result rather than a universal
retrieval-metric improvement.

**Appendix Table E2. Matched-backbone context-budget robustness on the frozen
LoTTE technology/search 100k split.**

| Backbone | Route mode | Dense $\mathrm{Hit@10}$ | Method $\mathrm{Hit@10}$ | Hit delta | Token saving |
|---|---|---:|---:|---:|---:|
| MiniLM | calibrated multi-route | 0.8705 | 0.8705 | +0.00 pp | 6.18% |
| BGE-base | full multi-route | 0.8993 | 0.8985 | -0.08 pp | 11.99% |
| E5-base | full multi-route | 0.8753 | 0.8689 | -0.64 pp | 12.20% |
| BGE-base | quality-first | 0.8993 | 0.9081 | +0.88 pp | 7.23% |

The full multi-route rows show that the quality-cost pattern is not tied to the
MiniLM backbone. More aggressive gated BGE/E5 variants lose more hit and are
treated as boundary settings. The BGE quality-first row demonstrates that the
frontier is tunable; an equivalent above-dense E5 point was not found on this
split.

## F. Downstream Answer-Level Evaluation

The formal downstream evaluation uses 300 deterministic queries from the
frozen LoTTE technology/search 100k test split. Seven methods produce 2,100
answers and 2,100 schema-valid judgments under the same
`deepseek-v4-flash` generator/judge configuration.

**Appendix Table F1. Downstream answer and context results.**

| Method | Correct | Faithful | Strict citation support | Insufficient context | Avg context tokens | Tokens / correct |
|---|---:|---:|---:|---:|---:|---:|
| MiniLM dense | 0.9200 | 0.9533 | 0.3533 | 0.0967 | 1461 | 1588 |
| BGE dense | 0.9167 | 0.9433 | 0.3567 | 0.0767 | 1698 | 1852 |
| BGE IntentRoute | 0.9167 | 0.9200 | 0.3700 | 0.0767 | 1596 | 1741 |
| E5 dense | 0.9167 | 0.9300 | 0.4100 | 0.0700 | 1525 | 1663 |
| E5 IntentRoute | 0.9200 | 0.9333 | 0.3633 | 0.0567 | 1341 | 1458 |
| Dense+MMR | 0.8900 | 0.9100 | 0.0733 | 0.0800 | 1240 | 1393 |
| IW+MMR | 0.9133 | 0.9267 | 0.0833 | 0.0900 | 1157 | 1267 |

**Appendix Table F2. Paired downstream comparisons.**

| Comparison | Correct delta | 95% CI | McNemar $p$ | Token saving | 95% CI |
|---|---:|---:|---:|---:|---:|
| BGE IntentRoute vs dense | +0.00 pp | [-2.67, +2.67] pp | 1.000 | 6.00% | [4.01%, 7.97%] |
| E5 IntentRoute vs dense | +0.33 pp | [-3.00, +3.67] pp | 1.000 | 12.04% | [9.93%, 14.16%] |
| IW+MMR vs Dense+MMR | +2.33 pp | [-1.67, +6.33] pp | 0.324 | 6.65% | [4.28%, 8.97%] |

The context-saving intervals are positive while correctness intervals include
zero. This supports answer-level correctness preservation with lower context,
not significant answer-quality improvement. The study still uses one
generator/judge model and is not a human evaluation.

## G. Calibration/Test Context-Budget Validation

The calibration/test protocol selects the final-context budget on calibration
queries and freezes it before evaluation on held-out test queries.

**Appendix Table G1. Frozen context-budget validation on LoTTE technology/search.**

| Scale | Selected policy | Calibration eligible | Hit delta vs dense | Token saving | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False / pending follow-up | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

The calibrated policies should be compared against dense-only adaptive
truncation because both reduce final context size. IntentRoute preserves
substantially more $\mathrm{Hit@10}$ at a still meaningful token saving level.
The 400k row is diagnostic rather than calibration-eligible in the current
artifact set and is marked for follow-up calibration.

## H. Cross-Domain Validation

LoTTE science/search is used as a second-domain validation, not as a replacement
for the main LoTTE technology/search scale-up.

**Appendix Table H1. Science/search fixed top-10 ranking validation.**

| Domain/scale | Corpus chunks | Queries | Dense $\mathrm{Hit@10}$ | IntentRoute $\mathrm{Hit@10}$ | Hit delta |
|---|---:|---:|---:|---:|---:|
| science/search 20k/q200 | 20,490 | 200 | 0.8950 | 0.9267 | +3.17 pp |
| science/search 100k | 101,187 | 596 | 0.8926 | 0.9077 | +1.51 pp |

**Appendix Table H2. Science/search frozen context-budget validation.**

| Domain/scale | Budget policy | Seed | Frozen test hit delta vs dense | Token saving | Strict NI by CI |
|---|---|---:|---:|---:|---:|
| 20k/q200 | `token_budget_r0.85_m4` | 13 | +2.86 pp | 13.18% | True |
| 20k/q200 | `token_budget_r0.85_m4` | 17 | +1.43 pp | 14.31% | False |
| 20k/q200 | `token_budget_r0.85_m4` | 19 | +0.71 pp | 13.91% | False |
| 100k | `token_budget_r0.85_m4` | 13 | -1.20 pp | 19.21% | False |
| 100k | `token_budget_r0.85_m4` | 17 | +0.00 pp | 17.53% | False |
| 100k | `token_budget_r0.85_m4` | 19 | -0.96 pp | 20.53% | False |

The fixed top-10 ranking gains transfer, while aggressive final-context budgets
require domain and scale calibration.

## I. Feedback-Driven Hard-Case Recovery

Hard-case recovery focuses on affected queries where dense top-10 retrieves at
least one GT chunk but the budgeted IntentRoute context misses.

**Appendix Table I1. Same-query feedback recovery on affected queries.**

| Domain | Retry method | Affected queries | Recovered | Recovery rate | Avg token saving vs dense |
|---|---|---:|---:|---:|---:|
| science 100k | arm boost | 34 | 5 | 14.71% | 17.40% |
| science 100k | arm boost + conservative budget | 34 | 14 | 41.18% | 5.76% |
| science 100k | full-context fallback | 34 | 17 | 50.00% | -8.07% |
| technology 100k | arm boost | 42 | 8 | 19.05% | 13.68% |
| technology 100k | arm boost + conservative budget | 42 | 9 | 21.43% | 11.75% |
| technology 100k | full-context fallback | 42 | 12 | 28.57% | 0.96% |

Same-query retry is post-feedback repair evidence. It is not a first-pass
generalization result.

**Appendix Table I2. Calibration-to-test recovery generalization.**

| Domain | Frozen test recovery policy | Mean hit delta versus budgeted-before-feedback | Avg token saving vs dense |
|---|---|---:|---:|
| science 100k | conservative budget on learned risky arms after calibration | +0.16 pp | 16.13% |
| science 100k | full-context fallback on learned risky arms after calibration | +0.48 pp | 13.09% |
| technology 100k | conservative budget on learned risky arms after calibration | -0.16 pp | 5.88% |
| technology 100k | full-context fallback on learned risky arms after calibration | +0.16 pp | 4.25% |

The held-out effect is small and domain-dependent. Feedback should therefore be
used as a controlled fallback trigger rather than as unconditional global
reranking.

## J. Strong Post-Retrieval Baselines

These baselines test whether simpler post-retrieval operations explain the
main final-context result.

**Appendix Table J1. Dense+Sentence-MMR same-budget baseline on LoTTE
technology/search 100k.**

| Budget target | $\mathrm{Hit@10}$ | Hit delta vs dense | $\mathrm{EvidenceRecall@10}$ | Avg context tokens | Token saving vs dense |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 0.8705 | 0.0000 | 0.7081 | 1470.1 | 0.00% |
| SentMMR seed13 budget | 0.8705 | 0.0000 | 0.7081 | 1287.8 | 12.40% |
| SentMMR seed17 budget | 0.8705 | 0.0000 | 0.7075 | 1278.0 | 13.07% |
| SentMMR seed19 budget | 0.8705 | 0.0000 | 0.7081 | 1302.1 | 11.43% |

Dense+Sentence-MMR preserves dense chunk-support on this split while reducing
selected sentence tokens. It is therefore a strong final-context compression
baseline, not a weak control.

**Appendix Table J2. Compressor-normalized comparison on LoTTE
technology/search 100k.**

| Source pool | Method | Ratio | $\mathrm{Hit@10}$ range | Saving vs dense |
|---|---|---:|---:|---:|
| Dense | top-10 | - | 0.8705 | 0.00% |
| Dense | SentMMR | 0.95 | 0.8705 | 5.33% |
| Dense | SentMMR | 0.90 | 0.8705 | 10.22% |
| Dense | SentMMR | 0.85 | 0.8705 | 15.16% |
| IntentRoute | target | - | 0.8657-0.8777 | 4.98-7.14% |
| IntentRoute | SentMMR | 0.95 | 0.8657-0.8777 | 10.07-12.14% |
| IntentRoute | SentMMR | 0.90 | 0.8657-0.8777 | 14.72-16.68% |
| IntentRoute | SentMMR | 0.85 | 0.8657-0.8777 | 19.41-21.24% |

Applying the same compressor to dense and IntentRoute evidence pools supports
the route-and-budget controller framing. The compressor is shared; the evidence
pool and budget controller determine the starting point.

**Appendix Table J3. Cross-encoder reranker baseline on LoTTE
technology/search 100k.**

| Method | $\mathrm{Hit@10}$ | $\mathrm{EvidenceRecall@10}$ | Avg context tokens | Token saving vs dense |
|---|---:|---:|---:|---:|
| Dense top-10 | 0.8705 | 0.7081 | 1470 | 0.00% |
| Cross-encoder top-10 | 0.8777 | 0.7332 | 1792 | -21.91% |
| IntentRoute target | 0.8657-0.8777 | 0.6766-0.6871 | 1365-1397 | 4.98-7.14% |
| Cross-encoder same budget | 0.8633-0.8729 | 0.6975-0.7044 | 1360-1390 | 5.43-7.49% |

The cross-encoder reranker improves full top-10 support metrics, but that full
reranked context is longer on average. Under the same per-query token budgets
as IntentRoute, reranking does not uniformly dominate the calibrated
controller.

**Appendix Table J4. SelectiveContext-lite prompt-pruning baseline.**

| Source pool | Ratio | $\mathrm{Hit@10}$ | Token saving vs dense | Extra saving vs source |
|---|---:|---:|---:|---:|
| Dense | 0.95 | 0.8705 | 5.66% | 5.66% |
| Dense | 0.90 | 0.8705 | 10.42% | 10.42% |
| Dense | 0.85 | 0.8705 | 15.31% | 15.31% |
| Dense | 0.75 | 0.8705 | 25.19% | 25.19% |
| IntentRoute | 0.95 | 0.8657-0.8777 | 10.38-12.42% | 5.62-5.69% |
| IntentRoute | 0.90 | 0.8657-0.8777 | 14.92-16.87% | 10.46-10.48% |
| IntentRoute | 0.85 | 0.8657-0.8777 | 19.53-21.40% | 15.31-15.35% |
| IntentRoute | 0.75 | 0.8657-0.8777 | 28.95-30.57% | 25.20-25.23% |

SelectiveContext-lite is a deterministic local proxy, not LLMLingua. Its role
is to show that prompt pruning can be stacked after either evidence pool and
does not replace upstream route-confidence-to-budget control.

## K. Route-Control Attribution and Arm Sensitivity

**Appendix Table K1. Static geometry versus uniform-random route control.**

| Setting | Full top-10 hit | Route reward | Selected-cluster hit | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Static nearest geometry | 0.8764 | 0.8563 | 0.8870 | +1.44 pp | 5.03% |
| Uniform random control | 0.8842 | 0.1499 | 0.1577 | +1.04 pp | 11.92% |

Dense/BM25 rescue keeps final fused hit high in both rows, while route reward
and selected-cluster hit separate meaningful local routing from random arm
selection. Geometry is therefore supported as a route-control signal, not a
standalone explanation of final fused quality.

**Appendix Table K2. Feedback and static route controls.**

| Setting | Route reward | Selected-cluster hit | Dense rate | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Learned full multi-route | 0.6790 | 0.5766 | 1.0000 | -1.68 pp | 17.86% |
| Learned gated | 0.6790 | 0.5766 | 0.7377 | -5.20 pp | 11.83% |
| Static nearest gated | 0.8563 | 0.8870 | 0.9586 | -2.40 pp | 12.01% |
| No-feedback gated | 0.1504 | 0.1570 | 1.0000 | -1.60 pp | 16.56% |

Feedback-updated LinUCB improves route quality over no-feedback/random controls,
but the learned gated threshold is a cost-aggressive boundary. Static geometry
remains a strong prior, while dense fallback explains part of the fused result.

**Appendix Table K3. Arm-count sensitivity.**

| $K$ | Static route reward | Full test hit delta | Full token saving | Gated dense rate | Gated hit delta |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.9128 | +1.44 pp | 6.23% | 0.4083 | -1.84 pp |
| 16 | 0.8826 | +0.80 pp | 10.49% | 0.6089 | -1.68 pp |
| 32 | 0.8563 | +0.56 pp | 4.68% | 0.7377 | -4.48 pp |
| 64 | 0.8272 | +0.40 pp | 11.19% | 0.8986 | -3.76 pp |
| 128 | 0.8479 | +1.20 pp | 10.23% | 0.9502 | -3.12 pp |

Full multi-route quality is stable across the tested grid, whereas gated
dense-saving behavior depends on arm granularity. Cross-scale correlations
between geometry diagnostics and final quality-cost gain are mixed and
small-sample; final behavior belongs to the complete calibrated controller.

## L. Reproducibility and Reporting Guardrails

The following rules apply when migrating the draft into a submission template:

- report query-level $\mathrm{Hit@10}$ as the primary retrieval headline;
- report $\mathrm{EvidenceRecall@10}$ separately for complete-evidence tasks;
- use final retrieved context tokens for prompt-context efficiency claims;
- label source candidate cost and dense invocation rate as retrieval-stage
  diagnostics;
- describe multi-epoch prequential adaptation as simulated repeated
  interaction, not IID held-out generalization;
- describe feedback as controlled simulation, not collected production
  feedback;
- describe geometry diagnostics as support for a piecewise local-structure
  interpretation, not theorem-level manifold proof;
- keep dense retrieval visible as a recall floor and fallback route.
