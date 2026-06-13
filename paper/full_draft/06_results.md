# 5. Results

## 5.1 Main Calibrated Token-Quality Frontier

The main cost result uses a calibrated token-budget policy. For each corpus
scale, the budget is selected on calibration queries and then frozen before
test evaluation. The measured cost is final LLM evidence-context input tokens
relative to dense top-10, not retrieval-side candidate count.

**Table 1. Calibrated token-quality frontier on LoTTE technology/search.**

| Scale | Frozen budget policy | IntentWeight hit delta vs dense | IntentWeight token saving | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

The calibrated IntentWeight policies save 6-18% final evidence-context tokens
under frozen policy selection. Dense-only adaptive truncation usually saves
more tokens, but it loses $\mathrm{Hit@10}$ on every scale. This comparison
shows that the effect is not merely dense top-k truncation: route confidence
helps decide where a shorter context remains safe. Strict seed-level
non-inferiority remains scale-dependent, so the paper should claim a bounded
quality-cost frontier rather than universal statistical superiority.

The earlier conservative confidence-only policy remains useful as a stable
baseline. It reduces final retrieved context tokens by 4.7-5.3% across LoTTE
technology/search 100k-638k while preserving dense-level $\mathrm{Hit@10}$.
Appendix A reports the complete confidence-only scale table and seed stability
diagnostics.

## 5.2 Cross-Domain Validation

We replicate the validation pattern on LoTTE science/search to test whether the
effect is limited to technology/search.

**Table 2. Cross-domain validation on LoTTE science/search.**

| Domain/scale | Dense $\mathrm{Hit@10}$ | IntentWeight fixed top-10 $\mathrm{Hit@10}$ | Hit delta | Budgeted token saving |
|---|---:|---:|---:|---:|
| science/search 20k/q200 | 0.8950 | 0.9267 | +3.17 pp | 13.18-14.31% |
| science/search 100k | 0.8926 | 0.9077 | +1.51 pp | 17.53-20.53% |

The fixed top-10 ranking-side effect transfers to a second LoTTE domain. The
context-budget result is more nuanced. At 20k/q200, the frozen budgeted
policies keep above-dense $\mathrm{Hit@10}$ while saving roughly 13-14% context
tokens. At 100k, the same aggressive budget saves roughly 17-21% tokens but can
introduce small $\mathrm{Hit@10}$ drops. This supports adaptive ranking across
domains while showing that compression strength must be calibrated per domain
and scale.

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

Feedback also provides a recovery path for tail queries harmed by aggressive
context budgets. A query is affected when dense top-10 retrieves at least one
GT evidence chunk but the budgeted IntentWeight context misses. Same-query
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

**Table 6. LoTTE geometry diagnostics across corpus scale.**

| Scale | $\mathrm{PCAdim90}$ sample | $\mathrm{PCAvar@64}$ sample | $\mathrm{NearestClusterHit@3}$ | $\mathrm{ContextRetention@10}$ | Confidence-only hit delta |
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
motivation and diagnostic, not as a theorem. Figure 3 visualizes the same trend.

## 5.6 Boundary, Robustness, and Downstream Checks

Secondary datasets and checks are used to bound the claim rather than expand it
into universal dense-retrieval dominance.

PubMedQA and Banking77 support the feedback-adaptation mechanism near quality
ceilings. PubMedQA is an evidence-retrieval proof-of-concept with section-level
ground truth, while Banking77 is better understood as an intent-routing proxy.
eManual and CUAD are limitation cases: eManual has heavy duplicate evidence
text and strict chunk-id labels, while CUAD remains a sparse GT-anchored smoke
case.

The encoder robustness check uses
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`. Under this stronger
MiniLM-family encoder, the dense baseline improves to $\mathrm{Hit@10}=0.8809$,
and IntentWeight still reaches mean $\mathrm{Hit@10}=0.8853$ while reducing
final context tokens by 3.35%. The downstream answer-quality check compares 60
LoTTE 100k queries with dense top-10 and compressed context; it does not show
obvious answer-quality degradation, but it remains a small sanity check rather
than a full human evaluation. Appendix D-F report the full boundary,
robustness, and downstream tables.
