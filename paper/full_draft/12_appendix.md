# Supplementary Material

## S1. Conservative Baseline and Seed Stability Diagnostics

The conservative confidence-only context policy is the stable baseline for
context compaction. The main text reports calibrated token-budget policies as
the primary cost result; this supplement keeps the earlier confidence-only scale
table and seed diagnostics. These intervals are engineering stability
diagnostics, not strong inferential proof: each scale has only three
observations.
Tables~\ref{tab:s1} and~\ref{tab:s2} report quality and token stability.

**Supplementary Table S1. Multi-seed retrieval-quality stability.**

| Scale | Dense $\mathrm{Hit@10}$ | Policy $\mathrm{Hit@10}$ mean | Std | 95% CI | Mean hit delta |
|---|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8652 | 0.0035 | [0.8565, 0.8739] | -0.0022 |
| 200k | 0.7970 | 0.8249 | 0.0079 | [0.8052, 0.8446] | +0.0280 |
| 400k | 0.7718 | 0.7819 | 0.0044 | [0.7709, 0.7929] | +0.0101 |
| 638k | 0.7282 | 0.7466 | 0.0089 | [0.7246, 0.7687] | +0.0185 |

**Supplementary Table S2. Multi-seed final context-token stability.**

| Scale | Dense $\mathrm{Tokens@10}$ | Policy $\mathrm{Tokens@10}$ mean | Std | 95% CI | Mean token saving | Saving 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 1472.39 | 1401.24 | 11.49 | [1372.70, 1429.79] | 4.83% | [2.89%, 6.77%] |
| 200k | 1444.12 | 1376.46 | 4.61 | [1365.01, 1387.91] | 4.69% | [3.89%, 5.48%] |
| 400k | 1482.30 | 1403.43 | 31.10 | [1326.16, 1480.69] | 5.32% | [0.11%, 10.53%] |
| 638k | 1525.62 | 1451.49 | 3.83 | [1441.97, 1461.00] | 4.86% | [4.24%, 5.48%] |

The token-saving direction is consistent across scales. The wider 400k token
interval should be interpreted as operating-point variance across the routed
ranking and context policy, not hidden as a uniform result.

## S2. Static Retrieval Baselines

Dense retrieval is the primary quality baseline. BM25 supplies lexical
coverage, but it is weaker as a standalone retriever on LoTTE. Static
dense-plus-BM25 reciprocal-rank fusion is competitive at some scales but does
not consistently dominate dense.
Table~\ref{tab:s3} reports these static baselines.

**Supplementary Table S3. Static LoTTE retrieval baselines across corpus scale.**

| Scale | Corpus chunks | BM25 $\mathrm{Hit@10}$ | Dense $\mathrm{Hit@10}$ | Static hybrid $\mathrm{Hit@10}$ |
|---|---:|---:|---:|---:|
| 100k | 101311 | 0.7232 | 0.8674 | 0.8624 |
| 200k | 201010 | 0.6292 | 0.7970 | 0.8003 |
| 400k | 400674 | 0.5721 | 0.7718 | 0.7617 |
| 638k | 638509 | 0.5084 | 0.7282 | 0.7181 |

The declining dense score as corpus scale grows motivates adaptive context
control, but it does not make dense retrieval obsolete. Dense remains an
important recall floor and fallback route in IntentRoute.

## S3. Cost Metric Separation

The experiments separate three efficiency layers:

1. source candidate cost: candidates considered before final fusion;
2. dense invocation rate: fraction of queries using global dense retrieval;
3. final context tokens: retrieved chunk tokens sent to the generator.

The main paper claim uses the third layer. Historical routing experiments
showed that reducing candidate counts does not automatically reduce final
context tokens when the final context remains fixed at top-10.
Table~\ref{tab:s4} records the correction audit that motivated this separation.

In Supplementary Table S4, every row labeled `LoTTE` refers specifically to
the technology/search domain; science/search is reported separately in
Supplementary Section S8.

**Supplementary Table S4. Representative fixed-top-10 correction audit.**

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

This audit motivated explicit final-context control. The conservative historical
policy reduces context size in high-confidence cases, while the stronger main
result uses an independently calibrated length budget. Neither candidate-count
savings nor route confidence alone establishes prompt-token savings.

## S4. Secondary Datasets and Boundary Cases

The secondary datasets have different roles and should not be pooled into the
main LoTTE evidence claim.

- **PubMedQA** is an evidence-retrieval proof-of-concept near a dense ceiling.
  Dense reaches $\mathrm{Hit@10}=0.9930$; trust-weighted feedback reaches
  $\mathrm{Hit@10}=0.9940$, last reward $0.8727$, and selected-cluster hit
  $0.8860$. The ground truth is abstract-level context, not a strict answer
  sentence.
- **CovidQA-RAG** is the biomedical transfer row with a non-ceiling dense
  baseline. The native-full RAGBench checkpoint contains 32,392 chunks and
  1,726 evaluated queries after skipping 39 without usable ground truth. Dense
  reaches $\mathrm{Hit@10}=0.6095$, BM25 reaches $0.4884$, hybrid RRF reaches
  $0.6037$, no-feedback IntentRoute reaches $0.6294$, and trust-weighted
  IntentRoute reaches $0.6300$ at fixed top-10. In the five-fold budgeted
  protocol, four of five folds select a compressed route, mean hit delta is
  -0.21 percentage points versus dense, mean final-context token saving is
  8.34%, and strict 1pp non-inferiority remains $0/3$ seeds.
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

### S4.1 eManual Duplicate-Text Diagnostic

eManual contains 18,812 corpus chunks but only 1,729 unique text strings.
Strict chunk-id evaluation can therefore mark semantically equivalent
retrievals as incorrect.
Table~\ref{tab:s5} quantifies the strict, text-equivalent, and deduplicated views.

**Supplementary Table S5. eManual strict, text-equivalent, and deduplicated
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

## S5. Encoder Robustness

The main scale-up uses `sentence-transformers/all-MiniLM-L6-v2`. A LoTTE
technology/search 100k
robustness check replaces it with
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA-tuned MiniLM-family
encoder with the same 384-dimensional embedding size and a similar
CPU-friendly resource class.
Tables~\ref{tab:s6} and~\ref{tab:s7} report encoder-family and matched-backbone robustness.

**Supplementary Table S6. QA-tuned MiniLM-family encoder robustness.**

| Method | $\mathrm{Hit@10}$ | $\mathrm{MRR@10}$ | $\mathrm{nDCG@10}$ | $\mathrm{EvidenceRecall@10}$ | Avg $\mathrm{Tokens@10}$ | Token ratio vs dense |
|---|---:|---:|---:|---:|---:|---:|
| Dense-only | 0.8809 | 0.7220 | 0.6616 | 0.7163 | 1514.51 | 1.0000x |
| Conservative policy | 0.8853 | 0.7118 | 0.6291 | 0.6789 | 1463.71 | 0.9665x |

Under the QA-tuned encoder, the dense baseline becomes stronger and the
conservative policy still preserves dense-level query hit while reducing final
context tokens by 3.35%. Ranking metrics and evidence recall are lower than
dense, so this is a bounded robustness result rather than a universal
retrieval-metric improvement.

**Supplementary Table S7. Matched-backbone context-budget robustness on the frozen
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

## S6. Downstream Answer-Level Evaluation

The formal downstream evaluation uses 300 deterministic queries from the
frozen LoTTE technology/search 100k test split. Seven methods produce 2,100
answers with `deepseek-v4-flash`. The fixed answers receive 2,100 DeepSeek,
2,100 GLM-5.2, and 2,065 MiniMax-M3 schema-valid judgments. Cross-judge
statistics use the 2,065 query-method keys shared by all judges.
Tables~\ref{tab:s8}, \ref{tab:s9}, \ref{tab:s10}, \ref{tab:s11},
and~\ref{tab:s12} report method results, paired tests, judge coverage,
agreement, and majority-vote comparisons.

**Supplementary Table S8. DeepSeek-judged downstream answer and context results.**

| Method | Correct | Faithful | Strict citation support | Insufficient context | Avg context tokens | Tokens / correct |
|---|---:|---:|---:|---:|---:|---:|
| MiniLM dense | 0.9200 | 0.9533 | 0.3533 | 0.0967 | 1461 | 1588 |
| BGE dense | 0.9167 | 0.9433 | 0.3567 | 0.0767 | 1698 | 1852 |
| BGE IntentRoute | 0.9167 | 0.9200 | 0.3700 | 0.0767 | 1596 | 1741 |
| E5 dense | 0.9167 | 0.9300 | 0.4100 | 0.0700 | 1525 | 1663 |
| E5 IntentRoute | 0.9200 | 0.9333 | 0.3633 | 0.0567 | 1341 | 1458 |
| Dense+MMR | 0.8900 | 0.9100 | 0.0733 | 0.0800 | 1240 | 1393 |
| IntentRoute+MMR | 0.9133 | 0.9267 | 0.0833 | 0.0900 | 1157 | 1267 |

**Supplementary Table S9. Original DeepSeek-judged paired downstream comparisons.**

| Comparison | Correct delta | 95% CI | McNemar $p$ | Token saving | 95% CI |
|---|---:|---:|---:|---:|---:|
| BGE IntentRoute vs dense | +0.00 pp | [-2.67, +2.67] pp | 1.000 | 6.00% | [4.01%, 7.97%] |
| E5 IntentRoute vs dense | +0.33 pp | [-3.00, +3.67] pp | 1.000 | 12.04% | [9.93%, 14.16%] |
| IntentRoute+MMR vs Dense+MMR | +2.33 pp | [-1.67, +6.33] pp | 0.324 | 6.65% | [4.28%, 8.97%] |

The context-saving intervals are positive while correctness intervals include
zero. The multi-judge extension below tests whether this conclusion depends on
the original DeepSeek judge.

**Supplementary Table S10. Multi-judge coverage and calibration.**

| Judge | Valid | Coverage | Correctness mean | Correct | Faithfulness mean | Faithful | Citations supported |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek | 2,100 | 100.00% | 4.672 | 91.33% | 4.782 | 93.10% | 89.57% |
| GLM-5.2 | 2,100 | 100.00% | 4.550 | 88.24% | 4.734 | 92.81% | 92.14% |
| MiniMax-M3 | 2,065 | 98.33% | 4.293 | 85.71% | 4.633 | 95.45% | 94.48% |

MiniMax-M3 rejects 35 query-method inputs spanning 18 queries through
provider-side content filtering. These values are not imputed. Absolute score
calibration differs across judges, so raw ordinal scores are not pooled.

**Supplementary Table S11. Pairwise agreement on 2,065 shared judgments.**

| Field | Judge pair | Raw agreement | Cohen's $\kappa$ |
|---|---|---:|---:|
| Correct | DS / GLM | 91.04% | 0.508 |
| Correct | DS / MM | 89.88% | 0.503 |
| Correct | GLM / MM | 92.15% | 0.653 |
| Faithful | DS / GLM | 91.72% | 0.364 |
| Faithful | DS / MM | 93.27% | 0.374 |
| Faithful | GLM / MM | 93.41% | 0.405 |

Here DS denotes DeepSeek and MM denotes MiniMax-M3. Three-judge unanimity is
86.54% for correctness and 89.20% for faithfulness.
The corresponding majority-positive rates are 88.96% and 95.35%. High raw
faithfulness agreement coexists with lower $\kappa$ because positive judgments
are highly prevalent.

**Supplementary Table S12. Three-judge-majority paired comparisons.**

| Comparison | $n$ | Correct delta (95% CI) | McNemar $p$ | Faithful delta (95% CI) | McNemar $p$ | Context saving (95% CI) |
|---|---:|---:|---:|---:|---:|---:|
| BGE IntentRoute vs dense | 289 | -3.46 pp [-6.92, 0.00] | 0.0755 | -4.15 pp [-6.92, -1.73] | 0.0018 | 6.27% [4.22%, 8.26%] |
| E5 IntentRoute vs dense | 289 | -2.08 pp [-5.88, +1.73] | 0.3616 | -0.69 pp [-3.81, +2.42] | 0.8238 | 11.97% [9.78%, 14.17%] |
| IntentRoute+MMR vs Dense+MMR | 295 | +0.34 pp [-3.39, +4.07] | 1.0000 | +4.07 pp [+0.68, +7.46] | 0.0290 | 6.75% [4.40%, 9.11%] |

No individual judge or majority-vote comparison finds a significant
correctness difference. This supports a bounded correctness-robustness claim,
not strict non-inferiority. Faithfulness is mixed: the BGE majority result is
negative, while the SentMMR composition is positive. The evaluation remains
LLM-as-judge evidence rather than human evaluation. The under-specified
`insufficient_context_appropriate` field is retained in raw artifacts but
excluded from headline analysis.

## S7. Calibration/Test Context-Budget Validation

The calibration/test protocol selects the final-context budget on calibration
queries and freezes it before evaluation on held-out test queries.
Tables~\ref{tab:s13}, \ref{tab:s14}, \ref{tab:s15}, and~\ref{tab:s16} report the
frozen split, independent calibration, partition sensitivity, and normalized
five-fold audit.

**Supplementary Table S13. Frozen context-budget validation on LoTTE technology/search.**

| Scale | Selected policy | Calibration eligible | Hit delta vs dense | Token saving | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False / original split | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

The calibrated policies should be compared against dense-only adaptive
truncation because both reduce final context size. IntentRoute preserves
substantially more $\mathrm{Hit@10}$ at a still meaningful token saving level.
The 400k row is diagnostic rather than calibration-eligible in the original
artifact set. Supplementary Table S16 reports the completed cross-fitted follow-up.

**Supplementary Table S14. Independently calibrated 100k quality constraints.**

| Calibration Hit margin | IntentRoute policy | IR test Hit delta | IR saving | Dense policy | Dense test Hit delta | Dense saving |
|---:|---|---:|---:|---|---:|---:|
| 0.0pp | `r0.95/m4` | +0.00pp | 6.18% | `r1.00/m4` | +0.00pp | 0.00% |
| 0.5pp | `r0.93/m4` | -0.32pp | 7.97% | `r1.00/m4` | +0.00pp | 0.00% |
| 1.0pp | `r0.84/m4` | -1.28pp | 17.13% | `r1.00/m4` | +0.00pp | 0.00% |
| 2.0pp | `r0.80/m4` | -1.60pp | 20.90% | `r0.82/m4` | -2.40pp | 25.22% |

The zero-margin row preserves equal mean test Hit while selecting nonzero
IntentRoute saving, but strict seed-level non-inferiority remains 0/3. Held-out
same-saving interpolation is descriptive only and finds small IntentRoute-minus-
Dense Hit differences from `+0.47pp` at 5% saving to `-0.01pp` at 20%.

**Supplementary Table S15. Calibration-partition sensitivity over 20 overlapping splits.**

| Scale | Eligible splits | Test Hit range | Mean test Hit delta | Saving range | Within 1pp of dense |
|---|---:|---:|---:|---:|---:|
| 100k | 12/20 | [-2.00, +0.72]pp | -0.45pp | [6.18%, 17.73%] | 14/20 |
| 200k | 19/20 | [+0.56, +3.52]pp | +1.53pp | [5.33%, 17.29%] | 20/20 |
| 400k | 16/20 | [-2.08, +2.80]pp | +0.45pp | [6.57%, 18.27%] | 17/20 |
| 638k | 19/20 | [-0.88, +2.24]pp | +0.44pp | [7.85%, 17.91%] | 20/20 |

These partitions reuse the same frozen rankings and overlap in their query
membership. They diagnose policy-selection sensitivity and must not be counted
as 20 independent experiments. The result supports stronger split stability at
200k/638k, moderate sensitivity at 100k, and continued diagnostic treatment of
400k.

**Supplementary Table S16. Normalized five-fold out-of-fold calibration using identical canonical query folds and policy rules across scales.**

| Scale | Eligible folds | Mean Hit delta | Mean token saving | Strict NI seeds | Selected-policy count | Dense compressed folds |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 2/5 | -1.06pp | 4.16% | 0/3 | 2 | 0/5 |
| 200k | 5/5 | +1.40pp | 16.07% | 2/3 | 1 | 0/5 |
| 400k | 5/5 | +0.00pp | 14.50% | 0/3 | 5 | 0/5 |
| 638k | 5/5 | +0.28pp | 15.23% | 0/3 | 3 | 0/5 |

Each canonical LoTTE query is held out exactly once and remains in the same
fold at every corpus scale. Dense and IntentRoute independently select from
the predefined budget grid; when no policy satisfies the zero-drop gate,
the method uses Dense top-10 fallback. The 400k result closes the missing
normalized calibration check, but its five distinct policies and 0/3 strict
non-inferiority result retain the partition-sensitivity boundary. The 100k row
similarly shows that positive original-split behavior does not imply uniform
cross-fitted behavior.

## S8. Cross-Domain Validation

LoTTE science/search is used as a second-domain validation, not as a replacement
for the main LoTTE technology/search scale-up.
Tables~\ref{tab:s17} and~\ref{tab:s18} separate ranking transfer from frozen-budget behavior.

**Supplementary Table S17. Science/search fixed top-10 ranking validation.**

| Domain/scale | Corpus chunks | Queries | Dense $\mathrm{Hit@10}$ | IntentRoute $\mathrm{Hit@10}$ | Hit delta |
|---|---:|---:|---:|---:|---:|
| science/search 20k/q200 | 20,490 | 200 | 0.8950 | 0.9267 | +3.17 pp |
| science/search 100k | 101,187 | 596 | 0.8926 | 0.9077 | +1.51 pp |

**Supplementary Table S18. Science/search frozen context-budget validation.**

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

## S9. Feedback-Driven Hard-Case Recovery

Hard-case recovery focuses on affected queries where dense top-10 retrieves at
least one GT chunk but the budgeted IntentRoute context misses.
Tables~\ref{tab:s19} and~\ref{tab:s20} distinguish same-query repair from held-out recovery.

**Supplementary Table S19. Same-query feedback recovery on affected queries.**

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

**Supplementary Table S20. Calibration-to-test recovery generalization.**

| Domain | Frozen test recovery policy | Mean hit delta versus budgeted-before-feedback | Avg token saving vs dense |
|---|---|---:|---:|
| science 100k | conservative budget on learned risky arms after calibration | +0.16 pp | 16.13% |
| science 100k | full-context fallback on learned risky arms after calibration | +0.48 pp | 13.09% |
| technology 100k | conservative budget on learned risky arms after calibration | -0.16 pp | 5.88% |
| technology 100k | full-context fallback on learned risky arms after calibration | +0.16 pp | 4.25% |

The held-out effect is small and domain-dependent. Feedback should therefore be
used as a controlled fallback trigger rather than as unconditional global
reranking.

### S9.1 Frozen Unseen-Query Policy Audit

The formal frozen-policy audit trains learned route state on four disjoint canonical folds for eight
prequential epochs, freezes policy matrices, feedback memory, route statistics,
and reward history, then ranks the fifth fold once with zero held-out feedback
updates. This retrieval-only audit covers 596 queries per domain, five folds,
and seeds 13/17/19.

On technology/search 100k, learned full routing reaches
$\mathrm{Hit@10}=0.8792$ versus 0.8674 for Dense, but is 0.11pp below cold
no-feedback full routing and has no significant paired advantage over
static-nearest full routing. On science/search 100k, learned full routing
reaches 0.9004 versus 0.8926 for Dense, but is 0.39pp below cold no-feedback
full and 0.56pp below static-nearest full. Learned gated routing is significantly
below Dense in all seeds in both domains (-4.08pp and -5.59pp mean deltas).
The audit therefore supports transfer of the full Dense/BM25-rescued route
surface, not a universal first-pass advantage of learned simulated feedback.

## S10. Strong Post-Retrieval Baselines

These baselines test whether simpler post-retrieval operations explain the
main final-context result.
Tables~\ref{tab:s21}, \ref{tab:s22}, \ref{tab:s23}, and~\ref{tab:s24} report
matched compression, reranking, and prompt-pruning controls.

**Supplementary Table S21. Dense+Sentence-MMR same-budget baseline on LoTTE
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

**Supplementary Table S22. Compressor-normalized comparison on LoTTE
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

**Supplementary Table S23. Cross-encoder reranker baseline on LoTTE
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

**Supplementary Table S24. SelectiveContext-lite prompt-pruning baseline.**

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
does not replace upstream route control or final-budget calibration.

## S11. Route-Control Attribution and Arm Sensitivity

Tables~\ref{tab:s25}, \ref{tab:s26}, \ref{tab:s27}, and~\ref{tab:s28} isolate
geometry, feedback, arm granularity, and frozen-trajectory route mediation.

**Supplementary Table S25. Static geometry versus uniform-random route control.**

| Setting | Full top-10 hit | Route reward | Selected-cluster hit | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Static nearest geometry | 0.8764 | 0.8563 | 0.8870 | +1.44 pp | 5.03% |
| Uniform random control | 0.8842 | 0.1499 | 0.1577 | +1.04 pp | 11.92% |

Dense/BM25 rescue keeps final fused hit high in both rows, while route reward
and selected-cluster hit separate meaningful local routing from random arm
selection. Geometry is therefore supported as a route-control signal, not a
standalone explanation of final fused quality.

**Supplementary Table S26. Feedback and static route controls.**

| Setting | Route reward | Selected-cluster hit | Dense rate | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Learned full multi-route | 0.6790 | 0.5766 | 1.0000 | -1.68 pp | 17.86% |
| Learned gated | 0.6790 | 0.5766 | 0.7377 | -5.20 pp | 11.83% |
| Static nearest gated | 0.8563 | 0.8870 | 0.9586 | -2.40 pp | 12.01% |
| No-feedback gated | 0.1504 | 0.1570 | 1.0000 | -1.60 pp | 16.56% |

Feedback-updated LinUCB improves route quality over no-feedback/random controls,
but the learned gated threshold is a cost-aggressive boundary. Static geometry
remains a strong prior, while dense fallback explains part of the fused result.

**Supplementary Table S27. Arm-count sensitivity.**

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

**Supplementary Table S28. Frozen-trajectory dynamic route mediation; Save is relative
to uncompressed dense.**

| Route | Src. Hit | Budget Hit | Save |
|---|---:|---:|---:|
| Gated | 0.8793 | 0.8705 | 6.18% |
| Full | 0.8841 | 0.8745 | 5.27% |
| Shuffled | 0.8313 | 0.8225 | 6.54% |
| Cluster | 0.7698 | 0.7626 | 6.93% |
| Dense | 0.8705 | 0.8561 | 13.83% |

The replay freezes selected arms and feedback state, and exactly reproduces the
original dynamic ranking before changing route shapes. Dynamic gating exceeds
the shuffled-tier control by 4.80 percentage points before and after the common
budget, with 3/3 paired intervals excluding zero. It does not exceed fixed full
fusion; instead, it exposes a bounded quality-cost trade-off. Route confidence
has no detected association with oracle safe-token headroom, so the result
supports route assignment rather than direct compression-safety prediction.

## S12. Reproducibility and Reporting Guardrails

### S12.1 Standard Ranking Metrics

For mean reciprocal rank, let $\rho_t$ be the rank of the first relevant chunk
within the top-$K$ list, or $\infty$ if no relevant chunk is retrieved:

$$
\mathrm{MRR@K}(q_t) =
\begin{cases}
\frac{1}{\rho_t}, & \rho_t \le K, \\
0, & \rho_t = \infty.
\end{cases}
$$

For binary relevance $\mathrm{rel}_{t,j} \in \{0,1\}$, we compute:

$$
\mathrm{DCG@K}(q_t) =
\sum_{j=1}^{K} \frac{\mathrm{rel}_{t,j}}{\log_2(j+1)},
$$

$$
\mathrm{nDCG@K}(q_t) =
\frac{\mathrm{DCG@K}(q_t)}{\mathrm{IDCG@K}(q_t)}.
$$

If $\mathrm{IDCG@K}(q_t)=0$, we set $\mathrm{nDCG@K}(q_t)=0$.

### S12.2 Controller Parameters

The complete shared controller configuration is:

- KMeans/MiniBatchKMeans arms: 32 fixed LinUCB arms;
- candidate arms per query: 3 cluster-local routes;
- context projection dimension: 64;
- LinUCB exploration: $\alpha=1.0$, decay 0.01, minimum 0.3;
- prequential epochs: 3 unless otherwise stated;
- feedback trust: default $\tau=0.75$ for noisy feedback updates;
- full-route candidate depths: dense/BM25/cluster = 100/100/100;
- lite-route depths: dense/BM25 = 20/20;
- dense safety floor: 5 full-route chunks and 2 lite-route chunks;
- route fusion: weighted reciprocal-rank fusion with $k=60$;
- full-route weights: dense 2.0, BM25 0.8, cluster 0.8;
- lite-route weights: dense 0.8, BM25 0.5, cluster 2.0;
- confidence thresholds: high 0.65 and mid 0.35;
- drift threshold: 1.0;
- token-budget grid: $r \in \{0.85,0.88,0.90,0.92,0.95,0.98\}$ and
  $m \in \{4,\ldots,8\}$.

The notation `token_budget_r0.85_m4` means that each query keeps a safe prefix
of at least four chunks and admits additional chunks only while the final
context remains within 85% of the original dense top-10 token budget. The
policy is selected on calibration queries and frozen before held-out test
evaluation.

### S12.3 Reporting Guardrails

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

### S12.4 Result-Family Protocol Registry

**Supplementary Table S29. Dataset, protocol, and evidentiary-role registry.**

| Result family | Corpus and query scope | Route/feedback protocol | Budget and paired endpoint | Paper role and boundary |
|---|---|---|---|---|
| LoTTE technology/search scale anchor | 100k--638k nested corpora; 596 canonical queries (417 in the original frozen split; 596 in OOF) | MiniLM, top-10, K=32, seeds 13/17/19; frozen scale-route artifacts | Original 30/70 calibration/test plus normalized five-fold OOF; paired bootstrap, McNemar, and 1pp NI | Main scale evidence; original and OOF results are reported separately |
| LoTTE science/search diagnostic | 20k/q200; 200 sampled queries | Historical MiniLM fixed-split route study | Fixed 30/70 calibration/test | Legacy cross-domain ranking and budget diagnostic; not pooled with OOF rows |
| LoTTE science/search common rows | 100k, 200k, 400k; 596 queries per scale | MiniLM, top-10, K=32, seeds 13/17/19; 8 prequential epochs; final-fused simulated feedback with no-feedback control | Five-fold OOF zero-drop budget selection, Dense fallback, paired bootstrap, McNemar, 1pp NI, and recovery replay | Cross-domain evidence; 400k is a weak scale boundary (1/5 eligible folds) |
| LoTTE recreation/search and writing/search expansion | 100,714/924 and 100,696/1,071 corpus/query pairs | MiniLM, top-10, K=32, seeds 13/17/19; 8 prequential epochs; trust-weighted and no-feedback controls | Five-fold OOF zero-drop budget selection, Dense fallback, paired bootstrap, McNemar, 1pp NI, geometry diagnostics, and post-failure recovery | Preregistered 100k external-validity test; writing is a useful no-feedback frontier, recreation is a weaker boundary, and trust-weighted calibration falls back in both; no pooling |
| Frozen-policy unseen-query audit | LoTTE technology/search and science/search 100k; 596 queries each | Five history/test folds; seeds 13/17/19; eight history epochs; policy and feedback state frozen on the held-out fold | Query-paired bootstrap and McNemar on retrieval metrics; no held-out feedback update or budget endpoint | Boundary evidence: full rescue surface transfers, but learned feedback does not beat matched static/cold full routing and frozen gating is unsafe |
| PubMedQA, CovidQA-RAG, eManual deduplicated | Native full: 4,348/1,000; 32,392/1,726; 1,729/130 corpus/query pairs | MiniLM, top-10, K=32, seeds 13/17/19; 8 prequential epochs; final-fused trust/no-feedback controls | Five-fold OOF zero-drop budget selection and paired statistics | Transfer and corrected-boundary rows; not a shared scale curve |
| Banking77 and CUAD | Banking77 native 10,003/3,080; CUAD GT-anchored 10k/79 evaluated | Historical route-learning proxy and sparse-GT smoke protocols | No common OOF token endpoint | Mechanism and boundary evidence only; excluded from pooled evidence-retrieval conclusions |

Table~\ref{tab:s29} is the canonical registry for the matched protocol
definitions used in the cross-dataset comparisons.

The registry describes the paper-facing result families rather than retroactively
equating their tasks. Detailed artifact hashes, historical protocol labels, and
all route parameters remain in the reproducibility audit under
`paper/experiments/`.

## S13. Preregistered LoTTE Domain Expansion

The domain-expansion protocol selected recreation/search and writing/search before downloading or
inspecting their outcomes, then retained both after the preregistered lexicality
ordering was contradicted. Recreation/search has lower query-positive token
coverage than writing/search (0.6755 versus 0.7478) and lower maximum Jaccard
overlap (0.0787 versus 0.1003). The corresponding recreation-minus-writing
bootstrap intervals are [-0.0901, -0.0543] and [-0.0268, -0.0165]. The
original lexicality premise is therefore not used to explain the budget result.
Table~\ref{tab:s30} reports the matched route and budget outcomes.

**Supplementary Table S30. Preregistered LoTTE 100k domain expansion. Full-route
Hit precedes independent five-fold context-budget calibration; trust rows with
zero eligible folds use Dense top-10 fallback.**

| Domain / control | Lexical coverage | Dense Hit | Full-route Hit | Nearest-cluster Hit@3 | Eligible folds | Budget Hit delta | Token saving | Strict NI seeds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| recreation / trust | 0.6755 | 0.8496 | 0.8597 | 0.8366 | 0/5 | +0.00 pp | 0.00% | n/a (fallback) |
| recreation / no feedback | 0.6755 | 0.8496 | 0.8546 | 0.8366 | 4/5 | -0.76 pp | 5.42% | 0/3 |
| writing / trust | 0.7478 | 0.8739 | 0.8842 | 0.8655 | 0/5 | +0.00 pp | 0.00% | n/a (fallback) |
| writing / no feedback | 0.7478 | 0.8739 | 0.8842 | 0.8655 | 5/5 | +0.12 pp | 10.09% | 2/3 |

Both domains contain usable cluster-local route signal, but their calibrated
frontiers and strict seed-level stability differ. The result supports bounded
external validity and domain-specific calibration. It does not establish that
geometry or trust-weighted feedback directly predicts compression safety, and
it does not convert Dense fallback into a positive token-saving result.

The post-failure replay remains supporting evidence only. Across seed-level
compression-only failures, arm boost recovers 12/40 events on
recreation/search and 28/29 on writing/search. Because the retry observes the
same query's simulated failure feedback, it is not first-pass unseen-query
generalization.
