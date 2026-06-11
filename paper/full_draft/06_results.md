# 5. Results

## 5.1 Main Token-Quality Frontier

The conservative confidence-based context policy is the main token-efficiency
result because it directly measures final retrieved context tokens. It is
selected as the conservative end of the context-compaction policy frontier.
More aggressive policies show that stronger context reduction is possible at a
visible $\mathrm{Hit@10}$ cost, while the conservative policy prioritizes
quality preservation over maximum token saving.

**Table 2. LoTTE token-quality frontier for the conservative context policy.**

| Scale | Corpus | Dense $\mathrm{Hit@10}$ | Conservative policy $\mathrm{Hit@10}$ | Hit delta | Dense $\mathrm{Tokens@10}$ | Conservative policy $\mathrm{Tokens@10}$ | Token saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE 100k | 101311 | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| LoTTE 200k | 201010 | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| LoTTE 400k | 400674 | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| LoTTE 638k | 638509 | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

The 100k result is near dense, with a small $\mathrm{Hit@10}$ drop. At 200k,
400k, and 638k, the conservative policy has mean $\mathrm{Hit@10}$ above dense
while using fewer final context tokens. The result should be framed as
conservative final context compaction, not as aggressive dense replacement.
Figure 2 visualizes the same result as a token-quality frontier across corpus
scale.

## 5.2 Seed Stability

The multi-seed stability analysis reports three-seed diagnostics for the
conservative policy. With only three seeds, these intervals should be presented
as engineering stability diagnostics, not as strong statistical significance
proof.

The 400k token-saving interval is wider than the other scales. We interpret
this as seed-level variance in route confidence and context-budget control, not
as a contradiction of the overall direction. CI-level confirmation of
$\mathrm{Hit@10}$ improvement is strongest at 200k. The 400k and 638k rows
should be reported as mean above-dense results with limited seed counts.

An additional five-seed robustness check extends the LoTTE 100k conservative
policy setting. The five-seed mean is $\mathrm{Hit@10}=0.8708$ versus dense
$0.8674$, with final context token ratio $0.9507\times$. The Hit delta
confidence interval overlaps zero, so this strengthens stability but does not
justify a statistical-superiority claim at 100k.

Appendix A reports the complete three-seed confidence-interval tables and the
five-seed LoTTE 100k extension.

## 5.3 Calibration/Test Context-Budget Validation

To reduce test-set model-selection bias, we also evaluate a calibration/test
context-budget protocol. The budget policy is selected only on calibration
queries and then frozen before evaluation on the test split. Token saving is
measured as final LLM evidence-context input tokens relative to dense top-10.

**Table 3. Calibration/test context-budget validation on LoTTE technology/search.**

| Scale | Selected policy | Hit delta vs dense | Token saving vs dense | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

The calibrated IntentWeight policies save 6-18% final evidence-context tokens
under frozen policy selection. Dense-only adaptive truncation usually saves
more tokens, but it loses $\mathrm{Hit@10}$ on every scale. This indicates that
IntentWeight is not merely truncating dense top-k lists; route confidence helps
decide where a shorter context is safer. Strict seed-level non-inferiority
remains scale-dependent and should not be overclaimed.

## 5.4 Cross-Domain Validation

We replicate the validation pattern on LoTTE science/search to test whether the
effect is limited to technology/search.

**Table 4. Cross-domain validation on LoTTE science/search.**

| Domain/scale | Dense $\mathrm{Hit@10}$ | IntentWeight fixed top-10 $\mathrm{Hit@10}$ | Hit delta | Budgeted token saving |
|---|---:|---:|---:|---:|
| science/search 20k/q200 | 0.8950 | 0.9267 | +3.17 pp | 13.18-14.31% |
| science/search 100k | 0.8926 | 0.9077 | +1.51 pp | 17.53-20.53% |

The fixed top-10 ranking-side effect transfers to a second LoTTE domain. The
context-budget result is more nuanced. At 20k/q200, the frozen budgeted
policies keep above-dense $\mathrm{Hit@10}$ while saving roughly 13-14%
context tokens. At 100k, the same aggressive budget saves roughly 17-21%
tokens but can introduce small $\mathrm{Hit@10}$ drops. This should be written
as cross-domain support for adaptive ranking and as a boundary on compression:
budget strength must be calibrated per domain and scale.

## 5.5 Component Ablation

The component ablation table summarizes which parts of the system provide the
quality floor, routing signal, feedback adaptation, and final token saving on
LoTTE 100k.

**Table 5. LoTTE 100k component ablation.**

| Component | Role | $\mathrm{Hit@10}$ | $\mathrm{EvidenceRecall@10}$ | $\mathrm{Tokens@10}$ | Token ratio | Dense rate | LinUCB rate | Cluster hit | Last reward |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense-only | Quality floor | 0.8674 | 0.7026 | 1472.39 | 1.0000 | - | - | - | - |
| BM25-only | Lexical baseline | 0.7232 | 0.5240 | 1745.12 | 1.1852 | - | - | - | - |
| Dense+BM25 hybrid | Static fusion | 0.8624 | 0.6848 | 1705.46 | 1.1583 | - | - | - | - |
| No feedback gated | Dense/full fallback control | 0.8826 | 0.7246 | 1561.15 | 1.0603 | 1.0000 | 0.0000 | 0.1553 | 0.1516 |
| Equal noisy feedback | No trust weighting | 0.8641 | 0.6604 | 1423.84 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | Default trust scoring | 0.8641 | 0.6661 | 1399.51 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | Best controlled-noise point | 0.8775 | 0.6795 | 1362.68 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Conservative final policy | Main conservative policy | 0.8652 | 0.6737 | 1401.24 | 0.9517 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Oracle feedback | Upper bound | 0.8758 | 0.6768 | 1327.03 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

Dense-only remains the quality floor. BM25-only is weaker as a standalone
retriever, and static dense+BM25 hybrid is near dense but uses more final
context tokens. No-feedback gated routing has high $\mathrm{Hit@10}$ because it
falls back to full dense/multi-route retrieval; it does not learn efficient
route control.
Trust-weighted feedback improves policy internals relative to equal noisy
feedback, especially selected-cluster hit and last true reward. The oracle row
shows the upper bound under clean feedback.

## 5.6 Feedback-Driven Policy Adaptation

The feedback experiments show that final $\mathrm{Hit@10}$ can be saturated by
dense and BM25 rescue routes, making feedback gains less visible in the fused
final ranking. The strongest evidence for LinUCB self-evolution is therefore in
route-policy metrics rather than only final $\mathrm{Hit@10}$.

**Table 6. Feedback-driven policy adaptation summary on LoTTE 100k.**

| Feedback mode | $\mathrm{Hit@10}$ | Token ratio | Dense rate | LinUCB rate | Selected-cluster hit | Last true reward |
|---|---:|---:|---:|---:|---:|---:|
| Equal noisy feedback | 0.8641 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | 0.8641 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | 0.8775 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Oracle feedback | 0.8758 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

Under default noisy feedback, trust weighting improves selected-cluster hit from
$0.5979$ to $0.7223$ and last true reward from $0.7517$ to $0.8328$ relative to
equal noisy feedback. Under mild trust-weighted noise, selected-cluster hit
reaches $0.7908$, last true reward reaches $0.8820$, dense rate falls to
$0.5826$, and final context token ratio falls to $0.9255\times$.

This supports the feedback self-evolution claim in a bounded form: controlled
trust-weighted simulated feedback improves the route-policy value field. It
does not prove that real human feedback has already been solved.

## 5.7 Feedback-Driven Hard-Case Recovery

We also test whether feedback can repair tail queries harmed by aggressive
final-context budgets. A query is affected when dense top-10 retrieves at least
one GT evidence chunk but the budgeted IntentWeight context misses. In
same-query retry, simulated feedback updates arm-level routing state and
triggers a safer retry policy. This is a post-feedback recovery experiment, not
a first-pass IID ranking claim.

**Table 7. Conservative post-feedback recovery on affected LoTTE 100k queries.**

| Domain | Affected queries | Recovered | Recovery rate | Avg token saving vs dense |
|---|---:|---:|---:|---:|
| science/search 100k | 34 | 14 | 41.18% | 5.76% |
| technology/search 100k | 42 | 9 | 21.43% | 11.75% |
| pooled | 76 | 23 | 30.26% | - |

The pooled conservative retry recovery rate is approximately 30%, with an
approximate Wilson interval around 21-41%. This supports a practical recovery
claim: budget-induced failures are not always permanent, and feedback can
repair a meaningful fraction of them. A stricter calibration-to-test variant
shows only small, domain-dependent effects, so the paper should frame feedback
as a controlled fallback trigger rather than as unconditional global reranking.

## 5.8 Secondary Dataset Evidence

The main paper claim is evaluated on LoTTE because it provides the cleanest
large-scale vertical retrieval setting for token-quality analysis. Other
datasets are used as supporting evidence and boundary cases rather than as
equal main benchmarks.

PubMedQA and Banking77 support the feedback self-evolution mechanism. In both
cases, final retrieval quality is already close to ceiling, so the important
signal is not only final $\mathrm{Hit@10}$ but also last true reward and
selected-cluster hit. PubMedQA is an evidence-retrieval proof-of-concept with
section-level ground truth, while Banking77 is better understood as an
intent-routing proxy.

eManual and CUAD are useful because they prevent overclaiming. eManual has
18,812 corpus chunks but only 1,729 unique text strings; many ground-truth
references share duplicate text. Under strict chunk-id evaluation, dense
retrieval reaches only $\mathrm{Hit@10}=0.3231$, but text-equivalent dense
evaluation reaches $0.5615$, and the deduplicated corpus baseline reaches
$0.8615$. This indicates that strict IDs can mark semantically equivalent
retrievals as wrong. CUAD remains a sparse smoke case using a GT-anchored
sample, so it should be reported only as a stress/limitation result.

Appendix D reports the full secondary-dataset table and the eManual
duplicate-text diagnostic.

## 5.9 Geometry Diagnostics

The geometry scale diagnostic validates whether LoTTE retains usable local
geometry as scale grows.

**Table 8. LoTTE geometry diagnostics across corpus scale.**

| Scale | $\mathrm{PCAdim90}$ sample | $\mathrm{PCAvar@64}$ sample | $\mathrm{NearestClusterHit@3}$ | $\mathrm{ContextRetention@10}$ | Conservative policy hit delta |
|---|---:|---:|---:|---:|---:|
| 100k | 182 | 0.6437 | 0.8870 | 0.9033 | -0.22 pp |
| 200k | 186 | 0.6292 | 0.8697 | 0.8947 | +2.80 pp |
| 400k | 190 | 0.6110 | 0.9016 | 0.8826 | +1.01 pp |
| 638k | 196 | 0.5867 | 0.9016 | 0.8571 | +1.85 pp |

$\mathrm{NearestClusterHit@3}$ remains high, around 0.87-0.90, suggesting
local geometry is useful for routing. $\mathrm{PCAdim90}$ increases and
$\mathrm{PCAvar@64}$ decreases with scale, suggesting the representation
geometry becomes more complex. Context retention declines with scale, showing
that geometry alone should not replace dense retrieval.

These diagnostics support the piecewise relevance-manifold framing as a useful
motivation and diagnostic, not as a theorem.
Figure 3 visualizes the geometry trend: nearest-cluster hit remains high, while
context retention and PCA concentration decline as the corpus grows.

## 5.10 Encoder Robustness

The encoder robustness check tests whether the result depends on the exact
`all-MiniLM-L6-v2` encoder. With
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA-tuned MiniLM-family
encoder, the dense baseline becomes stronger on LoTTE 100k: $\mathrm{Hit@10}$
increases to $0.8809$. IntentWeight still reaches mean
$\mathrm{Hit@10}=0.8853$ under the conservative policy and reduces final
context tokens by $3.35\%$.

This reduces the single-encoder risk but does not eliminate it. The result
shows same-resource-class robustness within a MiniLM family; it does not prove
the claim for all stronger encoders, rerankers, or late-interaction models.
Appendix E reports the complete robustness table.

## 5.11 Downstream Answer-Quality Check

The downstream generation smoke test compares dense top-10 context with the
compressed conservative-policy context on 60 sampled LoTTE 100k queries using
`deepseek-v4-flash` with thinking enabled.

The smoke does not show obvious answer-quality degradation from conservative
context compaction. Dense has a small average-score and relevance edge, so this
should not be overclaimed as the conservative policy beating dense in generated
answer quality. It is a sanity check, not a replacement for the retrieval and
final-context-token experiments. Appendix F reports the full smoke table.
