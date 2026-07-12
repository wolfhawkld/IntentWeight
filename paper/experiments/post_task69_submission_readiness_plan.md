# Task71 Post-Task69 Submission-Readiness Plan

Updated: 2026-07-12

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

## Current Baseline

The following evidence is closed and must be treated as frozen:

- Task69.1-69.6 are complete; its audit has zero missing mandatory batches.
- The science/search 400k row is a weak scale boundary: one of five budget
  folds is eligible, mean Hit@10 delta is -0.67pp, token saving is 3.15%,
  and strict 1pp non-inferiority is 0/3.
- The exact-cache backend is valid for Task69. The 100k full-route comparison
  matched legacy execution exactly, and a direct 400k 32-query check produced
  exactly equal rankings and non-runtime metrics for both routing modes.
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
2. End-to-end systems profile.
3. Literature, statistical framing, and manuscript integration.
4. Final Figure 1, author metadata, package regeneration, and external review.

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

## Workstream After Task70: Method-to-Code Alignment

Priority: P0. No new retrieval experiment is required.

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
- Protocol versions: ensure Supplementary Table S29 and method prose
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

## Phase 3: End-to-End Systems Profile

Priority: P0. CPU is the primary online route environment; GPU preprocessing
is reported separately.

Implement a reproducible profiling harness for the tested MiniLM pipeline:

- offline embedding, KMeans/context artifacts, Dense/BM25 rankings,
  exact-score cache construction, elapsed time, peak RSS, disk-cache size,
  and hardware configuration;
- warm/cold p50 and p95 retrieval-routing latency, throughput, and route
  invocation rates;
- separate Dense, BM25, cluster-local, fusion, routing, and budget stages;
- evaluate technology/search 100k and science/search 400k;
- report final-context tokens beside, but never as a replacement for, system
  latency or memory;
- state the deployment workload used to amortize one-time preprocessing.

The AMD GPU may profile embedding/cache construction. Online LinUCB routing
remains CPU work. CPU and GPU numbers must not be merged into one end-to-end
claim without one declared deployment setup.

Completion gate:

- create a main or supplementary systems-cost table;
- distinguish warm/cold and offline/online boundaries;
- use context efficiency, not general system efficiency, wherever broader
  systems data is absent.

## Phase 4: Literature, Positioning, and Statistical Framing

Priority: P0 before the next external review.

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

- Integrate the method audit, Task70 outcomes, systems profile, and updated
  literature into the main manuscript and supplement.
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
| Frozen Task70 lacks a clear learned-feedback advantage | Non-stationary or preference-shift experiment | Tests the setting where feedback adaptation should be uniquely useful. |
| A reviewer requires a current compression comparator | LLMLingua-2 or equivalent same-budget baseline | Stronger than a routine ablation while preserving route-versus-compressor decomposition. |
| Geometry motivation remains challenged | Representation-independent or intrinsic-dimension diagnostic | Strengthens the design hypothesis without claiming a manifold theorem. |
| Domain breadth remains insufficient | One or two LoTTE 100k domains | Run only for a predeclared domain-generalization question. |

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
- Do not alter the algorithm to match inaccurate prose; update prose to match
  the tested implementation.
- Do not weaken metrics, tokenization, split discipline, or baseline strength
  to make a result easier to obtain.

## Final Submission Gate

The paper is ready for final external review or submission only when:

1. Phases 1-5 pass their completion gates.
2. The main claim remains bounded to a calibrated quality-context-cost
   frontier, with Dense retained as a recall floor.
3. The Task70 outcome is integrated honestly, including a negative or mixed
   outcome if that is what the frozen test finds.
4. The systems profile prevents unsupported end-to-end efficiency claims.
5. The final author-produced Figure 1 and all author metadata are present and
   validated.
6. Regenerated review and journal packages pass without critical errors.
