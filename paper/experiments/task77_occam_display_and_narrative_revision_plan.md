# Task77 Occam Display and Narrative Revision Plan

Status: completed 2026-07-17

Date: 2026-07-17

## Objective

Task77 applies the approved Occam's-razor review to the submission-facing
manuscript. It removes duplicate presentation and internal workflow prose,
raises the information density of the main displays, and clarifies the causal
boundary between route control and final-context budgeting. It does not change
the method implementation, rerun retrieval, pool heterogeneous datasets, or
discard any experiment artifact.

## Immutable Scientific Boundaries

- Preserve the geometry-guided and feedback-adaptive IntentRoute thesis.
- Keep Dense as the primary quality baseline, recall floor, and fallback.
- Treat geometry as a reproducible local-route structure and diagnostic signal,
  not theorem-level manifold proof or a direct compression-safety predictor.
- Treat simulated feedback as a post-outcome update to future route state, not
  real-user feedback, current-query label access, or a direct budget signal.
- Attribute the final token-quality frontier to the complete controller:
  route construction, Dense/BM25 rescue, and independently calibrated budgeting.
- Preserve all negative, boundary, uncertainty, and strict-noninferiority results.
- Keep datasets with unlike GT semantics in separate rows; compute no pooled
  effect, p-value, or global superiority claim.

## Approved Display Changes

1. Replace the six-point geometry-to-gain scatter with a three-panel Figure 3:
   cross-scale geometry profile, geometry-versus-random route attribution, and
   arm-granularity/fallback behavior.
2. Promote the existing cross-dataset result snapshot to main Table 4 as a
   cross-domain evidence matrix.
3. Move the old main arm-count table to the supplement; retain all five rows and
   expose its controller trend in Figure 3 Panel C.
4. Journalize implementation labels in Table 1 while preserving the exact
   policy parameters in the text and supplement.

## Approved Text Simplifications

- Consolidate the duplicated prequential description: Method owns update order;
  Experimental Setup owns feedback modes, epochs, and frozen controls.
- Replace paper-facing "semantic drift" with "selected-arm centroid mismatch
  safeguard". Preserve legacy artifact and code labels for reproducibility.
- Remove the RLHF analogy from Related Work; motivate feedback through
  contextual-bandit, relevance-feedback, click, and implicit-feedback work.
- Merge standalone Dense and evidence-completeness limitation subsections into
  the surrounding limitations without deleting either boundary.
- Remove the QA-tuned MiniLM-family display from the submission package. Retain
  matched MiniLM/BGE/E5 and BGE quality-first evidence and all historical files.
- Retain Sentence-MMR as the formal shared compressor. Remove
  SelectiveContext-lite from the submission evidence set; identify official
  LLMLingua-2 as an untested future strong baseline rather than implying that it
  has already been evaluated.
- Remove the historical fixed-top-10 correction table and author-facing
  reporting-guardrail prose from the scientific supplement; preserve their
  provenance in experiment documentation and validators.
- Remove exact duplicate supplementary tables whose values already appear in a
  main table. Keep only genuinely additional protocol, seed, recovery, judge,
  and boundary evidence.

## Source Mapping

- Figure 3 Panel A:
  `task30_lotte_geometry_scale_validation.csv` and
  `task43_lotte_science_geometry_diagnostics.csv`.
- Figure 3 Panel B:
  `task58_geometry_random_ablation_summary.csv`.
- Figure 3 Panel C and moved arm-count table:
  `task60_arm_count_sensitivity_summary.csv`.
- Main cross-dataset matrix:
  `task69_cross_dataset_consistency.md` plus its source result families;
  Task73 recreation/writing rows remain source-derived from
  `task73_lotte_domain_expansion.json`.

## Validation Contract

- Generate the SVG deterministically from tracked source artifacts.
- Keep the main figure at the 190 mm full-width target, with no paper-facing
  text below 7 pt at 100% size and no Type 3 fonts after PDF conversion.
- Audit every main-table cell and Figure 3 datum against its source artifact.
- Regenerate Markdown review packet, ACL LaTeX, CAS LaTeX, PDFs, and manifests.
- Run citation, terminology, Task73/74 integration, evidence-provenance, PDF,
  and unit-test suites.
- Record all intentional removals and the final page/display counts in the
  Task77 summary.
