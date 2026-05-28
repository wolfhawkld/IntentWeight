# 5. Results

## 5.1 Main Token-Quality Frontier

Task29-C is the main token-efficiency result because it directly measures final
retrieved context tokens. It is selected as the conservative end of the
Task29-A/B/C token-quality frontier. Task29-A and Task29-B show that more
aggressive context reduction is possible at a visible $\mathrm{Hit@10}$ cost,
while Task29-C prioritizes quality preservation over maximum token saving.

| Scale | Corpus | Dense $\mathrm{Hit@10}$ | Task29-C $\mathrm{Hit@10}$ | Hit delta | Dense $\mathrm{Tokens@10}$ | Task29-C $\mathrm{Tokens@10}$ | Token saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE 100k | 101311 | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| LoTTE 200k | 201010 | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| LoTTE 400k | 400674 | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| LoTTE 638k | 638509 | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

The 100k result is near dense, with a small $\mathrm{Hit@10}$ drop. At 200k,
400k, and 638k, Task29-C has mean $\mathrm{Hit@10}$ above dense while using
fewer final context tokens. The result should be framed as conservative final
context compaction, not as aggressive dense replacement.

## 5.2 Seed Stability

Task29.3 reports three-seed stability diagnostics for Task29-C. With only three
seeds, these intervals should be presented as engineering stability diagnostics,
not as strong statistical significance proof.

| Scale | Task29-C $\mathrm{Hit@10}$ mean | $\mathrm{Hit@10}$ 95% CI | Token saving mean | Token saving 95% CI |
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

Task33.6 extends the LoTTE 100k Task29-C setting from three to five seeds. The
five-seed mean is $\mathrm{Hit@10}=0.8708$ versus dense $0.8674$, with final
context token ratio $0.9507\times$. The Hit delta confidence interval overlaps
zero, so this strengthens stability but does not justify a
statistical-superiority claim at 100k.

## 5.3 Component Ablation

Task33.3 converts the LoTTE 100k evidence into a paper-facing ablation table.
The table clarifies which components provide the quality floor, routing signal,
feedback adaptation, and final token saving.

| Component | Role | $\mathrm{Hit@10}$ | $\mathrm{EvidenceRecall@10}$ | $\mathrm{Tokens@10}$ | Token ratio | Dense rate | LinUCB rate | Cluster hit | Last reward |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense-only | Quality floor | 0.8674 | 0.7026 | 1472.39 | 1.0000 | - | - | - | - |
| BM25-only | Lexical baseline | 0.7232 | 0.5240 | 1745.12 | 1.1852 | - | - | - | - |
| Dense+BM25 hybrid | Static fusion | 0.8624 | 0.6848 | 1705.46 | 1.1583 | - | - | - | - |
| No feedback gated | Dense/full fallback control | 0.8826 | 0.7246 | 1561.15 | 1.0603 | 1.0000 | 0.0000 | 0.1553 | 0.1516 |
| Equal noisy feedback | No trust weighting | 0.8641 | 0.6604 | 1423.84 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | Default trust scoring | 0.8641 | 0.6661 | 1399.51 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | Best controlled-noise point | 0.8775 | 0.6795 | 1362.68 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Task29-C final policy | Main conservative policy | 0.8652 | 0.6737 | 1401.24 | 0.9517 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
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

Under default noisy feedback, trust weighting improves selected-cluster hit from
$0.5979$ to $0.7223$ and last true reward from $0.7517$ to $0.8328$ relative to
equal noisy feedback. Under mild trust-weighted noise, selected-cluster hit
reaches $0.7908$, last true reward reaches $0.8820$, dense rate falls to
$0.5826$, and final context token ratio falls to $0.9255\times$.

This supports the feedback self-evolution claim in a bounded form: controlled
trust-weighted simulated feedback improves the route-policy value field. It
does not prove that real human feedback has already been solved.

## 5.5 Geometry Diagnostics

Task30 validates whether LoTTE retains usable local geometry as scale grows.

| Scale | $\mathrm{PCAdim90}$ sample | $\mathrm{PCAvar@64}$ sample | $\mathrm{NearestClusterHit@3}$ | $\mathrm{ContextRetention@10}$ | Task29 Hit delta |
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

## 5.6 Encoder Robustness

Task33.1a tests whether the result depends on the exact `all-MiniLM-L6-v2`
encoder. With `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA-tuned
MiniLM-family encoder, the dense baseline becomes stronger on LoTTE 100k:
$\mathrm{Hit@10}$ increases to $0.8809$. IntentWeight Task29-C still reaches
mean $\mathrm{Hit@10}=0.8853$ and reduces final context tokens by $3.35\%$.

This reduces the single-encoder risk but does not eliminate it. The result
shows same-resource-class robustness within a MiniLM family; it does not prove
the claim for all stronger encoders, rerankers, or late-interaction models.

## 5.7 Downstream Generation Smoke

Task33.5 adds a small downstream sanity check. It compares dense top-10 context
with Task29-C compressed context on 60 sampled LoTTE 100k queries using
`deepseek-v4-flash` with thinking enabled.

| Method | Answer score | Faithfulness | Answer relevance | Win count | Context token proxy ratio |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 4.4000 | 4.6500 | 4.6500 | 14 | 1.0000 |
| Task29-C | 4.2833 | 4.6333 | 4.4500 | 14 | 0.9321 |
| Tie | - | - | - | 32 | - |

The smoke does not show obvious answer-quality degradation from Task29-C context
compaction. Dense has a small average-score and relevance edge, so this should
not be overclaimed as Task29-C beating dense in generated answer quality. It is
a sanity check, not a replacement for the retrieval and final-context-token
experiments.

## 5.8 Limitation Cases

eManual contains heavy duplicate evidence text and strict chunk-id labels. Task
14.5 shows that strict chunk-id recall can mark text-equivalent retrieved
evidence as wrong. The dataset is useful as a limitation case: geometry may be
usable, but the current learned route and strict labels understate retrieval
success.

CUAD remains a sparse smoke/stress case. Current experiments use GT-anchored
sampling rather than full-corpus comparable evaluation. CUAD should not be used
as main positive evidence.
