# 5. Results

## 5.1 Main Calibrated Token-Quality Frontier

The main cost result uses a calibrated token-budget policy. For each corpus
scale, the budget is selected on calibration queries and then frozen before
test evaluation. The measured cost is final LLM evidence-context input tokens
relative to dense top-10, not retrieval-side candidate count.

**Table 1. Calibrated token-quality frontier on LoTTE technology/search.**

| Scale | Frozen policy | Calib. eligible | IW hit delta | NI seeds | IW token saving | Dense-trunc hit delta | Dense-trunc token saving |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 0/3 | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 1/3 | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False / pending follow-up | +2.32 pp | 3/3 | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 0/3 | 17.53% | -3.84 pp | 21.90% |

The calibration-eligible operating points at 100k, 200k, and 638k save 6-18%
final evidence-context tokens under frozen policy selection. The 400k policy is
reported as a diagnostic frontier point and marked for follow-up: no candidate
satisfied the zero-observed-hit-drop calibration gate in the current run,
although the frozen test result is positive and all three seeds pass the
stricter 1pp non-inferiority check. This distinction prevents the table from
overstating calibration robustness while preserving 400k as a useful but
currently incomplete scale point.

Dense-only adaptive truncation usually saves more tokens, but it loses
$\mathrm{Hit@10}$ on every scale. This comparison shows that the effect is not
merely dense top-k truncation: route confidence helps decide where a shorter
context remains safe. Strict seed-level non-inferiority remains scale-dependent,
so the paper should claim a bounded quality-cost frontier rather than universal
statistical superiority.

The paired tests are query-level comparisons against dense top-10. They use
bootstrap confidence intervals for $\mathrm{Hit@10}$ deltas and final-context
token savings, and McNemar-style win/loss counts for hit differences. The
paired evidence supports token-cost superiority more consistently than strict
quality non-inferiority: all calibrated policies reduce final context tokens,
whereas the quality CI criterion is conservative and scale-dependent.

The earlier conservative confidence-only policy remains useful as a stable
baseline. It reduces final retrieved context tokens by 4.7-5.3% across LoTTE
technology/search 100k-638k while preserving dense-level $\mathrm{Hit@10}$.
Appendix A reports the complete confidence-only scale table and seed stability
diagnostics.

## 5.2 Cross-Domain Validation

We replicate the validation pattern on LoTTE science/search to test whether the
effect is limited to technology/search.

**Table 2. Cross-domain validation on LoTTE science/search.**

| Domain/scale | Dense $\mathrm{Hit@10}$ | IntentRoute fixed top-10 $\mathrm{Hit@10}$ | Hit delta | Budgeted token saving |
|---|---:|---:|---:|---:|
| science/search 20k/q200 | 0.8950 | 0.9267 | +3.17 pp | 13.18-14.31% |
| science/search 100k | 0.8926 | 0.9077 | +1.51 pp | 17.53-20.53% |

The fixed top-10 ranking-side effect transfers to a second LoTTE domain. The
context-budget result is more nuanced. At 20k/q200, the frozen budgeted
policies keep above-dense $\mathrm{Hit@10}$ while saving roughly 13-14% context
tokens. At 100k, the same aggressive budget saves roughly 17-21% tokens but can
introduce small $\mathrm{Hit@10}$ drops. This supports adaptive ranking across
domains while showing that compression strength must be calibrated per domain
and scale. Figure 2 includes both the technology/search scale-up and the
science/search budgeted validation points.

## 5.3 Component Ablation

The component ablation summarizes which parts of the system provide the quality
floor, routing signal, feedback adaptation, and final token saving on LoTTE
100k.

**Table 3. LoTTE 100k component ablation. The no-feedback gated row disables
learning; its high $\mathrm{Hit@10}$ reflects full dense fallback
($\mathrm{dense\ rate}=1.0$), not learned route efficiency.**

| Component | Role | $\mathrm{Hit@10}$ | $\mathrm{EvidenceRecall@10}$ | $\mathrm{Tokens@10}$ | Token ratio | Dense rate | LinUCB rate | Cluster hit | Last reward |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense-only | Quality floor | 0.8674 | 0.7026 | 1472.39 | 1.0000 | - | - | - | - |
| BM25-only | Lexical baseline | 0.7232 | 0.5240 | 1745.12 | 1.1852 | - | - | - | - |
| Dense+BM25 hybrid | Static fusion | 0.8624 | 0.6848 | 1705.46 | 1.1583 | - | - | - | - |
| No feedback gated | Full dense fallback, no learning | 0.8826 | 0.7246 | 1561.15 | 1.0603 | 1.0000 | 0.0000 | 0.1553 | 0.1516 |
| Equal noisy feedback | No trust weighting | 0.8641 | 0.6604 | 1423.84 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | Default trust scoring | 0.8641 | 0.6661 | 1399.51 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | Best controlled-noise point | 0.8775 | 0.6795 | 1362.68 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Conservative final policy | Confidence-only baseline | 0.8652 | 0.6737 | 1401.24 | 0.9517 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Oracle feedback | Upper bound | 0.8758 | 0.6768 | 1327.03 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

Dense-only remains the quality floor. BM25-only is weaker as a standalone
retriever, and static dense+BM25 hybrid is near dense but uses more final
context tokens. Trust-weighted feedback improves policy internals relative to
equal noisy feedback, especially selected-cluster hit and last true reward. The
oracle row shows the upper bound under clean feedback.

## 5.4 Feedback-Driven Adaptation and Recovery

Final $\mathrm{Hit@10}$ can be saturated by dense and BM25 rescue routes,
making feedback gains less visible in the fused final ranking. The clearer
feedback signal appears in route-policy metrics such as selected-cluster hit,
last true reward, dense rate, and LinUCB usage.

A dedicated control confirms this attribution. On the same 100k split,
feedback-updated LinUCB reaches route reward $0.6790$ versus $0.1504$ for the
no-feedback control and about $0.15$ for uniform random routing. Static nearest
geometry is a stronger prior at $0.8563$. The learned gated configuration can
reduce dense invocation, but its current threshold loses 5.20 percentage points
of frozen-test $\mathrm{Hit@10}$; it is therefore a cost-aggressive boundary,
not the main quality-preserving operating point. LinUCB is supported as an
adaptive confidence mechanism, not the sole source of fused retrieval quality.

**Table 4. Feedback-driven policy adaptation on LoTTE 100k.**

| Feedback mode | $\mathrm{Hit@10}$ | Token ratio | Dense rate | LinUCB rate | Selected-cluster hit | Last true reward |
|---|---:|---:|---:|---:|---:|---:|
| Equal noisy feedback | 0.8641 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | 0.8641 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | 0.8775 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Oracle feedback | 0.8758 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

Under default noisy feedback, trust weighting improves selected-cluster hit
from $0.5979$ to $0.7223$ and last true reward from $0.7517$ to $0.8328$
relative to equal noisy feedback. Under mild trust-weighted noise,
selected-cluster hit reaches $0.7908$, last true reward reaches $0.8820$,
dense rate falls to $0.5826$, and final context token ratio falls to
$0.9255\times$.
Figure 5 visualizes the same policy-field effect: feedback quality changes the
learned route signal before it becomes visible as a final fused-ranking gain.

Feedback also provides a recovery path for tail queries harmed by aggressive
context budgets. A query is affected when dense top-10 retrieves at least one
GT evidence chunk but the budgeted IntentRoute context misses. Same-query
retry is a post-feedback repair setting, not a first-pass IID ranking claim.

**Table 5. Conservative post-feedback recovery on affected LoTTE 100k queries.**

| Domain | Affected queries | Recovered | Recovery rate | Avg token saving vs dense |
|---|---:|---:|---:|---:|
| science/search 100k | 34 | 14 | 41.18% | 5.76% |
| technology/search 100k | 42 | 9 | 21.43% | 11.75% |
| pooled | 76 | 23 | 30.26% | - |

The pooled conservative retry recovery rate is approximately 30%, with an
approximate Wilson interval around 21-41%. This supports a practical recovery
claim: budget-induced failures are not always permanent, and feedback can
repair a meaningful fraction of them. A stricter calibration-to-test variant
has only small, domain-dependent effects, so feedback should be framed as a
controlled fallback trigger rather than as unconditional global reranking.

## 5.5 Geometry Diagnostics

The geometry scale diagnostic validates whether LoTTE retains usable local
geometry as scale grows.

**Table 6. LoTTE geometry diagnostics across domain and corpus scale.**

| Domain/scale | $\mathrm{PCAdim90}$ sample | $\mathrm{PCAvar@64}$ sample | $\mathrm{NearestClusterHit@3}$ | $\mathrm{ContextRetention@10}$ | Associated hit delta |
|---|---:|---:|---:|---:|---:|
| technology/search 100k | 182 | 0.6437 | 0.8870 | 0.9033 | -0.22 pp |
| technology/search 200k | 186 | 0.6292 | 0.8697 | 0.8947 | +2.80 pp |
| technology/search 400k | 190 | 0.6110 | 0.9016 | 0.8826 | +1.01 pp |
| technology/search 638k | 196 | 0.5867 | 0.9016 | 0.8571 | +1.85 pp |
| science/search 20k/q200 | 180 | 0.6377 | 0.9083 | 0.8939 | +3.17 pp |
| science/search 100k | 177 | 0.6459 | 0.8574 | 0.8628 | +1.51 pp |

$\mathrm{NearestClusterHit@3}$ remains high across both LoTTE domains,
suggesting local geometry is useful for routing. On technology/search,
$\mathrm{PCAdim90}$ increases and $\mathrm{PCAvar@64}$ decreases with scale,
suggesting the representation geometry becomes more complex. Science/search
also shows high local routing signal, but the 100k row has lower cluster-hit
and context-retention diagnostics than the 20k/q200 slice, matching the
observed need for domain-specific compression calibration. Context retention
declines with scale, showing that geometry alone should not replace dense
retrieval.

These diagnostics support the piecewise relevance-manifold framing as a useful
motivation and diagnostic, not as a theorem. Figure 3 visualizes the same trend.
Figure 4 further connects the geometry diagnostics to the observed
quality-cost frontier. The relationship is informative but not deterministic,
which is why IntentRoute treats geometry as a routing signal rather than as a
standalone retrieval rule.

The geometry-versus-random control makes this boundary explicit. Static nearest
geometry obtains route reward $0.8563$ and selected-cluster hit $0.8870$,
compared with $0.1499$ and $0.1577$ under uniform random arm selection. Yet
their final fused top-10 hit rates are both high ($0.8764$ and $0.8842$)
because dense and BM25 rescue remain active. Geometry is therefore validated at
the route-control layer; final fused hit alone cannot prove its contribution.

Arm-count sensitivity leads to the same mechanism-level conclusion. Across
$K \in \{8,16,32,64,128\}$, static route reward remains $0.8272$-$0.9128$ and
full multi-route hit remains $0.8775$-$0.8837$. Gated dense-saving behavior is
more sensitive: small $K$ permits aggressive dense reduction, while large $K$
spreads feedback across more arms and increases fallback. The fixed $K=32$
setting is a reproducible engineering point, not a geometrically optimal value.

## 5.6 Boundary, Robustness, and Downstream Checks

Secondary datasets and checks are used to bound the claim rather than expand it
into universal dense-retrieval dominance.

PubMedQA and Banking77 support the feedback-adaptation mechanism near quality
ceilings. PubMedQA is an evidence-retrieval proof-of-concept with section-level
ground truth, while Banking77 is better understood as an intent-routing proxy.
eManual and CUAD are limitation cases: eManual has heavy duplicate evidence
text and strict chunk-id labels, while CUAD remains a sparse GT-anchored smoke
case.

Matched-backbone evaluation extends the quality-cost pattern beyond MiniLM.

**Table 7. Matched-backbone frozen-test operating points at LoTTE
technology/search 100k.**

| Backbone and policy | Dense $\mathrm{Hit@10}$ | Method $\mathrm{Hit@10}$ | Hit delta | Token saving |
|---|---:|---:|---:|---:|
| MiniLM calibrated | 0.8705 | 0.8705 | +0.00 pp | 6.18% |
| BGE full multi-route | 0.8993 | 0.8985 | -0.08 pp | 11.99% |
| E5 full multi-route | 0.8753 | 0.8689 | -0.64 pp | 12.20% |
| BGE quality-first | 0.8993 | 0.9081 | +0.88 pp | 7.23% |

The BGE and E5 full multi-route rows are near their own dense baselines while
saving about 12% final context tokens. The BGE quality-first policy moves the
same frontier toward higher hit at lower saving, demonstrating tunability rather
than one fixed operating point. The corresponding E5 scan does not find an
above-dense token-saving point, so the positive-hit claim is BGE-specific. The
older QA-tuned MiniLM-family check remains in the appendix as supporting
evidence, not the main backbone-generalization result.

## 5.7 Strong Post-Retrieval Baselines

The post-retrieval baselines clarify what IntentRoute should and should not
claim. Dense+Sentence-MMR starts from dense top-10 chunks and selects
query-relevant, diverse sentence units under the same per-query final-context
token budgets used by IntentRoute. On LoTTE technology/search 100k, it
preserves dense chunk-support $\mathrm{Hit@10}=0.8705$ while reducing selected
sentence tokens by 11.4-13.1%. This is a strong final-context compression
baseline and means IntentRoute should not be framed as the only path to lower
generator input tokens.

The compressor-normalized comparison applies the same SentMMR layer to both
dense and IntentRoute evidence pools. Dense+SentMMR preserves dense
$\mathrm{Hit@10}$ at 0.95, 0.90, and 0.85 token ratios while saving roughly
5.3%, 10.2%, and 15.2% tokens. IntentRoute+SentMMR preserves each source
IntentRoute policy's chunk-support result and reaches larger total savings,
roughly 10.1-21.2% relative to dense, because it starts from a smaller evidence
pool. This supports a component view: SentMMR is a shared final-context
compressor, while IntentRoute is the upstream route-and-budget controller.

SelectiveContext-lite provides a second downstream prompt-pruning control.
Applied to dense top-10, it preserves chunk-support $\mathrm{Hit@10}=0.8705$
while saving 5.66%, 10.42%, 15.31%, and 25.19% tokens at ratios 0.95, 0.90,
0.85, and 0.75. Applied to IntentRoute evidence pools, it preserves each
source pool's hit result and adds the requested compression, reaching up to
30.57% total saving versus dense. This proxy is not LLMLingua; it demonstrates
that prompt pruning is complementary to upstream route-and-budget control.

The cross-encoder reranker baseline tests a different challenge. Reranking
dense top-50 candidates with `cross-encoder/ms-marco-MiniLM-L-6-v2` improves
full top-10 support metrics from dense $\mathrm{Hit@10}=0.8705$ and
$\mathrm{EvidenceRecall@10}=0.7081$ to $\mathrm{Hit@10}=0.8777$ and
$\mathrm{EvidenceRecall@10}=0.7332$. However, the reranked top-10 contains
longer chunks and increases final context tokens by about 21.9% relative to
dense top-10. When constrained under the same calibrated per-query budgets as
IntentRoute, the reranker same-budget variants reach
$\mathrm{Hit@10}=0.8633$-$0.8729$, which does not uniformly dominate the
IntentRoute target policies at $0.8657$-$0.8777$.

Together, these baselines narrow and strengthen the paper claim. IntentRoute
is not a replacement for sentence compression or cross-encoder reranking. It is
a low-compute controller that decides which evidence pool and budget should be
trusted before optional late-stage compression or reranking layers are applied.

## 5.8 Downstream Answer-Level Evaluation

The frozen downstream evaluation contains 300 queries, seven retrieval/context
methods, 2,100 generated answers, and 2,100 valid judgments. The matched
comparisons use the same query set and report paired uncertainty.

**Table 8. Matched downstream answer-quality and context-token comparisons.**

| Comparison | Baseline correct | IntentRoute correct | Correct delta (95% CI) | Token saving (95% CI) |
|---|---:|---:|---:|---:|
| BGE IntentRoute vs BGE dense | 0.9167 | 0.9167 | +0.00 pp [-2.67, +2.67] | 6.00% [4.01%, 7.97%] |
| E5 IntentRoute vs E5 dense | 0.9167 | 0.9200 | +0.33 pp [-3.00, +3.67] | 12.04% [9.93%, 14.16%] |
| IW+MMR vs Dense+MMR | 0.8900 | 0.9133 | +2.33 pp [-1.67, +6.33] | 6.65% [4.28%, 8.97%] |

All three context-saving intervals are positive, while every correctness-delta
interval includes zero and exact McNemar tests are non-significant. The result
supports judged correctness preservation with lower context, not a significant
answer-quality improvement. Faithfulness deltas are also non-significant; the
BGE point estimate is -2.33 percentage points and is retained as uncertainty
rather than hidden. Because only one generator/judge model is used, the table
is downstream support for the controller claim rather than a human-evaluation
or cross-model superiority result.
