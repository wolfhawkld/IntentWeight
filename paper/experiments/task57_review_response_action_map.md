# Task57 Review Response Action Map

Updated: 2026-06-24

## Objective

Convert the 2026-06-24 Hermes/GLM review into an executable experiment and
writing plan. This task saves the next-task roadmap and records which review
comments should be accepted, which are already answered by existing evidence,
and which should be reframed without weakening the core contribution.

This task does not add new experiment results. It is a planning and claim
control document for Task58 onward.

## Non-Negotiable Claim Frame

The paper should not be downgraded into "ordinary context compression." The
defensible contribution is a three-part control mechanism:

1. **Geometry / local structure** defines structured retrieval routes and
   motivates why cluster-local evidence can be informative.
2. **Feedback-updated LinUCB** turns static geometry and route features into an
   adaptive route-confidence signal, learning when local evidence is reliable
   and when dense fallback remains necessary.
3. **Confidence-based budget control** converts reliable route decisions into
   lower final evidence-context cost.

Recommended one-sentence framing:

> IntentRoute uses local geometry to define structured retrieval routes,
> feedback-updated LinUCB to estimate when those routes are reliable, and
> confidence-based budget control to convert reliable route decisions into
> lower final context cost.

This preserves the manifold/geometry and feedback/LinUCB contributions while
making the token-saving mechanism explicit.

## Fixed Seed Policy

Do not expand beyond the fixed seeds `13,17,19` for the current experiment
cycle. The attempted expansion beyond these seeds was too slow and did not
finish reliably on the local CPU-heavy workflow.

Statistical support should instead use:

- query-level paired bootstrap confidence intervals;
- McNemar-style paired hit tests;
- fixed-seed stability summaries;
- cross-backbone, cross-domain, cross-ablation consistency;
- calibration/test split discipline.

The paper should state that seed-level results are stability diagnostics, not
seed search or large-sample random-effects proof.

Runtime note from a low-cost check on 2026-06-24:

- BGE, 20 queries / 2k corpus, cached local artifacts: external elapsed times
  were `7.77s`, `8.92s`, `10.94s`, and `9.84s` for 1, 3, 5, and 7 seeds. This
  tiny slice is dominated by fixed loading/cache effects and is too noisy for a
  full-run extrapolation.
- BGE, 100 queries / 2k corpus, was stopped after more than 90 seconds before
  producing a result, because CPU-side model/query encoding and cache
  construction dominated the run.
- MiniLM, 100 queries / 2k corpus with cache hits, showed the cleaner seed-loop
  trend: `6.11s` for 1 seed, `8.22s` for 3 seeds, and `13.32s` for 5 seeds.

Conclusion: seed-loop cost does increase with seed count, but the larger
practical blocker for the strong-backbone runs is the combination of BGE CPU
encoding/cache construction and repeated artifact work. The project should keep
the fixed three seeds and spend additional compute on cross-condition
ablations, not seed expansion.

## Review Comment Assessment

| Review comment | Assessment | Response / action |
| --- | --- | --- |
| Novelty is unclear because manifold, LinUCB, and budget control each look incremental. | Accept. This is the main writing risk. | Reframe novelty around the integrated route-confidence-to-budget controller. Keep geometry and LinUCB as necessary control signals, not standalone theoretical claims. |
| Manifold should be removed because diagnostics are only PCA/KMeans. | Partially reject. The risk is real, but removal is unnecessary. | Keep bounded "manifold-inspired" or "local relevance structure" language. Add random/shuffled-geometry controls and geometry-to-control analysis to show the diagnostic is useful. |
| Random-cluster / shuffled-cluster control is missing. | Accept as high-value. | Task58 will run budget-matched random/shuffled geometry ablations under fixed seeds. Existing Task24 uniform-random evidence is useful but not enough for the current final-context-budget claim. |
| No-LinUCB / static control is missing. | Partially accept. Existing Task24/33.3 already show static and no-feedback controls, but not in the cleanest same-budget framing. | Task59 will compare learned LinUCB confidence with static-nearest, no-feedback, and random-control confidence under matched budget policies. |
| LinUCB contributes zero because static/random final Hit@10 can match full LinUCB. | Reject as overgeneralized. | Final Hit@10 is masked by dense/BM25 rescue paths. The correct LinUCB contribution is route confidence, selected-cluster quality, dense fallback behavior, and feedback-adaptive budget decisions. Task59 should make this explicit. |
| Feedback loop is circular because GT is used for reward and evaluation. | Accept as a limitation; do not overstate. | Keep "simulated feedback" and "controlled feedback adaptation" wording. Avoid "real user feedback" and strong "self-evolving" claims unless marked as simulated. |
| Downstream RAG evaluation is too small. | Accept for journal-strength evidence. | Task63 will expand the LLM answer evaluation. Main claim remains retrieval-backed answer support and context cost until this is complete. |
| Dataset diversity is limited to LoTTE family. | Accept as scope boundary. | Keep LoTTE as main benchmark. Task65 can add one non-LoTTE evidence retrieval dataset if time permits, but do not make universal domain claims. |
| LLMLingua / Selective Context baseline is missing. | Accept as a baseline risk. | Task62 will add at least one prompt-compression baseline on the 100k frozen split, positioned as complementary to retrieval-aware budget control. |
| More seeds are needed. | Modify. More seeds are not practical locally. | Use fixed seeds `13,17,19`; strengthen evidence through query-level paired tests and cross-condition consistency instead. |
| Arm count sensitivity is missing. | Accept with scoped execution. | Task60 will test a small cluster-count grid, prioritized on 100k. Larger scales are optional only if runtime is acceptable. |
| Geometry-to-gain regression would strengthen the manifold story. | Accept as diagnostic, not proof. | Task61 will analyze whether geometry metrics explain route-confidence and budget outcomes; avoid theorem-level claims from small sample sizes. |
| Results section is overloaded. | Accept. | Task64/65 will merge results into fewer claim-driven sections and move detailed rows to appendix. |

## Saved Task Roadmap

### Task58: Random/Shuffled Geometry Ablation

Goal: test whether the local geometry signal matters under the same final
context-budget evaluation frame.

Planned comparisons:

- normal geometry route confidence;
- random cluster-arm selection;
- shuffled cluster labels or randomized geometry control if implementation is
  tractable;
- same dense/BM25 rescue surface where possible;
- same Task38 frozen split and fixed seeds `13,17,19`.

Primary metrics:

- Hit@10 delta vs dense;
- final context token saving;
- selected-cluster hit;
- dense fallback rate;
- confidence distribution;
- calibration eligibility;
- paired query-level tests.

Expected paper use:

> Geometry is not claimed to replace dense retrieval. The ablation should show
> whether geometry provides useful route-control signal beyond random
> partitioning, especially in arm-quality and confidence/budget behavior.

### Task59: Static / No-LinUCB Feedback-Control Ablation

Goal: isolate what LinUCB and feedback adaptation add beyond static geometry
and static fusion.

Planned comparisons:

- learned LinUCB confidence + budget control;
- static nearest confidence + same budget search;
- no-feedback fallback/static fusion + same budget search;
- uniform random routing + same budget search;
- optional epsilon-greedy route control.

Primary metrics:

- final Hit@10 and token saving;
- selected-cluster hit;
- route confidence;
- dense fallback rate;
- compact-context rate;
- feedback recovery behavior where available.

Expected paper use:

> LinUCB should be written as a feedback-adaptive confidence/control mechanism,
> not as the sole source of fused-ranking Hit@10 gains.

### Task60: Arm Count Sensitivity

Goal: explain and stress-test the fixed `n_clusters=32` design choice.

Planned grid:

- `K in {8,16,32,64,128}` on LoTTE technology/search 100k;
- fixed seeds `13,17,19`;
- run only the minimum routing modes needed to compare quality-cost behavior;
- larger-scale follow-up only if runtime stays acceptable.

Primary metrics:

- Hit@10 and token saving;
- selected-cluster hit;
- context retention;
- dense fallback rate;
- elapsed runtime.

Expected paper use:

> KMeans is an engineering choice for fixed LinUCB arms and reproducibility.
> Sensitivity should show whether the controller is robust to reasonable arm
> counts, not that 32 is theoretically optimal.

### Task61: Geometry-To-Control / Geometry-To-Gain Analysis

Goal: connect geometry diagnostics to route-control outcomes without claiming a
manifold theorem.

Inputs:

- Task30 technology/search geometry;
- Task43 science/search geometry;
- Task58 random/shuffled geometry controls;
- Task60 arm-count sensitivity;
- existing Figure 4 geometry-to-gain data.

Analyses:

- correlations between geometry metrics and token saving / Hit delta;
- correlations between geometry metrics and selected-cluster hit / fallback;
- simple regressions only when sample size is adequate;
- explicit caveat for small-N diagnostics.

Expected paper use:

> Geometry diagnostics are explanatory and design-guiding signals; they are not
> mathematical proof that a smooth manifold model governs retrieval.

### Task62: Prompt-Compression Baseline

Goal: address LLMLingua / Selective Context baseline risk.

Preferred scope:

- LoTTE technology/search 100k frozen split;
- dense top-10 + prompt compression baseline;
- optionally IntentRoute evidence pool + same compressor;
- compare to SentMMR and Task48 compressor-normalized results.

Primary metrics:

- chunk-support Hit@10 preservation;
- evidence/citation support where measurable;
- final context token saving;
- runtime/cost notes.

Expected paper use:

> Prompt compression is a downstream context layer. IntentRoute operates
> upstream as a retrieval-aware route-and-budget controller and can be composed
> with compression.

### Task63: Expanded Downstream LLM Evaluation

Status: complete. The frozen 300-query run contains 2,100 generated answers and
2,100 valid judge records across seven methods. Matched comparisons preserve
judged correctness while reducing context tokens by 6.00% for BGE, 12.04% for
E5, and 6.65% for the SentMMR composition; correctness-delta confidence
intervals include zero and must not be framed as significant quality gains.

Goal: strengthen the RAG-facing sanity check beyond the current 60-query smoke
test.

Preferred scope:

- at least 300 frozen-test queries if quota allows;
- compare dense, BGE dense, BGE positive IntentRoute, Dense+SentMMR, and
  IntentRoute+SentMMR;
- use at least two judges or one judge plus strict citation-support checks if
  quota is limited.

Primary metrics:

- answer correctness;
- faithfulness;
- citation support;
- insufficient-context rate;
- context tokens;
- cost per correct answer.

Expected paper use:

> Use as downstream support only after completion. Until then, keep main claims
> tied to retrieval-backed answer support and context-token cost.

### Task64: Manuscript Claim Reframe

Status: complete. The title, abstract, contributions, method, setup, results,
discussion, limitations, conclusion, and appendix now center
route-confidence-to-budget control. Geometry/manifold remains motivation and
diagnostic support; trust-weighted LinUCB/feedback remains adaptive confidence
and recovery; dense remains the recall floor. Task53-63 evidence is integrated
with matched-backbone and downstream statistical boundaries.

Goal: update the full draft to reflect Task53-63 and the refined novelty
center.

Required changes:

- move the main novelty center to route-confidence-to-budget control;
- keep manifold/geometry as motivation plus diagnostic support;
- keep LinUCB/feedback as adaptive confidence estimation and recovery;
- add BGE/E5 matched-backbone evidence;
- add BGE positive-hit tunability;
- preserve dense as recall floor;
- avoid seed expansion claims.

### Task65: Table And Figure Refresh

Goal: make the final evidence easy to read.

Likely displays:

- matched-backbone table;
- random/shuffled geometry ablation table;
- static/no-LinUCB feedback-control table;
- arm-count sensitivity table;
- geometry-to-control figure;
- downstream answer/cost table if Task63 completes.

### Task66: Elsevier / IP&M Conversion

Goal: prepare the submission form after the claim/evidence structure stabilizes.

Tasks:

- convert ACL-style LaTeX to `elsarticle`;
- anonymize;
- shorten main results;
- move detailed ablations to appendix;
- regenerate PDF and validation packet.

### Task67: Final Validation And Review Packet

Goal: produce the final pre-submission evidence and review package.

Checks:

- Task51 experiment audit;
- manuscript consistency audit;
- LaTeX compile;
- figure/table source consistency;
- claim wording audit;
- final response-to-review summary.

## Execution Order

Recommended order:

1. Task58 random/shuffled geometry ablation.
2. Task59 static/no-LinUCB feedback-control ablation.
3. Task60 arm count sensitivity.
4. Task61 geometry-to-control analysis.
5. Task62 prompt-compression baseline.
6. Task63 expanded downstream LLM evaluation.
7. Task64 manuscript claim reframe.
8. Task65 table/figure refresh.
9. Task66 Elsevier/IP&M conversion.
10. Task67 final validation packet.

If runtime becomes a constraint, do not increase seed count. Reduce scale,
number of routing modes, or optional baselines first.

## Immediate Next Step

Start Task65 by refreshing the main tables and figures around the revised claim
structure, then reduce appendix/table density for the journal-facing layout.
