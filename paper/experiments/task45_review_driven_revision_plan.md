# Task45 Review-Driven Revision Plan

Updated: 2026-06-16

This plan records the revision priorities after reading the new `review_binqi`
comments:

- `review_binqi/04_updated_paper_review.md`
- `review_binqi/05_weakness_based_revision_suggestions.md`
- `review_binqi/06_detailed_experiment_section_plan.md`

The comments are broadly reasonable. They do not invalidate the current work;
they identify the remaining gaps between the current manuscript and a stronger
conference submission.

## Core Strategic Adjustment

The paper should not overclaim "manifold theory" or present LinUCB as a new
bandit algorithm. However, the main research chain should still be preserved:

> vertical/domain corpora exhibit local geometric structure; this motivates an
> adaptive multi-route retrieval policy; LinUCB and feedback learn when to trust
> compact local evidence versus fallback retrieval; the observable outcome is a
> quality-efficiency trade-off in final evidence context.

The role of each component should therefore be:

- piecewise local relevance structure: the design hypothesis and diagnostic
  support, not a fully proven mathematical theorem;
- LinUCB: the adaptive route-confidence learner that operationalizes the
  trade-off, not a new algorithmic contribution;
- feedback: the mechanism for online correction/recovery under controlled
  simulation, not proof of production RLHF;
- final-context budget control: the measurable operational endpoint where the
  quality-efficiency trade-off is evaluated.

The main novelty should be framed as:

> a manifold-inspired, feedback-adaptive evidence selection policy that learns
> a risk-calibrated trade-off between compact local retrieval and dense fallback.

This keeps the original research intent while aligning the claim with the
strongest current evidence: geometry diagnostics, feedback recovery/adaptation,
calibrated token-quality frontiers, and dense-only adaptive truncation
baselines.

Candidate title direction:

> IntentWeight: Feedback-Adaptive Evidence Selection under Local Structure for
> Efficient Retrieval-Augmented Reasoning

Alternative:

> IntentWeight: Manifold-Inspired Adaptive Retrieval with Risk-Calibrated
> Evidence Contexts

## Already Addressed by Task44

Task44 already responds to part of the review:

- adds Figure 4: geometry-to-gain diagnostic;
- adds Figure 5: feedback-driven route adaptation;
- improves table readability by removing hard table scaling and using
  full-width `tabularx`;
- splits the dense Table 3 ablation into quality/context-cost and route-policy
  panels;
- keeps the data audit and PDF audit passing.

These changes improve presentation quality, but they do not replace the need
for stronger baselines, stronger statistics, and clearer method details.

## Priority Plan

### P0-A: Reframe Title, Abstract, Introduction, and Contributions

Goal:

Reduce overclaim risk and align the manuscript with the strongest evidence.

Actions:

1. Keep the paper centered on the chain:
   local geometric structure -> adaptive route selection -> feedback correction
   -> quality-efficiency trade-off.
2. Avoid presenting manifold/local-structure diagnostics as a formal proof.
3. Present LinUCB as the mechanism that learns the route-confidence and fallback
   trade-off.
4. Present feedback as a recovery/risk-control mechanism, not as proof of real
   user-feedback deployment.
5. Use final-context-token reduction as the measurable efficiency endpoint, not
   as the whole research contribution.
6. Update abstract and conclusion to say the results are retrieval-level and
   final-context-token results; answer-level validation remains preliminary.

Expected outcome:

The claim remains faithful to the original research hypothesis while becoming
more defensible and less vulnerable to "component stacking" or over-theorized
manifold criticism.

### P0-B: Clean Up Calibration/Test Claims

Goal:

Avoid reviewer concerns around 400k `Calibration eligible=False` and
scale-dependent non-inferiority.

Actions:

1. Move strict main-result language to eligible operating points.
2. Treat the 400k calibrated-budget point as a diagnostic frontier point and
   explicitly mark it as pending follow-up unless its eligibility is
   re-established by a supplemental experiment.
3. Add or expose the non-inferiority margin used for calibration.
4. Explain `token_budget_r0.85_m4`, `r0.95_m4`, and related policy names.
5. Add a short note that strict non-inferiority is scale-dependent.

Expected outcome:

The main cost-quality claim becomes cleaner:

> IntentWeight exposes eligible operating points that reduce final
> evidence-context tokens while avoiding the larger Hit@10 losses observed
> under dense-only adaptive truncation.

### P0-C: Add Query-Level Paired Statistics

Goal:

Upgrade the current evidence from trend-level/seed-level diagnostics to
reviewer-facing paired evidence.

Actions:

1. Compute dense win / IntentWeight win / tie per scale.
2. Compute McNemar statistics for query-level Hit@10.
3. Compute paired bootstrap confidence intervals for:
   - Hit@10 delta;
   - EvidenceRecall@10 delta;
   - MRR@10 / nDCG@10 delta if available;
   - final context-token saving.
4. Report quality non-inferiority and token-cost superiority separately.

This can be done on the current device from existing ranking and paired-result
artifacts.

### P0-D: Add Method Reproducibility Details

Goal:

Make the method reproducible enough for an experimental systems/retrieval
paper.

Actions:

1. Add a feature-vector table:
   - query embedding/projection features;
   - dense confidence features;
   - BM25 confidence features;
   - route agreement features;
   - cluster geometry features;
   - semantic drift/fallback features;
   - budget-policy features.
2. Add a hyperparameter table:
   - number of arms;
   - LinUCB alpha;
   - reward/cost weights;
   - BM25/RRF parameters;
   - dense/BM25/cluster depths;
   - confidence thresholds;
   - final context budget candidates.
3. Add pseudocode for calibrated budget selection and inference-time fallback.
4. Explicitly define route confidence, semantic drift, and calibration
   eligibility.

### P0-E: Add Dense+Sentence-MMR Same-Budget Baseline

Goal:

Answer the most cost-effective strong-baseline criticism:

> Why not simply compress dense top-10 context?

Actions:

1. Take dense top-10 retrieved chunks.
2. Split chunks into sentence-like evidence units.
3. Rank or select sentences by query-sentence embedding similarity plus MMR
   diversity.
4. Match the final token budget used by IntentWeight.
5. Compare Hit@10/evidence support proxies and final context tokens.

This is the highest-priority new baseline because it directly challenges the
central final-context budget claim and is much cheaper than full reranker or
LLM-compression baselines.

### P1-A: Reranker Same-Budget Baseline

Goal:

Address the standard strong-retrieval baseline expectation.

Rationale:

Reranker experiments are not required because embedding similarity is known to
fail; they are required because a reviewer will reasonably ask whether a
standard cross-encoder reranker over dense/RRF candidates can select an equally
small context more simply.

Minimal experiment:

1. Dense or RRF top-50 candidate pool.
2. Cross-encoder rerank candidate chunks.
3. Apply the same token budget as IntentWeight.
4. Compare quality-cost metrics on at least LoTTE 100k.

Possible outcomes:

- IntentWeight close to reranker with lower compute: lightweight controller
  claim strengthened.
- IntentWeight + reranker is best: method is complementary.
- Reranker dominates: claim should be narrowed, but the paper becomes more
  honest.

### P1-B: Expand Answer-Level Evaluation

Goal:

Move downstream LLM evaluation beyond a 60-query sanity check.

Recommended minimum:

- 300 queries.

Preferred:

- 500 queries.

Metrics:

- answer correctness;
- faithfulness;
- citation/context support;
- hallucination rate;
- pairwise win/tie/loss vs dense;
- input tokens/query;
- cost/correct answer.

This likely requires paid LLM calls and should be scheduled deliberately.

### P1-C: Stronger Encoder / Additional LoTTE Domains on GPU Machine

Goal:

Address robustness and external validity without overloading this CPU machine.

Planned off-device work:

1. BGE/E5/GTE or comparable stronger embedding model on the AMD GPU machine.
2. Additional LoTTE domains beyond technology/search and science/search.
3. Possibly more domain-scale points if compute allows.

Interpretation:

The goal is not to prove IntentWeight universally beats stronger dense models.
The goal is to test whether the final-context budget benefit persists under a
stronger encoder and more domains.

### P1-D: More Realistic Feedback Simulation

Goal:

Reduce the simulated-feedback weakness without claiming real user deployment.

Possible settings:

- label noise at 10/20/30/40%;
- delayed feedback;
- click-biased implicit feedback;
- sparse feedback;
- adversarial or low-trust feedback.

Recommended framing:

Feedback is a recovery/risk-control signal, not evidence of unconditional
first-pass improvement.

### P1-E: Evidence Completeness / Multi-Evidence Analysis

Goal:

Address the limitation that Hit@10 measures usable evidence, not complete
evidence collection.

Actions:

1. Bucket queries by number of GT chunks:
   - `|GT| = 1`;
   - `|GT| = 2-3`;
   - `|GT| >= 4`.
2. Report Hit@10, EvidenceRecall@10, nDCG@10, token saving by bucket.
3. Use the result to clarify when compaction should be disabled.

## Lower Priority / Optional

### P2-A: Non-LoTTE Corpus

Useful for stronger external validity, but less urgent than the same-budget
baseline, paired statistics, and answer-level evaluation. If added, it should
be a domain corpus with query-qrels and passage-level evidence, not a weak proxy
dataset.

### P2-B: Full Prompt-Compression Baseline

LLMLingua / Selective Context / DSLR-style baselines are relevant, but may
require more engineering. Dense+Sentence-MMR is the practical first baseline.

### P2-C: More Review-Facing Claim Tables

Possible useful additions:

- "what is claimed / not claimed" table;
- decision map for fallback / compaction / recovery;
- related-work comparison table.

These are helpful after the main framing and experiment gaps are addressed.

## Suggested Execution Order

1. Task45.1: Reframe title, abstract, introduction, contribution wording, and
   conclusion around manifold-inspired adaptive evidence selection with
   risk-calibrated final-context budget control as the measurable endpoint.
2. Task45.2: Clean calibration/test result presentation and handle the 400k
   `eligible=False` point.
3. Task45.3: Add paired non-inferiority statistics from existing artifacts.
4. Task45.4: Add method reproducibility details and pseudocode.
5. Task46: Implement Dense+Sentence-MMR same-budget baseline.
6. Task47: Plan/run reranker same-budget baseline.
7. Task48: Expand LLM answer-level evaluation when LLM budget is available.
8. Off-device track: run BGE/stronger encoder and additional LoTTE domains on
   the GPU machine.

## Current Recommendation

Start with Task45.1-45.4 on the current device. They directly address the most
credible review comments and do not require new heavy experiments. Then run
Task46 because Dense+Sentence-MMR same-budget is the highest-value new baseline
for the current paper claim.

## Human-Validation Alignment Update

Updated: 2026-06-17

After adding `docs/human_validation_criteria.md`, the plan should be interpreted
through five publication-readiness categories:

1. claim and manuscript narrative;
2. experimental evidence and baseline fairness;
3. statistical and analytical rigor;
4. presentation, reproducibility, and artifact traceability;
5. human-AI workflow and final submission readiness.

The original Task45 plan is still directionally correct, but the following
adjustments make it better aligned with a publishable-paper workflow.

### Adjustment 1: Keep Task45 as a Manuscript-Claim Repair Stage

Task45 should not become another experiment task. Its job is to make the paper
claim, section logic, method details, and evidence presentation consistent with
the strongest current evidence.

Required outputs:

- title/abstract/introduction/conclusion claim boundary revision;
- method reproducibility details and pseudocode;
- calibration/test caveat cleanup;
- paired-statistics insertion where existing artifacts already support it;
- claim-to-evidence crosswalk for the main tables and figures.

### Adjustment 2: Promote Task46 from "MMR Experiment" to Baseline-Fairness Test

Task46 should still start with Dense+Sentence-MMR, but the task objective should
be broader:

> test whether a simple same-budget dense-context compression baseline can
> explain away IntentWeight's final-context-token advantage.

Minimum Task46 scope:

1. Dense top-10 as the source candidate set.
2. Sentence or evidence-unit segmentation.
3. Query-sentence similarity plus MMR diversity selection.
4. Same final-token budget as IntentWeight.
5. Query-level comparison against dense fixed top-10 and IntentWeight.
6. Artifact-backed outputs for quality, token count, win/loss/tie, and harmed
   cases.

Task46 should not be considered complete if it only reports an average score
without query-level or artifact-traceable evidence.

### Adjustment 3: Keep Reranker as Task47, but Do Not Block Task46 on It

The reranker baseline is important, but it is heavier and may require more
dependencies or model/runtime choices. It should remain Task47.

Task46 answers the cheaper and more immediate reviewer objection:

> why not just compress dense retrieval under the same token budget?

Task47 answers the stronger but costlier objection:

> why not use a standard cross-encoder reranker to select the compact context?

### Adjustment 4: Add an Evidence Completeness Check Before Overusing Hit@10

Before finalizing the manuscript text, add a lightweight evidence-completeness
summary from existing artifacts where possible:

- `Hit@10`: at least one usable evidence chunk;
- `EvidenceRecall@10`: how much labeled evidence is covered;
- bucketed behavior for `|GT| = 1`, `2-3`, and `>=4` if available.

This protects the paper from overstating `Hit@10` as complete evidence
collection.

### Adjustment 4b: Track 400k Calibration as a Follow-up Gap

The 400k scale currently has positive frozen-test behavior but
`Calibration eligible=False`. Until a supplemental experiment re-establishes
eligibility, paper-facing text should:

- mark 400k as diagnostic or pending follow-up;
- avoid pooling it into the strongest calibration-eligible claim;
- keep its positive frozen-test result as useful evidence;
- list the missing eligibility as a planned follow-up experiment rather than
  hiding it.

### Adjustment 5: Treat Off-Device Work as Robustness, Not a Main-Path Blocker

Additional LoTTE domains and stronger GPU embedding models are valuable, but
they should not block the current CPU-side paper repair path.

Current-device main path:

1. Task45: claim/method/statistics/presentation repair.
2. Task46: same-budget dense compression baseline.
3. Task47: reranker same-budget baseline if practical.
4. Task48: expanded LLM answer-level evaluation when budget is available.

Off-device robustness path:

- stronger embedding model;
- additional LoTTE domains;
- larger answer-level or reranker evaluation if compute allows.

### Adjusted Immediate Next Step

Given Task44 is complete, the next task should be:

> Task45.1-45.4: revise the manuscript and supporting plan using the human
> validation criteria, preserving the local-structure -> LinUCB/feedback ->
> quality-efficiency trade-off logic chain, without starting new heavy
> experiments yet.

After that, run Task46 as the first new experiment task.
