# 5. Results

## 5.1 Calibrated Token-Quality Frontier

The main cost result uses a calibrated token-budget policy. For each corpus
scale, the budget is selected on calibration queries and then frozen before
test evaluation. Cost is measured as final LLM evidence-context input tokens
relative to dense top-10, not retrieval-side candidate count.
Table~\ref{tab:1} reports the resulting scale-wise operating points.

**Table 1. Calibrated token-quality frontier on LoTTE technology/search.**

| Scale | Frozen policy | Calib. eligible | IntentRoute hit delta | NI seeds | IntentRoute token saving | Dense-trunc hit delta | Dense-trunc token saving |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 0/3 | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 1/3 | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False / diagnostic | +2.32 pp | 3/3 | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 0/3 | 17.53% | -3.84 pp | 21.90% |

The calibration-eligible 100k, 200k, and 638k operating points save 6-18%
final context tokens. The 400k row is retained as a diagnostic point because
no candidate met the zero-observed-hit-drop calibration gate, even though its
frozen-test result is positive. Dense-only adaptive truncation saves more
tokens but loses $\mathrm{Hit@10}$ at every scale. IntentRoute therefore
targets a more quality-preserving bounded frontier rather than maximum
compression.

An independently calibrated 100k audit gives Dense and IntentRoute the same
fine budget grid but lets each select its own action. Under the zero observed
calibration-drop rule, IntentRoute selects `r0.95/m4` and retains the
Table~\ref{tab:1}
result of `6.18%` test saving with `0.00pp` mean Hit delta; Dense selects
`r1.00/m4`, or no compression. Their mean test Hit is equal, although strict
IntentRoute non-inferiority is not established in any seed. A descriptive
same-saving interpolation over the held-out Pareto curves shows only small Hit
differences: `+0.47pp`, `+0.04pp`, `+0.22pp`, and `-0.01pp` at 5%, 10%, 15%,
and 20% saving, respectively. This supports a bounded conservative operating
point, not universal frontier dominance.

A 20-partition sensitivity audit further separates stable scales from split
sensitivity. Frozen selected policies retain mean Hit within `1pp` of dense on
all 20 test partitions at 200k and 638k, versus 14/20 at 100k and 17/20 at 400k.
The 100k mean range is `-2.00pp` to `+0.72pp`; 400k varies from `-2.08pp` to
`+2.80pp`. The original pre-specified split remains the primary result, while
the repeated partitions strengthen 200k/638k and keep 100k/400k interpretation
more cautious.

A normalized five-fold follow-up uses the same canonical query folds,
predefined budget grid, zero-drop gate, three route seeds, Dense fallback, and paired
statistics at every scale. Its out-of-fold IntentRoute Hit deltas and token
savings are respectively `-1.06pp/4.16%`, `+1.40pp/16.07%`,
`+0.00pp/14.50%`, and `+0.28pp/15.23%` from 100k through 638k. Independently
calibrated Dense finds no eligible compressed action in any fold and therefore
uses top-10 fallback. At 400k, all five IntentRoute folds are eligible, closing
the missing normalized follow-up, but they select five different policies and
strict non-inferiority remains `0/3` seeds. Supplementary Table S16 reports the fold-level
results. This supports the average 400k trade-off without erasing the original
split failure or claiming stable policy selection.

Query-level paired bootstrap intervals and McNemar-style win/loss counts show
that token savings are more consistent than strict quality non-inferiority.
The conservative confidence-only policy remains a stable 4.7-5.3% saving
baseline; complete seed and policy details are reported in Supplementary Sections S1 and S7.
Figure 2 visualizes the quality-cost frontier.

## 5.2 Matched-Backbone Robustness

Matched-backbone evaluation tests whether the controller pattern is specific
to MiniLM. Each IntentRoute row is compared with dense retrieval using the same
encoder and frozen test split.
Table~\ref{tab:2} summarizes the matched-backbone comparison.

**Table 2. Matched-backbone operating points on LoTTE technology/search 100k.**

| Backbone and policy | Dense $\mathrm{Hit@10}$ | IntentRoute $\mathrm{Hit@10}$ | Hit delta | Token saving |
|---|---:|---:|---:|---:|
| MiniLM calibrated | 0.8705 | 0.8705 | +0.00 pp | 6.18% |
| BGE full multi-route | 0.8993 | 0.8985 | -0.08 pp | 11.99% |
| E5 full multi-route | 0.8753 | 0.8689 | -0.64 pp | 12.20% |
| BGE quality-first | 0.8993 | 0.9081 | +0.88 pp | 7.23% |

BGE and E5 full multi-route policies remain near their respective dense
baselines while saving about 12% context tokens. The BGE quality-first point
moves the same frontier toward higher retrieval hit at lower saving. The E5
scan did not produce an above-dense token-saving point, so positive-hit
tunability is BGE-specific rather than a universal claim. Supplementary Section S5 reports
the supporting encoder details.

## 5.3 Route-Control Attribution

The route controls isolate geometry, feedback, and dense rescue. The
geometry-versus-random rows change arm selection under an otherwise matched
full rescue surface. The learned, static, and no-feedback rows test whether
LinUCB updates and gating explain route quality and final cost.
Table~\ref{tab:3} separates route-level effects from rescued final quality.

**Table 3. Geometry, feedback, and rescue-route controls on LoTTE technology/search 100k. Each row uses its paired frozen-protocol dense baseline.**

| Control | Route reward | Cluster hit | Dense rate | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Static nearest geometry | 0.8563 | 0.8870 | 1.0000 | +1.44 pp | 5.03% |
| Uniform random arms | 0.1499 | 0.1577 | 1.0000 | +1.04 pp | 11.92% |
| Learned full multi-route | 0.6790 | 0.5766 | 1.0000 | -1.68 pp | 17.86% |
| Learned gated | 0.6790 | 0.5766 | 0.7377 | -5.20 pp | 11.83% |
| Static-nearest gated | 0.8563 | 0.8870 | 0.9586 | -2.40 pp | 12.01% |
| No-feedback gated | 0.1504 | 0.1570 | 1.0000 | -1.60 pp | 16.56% |

Static nearest geometry sharply exceeds random routing on route reward and
selected-cluster hit, but dense and BM25 rescue keep final fused hit high for
both. Feedback-updated LinUCB likewise improves route quality over the
no-feedback control, but the tested learned-gated threshold loses 5.20
percentage points of frozen-test hit. These results support geometry and
feedback as route-confidence signals; neither alone explains final fused
quality or justifies unconditional dense removal.

Feedback remains useful as a recovery trigger. Conservative same-query retry
recovers 23 of 76 budget-induced misses across the technology/search and
science/search 100k settings, but
the stricter calibration-to-test effect is small and domain-dependent.
Supplementary Sections S9 and S11 contain the full recovery and control tables.

A frozen-trajectory route replay further isolates the confidence gate. Keeping
the selected arms and feedback state fixed, the original query-to-tier
assignment exceeds a shuffled-tier control with identical tier frequencies by
4.80 percentage points of Hit@10, both before and after the common
`r0.95/m4` budget; all three seed-level paired intervals exclude zero. It also
exceeds an always-cluster-primary route by 10.79 percentage points after
budgeting. Fixed full fusion remains 0.40 percentage points above dynamic
gating while saving 0.91 percentage points fewer tokens, and that hit
difference is not statistically detected. The result supports confidence as a
route/fallback assignment signal, not as a direct compression-safety score.

## 5.4 Arm Granularity And Geometry-To-Control Analysis

Arm-count sensitivity tests whether the fixed $K=32$ clustering choice is a
hidden optimum. Full multi-route quality remains stable over a 16-fold range,
whereas aggressive gated behavior changes substantially with arm granularity.
Table~\ref{tab:4} reports the tested arm-count grid.

**Table 4. Arm-count sensitivity on LoTTE technology/search 100k.**

| $K$ | Static route reward | Full hit delta | Full token saving | Gated dense rate | Gated hit delta |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.9128 | +1.44 pp | 6.23% | 0.4083 | -1.84 pp |
| 16 | 0.8826 | +0.80 pp | 10.49% | 0.6089 | -1.68 pp |
| 32 | 0.8563 | +0.56 pp | 4.68% | 0.7377 | -4.48 pp |
| 64 | 0.8272 | +0.40 pp | 11.19% | 0.8986 | -3.76 pp |
| 128 | 0.8479 | +1.20 pp | 10.23% | 0.9502 | -3.12 pp |

The full route surface stays above its paired dense baseline throughout the
grid, while gated dense use rises from 0.4083 to 0.9502 as $K$ grows. This
supports $K$ as an engineering parameter governing feedback sparsity and
fallback behavior, not a geometrically privileged constant.

Across LoTTE technology/search scales, nearest-cluster hit remains high while context retention
and PCA concentration vary. Figure 3 relates context retention to observed hit
delta and token saving. The small cross-scale sample does not show a
deterministic geometry-to-gain law: geometry identifies plausible local route
structure, while calibration, fusion, and dense rescue determine the final
operating point. Full diagnostics are retained in Supplementary Section S11.

## 5.5 Cross-Domain, Mechanism, And Boundary Evidence

On LoTTE science/search, fixed top-10 IntentRoute reaches
$\mathrm{Hit@10}=0.9267$ versus 0.8950 for dense at 20k/q200 and 0.9077 versus
0.8926 at 100k. Frozen budget policies save 13-14% tokens at 20k/q200 while
remaining above dense. At 100k, the more aggressive policy saves 17-21% but
can introduce small hit losses. The ranking signal transfers, but compression
strength requires domain- and scale-specific calibration. Supplementary Section S8 reports
the complete seed-level table.

The matched five-fold protocol makes this boundary explicit on the
shared 596-query science/search population. At 100k, 200k, and 400k, the mean
IntentRoute $\mathrm{Hit@10}$ deltas are -0.11pp, -0.67pp, and -0.67pp, with
16.88%, 10.75%, and 3.15% final-context token saving, respectively; strict
1pp non-inferiority is `0/3` seeds at every scale. At 400k, only one of five
folds selects a compressed policy. Its recovery replay has only 3-6
budget-induced affected queries per seed, so it closes a protocol endpoint but
does not overturn the scale-boundary interpretation. The supplementary protocol
registry records the matched protocol and evidence roles without pooling these rows into
the technology/search headline.

The supporting transfer checks cover different retrieval abstractions and dense
ceilings. On PubMedQA, dense retrieval reaches $\mathrm{Hit@10}=0.9930$, while
the trust-weighted policy reaches $0.9940$ with selected-cluster hit $0.8860$.
CovidQA-RAG is more discriminative: dense reaches $\mathrm{Hit@10}=0.6095$,
trust-weighted fixed top-10 IntentRoute reaches $0.6300$, and a five-fold
budgeted evaluation saves 8.34% final-context tokens with a -0.21 percentage
point mean hit delta versus dense. The strict 1pp non-inferiority rule remains
unmet on CovidQA-RAG, so this row supports transfer of the quality-efficiency
trade-off rather than a guaranteed non-inferior result. On the Banking77
intent-routing proxy, the corresponding dense and trust-weighted scores are
$0.9805$ and $0.9844$, and selected-cluster hit reaches $0.9983$. The
near-ceiling PubMedQA and Banking77 final scores limit claims about aggregate
improvement, but the route diagnostics support feedback adaptation beyond the
LoTTE task format.

The two boundary datasets explain why benchmark construction matters. eManual
contains 18,812 chunks but only 1,729 unique text strings: dense
$\mathrm{Hit@10}$ increases from $0.3231$ under strict chunk identity to
$0.5615$ under text-equivalent matching and $0.8615$ after corpus
deduplication. On the GT-anchored CUAD sample, dense reaches $0.0759$ and the
trust-weighted smoke run reaches $0.0886$; sparse evidence anchors prevent this
sample from serving as full-corpus positive evidence. Supplementary Sections
S4 and S8 retain the complete tables. These datasets support mechanism,
transfer, and boundary analysis rather than replacing the LoTTE token-saving
headline or establishing universal dense-retrieval dominance.

## 5.6 Strong Post-Retrieval Baselines

Dense+Sentence-MMR preserves dense chunk-support
$\mathrm{Hit@10}=0.8705$ while saving 11.4-13.1% selected-sentence tokens.
When the same compressor is applied to both source pools,
IntentRoute+Sentence-MMR reaches 10.1-21.2% total saving because it starts from
a smaller evidence pool. SelectiveContext-lite similarly adds prompt pruning
after either source pool and reaches up to 30.57% total saving over dense for
the tested IntentRoute variants. These controls show that downstream
compression is complementary, not unique to IntentRoute.

A cross-encoder reranker improves dense full-top-10 support from
$\mathrm{Hit@10}=0.8705$ to 0.8777 and evidence recall from 0.7081 to 0.7332,
but increases context tokens by 21.9%. Under matched context budgets, its
$\mathrm{Hit@10}$ range of 0.8633-0.8729 does not uniformly dominate the
IntentRoute range of 0.8657-0.8777. Supplementary Section S10 contains all compressor and
reranker tables.

## 5.7 Downstream Answer-Level Evaluation

The frozen downstream evaluation contains 300 queries, seven methods, 2,100
generated answers, and 6,265 valid judgments from DeepSeek, GLM-5.2, and
MiniMax-M3. Cross-judge results use the 2,065 query-method keys valid for all
three judges; 35 MiniMax-M3 judgments rejected by provider-side filtering are
not imputed.
Table~\ref{tab:5} reports the matched correctness and context-token results.

**Table 5. Matched downstream answer-quality and context-token comparisons.**

| Comparison | DeepSeek $\Delta$ | GLM $\Delta$ | MiniMax $\Delta$ | Majority $\Delta$ (95% CI) | Context saving (95% CI) |
|---|---:|---:|---:|---:|---:|
| BGE IntentRoute vs BGE dense | +0.00 pp | -3.00 pp | -2.42 pp | -3.46 pp [-6.92, 0.00] | 6.27% [4.22%, 8.26%] |
| E5 IntentRoute vs E5 dense | +0.33 pp | -1.33 pp | -2.77 pp | -2.08 pp [-5.88, +1.73] | 11.97% [9.78%, 14.17%] |
| IntentRoute+MMR vs Dense+MMR | +2.33 pp | +0.33 pp | +1.36 pp | +0.34 pp [-3.39, +4.07] | 6.75% [4.40%, 9.11%] |

All context-saving intervals are positive. Every individual-judge and
majority-vote correctness interval includes zero, and all correctness McNemar
tests are non-significant. Absolute judge calibration differs: pairwise raw
agreement is 89.88-92.15% for correctness, with Cohen's $\kappa$ of
0.503-0.653. This supports lower context without a statistically detectable
correctness difference, but not strict non-inferiority or significant
answer-quality improvement.

Faithfulness is not uniformly preserved. The three-judge majority estimates a
-4.15 pp BGE faithfulness change (95% CI [-6.92, -1.73], $p=0.0018$) and a
+4.07 pp change for the SentMMR composition (95% CI [+0.68, +7.46],
$p=0.0290$); E5 remains non-significant. Supplementary Section S6 reports judge coverage,
agreement, full method-level results, and the mixed faithfulness boundary.
