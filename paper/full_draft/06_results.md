# 5. Results

## 5.1 Calibrated Token-Quality Frontier

The main cost result uses a calibrated token-budget policy. For each corpus
scale, the budget is selected on calibration queries and then frozen before
test evaluation. Cost is measured as final LLM evidence-context input tokens
relative to dense top-10, not retrieval-side candidate count.
Table~\ref{tab:1} reports the resulting scale-wise operating points.

**Table 1. Calibrated token-quality frontier on LoTTE technology/search.**

| Scale | Frozen context action | Calibration status | IntentRoute hit delta | NI seeds | IntentRoute token saving | Dense-trunc hit delta | Dense-trunc token saving |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | 95% budget; minimum 4 chunks | Eligible | +0.00 pp | 0/3 | 6.18% | -1.44 pp | 13.83% |
| 200k | 85% budget; minimum 4 chunks | Eligible | +1.20 pp | 1/3 | 16.00% | -2.40 pp | 21.95% |
| 400k | 98% budget; minimum 4 chunks | Diagnostic only | +2.32 pp | 3/3 | 6.57% | -0.24 pp | 11.44% |
| 638k | 85% budget; minimum 4 chunks | Eligible | -0.08 pp | 0/3 | 17.53% | -3.84 pp | 21.90% |

The calibration-eligible 100k, 200k, and 638k operating points save 6-18%
final context tokens. The 400k row is retained as a diagnostic point because
no candidate met the zero-observed-hit-drop calibration gate, even though its
frozen-test result is positive. Dense-only adaptive truncation saves more
tokens but loses $\mathrm{Hit@10}$ at every scale. IntentRoute therefore
targets a more quality-preserving bounded frontier rather than maximum
compression.

The artifact identifiers for these four actions are, respectively,
`token_budget_r0.95_m4`, `token_budget_r0.85_m4`,
`token_budget_r0.98_m4`, and `token_budget_r0.85_m4`; the journal-facing labels
state the same ratio and mandatory-prefix parameters directly.

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
strict non-inferiority remains `0/3` seeds. Supplementary Table S12 reports the fold-level
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

The formal frozen-policy audit separates this repeated-interaction evidence from
first-pass transfer to unseen queries. Across five folds and seeds 13/17/19,
learned full routing is above Dense on average in technology/search 100k
(+1.17pp) and science/search 100k (+0.78pp), but it does not exceed matched
cold no-feedback full routing (-0.11pp and -0.39pp) or static-nearest full
routing (+0.28pp and -0.56pp); no such paired comparison is significant across
all seeds. Learned gated routing is instead significantly below Dense by 4.08pp
and 5.59pp in the two domains. Thus, the full rescue surface transfers, whereas
controlled feedback is supported as repeated-query adaptation and conditional
recovery rather than a universal frozen first-pass improvement.

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

Arm-count sensitivity tests whether the fixed $K=32$ choice is a hidden
optimum. Figure 3 combines three evidence layers. Panel A shows that
nearest-cluster hit remains high across the measured technology/search and
science/search scales while context retention and PCA concentration vary.
Panel B shows the large static-geometry advantage over uniform-random arms in
route reward and selected-cluster hit, alongside their much smaller difference
in rescued final fused Hit. Panel C shows that gated Dense use rises from
0.4083 to 0.9502 over $K=8$--$128$, while every gated point loses Hit.

The complete arm-count grid is retained in Supplementary Table S20. Full
multi-route quality remains stable across that grid, so $K=32$ is a reproducible
engineering point governing route granularity, feedback sparsity, and fallback,
not a geometrically privileged optimum. The composite figure supports local
structure as a route-control surface; it does not posit a deterministic
geometry-to-token-saving law.

## 5.5 Cross-Domain, Mechanism, And Boundary Evidence

Table~\ref{tab:4} puts every completed dataset-scale endpoint in one evidence
matrix. The rows remain separate because they differ in query population,
ground-truth semantics, protocol, and evidentiary role; no pooled effect is
computed.

**Table 4. Cross-dataset and cross-domain evidence matrix. Five-fold rows use independently calibrated frozen budgets; the science 20k row is a legacy fixed-split diagnostic. Dashes denote no common final-context endpoint, and no rows are pooled.**

| Dataset | Scale | Dense Hit@10 | IntentRoute Hit@10 | Hit delta | Token saving | Strict NI seeds | Evidentiary role |
|---|---|---:|---:|---:|---:|---:|---|
| LoTTE technology/search | 100k | 0.8674 | 0.8568 | -1.06 pp | 4.16% | 0/3 | Full-stack scale |
| LoTTE technology/search | 200k | 0.7970 | 0.8110 | +1.40 pp | 16.07% | 2/3 | Full-stack scale |
| LoTTE technology/search | 400k | 0.7718 | 0.7718 | +0.00 pp | 14.50% | 0/3 | Split-sensitive scale |
| LoTTE technology/search | 638k | 0.7282 | 0.7310 | +0.28 pp | 15.23% | 0/3 | Full-stack scale |
| LoTTE science/search | 20k/q200 | 0.8929 | 0.9095 | +1.67 pp | 13.80% | 1/3 | Legacy cross-domain diagnostic |
| LoTTE science/search | 100k | 0.8926 | 0.8915 | -0.11 pp | 16.88% | 0/3 | Cross-domain |
| LoTTE science/search | 200k | 0.8574 | 0.8507 | -0.67 pp | 10.75% | 0/3 | Cross-domain scale |
| LoTTE science/search | 400k | 0.8238 | 0.8171 | -0.67 pp | 3.15% | 0/3 | Scale boundary |
| LoTTE recreation/search | 100k | 0.8496 | 0.8420 | -0.76 pp | 5.42% | 0/3 | External-validity boundary |
| LoTTE writing/search | 100k | 0.8739 | 0.8752 | +0.12 pp | 10.09% | 2/3 | External-validity frontier |
| PubMedQA | Native full | 0.9930 | 0.9930 | +0.00 pp | 0.00% | 3/3 | Dense-ceiling transfer |
| CovidQA-RAG | Native full | 0.6112 | 0.6091 | -0.21 pp | 9.00% | 0/3 | Biomedical transfer |
| eManual deduplicated | Native full | 0.8615 | 0.8590 | -0.26 pp | 16.20% | 0/3 | Corrected boundary |
| Banking77 | Native full | 0.9805 | 0.9844 | +0.39 pp | -- | -- | Intent-routing mechanism |
| CUAD GT-anchored | 10k sample | 0.0759 | 0.0886 | +1.27 pp | -- | -- | Sparse-GT boundary |

The common five-fold rows expose domain heterogeneity rather than a universal
no-loss rule. Science/search saving falls from 16.88% at 100k to 3.15% at 400k,
where only one fold compresses. Recreation/search yields 5.42% saving at
-0.76pp, whereas writing/search yields 10.09% at +0.12pp; trust-weighted
calibration selects Dense fallback in every fold of both domains. Their
$\mathrm{NearestClusterHit@3}$ values of 0.8366 and 0.8655 nevertheless show
that useful local-route structure can coexist with different safe budget
frontiers. Supplementary Table S23 retains their complete route and calibration
controls.

PubMedQA is a Dense-ceiling transfer row rather than evidence of additional
compression. CovidQA-RAG and deduplicated eManual provide non-ceiling transfer
and corrected-boundary results, while Banking77 and CUAD have no comparable
final-context endpoint. The latter two therefore support route mechanism or
benchmark-boundary analysis only. Supplementary Sections S4, S8, and S12 retain
the corresponding dataset, seed, and protocol details.

## 5.6 Strong Post-Retrieval Baselines

Dense+Sentence-MMR preserves dense chunk-support
$\mathrm{Hit@10}=0.8705$ while saving 11.4-13.1% selected-sentence tokens.
When the same compressor is applied to both source pools,
IntentRoute+Sentence-MMR reaches 10.1-21.2% total saving because it starts from
a smaller evidence pool. This matched control shows that downstream compression
is complementary rather than unique to IntentRoute. The official LLMLingua-2
follow-up applies the same learned compressor to both frozen source pools. On
300 queries, IntentRoute+LLMLingua-2 uses 1,175.0 mean context tokens versus
1,259.2 for Dense+LLMLingua-2, a paired 6.69% saving (95% CI [4.32%, 9.03%]).
The three-judge majority correctness change is +0.67 pp (95% CI [-3.00,
+4.33], $p=0.8642$), so the result supports compressor complementarity without
strict non-inferiority or significant quality improvement.

A cross-encoder reranker improves dense full-top-10 support from
$\mathrm{Hit@10}=0.8705$ to 0.8777 and evidence recall from 0.7081 to 0.7332,
but increases context tokens by 21.9%. Under matched context budgets, its
$\mathrm{Hit@10}$ range of 0.8633-0.8729 does not uniformly dominate the
IntentRoute range of 0.8657-0.8777. Supplementary Section S10 contains all compressor and
reranker tables.

## 5.7 Downstream Answer-Level Evaluation

The primary frozen downstream evaluation contains 300 queries, seven methods, 2,100
generated answers, and 6,272 valid judgments from DeepSeek, GLM-5.2, and
MiniMax-M3. Cross-judge results use the 2,072 query-method keys valid for all
three judges; 28 MiniMax-M3 judgments remain unavailable after provider-side
filtering and are not imputed. The matched LLMLingua-2 extension adds 600
generated answers and complete three-judge coverage for both new endpoints and
the two reused Sentence-MMR endpoints.
Table~\ref{tab:5} reports the matched correctness and context-token results.

**Table 5. Matched downstream answer-quality and context-token comparisons.**

| Comparison | DeepSeek $\Delta$ | GLM $\Delta$ | MiniMax $\Delta$ | Majority $\Delta$ (95% CI) | Context saving (95% CI) |
|---|---:|---:|---:|---:|---:|
| BGE IntentRoute vs BGE dense | +0.00 pp | -3.00 pp | -2.42 pp | -3.46 pp [-6.92, 0.00] | 6.27% [4.22%, 8.26%] |
| E5 IntentRoute vs E5 dense | +0.33 pp | -1.33 pp | -2.77 pp | -2.08 pp [-5.88, +1.73] | 11.97% [9.78%, 14.17%] |
| IntentRoute+MMR vs Dense+MMR | +2.33 pp | +0.33 pp | +1.33 pp | +0.33 pp [-3.33, +4.00] | 6.65% [4.19%, 8.97%] |
| IntentRoute + LLMLingua-2 vs Dense + LLMLingua-2 | +3.00 pp | +0.67 pp | +0.00 pp | +0.67 pp [-3.00, +4.33] | 6.69% [4.32%, 9.03%] |

All context-saving intervals are positive. Every individual-judge and
majority-vote correctness interval includes zero, and all correctness McNemar
tests are non-significant. Absolute judge calibration differs: pairwise raw
agreement is 89.88-92.15% for correctness, with Cohen's $\kappa$ of
0.503-0.653. This supports lower context without a statistically detectable
correctness difference, but not strict non-inferiority or significant
answer-quality improvement.

Faithfulness is not uniformly preserved. The three-judge majority estimates a
-4.15 pp BGE faithfulness change (95% CI [-6.92, -1.73], $p=0.0018$) and a
+3.67 pp change for the SentMMR composition (95% CI [+0.33, +7.00],
$p=0.0522$); E5 remains non-significant. Supplementary Section S6 reports judge coverage,
agreement, full method-level results, and the mixed faithfulness boundary.
