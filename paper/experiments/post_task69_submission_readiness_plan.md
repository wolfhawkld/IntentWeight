# Task71 Post-Task69 Submission-Readiness Plan

> **Historical checkpoint:** This document preserves the state at its stated
> date. Do not use its counts or remaining-work list as current status; use
> `paper/experiments/task80_authoritative_submission_state.md` and
> `paper/experiments/task80_remaining_work_checklist.md`.

Updated: 2026-07-15

## Purpose

This plan consolidates the post-Task69 work identified through the completed
experiment expansion, the Sol scientific review, and the exact-cache
validation for LoTTE science/search 400k. It closes remaining
submission-critical evidence gaps without lowering the evaluation standard or
adding datasets only for count.

The central paper direction remains:

`local geometry -> adaptive route selection -> feedback-informed adaptation -> independently calibrated context budget -> bounded quality-context-cost trade-off`

It does not restore unsupported direct-compression, unseen-query, or
end-to-end-efficiency claims.

The plan deliberately separates paper evidence from adjacent product ideas.
High-frequency answer caching, context caching, real-user RLHF, and a
per-query learned compression ratio may be useful future engineering features,
but they are not prerequisites for, or implicit conclusions of, this paper.

## Current Baseline

The following evidence is closed and must be treated as frozen:

- Task69.1-69.6 are complete; its audit has zero missing mandatory batches.
- The science/search 400k row is a weak scale boundary: one of five budget
  folds is eligible, mean Hit@10 delta is -0.67pp, token saving is 3.15%,
  and strict 1pp non-inferiority is 0/3.
- The exact-cache backend is valid for Task69. The 100k full-route comparison
  matched legacy execution exactly, and a direct 400k 32-query check produced
  exactly equal rankings and non-runtime metrics for both routing modes.
- Task72.2 closes the post-review runtime-integrity risks: future
  embedding-dependent artifacts are content-bound, checkpoints are provenance
  bound and structurally validated, cached random partitions use the active
  arm indices, and checkpoint recovery is separated from execution timing.
- Matched-backbone MiniLM, BGE, and E5 evidence is complete. A third encoder
  is not required for the current paper.
- The journal package passes technical validation. Figure 1 is technically
  compliant as a placeholder but remains a non-final author-produced asset.

## Completed Task70 and Immediate Next Workstream

Task70's formal frozen unseen-query evaluation is complete. It covers two
100k LoTTE domains, five canonical folds, seeds 13/17/19, eight history
epochs, frozen held-out ranking, paired bootstrap intervals, and McNemar
tests. The outcome establishes a necessary boundary: learned feedback does
not outperform matched static-nearest or cold no-feedback full routing on
first-pass unseen queries. See `task70_formal_frozen_policy_summary.md`.

Execution sequence:

1. Method-to-code alignment and claim sweep using the tested implementation
   and the formal Task70 boundary.
2. Literature, statistical framing, and manuscript integration.
3. Final Figure 1, author metadata, package regeneration, and external review.

The Task71 number denotes the post-Task69 submission-readiness workstream.

## Non-Negotiable Interpretation Rules

1. Do not mix partial legacy 400k outputs with optimized-backend 400k results.
   Legacy artifacts are provenance only.
2. Do not cite the pre-fix Task40 top-100 Dense-cache recovery accounting.
   Corrected top-k-scoped recovery artifacts are authoritative.
3. Do not pool technology/search, science/search, Banking77, CUAD, or
   historical fixed-split diagnostics as equivalent replications.
4. Do not state `route confidence -> direct safe-compression prediction`.
   Route control shapes the candidate pool; independent calibration selects
   the final context budget.
5. Do not represent repeated-query prequential adaptation as unseen-query
   generalization.
6. Do not describe final-context token saving as end-to-end latency, energy,
   memory, or total serving-cost reduction before the systems profile exists.
7. Retain seeds 13/17/19 and five-fold cross-fitting where specified. Do not
   weaken the design because larger seed counts are too slow on the CPU.

## Claim Ledger After Task70

The following distinctions are part of the paper claim boundary and must be
preserved in all later experiments, tables, figures, and prose.

1. **Feedback scope.** The tested mechanism is a contextual-bandit controller
   with controlled simulated feedback, not production RLHF. It supports
   repeated-interaction adaptation and conditional hard-case recovery. Task70
   rules out presenting it as a stable first-pass advantage on arbitrary
   unseen queries.
2. **Budget scope.** LinUCB feedback changes route state and evidence-pool
   composition. A separate calibration procedure selects the final-context
   budget. The paper does not claim that LinUCB learns a per-query or
   per-region compression ratio, nor that route confidence directly predicts
   safe compression.
3. **Cost scope.** Final evidence-context tokens are a provider-independent
   measure of downstream LLM input-token demand. Given a declared input-token
   price, they can be translated into a conditional LLM input-cost saving. This
   alone is not an end-to-end total-cost, latency, memory, or energy claim.
4. **Generalization scope.** A useful operating point need not exist for every
   corpus, scale, query region, or calibration fold. Dense fallback is a
   designed safe outcome when the calibration gate rejects compression; a zero
   saving row is not evidence that the method has failed to execute.
5. **Statistical scope.** Additional datasets improve external validity only
   when they use the common protocol and answer a predeclared question. They
   must not be pooled mechanically to manufacture a stronger significance
   result for heterogeneous tasks.

## Task71.1: Method-to-Code Alignment (Complete)

Priority: P0. No new retrieval experiment is required.

Completed: 2026-07-13. The line-level audit is recorded in
`task71_1_method_code_alignment_audit.md`. The canonical draft, ACL migration,
and journal submission package now describe the tested controller context,
feedback update, budget operator, attribution, common protocol, and frozen
unseen-query boundary without changing the evaluated method or result
artifacts.

Audit all paper-facing method statements against the tested implementation,
then update the manuscript, reproducibility notes, and regression checks:

- LinUCB context: describe the tested PCA-projected query representation, not
  an unimplemented concatenation of dense, lexical, geometry, feedback, and
  budget features.
- Reward: remove the unimplemented cost-penalized reward equation. State that
  evidence reward updates the controller while route gating and independently
  calibrated final-context budgeting control cost.
- Budget operator: describe an order-preserving budgeted subset with a
  mandatory prefix, not a guaranteed longest contiguous ranked prefix.
- Protocol versions: ensure Supplementary Table S22 and method prose
  distinguish historical versus common protocols, reward attribution, epochs,
  seeds, Dense rescue, backbone, and budget policy.
- Claim sweep: remove direct confidence-to-compression and unrestricted
  system-efficiency wording from the title, abstract, method, results,
  discussion, conclusion, captions, and supplement.

Completion gate:

- record a line-level implementation-to-manuscript audit;
- make equations and pseudocode match tested behavior;
- pass targeted regression tests and manuscript validators;
- do not rerun core results because the tested method is described accurately
  rather than changed.

Validation completed: full-draft, ACL LaTeX, ACL PDF, table/figure, paper
evidence, and journal-submission validators pass. The journal build explicitly
loads Latin Modern in the CAS manuscript and supplement so the generated PDFs
contain no Type 3 fonts.

## Task70: Formal Frozen Unseen-Query Evaluation (Complete)

Priority: P0. CPU route execution; GPU is not required.

The earlier Task70 smoke run verified only the freeze mechanism. The formal
replacement is complete; the frozen-policy boundary now needs manuscript
integration rather than another execution pass.

Formal design:

- Primary dataset: LoTTE technology/search 100k, five canonical folds.
- Confirmatory dataset: LoTTE science/search 100k under the same protocol.
- Seeds 13, 17, and 19; learned policies train on four folds for eight
  prequential history epochs.
- Rank the held-out fold once with policy, feedback memory, route statistics,
  and reward history frozen.
- Compare learned full and gated routes with static-nearest full and gated,
  cold no-feedback full and gated, fixed full fusion, and Dense.
- Report Hit@10, EvidenceRecall@10, MRR@10, nDCG@10, route/candidate metrics,
  paired bootstrap intervals, exact McNemar tests, and seed summaries.
- Keep context-token saving separate. This task establishes unseen-query
  route-policy transfer, not unseen-query compression safety.

Decision rule:

- Result: learned full routing is above Dense on average in both domains but
  does not exceed matched static-nearest or cold full routing. Learned gated
  routing is significantly below Dense in all three seeds in both domains.
- Paper boundary: retain feedback as recurring-query adaptation and hard-case
  recovery, not a universal first-pass or frozen unseen-query advantage.

## Task71.2: Auxiliary Implementation Operational Audit (Complete, Not Paper Evidence)

Priority: P2. Retained for implementation reproducibility only.

Completed, 2026-07-13: the artifact-backed LoTTE technology/search 100k
reference implementation profile is recorded in
`results/task71_2_systems_profile/lotte_technology_search_100k_systems_profile_aggregate.{json,csv,md}`.
It measures reward observation, trust weighting, state bookkeeping, LinUCB
updates, persistence sizing, cached artifact loading, and MiniLM query
encoding on one declared WSL/CPU configuration. These quantities are hardware,
cache-policy, and retrieval-backend dependent; they are not statistically
generalizable systems evidence. Accordingly, they are excluded from the main
paper, supplementary experiment tables, and the quality-context-cost argument.

The scripts and raw artifacts remain useful for implementation inspection. No
science/search 400k hardware profile, offline-construction rerun, amortized
serving-cost calculation, or cross-device benchmark is required for this
paper. A future systems paper would need matched Dense/Hybrid/IntentRoute
comparisons across declared deployment configurations before making latency,
memory, throughput, or end-to-end cost claims.

## Task71.3: Literature, Positioning, and Statistical Framing

Priority: P0 before the next external review.

Completed 2026-07-13. The task refreshed direct adaptive-retrieval and
adaptive-context-compression positioning from primary 2025 sources, documented
the role of the 1pp engineering guardrail, and distinguished primary frozen
comparison families from exploratory mechanism, robustness, and boundary
analyses. It did not alter numerical result artifacts or create a global pooled
superiority claim. The full-draft, ACL LaTeX, journal-submission, and
evidence-traceability validators passed after regeneration.

- Refresh related work from current primary sources for adaptive RAG, context
  selection/compression, and bandit retrieval.
- Position novelty as controlled systems composition and evidence attribution,
  not first use of geometry, LinUCB, adaptive RAG, or budget control.
- Foreground cross-fitted evidence and scale boundaries over favorable
  fixed-split results.
- Explain the application meaning of the 1pp non-inferiority margin and label
  exploratory comparison families; add multiplicity-aware reporting if it
  changes an inference.
- Keep the current IntentRoute naming unless a title change is explicitly
  approved after the claim sweep. Do not change it solely to add budget.

## Phase 5: Paper Integration and Submission Assets

Priority: P0 after Phases 1-4.

Automated integration completed 2026-07-13. The audit in
`phase5_submission_integration_audit.md` confirms that Task71.1 method/code
alignment, the Task70 frozen-policy boundary, and Task71.3 literature and
statistical framing are present in the canonical draft and generated packages.
The phase remains open only for final author-produced artwork, submission
metadata, and independent human review.

- Integrate the method audit, Task70 outcomes, and updated literature into the
  main manuscript and supplement. Do not promote Task71.2 implementation
  timing to paper evidence.
- Regenerate tables and figures only from traceable artifacts.
- Update stale Task67 historical text: the current Figure 1 placeholder now
  passes technical dimension/font validation but is still non-final artwork.
- The author supplies the final manual Figure 1 vector PDF following
  `paper/full_draft/figures/figure1_author_spec.md`; validate physical size,
  embedded fonts, text size, clipping, and method semantics.
- Complete author-owned fields: authors and affiliations, CRediT, funding,
  conflicts, acknowledgements, data/code URLs, and AI-use disclosure.
- Rebuild review and journal packages; run experiment, evidence, LaTeX, PDF,
  anonymity, table/figure, and submission validators.
- Request a final independent review only after all generated artifacts and
  the final Figure 1 are frozen.

## Conditional High-Value Strengthening

These are not blockers. Select them only after P0 outcomes are known and only
when they answer a defined scientific question.

| Condition or gap | Follow-up | Rationale |
|---|---|---|
| Feedback remains central after the Task70 boundary | Task72: recurrent, non-stationary feedback-stream evaluation without answer/context caching | Completed 2026-07-13. It found no stable final-retrieval feedback advantage under full fusion; retain as a credit-assignment boundary, not positive feedback evidence. |
| A reviewer requires a current compression comparator | LLMLingua-2 or equivalent same-budget baseline | Stronger than a routine ablation while preserving route-versus-compressor decomposition. |
| Geometry motivation remains challenged | Representation-independent or intrinsic-dimension diagnostic | Strengthens the design hypothesis without claiming a manifold theorem. |
| Domain breadth remains insufficient | Task73: one or two LoTTE 100k domains under the full common protocol | Tests a predeclared domain-generalization question; do not use dataset count alone as rationale. |
| Deployment-facing monetary interpretation is requested | Dated LLM input-price sensitivity table from final-context tokens | Converts measured final-context tokens to a conditional generation-stage input-cost component without claiming total-cost dominance. |

## Conditional Follow-Up Task Definitions

### Task72: Recurrent Feedback-Stream Evaluation

Priority: P1 research strengthening. This task is optional for submission, but
is the most direct way to strengthen the feedback-adaptation part of the
existing thesis after Task70.

Design a controlled query stream with recurring local intents and a declared
non-stationary preference or relevance shift. The protocol must keep answer
caching and context caching disabled: every event executes retrieval and
generation-context construction anew. It should separately report repeated
queries, semantically nearby queries, and entirely unseen queries.

Required controls: Dense, static-nearest routing, cold no-feedback routing,
and learned feedback routing with the same Dense/BM25 rescue and budget
policy. Report query-level Hit@10/EvidenceRecall@10, recovery rate, final
context tokens, Dense invocation rate, and confidence intervals. The result
may support recurrent-stream adaptation even if it shows no gain on entirely
unseen queries; it must not be reframed as general RLHF validation.

Completed 2026-07-13; see `task72_recurrent_feedback_stream_summary.md`.
The declared two-domain, three-seed run has complete coverage but does not
support a stable learned-feedback improvement in final fused retrieval or
recovery after the local-intent shift. It strengthens the existing attribution
boundary: full-fused reward can be dominated by Dense/BM25 rescue and cannot be
used as direct evidence that feedback improves the cluster route. Retain this
as boundary evidence only.

### Task72.1: Cluster-Credit Feedback Ablation

Priority: P1 mechanism clarification. Completed 2026-07-13; see
`task72_1_cluster_credit_ablation_summary.md`.

Task72.1 reuses the Task72 streams unchanged and removes Dense/BM25 rescue so
feedback reward, LinUCB update, and evaluation share a cluster-only retrieval
objective. It confirms learnable route capacity under oracle feedback and
conditional improvements under noisy feedback relative to cold LinUCB, but
does not establish stable trust-weighting superiority or beat static-nearest
geometry. This is supporting mechanism evidence only. It must be reported with
the Task72 full-fusion boundary rather than used to claim production RLHF or
universal feedback gains.

### Task72.2: Runtime Integrity Hardening

Priority: P0 infrastructure gate before Task73. Completed 2026-07-15; see
`task72_2_runtime_integrity_hardening.md`.

Task72.2 binds embedding-dependent artifacts to exact embedding content,
introduces source/input/artifact-bound checkpoint v2 validation, fixes cached
random-partition arm-index consistency, and separates cache construction,
actual seed computation, and checkpoint restoration timing. It changes no
Task69 retrieval result or paper claim. Historical checkpoints remain
provenance only; future experiments must use the hardened implementation and
fresh output directories.

### Task73: Hypothesis-Driven LoTTE Domain Expansion

Priority: P2 external-validity strengthening. Run one or two of
lifestyle/search, recreation/search, and writing/search at 100k only after
stating what domain property is being tested. Use the frozen Task69 common
protocol: shared preprocessing, MiniLM backbone, K=32, seeds 13/17/19,
eight-epoch prequential trajectory, Dense/BM25/hybrid controls, five-fold
cross-fitted budget selection, paired statistics, and explicit non-pooling.

The objective is to estimate heterogeneity of the bounded operating frontier,
not to obtain a single pooled p-value or force every domain to save tokens.

Completed 2026-07-15. The predeclared contrast selected recreation/search
and writing/search before outcome inspection. Both domains completed the full
common protocol, including matched baselines, trust/no-feedback routes,
five-fold budgets, paired statistics, geometry, and cross-fitted post-failure
recovery. The assumed lexicality ordering was reversed by the measured
query-positive overlap and therefore is not used to explain the result.
Writing/no-feedback provides a useful 10.09% saving frontier with a +0.12pp
mean Hit@10 change but only 2/3 strict NI seeds; recreation/no-feedback is a
weaker 5.42%/-0.76pp boundary with 0/3 strict NI seeds. Trust-weighted routes
fall back to Dense in all folds in both domains. See
`task73_lotte_domain_expansion_summary.md`.

### Task74: Task73 Evidence Integration And Submission Audit

Priority: P0 manuscript synchronization after Task73. Completed 2026-07-16;
see `task74_task73_manuscript_integration_plan.md` and
`task74_task73_manuscript_integration_summary.md`.

Task74 updates the canonical manuscript from seven settings/six domain areas to
nine settings/eight domain areas, integrates the predeclared Task73
heterogeneity result without changing the method or experiment, adds a
source-derived supplementary table, and regenerates all review and journal
packages. It must preserve the writing useful-frontier result, the recreation
strict-NI boundary, trust-weighted Dense fallback in both domains, the reversed
lexicality premise, and the separation between geometry-defined route signal
and independently calibrated context budgeting.

### Task75: Final Text And Literature Closure

Priority: P0 manuscript closure. Completed 2026-07-16; see
`task75_final_text_and_literature_plan.md` and
`task75_final_text_and_literature_summary.md`.

Task75 closes preregistration terminology, generation-stage input-cost scope,
feedback framing, direct 2026 literature positioning, conclusion length, and
the CAS-native STIX math-font defect without changing experiment evidence.

### Task76: Evidence-Preserving Editorial Compression

Priority: P1 submission-quality improvement. Completed 2026-07-16; see
`task76_manuscript_editorial_compression_plan.md` and
`task76_manuscript_editorial_compression_summary.md`.

Task76 removes 1,437 repeated words (10.53%) from Introduction, Discussion, and
Limitations while preserving the Task75 technical sections, all numerical and
negative evidence, the geometry/LinUCB/feedback thesis, and exact claim
boundaries. The CAS main manuscript is 25 pages and passes the complete evidence
and submission audit.

## Optional GPU / Overnight Expansion Queue

None of these closes the current paper. Do not start them before Phases 1-3
unless an external deadline makes that necessary.

1. FinQA full common protocol: preferred optional GPU expansion because it
   adds finance-domain breadth. It has 196,659 chunks and 16,562 queries.
2. One or two of LoTTE lifestyle, recreation, or writing at 100k: only when
   their domain difference tests a specific hypothesis.
3. TechQA or LegalBench-RAG: first validate license, preprocessing, corpus
   construction, and ground-truth-to-chunk mapping.
4. LoTTE science/search native full: optional scale breadth only; it should
   not displace more discriminative evidence.
5. Additional embedding backbone: deferred. MiniLM, BGE, and E5 already cover
   the current robustness claim.

## Explicit Non-Goals

- Do not rerun Task69 science/search 400k merely to reproduce slow legacy
  execution. The optimized backend has direct scale-specific equivalence
  evidence and is the only backend used by the completed 400k table.
- Do not expand seed count beyond 13/17/19 under current CPU constraints.
- Do not add all remaining LoTTE domains, every vertical dataset, or a third
  encoder for dataset-count optics.
- Do not add high-confidence answer caching, context caching, or semantic
  response reuse to the paper method. These are separate product optimizations
  whose cost model and correctness criteria differ from evidence selection.
- Do not relabel controlled simulated-feedback routing as RLHF or claim that
  the present experiments validate real-user feedback behavior.
- Do not introduce a per-query learned compression-ratio mechanism without a
  new method definition and a fully rerun evaluation family.
- Do not pool heterogeneous datasets, repeated-query trajectories, or
  overlapping calibration partitions as if they were IID replications.
- Do not alter the algorithm to match inaccurate prose; update prose to match
  the tested implementation.
- Do not weaken metrics, tokenization, split discipline, or baseline strength
  to make a result easier to obtain.

## Final Submission Gate

The paper is ready for final external review or submission only when:

1. Task71.1, Task71.3, and Phase 5 pass their completion gates. Task71.2 is an
   auxiliary reproducibility audit rather than a submission gate.
2. The main claim remains bounded to a calibrated quality-context-cost
   frontier, with Dense retained as a recall floor.
3. The Task70 outcome is integrated honestly, including a negative or mixed
   outcome if that is what the frozen test finds.
4. The manuscript avoids unsupported end-to-end latency, memory, throughput,
   energy, or total-serving-cost claims.
5. The final author-produced Figure 1 and all author metadata are present and
   validated.
6. Regenerated review and journal packages pass without critical errors.
