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

A five-seed extension is also available for LoTTE 100k. The additional seeds
test sensitivity to KMeans initialization and route-policy stochasticity.

**Appendix Table A3. Five-seed LoTTE 100k extension.**

| Setting | Seeds | $\mathrm{Hit@10}$ | Avg $\mathrm{Tokens@10}$ | Token ratio vs dense | Token saving |
|---|---:|---:|---:|---:|---:|
| Dense-only | 1 | 0.8674 | 1472.39 | 1.0000x | 0.00% |
| Conservative policy | 5 | 0.8708 | 1399.83 | 0.9507x | 4.93% |

The five-seed hit-delta interval is $[-0.0082, +0.0150]$. This supports
dense-level retrieval quality with stable context-token reduction, not a
statistical-superiority claim.

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
important recall floor and fallback route in IntentWeight.

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

## F. Downstream Answer-Quality Check

A small downstream answer-quality check compares dense top-10 context with the
compressed conservative-policy context on 60 sampled LoTTE 100k queries. The
same LLM configuration generates and judges answers in this check.

**Appendix Table F1. Downstream answer-quality check.**

| Method | Answer score | Faithfulness | Answer relevance | Win count | Prompt context-token proxy ratio |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 4.4000 | 4.6500 | 4.6500 | 14 | 1.0000x |
| Conservative policy | 4.2833 | 4.6333 | 4.4500 | 14 | 0.9321x |
| Tie | - | - | - | 32 | - |

The check does not show obvious answer-quality degradation from conservative
context compaction. It is not a full human evaluation: the sample is small,
one generator/judge model is used, and LLM-as-judge can be biased.

## G. Calibration/Test Context-Budget Validation

The calibration/test protocol selects the final-context budget on calibration
queries and freezes it before evaluation on held-out test queries.

**Appendix Table G1. Frozen context-budget validation on LoTTE technology/search.**

| Scale | Selected policy | Calibration eligible | Hit delta vs dense | Token saving | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

The calibrated policies should be compared against dense-only adaptive
truncation because both reduce final context size. IntentWeight preserves
substantially more $\mathrm{Hit@10}$ at a still meaningful token saving level.

## H. Cross-Domain Validation

LoTTE science/search is used as a second-domain validation, not as a replacement
for the main LoTTE technology/search scale-up.

**Appendix Table H1. Science/search fixed top-10 ranking validation.**

| Domain/scale | Corpus chunks | Queries | Dense $\mathrm{Hit@10}$ | IntentWeight $\mathrm{Hit@10}$ | Hit delta |
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
least one GT chunk but the budgeted IntentWeight context misses.

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

## J. Reproducibility and Reporting Guardrails

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
