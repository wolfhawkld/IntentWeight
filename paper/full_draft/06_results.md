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

## 5.2 Seed Stability

This section is appendix-facing in a conference-length version. The main text
should summarize the direction and keep the detailed interval table in the
appendix unless space permits.

The multi-seed stability analysis reports three-seed diagnostics for the
conservative policy. With only three seeds, these intervals should be presented
as engineering stability diagnostics, not as strong statistical significance
proof.

**Appendix Table A1. Multi-seed stability diagnostics for the conservative
context policy.**

| Scale | Conservative policy $\mathrm{Hit@10}$ mean | $\mathrm{Hit@10}$ 95% CI | Token saving mean | Token saving 95% CI |
|---|---:|---:|---:|---:|
| 100k | 0.8652 | [0.8565, 0.8739] | 4.83% | [2.89%, 6.77%] |
| 200k | 0.8249 | [0.8052, 0.8446] | 4.69% | [3.89%, 5.48%] |
| 400k | 0.7819 | [0.7709, 0.7929] | 5.32% | [0.11%, 10.53%] |
| 638k | 0.7466 | [0.7246, 0.7687] | 4.86% | [4.24%, 5.48%] |

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

## 5.3 Component Ablation

The component ablation table summarizes which parts of the system provide the
quality floor, routing signal, feedback adaptation, and final token saving on
LoTTE 100k.

**Table 3. LoTTE 100k component ablation.**

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

## 5.4 Feedback Self-Evolution

The feedback experiments show that final $\mathrm{Hit@10}$ can be saturated by
dense and BM25 rescue routes, making feedback gains less visible in the fused
final ranking. The strongest evidence for LinUCB self-evolution is therefore in
route-policy metrics rather than only final $\mathrm{Hit@10}$.

**Table 4. Feedback self-evolution summary on LoTTE 100k.**

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

## 5.5 Secondary Dataset Evidence

The main paper claim is evaluated on LoTTE because it provides the cleanest
large-scale vertical retrieval setting for token-quality analysis. Other
datasets are used as supporting evidence and boundary cases rather than as
equal main benchmarks.

This section is appendix-facing in a conference-length version. A short main
text paragraph can summarize the secondary evidence and boundary cases, while
the full table can move to the appendix.

**Appendix Table D1. Secondary dataset evidence and boundary cases.**

| Dataset | Role | Dense/reference $\mathrm{Hit@10}$ | Supporting / diagnostic result | Paper interpretation |
|---|---|---|---|---|
| PubMedQA | Evidence retrieval proof-of-concept | 0.9930 | Trust-weighted $\mathrm{Hit@10}=0.9940$, last reward $0.8727$, selected-cluster hit $0.8860$ | Feedback improves policy internals near a dense ceiling; GT is abstract-level context. |
| Banking77 | Intent routing proxy | 0.9805 | Trust-weighted $\mathrm{Hit@10}=0.9844$, last reward $0.9805$, selected-cluster hit $0.9983$ | Strong intent-structure evidence; not an evidence-retrieval main benchmark. |
| eManual | Duplicate/weak-label limitation | 0.3231 strict; 0.5615 text-equivalent | Deduplicated dense $\mathrm{Hit@10}=0.8615$; nearest-centroid text-equivalent $\mathrm{Hit@10}=0.5462$ | Strict chunk IDs understate success because many evidence texts are duplicated. |
| CUAD | Sparse legal smoke/stress case | 0.0759 | Trust-weighted smoke $\mathrm{Hit@10}=0.0886$ | Too sparse and sampled to serve as positive main evidence. |

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

## 5.6 Geometry Diagnostics

The geometry scale diagnostic validates whether LoTTE retains usable local
geometry as scale grows.

**Table 5. LoTTE geometry diagnostics across corpus scale.**

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

## 5.7 Encoder Robustness

This section is appendix-facing in a conference-length version.

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

## 5.8 Downstream Generation Smoke

The downstream generation smoke test compares dense top-10 context with the
compressed conservative-policy context on 60 sampled LoTTE 100k queries using
`deepseek-v4-flash` with thinking enabled.

This section is appendix-facing unless the target venue explicitly values a
small generation sanity check in the main result section.

**Appendix Table F1. Downstream generation smoke test.**

| Method | Answer score | Faithfulness | Answer relevance | Win count | Context token proxy ratio |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 4.4000 | 4.6500 | 4.6500 | 14 | 1.0000 |
| Conservative policy | 4.2833 | 4.6333 | 4.4500 | 14 | 0.9321 |
| Tie | - | - | - | 32 | - |

The smoke does not show obvious answer-quality degradation from conservative
context compaction. Dense has a small average-score and relevance edge, so this
should not be overclaimed as the conservative policy beating dense in generated
answer quality. It is a sanity check, not a replacement for the retrieval and
final-context-token experiments.
